from __future__ import annotations

import argparse
import math
import os
import re
import sqlite3
import time
from datetime import datetime
from pathlib import Path

import pandas as pd
import requests

import component_matcher_build as cmb


ROOT = Path(__file__).resolve().parent
OFFICIAL_CSV = ROOT / "Inductor" / "official_inductor_expansion.csv"
SNAPSHOT_CSV = ROOT / "Inductor" / "murata_inductor_family_expansion.csv"
DB_PATH = ROOT / "components.db"
API_URL = "https://pimapi.murata.com/public/api/pim/v1/products/search"
LANGUAGE_REGION = "en-global"
PAGE_SIZE = 100
DEFAULT_TIMEOUT = 60

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Content-Type": "application/json",
}


CATEGORY_CONFIGS = [
    {
        "key": "power",
        "product_category_id": "inductor",
        "filters": [
            {"id": "productionStatus", "value": "available"},
            {"id": "targetCircuitClassification", "value": "InductorForPowerLines"},
        ],
        "component_type": "功率电感",
        "special_use": "Power Inductor",
        "series_desc_suffix": "功率电感系列",
    },
    {
        "key": "rf",
        "product_category_id": "inductor",
        "filters": [
            {"id": "productionStatus", "value": "available"},
            {"id": "targetCircuitClassification", "value": "RFInductor"},
        ],
        "component_type": "射频电感",
        "special_use": "RF Inductor",
        "series_desc_suffix": "RF高频电感系列",
    },
    {
        "key": "general",
        "product_category_id": "inductor",
        "filters": [
            {"id": "productionStatus", "value": "available"},
            {"id": "targetCircuitClassification", "value": "GeneralCircuits"},
        ],
        "component_type": "功率电感",
        "special_use": "General Circuit Inductor",
        "series_desc_suffix": "通用电感系列",
    },
    {
        "key": "cmc",
        "product_category_id": "commonModeChokeCoilCommonModeNoiseFilter",
        "filters": [
            {"id": "productionStatus", "value": "available"},
        ],
        "component_type": "共模电感",
        "special_use": "Common Mode Choke",
        "series_desc_suffix": "共模电感系列",
    },
    {
        "key": "bead",
        "product_category_id": "ferriteBeadInductortypefilter",
        "filters": [
            {"id": "productionStatus", "value": "available"},
        ],
        "component_type": "磁珠",
        "special_use": "Ferrite Bead",
        "series_desc_suffix": "磁珠系列",
    },
]

TARGET_TYPES = ("功率电感", "射频电感", "共模电感", "磁珠")
KEY_COLUMNS = ["品牌", "型号", "器件类型"]


def clean_text(value: object) -> str:
    if value is None:
        return ""
    try:
        if value != value:
            return ""
    except Exception:
        pass
    text = str(value).strip()
    return "" if text.lower() == "nan" else text


def truncate_text(text: object, max_len: int = 220) -> str:
    cleaned = clean_text(text)
    if len(cleaned) <= max_len:
        return cleaned
    return cleaned[: max_len - 1].rstrip() + "…"


def trim_number(value: object) -> str:
    text = clean_text(value)
    if not text:
        return ""
    try:
        number = float(text)
    except Exception:
        return text
    if math.isfinite(number):
        trimmed = f"{number:.6f}".rstrip("0").rstrip(".")
        return trimmed if trimmed else "0"
    return text


def first_nonempty(*values: object) -> str:
    for value in values:
        text = clean_text(value)
        if text:
            return text
    return ""


def build_item_lookup(item: dict) -> dict[str, dict]:
    lookup: dict[str, dict] = {}
    for info in item.get("itemInfoList", []):
        key = clean_text(info.get("id", ""))
        if not key:
            continue
        chosen = {}
        for candidate in info.get("valueList", []) or []:
            if any(clean_text(candidate.get(field, "")) for field in ("displayName", "value", "linkUrl", "assetUrl")):
                chosen = candidate
                break
        lookup[key] = chosen
    return lookup


