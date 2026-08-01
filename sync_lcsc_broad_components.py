from __future__ import annotations

import argparse
import math
import os
import re
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable

import pandas as pd
import requests

import component_matcher as cm
from incremental_semiconductor_cache_update import (
    collect_prepared_pairs_by_source_markers,
    refresh_search_sidecar_rows,
    replace_prepared_cache_rows,
)


ROOT = Path(__file__).resolve().parent
LCSC_QUERY_URL = "https://wmsc.lcsc.com/ftps/wm/product/query/list"
PAGE_SIZE = 100
SOURCE_MARKER = "LCSC category exact MPN"

CATEGORY_CONFIG = {
    "electrolytic": {
        "catalog_ids": (1140,),
        "output": ROOT / "Capacitor" / "lcsc_all_brand_electrolytic.csv",
    },
    "timing": {
        "catalog_ids": (1155, 1157),
        "output": next(
            (path for path in ROOT.glob("Crystal*") if path.is_dir()),
            ROOT / "Crystal",
        )
        / "lcsc_all_brand_timing_exact_mpn.csv",
    },
}
CRYSTAL_DIR = CATEGORY_CONFIG["timing"]["output"].parent

COMMON_COLUMNS = [
    "器件类型",
    "品牌",
    "型号",
    "系列",
    "安装方式",
    "封装代码",
    "尺寸（inch）",
    "尺寸（mm）",
    "规格摘要",
    "生产状态",
    "官网链接",
    "数据来源",
    "数据状态",
    "校验时间",
    "校验备注",
    "备注1",
    "备注2",
    "备注3",
    "容值",
    "容值单位",
    "容值误差",
    "耐压（V）",
    "直径（mm）",
    "高度（mm）",
    "长度（mm）",
    "宽度（mm）",
    "脚距（mm）",
    "极性",
    "ESR",
    "纹波电流",
    "寿命（h）",
    "工作温度",
    "特殊用途",
    "MOQ",
    "封装数量",
    "型号粒度",
    "资料完整度",
    "缺失关键参数",
    "频率",
    "频率单位",
    "频差（ppm）",
    "输出频率",
    "电源电压",
    "输出类型",
    "负载电容（pF）",
    "频率温度特性（ppm）",
    "存储温度",
    "AEC等级",
    "官方规格编号",
]


def clean_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, float) and math.isnan(value):
        return ""
    text = str(value).strip()
    return "" if text.lower() in {"nan", "none", "null", "-"} else text


def first_number(value: Any) -> str:
    match = re.search(r"[+\-]?\d+(?:\.\d+)?", clean_text(value).replace(",", ""))
    if not match:
        return ""
    number = match.group(0).lstrip("+")
    try:
        numeric = float(number)
    except ValueError:
        return number
    return str(int(numeric)) if numeric.is_integer() else f"{numeric:.12f}".rstrip("0").rstrip(".")


def normalized_model(value: Any) -> str:
    return re.sub(r"[\s_\-]", "", clean_text(value).upper())


def canonical_brand(value: Any) -> str:
    text = clean_text(value)
    upper = re.sub(r"[^A-Z0-9]", "", text.upper())
    if upper == "NCC":
        return "日本贵弥功Chemi-Con"
    aliases = (
        (("NIPPONCHEMICON", "CHEMICON"), "日本贵弥功Chemi-Con"),
        (("NICHICON",), "尼吉康Nichicon"),
        (("PANASONIC",), "松下Panasonic"),
        (("JIANGHAI",), "江海Jianghai"),
        (("RUBYCON",), "Rubycon"),
        (("EPSON",), "爱普生Epson"),
        (("KYOCERA",), "京瓷Kyocera"),
        (("DAISHINKU", "KDS"), "KDS大真空"),
        (("SIWARD",), "希华Siward"),
        (("SITIME",), "SiTime"),
        (("ABRACON",), "Abracon"),
        (("HOSONIC",), "鸿星HOSONIC"),
        (("TKD",), "TKD泰晶"),
        (("HELE",), "YL惠伦"),
        (("MURATA",), "村田Murata"),
    )
    for needles, label in aliases:
        if any(needle in upper for needle in needles):
            return label
    return text


