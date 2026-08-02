"""Process-wide member-auth synchronization state shared across Streamlit reruns."""

import secrets
import threading


REMOTE_LOCK = threading.Lock()
REFRESH_LOCK = threading.Lock()
REFRESH_CACHE = {"checked_at": 0.0, "db_path": ""}
FLUSH_CONDITION = threading.Condition(threading.Lock())
FLUSH_STATE = {
    "generation": 0,
    "running": False,
    "last_result": None,
}

SCHEMA_LOCK = threading.RLock()
SCHEMA_READY_PATHS = set()

PASSWORD_CACHE_LOCK = threading.Lock()
PASSWORD_CACHE_SECRET = secrets.token_bytes(32)
PASSWORD_CACHE = {}

APP_CODE_LOCK = threading.Lock()
APP_CODE_CACHE = {"key": None, "code": None}
