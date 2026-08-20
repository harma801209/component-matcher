from __future__ import annotations

import argparse
import re
import shutil
import sqlite3
from datetime import datetime
from pathlib import Path

import fitz
import pandas as pd
import requests

import component_matcher as cm
from incremental_semiconductor_cache_update import (
    refresh_search_sidecar_rows,
    replace_prepared_cache_rows,
)


ROOT = Path(__file__).resolve().parent
DB_PATH = ROOT / "components.db"
SOURCE_DIR = ROOT / "cache" / "joyin_varistor_sources"
JMV_URL = "https://www.joyin.com.tw/storage/system/product/pdf/MLV_JMV_datasheet.pdf"
JVR_URL = "https://www.joyin.com.tw/storage/system/product/pdf/MOV_JVR_datasheet20250305.pdf"

JMV_SERIES = {
    "S": ("JMV-S", "JOYIN JMV-S 浪涌/ESD保护多层贴片压敏电阻", "多层 | 贴片 | ESD/浪涌保护"),
    "C": ("JMV-C", "JOYIN JMV-C 低电容ESD保护多层贴片压敏电阻", "多层 | 贴片 | 低电容 | 高速I/O | ESD保护"),
    "E": ("JMV-E", "JOYIN JMV-E EMI/ESD双功能多层贴片压敏电阻", "多层 | 贴片 | EMI/ESD双功能"),
    "N": ("JMV-N", "JOYIN JMV-N 网络保护多层贴片压敏电阻", "多层 | 贴片 | 网络保护 | 高工作电压"),
    "B": ("JMV-B", "JOYIN JMV-B 基站用高浪涌多层贴片压敏电阻", "多层 | 贴片 | 基站 | 高浪涌"),
}

JVR_SERIES = {
    "N": ("JVR-N", "JOYIN JVR-N 标准径向引线金属氧化物压敏电阻", "标准 | 径向引线 | 浪涌保护"),
    "S": ("JVR-S", "JOYIN JVR-S 高浪涌径向引线金属氧化物压敏电阻", "高浪涌 | 径向引线 | 浪涌保护"),
    "U": ("JVR-U", "JOYIN JVR-U 超高浪涌径向引线金属氧化物压敏电阻", "超高浪涌 | 径向引线 | 浪涌保护"),
}

JMV_DIMS = {
    "0201": ("0.60", "0.30", "0.30"),
    "0402": ("1.00", "0.50", "0.34"),
    "0603": ("1.60", "0.85", "0.51"),
    "0805": ("2.00", "1.25", "0.90"),
    "1206": ("3.20", "1.60", "1.70"),
    "1210": ("3.20", "2.50", "1.70"),
    "1812": ("4.50", "3.20", "2.50"),
    "2220": ("5.70", "5.20", "4.00"),
}

JVR_TOLERANCE = {
    "K": "±10%",
    "L": "±15%",
    "M": "±20%",
    "P": "±25%",
}


def clean_text(value: object) -> str:
    text = str(value or "").strip()
    return "" if text.lower() in {"nan", "none"} else text


def backup_database() -> Path:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = DB_PATH.with_name(f"{DB_PATH.name}.joyin_varistors_{timestamp}.bak")
    shutil.copy2(DB_PATH, backup_path)
    return backup_path


def download_sources(refresh: bool = False) -> tuple[Path, Path]:
    SOURCE_DIR.mkdir(parents=True, exist_ok=True)
    paths = (
        SOURCE_DIR / "MLV_JMV_datasheet.pdf",
        SOURCE_DIR / "MOV_JVR_datasheet20250305.pdf",
    )
    for url, path in ((JMV_URL, paths[0]), (JVR_URL, paths[1])):
        if path.exists() and not refresh:
            continue
        response = requests.get(url, timeout=60)
        response.raise_for_status()
        path.write_bytes(response.content)
    return paths


def pdf_text(path: Path) -> str:
    with fitz.open(path) as doc:
        return "\n".join(page.get_text("text") for page in doc)


def normalize_number_text(value: str) -> str:
    try:
        return f"{float(value):g}"
    except ValueError:
        return clean_text(value)


