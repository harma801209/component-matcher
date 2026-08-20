from __future__ import annotations

import json
import os
import secrets
import sqlite3
import threading
import time
import zlib
from contextlib import closing
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
BOM_JOB_DB_PATH = Path(
    os.getenv("BOM_JOB_DB_PATH", str(BASE_DIR / "cache" / "bom_jobs.sqlite"))
).expanduser().resolve()
BOM_JOB_RETENTION_SECONDS = int(os.getenv("BOM_JOB_RETENTION_SECONDS", str(72 * 60 * 60)))
_SCHEMA_LOCK = threading.Lock()
_SCHEMA_READY = set()


def _connect() -> sqlite3.Connection:
    BOM_JOB_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(BOM_JOB_DB_PATH), timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA busy_timeout=30000")
    conn.execute("PRAGMA journal_mode=WAL")
    ensure_schema(conn)
    return conn


def ensure_schema(conn: sqlite3.Connection | None = None) -> None:
    path_key = str(BOM_JOB_DB_PATH)
    if path_key in _SCHEMA_READY:
        return
    with _SCHEMA_LOCK:
        if path_key in _SCHEMA_READY:
            return
        owns_connection = conn is None
        if conn is None:
            BOM_JOB_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
            conn = sqlite3.connect(str(BOM_JOB_DB_PATH), timeout=30)
        try:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS bom_jobs (
                    job_id TEXT PRIMARY KEY,
                    member_key TEXT NOT NULL,
                    run_signature TEXT NOT NULL,
                    file_name TEXT NOT NULL DEFAULT '',
                    file_type TEXT NOT NULL DEFAULT '',
                    file_sha256 TEXT NOT NULL DEFAULT '',
                    file_bytes BLOB,
                    settings_json TEXT NOT NULL DEFAULT '{}',
                    mappings_json TEXT NOT NULL DEFAULT '{}',
                    checkpoint_blob BLOB,
                    status TEXT NOT NULL DEFAULT 'ready',
                    total_rows INTEGER NOT NULL DEFAULT 0,
                    processed_rows INTEGER NOT NULL DEFAULT 0,
                    unique_rows INTEGER NOT NULL DEFAULT 0,
                    error_text TEXT NOT NULL DEFAULT '',
                    created_at REAL NOT NULL,
                    updated_at REAL NOT NULL,
                    completed_at REAL NOT NULL DEFAULT 0
                );
                CREATE UNIQUE INDEX IF NOT EXISTS idx_bom_jobs_member_signature
                    ON bom_jobs(member_key, run_signature);
                CREATE INDEX IF NOT EXISTS idx_bom_jobs_updated_at
                    ON bom_jobs(updated_at DESC);
                CREATE TABLE IF NOT EXISTS runtime_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    metric_type TEXT NOT NULL,
                    duration_ms INTEGER NOT NULL DEFAULT 0,
                    total_rows INTEGER NOT NULL DEFAULT 0,
                    unique_rows INTEGER NOT NULL DEFAULT 0,
                    success_rows INTEGER NOT NULL DEFAULT 0,
                    warning_rows INTEGER NOT NULL DEFAULT 0,
                    failed_rows INTEGER NOT NULL DEFAULT 0,
                    metadata_json TEXT NOT NULL DEFAULT '{}',
                    created_at REAL NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_runtime_metrics_type_created
                    ON runtime_metrics(metric_type, created_at DESC);
                """
            )
            conn.commit()
            _SCHEMA_READY.add(path_key)
        finally:
            if owns_connection:
                conn.close()


def _json_default(value):
    if hasattr(value, "item"):
        try:
            return value.item()
        except Exception:
            pass
    if hasattr(value, "isoformat"):
        try:
            return value.isoformat()
        except Exception:
            pass
    return str(value)


def _encode_json(value) -> bytes:
    payload = json.dumps(value, ensure_ascii=False, separators=(",", ":"), default=_json_default)
    return zlib.compress(payload.encode("utf-8"), level=6)


def _decode_json(blob, default):
    if not blob:
        return default
    try:
        return json.loads(zlib.decompress(bytes(blob)).decode("utf-8"))
    except Exception:
        return default


def _decode_row(row) -> dict | None:
    if row is None:
        return None
    result = dict(row)
    result["settings"] = json.loads(result.pop("settings_json", "{}") or "{}")
    result["mappings"] = json.loads(result.pop("mappings_json", "{}") or "{}")
    result["checkpoint"] = _decode_json(result.pop("checkpoint_blob", None), {})
    return result


def cleanup_expired_jobs(now: float | None = None) -> int:
    current = float(now or time.time())
    cutoff = current - max(3600, BOM_JOB_RETENTION_SECONDS)
    with closing(_connect()) as conn:
        cursor = conn.execute("DELETE FROM bom_jobs WHERE updated_at < ?", (cutoff,))
        conn.execute("DELETE FROM runtime_metrics WHERE created_at < ?", (current - 30 * 86400,))
        conn.commit()
        return int(cursor.rowcount or 0)


def create_or_update_job(*, member_key: str, run_signature: str, file_name: str,
                         file_type: str, file_sha256: str, file_bytes: bytes,
                         settings: dict, mappings: dict, total_rows: int) -> dict:
    now = time.time()
    cleanup_expired_jobs(now)
    member_key = str(member_key or "").strip()
    run_signature = str(run_signature or "").strip()
    if not member_key or not run_signature:
        raise ValueError("member_key and run_signature are required")
    with closing(_connect()) as conn:
        row = conn.execute(
            "SELECT * FROM bom_jobs WHERE member_key=? AND run_signature=?",
            (member_key, run_signature),
        ).fetchone()
        if row is None:
            job_id = secrets.token_urlsafe(18)
            conn.execute(
                """
                INSERT INTO bom_jobs (
                    job_id, member_key, run_signature, file_name, file_type, file_sha256,
                    file_bytes, settings_json, mappings_json, status, total_rows,
                    processed_rows, unique_rows, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'ready', ?, 0, 0, ?, ?)
                """,
                (job_id, member_key, run_signature, str(file_name or ""),
                 str(file_type or ""), str(file_sha256 or ""),
                 sqlite3.Binary(bytes(file_bytes or b"")),
                 json.dumps(settings or {}, ensure_ascii=False, default=_json_default),
                 json.dumps(mappings or {}, ensure_ascii=False, default=_json_default),
                 int(total_rows or 0), now, now),
            )
        else:
            job_id = row["job_id"]
            conn.execute(
                """
                UPDATE bom_jobs SET file_name=?, file_type=?, file_sha256=?, file_bytes=?,
                    settings_json=?, mappings_json=?, total_rows=?, updated_at=? WHERE job_id=?
                """,
                (str(file_name or ""), str(file_type or ""), str(file_sha256 or ""),
                 sqlite3.Binary(bytes(file_bytes or b"")),
                 json.dumps(settings or {}, ensure_ascii=False, default=_json_default),
                 json.dumps(mappings or {}, ensure_ascii=False, default=_json_default),
                 int(total_rows or 0), now, job_id),
            )
        conn.commit()
    return get_job(job_id, member_key=member_key)


def get_job(job_id: str, *, member_key: str | None = None) -> dict | None:
    job_id = str(job_id or "").strip()
    if not job_id:
        return None
    with closing(_connect()) as conn:
        if member_key is None:
            row = conn.execute("SELECT * FROM bom_jobs WHERE job_id=?", (job_id,)).fetchone()
        else:
            row = conn.execute(
                "SELECT * FROM bom_jobs WHERE job_id=? AND member_key=?",
                (job_id, str(member_key or "").strip()),
            ).fetchone()
    return _decode_row(row)


def save_checkpoint(job_id: str, checkpoint: dict, *, processed_rows: int,
                    unique_rows: int = 0, status: str = "running",
                    error_text: str = "") -> None:
    now = time.time()
    with closing(_connect()) as conn:
        conn.execute(
            """
            UPDATE bom_jobs SET checkpoint_blob=?, processed_rows=?, unique_rows=?, status=?,
                error_text=?, updated_at=?, completed_at=? WHERE job_id=?
            """,
            (sqlite3.Binary(_encode_json(checkpoint or {})), int(processed_rows or 0),
             int(unique_rows or 0), str(status or "running"), str(error_text or "")[:2000],
             now, now if status == "complete" else 0, str(job_id or "")),
        )
        conn.commit()


def reset_failed_rows(job_id: str, *, member_key: str,
                      retry_statuses: set[str] | None = None) -> dict:
    retry_statuses = retry_statuses or {"解析失败", "无匹配"}
    job = get_job(job_id, member_key=member_key)
    if not job:
        return {}
    checkpoint = job.get("checkpoint") or {}
    sheet_rows = checkpoint.get("sheet_rows", checkpoint)
    kept = {}
    for sheet_name, rows in (sheet_rows or {}).items():
        kept[str(sheet_name)] = {
            str(row_index): row for row_index, row in (rows or {}).items()
            if str((row or {}).get("状态", "")).strip() not in retry_statuses
        }
    payload = {"sheet_rows": kept}
    save_checkpoint(job_id, payload, processed_rows=sum(len(rows) for rows in kept.values()), status="ready")
    return payload


def record_metric(metric_type: str, *, duration_ms: int, total_rows: int = 0,
                  unique_rows: int = 0, success_rows: int = 0,
                  warning_rows: int = 0, failed_rows: int = 0,
                  metadata: dict | None = None) -> None:
    with closing(_connect()) as conn:
        conn.execute(
            """
            INSERT INTO runtime_metrics (metric_type, duration_ms, total_rows, unique_rows,
                success_rows, warning_rows, failed_rows, metadata_json, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (str(metric_type or ""), max(0, int(duration_ms or 0)),
             max(0, int(total_rows or 0)), max(0, int(unique_rows or 0)),
             max(0, int(success_rows or 0)), max(0, int(warning_rows or 0)),
             max(0, int(failed_rows or 0)),
             json.dumps(metadata or {}, ensure_ascii=False, default=_json_default), time.time()),
        )
        conn.commit()


