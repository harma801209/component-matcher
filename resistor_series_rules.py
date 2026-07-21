from __future__ import annotations

import re
from typing import Callable


UNIROYAL_BRAND_TOKENS = ("UNI-ROYAL", "UNIROYAL", "厚声", "UNIOHM")
TAI_BRAND_TOKENS = ("TA-I", "大毅")
VIKING_BRAND_TOKENS = ("VIKING", "光颉")
YAGEO_BRAND_TOKENS = ("YAGEO", "国巨")
BRIGHTKING_BRAND_TOKENS = ("BRIGHTKING", "君耀")
STE_BRAND_TOKENS = ("STE(松田)", "松田", "SONGTIAN")
RALEC_BRAND_TOKENS = ("RALEC", "旺诠")
SAMSUNG_BRAND_TOKENS = ("SAMSUNG", "三星")
WALSIN_BRAND_TOKENS = ("WALSIN", "华新科", "华科")
FENGHUA_BRAND_TOKENS = ("FENGHUA", "风华")
FOJAN_BRAND_TOKENS = ("FOJAN", "富捷")
LIZ_BRAND_TOKENS = ("LIZ", "丽智")
RESI_BRAND_TOKENS = ("RESI", "睿思", "开步")
TYOHM_BRAND_TOKENS = ("TYOHM", "TY-OHM", "幸亚")
VO_BRAND_TOKENS = ("VO", "翔胜")
VENKEL_BRAND_TOKENS = ("VENKEL",)
RCD_BRAND_TOKENS = ("RCD", "RCD COMPONENTS")
RIEDON_BRAND_TOKENS = ("RIEDON",)
THUNDER_BRAND_TOKENS = ("THUNDER COMPONENT", "THUNDER", "帝谷")
NTE_BRAND_TOKENS = ("NTE ELECTRONICS", "NTE")


UNIROYAL_OFFICIAL_SERIES_PROFILES = {
    "AS": {"系列说明": "抗浪涌厚膜晶片电阻器", "器件类型": "厚膜电阻", "特殊用途": "抗浪涌"},
    "CM": {"系列说明": "工业级厚膜晶片电阻器", "器件类型": "厚膜电阻", "特殊用途": "工业级"},
    "CQ": {"系列说明": "汽车级晶片电阻器", "器件类型": "厚膜电阻", "特殊用途": "车规"},
    "CS": {"系列说明": "汽车级低阻厚膜晶片电阻器", "器件类型": "厚膜电阻", "特殊用途": "车规"},
    "ES": {"系列说明": "防静电厚膜晶片电阻器", "器件类型": "厚膜电阻", "特殊用途": "防静电"},
    "HP": {"系列说明": "高功率厚膜晶片电阻器", "器件类型": "厚膜电阻", "特殊用途": "高功率"},
    "HQ": {"系列说明": "汽车级高功率厚膜晶片电阻器", "器件类型": "厚膜电阻", "特殊用途": "车规 | 高功率"},
    "HS": {"系列说明": "高功率抗浪涌厚膜晶片电阻器", "器件类型": "厚膜电阻", "特殊用途": "高功率 | 抗浪涌"},
    "HV": {"系列说明": "高压厚膜晶片电阻器", "器件类型": "厚膜电阻", "特殊用途": "高压"},
    "LE": {"系列说明": "软灯条专用晶片电阻器", "器件类型": "厚膜电阻", "特殊用途": "LED"},
    "LT": {"系列说明": "低T.C.R厚膜晶片电阻器", "器件类型": "厚膜电阻", "特殊用途": "低TCR"},
    "NM": {"系列说明": "无磁厚膜晶片电阻器", "器件类型": "厚膜电阻", "特殊用途": "无磁"},
    "NQ": {"系列说明": "抗硫化汽车级晶片电阻器", "器件类型": "厚膜电阻", "特殊用途": "车规 | 抗硫化"},
    "NS": {"系列说明": "高品质抗硫化汽车级晶片电阻器", "器件类型": "厚膜电阻", "特殊用途": "车规 | 抗硫化"},
    "PF": {"系列说明": "完全无铅厚膜晶片电阻器", "器件类型": "厚膜电阻", "特殊用途": "无铅"},
    "PS": {"系列说明": "高精密抗浪涌厚膜晶片电阻器", "器件类型": "厚膜电阻", "特殊用途": "高精密 | 抗浪涌"},
    "TC": {"系列说明": "高精密薄膜晶片电阻器", "器件类型": "薄膜电阻", "特殊用途": "高精密"},
    "VS": {"系列说明": "高压抗硫化厚膜晶片电阻器", "器件类型": "厚膜电阻", "特殊用途": "高压 | 抗硫化"},
    "WR": {"系列说明": "宽端子厚膜晶片电阻器", "器件类型": "厚膜电阻", "特殊用途": "宽端子"},
    "LR051WF": {"系列说明": "厚声 UNI-ROYAL LR051WF 金属合金低阻电流检测贴片电阻", "器件类型": "合金电阻", "特殊用途": "电流检测 | 低阻 | 金属合金 | 贴片"},
    "LR061WF": {"系列说明": "厚声 UNI-ROYAL LR061WF 金属合金低阻电流检测贴片电阻", "器件类型": "合金电阻", "特殊用途": "电流检测 | 低阻 | 金属合金 | 贴片"},
    "LR122WF": {"系列说明": "厚声 UNI-ROYAL LR122WF 金属合金低阻电流检测贴片电阻", "器件类型": "合金电阻", "特殊用途": "电流检测 | 低阻 | 金属合金 | 贴片"},
    "LR123WF": {"系列说明": "厚声 UNI-ROYAL LR123WF 金属合金低阻电流检测贴片电阻", "器件类型": "合金电阻", "特殊用途": "电流检测 | 低阻 | 金属合金 | 贴片"},
    "ML061WF": {"系列说明": "厚声 UNI-ROYAL ML061WF 金属合金低阻电流检测贴片电阻", "器件类型": "合金电阻", "特殊用途": "电流检测 | 低阻 | 金属合金 | 贴片"},
    "MS05W": {"系列说明": "厚声 UNI-ROYAL MS05W 金属带电流检测贴片电阻", "器件类型": "合金电阻", "特殊用途": "电流检测 | 低阻 | 金属带 | 贴片"},
    "MS06W": {"系列说明": "厚声 UNI-ROYAL MS06W 金属带电流检测贴片电阻", "器件类型": "合金电阻", "特殊用途": "电流检测 | 低阻 | 金属带 | 贴片"},
    "MS061WF": {"系列说明": "厚声 UNI-ROYAL MS061WF 金属带电流检测贴片电阻", "器件类型": "合金电阻", "特殊用途": "电流检测 | 低阻 | 金属带 | 贴片"},
    "MS071AF": {"系列说明": "厚声 UNI-ROYAL MS071AF 金属带电流检测贴片电阻", "器件类型": "合金电阻", "特殊用途": "电流检测 | 低阻 | 金属带 | 贴片"},
    "MS121WF": {"系列说明": "厚声 UNI-ROYAL MS121WF 金属带电流检测贴片电阻", "器件类型": "合金电阻", "特殊用途": "电流检测 | 低阻 | 金属带 | 贴片"},
    "MS122WF": {"系列说明": "厚声 UNI-ROYAL MS122WF 金属带电流检测贴片电阻", "器件类型": "合金电阻", "特殊用途": "电流检测 | 低阻 | 金属带 | 贴片"},
    "MS122WJ": {"系列说明": "厚声 UNI-ROYAL MS122WJ 金属带电流检测贴片电阻", "器件类型": "合金电阻", "特殊用途": "电流检测 | 低阻 | 金属带 | 贴片"},
    "MS123WF": {"系列说明": "厚声 UNI-ROYAL MS123WF 金属带电流检测贴片电阻", "器件类型": "合金电阻", "特殊用途": "电流检测 | 低阻 | 金属带 | 贴片"},
    "MS275WF": {"系列说明": "厚声 UNI-ROYAL MS275WF 大功率金属带电流检测贴片电阻", "器件类型": "合金电阻", "特殊用途": "电流检测 | 低阻 | 金属带 | 大功率 | 贴片"},
    "M27W2FF": {"系列说明": "厚声 UNI-ROYAL M27W2FF MELF 圆柱贴片电阻", "器件类型": "薄膜电阻", "特殊用途": "MELF | 圆柱贴片"},
    "4D03": {"系列说明": "厚声 UNI-ROYAL 4D03 贴片排列电阻/电阻网络", "器件类型": "贴片电阻", "特殊用途": "电阻阵列 | 贴片"},
    "普通厚膜": {"系列说明": "普通厚膜晶片电阻器", "器件类型": "厚膜电阻", "特殊用途": ""},
}

TAI_OFFICIAL_SERIES_PROFILES = {
    "RB": {"系列说明": "薄膜晶片电阻器", "器件类型": "薄膜电阻", "特殊用途": "高精密"},
    "RBA": {"系列说明": "车规薄膜晶片电阻器", "器件类型": "薄膜电阻", "特殊用途": "车规 | 高精密"},
    "RM": {"系列说明": "厚膜晶片电阻器", "器件类型": "厚膜电阻", "特殊用途": ""},
    "RMH": {"系列说明": "高压厚膜晶片电阻器", "器件类型": "厚膜电阻", "特殊用途": "高压"},
    "RMS": {"系列说明": "抗硫化车载晶片电阻", "器件类型": "厚膜电阻", "特殊用途": "车规 | 抗硫化"},
    "RMSV": {"系列说明": "高功率抗硫化车载晶片电阻", "器件类型": "厚膜电阻", "特殊用途": "车规 | 抗硫化 | 高功率"},
    "RASS": {"系列说明": "抗硫化抗突波车载晶片电阻", "器件类型": "厚膜电阻", "特殊用途": "车规 | 抗硫化 | 抗浪涌"},
}

VIKING_OFFICIAL_SERIES_PROFILES = {
    "AR": {"系列说明": "薄膜精密晶片电阻器", "器件类型": "薄膜电阻", "特殊用途": "高精密"},
    "AS": {"系列说明": "抗硫化厚膜晶片电阻器", "器件类型": "厚膜电阻", "特殊用途": "抗硫化"},
    "ASG": {"系列说明": "绿色抗硫化厚膜晶片电阻器", "器件类型": "厚膜电阻", "特殊用途": "抗硫化 | 绿色"},
    "CR": {"系列说明": "通用厚膜晶片电阻器", "器件类型": "厚膜电阻", "特殊用途": ""},
}

YAGEO_OFFICIAL_SERIES_PROFILES = {
    "AA": {"系列说明": "汽车级抗硫化厚膜晶片电阻器", "器件类型": "厚膜电阻", "特殊用途": "车规 | 抗硫化"},
    "AC": {"系列说明": "汽车级厚膜晶片电阻器", "器件类型": "厚膜电阻", "特殊用途": "车规"},
    "AF": {"系列说明": "抗硫化厚膜晶片电阻器", "器件类型": "厚膜电阻", "特殊用途": "抗硫化"},
    "AR": {"系列说明": "镍金端接片式电阻器", "器件类型": "厚膜电阻", "特殊用途": "Ni/Au端接"},
    "AT": {"系列说明": "车规薄膜晶片电阻器", "器件类型": "薄膜电阻", "特殊用途": "车规 | 高精密"},
    "CFR": {"系列说明": "碳膜引线电阻器", "器件类型": "碳膜电阻", "特殊用途": ""},
    "FMP": {"系列说明": "金属膜引线电阻器", "器件类型": "薄膜电阻", "特殊用途": ""},
    "KNP": {"系列说明": "轴向线绕电阻器", "器件类型": "绕线电阻", "特殊用途": ""},
    "HHV": {"系列说明": "高压金属釉膜固定电阻器", "器件类型": "薄膜电阻", "特殊用途": "高压"},
    "MF": {"系列说明": "金属膜固定电阻器", "器件类型": "薄膜电阻", "特殊用途": ""},
    "MFR": {"系列说明": "金属膜精密引线电阻器", "器件类型": "薄膜电阻", "特殊用途": "高精密"},
    "MMF": {"系列说明": "微型金属膜引线电阻器", "器件类型": "薄膜电阻", "特殊用途": "小型化"},
    "MMP": {"系列说明": "金属膜引线电阻器", "器件类型": "薄膜电阻", "特殊用途": ""},
    "PA": {"系列说明": "车规金属电流检测电阻器", "器件类型": "合金电阻", "特殊用途": "车规 | 电流检测 | 低TCR"},
    "PE": {"系列说明": "车规低TCR金属电流检测电阻器", "器件类型": "合金电阻", "特殊用途": "车规 | 电流检测 | 低TCR"},
    "PNP": {"系列说明": "功率线绕电阻器", "器件类型": "绕线电阻", "特殊用途": "高功率"},
    "PS": {"系列说明": "宽端子低TCR金属电流检测电阻器", "器件类型": "合金电阻", "特殊用途": "电流检测 | 低TCR | 宽端子"},
    "PT": {"系列说明": "低TCR电流检测厚膜片式电阻器", "器件类型": "厚膜电阻", "特殊用途": "电流检测 | 低TCR"},
    "PU": {"系列说明": "车规功率分流金属电流检测电阻器", "器件类型": "合金电阻", "特殊用途": "车规 | 电流检测 | 功率分流"},
    "RC": {"系列说明": "通用厚膜晶片电阻器", "器件类型": "厚膜电阻", "特殊用途": ""},
    "RE": {"系列说明": "高精度厚膜片式电阻器", "器件类型": "厚膜电阻", "特殊用途": "高精密"},
    "RL": {"系列说明": "电流检测低阻厚膜片式电阻器", "器件类型": "厚膜电阻", "特殊用途": "电流检测"},
    "RT": {"系列说明": "高精度高稳定薄膜晶片电阻器", "器件类型": "薄膜电阻", "特殊用途": "高精密"},
    "RV": {"系列说明": "高压厚膜片式电阻器", "器件类型": "厚膜电阻", "特殊用途": "高压"},
    "RSF": {"系列说明": "金属氧化膜固定电阻器", "器件类型": "金属氧化膜电阻", "特殊用途": ""},
    "SR": {"系列说明": "抗浪涌厚膜片式电阻器", "器件类型": "厚膜电阻", "特殊用途": "抗浪涌"},
}

RALEC_OFFICIAL_SERIES_PROFILES = {
    "LR": {"系列说明": "金属合金低阻电流检测贴片电阻", "器件类型": "合金电阻", "特殊用途": "电流检测 | 低阻 | 金属合金"},
    "LRE": {"系列说明": "金属合金低阻电流检测贴片电阻", "器件类型": "合金电阻", "特殊用途": "电流检测 | 低阻 | 金属合金"},
    "RAT": {"系列说明": "车规级厚膜贴片电阻", "器件类型": "厚膜电阻", "特殊用途": "车规"},
    "RHW": {"系列说明": "宽端子高功率厚膜贴片电阻", "器件类型": "厚膜电阻", "特殊用途": "宽端子 | 高功率"},
    "RTH": {"系列说明": "高功率厚膜贴片电阻", "器件类型": "厚膜电阻", "特殊用途": "高功率"},
    "RTG": {"系列说明": "抗浪涌厚膜贴片电阻", "器件类型": "厚膜电阻", "特殊用途": "抗浪涌"},
    "RTR": {"系列说明": "高精度厚膜贴片电阻", "器件类型": "厚膜电阻", "特殊用途": "高精度"},
    "RTV": {"系列说明": "高压厚膜贴片电阻", "器件类型": "厚膜电阻", "特殊用途": "高压"},
    "RTT": {"系列说明": "通用厚膜贴片电阻", "器件类型": "厚膜电阻", "特殊用途": ""},
    "RTW": {"系列说明": "宽端子厚膜贴片电阻", "器件类型": "厚膜电阻", "特殊用途": "宽端子"},
}

SAMSUNG_OFFICIAL_SERIES_PROFILES = {
    "RC": {"系列说明": "通用厚膜贴片电阻", "器件类型": "厚膜电阻", "特殊用途": ""},
    "RCS": {"系列说明": "抗硫化通用厚膜贴片电阻", "器件类型": "厚膜电阻", "特殊用途": "抗硫化"},
    "RCB": {"系列说明": "反装厚膜贴片电阻", "器件类型": "厚膜电阻", "特殊用途": "反装"},
    "RCA": {"系列说明": "车规级厚膜贴片电阻", "器件类型": "厚膜电阻", "特殊用途": "车规"},
    "RCW": {"系列说明": "高功率厚膜贴片电阻", "器件类型": "厚膜电阻", "特殊用途": "高功率"},
    "RCWS": {"系列说明": "抗硫化高功率厚膜贴片电阻", "器件类型": "厚膜电阻", "特殊用途": "抗硫化 | 高功率"},
    "RCV": {"系列说明": "高压厚膜贴片电阻", "器件类型": "厚膜电阻", "特殊用途": "高压"},
    "RCVS": {"系列说明": "抗硫化高压厚膜贴片电阻", "器件类型": "厚膜电阻", "特殊用途": "抗硫化 | 高压"},
    "RU": {"系列说明": "厚膜电流检测贴片电阻", "器件类型": "厚膜电阻", "特殊用途": "电流检测"},
    "RJ": {"系列说明": "宽端子电流检测贴片电阻", "器件类型": "厚膜电阻", "特殊用途": "电流检测 | 宽端子"},
    "RL": {"系列说明": "金属电流检测贴片电阻", "器件类型": "合金电阻", "特殊用途": "电流检测"},
}