def decode_jmv_voltage(code: str) -> str:
    text = code.upper().replace("R", ".")
    if re.fullmatch(r"\d{3}", text) and text.endswith("0"):
        text = str(int(text[:2]))
    try:
        return f"{float(text):g}"
    except ValueError:
        return ""


def decode_jvr_voltage(code: str) -> str:
    if not re.fullmatch(r"\d{3}", code):
        return ""
    first_two = int(code[:2])
    multiplier = int(code[2])
    return str(first_two * (10 ** multiplier))


def decode_capacitance_code(code: str) -> str:
    text = code.upper()
    if "R" in text:
        return text.replace("R", ".")
    if not re.fullmatch(r"\d{3}", text):
        return text
    value = int(text[:2]) * (10 ** int(text[2]))
    return f"{value:g}"


def parse_jmv_models(jmv_pdf: Path) -> list[str]:
    text = pdf_text(jmv_pdf)
    models = set(re.findall(r"\bJMV\d{4}[SCENB][A-Z0-9R]+(?:-[A-Z0-9]+)?\b", text))
    return sorted(models)


def parse_jmv_working_voltage_map(jmv_pdf: Path, models: list[str]) -> dict[str, str]:
    text = pdf_text(jmv_pdf)
    voltage_map: dict[str, str] = {}
    numeric_pattern = re.compile(r"\d+(?:\.\d+)?")
    for model in models:
        index = text.find(model)
        if index < 0:
            continue
        family_match = re.match(r"^JMV\d{4}([SCENB])", model)
        if not family_match:
            continue
        family = family_match.group(1)
        snippet = text[index + len(model) : index + len(model) + 260].replace("*", "")
        values = numeric_pattern.findall(snippet)
        value_index = 1 if family in {"N", "B"} else 0
        if len(values) > value_index:
            voltage_map[model] = normalize_number_text(values[value_index])
    return voltage_map


def parse_jvr_models(jvr_pdf: Path) -> list[str]:
    text = pdf_text(jvr_pdf)
    models = {
        "".join(match)
        for match in re.findall(r"\b(JVR)\s*(\d{2}[NSU])\s*(\d{3}[KLMP])\b", text)
    }
    return sorted(models)


def jmv_row(
    model: str,
    brand: str = "JOYIN(久尹)",
    source_note: str = "Joyin official JMV datasheet",
    working_voltage: str | None = None,
) -> dict[str, str] | None:
    match = re.match(r"^JMV(?P<size>\d{4})(?P<family>[SCENB])(?P<voltage>[0-9R]+)(?P<packing>[TK])(?P<suffix>[A-Z0-9R-]+)$", model)
    if not match:
        return None
    size = match.group("size")
    family = match.group("family")
    voltage = clean_text(working_voltage) or decode_jmv_voltage(match.group("voltage"))
    series, desc, use = JMV_SERIES[family]
    length, width, height = JMV_DIMS.get(size, ("", "", ""))
    cap_match = re.match(r"(?P<cap>[0-9R]+)", match.group("suffix"))
    capacitance = decode_capacitance_code(cap_match.group("cap")) if cap_match else ""
    size_mm = "x".join(part for part in (length, width, height) if part)
    summary_parts = [
        "Joyin JMV 多层贴片压敏电阻",
        series,
        size,
        f"VDC={voltage}V" if voltage else "",
        f"CP≈{capacitance}pF" if capacitance else "",
    ]
    return {
        "品牌": brand,
        "型号": model,
        "系列": series,
        "系列说明": desc,
        "器件类型": "贴片压敏电阻",
        "安装方式": "贴片",
        "封装代码": size,
        "尺寸（inch）": size,
        "尺寸（mm）": size_mm,
        "长度（mm）": length,
        "宽度（mm）": width,
        "高度（mm）": height,
        "耐压（V）": voltage,
        "压敏电压": voltage,
        "特殊用途": use,
        "规格摘要": " ".join(part for part in summary_parts if part),
        "生产状态": "Active",
        "工作温度": "-40~85℃",
        "官网链接": JMV_URL,
        "数据来源": source_note,
        "数据状态": "官方PDF规格表/命名规则",
        "校验时间": datetime.now().strftime("%Y-%m-%d"),
        "校验备注": f"JMV datasheet: family={series}, size={size}, max DC working voltage={voltage}V, capacitance code={capacitance}pF",
    }


