from __future__ import annotations

import argparse
import io
import json
import math
import os
import re
import sys
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.parse import urljoin

import pandas as pd
import requests

import component_matcher as cm
from incremental_semiconductor_cache_update import (
    refresh_search_sidecar_rows,
    replace_prepared_cache_rows,
)


ROOT = Path(__file__).resolve().parent
CRYSTAL_DIR = next((path for path in ROOT.glob("Crystal*") if path.is_dir()), ROOT / "Crystal")
DEFAULT_OUTPUT = CRYSTAL_DIR / "多品牌官方晶振资料.csv"

NDK_API_URL = "https://www.ndk.com/cgi-bin/parametric/searchlist.php"
NDK_PRODUCTS_BASE = "https://www.ndk.com"
KYOCERA_BASE = "https://ele.kyocera.com"
TXC_SEARCH_URL = "https://www.txccorp.com/en/search/act/?act=1&filter=&page=1&keyword="

KYOCERA_SOURCES = {
    "crystal": {
        "url": f"{KYOCERA_BASE}/sites/default/files/headless/en__3926.json",
        "component_type": "晶振",
        "category": "Crystal Units",
    },
    "spxo": {
        "url": f"{KYOCERA_BASE}/sites/default/files/headless/en__3931.json",
        "component_type": "振荡器",
        "category": "Clock Oscillators (SPXO)",
    },
    "tcxo": {
        "url": f"{KYOCERA_BASE}/sites/default/files/headless/en__3941.json",
        "component_type": "振荡器",
        "category": "Temperature Compensated Crystal Oscillators (TCXO)",
    },
}

KDS_SOURCES = {
    "https://www.kds.info/en/products/model/1-l-qr/": "晶振",
    "https://www.kds.info/en/products/model/m-qr-khz/": "晶振",
    "https://www.kds.info/en/products/model/m-qr-tsb/": "晶振",
    "https://www.kds.info/en/products/model/tcxo/": "振荡器",
    "https://www.kds.info/en/products/model/spxo/": "振荡器",
    "https://www.kds.info/en/products/model/vcxo/": "振荡器",
    "https://www.kds.info/en/products/model/4-l-mems/": "振荡器",
}

MURATA_SOURCES = [
    "https://www.murata.com/en-us/products/timingdevice/crystalu/overview/lineup/xrcgefxm",
    "https://www.murata.com/en-us/products/timingdevice/crystalu/overview/lineup/xrcgbfc",
    "https://www.murata.com/en-us/products/timingdevice/crystalu/overview/lineup/xrcgefa",
    "https://www.murata.com/en-us/products/timingdevice/crystalu/overview/lineup/xrcgafa",
    "https://www.murata.com/en-us/products/timingdevice/crystalu/overview/lineup/xrcgbfa",
    "https://www.murata.com/en-us/products/timingdevice/crystalu/overview/lineup/xrcgb",
]

SITIME_SOURCES = [
    "https://www.sitime.com/products/mhz-oscillators/lvcmos-oscillators",
    "https://www.sitime.com/products/mhz-oscillators/differential-oscillators",
    "https://www.sitime.com/products/mhz-oscillators/high-temperature-oscillators",
    "https://www.sitime.com/products/mhz-oscillators/spread-spectrum-oscillators",
    "https://www.sitime.com/products/mhz-oscillators/voltage-controlled-oscillators",
    "https://www.sitime.com/products/32-khz-mpower-oscillators/32-khz-oscillators",
    "https://www.sitime.com/products/32-khz-mpower-oscillators/32-khz-tcxos",
    "https://www.sitime.com/products/32-khz-mpower-oscillators/1-hz-462-khz-oscillators",
    "https://www.sitime.com/products/32-khz-mpower-oscillators/1-26-mhz-oscillators",
]

STANDARD_COLUMNS = [
    "品牌",
    "型号",
    "系列",
    "尺寸（inch）",
    "材质（介质）",
    "容值",
    "容值单位",
    "容值误差",
    "耐压（V）",
    "特殊用途",
    "备注1",
    "备注2",
    "备注3",
    "器件类型",
    "安装方式",
    "封装代码",
    "尺寸（mm）",
    "规格摘要",
    "生产状态",
    "长度（mm）",
    "宽度（mm）",
    "高度（mm）",
    "官网链接",
    "数据来源",
    "数据状态",
    "校验时间",
    "校验备注",
    "ESR",
    "工作温度",
    "系列说明",
    "输出频率",
    "频率",
    "频率单位",
    "频差（ppm）",
    "电源电压",
    "输出类型",
    "占空比",
    "负载电容（pF）",
    "驱动电平",
    "尺寸来源",
    "型号粒度",
    "频率下限",
    "频率上限",
    "频率选项",
    "频差选项",
    "电压选项",
    "负载电容选项",
    "储存温度",
    "频率温度特性（ppm）",
    "泛音阶次",
    "AEC等级",
    "封装数量",
    "官方规格编号",
    "长期稳定度",
    "相位噪声",
]


def clean_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, float) and math.isnan(value):
        return ""
    text = str(value).strip()
    return "" if text.lower() in {"nan", "none", "null"} else text


def clean_number(value: Any) -> str:
    text = clean_text(value)
    if text == "":
        return ""
    match = re.search(r"[+\-]?\d+(?:\.\d+)?", text.replace(",", ""))
    if not match:
        return ""
    number = match.group(0).lstrip("+")
    try:
        numeric = float(number)
    except Exception:
        return number
    if numeric.is_integer():
        return str(int(numeric))
    return f"{numeric:.12f}".rstrip("0").rstrip(".")


def normalized_option_string(values: list[Any]) -> str:
    normalized = []
    for value in values:
        number = clean_number(value)
        if number != "" and number not in normalized:
            normalized.append(number)
    return "|" + "|".join(normalized) + "|" if normalized else ""


def extract_numeric_options(text: Any, *, ppb_to_ppm: bool = False) -> list[str]:
    raw = clean_text(text).replace(",", "")
    values = []
    for match in re.finditer(r"[+\-]?\d+(?:\.\d+)?", raw):
        number = clean_number(match.group(0))
        if number == "":
            continue
        if ppb_to_ppm and "PPB" in raw.upper():
            number = clean_number(float(number) / 1000.0)
        if number not in values:
            values.append(number)
    return values


