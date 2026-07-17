from __future__ import annotations

import argparse
import html
import os
import re
import sys
import tempfile
from datetime import datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

import pandas as pd
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

import component_matcher as cm
from incremental_semiconductor_cache_update import (
    refresh_search_sidecar_rows,
    replace_prepared_cache_rows,
)


ROOT = Path(__file__).resolve().parent
CRYSTAL_DIR = next((path for path in ROOT.glob("Crystal*") if path.is_dir()), None)
DEFAULT_OUTPUT = (
    CRYSTAL_DIR / "Epson官方产品编号.csv"
    if CRYSTAL_DIR is not None
    else ROOT / "Epson官方产品编号.csv"
)
MULTIBRAND_TIMING_SOURCE = (
    CRYSTAL_DIR / "多品牌官方晶振资料.csv"
    if CRYSTAL_DIR is not None
    else None
)

BRAND = "爱普生Epson"
JSON_BASE_URL = "https://download.epsondevice.com/td/ps/"
PDF_BASE_URL = "https://download.epsondevice.com/td/pdf/"
PRODUCT_BASE_URL = "https://www.epsondevice.com/crystal/en/products/"
MIN_EXPECTED_ROWS = 5_000

SOURCE_SPECS = {
    "xtal_32khz.json": {
        "component_type": "晶振",
        "category": "32.768kHz石英晶体单元",
        "frequency_unit": "kHz",
        "frequency_multiplier": "1",
        "pdf_dir": "td_xtal_32khz",
    },
    "xtal_mhz.json": {
        "component_type": "晶振",
        "category": "MHz石英晶体单元",
        "frequency_unit": "MHz",
        "frequency_multiplier": "1",
        "pdf_dir": "td_xtal_mhz",
    },
    "spxo_32k_cmos.json": {
        "component_type": "振荡器",
        "category": "32.768kHz SPXO",
        "frequency_unit": "kHz",
        "frequency_multiplier": "1000",
        "pdf_dir": "app",
        "series_pdf": True,
    },
    "spxo_mhz_cmos.json": {
        "component_type": "振荡器",
        "category": "CMOS SPXO",
        "frequency_unit": "MHz",
        "frequency_multiplier": "1",
        "pdf_dir": "td_spxo_spso_mhz",
    },
    "spxo_prog.json": {
        "component_type": "振荡器",
        "category": "可编程SPXO",
        "frequency_unit": "MHz",
        "frequency_multiplier": "1",
        "pdf_dir": "td_spxo_spso_mhz",
        "special": "可编程",
    },
    "spxo_lvds.json": {
        "component_type": "振荡器",
        "category": "LVDS SPXO",
        "frequency_unit": "MHz",
        "frequency_multiplier": "1",
        "pdf_dir": "td_spxo_spso_mhz",
    },
    "spxo_lvpecl.json": {
        "component_type": "振荡器",
        "category": "LV-PECL SPXO",
        "frequency_unit": "MHz",
        "frequency_multiplier": "1",
        "pdf_dir": "td_spxo_spso_mhz",
    },
    "spxo_spso_hcsl.json": {
        "component_type": "振荡器",
        "category": "HCSL SPXO",
        "frequency_unit": "MHz",
        "frequency_multiplier": "1",
        "pdf_dir": "td_spxo_spso_mhz",
    },
    "moso_hcsl.json": {
        "component_type": "振荡器",
        "category": "HCSL SAW振荡器",
        "frequency_unit": "MHz",
        "frequency_multiplier": "1",
        "pdf_dir": "td_spxo_spso_mhz",
        "special": "SAW",
    },
    "moso_lvds.json": {
        "component_type": "振荡器",
        "category": "LVDS SAW振荡器",
        "frequency_unit": "MHz",
        "frequency_multiplier": "1",
        "pdf_dir": "td_spxo_spso_mhz",
        "special": "SAW",
    },
    "moso_lvpecl.json": {
        "component_type": "振荡器",
        "category": "LV-PECL SAW振荡器",
        "frequency_unit": "MHz",
        "frequency_multiplier": "1",
        "pdf_dir": "td_spxo_spso_mhz",
        "special": "SAW",
    },
    "spso_lvds.json": {
        "component_type": "振荡器",
        "category": "LVDS SPSO",
        "frequency_unit": "MHz",
        "frequency_multiplier": "1",
        "pdf_dir": "td_spxo_spso_mhz",
    },
    "spso_lvpecl.json": {
        "component_type": "振荡器",
        "category": "LV-PECL SPSO",
        "frequency_unit": "MHz",
        "frequency_multiplier": "1",
        "pdf_dir": "td_spxo_spso_mhz",
    },
    "tcxo_a.json": {
        "component_type": "振荡器",
        "category": "TCXO/VC-TCXO",
        "frequency_unit": "MHz",
        "frequency_multiplier": "1",
        "pdf_dir": "td_tcxo_mhz",
        "special": "温补",
    },
    "tcxo_b.json": {
        "component_type": "振荡器",
        "category": "高稳定度TCXO/VC-TCXO",
        "frequency_unit": "MHz",
        "frequency_multiplier": "1",
        "pdf_dir": "td_tcxo_mhz",
        "special": "温补",
    },
    "ss_osc.json": {
        "component_type": "振荡器",
        "category": "扩频晶体振荡器",
        "frequency_unit": "MHz",
        "frequency_multiplier": "1",
        "pdf_dir": "td_ss_osc_mhz",
        "special": "扩频/EMI",
    },
    "vcxo_cmos.json": {
        "component_type": "振荡器",
        "category": "CMOS VCXO",
        "frequency_unit": "MHz",
        "frequency_multiplier": "1",
        "pdf_dir": "td_vcxo_vcso_mhz",
        "special": "压控",
    },
    "vcxo_lvds.json": {
        "component_type": "振荡器",
        "category": "LVDS VCXO",
        "frequency_unit": "MHz",
        "frequency_multiplier": "1",
        "pdf_dir": "td_vcxo_vcso_mhz",
        "special": "压控",
    },
    "vcxo_lvpecl.json": {
        "component_type": "振荡器",
        "category": "LV-PECL VCXO",
        "frequency_unit": "MHz",
        "frequency_multiplier": "1",
        "pdf_dir": "td_vcxo_vcso_mhz",
        "special": "压控",
    },
    "vcxo_sine_wave.json": {
        "component_type": "振荡器",
        "category": "正弦波VCXO",
        "frequency_unit": "MHz",
        "frequency_multiplier": "1",
        "pdf_dir": "td_vcxo_vcso_mhz",
        "special": "压控",
    },
    "rtc.json": {
        "component_type": "实时时钟模块",
        "category": "RTC实时时钟模块",
        "frequency_unit": "kHz",
        "fixed_frequency": "32.768",
        "pdf_dir": "",
        "special": "内置32.768kHz晶体",
    },
}

