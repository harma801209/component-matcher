from __future__ import annotations

import argparse
import datetime as dt
import shutil
import sqlite3
from decimal import Decimal
from pathlib import Path

import pandas as pd
import requests

import component_matcher as cm
from incremental_semiconductor_cache_update import refresh_search_sidecar_rows
from sync_selected_cache_rows import stream_replace_prepared_rows


ROOT = Path(__file__).resolve().parent
DB_PATH = ROOT / "components.db"
SOURCE_DIR = ROOT / "cache" / "sunlord_sources"

SUNLORD_BRAND = "Sunlord(顺络)"
SDNT_URL = "https://www.sunlordinc.com/uploads/files/20221123/SDNT%20series%20of%20Chip%20Temp.sensor%20NTC%20Thermistor.pdf"
SVMH_URL = "https://www.sunlordinc.com/uploads/files/20221123/SVMH%20Series%20of%20Multilayer%20Chip%20Varistor%20of%20Super%20High%20Voltage.pdf"

TODAY = dt.datetime.now().strftime("%Y-%m-%d %H:%M")

SDNT_DIMENSIONS = {
    "0603": ("0201", "0.60", "0.30", "0.30", "<3s", "1.0mW/degC", "100mW"),
    "1005": ("0402", "1.00", "0.50", "0.50", "<3s", "1.0mW/degC", "100mW"),
    "1608": ("0603", "1.60", "0.80", "0.80", "<5s", "1.0mW/degC", "100mW"),
    "2012": ("0805", "2.00", "1.25", "0.85", "<5s", "2.0mW/degC", "200mW"),
}

SDNT_TOLERANCES = {
    "F": "±1%",
    "H": "±3%",
    "J": "±5%",
    "K": "±10%",
}
SDNT_B_TOLERANCES = {
    "F": "±1%",
    "H": "±3%",
}

SDNT_BASE_SPECS = [
    ("SDNT0603C", "103", "10", "3380", "0.31"),
    ("SDNT0603C", "223", "22", "3380", "0.21"),
    ("SDNT0603C", "473", "47", "4050", "0.14"),
    ("SDNT0603C", "683", "68", "4250", "0.12"),
    ("SDNT0603C", "104", "100", "4250", "0.10"),
    ("SDNT1005X", "682", "6.8", "3950", "0.38"),
    ("SDNT1005X", "103", "10", "3380", "0.31"),
    ("SDNT1005X", "103", "10", "3950", "0.33"),
    ("SDNT1005X", "103", "10", "4050", "0.33"),
    ("SDNT1005X", "153", "15", "3450", "0.25"),
    ("SDNT1005X", "223", "22", "3950", "0.23"),
    ("SDNT1005X", "303", "30", "3950", "0.15"),
    ("SDNT1005X", "333", "33", "3950", "0.15"),
    ("SDNT1005X", "473", "47", "4050", "0.12"),
    ("SDNT1005X", "473", "47", "4100", "0.12"),
    ("SDNT1005X", "503", "50", "4100", "0.12"),
    ("SDNT1005X", "683", "68", "4150", "0.11"),
    ("SDNT1005X", "104", "100", "3950", "0.1"),
    ("SDNT1005X", "104", "100", "4150", "0.1"),
    ("SDNT1005X", "104", "100", "4250", "0.1"),
    ("SDNT1005X", "154", "150", "4150", "0.08"),
    ("SDNT1005X", "224", "220", "4250", "0.06"),
    ("SDNT1608X", "222", "2.2", "3450", "0.67"),
    ("SDNT1608X", "472", "4.7", "3950", "0.46"),
    ("SDNT1608X", "502", "5", "3950", "0.44"),
    ("SDNT1608X", "103", "10", "3380", "0.31"),
    ("SDNT1608X", "103", "10", "3450", "0.31"),
    ("SDNT1608X", "103", "10", "3950", "0.33"),
    ("SDNT1608X", "153", "15", "3950", "0.25"),
    ("SDNT1608X", "223", "22", "3950", "0.21"),
    ("SDNT1608X", "223", "22", "4050", "0.21"),
    ("SDNT1608X", "333", "33", "4050", "0.17"),
    ("SDNT1608X", "473", "47", "4050", "0.14"),
    ("SDNT1608X", "473", "47", "4150", "0.14"),
    ("SDNT1608X", "503", "50", "4150", "0.13"),
    ("SDNT1608X", "683", "68", "4150", "0.12"),
    ("SDNT1608X", "104", "100", "3950", "0.1"),
    ("SDNT1608X", "104", "100", "4250", "0.1"),
    ("SDNT1608X", "124", "120", "4250", "0.1"),
    ("SDNT1608X", "154", "150", "4250", "0.08"),
    ("SDNT1608X", "224", "220", "4300", "0.06"),
    ("SDNT2012X", "472", "4.7", "3950", "0.65"),
    ("SDNT2012X", "502", "5", "3950", "0.6"),
    ("SDNT2012X", "103", "10", "3450", "0.4"),
    ("SDNT2012X", "103", "10", "3950", "0.44"),
    ("SDNT2012X", "223", "22", "4050", "0.31"),
    ("SDNT2012X", "333", "33", "4050", "0.24"),
    ("SDNT2012X", "473", "47", "4050", "0.2"),
    ("SDNT2012X", "473", "47", "4150", "0.2"),
    ("SDNT2012X", "503", "50", "4150", "0.18"),
    ("SDNT2012X", "104", "100", "3950", "0.14"),
    ("SDNT2012X", "104", "100", "4250", "0.14"),
    ("SDNT2012X", "154", "150", "4250", "0.11"),
    ("SDNT2012X", "224", "220", "4300", "0.08"),
]