def frequency_profile(text: Any, default_unit: str) -> dict[str, str]:
    raw = clean_text(text).replace(",", "")
    unit_match = re.search(r"\b(GHZ|MHZ|KHZ|HZ)\b", raw, flags=re.I)
    unit = (unit_match.group(1) if unit_match else default_unit).upper()
    values = extract_numeric_options(raw)
    if not values:
        return {"unit": unit, "exact": "", "minimum": "", "maximum": "", "options": ""}

    has_range = bool(
        re.search(r"(?:\bTO\b|~|≤|≦|≥|≧|>=|<=|－|–|—|<|>)", raw, flags=re.I)
    )
    exact = values[0] if len(values) == 1 and not has_range else ""
    minimum = values[0] if has_range and len(values) >= 2 else ""
    maximum = values[1] if has_range and len(values) >= 2 else ""
    remaining = values[2:] if has_range and len(values) > 2 else values if not has_range and len(values) > 1 else []
    return {
        "unit": unit,
        "exact": exact,
        "minimum": minimum,
        "maximum": maximum,
        "options": normalized_option_string(remaining),
    }


def tolerance_profile(text: Any) -> tuple[str, str]:
    raw = clean_text(text)
    values = extract_numeric_options(raw, ppb_to_ppm=True)
    if not values:
        return "", ""
    return values[0], normalized_option_string(values)


def voltage_profile(text: Any) -> tuple[str, str]:
    raw = clean_text(text).upper().replace("V", "").replace(" ", "")
    if raw == "":
        return "", ""
    values = extract_numeric_options(raw)
    if not values:
        return "", ""
    if re.search(r"(?:TO|~|－|–|—)", raw, flags=re.I) and len(values) >= 2:
        return f"{values[0]}~{values[1]}", normalized_option_string(values)
    return values[0], normalized_option_string(values)


def package_code_from_dimensions(length: Any, width: Any) -> str:
    try:
        length_code = int(round(float(clean_number(length)) * 10))
        width_code = int(round(float(clean_number(width)) * 10))
    except Exception:
        return ""
    if not (0 < length_code <= 99 and 0 < width_code <= 99):
        return ""
    return f"{length_code:02d}{width_code:02d}"


def dimensions_from_text(value: Any) -> tuple[str, str, str, str]:
    raw = clean_text(value).replace("×", "x").replace("*", "x")
    values = re.findall(r"\d+(?:\.\d+)?", raw)
    if len(values) < 2:
        return "", "", "", ""
    length = clean_number(values[0])
    width = clean_number(values[1])
    height = clean_number(values[2]) if len(values) >= 3 else ""
    return length, width, height, package_code_from_dimensions(length, width)


def normalize_temperature(value: Any) -> str:
    text = clean_text(value)
    if text == "":
        return ""
    text = text.replace("〜", "~").replace(" to ", "~").replace("TO", "~")
    text = text.replace("℃", "°C")
    if "°C" not in text:
        text += "°C"
    return text.replace(" ", "")


def normalize_status(value: Any) -> str:
    text = clean_text(value)
    mapping = {
        "1.In Planning": "规划中",
        "2.Production": "量产",
        "3.NRND": "NRND",
        "4.Discontinued": "停产",
        "Production": "量产",
        "New": "新品",
        "Active": "量产",
        "Sample": "样品",
        "New Product / Sample": "新品/样品",
    }
    return mapping.get(text, text)


def base_row(**values: Any) -> dict[str, Any]:
    row = {column: "" for column in STANDARD_COLUMNS}
    row.update(values)
    return row


def timing_summary(row: dict[str, Any]) -> str:
    component_type = clean_text(row.get("器件类型"))
    frequency = clean_text(row.get("频率") or row.get("输出频率"))
    frequency_unit = clean_text(row.get("频率单位"))
    if not frequency:
        minimum = clean_text(row.get("频率下限"))
        maximum = clean_text(row.get("频率上限"))
        if minimum and maximum:
            frequency = f"{minimum}~{maximum}"
    parts = [
        clean_text(row.get("品牌")),
        clean_text(row.get("型号")),
        component_type,
        f"{frequency}{frequency_unit}" if frequency else clean_text(row.get("频率选项")),
        clean_text(row.get("尺寸（mm）")),
        f"±{clean_text(row.get('频差（ppm）'))}ppm" if clean_text(row.get("频差（ppm）")) else "",
        f"CL {clean_text(row.get('负载电容（pF）'))}pF" if clean_text(row.get("负载电容（pF）")) else "",
        clean_text(row.get("输出类型")),
        f"{clean_text(row.get('电源电压'))}V" if clean_text(row.get("电源电压")) else "",
        clean_text(row.get("工作温度")),
        clean_text(row.get("特殊用途")),
    ]
    return "；".join(part for part in parts if part)


def finalize_rows(rows: list[dict[str, Any]]) -> pd.DataFrame:
    frame = pd.DataFrame(rows)
    for column in STANDARD_COLUMNS:
        if column not in frame.columns:
            frame[column] = ""
    frame = frame.loc[:, STANDARD_COLUMNS].copy()
    for column in frame.columns:
        frame[column] = frame[column].map(clean_text)
    blank_summary = frame["规格摘要"].eq("")
    if blank_summary.any():
        frame.loc[blank_summary, "规格摘要"] = frame.loc[blank_summary].apply(
            lambda row: timing_summary(row.to_dict()),
            axis=1,
        )
    frame["_key"] = (
        frame["品牌"].astype(str).str.strip()
        + "\0"
        + frame["型号"].astype(str).str.upper().str.replace(r"[\s\-_]", "", regex=True)
    )
    frame["_status_rank"] = frame["生产状态"].map(
        {"量产": 0, "新品": 1, "新品/样品": 2, "样品": 3, "规划中": 4, "NRND": 5, "停产": 9}
    ).fillna(6)
    frame = frame.sort_values(
        ["_status_rank", "型号粒度", "品牌", "型号"],
        kind="stable",
    ).drop_duplicates("_key", keep="first")
    return frame.drop(columns=["_key", "_status_rank"]).reset_index(drop=True)


def request_session() -> requests.Session:
    session = requests.Session()
    session.headers.update(
        {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132 Safari/537.36"
            )
        }
    )
    return session