WALSIN_OFFICIAL_SERIES_PROFILES = {
    "WR": {"系列说明": "通用厚膜贴片电阻", "器件类型": "厚膜电阻", "特殊用途": ""},
    "MR": {"系列说明": "车规级厚膜贴片电阻", "器件类型": "厚膜电阻", "特殊用途": "车规"},
    "SR": {"系列说明": "抗硫化车规级厚膜贴片电阻", "器件类型": "厚膜电阻", "特殊用途": "车规 | 抗硫化"},
    "WF": {"系列说明": "通用厚膜贴片电阻", "器件类型": "厚膜电阻", "特殊用途": ""},
    "WW": {"系列说明": "低阻电流检测贴片电阻", "器件类型": "合金电阻", "特殊用途": "电流检测 | 低阻"},
}

FENGHUA_OFFICIAL_SERIES_PROFILES = {
    "RC": {"系列说明": "通用厚膜贴片固定电阻", "器件类型": "厚膜电阻", "特殊用途": ""},
    "RS": {"系列说明": "通用厚膜贴片固定电阻", "器件类型": "厚膜电阻", "特殊用途": ""},
}

FOJAN_OFFICIAL_SERIES_PROFILES = {
    "FRC": {"系列说明": "普通厚膜贴片电阻", "器件类型": "厚膜电阻", "特殊用途": ""},
    "FRP": {"系列说明": "高功率厚膜贴片电阻", "器件类型": "厚膜电阻", "特殊用途": "高功率"},
    "FRL": {"系列说明": "低阻值厚膜贴片电阻", "器件类型": "厚膜电阻", "特殊用途": "低阻值"},
    "FRS": {"系列说明": "抗浪涌厚膜贴片电阻", "器件类型": "厚膜电阻", "特殊用途": "抗浪涌"},
    "FRH": {"系列说明": "高精度厚膜贴片电阻", "器件类型": "厚膜电阻", "特殊用途": "高精度"},
    "FRV": {"系列说明": "高压厚膜贴片电阻", "器件类型": "厚膜电阻", "特殊用途": "高压"},
    "FRQ": {"系列说明": "车规级厚膜贴片电阻", "器件类型": "厚膜电阻", "特殊用途": "车规"},
    "FRR": {"系列说明": "抗硫化厚膜贴片电阻", "器件类型": "厚膜电阻", "特殊用途": "抗硫化"},
    "FRG": {"系列说明": "高阻值厚膜贴片电阻", "器件类型": "厚膜电阻", "特殊用途": "高阻值"},
    "FRD": {"系列说明": "LED专用厚膜贴片电阻", "器件类型": "厚膜电阻", "特殊用途": "LED"},
    "FRM": {"系列说明": "高功率合金采样电阻", "器件类型": "合金电阻", "特殊用途": "高功率 | 电流采样"},
    "FPM": {"系列说明": "高功率合金电阻", "器件类型": "合金电阻", "特殊用途": "高功率"},
    "FPL": {"系列说明": "高功率低阻值厚膜贴片电阻", "器件类型": "厚膜电阻", "特殊用途": "高功率 | 低阻值"},
    "FPS": {"系列说明": "高功率抗浪涌贴片电阻", "器件类型": "厚膜电阻", "特殊用途": "高功率 | 抗浪涌"},
    "FQP": {"系列说明": "车规级高功率厚膜贴片电阻", "器件类型": "厚膜电阻", "特殊用途": "车规 | 高功率"},
    "FNL": {"系列说明": "低阻值低温漂厚膜片式电阻", "器件类型": "厚膜电阻", "特殊用途": "低阻值 | 低温漂"},
    "FRC-X": {"系列说明": "低温度系数厚膜片式电阻", "器件类型": "厚膜电阻", "特殊用途": "低温漂"},
    "FRH-X": {"系列说明": "高精度低温漂厚膜片式电阻", "器件类型": "厚膜电阻", "特殊用途": "高精度 | 低温漂"},
    "FRL-L": {"系列说明": "低阻低温漂厚膜片式电阻", "器件类型": "厚膜电阻", "特殊用途": "低阻值 | 低温漂"},
    "FPW": {"系列说明": "高功率宽电极厚膜电阻", "器件类型": "厚膜电阻", "特殊用途": "高功率 | 宽端子"},
    "FCW": {"系列说明": "宽电极厚膜贴片电阻", "器件类型": "厚膜电阻", "特殊用途": "宽端子"},
    "FRE": {"系列说明": "抗静电厚膜晶片电阻", "器件类型": "厚膜电阻", "特殊用途": "防静电"},
    "FRJ": {"系列说明": "低阻低温漂厚膜晶片电阻", "器件类型": "厚膜电阻", "特殊用途": "低阻值 | 低温漂"},
    "FRB": {"系列说明": "低温漂厚膜片式电阻", "器件类型": "厚膜电阻", "特殊用途": "低温漂"},
    "FCP": {"系列说明": "常规超高功率厚膜片式电阻", "器件类型": "厚膜电阻", "特殊用途": "高功率"},
    "FRC-P": {"系列说明": "无铅厚膜片式电阻", "器件类型": "厚膜电阻", "特殊用途": "无铅"},
    "FRZ": {"系列说明": "无磁厚膜片式电阻", "器件类型": "厚膜电阻", "特殊用途": "无磁"},
    "FRP-X": {"系列说明": "低温漂高功率厚膜片式电阻", "器件类型": "厚膜电阻", "特殊用途": "高功率 | 低温漂"},
    "FTH": {"系列说明": "高精度薄膜贴片电阻", "器件类型": "薄膜电阻", "特殊用途": "高精度 | 低温漂"},
    "FRT": {"系列说明": "薄膜贴片电阻", "器件类型": "薄膜电阻", "特殊用途": "高精度 | 低温漂"},
    "FQT": {"系列说明": "汽车级薄膜电阻", "器件类型": "薄膜电阻", "特殊用途": "车规 | 高精度 | 低温漂"},
    "FTR": {"系列说明": "抗硫化车规薄膜片式电阻", "器件类型": "薄膜电阻", "特殊用途": "车规 | 抗硫化 | 低温漂"},
    "FMB": {"系列说明": "薄膜合金贴片电阻", "器件类型": "合金电阻", "特殊用途": "低阻值 | 低温漂"},
    "FQA": {"系列说明": "车规厚膜贴片排阻", "器件类型": "厚膜电阻", "特殊用途": "车规 | 排阻"},
    "FRA": {"系列说明": "厚膜贴片排阻", "器件类型": "厚膜电阻", "特殊用途": "排阻"},
    "FAR": {"系列说明": "抗硫化车规厚膜贴片排阻", "器件类型": "厚膜电阻", "特殊用途": "车规 | 抗硫化 | 排阻"},
    "FRN": {"系列说明": "汽车级高品质抗硫化厚膜片式电阻", "器件类型": "厚膜电阻", "特殊用途": "车规 | 抗硫化"},
    "FQL-L": {"系列说明": "汽车级低阻低温漂厚膜片式电阻", "器件类型": "厚膜电阻", "特殊用途": "车规 | 低阻值 | 低温漂"},
    "FQS": {"系列说明": "车规抗浪涌抗硫化厚膜贴片电阻", "器件类型": "厚膜电阻", "特殊用途": "车规 | 抗浪涌 | 抗硫化"},
    "FQL": {"系列说明": "车规低阻厚膜电阻", "器件类型": "厚膜电阻", "特殊用途": "车规 | 低阻值"},
    "FUP": {"系列说明": "车规超高功率厚膜片式电阻", "器件类型": "厚膜电阻", "特殊用途": "车规 | 高功率 | 抗硫化"},
    "FQW": {"系列说明": "车规宽电极厚膜片式电阻", "器件类型": "厚膜电阻", "特殊用途": "车规 | 宽端子 | 抗硫化"},
    "FPR": {"系列说明": "车规高功率抗硫化厚膜电阻", "器件类型": "厚膜电阻", "特殊用途": "车规 | 高功率 | 抗硫化"},
    "FQV": {"系列说明": "车规高压抗硫化厚膜电阻", "器件类型": "厚膜电阻", "特殊用途": "车规 | 高压 | 抗硫化"},
    "FWP": {"系列说明": "高功率合金分流电阻", "器件类型": "合金电阻", "特殊用途": "车规 | 高功率 | 电流检测"},
    "FWPK": {"系列说明": "四端子合金贴片电阻", "器件类型": "合金电阻", "特殊用途": "四端子 | 高功率 | 电流检测"},
    "FMK": {"系列说明": "四引脚插件合金电阻", "器件类型": "合金电阻", "特殊用途": "车规 | 四端子 | 电流检测"},
    "FSM": {"系列说明": "全合金贴片电阻", "器件类型": "合金电阻", "特殊用途": "低阻值 | 电流检测"},
    "FCM": {"系列说明": "裸片合金高功率贴片电阻", "器件类型": "合金电阻", "特殊用途": "车规 | 高功率 | 电流检测"},
    "FMH": {"系列说明": "金属膜合金高功率电阻", "器件类型": "合金电阻", "特殊用途": "高功率 | 电流检测"},
    "FUS": {"系列说明": "高功率合金分流器", "器件类型": "合金电阻", "特殊用途": "车规 | 高功率 | 电流检测"},
    "FCR": {"系列说明": "插件合金电阻", "器件类型": "合金电阻", "特殊用途": "车规 | 电流检测"},
    "FSR": {"系列说明": "插件跳线电阻", "器件类型": "厚膜电阻", "特殊用途": "抗浪涌 | 电流检测"},
    "FSHM": {"系列说明": "高功率合金电阻", "器件类型": "合金电阻", "特殊用途": "车规 | 高功率 | 抗浪涌 | 抗硫化"},
    "FCS": {"系列说明": "大电流合金分流器", "器件类型": "合金电阻", "特殊用途": "车规 | 高功率 | 电流检测"},
    "FWK": {"系列说明": "高功率四引脚贴片合金电阻", "器件类型": "合金电阻", "特殊用途": "高功率 | 四端子 | 电流检测"},
    "FWKP": {"系列说明": "高功率低温漂四引脚贴片合金电阻", "器件类型": "合金电阻", "特殊用途": "高功率 | 低温漂 | 四端子 | 高精度 | 电流检测"},
    "FPCS": {"系列说明": "内置NTC温度传感器合金电阻", "器件类型": "合金电阻", "特殊用途": "电流检测"},
    "FCN": {"系列说明": "合金分流器电阻", "器件类型": "合金电阻", "特殊用途": "电流检测"},
    "FHS": {"系列说明": "分流器高功率合金电阻", "器件类型": "合金电阻", "特殊用途": "高功率 | 电流检测"},
    "FJR": {"系列说明": "电流感测贴片电阻", "器件类型": "合金电阻", "特殊用途": "电流检测"},
    "FSP": {"系列说明": "低温漂全合金贴片电阻", "器件类型": "合金电阻", "特殊用途": "低温漂 | 电流检测"},
    "FMS": {"系列说明": "半合金贴片电阻", "器件类型": "合金电阻", "特殊用途": "低阻值 | 电流检测"},
}

OFFICIAL_RESISTOR_BRAND_RULES = {
    "UNIROYAL": {"brand_tokens": UNIROYAL_BRAND_TOKENS, "profiles": UNIROYAL_OFFICIAL_SERIES_PROFILES},
    "TAI": {"brand_tokens": TAI_BRAND_TOKENS, "profiles": TAI_OFFICIAL_SERIES_PROFILES},
    "VIKING": {"brand_tokens": VIKING_BRAND_TOKENS, "profiles": VIKING_OFFICIAL_SERIES_PROFILES},
    "YAGEO": {"brand_tokens": YAGEO_BRAND_TOKENS, "profiles": YAGEO_OFFICIAL_SERIES_PROFILES},
    "RALEC": {"brand_tokens": RALEC_BRAND_TOKENS, "profiles": RALEC_OFFICIAL_SERIES_PROFILES},
    "SAMSUNG": {"brand_tokens": SAMSUNG_BRAND_TOKENS, "profiles": SAMSUNG_OFFICIAL_SERIES_PROFILES},
    "WALSIN": {"brand_tokens": WALSIN_BRAND_TOKENS, "profiles": WALSIN_OFFICIAL_SERIES_PROFILES},
    "FENGHUA": {"brand_tokens": FENGHUA_BRAND_TOKENS, "profiles": FENGHUA_OFFICIAL_SERIES_PROFILES},
    "FOJAN": {"brand_tokens": FOJAN_BRAND_TOKENS, "profiles": FOJAN_OFFICIAL_SERIES_PROFILES},
}

OFFICIAL_RESISTOR_SERIES_CODES = {
    code
    for rule in OFFICIAL_RESISTOR_BRAND_RULES.values()
    for code in rule.get("profiles", {}).keys()
}

MOJIBAKE_TEXT_REPLACEMENTS = {
    "鍘氳啘鐢甸樆": "厚膜电阻",
    "钖勮啘鐢甸樆": "薄膜电阻",
    "鍚堥噾鐢甸樆": "合金电阻",
    "缁曠嚎鐢甸樆": "绕线电阻",
    "纰宠啘鐢甸樆": "碳膜电阻",
    "閲戝睘姘у寲鑶滅數闃": "金属氧化膜电阻",
    "閸樻俺鍟橀悽鐢告▎": "厚膜电阻",
    "閽栧嫯鍟橀悽鐢告▎": "薄膜电阻",
    "缂佹洜鍤庨悽鐢告▎": "绕线电阻",
    "绾板疇鍟橀悽鐢告▎": "碳膜电阻",
    "楂樺姛鐜": "高功率",
    "楂樼簿": "高精度",
    "楂樺帇": "高压",
    "鎶楃～": "抗硫",
    "鎶楁氮娑": "抗浪涌",
    "杞﹁": "车规",
    "浣庨樆": "低阻",
    "瀹界瀛": "宽端子",
}


def clean_text(value: object) -> str:
    if value is None:
        return ""
    text = str(value).strip()
    if text.lower() in {"none", "nan"}:
        return ""
    for bad_text, good_text in MOJIBAKE_TEXT_REPLACEMENTS.items():
        text = text.replace(bad_text, good_text)
    text = text.replace("?", "")
    return text


def clean_brand(brand: object) -> str:
    return clean_text(brand)


def normalize_model_text(model: object) -> str:
    text = clean_text(model).upper()
    if text == "":
        return ""
    text = text.replace("Ω", "").replace("OHMS", "").replace("OHM", "")
    return re.sub(r"\s+", "", text)


def normalize_series_code(series: object) -> str:
    text = clean_text(series).upper()
    if text == "":
        return ""
    if text in OFFICIAL_RESISTOR_SERIES_CODES:
        return text
    if len(text) > 2 and text.endswith("T"):
        stripped = text[:-1]
        if stripped in OFFICIAL_RESISTOR_SERIES_CODES:
            return stripped
    return text


def identify_resistor_brand_family(brand: object) -> str:
    brand_text = clean_brand(brand)
    brand_upper = brand_text.upper()
    for family, rule in OFFICIAL_RESISTOR_BRAND_RULES.items():
        tokens = rule.get("brand_tokens", ())
        if any(token in brand_upper or token in brand_text for token in tokens):
            return family
    return ""


def _definitions_for_brand_family(family: str) -> dict[str, dict[str, str]]:
    rule = OFFICIAL_RESISTOR_BRAND_RULES.get(family, {})
    return rule.get("profiles", {})


def _match_known_series_prefix(text: str, definitions: dict[str, dict[str, str]]) -> str:
    compact = normalize_model_text(text)
    if compact == "":
        return ""
    for code in sorted(definitions.keys(), key=len, reverse=True):
        if compact.startswith(code):
            return code
    return ""


def _resolve_uniroyal_series_code_from_model(compact: str) -> str:
    direct = _match_known_series_prefix(compact, UNIROYAL_OFFICIAL_SERIES_PROFILES)
    if direct != "":
        return direct
    if re.match(r"^\d{4,5}[A-Z0-9]{2,}", compact):
        return "普通厚膜"
    return ""


def _resolve_generic_series_code_from_model(compact: str, family: str) -> str:
    return _match_known_series_prefix(compact, _definitions_for_brand_family(family))


def _resolve_walsin_series_code_from_model(compact: str) -> str:
    pattern_candidates = [
        r"^(?P<series>WW\d{2}[A-Z]{2})(?=\d|[A-Z]|-|_|$)",
        r"^(?P<series>FVF\d{2}F)(?=\d|[A-Z]|-|_|$)",
        r"^(?P<series>(?:WR|WF|MR|SR|WK|WM)\d{2}[A-Z]{1,2})(?=\d|[A-Z]|-|_|$)",
    ]
    for pattern in pattern_candidates:
        match = re.match(pattern, compact)
        if match is not None:
            return clean_text(match.group("series"))
    match = re.match(r"^(?P<series>[A-Z]{2,4})(?=\d)", compact)
    if match is None:
        return ""
    return clean_text(match.group("series"))


