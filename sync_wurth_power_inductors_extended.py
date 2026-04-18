from __future__ import annotations

import argparse
import html
import re
import sqlite3
import unicodedata
from datetime import datetime
from io import StringIO
from pathlib import Path
from urllib.request import Request, urlopen

import pandas as pd

import component_matcher_build as cmb
import sync_inductor_official_to_db as sidb


ROOT = Path(__file__).resolve().parent
OFFICIAL_CSV = ROOT / "Inductor" / "official_inductor_expansion.csv"
SNAPSHOT_CSV = ROOT / "Inductor" / "wurth_power_inductor_extended_expansion.csv"
COMPONENTS_DB = ROOT / "components.db"
BRAND = "Wurth Elektronik"
STAMP = datetime.now().strftime("%Y-%m-%d %H:%M")

PAGE_CONFIGS = [
    {
        "code": "WE-LHMI",
        "url": "https://www.we-online.com/en/components/products/WE-LHMI",
        "size_pattern": r"WE-LHMI[_-](\d{4})",
        "component_type": "功率电感",
        "special_use": "Wurth WE-LHMI high-current molded power inductor",
        "series_desc": "Wurth WE-LHMI molded power inductor series",
        "mount": "SMT",
        "material": "Ferrite",
        "fields": {
            "inductance": "luh",
            "current": "irp40ka",
            "saturation": "isat10a",
            "dcr": "rdcmaxmohm",
            "fres": "fresmhz",
        },
    },
    {
        "code": "WE-XHMI",
        "url": "https://www.we-online.com/en/components/products/WE-XHMI",
        "size_pattern": r"WE-XHMI[_-](\d{4})",
        "component_type": "功率电感",
        "special_use": "Wurth WE-XHMI high-current molded power inductor",
        "series_desc": "Wurth WE-XHMI high-current power inductor series",
        "mount": "SMT",
        "material": "Ferrite",
        "fields": {
            "inductance": "luh",
            "current": "irp40ka",
            "saturation": "isat30a",
            "dcr": "rdcmaxmohm",
            "fres": "fresmhz",
        },
    },
    {
        "code": "WE-PMI",
        "url": "https://www.we-online.com/en/components/products/WE-PMI",
        "size_pattern": r"WE-PMI[_-](\d{4}[A-Z]{0,2})",
        "component_type": "功率电感",
        "special_use": "Wurth WE-PMI low-profile power inductor",
        "series_desc": "Wurth WE-PMI low-profile power inductor series",
        "mount": "SMT",
        "material": "Ferrite",
        "fields": {
            "inductance": "luh",
            "current": "irma",
            "saturation": "isatma",
            "dcr": "rdcmohm",
            "fres": "fresmhz",
        },
    },
    {
        "code": "WE-PMFI",
        "url": "https://www.we-online.com/en/components/products/WE-PMFI",
        "size_pattern": r"WE-PMFI[_-](\d{4,6})",
        "component_type": "功率电感",
        "special_use": "Wurth WE-PMFI molded flat-wire power inductor",
        "series_desc": "Wurth WE-PMFI molded flat-wire power inductor series",
        "mount": "SMT",
        "material": "Metal Alloy",
        "fields": {
            "inductance": "luh",
            "current": "irp40ka",
            "saturation": "isat30a",
            "dcr": "rdctypmohm",
            "fres": "fresmhz",
            "voltage": "vopv",
        },
    },
    {
        "code": "WE-HCF",
        "url": "https://www.we-online.com/en/components/products/WE-HCF",
        "size_pattern": r"WE-HCF[_-](\d{4}[A-Z]?)",
        "component_type": "功率电感",
        "special_use": "Wurth WE-HCF high-current flat-wire power inductor",
        "series_desc": "Wurth WE-HCF high-current flat-wire power inductor series",
        "mount": "SMT",
        "material": "MnZn",
        "fields": {
            "inductance": "luh",
            "current": "irp40ka",
            "saturation": "isat10a",
            "dcr": "rdcmaxmohm",
            "fres": "fresmhz",
            "wire": "wiretype",
        },
    },
    {
        "code": "WE-HCFAT",
        "url": "https://www.we-online.com/en/components/products/WE-HCFAT",
        "size_pattern": r"(?:WE-HCFAT|IndHCFAT)[_-](\d{4})",
        "component_type": "功率电感",
        "special_use": "Wurth WE-HCFAT automotive flat-wire power inductor",
        "series_desc": "Wurth WE-HCFAT automotive flat-wire power inductor series",
        "mount": "THT",
        "material": "MnZn",
        "fields": {
            "inductance": "luh",
            "current": "ira",
            "saturation": "isata",
            "dcr": "rdctypmohm",
        },
    },
    {
        "code": "WE-LHMD",
        "url": "https://www.we-online.com/en/components/products/WE-LHMD",
        "size_pattern": r"WE-LHMD[_-](\d{4})",
        "component_type": "功率电感",
        "special_use": "Wurth WE-LHMD automotive power inductor",
        "series_desc": "Wurth WE-LHMD automotive power inductor series",
        "mount": "SMT",
        "material": "Ferrite",
        "fields": {
            "inductance": "luh",
            "current": "ira",
            "saturation": "isata",
            "dcr": "rdcmohm",
            "tol": "toll",
        },
    },
]