def abracon_api_rows(kind: str, timeout_ms: int = 120_000) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    try:
        from playwright.sync_api import sync_playwright
    except Exception as exc:
        raise RuntimeError("Playwright is required to read the Abracon official API") from exc

    page_url = f"https://abracon.com/parametric/{kind}?part_status=Active"
    api_url = f"https://abracon.com/parametric/api/{kind}"
    all_rows: list[dict[str, Any]] = []
    columns: list[dict[str, Any]] = []
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        page = browser.new_page(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132 Safari/537.36"
            )
        )
        try:
            page.goto(page_url, wait_until="domcontentloaded", timeout=timeout_ms)
            page.wait_for_timeout(7_000)
            page_number = 1
            total = None
            while total is None or len(all_rows) < total:
                payload = {
                    "searchString": "",
                    "facetFilters": [
                        {
                            "Name": "part_status",
                            "CheckedValues": ["Active"],
                            "Ranged": False,
                        }
                    ],
                    "series": "",
                    "orderBy": [],
                    "page": page_number,
                    "resultsPerPage": 5_000,
                }
                result = page.evaluate(
                    """
                    async ([url, payload]) => {
                      const response = await fetch(url, {
                        method: "POST",
                        headers: {
                          "Content-Type": "application/json;charset=UTF-8",
                          "Accept": "application/json"
                        },
                        body: JSON.stringify(payload)
                      });
                      return {status: response.status, text: await response.text()};
                    }
                    """,
                    [api_url, payload],
                )
                if int(result["status"]) != 200 or not clean_text(result["text"]).startswith("{"):
                    raise RuntimeError(
                        f"Abracon {kind} API failed on page {page_number}: "
                        f"{result['status']} {clean_text(result['text'])[:200]}"
                    )
                document = json.loads(result["text"])
                total = int(document.get("Count", 0) or 0)
                columns = document.get("Columns", columns) or columns
                batch = document.get("Rows", []) or []
                all_rows.extend(batch)
                if not batch:
                    break
                page_number += 1
        finally:
            browser.close()
    if total is None or len(all_rows) != total:
        raise RuntimeError(f"Abracon {kind} row count mismatch: expected={total} actual={len(all_rows)}")
    return all_rows, columns


def abracon_cells(row: dict[str, Any], columns: list[dict[str, Any]]) -> dict[str, str]:
    result = {}
    cells = row.get("Cells", []) or []
    for index, column in enumerate(columns):
        if index >= len(cells):
            continue
        result[clean_text(column.get("Id"))] = clean_text(cells[index].get("Content"))
    return result


def build_abracon_rows(checked_at: str) -> list[dict[str, Any]]:
    result = []
    for kind, component_type in [("crystals", "晶振"), ("oscillators", "振荡器")]:
        source_rows, columns = abracon_api_rows(kind)
        source_url = f"https://abracon.com/parametric/{kind}?part_status=Active"
        for source_row in source_rows:
            cells = abracon_cells(source_row, columns)
            model = clean_text(source_row.get("SkuName"))
            if model == "":
                continue
            description = clean_text(source_row.get("Description"))
            frequency_text = cells.get("frequency", "")
            unit_match = re.search(r"(\d+(?:\.\d+)?)\s*(GHZ|MHZ|KHZ|HZ)", description, flags=re.I)
            default_unit = unit_match.group(2) if unit_match else "MHz"
            profile = frequency_profile(frequency_text or (unit_match.group(0) if unit_match else ""), default_unit)
            tolerance_raw = (
                cells.get("frequency_tolerance", "")
                if component_type == "晶振"
                else cells.get("frequency_stability", "")
            )
            tolerance, tolerance_options = tolerance_profile(tolerance_raw)
            length = clean_number(cells.get("length_mm", ""))
            width = clean_number(cells.get("width_mm", ""))
            height = clean_number(cells.get("height_mm", ""))
            size_code = package_code_from_dimensions(length, width)
            voltage, voltage_options = voltage_profile(cells.get("supply_voltage", ""))
            load_cap = clean_number(cells.get("load_capacitance", ""))
            official_brand = clean_text(cells.get("brand", "")) or "Abracon"
            automotive = clean_text(cells.get("automotive_rating", ""))
            row = base_row(
                品牌=official_brand,
                型号=model,
                系列=clean_text(source_row.get("Series")),
                **{
                    "尺寸（inch）": size_code,
                    "材质（介质）": "Quartz" if component_type == "晶振" else "MEMS/Quartz",
                    "容值": profile["exact"],
                    "容值单位": profile["unit"],
                    "容值误差": tolerance,
                    "耐压（V）": voltage,
                    "特殊用途": automotive,
                    "备注1": description,
                    "备注2": clean_text(source_row.get("Datasheet")),
                    "备注3": source_url,
                    "器件类型": component_type,
                    "安装方式": "贴片" if "SURFACE" in cells.get("mounting_type", "").upper() else clean_text(cells.get("mounting_type", "")),
                    "封装代码": size_code or clean_text(cells.get("package_case", "")),
                    "尺寸（mm）": " x ".join(value for value in [length, width, height] if value),
                    "生产状态": normalize_status(cells.get("part_status", "")),
                    "长度（mm）": length,
                    "宽度（mm）": width,
                    "高度（mm）": height,
                    "官网链接": clean_text(source_row.get("Datasheet")) or source_url,
                    "数据来源": f"https://abracon.com/parametric/api/{kind}",
                    "数据状态": "Abracon官方逐料号参数",
                    "校验时间": checked_at,
                    "校验备注": "型号及参数由Abracon官方参数选型API直接映射",
                    "ESR": clean_text(cells.get("esr", "")),
                    "工作温度": normalize_temperature(cells.get("operating_temperature", "")),
                    "系列说明": f"{official_brand} {clean_text(source_row.get('Series'))} {clean_text(cells.get('sub_category') or cells.get('category'))}",
                    "输出频率": profile["exact"] if component_type == "振荡器" else "",
                    "频率": profile["exact"] if component_type == "晶振" else "",
                    "频率单位": profile["unit"],
                    "频差（ppm）": tolerance,
                    "电源电压": voltage,
                    "输出类型": clean_text(cells.get("output", "")),
                    "负载电容（pF）": load_cap,
                    "尺寸来源": "Abracon官方参数选型API",
                    "型号粒度": "官方逐料号",
                    "频率下限": profile["minimum"],
                    "频率上限": profile["maximum"],
                    "频率选项": profile["options"],
                    "频差选项": tolerance_options,
                    "电压选项": voltage_options,
                    "负载电容选项": normalized_option_string(extract_numeric_options(cells.get("load_capacitance", ""))),
                    "频率温度特性（ppm）": clean_number(cells.get("frequency_stability", "")),
                    "泛音阶次": clean_text(cells.get("operating_mode", "")),
                    "AEC等级": automotive,
                    "长期稳定度": clean_text(cells.get("absolute_pull_range", "")),
                    "相位噪声": clean_text(cells.get("rms_phase_jitter_typ", "")),
                },
            )
            row["规格摘要"] = timing_summary(row)
            result.append(row)
    return result