def resolve_walsin_resistor_series_code_from_model(model: object) -> str:
    return _resolve_walsin_series_code_from_model(normalize_model_text(model))


def _resolve_yageo_series_code_from_model(compact: str) -> str:
    if compact.startswith("VRS0402SR"):
        return "VRS0402SR"
    kd_match = re.match(r"^\d{3}(KD(?:07|10|20))", compact)
    if kd_match is not None:
        return clean_text(kd_match.group(1))
    for series in (
        "AA", "AC", "AF", "AR", "AT",
        "CFR", "FCR", "FC", "CF", "FKN", "FMP", "FMF", "HHV", "KNP", "MF", "MFR", "MMF", "MMP", "NKN",
        "PA", "PE", "PNP", "PS", "PT", "PU",
        "RC", "RE", "RL", "RSF", "RT", "RV", "SR",
    ):
        if compact.startswith(series):
            return series
    return ""


def _resolve_ralec_series_code_from_model(compact: str) -> str:
    direct = _match_known_series_prefix(compact, RALEC_OFFICIAL_SERIES_PROFILES)
    if direct != "":
        return direct
    if re.match(r"^LRE\d{4}-?2[C1A2345B]R\d{3,6}[DFGJ][A1245]$", compact):
        return "LRE"
    if re.match(r"^LR(?:0603|0805|1206|1210|2010|2512H|2512|2725|2728|4527S|4527)-?2[C1A2345B]R\d{3,6}[DFGJ][A1245]$", compact):
        return "LR"
    return ""


def _resolve_samsung_series_code_from_model(compact: str) -> str:
    for series in ("RCWS", "RCVS", "RCS", "RCB", "RCA", "RCW", "RCV", "RU", "RJ", "RL", "RC"):
        if compact.startswith(series):
            return series
    return ""


def _resolve_walsin_official_series_code_from_model(compact: str) -> str:
    for series in ("WW", "WF", "MR", "SR", "WR"):
        if compact.startswith(series):
            return series
    return ""


def _resolve_fenghua_series_code_from_model(compact: str) -> str:
    if compact.startswith("RC"):
        return "RC"
    if compact.startswith("RS"):
        return "RS"
    return ""


def _resolve_fojan_series_code_from_model(compact: str) -> str:
    return _match_known_series_prefix(compact, FOJAN_OFFICIAL_SERIES_PROFILES)


def _resolve_liz_series_code_from_model(compact: str) -> str:
    direct = _match_known_series_prefix(compact, LIZ_OFFICIAL_SERIES_PROFILES)
    if direct != "":
        return direct
    if re.match(r"^CR\d{4}", compact):
        return "CR"
    if re.match(r"^RM\d{4}", compact):
        return "RM"
    return ""


def _resolve_resi_series_code_from_model(compact: str) -> str:
    direct = _match_known_series_prefix(compact, RESI_OFFICIAL_SERIES_PROFILES)
    if direct != "":
        return direct
    match = re.match(r"^(PTFR|AECR|AHCR|HPCR|ETCR|EWWR|PWWR|MMFR|LMERW|LMER|LMF|MFR)", compact)
    return clean_text(match.group(1)) if match is not None else ""


def _resolve_tyohm_series_code_from_model(compact: str) -> str:
    direct = _match_known_series_prefix(compact, TYOHM_OFFICIAL_SERIES_PROFILES)
    if direct != "":
        return direct
    match = re.match(r"^(RMC|RN|RD|WMF|WLR|RJM)", compact)
    return clean_text(match.group(1)) if match is not None else ""


def _resolve_vo_series_code_from_model(compact: str) -> str:
    direct = _match_known_series_prefix(compact, VO_OFFICIAL_SERIES_PROFILES)
    if direct != "":
        return direct
    if re.match(r"^SCR\d{4}", compact) or re.match(r"^\d{4}[±+\-]?\d", compact):
        return "SCR"
    if compact.startswith("CR"):
        return "CR"
    if compact.startswith("MF"):
        return "MF"
    return ""


def _resolve_venkel_series_code_from_model(compact: str) -> str:
    direct = _match_known_series_prefix(compact, VENKEL_OFFICIAL_SERIES_PROFILES)
    if direct != "":
        return direct
    for pattern, series in (
        (r"^HPTF\d{4}", "HPTF"),
        (r"^TFCR\d{4}", "TFCR"),
        (r"^HPCR\d{4}", "HPCR"),
        (r"^CR\d{4}", "CR"),
    ):
        if re.match(pattern, compact):
            return series
    return ""


def _resolve_rcd_series_code_from_model(compact: str) -> str:
    direct = _match_known_series_prefix(compact, RCD_OFFICIAL_SERIES_PROFILES)
    if direct != "":
        return direct
    for pattern, series in (
        (r"^BLU\d{4}", "BLU"),
        (r"^RSF\d", "RSF"),
        (r"^GP\d", "GP"),
        (r"^125-", "125"),
        (r"^160-", "160"),
        (r"^175-", "175"),
    ):
        if re.match(pattern, compact):
            return series
    return ""


def _resolve_riedon_series_code_from_model(compact: str) -> str:
    direct = _match_known_series_prefix(compact, RIEDON_OFFICIAL_SERIES_PROFILES)
    if direct != "":
        return direct
    for pattern, series in (
        (r"^UB\d", "UB"),
        (r"^SM\d", "SM"),
        (r"^S[1-5]-", "S"),
        (r"^PFS\d", "PFS"),
        (r"^PFC\d", "PFC"),
        (r"^PF\d", "PF"),
        (r"^HVS\d{4}", "HVS"),
        (r"^10\d-", "100"),
    ):
        if re.match(pattern, compact):
            return series
    return ""


def _resolve_thunder_series_code_from_model(compact: str) -> str:
    direct = _match_known_series_prefix(compact, THUNDER_OFFICIAL_SERIES_PROFILES)
    if direct != "":
        return direct
    if compact.startswith("MELF-MFR0204"):
        return "MELF-MFR0204"
    if compact.startswith("MFR"):
        return "MFR"
    return ""


def _resolve_nte_series_code_from_model(compact: str) -> str:
    direct = _match_known_series_prefix(compact, NTE_OFFICIAL_SERIES_PROFILES)
    if direct != "":
        return direct
    for pattern, series in (
        (r"^SR1-", "SR1"),
        (r"^[EHLQ]W\d", "MO"),
        (r"^NTE\d", "NTE"),
    ):
        if re.match(pattern, compact):
            return series
    return ""


def _resolve_panasonic_series_code_from_model(compact: str) -> str:
    normalized = compact.replace("_", "-")
    direct = _match_known_series_prefix(normalized, PANASONIC_OFFICIAL_SERIES_PROFILES)
    if direct != "":
        return direct
    if normalized.replace("-", "").startswith("ERTJ0ER"):
        return "ERT-J0ER"
    era_match = re.match(r"^ERA-?(?P<size>\d{1,2})(?P<family>[AVKP])", normalized)
    if era_match is not None:
        return f"ERA-{era_match.group('size')}{era_match.group('family')}"
    erd_match = re.match(r"^(ERD-S\d+)", normalized)
    if erd_match is not None:
        return erd_match.group(1)
    erg_match = re.match(r"^(ERG-\d+[A-Z]+)", normalized)
    if erg_match is not None:
        return erg_match.group(1)
    erz_match = re.match(r"^(ERZ-[A-Z]\d+[A-Z])", normalized)
    if erz_match is not None:
        return erz_match.group(1)
    if normalized.startswith("ERO-S2PH"):
        return "ERO-S2PH"
    return ""


def _resolve_koa_series_code_from_model(compact: str) -> str:
    direct = _match_known_series_prefix(compact, KOA_OFFICIAL_SERIES_PROFILES)
    if direct != "":
        return direct
    for pattern, series in (
        (r"^HV73\d", "HV73"),
        (r"^RK73[BGHZ]?", "RK73"),
        (r"^SR73\d", "SR73"),
        (r"^SR73W", "SR73W"),
        (r"^WK73S", "WK73S"),
        (r"^WK73R", "WK73R"),
        (r"^SLR\d", "SLR"),
        (r"^CFS?", "CF"),
        (r"^MOS", "MOS"),
    ):
        if re.match(pattern, compact):
            return series
    return ""


def _resolve_vishay_series_code_from_model(compact: str) -> str:
    direct = _match_known_series_prefix(compact, VISHAY_OFFICIAL_SERIES_PROFILES)
    if direct != "":
        return direct
    for pattern, series in (
        (r"^C4A", "C4A"),
        (r"^C5K", "C5K"),
        (r"^CEA", "CEA"),
        (r"^J5K", "J5K"),
        (r"^W2A", "W2A"),
        (r"^MQ", "MQ"),
        (r"^PTS\d{4}", "PTS"),
        (r"^TFPT\d{4}", "TFPT"),
        (r"^TNPU\d{4}", "TNPU"),
        (r"^MCU\d{4}", "MCU"),
        (r"^MCT\d{4}", "MCT"),
        (r"^MCS\d{4}", "MCS"),
        (r"^MMU\d{4}", "MMU"),
        (r"^CP\d{4}", "CP"),
        (r"^CA\d{4}", "CA"),
        (r"^CH\d{4}", "CH"),
        (r"^NFR\d{4}", "NFR"),
        (r"^PTF\d+", "PTF"),
        (r"^RS\d{2}", "RS"),
        (r"^LTO\d+", "LTO"),
        (r"^D2TO\d+", "D2TO"),
        (r"^AC\d{4}", "AC"),
        (r"^ERL\d+", "ERL"),
        (r"^Y1624", "Y1624"),
        (r"^Y1628", "Y1628"),
        (r"^Y1629", "Y1629"),
        (r"^Y4073", "Y4073"),
        (r"^Y4076", "Y4076"),
        (r"^Y1487", "Y1487"),
        (r"^PCAN\d{4}", "PCAN"),
        (r"^UM[AB]\d{4}", "UMB/UMA"),
        (r"^SM-", "SM"),
        (r"^MSP\d", "MSP"),
        (r"^RCG\d{4}", "RCG"),
        (r"^MRS\d{4}", "MRS"),
        (r"^HVR\d{4}", "HVR"),
        (r"^RCC\d{4}", "RCC"),
        (r"^NTCLE", "NTCLE"),
        (r"^CW\d", "CW"),
    ):
        if re.match(pattern, compact):
            return series
    return ""


def _resolve_rohm_series_code_from_model(compact: str) -> str:
    direct = _match_known_series_prefix(compact, ROHM_OFFICIAL_SERIES_PROFILES)
    if direct != "":
        return direct
    if compact.startswith("TRR"):
        return "TRR"
    return ""


def _resolve_stackpole_series_code_from_model(compact: str) -> str:
    direct = _match_known_series_prefix(compact, STACKPOLE_OFFICIAL_SERIES_PROFILES)
    if direct != "":
        return direct
    for pattern, series in (
        (r"^SM(?:H|N)?\d{4}", "SM"),
        (r"^WW\d", "WW"),
        (r"^CFM?\d", "CF"),
        (r"^PCFM?\d", "PCF"),
        (r"^HDM\d", "HDM"),
        (r"^PRNF", "PRNF"),
        (r"^FRN\d", "FRN"),
        (r"^FRC\d", "FRC"),
        (r"^RVC\d", "RVC"),
        (r"^CSRT\d", "CSRT"),
        (r"^CSR\d", "CSR"),
        (r"^CB\d", "CB"),
        (r"^RNS", "RNS"),
        (r"^RSMF", "RSMF"),
        (r"^RSF", "RSF"),
    ):
        if re.match(pattern, compact):
            return series
    return ""


def _resolve_te_series_code_from_model(compact: str) -> str:
    direct = _match_known_series_prefix(compact, TE_OFFICIAL_SERIES_PROFILES)
    if direct != "":
        return direct
    for pattern, series in (
        (r"^350[34]", "3503/3504"),
        (r"^350[2-6]", "3500"),
        (r"^34[23]0", "3400"),
        (r"^35[2-6]\d", "3500"),
        (r"^CRGV", "CRGV"),
        (r"^CRG", "CRG"),
        (r"^ROX", "ROX"),
        (r"^RLP73", "RLP73"),
        (r"^RLW73", "RLW73"),
        (r"^RL73", "RL73"),
        (r"^RP73F", "RP73F"),
        (r"^SMF\d", "SMF"),
        (r"^SMW\d", "SMW"),
        (r"^CFR\d+", "CFR"),
        (r"^MPT\d+", "MPT"),
        (r"^SMA-", "SMA"),
        (r"^RR0\d", "RR"),
    ):
        if re.match(pattern, compact):
            return series
    return ""


def _resolve_fenghua_series_code_from_model_extended(compact: str) -> str:
    direct = _resolve_fenghua_series_code_from_model(compact)
    if direct != "":
        return direct
    for pattern, series in (
        (r"^TD\d{2}", "TD"),
        (r"^TE\d{2}", "TE"),
        (r"^TF\d{2}", "TF"),
        (r"^AB[A-Z]\d{2}", "AB"),
        (r"^AC[A-Z]\d{2}", "AC"),
        (r"^RH[CS]-", "RHC/RHS"),
        (r"^FNR", "FNR"),
    ):
        if re.match(pattern, compact):
            return series
    return ""


def _resolve_hyphen_prefix_series_code_from_model(compact: str) -> str:
    if "-" not in compact:
        return ""
    prefix = compact.split("-", 1)[0]
    return clean_text(prefix)


def _resolve_xicon_series_code_from_model(compact: str) -> str:
    if "-" not in compact:
        return ""
    parts = [part for part in compact.split("-") if part]
    if len(parts) < 2:
        return ""
    if parts[0] == "R":
        if len(parts) >= 3 and re.fullmatch(r"CR\d+[A-Z]*", parts[2], flags=re.I):
            return clean_text(f"R-{parts[1]}-{parts[2]}")
        return clean_text(f"R-{parts[1]}")
    series_parts = [clean_text(parts[0])]
    if len(parts) >= 2 and re.fullmatch(r"CR\d+[A-Z]*", parts[1], flags=re.I):
        series_parts.append(clean_text(parts[1]))
    return clean_text("-".join(part for part in series_parts if part != ""))


BRAND_MODEL_PREFIX_RESOLVERS: dict[str, Callable[[str], str]] = {
    "UNIROYAL": _resolve_uniroyal_series_code_from_model,
    "TAI": lambda compact: _resolve_generic_series_code_from_model(compact, "TAI"),
    "VIKING": lambda compact: _resolve_generic_series_code_from_model(compact, "VIKING"),
    "YAGEO": _resolve_yageo_series_code_from_model,
    "RALEC": _resolve_ralec_series_code_from_model,
    "SAMSUNG": _resolve_samsung_series_code_from_model,
    "WALSIN": _resolve_walsin_official_series_code_from_model,
    "FENGHUA": _resolve_fenghua_series_code_from_model_extended,
    "FOJAN": _resolve_fojan_series_code_from_model,
    "LIZ": _resolve_liz_series_code_from_model,
    "RESI": _resolve_resi_series_code_from_model,
    "TYOHM": _resolve_tyohm_series_code_from_model,
    "VO": _resolve_vo_series_code_from_model,
    "VENKEL": _resolve_venkel_series_code_from_model,
    "RCD": _resolve_rcd_series_code_from_model,
    "RIEDON": _resolve_riedon_series_code_from_model,
    "THUNDER": _resolve_thunder_series_code_from_model,
    "NTE": _resolve_nte_series_code_from_model,
    "VISHAY": _resolve_vishay_series_code_from_model,
    "KOA": _resolve_koa_series_code_from_model,
    "STACKPOLE": _resolve_stackpole_series_code_from_model,
    "PANASONIC": _resolve_panasonic_series_code_from_model,
    "ROHM": _resolve_rohm_series_code_from_model,
    "TE": _resolve_te_series_code_from_model,
}


def resolve_official_resistor_series_code_from_model(model: object, brand: object = "") -> str:
    family = identify_resistor_brand_family(brand)
    if family == "":
        return ""
    compact = normalize_model_text(model)
    if compact == "":
        return ""
    resolver = BRAND_MODEL_PREFIX_RESOLVERS.get(family)
    if resolver is not None:
        resolved = clean_text(resolver(compact))
        if resolved != "":
            return resolved
    return clean_text(_match_known_series_prefix(compact, _definitions_for_brand_family(family)))


def lookup_official_resistor_series_profile_by_code(brand: object, series: object) -> dict[str, str]:
    family = identify_resistor_brand_family(brand)
    if family == "":
        return {}
    definitions = _definitions_for_brand_family(family)
    series_code = normalize_series_code(series)
    if series_code == "":
        return {}
    profile = definitions.get(series_code)
    if not profile:
        inferred_code = resolve_official_resistor_series_code_from_model(series_code, brand)
        profile = definitions.get(inferred_code, {})
        if profile:
            series_code = inferred_code
    if not profile:
        return {}
    return {
        "系列": series_code,
        "系列说明": clean_text(profile.get("系列说明", "")),
        "器件类型": clean_text(profile.get("器件类型", "")),
        "特殊用途": clean_text(profile.get("特殊用途", "")),
    }


