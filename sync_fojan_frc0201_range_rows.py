from __future__ import annotations

import argparse
import datetime as dt
import sqlite3
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

import pandas as pd

import component_matcher as cm
from incremental_semiconductor_cache_update import refresh_search_sidecar_rows
from sync_selected_cache_rows import stream_replace_prepared_rows


ROOT = Path(__file__).resolve().parent
DB_PATH = ROOT / "components.db"

BRAND = "FOJAN(富捷)"
SERIES = "FRC"
SIZE_INCH = "0201"
SIZE_MM = "0.60×0.30"
POWER_TEXT = "50mW"
POWER_WATT = "0.05"
TEMPERATURE = "-55~155℃"
PACKAGE = "15000PCS"
DATA_SOURCE = "FOJAN FRC 0201 price-range seed"
MODEL_AUTHORITY = "fojan_frc0201_price_range_seed"

E24_BASES = [10, 11, 12, 13, 15, 16, 18, 20, 22, 24, 27, 30, 33, 36, 39, 43, 47, 51, 56, 62, 68, 75, 82, 91]
E96_BASES = [
    100, 102, 105, 107, 110, 113, 115, 118, 121, 124, 127, 130,
    133, 137, 140, 143, 147, 150, 154, 158, 162, 165, 169, 174,
    178, 182, 187, 191, 196, 200, 205, 210, 215, 221, 226, 232,
    237, 243, 249, 255, 261, 267, 274, 280, 287, 294, 301, 309,
    316, 324, 332, 340, 348, 357, 365, 374, 383, 392, 402, 412,
    422, 432, 442, 453, 464, 475, 487, 499, 511, 523, 536, 549,
    562, 576, 590, 604, 619, 634, 649, 665, 681, 698, 715, 732,
    750, 768, 787, 806, 825, 845, 866, 887, 909, 931, 953, 976,
]


def decimal_text(value: Decimal) -> str:
    normalized = value.normalize()
    text = format(normalized, "f")
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    return text


def quantize_value(value: Decimal, places: int = 6) -> Decimal:
    quant = Decimal(1).scaleb(-places)
    return value.quantize(quant, rounding=ROUND_HALF_UP).normalize()


def resistor_code(value: Decimal, significant_digits: int) -> str:
    if value == 0:
        return "000" if significant_digits == 2 else "0000"

    if value < Decimal("10"):
        decimal_places = significant_digits - 1
        text = f"{value:.{decimal_places}f}"
        whole, frac = text.split(".", 1)
        return f"{whole}R{frac}"

    if value < Decimal("100"):
        if significant_digits == 2:
            return f"{int(value.to_integral_value(rounding=ROUND_HALF_UP)):02d}0"
        text = f"{value:.1f}"
        whole, frac = text.split(".", 1)
        return f"{whole}R{frac}"

    upper_limit = Decimal(10) ** significant_digits
    lower_limit = Decimal(10) ** (significant_digits - 1)
    significant = Decimal(value)
    multiplier = 0
    while significant >= upper_limit:
        significant = significant / Decimal(10)
        multiplier += 1
    while significant < lower_limit:
        significant = significant * Decimal(10)
        multiplier -= 1
    sig_int = int(significant.to_integral_value(rounding=ROUND_HALF_UP))
    if sig_int >= int(upper_limit):
        sig_int //= 10
        multiplier += 1
    return f"{sig_int:0{significant_digits}d}{multiplier}"


def display_resistance(value: Decimal) -> str:
    if value >= Decimal("1000000"):
        return f"{decimal_text(value / Decimal('1000000'))}MΩ"
    if value >= Decimal("1000"):
        return f"{decimal_text(value / Decimal('1000'))}KΩ"
    return f"{decimal_text(value)}Ω"


def generate_5_percent_values() -> list[Decimal]:
    values: set[Decimal] = set()
    for base in E24_BASES:
        for decade in range(0, 8):
            value = quantize_value(Decimal(base) * (Decimal(10) ** Decimal(decade - 1)))
            if Decimal("1") <= value <= Decimal("10000000"):
                values.add(value)
    return sorted(values)


def generate_1_percent_values() -> list[Decimal]:
    values: set[Decimal] = set()
    for base in E96_BASES:
        for decade in range(0, 8):
            value = quantize_value((Decimal(base) / Decimal(100)) * (Decimal(10) ** Decimal(decade)))
            if Decimal("1") <= value <= Decimal("10000000"):
                values.add(value)
    for base in E24_BASES:
        for decade in range(0, 8):
            value = quantize_value(Decimal(base) * (Decimal(10) ** Decimal(decade - 1)))
            if Decimal("1") <= value <= Decimal("10000000"):
                values.add(value)
    return sorted(values)