RX8025T_REFERENCE_URL = "https://www.nscn.cn/tech/rx8025t-ub-uc.html"
RX8025T_DISTRIBUTOR_URL = (
    "https://www.lcsc.com/product-detail/"
    "Real-time-Clocks-RTC_Seiko-Epson-RX8025T-UC_C53691.html"
)
RX8025T_VARIANTS = (
    {
        "model": "RX8025T-UB",
        "temperature": "-40~+85°C",
        "grade": "工业级/内置DTCXO",
    },
    {
        "model": "RX8025T-UC",
        "temperature": "-30~+70°C",
        "grade": "商业级/内置DTCXO",
    },
)


def clean_text(value: Any) -> str:
    text = str(value or "").strip()
    return "" if text.lower() in {"nan", "none", "null"} else text


def decimal_text(value: Any, multiplier: str = "1") -> str:
    raw = clean_text(value)
    if raw == "":
        return ""
    try:
        number = Decimal(raw) * Decimal(multiplier)
    except (InvalidOperation, ValueError):
        return raw
    text = format(number, "f")
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    return text or "0"


def normalize_frequency_tolerance(value: Any) -> str:
    text = clean_text(value).upper().replace("±", "+/-")
    if text == "":
        return ""
    matches = re.findall(r"\+/-\s*(\d+(?:\.\d+)?)", text)
    if matches:
        return decimal_text(matches[-1])
    match = re.search(r"(\d+(?:\.\d+)?)", text)
    return decimal_text(match.group(1)) if match else ""