def kyocera_field(row: dict[str, Any], field: str) -> Any:
    values = row.get(field) or []
    if not values:
        return ""
    value = values[0].get("value", "")
    if isinstance(value, dict):
        return value.get("name", "")
    return value


def build_kyocera_rows(session: requests.Session, checked_at: str) -> list[dict[str, Any]]:
    result = []
    for source_name, source_spec in KYOCERA_SOURCES.items():
        response = session.get(source_spec["url"], timeout=180)
        response.raise_for_status()
        for source_row in response.json():
            status = normalize_status(kyocera_field(source_row, "field_cry_production_status"))
            if status == "停产":
                continue
            model = clean_text(kyocera_field(source_row, "field_cry_part_num")) or clean_text(
                kyocera_field(source_row, "title")
            )
            if model == "":
                continue
            frequency = clean_text(kyocera_field(source_row, "field_cry_freq_mhz"))
            frequency_unit = "MHz"
            if frequency == "":
                frequency = clean_text(kyocera_field(source_row, "field_cry_freq_khz"))
                frequency_unit = "kHz"
            profile = frequency_profile(frequency, frequency_unit)
            tolerance_source = clean_text(kyocera_field(source_row, "field_cry_freq_tolerance"))
            if tolerance_source == "":
                tolerance_source = clean_text(kyocera_field(source_row, "field_cry_freq_temp_char"))
            tolerance, tolerance_options = tolerance_profile(tolerance_source)
            dimensions = clean_text(kyocera_field(source_row, "field_cry_dimensions"))
            length, width, height_from_dim, size_code = dimensions_from_text(dimensions)
            height = clean_number(kyocera_field(source_row, "field_cry_height_max")) or height_from_dim
            voltage, voltage_options = voltage_profile(
                kyocera_field(source_row, "field_cry_supply_voltage")
            )
            load_cap_text = clean_text(kyocera_field(source_row, "field_cry_load_capacitance"))
            load_cap = clean_number(load_cap_text)
            path_values = source_row.get("path") or []
            page_url = (
                urljoin(KYOCERA_BASE, clean_text(path_values[0].get("alias")))
                if path_values
                else source_spec["url"]
            )
            applications = [
                clean_text(value.get("value"))
                for value in source_row.get("field_cry_applications", []) or []
                if clean_text(value.get("value"))
            ]
            aec = clean_text(kyocera_field(source_row, "field_cry_aec"))
            special_use = "/".join(dict.fromkeys(([aec] if aec else []) + applications))
            model_granularity = "官方料号模板" if "*" in model or "?" in model else "官方逐料号"
            component_type = source_spec["component_type"]
            series = clean_text(kyocera_field(source_row, "field_cry_series"))
            row = base_row(
                品牌="京瓷Kyocera",
                型号=model,
                系列=series,
                **{
                    "尺寸（inch）": size_code,
                    "材质（介质）": "Quartz" if component_type == "晶振" else "",
                    "容值": profile["exact"],
                    "容值单位": profile["unit"],
                    "容值误差": tolerance,
                    "耐压（V）": voltage,
                    "特殊用途": special_use,
                    "备注1": clean_text(kyocera_field(source_row, "field_cry_type")),
                    "备注2": clean_text((source_row.get("catalog") or {}).get("file_uri")) if isinstance(source_row.get("catalog"), dict) else "",
                    "备注3": source_spec["url"],
                    "器件类型": component_type,
                    "安装方式": "贴片",
                    "封装代码": size_code,
                    "尺寸（mm）": " x ".join(value for value in [length, width, height] if value),
                    "生产状态": status,
                    "长度（mm）": length,
                    "宽度（mm）": width,
                    "高度（mm）": height,
                    "官网链接": page_url,
                    "数据来源": source_spec["url"],
                    "数据状态": f"Kyocera官方{model_granularity}",
                    "校验时间": checked_at,
                    "校验备注": "型号、频率及关键参数由Kyocera官方静态产品JSON直接映射",
                    "工作温度": normalize_temperature(
                        f"{kyocera_field(source_row, 'field_cry_temp_range_min')}~"
                        f"{kyocera_field(source_row, 'field_cry_temp_range_max')}"
                    ),
                    "系列说明": f"Kyocera {series} {source_spec['category']}",
                    "输出频率": profile["exact"] if component_type == "振荡器" else "",
                    "频率": profile["exact"] if component_type == "晶振" else "",
                    "频率单位": profile["unit"],
                    "频差（ppm）": tolerance,
                    "电源电压": voltage,
                    "输出类型": clean_text(kyocera_field(source_row, "field_cry_output_type")),
                    "负载电容（pF）": load_cap,
                    "尺寸来源": "Kyocera官方产品JSON",
                    "型号粒度": model_granularity,
                    "频率下限": profile["minimum"],
                    "频率上限": profile["maximum"],
                    "频率选项": profile["options"],
                    "频差选项": tolerance_options,
                    "电压选项": voltage_options,
                    "负载电容选项": normalized_option_string(extract_numeric_options(load_cap_text)),
                    "频率温度特性（ppm）": clean_number(
                        kyocera_field(source_row, "field_cry_temp_char")
                    ),
                    "AEC等级": aec,
                    "封装数量": clean_text(
                        kyocera_field(source_row, "field_cry_quantity_per_package")
                    ),
                },
            )
            row["规格摘要"] = timing_summary(row)
            result.append(row)
    return result


def ndk_categories(session: requests.Session) -> list[dict[str, Any]]:
    response = session.post(
        NDK_API_URL,
        data={
            "category": "other",
            "subcategory": "categories",
            "rowmax": 99,
            "language": "英語",
        },
        timeout=90,
    )
    response.raise_for_status()
    document = response.json()
    if document.get("status") != "ok":
        raise RuntimeError("NDK category API returned a failed status")
    return document.get("data", []) or []