def query_page(
    *,
    catalog_id: int,
    current_page: int,
    brand_id: int | None = None,
    retries: int = 5,
) -> dict[str, Any]:
    payload = {
        "globalKeyword": "",
        "scene": "",
        "catalogIdList": [int(catalog_id)],
        "brandIdList": [] if brand_id is None else [int(brand_id)],
        "encapValueList": [],
        "isStock": False,
        "isHot": False,
        "isDiscount": False,
        "isNew": False,
        "isPreSale": False,
        "isRecom": False,
        "paramNameValueMap": {},
        "currentPage": int(current_page),
        "pageSize": PAGE_SIZE,
    }
    referer = (
        f"https://www.lcsc.com/category/{catalog_id}.html"
        if brand_id is None
        else f"https://www.lcsc.com/category/{catalog_id}.html?brand={brand_id}"
    )
    last_error: Exception | None = None
    for attempt in range(retries):
        try:
            response = requests.post(
                LCSC_QUERY_URL,
                json=payload,
                headers={
                    "Content-Type": "application/json",
                    "Referer": referer,
                    "User-Agent": "Mozilla/5.0 component-library-sync/1.0",
                },
                timeout=120,
            )
            response.raise_for_status()
            data = response.json()
            result = data.get("result")
            if data.get("code") != 200 or not isinstance(result, dict):
                raise RuntimeError(clean_text(data.get("msg")) or f"LCSC code {data.get('code')}")
            return result
        except Exception as exc:  # network retries are intentionally bounded
            last_error = exc
            if attempt + 1 < retries:
                time.sleep(min(8.0, 0.8 * (2**attempt)))
    raise RuntimeError(
        f"LCSC page failed: catalog={catalog_id}, brand={brand_id}, page={current_page}"
    ) from last_error


def fetch_remaining_pages(
    catalog_id: int,
    brand_id: int | None,
    first_page: dict[str, Any],
    workers: int,
) -> list[dict[str, Any]]:
    pages = [first_page]
    total_pages = int(first_page.get("totalPage") or 0)
    if total_pages <= 1:
        return pages
    with ThreadPoolExecutor(max_workers=max(1, workers)) as executor:
        futures = {
            executor.submit(
                query_page,
                catalog_id=catalog_id,
                brand_id=brand_id,
                current_page=page_number,
            ): page_number
            for page_number in range(2, total_pages + 1)
        }
        ordered: dict[int, dict[str, Any]] = {}
        for future in as_completed(futures):
            ordered[futures[future]] = future.result()
    pages.extend(ordered[number] for number in sorted(ordered))
    return pages


def discover_brands(catalog_id: int, workers: int) -> tuple[dict[int, str], int]:
    first = query_page(catalog_id=catalog_id, current_page=1)
    actual_total = int(first.get("actualTotalRow") or first.get("totalRow") or 0)
    pages = fetch_remaining_pages(catalog_id, None, first, workers)
    brands: dict[int, str] = {}
    for page in pages:
        for row in page.get("dataList") or []:
            brand_id = row.get("brandId")
            if brand_id is None:
                continue
            brands[int(brand_id)] = clean_text(row.get("brandNameEn")) or str(brand_id)
    return brands, actual_total


def fetch_brand_rows(catalog_id: int, brand_id: int) -> tuple[list[dict[str, Any]], int, bool]:
    first = query_page(catalog_id=catalog_id, brand_id=brand_id, current_page=1)
    actual_total = int(first.get("actualTotalRow") or first.get("totalRow") or 0)
    total_row = int(first.get("totalRow") or 0)
    pages = [first]
    for page_number in range(2, int(first.get("totalPage") or 0) + 1):
        pages.append(
            query_page(
                catalog_id=catalog_id,
                brand_id=brand_id,
                current_page=page_number,
            )
        )
    rows = [row for page in pages for row in (page.get("dataList") or [])]
    return rows, actual_total, actual_total <= total_row


