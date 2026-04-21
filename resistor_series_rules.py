from __future__ import annotations

import re


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
    if len(text) > 1 and text.endswith("T"):
        return text[:-1]
    return text


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
    series = infer_resistor_series_code(model, brand=brand)
    return {
        "系列": series,
        "系列说明": build_resistor_series_description(
            brand=brand,
            series=series,
            component_type=component_type,
            special_use=special_use,
        ),
    }