def build_ndk_rows(session: requests.Session, checked_at: str) -> list[dict[str, Any]]:
    result = []
    for category in ndk_categories(session):
        response = session.post(
            NDK_API_URL,
            data={
                "category": category["大分類"],
                "subcategory": category["小分類"],
                "rowmax": 9999,
                "language": "英語",
                "page": 1,
            },
            timeout=240,
        )
        response.raise_for_status()
        document = response.json()
        if document.get("status") != "ok":
            raise RuntimeError(f"NDK API failed: {category['小分類']}")
        component_type = "晶振" if category["大分類名"] == "Crystal Units" else "振荡器"
        subcategory_name = clean_text(category.get("小分類名"))
        default_unit = "kHz" if ("kHz" in subcategory_name or "音叉" in category["小分類"]) else "MHz"
        for source_row in document.get("data", []) or []:
            series = clean_text(source_row.get("Model"))
            spec_number = clean_text(source_row.get("Specification number"))
            profile = frequency_profile(source_row.get("Nominal frequency"), default_unit)
            if series == "" or (
                profile["exact"] == ""
                and profile["minimum"] == ""
                and profile["options"] == ""
            ):
                continue
            frequency_label = profile["exact"] or (
                f"{profile['minimum']}~{profile['maximum']}"
                if profile["minimum"] and profile["maximum"]
                else clean_text(source_row.get("Nominal frequency"))
            )
            model = " · ".join(
                part
                for part in [
                    series,
                    f"{frequency_label}{profile['unit']}" if frequency_label else "",
                    spec_number,
                ]
                if part
            )
            model_granularity = (
                "官方系列范围"
                if profile["minimum"] or profile["maximum"] or profile["options"]
                else "官方型号+频率+规格编号"
            )
            tolerance_source = (
                source_row.get("Frequency tolerance")
                if component_type == "晶振"
                else source_row.get("Frequency temperature characteristics Max.")
                or source_row.get("Frequency tolerance Max.")
                or source_row.get("Frequency tolerance")
            )
            tolerance, tolerance_options = tolerance_profile(tolerance_source)
            dimension_text = clean_text(source_row.get("Package size(LxW)"))
            length, width, _height_from_dim, size_code = dimensions_from_text(dimension_text)
            height = clean_number(source_row.get("Package size(H)"))
            voltage, voltage_options = voltage_profile(source_row.get("Supply voltage"))
            load_cap_text = clean_text(source_row.get("Load capacitance"))
            load_cap = clean_number(load_cap_text)
            product_url = urljoin(
                NDK_PRODUCTS_BASE,
                clean_text(source_row.get("製品情報へのURL")),
            )
            datasheet = clean_text(source_row.get("データシート"))
            datasheet_url = (
                f"https://www.ndk.com/en/products/upload/lineup/pdf/{datasheet}"
                if datasheet
                else ""
            )
            aec = clean_text(source_row.get("AEC"))
            features = clean_text(source_row.get("Features"))
            row = base_row(
                品牌="NDK",
                型号=model,
                系列=series,
                **{
                    "尺寸（inch）": size_code,
                    "材质（介质）": "Quartz",
                    "容值": profile["exact"],
                    "容值单位": profile["unit"],
                    "容值误差": tolerance,
                    "耐压（V）": voltage,
                    "特殊用途": "/".join(value for value in [aec, features] if value),
                    "备注1": features,
                    "备注2": datasheet_url,
                    "备注3": NDK_API_URL,
                    "器件类型": component_type,
                    "安装方式": "贴片",
                    "封装代码": size_code,
                    "尺寸（mm）": " x ".join(value for value in [length, width, height] if value),
                    "生产状态": normalize_status(source_row.get("Status")),
                    "长度（mm）": length,
                    "宽度（mm）": width,
                    "高度（mm）": height,
                    "官网链接": product_url,
                    "数据来源": NDK_API_URL,
                    "数据状态": (
                        "NDK官方系列范围，需确认具体频率配置"
                        if model_granularity == "官方系列范围"
                        else "NDK官方型号+频率+规格编号"
                    ),
                    "校验时间": checked_at,
                    "校验备注": "NDK官网说明下单时须同时指定型号、频率及规格编号",
                    "ESR": clean_text(source_row.get("Equivalent series resistance")),
                    "工作温度": normalize_temperature(
                        source_row.get("Operating temperature rang")
                    ),
                    "系列说明": f"NDK {series} {subcategory_name}",
                    "输出频率": profile["exact"] if component_type == "振荡器" else "",
                    "频率": profile["exact"] if component_type == "晶振" else "",
                    "频率单位": profile["unit"],
                    "频差（ppm）": tolerance,
                    "电源电压": voltage,
                    "输出类型": clean_text(source_row.get("Output specification")),
                    "负载电容（pF）": load_cap,
                    "驱动电平": clean_text(source_row.get("Level of drive")),
                    "尺寸来源": "NDK官方参数搜索",
                    "型号粒度": model_granularity,
                    "频率下限": profile["minimum"],
                    "频率上限": profile["maximum"],
                    "频率选项": profile["options"],
                    "频差选项": tolerance_options,
                    "电压选项": voltage_options,
                    "负载电容选项": normalized_option_string(
                        extract_numeric_options(load_cap_text)
                    ),
                    "储存温度": normalize_temperature(
                        source_row.get("Storage temperature range")
                    ),
                    "频率温度特性（ppm）": clean_number(
                        source_row.get("Frequency temperature characteristics")
                        or source_row.get("Frequency temperature characteristics Max.")
                    ),
                    "泛音阶次": clean_text(source_row.get("Overtone order")),
                    "AEC等级": aec,
                    "官方规格编号": spec_number,
                    "长期稳定度": clean_text(
                        source_row.get("Long-term frequency stability Max.")
                    ),
                    "相位噪声": clean_text(source_row.get("Phase noise Typ.")),
                },
            )
            row["规格摘要"] = timing_summary(row)
            result.append(row)
    return result


def read_official_tables(session: requests.Session, url: str) -> list[pd.DataFrame]:
    response = session.get(url, timeout=120)
    if response.status_code == 404:
        return []
    response.raise_for_status()
    try:
        return pd.read_html(io.StringIO(response.text), flavor="lxml")
    except Exception:
        return []


def dataframe_value(row: pd.Series, *names: str) -> str:
    for name in names:
        if name in row.index:
            value = clean_text(row.get(name))
            if value:
                return value
    return ""


