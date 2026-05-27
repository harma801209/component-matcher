from __future__ import annotations

import shutil
import sqlite3
from datetime import datetime
from pathlib import Path

import component_matcher as cm


BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "components.db"

SOURCE_URL = "https://www.lcsc.com/product-detail/Current-Sense-Resistors-Shunt-Resistors_RALEC-LR2512-22R001F4_C154668.html"
SOURCE_NOTE = "RALEC LR Series IE-SP-022 datasheet; LCSC C154668"

SEED_MODELS = [
    "LR2512-22R001F4",
]


def now_text() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M")


def make_backup() -> Path:
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = DB_PATH.with_name(f"components.db.ralec_lr_resistors_{stamp}.bak")
    shutil.copy2(DB_PATH, backup_path)
    return backup_path


def build_row_from_parsed(columns: list[str], model: str) -> dict[str, object]:
    parsed = cm.parse_model_rule(model, brand="旺诠RALEC", component_type="合金电阻") or {}
    row = {col: "" for col in columns}
    for key, value in parsed.items():
        if key in row and key != "型号":
            row[key] = value
    row["品牌"] = "旺诠RALEC"
    row["型号"] = model
    row["官网链接"] = SOURCE_URL
    row["数据来源"] = SOURCE_NOTE
    row["数据状态"] = "规格书/代理可查"
    row["校验时间"] = now_text()
    row["校验备注"] = "R001=1mΩ; F=±1%; 22=2 terminals + 2W; packaging 4=4000pcs"
    row["生产状态"] = "Active"
    return row


def upsert_row(conn: sqlite3.Connection, table: str, columns: list[str], row: dict[str, object]) -> str:
    model = str(row["型号"])
    brand = str(row["品牌"])
    existing = conn.execute(
        f"SELECT rowid FROM {table} WHERE 品牌 = ? AND 型号 = ? LIMIT 1",
        (brand, model),
    ).fetchone()
    if existing is None:
        placeholders = ",".join("?" for _ in columns)
        quoted_cols = ",".join(f'"{col}"' for col in columns)
        values = [row.get(col, "") for col in columns]
        conn.execute(f"INSERT INTO {table} ({quoted_cols}) VALUES ({placeholders})", values)
        return "inserted"

    rowid = existing[0]
    update_cols = [col for col in columns if col not in {"品牌", "型号"}]
    assignments = ",".join(f'"{col}" = ?' for col in update_cols)
    values = [row.get(col, "") for col in update_cols]
    values.append(rowid)
    conn.execute(f"UPDATE {table} SET {assignments} WHERE rowid = ?", values)
    return "updated"


def update_existing_ralec_lr_rows(conn: sqlite3.Connection, table: str) -> int:
    rows = conn.execute(
        f"""
        SELECT rowid, 品牌, 型号
        FROM {table}
        WHERE (品牌 LIKE '%RALEC%' OR 品牌 LIKE '%旺诠%')
          AND (型号 LIKE 'LR%' OR 型号 LIKE 'LRE%')
        """
    ).fetchall()
    updated = 0
    for rowid, brand, model in rows:
        parsed = cm.parse_model_rule(model, brand=brand, component_type="合金电阻")
        if not parsed:
            continue
        fields = {
            "系列": parsed.get("系列", ""),
            "系列说明": parsed.get("系列说明", ""),
            "器件类型": parsed.get("器件类型", ""),
            "特殊用途": parsed.get("特殊用途", ""),
            "尺寸（inch）": parsed.get("尺寸（inch）", ""),
            "尺寸（mm）": parsed.get("尺寸（mm）", ""),
            "长度（mm）": parsed.get("长度（mm）", ""),
            "宽度（mm）": parsed.get("宽度（mm）", ""),
            "高度（mm）": parsed.get("高度（mm）", ""),
            "容值": parsed.get("容值", ""),
            "容值单位": parsed.get("容值单位", ""),
            "容值误差": parsed.get("容值误差", ""),
            "安装方式": parsed.get("安装方式", ""),
            "封装代码": parsed.get("封装代码", ""),
            "规格摘要": parsed.get("规格摘要", ""),
            "_model_rule_authority": parsed.get("_model_rule_authority", ""),
            "_resistance_ohm": parsed.get("_resistance_ohm", ""),
        }
        assignments = ",".join(f'"{col}" = ?' for col in fields)
        conn.execute(
            f"UPDATE {table} SET {assignments} WHERE rowid = ?",
            [fields[col] for col in fields] + [rowid],
        )
        updated += 1
    return updated


def main() -> None:
    backup_path = make_backup()
    conn = sqlite3.connect(DB_PATH)
    try:
        table = "components"
        columns = [row[1] for row in conn.execute(f"PRAGMA table_info({table})")]
        inserted = 0
        updated = 0
        for model in SEED_MODELS:
            status = upsert_row(conn, table, columns, build_row_from_parsed(columns, model))
            inserted += int(status == "inserted")
            updated += int(status == "updated")
        normalized = update_existing_ralec_lr_rows(conn, table)
        conn.commit()
    finally:
        conn.close()
    print(f"backup={backup_path.name}")
    print(f"inserted={inserted}")
    print(f"updated={updated}")
    print(f"normalized_existing={normalized}")


if __name__ == "__main__":
    main()