SVMH_DIMENSIONS = {
    "2016": ("0806", "2.20", "1.60", "2.00"),
    "3216": ("1206", "3.20", "1.60", "2.00"),
    "3225": ("1210", "3.20", "2.50", "2.60"),
    "4532": ("1812", "4.60", "3.50", "3.50"),
    "5650": ("2220", "6.00", "5.30", "3.60"),
}

SVMH_SPECS = [
    ("SVMH2016KA151PT101", "200", "150", "240", "216-264", "360", "5.0", "0.36", "100"),
    ("SVMH2016KA151PT181", "200", "150", "240", "216-264", "360", "5.0", "0.36", "180"),
    ("SVMH2016KA171PT181", "225", "175", "270", "243-297", "410", "5.0", "0.40", "180"),
    ("SVMH2016KA191PT101", "250", "195", "300", "270-330", "450", "5.0", "0.40", "100"),
    ("SVMH2016KA211PT101", "275", "210", "330", "297-363", "495", "5.0", "0.36", "100"),
    ("SVMH2016KA231PT101", "300", "230", "360", "324-396", "540", "5.0", "0.36", "100"),
    ("SVMH2016KA251PT700", "320", "250", "390", "351-429", "590", "5.0", "0.30", "70"),
    ("SVMH2016KA251PT500", "320", "250", "390", "351-429", "590", "5.0", "0.36", "50"),
    ("SVMH2016KA271PT500", "350", "275", "430", "387-473", "650", "5.0", "0.40", "50"),
    ("SVMH2016KA301PT500", "385", "300", "470", "423-517", "710", "5.0", "0.30", "50"),
    ("SVMH2016KA321PT500", "410", "320", "510", "459-561", "880", "5.0", "0.30", "50"),
    ("SVMH3216KA151PT301", "200", "150", "240", "216-264", "360", "5.0", "0.9", "300"),
    ("SVMH3216KA171PT301", "225", "175", "270", "243-297", "410", "5.0", "1.0", "300"),
    ("SVMH3216KA191PT201", "250", "195", "300", "270-330", "450", "5.0", "1.0", "200"),
    ("SVMH3216KA211PT201", "275", "210", "330", "297-363", "495", "5.0", "1.0", "200"),
    ("SVMH3216KA231PT201", "300", "230", "360", "324-396", "540", "5.0", "0.9", "200"),
    ("SVMH3216KA251PT101", "320", "250", "390", "351-429", "590", "5.0", "0.9", "100"),
    ("SVMH3216KA271PT101", "350", "275", "430", "387-473", "650", "5.0", "1.0", "100"),
    ("SVMH3216KA301PT101", "385", "300", "470", "423-517", "710", "5.0", "0.5", "100"),
    ("SVMH3216KA321PT600", "410", "320", "510", "459-561", "880", "5.0", "0.5", "60"),
    ("SVMH3225KA151PT401", "200", "150", "240", "216-264", "360", "5.0", "1.8", "400"),
    ("SVMH3225KA171PT401", "225", "175", "270", "243-297", "410", "5.0", "2.0", "400"),
    ("SVMH3225KA191PT401", "250", "195", "300", "270-330", "450", "5.0", "2.0", "400"),
    ("SVMH3225KA211PT401", "275", "210", "330", "297-363", "495", "5.0", "1.8", "400"),
    ("SVMH3225KA231PT401", "300", "230", "360", "324-396", "540", "5.0", "1.8", "400"),
    ("SVMH3225KA251PT201", "320", "250", "390", "351-429", "590", "5.0", "1.8", "200"),
    ("SVMH3225KA271PT201", "350", "275", "430", "387-473", "650", "5.0", "1.8", "200"),
    ("SVMH3225KA301PT201", "385", "300", "470", "423-517", "710", "5.0", "2.0", "200"),
    ("SVMH3225KA301PT301", "385", "300", "470", "423-517", "710", "5.0", "2.0", "300"),
    ("SVMH3225KA321PT151", "410", "320", "510", "459-561", "880", "5.0", "2.0", "150"),
    ("SVMH3225KA321PT251", "410", "320", "510", "459-561", "880", "5.0", "2.0", "250"),
    ("SVMH4532KA171PT801", "225", "175", "270", "243-297", "410", "5.0", "7.2", "800"),
    ("SVMH4532KA301PT401", "385", "300", "470", "423-517", "710", "5.0", "7.2", "400"),
    ("SVMH4532KA301PT801", "385", "300", "470", "423-517", "710", "5.0", "5.0", "800"),
    ("SVMH4532KA321PT251", "410", "320", "510", "459-561", "880", "5.0", "5.0", "250"),
    ("SVMH5650KA151PT152", "200", "150", "240", "216-264", "395", "10.0", "15", "1500"),
    ("SVMH5650KA171PT152", "225", "175", "270", "243-297", "455", "10.0", "15", "1500"),
    ("SVMH5650KA191PT122", "250", "195", "300", "270-330", "495", "10.0", "15", "1200"),
    ("SVMH5650KA191PT152", "250", "195", "300", "270-330", "495", "10.0", "15", "1500"),
    ("SVMH5650KA211PT122", "275", "210", "330", "297-363", "540", "10.0", "10", "1200"),
    ("SVMH5650KA211PT152", "275", "210", "330", "297-363", "540", "10.0", "10", "1500"),
    ("SVMH5650KA231PT122", "300", "230", "360", "324-396", "595", "10.0", "10", "1200"),
    ("SVMH5650KA231PT152", "300", "230", "360", "324-396", "595", "10.0", "10", "1500"),
    ("SVMH5650KA231PT202", "300", "230", "360", "324-396", "595", "10.0", "10", "2000"),
    ("SVMH5650KA251PT801", "320", "250", "390", "351-429", "650", "10.0", "10", "800"),
    ("SVMH5650KA271PT801", "350", "275", "430", "387-473", "710", "10.0", "10", "800"),
    ("SVMH5650KA301PT801", "385", "300", "470", "423-517", "775", "10.0", "10", "800"),
    ("SVMH5650KA321PT102", "410", "320", "510", "459-561", "845", "10.0", "10", "1000"),
]


