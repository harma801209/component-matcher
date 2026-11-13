"""Read-only engineering reference; no inventory, matching, or BOM writes."""
from dataclasses import dataclass
from html import escape
import re
import unicodedata

TITLE = "常规料器件替代建议"


@dataclass(frozen=True)
class Advice:
    key: str
    category: str
    impact: str
    title: str
    use: str
    original: str
    candidate: str
    why: str
    checks: str
    risks: str
    verify: str
    stop: str
    source: tuple[str, str] | None = None


CASES = (
    Advice("pullup", "电阻", "需重算", "普通上拉：8.87 kΩ → 10 kΩ",
           "低速、非定时的开漏状态脚或配置脚", "8.87 kΩ，0603，±1%",
           "10 kΩ，0603，±1%；保持额定功率和电压要求",
           "如果 8.87 kΩ 不是阈值或时序设计值，可优先查团队已批准的 10 kΩ 通用料。",
           "最大漏电下的高电平、拉低电流、上升沿（R 与总电容）、上电采样时刻。",
           "上升变慢或高电平裕量不足，启动时可能读错状态。",
           "在最长线缆、最大电容和温度边界实测高低电平、上升沿和上电采样。",
           "I²C、高速总线、精密阈值和 RC 定时不能照此例直接替换。"),
    Advice("divider", "电阻", "需重算", "分压网络：用两颗优选值维持比例",
           "设计阶段的直流分压", "上臂 12.4 kΩ、下臂 6.2 kΩ",
           "上臂 20 kΩ、下臂 10 kΩ；空载分压比同为 1/3",
           "不是把一颗电阻四舍五入，而是一起调整两臂；优先从现有批准阻值选配。",
           "计算带载比例、两臂误差与温漂、输入漏电和采样建立时间；等效源阻抗由约 4.13 kΩ 升至约 6.67 kΩ。",
           "ADC 可能未充分建立；开关电源反馈的噪声、环路或启动表现可能改变。",
           "对容差、输入电压与负载做最坏情况计算，再测阈值、采样误差与动态响应。",
           "若器件手册规定反馈电阻范围或与补偿网络耦合，先按控制器手册重新设计。"),
    Advice("precision-r", "电阻", "同规格换供方", "精密、取样与耐脉冲电阻：保留关键规格",
           "分流取样、精密增益、浪涌或高压位置", "特殊阻值、低温漂、四端或耐脉冲结构",
           "先查同阻值、同结构、同精度且满足温漂、脉冲与降额要求的第二来源",
           "放宽采购品牌通常比放宽精度、温漂或结构更可控。",
           "比较 TCR、长期漂移、额定功率、最大工作电压、脉冲曲线、端子与焊盘。",
           "同阻值同功率不代表脉冲承受能力相同；二端替四端会引入铜箔与焊点误差。",
           "实测电流或增益误差、热态漂移、温升和目标脉冲下的稳定性。",
           "找不到同等四端、高压或脉冲能力时，保留原规格或单独做设计变更。",
           ("Vishay：电压、脉冲与选型", "https://www.vishay.com/en/resistors/melf-selector-tool/")),
    Advice("mlcc-100n", "陶瓷电容", "需重算", "一般去耦：82 nF → 100 nF",
           "芯片手册允许该容量范围的一般电源去耦", "82 nF、0603、X7R",
           "100 nF、0603、X7R；原厂型号示例 Murata GRM188R71H104KA93D（50 V、±10%）",
           "先核对容量窗口，再优先查 100 nF 的批准料；示例型号仅用于检索和比规格。",
           "电压及瞬态裕量、实际偏压与温度下的有效容量、尺寸厚度、阻抗曲线与布局。",
           "阻抗谷值和谐振点改变，某些频段的噪声可能上升。",
           "检查原厂偏压曲线；板上测电源纹波、负载阶跃和关键频段噪声。",
           "精密滤波、补偿、定时及 RF 匹配位置不能套用这个例子。",
           ("Murata：示例料号特性曲线", "https://ds.murata.com/simsurfing/mlcc.html?partnumbers=%5B%22GRM188R71H104KA93%22%5D")),
    Advice("mlcc-area", "陶瓷电容", "需改板", "小封装高容值：优先保证有效容量",
           "低压电源输入或去耦位置，PCB 尚可调整", "0402、10 µF 的小封装组合",
           "先评估 0603／0805 的 10 µF，或符合电源手册的多颗并联方案",
           "不死守小封装；按最坏工况所需有效容量反推选型，再查可采购候选。",
           "直流偏压、温度、容差和老化后的有效容量；板高、焊盘、布局、启动浪涌。",
           "标称容量相同，带偏压时可能差很多；并联后 ESL、谐振和启动行为也会变。",
           "用原厂曲线做最坏情况预算，测启动、纹波、负载阶跃和 EMI。",
           "C0G 精密位置、软端子或认证要求不能因供货方便而放宽。",
           ("Murata：直流偏压与容量", "https://www.murata.com/support/faqs/capacitor/ceramiccapacitor/char/0005")),
    Advice("bulk", "电解／聚合物电容", "同规格换供方", "低 ESR 电源电容：按稳定窗口选第二来源",
           "LDO 或开关电源输出", "小外形、特定 ESR 的铝电解或聚合物电容",
           "优先同技术、同容量等级，且全温 ESR 落在控制器允许范围的候选",
           "与其换成任意同容量 MLCC，不如先找电气和机械窗口都满足的第二来源。",
           "电容与 ESR 上下限、温频曲线、纹波电流、寿命、漏电、极性、高度和焊盘。",
           "ESR 过低或过高都可能引起振荡；低温时纹波、寿命和启动表现也可能变差。",
           "按原芯片手册核查稳定区，在冷启动、负载阶跃和高温满载验证。",
           "没有控制器稳定窗口或实际工况数据时，不把跨介质候选列为直接替代。",
           ("TI：LDO 输出电容与 ESR", "https://www.ti.com/lit/an/snva167a/snva167a.pdf")),
    Advice("power-l", "电感", "需重算", "降压电感：3.9 µH 可先比较 3.3／4.7 µH",
           "设计阶段的降压电源，控制器允许多种感值", "3.9 µH、低高度屏蔽功率电感",
           "按控制器范围比较 3.3 µH 与 4.7 µH；若都不满足，保留 3.9 µH 找第二来源",
           "先比较常用感值候选的整个工况窗口；不只比较标称感值。",
           "最坏输入与开关频率下的纹波、峰值与 RMS 电流、热态饱和、DCR、结构与高度；比较同一饱和判据。",
           "感值偏低可能增加纹波和峰值；偏高可能改变动态和轻载行为；损耗和 EMI 也会变。",
           "检查电感电流波形、过流裕量、温升、效率、负载阶跃和 EMI。",
           "射频匹配、谐振及规定电感范围的设计不按邻近值盲换。",
           ("Coilcraft：降压转换器电感选型", "https://www.coilcraft.com/en-us/resources/application-notes/selecting-the-best-inductor-for-your-dc-dc-convert/")),
    Advice("bead", "磁珠／共模", "同规格换供方", "磁珠：同为 600 Ω @ 100 MHz 也要看曲线",
           "电源支路滤波", "600 Ω @ 100 MHz，特殊外形或材料",
           "优先同焊盘、同目标频段阻抗且在实际偏置电流下满足要求的系列",
           "阻抗单点只是筛选起点，不能用作放行依据。",
           "工作电流下的 Z/R/X 曲线、DCR、压降、温升和与两侧电容构成的谐振。",
           "标称相同仍可能滤波失效，或者因共振放大某段噪声。",
           "对比有负载时的电源噪声频谱、压降、温升和 EMI。",
           "差分共模扼流圈不能用普通磁珠直接代换；还需验证差模损耗和信号完整性。",
           ("ADI AN-1368：磁珠偏置与谐振", "https://www.analog.com/en/resources/app-notes/an-1368.html")),
    Advice("xtal", "晶振／振荡器", "需重算", "24 MHz 晶体：优先统一封装与负载电容",
           "MCU 外部无源晶体，硬件仍可调试", "24 MHz、非团队常用负载电容或外形",
           "先找同频率、同 CL 与同焊盘的第二来源；若改为另一 CL，重选两侧负载电容",
           "先统一器件平台，不为采购方便直接改工作频率。",
           "CL 与板级杂散电容、ESR、起振裕量、驱动功率、全温频偏和引脚。",
           "能起振不代表频率达标；冷启动可能失败，有源振荡器也不是无源晶体的同焊盘替代。",
           "测起振时间、频偏、驱动功率，并做多板全温反复上电。",
           "USB、无线与精密时钟必须满足主芯片的时钟要求。",
           ("Epson：振荡电路设计注意事项", "https://www.epsondevice.com/crystal/en/support/precaution/design.html")),
    Advice("mos", "MOSFET", "同规格换供方", "MOS 管：按实际驱动电压选通用封装",
           "低压负载开关或 PWM 开关", "特殊封装或只有较高 VGS 下给出导通电阻的器件",
           "在同极性、同焊盘和同引脚候选中，筛选实际最低 VGS 下有最大 RDS(on) 保证的料",
           "按驱动条件筛规格，避免采购到阈值看似接近、实际却导通不足的器件。",
           "VDS 裕量、VGS 极限、热态 RDS(on)、Qg、体二极管、SOA 与 PCB 散热。",
           "阈值电压不是充分导通电压；Qg 变大可能加重驱动损耗和开关温升。",
           "实测栅极波形、开关尖峰、最坏负载温升与瞬态应力。",
           "线性限流、热插拔、并联或雪崩工况须单独核对 SOA，不按额定电流盲换。",
           ("TI：LM3488-Q1，Power MOSFET Selection", "https://www.ti.com/lit/ds/symlink/lm3488-q1.pdf")),
    Advice("tvs", "二极管／保护器件", "同规格换供方", "TVS：同标称电压不代表同保护能力",
           "接口或电源浪涌保护", "指定封装的单向或双向 TVS",
           "优先同极性、同焊盘，且在规定脉冲下满足钳位目标的第二来源",
           "先按正常工作上限及被保护器件耐受极限定义窗口，再筛选标准系列。",
           "VRWM、VBR、目标脉冲电流及波形下的 VCL、温度降额、漏电、结电容和布线。",
           "只比击穿电压会漏掉动态钳位差异；高速接口还可能因结电容恶化信号。",
           "按产品适用标准做浪涌或 ESD 测试，同时测芯片端残压及功能。",
           "不要把 TVS 换成普通稳压管或只按封装和功率瓦数签核。",
           ("ST AN5887：TVS 钳位机制", "https://www.st.com/resource/en/application_note/an5887-tvs-devices-for-power-line-communication-applications-stmicroelectronics.pdf")),
    Advice("opamp", "模拟 IC", "需重算", "低速双运放：优先验证标准双运放平台",
           "低速信号调理、负载轻且电压余量充分", "特殊封装或非必要高带宽的双运放",
           "可把 TI LM358B 系列作为比较起点；确认完整订货号、封装与引脚",
           "设计阶段先用可复用的平台，但通用型号不是精密或高速运放的等效件。",
           "供电、输入共模、输出摆幅与负载、失调、偏置、带宽、压摆率和容性负载稳定性。",
           "输入或输出靠近正电源时可能饱和；失调和速度可能不够。",
           "测输入输出边界、闭环误差、阶跃和最大容性负载下的稳定性。",
           "需要轨到轨输入输出、低失调或高速 ADC 驱动时，不默认选 LM358B。",
           ("TI：LM358B 产品资料", "https://www.ti.com/product/LM358B")),
)