def pick_value(lookup: dict[str, dict], key: str) -> str:
    entry = lookup.get(key.strip(), {})
    return clean_text(entry.get("value"))


def pick_display(lookup: dict[str, dict], key: str) -> str:
    entry = lookup.get(key.strip(), {})
    return first_nonempty(entry.get("displayName"), entry.get("value"))


def pick_unit(lookup: dict[str, dict], key: str) -> str:
    entry = lookup.get(key.strip(), {})
    return clean_text(entry.get("unit"))


def pick_link(lookup: dict[str, dict], key: str) -> str:
    entry = lookup.get(key.strip(), {})
    return first_nonempty(entry.get("linkUrl"), entry.get("assetUrl"))


def format_size_mm(length: str, width: str, thickness: str) -> str:
    parts = [part for part in (trim_number(length), trim_number(width), trim_number(thickness)) if part]
    if not parts:
        return ""
    return " x ".join(parts) + " mm"


def join_summary(*parts: object) -> str:
    cleaned = [truncate_text(part, 180) for part in parts if clean_text(part)]
    return " | ".join(cleaned)


def format_note(label: str, *values: object) -> str:
    cleaned = [clean_text(v) for v in values if clean_text(v)]
    if not cleaned:
        return ""
    return f"{label}: " + " | ".join(cleaned)


def normalize_status(value: str) -> str:
    status = clean_text(value).lower()
    if status in {"available", "in production", "production"}:
        return "Active"
    if status == "nrnd":
        return "NRND"
    if status in {"planneddiscontinue", "planned discontinue"}:
        return "Planned Discontinue"
    if status == "discontinued":
        return "Discontinued"
    return clean_text(value)


def fetch_page(session: requests.Session, config: dict, page: int, page_size: int) -> dict:
    payload = {
        "productCategoryId": config["product_category_id"],
        "languageRegion": LANGUAGE_REGION,
        "pageSize": page_size,
        "page": page,
        "partNum": "",
        "searchCondClass": 2,
        "series": "",
        "sortKey": "",
        "valSearchCondList": config["filters"],
        "rangeValSearchCondList": [],
        "dateRangeSearchCondList": [],
    }
    response = session.post(API_URL, json=payload, timeout=DEFAULT_TIMEOUT)
    response.raise_for_status()
    return response.json()


def fetch_category_rows(config: dict, page_size: int = PAGE_SIZE) -> pd.DataFrame:
    session = requests.Session()
    session.headers.update(HEADERS)

    first = fetch_page(session, config, 1, page_size)
    total = int(first.get("totalNum", 0) or 0)
    pages = max(1, math.ceil(total / page_size))
    print(f"[murata:{config['key']}] total={total} page_size={page_size} pages={pages}", flush=True)

    rows: list[dict[str, str]] = []
    for page in range(1, pages + 1):
        page_data = first if page == 1 else fetch_page(session, config, page, page_size)
        items = page_data.get("productSearchResult", []) or []
        print(f"[murata:{config['key']}] page {page}/{pages} items={len(items)}", flush=True)
        for item in items:
            row = build_row(item, config, page)
            if row:
                rows.append(row)
        time.sleep(0.1)

    if not rows:
        return pd.DataFrame()

    df = pd.DataFrame(rows).fillna("")
    df = df.drop_duplicates(subset=KEY_COLUMNS, keep="first").reset_index(drop=True)
    return df


