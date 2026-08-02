"""Streamlit Community Cloud entrypoint."""

import os
import threading
import traceback

import streamlit as st
from streamlit.runtime.scriptrunner_utils.exceptions import RerunException, StopException
import member_auth_runtime as member_auth_runtime_state


BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Public release nudge:
# Update this stamp when publishing public-facing changes so Streamlit Cloud
# rechecks the checkout. This does not change runtime behavior.
# The sync script may refresh this automatically when the public bundle is rebuilt.
PUBLIC_RELEASE_STAMP = "2026-08-02T13:18:00+08:00"

# The public entrypoint must never spend startup time rebuilding data.
# Keep auto-update disabled unless a manual dev run opts back in explicitly.
os.environ["COMPONENT_MATCHER_PUBLIC_MODE"] = "1"
os.environ["COMPONENT_MATCHER_SKIP_AUTO_UPDATE"] = "1"
os.environ["COMPONENT_MATCHER_RELEASE_STAMP"] = PUBLIC_RELEASE_STAMP


if not hasattr(member_auth_runtime_state, "APP_CODE_LOCK"):
    member_auth_runtime_state.APP_CODE_LOCK = threading.Lock()
if not hasattr(member_auth_runtime_state, "APP_CODE_CACHE"):
    member_auth_runtime_state.APP_CODE_CACHE = {"key": None, "code": None}


def load_compiled_component_matcher():
    source_path = os.path.join(BASE_DIR, "component_matcher.py")
    cache_key = (source_path, PUBLIC_RELEASE_STAMP)
    with member_auth_runtime_state.APP_CODE_LOCK:
        cache = member_auth_runtime_state.APP_CODE_CACHE
        if cache.get("key") == cache_key and cache.get("code") is not None:
            return cache["code"], source_path
        with open(source_path, "r", encoding="utf-8") as source_file:
            compiled_code = compile(source_file.read(), source_path, "exec")
        cache["key"] = cache_key
        cache["code"] = compiled_code
        return compiled_code, source_path


def run_component_matcher():
    compiled_code, source_path = load_compiled_component_matcher()
    namespace = {
        "__name__": "__main__",
        "__file__": source_path,
        "__package__": None,
        "__cached__": None,
        "__loader__": None,
        "__spec__": None,
    }
    exec(compiled_code, namespace)

try:
    run_component_matcher()
except (StopException, RerunException):
    raise
except Exception as exc:
    st.error("应用启动失败，请查看下方错误详情。")
    st.exception(exc)
    st.code(traceback.format_exc())
except BaseException as exc:
    st.error("应用启动被意外终止，请查看下方错误详情。")
    st.exception(exc)
    st.code(traceback.format_exc())