def clean_text(value: object) -> str:
    text = str(value or "").strip()
    return "" if text.lower() in {"nan", "none"} else text


def download_sources(refresh: bool = False) -> None:
    SOURCE_DIR.mkdir(parents=True, exist_ok=True)
    for url, filename in ((SDNT_URL, "SDNT.pdf"), (SVMH_URL, "SVMH.pdf")):
        path = SOURCE_DIR / filename
        if path.exists() and not refresh:
            continue
        response = requests.get(url, timeout=60)
        response.raise_for_status()
        path.write_bytes(response.content)


def backup_database() -> Path:
    timestamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = DB_PATH.with_name(f"{DB_PATH.name}.sunlord_ntc_varistor_{timestamp}.bak")
    shutil.copy2(DB_PATH, backup_path)
    return backup_path


def db_columns(conn: sqlite3.Connection) -> list[str]:
    return [row[1] for row in conn.execute('PRAGMA table_info("components")').fetchall()]


def decimal_text(value: Decimal) -> str:
    text = format(value.normalize(), "f")
    return text.rstrip("0").rstrip(".") if "." in text else text


def kohm_to_ohm_text(kohm_text: str) -> str:
    return decimal_text(Decimal(kohm_text) * Decimal(1000))


def size_code_from_series(series: str) -> str:
    return series[4:8]


