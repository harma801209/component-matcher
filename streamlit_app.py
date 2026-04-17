"""Streamlit Community Cloud entrypoint."""

import os
import runpy
import traceback

import streamlit as st


BASE_DIR = os.path.dirname(os.path.abspath(__file__))

try:
    runpy.run_path(os.path.join(BASE_DIR, "component_matcher.py"), run_name="__main__")
except Exception as exc:
    st.set_page_config(page_title="富临通元器件匹配系统", page_icon="📦", layout="wide")
    st.error("应用启动失败，请查看下方错误详情。")
    st.exception(exc)
    st.code(traceback.format_exc())