def normalize_ppm_spec(value: Any) -> str:
    text = html.unescape(clean_text(value)).replace("−", "-").replace("＋", "+")
    text = re.sub(r"\s+", " ", text).strip()
    if text == "":
        return ""
    upper = text.upper()
    if "INCLUDED IN" in upper:
        years = re.search(r"(\d+)\s*YEARS?", upper)
        if "FIRST YEAR" in upper:
            return "包含在总频差内（首年）"
        if years:
            return f"包含在总频差内（{years.group(1)}年）"
        return "包含在总频差内"
    if upper == "TBD":
        return "TBD"
    numbers = []
    for match in re.finditer(r"[+\-]?\+?\d+(?:\.\d+)?", text):
        try:
            numbers.append(abs(Decimal(match.group(0).replace("++", "+"))))
        except (InvalidOperation, ValueError):
            continue
    if not numbers:
        return text
    maximum = max(numbers)
    return f"±{decimal_text(maximum)}ppm"


def normalize_turnover_temperature(value: Any) -> str:
    text = html.unescape(clean_text(value))
    if text == "":
        return ""
    text = text.replace("°C", "℃").replace("degC", "℃").replace("+/-", "±")
    text = re.sub(r"\s+", " ", text).strip()
    return text


def normalize_parabolic_coefficient(value: Any) -> str:
    number = decimal_text(value)
    return f"{number}ppm/℃²" if number else ""


def normalize_overtone_order(value: Any) -> str:
    text = html.unescape(clean_text(value)).strip()
    if text == "":
        return ""
    upper = text.upper()
    if "FUNDAMENTAL" in upper:
        return "基频（Fundamental）"
    if re.search(r"\b3(?:RD)?\b", upper) and "OVERTONE" in upper:
        return "三次泛音（3rd Overtone）"
    if "OVERTONE" in upper:
        return text
    return text


def frequency_temperature_characteristic(product: dict[str, Any]) -> str:
    raw = (
        product.get("frequencyTolTempRange")
        or product.get("frequencyTolOpTemp")
        or product.get("frequncyTol")
    )
    normalized = normalize_frequency_tolerance(raw)
    return f"±{normalized}ppm" if normalized else ""


def aging_text(product: dict[str, Any]) -> str:
    return normalize_ppm_spec(product.get("frequencyAging") or product.get("25CAging"))


def automotive_grade_text(product: dict[str, Any]) -> str:
    grades = []
    if clean_text(product.get("aecq100")).lower() == "yes":
        grades.append("AEC-Q100")
    if clean_text(product.get("aecq200")).lower() == "yes":
        grades.append("AEC-Q200")
    return "/".join(grades)


def package_code(length: Any, width: Any) -> str:
    try:
        length_code = int(round(float(clean_text(length)) * 10))
        width_code = int(round(float(clean_text(width)) * 10))
    except Exception:
        return ""
    return f"{length_code:02d}{width_code:02d}"


def dimension_text(product: dict[str, Any]) -> str:
    values = [
        decimal_text(product.get("dimensionL")),
        decimal_text(product.get("dimensionW")),
        decimal_text(product.get("dimensionH")),
    ]
    return " x ".join(value for value in values if value != "")


