from __future__ import annotations

from datetime import datetime
import json
import html
import math
import re
import time
from pathlib import Path

import pandas as pd
import requests


ROOT = Path(__file__).resolve().parent
OFFICIAL_CSV = ROOT / "Inductor" / "official_inductor_expansion.csv"
SNAPSHOT_CSV = ROOT / "Inductor" / "taiyo_yuden_inductor_expansion.csv"
SEARCH_URL = "https://ds.yuden.co.jp/TYCOMPAS/ut/search"
DETAIL_URL = "https://ds.yuden.co.jp/TYCOMPAS/ut/detail"
SPEC_SHEET_URL = "https://ds.yuden.co.jp/TYCOMPAS/ut/specSheet?pn={part_no}"
TODAY = datetime.now().strftime("%Y-%m-%d")

BRAND = "太阳诱电Taiyo Yuden"
PAGE_SIZE = 50
KEY_COLUMNS = ["品牌", "型号", "器件类型"]

APP_NAME_MAP = {
    "AP0": "General Equipment",
    "AP1": "Auto. (Powertrain/Safety)",
    "AP2": "Auto. (Body/Info) & High Reliability",
    "AP3": "Telecom-Infrastructure & Industrial",
    "AP4": "Medical (International Class. I ・ II)",
    "AP5": "Medical (International Class. Ⅲ）",
    "AP6": "Mobile Devices",
}

QUERY_SPECS = [
    {
        "key": "WDLD",
        "params": {"SR3-L": "WDLD"},
        "component_type": "功率电感",
        "mounting": "THT",
        "material": "FERRITE",
        "special_use": "Axial Leaded Inductor",
        "series_desc": "Taiyo Yuden axial leaded standard inductors",
        "authority": "taiyo_yuden_tycompas_wdld",
        "need_detail": True,
    },
    {
        "key": "LPOWM",
        "params": {"SR0-L": "LPOWM"},
        "component_type": "功率电感",
        "mounting": "SMT",
        "material": "METAL",
        "special_use": "Power Inductor",
        "series_desc": "Taiyo Yuden wire-wound metal power inductors",
        "authority": "taiyo_yuden_tycompas_lpowm",
        "need_detail": False,
    },
    {
        "key": "LPOWF",
        "params": {"SR0-L": "LPOWF"},
        "component_type": "功率电感",
        "mounting": "SMT",
        "material": "FERRITE",
        "special_use": "Power Inductor",
        "series_desc": "Taiyo Yuden wire-wound ferrite power inductors",
        "authority": "taiyo_yuden_tycompas_lpowf",
        "need_detail": False,
    },
    {
        "key": "LHF",
        "params": {"SR0-L": "LHF"},
        "component_type": "射频电感",
        "mounting": "SMT",
        "material": "CERAMIC",
        "special_use": "High-Frequency Inductor",
        "series_desc": "Taiyo Yuden multilayer chip inductors for high-frequency applications",
        "authority": "taiyo_yuden_tycompas_lhf",
        "need_detail": False,
    },
    {
        "key": "LSTD",
        "params": {"SR0-L": "LSTD"},
        "component_type": "功率电感",
        "mounting": "SMT",
        "material": "FERRITE",
        "special_use": "Standard Inductor",
        "series_desc": "Taiyo Yuden standard inductors",
        "authority": "taiyo_yuden_tycompas_lstd",
        "need_detail": False,
    },
    {
        "key": "LDAMP",
        "params": {"SR0-L": "LDAMP"},
        "component_type": "功率电感",
        "mounting": "SMT",
        "material": "FERRITE",
        "special_use": "Class D Amplifier Inductor",
        "series_desc": "Taiyo Yuden class D amplifier inductors",
        "authority": "taiyo_yuden_tycompas_ldamp",
        "need_detail": False,
    },
]

DETAIL_PAIR_RE = re.compile(r'<td class="ItemName">(.*?)</td>\s*<td class="ItemValue">(.*?)</td>', re.S)
DETAIL_SERIES_RE = re.compile(
    r'<div id="ClassificationSeriesArea">.*?<span class="ClassificationSeries">\s*\[(.*?)\]</span>',
    re.S,
)


def clean_text(value: object) -> str:
    if value is None:
        return ""
    try:
        if value != value:
            return ""
    except Exception:
        pass
    text = str(value).strip()
    return "" if text.lower() == "nan" else text


def textify(value: object) -> str:
    text = html.unescape(clean_text(value))
    text = re.sub(r"(?i)<br\s*/?>", " ", text)
    text = re.sub(r"<[^>]+>", " ", text)
    text = text.replace("\xa0", " ")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def first_nonempty(*values: object) -> str:
    for value in values:
        text = clean_text(value)
        if text:
            return text
    return ""


