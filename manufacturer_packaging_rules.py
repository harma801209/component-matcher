from __future__ import annotations

import re
from typing import Any


YAGEO_RC_SOURCE = "https://yageogroup.com/content/datasheet/asset/file/PYU-RC_GROUP_51_ROHS_L"
PANASONIC_RESISTOR_SOURCE = "https://industrial.panasonic.com/cdbs/www-data/pdf/RDM0000/DMM0000COL26.pdf"
VISHAY_NTCS_SOURCES = {
    "0402": "https://www.vishay.com/docs/29003/ntcs0402e3t.pdf",
    "0603": "https://www.vishay.com/docs/29056/ntcs0603e3t.pdf",
    "0805": "https://www.vishay.com/docs/29044/ntcs0805e3t.pdf",
}
TDK_MLCC_PRODUCT_URL = "https://product.tdk.com/en/search/capacitor/ceramic/mlcc/info?part_no={}"

YAGEO_RC_7_INCH_QUANTITIES = {
    ("0075", "S"): 20000,
    ("0100", "R"): 20000,
    ("0201", "R"): 10000,
    ("0402", "R"): 10000,
    ("0603", "R"): 5000,
    ("0805", "R"): 5000,
    ("1206", "R"): 5000,
    ("1210", "R"): 5000,
    ("1218", "K"): 4000,
    ("2010", "K"): 4000,
    ("2512", "K"): 4000,
}

PANASONIC_STANDARD_REEL_QUANTITIES = {
    "0201": 15000,
    "0402": 10000,
    "0603": 5000,
    "0805": 5000,
    "1206": 5000,
    "1210": 5000,
    "1812": 5000,
    "2010": 5000,
    "2512": 4000,
}


def _text(record: Any, *keys: str) -> str:
    for key in keys:
        value = record.get(key, "")
        if value is not None:
            text = str(value).strip()
            if text and text.lower() not in {"nan", "none"}:
                return text
    return ""


def _brand_key(value: object) -> str:
    return re.sub(r"[^A-Z0-9\u4e00-\u9fff]+", "", str(value or "").upper())


def _model_text(value: object) -> str:
    return re.sub(r"\s+", "", str(value or "").upper())


def _packaging_result(quantity: int, method: str, source_name: str, source_url: str) -> dict[str, str]:
    return {
        "MOQ": f"{int(quantity)}PCS",
        "MOQ来源": f"原厂标准包装数量：{source_name}",
        "包装方式": method,
        "包装数量来源": source_url,
    }


def lookup_manufacturer_packaging(record: Any) -> dict[str, str]:
    if record is None or not hasattr(record, "get"):
        return {}
    brand = _brand_key(_text(record, "品牌"))
    model = _model_text(_text(record, "型号"))
    series = _text(record, "系列").upper()
    size = _text(record, "尺寸（inch）", "尺寸").upper()
    if not model:
        return {}

    if ("YAGEO" in brand or "国巨" in brand) and series == "RC":
        match = re.match(r"^RC(?P<size>0075|0100|0201|0402|0603|0805|1206|1210|1218|2010|2512)[A-Z](?P<pack>[RKS])-07", model)
        if match and (not size or size == match.group("size")):
            key = (match.group("size"), match.group("pack"))
            quantity = YAGEO_RC_7_INCH_QUANTITIES.get(key)
            if quantity:
                method = "178mm纸带卷盘" if key[1] == "R" else "178mm压纹/ESD卷盘"
                return _packaging_result(quantity, method, "YAGEO RC_L Table 4", YAGEO_RC_SOURCE)

    if "PANASONIC" in brand and (model.startswith("ERJ") or model.startswith("ERA")):
        quantity = PANASONIC_STANDARD_REEL_QUANTITIES.get(size)
        if quantity and not (model.startswith("ERA") and size in {"1210", "1812", "2010", "2512"}):
            return _packaging_result(
                quantity,
                "Panasonic标准载带卷盘",
                "Panasonic Surface Mount Resistors Packaging Method",
                PANASONIC_RESISTOR_SOURCE,
            )

    if "VISHAY" in brand or "威世" in brand:
        vishay_rules = {
            "NTCS0402E": ("0402", 10000),
            "NTCS0603E": ("0603", 4000),
            "NTCS0805E": ("0805", 4000),
        }
        for prefix, (rule_size, quantity) in vishay_rules.items():
            if model.startswith(prefix) and (not size or size == rule_size):
                return _packaging_result(
                    quantity,
                    "8mm冲孔纸带卷盘",
                    f"Vishay {prefix} datasheet",
                    VISHAY_NTCS_SOURCES[rule_size],
                )

    if ("TDK" in brand or "东电化" in brand) and series == "C" and size == "0603":
        clean_model = re.sub(r"[^A-Z0-9]", "", model)
        if re.fullmatch(r"C1608[A-Z0-9]+080A[A-Z]", clean_model):
            return _packaging_result(
                4000,
                "180mm冲孔纸带卷盘",
                "TDK C1608/080/A official product packaging",
                TDK_MLCC_PRODUCT_URL.format(clean_model),
            )

    return {}
