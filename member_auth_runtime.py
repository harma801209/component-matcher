"""Process-wide member-auth synchronization state shared across Streamlit reruns."""

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