def normalize_number_text(value: object) -> str:
    text = clean_text(value).replace(",", "")
    if not text:
        return ""
    match = re.search(r"[0-9]+(?:\.[0-9]+)?", text)
    return match.group(0) if match else text


def normalize_mm_number(value: object) -> str:
    text = normalize_number_text(value)
    if not text:
        return ""
    try:
        number = float(text)
    except Exception:
        return text
    if math.isfinite(number):
        formatted = f"{number:.4f}".rstrip("0").rstrip(".")
        return formatted if formatted else "0"
    return text


def extract_value_pair(text: object) -> tuple[str, str]:
    cleaned = clean_text(text).replace(",", "").replace("µ", "u").replace("μ", "u")
    if not cleaned:
        return "", ""
    match = re.match(r"^([0-9]+(?:\.[0-9]+)?)(?:\s*([a-zA-Z]+))?$", cleaned)
    if not match:
        return cleaned, ""
    value = match.group(1)
    unit = (match.group(2) or "").upper()
    if unit == "UH":
        unit = "UH"
    elif unit == "NH":
        unit = "NH"
    elif unit == "MH":
        unit = "MH"
    return value, unit


def parse_inductance(text: object) -> tuple[str, str]:
    cleaned = clean_text(text).replace(",", "").replace("µ", "u").replace("μ", "u")
    if not cleaned:
        return "", ""
    match = re.match(r"^([0-9]+(?:\.[0-9]+)?)\s*([numk]?H)$", cleaned, flags=re.I)
    if match:
        value = match.group(1)
        unit = match.group(2).upper()
        unit = {"UH": "UH", "NH": "NH", "MH": "MH"}.get(unit, unit)
        return value, unit
    return extract_value_pair(cleaned)


def normalize_tolerance(text: object) -> str:
    cleaned = clean_text(text)
    if not cleaned:
        return ""
    cleaned = cleaned.replace(" ", "")
    cleaned = cleaned.replace("％", "%")
    return cleaned


def format_amp(value: object) -> str:
    text = clean_text(value)
    if not text:
        return ""
    number = normalize_number_text(text)
    if not number:
        return text
    return f"{number}A"


def to_milliohm_text(value: object) -> str:
    text = clean_text(value)
    if not text:
        return ""
    if any(token in text.lower() for token in ("mω", "mohm", "mohms")):
        return normalize_number_text(text)
    if "mΩ" in text or "mohm" in text.lower():
        return normalize_number_text(text)
    number = normalize_number_text(text)
    if not number:
        return ""
    try:
        return normalize_mm_number(float(number) * 1000)
    except Exception:
        return number


def format_dcr(typ: object, max_value: object) -> str:
    typ_text = to_milliohm_text(typ)
    max_text = to_milliohm_text(max_value)
    if typ_text and max_text and typ_text != max_text:
        return f"{typ_text}mΩ typ / {max_text}mΩ max"
    if max_text:
        return f"{max_text}mΩ max"
    if typ_text:
        return f"{typ_text}mΩ typ"
    return ""


def parse_case_inch(case_size: object) -> str:
    text = clean_text(case_size)
    if not text:
        return ""
    match = re.search(r"\b(\d{4})\b", text)
    return match.group(1) if match else ""


def split_mm_pair(text: object) -> tuple[str, str]:
    cleaned = clean_text(text).replace("×", "x").replace("X", "x")
    if not cleaned:
        return "", ""
    parts = [part.strip() for part in cleaned.split("x") if part.strip()]
    if len(parts) < 2:
        return "", ""
    return normalize_mm_number(parts[0]), normalize_mm_number(parts[1])


def build_smt_size_mm(record: dict[str, object]) -> str:
    length = normalize_mm_number(record.get("SizeL_Spec_M"))
    width = normalize_mm_number(record.get("SizeW_Spec_M"))
    height = normalize_mm_number(record.get("SizeTH_Spec_M"))
    if not length or not width:
        pair = split_mm_pair(record.get("Size_List_M"))
        if pair[0]:
            length = length or pair[0]
        if pair[1]:
            width = width or pair[1]
    if not height:
        height = normalize_mm_number(record.get("Thick_Srch_M"))
    parts = [part for part in (length, width, height) if part]
    return " x ".join(parts) + " mm" if parts else ""


