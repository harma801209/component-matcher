from __future__ import annotations

import argparse
import shutil
import sqlite3
from datetime import datetime
from pathlib import Path

import pandas as pd

import component_matcher as cm
from incremental_semiconductor_cache_update import refresh_search_sidecar_rows
from sync_selected_cache_rows import stream_replace_prepared_rows


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


def merge_source_text(current: object, candidate: object) -> str:
    current_text = clean_value(current)
    candidate_text = clean_value(candidate)
    if candidate_text == "":
        return current_text
    if current_text == "":
        return candidate_text
    parts: list[str] = []
    for source_text in [current_text, candidate_text]:
        for part in source_text.split("/"):
            part = clean_value(part)
            if part and part not in parts:
                parts.append(part)
    return " / ".join(parts)


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


def valid_aluminum_dimension(value: object) -> str:
    text = cm.normalize_dimension_mm_value(value)
    if text == "" or text.startswith("."):
        return ""
    try:
        number = float(text.split("±", 1)[0].split("+", 1)[0])
    except Exception:
        return ""
    if 1.0 <= number <= 120.0:
        return text
    return ""


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


def build_aluminum_unique_reference_updates(conn: sqlite3.Connection) -> list[tuple[str, str, str, str, str, str, str, int]]:
    frame = pd.read_sql_query(
        '''
        SELECT rowid AS "__rowid__", *
        FROM components
        WHERE "器件类型" = "铝电解电容"
        ''',
        conn,
    )
    if frame.empty:
        return []

    for column in ["品牌", "系列", "容值", "容值单位", "耐压（V）", "型号", "高度（mm）", "直径（mm）"]:
        if column not in frame.columns:
            frame[column] = ""
        frame[column] = frame[column].apply(clean_value)

    key_columns = ["品牌", "系列", "容值", "容值单位", "耐压（V）"]
    blank = frame[frame["高度（mm）"].eq("")].copy()
    filled = frame[frame["高度（mm）"].ne("")].copy()
    if blank.empty or filled.empty:
        return []

    filled["_height_valid"] = filled["高度（mm）"].apply(valid_aluminum_dimension)
    filled["_diameter_valid"] = filled["直径（mm）"].apply(valid_aluminum_dimension)
    filled = filled[filled["_height_valid"].ne("") & filled["_diameter_valid"].ne("")].copy()
    if filled.empty:
        return []

    dimension_map: dict[tuple[str, ...], tuple[str, str]] = {}
    ambiguous_keys: set[tuple[str, ...]] = set()
    for key_values, group in filled.groupby(key_columns, dropna=False):
        key = tuple(clean_value(value) for value in key_values)
        dimensions = {
            (clean_value(row["直径（mm）"]), clean_value(row["高度（mm）"]))
            for _, row in group.iterrows()
            if valid_aluminum_dimension(row["直径（mm）"]) and valid_aluminum_dimension(row["高度（mm）"])
        }
        if len(dimensions) == 1:
            dimension_map[key] = next(iter(dimensions))
        elif len(dimensions) > 1:
            ambiguous_keys.add(key)

    updates: list[tuple[str, str, str, str, str, str, str, int]] = []
    for _, row in blank.iterrows():
        key = tuple(clean_value(row.get(column, "")) for column in key_columns)
        if key in ambiguous_keys or key not in dimension_map:
            continue
        diameter, height = dimension_map[key]
        if diameter == "" or height == "":
            continue

        size_text = f"{diameter}×{height}"
        source = merge_source_text(row.get("尺寸来源", ""), "本地库同系列同容值同耐压唯一尺寸")
        updates.append(
            (
                size_text,
                size_text,
                clean_value(row.get("长度（mm）", "")),
                clean_value(row.get("宽度（mm）", "")),
                height,
                diameter,
                source,
                int(row["__rowid__"]),
            )
        )
    return updates


def merge_updates(updates: list[tuple[str, str, str, str, str, str, str, int]]) -> list[tuple[str, str, str, str, str, str, str, int]]:
    merged: dict[int, tuple[str, str, str, str, str, str, str, int]] = {}
    for update in updates:
        merged[int(update[-1])] = update
    return list(merged.values())


def refresh_changed_rows(rowids: list[int]) -> tuple[int, int, dict[str, int]]:
    if not rowids:
        return 0, 0, {}
    placeholders = ",".join("?" for _ in rowids)
    with sqlite3.connect(DB_PATH) as conn:
        changed_frame = pd.read_sql_query(
            f'SELECT * FROM components WHERE rowid IN ({placeholders})',
            conn,
            params=rowids,
        )
    if changed_frame.empty:
        return 0, 0, {}
    prepared = cm.prepare_search_dataframe(cm.deduplicate_component_rows(changed_frame))
    removed, inserted = stream_replace_prepared_rows(prepared)
    sidecar_counts = refresh_search_sidecar_rows(prepared)
    return removed, inserted, sidecar_counts


def main() -> int:
    parser = argparse.ArgumentParser(description="Backfill non-MLCC capacitor dimensions from local fields and safe local references.")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--skip-cache", action="store_true")
    args = parser.parse_args()

    if not DB_PATH.exists():
        raise FileNotFoundError(DB_PATH)
    with sqlite3.connect(DB_PATH, timeout=60) as conn:
        conn.execute("PRAGMA busy_timeout = 60000")
        rows = load_target_rows(conn)
        current_height_by_rowid = {
            int(row["__rowid__"]): clean_value(row.get("高度（mm）", ""))
            for _, row in rows.iterrows()
        }
        updates = merge_updates(build_updates(rows) + build_aluminum_unique_reference_updates(conn))
        height_updates = sum(
            1
            for update in updates
            if clean_value(update[4]) != "" and current_height_by_rowid.get(int(update[-1]), "") == ""
        )
        print(f"target_rows={len(rows)}")
        print(f"updates={len(updates)}")
        print(f"height_updates={height_updates}")
        if args.dry_run:
            print("dry_run=1")
            for update in updates[:20]:
                print(f"rowid={update[-1]} size={update[0]} height={update[4]} diameter={update[5]} source={update[6]}")
            return 0

        backup_path = backup_database()
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
    print(f"updated_rows={len(updates)}")

    if not args.skip_cache and updates:
        rowids = [int(update[-1]) for update in updates]
        removed, inserted, sidecar_counts = refresh_changed_rows(rowids)
        print(f"prepared_removed={removed}")
        print(f"prepared_inserted={inserted}")
        print(f"search_core_rows={sidecar_counts.get(cm.COMPONENTS_SEARCH_CORE_TABLE, 0)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
