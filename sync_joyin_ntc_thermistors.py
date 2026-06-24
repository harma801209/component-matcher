from __future__ import annotations

import argparse
import datetime as dt
import re
import shutil
import sqlite3
from pathlib import Path

import pandas as pd
from pypdf import PdfReader

import component_matcher as cm
from incremental_semiconductor_cache_update import refresh_search_sidecar_rows
from sync_selected_cache_rows import stream_replace_prepared_rows


ROOT = Path(__file__).resolve().parent
DB_PATH = ROOT / "components.db"
DEFAULT_SOURCE_DIR = Path.home() / "Desktop" / "被动产品线资料" / "信昌PDC" / "Resistor电阻" / "NTC"
BRAND = "JOYIN(久尹)"
COMPONENT_TYPE = "热敏电阻"
DATA_SOURCE_PREFIX = "JOYIN JSN NTC official datasheet"

SERIES_FILES = {
    "JSN-A": "JSN-A_250121.pdf",
    "JSN-C": "JSN-C_250121.pdf",
    "JSN-G": "JSN-G_250121.pdf",
    "JSN-H": "JSN-H_250121.pdf",
}

SERIES_PROFILES = {
    "JSN-A": {
        "description": "JOYIN JSN-A Automotive SMD NTC thermistor series",
        "special_use": "车规 | AEC-Q200 | 175℃ | 测温 | 贴片 | NTC",
        "temperature": "-40~175℃",
    },
    "JSN-C": {
        "description": "JOYIN JSN-C Automotive SMD NTC thermistor series",
        "special_use": "车规 | AEC-Q200 | 150℃ | 测温 | 贴片 | NTC",
        "temperature": "-40~150℃",
    },
    "JSN-G": {
        "description": "JOYIN JSN-G SMD NTC thermistor series",
        "special_use": "标准 | UL/TUV | 125℃ | 测温 | 贴片 | NTC",
        "temperature": "-40~125℃",
    },
    "JSN-H": {
        "description": "JOYIN JSN-H SMD NTC thermistor series",
        "special_use": "标准 | 150℃ | 测温 | 贴片 | NTC",
        "temperature": "-40~150℃",
    },
}

SIZE_PROFILES = {
    "Z": {"inch": "0201", "body": "0603", "length": "0.60", "width": "0.30", "height": "0.30"},
    "A": {"inch": "0402", "body": "1005", "length": "1.00", "width": "0.50", "height": "0.50"},
    "B": {"inch": "0603", "body": "1608", "length": "1.60", "width": "0.80", "height": "0.80"},
    "C": {"inch": "0805", "body": "2012", "length": "2.00", "width": "1.25", "height": "0.85"},
}

RESISTANCE_TOLERANCE_CODES = {
    "0.5": "D",
    "0.7": "E",
    "1": "F",
    "2": "G",
    "3": "H",
    "5": "J",
    "10": "K",
}
B_TOLERANCE_CODES = {
    "0.5": "D",
    "0.7": "E",
    "1": "F",
    "2": "G",
    "3": "H",
    "5": "J",
}
B_CONDITION_MAP = {
    "A": "25/50℃",
    "B": "25/85℃",
    "C": "25/100℃",
}

BASE_ROW_RE = re.compile(
    r"(?P<template>JSN(?P<size>[ZABC])(?P<res_code>\d{3})X(?P<b_code>\d{3})Y(?P<b_condition>[ABC])B?X(?P<suffix>[ACGH]))"
    r"\s+(?P<r25>[\d,]+)\s+(?P<r_tols>[\d,.]+)\s+(?P<b_value>\d+)\s+(?P<b_tols>[\d,.]+)"
    r"\s+Approx\.\s+(?P<dissipation>[\d.]+)\s+Approx\.\s+(?P<time_constant>[\d.]+)\s+(?P<max_power>\d+)"
)


def clean_text(value: object) -> str:
    text = str(value or "").strip()
    return "" if text.lower() in {"nan", "none"} else text


def normalize_percent_token(value: str) -> str:
    text = clean_text(value).replace("%", "")
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    return text


def ohm_text_from_pdf(value: str) -> str:
    return clean_text(value).replace(",", "")