def metric_summary(metric_type: str, limit: int = 100) -> dict:
    with closing(_connect()) as conn:
        rows = conn.execute(
            """SELECT duration_ms, total_rows, unique_rows, success_rows, warning_rows,
                      failed_rows, created_at FROM runtime_metrics WHERE metric_type=?
               ORDER BY created_at DESC LIMIT ?""",
            (str(metric_type or ""), max(1, min(int(limit or 100), 1000))),
        ).fetchall()
    empty = {"runs": 0, "p50_ms": 0, "p95_ms": 0, "rows_per_second": 0.0,
             "dedupe_rate": 0.0, "failed_rows": 0}
    if not rows:
        return empty
    durations = sorted(int(row["duration_ms"] or 0) for row in rows)
    def percentile(fraction: float) -> int:
        index = min(len(durations) - 1, max(0, int(round((len(durations) - 1) * fraction))))
        return durations[index]
    total_rows = sum(int(row["total_rows"] or 0) for row in rows)
    unique_rows = sum(int(row["unique_rows"] or 0) for row in rows)
    duration_seconds = sum(int(row["duration_ms"] or 0) for row in rows) / 1000.0
    return {"runs": len(rows), "p50_ms": percentile(0.50), "p95_ms": percentile(0.95),
            "rows_per_second": total_rows / duration_seconds if duration_seconds > 0 else 0.0,
            "dedupe_rate": 1.0 - unique_rows / total_rows if total_rows > 0 else 0.0,
            "failed_rows": sum(int(row["failed_rows"] or 0) for row in rows)}
