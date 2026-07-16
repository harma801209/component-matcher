from __future__ import annotations

import json
import os
import sqlite3
import tempfile
import importlib
from pathlib import Path

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

import component_matcher as cm


ROOT = Path(__file__).resolve().parent
SEED_MODULE_NAMES = [
    "sync_semiconductor_seed",
    "sync_passive_gap_seed",
]


def clean_model_key(value: object) -> str:
    return str(value or "").upper().replace("-", "").replace(" ", "").replace("_", "")


def iter_seed_rows() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for module_name in SEED_MODULE_NAMES:
        module = importlib.import_module(module_name)
        rows.extend(getattr(module, "SEED_ROWS", []))
    return rows


def seed_brand_model_pairs() -> list[tuple[str, str, str]]:
    pairs: list[tuple[str, str, str]] = []
    seen: set[tuple[str, str]] = set()
    for row in iter_seed_rows():
        brand = str(row.get("品牌", "") or "").strip()
        model = str(row.get("型号", "") or "").strip()
        if not brand or not model:
            continue
        key = (brand, model)
        if key in seen:
            continue
        seen.add(key)
        pairs.append((brand, model, clean_model_key(model)))
    return pairs


def load_seed_rows_from_database() -> pd.DataFrame:
    pairs = seed_brand_model_pairs()
    if not pairs:
        raise RuntimeError("no seed rows configured")

    clauses = []
    params: list[str] = []
    for brand, model, _clean in pairs:
        clauses.append("([品牌] = ? AND [型号] = ?)")
        params.extend([brand, model])
    sql = f"SELECT * FROM components WHERE {' OR '.join(clauses)}"

    with sqlite3.connect(cm.DB_PATH) as conn:
        frame = pd.read_sql_query(sql, conn, params=params)
    if frame.empty:
        raise RuntimeError("no seed rows found in components.db")
    return cm.deduplicate_component_rows(frame)


def make_prepared_key(frame: pd.DataFrame) -> pd.Series:
    brand = frame["品牌"].astype("string").fillna("").str.strip()
    if "_model_clean" in frame.columns:
        model_clean = frame["_model_clean"].astype("string").fillna("").str.strip()
    else:
        model_clean = frame["型号"].map(clean_model_key).astype("string")
    return brand + "\0" + model_clean


def normalize_prepared_dtypes(frame: pd.DataFrame) -> pd.DataFrame:
    stable_float_columns = [
        "容值_pf",
        "_resistance_ohm",
        "_pf",
        "_tol_num",
        "_volt_num",
        "_res_ohm",
        "_power_watt",
    ]
    normalized = frame.copy()
    for col in stable_float_columns:
        if col in normalized.columns:
            normalized[col] = pd.to_numeric(normalized[col], errors="coerce").astype("float64")
    string_columns = [col for col in normalized.columns if col not in stable_float_columns]
    for col in string_columns:
        normalized[col] = normalized[col].astype("string")
    return normalized


def coerce_frame_to_schema(frame: pd.DataFrame, schema: pa.Schema) -> pd.DataFrame:
    normalized = frame.reindex(columns=schema.names, fill_value="").copy()
    for field in schema:
        column = field.name
        if pa.types.is_integer(field.type) or pa.types.is_floating(field.type):
            normalized[column] = pd.to_numeric(normalized[column], errors="coerce")
        elif pa.types.is_boolean(field.type):
            normalized[column] = normalized[column].map(
                lambda value: None
                if str(value or "").strip() == ""
                else str(value).strip().lower() in {"1", "true", "yes", "y"}
            )
        else:
            normalized[column] = normalized[column].astype("string").fillna("")
    return normalized


