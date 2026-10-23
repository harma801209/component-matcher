"""Evidence-backed safety MLCC metadata; certification is not construction.

PDC FKFH-000-001-25, 2025-09-23, sections 2, 4, 6 and 7:
https://www.pdc.com.tw/storage/architecture/product~~19/product~~106/product~~141/FKFH_Series.pdf
Only the three reviewed, already-catalogued FK08X order numbers are enriched.
This module never generates order numbers or changes prices/runtime databases.
"""
import re


PDC_REVIEWED_SAFETY_MODELS = (
    "FK08X121K502EEQ", "FK08X151K502EEQ", "FK08X221K502EEQ",
)
PDC_SAFETY_SOURCE = "PDC FKFH-000-001-25 (2025-09-23), sections 2/4/6/7"


def _text(value):
    text = "" if value is None else str(value).strip()
    return "" if text.lower() in {"nan", "none", "<na>"} else text


def safety_class_tokens(text):
    return tuple(dict.fromkeys(re.findall(
        r"(?<![A-Z0-9])(X1|X2|Y1|Y2)(?![A-Z0-9])", _text(text).upper()
    )))


def documented_pdc_safety_fields(brand, model):
    brand = _text(brand).upper()
    model = re.sub(r"\s+", "", _text(model).upper())
    if ("PDC" not in brand and "信昌" not in brand) or model not in PDC_REVIEWED_SAFETY_MODELS:
        return {}
    return {
        "器件类型": "MLCC", "安规": "X1/Y2", "_safety_class": "X1/Y2",
        "耐压（V）": "250", "_volt": "250", "_volt_num": 250.0,
        "工作温度": "-55~125℃", "_temp_low": -55.0, "_temp_high": 125.0,
        "安装方式": "贴片", "_mount_style": "贴片", "_mlcc_series_class": "安规",
        "特殊用途": "安规/无卤", "_special_use_norm": "安规/无卤",
    }


def enrich_documented_safety_mlcc_record(record):
    fields = documented_pdc_safety_fields(record.get("品牌"), record.get("型号"))
    if not fields:
        return record
    out = dict(record)
    # Preserve other documented attributes; never interpret 502 as working V.
    special = _text(out.get("特殊用途"))
    fields["特殊用途"] = "/".join(dict.fromkeys(
        [part for part in special.split("/") if part] + ["安规", "无卤"]
    ))
    fields["_special_use_norm"] = fields["特殊用途"]
    out.update(fields)
    source = _text(out.get("数据来源"))
    if PDC_SAFETY_SOURCE not in source:
        out["数据来源"] = "; ".join(part for part in (source, PDC_SAFETY_SOURCE) if part)
    return out


def enrich_documented_safety_mlcc_frame(frame):
    if frame is None or frame.empty or not {"品牌", "型号"}.issubset(frame.columns):
        return frame
    positions = frame["型号"].isin(PDC_REVIEWED_SAFETY_MODELS).to_numpy().nonzero()[0]
    changes = {}
    for position in positions:
        row = frame.iloc[position].to_dict()
        enriched = enrich_documented_safety_mlcc_record(row)
        if enriched is not row:
            changes[position] = enriched
    if not changes:
        return frame
    out = frame.copy()
    for position, enriched in changes.items():
        for key, value in enriched.items():
            if key not in out:
                out[key] = None
            if key in out and str(out[key].dtype) == "category":
                out[key] = out[key].astype(object)
            out.iat[position, out.columns.get_loc(key)] = value
    return out


def required_mlcc_safety_classes(spec):
    return set(safety_class_tokens(" ".join(_text(spec.get(key)) for key in (
        "_safety_class", "安规", "特殊用途", "型号",
    ))))


def _temperature_bounds(text):
    match = re.search(r"(?:(-?\d+(?:\.\d+)?)\s*[~～至]\s*)?(-?\d+(?:\.\d+)?)\s*(?:℃|°\s*C)", _text(text), re.I)
    if not match:
        return None, None
    return (float(match.group(1)) if match.group(1) else None, float(match.group(2)))


def safety_mlcc_candidate_satisfies(row, spec):
    required = required_mlcc_safety_classes(spec)
    if not required:
        return True
    actual = set(safety_class_tokens(" ".join(_text(row.get(key)) for key in (
        "安规", "_safety_class", "特殊用途", "_special_use_norm",
    ))))
    if not required.issubset(actual):
        return False
    # Unknown is not evidence of compliance. Do not silently drop a BOM limit.
    requested_text = " ".join(_text(spec.get(key)) for key in ("型号", "工作温度", "特殊用途"))
    low, high = _temperature_bounds(requested_text)
    actual_low, actual_high = _temperature_bounds(row.get("工作温度"))
    if high is not None and (actual_high is None or actual_high < high):
        return False
    if low is not None and (actual_low is None or actual_low > low):
        return False
    if "无卤" in requested_text and "无卤" not in _text(row.get("特殊用途")):
        return False
    return True