def build_common_fields(lookup: dict[str, dict], config: dict, page_no: int) -> dict[str, str] | None:
    part_num = first_nonempty(pick_value(lookup, "partNum"), pick_display(lookup, "publicPartNum"))
    if not part_num:
        return None

    series = pick_value(lookup, "series")
    product_name = pick_display(lookup, "productName")
    size_code = first_nonempty(
        pick_value(lookup, "sizeCodeInMmInch"),
        pick_display(lookup, "sizeCodeInMmInch"),
    )
    size_mm = format_size_mm(
        pick_value(lookup, "length"),
        pick_value(lookup, "width"),
        first_nonempty(pick_value(lookup, "thickness"), pick_value(lookup, "thicknessMax")),
    )
    temp_display = first_nonempty(pick_display(lookup, "operaTemp"), pick_display(lookup, "operaTempMax"))
    spec_url = pick_link(lookup, "specificationSheetUrl")
    series_url = pick_link(lookup, "seriesUrl")
    doc_url = first_nonempty(
        spec_url,
        series_url,
        pick_link(lookup, "generalDocumentUrls1"),
        pick_link(lookup, "generalDocumentUrls2"),
        pick_link(lookup, "generalUrls1"),
        pick_link(lookup, "generalUrls2"),
    )
    product_features = pick_display(lookup, "productFeatures")
    special_notes = pick_display(lookup, "specialNotes")
    search_description = pick_display(lookup, "searchDescription")
    current_l = first_nonempty(
        pick_display(lookup, "ratedCurrentForLChangeDisp"),
        pick_display(lookup, "ratedCurrentForLChangeMax"),
        pick_display(lookup, "ratedCurrent"),
        pick_display(lookup, "ratedCurrentAt125deg"),
        pick_display(lookup, "ratedCurrentAt85deg"),
        pick_display(lookup, "ratedCurrentAt150deg"),
    )
    current_t = first_nonempty(
        pick_display(lookup, "ratedCurrentForTempChangeDisp"),
        pick_display(lookup, "ratedCurrentForTempChangeMax"),
        pick_display(lookup, "ratedCurrentForTempChangeMax85"),
        pick_display(lookup, "ratedCurrentForTempChangeMax105"),
        pick_display(lookup, "ratedCurrentForTempChangeMax125"),
        pick_display(lookup, "ratedCurrentForTempChangeMax150"),
        pick_display(lookup, "ratedCurrentForTempChangeMax155"),
    )
    dcr_display = first_nonempty(pick_display(lookup, "dcResistanceMax"), pick_display(lookup, "dcResistance"))
    shield = pick_display(lookup, "magneticShieldType")
    inductance_value = first_nonempty(pick_value(lookup, "inductance"))
    inductance_unit = first_nonempty(pick_unit(lookup, "inductance"), pick_unit(lookup, "inductanceFrequency"))
    inductance_tol = pick_display(lookup, "inductanceTolerance")
    common_mode = first_nonempty(pick_display(lookup, "commonModeImpedance100"))
    common_mode_inductance = first_nonempty(pick_value(lookup, "commonModeInductance"))
    common_mode_unit = first_nonempty(pick_unit(lookup, "commonModeInductance"))
    impedance100 = first_nonempty(pick_display(lookup, "impedance100"))
    impedance2000 = first_nonempty(pick_display(lookup, "impedance2000"))
    impedance_target = first_nonempty(pick_display(lookup, "impedanceAtTargetFrequency"))
    circuit_numbers = pick_display(lookup, "circuitNumbers")
    shape = pick_display(lookup, "shape")
    recommended_apps = pick_display(lookup, "recommendedApplications")
    part_num_with_package = first_nonempty(pick_value(lookup, "partNumWithPackageCode"))
    package_code = first_nonempty(size_code, part_num_with_package)
    production_status = normalize_status(pick_value(lookup, "productionStatus"))

    base = {
        "品牌": "村田Murata",
        "型号": part_num,
        "系列": series,
        "尺寸（inch）": "",
        "材质（介质）": "",
        "容值": "",
        "容值单位": "",
        "容值误差": "",
        "耐压（V）": "",
        "备注1": "",
        "备注2": spec_url or series_url,
        "备注3": "",
        "器件类型": config["component_type"],
        "安装方式": "SMT" if config["key"] in {"power", "rf", "general"} else ("SMT" if shape or package_code else "SMT"),
        "封装代码": package_code,
        "尺寸（mm）": size_mm,
        "规格摘要": "",
        "生产状态": production_status,
        "长度（mm）": trim_number(pick_value(lookup, "length")),
        "宽度（mm）": trim_number(pick_value(lookup, "width")),
        "高度（mm）": trim_number(first_nonempty(pick_value(lookup, "thickness"), pick_value(lookup, "thicknessMax"))),
        "官网链接": doc_url,
        "数据来源": "Murata official PIM API",
        "数据状态": "官方API抽取",
        "校验时间": datetime.now().strftime("%Y-%m-%d"),
        "校验备注": f"Murata PIM product search API {config['key']} page {page_no}",
        "直径（mm）": "",
        "脚距（mm）": "",
        "极性": "",
        "ESR": "",
        "纹波电流": "",
        "寿命（h）": "",
        "工作温度": temp_display,
        "阻值@25C": "",
        "阻值单位": "",
        "阻值误差": "",
        "B值": "",
        "B值条件": "",
        "共模阻抗": common_mode,
        "阻抗单位": "Ω" if common_mode else "",
        "额定电流": current_l or current_t,
        "DCR": dcr_display,
        "回路数": circuit_numbers,
        "电感值": inductance_value or common_mode_inductance,
        "电感单位": inductance_unit or common_mode_unit,
        "电感误差": inductance_tol,
        "饱和电流": "",
        "屏蔽类型": shield,
        "阻抗@100MHz": impedance100 or impedance_target,
        "系列说明": f"Murata {series} {config['series_desc_suffix']}".strip(),
        "_model_rule_authority": "Murata official PIM API",
        "_resistance_ohm": "",
        "输出频率": "",
        "频率单位": "",
        "频差（ppm）": "",
        "电源电压": "",
        "输出类型": "",
        "占空比": "",
        "频率": "",
        "负载电容（pF）": "",
        "驱动电平": "",
        "_body_size": size_mm,
    }

    if config["key"] in {"power", "rf", "general"}:
        current_summary = format_note("Current", current_l, current_t)
        summary = join_summary(
            search_description,
            product_name,
            shield,
            temp_display,
            current_summary,
            dcr_display,
            special_notes,
        )
        base.update(
            {
                "特殊用途": config["special_use"],
                "备注1": current_summary,
                "备注3": join_summary(special_notes, product_features),
                "规格摘要": summary,
            }
        )
    elif config["key"] == "cmc":
        common_mode_note = format_note("Common mode impedance", common_mode)
        current_summary = format_note("Rated current", current_l or current_t)
        summary = join_summary(
            search_description,
            product_name,
            common_mode_note,
            current_summary,
            dcr_display,
            temp_display,
            product_features,
        )
        base.update(
            {
                "特殊用途": config["special_use"],
                "备注1": join_summary(common_mode_note, current_summary, format_note("Circuit", circuit_numbers)),
                "备注3": join_summary(special_notes, product_features, recommended_apps),
                "规格摘要": summary,
                "共模阻抗": common_mode,
                "阻抗单位": "Ω" if common_mode else "",
                "电感值": common_mode_inductance,
                "电感单位": common_mode_unit,
                "阻抗@100MHz": common_mode,
            }
        )
    else:
        impedance_note = join_summary(
            format_note("Impedance@100MHz", impedance100),
            format_note("Impedance@TargetFreq", impedance_target),
            format_note("Impedance@2kHz", impedance2000),
        )
        current_summary = format_note("Rated current", current_l or current_t)
        summary = join_summary(
            search_description,
            product_name,
            impedance_note,
            current_summary,
            dcr_display,
            temp_display,
            product_features,
        )
        base.update(
            {
                "特殊用途": config["special_use"],
                "备注1": join_summary(impedance_note, current_summary),
                "备注3": join_summary(special_notes, product_features, recommended_apps),
                "规格摘要": summary,
                "共模阻抗": "",
                "阻抗单位": "",
                "阻抗@100MHz": impedance100,
                "电感值": "",
                "电感单位": "",
                "电感误差": "",
            }
        )

    if not base["备注2"]:
        base["备注2"] = series_url or spec_url
    return base