def temperature_text(product: dict[str, Any]) -> str:
    direct = clean_text(
        product.get("operatingTempRange")
        or product.get("tempRange")
        or product.get("operatingTemp")
        or product.get("operTemperature")
    )
    if direct:
        direct = html.unescape(direct).replace("−", "-").replace("＋", "+")
        direct = direct.replace("++", "+")
        direct = re.sub(r"\s+to\s+", "~", direct, flags=re.I).replace(" ", "")
        return direct if "°C" in direct else f"{direct}°C"
    low = decimal_text(product.get("operatingTempMin"))
    high = decimal_text(product.get("operatingTempMax"))
    if low and high:
        return f"{low}~{high}°C"
    return ""


def voltage_text(product: dict[str, Any]) -> str:
    direct = clean_text(product.get("operVoltage"))
    if direct:
        return re.sub(r"\s+to\s+", "~", direct, flags=re.I).replace(" ", "")
    low = decimal_text(product.get("supplyVoltageMin"))
    typical = decimal_text(product.get("supplyVoltageTyp"))
    high = decimal_text(product.get("supplyVoltageMax"))
    if low and high and low != high:
        return f"{low}~{high}"
    return typical or low or high


def oscillator_tolerance(product: dict[str, Any], source_name: str) -> str:
    if source_name.startswith("tcxo_"):
        return normalize_frequency_tolerance(
            product.get("frequencyTolOpTemp") or product.get("frequencyTol25C")
        )
    return normalize_frequency_tolerance(
        product.get("frequencyTol25C") or product.get("frequencyTol")
    )


def special_use_text(product: dict[str, Any], source_spec: dict[str, Any]) -> str:
    values = []
    configured = clean_text(source_spec.get("special"))
    if configured:
        values.append(configured)
    if clean_text(product.get("aecq100")).lower() == "yes":
        values.append("车规/AEC-Q100")
    if clean_text(product.get("aecq200")).lower() == "yes":
        values.append("车规/AEC-Q200")
    return "/".join(dict.fromkeys(values))


def product_page_url(component_type: str, model: str) -> str:
    slug = re.sub(r"[^a-z0-9]", "", model.lower())
    if component_type == "晶振":
        family = "crystal-unit"
    elif component_type == "实时时钟模块":
        family = "rtc"
    else:
        family = "crystal-oscillator"
    return f"{PRODUCT_BASE_URL}{family}/{slug}.html"


def datasheet_url(product: dict[str, Any], source_spec: dict[str, Any]) -> str:
    if clean_text(product.get("pdf_switch")) != "1":
        return ""
    model = clean_text(product.get("model"))
    pn = clean_text(product.get("pn"))
    pdf_dir = clean_text(source_spec.get("pdf_dir"))
    if pdf_dir == "":
        return ""
    if source_spec.get("series_pdf"):
        filename = f"{model}_en.pdf"
    else:
        filename = f"{model}_{pn}_en.pdf"
    return f"{PDF_BASE_URL}{pdf_dir}/{filename}"


def build_summary(
    product: dict[str, Any],
    source_spec: dict[str, Any],
    frequency: str,
    tolerance: str,
    voltage: str,
) -> str:
    temp_characteristic = frequency_temperature_characteristic(product)
    aging = aging_text(product)
    turnover = normalize_turnover_temperature(product.get("turnoverTemp"))
    parabolic = normalize_parabolic_coefficient(product.get("parabolicCoef"))
    overtone = normalize_overtone_order(product.get("overtoneOrder"))
    parts = [
        f"Epson官方PN {clean_text(product.get('pn'))}",
        clean_text(source_spec.get("category")),
        f"{frequency}{source_spec.get('frequency_unit', '')}" if frequency else "",
        dimension_text(product),
        f"频差±{tolerance}ppm" if tolerance else "",
        f"输出{clean_text(product.get('output'))}" if clean_text(product.get("output")) else "",
        f"电源{voltage}V" if voltage else "",
        f"负载电容{clean_text(product.get('loadCapPf') or product.get('loadCap'))}pF"
        if clean_text(product.get("loadCapPf") or product.get("loadCap"))
        else "",
        f"接口{clean_text(product.get('interface'))}" if clean_text(product.get("interface")) else "",
        f"计时电压{clean_text(product.get('clockVoltage'))}V"
        if clean_text(product.get("clockVoltage"))
        else "",
        f"备用电流{clean_text(product.get('backUpCurrent'))}µA"
        if clean_text(product.get("backUpCurrent"))
        else "",
        f"月偏差{clean_text(product.get('monthlyDeviation_sec'))}s"
        if clean_text(product.get("monthlyDeviation_sec"))
        else "",
        temperature_text(product),
        f"温度特性{temp_characteristic}" if temp_characteristic else "",
        f"25℃老化{aging}" if aging else "",
        f"拐点温度{turnover}" if turnover else "",
        f"抛物线系数{parabolic}" if parabolic else "",
        overtone,
        clean_text(product.get("description")),
    ]
    return "；".join(part for part in parts if clean_text(part))


