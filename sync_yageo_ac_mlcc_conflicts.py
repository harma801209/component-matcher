from __future__ import annotations

import argparse
import json
import os
import shutil
import sqlite3
import tempfile
from datetime import datetime
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq


ROOT = Path(__file__).resolve().parent
DB_PATH = ROOT / "components.db"
PREPARED_PATH = ROOT / "cache" / "components_prepared_v5.parquet"
PREPARED_META_PATH = ROOT / "cache" / "components_prepared_v5_meta.json"
SEARCH_PATH = ROOT / "cache" / "components_search.sqlite"
RESISTOR_TYPES = (
    "贴片电阻",
    "厚膜电阻",
    "薄膜电阻",
    "合金电阻",
    "绕线电阻",
    "碳膜电阻",
    "金属氧化膜电阻",
)
MODEL_DIELECTRIC_SQL = """
(
    UPPER(型号) LIKE '%X7R%'
    OR UPPER(型号) LIKE '%X5R%'
    OR UPPER(型号) LIKE '%NPO%'
    OR UPPER(型号) LIKE '%NP0%'
    OR UPPER(型号) LIKE '%C0G%'
)
"""


def target_where_sql() -> str:
    placeholders = ",".join("?" for _ in RESISTOR_TYPES)
    return f"""
        (品牌 LIKE '%YAGEO%' OR 品牌 LIKE '%国巨%')
        AND UPPER(型号) LIKE 'AC%'
        AND {MODEL_DIELECTRIC_SQL}
        AND 器件类型 IN ({placeholders})
    """


def is_target_frame(frame):
    brand = frame["品牌"].astype("string").fillna("").str.upper()
    model = frame["型号"].astype("string").fillna("").str.upper()
    component_type = frame["器件类型"].astype("string").fillna("")
    dielectric = model.str.contains("X7R|X5R|NPO|NP0|C0G", regex=True)
    return (
        (brand.str.contains("YAGEO", regex=False) | brand.str.contains("国巨", regex=False))
        & model.str.startswith("AC")
        & dielectric
        & component_type.isin(RESISTOR_TYPES)
    )


def sync_cache_cleanup(batch_size=50_000):
    if not PREPARED_PATH.exists() or not SEARCH_PATH.exists():
        raise FileNotFoundError("prepared cache or search sidecar is missing")

    parquet_file = pq.ParquetFile(PREPARED_PATH)
    schema = parquet_file.schema_arrow
    fd, temp_name = tempfile.mkstemp(
        prefix=f"{PREPARED_PATH.name}.yageo_cleanup.",
        suffix=".tmp",
        dir=str(PREPARED_PATH.parent),
    )
    os.close(fd)
    temp_path = Path(temp_name)
    removed_rows = 0
    marked_mlcc_rows = 0
    try:
        with pq.ParquetWriter(temp_path, schema=schema, compression="snappy") as writer:
            for batch in parquet_file.iter_batches(batch_size=batch_size):
                frame = batch.to_pandas()
                remove_mask = is_target_frame(frame)
                removed_rows += int(remove_mask.sum())
                kept = frame.loc[~remove_mask].copy()
                brand = kept["品牌"].astype("string").fillna("").str.upper()
                model = kept["型号"].astype("string").fillna("").str.upper()
                mlcc_mask = (
                    (brand.str.contains("YAGEO", regex=False) | brand.str.contains("国巨", regex=False))
                    & model.str.startswith("AC")
                    & model.str.contains("X7R|X5R|NPO|NP0|C0G", regex=True)
                    & kept["器件类型"].astype("string").fillna("").eq("MLCC")
                )
                if "_model_rule_authority" in kept.columns and mlcc_mask.any():
                    kept.loc[mlcc_mask, "_model_rule_authority"] = "yageo_mlcc_model"
                    marked_mlcc_rows += int(mlcc_mask.sum())
                writer.write_table(pa.Table.from_pandas(kept, schema=schema, preserve_index=False))
        parquet_file.close()
        os.replace(temp_path, PREPARED_PATH)
    finally:
        try:
            parquet_file.close()
        except Exception:
            pass
        temp_path.unlink(missing_ok=True)

    search_removed = 0
    placeholders = ",".join("?" for _ in RESISTOR_TYPES)
    with sqlite3.connect(SEARCH_PATH, timeout=60) as conn:
        for table_name in ("components_search_core", "components_search_resistor"):
            cursor = conn.execute(
                f"""
                DELETE FROM {table_name}
                WHERE ([品牌] LIKE '%YAGEO%' OR [品牌] LIKE '%国巨%')
                  AND UPPER([型号]) LIKE 'AC%'
                  AND (
                      UPPER([型号]) LIKE '%X7R%' OR UPPER([型号]) LIKE '%X5R%'
                      OR UPPER([型号]) LIKE '%NPO%' OR UPPER([型号]) LIKE '%NP0%'
                      OR UPPER([型号]) LIKE '%C0G%'
                  )
                  AND [_component_type] IN ({placeholders})
                """,
                RESISTOR_TYPES,
            )
            search_removed += int(cursor.rowcount or 0)
        conn.commit()

    meta = {}
    if PREPARED_META_PATH.exists():
        try:
            meta = json.loads(PREPARED_META_PATH.read_text(encoding="utf-8"))
        except Exception:
            meta = {}
    stat = DB_PATH.stat()
    meta.update(
        {
            "db_path": str(DB_PATH),
            "db_mtime": stat.st_mtime,
            "db_size": stat.st_size,
            "yageo_ac_mlcc_cleanup_rows": removed_rows,
        }
    )
    PREPARED_META_PATH.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    return removed_rows, search_removed, marked_mlcc_rows