def build_candidate_rows() -> pd.DataFrame:
    checked_at = dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    rows: list[dict[str, object]] = []

    for value in generate_5_percent_values():
        code = resistor_code(value, significant_digits=2)
        model = f"FRC0201J{code} TS"
        summary = f"厚膜电阻 {display_resistance(value)} ±5% {POWER_TEXT}"
        rows.append(
            {
                "品牌": BRAND,
                "型号": model,
                "系列": SERIES,
                "尺寸（inch）": SIZE_INCH,
                "特殊用途": "",
                "备注1": summary,
                "备注2": f"Package={PACKAGE}",
                "器件类型": "厚膜电阻",
                "安装方式": "贴片",
                "封装代码": SIZE_INCH,
                "尺寸（mm）": SIZE_MM,
                "规格摘要": summary,
                "生产状态": "可生产",
                "工作温度": TEMPERATURE,
                "阻值@25C": decimal_text(value),
                "阻值单位": "Ω",
                "阻值误差": "±5%",
                "容值误差": "±5%",
                "系列说明": "普通厚膜贴片电阻",
                "数据来源": DATA_SOURCE,
                "数据状态": "按富捷FRC0201范围生成",
                "校验时间": checked_at,
                "校验备注": "pricing/fojan_resistor_series_pricing.csv: FRC 0201 1/20W 5% range",
                "_model_rule_authority": MODEL_AUTHORITY,
                "_resistance_ohm": float(value),
            }
        )

    for value in generate_1_percent_values():
        code = resistor_code(value, significant_digits=3)
        model = f"FRC0201F{code}TS"
        summary = f"厚膜电阻 {display_resistance(value)} ±1% {POWER_TEXT}"
        rows.append(
            {
                "品牌": BRAND,
                "型号": model,
                "系列": SERIES,
                "尺寸（inch）": SIZE_INCH,
                "特殊用途": "",
                "备注1": summary,
                "备注2": f"Package={PACKAGE}",
                "器件类型": "厚膜电阻",
                "安装方式": "贴片",
                "封装代码": SIZE_INCH,
                "尺寸（mm）": SIZE_MM,
                "规格摘要": summary,
                "生产状态": "可生产",
                "工作温度": TEMPERATURE,
                "阻值@25C": decimal_text(value),
                "阻值单位": "Ω",
                "阻值误差": "±1%",
                "容值误差": "±1%",
                "系列说明": "普通厚膜贴片电阻",
                "数据来源": DATA_SOURCE,
                "数据状态": "按富捷FRC0201范围生成",
                "校验时间": checked_at,
                "校验备注": "pricing/fojan_resistor_series_pricing.csv: FRC 0201 1/20W 1% range",
                "_model_rule_authority": MODEL_AUTHORITY,
                "_resistance_ohm": float(value),
            }
        )

    return pd.DataFrame(rows).drop_duplicates(subset=["品牌", "型号"], keep="first").reset_index(drop=True)


def db_columns(conn: sqlite3.Connection) -> list[str]:
    return [row[1] for row in conn.execute('PRAGMA table_info("components")').fetchall()]


def existing_non_generated_model_keys(conn: sqlite3.Connection) -> set[str]:
    rows = conn.execute(
        """
        SELECT 型号
        FROM components
        WHERE (品牌 LIKE '%FOJAN%' OR 品牌 LIKE '%富捷%')
          AND COALESCE(数据来源, '') <> ?
        """,
        (DATA_SOURCE,),
    ).fetchall()
    return {cm.clean_model(row[0]) for row in rows if row and cm.clean_model(row[0]) != ""}


def upsert_generated_rows(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        return frame
    with sqlite3.connect(DB_PATH, timeout=60) as conn:
        conn.execute("PRAGMA busy_timeout = 60000")
        cols = db_columns(conn)
        conn.execute(
            "DELETE FROM components WHERE 品牌 = ? AND COALESCE(数据来源, '') = ?",
            (BRAND, DATA_SOURCE),
        )
        existing = existing_non_generated_model_keys(conn)
        selected = frame.loc[~frame["型号"].map(lambda value: cm.clean_model(value) in existing)].copy()
        if selected.empty:
            return selected
        selected.reindex(columns=cols, fill_value="").to_sql(
            "components",
            conn,
            if_exists="append",
            index=False,
            method="multi",
            chunksize=cm.sqlite_bulk_insert_chunksize(selected.reindex(columns=cols, fill_value="")),
        )
    return selected


def refresh_runtime_indexes(frame: pd.DataFrame) -> tuple[int, int, dict[str, int]]:
    if frame.empty:
        return 0, 0, {}
    with sqlite3.connect(DB_PATH, timeout=60) as conn:
        cols = db_columns(conn)
    seed_frame = frame.reindex(columns=cols, fill_value="")
    seed_prepared = cm.prepare_search_dataframe(seed_frame)
    if seed_prepared.empty:
        raise RuntimeError("generated FOJAN FRC0201 rows produced an empty prepared frame")
    removed_rows, inserted_rows = stream_replace_prepared_rows(seed_prepared)
    sidecar_counts = refresh_search_sidecar_rows(seed_prepared)
    return removed_rows, inserted_rows, sidecar_counts


def main() -> None:
    parser = argparse.ArgumentParser(description="Fill missing FOJAN FRC0201 rows from the official range/price table.")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    candidates = build_candidate_rows()
    print(f"candidate_rows={len(candidates)}")
    print("has_33r_5pct=" + str(bool((candidates["型号"] == "FRC0201J330 TS").any())))
    if args.dry_run:
        return

    inserted = upsert_generated_rows(candidates)
    removed_cache, inserted_cache, sidecar_counts = refresh_runtime_indexes(inserted)
    print(f"db_upserted={len(inserted)}")
    print(f"prepared_rows_removed={removed_cache}")
    print(f"prepared_rows_inserted={inserted_cache}")
    print(f"search_core_rows={sidecar_counts.get(cm.COMPONENTS_SEARCH_CORE_TABLE, 0)}")


if __name__ == "__main__":
    main()