def lookup_official_resistor_series_profile_by_model(model: object, brand: object) -> dict[str, str]:
    series_code = resolve_official_resistor_series_code_from_model(model, brand)
    if series_code == "":
        return {}
    return lookup_official_resistor_series_profile_by_code(brand, series_code)


def infer_resistor_size_from_model(model: object) -> str:
    compact = normalize_model_text(model)
    if compact == "":
        return ""

    size_patterns = [
        r"^(?P<size>\d{4})(?=[A-Z0-9])",
        r"^[A-Z]{2,5}(?P<size>\d{4})(?=[A-Z0-9])",
        r"^[A-Z]{2,5}(?P<size>\d{2,4})(?=[A-Z0-9])",
    ]
    for pattern in size_patterns:
        match = re.match(pattern, compact)
        if match is not None:
            return clean_text(match.group("size"))
    return ""


def _match_series_pattern(compact: str, pattern: str) -> str:
    match = re.match(pattern, compact)
    if match is None:
        return ""
    series = clean_text(match.group("series"))
    return normalize_series_code(series)


def infer_resistor_series_code(model: object, brand: object = "") -> str:
    official_profile = lookup_official_resistor_series_profile_by_model(model, brand)
    if official_profile:
        return clean_text(official_profile.get("系列", ""))

    compact = normalize_model_text(model)
    if compact == "":
        return ""

    brand_text = clean_brand(brand)
    brand_upper = brand_text.upper()

    if any(token in brand_upper or token in brand_text for token in ("WALSIN", "华新科", "华科")):
        resolved = _resolve_walsin_series_code_from_model(compact)
        if resolved != "":
            return resolved

    if any(token in brand_upper or token in brand_text for token in ("YAGEO", "国巨")):
        resolved = _resolve_yageo_series_code_from_model(compact)
        if resolved != "":
            return resolved

    if any(token in brand_upper or token in brand_text for token in ("华星机电", "RIEDON", "NTE ELECTRONICS")):
        resolved = _resolve_hyphen_prefix_series_code_from_model(compact)
        if resolved != "":
            return resolved

    if any(token in brand_upper or token in brand_text for token in ("XICON",)):
        resolved = _resolve_xicon_series_code_from_model(compact)
        if resolved != "":
            return resolved

    patterns: list[str] = [
        r"^(?P<series>(?:MELF-)?MFR\d{4})(?=\d|/|-|$)",
        r"^(?P<series>RP73PF\d[A-Z])",
        r"^(?P<series>(?:CRCW|TNPW)\d{4})(?=\d|-|$)",
        r"^(?P<series>SMM\d{5}[A-Z])(?=\d|-|$)",
        r"^(?P<series>RMS\d{2}[A-Z]{2})",
        r"^(?P<series>RM\d{2}[A-Z]{2})",
        r"^(?P<series>ARG?\d{2}[A-Z]{2,3})",
        r"^(?P<series>[A-Z]{2,5}\d{2,4}[A-Z]{1,3})(?=\d|-|$)",
        r"^(?P<series>\d{4}[A-Z]\d[A-Z])(?=\d|-|$)",
        r"^(?P<series>\d{4}[A-Z]{2,3})(?=\d|-|$)",
    ]

    if any(token in brand_upper or token in brand_text for token in ("UNI-ROYAL", "UNIROYAL", "厚声")):
        patterns = [
            r"^(?P<series>\d{4}[A-Z]\d[A-Z])(?=\d|-|$)",
            r"^(?P<series>\d{4}[A-Z]{2,3})(?=\d|-|$)",
        ] + patterns

    if any(token in brand_upper or token in brand_text for token in ("VISHAY", "威世")):
        patterns = [
            r"^(?P<series>(?:CRCW|TNPW)\d{4})(?=\d|-|$)",
            r"^(?P<series>SMM\d{5}[A-Z])(?=\d|-|$)",
        ] + patterns

    seen_patterns = []
    for pattern in patterns:
        if pattern in seen_patterns:
            continue
        seen_patterns.append(pattern)
        series = _match_series_pattern(compact, pattern)
        if series:
            return series

    size_code = infer_resistor_size_from_model(compact)
    if size_code:
        return size_code
    return compact[:8]


def build_resistor_series_description(
    brand: object = "",
    series: object = "",
    component_type: object = "",
    special_use: object = "",
) -> str:
    brand_text = clean_brand(brand)
    series_text = clean_text(series)
    special_text = clean_text(special_use)
    component_text = clean_text(component_type) or "电阻"

    official_profile = lookup_official_resistor_series_profile_by_code(brand, series_text)
    official_desc = clean_text(official_profile.get("系列说明", ""))
    if official_desc != "":
        return official_desc

    parts = []
    if special_text:
        parts.append(special_text)
    if component_text:
        parts.append(component_text)
    if not parts:
        return ""
    return " ".join(parts) + "系列"


def infer_resistor_series_profile(
    model: object,
    brand: object = "",
    component_type: object = "",
    special_use: object = "",
) -> dict[str, str]:
    official_profile = lookup_official_resistor_series_profile_by_model(model, brand)
    if official_profile:
        return {
            "系列": clean_text(official_profile.get("系列", "")),
            "系列说明": clean_text(official_profile.get("系列说明", "")),
            "器件类型": clean_text(official_profile.get("器件类型", "")) or clean_text(component_type),
            "特殊用途": clean_text(official_profile.get("特殊用途", "")) or clean_text(special_use),
        }

    series = infer_resistor_series_code(model, brand=brand)
    return {
        "系列": series,
        "系列说明": build_resistor_series_description(
            brand=brand,
            series=series,
            component_type=component_type,
            special_use=special_use,
        ),
        "器件类型": clean_text(component_type),
        "特殊用途": clean_text(special_use),
    }


def _build_series_profiles(entries: dict[str, tuple[str, str, str]]) -> dict[str, dict[str, str]]:
    profiles: dict[str, dict[str, str]] = {}
    for code, (series_desc, component_type, special_use) in entries.items():
        profiles[code] = {
            "系列说明": series_desc,
            "器件类型": component_type,
            "特殊用途": special_use,
        }
    return profiles


VISHAY_OFFICIAL_SERIES_PROFILES = _build_series_profiles(
    {
        "CRCW": ("标准厚膜片式电阻器", "厚膜电阻", ""),
        "CRCW-HP": ("高功率脉冲防护厚膜片式电阻器", "厚膜电阻", "高功率"),
        "CMF": ("精密金属膜轴向电阻器", "薄膜电阻", "高精密"),
        "D/CRCW": ("标准厚膜片式电阻器", "厚膜电阻", ""),
        "D/CRCW-HR": ("高值厚膜片式电阻器", "厚膜电阻", ""),
        "D/CRCW-IF": ("脉冲防护厚膜片式电阻器", "厚膜电阻", ""),
        "D/CRCW-P": ("半精密厚膜片式电阻器", "厚膜电阻", ""),
        "ERC": ("工业级金属膜轴向电阻器", "薄膜电阻", ""),
        "MCA": ("专业薄膜片式电阻器", "薄膜电阻", "车规"),
        "MBB": ("精密薄膜电阻器", "薄膜电阻", ""),
        "MBA": ("精密薄膜电阻器", "薄膜电阻", ""),
        "MCT": ("精密薄膜电阻器", "薄膜电阻", ""),
        "M55342": ("军规高可靠薄膜电阻器", "薄膜电阻", "军规"),
        "D55342": ("军规高可靠薄膜电阻器", "薄膜电阻", "军规"),
        "MMA0204": ("MMA 0204 薄膜 MELF 电阻器", "薄膜电阻", "MELF"),
        "PAT": ("高精度薄膜芯片电阻器", "薄膜电阻", ""),
        "PLT": ("精密低 TCR 薄膜片式电阻器", "薄膜电阻", "高精度 | 低TCR"),
        "PLTT": ("高温精密低 TCR 薄膜片式电阻器", "薄膜电阻", "高温 | 高精度 | 低TCR"),
        "PNM": ("非磁性薄膜芯片电阻器", "薄膜电阻", "非磁性"),
        "P2TC": ("高精度薄膜芯片电阻器", "薄膜电阻", "高精度"),
        "PTN": ("精密薄膜片式电阻器", "薄膜电阻", "高精度"),
        "RCP": ("高功率厚膜片式电阻器", "厚膜电阻", "高功率"),
        "PHP": ("高功率厚膜片式电阻器", "厚膜电阻", "高功率"),
        "2500": ("厚膜片式电阻器", "厚膜电阻", ""),
        "RN50": ("军规金属膜电阻器", "薄膜电阻", "军规"),
        "RN50C": ("军规金属膜电阻器", "薄膜电阻", "军规"),
        "RN55": ("军规金属膜电阻器", "薄膜电阻", "军规"),
        "RN60": ("军规金属膜电阻器", "薄膜电阻", "军规"),
        "RN65": ("军规金属膜电阻器", "薄膜电阻", "军规"),
        "RN70": ("军规金属膜电阻器", "薄膜电阻", "军规"),
        "RN75": ("军规金属膜电阻器", "薄膜电阻", "军规"),
        "RLR05": ("军规轴向薄膜电阻器", "薄膜电阻", "军规"),
        "RLR07": ("军规轴向薄膜电阻器", "薄膜电阻", "军规"),
        "RLR20": ("军规轴向薄膜电阻器", "薄膜电阻", "军规"),
        "RLR32": ("军规轴向薄膜电阻器", "薄膜电阻", "军规"),
        "RNC50": ("高稳定薄膜电阻器", "薄膜电阻", "军规"),
        "RNC55": ("高稳定薄膜电阻器", "薄膜电阻", "军规"),
        "RNC60": ("高稳定薄膜电阻器", "薄膜电阻", "军规"),
        "RNC65": ("高稳定薄膜电阻器", "薄膜电阻", "军规"),
        "RNC70": ("高稳定薄膜电阻器", "薄膜电阻", "军规"),
        "RNC75": ("高稳定薄膜电阻器", "薄膜电阻", "军规"),
        "RNR50": ("军规金属膜电阻器", "薄膜电阻", "军规"),
        "RNR55": ("军规金属膜电阻器", "薄膜电阻", "军规"),
        "RNR60": ("军规金属膜电阻器", "薄膜电阻", "军规"),
        "RNR65": ("军规金属膜电阻器", "薄膜电阻", "军规"),
        "RNR70": ("军规金属膜电阻器", "薄膜电阻", "军规"),
        "RNR75": ("军规金属膜电阻器", "薄膜电阻", "军规"),
        "RL07": ("高精密低温漂金属膜引线电阻器", "薄膜电阻", "高精密 | 低TCR"),
        "RL20": ("高精密低温漂金属膜引线电阻器", "薄膜电阻", "高精密 | 低TCR"),
        "RNN50": ("军规金属膜电阻器", "薄膜电阻", "军规"),
        "RNN55": ("军规金属膜电阻器", "薄膜电阻", "军规"),
        "RNN60": ("军规金属膜电阻器", "薄膜电阻", "军规"),
        "RNN65": ("军规金属膜电阻器", "薄膜电阻", "军规"),
        "RNN70": ("军规金属膜电阻器", "薄膜电阻", "军规"),
        "RNN75": ("军规金属膜电阻器", "薄膜电阻", "军规"),
        "RWR74S": ("军规线绕电阻器", "绕线电阻", "军规"),
        "RWR74N": ("军规线绕电阻器", "绕线电阻", "军规"),
        "RWR78S": ("军规线绕电阻器", "绕线电阻", "军规"),
        "RWR78N": ("军规线绕电阻器", "绕线电阻", "军规"),
        "RWR80N": ("军规线绕电阻器", "绕线电阻", "军规"),
        "RWR80S": ("军规线绕电阻器", "绕线电阻", "军规"),
        "RWR81N": ("军规线绕电阻器", "绕线电阻", "军规"),
        "RWR81S": ("军规线绕电阻器", "绕线电阻", "军规"),
        "RWR81SR": ("军规线绕电阻器", "绕线电阻", "军规"),
        "RWR82N": ("军规线绕电阻器", "绕线电阻", "军规"),
        "RWR82S": ("军规线绕电阻器", "绕线电阻", "军规"),
        "RWR84N": ("军规线绕电阻器", "绕线电阻", "军规"),
        "RWR84S": ("军规线绕电阻器", "绕线电阻", "军规"),
        "RWR89N": ("军规线绕电阻器", "绕线电阻", "军规"),
        "RWR89S": ("军规线绕电阻器", "绕线电阻", "军规"),
        "SFR16": ("低噪声金属膜引线电阻器", "薄膜电阻", "低噪声"),
        "SFR25": ("标准金属膜引线电阻器", "薄膜电阻", ""),
        "SFR25H": ("高功率金属膜引线电阻器", "薄膜电阻", "高功率"),
        "SMM0204": ("薄膜 Mini-MELF 电阻器", "薄膜电阻", "Mini-MELF"),
        "RWR71N": ("军规线绕电阻器", "绕线电阻", "军规"),
        "RWR71S": ("军规线绕电阻器", "绕线电阻", "军规"),
        "TNPW": ("高稳定薄膜片式电阻器", "薄膜电阻", "高稳定"),
    }
)

VISHAY_OFFICIAL_SERIES_PROFILES.update(
    _build_series_profiles(
        {
            "OMM": ("Professional MELF thin film resistor", "钖勮啘鐢甸樆", "precision | MELF"),
            "MMU": ("Professional thin film MELF resistor", "钖勮啘鐢甸樆", "precision | MELF"),
            "MCS": ("Professional thin film chip resistor", "钖勮啘鐢甸樆", "precision"),
            "MCW": ("Wide-terminal thin film chip resistor", "钖勮啘鐢甸樆", "wide terminal | precision"),
            "MMB": ("Professional thin film MELF resistor", "钖勮啘鐢甸樆", "precision | MELF"),
            "SMM0207": ("Thin film Mini-MELF resistor", "钖勮啘鐢甸樆", "Mini-MELF"),
            "WSC": ("Surface-mount wirewound power resistor", "缁曠嚎鐢甸樆", "power"),
            "RCS": ("Automotive thick film chip resistor", "鍘氳啘鐢甸樆", "automotive"),
            "RCA": ("Automotive thick film chip resistor", "鍘氳啘鐢甸樆", "automotive"),
            "RCWE": ("Wide-terminal thick film chip resistor", "鍘氳啘鐢甸樆", "wide terminal"),
            "CRHP": ("High-power thick film chip resistor", "鍘氳啘鐢甸樆", "high power"),
            "CRHV": ("High-voltage thick film chip resistor", "鍘氳啘鐢甸樆", "high voltage"),
            "DTO": ("Thick film power resistor", "鍘氳啘鐢甸樆", "power"),
            "RCL": ("Long-side terminal thick film chip resistor", "鍘氳啘鐢甸樆", "wide terminal"),
            "ROX": ("Metal oxide film resistor", "metal oxide resistor", "metal oxide"),
            "RNX": ("Precision metal oxide film resistor", "metal oxide resistor", "precision | metal oxide"),
            "CMA": ("Carbon film MELF resistor", "纰宠啘鐢甸樆", "MELF"),
            "CMB": ("Carbon film MELF resistor", "纰宠啘鐢甸樆", "MELF"),
        }
    )
)

KOA_OFFICIAL_SERIES_PROFILES = _build_series_profiles(
    {
        "HV73": ("高压芯片电阻器", "厚膜电阻", "高压"),
        "RK73": ("通用厚膜芯片电阻器", "厚膜电阻", ""),
        "RK73B": ("通用厚膜芯片电阻器", "厚膜电阻", ""),
        "RK73G": ("高精度厚膜芯片电阻器", "厚膜电阻", "高精度"),
        "RK73H": ("通用厚膜芯片电阻器", "厚膜电阻", ""),
        "RK73Z": ("通用厚膜芯片电阻器", "厚膜电阻", ""),
        "RN73": ("角形金属膜芯片电阻器", "薄膜电阻", "高精度"),
        "RN73H": ("高精度金属膜芯片电阻器", "薄膜电阻", "高精度"),
        "RN73R": ("高精度金属膜芯片电阻器", "薄膜电阻", "高精度"),
        "RNS": ("引线高精度金属膜电阻器", "薄膜电阻", "高精度"),
        "RS73": ("高精度高可靠金属膜芯片电阻器", "薄膜电阻", "高可靠"),
        "SG73": ("浪涌/脉冲抗性芯片电阻器", "厚膜电阻", "抗浪涌"),
        "SG73G": ("浪涌/脉冲抗性芯片电阻器", "厚膜电阻", "抗浪涌"),
        "SG73P": ("耐脉冲芯片电阻器", "厚膜电阻", "抗浪涌"),
        "SG73S": ("耐脉冲芯片电阻器", "厚膜电阻", "抗浪涌"),
        "WG73": ("浪涌抗性芯片电阻器", "厚膜电阻", "抗浪涌"),
        "WN73H": ("高精度宽端子金属膜芯片电阻器", "薄膜电阻", "高可靠"),
        "RF73": ("熔断电阻器", "厚膜电阻", "熔断"),
        "TLRZ": ("大电流跳线", "跳线", ""),
        "WK73R": ("宽端子高功率芯片电阻器", "厚膜电阻", "高功率"),
    }
)