def replace_prepared_cache_rows(seed_prepared: pd.DataFrame, batch_size: int = 50_000) -> int:
    prepared_path = Path(cm.PREPARED_CACHE_PATH)
    meta_path = Path(cm.PREPARED_CACHE_META_PATH)
    if not prepared_path.exists():
        raise FileNotFoundError(prepared_path)
    if seed_prepared is None or seed_prepared.empty:
        return 0

    parquet_file = pq.ParquetFile(prepared_path)
    schema = parquet_file.schema_arrow
    seed_prepared = coerce_frame_to_schema(seed_prepared, schema)
    remove_keys = set(make_prepared_key(seed_prepared).astype(str))

    tmp_dir = prepared_path.parent
    fd, tmp_name = tempfile.mkstemp(
        prefix=f"{prepared_path.name}.incremental.",
        suffix=".tmp",
        dir=str(tmp_dir),
    )
    os.close(fd)
    tmp_path = Path(tmp_name)
    try:
        with pq.ParquetWriter(tmp_path, schema=schema, compression="snappy") as writer:
            for batch in parquet_file.iter_batches(batch_size=int(batch_size)):
                frame = batch.to_pandas()
                keep_mask = ~make_prepared_key(frame).astype(str).isin(remove_keys)
                kept = frame.loc[keep_mask].copy()
                if not kept.empty:
                    writer.write_table(
                        pa.Table.from_pandas(
                            coerce_frame_to_schema(kept, schema),
                            schema=schema,
                            preserve_index=False,
                        )
                    )
            writer.write_table(
                pa.Table.from_pandas(
                    seed_prepared,
                    schema=schema,
                    preserve_index=False,
                )
            )
        parquet_file.close()
        cm.replace_file_atomically(str(tmp_path), str(prepared_path))
    finally:
        try:
            parquet_file.close()
        except Exception:
            pass
        if tmp_path.exists():
            tmp_path.unlink(missing_ok=True)

    tmp_meta = meta_path.with_suffix(meta_path.suffix + ".incremental.tmp")
    tmp_meta.write_text(
        json.dumps(cm.get_database_signature(), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    cm.replace_file_atomically(str(tmp_meta), str(meta_path))
    return int(len(seed_prepared))


def refresh_search_sidecar_rows(seed_prepared: pd.DataFrame) -> dict[str, int]:
    search_path = Path(cm.SEARCH_DB_PATH)
    if not search_path.exists():
        raise FileNotFoundError(search_path)

    frames = cm.build_search_sidecar_frames(seed_prepared)
    if not frames:
        raise RuntimeError("no search sidecar frames generated")

    specs = cm.get_search_sidecar_table_specs()
    pairs = seed_prepared.loc[:, ["品牌", "型号"]].drop_duplicates()
    with sqlite3.connect(search_path, timeout=60) as conn:
        conn.execute("PRAGMA busy_timeout = 60000")
        for table_name, spec in specs.items():
            existing_columns = {
                str(row[1])
                for row in conn.execute(f'PRAGMA table_info("{table_name}")').fetchall()
            }
            numeric_columns = set(spec.get("numeric", []))
            for column in spec.get("columns", []):
                if column in existing_columns:
                    continue
                sql_type = "REAL" if column in numeric_columns else "TEXT"
                escaped_column = str(column).replace('"', '""')
                conn.execute(
                    f'ALTER TABLE "{table_name}" ADD COLUMN "{escaped_column}" {sql_type}'
                )
        for table_name, spec in specs.items():
            columns = set(spec.get("columns", []))
            if not {"品牌", "型号"}.issubset(columns):
                continue
            try:
                for row in pairs.itertuples(index=False):
                    conn.execute(
                        f'DELETE FROM {table_name} WHERE [品牌] = ? AND [型号] = ?',
                        (str(row.品牌), str(row.型号)),
                    )
            except sqlite3.OperationalError:
                continue

        for table_name, frame in frames.items():
            if frame is None or frame.empty:
                continue
            frame.to_sql(
                table_name,
                conn,
                if_exists="append",
                index=False,
                method="multi",
                chunksize=cm.sqlite_bulk_insert_chunksize(frame),
            )

        row_counts: dict[str, int] = {}
        for table_name in specs:
            try:
                row_counts[table_name] = int(conn.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0])
            except Exception:
                row_counts[table_name] = 0
        cm.write_search_index_meta(conn, row_counts)
    return row_counts


def main() -> None:
    seed_rows = load_seed_rows_from_database()
    seed_prepared = cm.prepare_search_dataframe(seed_rows)
    if seed_prepared.empty:
        raise RuntimeError("prepared seed rows are empty")
    replaced = replace_prepared_cache_rows(seed_prepared)
    row_counts = refresh_search_sidecar_rows(seed_prepared)
    print(f"incremental_seed_rows={len(seed_rows)}")
    print(f"prepared_rows_replaced={replaced}")
    print(f"search_core_rows={row_counts.get(cm.COMPONENTS_SEARCH_CORE_TABLE, 0)}")


if __name__ == "__main__":
    main()
