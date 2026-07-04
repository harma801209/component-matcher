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
TDK_NTC_PRODUCT_URL = "https://product.tdk.com/en/search/sensor/ntc/chip-ntc-thermistor/info?part_no={}"
YAGEO_CAPACITOR_PRODUCT_URL = "https://yageogroup.com/products/Capacitors/part/{}"
MURATA_PRODUCT_URL = "https://www.murata.com/en-us/products/productdetail?partno={}"
SAMSUNG_MLCC_PRODUCT_URL = "https://product.samsungsem.com/mlcc/basic-search.do?partNumber={}"
SAMSUNG_RESISTOR_SOURCE = "https://www.samsungsem.com/resources/file/global/support/product_catalog/Chip_Resistor.pdf"
WALSIN_WR_SOURCE = "https://www.passivecomponent.com/wp-content/uploads/chipR/ASC_WR.pdf"
WALSIN_MLCC_GENERAL_SOURCE = "https://www.passivecomponent.com/wp-content/uploads/datasheet/WTC_MLCC_General_Purpose.pdf"
WALSIN_SPECIAL_MLCC_SOURCES = {
    "SH": "https://www.passivecomponent.com/wp-content/uploads/datasheet/WTC_MLCC_Soft_term_SH.pdf",
    "RF": "https://www.passivecomponent.com/wp-content/uploads/datasheet/WTC_MLCC_Microwave_RF.pdf",
    "HH": "https://www.passivecomponent.com/wp-content/uploads/datasheet/WTC_MLCC_HQ_Low_ESR_HH.pdf",
    "MT": "https://www.passivecomponent.com/wp-content/uploads/datasheet/WTC_MLCC_Automotive_MT.pdf",
}

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

YAGEO_CC_REEL_QUANTITIES = {
    ("0201", "R"): 15000,
    ("0402", "R"): 10000,
    ("0402", "P"): 50000,
    ("0603", "R"): 4000,
    ("0603", "P"): 15000,
}

MURATA_MLCC_REEL_QUANTITIES = {
    ("0402", "D"): 10000,
    ("0402", "W"): 20000,
    ("0402", "J"): 50000,
    ("0402", "V"): 100000,
    ("0603", "D"): 4000,
    ("0603", "W"): 8000,
    ("0603", "J"): 10000,
    ("0603", "V"): 30000,
    ("0805", "L"): 3000,
    ("0805", "K"): 10000,
}

SAMSUNG_RESISTOR_CS_QUANTITIES = {
    "0402": 20000,
    "0603": 15000,
    "1005": 10000,
    "1608": 5000,
    "2012": 5000,
    "3216": 5000,
    "3225": 5000,
    "5025": 4000,
    "6432": 4000,
}

WALSIN_WR_PACKAGING_QUANTITIES = {
    ("02", "T"): 10000,
    ("02", "A"): 15000,
    ("02", "D"): 20000,
    ("02", "G"): 70000,
    ("02", "H"): 50000,
    ("04", "T"): 10000,
    ("04", "A"): 15000,
    ("04", "D"): 20000,
    ("04", "G"): 70000,
    ("04", "H"): 50000,
    ("06", "T"): 5000,
    ("06", "Q"): 10000,
    ("06", "G"): 20000,
    ("08", "T"): 5000,
    ("08", "Q"): 10000,
    ("08", "G"): 20000,
    ("10", "T"): 5000,
    ("10", "Q"): 10000,
    ("10", "G"): 20000,
    ("12", "T"): 5000,
    ("12", "Q"): 10000,
    ("12", "G"): 20000,
    ("18", "T"): 3000,
    ("20", "T"): 4000,
    ("20", "Q"): 8000,
    ("20", "G"): 16000,
    ("25", "T"): 4000,
    ("25", "Q"): 8000,
    ("25", "G"): 16000,
}

