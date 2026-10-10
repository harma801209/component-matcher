"""Isolated UI fixture; report clicks are captured, never saved to business data."""
import os
import platform
import runpy
import sys
import tempfile
from pathlib import Path

platform._wmi = None
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import pandas as pd
import streamlit as st
from precision_theme import CSS


@st.cache_resource
def preview_helpers():
    runtime = tempfile.mkdtemp(prefix="no-alt-card-preview-")
    for key, name in [("MEMBER_AUTH_DB_PATH", "members"), ("COST_PRICE_DB_PATH", "cost"),
                      ("NO_MATCH_REPORT_DB_PATH", "reports"), ("BOM_JOB_DB_PATH", "bom")]:
        os.environ[key] = str(Path(runtime) / (name + ".sqlite"))
    os.environ["COMPONENT_MATCHER_BUILD_MODE"] = "1"
    os.environ["COMPONENT_MATCHER_STARTUP_MAINTENANCE"] = "0"
    os.environ["MEMBER_AUTH_REMOTE_FORCE"] = "0"
    os.environ["RUNTIME_STORE_REMOTE_FORCE"] = "0"
    loaded = runpy.run_path(str(ROOT / "component_matcher.py"), run_name="isolated_card_preview")
    app = loaded["clean_text"].__globals__
    # Preserve the native callback wiring, but never submit the QA fixture report.
    def capture(payload):
        st.session_state["preview_report"] = payload["query_text"]
    app["submit_no_match_report_payload"] = capture
    return app


st.set_page_config(layout="wide")
app = preview_helpers()
st.markdown(CSS, unsafe_allow_html=True)
st.title("型号结果分组验证")
st.caption("只读演示；回报按钮只验证型号关联，不写入数据库。")
if st.session_state.get("preview_report"):
    st.success("已点击：" + st.session_state["preview_report"])
for index, model in enumerate(["FRQ0603F33R0TS", "FRQ0603F1002TS", "FRQ0603F33R0TS"], 1):
    frame = pd.DataFrame([{
        "品牌": "FOJAN(富捷)", "型号": model,
        "器件类别": "厚膜电阻（Thick Film Resistor）", "系列": "FRQ",
        "系列说明": "车规级厚膜贴片电阻", "尺寸（公制）": "1608",
        "尺寸（英制）": "0603", "参数值": "33" if "33R0" in model else "10",
        "参数单位": "Ω" if "33R0" in model else "KΩ",
    }])
    fragment = app["render_clickable_result_table"](frame, wrap_iframe=False, show_official_status=False)
    app["render_no_alt_match_card"](
        header_html='<div style="display:flex;align-items:center;gap:10px;">'
                    '<strong style="font-size:20px;">匹配料号资料</strong>'
                    f'<span class="match-card-query-pill">{model}</span></div>',
        table_fragment=fragment, query_text=model, mode="料号",
        part_info_df=frame, instance_key=index,
    )
