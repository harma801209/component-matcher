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
PUBLIC_RELEASE_STAMP = "2026-08-13T09:57:49+08:00"

# The public entrypoint must never spend startup time rebuilding data.
# Keep auto-update disabled unless a manual dev run opts back in explicitly.
os.environ["COMPONENT_MATCHER_PUBLIC_MODE"] = "1"
os.environ["COMPONENT_MATCHER_SKIP_AUTO_UPDATE"] = "1"
os.environ["COMPONENT_MATCHER_RELEASE_STAMP"] = PUBLIC_RELEASE_STAMP


if not hasattr(member_auth_runtime_state, "APP_CODE_LOCK"):
    member_auth_runtime_state.APP_CODE_LOCK = threading.Lock()
if not hasattr(member_auth_runtime_state, "APP_CODE_CACHE"):
    member_auth_runtime_state.APP_CODE_CACHE = {
        "key": None,
        "base_namespace": None,
        "page_shell_code": None,
        "app_code": None,
    }


def _source_segment_with_original_lines(source, start, end):
    return "\n" * source[:start].count("\n") + source[start:end]


def load_component_matcher_runtime():
    source_path = os.path.join(BASE_DIR, "component_matcher.py")
    cache_key = (source_path, PUBLIC_RELEASE_STAMP)
    with member_auth_runtime_state.APP_CODE_LOCK:
        cache = member_auth_runtime_state.APP_CODE_CACHE
        if (
            cache.get("key") == cache_key
            and cache.get("base_namespace") is not None
            and cache.get("page_shell_code") is not None
            and cache.get("app_code") is not None
        ):
            return cache, source_path
        with open(source_path, "r", encoding="utf-8") as source_file:
            source = source_file.read()

        page_shell_start = source.index("\nst.set_page_config(") + 1
        page_shell_end = source.index("\nBOM_NONE_OPTION =", page_shell_start) + 1
        app_start = source.index("\nrequire_app_access()\n", page_shell_end) + 1

        definitions_source = (
            source[:page_shell_start]
            + "\n" * source[page_shell_start:page_shell_end].count("\n")
            + source[page_shell_end:app_start]
        )
        page_shell_source = _source_segment_with_original_lines(
            source, page_shell_start, page_shell_end
        )
        app_source = _source_segment_with_original_lines(source, app_start, len(source))

        base_namespace = {
            "__name__": "component_matcher_runtime",
            "__file__": source_path,
            "__package__": None,
            "__cached__": None,
            "__loader__": None,
            "__spec__": None,
        }
        exec(compile(definitions_source, source_path, "exec"), base_namespace)
        cache.clear()
        cache.update(
            {
                "key": cache_key,
                "base_namespace": base_namespace,
                "page_shell_code": compile(page_shell_source, source_path, "exec"),
                "app_code": compile(app_source, source_path, "exec"),
            }
        )
        return cache, source_path


def run_component_matcher():
    runtime, _ = load_component_matcher_runtime()
    namespace = runtime["base_namespace"].copy()
    exec(runtime["page_shell_code"], namespace)
    exec(runtime["app_code"], namespace)

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