def format_resistance_display(ohm_text: str) -> tuple[str, str, str]:
    try:
        ohm = float(ohm_text)
    except ValueError:
        return ohm_text, "Ω", f"{ohm_text}Ω"
    if ohm >= 1000:
        kohm = f"{ohm / 1000.0:.6f}".rstrip("0").rstrip(".")
        return kohm, "KΩ", f"{kohm}KΩ"
    value = f"{ohm:.6f}".rstrip("0").rstrip(".")
    return value, "Ω", f"{value}Ω"


def expand_tolerance_codes(tokens: str, mapping: dict[str, str]) -> list[tuple[str, str]]:
    pairs: list[tuple[str, str]] = []
    for token in clean_text(tokens).split(","):
        normalized = normalize_percent_token(token)
        code = mapping.get(normalized)
        if code:
            pairs.append((code, f"±{normalized}%"))
    return pairs


def make_model(template: str, r_tol_code: str, b_tol_code: str) -> str:
    match = re.fullmatch(
        r"(?P<prefix>JSN[ZABC]\d{3})X(?P<b_code>\d{3})Y(?P<tail>[ABC]B?X[ACGH])",
        template,
    )
    if not match:
        raise ValueError(f"unsupported JSN template: {template}")
    return f"{match.group('prefix')}{r_tol_code}{match.group('b_code')}{b_tol_code}{match.group('tail')}"


def extract_base_rows(pdf_path: Path, series: str) -> list[dict[str, str]]:
    reader = PdfReader(str(pdf_path))
    rows: list[dict[str, str]] = []
    for page_no, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""
        normalized_text = re.sub(r"\s+", " ", text)
        for match in BASE_ROW_RE.finditer(normalized_text):
            row = match.groupdict()
            row["series"] = series
            row["page_no"] = str(page_no)
            rows.append(row)
    return rows


def build_rows(source_dir: Path) -> pd.DataFrame:
    rows: list[dict[str, str]] = []
    checked_at = dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    for series, filename in SERIES_FILES.items():
        pdf_path = source_dir / filename
        if not pdf_path.exists():
            raise FileNotFoundError(pdf_path)
        profile = SERIES_PROFILES[series]
        for base in extract_base_rows(pdf_path, series):
            size = SIZE_PROFILES.get(base["size"], {})
            r25_ohm = ohm_text_from_pdf(base["r25"])
            display_value, display_unit, r_display = format_resistance_display(r25_ohm)
            b_condition = B_CONDITION_MAP.get(base["b_condition"], "")
            r_tolerances = expand_tolerance_codes(base["r_tols"], RESISTANCE_TOLERANCE_CODES)
            b_tolerances = expand_tolerance_codes(base["b_tols"], B_TOLERANCE_CODES)
            if not r_tolerances or not b_tolerances:
                raise ValueError(f"missing tolerance mapping for {base['template']}")

            for r_tol_code, r_tol_text in r_tolerances:
                for b_tol_code, b_tol_text in b_tolerances:
                    model = make_model(base["template"], r_tol_code, b_tol_code)
                    summary = (
                        f"{r_display} {r_tol_text} B{b_condition}={base['b_value']}K {b_tol_text} "
                        f"{size.get('inch', '')} {profile['temperature']}"
                    ).strip()
                    rows.append(
                        {
                            "品牌": BRAND,
                            "型号": model,
                            "系列": series,
                            "尺寸（inch）": size.get("inch", ""),
                            "材质（介质）": "NTC",
                            "容值": display_value,
                            "容值单位": display_unit,
                            "容值误差": r_tol_text,
                            "特殊用途": profile["special_use"],
                            "备注1": f"δ={base['dissipation']}mW/℃",
                            "备注2": f"τ={base['time_constant']}s",
                            "备注3": f"Max Power={base['max_power']}mW",
                            "器件类型": COMPONENT_TYPE,
                            "安装方式": "贴片",
                            "封装代码": size.get("inch", ""),
                            "尺寸（mm）": f"{size.get('length', '')}×{size.get('width', '')}×{size.get('height', '')}",
                            "规格摘要": summary,
                            "生产状态": "量产",
                            "长度（mm）": size.get("length", ""),
                            "宽度（mm）": size.get("width", ""),
                            "高度（mm）": size.get("height", ""),
                            "数据来源": f"{DATA_SOURCE_PREFIX}: {filename}",
                            "数据状态": "官方PDF规格书",
                            "校验时间": checked_at,
                            "校验备注": f"{filename} page {base['page_no']}; template={base['template']}",
                            "工作温度": profile["temperature"],
                            "阻值@25C": r25_ohm,
                            "阻值单位": "Ω",
                            "阻值误差": r_tol_text,
                            "B值": base["b_value"],
                            "B值条件": b_condition,
                            "系列说明": profile["description"],
                            "_model_rule_authority": "joyin_jsn_ntc_pdf",
                        }
                    )

    frame = pd.DataFrame(rows)
    frame = frame.drop_duplicates(subset=["品牌", "型号"], keep="first").reset_index(drop=True)
    return frame


