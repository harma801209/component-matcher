"""Streamlit Community Cloud entrypoint."""

import os
import runpy
import traceback

import streamlit as st


BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Public release nudge:
# Update this stamp when publishing public-facing changes so Streamlit Cloud
# rechecks the checkout. This does not change runtime behavior.
PUBLIC_RELEASE_STAMP = "2026-04-19T20:16:56+08:00"

try:
    runpy.run_path(os.path.join(BASE_DIR, "component_matcher.py"), run_name="__main__")
except Exception as exc:
    st.error("应用启动失败，请查看下方错误详情。")
    st.exception(exc)
    st.code(traceback.format_exc())