def build_product_row(
    product: dict[str, Any],
    source_name: str,
    source_spec: dict[str, Any],
    checked_at: str,
) -> dict[str, Any]:
    component_type = clean_text(source_spec["component_type"])
    model = clean_text(product.get("model"))
    pn = clean_text(product.get("pn"))
    fixed_frequency = clean_text(source_spec.get("fixed_frequency"))
    frequency = fixed_frequency or decimal_text(
        product.get(clean_text(source_spec.get("frequency_field")) or "frequencyMin"),
        multiplier=clean_text(source_spec.get("frequency_multiplier")) or "1",
    )
    tolerance = (
        normalize_frequency_tolerance(product.get("frequencyTol25C"))
        if component_type == "晶振"
        else (
            normalize_frequency_tolerance(product.get("frequncyTol"))
            if component_type == "实时时钟模块"
            else oscillator_tolerance(product, source_name)
        )
    )
    voltage = voltage_text(product) if component_type in {"振荡器", "实时时钟模块"} else ""
    size_code = (
        ""
        if component_type == "实时时钟模块"
        else package_code(product.get("dimensionL"), product.get("dimensionW"))
    )
    size_mm = dimension_text(product)
    source_url = f"{JSON_BASE_URL}{source_name}"
    load_cap = clean_text(product.get("loadCapPf") or product.get("loadCap"))
    esr = clean_text(product.get("esrMax"))
    if esr:
        esr = f"{esr}{'kΩ' if source_name == 'xtal_32khz.json' else 'Ω'} Max"
    drive = clean_text(product.get("driveLevel"))
    if drive:
        drive = f"{drive}µW Max"
    duty = clean_text(product.get("symmetry"))
    if not duty:
        duty_min = clean_text(product.get("symmetryMin"))
        duty_max = clean_text(product.get("symmetryMax"))
        if duty_min and duty_max:
            duty = f"{duty_min}~{duty_max}"
    if duty and "%" not in duty:
        duty = re.sub(r"\s+to\s+", "~", duty, flags=re.I) + "%"

    series_desc = f"Epson {model} {clean_text(source_spec.get('category'))}系列"
    special_use = special_use_text(product, source_spec)
    temp_characteristic = frequency_temperature_characteristic(product)
    aging = aging_text(product)
    turnover = normalize_turnover_temperature(product.get("turnoverTemp"))
    parabolic = normalize_parabolic_coefficient(product.get("parabolicCoef"))
    overtone = normalize_overtone_order(product.get("overtoneOrder"))
    aec_grade = automotive_grade_text(product)
    return {
        "品牌": BRAND,
        "型号": pn,
        "系列": model,
        "尺寸（inch）": size_code,
        "材质（介质）": (
            "Quartz"
            if component_type == "晶振"
            else ("内置石英晶体/RTC IC" if component_type == "实时时钟模块" else "")
        ),
        "容值": frequency,
        "容值单位": clean_text(source_spec.get("frequency_unit")),
        "容值误差": tolerance,
        "耐压（V）": voltage,
        "特殊用途": special_use,
        "备注1": clean_text(product.get("description")),
        "备注2": datasheet_url(product, source_spec),
        "备注3": source_url,
        "器件类型": component_type,
        "安装方式": "贴片",
        "封装代码": clean_text(product.get("pkgType")) if component_type == "实时时钟模块" else size_code,
        "尺寸（mm）": size_mm,
        "规格摘要": build_summary(product, source_spec, frequency, tolerance, voltage),
        "生产状态": "官网选型器可选",
        "长度（mm）": decimal_text(product.get("dimensionL")),
        "宽度（mm）": decimal_text(product.get("dimensionW")),
        "高度（mm）": decimal_text(product.get("dimensionH")),
        "官网链接": product_page_url(component_type, model),
        "数据来源": source_url,
        "数据状态": "Epson官方产品编号级参数",
        "校验时间": checked_at,
        "校验备注": "型号、频率及关键参数由Epson官方参数选型JSON直接映射",
        "ESR": esr,
        "工作温度": temperature_text(product),
        "系列说明": series_desc,
        "输出频率": frequency if component_type in {"振荡器", "实时时钟模块"} else "",
        "频率": frequency if component_type == "晶振" else "",
        "频率单位": clean_text(source_spec.get("frequency_unit")),
        "频差（ppm）": f"±{tolerance}ppm" if tolerance else "",
        "电源电压": voltage,
        "输出类型": clean_text(product.get("output")),
        "占空比": duty,
        "负载电容（pF）": load_cap,
        "驱动电平": drive,
        "尺寸来源": "Epson官方参数选型JSON",
        "型号粒度": "官方逐料号",
        "频率温度特性（ppm）": temp_characteristic,
        "25℃老化（ppm）": aging,
        "拐点温度": turnover,
        "抛物线系数（ppm/℃²）": parabolic,
        "泛音阶次": overtone,
        "AEC等级": aec_grade,
        "官方规格编号": pn,
        "接口类型": clean_text(product.get("interface")),
        "计时电压（V）": re.sub(
            r"\s+to\s+",
            "~",
            clean_text(product.get("clockVoltage")),
            flags=re.I,
        ).replace(" ", ""),
        "备用电流（µA）": clean_text(product.get("backUpCurrent")),
        "月偏差（s）": clean_text(product.get("monthlyDeviation_sec")),
    }


