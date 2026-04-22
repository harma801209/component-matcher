from __future__ import annotations

import re
from typing import Callable


UNIROYAL_BRAND_TOKENS = ("UNI-ROYAL", "UNIROYAL", "厚声", "UNIOHM")
TAI_BRAND_TOKENS = ("TA-I", "大毅")
VIKING_BRAND_TOKENS = ("VIKING", "光颉")
YAGEO_BRAND_TOKENS = ("YAGEO", "国巨")
RALEC_BRAND_TOKENS = ("RALEC", "旺诠")


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

RALEC_OFFICIAL_SERIES_PROFILES = {
    "RAT": {"系列说明": "Automotive grade thick film chip resistor", "器件类型": "厚膜电阻", "特殊用途": "车规"},
    "RHW": {"系列说明": "Wide terminal high power thick film chip resistor", "器件类型": "厚膜电阻", "特殊用途": "wide terminal | high power"},
    "RTH": {"系列说明": "High power thick film chip resistor", "器件类型": "厚膜电阻", "特殊用途": "high power"},
    "RTG": {"系列说明": "Anti-surge thick film chip resistor", "器件类型": "厚膜电阻", "特殊用途": "anti-surge"},
    "RTR": {"系列说明": "High precision thick film chip resistor", "器件类型": "厚膜电阻", "特殊用途": "high precision"},
    "RTV": {"系列说明": "High voltage thick film chip resistor", "器件类型": "厚膜电阻", "特殊用途": "high voltage"},
    "RTT": {"系列说明": "General-purpose thick film chip resistor", "器件类型": "厚膜电阻", "特殊用途": ""},
    "RTW": {"系列说明": "Wide terminal thick film chip resistor", "器件类型": "厚膜电阻", "特殊用途": "wide terminal"},
}

OFFICIAL_RESISTOR_BRAND_RULES = {
    "UNIROYAL": {"brand_tokens": UNIROYAL_BRAND_TOKENS, "profiles": UNIROYAL_OFFICIAL_SERIES_PROFILES},
    "TAI": {"brand_tokens": TAI_BRAND_TOKENS, "profiles": TAI_OFFICIAL_SERIES_PROFILES},
    "VIKING": {"brand_tokens": VIKING_BRAND_TOKENS, "profiles": VIKING_OFFICIAL_SERIES_PROFILES},
    "YAGEO": {"brand_tokens": YAGEO_BRAND_TOKENS, "profiles": YAGEO_OFFICIAL_SERIES_PROFILES},
    "RALEC": {"brand_tokens": RALEC_BRAND_TOKENS, "profiles": RALEC_OFFICIAL_SERIES_PROFILES},
}

OFFICIAL_RESISTOR_SERIES_CODES = {
    code
    for rule in OFFICIAL_RESISTOR_BRAND_RULES.values()
    for code in rule.get("profiles", {}).keys()
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
    if text in OFFICIAL_RESISTOR_SERIES_CODES:
        return text
    if len(text) > 2 and text.endswith("T"):
        stripped = text[:-1]
        if stripped not in OFFICIAL_RESISTOR_SERIES_CODES:
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
        "D/CRCW": ("标准厚膜片式电阻器", "厚膜电阻", ""),
        "D/CRCW-HR": ("高值厚膜片式电阻器", "厚膜电阻", ""),
        "D/CRCW-IF": ("脉冲防护厚膜片式电阻器", "厚膜电阻", ""),
        "D/CRCW-P": ("半精密厚膜片式电阻器", "厚膜电阻", ""),
        "MCA": ("专业薄膜片式电阻器", "薄膜电阻", "车规"),
        "MBB": ("精密薄膜电阻器", "薄膜电阻", ""),
        "MBA": ("精密薄膜电阻器", "薄膜电阻", ""),
        "MCT": ("精密薄膜电阻器", "薄膜电阻", ""),
        "M55342": ("军规高可靠薄膜电阻器", "薄膜电阻", "军规"),
        "D55342": ("军规高可靠薄膜电阻器", "薄膜电阻", "军规"),
        "PAT": ("高精度薄膜芯片电阻器", "薄膜电阻", ""),
        "PNM": ("非磁性薄膜芯片电阻器", "薄膜电阻", "非磁性"),
        "P2TC": ("高精度薄膜芯片电阻器", "薄膜电阻", "高精度"),
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
        "RWR82S": ("军规线绕电阻器", "绕线电阻", "军规"),
        "RWR84S": ("军规线绕电阻器", "绕线电阻", "军规"),
        "RWR89N": ("军规线绕电阻器", "绕线电阻", "军规"),
        "RWR89S": ("军规线绕电阻器", "绕线电阻", "军规"),
        "RWR71N": ("军规线绕电阻器", "绕线电阻", "军规"),
        "RWR71S": ("军规线绕电阻器", "绕线电阻", "军规"),
        "TNPW": ("高稳定薄膜片式电阻器", "薄膜电阻", "高稳定"),
    }
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
        "RGC": ("金阻挡厚膜芯片电阻器", "厚膜电阻", ""),
        "RMCF": ("通用厚膜芯片电阻器", "厚膜电阻", ""),
        "RMCG": ("金阻挡厚膜芯片电阻器", "厚膜电阻", ""),
        "RMCP": ("通用高功率厚膜芯片电阻器", "厚膜电阻", "高功率"),
        "RMCS": ("抗硫厚膜芯片电阻器", "厚膜电阻", "抗硫"),
        "RMCW": ("宽端子厚膜芯片电阻器", "厚膜电阻", "宽端子"),
        "RMEA": ("车规抗硫厚膜芯片电阻器", "厚膜电阻", "车规/抗硫"),
        "RMEF": ("通用厚膜芯片电阻器", "厚膜电阻", ""),
        "RNAN": ("薄膜高功率铝氮化物基芯片电阻器", "薄膜电阻", "高功率"),
        "RNCA": ("车规抗硫薄膜芯片电阻器", "薄膜电阻", "车规/抗硫"),
        "RNCF": ("精密薄膜芯片电阻器", "薄膜电阻", "高精度"),
        "RNCP": ("抗硫高功率薄膜芯片电阻器", "薄膜电阻", "抗硫/高功率"),
        "RNCS": ("防潮精密薄膜芯片电阻器", "薄膜电阻", "防潮"),
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
    }
)
