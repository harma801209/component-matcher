from __future__ import annotations

import shutil
import sqlite3
from datetime import datetime
from pathlib import Path

import pandas as pd

import component_matcher as cm


ROOT = Path(__file__).resolve().parent
DB_PATH = ROOT / "components.db"

UPDATE_COLUMNS = ["尺寸（mm）", "_body_size", "长度（mm）", "宽度（mm）", "高度（mm）", "直径（mm）", "尺寸来源"]
NON_MLCC_CAP_TYPES = ["铝电解电容", "薄膜电容", "钽电容", "引线型陶瓷电容"]


def clean_value(value: object, dimension: bool = False) -> str:
    if dimension:
        return cm.normalize_dimension_mm_value(value)
    return cm.clean_text(value)


def values_differ(before: object, after: object, column: str) -> bool:
    return clean_value(before, dimension=column.endswith("（mm）")) != clean_value(after, dimension=column.endswith("（mm）"))


def backup_database() -> Path:
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = DB_PATH.with_suffix(f".capacitor_dimensions_{stamp}.bak")
    shutil.copy2(DB_PATH, backup_path)
    return backup_path


def load_target_rows(conn: sqlite3.Connection) -> pd.DataFrame:
    placeholders = ",".join("?" for _ in NON_MLCC_CAP_TYPES)
    return pd.read_sql_query(
        f'''
        SELECT rowid AS "__rowid__", *
        FROM components
        WHERE "器件类型" IN ({placeholders})
          AND (
            COALESCE("尺寸（mm）", "") <> ""
            OR COALESCE("_body_size", "") <> ""
            OR COALESCE("规格摘要", "") <> ""
            OR COALESCE("型号", "") <> ""
          )
          AND (
            COALESCE("高度（mm）", "") = ""
            OR COALESCE("直径（mm）", "") = ""
            OR COALESCE("尺寸来源", "") = ""
            OR COALESCE("_body_size", "") = ""
            OR COALESCE("尺寸（mm）", "") NOT LIKE "%mm"
          )
        ''',
        conn,
        params=NON_MLCC_CAP_TYPES,
    )


def build_updates(frame: pd.DataFrame) -> list[tuple[str, str, str, str, str, str, str, int]]:
    if frame.empty:
        return []
    enriched = cm.normalize_capacitor_dimension_fields_in_dataframe(frame)
    updates: list[tuple[str, str, str, str, str, str, str, int]] = []
    for idx in frame.index:
        changed = False
        values = []
        for column in UPDATE_COLUMNS:
            before = frame.at[idx, column] if column in frame.columns else ""
            after = enriched.at[idx, column] if column in enriched.columns else ""
            if values_differ(before, after, column):
                changed = True
            values.append(clean_value(after, dimension=column.endswith("（mm）")))
        if changed:
            values.append(int(frame.at[idx, "__rowid__"]))
            updates.append(tuple(values))
    return updates


def main() -> int:
    if not DB_PATH.exists():
        raise FileNotFoundError(DB_PATH)
    backup_path = backup_database()
    with sqlite3.connect(DB_PATH, timeout=60) as conn:
        conn.execute("PRAGMA busy_timeout = 60000")
        rows = load_target_rows(conn)
        updates = build_updates(rows)
        if updates:
            conn.executemany(
                '''
                UPDATE components
                   SET "尺寸（mm）" = ?,
                       "_body_size" = ?,
                       "长度（mm）" = ?,
                       "宽度（mm）" = ?,
                       "高度（mm）" = ?,
                       "直径（mm）" = ?,
                       "尺寸来源" = ?
                 WHERE rowid = ?
                ''',
                updates,
            )
            conn.commit()
    print(f"backup={backup_path.name}")
    print(f"target_rows={len(rows)}")
    print(f"updated_rows={len(updates)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