def db_columns(conn: sqlite3.Connection) -> list[str]:
    return [row[1] for row in conn.execute('PRAGMA table_info("components")').fetchall()]


def backup_database() -> Path:
    timestamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = DB_PATH.with_name(f"{DB_PATH.name}.joyin_ntc_{timestamp}.bak")
    shutil.copy2(DB_PATH, backup_path)
    return backup_path


def replace_joyin_ntc_rows(frame: pd.DataFrame) -> tuple[int, int]:
    if frame.empty:
        raise RuntimeError("no Joyin NTC rows were generated")
    with sqlite3.connect(DB_PATH, timeout=60) as conn:
        conn.execute("PRAGMA busy_timeout = 60000")
        cols = db_columns(conn)
        params = (COMPONENT_TYPE, f"{DATA_SOURCE_PREFIX}%")
        existing = conn.execute(
            """
            SELECT COUNT(*)
            FROM components
            WHERE (品牌 LIKE '%JOYIN%' OR 品牌 LIKE '%久尹%')
              AND 器件类型 = ?
              AND 数据来源 LIKE ?
            """,
            params,
        ).fetchone()[0]
        conn.execute(
            """
            DELETE FROM components
            WHERE (品牌 LIKE '%JOYIN%' OR 品牌 LIKE '%久尹%')
              AND 器件类型 = ?
              AND 数据来源 LIKE ?
            """,
            params,
        )
        insert_frame = frame.reindex(columns=cols, fill_value="")
        # SQLite often caps one statement at 999 parameters; the components table
        # has many columns, so keep each multi-row insert deliberately small.
        insert_frame.to_sql("components", conn, if_exists="append", index=False, method="multi", chunksize=10)
    return int(existing), int(len(frame))


def refresh_runtime_indexes(frame: pd.DataFrame) -> tuple[int, int, dict[str, int]]:
    with sqlite3.connect(DB_PATH, timeout=60) as conn:
        cols = db_columns(conn)
    seed_frame = frame.reindex(columns=cols, fill_value="")
    seed_prepared = cm.prepare_search_dataframe(seed_frame)
    if seed_prepared.empty:
        raise RuntimeError("Joyin NTC rows produced an empty prepared frame")
    removed_rows, inserted_rows = stream_replace_prepared_rows(seed_prepared)
    sidecar_counts = refresh_search_sidecar_rows(seed_prepared)
    return removed_rows, inserted_rows, sidecar_counts


def main() -> None:
    parser = argparse.ArgumentParser(description="Import JOYIN JSN SMD NTC thermistors from official PDFs.")
    parser.add_argument("--source-dir", default=str(DEFAULT_SOURCE_DIR))
    parser.add_argument("--no-backup", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    source_dir = Path(args.source_dir)
    frame = build_rows(source_dir)
    print(f"generated_rows={len(frame)}")
    print("series_counts=" + repr(frame["系列"].value_counts().sort_index().to_dict()))
    print("sample_models=" + ", ".join(frame["型号"].head(8).tolist()))

    if args.dry_run:
        return

    if not args.no_backup:
        backup_path = backup_database()
        print(f"backup={backup_path}")

    removed, inserted = replace_joyin_ntc_rows(frame)
    removed_cache, inserted_cache, sidecar_counts = refresh_runtime_indexes(frame)
    print(f"db_removed={removed}")
    print(f"db_inserted={inserted}")
    print(f"prepared_rows_removed={removed_cache}")
    print(f"prepared_rows_inserted={inserted_cache}")
    print(f"search_core_rows={sidecar_counts.get(cm.COMPONENTS_SEARCH_CORE_TABLE, 0)}")


if __name__ == "__main__":
    main()