def build_base_row() -> dict[str, str]:
    return {
        "品牌": SUNLORD_BRAND,
        "安装方式": "贴片",
        "数据状态": "官方规格书命名规则生成",
        "校验时间": TODAY,
        "生产状态": "量产",
    }


def build_sdnt_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for series, resistance_code, r25_kohm, b_value, max_current in SDNT_BASE_SPECS:
        size_code = size_code_from_series(series)
        size_inch, length, width, height, thermal_time, dissipation, rated_power = SDNT_DIMENSIONS[size_code]
        for tolerance_code, tolerance in SDNT_TOLERANCES.items():
            for b_tolerance_code, b_tolerance in SDNT_B_TOLERANCES.items():
                model = f"{series}{resistance_code}{tolerance_code}{b_value}{b_tolerance_code}TF"
                row = build_base_row()
                row.update(
                    {
                        "型号": model,
                        "系列": series,
                        "系列说明": f"Sunlord {series} 片式温度传感 NTC 热敏电阻",
                        "器件类型": "热敏电阻",
                        "特殊用途": "测温 | 贴片 | NTC",
                        "尺寸（inch）": size_inch,
                        "封装代码": size_inch,
                        "尺寸（mm）": f"{length}x{width}x{height}",
                        "长度（mm）": length,
                        "宽度（mm）": width,
                        "高度（mm）": height,
                        "阻值@25C": kohm_to_ohm_text(r25_kohm),
                        "阻值单位": "Ω",
                        "阻值误差": tolerance,
                        "B值": b_value,
                        "B值条件": "B25/50",
                        "规格摘要": f"{series} {size_inch} R25={r25_kohm}kΩ {tolerance}; B25/50={b_value}K {b_tolerance}; {rated_power}",
                        "工作温度": "-40~125°C",
                        "额定电流": f"{max_current}mA",
                        "官网链接": SDNT_URL,
                        "数据来源": "Sunlord SDNT official PDF table generated",
                        "校验备注": "SDNT PDF table: Chip Temp. Sensing NTC Thermistor",
                        "备注1": f"R25 {r25_kohm}kΩ; B25/50 {b_value}K; B tolerance {b_tolerance}; Imax {max_current}mA; thermal time {thermal_time}; dissipation {dissipation}; rated power {rated_power}",
                        "备注2": "□=阻值误差(F/H/J/K), ◎=B值误差(F/H); 依据顺络SDNT规格书生成",
                        "_model_rule_authority": "Sunlord SDNT official PDF",
                    }
                )
                rows.append(row)
    return rows