STACKPOLE_OFFICIAL_SERIES_PROFILES = _build_series_profiles(
    {
        "FCR": ("可调厚膜芯片电阻器", "厚膜电阻", ""),
        "HMC": ("高功率厚膜芯片电阻器", "厚膜电阻", "高功率"),
        "HVCB": ("高压厚膜芯片电阻器", "厚膜电阻", "高压"),
        "MLF": ("金属膜引线电阻器", "薄膜电阻", ""),
        "MLFA": ("车规金属膜引线电阻器", "薄膜电阻", "车规"),
        "MLFM": ("金属膜引线电阻器", "薄膜电阻", ""),
        "RGC": ("金阻挡厚膜芯片电阻器", "厚膜电阻", ""),
        "RMCF": ("通用厚膜芯片电阻器", "厚膜电阻", ""),
        "RMCG": ("金阻挡厚膜芯片电阻器", "厚膜电阻", ""),
        "RMCP": ("通用高功率厚膜芯片电阻器", "厚膜电阻", "高功率"),
        "RMCS": ("抗硫厚膜芯片电阻器", "厚膜电阻", "抗硫"),
        "RMCW": ("宽端子厚膜芯片电阻器", "厚膜电阻", "宽端子"),
        "RMEA": ("车规抗硫厚膜芯片电阻器", "厚膜电阻", "车规/抗硫"),
        "RMEF": ("通用厚膜芯片电阻器", "厚膜电阻", ""),
        "RHC": ("高功率厚膜片式电阻器", "厚膜电阻", "高功率"),
        "RNAN": ("薄膜高功率铝氮化物基芯片电阻器", "薄膜电阻", "高功率"),
        "RNCA": ("车规抗硫薄膜芯片电阻器", "薄膜电阻", "车规/抗硫"),
        "RNCF": ("精密薄膜芯片电阻器", "薄膜电阻", "高精度"),
        "RNCP": ("抗硫高功率薄膜芯片电阻器", "薄膜电阻", "抗硫/高功率"),
        "RNCS": ("防潮精密薄膜芯片电阻器", "薄膜电阻", "防潮"),
        "RNF": ("通用金属膜引线电阻器", "薄膜电阻", ""),
        "RNMF": ("通用金属膜引线电阻器", "薄膜电阻", ""),
        "RPC": ("抗脉冲厚膜片式电阻器", "厚膜电阻", "抗脉冲"),
        "RTAN": ("钽氮化物薄膜芯片电阻器", "薄膜电阻", "抗硫"),
        "RMWA": ("车规宽端子厚膜芯片电阻器", "厚膜电阻", "车规/宽端子"),
    }
)

PANASONIC_OFFICIAL_SERIES_PROFILES = _build_series_profiles(
    {
        "ERA-1A": ("高精度薄膜芯片电阻器", "薄膜电阻", "高可靠"),
        "ERA-2A": ("高精度薄膜芯片电阻器", "薄膜电阻", "高可靠"),
        "ERA-3A": ("高精度薄膜芯片电阻器", "薄膜电阻", "高可靠"),
        "ERA-6A": ("高精度薄膜芯片电阻器", "薄膜电阻", "高可靠"),
        "ERA-8A": ("高精度薄膜芯片电阻器", "薄膜电阻", "高可靠"),
        "ERA-2V": ("高精度薄膜芯片电阻器", "薄膜电阻", "高可靠"),
        "ERA-3V": ("高精度薄膜芯片电阻器", "薄膜电阻", "高可靠"),
        "ERA-6V": ("高精度薄膜芯片电阻器", "薄膜电阻", "高可靠"),
        "ERA-8V": ("高精度薄膜芯片电阻器", "薄膜电阻", "高可靠"),
        "ERJ": ("厚膜芯片电阻器", "厚膜电阻", ""),
        "ERJ-B": ("厚膜芯片电阻器", "厚膜电阻", ""),
        "ERJ-BW": ("宽端子厚膜芯片电阻器", "厚膜电阻", "宽端子"),
        "ERJ-H": ("高温厚膜芯片电阻器", "厚膜电阻", "高温"),
        "ERJ-LW": ("宽端子厚膜芯片电阻器", "厚膜电阻", "宽端子"),
        "ERJ-S": ("抗硫化厚膜芯片电阻器", "厚膜电阻", "抗硫"),
        "ERJ-U": ("抗硫化厚膜芯片电阻器", "厚膜电阻", "抗硫"),
        "ERJ-U0X": ("抗硫化厚膜芯片电阻器", "厚膜电阻", "抗硫/抗浪涌"),
        "ERJ-U2R": ("高精度抗硫化厚膜芯片电阻器", "厚膜电阻", "抗硫"),
        "ERJ-U3R": ("高精度抗硫化厚膜芯片电阻器", "厚膜电阻", "抗硫"),
        "ERJ-U6R": ("高精度抗硫化厚膜芯片电阻器", "厚膜电阻", "抗硫"),
        "ERJ-UP": ("抗硫化抗浪涌厚膜芯片电阻器", "厚膜电阻", "抗硫/抗浪涌"),
        "ERJC1": ("抗硫化高功率宽端子厚膜芯片电阻器", "厚膜电阻", "抗硫/高功率"),
        "ERJP": ("高功率厚膜芯片电阻器", "厚膜电阻", "高功率"),
        "ERJPB": ("高精度厚膜芯片电阻器", "厚膜电阻", "高精度"),
        "ERJPC3": ("高精度厚膜芯片电阻器", "厚膜电阻", "高精度"),
        "ERJPC6": ("高精度厚膜芯片电阻器", "厚膜电阻", "高精度"),
        "ERJT": ("厚膜芯片电阻器", "厚膜电阻", ""),
    }
)

ROHM_OFFICIAL_SERIES_PROFILES = _build_series_profiles(
    {
        "ESR": ("抗浪涌厚膜芯片电阻器", "厚膜电阻", "抗浪涌"),
        "KTR": ("高压厚膜芯片电阻器", "厚膜电阻", "高压"),
        "LTR": ("宽端子高功率厚膜芯片电阻器", "厚膜电阻", "高功率"),
        "LHR": ("宽端子高功率低TCR厚膜芯片电阻器", "厚膜电阻", "高功率"),
        "MCR": ("通用厚膜芯片电阻器", "厚膜电阻", ""),
        "MCRE": ("通用厚膜芯片电阻器", "厚膜电阻", ""),
        "MCRL": ("高功率低阻厚膜芯片电阻器", "厚膜电阻", "高功率"),
        "MCRS": ("通用厚膜芯片电阻器", "厚膜电阻", ""),
        "MNR": ("通用厚膜芯片电阻器", "厚膜电阻", ""),
        "SDR": ("高抗浪涌厚膜芯片电阻器", "厚膜电阻", "抗浪涌"),
        "SFR": ("抗硫厚膜芯片电阻器", "厚膜电阻", "抗硫"),
        "UCR": ("通用厚膜芯片电阻器", "厚膜电阻", ""),
    }
)

SUSUMU_OFFICIAL_SERIES_PROFILES = _build_series_profiles(
    {
        "HRG": ("高功率薄膜芯片电阻器", "薄膜电阻", "高功率"),
        "NRG": ("非磁性金属薄膜芯片电阻器", "薄膜电阻", "非磁性"),
        "PRG": ("高功率薄膜芯片电阻器", "薄膜电阻", "高功率"),
        "RG": ("最高精度金属薄膜芯片电阻器", "薄膜电阻", "高精度"),
        "RGA": ("高温金属薄膜芯片电阻器", "薄膜电阻", "高温"),
        "RGT": ("宽温度范围金属薄膜芯片电阻器", "薄膜电阻", "宽温"),
        "RGV": ("高压金属薄膜芯片电阻器", "薄膜电阻", "高压"),
        "RM": ("电阻网络", "电阻网络", ""),
        "RS": ("音频薄膜芯片电阻器", "薄膜电阻", "高精度"),
        "RT": ("高温薄膜芯片电阻器", "薄膜电阻", "高温"),
        "RR": ("通用薄膜芯片电阻器", "薄膜电阻", ""),
        "URG": ("最高可靠性金属薄膜芯片电阻器", "薄膜电阻", "高可靠"),
    }
)

TE_OFFICIAL_SERIES_PROFILES = _build_series_profiles(
    {
        "CPF": ("高精度薄膜芯片电阻器", "薄膜电阻", "高精度"),
        "CRGH": ("高功率厚膜芯片电阻器", "厚膜电阻", "高功率"),
        "CRGP": ("高功率厚膜芯片电阻器", "厚膜电阻", "高功率"),
        "RA73F": ("厚膜芯片电阻器", "厚膜电阻", ""),
        "RN73": ("高精度薄膜芯片电阻器", "薄膜电阻", "高精度"),
        "RN73C": ("高精度薄膜芯片电阻器", "薄膜电阻", "高精度"),
        "RN73D": ("高精度薄膜芯片电阻器", "薄膜电阻", "高精度"),
        "RP73D": ("高精度薄膜芯片电阻器", "薄膜电阻", "高精度"),
        "RP73PF": ("高精度薄膜芯片电阻器", "薄膜电阻", "高精度"),
        "RQ73C": ("高精度薄膜芯片电阻器", "薄膜电阻", "高精度"),
        "RLC73": ("高功率厚膜芯片电阻器", "厚膜电阻", "高功率"),
        "RU73X": ("抗硫厚膜芯片电阻器", "厚膜电阻", "抗硫"),
    }
)

KAMAYA_OFFICIAL_SERIES_PROFILES = _build_series_profiles(
    {
        "RMCU": ("高功率抗浪涌厚膜芯片电阻器", "厚膜电阻", "高功率/抗浪涌"),
        "RMCH": ("车规高功率厚膜芯片电阻器", "厚膜电阻", "车规/高功率"),
        "RMGW": ("车规抗硫厚膜芯片电阻器", "厚膜电阻", "车规/抗硫"),
        "RMAW": ("车规抗硫厚膜芯片电阻器", "厚膜电阻", "车规/抗硫"),
        "RVAC": ("车规高压抗硫厚膜芯片电阻器", "厚膜电阻", "车规/高压/抗硫"),
        "RPCH": ("车规抗浪涌厚膜芯片电阻器", "厚膜电阻", "车规/抗浪涌"),
        "RPGW": ("车规高功率抗硫厚膜芯片电阻器", "厚膜电阻", "车规/高功率/抗硫"),
        "RMC": ("车规/通用厚膜芯片电阻器", "厚膜电阻", "车规/通用"),
        "RGC": ("车规通用厚膜芯片电阻器", "厚膜电阻", "车规"),
        "RNC": ("通用厚膜芯片电阻器", "厚膜电阻", ""),
        "RMPC": ("高功率厚膜芯片电阻器", "厚膜电阻", "高功率"),
        "TWMC": ("车规宽端子厚膜芯片电阻器", "厚膜电阻", "车规/宽端子"),
        "FCR": ("通用厚膜芯片电阻器", "厚膜电阻", ""),
        "RVC": ("车规高压厚膜芯片电阻器", "厚膜电阻", "车规/高压"),
        "RZC": ("高压厚膜芯片电阻器", "厚膜电阻", "高压"),
        "RPC": ("车规抗浪涌厚膜芯片电阻器", "厚膜电阻", "车规/抗浪涌"),
        "RBX": ("车规高功率厚膜芯片电阻器", "厚膜电阻", "车规/高功率"),
        "RCC": ("低阻厚膜芯片电阻器", "厚膜电阻", "低阻"),
        "RLC": ("车规低阻厚膜芯片电阻器", "厚膜电阻", "车规/低阻"),
        "RLP": ("车规低阻厚膜芯片电阻器", "厚膜电阻", "车规/低阻"),
        "MLP": ("车规低阻厚膜芯片电阻器", "厚膜电阻", "车规/低阻"),
        "MLP63C": ("车规低阻厚膜芯片电阻器", "厚膜电阻", "车规/低阻"),
        "WLP63": ("低阻厚膜芯片电阻器", "厚膜电阻", "低阻"),
        "TWLC": ("车规低阻厚膜芯片电阻器", "厚膜电阻", "车规/低阻"),
        "RAC": ("电阻网络", "电阻网络", ""),
        "RAAW": ("车规抗硫电阻网络", "电阻网络", "车规/抗硫"),
        "LTC": ("热敏电阻器", "热敏电阻", ""),
        "LPT": ("热敏电阻器", "热敏电阻", ""),
    }
)

MERITEK_OFFICIAL_SERIES_PROFILES = _build_series_profiles(
    {
        "CR": ("通用厚膜贴片电阻", "厚膜电阻", ""),
        "RN73": ("精密薄膜贴片电阻", "薄膜电阻", "高精密"),
    }
)
MERITEK_OFFICIAL_SERIES_PROFILES.update(
    _build_series_profiles(
        {
            "MVR05D": ("Meritek MVR05D 5mm 径向引线金属氧化物压敏电阻（MOV）", "引线型压敏电阻", "MOV | 浪涌抑制 | 径向引线 | 5mm"),
            "MVR07D": ("Meritek MVR07D 7mm 径向引线金属氧化物压敏电阻（MOV）", "引线型压敏电阻", "MOV | 浪涌抑制 | 径向引线 | 7mm"),
            "MVR10D": ("Meritek MVR10D 10mm 径向引线金属氧化物压敏电阻（MOV）", "引线型压敏电阻", "MOV | 浪涌抑制 | 径向引线 | 10mm"),
            "MVR14D": ("Meritek MVR14D 14mm 径向引线金属氧化物压敏电阻（MOV）", "引线型压敏电阻", "MOV | 浪涌抑制 | 径向引线 | 14mm"),
            "MVR20D": ("Meritek MVR20D 20mm 径向引线金属氧化物压敏电阻（MOV）", "引线型压敏电阻", "MOV | 浪涌抑制 | 径向引线 | 20mm"),
            "MVR05D-S": ("Meritek MVR-S 5mm 高浪涌径向引线金属氧化物压敏电阻（MOV）", "引线型压敏电阻", "MOV | 高浪涌 | 径向引线 | 5mm"),
            "MVR07D-S": ("Meritek MVR-S 7mm 高浪涌径向引线金属氧化物压敏电阻（MOV）", "引线型压敏电阻", "MOV | 高浪涌 | 径向引线 | 7mm"),
            "MVR10D-S": ("Meritek MVR-S 10mm 高浪涌径向引线金属氧化物压敏电阻（MOV）", "引线型压敏电阻", "MOV | 高浪涌 | 径向引线 | 10mm"),
            "MVR14D-S": ("Meritek MVR-S 14mm 高浪涌径向引线金属氧化物压敏电阻（MOV）", "引线型压敏电阻", "MOV | 高浪涌 | 径向引线 | 14mm"),
            "MVR20D-S": ("Meritek MVR-S 20mm 高浪涌径向引线金属氧化物压敏电阻（MOV）", "引线型压敏电阻", "MOV | 高浪涌 | 径向引线 | 20mm"),
        }
    )
)


def _resolve_meritek_series_code_from_model(compact: str) -> str:
    direct = _match_known_series_prefix(compact, MERITEK_OFFICIAL_SERIES_PROFILES)
    if direct != "":
        return direct
    match = re.match(r"^(MVR(?:05|07|10|14|20)D)", compact)
    if match is None:
        return ""
    series = clean_text(match.group(1))
    if compact.endswith("-S") and f"{series}-S" in MERITEK_OFFICIAL_SERIES_PROFILES:
        return f"{series}-S"
    return series


BRAND_MODEL_PREFIX_RESOLVERS["MERITEK"] = _resolve_meritek_series_code_from_model

LIZ_OFFICIAL_SERIES_PROFILES = _build_series_profiles(
    {
        "CR": ("通用厚膜贴片电阻", "厚膜电阻", "通用"),
        "RC": ("高压厚膜贴片电阻", "厚膜电阻", "高压"),
        "RL": ("低温漂厚膜贴片电阻", "厚膜电阻", "低TCR"),
        "PF": ("无铅厚膜贴片电阻", "厚膜电阻", "无铅"),
        "UR": ("低阻低TCR高功率厚膜贴片电阻", "厚膜电阻", "低阻 | 低TCR | 高功率 | 电流检测"),
        "RM": ("合金电流检测贴片电阻", "合金电阻", "电流检测 | 低阻"),
        "CA": ("凸电极厚膜排阻", "贴片电阻", "排阻"),
    }
)

RESI_OFFICIAL_SERIES_PROFILES = _build_series_profiles(
    {
        "PTFR": ("精密薄膜贴片电阻", "薄膜电阻", "高精度 | 低TCR | 车规"),
        "AECR": ("车规厚膜贴片电阻", "厚膜电阻", "车规 | AEC-Q200"),
        "AHCR": ("大功率贴片厚膜电阻", "厚膜电阻", "高功率 | 抗硫 | 车规"),
        "HPCR": ("高功率厚膜贴片电阻", "厚膜电阻", "高功率"),
        "ETCR": ("普通厚膜贴片电阻", "厚膜电阻", "通用"),
        "EWWR": ("涂覆型线绕固定电阻", "绕线电阻", "高功率 | 抗脉冲"),
        "PWWR": ("大功率线绕插件电阻", "绕线电阻", "高功率"),
        "MMFR": ("精密金属膜插件电阻", "薄膜电阻", "高精度 | 低TCR"),
        "PMFR": ("精密金属膜插件电阻", "薄膜电阻", "高精度 | 低TCR"),
        "LMERW": ("低阻合金电流检测电阻", "合金电阻", "低阻 | 电流检测"),
        "LMER": ("低阻合金电流检测电阻", "合金电阻", "低阻 | 电流检测"),
        "LMF": ("低阻合金电流检测电阻", "合金电阻", "低阻 | 电流检测"),
        "MFR": ("金属膜插件电阻", "薄膜电阻", "高精度"),
        "HVLR": ("高压厚膜插件电阻", "厚膜电阻", "高压"),
        "HVHR": ("高阻高压厚膜插件电阻", "厚膜电阻", "高压 | 高阻"),
        "TCTR": ("厚膜贴片热敏电阻", "热敏电阻", "NTC | 车规"),
    }
)