def build_rtc_series_alias_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    aliases: list[dict[str, Any]] = []
    seen_models: set[str] = set()
    for row in rows:
        if clean_text(row.get("器件类型")) != "实时时钟模块":
            continue
        model = clean_text(row.get("系列"))
        if model == "" or model in seen_models:
            continue
        seen_models.add(model)
        alias = dict(row)
        alias["型号"] = model
        alias["型号粒度"] = "官方系列型号/具体PN需确认"
        alias["官方规格编号"] = ""
        alias["数据状态"] = "Epson官方系列级参数"
        alias["校验备注"] = "系列型号来自Epson官方RTC参数选型JSON；下单前需确认完整产品编号"
        aliases.append(alias)
    return aliases


def build_rx8025t_variant_rows(checked_at: str) -> list[dict[str, Any]]:
    rows = []
    for variant in RX8025T_VARIANTS:
        model = clean_text(variant["model"])
        temperature = clean_text(variant["temperature"])
        grade = clean_text(variant["grade"])
        rows.append(
            {
                "品牌": BRAND,
                "型号": model,
                "系列": "RX8025T",
                "尺寸（inch）": "",
                "材质（介质）": "内置32.768kHz DTCXO/RTC IC",
                "容值": "32.768",
                "容值单位": "kHz",
                "容值误差": "5",
                "耐压（V）": "2.2~5.5",
                "特殊用途": grade,
                "备注1": "I²C实时时钟模块；内置32.768kHz数字温度补偿晶体振荡器",
                "备注2": RX8025T_DISTRIBUTOR_URL if model.endswith("-UC") else "",
                "备注3": RX8025T_REFERENCE_URL,
                "器件类型": "实时时钟模块",
                "安装方式": "贴片",
                "封装代码": "SOP-14-208mil",
                "尺寸（mm）": "",
                "规格摘要": (
                    f"Epson {model}；RTC实时时钟模块；32.768kHz；"
                    f"频率温度特性±5ppm；{temperature}；I²C；"
                    "接口电压2.2~5.5V；计时电压1.8~5.5V；备用电流0.8µA典型"
                ),
                "生产状态": "渠道可购，Epson全球参数选型未列出",
                "官网链接": RX8025T_REFERENCE_URL,
                "数据来源": RX8025T_REFERENCE_URL,
                "数据状态": "爱普生授权代理与经销渠道型号资料确认",
                "校验时间": checked_at,
                "校验备注": "中国市场型号；参数与型号由爱普生授权代理资料和经销渠道MPN交叉确认",
                "工作温度": temperature,
                "系列说明": "Epson RX8025T 内置DTCXO的I²C实时时钟模块",
                "输出频率": "32.768",
                "频率单位": "kHz",
                "频差（ppm）": "±5ppm",
                "电源电压": "2.2~5.5",
                "负载电容（pF）": "",
                "尺寸来源": "渠道资料SOP-14-208mil",
                "型号粒度": "渠道确认精确型号",
                "频率温度特性（ppm）": "±5ppm",
                "AEC等级": "",
                "接口类型": "I²C",
                "计时电压（V）": "1.8~5.5",
                "备用电流（µA）": "0.8 Typ.",
                "月偏差（s）": "",
            }
        )
    return rows