def build_svmh_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for model, vdc, vac, varistor_v, varistor_range, clamp_v, clamp_current, energy, peak_current in SVMH_SPECS:
        body = model[4:8]
        size_inch, length, width, height = SVMH_DIMENSIONS[body]
        series = f"SVMH{body}"
        row = build_base_row()
        row.update(
            {
                "型号": model,
                "系列": series,
                "系列说明": f"Sunlord {series} 高电压多层贴片压敏电阻（浪涌抑制）",
                "器件类型": "贴片压敏电阻",
                "特殊用途": "高电压 | 多层 | 贴片 | 浪涌抑制 | AC电路",
                "尺寸（inch）": size_inch,
                "封装代码": size_inch,
                "尺寸（mm）": f"{length}x{width}x{height}",
                "长度（mm）": length,
                "宽度（mm）": width,
                "高度（mm）": height,
                "耐压（V）": varistor_v,
                "压敏电压": varistor_v,
                "规格摘要": f"{series} {size_inch} Vw={vdc}VDC/{vac}VAC; Vb={varistor_v}V [{varistor_range}]; Vc={clamp_v}V; {energy}J; {peak_current}A",
                "工作温度": "-55~125°C",
                "额定电流": f"{peak_current}A",
                "官网链接": SVMH_URL,
                "数据来源": "Sunlord SVMH official PDF table generated",
                "校验备注": "SVMH PDF table: High Voltage Multilayer Chip Varistor for Surge Suppression",
                "备注1": f"Max working {vdc}VDC/{vac}VAC; Varistor voltage {varistor_v}V [{varistor_range}] @1mA DC; Clamping {clamp_v}V @{clamp_current}A 8/20us; Energy {energy}J 10/1000us; Peak current {peak_current}A 8/20us",
                "备注2": "耐压（V）字段存放压敏电压Vb标称值；工作电压与钳位电压见备注/规格摘要",
                "_model_rule_authority": "Sunlord SVMH official PDF",
            }
        )
        rows.append(row)
    return rows


def generated_rows() -> list[dict[str, str]]:
    rows = build_sdnt_rows() + build_svmh_rows()
    unique: dict[tuple[str, str], dict[str, str]] = {}
    for row in rows:
        unique[(row["品牌"], row["型号"])] = row
    return list(unique.values())


def load_existing_rows(conn: sqlite3.Connection, models: list[str]) -> dict[tuple[str, str], dict[str, str]]:
    if not models:
        return {}
    columns = db_columns(conn)
    quoted_columns = ", ".join(f"[{col}]" for col in columns)
    existing: dict[tuple[str, str], dict[str, str]] = {}
    for start in range(0, len(models), 800):
        batch = models[start : start + 800]
        placeholders = ",".join("?" for _ in batch)
        params = [SUNLORD_BRAND, *batch]
        frame = pd.read_sql_query(
            f"SELECT {quoted_columns} FROM components WHERE [品牌]=? AND [型号] IN ({placeholders})",
            conn,
            params=params,
        )
        for row in frame.to_dict(orient="records"):
            existing[(clean_text(row.get("品牌")), clean_text(row.get("型号")))] = {
                col: clean_text(row.get(col, "")) for col in columns
            }
    return existing


def merge_with_existing(conn: sqlite3.Connection, rows: list[dict[str, str]]) -> list[dict[str, str]]:
    columns = db_columns(conn)
    existing = load_existing_rows(conn, [row["型号"] for row in rows])
    merged: list[dict[str, str]] = []
    for row in rows:
        key = (row["品牌"], row["型号"])
        out = {col: "" for col in columns}
        previous = existing.get(key)
        if previous:
            out.update(previous)
            old_note = " | ".join(clean_text(previous.get(col, "")) for col in ("备注1", "备注2") if clean_text(previous.get(col, "")) != "")
            if old_note and clean_text(row.get("备注3", "")) == "":
                row["备注3"] = f"原库资料保留: {old_note[:240]}"
        for col, value in row.items():
            if col in out and clean_text(value) != "":
                out[col] = clean_text(value)
        merged.append(out)
    return merged