TYOHM_OFFICIAL_SERIES_PROFILES = _build_series_profiles(
    {
        "RMC": ("通用厚膜贴片电阻", "厚膜电阻", "通用"),
        "RN": ("金属膜插件电阻", "薄膜电阻", "高精度"),
        "RD": ("碳膜插件电阻", "碳膜电阻", "通用"),
        "WMF": ("浪涌抑制NTC热敏电阻", "热敏电阻", "NTC"),
        "WLR": ("氧化锌压敏电阻", "贴片压敏电阻", "压敏"),
        "RJM": ("精密金属膜电阻", "薄膜电阻", "高精度"),
    }
)

EVER_OHMS_OFFICIAL_SERIES_PROFILES = _build_series_profiles(
    {
        "CR": ("通用厚膜贴片电阻", "厚膜电阻", "通用"),
        "CRH": ("高功率厚膜贴片电阻", "厚膜电阻", "高功率"),
        "TR": ("精密薄膜贴片电阻", "薄膜电阻", "高精度"),
        "TP": ("精密薄膜贴片电阻", "薄膜电阻", "高精度 | 低TCR"),
        "QR": ("车规宽端子厚膜贴片电阻", "厚膜电阻", "车规 | 宽端子 | AEC-Q200"),
        "HR": ("高压厚膜贴片电阻", "厚膜电阻", "高压"),
        "FCR": ("保险丝型厚膜贴片电阻", "贴片电阻", "熔断 | 保险丝型"),
    }
)

CAL_CHIP_OFFICIAL_SERIES_PROFILES = _build_series_profiles(
    {
        "RM": ("通用厚膜贴片电阻", "厚膜电阻", ""),
        "RN": ("精密薄膜贴片电阻", "薄膜电阻", "高精密"),
    }
)

OHMITE_OFFICIAL_SERIES_PROFILES = _build_series_profiles(
    {
        "ACPP": ("精密薄膜贴片电阻", "薄膜电阻", "高精密"),
        "MRA": ("精密 MELF 电阻", "薄膜电阻", "高精密 | MELF"),
        "MOX": ("高压金属氧化膜/厚膜电阻", "金属氧化膜电阻", "高压"),
        "RW": ("线绕功率电阻", "绕线电阻", "高功率"),
        "SM": ("表面贴装功率电阻", "厚膜电阻", "高功率"),
        "MC": ("表面贴装功率电阻", "厚膜电阻", "高功率"),
        "OJ": ("碳质合成电阻", "碳膜电阻", "碳质合成"),
        "OL": ("碳质合成电阻", "碳膜电阻", "碳质合成"),
    }
)

OHMITE_OFFICIAL_SERIES_PROFILES.update(
    _build_series_profiles(
        {
            "RH": ("Ohmite RH 铝壳线绕功率电阻", "绕线电阻", "高功率 | 铝壳"),
            "RN": ("Ohmite RN 精密线绕功率电阻", "绕线电阻", "高功率 | 高精度"),
            "WN": ("Ohmite WN 线绕功率电阻", "绕线电阻", "高功率"),
            "WHE": ("Ohmite WHE 高功率线绕电阻", "绕线电阻", "高功率"),
            "WH": ("Ohmite WH 小型模压线绕功率电阻", "绕线电阻", "高功率 | 模压封装"),
            "WL": ("Ohmite WL 低阻电流检测线绕电阻", "绕线电阻", "低阻 | 电流检测"),
            "HVC": ("Ohmite HVC 高压厚膜芯片电阻", "厚膜电阻", "高压"),
            "TKH": ("Ohmite TKH 高功率厚膜功率电阻", "厚膜电阻", "高功率 | 厚膜"),
            "MEV": ("Ohmite MEV 高压厚膜电阻", "厚膜电阻", "高压"),
            "FCSL": ("Ohmite FCSL 金属箔电流检测电阻", "合金电阻", "低阻 | 电流检测"),
        }
    )
)

BOURNS_OFFICIAL_SERIES_PROFILES = _build_series_profiles(
    {
        "CR": ("通用厚膜贴片电阻", "厚膜电阻", ""),
        "CRT": ("精密薄膜贴片电阻", "薄膜电阻", "高精密"),
        "CRM": ("高功率厚膜贴片电阻", "厚膜电阻", "高功率"),
        "PWR": ("功率电阻", "绕线电阻", "高功率"),
    }
)

SUNWAY_OFFICIAL_SERIES_PROFILES = _build_series_profiles(
    {
        "SC": ("通用厚膜贴片电阻", "厚膜电阻", ""),
        "SM": ("低阻厚膜贴片电阻", "厚膜电阻", "低阻 | 电流检测"),
    }
)

VO_OFFICIAL_SERIES_PROFILES = _build_series_profiles(
    {
        "SCR": ("通用厚膜贴片电阻", "厚膜电阻", "通用"),
        "CR": ("碳膜插件电阻", "碳膜电阻", "通用"),
        "MF": ("金属膜插件电阻", "薄膜电阻", "通用 | 高精度"),
    }
)

VENKEL_OFFICIAL_SERIES_PROFILES = _build_series_profiles(
    {
        "CR": ("通用厚膜贴片电阻", "厚膜电阻", "通用"),
        "HPCR": ("高功率厚膜贴片电阻", "厚膜电阻", "高功率"),
        "TFCR": ("精密薄膜贴片电阻", "薄膜电阻", "高精度 | 低TCR"),
        "HPTF": ("高功率精密薄膜贴片电阻", "薄膜电阻", "高功率 | 高精度 | 低TCR"),
    }
)

RCD_OFFICIAL_SERIES_PROFILES = _build_series_profiles(
    {
        "BLU": ("精密薄膜贴片电阻", "薄膜电阻", "高精度 | 低TCR"),
        "GP": ("通用金属膜插件电阻", "薄膜电阻", "通用"),
        "RSF": ("阻燃金属氧化膜插件电阻", "金属氧化膜电阻", "阻燃"),
        "125": ("轴向绕线功率电阻", "绕线电阻", "高功率"),
        "160": ("轴向绕线功率电阻", "绕线电阻", "高功率"),
        "175": ("轴向绕线功率电阻", "绕线电阻", "高功率"),
    }
)

RIEDON_OFFICIAL_SERIES_PROFILES = _build_series_profiles(
    {
        "UB": ("脉冲功率绕线电阻", "绕线电阻", "高功率 | 抗脉冲"),
        "S": ("精密功率绕线电阻", "绕线电阻", "高功率 | 高精度"),
        "SM": ("表面贴装功率绕线电阻", "绕线电阻", "高功率 | 贴片"),
        "PF": ("功率薄膜电阻", "薄膜电阻", "高功率"),
        "PFS": ("表面贴装功率薄膜电阻", "薄膜电阻", "高功率 | 贴片"),
        "PFC": ("TO封装厚膜功率电阻", "厚膜电阻", "高功率 | TO封装"),
        "HVS": ("高压厚膜贴片电阻", "厚膜电阻", "高压"),
        "100": ("精密绕线电阻", "绕线电阻", "高精度"),
        "PF1262": ("功率薄膜电阻", "薄膜电阻", "高功率"),
        "PF2203": ("功率薄膜电阻", "薄膜电阻", "高功率"),
        "PF2205": ("功率薄膜电阻", "薄膜电阻", "高功率"),
        "PF2472": ("功率薄膜电阻", "薄膜电阻", "高功率"),
        "PFC10": ("TO封装厚膜功率电阻", "厚膜电阻", "高功率 | TO封装"),
        "PFS35": ("表面贴装功率薄膜电阻", "薄膜电阻", "高功率 | 贴片"),
    }
)

THUNDER_OFFICIAL_SERIES_PROFILES = _build_series_profiles(
    {
        "MELF-MFR0204": ("MELF金属膜电阻", "薄膜电阻", "MELF | 高精度"),
        "MFR": ("金属膜电阻", "薄膜电阻", "高精度"),
    }
)

NTE_OFFICIAL_SERIES_PROFILES = _build_series_profiles(
    {
        "SR1": ("厚膜贴片电阻", "厚膜电阻", "通用"),
        "MO": ("金属氧化膜插件电阻", "金属氧化膜电阻", "通用"),
        "NTE": ("通用插件电阻", "贴片电阻", "通用"),
    }
)

YAGEO_OFFICIAL_SERIES_PROFILES.update(
    _build_series_profiles(
        {
            "FMF": ("金属膜插件电阻", "薄膜电阻", "通用 | 高稳定"),
            "FCR": ("碳膜插件电阻", "碳膜电阻", "通用"),
            "CF": ("碳膜插件电阻", "碳膜电阻", "通用"),
            "FC": ("碳膜插件电阻", "碳膜电阻", "通用"),
            "FKN": ("保险丝型绕线电阻", "绕线电阻", "熔断 | 高功率"),
            "NKN": ("阻燃绕线电阻", "绕线电阻", "阻燃 | 高功率"),
        }
    )
)

YAGEO_OFFICIAL_SERIES_PROFILES.update(
    _build_series_profiles(
        {
            "RP": ("Yageo RP 高精密薄膜芯片电阻器", "薄膜电阻", "高精度 | 低TCR"),
        }
    )
)

YAGEO_OFFICIAL_SERIES_PROFILES.update(
    _build_series_profiles(
        {
            "KD07": ("YAGEO KD07 7mm 径向引线金属氧化物压敏电阻（MOV）", "引线型压敏电阻", "MOV | 浪涌抑制 | 径向引线 | 7mm"),
            "KD10": ("YAGEO KD10 10mm 径向引线金属氧化物压敏电阻（MOV）", "引线型压敏电阻", "MOV | 浪涌抑制 | 径向引线 | 10mm"),
            "KD20": ("YAGEO KD20 20mm 径向引线金属氧化物压敏电阻（MOV）", "引线型压敏电阻", "MOV | 浪涌抑制 | 径向引线 | 20mm"),
            "VRS0402SR": ("YAGEO VRS0402SR 多层贴片压敏电阻（ESD/浪涌保护）", "贴片压敏电阻", "多层 | 贴片 | ESD/浪涌保护 | 0402"),
        }
    )
)

BRIGHTKING_OFFICIAL_SERIES_PROFILES = _build_series_profiles(
    {
        "KD05": ("BrightKing KD05 5mm 径向引线金属氧化物压敏电阻（MOV）", "引线型压敏电阻", "MOV | 浪涌抑制 | 径向引线 | 5mm"),
        "KD07": ("BrightKing KD07 7mm 径向引线金属氧化物压敏电阻（MOV）", "引线型压敏电阻", "MOV | 浪涌抑制 | 径向引线 | 7mm"),
        "KD10": ("BrightKing KD10 10mm 径向引线金属氧化物压敏电阻（MOV）", "引线型压敏电阻", "MOV | 浪涌抑制 | 径向引线 | 10mm"),
        "KD14": ("BrightKing KD14 14mm 径向引线金属氧化物压敏电阻（MOV）", "引线型压敏电阻", "MOV | 浪涌抑制 | 径向引线 | 14mm"),
        "KD20": ("BrightKing KD20 20mm 径向引线金属氧化物压敏电阻（MOV）", "引线型压敏电阻", "MOV | 浪涌抑制 | 径向引线 | 20mm"),
        "KD25": ("BrightKing KD25 25mm 径向引线金属氧化物压敏电阻（MOV）", "引线型压敏电阻", "MOV | 浪涌抑制 | 径向引线 | 25mm"),
        "KD32": ("BrightKing KD32 32mm 径向引线金属氧化物压敏电阻（MOV）", "引线型压敏电阻", "MOV | 浪涌抑制 | 径向引线 | 32mm"),
        "KD53": ("BrightKing KD53 53mm 径向引线金属氧化物压敏电阻（MOV）", "引线型压敏电阻", "MOV | 浪涌抑制 | 径向引线 | 53mm"),
    }
)


def _resolve_brightking_series_code_from_model(compact: str) -> str:
    direct = _match_known_series_prefix(compact, BRIGHTKING_OFFICIAL_SERIES_PROFILES)
    if direct != "":
        return direct
    match = re.match(r"^(?:\d{3})?KD(?P<diameter>\d{2})(?:[A-Z0-9]|-|$)", compact)
    if match is None:
        return ""
    series_code = clean_text(f"KD{match.group('diameter')}")
    return series_code if series_code in BRIGHTKING_OFFICIAL_SERIES_PROFILES else ""


OFFICIAL_RESISTOR_BRAND_RULES.update(
    {
        "BRIGHTKING": {
            "brand_tokens": BRIGHTKING_BRAND_TOKENS,
            "profiles": BRIGHTKING_OFFICIAL_SERIES_PROFILES,
        }
    }
)
BRAND_MODEL_PREFIX_RESOLVERS["BRIGHTKING"] = _resolve_brightking_series_code_from_model
OFFICIAL_RESISTOR_SERIES_CODES.update(BRIGHTKING_OFFICIAL_SERIES_PROFILES.keys())

STE_OFFICIAL_VARISTOR_SERIES_PROFILES = _build_series_profiles(
    {
        "STE05D": ("STE STE05D 5D 标准径向引线金属氧化物压敏电阻（MOV）", "引线型压敏电阻", "MOV | 浪涌抑制 | 径向引线 | 5D"),
        "STE07D": ("STE STE07D 7D 标准径向引线金属氧化物压敏电阻（MOV）", "引线型压敏电阻", "MOV | 浪涌抑制 | 径向引线 | 7D"),
        "STE10D": ("STE STE10D 10D 标准径向引线金属氧化物压敏电阻（MOV）", "引线型压敏电阻", "MOV | 浪涌抑制 | 径向引线 | 10D"),
        "STE14D": ("STE STE14D 14D 标准径向引线金属氧化物压敏电阻（MOV）", "引线型压敏电阻", "MOV | 浪涌抑制 | 径向引线 | 14D"),
        "STE20D": ("STE STE20D 20D 标准径向引线金属氧化物压敏电阻（MOV）", "引线型压敏电阻", "MOV | 浪涌抑制 | 径向引线 | 20D"),
        "SMDMOV3225": ("STE SMDMOV3225 表面贴装金属氧化物压敏电阻", "贴片压敏电阻", "MOV | 表面贴装 | 浪涌抑制 | 3225"),
        "SMDMOV4032": ("STE SMDMOV4032 表面贴装金属氧化物压敏电阻", "贴片压敏电阻", "MOV | 表面贴装 | 浪涌抑制 | 4032"),
        "ST3225K": ("STE ST3225K 多层贴片压敏电阻", "贴片压敏电阻", "多层 | 贴片 | ESD/浪涌保护 | 3225"),
        "ST4032K": ("STE ST4032K 多层贴片压敏电阻", "贴片压敏电阻", "多层 | 贴片 | ESD/浪涌保护 | 4032"),
    }
)


def _resolve_ste_varistor_series_code_from_model(compact: str) -> str:
    direct = _match_known_series_prefix(compact, STE_OFFICIAL_VARISTOR_SERIES_PROFILES)
    if direct != "":
        return direct
    for pattern in (
        r"^(STE\d{2}D)",
        r"^(SMDMOV(?:3225|4032))",
        r"^(ST(?:3225|4032)K)",
    ):
        match = re.match(pattern, compact)
        if match is not None:
            series_code = clean_text(match.group(1))
            return series_code if series_code in STE_OFFICIAL_VARISTOR_SERIES_PROFILES else ""
    return ""


OFFICIAL_RESISTOR_BRAND_RULES.update(
    {
        "STE_VARISTOR": {
            "brand_tokens": STE_BRAND_TOKENS,
            "profiles": STE_OFFICIAL_VARISTOR_SERIES_PROFILES,
        }
    }
)
BRAND_MODEL_PREFIX_RESOLVERS["STE_VARISTOR"] = _resolve_ste_varistor_series_code_from_model
OFFICIAL_RESISTOR_SERIES_CODES.update(STE_OFFICIAL_VARISTOR_SERIES_PROFILES.keys())

