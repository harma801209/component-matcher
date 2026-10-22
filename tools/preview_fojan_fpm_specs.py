"""Isolated search-result UI; no member, cost, report or catalogue writes."""
import os
import platform
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
def helpers(source_version):
    runtime = tempfile.mkdtemp(prefix='fojan-fpm-preview-')
    for key, name in [('MEMBER_AUTH_DB_PATH','members'),('COST_PRICE_DB_PATH','cost'),
                      ('NO_MATCH_REPORT_DB_PATH','reports'),('BOM_JOB_DB_PATH','bom')]:
        os.environ[key] = str(Path(runtime)/(name+'.sqlite'))
    os.environ.update(COMPONENT_MATCHER_BUILD_MODE='1',COMPONENT_MATCHER_STARTUP_MAINTENANCE='0',
                      MEMBER_AUTH_REMOTE_FORCE='0',RUNTIME_STORE_REMOTE_FORCE='0')
    path = ROOT/'component_matcher.py'
    # Load the real definitions, not the production startup/UI block. Build mode
    # prevents maintenance but intentionally does not suppress the public UI.
    source = path.read_text(encoding='utf-8').split('\nrequire_app_access()\n',1)[0]
    loaded = {'__name__':'isolated_fpm_preview','__file__':str(path)}
    exec(compile(source,str(path),'exec'),loaded)
    return loaded['clean_text'].__globals__


st.set_page_config(layout='wide')
app = helpers((ROOT/'component_matcher.py').stat().st_mtime_ns)
st.markdown(CSS, unsafe_allow_html=True)
st.title('富捷FPM规格补全验证')
st.caption('隔离数据库，只验证实际解析和正式表格渲染。')
text = st.text_area('请输入料号，可多行输入', 'FPM253WFR300TM')
if st.button('开始匹配'):
    st.session_state['fpm_preview_queries'] = text.splitlines()
for index, model in enumerate(st.session_state.get('fpm_preview_queries', [])):
    resolved = app['resolve_search_query_dataframe_and_spec'](model, get_full_search_df=lambda:pd.DataFrame())
    display = app['build_part_info_df'](resolved['query_df'], resolved['spec'], model)
    fragment = app['render_clickable_result_table'](display, wrap_iframe=False, show_official_status=False)
    app['render_no_alt_match_card'](
        header_html='<strong>匹配料号资料</strong>', table_fragment=fragment,
        query_text=model, mode='料号', part_info_df=display, instance_key=index)