def clean_text(text) -> str:
    if text is None:
        return ""
    text = html.unescape(str(text))
    text = text.replace("\xa0", " ")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def normalize_key(text: str) -> str:
    text = unicodedata.normalize("NFKC", clean_text(text))
    text = text.replace("µ", "u").replace("μ", "u")
    text = text.replace("Ω", "ohm").replace("Ω", "ohm")
    return re.sub(r"[^a-z0-9]+", "", text.lower())


def size_key_candidates(text: str) -> list[str]:
    raw = clean_text(text).upper()
    if not raw:
        return []
    normalized = normalize_key(raw)
    candidates = [normalized]

    digits = re.sub(r"[^0-9A-Z]+", "", raw)
    if digits and normalize_key(digits) not in candidates:
        candidates.append(normalize_key(digits))

    m = re.search(r"(\d{3,6})([A-Z]{0,3})", raw)
    if m:
        num, suffix = m.groups()
        if num.startswith("0") and len(num) == 4:
            num = num[1:]
        if suffix:
            candidates.append(normalize_key(num + suffix))
        candidates.append(normalize_key(num))

    ext = re.search(r"EXT\.?(\d{4})", raw)
    if ext:
        candidates.append(normalize_key(ext.group(1)))

    seen = set()
    deduped = []
    for item in candidates:
        if item and item not in seen:
            seen.add(item)
            deduped.append(item)
    return deduped


def get_column(columns: list[str], key: str) -> str:
    target = normalize_key(key)
    for column in columns:
        if normalize_key(column) == target:
            return column
    for column in columns:
        if target in normalize_key(column):
            return column
    return ""


def get_cell(row: pd.Series, colmap: dict[str, str], key: str) -> str:
    column = colmap.get(normalize_key(key), "")
    if not column:
        column = get_column(list(colmap.values()), key)
    if not column:
        return ""
    return clean_text(row[column])


def first_number(text: str) -> str:
    match = re.search(r"[-+]?(?:\d+\.\d+|\d+)", clean_text(text).replace(",", "."))
    return match.group(0) if match else ""


def value_with_unit(text: str, unit: str) -> str:
    num = first_number(text)
    return f"{num} {unit}".strip() if num else ""


def parse_status(row_text: str) -> str:
    match = re.search(r"\b(PCN pending|New|Active)\b", clean_text(row_text))
    return match.group(1) if match else ""


def parse_size_code(pattern: str, row_text: str) -> str:
    match = re.search(pattern, row_text, flags=re.I)
    return clean_text(match.group(1)) if match else ""


def fetch_html(url: str) -> str:
    request = Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "Accept-Language": "en-US,en;q=0.9",
        },
    )
    with urlopen(request, timeout=120) as response:
        return response.read().decode("utf-8", "replace")


def build_size_map(table0: pd.DataFrame) -> dict[str, dict[str, str]]:
    size_map: dict[str, dict[str, str]] = {}
    if table0 is None or table0.empty:
        return size_map

    columns = list(table0.columns)
    mount_col = get_column(columns, "mount")
    material_col = get_column(columns, "material")

    for _, row in table0.iterrows():
        size = clean_text(row.iloc[0]) if len(row) > 0 else ""
        if not size:
            continue
        length = clean_text(row.iloc[2]) if len(row) > 2 else ""
        width = clean_text(row.iloc[3]) if len(row) > 3 else ""
        height = clean_text(row.iloc[4]) if len(row) > 4 else ""
        dims = [part for part in [length, width, height] if part and part != "nan"]
        payload = {
            "size": size,
            "size_mm": " x ".join(dims) + (" mm" if dims else ""),
            "length": length,
            "width": width,
            "height": height,
            "mount": clean_text(row[mount_col]) if mount_col else "",
            "material": clean_text(row[material_col]) if material_col else "",
        }
        for candidate in size_key_candidates(size):
            size_map[candidate] = payload
    return size_map


def lookup_size(size_map: dict[str, dict[str, str]], size_code: str) -> dict[str, str]:
    for candidate in size_key_candidates(size_code):
        if candidate in size_map:
            return size_map[candidate]
    return {}