def fetch_catalog_rows(catalog_id: int, workers: int) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    brands, catalog_actual = discover_brands(catalog_id, workers)
    fetched: list[dict[str, Any]] = []
    capped: list[str] = []
    errors: list[str] = []
    with ThreadPoolExecutor(max_workers=max(1, workers)) as executor:
        futures = {
            executor.submit(fetch_brand_rows, catalog_id, brand_id): (brand_id, brand_name)
            for brand_id, brand_name in brands.items()
        }
        for future in as_completed(futures):
            brand_id, brand_name = futures[future]
            try:
                rows, _actual, complete = future.result()
                fetched.extend(rows)
                if not complete:
                    capped.append(f"{brand_name}({brand_id})")
            except Exception as exc:
                errors.append(f"{brand_name}({brand_id}): {exc}")
    return fetched, {
        "catalog_id": catalog_id,
        "catalog_actual_rows": catalog_actual,
        "discovered_brands": len(brands),
        "fetched_rows": len(fetched),
        "capped_brands": capped,
        "errors": errors,
    }


def param_map(row: dict[str, Any]) -> dict[str, str]:
    result: dict[str, str] = {}
    for item in row.get("paramVOList") or []:
        name = clean_text(item.get("paramNameEn") or item.get("paramName"))
        value = clean_text(item.get("paramValueEn") or item.get("paramValue"))
        if name and value:
            result[name] = value
    return result


def quantity(value: Any, default_unit: str = "") -> tuple[str, str]:
    text = clean_text(value).replace("μ", "u").replace("µ", "u")
    match = re.search(r"([+\-]?\d+(?:\.\d+)?)\s*([A-Za-z]+)?", text)
    if not match:
        return "", default_unit
    return first_number(match.group(1)), clean_text(match.group(2)).upper() or default_unit


def frequency_quantity(value: Any, fallback_text: Any = "") -> tuple[str, str]:
    number, unit = quantity(value, "")
    if number and unit in {"HZ", "KHZ", "MHZ", "GHZ"}:
        return number, unit
    text = clean_text(fallback_text).replace("μ", "u").replace("µ", "u")
    match = re.search(r"(?<![A-Z0-9.])(\d+(?:\.\d+)?)\s*(GHZ|MHZ|KHZ|HZ)(?![A-Z])", text, re.I)
    if not match:
        return "", ""
    return first_number(match.group(1)), match.group(2).upper()


def is_exact_timing_model(value: Any) -> bool:
    """Reject distributor description text that is not a stable orderable MPN."""
    model = clean_text(value).strip()
    if not model or len(model) > 120:
        return False

    compact = re.sub(r"\s+", "", model.upper())
    if not re.search(r"\d", compact):
        return False
    if not re.search(r"[A-Z]", compact) and re.fullmatch(r"[0-9._-]{5,}", compact):
        return True

    # Some distributor rows put only frequency/tolerance/voltage or package
    # tokens in productModel, for example "85MHz 25PPM 3.3V". Those values
    # are useful specifications but are not manufacturer order numbers.
    residue = model.upper()
    residue = re.sub(r"[+\-]?\d+(?:\.\d+)?(?:GHZ|MHZ|KHZ|HZ)", "", residue)
    residue = re.sub(r"[+\-]?\d+(?:\.\d+)?PPM", "", residue)
    residue = re.sub(r"[+\-]?\d+(?:\.\d+)?(?:PF|V)", "", residue)
    residue = re.sub(r"(?<![A-Z0-9])\d+(?:\.\d+)?[MK](?![A-Z0-9])", "", residue)
    residue = re.sub(r"(?<![A-Z0-9])\d+P(?![A-Z0-9])", "", residue)
    residue = re.sub(r"(?:SMD)?\d{4}(?:-\d+P)?", "", residue)
    residue = re.sub(r"(?:CRYSTAL|OSCILLATOR|OSC|XO|TCXO|VCXO|OCXO)", "", residue)
    residue = re.sub(r"[^A-Z0-9]", "", residue)
    if not residue:
        return False

    # Numeric and single-letter manufacturer codes can be valid order numbers,
    # so reject only when the value is completely explained by specification
    # tokens rather than requiring a particular model-code shape.
    return bool(residue)