def parse_detail_size_mm(detail_specs: dict[str, str]) -> tuple[str, str, str, str]:
    case_size = first_nonempty(detail_specs.get("Case Size (mm)"), detail_specs.get("Case Size (EIA/JIS)"))
    diameter, length = split_mm_pair(case_size)
    if not diameter and not length:
        length = normalize_mm_number(detail_specs.get("Dimension L"))
        diameter = normalize_mm_number(detail_specs.get("Dimension D"))
    return diameter, length, "", ""


def build_leaded_size_mm(detail_specs: dict[str, str]) -> tuple[str, str, str, str, str]:
    diameter, length, width, height = parse_detail_size_mm(detail_specs)
    parts = [part for part in (diameter, length) if part]
    size_mm = " x ".join(parts) + " mm" if parts else ""
    return size_mm, diameter, length, width, height


def derive_series(part_number: str, pre_pn: str) -> str:
    if pre_pn:
        return pre_pn
    if "-" in part_number:
        return part_number.split("-", 1)[0]
    match = re.match(r"^(.*?)(?:[0-9]+(?:R[0-9]+)?[A-Z]?)$", part_number)
    if match and match.group(1):
        return match.group(1)
    return part_number


def normalize_status(sr2: object) -> str:
    status = clean_text(sr2).upper()
    if status in {"MP", "LM", "CPN"}:
        return "Active"
    if status == "NPRF":
        return "NRND"
    if status == "POUT":
        return "Phaseout"
    if status == "OBSL":
        return "Discontinued"
    if status == "UDEV":
        return "Under Development"
    return clean_text(sr2)


def sr6_names(values: object) -> str:
    if not values:
        return ""
    raw_values = values if isinstance(values, (list, tuple)) else [values]
    names: list[str] = []
    for item in raw_values:
        text = clean_text(item)
        if "@" in text:
            text = text.split("@", 1)[1]
        text = text.replace("SR6-L_", "")
        text = text.replace("SR6-", "")
        name = APP_NAME_MAP.get(text, text)
        if name and name not in names:
            names.append(name)
    return " | ".join(names)


def fetch_text(session: requests.Session, url: str, params: dict[str, str], timeout: int = 60) -> str:
    last_error: Exception | None = None
    for attempt in range(1, 6):
        try:
            response = session.get(url, params=params, timeout=timeout)
            response.raise_for_status()
            return response.text
        except Exception as exc:
            last_error = exc
            time.sleep(min(6, attempt * 2))
    raise RuntimeError(f"failed to fetch {url}: {last_error}")


def fetch_json(session: requests.Session, params: dict[str, str]) -> dict:
    text = fetch_text(session, SEARCH_URL, params, timeout=60)
    return json.loads(text)


def extract_detail_fields(session: requests.Session, part_no: str) -> tuple[dict[str, str], str]:
    html_text = fetch_text(session, DETAIL_URL, {"pn": part_no, "u": "M"}, timeout=60)
    detail_specs: dict[str, str] = {}
    for raw_name, raw_value in DETAIL_PAIR_RE.findall(html_text):
        name = textify(raw_name)
        value = textify(raw_value)
        if name and value and name not in detail_specs:
            detail_specs[name] = value
    series_desc = ""
    series_match = DETAIL_SERIES_RE.search(html_text)
    if series_match:
        series_desc = textify(series_match.group(1))
    return detail_specs, series_desc


def format_model_summary(
    inductance_value: str,
    inductance_unit: str,
    tolerance: str,
    size_code: str,
    size_mm: str,
    current: str,
    sat_current: str,
    dcr: str,
) -> str:
    parts = []
    if inductance_value and inductance_unit:
        parts.append(f"L={inductance_value}{inductance_unit}")
    elif inductance_value:
        parts.append(f"L={inductance_value}")
    if tolerance:
        parts.append(f"Tol={tolerance}")
    if size_code:
        parts.append(f"Case={size_code}")
    if size_mm:
        parts.append(size_mm)
    if current:
        parts.append(f"Irms={current}")
    if sat_current:
        parts.append(f"Isat={sat_current}")
    if dcr:
        parts.append(f"DCR={dcr}")
    return " | ".join(parts)