def build_row(item: dict, config: dict, page_no: int) -> dict[str, str] | None:
    lookup = build_item_lookup(item)
    return build_common_fields(lookup, config, page_no)


def fetch_all_rows(categories: list[str] | None = None, page_size: int = PAGE_SIZE) -> pd.DataFrame:
    selected = CATEGORY_CONFIGS
    if categories:
        category_set = {clean_text(cat).strip().lower() for cat in categories if clean_text(cat).strip()}
        selected = [cfg for cfg in CATEGORY_CONFIGS if cfg["key"].lower() in category_set]
    frames: list[pd.DataFrame] = []
    for config in selected:
        frame = fetch_category_rows(config, page_size=page_size)
        if not frame.empty:
            frames.append(frame)
    if not frames:
        return pd.DataFrame()
    combined = pd.concat(frames, ignore_index=True).fillna("")
    combined = combined.drop_duplicates(subset=KEY_COLUMNS, keep="first").reset_index(drop=True)
    return combined


def merge_into_official_csv(new_rows: pd.DataFrame) -> tuple[int, int]:
    if new_rows is None or new_rows.empty:
        return 0, 0

    if OFFICIAL_CSV.exists():
        existing = pd.read_csv(OFFICIAL_CSV, encoding="utf-8-sig").fillna("")
    else:
        existing = pd.DataFrame(columns=list(new_rows.columns))

    columns = list(existing.columns)
    for col in new_rows.columns:
        if col not in columns:
            columns.append(col)

    existing = existing.reindex(columns=columns, fill_value="")
    new_rows = new_rows.reindex(columns=columns, fill_value="")

    if {"品牌", "型号"}.issubset(existing.columns) and {"品牌", "型号"}.issubset(new_rows.columns):
        incoming_keys = {
            (clean_text(brand), clean_text(model))
            for brand, model in zip(new_rows["品牌"].astype(str), new_rows["型号"].astype(str))
            if clean_text(brand) and clean_text(model)
        }
        if incoming_keys:
            existing = existing[
                ~existing.apply(
                    lambda row: (
                        clean_text(row.get("品牌", "")),
                        clean_text(row.get("型号", "")),
                    ) in incoming_keys,
                    axis=1,
                )
            ]

    merged = pd.concat([existing, new_rows], ignore_index=True).fillna("")
    merged = merged.drop_duplicates(subset=KEY_COLUMNS, keep="first").reset_index(drop=True)
    merged.to_csv(OFFICIAL_CSV, index=False, encoding="utf-8-sig")
    return len(existing), len(merged)


