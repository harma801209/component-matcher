from __future__ import annotations

import argparse
import shutil
import sqlite3
from datetime import datetime
from decimal import Decimal
from pathlib import Path

import pandas as pd

import component_matcher as cm
from incremental_semiconductor_cache_update import refresh_search_sidecar_rows
from sync_selected_cache_rows import stream_replace_prepared_rows


ROOT = Path(__file__).resolve().parent
DB_PATH = ROOT / "components.db"


def clean_text(value: object) -> str:
    text = str(value or "").strip()
    return "" if text.lower() in {"nan", "none"} else text


def decimal_text(value: float) -> str:
    decimal_value = Decimal(str(float(value))).normalize()
    text = format(decimal_value, "f")
    return text.rstrip("0").rstrip(".") if "." in text else text


def row_current_ohm(row: dict[str, object]) -> float | None:
    value = clean_text(row.get("容值", ""))
    unit = clean_text(row.get("容值单位", ""))
    if value == "":
        return None
    return cm.parse_resistive_measurement_to_ohms(f"{value}{unit}", default_unit=unit or "Ω")


def resistance_fields_from_summary(row: dict[str, object], normalize_units: bool = False) -> tuple[str, str, str, str] | None:
    if cm.normalize_component_type(row.get("器件类型", "")) not in cm.RESISTOR_COMPONENT_TYPES:
        return None
    summary = clean_text(row.get("规格摘要", ""))
    if summary == "":
        return None
    parsed_ohm = cm.find_explicit_resistance_in_text(summary)
    if parsed_ohm is None:
        return None

    value, unit = cm.ohm_to_library_value_unit(parsed_ohm)
    current_ohm = row_current_ohm(row)
    current_value = clean_text(row.get("容值", ""))
    current_unit = cm.normalize_library_value_unit(row.get("容值单位", ""))
    numeric_mismatch = (
        current_ohm is None
        or abs(float(current_ohm) - float(parsed_ohm)) > max(abs(float(parsed_ohm)), 1.0) * 1e-9
    )
    presentation_mismatch = current_value != value or current_unit != unit
    if not numeric_mismatch and not (normalize_units and presentation_mismatch):
        return None

    return value, unit, decimal_text(parsed_ohm), "Ω"


def find_updates(limit: int = 0, normalize_units: bool = False, chunk_size: int = 50_000) -> tuple[list[tuple[int, str, str, str, str]], list[dict[str, object]]]:
    updates: list[tuple[int, str, str, str, str]] = []
    samples: list[dict[str, object]] = []
    query = """
        SELECT rowid, [品牌], [型号], [器件类型], [尺寸（inch）], [容值], [容值单位],
               [阻值@25C], [阻值单位], [规格摘要]
        FROM components
        WHERE [规格摘要] IS NOT NULL
          AND [规格摘要] <> ''
          AND [器件类型] LIKE '%电阻%'
    """
    with sqlite3.connect(DB_PATH) as conn:
        for chunk in pd.read_sql_query(query, conn, chunksize=chunk_size):
            for row in chunk.to_dict(orient="records"):
                fields = resistance_fields_from_summary(row, normalize_units=normalize_units)
                if fields is None:
                    continue
                value, unit, ohm_text, ohm_unit = fields
                updates.append((int(row["rowid"]), value, unit, ohm_text, ohm_unit))
                if len(samples) < 30:
                    samples.append(
                        {
                            "rowid": int(row["rowid"]),
                            "品牌": row.get("品牌", ""),
                            "型号": row.get("型号", ""),
                            "old": f"{clean_text(row.get('容值', ''))}{clean_text(row.get('容值单位', ''))}",
                            "new": f"{value}{unit}",
                            "规格摘要": row.get("规格摘要", ""),
                        }
                    )
                if limit > 0 and len(updates) >= limit:
                    return updates, samples
    return updates, samples


def load_rows_by_rowid(rowids: list[int], batch_size: int = 900) -> pd.DataFrame:
    if not rowids:
        return pd.DataFrame()
    frames: list[pd.DataFrame] = []
    with sqlite3.connect(DB_PATH) as conn:
        for start in range(0, len(rowids), batch_size):
            batch = rowids[start : start + batch_size]
            placeholders = ",".join(["?"] * len(batch))
            frames.append(pd.read_sql_query(f"SELECT * FROM components WHERE rowid IN ({placeholders})", conn, params=batch))
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()


def backup_database() -> Path:
    backup_path = DB_PATH.with_name(f"{DB_PATH.name}.resistor_value_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.bak")
    shutil.copy2(DB_PATH, backup_path)
    return backup_path


def apply_updates(updates: list[tuple[int, str, str, str, str]]) -> None:
    if not updates:
        return
    params = [(value, unit, ohm_text, ohm_unit, rowid) for rowid, value, unit, ohm_text, ohm_unit in updates]
    with sqlite3.connect(DB_PATH) as conn:
        conn.executemany(
            """
            UPDATE components
               SET [容值] = ?,
                   [容值单位] = ?,
                   [阻值@25C] = ?,
                   [阻值单位] = ?
             WHERE rowid = ?
            """,
            params,
        )
        conn.commit()


def main() -> None:
    parser = argparse.ArgumentParser(description="Correct resistor value fields from explicit resistance text in 规格摘要.")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--no-backup", action="store_true")
    parser.add_argument("--skip-cache", action="store_true")
    parser.add_argument("--normalize-units", action="store_true", help="Also rewrite equivalent values such as 1000Ω to 1KΩ.")
    parser.add_argument("--limit", type=int, default=0)
    args = parser.parse_args()

    updates, samples = find_updates(limit=max(args.limit, 0), normalize_units=bool(args.normalize_units))
    print(f"candidate_updates={len(updates)}")
    for sample in samples:
        print(
            "sample\t"
            f"rowid={sample['rowid']}\t"
            f"brand={sample['品牌']}\t"
            f"model={sample['型号']}\t"
            f"{sample['old']} -> {sample['new']}\t"
            f"summary={sample['规格摘要']}"
        )
    if args.dry_run or not updates:
        return

    backup_path = None if args.no_backup else backup_database()
    if backup_path is not None:
        print(f"backup={backup_path}")
    apply_updates(updates)
    print(f"db_updated_rows={len(updates)}")

    if args.skip_cache:
        return

    rowids = [rowid for rowid, *_ in updates]
    db_rows = load_rows_by_rowid(rowids)
    seed_prepared = cm.prepare_search_dataframe(cm.deduplicate_component_rows(db_rows))
    removed_rows, inserted_rows = stream_replace_prepared_rows(seed_prepared)
    sidecar_counts = refresh_search_sidecar_rows(seed_prepared)
    print(f"cache_db_rows={len(db_rows)}")
    print(f"prepared_rows_removed={removed_rows}")
    print(f"prepared_rows_inserted={inserted_rows}")
    print(f"search_core_rows={sidecar_counts.get(cm.COMPONENTS_SEARCH_CORE_TABLE, 0)}")


if __name__ == "__main__":
    main()
