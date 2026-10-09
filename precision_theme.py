"""Option 1: readable light surfaces and a precision-blue navigation rail."""
import html

PALETTE = {
    "backgroundColor": "#f4f7fc", "secondaryBackgroundColor": "#ffffff",
    "textColor": "#172b4d", "primaryColor": "#1555e8",
}

TABLE_CSS = """
<style>
html,body {background:#fff!important;color:#172b4d!important;color-scheme:light;}
body,input,button {font-family:"Segoe UI","Microsoft YaHei",sans-serif;}
.section-title,.result-title,.match-card-head {color:#172b4d!important;}
.result-section-card {background:#fff!important;border:1px solid #d4dfed!important;border-radius:10px!important;box-shadow:none!important;padding:0!important;}
.result-table {background:#fff!important;color:#172b4d!important;font-size:14px!important;}
.result-table th {background:#f0f4fa!important;color:#30496e!important;font-weight:700!important;box-shadow:0 1px 0 #d4dfed!important;}
.result-table th,.result-table td {border-color:#dce4ef!important;padding:8px 10px!important;font-size:14px!important;line-height:1.5!important;white-space:normal;overflow:visible;text-overflow:clip;}
.result-table td {color:#172b4d!important;}
.result-table tr:nth-child(even) td {background:#f8faff;}
.result-table tr.exact-match td {background:#eaf8f1!important;color:#096443!important;}
.result-table tr.partial-match-row td,.result-table tr.parse-fail-row td {background:#fff0f1!important;color:#942b3b!important;}
.result-table tr.substitute-row td {background:#edf4ff!important;color:#204d94!important;}
.result-table tr.warn-row td {background:#fff7e3!important;color:#825313!important;}
.result-table td.param-hit {color:#a62432!important;font-weight:600;}
.match-card-footer {background:#f4f7fc!important;border-color:#d4dfed!important;color:#30496e!important;}
.result-table tbody tr:hover td {background:#eaf2ff!important;}
a,summary,.copyable-model {color:#154fc8!important;}
.copyable-model {white-space:nowrap;}
.bom-result-table-wrap {max-height:min(560px,calc(100vh - 24px))!important;overflow:auto!important;overscroll-behavior:contain;}
button,.bom-download-btn {background:#fff!important;color:#1a4d9b!important;border-color:#bbcde5!important;}
input {background:#fff!important;color:#172b4d!important;}
::-webkit-scrollbar {width:12px;height:12px;}
::-webkit-scrollbar-track {background:#f0f4fa;}
::-webkit-scrollbar-thumb {background:#8095b1;border:2px solid #f0f4fa;border-radius:6px;}
*:focus-visible {outline:3px solid #1555e8;outline-offset:2px;}
</style>
"""