def build_row(
    record: dict[str, object],
    spec: dict[str, object],
    *,
    detail_specs: dict[str, str] | None = None,
    detail_series_desc: str = "",
) -> dict[str, str]:
    row: dict[str, str] = {}
    part_no = clean_text(record.get("PartNumber"))
    pre_pn = clean_text(record.get("Pre_PN"))
    series = derive_series(part_no, pre_pn)
    sr2 = clean_text(record.get("SR2"))

    inductance_value, inductance_unit = parse_inductance(record.get("Ind_List"))
    inductance_tol = normalize_tolerance(record.get("Ind_Tole"))
    current = first_nonempty(format_amp(record.get("Current_Srch")), format_amp(detail_specs.get("Rated Current (max)") if detail_specs else ""))
    sat_current = first_nonempty(format_amp(record.get("Sat_Current")), format_amp(detail_specs.get("Saturation Current (max)") if detail_specs else ""))
    temp_current = first_nonempty(format_amp(record.get("Temp_Current")), format_amp(detail_specs.get("Temperature Rise Current (max)") if detail_specs else ""))
    temp_current_typ = first_nonempty(format_amp(record.get("Temp_Current_typ")), format_amp(detail_specs.get("Temperature Rise Current (typ)") if detail_specs else ""))
    sat_current_typ = first_nonempty(format_amp(record.get("Sat_Current_typ")), format_amp(detail_specs.get("Saturation Current (typ)") if detail_specs else ""))
    dcr = first_nonempty(
        format_dcr(record.get("DCR_typ"), record.get("DCR_max")),
        format_dcr(detail_specs.get("DC Resistance (typ)") if detail_specs else "", detail_specs.get("DC Resistance (max)") if detail_specs else ""),
    )
    work_temp = first_nonempty(clean_text(record.get("Temp_Range")), detail_specs.get("Operating Temp. Range") if detail_specs else "")
    packaging = first_nonempty(clean_text(record.get("Packaging")), detail_specs.get("Standard Quantity") if detail_specs else "")
    sr6_text = sr6_names(record.get("SR6"))
    status = normalize_status(sr2)

    if spec["mounting"] == "THT":
        size_mm, diameter, length, width, height = build_leaded_size_mm(detail_specs or {})
        size_code = ""
        note1_parts = [
            f"RatedCurrent={current}" if current else "",
            f"SatCurrent={sat_current}" if sat_current else "",
            f"TempRise={temp_current or temp_current_typ}" if (temp_current or temp_current_typ) else "",
            f"Packaging={packaging}" if packaging else "",
        ]
        row["直径（mm）"] = diameter
        row["长度（mm）"] = length
        row["宽度（mm）"] = width
        row["高度（mm）"] = height
    else:
        size_code = parse_case_inch(record.get("Case_Size"))
        size_mm = build_smt_size_mm(record)
        note1_parts = [
            f"RatedCurrent={current}" if current else "",
            f"SatCurrent={sat_current or sat_current_typ}" if (sat_current or sat_current_typ) else "",
            f"TempRise={temp_current or temp_current_typ}" if (temp_current or temp_current_typ) else "",
            f"Packaging={packaging}" if packaging else "",
        ]
        row["长度（mm）"] = normalize_mm_number(record.get("SizeL_Spec_M")) or split_mm_pair(record.get("Size_List_M"))[0]
        row["宽度（mm）"] = normalize_mm_number(record.get("SizeW_Spec_M")) or split_mm_pair(record.get("Size_List_M"))[1]
        row["高度（mm）"] = normalize_mm_number(record.get("SizeTH_Spec_M")) or normalize_mm_number(record.get("Thick_Srch_M"))

    note1 = " | ".join(part for part in note1_parts if part)
    note2 = SPEC_SHEET_URL.format(part_no=part_no)
    note3 = " | ".join(part for part in [spec["series_desc"], detail_series_desc, f"Applications={sr6_text}" if sr6_text else ""] if part)
    spec_summary = format_model_summary(inductance_value, inductance_unit, inductance_tol, size_code, size_mm, current, sat_current or sat_current_typ, dcr)

    row.update(
        {
            "品牌": BRAND,
            "型号": part_no,
            "系列": series,
            "尺寸（inch）": size_code,
            "材质（介质）": spec["material"],
            "容值": "",
            "容值单位": "",
            "容值误差": "",
            "耐压（V）": "",
            "特殊用途": spec["special_use"],
            "备注1": note1,
            "备注2": note2,
            "备注3": note3,
            "器件类型": spec["component_type"],
            "安装方式": spec["mounting"],
            "封装代码": size_code,
            "尺寸（mm）": size_mm,
            "规格摘要": spec_summary,
            "生产状态": status,
            "官网链接": f"{DETAIL_URL}?pn={part_no}&u=M",
            "数据来源": "Taiyo Yuden official TY-COMPAS search API",
            "数据状态": "官方网页抽取",
            "校验时间": TODAY,
            "校验备注": f"TY-COMPAS {spec['key']} search api",
            "额定电流": current,
            "DCR": dcr,
            "电感值": inductance_value,
            "电感单位": inductance_unit,
            "电感误差": inductance_tol,
            "工作温度": work_temp,
            "系列说明": detail_series_desc or spec["series_desc"],
            "_model_rule_authority": spec["authority"],
        }
    )
    return row