def _search_text(value):
    text = unicodedata.normalize("NFKC", value).casefold()
    return "".join(text.replace("μ", "u").replace("ω", "ohm").split())


def filter_advice(category="全部", impact="全部", keyword=""):
    terms = [_search_text(term) for term in keyword.split()]
    return tuple(case for case in CASES
                 if (category == "全部" or category == case.category)
                 and (impact == "全部" or impact == case.impact)
                 and all(term in _search_text(" ".join((
                     case.category, case.impact, case.title, case.use, case.original,
                     case.candidate, case.why, case.checks, case.risks,
                 ))) for term in terms))


_COMPARISON_STYLE = """
<style>
.std-advice-scroll { max-height: min(52vh, 34rem); overflow: auto; border: 1px solid #ccd8e8; border-radius: .75rem; background: #fff; }
.std-advice-scroll:focus-visible { outline: 2px solid #2056ad; outline-offset: 2px; }
.std-advice-scroll .std-advice-table { width: 100%; margin: 0; table-layout: fixed; border: 0; border-collapse: separate; border-spacing: 0; color: #172e4b; font-size: .9rem; line-height: 1.45; }
.std-advice-table :is(th, td) { border: 0; border-bottom: 1px solid #e0e8f3; padding: .8rem; text-align: left; vertical-align: top; overflow-wrap: anywhere; }
.std-advice-table thead th { position: sticky; top: 0; z-index: 1; color: #234268; background: #edf3fb; }
.std-advice-table tbody th { font-weight: 400; }
.std-advice-table tbody tr:nth-child(even) { background: #f7f9fd; }
.std-advice-table tbody tr:last-child :is(th, td) { border-bottom: 0; }
.std-advice-table .std-advice-use { display: block; margin-top: .25rem; color: #4b617c; }
.std-advice-table .std-advice-target { color: #174e9b; font-weight: 600; }
.std-advice-table .std-advice-impact { display: inline-block; border-radius: .35rem; padding: .15rem .4rem; font-weight: 600; background: #e8effa; color: #254b81; }
.std-advice-table .std-advice-calculate { background: #fff3db; color: #794604; }
.std-advice-table .std-advice-layout { background: #fbe8e8; color: #892c3a; }
.std-advice-table .std-advice-mobile-label { display: none; }
@media (max-width: 850px) {
  .std-advice-scroll { max-height: min(56vh, 34rem); }
  .std-advice-table, .std-advice-table tbody, .std-advice-table tr, .std-advice-table :is(th, td) { display: block; }
  .std-advice-table thead { position: absolute; width: 1px; height: 1px; overflow: hidden; clip-path: inset(50%); }
  .std-advice-table colgroup { display: none; }
  .std-advice-table tbody tr { padding: .45rem .75rem; border-bottom: 1px solid #e0e8f3; }
  .std-advice-table tbody tr:last-child { border-bottom: 0; }
  .std-advice-table :is(th, td) { padding: .32rem 0; border: 0; }
  .std-advice-table .std-advice-mobile-label { display: block; font-size: .8rem; color: #4b617c; font-weight: 600; }
}
</style>
""".strip()