def build_txc_rows(session: requests.Session, checked_at: str) -> list[dict[str, Any]]:
    tables = read_official_tables(session, TXC_SEARCH_URL)
    product_tables = [table for table in tables if "Product Series" in table.columns]
    if not product_tables:
        raise RuntimeError("TXC official product table was not found")
    result = []
    for source_row in pd.concat(product_tables, ignore_index=True).to_dict("records"):
        series = clean_text(source_row.get("Product Series"))
        group = clean_text(source_row.get("Product Group"))
        if series == "":
            continue
        component_type = "晶振" if ("CRYSTAL" in group.upper() or "TSX" in group.upper()) else "振荡器"
        profile = frequency_profile(source_row.get("Nominal Frequency"), "MHz")
        tolerance, tolerance_options = tolerance_profile(source_row.get("Frequency Stability"))
        length, width, height, size_code = dimensions_from_text(source_row.get("Product Size"))
        voltage, voltage_options = voltage_profile(source_row.get("Supply Voltage"))
        special_use = "/".join(
            value
            for value in [
                clean_text(source_row.get("Solutions")),
                clean_text(source_row.get("Product Features")),
            ]
            if value
        )
        row = base_row(
            品牌="TXC",
            型号=series,
            系列=series,
            **{
                "尺寸（inch）": size_code,
                "材质（介质）": "Quartz",
                "容值": profile["exact"],
                "容值单位": profile["unit"],
                "容值误差": tolerance,
                "耐压（V）": voltage,
                "特殊用途": special_use,
                "备注1": group,
                "备注2": f"https://www.txccorp.com/en/product-download/{series.lower()}/",
                "备注3": TXC_SEARCH_URL,
                "器件类型": component_type,
                "安装方式": "贴片",
                "封装代码": size_code,
                "尺寸（mm）": " x ".join(value for value in [length, width, height] if value),
                "生产状态": "官方当前系列",
                "长度（mm）": length,
                "宽度（mm）": width,
                "高度（mm）": height,
                "官网链接": f"https://www.txccorp.com/en/product-download/{series.lower()}/",
                "数据来源": TXC_SEARCH_URL,
                "数据状态": "TXC官方系列范围，需确认完整订购料号",
                "校验时间": checked_at,
                "校验备注": "系列、尺寸及参数范围由TXC官方Product Search直接映射",
                "工作温度": normalize_temperature(source_row.get("Operating Temperature")),
                "系列说明": f"TXC {series} {group}",
                "输出频率": profile["exact"] if component_type == "振荡器" else "",
                "频率": profile["exact"] if component_type == "晶振" else "",
                "频率单位": profile["unit"],
                "频差（ppm）": tolerance,
                "电源电压": voltage,
                "输出类型": clean_text(source_row.get("Output Type")),
                "尺寸来源": "TXC官方Product Search",
                "型号粒度": "官方系列范围",
                "频率下限": profile["minimum"],
                "频率上限": profile["maximum"],
                "频率选项": profile["options"],
                "频差选项": tolerance_options,
                "电压选项": voltage_options,
                "AEC等级": "AEC-Q200" if "AUTOMOTIVE" in group.upper() else "",
            },
        )
        row["规格摘要"] = timing_summary(row)
        result.append(row)
    return result


def clean_kds_model(value: Any) -> str:
    text = clean_text(value)
    text = re.sub(r"\s*[（(][^）)]*(?:ARKH|KHZ)[^）)]*[）)]\s*", "", text, flags=re.I)
    return text.strip()


def build_kds_rows(session: requests.Session, checked_at: str) -> list[dict[str, Any]]:
    merged: dict[str, dict[str, Any]] = {}
    for source_url, component_type in KDS_SOURCES.items():
        for table in read_official_tables(session, source_url):
            if "Model" not in table.columns:
                continue
            for _, source_row in table.iterrows():
                model = clean_kds_model(source_row.get("Model"))
                if model == "":
                    continue
                frequency_column = next(
                    (column for column in table.columns if str(column).startswith("Frequency [")),
                    "",
                )
                default_unit = "kHz" if "kHz" in frequency_column else "MHz"
                profile = frequency_profile(source_row.get(frequency_column, ""), default_unit)
                tolerance_source = dataframe_value(
                    source_row,
                    "Frequency Tolerance [×10-6]",
                    "Freq. Temp. Characteristics [×10-6]",
                )
                tolerance, tolerance_options = tolerance_profile(tolerance_source)
                length, width, _height_from_dim, size_code = dimensions_from_text(
                    source_row.get("Size (L×W) [mm]")
                )
                height = clean_number(source_row.get("Height (Max.) [mm]"))
                voltage, voltage_options = voltage_profile(source_row.get("Supply Voltage [V]"))
                load_cap_text = dataframe_value(source_row, "Load Capacitance [pF]")
                load_cap = clean_number(load_cap_text)
                aec = dataframe_value(source_row, "Reliability Specification")
                features = dataframe_value(source_row, "Features")
                candidate = base_row(
                    品牌="KDS大真空",
                    型号=model,
                    系列=model,
                    **{
                        "尺寸（inch）": size_code,
                        "材质（介质）": "Quartz" if component_type == "晶振" else "MEMS/Quartz",
                        "容值": profile["exact"],
                        "容值单位": profile["unit"],
                        "容值误差": tolerance,
                        "耐压（V）": voltage,
                        "特殊用途": "/".join(value for value in [aec, features] if value),
                        "备注1": features,
                        "备注2": f"https://ftp.kds.info/products/{model}_en.pdf",
                        "备注3": source_url,
                        "器件类型": component_type,
                        "安装方式": "贴片",
                        "封装代码": size_code,
                        "尺寸（mm）": " x ".join(value for value in [length, width, height] if value),
                        "生产状态": normalize_status(source_row.get("Status")),
                        "长度（mm）": length,
                        "宽度（mm）": width,
                        "高度（mm）": height,
                        "官网链接": f"https://www.kds.info/en/products/{model.lower()}/",
                        "数据来源": source_url,
                        "数据状态": "KDS官方系列范围，需确认完整订购料号",
                        "校验时间": checked_at,
                        "校验备注": "系列及参数范围由KDS官方产品表直接映射",
                        "ESR": dataframe_value(source_row, "Series Resistance (max.) [Ω]"),
                        "工作温度": normalize_temperature(
                            source_row.get("Operating Temp. Range [℃]")
                        ),
                        "系列说明": f"KDS {model} {features}".strip(),
                        "输出频率": profile["exact"] if component_type == "振荡器" else "",
                        "频率": profile["exact"] if component_type == "晶振" else "",
                        "频率单位": profile["unit"],
                        "频差（ppm）": tolerance,
                        "电源电压": voltage,
                        "输出类型": dataframe_value(source_row, "Output"),
                        "负载电容（pF）": load_cap,
                        "尺寸来源": "KDS官方产品表",
                        "型号粒度": "官方系列范围",
                        "频率下限": profile["minimum"],
                        "频率上限": profile["maximum"],
                        "频率选项": profile["options"],
                        "频差选项": tolerance_options,
                        "电压选项": voltage_options,
                        "负载电容选项": normalized_option_string(
                            extract_numeric_options(load_cap_text)
                        ),
                        "频率温度特性（ppm）": clean_number(
                            source_row.get("Freq. Temp. Characteristics [×10-6]")
                        ),
                        "AEC等级": aec,
                    },
                )
                candidate["规格摘要"] = timing_summary(candidate)
                existing = merged.get(model)
                if existing is None:
                    merged[model] = candidate
                    continue
                combined_special = "/".join(
                    dict.fromkeys(
                        value
                        for value in [
                            clean_text(existing.get("特殊用途")),
                            clean_text(candidate.get("特殊用途")),
                        ]
                        if value
                    )
                )
                existing["特殊用途"] = combined_special
                if "AEC" in combined_special.upper():
                    existing["AEC等级"] = aec or existing.get("AEC等级", "")
                if existing.get("频率下限", "") == "" and candidate.get("频率下限", ""):
                    existing["频率下限"] = candidate["频率下限"]
                    existing["频率上限"] = candidate["频率上限"]
                existing["频率选项"] = normalized_option_string(
                    extract_numeric_options(existing.get("频率选项", ""))
                    + extract_numeric_options(candidate.get("频率选项", ""))
                )
                existing["频差选项"] = normalized_option_string(
                    extract_numeric_options(existing.get("频差选项", ""))
                    + extract_numeric_options(candidate.get("频差选项", ""))
                )
                existing["负载电容选项"] = normalized_option_string(
                    extract_numeric_options(existing.get("负载电容选项", ""))
                    + extract_numeric_options(candidate.get("负载电容选项", ""))
                )
    return list(merged.values())