CSS = """
<style>
:root {color-scheme:light;--wb-bg:#f4f7fc;--wb-panel:#fff;--wb-line:#d9e3ef;--wb-text:#172b4d;--wb-muted:#4d6384;--wb-blue:#1555e8;--wb-header-height:52px;}
.stApp,[data-testid="stAppViewContainer"],[data-testid="stMain"] {background:var(--wb-bg)!important;color:var(--wb-text)!important;}
[data-testid="stElementContainer"]:has([data-testid="stMarkdownContainer"] > style:only-child),[data-testid="stElementContainer"]:has(> iframe[height="0"]) {display:none!important;}
body,input,textarea,button {font-family:"Segoe UI","Microsoft YaHei",sans-serif;}
.block-container,[data-testid="stMainBlockContainer"] {max-width:none!important;width:calc(100% - 150px)!important;margin-left:150px!important;padding:1rem 1.5rem 2rem!important;}
.wb-sidebar {position:fixed;left:0;top:0;bottom:0;width:150px;background:#193253;z-index:1000;padding-top:0;border-right:1px solid #294463;}
.wb-nav {display:flex;flex-direction:column;gap:8px;}
.wb-nav a {display:flex;align-items:center;gap:8px;padding:14px 10px;color:#d4dfef;text-decoration:none;white-space:nowrap;font-size:15px;font-weight:600;border-left:3px solid transparent;}
.wb-nav a:hover,.wb-nav a:focus-visible {background:#1555e8;color:#fff;border-left-color:#75a9ff;}
.wb-nav-icon {width:22px;height:22px;flex:none;display:block;}
.wb-header {display:flex;align-items:center;gap:14px;height:var(--wb-header-height);min-height:var(--wb-header-height);box-sizing:border-box;background:#fff;border-bottom:1px solid var(--wb-line);margin:-2rem -1.5rem 20px;padding:2px 20px;}
.wb-logo {width:112px;height:46px;object-fit:contain;}
.wb-brand {font-size:19px;font-weight:750;color:#172b4d;border-left:1px solid #cdd9e8;padding-left:16px;white-space:nowrap;}
.wb-badge {font-size:12px;white-space:nowrap;border-radius:15px;padding:5px 11px;color:#1555e8;background:#e8efff;font-weight:650;}
.wb-user {color:#30496e;font-size:15px;margin-left:auto;white-space:nowrap;}
.wb-account {margin-left:auto;display:flex;align-items:center;gap:10px;white-space:nowrap;}
.wb-account a {text-decoration:none;}
.wb-account .wb-user {margin-left:0;}
.wb-login-button {display:inline-flex;align-items:center;justify-content:center;gap:7px;min-height:38px;padding:7px 15px;background:#1555e8;color:#fff!important;border:1px solid #1555e8;border-radius:7px;font-size:14px;font-weight:600;}
.wb-login-button:hover {background:#1046c4;border-color:#1046c4;}
.wb-user-link {display:inline-flex;align-items:center;justify-content:center;min-height:36px;padding:6px 14px;border:1px solid #cbdcf6;border-radius:999px;background:#e8efff;color:#1555e8!important;font-weight:600;line-height:1.5;box-sizing:border-box;}
.wb-user-link:hover {background:#dce8ff;border-color:#abc4ed;text-decoration:none;}
.wb-title {font-size:25px;font-weight:750;color:#172b4d;margin:0 0 6px;}
.wb-subtitle {color:#4d6384;font-size:14px;line-height:1.55;margin:0 0 14px;}
.wb-test-note {font-size:13px;color:#4d6384;margin:0 0 18px;}
.st-key-workbench-search-panel {background:#fff;border:1px solid #d9e3ef;border-radius:10px;padding:18px 20px;margin-bottom:16px;}
.st-key-workbench-search-panel [data-testid="stButton"] button[kind="primary"] {min-height:42px!important;width:150px!important;}
.main-title,.result-title,.section-title {color:#172b4d!important;font-weight:700!important;}
.sub-title,.sub-title-2 {color:#4d6384!important;}
[data-testid="stMarkdownContainer"] p,[data-testid="stWidgetLabel"] p {color:inherit;font-size:14px;line-height:1.55;}
[data-testid="stWidgetLabel"] p {font-weight:600;}
[data-testid="stCaptionContainer"] {color:#4d6384!important;font-size:13px!important;line-height:1.5!important;}
[data-testid="stCaptionContainer"] p {color:#4d6384!important;}
[data-baseweb="select"]>div,[data-baseweb="input"]>div,[data-baseweb="textarea"],textarea {background:#fff!important;color:#172b4d!important;border-color:#b8c9df!important;border-radius:7px!important;}
[data-testid="stTextArea"] textarea {font-family:"Segoe UI","Microsoft YaHei",sans-serif;font-size:15px!important;line-height:1.6!important;padding:12px!important;}
/* Keep the two search controls consistent across old and new widget markup. */
.st-key-workbench-search-panel [data-testid="stSelectbox"] [role="group"]:has([role="combobox"]),
.st-key-workbench-search-panel [data-testid="stSelectbox"] [data-baseweb="select"]>div,
.st-key-workbench-search-panel [data-testid="stTextAreaRootElement"] {border:1px solid #b8c9df!important;border-radius:7px!important;background:#fff!important;box-sizing:border-box!important;}
.st-key-workbench-search-panel [data-testid="stSelectbox"] [role="group"]:has([role="combobox"]):focus-within,
.st-key-workbench-search-panel [data-testid="stSelectbox"] [data-baseweb="select"]>div:focus-within,
.st-key-workbench-search-panel [data-testid="stTextAreaRootElement"]:focus-within {border-color:#1555e8!important;}
.st-key-workbench-search-panel [data-testid="stSelectbox"] [role="combobox"] {font-family:"Source Sans",sans-serif!important;font-size:16px!important;font-weight:400!important;line-height:1.4!important;}
[data-testid="stButton"] button,[data-testid="stDownloadButton"] button,[data-testid="stFormSubmitButton"] button {background:#fff!important;color:#244469!important;border:1px solid #b8c9df!important;border-radius:7px!important;min-height:44px!important;font-weight:600!important;}
[data-testid="stButton"] button:hover,[data-testid="stDownloadButton"] button:hover {background:#edf4ff!important;border-color:#1555e8!important;}
[data-testid="stButton"] button[kind="primary"],[data-testid="stFormSubmitButton"] button[kind="primary"] {background:#1555e8!important;color:#fff!important;border-color:#1555e8!important;}
[data-testid="stButton"] button:disabled {opacity:.55!important;}
[data-testid="stSegmentedControl"] button {color:#30496e!important;background:#fff!important;border-color:#c7d5e7!important;min-height:45px!important;}
[data-testid="stSegmentedControl"] button[aria-pressed="true"],[data-testid="stSegmentedControl"] button[aria-selected="true"],[data-testid="stSegmentedControl"] button[data-selected="true"] {color:#154fc8!important;background:#edf4ff!important;box-shadow:inset 0 0 0 1px #1555e8!important;}
[data-testid="stAlert"] {border-radius:8px!important;border:1px solid #d4dfed!important;}
[data-testid="stAlert"] [data-testid="stMarkdownContainer"] p {color:inherit!important;}
[data-testid="stForm"],[data-testid="stExpander"],[data-testid="stFileUploaderDropzone"] {background:#fff!important;border-color:#d4dfed!important;border-radius:9px!important;}
[data-testid="stMetric"] {background:#fff;border:1px solid #d9e3ef;border-radius:9px;padding:18px;}
[data-testid="stTabs"] button {color:#4d6384!important;font-size:16px!important;}
[data-testid="stTabs"] button[aria-selected="true"] {color:#1555e8!important;}
.tool-panel,.admin-hero,.admin-login-panel,.admin-module-card,.admin-metric-card,.bom-progress-card,.bom-progress-panel,.search-progress-card,.search-progress-panel {background:#fff!important;border-color:#d9e3ef!important;border-radius:12px!important;box-shadow:none!important;}
.admin-hero-title,.admin-login-title,.admin-module-name,.admin-module-number span,.tool-panel-title,.admin-stat-value,.admin-section-title,.admin-empty-title,.interp-chip strong {color:#172b4d!important;}
.admin-help-text,.admin-hero-subtitle,.admin-login-desc,.tool-panel-note,.admin-module-desc,.admin-stat-label,.admin-stat-note,.admin-section-desc,.admin-empty-desc,.admin-switch-hint,.interp-summary {color:#4d6384!important;}
.admin-stat-card,.admin-empty-state,.interp-card {background:#fff!important;border-color:#d4dfed!important;box-shadow:none!important;}
.admin-eyebrow,.admin-hero-badge,.admin-section-meta,.interp-chip,.match-card-query-pill {background:#eaf1ff!important;color:#204d94!important;border-color:#c2d4f2!important;}
.admin-action-hint,.interp-rule-note {background:#fff7e3!important;color:#825313!important;border-color:#ead79d!important;}
.bom-download-btn,.bom-preview-toggle-inline .bom-download-btn {background:#fff!important;color:#154fc8!important;border-color:#bbcde5!important;box-shadow:none!important;}
.bom-progress-title,.bom-progress-current strong,.bom-progress-summary strong,.search-progress-summary-status,.search-progress-summary-stage {color:#172b4d!important;}
.bom-progress-subtitle,.search-progress-summary-note,.search-progress-summary-meta {color:#4d6384!important;}
.bom-progress-current,.bom-progress-summary,.search-progress-summary {background:#f4f8ff!important;border-color:#c7d8ef!important;color:#30496e!important;}
.bom-progress-chip {background:#f0f4fa!important;border-color:#d4dfed!important;color:#30496e!important;}
.bom-progress-chip.success {background:#e7f7ef!important;color:#096443!important;}
.bom-progress-chip.warn {background:#fff5dc!important;color:#825313!important;}
.bom-progress-chip.fail {background:#fff0f1!important;color:#942b3b!important;}
.native-no-alt-match-alert {background:#edf4ff!important;color:#204d94!important;border-color:#c2d4f2!important;}
.admin-login-fixed,.member-login-fixed,.bom-entry-fixed,.member-logout-fixed {display:none!important;}
[data-testid="stDataFrame"] {border:1px solid #d4dfed;border-radius:8px;}
*:focus-visible {outline:3px solid #1555e8!important;outline-offset:3px;}
@media(prefers-reduced-motion:reduce) {* {scroll-behavior:auto!important;transition:none!important;}}
@media(max-width:1100px) {:root {--wb-header-height:50.4px;}.wb-sidebar {width:140px;}.wb-nav a {padding:14px 9px;font-size:14px;gap:8px;}.block-container,[data-testid="stMainBlockContainer"] {width:calc(100% - 140px)!important;margin-left:140px!important;padding:1rem 1.25rem!important;}.wb-header {margin:-2rem -1.25rem 18px;padding:1px 16px;gap:12px;}.wb-brand {font-size:18px;padding-left:12px;}.wb-logo {width:105px;}}
@media(max-width:760px) {.wb-sidebar {position:static;width:auto;padding:0;background:#193253;border-radius:7px;margin:0 0 14px;}.wb-nav {flex-direction:row;flex-wrap:wrap;gap:0;}.wb-nav a {flex:1 1 45%;padding:10px 10px;font-size:13px;gap:8px;border-left:0;border-bottom:3px solid transparent;}.wb-nav a:hover,.wb-nav a:focus-visible {border-bottom-color:#75a9ff;}.block-container,[data-testid="stMainBlockContainer"] {width:100%!important;margin-left:0!important;padding:.8rem!important;}.wb-header {height:auto;min-height:64px;margin:0 0 16px;padding:8px 10px;gap:8px;flex-wrap:wrap;border:1px solid #d9e3ef;border-radius:8px;}.wb-brand {font-size:17px;padding-left:10px;}.wb-logo {width:95px;height:40px;}.wb-badge {font-size:12px;padding:5px 10px;}.wb-user {font-size:13px;}.wb-title {font-size:23px;}.wb-subtitle {font-size:14px;}.st-key-workbench-search-panel {padding:14px 12px;}}
</style>
"""