def fetch_query_rows(session: requests.Session, spec: dict[str, object], seen_parts: set[str]) -> list[dict[str, str]]:
    query_params = {"cid": "L", "u": "M", **{key: value for key, value in spec["params"].items()}}
    first = fetch_json(session, {**query_params, "pg": "1"})
    total = int(first.get("record_count") or 0)
    pages = max(1, math.ceil(total / PAGE_SIZE))
    print(f"[taiyo_yuden:{spec['key']}] total={total} page_size={PAGE_SIZE} pages={pages}", flush=True)

    rows: list[dict[str, str]] = []
    skipped = 0
    for page in range(1, pages + 1):
        page_data = first if page == 1 else fetch_json(session, {**query_params, "pg": str(page)})
        records = page_data.get("records", []) or []
        print(f"[taiyo_yuden:{spec['key']}] page {page}/{pages} records={len(records)}", flush=True)
        for record in records:
            part_no = clean_text(record.get("PartNumber"))
            if not part_no or part_no in seen_parts:
                skipped += 1
                continue
            seen_parts.add(part_no)
            detail_specs: dict[str, str] = {}
            detail_series_desc = ""
            if spec.get("need_detail"):
                detail_specs, detail_series_desc = extract_detail_fields(session, part_no)
            row = build_row(
                record,
                spec,
                detail_specs=detail_specs,
                detail_series_desc=detail_series_desc,
            )
            rows.append(row)
            time.sleep(0.02)
        time.sleep(0.05)

    print(f"[taiyo_yuden:{spec['key']}] collected={len(rows)} skipped_duplicates={skipped}", flush=True)
    return rows


def merge_rows(existing: pd.DataFrame, incoming: pd.DataFrame) -> pd.DataFrame:
    if existing.empty:
        return incoming
    if incoming.empty:
        return existing
    work = existing.copy().fillna("")
    new_rows = incoming.copy().fillna("")
    if set(KEY_COLUMNS).issubset(work.columns):
        key_frame = new_rows.loc[:, KEY_COLUMNS].drop_duplicates().fillna("")
        merged_work = work.merge(key_frame.assign(_drop_marker=1), on=KEY_COLUMNS, how="left")
        work = merged_work[merged_work["_drop_marker"].isna()].drop(columns=["_drop_marker"]).copy()
    merged = pd.concat([work, new_rows], ignore_index=True)
    merged = merged.drop_duplicates(subset=KEY_COLUMNS, keep="last").reset_index(drop=True)
    return merged


def main() -> int:
    if not OFFICIAL_CSV.exists():
        raise SystemExit(f"missing official csv: {OFFICIAL_CSV}")

    existing = pd.read_csv(OFFICIAL_CSV, encoding="utf-8-sig", dtype=str, keep_default_na=False).fillna("")
    columns = list(existing.columns)

    session = requests.Session()
    session.headers.update(
        {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0 Safari/537.36",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "en-US,en;q=0.9",
            "Referer": "https://ds.yuden.co.jp/TYCOMPAS/ut/specificationSearcher?cid=L",
        }
    )

    seen_parts: set[str] = set()
    rows: list[dict[str, str]] = []
    for spec in QUERY_SPECS:
        rows.extend(fetch_query_rows(session, spec, seen_parts))

    if not rows:
        raise SystemExit("no Taiyo Yuden rows collected")

    df = pd.DataFrame(rows).fillna("")
    for column in columns:
        if column not in df.columns:
            df[column] = ""
    df = df[columns].fillna("")
    df = df.drop_duplicates(subset=KEY_COLUMNS, keep="first").reset_index(drop=True)
    df = df.sort_values(by=["器件类型", "型号"], kind="stable").reset_index(drop=True)

    snapshot = df.copy()
    snapshot.to_csv(SNAPSHOT_CSV, index=False, encoding="utf-8-sig")

    merged = merge_rows(existing, df)
    merged = merged.reindex(columns=columns).fillna("")
    merged.to_csv(OFFICIAL_CSV, index=False, encoding="utf-8-sig")

    summary = merged[merged["品牌"].astype(str).eq(BRAND)] if "品牌" in merged.columns else pd.DataFrame()
    print(
        f"taiyo_yuden_rows={len(df)} brand_total={len(summary)} merged_total={len(merged)} snapshot={SNAPSHOT_CSV}",
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