def extract_dimensions(row: dict[str, Any], parameters: dict[str, str]) -> dict[str, str]:
    package = clean_text(row.get("encapStandard"))
    diameter = first_number(parameters.get("Diameter"))
    height = first_number(parameters.get("Height - Seated (Max)"))
    pitch = first_number(parameters.get("Pin Spacing"))
    if not diameter:
        match = re.search(r"D\s*(\d+(?:\.\d+)?)", package, re.I)
        diameter = first_number(match.group(1)) if match else ""
    if not height:
        match = re.search(r"L\s*(\d+(?:\.\d+)?)", package, re.I)
        height = first_number(match.group(1)) if match else ""
    body = f"{diameter}×{height}" if diameter and height else ""
    smd_match = re.search(r"(?:SMD)?(\d{4})(?:-\d+P)?", package.upper())
    size_code = smd_match.group(1) if smd_match else ""
    length = width = ""
    if size_code:
        length = first_number(int(size_code[:2]) / 10)
        width = first_number(int(size_code[2:]) / 10)
    return {
        "package": package,
        "diameter": diameter,
        "height": height,
        "pitch": pitch,
        "body": body,
        "size_code": size_code,
        "length": length,
        "width": width,
    }


def production_status(value: Any) -> str:
    text = clean_text(value)
    return "量产" if text.lower() == "normal" else text


def source_urls(row: dict[str, Any]) -> tuple[str, str, str]:
    product_code = clean_text(row.get("productCode"))
    product_url = clean_text(row.get("url")) or (
        f"https://www.lcsc.com/product-detail/{product_code}.html" if product_code else ""
    )
    pdf_url = clean_text(row.get("pdfUrl") or row.get("pdfLinkUrl"))
    return product_code, product_url, pdf_url


def completeness(required: dict[str, str]) -> tuple[str, str]:
    missing = [name for name, value in required.items() if clean_text(value) == ""]
    if not missing:
        return "关键参数完整", ""
    return "需确认", "、".join(missing)


def build_electrolytic_row(row: dict[str, Any], checked_at: str) -> dict[str, str]:
    parameters = param_map(row)
    capacitance, capacitance_unit = quantity(parameters.get("Capacitance"), "UF")
    voltage = first_number(parameters.get("Voltage Rating"))
    tolerance = clean_text(parameters.get("Tolerance"))
    dimensions = extract_dimensions(row, parameters)
    lifetime = first_number(parameters.get("Lifetime"))
    product_code, product_url, pdf_url = source_urls(row)
    model = clean_text(row.get("productModel"))
    brand = canonical_brand(row.get("brandNameEn"))
    installation = "贴片" if "SMD" in dimensions["package"].upper() else "插件"
    status, missing = completeness(
        {
            "容值": capacitance,
            "耐压": voltage,
            "误差": tolerance,
            "尺寸": dimensions["body"],
            "工作温度": clean_text(parameters.get("Operating Temperature")),
        }
    )
    intro = clean_text(row.get("productIntroEn"))
    return {
        "器件类型": "铝电解电容",
        "品牌": brand,
        "型号": model,
        "系列": "",
        "安装方式": installation,
        "封装代码": dimensions["package"],
        "尺寸（mm）": dimensions["body"],
        "规格摘要": intro or f"{brand} {model}",
        "生产状态": production_status(row.get("productCycle")),
        "官网链接": pdf_url or product_url,
        "数据来源": SOURCE_MARKER,
        "数据状态": "专业分销商逐料号；原厂规格书优先核验",
        "校验时间": checked_at,
        "校验备注": f"LCSC {product_code} exact MPN" + ("; manufacturer PDF attached" if pdf_url else "; PDF missing"),
        "备注1": intro,
        "备注2": pdf_url,
        "备注3": product_url,
        "容值": capacitance,
        "容值单位": capacitance_unit,
        "容值误差": tolerance,
        "耐压（V）": voltage,
        "直径（mm）": dimensions["diameter"],
        "高度（mm）": dimensions["height"],
        "脚距（mm）": dimensions["pitch"],
        "极性": "有极性",
        "ESR": clean_text(parameters.get("Equivalent Series Resistance(ESR)")),
        "纹波电流": clean_text(parameters.get("Ripple Current")),
        "寿命（h）": lifetime,
        "工作温度": clean_text(parameters.get("Operating Temperature")),
        "MOQ": first_number(row.get("minBuyNumber")),
        "封装数量": first_number(row.get("minPacketNumber")),
        "型号粒度": "专业分销商逐料号",
        "资料完整度": status,
        "缺失关键参数": missing,
        "官方规格编号": model,
    }


