from __future__ import annotations

import re
from typing import Callable


UNIROYAL_BRAND_TOKENS = ("UNI-ROYAL", "UNIROYAL", "厚声", "UNIOHM")
TAI_BRAND_TOKENS = ("TA-I", "大毅")
VIKING_BRAND_TOKENS = ("VIKING", "光颉")
YAGEO_BRAND_TOKENS = ("YAGEO", "国巨")


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
    "AT": {"系列说明": "车规薄膜晶片电阻器", "器件类型": "薄膜电阻", "特殊用途": "车规 | 高精密"},
    "RC": {"系列说明": "通用厚膜晶片电阻器", "器件类型": "厚膜电阻", "特殊用途": ""},
    "RT": {"系列说明": "高精度高稳定薄膜晶片电阻器", "器件类型": "薄膜电阻", "特殊用途": "高精密"},
}

OFFICIAL_RESISTOR_BRAND_RULES = {
    "UNIROYAL": {"brand_tokens": UNIROYAL_BRAND_TOKENS, "profiles": UNIROYAL_OFFICIAL_SERIES_PROFILES},
    "TAI": {"brand_tokens": TAI_BRAND_TOKENS, "profiles": TAI_OFFICIAL_SERIES_PROFILES},
    "VIKING": {"brand_tokens": VIKING_BRAND_TOKENS, "profiles": VIKING_OFFICIAL_SERIES_PROFILES},
    "YAGEO": {"brand_tokens": YAGEO_BRAND_TOKENS, "profiles": YAGEO_OFFICIAL_SERIES_PROFILES},
}


def clean_text(value: object) -> str:
    if value is None:
        return ""
    text = str(value).strip()
    if text.lower() in {"none", "nan"}:
        return ""
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
    if len(text) > 2 and text.endswith("T"):
        return text[:-1]
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


BRAND_MODEL_PREFIX_RESOLVERS: dict[str, Callable[[str], str]] = {
    "UNIROYAL": _resolve_uniroyal_series_code_from_model,
    "TAI": lambda compact: _resolve_generic_series_code_from_model(compact, "TAI"),
    "VIKING": lambda compact: _resolve_generic_series_code_from_model(compact, "VIKING"),
    "YAGEO": lambda compact: _resolve_generic_series_code_from_model(compact, "YAGEO"),
}


def resolve_official_resistor_series_code_from_model(model: object, brand: object = "") -> str:
    family = identify_resistor_brand_family(brand)
    if family == "":
        return ""
    compact = normalize_model_text(model)
    if compact == "":
        return ""
    resolver = BRAND_MODEL_PREFIX_RESOLVERS.get(family)
    if resolver is None:
        return ""
    return clean_text(resolver(compact))


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
    if brand_text:
        parts.append(brand_text)
    if series_text:
        parts.append(series_text)
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
