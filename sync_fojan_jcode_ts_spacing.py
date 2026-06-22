from __future__ import annotations

import json
import os
import re
import sqlite3
import tempfile
from pathlib import Path

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq


ROOT = Path(__file__).resolve().parent
DB_PATH = ROOT / "components.db"
SEARCH_DB_PATH = ROOT / "cache" / "components_search.sqlite"
PREPARED_PATH = ROOT / "cache" / "components_prepared_v5.parquet"
META_PATH = ROOT / "cache" / "components_prepared_v5_meta.json"
REPORT_PATH = ROOT / "reports" / "fojan_jcode_ts_spacing_updates.csv"

MODEL_RE = re.compile(r"^(FR[A-Z]\d{4}J[0-9R]+)TS$", re.IGNORECASE)


def clean_text(value: object) -> str:
    text = str(value or "").strip()
    return "" if text.lower() in {"nan", "none"} else text


def clean_model(value: object) -> str:
    return clean_text(value).upper().replace(" ", "")


def spaced_fojan_jcode_model(value: object) -> str:
    text = clean_text(value)
    if " " in text:
        return text
    match = MODEL_RE.fullmatch(text.upper())
    if match is None:
        return text
    return f"{match.group(1)} TS"


def is_fojan_resistor_row(brand: object, component_type: object, model: object) -> bool:
    brand_text = clean_text(brand).upper()
    type_text = clean_text(component_type)
    model_text = clean_text(model)
    return (
        ("FOJAN" in brand_text or "富捷" in brand_text)
        and "电阻" in type_text
        and spaced_fojan_jcode_model(model_text) != model_text
    )


def replace_file_atomically(source_path: Path, target_path: Path) -> None:
    os.replace(source_path, target_path)


def update_components_db() -> pd.DataFrame:
    updated_rows: list[dict[str, object]] = []
    with sqlite3.connect(DB_PATH, timeout=60) as conn:
        conn.execute("PRAGMA busy_timeout = 60000")
        rows = conn.execute(
            """
            SELECT rowid, 品牌, 型号, 器件类型
            FROM components
            WHERE (品牌 LIKE '%富捷%' OR 品牌 LIKE '%FOJAN%')
              AND 器件类型 LIKE '%电阻%'
              AND 型号 LIKE '%J%TS'
              AND 型号 NOT LIKE '% %'
            """
        ).fetchall()
        for rowid, brand, model, component_type in rows:
            new_model = spaced_fojan_jcode_model(model)
            if new_model == clean_text(model):
                continue
            conn.execute("UPDATE components SET 型号 = ? WHERE rowid = ?", (new_model, int(rowid)))
            updated_rows.append(
                {
                    "source": "components.db",
                    "rowid": int(rowid),
                    "brand": clean_text(brand),
                    "component_type": clean_text(component_type),
                    "old_model": clean_text(model),
                    "new_model": new_model,
                }
            )
        conn.commit()
    return pd.DataFrame(updated_rows)