def timing_component_type(row: dict[str, Any], catalog_id: int) -> str:
    catalog_name = clean_text(row.get("catalogName")).upper()
    if catalog_id == 1157 or any(word in catalog_name for word in ("OSCILLATOR", "TCXO", "VCXO", "OCXO")):
        return "振荡器"
    return "晶振"


def build_timing_row(row: dict[str, Any], catalog_id: int, checked_at: str) -> dict[str, str] | None:
    parameters = param_map(row)
    component_type = timing_component_type(row, catalog_id)
    intro = clean_text(row.get("productIntroEn"))
    frequency, frequency_unit = frequency_quantity(parameters.get("Frequency"), intro)
    # LCSC contains a small number of unrelated legacy products under its timing
    # categories. A real crystal/oscillator must expose an explicit frequency.
    if not frequency or not frequency_unit:
        return None
    tolerance = clean_text(
        parameters.get("Normal temperature Frequency Tolerance")
        or parameters.get("Frequency Stability")
    )
    voltage = first_number(parameters.get("Voltage - Supply"))
    load_capacitance = first_number(parameters.get("Load Capacitance"))
    dimensions = extract_dimensions(row, parameters)
    product_code, product_url, pdf_url = source_urls(row)
    model = clean_text(row.get("productModel"))
    if not is_exact_timing_model(model):
        return None
    brand = canonical_brand(row.get("brandNameEn"))
    required = {
        "频率": frequency,
        "封装尺寸": dimensions["size_code"],
        "频差/稳定度": tolerance,
        "工作温度": clean_text(parameters.get("Operating Temperature")),
    }
    if component_type == "晶振":
        required["负载电容"] = load_capacitance
        required["ESR"] = clean_text(parameters.get("Equivalent Series Resistance(ESR)"))
    else:
        required["电源电压"] = voltage
    status, missing = completeness(required)
    return {
        "器件类型": component_type,
        "品牌": brand,
        "型号": model,
        "系列": "",
        "安装方式": "贴片" if dimensions["size_code"] or "SMD" in dimensions["package"].upper() else "",
        "封装代码": dimensions["size_code"] or dimensions["package"],
        "尺寸（inch）": dimensions["size_code"],
        "尺寸（mm）": " x ".join(value for value in (dimensions["length"], dimensions["width"]) if value),
        "长度（mm）": dimensions["length"],
        "宽度（mm）": dimensions["width"],
        "规格摘要": intro or f"{brand} {model}",
        "生产状态": production_status(row.get("productCycle")),
        "官网链接": pdf_url or product_url,
        "数据来源": SOURCE_MARKER,
        "数据状态": "专业分销商逐料号；原厂规格书优先核验",
        "校验时间": checked_at,
        "校验备注": f"LCSC {product_code} exact MPN" + ("; manufacturer PDF attached" if pdf_url else "; PDF missing"),
        "备注1": intro,
        "备注2": pdf_url,
        "备注3": product_url,
        "容值": frequency,
        "容值单位": frequency_unit,
        "容值误差": tolerance,
        "ESR": clean_text(parameters.get("Equivalent Series Resistance(ESR)")),
        "工作温度": clean_text(parameters.get("Operating Temperature")),
        "MOQ": first_number(row.get("minBuyNumber")),
        "封装数量": first_number(row.get("minPacketNumber")),
        "型号粒度": "专业分销商逐料号",
        "资料完整度": status,
        "缺失关键参数": missing,
        "频率": frequency if component_type == "晶振" else "",
        "频率单位": frequency_unit,
        "频差（ppm）": tolerance,
        "输出频率": frequency if component_type == "振荡器" else "",
        "电源电压": voltage,
        "输出类型": clean_text(parameters.get("Output Type")),
        "负载电容（pF）": load_capacitance,
        "频率温度特性（ppm）": clean_text(parameters.get("Frequency Stability")),
        "存储温度": clean_text(parameters.get("Storage Temperature")),
        "AEC等级": "AEC-Q200" if "AEC-Q200" in intro.upper() else "",
        "官方规格编号": model,
    }