def build_http_session() -> requests.Session:
    retry = Retry(
        total=6,
        connect=6,
        read=6,
        backoff_factor=0.8,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=frozenset({"GET"}),
    )
    session = requests.Session()
    session.headers.update(
        {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 Chrome/132 Safari/537.36"
            )
        }
    )
    session.mount("https://", HTTPAdapter(max_retries=retry))
    return session


def fetch_official_rows(timeout: int = 45) -> tuple[pd.DataFrame, dict[str, int]]:
    checked_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    rows: list[dict[str, Any]] = []
    counts: dict[str, int] = {}
    session = build_http_session()
    try:
        for source_name, source_spec in SOURCE_SPECS.items():
            response = session.get(f"{JSON_BASE_URL}{source_name}", timeout=timeout)
            response.raise_for_status()
            products = response.json()
            if not isinstance(products, list):
                raise RuntimeError(f"{source_name} did not return a product list")
            counts[source_name] = len(products)
            for product in products:
                if not isinstance(product, dict):
                    continue
                if clean_text(product.get("pn")) == "" or clean_text(product.get("model")) == "":
                    continue
                rows.append(build_product_row(product, source_name, source_spec, checked_at))
        rows.extend(build_rtc_series_alias_rows(rows))
        supplemental_rows = build_rx8025t_variant_rows(checked_at)
        counts["rx8025t_channel_variants"] = len(supplemental_rows)
        rows.extend(supplemental_rows)
    finally:
        session.close()

    frame = pd.DataFrame(rows)
    if len(frame) < MIN_EXPECTED_ROWS:
        raise RuntimeError(f"Epson official result is unexpectedly small: {len(frame)} rows")
    if frame["型号"].duplicated().any():
        duplicates = frame.loc[frame["型号"].duplicated(keep=False), "型号"].head(10).tolist()
        raise RuntimeError(f"Epson official product numbers are duplicated: {duplicates}")
    if frame["容值"].astype(str).str.strip().eq("").any():
        raise RuntimeError("Epson official result contains rows without an exact frequency")
    return frame.sort_values(["器件类型", "系列", "型号"], kind="stable").reset_index(drop=True), counts