def main() -> None:
    parser = argparse.ArgumentParser(description="Remove Yageo AC MLCC rows misclassified as resistors.")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--no-backup", action="store_true")
    parser.add_argument("--sync-cache", action="store_true")
    args = parser.parse_args()

    where_sql = target_where_sql()
    with sqlite3.connect(DB_PATH, timeout=60) as conn:
        candidate_count = int(
            conn.execute(f"SELECT COUNT(*) FROM components WHERE {where_sql}", RESISTOR_TYPES).fetchone()[0]
        )
        orphan_count = int(
            conn.execute(
                f"""
                SELECT COUNT(*)
                FROM components bad
                WHERE {where_sql.replace('品牌', 'bad.品牌').replace('型号', 'bad.型号').replace('器件类型', 'bad.器件类型')}
                  AND NOT EXISTS (
                      SELECT 1 FROM components good
                      WHERE good.品牌 = bad.品牌 AND good.型号 = bad.型号 AND good.器件类型 = 'MLCC'
                  )
                """,
                RESISTOR_TYPES,
            ).fetchone()[0]
        )
    print(f"candidates={candidate_count}")
    print(f"without_mlcc_counterpart={orphan_count}")
    if args.dry_run:
        return
    if candidate_count == 0:
        if args.sync_cache:
            removed_rows, search_removed, marked_rows = sync_cache_cleanup()
            print(f"prepared_cache_deleted={removed_rows}")
            print(f"search_sidecar_deleted={search_removed}")
            print(f"prepared_mlcc_authority_marked={marked_rows}")
        return
    if orphan_count != 0:
        raise RuntimeError("cleanup aborted because some candidate rows have no MLCC counterpart")

    if not args.no_backup:
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = DB_PATH.with_name(f"{DB_PATH.name}.yageo_ac_mlcc_cleanup_{stamp}.bak")
        shutil.copy2(DB_PATH, backup_path)
        print(f"backup={backup_path}")

    with sqlite3.connect(DB_PATH, timeout=60) as conn:
        cursor = conn.execute(f"DELETE FROM components WHERE {where_sql}", RESISTOR_TYPES)
        conn.execute(
            f"""
            UPDATE components
            SET _model_rule_authority='yageo_mlcc_model'
            WHERE (品牌 LIKE '%YAGEO%' OR 品牌 LIKE '%国巨%')
              AND UPPER(型号) LIKE 'AC%'
              AND {MODEL_DIELECTRIC_SQL}
              AND 器件类型='MLCC'
            """
        )
        conn.commit()
        print(f"deleted={int(cursor.rowcount or 0)}")
    if args.sync_cache:
        removed_rows, search_removed, marked_rows = sync_cache_cleanup()
        print(f"prepared_cache_deleted={removed_rows}")
        print(f"search_sidecar_deleted={search_removed}")
        print(f"prepared_mlcc_authority_marked={marked_rows}")


if __name__ == "__main__":
    main()