def _comparison_html(cases):
    def cell(label, value, css=""):
        return (f'<td role="cell" class="{css}"><span aria-hidden="true" '
                f'class="std-advice-mobile-label">{label}</span>{value}</td>')

    impact_classes = {"需重算": "std-advice-calculate", "需改板": "std-advice-layout"}
    headings = ("应用场景", "原规格", "常规候选", "改动程度", "关键风险")
    rows = []
    for case in cases:
        badge = (f'<span class="std-advice-impact {impact_classes.get(case.impact, "")}">'
                 f'{escape(case.impact)}</span>')
        rows.append(
            '<tr role="row"><th scope="row" role="rowheader">'
            f'<strong>{escape(case.title)}</strong>'
            f'<span class="std-advice-use">{escape(case.category)} · {escape(case.use)}</span></th>'
            + cell(headings[1], escape(case.original))
            + cell(headings[2], escape(case.candidate), "std-advice-target")
            + cell(headings[3], badge)
            + cell(headings[4], escape(case.risks))
            + '</tr>'
        )
    header = ''.join(f'<th scope="col" role="columnheader">{label}</th>' for label in headings)
    columns = ''.join(f'<col style="width:{width}%">' for width in (22, 16, 27, 11, 24))
    return (
        _COMPARISON_STYLE
        + '<div class="std-advice-scroll" role="region" aria-label="可滚动的规格对照表" tabindex="0">'
        + '<table class="std-advice-table" role="table" aria-label="规格替代对照">'
        + f'<colgroup>{columns}</colgroup><thead role="rowgroup"><tr role="row">{header}</tr></thead>'
        + '<tbody role="rowgroup">' + ''.join(rows) + '</tbody></table></div>'
    )