def write_csv_atomically(frame: pd.DataFrame, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(
        prefix=f"{output_path.name}.",
        suffix=".tmp",
        dir=str(output_path.parent),
    )
    os.close(fd)
    temp_path = Path(temp_name)
    try:
        frame.to_csv(temp_path, index=False, encoding="utf-8-sig")
        os.replace(temp_path, output_path)
    finally:
        temp_path.unlink(missing_ok=True)


def prepare_runtime_cache_frame(
    frame: pd.DataFrame,
    source_path: Path,
) -> tuple[pd.DataFrame, pd.DataFrame, int]:
    normalized = cm.normalize_imported_component_dataframe(frame, source_path=str(source_path))
    normalized = cm.deduplicate_component_rows(normalized)
    cache_frames = [normalized]
    companion_rows = 0
    if (
        MULTIBRAND_TIMING_SOURCE is not None
        and MULTIBRAND_TIMING_SOURCE.exists()
        and MULTIBRAND_TIMING_SOURCE.resolve() != source_path.resolve()
    ):
        companion_frame = pd.read_csv(
            MULTIBRAND_TIMING_SOURCE,
            dtype=str,
            keep_default_na=False,
        )
        companion_normalized = cm.normalize_imported_component_dataframe(
            companion_frame,
            source_path=str(MULTIBRAND_TIMING_SOURCE),
        )
        companion_normalized = cm.deduplicate_component_rows(companion_normalized)
        companion_rows = int(len(companion_normalized))
        cache_frames.append(companion_normalized)
    combined = pd.concat(cache_frames, ignore_index=True, sort=False)
    combined = cm.deduplicate_component_rows(combined)
    prepared = cm.prepare_search_dataframe(combined)
    return normalized, prepared, companion_rows


def refresh_runtime_caches(frame: pd.DataFrame, source_path: Path) -> dict[str, int]:
    normalized, prepared, companion_rows = prepare_runtime_cache_frame(
        frame,
        source_path,
    )
    if prepared.empty:
        raise RuntimeError("Epson rows produced an empty prepared cache frame")
    counts = refresh_search_sidecar_rows(prepared)
    try:
        replaced = replace_prepared_cache_rows(prepared)
    except PermissionError:
        # A running Streamlit process can keep the parquet file open on Windows.
        # The search sidecar is already refreshed and serves timing queries.
        replaced = -1
    return {
        "source_rows": int(len(frame)),
        "normalized_rows": int(len(normalized)),
        "companion_rows": companion_rows,
        "prepared_rows": int(len(prepared)),
        "prepared_rows_replaced": int(replaced),
        "search_core_rows": int(counts.get(cm.COMPONENTS_SEARCH_CORE_TABLE, 0)),
        "search_value_rows": int(counts.get(cm.COMPONENTS_SEARCH_VALUE_TABLE, 0)),
    }


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    parser = argparse.ArgumentParser(
        description="Synchronize Epson official crystal, oscillator, and RTC product numbers."
    )
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT))
    parser.add_argument("--timeout", type=int, default=45)
    parser.add_argument(
        "--apply-cache",
        action="store_true",
        help="Incrementally update the prepared and search caches after writing the source CSV.",
    )
    args = parser.parse_args()

    output_path = Path(args.output)
    if not output_path.is_absolute():
        output_path = (ROOT / output_path).resolve()

    frame, source_counts = fetch_official_rows(timeout=args.timeout)
    write_csv_atomically(frame, output_path)
    print(f"source_csv={output_path}")
    print(f"official_rows={len(frame)}")
    print(f"crystal_rows={(frame['器件类型'] == '晶振').sum()}")
    print(f"oscillator_rows={(frame['器件类型'] == '振荡器').sum()}")
    print(f"rtc_rows={(frame['器件类型'] == '实时时钟模块').sum()}")
    print("source_counts=" + ",".join(f"{key}:{value}" for key, value in source_counts.items()))

    if args.apply_cache:
        cache_counts = refresh_runtime_caches(frame, output_path)
        for key, value in cache_counts.items():
            print(f"{key}={value}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