def navigation_icon(name):
    # Inline SVG keeps navigation readable across Streamlit versions and embeds.
    shapes = {
        "search": '<circle cx="10.5" cy="10.5" r="6.5"/><path d="m15.5 15.5 5 5"/>',
        "list_alt": '<rect x="3" y="3" width="18" height="18" rx="2"/><path d="M10 7h7M10 12h7M10 17h7M7 7h.01M7 12h.01M7 17h.01"/>',
        "person": '<circle cx="12" cy="8" r="3.5"/><path d="M4.5 21v-2a7.5 5.5 0 0 1 15 0v2Z"/>',
        "settings": '<path d="m9 3-.7 2.3-2 .9-2.3-.5-1.5 2.6 1.7 1.8-.2 2.2-1.5 1.8L4 16.7l2.3-.5 2 .9.7 2.3h3l.7-2.3 2-.9 2.3.5 1.5-2.6-1.5-1.8-.2-2.2 1.7-1.8L17 5.7l-2.3.5-2-.9L12 3Z"/><circle cx="10.5" cy="11.2" r="3"/>',
    }
    return '<svg class="wb-nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" focusable="false">' + shapes[name] + '</svg>'


def render_header(st, logo_b64, active, links, member, login_href=None, is_trial=False):
    icons = {"search": "search", "bom": "list_alt", "member": "person", "admin": "settings"}
    nav = "".join(
        f'<a href="{html.escape(href, quote=True)}" target="_self" class="{"active" if key == active else ""}"'
        f'{" aria-current=\"page\"" if key == active else ""}>'
        f'{navigation_icon(icons[key])}{html.escape(label)}</a>'
        for key, label, href in links
    )
    member_href = next((href for key, _, href in links if key == "member"), "?member=1")
    if member:
        user = html.escape(str(member.get("display_name") or member.get("username") or "会员"))
        account = f'<a class="wb-user wb-user-link" href="{html.escape(member_href, quote=True)}" target="_self" title="查看会员资料">{user}</a>'
    else:
        href = html.escape(login_href or member_href, quote=True)
        account = f'<a class="wb-login-button" href="{href}" target="_self" role="button" aria-label="会员登录">{navigation_icon("person")}会员登录</a>'
    titles = {
        "search": ("元器件搜索", "支持完整型号与规格参数，每行一条。系统按原有规则匹配同规格品牌型号与对应价格。"),
        "bom": ("BOM 批量匹配", "上传、复核、指定品牌匹配，保留原始内容并导出完整结果。"),
        "member": ("会员中心", "管理账号资料、客户与使用记录。"),
        "admin": ("管理后台", "维护会员、客户、成本清单与匹配规则。"),
    }
    title, description = titles[active]
    badge = '<span class="wb-badge" title="本机测试版，业务资料独立，不同步到正式系统">测试版</span>' if is_trial else ""
    st.markdown(
        f'<aside class="wb-sidebar"><nav class="wb-nav" aria-label="主导航">{nav}</nav></aside>'
        f'<div class="wb-header"><img class="wb-logo" src="data:image/png;base64,{logo_b64}" alt="Fruition 富临通">'
        f'<span class="wb-brand">富临通元器件匹配系统</span>{badge}<div class="wb-account">{account}</div></div>'
        f'<div class="wb-page-heading"><div class="wb-title">{title}</div><div class="wb-subtitle">{description}</div></div>',
        unsafe_allow_html=True,
    )