def finalize_rows(rows: Iterable[dict[str, str] | None]) -> pd.DataFrame:
    frame = pd.DataFrame(row for row in rows if row is not None).reindex(columns=COMMON_COLUMNS, fill_value="")
    if frame.empty:
        return frame
    frame["品牌"] = frame["品牌"].map(canonical_brand)
    frame["型号"] = frame["型号"].map(clean_text)
    frame = frame[(frame["品牌"] != "") & (frame["型号"] != "")].copy()
    frame["_model_key"] = frame["型号"].map(normalized_model)
    frame["_quality"] = (
        frame["资料完整度"].eq("关键参数完整").astype(int) * 10
        + frame["备注2"].ne("").astype(int) * 3
        + frame["生产状态"].eq("量产").astype(int)
    )
    frame = frame.sort_values(["品牌", "_model_key", "_quality"], ascending=[True, True, False])
    frame = frame.drop_duplicates(["品牌", "_model_key"], keep="first")
    return frame.drop(columns=["_model_key", "_quality"]).reset_index(drop=True)


def write_csv_atomically(frame: pd.DataFrame, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=output_path.name + ".", suffix=".tmp", dir=output_path.parent)
    os.close(fd)
    temp_path = Path(temp_name)
    try:
        frame.to_csv(temp_path, index=False, encoding="utf-8-sig")
        os.replace(temp_path, output_path)
    finally:
        temp_path.unlink(missing_ok=True)


def prepared_identity_key(frame: pd.DataFrame) -> pd.Series:
    brand = frame["品牌"].astype(str).map(
        lambda value: cm.canonical_cost_price_brand_label(value).upper()
    )
    model = frame["型号"].astype(str).map(cm.clean_model)
    if "_component_type" in frame.columns:
        component_type = frame["_component_type"].astype(str).map(cm.normalize_component_type)
    else:
        component_type = frame.apply(
            lambda row: cm.infer_db_component_type(row)
            or cm.normalize_component_type(row.get("器件类型", "")),
            axis=1,
        )
    return brand + "|" + model + "|" + component_type


def merge_authoritative_timing_overlaps(
    normalized: pd.DataFrame,
    source_paths: set[Path],
) -> pd.DataFrame:
    if normalized is None or normalized.empty:
        return normalized
    timing_mask = normalized["器件类型"].astype(str).map(cm.normalize_component_type).isin(
        cm.TIMING_COMPONENT_TYPES
    )
    if not timing_mask.any():
        return normalized

    target_keys = set(prepared_identity_key(cm.prepare_search_dataframe(normalized.loc[timing_mask])))
    authoritative_frames: list[pd.DataFrame] = []
    resolved_sources = {path.resolve() for path in source_paths}
    for path in sorted(CRYSTAL_DIR.glob("*.csv")):
        if path.resolve() in resolved_sources or "lcsc" in path.name.lower():
            continue
        try:
            source = pd.read_csv(path, dtype=str, keep_default_na=False)
            source_normalized = cm.normalize_imported_component_dataframe(source, source_path=str(path))
            source_prepared = cm.prepare_search_dataframe(source_normalized)
        except Exception:
            continue
        if source_prepared.empty:
            continue
        overlap = source_prepared[prepared_identity_key(source_prepared).isin(target_keys)].copy()
        if not overlap.empty:
            authoritative_frames.append(overlap)

    if not authoritative_frames:
        return normalized
    combined = pd.concat(
        [cm.prepare_search_dataframe(normalized)] + authoritative_frames,
        ignore_index=True,
        sort=False,
    )
    combined = cm.prioritize_component_rows_for_lookup(combined)
    combined["_broad_sync_identity"] = prepared_identity_key(combined)
    combined = combined.drop_duplicates("_broad_sync_identity", keep="first")
    return combined.drop(columns=["_broad_sync_identity"], errors="ignore").reset_index(drop=True)