def build_murata_rows(session: requests.Session, checked_at: str) -> list[dict[str, Any]]:
    result = []
    for source_url in MURATA_SOURCES:
        tables = read_official_tables(session, source_url)
        for table in tables:
            if "Series" not in table.columns:
                continue
            for _, source_row in table.iterrows():
                series = clean_text(source_row.get("Series"))
                if series == "":
                    continue
                frequency_text = dataframe_value(source_row, "Frequency", "Frequency Range")
                if re.search(r"(?<![KMG])HZ", frequency_text, flags=re.I):
                    frequency_text = re.sub(
                        r"(?<![KMG])HZ",
                        "MHz",
                        frequency_text,
                        flags=re.I,
                    )
                profile = frequency_profile(frequency_text, "MHz")
                tolerance_raw = dataframe_value(source_row, "Frequency Tolerance")
                tolerance, tolerance_options = tolerance_profile(tolerance_raw)
                load_cap_text = dataframe_value(source_row, "Load Capacitance")
                load_cap = clean_number(load_cap_text)
                special_use = dataframe_value(source_row, "Remarks")
                if "AUTOMOTIVE" in source_url.upper() or "F-A" in series.upper() or "FXA" in series.upper():
                    special_use = "/".join(value for value in [special_use, "车规"] if value)
                row = base_row(
                    品牌="村田Murata",
                    型号=series,
                    系列=series,
                    **{
                        "尺寸（inch）": "2016",
                        "材质（介质）": "Quartz",
                        "容值": profile["exact"],
                        "容值单位": profile["unit"],
                        "容值误差": tolerance,
                        "特殊用途": special_use,
                        "备注1": dataframe_value(
                            source_row,
                            "Frequency Shift by Temperature",
                            "Frequency Shift by  Temperature",
                        ),
                        "备注2": source_url,
                        "备注3": source_url,
                        "器件类型": "晶振",
                        "安装方式": "贴片",
                        "封装代码": "2016",
                        "尺寸（mm）": "2.0 x 1.6",
                        "生产状态": "官方当前系列",
                        "长度（mm）": "2",
                        "宽度（mm）": "1.6",
                        "官网链接": source_url,
                        "数据来源": source_url,
                        "数据状态": "Murata官方系列范围，需确认完整订购料号",
                        "校验时间": checked_at,
                        "校验备注": "系列及参数范围由Murata官方产品页面直接映射",
                        "ESR": dataframe_value(
                            source_row,
                            "Equivalent Series Resistance (max.)",
                            "Equivalent Series  Resistance (max.)",
                        ),
                        "系列说明": f"Murata {series} crystal unit",
                        "频率": profile["exact"],
                        "频率单位": profile["unit"],
                        "频差（ppm）": tolerance,
                        "负载电容（pF）": load_cap,
                        "驱动电平": dataframe_value(
                            source_row,
                            "Drive Level (max.)",
                            "Drive Level  (max.)",
                            "Drive Level(max.)",
                        ),
                        "尺寸来源": "Murata官方产品页面",
                        "型号粒度": "官方系列范围",
                        "频率下限": profile["minimum"],
                        "频率上限": profile["maximum"],
                        "频率选项": profile["options"],
                        "频差选项": tolerance_options,
                        "负载电容选项": normalized_option_string(
                            extract_numeric_options(load_cap_text)
                        ),
                        "频率温度特性（ppm）": clean_number(
                            dataframe_value(
                                source_row,
                                "Frequency Shift by Temperature",
                                "Frequency Shift by  Temperature",
                            )
                        ),
                        "AEC等级": "AEC-Q200" if "车规" in special_use else "",
                        "长期稳定度": dataframe_value(source_row, "Frequency Aging"),
                    },
                )
                row["规格摘要"] = timing_summary(row)
                result.append(row)
    return result


