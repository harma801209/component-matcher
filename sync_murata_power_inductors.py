from __future__ import annotations

import argparse
import math
import re
import sqlite3
import time
from datetime import datetime
from pathlib import Path

import pandas as pd
import requests


ROOT = Path(__file__).resolve().parent
OFFICIAL_CSV = ROOT / "Inductor" / "official_inductor_expansion.csv"
MURATA_CSV = ROOT / "Inductor" / "murata_power_inductor_expansion.csv"
DB_PATH = ROOT / "components.db"

API_URL = "https://pimapi.murata.com/public/api/pim/v1/products/search"
LANGUAGE_REGION = "en-global"
PAGE_SIZE = 100
DEFAULT_TIMEOUT = 60

TARGET_FILTERS = [
    {"id": "productionStatus", "value": "available"},
    {"id": "targetCircuitClassification", "value": "InductorForPowerLines"},
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Content-Type": "application/json",
}


def clean_text(value: object) -> str:
    if value is None:
        return ""
    try:
        if value != value:  # NaN
            return ""
    except Exception:
        pass
    text = str(value).strip()
    return "" if text.lower() == "nan" else text


def trim_number(value: object) -> str:
    text = clean_text(value)
    if text == "":
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
    length = trim_number(length)
    width = trim_number(width)
    thickness = trim_number(thickness)
    parts = [part for part in (length, width, thickness) if part]
    if not parts:
        return ""
    return " x ".join(parts) + " mm"


def format_current_note(*values: str) -> str:
    parts = []
    labels = ["L change", "Temp rise", "Q/SRF"]
    for label, value in zip(labels, values):
        text = clean_text(value)
        if text:
            parts.append(f"{label}: {text}")
    return " | ".join(parts)


def build_summary(lookup: dict[str, dict]) -> str:
    parts = [
        pick_display(lookup, "searchDescription"),
        pick_display(lookup, "construction"),
        pick_display(lookup, "magneticShieldType"),
        pick_display(lookup, "operaTemp"),
        pick_display(lookup, "ratedCurrentForLChangeDisp"),
        pick_display(lookup, "ratedCurrentForTempChangeDisp"),
        pick_display(lookup, "dcResistanceMax"),
        pick_display(lookup, "q"),
        pick_display(lookup, "srf"),
    ]
    return " | ".join([part for part in parts if part])


def build_series_description(series: str, construction: str) -> str:
    series = clean_text(series)
    construction = clean_text(construction)
    if series and construction:
        return f"Murata {series} 功率电感系列（{construction}）"
    if series:
        return f"Murata {series} 功率电感系列"
    return "Murata 功率电感系列"


def map_status(value: str) -> str:
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