def refresh_runtime_caches(frames: list[tuple[pd.DataFrame, Path]]) -> dict[str, int]:
    normalized_frames = [
        cm.normalize_imported_component_dataframe(frame, source_path=str(path))
        for frame, path in frames
        if frame is not None and not frame.empty
    ]
    normalized = cm.deduplicate_component_rows(pd.concat(normalized_frames, ignore_index=True))
    normalized = merge_authoritative_timing_overlaps(
        normalized,
        {path.resolve() for _frame, path in frames},
    )
    prepared = cm.prepare_search_dataframe(normalized)
    if prepared.empty:
        raise RuntimeError("broad component sync produced an empty prepared frame")
    stale_pairs = collect_prepared_pairs_by_source_markers({SOURCE_MARKER})
    counts = refresh_search_sidecar_rows(prepared, extra_remove_pairs=stale_pairs)
    try:
        replaced = replace_prepared_cache_rows(prepared, extra_remove_pairs=stale_pairs)
    except (FileNotFoundError, PermissionError):
        replaced = -1
    return {
        "normalized_rows": len(normalized),
        "prepared_rows": len(prepared),
        "prepared_rows_replaced": replaced,
        "search_core_rows": counts.get(cm.COMPONENTS_SEARCH_CORE_TABLE, 0),
        "search_value_rows": counts.get(cm.COMPONENTS_SEARCH_VALUE_TABLE, 0),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Synchronize broad exact-MPN timing and electrolytic data from LCSC categories.")
    parser.add_argument("--groups", default="electrolytic,timing", help="Comma-separated groups: electrolytic,timing")
    parser.add_argument("--workers", type=int, default=6)
    parser.add_argument("--apply-cache", action="store_true")
    args = parser.parse_args()
    selected = {value.strip().lower() for value in args.groups.split(",") if value.strip()}
    invalid = selected - set(CATEGORY_CONFIG)
    if invalid:
        raise SystemExit(f"unknown groups: {','.join(sorted(invalid))}")

    checked_at = datetime.now().strftime("%Y-%m-%d")
    written: list[tuple[pd.DataFrame, Path]] = []
    for group in ("electrolytic", "timing"):
        if group not in selected:
            continue
        config = CATEGORY_CONFIG[group]
        source_rows: list[tuple[int, dict[str, Any]]] = []
        reports: list[dict[str, Any]] = []
        for catalog_id in config["catalog_ids"]:
            rows, report = fetch_catalog_rows(int(catalog_id), max(1, args.workers))
            reports.append(report)
            source_rows.extend((int(catalog_id), row) for row in rows)
        if group == "electrolytic":
            frame = finalize_rows(build_electrolytic_row(row, checked_at) for _catalog, row in source_rows)
        else:
            frame = finalize_rows(build_timing_row(row, catalog, checked_at) for catalog, row in source_rows)
        output_path = Path(config["output"])
        write_csv_atomically(frame, output_path)
        written.append((frame, output_path))
        print(f"group={group}")
        print(f"source_csv={output_path}")
        print(f"exact_rows={len(frame)}")
        print(f"brands={frame['品牌'].nunique() if not frame.empty else 0}")
        print(f"complete_rows={(frame['资料完整度'] == '关键参数完整').sum() if not frame.empty else 0}")
        for report in reports:
            print(
                "catalog_report="
                f"{report['catalog_id']} actual:{report['catalog_actual_rows']} "
                f"brands:{report['discovered_brands']} fetched:{report['fetched_rows']} "
                f"capped:{len(report['capped_brands'])} errors:{len(report['errors'])}"
            )
            if report["capped_brands"]:
                print("capped_brands=" + ",".join(report["capped_brands"]))
            if report["errors"]:
                print("fetch_errors=" + " | ".join(report["errors"]))
    if args.apply_cache and written:
        for key, value in refresh_runtime_caches(written).items():
            print(f"{key}={value}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