WALSIN_MLCC_7_INCH_QUANTITIES = {
    ("0201", 0.30): (15000, "7英寸纸带卷盘"),
    ("0402", 0.50): (10000, "7英寸纸带卷盘"),
    ("0603", 0.50): (4000, "7英寸纸带卷盘"),
    ("0603", 0.80): (4000, "7英寸纸带卷盘"),
    ("0805", 0.50): (4000, "7英寸纸带卷盘"),
    ("0805", 0.60): (4000, "7英寸纸带卷盘"),
    ("0805", 0.80): (4000, "7英寸纸带卷盘"),
    ("0805", 0.85): (4000, "7英寸纸带卷盘"),
    ("0805", 1.25): (3000, "7英寸压纹带卷盘"),
    ("1206", 0.80): (4000, "7英寸纸带卷盘"),
    ("1206", 0.85): (4000, "7英寸纸带卷盘"),
    ("1206", 0.95): (3000, "7英寸压纹带卷盘"),
    ("1206", 1.15): (3000, "7英寸压纹带卷盘"),
    ("1206", 1.25): (3000, "7英寸压纹带卷盘"),
    ("1206", 1.60): (2000, "7英寸压纹带卷盘"),
    ("1210", 0.85): (3000, "7英寸压纹带卷盘"),
    ("1210", 0.95): (3000, "7英寸压纹带卷盘"),
    ("1210", 1.25): (3000, "7英寸压纹带卷盘"),
    ("1210", 1.60): (2000, "7英寸压纹带卷盘"),
    ("1210", 2.00): (1000, "7英寸压纹带卷盘"),
    ("1210", 2.50): (1000, "7英寸压纹带卷盘"),
    ("1808", 1.25): (2000, "7英寸压纹带卷盘"),
    ("1808", 1.40): (2000, "7英寸压纹带卷盘"),
    ("1808", 1.60): (2000, "7英寸压纹带卷盘"),
    ("1808", 2.00): (1000, "7英寸压纹带卷盘"),
    ("1812", 1.25): (1000, "7英寸压纹带卷盘"),
    ("1812", 1.60): (1000, "7英寸压纹带卷盘"),
    ("1812", 2.00): (1000, "7英寸压纹带卷盘"),
    ("1812", 2.50): (500, "7英寸压纹带卷盘"),
    ("1812", 2.80): (500, "7英寸压纹带卷盘"),
}

WALSIN_SPECIAL_MLCC_SIZE_CODES = {
    "SH": {"15": "0402", "18": "0603", "21": "0805", "31": "1206", "32": "1210", "42": "1808", "43": "1812", "46": "1825", "55": "2220", "56": "2225"},
    "RF": {"02": "01005", "03": "0201", "15": "0402", "18": "0603", "11": "0505", "21": "0805", "22": "1111"},
    "HH": {"03": "0201", "15": "0402", "18": "0603", "21": "0805"},
    "MT": {"03": "0201", "15": "0402", "18": "0603", "21": "0805", "31": "1206", "32": "1210"},
}