def build_row(item: dict, page_no: int) -> dict[str, str]:
    lookup = build_item_lookup(item)
    brand = "村田Murata"
    part_num = first_nonempty(pick_value(lookup, "partNum"), pick_display(lookup, "publicPartNum"))
    if not part_num:
        return {}

    series = pick_value(lookup, "series")
    construction = pick_display(lookup, "construction")
    shield = pick_display(lookup, "magneticShieldType")
    size_mm_code = first_nonempty(pick_value(lookup, "sizeCodeInMmInch"), pick_display(lookup, "sizeCodeInMmInch"))
    size_inch = first_nonempty(pick_value(lookup, "sizeCodeInInch"), pick_display(lookup, "sizeCodeInInch"))
    length = pick_value(lookup, "length")
    width = pick_value(lookup, "width")
    thickness = first_nonempty(
        pick_value(lookup, "thickness"),
        pick_value(lookup, "thicknessMax"),
    )
    size_mm = format_size_mm(length, width, thickness)

    inductance_value = first_nonempty(pick_value(lookup, "inductance"))
    inductance_unit = first_nonempty(pick_unit(lookup, "inductance"), pick_unit(lookup, "inductanceFrequency"))
    inductance_tol = pick_display(lookup, "inductanceTolerance")

    current_l = first_nonempty(
        pick_display(lookup, "ratedCurrentForLChangeDisp"),
        pick_display(lookup, "ratedCurrentForLChangeMax"),
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
    current_display = current_l or current_t

    dcr_display = first_nonempty(pick_display(lookup, "dcResistanceMax"), pick_display(lookup, "dcResistance"))
    q_display = first_nonempty(pick_display(lookup, "q"))
    srf_display = first_nonempty(pick_display(lookup, "srf"))
    temp_display = first_nonempty(pick_display(lookup, "operaTemp"), pick_display(lookup, "operaTempMax"))
    series_url = pick_link(lookup, "seriesUrl")
    spec_pdf = pick_link(lookup, "specificationSheetUrl")
    notes = pick_display(lookup, "specialNotes")
    package_code = size_mm_code
    if not package_code:
        package_code = first_nonempty(pick_value(lookup, "partNumWithPackageCode"))

    return {
        "品牌": brand,
        "型号": part_num,
        "系列": series,
        "尺寸（inch）": size_inch,
        "材质（介质）": "",
        "容值": inductance_value,
        "容值单位": inductance_unit,
        "容值误差": inductance_tol,
        "耐压（V）": "",
        "特殊用途": "Power Inductor",
        "备注1": format_current_note(current_l, current_t, first_nonempty(q_display, srf_display)),
        "备注2": spec_pdf or series_url,
        "备注3": " | ".join(
            part
            for part in [
                notes,
                f"Construction: {construction}" if construction else "",
                f"Shield: {shield}" if shield else "",
                f"Operating temp: {temp_display}" if temp_display else "",
                f"Q: {q_display}" if q_display else "",
                f"SRF: {srf_display}" if srf_display else "",
            ]
            if part
        ),
        "器件类型": "功率电感",
        "安装方式": "SMT",
        "封装代码": package_code,
        "尺寸（mm）": size_mm,
        "规格摘要": build_summary(lookup),
        "生产状态": map_status(pick_value(lookup, "productionStatus")),
        "长度（mm）": trim_number(length),
        "宽度（mm）": trim_number(width),
        "高度（mm）": trim_number(thickness),
        "官网链接": series_url or spec_pdf,
        "数据来源": "Murata official PIM API",
        "数据状态": "官方API抽取",
        "校验时间": datetime.now().strftime("%Y-%m-%d"),
        "校验备注": f"Murata PIM product search API page {page_no}",
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
        "共模阻抗": "",
        "阻抗单位": "",
        "额定电流": current_display,
        "DCR": dcr_display,
        "回路数": "",
        "电感值": inductance_value,
        "电感单位": inductance_unit,
        "电感误差": inductance_tol,
        "饱和电流": "",
        "屏蔽类型": shield,
        "阻抗@100MHz": "",
        "系列说明": build_series_description(series, construction),
    }


def fetch_page(session: requests.Session, page: int, page_size: int) -> dict:
    payload = {
        "productCategoryId": "inductor",
        "languageRegion": LANGUAGE_REGION,
        "pageSize": page_size,
        "page": page,
        "partNum": "",
        "searchCondClass": 2,
        "series": "",
        "sortKey": "",
        "valSearchCondList": TARGET_FILTERS,
        "rangeValSearchCondList": [],
        "dateRangeSearchCondList": [],
    }
    response = session.post(API_URL, json=payload, timeout=DEFAULT_TIMEOUT)
    response.raise_for_status()
    return response.json()


def fetch_all_rows(page_size: int = PAGE_SIZE) -> pd.DataFrame:
    session = requests.Session()
    session.headers.update(HEADERS)

    first = fetch_page(session, 1, page_size)
    total = int(first.get("totalNum", 0) or 0)
    pages = max(1, math.ceil(total / page_size))
    print(f"[murata] total={total} page_size={page_size} pages={pages}", flush=True)

    rows: list[dict[str, str]] = []
    for page in range(1, pages + 1):
        if page == 1:
            page_data = first
        else:
            page_data = fetch_page(session, page, page_size)
        items = page_data.get("productSearchResult", []) or []
        print(f"[murata] page {page}/{pages} items={len(items)}", flush=True)
        for item in items:
            row = build_row(item, page)
            if row:
                rows.append(row)
        time.sleep(0.15)

    if not rows:
        return pd.DataFrame()

    df = pd.DataFrame(rows)
    df = df.fillna("")
    df = df.drop_duplicates(subset=["品牌", "型号", "器件类型"], keep="first").reset_index(drop=True)
    return df


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

    merged = pd.concat([existing, new_rows], ignore_index=True)
    merged = merged.fillna("")
    merged = merged.drop_duplicates(subset=["品牌", "型号", "器件类型"], keep="first").reset_index(drop=True)

    existing_rows = len(existing)
    merged.to_csv(OFFICIAL_CSV, index=False, encoding="utf-8-sig")
    return existing_rows, len(merged)


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


def apply_to_database(source_rows: pd.DataFrame) -> tuple[int, int]:
    if source_rows is None or source_rows.empty:
        return 0, 0

    import component_matcher_build as cmb
    import sync_inductor_official_to_db as sidb

    module = cmb._load_component_matcher()
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    conn.execute("PRAGMA temp_store=MEMORY")
    try:
        db_columns = [row[1] for row in conn.execute("PRAGMA table_info(components)").fetchall()]
        conn.execute(
            """
            DELETE FROM components
            WHERE "品牌" = ?
              AND "器件类型" IN ("功率电感", "共模电感", "磁珠")
            """,
            ("村田Murata",),
        )
        conn.commit()

        db_rows = build_db_rows(source_rows, db_columns)
        db_rows.to_sql(
            "_tmp_murata_power_inductors",
            conn,
            if_exists="replace",
            index=False,
            method="multi",
            chunksize=250,
        )

        insert_cols_sql = ", ".join(f'"{col}"' for col in db_columns)
        select_cols_sql = ", ".join(f't."{col}"' for col in db_columns)
        conn.execute(
            f"""
            INSERT INTO components ({insert_cols_sql})
            SELECT {select_cols_sql}
            FROM "_tmp_murata_power_inductors" t
            """
        )
        inserted = int(conn.execute("SELECT changes()").fetchone()[0] or 0)
        deleted = 0
        conn.execute('DROP TABLE IF EXISTS "_tmp_murata_power_inductors"')
        conn.commit()
    finally:
        conn.close()

    sidb.refresh_search_sidecar_subset(module, db_rows)
    sidb.refresh_prepared_cache_subset(module, db_rows)
    return deleted, inserted


def main() -> int:
    parser = argparse.ArgumentParser(description="Fetch Murata power inductor products and merge them into the official inductor source CSV.")
    parser.add_argument("--page-size", type=int, default=PAGE_SIZE)
    parser.add_argument("--skip-merge", action="store_true", help="Only export the Murata snapshot CSV.")
    parser.add_argument("--apply-db", action="store_true", help="Also write the Murata rows into components.db and refresh the caches for this subset.")
    args = parser.parse_args()

    MURATA_CSV.parent.mkdir(parents=True, exist_ok=True)
    rows = fetch_all_rows(page_size=args.page_size)
    if rows.empty:
        raise SystemExit("No Murata power inductor rows were fetched.")

    rows.to_csv(MURATA_CSV, index=False, encoding="utf-8-sig")
    print(f"[murata] wrote snapshot: {MURATA_CSV} ({len(rows)} rows)", flush=True)

    if not args.skip_merge:
        before, after = merge_into_official_csv(rows)
        print(f"[murata] merged into official CSV: {before} -> {after} rows", flush=True)

    if args.apply_db:
        deleted, inserted = apply_to_database(rows)
        print(f"[murata] applied to DB: deleted={deleted} inserted={inserted}", flush=True)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