def update_search_sidecar() -> pd.DataFrame:
    if not SEARCH_DB_PATH.exists():
        return pd.DataFrame()
    updates: list[dict[str, object]] = []
    with sqlite3.connect(SEARCH_DB_PATH, timeout=60) as conn:
        conn.execute("PRAGMA busy_timeout = 60000")
        tables = [
            row[0]
            for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
        ]
        for table in tables:
            columns = [row[1] for row in conn.execute(f"PRAGMA table_info({table})").fetchall()]
            if not {"品牌", "型号"}.issubset(columns):
                continue
            component_column = "_component_type" if "_component_type" in columns else "器件类型" if "器件类型" in columns else ""
            select_component = f", {component_column}" if component_column else ", ''"
            rows = conn.execute(
                f"""
                SELECT rowid, 品牌, 型号{select_component}
                FROM {table}
                WHERE (品牌 LIKE '%富捷%' OR 品牌 LIKE '%FOJAN%')
                  AND 型号 LIKE '%J%TS'
                  AND 型号 NOT LIKE '% %'
                """
            ).fetchall()
            for rowid, brand, model, component_type in rows:
                if component_column and "电阻" not in clean_text(component_type):
                    continue
                new_model = spaced_fojan_jcode_model(model)
                if new_model == clean_text(model):
                    continue
                assignments = ["型号 = ?"]
                params: list[object] = [new_model]
                if "_model_clean" in columns:
                    assignments.append("_model_clean = ?")
                    params.append(clean_model(new_model))
                params.append(int(rowid))
                conn.execute(
                    f"UPDATE {table} SET {', '.join(assignments)} WHERE rowid = ?",
                    params,
                )
                updates.append(
                    {
                        "source": table,
                        "rowid": int(rowid),
                        "brand": clean_text(brand),
                        "component_type": clean_text(component_type),
                        "old_model": clean_text(model),
                        "new_model": new_model,
                    }
                )
        conn.commit()
    return pd.DataFrame(updates)


def update_prepared_cache(batch_size: int = 50_000) -> int:
    if not PREPARED_PATH.exists():
        return 0
    parquet_file = pq.ParquetFile(PREPARED_PATH)
    schema = parquet_file.schema_arrow
    fd, tmp_name = tempfile.mkstemp(
        prefix=f"{PREPARED_PATH.name}.fojan_spacing.",
        suffix=".tmp",
        dir=str(PREPARED_PATH.parent),
    )
    os.close(fd)
    tmp_path = Path(tmp_name)
    changed_rows = 0
    try:
        with pq.ParquetWriter(tmp_path, schema=schema, compression="snappy") as writer:
            for batch in parquet_file.iter_batches(batch_size=batch_size):
                frame = batch.to_pandas()
                if {"品牌", "型号", "器件类型"}.issubset(frame.columns):
                    mask = frame.apply(
                        lambda row: is_fojan_resistor_row(
                            row.get("品牌", ""),
                            row.get("器件类型", ""),
                            row.get("型号", ""),
                        ),
                        axis=1,
                    )
                    if mask.any():
                        changed_rows += int(mask.sum())
                        frame.loc[mask, "型号"] = frame.loc[mask, "型号"].map(spaced_fojan_jcode_model)
                        if "_model_clean" in frame.columns:
                            frame.loc[mask, "_model_clean"] = frame.loc[mask, "型号"].map(clean_model)
                writer.write_table(pa.Table.from_pandas(frame, schema=schema, preserve_index=False))
        parquet_file.close()
        replace_file_atomically(tmp_path, PREPARED_PATH)
    finally:
        if tmp_path.exists():
            tmp_path.unlink(missing_ok=True)

    meta = {}
    if META_PATH.exists():
        try:
            meta = json.loads(META_PATH.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            meta = {}
    if DB_PATH.exists():
        stat = DB_PATH.stat()
        meta.update(
            {
                "db_path": str(DB_PATH),
                "db_mtime": stat.st_mtime,
                "db_size": stat.st_size,
                "fojan_jcode_ts_spacing_synced_rows": int(changed_rows),
            }
        )
        if "cache_version" not in meta:
            meta["cache_version"] = 7
        META_PATH.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    return int(changed_rows)


def main() -> None:
    db_updates = update_components_db()
    sidecar_updates = update_search_sidecar()
    prepared_updates = update_prepared_cache()
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    report = pd.concat([db_updates, sidecar_updates], ignore_index=True)
    report.to_csv(REPORT_PATH, index=False, encoding="utf-8-sig")
    print(f"db_rows_updated={len(db_updates)}")
    print(f"search_sidecar_rows_updated={len(sidecar_updates)}")
    print(f"prepared_rows_updated={prepared_updates}")
    print(f"report_path={REPORT_PATH}")


if __name__ == "__main__":
    main()