WALSIN_SPECIAL_MLCC_7_INCH_QUANTITIES = {
    "SH": {
        ("0402", 0.50): (10000, "7英寸纸带卷盘"),
        ("0603", 0.80): (4000, "7英寸纸带卷盘"),
        ("0805", 0.60): (4000, "7英寸纸带卷盘"),
        ("0805", 0.80): (4000, "7英寸纸带卷盘"),
        ("0805", 1.25): (3000, "7英寸压纹带卷盘"),
        ("1206", 0.80): (4000, "7英寸纸带卷盘"),
        ("1206", 0.95): (3000, "7英寸压纹带卷盘"),
        ("1206", 1.15): (3000, "7英寸压纹带卷盘"),
        ("1206", 1.25): (3000, "7英寸压纹带卷盘"),
        ("1206", 1.60): (2000, "7英寸压纹带卷盘"),
        ("1210", 0.95): (3000, "7英寸压纹带卷盘"),
        ("1210", 1.25): (3000, "7英寸压纹带卷盘"),
        ("1210", 1.60): (2000, "7英寸压纹带卷盘"),
        ("1210", 2.00): (1000, "7英寸压纹带卷盘"),
        ("1210", 2.50): (1000, "7英寸压纹带卷盘"),
        ("1808", 1.25): (2000, "7英寸压纹带卷盘"),
        ("1808", 1.60): (2000, "7英寸压纹带卷盘"),
        ("1808", 2.00): (1000, "7英寸压纹带卷盘"),
        ("1812", 1.25): (1000, "7英寸压纹带卷盘"),
        ("1812", 1.60): (1000, "7英寸压纹带卷盘"),
        ("1812", 2.00): (1000, "7英寸压纹带卷盘"),
        ("1812", 2.50): (500, "7英寸压纹带卷盘"),
        ("1812", 2.80): (500, "7英寸压纹带卷盘"),
        ("1812", 3.10): (500, "7英寸压纹带卷盘"),
        ("1825", 2.00): (1000, "7英寸压纹带卷盘"),
        ("1825", 2.50): (500, "7英寸压纹带卷盘"),
        ("2220", 2.80): (500, "7英寸压纹带卷盘"),
    },
    "RF": {
        ("01005", 0.20): (20000, "7英寸纸带卷盘"),
        ("0201", 0.30): (15000, "7英寸纸带卷盘"),
        ("0402", 0.50): (10000, "7英寸纸带卷盘"),
        ("0603", 0.50): (4000, "7英寸纸带卷盘"),
        ("0603", 0.80): (4000, "7英寸纸带卷盘"),
        ("0805", 0.60): (4000, "7英寸纸带卷盘"),
        ("0805", 0.85): (4000, "7英寸纸带卷盘"),
        ("0505", 1.15): (3000, "7英寸压纹带卷盘"),
        ("1111", 1.78): (2000, "7英寸压纹带卷盘"),
    },
    "HH": {
        ("0201", 0.30): (15000, "7英寸纸带卷盘"),
        ("0402", 0.50): (10000, "7英寸纸带卷盘"),
        ("0603", 0.80): (4000, "7英寸纸带卷盘"),
        ("0805", 0.60): (4000, "7英寸纸带卷盘"),
        ("0805", 0.80): (4000, "7英寸纸带卷盘"),
        ("0805", 1.25): (3000, "7英寸压纹带卷盘"),
    },
    "MT": {
        ("0201", 0.30): (15000, "7英寸纸带卷盘"),
        ("0402", 0.50): (10000, "7英寸纸带卷盘"),
        ("0603", 0.80): (4000, "7英寸纸带卷盘"),
        ("0805", 0.60): (4000, "7英寸纸带卷盘"),
        ("0805", 0.80): (4000, "7英寸纸带卷盘"),
        ("0805", 1.25): (3000, "7英寸压纹带卷盘"),
        ("1206", 0.80): (4000, "7英寸纸带卷盘"),
        ("1206", 0.95): (3000, "7英寸压纹带卷盘"),
        ("1206", 1.15): (3000, "7英寸压纹带卷盘"),
        ("1206", 1.25): (3000, "7英寸压纹带卷盘"),
        ("1206", 1.60): (2000, "7英寸压纹带卷盘"),
        ("1210", 0.95): (3000, "7英寸压纹带卷盘"),
        ("1210", 1.25): (3000, "7英寸压纹带卷盘"),
        ("1210", 1.60): (2000, "7英寸压纹带卷盘"),
        ("1210", 2.00): (1000, "7英寸压纹带卷盘"),
        ("1210", 2.50): (1000, "7英寸压纹带卷盘"),
    },
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


def _leading_number(value: object) -> float | None:
    match = re.match(r"\s*(\d+(?:\.\d+)?)", str(value or ""))
    return float(match.group(1)) if match else None


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

    if ("YAGEO" in brand or "国巨" in brand) and series == "CC":
        match = re.match(r"^CC(?P<size>0201|0402|0603)[A-Z](?P<pack>[RP])", model)
        if match and (not size or size == match.group("size")):
            key = (match.group("size"), match.group("pack"))
            quantity = YAGEO_CC_REEL_QUANTITIES.get(key)
            if quantity:
                reel = "178mm" if key[1] == "R" else "330mm"
                return _packaging_result(
                    quantity,
                    f"{reel}纸带卷盘",
                    f"YAGEO {model} official product packaging",
                    YAGEO_CAPACITOR_PRODUCT_URL.format(model),
                )

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

    if ("MURATA" in brand or "村田" in brand) and series in {"GRM", "GCM", "GCJ"}:
        clean_model = re.sub(r"[^A-Z0-9]", "", model)
        pack_code = clean_model[-1:] if clean_model else ""
        quantity = MURATA_MLCC_REEL_QUANTITIES.get((size, pack_code))
        if quantity:
            methods = {
                "D": "180mm纸带卷盘",
                "W": "180mm窄间距纸带卷盘",
                "J": "330mm纸带卷盘",
                "V": "330mm窄间距纸带卷盘",
                "L": "180mm压纹带卷盘",
                "K": "330mm压纹带卷盘",
            }
            return _packaging_result(
                quantity,
                methods[pack_code],
                f"Murata {series}/{size}/{pack_code} official product packaging",
                MURATA_PRODUCT_URL.format(clean_model),
            )

    if ("SAMSUNG" in brand or "三星" in brand) and series == "CL":
        clean_model = re.sub(r"[^A-Z0-9]", "", model)
        size_codes = {
            "01005": "CL02",
            "0201": "CL03",
            "0402": "CL05",
            "0603": "CL10",
            "0805": "CL21",
            "1206": "CL31",
            "1210": "CL32",
            "1808": "CL42",
        }
        height = _leading_number(_text(record, "高度（mm）", "厚度(mm)", "厚度（mm）"))
        quantity = None
        method = ""
        if clean_model.startswith(size_codes.get(size, "_")) and clean_model.endswith("C") and height is not None:
            if (size, height) in {("01005", 0.2), ("0201", 0.3), ("0402", 0.5)}:
                quantity = {"01005": 20000, "0201": 10000, "0402": 10000}[size]
                method = "7英寸纸带卷盘"
            elif size == "0603" and height <= 0.8:
                quantity, method = 4000, "7英寸纸带卷盘"
            elif size == "0603" and height >= 1.0:
                quantity, method = 3000, "7英寸压纹带卷盘"
            elif size in {"0805", "1206"} and height <= 0.85:
                quantity, method = 4000, "7英寸纸带卷盘"
            elif size in {"0805", "1206"} and height >= 1.0:
                quantity, method = 2000, "7英寸压纹带卷盘"
            elif size in {"1210", "1808"} and height <= 1.6:
                quantity, method = 2000, "7英寸压纹带卷盘"
            elif size in {"1210", "1808"} and height >= 2.0:
                quantity, method = 1000, "7英寸压纹带卷盘"
        if quantity:
            return _packaging_result(
                quantity,
                method,
                f"Samsung CL/{size}/{height:g}mm/7-inch official packaging table",
                SAMSUNG_MLCC_PRODUCT_URL.format(clean_model),
            )

    if ("SAMSUNG" in brand or "三星" in brand) and series in {"RC", "RCS", "RU", "RJ"}:
        clean_model = re.sub(r"[^A-Z0-9]", "", model)
        match = re.fullmatch(r"(?P<family>RCS|RUK|RUT|RC|RU|RJ)(?P<metric>0402|0603|1005|1608|2012|3216|3225|5025|6432|1220|1632)[A-Z0-9R]+CS", clean_model)
        matched_series = "RU" if match and match.group("family") in {"RU", "RUK", "RUT"} else (match.group("family") if match else "")
        if match and matched_series == series:
            metric = match.group("metric")
            if series == "RJ":
                quantity = 4000 if metric == "1220" and clean_model.endswith("R002CS") else 5000
            else:
                quantity = SAMSUNG_RESISTOR_CS_QUANTITIES.get(metric)
            carrier = "压纹塑料带" if metric in {"5025", "6432"} or quantity == 4000 else "纸带"
            if not quantity:
                return {}
            return _packaging_result(
                quantity,
                f"7英寸{carrier}卷盘",
                f"Samsung {series}/{metric}/CS official packaging table",
                SAMSUNG_RESISTOR_SOURCE,
            )

    if ("WALSIN" in brand or "华新科" in brand) and series == "WR":
        clean_model = re.sub(r"[^A-Z0-9]", "", model)
        match = re.fullmatch(r"WR(?P<size_code>02|04|06|08|10|12|18|20|25)[A-Z0-9R]+(?P<pack>[TQGADH])L", clean_model)
        if match:
            key = (match.group("size_code"), match.group("pack"))
            quantity = WALSIN_WR_PACKAGING_QUANTITIES.get(key)
            if quantity:
                pack = match.group("pack")
                reel = "254mm" if key == ("18", "T") or pack == "Q" else ("330mm" if pack in {"G", "H"} else "178mm")
                return _packaging_result(
                    quantity,
                    f"{reel}载带卷盘",
                    f"Walsin WR/{key[0]}/{pack} official packaging table",
                    WALSIN_WR_SOURCE,
                )

    if ("WALSIN" in brand or "华新科" in brand) and series in {
        "常规",
        "0201N",
        "0402N",
        "0603N",
        "0805N",
        "1206N",
        "1808N",
    }:
        clean_model = re.sub(r"[^A-Z0-9]", "", model)
        match = re.fullmatch(r"(?P<size>0201|0402|0603|0805|1206|1210|1808|1812)[A-Z0-9R]+CT", clean_model)
        height = _leading_number(_text(record, "高度（mm）", "厚度(mm)", "厚度（mm）"))
        if match and height is not None and (not size or size == match.group("size")):
            rule = WALSIN_MLCC_7_INCH_QUANTITIES.get((match.group("size"), round(height, 2)))
            if rule:
                quantity, method = rule
                return _packaging_result(
                    quantity,
                    method,
                    f"Walsin general MLCC/{size}/{height:g}mm/T official packaging table",
                    WALSIN_MLCC_GENERAL_SOURCE,
                )

    if ("WALSIN" in brand or "华新科" in brand) and series in WALSIN_SPECIAL_MLCC_SIZE_CODES:
        clean_model = re.sub(r"[^A-Z0-9]", "", model)
        match = re.fullmatch(r"(?P<family>SH|RF|HH|MT)(?P<size_code>\d{2})[A-Z0-9R]+CT", clean_model)
        height = _leading_number(_text(record, "高度（mm）", "厚度(mm)", "厚度（mm）"))
        if match and match.group("family") == series and height is not None:
            expected_size = WALSIN_SPECIAL_MLCC_SIZE_CODES[series].get(match.group("size_code"))
            rule = WALSIN_SPECIAL_MLCC_7_INCH_QUANTITIES[series].get((expected_size, round(height, 2)))
            if expected_size and (not size or size == expected_size) and rule:
                quantity, method = rule
                return _packaging_result(
                    quantity,
                    method,
                    f"Walsin {series}/{expected_size}/{height:g}mm/T official packaging table",
                    WALSIN_SPECIAL_MLCC_SOURCES[series],
                )

    if "TDK" in brand or "东电化" in brand:
        clean_model = re.sub(r"[^A-Z0-9]", "", model)
        tdk_mlcc_rules = (
            ("C", "0201", r"C0603[A-Z0-9]+030B[A-Z]", 15000, "C0603/030/B"),
            ("C", "0402", r"C1005[A-Z0-9]+050B[A-Z]", 10000, "C1005/050/B"),
            ("C", "0603", r"C1608[A-Z0-9]+080A[A-Z]", 4000, "C1608/080/A"),
            ("C", "0805", r"C2012[A-Z0-9]+060A[A-Z]", 4000, "C2012/060/A"),
            ("C", "0805", r"C2012[A-Z0-9]+125A[A-Z]", 2000, "C2012/125/A"),
        )
        for rule_series, rule_size, pattern, quantity, source_key in tdk_mlcc_rules:
            if series == rule_series and size == rule_size and re.fullmatch(pattern, clean_model):
                return _packaging_result(
                    quantity,
                    "180mm冲孔纸带卷盘",
                    f"TDK {source_key} official product packaging",
                    TDK_MLCC_PRODUCT_URL.format(clean_model),
                )

        tdk_ntc_rules = {
            "NTCG06": ("0201", 15000),
            "NTCG10": ("0402", 10000),
            "NTCG16": ("0603", 4000),
        }
        for prefix, (rule_size, quantity) in tdk_ntc_rules.items():
            if series == "NTCG" and clean_model.startswith(prefix) and size == rule_size:
                return _packaging_result(
                    quantity,
                    "180mm冲孔纸带卷盘",
                    f"TDK {prefix} official product packaging",
                    TDK_NTC_PRODUCT_URL.format(clean_model),
                )

    return {}
