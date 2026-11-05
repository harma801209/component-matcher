"""One-shot, session-local BOM start intents, independent of widget rerenders."""
import secrets
import sqlite3
from contextlib import contextmanager
from concurrent.futures import FIRST_COMPLETED, ThreadPoolExecutor, wait
from copy import deepcopy

START_KEY = '_bom_match_start_intent'


class _RowSearchConnection(sqlite3.Connection):
    """Public-index handle owned by one row, not by each nested read helper."""
    def close(self):
        if not getattr(self, '_row_owns_connection', False):
            super().close()

    def release(self):
        self._row_owns_connection = False
        super().close()


def lease_public_search_connection(pool, key, connect, initialize):
    if key in pool:
        return pool[key]
    conn = connect(factory=_RowSearchConnection)
    try:
        initialize(conn)
    except BaseException:
        conn.close()
        raise
    conn._row_owns_connection = True
    pool[key] = conn
    return conn


@contextmanager
def search_connection_scope(state):
    """Worker-thread-local, row-local lifetime; never cache prices or members."""
    missing = object()
    previous = getattr(state, 'connections', missing)
    owned = {}
    state.connections = owned
    try:
        yield
    finally:
        try:
            for conn in owned.values():
                conn.release()
        finally:
            if previous is missing:
                delattr(state, 'connections')
            else:
                state.connections = previous


@contextmanager
def bounded_results(worker, items, max_workers, heartbeat):
    """Keep only active rows queued; a UI rerun must not drain an entire BOM.

    Results are consumed on the caller/UI thread. Refill only after its progress
    and checkpoint callbacks succeed. Running Python threads cannot be killed;
    at interruption at most max_workers rows finish, without new row dispatch.
    """
    executor = ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix='bom-match')
    pending = set()
    items = iter(items)

    def submit_next():
        item = next(items, None)
        if item is not None:
            pending.add(executor.submit(worker, *item))

    def results():
        for _ in range(max_workers):
            submit_next()
        while pending:
            finished, _ = wait(pending, timeout=1.0, return_when=FIRST_COMPLETED)
            if not finished:
                heartbeat()
                continue
            for future in finished:
                pending.remove(future)
                yield future.result()
                submit_next()

    try:
        yield results()
    finally:
        for future in pending:
            future.cancel()
        executor.shutdown(wait=False, cancel_futures=True)


def queue_start(state, workbook_signature, export_mode):
    state[START_KEY] = {'workbook': str(workbook_signature), 'mode': str(export_mode),
                        'nonce': secrets.token_urlsafe(18)}


def consume_start(state, workbook_signature, export_mode):
    intent = state.pop(START_KEY, None)
    return bool(isinstance(intent, dict) and intent.get('nonce')
                and intent.get('workbook') == str(workbook_signature)
                and intent.get('mode') == str(export_mode))


def completed_rows(job, run_signature, sheet_lengths, member_key):
    """Recover complete rows, never run a matcher or reuse another price scope."""
    if (not isinstance(job, dict) or job.get('status') != 'complete'
            or not member_key or job.get('member_key') != member_key
            or job.get('run_signature') != run_signature or not sheet_lengths):
        return None
    total = sum(sheet_lengths.values())
    if total <= 0 or job.get('total_rows') != total or job.get('processed_rows') != total:
        return None
    checkpoint = job.get('checkpoint')
    if not isinstance(checkpoint, dict):
        return None
    sheets = checkpoint.get('sheet_rows')
    if not isinstance(sheets, dict) or set(sheets) != set(sheet_lengths):
        return None
    restored = {}
    for name, length in sheet_lengths.items():
        rows = sheets[name]
        if not isinstance(rows, dict) or len(rows) != length:
            return None
        keys = [str(key) for key in rows]
        if len(set(keys)) != length or set(keys) != {str(i) for i in range(length)}:
            return None
        rows = {str(key): value for key, value in rows.items()}
        ordered = [rows[str(i)] for i in range(length)]
        if any(not isinstance(row, dict) or not row.get('状态')
               or str(row.get('BOM行号', '')) != str(i + 2) for i, row in enumerate(ordered)):
            return None
        restored[name] = deepcopy(ordered)
    return restored