def normalize_lookup_model(value):
    text = unicodedata.normalize("NFKC", value).strip()
    if "\n" in text or "\r" in text:
        return ""
    compact = "".join(text.split()).upper()
    if re.fullmatch(r"[A-Z0-9][A-Z0-9./_+:#-]{1,95}", compact):
        return compact
    return ""


def part_summary(row, clean_text):
    """Allowlist catalogue data: pricing and internal fields never enter this view."""
    value = " ".join(filter(None, (
        clean_text(row.get("容值")), clean_text(row.get("容值单位")),
    )))
    summary = {
        "品牌": clean_text(row.get("品牌")),
        "型号": clean_text(row.get("型号")),
        "器件类别": clean_text(row.get("器件类型")),
        "系列": clean_text(row.get("系列")),
        "尺寸（英制）": clean_text(row.get("尺寸（inch）")),
        "尺寸／封装": clean_text(row.get("尺寸（mm）")) or clean_text(row.get("封装代码")),
        "参数值": value,
        "误差": clean_text(row.get("容值误差")),
        "介质": clean_text(row.get("材质（介质）")),
        "额定电压": clean_text(row.get("耐压（V）")),
        "功率": clean_text(row.get("功率")),
        "温度系数": clean_text(row.get("温度系数")),
        "特殊用途": clean_text(row.get("特殊用途")),
        "规格摘要": clean_text(row.get("规格摘要")),
    }
    return {key: val for key, val in summary.items() if val}