VISHAY_OFFICIAL_SERIES_PROFILES.update(
    _build_series_profiles(
        {
            "MCU": ("专业薄膜片式电阻器", "薄膜电阻", "高精度"),
            "MCS": ("专业薄膜片式电阻器", "薄膜电阻", "高精度"),
            "MMU": ("薄膜MELF电阻器", "薄膜电阻", "MELF"),
            "TNPU": ("超高精密薄膜片式电阻器", "薄膜电阻", "高精度 | 低TCR"),
            "CP": ("商业级轴向绕线功率电阻", "绕线电阻", "高功率"),
            "CA": ("商业级轴向绕线功率电阻", "绕线电阻", "高功率"),
            "MRS": ("专业金属膜插件电阻", "薄膜电阻", "高稳定"),
            "HVR": ("高压金属玻璃釉膜电阻", "薄膜电阻", "高压"),
            "RCC": ("厚膜贴片电阻", "厚膜电阻", "通用"),
            "NTCLE": ("NTC热敏电阻器", "热敏电阻", "NTC"),
            "CW": ("轴向绕线功率电阻", "绕线电阻", "高功率"),
            "CH": ("精密薄膜贴片电阻", "薄膜电阻", "高精度"),
            "NFR": ("金属膜插件电阻", "薄膜电阻", "通用"),
            "PTF": ("精密金属膜插件电阻", "薄膜电阻", "高精度 | 低TCR"),
            "RS": ("绕线功率电阻", "绕线电阻", "高功率"),
            "LTO": ("TO封装厚膜功率电阻", "厚膜电阻", "高功率 | TO封装"),
            "D2TO": ("TO封装厚膜功率电阻", "厚膜电阻", "高功率 | TO封装"),
            "AC": ("水泥绕线功率电阻", "绕线电阻", "高功率"),
            "ERL": ("精密金属膜电阻", "薄膜电阻", "高精度"),
            "Y1487": ("Bulk Metal Foil 超精密电阻", "薄膜电阻", "超高精度 | 低TCR"),
            "RCG": ("通用厚膜贴片电阻", "厚膜电阻", "通用"),
        }
    )
)

VISHAY_OFFICIAL_SERIES_PROFILES.update(
    _build_series_profiles(
        {
            "C4A": ("Vishay Micro-Measurements C4A Advanced Sensors 箔式电阻应变片", "电阻应变片", "应变测量 | 箔式 | Advanced Sensors"),
            "C5K": ("Vishay Micro-Measurements C5K 高疲劳寿命箔式电阻应变片", "电阻应变片", "应变测量 | 箔式 | 高疲劳寿命"),
            "CEA": ("Vishay Micro-Measurements CEA 通用箔式电阻应变片", "电阻应变片", "应变测量 | 箔式 | 通用"),
            "J5K": ("Vishay Micro-Measurements J5K 高性能箔式电阻应变片", "电阻应变片", "应变测量 | 箔式 | 高性能"),
            "W2A": ("Vishay Micro-Measurements W2A 桥式/剪切型箔式电阻应变片", "电阻应变片", "应变测量 | 箔式 | 桥式"),
            "MQ": ("Vishay/VPG Powertron MQ 高精密表面贴装箔电阻", "薄膜电阻", "高精密 | 低TCR | Foil | 贴片"),
            "PTS": ("Vishay PTS 铂薄膜 SMD RTD 温度传感器", "RTD温度传感器", "Pt100 | 铂薄膜 | 温度检测 | 贴片"),
            "TFPT": ("Vishay TFPT 镍薄膜线性 PTC 热敏电阻", "热敏电阻", "PTC | 温度检测 | 镍薄膜 | 贴片"),
            "Y1624": ("Vishay Foil 高精密 Bulk Metal Foil 电阻", "薄膜电阻", "高精度 | 低TCR | Foil"),
            "Y1628": ("Vishay Foil VSMP/Y1628 Bulk Metal Foil 高精密贴片电阻", "薄膜电阻", "高精密 | Bulk Metal Foil | 低TCR | 贴片"),
            "Y1629": ("Vishay Foil 高精密 Bulk Metal Foil 电阻", "薄膜电阻", "高精度 | 低TCR | Foil"),
            "Y4073": ("Vishay Foil FRFC1206/Y4073 Z-Foil 高精密贴片电阻", "薄膜电阻", "超高精密 | Z-Foil | 低TCR | 贴片"),
            "Y4076": ("Vishay Foil FRFC2512/Y4076 Z-Foil 高精密贴片电阻", "薄膜电阻", "超高精密 | Z-Foil | 低TCR | 贴片"),
            "PCAN": ("Sfernice PCAN 车规精密薄膜片式电阻器", "薄膜电阻", "车规 | 高精度 | 薄膜"),
            "UMB/UMA": ("Beyschlag UMB/UMA 高精密薄膜MELF电阻器", "薄膜电阻", "高精度 | MELF | 低TCR"),
            "SM": ("Vishay Dale SM 表面贴装绕线功率电阻", "绕线电阻", "高功率 | 贴片"),
            "MSP": ("Vishay Dale MSP 模压封装功率电阻", "绕线电阻", "高功率 | 模压封装"),
        }
    )
)

KOA_OFFICIAL_SERIES_PROFILES.update(
    _build_series_profiles(
        {
            "WK73S": ("宽端子低阻电流检测贴片电阻", "厚膜电阻", "宽端子 | 低阻 | 电流检测 | AEC-Q200"),
            "WK73R": ("宽端子高功率贴片电阻", "厚膜电阻", "宽端子 | 高功率"),
            "SR73": ("低阻厚膜电流检测贴片电阻", "厚膜电阻", "低阻 | 电流检测"),
            "SR73W": ("低阻厚膜电流检测贴片电阻", "厚膜电阻", "低阻 | 电流检测"),
            "SLR": ("表面贴装模压电流检测电阻", "厚膜电阻", "电流检测"),
            "CF": ("碳膜插件电阻", "碳膜电阻", "通用"),
            "MOS": ("金属氧化膜插件电阻", "金属氧化膜电阻", "通用"),
        }
    )
)

STACKPOLE_OFFICIAL_SERIES_PROFILES.update(
    _build_series_profiles(
        {
            "SM": ("表面贴装绕线电阻", "绕线电阻", "高功率"),
            "WW": ("绕线插件电阻", "绕线电阻", "高功率"),
            "CF": ("碳膜插件电阻", "碳膜电阻", "通用"),
            "PCF": ("脉冲耐受碳膜插件电阻", "碳膜电阻", "抗脉冲"),
            "HDM": ("高稳定碳膜插件电阻", "碳膜电阻", "高稳定"),
            "PRNF": ("阻燃金属膜插件电阻", "薄膜电阻", "阻燃"),
            "RNS": ("金属膜插件电阻", "薄膜电阻", "通用"),
            "RSF": ("金属氧化膜插件电阻", "金属氧化膜电阻", "通用"),
            "RSMF": ("金属氧化膜插件电阻", "金属氧化膜电阻", "通用"),
            "FRN": ("阻燃金属膜插件电阻", "薄膜电阻", "阻燃"),
            "FRC": ("通用厚膜贴片电阻", "厚膜电阻", "通用"),
            "RVC": ("高压厚膜贴片电阻", "厚膜电阻", "高压"),
            "CSR": ("低阻电流检测贴片电阻", "合金电阻", "低阻 | 电流检测"),
            "CSRT": ("低阻电流检测贴片电阻", "合金电阻", "低阻 | 电流检测"),
            "CB": ("涂覆绕线功率电阻", "绕线电阻", "高功率"),
        }
    )
)

PANASONIC_OFFICIAL_SERIES_PROFILES.update(
    _build_series_profiles(
        {
            "ERA-3K": ("高可靠薄膜芯片电阻器", "薄膜电阻", "高可靠"),
            "ERA-6K": ("高可靠薄膜芯片电阻器", "薄膜电阻", "高可靠"),
            "ERA-8K": ("高可靠薄膜芯片电阻器", "薄膜电阻", "高可靠"),
            "ERA-8P": ("高压薄膜芯片电阻器", "薄膜电阻", "高压 | 高可靠"),
            "ERA-14EB": ("金属膜矩形片式电阻器", "薄膜电阻", "高精度"),
            "ERA-14HD": ("金属膜矩形片式电阻器", "薄膜电阻", "高精度"),
            "ERO-S2PH": ("金属膜插件电阻器", "薄膜电阻", "通用"),
            "ERD-S1": ("碳膜插件电阻器", "碳膜电阻", "通用"),
            "ERD-S2": ("碳膜插件电阻器", "碳膜电阻", "通用"),
            "ERG-1SJ": ("金属氧化膜插件电阻器", "金属氧化膜电阻", "阻燃"),
            "ERG-2SJ": ("金属氧化膜插件电阻器", "金属氧化膜电阻", "阻燃"),
            "ERG-3SJ": ("金属氧化膜插件电阻器", "金属氧化膜电阻", "阻燃"),
            "ERG-1FJ": ("金属氧化膜插件电阻器", "金属氧化膜电阻", "阻燃"),
            "ERG-2FJ": ("金属氧化膜插件电阻器", "金属氧化膜电阻", "阻燃"),
            "ERG-3FJ": ("金属氧化膜插件电阻器", "金属氧化膜电阻", "阻燃"),
            "ERZ-E": ("ZNR氧化锌压敏电阻", "贴片压敏电阻", "压敏 | 浪涌吸收"),
            "ERZ-V": ("ZNR氧化锌压敏电阻", "贴片压敏电阻", "压敏 | 浪涌吸收"),
            "ERT-J0ER": ("Panasonic ERT-J0ER 0402 片式 NTC 热敏电阻", "热敏电阻", "测温 | 温度补偿 | 贴片 | NTC | 0402"),
        }
    )
)

ROHM_OFFICIAL_SERIES_PROFILES.update(
    _build_series_profiles(
        {
            "TRR": ("通用厚膜贴片电阻器", "厚膜电阻", "通用"),
        }
    )
)

TE_OFFICIAL_SERIES_PROFILES.update(
    _build_series_profiles(
        {
            "3503/3504": ("氮化铝薄膜功率电阻", "薄膜电阻", "高功率 | 高精度"),
            "3400": ("厚膜片式功率电阻", "厚膜电阻", "高功率"),
            "3500": ("厚膜片式功率电阻", "厚膜电阻", "高功率"),
            "CRG": ("通用厚膜片式电阻", "厚膜电阻", "通用"),
            "CRGV": ("高压厚膜片式电阻", "厚膜电阻", "高压"),
            "RL73": ("低阻电流检测厚膜贴片电阻", "厚膜电阻", "低阻 | 电流检测"),
            "RR": ("金属膜插件电阻", "薄膜电阻", "通用"),
            "ROX": ("金属氧化膜插件电阻", "金属氧化膜电阻", "阻燃"),
            "RLP73": ("低阻电流检测厚膜贴片电阻", "厚膜电阻", "低阻 | 电流检测"),
            "RLW73": ("宽端子低阻电流检测厚膜贴片电阻", "厚膜电阻", "宽端子 | 低阻 | 电流检测"),
            "CFR": ("碳膜插件电阻", "碳膜电阻", "通用"),
            "MPT": ("TO封装厚膜功率电阻", "厚膜电阻", "高功率 | TO封装"),
            "SMA": ("精密薄膜电阻网络/阵列", "薄膜电阻", "高精度"),
        }
    )
)

TE_OFFICIAL_SERIES_PROFILES.update(
    _build_series_profiles(
        {
            "RP73F": ("TE RP73F 高精密薄膜芯片电阻器", "薄膜电阻", "高精度 | 低TCR"),
            "SMF": ("TE SMF 金属膜功率电阻", "薄膜电阻", "高功率 | 金属膜"),
            "SMW": ("TE SMW 表面贴装绕线功率电阻", "绕线电阻", "高功率 | 贴片"),
        }
    )
)

FENGHUA_OFFICIAL_SERIES_PROFILES.update(
    {
        "TD": {"系列说明": "精密薄膜贴片电阻", "器件类型": "薄膜电阻", "特殊用途": "高精度"},
        "TE": {"系列说明": "精密薄膜贴片电阻", "器件类型": "薄膜电阻", "特殊用途": "高精度"},
        "TF": {"系列说明": "精密薄膜贴片电阻", "器件类型": "薄膜电阻", "特殊用途": "高精度"},
        "AB": {"系列说明": "车规厚膜贴片电阻", "器件类型": "厚膜电阻", "特殊用途": "车规"},
        "AC": {"系列说明": "车规抗硫厚膜贴片电阻", "器件类型": "厚膜电阻", "特殊用途": "车规 | 抗硫"},
        "RHC/RHS": {"系列说明": "高功率厚膜贴片电阻", "器件类型": "厚膜电阻", "特殊用途": "高功率"},
        "FNR": {"系列说明": "氧化锌压敏电阻", "器件类型": "贴片压敏电阻", "特殊用途": "压敏"},
    }
)

OFFICIAL_RESISTOR_BRAND_RULES.update(
    {
        "VISHAY": {
            "brand_tokens": ("VISHAY", "VISHAY DALE", "VISHAY BEYSCHLAG", "DALE", "HOLSWORTHY", "VITROHM", "DRALORIC", "SFERNICE"),
            "profiles": VISHAY_OFFICIAL_SERIES_PROFILES,
        },
        "KOA": {
            "brand_tokens": ("KOA",),
            "profiles": KOA_OFFICIAL_SERIES_PROFILES,
        },
        "STACKPOLE": {
            "brand_tokens": ("STACKPOLE", "SEI"),
            "profiles": STACKPOLE_OFFICIAL_SERIES_PROFILES,
        },
        "PANASONIC": {
            "brand_tokens": ("PANASONIC", "松下"),
            "profiles": PANASONIC_OFFICIAL_SERIES_PROFILES,
        },
        "ROHM": {
            "brand_tokens": ("ROHM", "罗姆"),
            "profiles": ROHM_OFFICIAL_SERIES_PROFILES,
        },
        "SUSUMU": {
            "brand_tokens": ("SUSUMU", "进工业", "進工業"),
            "profiles": SUSUMU_OFFICIAL_SERIES_PROFILES,
        },
        "TE": {
            "brand_tokens": ("TE CONNECTIVITY", "泰科", "HOLSWORTHY", "NEOHM"),
            "profiles": TE_OFFICIAL_SERIES_PROFILES,
        },
        "KAMAYA": {
            "brand_tokens": ("KAMAYA", "釜屋電機", "釜屋电机"),
            "profiles": KAMAYA_OFFICIAL_SERIES_PROFILES,
        },
        "MERITEK": {
            "brand_tokens": ("MERITEK",),
            "profiles": MERITEK_OFFICIAL_SERIES_PROFILES,
        },
        "EVER_OHMS": {
            "brand_tokens": ("EVER OHMS", "EVEROHMS", "天二", "澶╀簩"),
            "profiles": EVER_OHMS_OFFICIAL_SERIES_PROFILES,
        },
        "CAL_CHIP": {
            "brand_tokens": ("CAL-CHIP", "CAL CHIP"),
            "profiles": CAL_CHIP_OFFICIAL_SERIES_PROFILES,
        },
        "OHMITE": {
            "brand_tokens": ("OHMITE",),
            "profiles": OHMITE_OFFICIAL_SERIES_PROFILES,
        },
        "BOURNS": {
            "brand_tokens": ("BOURNS",),
            "profiles": BOURNS_OFFICIAL_SERIES_PROFILES,
        },
        "SUNWAY": {
            "brand_tokens": ("SUNWAY", "信维", "信维通信"),
            "profiles": SUNWAY_OFFICIAL_SERIES_PROFILES,
        },
        "LIZ": {
            "brand_tokens": LIZ_BRAND_TOKENS,
            "profiles": LIZ_OFFICIAL_SERIES_PROFILES,
        },
        "RESI": {
            "brand_tokens": RESI_BRAND_TOKENS,
            "profiles": RESI_OFFICIAL_SERIES_PROFILES,
        },
        "TYOHM": {
            "brand_tokens": TYOHM_BRAND_TOKENS,
            "profiles": TYOHM_OFFICIAL_SERIES_PROFILES,
        },
        "VO": {
            "brand_tokens": VO_BRAND_TOKENS,
            "profiles": VO_OFFICIAL_SERIES_PROFILES,
        },
        "VENKEL": {
            "brand_tokens": VENKEL_BRAND_TOKENS,
            "profiles": VENKEL_OFFICIAL_SERIES_PROFILES,
        },
        "RCD": {
            "brand_tokens": RCD_BRAND_TOKENS,
            "profiles": RCD_OFFICIAL_SERIES_PROFILES,
        },
        "RIEDON": {
            "brand_tokens": RIEDON_BRAND_TOKENS,
            "profiles": RIEDON_OFFICIAL_SERIES_PROFILES,
        },
        "THUNDER": {
            "brand_tokens": THUNDER_BRAND_TOKENS,
            "profiles": THUNDER_OFFICIAL_SERIES_PROFILES,
        },
        "NTE": {
            "brand_tokens": NTE_BRAND_TOKENS,
            "profiles": NTE_OFFICIAL_SERIES_PROFILES,
        },
    }
)

OFFICIAL_RESISTOR_SERIES_CODES.update(
    code
    for rule in OFFICIAL_RESISTOR_BRAND_RULES.values()
    for code in rule.get("profiles", {}).keys()
)