def jvr_row(model: str, brand: str = "JOYIN(久尹)", source_note: str = "Joyin official JVR datasheet") -> dict[str, str] | None:
    match = re.match(r"^JVR(?P<body>\d{2})(?P<family>[NSU])(?P<voltage>\d{3})(?P<tol>[KLMP])", model)
    if not match:
        return None
    body = match.group("body")
    family = match.group("family")
    voltage = decode_jvr_voltage(match.group("voltage"))
    tolerance = JVR_TOLERANCE.get(match.group("tol"), "")
    series, desc, use = JVR_SERIES[family]
    body_mm = str(int(body))
    summary_parts = [
        "Joyin JVR 径向引线金属氧化物压敏电阻",
        series,
        f"{body_mm}D",
        f"V1mA={voltage}V" if voltage else "",
        tolerance,
    ]
    return {
        "品牌": brand,
        "型号": model,
        "系列": series,
        "系列说明": desc,
        "器件类型": "引线型压敏电阻",
        "安装方式": "插件",
        "封装代码": f"{body_mm}D",
        "尺寸（mm）": f"{body_mm}D",
        "直径（mm）": body_mm,
        "耐压（V）": voltage,
        "压敏电压": voltage,
        "容值误差": tolerance,
        "特殊用途": use,
        "规格摘要": " ".join(part for part in summary_parts if part),
        "生产状态": "Active",
        "工作温度": "-40~85℃",
        "官网链接": JVR_URL,
        "数据来源": source_note,
        "数据状态": "官方PDF规格表/命名规则",
        "校验时间": datetime.now().strftime("%Y-%m-%d"),
        "校验备注": f"JVR datasheet: family={series}, disk={body_mm}mm, varistor voltage={voltage}V, tolerance={tolerance}",
    }


def existing_joyin_variant_rows(conn: sqlite3.Connection, jmv_voltage_map: dict[str, str]) -> list[dict[str, str]]:
    conn.row_factory = sqlite3.Row
    rows: list[dict[str, str]] = []
    for row in conn.execute(
        """
        SELECT [品牌] AS brand, [型号] AS model
        FROM components
        WHERE ([品牌] LIKE '%Joyin%' OR [品牌] LIKE '%JOYIN%' OR [品牌] LIKE '%久尹%')
          AND ([型号] LIKE 'JMV%' OR [型号] LIKE 'JVR%')
        """
    ):
        brand = clean_text(row["brand"]) or "JOYIN(久尹)"
        model = clean_text(row["model"]).upper()
        if model.startswith("JMV"):
            built = jmv_row(
                model,
                brand=brand,
                source_note="JLC row normalized by Joyin official JMV naming rule",
                working_voltage=jmv_voltage_map.get(model),
            )
        else:
            built = jvr_row(model, brand=brand, source_note="Existing row normalized by Joyin official JVR naming rule")
        if built:
            rows.append(built)
    return rows