def _render_part_lookup(st, *, lookup_part, member_id, login_href, open_match):
    st.subheader("按料号查库")
    result_key = "_standard_advice_lookup_result"
    if not member_id:
        st.session_state.pop(result_key, None)
        if login_href:
            st.markdown(f"[登录后查询库内料号]({login_href})")
        else:
            st.caption("登录后可查询库内料号。")
        return
    with st.form("standard_advice_part_lookup", border=False):
        raw_model = st.text_input(
            "原器件料号", placeholder="例如 FRC0402F1001TS", max_chars=120,
            key="standard_advice_lookup_model",
        )
        submitted = st.form_submit_button("查询料号", type="primary")
    model = normalize_lookup_model(raw_model)
    if submitted:
        st.session_state.pop(result_key, None)
        if not model:
            st.warning("请输入一个完整料号；用途或规格请用下方的案例筛选。")
            return
        with st.spinner("正在查询器件库…"):
            result = lookup_part(model)
        st.session_state[result_key] = (member_id, model, result)
    owner, looked_up, result = st.session_state.get(result_key, (None, "", None))
    if owner != member_id or looked_up != model:
        return
    if result is None:
        st.warning("器件库暂不可用，请稍后重试。")
    elif not result:
        st.warning("库内没有找到这个完整料号。请核对品牌、型号和订货尾码。")
    else:
        st.caption("以下是原器件的库内资料，不代表已找到替代型号。下方是按电路用途筛选的设计案例。")
        for part in result:
            with st.container(border=True):
                st.text(" · ".join(part[label] for label in ("品牌", "型号") if label in part))
                for label, value in part.items():
                    if label not in ("品牌", "型号"):
                        st.text(f"{label}：{value}")
        if open_match and st.button("用此料号查替代型号", key="standard_advice_open_match"):
            open_match(model)


def render_page(st, *, lookup_part=None, member_id=None, login_href=None, open_match=None):
    st.info("用于设计阶段选型，不是等效替代、现货或采购批准。先确认电路用途和不可放宽的条件，再由采购核实供应。")
    if lookup_part is not None:
        _render_part_lookup(st, lookup_part=lookup_part, member_id=member_id,
                            login_href=login_href, open_match=open_match)
    st.subheader("设计案例筛选")
    search, left, right = st.columns((2, 1, 1))
    keyword = search.text_input("筛选案例用途或规格", placeholder="例如 去耦、100 nF、24 MHz", key="standard_advice_keyword")
    category = left.selectbox("器件类别", ["全部", *dict.fromkeys(c.category for c in CASES)], key="standard_advice_category")
    impact = right.selectbox("设计影响", ["全部", "同规格换供方", "需重算", "需改板"], key="standard_advice_impact")
    cases = filter_advice(category, impact, keyword)
    st.subheader("规格替代对照")
    st.caption(f"显示 {len(cases)} / {len(CASES)} 条设计案例")
    if not cases:
        st.warning("没有符合筛选条件的案例。可清空关键字，或换器件类别和设计影响。")
    else:
        st.markdown(_comparison_html(cases), unsafe_allow_html=True)
        st.subheader("评审与验证")
        by_key = {case.key: case for case in cases}
        if st.session_state.get("standard_advice_case") not in by_key:
            st.session_state.pop("standard_advice_case", None)
        selected = st.selectbox(
            "选择案例查看详情", list(by_key), format_func=lambda key: by_key[key].title,
            key="standard_advice_case",
        )
        case = by_key[selected]
        with st.container(border=True):
            st.markdown(f"**{case.title}** · {case.impact}")
            original, candidate = st.columns(2)
            original.markdown(f"**原规格**\n\n{case.original}")
            candidate.markdown(f"**常规候选**\n\n{case.candidate}")
            st.markdown(f"**为什么这样改：**{case.why}")
            checks, verify = st.columns(2)
            checks.markdown(f"**替代前确认**\n\n{case.checks}")
            verify.markdown(f"**样板验证**\n\n{case.verify}")
            st.warning(f"不能直接套用：{case.stop}")
            if case.source:
                label, url = case.source
                st.markdown(f"原厂参考：[{label}]({url})")

    with st.expander("设计评审流程"):
        st.markdown(
            "1. 标出工作条件与硬约束：电气范围、焊盘、温度、安规、车规及寿命。\n"
            "2. 先查企业批准料；请采购确认独立供应来源、交期、MOQ 和生命周期。\n"
            "3. 对候选逐项比较数据手册，做最坏情况计算；需要改值或改板的单独评审。\n"
            "4. 样板验证后由研发签核并更新 BOM／AVL，保留原料号和变更记录。"
        )