def build_db_rows(source_rows: pd.DataFrame, db_columns: list[str]) -> pd.DataFrame:
    work = source_rows.copy().fillna("")
    if "_model_rule_authority" not in work.columns:
        work["_model_rule_authority"] = "Murata official PIM API"
    if "_resistance_ohm" not in work.columns:
        work["_resistance_ohm"] = ""
    if "_body_size" not in work.columns:
        work["_body_size"] = work.get("尺寸（mm）", "")
    if "容值_pf" not in work.columns:
        work["容值_pf"] = ""
    for col in db_columns:
        if col not in work.columns:
            work[col] = ""
    return work[db_columns].fillna("")


def replace_rows(conn: sqlite3.Connection, df: pd.DataFrame, db_columns: list[str]) -> tuple[int, int]:
    if df is None or df.empty:
        return 0, 0

    work = build_db_rows(df, db_columns)
    temp_table = "_tmp_murata_inductor_family"
    work.to_sql(temp_table, conn, if_exists="replace", index=False, method="multi", chunksize=250)
    cur = conn.cursor()
    cur.execute(
        f"""
        DELETE FROM components
        WHERE "品牌" = ?
          AND "器件类型" IN ({",".join("?" for _ in TARGET_TYPES)})
        """,
        ("村田Murata", *TARGET_TYPES),
    )
    deleted = int(cur.execute("SELECT changes()").fetchone()[0] or 0)
    insert_cols_sql = ", ".join(f'"{col}"' for col in db_columns)
    select_cols_sql = ", ".join(f't."{col}"' for col in db_columns)
    cur.execute(
        f"""
        INSERT INTO components ({insert_cols_sql})
        SELECT {select_cols_sql}
        FROM "{temp_table}" t
        """
    )
    inserted = int(cur.execute("SELECT changes()").fetchone()[0] or 0)
    cur.execute(f'DROP TABLE IF EXISTS "{temp_table}"')
    conn.commit()
    return deleted, inserted