def dedupe_rows(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    seen: set[tuple[str, str, str]] = set()
    deduped: list[dict[str, str]] = []
    for row in rows:
        key = (row["品牌"], row["型号"], row["器件类型"])
        if key in seen:
            continue
        seen.add(key)
        deduped.append(row)
    return deduped


def upsert_rows(conn: sqlite3.Connection, rows: list[dict[str, str]], dry_run: bool) -> tuple[int, int, list[int]]:
    columns = {row[1] for row in conn.execute("PRAGMA table_info(components)")}
    insert_count = 0
    update_count = 0
    changed_rowids: list[int] = []
    for row in rows:
        row = {key: clean_text(value) for key, value in row.items() if key in columns and clean_text(value) != ""}
        existing = conn.execute(
            """
            SELECT rowid, *
            FROM components
            WHERE [品牌] = ? AND [型号] = ? AND [器件类型] = ?
            LIMIT 1
            """,
            (row.get("品牌", ""), row.get("型号", ""), row.get("器件类型", "")),
        ).fetchone()
        if existing is None:
            cols = list(row)
            if not dry_run:
                placeholders = ",".join("?" for _ in cols)
                conn.execute(
                    f"INSERT INTO components ({','.join(f'[{col}]' for col in cols)}) VALUES ({placeholders})",
                    [row[col] for col in cols],
                )
                changed_rowids.append(int(conn.execute("SELECT last_insert_rowid()").fetchone()[0]))
            insert_count += 1
            continue
        rowid = int(existing[0])
        patch = {key: value for key, value in row.items() if clean_text(existing[key]) != value}
        if patch:
            if not dry_run:
                assignments = ",".join(f"[{col}] = ?" for col in patch)
                conn.execute(f"UPDATE components SET {assignments} WHERE rowid = ?", list(patch.values()) + [rowid])
                changed_rowids.append(rowid)
            update_count += 1
    return insert_count, update_count, changed_rowids


def load_changed_rows(conn: sqlite3.Connection, rowids: list[int]) -> pd.DataFrame:
    if not rowids:
        return pd.DataFrame()
    frames: list[pd.DataFrame] = []
    for offset in range(0, len(rowids), 800):
        chunk = rowids[offset : offset + 800]
        placeholders = ",".join("?" for _ in chunk)
        frames.append(pd.read_sql_query(f"SELECT * FROM components WHERE rowid IN ({placeholders})", conn, params=chunk))
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()


def build_rows(refresh_sources: bool = False) -> list[dict[str, str]]:
    jmv_pdf, jvr_pdf = download_sources(refresh=refresh_sources)
    rows: list[dict[str, str]] = []
    jmv_models = parse_jmv_models(jmv_pdf)
    jmv_voltage_map = parse_jmv_working_voltage_map(jmv_pdf, jmv_models)
    rows.extend(row for model in jmv_models if (row := jmv_row(model, working_voltage=jmv_voltage_map.get(model))))
    rows.extend(row for model in parse_jvr_models(jvr_pdf) if (row := jvr_row(model)))
    with sqlite3.connect(DB_PATH) as conn:
        rows.extend(existing_joyin_variant_rows(conn, jmv_voltage_map))
    return dedupe_rows(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description="Sync Joyin/J久尹 JMV/JVR official varistor rows into components.db.")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--refresh-sources", action="store_true")
    parser.add_argument("--skip-cache", action="store_true")
    parser.add_argument("--refresh-prepared", action="store_true")
    parser.add_argument("--no-backup", action="store_true")
    args = parser.parse_args()

    rows = build_rows(refresh_sources=args.refresh_sources)
    backup_path = None
    with sqlite3.connect(DB_PATH, timeout=60) as conn:
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA busy_timeout = 60000")
        if rows and not args.dry_run and not args.no_backup:
            backup_path = backup_database()
        insert_count, update_count, changed_rowids = upsert_rows(conn, rows, dry_run=args.dry_run)
        if not args.dry_run:
            conn.commit()
        changed_rows = load_changed_rows(conn, changed_rowids) if changed_rowids and not args.dry_run and not args.skip_cache else pd.DataFrame()

    prepared_rows = 0
    search_core_rows = 0
    if not args.dry_run and not args.skip_cache and not changed_rows.empty:
        prepared = cm.prepare_search_dataframe(changed_rows)
        if not prepared.empty:
            if args.refresh_prepared:
                try:
                    prepared_rows = replace_prepared_cache_rows(prepared)
                except Exception as exc:
                    print(f"prepared_cache_refresh_warning={type(exc).__name__}: {exc}")
            counts = refresh_search_sidecar_rows(prepared)
            search_core_rows = counts.get(cm.COMPONENTS_SEARCH_CORE_TABLE, 0)

    print(f"source_rows={len(rows)}")
    print(f"insert_rows={insert_count}")
    print(f"update_rows={update_count}")
    print(f"changed_rows={0 if args.dry_run else len(changed_rowids)}")
    print(f"prepared_rows={prepared_rows}")
    print(f"search_core_rows={search_core_rows}")
    if backup_path:
        print(f"backup_path={backup_path}")


if __name__ == "__main__":
    main()