PDC_BRAND_TOKENS = ("PDC", "PSA", "信昌", "信昌电陶", "PROSPERITY DIELECTRICS")
PDC_OFFICIAL_SERIES_PROFILES = _build_series_profiles(
    {
        "FMF": ("金属条电流检测电阻（AEC-Q200）", "合金电阻", "电流检测 | 金属条 | 低阻 | AEC-Q200"),
        "FCF": ("通用厚膜贴片电阻/低阻电流检测贴片电阻", "厚膜电阻", "通用厚膜 | 电流检测 | 低阻"),
        "WCF": ("宽端子高功率厚膜贴片电阻（AEC-Q200）", "厚膜电阻", "宽端子 | 高功率 | AEC-Q200"),
        "AVF": ("高压抗硫化厚膜贴片电阻（AEC-Q200）", "厚膜电阻", "高压 | 抗硫化 | AEC-Q200"),
        "AVS": ("高压安规抗硫化厚膜贴片电阻（AEC-Q200）", "厚膜电阻", "高压 | 安规 | 抗硫化 | AEC-Q200"),
        "FAF": ("高精密薄膜贴片电阻", "薄膜电阻", "高精密 | 薄膜"),
        "FBF": ("低阻厚膜电流检测贴片电阻", "厚膜电阻", "电流检测 | 低阻 | 厚膜"),
        "FNF": ("抗浪涌厚膜贴片电阻（AEC-Q200）", "厚膜电阻", "抗浪涌 | AEC-Q200"),
        "FOF": ("金属箔高功率抗硫化电流检测电阻", "合金电阻", "电流检测 | 金属箔 | 抗硫化"),
        "FPF": ("高功率厚膜贴片电阻", "厚膜电阻", "高功率 | 厚膜"),
        "FPS": ("抗浪涌高功率厚膜贴片电阻", "厚膜电阻", "高功率 | 抗浪涌 | 厚膜"),
        "FVF": ("高压厚膜贴片电阻", "厚膜电阻", "高压 | 厚膜"),
        "FVS": ("高压安规厚膜贴片电阻", "厚膜电阻", "高压 | 安规 | 厚膜"),
        "FWF": ("车规厚膜贴片电阻/抗硫化车规厚膜贴片电阻", "厚膜电阻", "车规 | 厚膜 | 抗硫化"),
        "FHF": ("高阻值厚膜贴片电阻", "厚膜电阻", "高阻值 | 厚膜"),
    }
)


def _resolve_pdc_series_code_from_model(compact: str) -> str:
    direct = _match_known_series_prefix(compact, PDC_OFFICIAL_SERIES_PROFILES)
    if direct != "":
        return direct
    match = re.match(r"^(WCF|AVF|AVS|FAF|FBF|FCF|FHF|FMF|FNF|FOF|FPF|FPS|FVF|FVS|FWF)", compact)
    return clean_text(match.group(1)) if match is not None else ""


OFFICIAL_RESISTOR_BRAND_RULES.update(
    {
        "PDC": {
            "brand_tokens": PDC_BRAND_TOKENS,
            "profiles": PDC_OFFICIAL_SERIES_PROFILES,
        }
    }
)
BRAND_MODEL_PREFIX_RESOLVERS["PDC"] = _resolve_pdc_series_code_from_model
OFFICIAL_RESISTOR_SERIES_CODES.update(PDC_OFFICIAL_SERIES_PROFILES.keys())


SUNLORD_BRAND_TOKENS = ("SUNLORD", "顺络")
SUNLORD_OFFICIAL_SERIES_PROFILES = _build_series_profiles(
    {
        "SDNT0402C": ("Sunlord SDNT0402C 片式温度传感 NTC 热敏电阻", "热敏电阻", "测温 | 贴片 | NTC"),
        "SDNT0603C": ("Sunlord SDNT0603C 片式温度传感 NTC 热敏电阻", "热敏电阻", "测温 | 贴片 | NTC"),
        "SDNT0603X": ("Sunlord SDNT0603X 片式温度传感 NTC 热敏电阻", "热敏电阻", "测温 | 贴片 | NTC"),
        "SDNT1005X": ("Sunlord SDNT1005X 片式温度传感 NTC 热敏电阻", "热敏电阻", "测温 | 贴片 | NTC"),
        "SDNT1608X": ("Sunlord SDNT1608X 片式温度传感 NTC 热敏电阻", "热敏电阻", "测温 | 贴片 | NTC"),
        "SDNT2012X": ("Sunlord SDNT2012X 片式温度传感 NTC 热敏电阻", "热敏电阻", "测温 | 贴片 | NTC"),
        "SDV0603E": ("Sunlord SDV0603E 多层贴片压敏电阻（ESD/浪涌抑制）", "贴片压敏电阻", "多层 | 贴片 | ESD/浪涌保护"),
        "SDV0603S": ("Sunlord SDV0603S 多层贴片压敏电阻（ESD/浪涌抑制）", "贴片压敏电阻", "多层 | 贴片 | ESD/浪涌保护"),
        "SDV1005A": ("Sunlord SDV1005A 多层贴片压敏电阻（ESD/浪涌抑制）", "贴片压敏电阻", "多层 | 贴片 | ESD/浪涌保护"),
        "SDV1005E": ("Sunlord SDV1005E 多层贴片压敏电阻（ESD/浪涌抑制）", "贴片压敏电阻", "多层 | 贴片 | ESD/浪涌保护"),
        "SDV1005H": ("Sunlord SDV1005H 多层贴片压敏电阻（ESD/浪涌抑制）", "贴片压敏电阻", "多层 | 贴片 | ESD/浪涌保护"),
        "SDV1005S": ("Sunlord SDV1005S 多层贴片压敏电阻（ESD/浪涌抑制）", "贴片压敏电阻", "多层 | 贴片 | ESD/浪涌保护"),
        "SDV1608A": ("Sunlord SDV1608A 多层贴片压敏电阻（ESD/浪涌抑制）", "贴片压敏电阻", "多层 | 贴片 | ESD/浪涌保护"),
        "SDV1608E": ("Sunlord SDV1608E 多层贴片压敏电阻（ESD/浪涌抑制）", "贴片压敏电阻", "多层 | 贴片 | ESD/浪涌保护"),
        "SDV1608H": ("Sunlord SDV1608H 多层贴片压敏电阻（ESD/浪涌抑制）", "贴片压敏电阻", "多层 | 贴片 | ESD/浪涌保护"),
        "SDV1608S": ("Sunlord SDV1608S 多层贴片压敏电阻（ESD/浪涌抑制）", "贴片压敏电阻", "多层 | 贴片 | ESD/浪涌保护"),
        "SDV2012A": ("Sunlord SDV2012A 多层贴片压敏电阻（ESD/浪涌抑制）", "贴片压敏电阻", "多层 | 贴片 | ESD/浪涌保护"),
        "SDV2012E": ("Sunlord SDV2012E 多层贴片压敏电阻（ESD/浪涌抑制）", "贴片压敏电阻", "多层 | 贴片 | ESD/浪涌保护"),
        "SDVL4532SD": ("Sunlord SDVL4532SD 大尺寸贴片压敏电阻（浪涌抑制）", "贴片压敏电阻", "贴片 | 浪涌抑制"),
        "SDVL5650SD": ("Sunlord SDVL5650SD 大尺寸贴片压敏电阻（浪涌抑制）", "贴片压敏电阻", "贴片 | 浪涌抑制"),
        "SVMH2016": ("Sunlord SVMH2016 高电压多层贴片压敏电阻（浪涌抑制）", "贴片压敏电阻", "高电压 | 多层 | 贴片 | 浪涌抑制 | AC电路"),
        "SVMH3216": ("Sunlord SVMH3216 高电压多层贴片压敏电阻（浪涌抑制）", "贴片压敏电阻", "高电压 | 多层 | 贴片 | 浪涌抑制 | AC电路"),
        "SVMH3225": ("Sunlord SVMH3225 高电压多层贴片压敏电阻（浪涌抑制）", "贴片压敏电阻", "高电压 | 多层 | 贴片 | 浪涌抑制 | AC电路"),
        "SVMH4532": ("Sunlord SVMH4532 高电压多层贴片压敏电阻（浪涌抑制）", "贴片压敏电阻", "高电压 | 多层 | 贴片 | 浪涌抑制 | AC电路"),
        "SVMH5650": ("Sunlord SVMH5650 高电压多层贴片压敏电阻（浪涌抑制）", "贴片压敏电阻", "高电压 | 多层 | 贴片 | 浪涌抑制 | AC电路"),
    }
)


def _resolve_sunlord_series_code_from_model(compact: str) -> str:
    direct = _match_known_series_prefix(compact, SUNLORD_OFFICIAL_SERIES_PROFILES)
    if direct != "":
        return direct
    for pattern in (
        r"^(SDNT\d{4}[A-Z])",
        r"^(SVMH\d{4})",
        r"^(SDVL\d{4}[A-Z]{2})",
        r"^(SDV\d{4}[A-Z])",
    ):
        match = re.match(pattern, compact)
        if match is not None:
            return clean_text(match.group(1))
    return ""


OFFICIAL_RESISTOR_BRAND_RULES.update(
    {
        "SUNLORD": {
            "brand_tokens": SUNLORD_BRAND_TOKENS,
            "profiles": SUNLORD_OFFICIAL_SERIES_PROFILES,
        }
    }
)
BRAND_MODEL_PREFIX_RESOLVERS["SUNLORD"] = _resolve_sunlord_series_code_from_model
OFFICIAL_RESISTOR_SERIES_CODES.update(SUNLORD_OFFICIAL_SERIES_PROFILES.keys())


TDK_THERMISTOR_BRAND_TOKENS = ("TDK", "东电化", "EPCOS")
TDK_THERMISTOR_OFFICIAL_SERIES_PROFILES = _build_series_profiles(
    {
        "NTCG": ("TDK NTCG 片式 NTC 热敏电阻（温度检测/补偿）", "热敏电阻", "测温 | 贴片 | NTC"),
        "NTCF": ("TDK NTCF 薄膜型片式 NTC 热敏电阻（温度检测/补偿）", "热敏电阻", "测温 | 贴片 | NTC"),
        "NTCDA": ("TDK NTCDA 连接器/线束用 NTC 温度传感热敏电阻", "热敏电阻", "测温 | 传感器 | NTC"),
        "NTCDP": ("TDK NTCDP 连接器/线束用 NTC 温度传感热敏电阻", "热敏电阻", "测温 | 传感器 | NTC"),
        "NTCDS": ("TDK NTCDS 连接器/线束用 NTC 温度传感热敏电阻", "热敏电阻", "测温 | 传感器 | NTC"),
        "NTCDZ": ("TDK NTCDZ 连接器/线束用 NTC 温度传感热敏电阻", "热敏电阻", "测温 | 传感器 | NTC"),
        "NTCRP": ("TDK NTCRP 连接器/线束用 NTC 温度传感热敏电阻", "热敏电阻", "测温 | 传感器 | NTC"),
        "NTCSP": ("TDK NTCSP 车规高温片式 NTC 热敏电阻", "热敏电阻", "车规 | 高温 | 贴片 | NTC"),
        "B57164": ("TDK/EPCOS B57164 引线型 NTC 温度测量热敏电阻", "热敏电阻", "测温 | 引线型 | NTC"),
        "B57236": ("TDK/EPCOS B57236 S236 NTC 浪涌电流限制热敏电阻", "热敏电阻", "浪涌电流限制 | NTC | 引线型"),
        "B57237": ("TDK/EPCOS B57237 S237 NTC 浪涌电流限制热敏电阻", "热敏电阻", "浪涌电流限制 | NTC | 引线型"),
        "B57330": ("TDK/EPCOS B57330 片式 NTC 温度测量热敏电阻", "热敏电阻", "测温 | 贴片 | NTC"),
        "B57331": ("TDK/EPCOS B57331 片式 NTC 温度测量热敏电阻", "热敏电阻", "测温 | 贴片 | NTC"),
        "B57421": ("TDK/EPCOS B57421 片式 NTC 温度测量热敏电阻", "热敏电阻", "测温 | 贴片 | NTC"),
        "B57442": ("TDK/EPCOS B57442 车规片式 NTC 温度测量热敏电阻", "热敏电阻", "车规 | 测温 | 贴片 | NTC"),
        "B57621": ("TDK/EPCOS B57621 片式 NTC 温度测量热敏电阻", "热敏电阻", "测温 | 贴片 | NTC"),
        "B57861": ("TDK/EPCOS B57861 引线型 NTC 温度测量热敏电阻", "热敏电阻", "测温 | 引线型 | NTC"),
        "B57891": ("TDK/EPCOS B57891 引线型 NTC 温度测量热敏电阻", "热敏电阻", "测温 | 引线型 | NTC"),
        "B59052": ("TDK/EPCOS B59052 PTC 限温传感热敏电阻", "热敏电阻", "限温传感 | PTC"),
        "B59100": ("TDK/EPCOS B59100 PTC 马达保护/限温传感热敏电阻", "热敏电阻", "马达保护 | 限温传感 | PTC"),
        "B59115": ("TDK/EPCOS B59115 贴片 PTC 过流保护热敏电阻", "热敏电阻", "过流保护 | 贴片 | PTC"),
        "B59421": ("TDK/EPCOS B59421 贴片 PTC 限温传感热敏电阻", "热敏电阻", "限温传感 | 贴片 | PTC"),
        "B59451": ("TDK/EPCOS B59451 PTC 过流保护热敏电阻", "热敏电阻", "过流保护 | PTC"),
        "B59641": ("TDK/EPCOS B59641 贴片 PTC 限温传感热敏电阻", "热敏电阻", "限温传感 | 贴片 | PTC"),
        "B59721": ("TDK/EPCOS B59721 贴片 PTC 限温传感热敏电阻", "热敏电阻", "限温传感 | 贴片 | PTC"),
        "B59754": ("TDK/EPCOS B59754 PTC 过流保护热敏电阻", "热敏电阻", "过流保护 | PTC"),
        "B59807": ("TDK/EPCOS B59807 贴片 PTC 过流保护热敏电阻", "热敏电阻", "过流保护 | 贴片 | PTC"),
        "B59840": ("TDK/EPCOS B59840 PTC 过流保护热敏电阻", "热敏电阻", "过流保护 | PTC"),
        "B59850": ("TDK/EPCOS B59850 PTC 过流保护热敏电阻", "热敏电阻", "过流保护 | PTC"),
        "B59860": ("TDK/EPCOS B59860 PTC 过流保护热敏电阻", "热敏电阻", "过流保护 | PTC"),
        "B59875": ("TDK/EPCOS B59875 PTC 过流保护热敏电阻", "热敏电阻", "过流保护 | PTC"),
        "B59890": ("TDK/EPCOS B59890 PTC 过流保护热敏电阻", "热敏电阻", "过流保护 | PTC"),
        "B59955": ("TDK/EPCOS B59955 PTC 过流保护热敏电阻", "热敏电阻", "过流保护 | PTC"),
        "B59995": ("TDK/EPCOS B59995 PTC 过流保护热敏电阻", "热敏电阻", "过流保护 | PTC"),
    }
)


def _resolve_tdk_thermistor_series_code_from_model(compact: str) -> str:
    direct = _match_known_series_prefix(compact, TDK_THERMISTOR_OFFICIAL_SERIES_PROFILES)
    if direct != "":
        return direct
    for pattern in (
        r"^(NTCSP)",
        r"^(NTC(?:DA|DP|DS|DZ|RP|F|G))",
        r"^(B57(?:164|236|237|330|331|421|442|621|861|891))",
        r"^(B59(?:052|100|115|421|451|641|721|754|807|840|850|860|875|890|955|995))",
    ):
        match = re.match(pattern, compact)
        if match is not None:
            return clean_text(match.group(1))
    return ""


OFFICIAL_RESISTOR_BRAND_RULES.update(
    {
        "TDK_THERMISTOR": {
            "brand_tokens": TDK_THERMISTOR_BRAND_TOKENS,
            "profiles": TDK_THERMISTOR_OFFICIAL_SERIES_PROFILES,
        }
    }
)
BRAND_MODEL_PREFIX_RESOLVERS["TDK_THERMISTOR"] = _resolve_tdk_thermistor_series_code_from_model
OFFICIAL_RESISTOR_SERIES_CODES.update(TDK_THERMISTOR_OFFICIAL_SERIES_PROFILES.keys())


MITSUBISHI_THERMISTOR_BRAND_TOKENS = ("MITSUBISHI", "三菱")
MITSUBISHI_THERMISTOR_OFFICIAL_SERIES_PROFILES = _build_series_profiles(
    {
        "TH11": ("Mitsubishi Materials TH11 片式 NTC 热敏电阻", "热敏电阻", "测温 | 贴片 | NTC | 高精度"),
    }
)


def _resolve_mitsubishi_thermistor_series_code_from_model(compact: str) -> str:
    if compact.startswith("TH11"):
        return "TH11"
    return ""


OFFICIAL_RESISTOR_BRAND_RULES.update(
    {
        "MITSUBISHI_THERMISTOR": {
            "brand_tokens": MITSUBISHI_THERMISTOR_BRAND_TOKENS,
            "profiles": MITSUBISHI_THERMISTOR_OFFICIAL_SERIES_PROFILES,
        }
    }
)
BRAND_MODEL_PREFIX_RESOLVERS["MITSUBISHI_THERMISTOR"] = _resolve_mitsubishi_thermistor_series_code_from_model
OFFICIAL_RESISTOR_SERIES_CODES.update(MITSUBISHI_THERMISTOR_OFFICIAL_SERIES_PROFILES.keys())