def upsert_rows(conn: sqlite3.Connection, rows: list[dict[str, str]]) -> int:
    if not rows:
        return 0
    columns = db_columns(conn)
    merged = merge_with_existing(conn, rows)
    models = [row["型号"] for row in merged]
    for start in range(0, len(models), 800):
        batch = models[start : start + 800]
        placeholders = ",".join("?" for _ in batch)
        conn.execute(
            f"DELETE FROM components WHERE [品牌]=? AND [型号] IN ({placeholders})",
            [SUNLORD_BRAND, *batch],
        )
    quoted_columns = ", ".join(f"[{col}]" for col in columns)
    placeholders = ", ".join("?" for _ in columns)
    conn.executemany(
        f"INSERT INTO components ({quoted_columns}) VALUES ({placeholders})",
        [[row.get(col, "") for col in columns] for row in merged],
    )
    return len(merged)


def refresh_cache() -> tuple[int, int, dict[str, int]]:
    with sqlite3.connect(DB_PATH) as conn:
        db_rows = pd.read_sql_query(
            "SELECT * FROM components WHERE [品牌]=? AND [器件类型] IN ('热敏电阻','贴片压敏电阻')",
            conn,
            params=[SUNLORD_BRAND],
        )
    if db_rows.empty:
        return 0, 0, {}
    seed_prepared = cm.prepare_search_dataframe(cm.deduplicate_component_rows(db_rows))
    removed_rows, inserted_rows = stream_replace_prepared_rows(seed_prepared)
    sidecar_counts = refresh_search_sidecar_rows(seed_prepared)
    return removed_rows, inserted_rows, sidecar_counts


def main() -> None:
    parser = argparse.ArgumentParser(description="Sync Sunlord SDNT NTC and SVMH chip varistor official rows.")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--skip-cache", action="store_true")
    parser.add_argument("--refresh-sources", action="store_true")
    parser.add_argument("--no-backup", action="store_true")
    args = parser.parse_args()

    download_sources(refresh=args.refresh_sources)
    rows = generated_rows()
    print(f"generated_rows={len(rows)}")
    print(f"generated_sdnt_rows={sum(1 for row in rows if row['器件类型'] == '热敏电阻')}")
    print(f"generated_svmh_rows={sum(1 for row in rows if row['器件类型'] == '贴片压敏电阻')}")

    with sqlite3.connect(DB_PATH) as conn:
        before = pd.read_sql_query(
            "SELECT [器件类型], COUNT(*) rows FROM components WHERE [品牌]=? AND [器件类型] IN ('热敏电阻','贴片压敏电阻') GROUP BY [器件类型]",
            conn,
            params=[SUNLORD_BRAND],
        )
        print("existing_before=" + before.to_json(orient="records", force_ascii=False))

    if args.dry_run:
        print("dry_run=1")
        return

    backup_path = None if args.no_backup else backup_database()
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("BEGIN")
        upserted = upsert_rows(conn, rows)
        conn.commit()
    print(f"dry_run=0")
    if backup_path is not None:
        print(f"backup_path={backup_path}")
    print(f"upserted_rows={upserted}")

    if not args.skip_cache:
        removed_rows, inserted_rows, sidecar_counts = refresh_cache()
        print(f"prepared_removed={removed_rows}")
        print(f"prepared_inserted={inserted_rows}")
        print(f"search_core_rows={sidecar_counts.get(cm.COMPONENTS_SEARCH_CORE_TABLE, 0)}")


if __name__ == "__main__":
    main()
