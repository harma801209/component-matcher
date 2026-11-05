"""One-shot, session-local BOM start intents, independent of widget rerenders."""
import secrets
import sqlite3
from contextlib import contextmanager, nullcontext
from concurrent.futures import FIRST_COMPLETED, Future, ThreadPoolExecutor, wait
from copy import deepcopy
from queue import SimpleQueue
from threading import Event

START_KEY = '_bom_match_start_intent'


def materialize_public_capacitor_index(conn):
    """Snapshot the exact public overlay once for indexed, task-local reads.

    Caller is exclusively the BOM read-only public-index initializer. Keep every
    row/column/duplicate as returned by the existing overlay, without decoding,
    changing qualification rules, storing prices or modifying the main file.
    """
    source = 'components_search_capacitor'
    target = 'bom_public_capacitor_snapshot'
    if conn.execute('SELECT 1 FROM temp.sqlite_master WHERE name=?', (target,)).fetchone():
        return
    view = conn.execute('SELECT type FROM temp.sqlite_master WHERE name=?', (source,)).fetchone()
    if not view or view[0] != 'view':
        return  # An ordinary already-indexed main table needs no snapshot.
    columns = [row[1] for row in conn.execute('PRAGMA table_info("components_search_capacitor")')]
    conn.execute(f'CREATE TEMP TABLE "{target}" AS SELECT * FROM "{source}"')
    for label, fields in (('identity', ('品牌','型号','_component_type')),
                          ('spec', ('_component_type','_size','_mat','_pf','_tol','_volt_num'))):
        present = [field for field in fields if field in columns]
        if present:
            quoted = ','.join('"'+field+'"' for field in present)
            conn.execute(f'CREATE INDEX "{target}_{label}" ON "{target}"({quoted})')
    conn.execute(f'DROP VIEW temp."{source}"')
    conn.execute(f'CREATE TEMP VIEW "{source}" AS SELECT * FROM temp."{target}"')


class _RowSearchConnection(sqlite3.Connection):
    """Public-index handle owned by one worker scope, not nested read helpers."""
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
    """Worker-thread-local lifetime; never cache prices or members.

    The BOM coordinator owns this scope for one worker in one task. Connections
    are opened lazily and released on that same thread, including interruption.
    """
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
def bounded_results(worker, items, max_workers, heartbeat, worker_scope=None):
    """Keep only active rows queued; a UI rerun must not drain an entire BOM.

    Results are consumed on the caller/UI thread. Refill only after its progress
    and checkpoint callbacks succeed. Running Python threads cannot be killed;
    at interruption at most max_workers rows finish, without new row dispatch.
    """
    executor = ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix='bom-match')
    inbox = SimpleQueue()
    stopping = Event()
    pending = set()
    items = iter(items)
    complete = False

    def lane():
        # A persistent lane keeps public SQL overlays on its own worker thread.
        # Only the coordinator supplies new rows, after callbacks succeed.
        with (worker_scope() if worker_scope is not None else nullcontext()):
            while not stopping.is_set():
                ticket = inbox.get()
                if ticket is None:
                    return
                future, item = ticket
                if stopping.is_set():
                    future.cancel()
                    return
                if future.set_running_or_notify_cancel():
                    try:
                        future.set_result(worker(*item))
                    except BaseException as exc:
                        future.set_exception(exc)

    lanes = []

    def submit_next():
        item = next(items, None)
        if item is not None:
            future = Future()
            pending.add(future)
            inbox.put((future, item))

    def results():
        nonlocal complete
        for _ in range(max_workers):
            submit_next()
        while pending:
            finished, _ = wait(pending | set(lanes), timeout=1.0, return_when=FIRST_COMPLETED)
            if not finished:
                heartbeat()
                continue
            for future in finished:
                if future in lanes:
                    future.result()  # Propagate scope/worker startup failures.
                    raise RuntimeError('BOM worker exited before task completion')
                pending.remove(future)
                yield future.result()
                submit_next()
        complete = True

    try:
        for _ in range(max_workers):
            lanes.append(executor.submit(lane))
        yield results()
    finally:
        stopping.set()
        for future in pending:
            future.cancel()
        for _ in range(max_workers):
            inbox.put(None)
        executor.shutdown(wait=complete, cancel_futures=True)
        if complete:
            for future in lanes:
                future.result()  # Cleanup must complete before normal return.


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