def build_sitime_rows(session: requests.Session, checked_at: str) -> list[dict[str, Any]]:
    result = []
    seen = set()
    for source_url in SITIME_SOURCES:
        for table in read_official_tables(session, source_url):
            device_column = next(
                (column for column in ["Device", "Product"] if column in table.columns),
                "",
            )
            if device_column == "":
                continue
            for _, source_row in table.iterrows():
                device = clean_text(source_row.get(device_column))
                if not re.fullmatch(r"SiT[A-Z0-9\-]+", device, flags=re.I):
                    continue
                size_text = dataframe_value(
                    source_row,
                    "Package Size(mm)",
                    "Package Size(mm²)",
                    "Package Size",
                )
                size_values = re.findall(r"\d+(?:\.\d+)?\s*[xX×]\s*\d+(?:\.\d+)?", size_text)
                if not size_values:
                    size_values = [""]
                for size_text_value in size_values:
                    length, width, height, size_code = dimensions_from_text(size_text_value)
                    model = device if len(size_values) == 1 else f"{device} [{size_code}]"
                    key = (model, source_url)
                    if key in seen:
                        continue
                    seen.add(key)
                    profile = frequency_profile(source_row.get("Frequency"), "MHz")
                    tolerance, tolerance_options = tolerance_profile(
                        dataframe_value(source_row, "Stability(ppm)", "Frequency Stability (ppm)")
                    )
                    voltage, voltage_options = voltage_profile(
                        dataframe_value(source_row, "Supply Voltage(V)", "Voltage Supply (V)")
                    )
                    row = base_row(
                        品牌="SiTime",
                        型号=model,
                        系列=device,
                        **{
                            "尺寸（inch）": size_code,
                            "材质（介质）": "MEMS",
                            "容值": profile["exact"],
                            "容值单位": profile["unit"],
                            "容值误差": tolerance,
                            "耐压（V）": voltage,
                            "备注1": clean_text(source_row.get("Availability")),
                            "备注2": source_url,
                            "备注3": source_url,
                            "器件类型": "振荡器",
                            "安装方式": "贴片",
                            "封装代码": size_code,
                            "尺寸（mm）": " x ".join(value for value in [length, width, height] if value),
                            "生产状态": normalize_status(source_row.get("Availability")),
                            "长度（mm）": length,
                            "宽度（mm）": width,
                            "高度（mm）": height,
                            "官网链接": source_url,
                            "数据来源": source_url,
                            "数据状态": "SiTime官方可配置系列，需生成完整订购料号",
                            "校验时间": checked_at,
                            "校验备注": "系列和可配置范围由SiTime官方产品表直接映射",
                            "工作温度": normalize_temperature(
                                dataframe_value(
                                    source_row,
                                    "Temp. Range(°C)",
                                    "Operating Temperature Range (°C)",
                                )
                            ),
                            "系列说明": f"SiTime {device} configurable MEMS oscillator",
                            "输出频率": profile["exact"],
                            "频率单位": profile["unit"],
                            "频差（ppm）": tolerance,
                            "电源电压": voltage,
                            "输出类型": dataframe_value(source_row, "Output Type"),
                            "尺寸来源": "SiTime官方产品表",
                            "型号粒度": "官方可配置系列",
                            "频率下限": profile["minimum"],
                            "频率上限": profile["maximum"],
                            "频率选项": profile["options"],
                            "频差选项": tolerance_options,
                            "电压选项": voltage_options,
                        },
                    )
                    row["规格摘要"] = timing_summary(row)
                    result.append(row)
    return result


def fetch_official_rows(selected_sources: set[str] | None = None) -> tuple[pd.DataFrame, dict[str, int]]:
    checked_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    selected = selected_sources or {
        "abracon",
        "kyocera",
        "ndk",
        "txc",
        "kds",
        "murata",
        "sitime",
    }
    session = request_session()
    rows = []
    counts: dict[str, int] = {}
    try:
        builders = [
            ("abracon", lambda: build_abracon_rows(checked_at)),
            ("kyocera", lambda: build_kyocera_rows(session, checked_at)),
            ("ndk", lambda: build_ndk_rows(session, checked_at)),
            ("txc", lambda: build_txc_rows(session, checked_at)),
            ("kds", lambda: build_kds_rows(session, checked_at)),
            ("murata", lambda: build_murata_rows(session, checked_at)),
            ("sitime", lambda: build_sitime_rows(session, checked_at)),
        ]
        for source_name, builder in builders:
            if source_name not in selected:
                continue
            source_rows = builder()
            counts[source_name] = len(source_rows)
            rows.extend(source_rows)
    finally:
        session.close()
    frame = finalize_rows(rows)
    if "abracon" in selected and counts.get("abracon", 0) < 15_000:
        raise RuntimeError(f"Abracon official result is unexpectedly small: {counts.get('abracon', 0)}")
    if "kyocera" in selected and counts.get("kyocera", 0) < 8_000:
        raise RuntimeError(f"Kyocera official result is unexpectedly small: {counts.get('kyocera', 0)}")
    if "ndk" in selected and counts.get("ndk", 0) < 4_000:
        raise RuntimeError(f"NDK official result is unexpectedly small: {counts.get('ndk', 0)}")
    return frame, counts


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


def refresh_runtime_caches(frame: pd.DataFrame, source_path: Path) -> dict[str, int]:
    normalized = cm.normalize_imported_component_dataframe(frame, source_path=str(source_path))
    normalized = cm.deduplicate_component_rows(normalized)
    prepared = cm.prepare_search_dataframe(normalized)
    if prepared.empty:
        raise RuntimeError("Multi-brand timing rows produced an empty prepared frame")
    counts = refresh_search_sidecar_rows(prepared)
    try:
        replaced = replace_prepared_cache_rows(prepared)
    except PermissionError:
        # A running Streamlit process can keep the parquet file open on Windows.
        # The compact search sidecar is already refreshed and is sufficient for
        # public/runtime matching; defer the parquet replacement instead of
        # interrupting an active user session.
        replaced = -1
    return {
        "source_rows": int(len(frame)),
        "normalized_rows": int(len(normalized)),
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
        description="Synchronize official multi-brand crystal and oscillator data."
    )
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT))
    parser.add_argument(
        "--sources",
        default="abracon,kyocera,ndk,txc,kds,murata,sitime",
        help="Comma-separated sources: abracon,kyocera,ndk,txc,kds,murata,sitime",
    )
    parser.add_argument(
        "--apply-cache",
        action="store_true",
        help="Incrementally refresh prepared and search caches after writing the CSV.",
    )
    args = parser.parse_args()

    output_path = Path(args.output)
    if not output_path.is_absolute():
        output_path = (ROOT / output_path).resolve()
    selected_sources = {
        clean_text(value).lower()
        for value in clean_text(args.sources).split(",")
        if clean_text(value)
    }
    frame, source_counts = fetch_official_rows(selected_sources)
    write_csv_atomically(frame, output_path)
    print(f"source_csv={output_path}")
    print(f"official_rows={len(frame)}")
    print(f"crystal_rows={(frame['器件类型'] == '晶振').sum()}")
    print(f"oscillator_rows={(frame['器件类型'] == '振荡器').sum()}")
    print(
        "source_counts="
        + ",".join(f"{name}:{count}" for name, count in sorted(source_counts.items()))
    )
    print(
        "granularity_counts="
        + ",".join(
            f"{name}:{count}"
            for name, count in frame["型号粒度"].value_counts().sort_index().items()
        )
    )
    if args.apply_cache:
        for key, value in refresh_runtime_caches(frame, output_path).items():
            print(f"{key}={value}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