def refresh_cache_subset(module, updated_rows: pd.DataFrame) -> tuple[bool, bool]:
    import sync_inductor_official_to_db as sidb

    search_refreshed = sidb.refresh_search_sidecar_subset(module, updated_rows)
    prepared_refreshed = sidb.refresh_prepared_cache_subset(module, updated_rows)
    return search_refreshed, prepared_refreshed


def apply_to_database(source_rows: pd.DataFrame) -> tuple[int, int]:
    if source_rows is None or source_rows.empty:
        return 0, 0

    module = cmb._load_component_matcher()
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    conn.execute("PRAGMA temp_store=MEMORY")
    try:
        db_columns = [row[1] for row in conn.execute("PRAGMA table_info(components)").fetchall()]
        deleted, inserted = replace_rows(conn, source_rows, db_columns)
        conn.close()
    except Exception:
        conn.close()
        raise

    db_rows = build_db_rows(source_rows, db_columns)
    search_refreshed, prepared_refreshed = refresh_cache_subset(module, db_rows)
    print(f"[murata] search cache refreshed={search_refreshed} prepared cache refreshed={prepared_refreshed}", flush=True)
    return deleted, inserted


def summarize_field_fill(df: pd.DataFrame) -> dict[str, int]:
    summary = {"rows": int(len(df))}
    for col in ["规格摘要", "电感值", "电感单位", "共模阻抗", "阻抗@100MHz", "额定电流", "DCR", "工作温度", "安装方式", "生产状态"]:
        if col in df.columns:
            summary[col] = int(df[col].astype(str).str.strip().ne("").sum())
    return summary


def load_official_rows_from_db(conn: sqlite3.Connection, source_df: pd.DataFrame) -> pd.DataFrame:
    db_df = pd.read_sql_query(
        """
        SELECT *
        FROM components
        WHERE "器件类型" IN ("功率电感", "共模电感", "磁珠")
        """,
        conn,
    ).fillna("")
    if db_df.empty or source_df.empty:
        return pd.DataFrame()
    keys = source_df.loc[:, KEY_COLUMNS].drop_duplicates()
    return db_df.merge(keys, on=KEY_COLUMNS, how="inner")


def main() -> int:
    parser = argparse.ArgumentParser(description="Fetch Murata inductor family products and merge them into the official inductor source CSV.")
    parser.add_argument("--page-size", type=int, default=PAGE_SIZE)
    parser.add_argument("--categories", nargs="*", default=[], help="Optional category keys to fetch: power rf general cmc bead")
    parser.add_argument("--skip-merge", action="store_true", help="Only export the Murata snapshot CSV.")
    parser.add_argument("--apply-db", action="store_true", help="Also write the Murata rows into components.db and refresh the caches for this subset.")
    args = parser.parse_args()

    SNAPSHOT_CSV.parent.mkdir(parents=True, exist_ok=True)
    rows = fetch_all_rows(categories=args.categories or None, page_size=args.page_size)
    if rows.empty:
        raise SystemExit("No Murata inductor family rows were fetched.")

    rows.to_csv(SNAPSHOT_CSV, index=False, encoding="utf-8-sig")
    print(f"[murata] wrote snapshot: {SNAPSHOT_CSV} ({len(rows)} rows)", flush=True)

    if not args.skip_merge:
        before, after = merge_into_official_csv(rows)
        print(f"[murata] merged into official CSV: {before} -> {after} rows", flush=True)

    if args.apply_db:
        deleted, inserted = apply_to_database(rows)
        print(f"[murata] applied to DB: deleted={deleted} inserted={inserted}", flush=True)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