def parse_page(config: dict[str, str]) -> pd.DataFrame:
    html_text = fetch_html(config["url"])
    tables = pd.read_html(StringIO(html_text))
    if len(tables) < 2:
        return pd.DataFrame()

    size_map = build_size_map(tables[0])
    table = tables[1].fillna("")
    columns = list(table.columns)
    colmap = {normalize_key(column): column for column in columns}
    order_col = colmap.get("ordercode", "")
    if not order_col:
        order_col = get_column(columns, "Order Code")
    if not order_col:
        return pd.DataFrame()

    rows: list[dict[str, str]] = []
    for _, row in table.iterrows():
        order_code = clean_text(row[order_col])
        if not order_code:
            continue

        row_text = " | ".join(clean_text(value) for value in row.tolist() if clean_text(value))
        size_code = parse_size_code(config["size_pattern"], row_text)
        size_info = lookup_size(size_map, size_code)
        if not size_info and len(size_map) == 1:
            size_info = next(iter(size_map.values()))
            size_code = size_info.get("size", size_code)

        fields = config["fields"]
        inductance_text = get_cell(row, colmap, fields["inductance"]) or get_cell(row, colmap, "luh")
        current_text = get_cell(row, colmap, fields.get("current", ""))
        saturation_text = get_cell(row, colmap, fields.get("saturation", ""))
        dcr_text = get_cell(row, colmap, fields.get("dcr", ""))
        fres_text = get_cell(row, colmap, fields.get("fres", ""))
        voltage_text = get_cell(row, colmap, fields.get("voltage", ""))
        tol_text = get_cell(row, colmap, fields.get("tol", ""))

        value_text, value_unit = "", ""
        if inductance_text:
            value_text = first_number(inductance_text)
            value_unit = "UH"

        current_text = value_with_unit(current_text, "A") or value_with_unit(current_text, "mA")
        saturation_text = value_with_unit(saturation_text, "A") or value_with_unit(saturation_text, "mA")
        dcr_text = value_with_unit(dcr_text, "mΩ")
        fres_text = value_with_unit(fres_text, "MHz")
        voltage_text = value_with_unit(voltage_text, "V")

        status = parse_status(row_text)
        mount = clean_text(size_info.get("mount") or config.get("mount", ""))
        material = clean_text(size_info.get("material") or config.get("material", ""))
        size_label = clean_text(size_code or size_info.get("size", ""))
        size_mm = clean_text(size_info.get("size_mm", ""))
        length = clean_text(size_info.get("length", ""))
        width = clean_text(size_info.get("width", ""))
        height = clean_text(size_info.get("height", ""))

        summary_parts = [
            part
            for part in [
                clean_text(get_cell(row, colmap, "datasheet")),
                f"L={value_text}{value_unit}" if value_text else "",
                current_text,
                saturation_text,
                dcr_text,
                fres_text,
                voltage_text,
                tol_text,
                size_label,
            ]
            if part
        ]

        rows.append(
            {
                "品牌": BRAND,
                "型号": order_code,
                "系列": config["code"],
                "尺寸（inch）": size_label,
                "材质（介质）": material,
                "容值": "",
                "容值单位": "",
                "容值误差": "",
                "耐压（V）": voltage_text,
                "特殊用途": config["special_use"],
                "备注1": clean_text(get_cell(row, colmap, "datasheet")),
                "备注2": config["url"],
                "备注3": " | ".join(
                    [part for part in [current_text, saturation_text, dcr_text, fres_text, tol_text] if part]
                ),
                "器件类型": config["component_type"],
                "安装方式": mount,
                "封装代码": size_label,
                "尺寸（mm）": size_mm,
                "规格摘要": " | ".join(summary_parts),
                "生产状态": status,
                "长度（mm）": length,
                "宽度（mm）": width,
                "高度（mm）": height,
                "官网链接": config["url"],
                "数据来源": f"Wurth official {config['code']} product page",
                "数据状态": "official",
                "校验时间": STAMP,
                "校验备注": f"Parsed from official {config['code']} product page",
                "直径（mm）": "",
                "脚距（mm）": "",
                "极性": "",
                "ESR": "",
                "纹波电流": "",
                "寿命（h）": "",
                "工作温度": "",
                "阻值@25C": "",
                "阻值单位": "",
                "阻值误差": "",
                "B值": "",
                "B值条件": "",
                "共模阻抗": "",
                "阻抗单位": "",
                "额定电流": current_text,
                "DCR": dcr_text,
                "回路数": "",
                "电感值": value_text,
                "电感单位": value_unit,
                "电感误差": tol_text,
                "饱和电流": saturation_text,
                "屏蔽类型": "",
                "阻抗@100MHz": "",
                "系列说明": config["series_desc"],
                "_model_rule_authority": f"Wurth official {config['code']} product page",
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
        )

    df = pd.DataFrame(rows).fillna("")
    if df.empty:
        return df
    return df.drop_duplicates(subset=["器件类型", "品牌", "型号"], keep="first").reset_index(drop=True)


def merge_into_official_csv(new_rows: pd.DataFrame) -> tuple[int, int]:
    if new_rows is None or new_rows.empty:
        return 0, 0

    if OFFICIAL_CSV.exists():
        existing = pd.read_csv(OFFICIAL_CSV, encoding="utf-8-sig").fillna("")
    else:
        existing = pd.DataFrame(columns=list(new_rows.columns))

    columns = list(existing.columns)
    for column in new_rows.columns:
        if column not in columns:
            columns.append(column)

    existing = existing.reindex(columns=columns, fill_value="")
    new_rows = new_rows.reindex(columns=columns, fill_value="")

    incoming_keys = {
        (clean_text(row.get("器件类型", "")), clean_text(row.get("品牌", "")), clean_text(row.get("型号", "")))
        for _, row in new_rows.iterrows()
    }
    if incoming_keys:
        existing = existing[
            ~existing.apply(
                lambda row: (
                    clean_text(row.get("器件类型", "")),
                    clean_text(row.get("品牌", "")),
                    clean_text(row.get("型号", "")),
                )
                in incoming_keys,
                axis=1,
            )
        ]

    merged = pd.concat([existing, new_rows], ignore_index=True).fillna("")
    merged = merged.drop_duplicates(subset=["器件类型", "品牌", "型号"], keep="first").reset_index(drop=True)
    merged.to_csv(OFFICIAL_CSV, index=False, encoding="utf-8-sig")
    return len(existing), len(merged)


def update_database_and_caches(module, new_rows: pd.DataFrame) -> tuple[int, int, bool, bool]:
    if new_rows is None or new_rows.empty:
        return 0, 0, False, False
    if not COMPONENTS_DB.exists():
        raise SystemExit(f"missing components db: {COMPONENTS_DB}")

    conn = sqlite3.connect(str(COMPONENTS_DB), timeout=60)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    conn.execute("PRAGMA temp_store=MEMORY")
    db_columns = [row[1] for row in conn.execute("PRAGMA table_info(components)").fetchall()]

    updated_rows = new_rows.fillna("").reindex(columns=db_columns, fill_value="")
    deleted, inserted = sidb.replace_rows(conn, updated_rows, db_columns)
    db_subset = sidb.load_official_rows_from_db(conn, updated_rows)
    conn.close()

    search_refreshed = sidb.refresh_search_sidecar_subset(module, db_subset)
    prepared_refreshed = sidb.refresh_prepared_cache_subset(module, db_subset)
    return deleted, inserted, search_refreshed, prepared_refreshed


def main() -> int:
    parser = argparse.ArgumentParser(description="Extend Wurth power inductor coverage from official product pages.")
    parser.add_argument("--skip-db", action="store_true", help="Only update the official CSV snapshot, skip DB/cache refresh.")
    args = parser.parse_args()

    all_rows = []
    for config in PAGE_CONFIGS:
        print(f"[wurth] scraping {config['code']} ...", flush=True)
        rows = parse_page(config)
        print(f"[wurth] {config['code']}: {len(rows)} rows", flush=True)
        if not rows.empty:
            all_rows.append(rows)

    if not all_rows:
        raise SystemExit("No Wurth rows were parsed.")

    df = pd.concat(all_rows, ignore_index=True).fillna("")
    df = df.drop_duplicates(subset=["器件类型", "品牌", "型号"], keep="first").reset_index(drop=True)
    df = df.sort_values(by=["器件类型", "系列", "型号"], kind="stable").reset_index(drop=True)
    df.to_csv(SNAPSHOT_CSV, index=False, encoding="utf-8-sig")
    before, after = merge_into_official_csv(df)
    print(f"[wurth] wrote snapshot: {SNAPSHOT_CSV}")
    print(f"[wurth] merged official csv: {before} -> {after}")

    if args.skip_db:
        print("[wurth] skipped DB/cache refresh by request")
        return 0

    module = cmb._load_component_matcher()
    deleted, inserted, search_refreshed, prepared_refreshed = update_database_and_caches(module, df)
    print(
        f"[wurth] db deleted={deleted} inserted={inserted} "
        f"search_refreshed={search_refreshed} prepared_refreshed={prepared_refreshed}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
