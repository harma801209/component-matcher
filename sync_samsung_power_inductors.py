from __future__ import annotations

from datetime import datetime
from pathlib import Path
import re

import fitz
import pandas as pd
import requests


ROOT = Path(__file__).resolve().parent
OFFICIAL_CSV = ROOT / "Inductor" / "official_inductor_expansion.csv"
SNAPSHOT_CSV = ROOT / "Inductor" / "samsung_power_inductor_expansion.csv"
PDF_URL = "https://www.samsungsem.com/resources/file/cn/support/product_catalog/Power_Inductor.pdf"
PDF_PATH = ROOT / "cache" / "samsung_power_inductor.pdf"
TODAY = datetime.now().strftime("%Y-%m-%d")

BRAND = "三星Samsung"
TARGET_COMPONENT_TYPE = "功率电感"
SECTION_PAGES: dict[int, str] = {
    8: "Thin Film General Type",
    10: "Thin Film L Type",
    12: "Thin Film Bottom Type",
    14: "Wire Wound General Type",
    16: "Wire Wound L Type",
}

SIZE_MAP: dict[tuple[float, float], str] = {
    (1.6, 0.8): "0603",
    (1.4, 1.2): "0605",
    (2.0, 1.2): "0805",
    (2.0, 1.25): "0805",
    (2.1, 1.3): "0805",
    (2.0, 1.6): "0806",
    (2.55, 2.05): "1008",
    (2.5, 2.0): "1008",
    (3.2, 2.5): "1210",
    (4.1, 3.8): "1616",
    (4.1, 4.1): "1616",
}


def clean_text(value: object) -> str:
    if value is None:
        return ""
    try:
        if value != value:  # NaN
            return ""
    except Exception:
        pass
    text = str(value).strip()
    return "" if text.lower() == "nan" else text


def normalize_mm_number(text: str) -> str:
    raw = clean_text(text)
    if raw == "":
        return ""
    match = re.search(r"\d+(?:\.\d+)?", raw)
    if not match:
        return ""
    number = float(match.group(0))
    formatted = f"{number:.4f}".rstrip("0").rstrip(".")
    return formatted if formatted else "0"


def normalize_page_rows(page_text: str) -> list[list[str]]:
    lines = [line.strip() for line in page_text.splitlines() if line.strip()]
    rows: list[list[str]] = []
    i = 0
    while i < len(lines):
        if re.fullmatch(r"CIG[A-Z0-9]+#", lines[i]):
            values = lines[i + 1 : i + 9]
            if len(values) < 8:
                break
            rows.append([lines[i], *values])
            i += 9
            continue
        i += 1
    return rows


def parse_inductance(inductance_text: str) -> tuple[str, str]:
    raw = clean_text(inductance_text)
    match = re.fullmatch(r"([0-9]+(?:\.[0-9]+)?)([A-Za-z]+)", raw.replace(" ", ""))
    if not match:
        return raw, ""
    value = match.group(1)
    unit = match.group(2).upper()
    if unit == "UH":
        unit = "UH"
    elif unit == "NH":
        unit = "NH"
    elif unit == "MH":
        unit = "MH"
    return value, unit


def parse_numeric_amp(text: str) -> str:
    raw = clean_text(text).replace(" ", "")
    if raw == "":
        return ""
    match = re.search(r"([0-9]+(?:\.[0-9]+)?)", raw)
    return match.group(1) if match else raw


def parse_percentage(text: str) -> str:
    raw = clean_text(text)
    if raw == "":
        return ""
    cleaned = raw.replace("±", "").replace("%", "").strip()
    match = re.search(r"[0-9]+(?:\.[0-9]+)?", cleaned)
    return match.group(0) if match else cleaned


def derive_size_inch(l_size: str, w_size: str) -> str:
    key = (round(float(normalize_mm_number(l_size) or 0), 2), round(float(normalize_mm_number(w_size) or 0), 2))
    return SIZE_MAP.get(key, "")


def build_series(model: str) -> str:
    cleaned = clean_text(model)
    if cleaned.endswith("#") and len(cleaned) > 6:
        return cleaned[:-6]
    return cleaned


def build_size_mm(l_size: str, w_size: str, t_size: str) -> str:
    return " x ".join([clean_text(l_size), clean_text(w_size), clean_text(t_size)])


def build_summary(inductance: str, tol: str, isat: str, itemp: str, dcr: str, size_mm: str) -> str:
    parts = [
        f"L={inductance}",
        f"Tol={tol}",
        f"Isat={isat}",
        f"Itemp={itemp}",
        f"DCR={dcr}",
        size_mm,
    ]
    return " | ".join(part for part in parts if part)


def download_pdf() -> None:
    if PDF_PATH.exists() and PDF_PATH.stat().st_size > 1000:
        return
    PDF_PATH.parent.mkdir(parents=True, exist_ok=True)
    response = requests.get(PDF_URL, timeout=120)
    response.raise_for_status()
    PDF_PATH.write_bytes(response.content)


def extract_rows() -> pd.DataFrame:
    download_pdf()
    pdf = fitz.open(str(PDF_PATH))
    rows: list[dict[str, str]] = []
    for page_index, section in SECTION_PAGES.items():
        if page_index >= pdf.page_count:
            continue
        page = pdf.load_page(page_index)
        page_rows = normalize_page_rows(page.get_text("text"))
        for model, inductance_text, tol_text, isat_text, itemp_text, dcr_text, l_size, w_size, t_size in page_rows:
            inductance_value, inductance_unit = parse_inductance(inductance_text)
            tol = parse_percentage(tol_text)
            isat = clean_text(isat_text)
            itemp = clean_text(itemp_text)
            dcr = clean_text(dcr_text)
            size_inch = derive_size_inch(l_size, w_size)
            size_mm = build_size_mm(l_size, w_size, t_size)
            series = build_series(model)
            rows.append(
                {
                    "品牌": BRAND,
                    "型号": model,
                    "系列": series,
                    "尺寸（inch）": size_inch,
                    "材质（介质）": "",
                    "容值": "",
                    "容值单位": "",
                    "容值误差": "",
                    "耐压（V）": "",
                    "特殊用途": "Power Inductor",
                    "备注1": f"Isat Max: {isat} | Itemp Max: {itemp}",
                    "备注2": PDF_URL,
                    "备注3": section,
                    "器件类型": TARGET_COMPONENT_TYPE,
                    "安装方式": "SMT",
                    "封装代码": size_inch,
                    "尺寸（mm）": size_mm,
                    "规格摘要": build_summary(inductance_value, tol, isat, itemp, dcr, size_mm),
                    "生产状态": "Active",
                    "长度（mm）": normalize_mm_number(l_size),
                    "宽度（mm）": normalize_mm_number(w_size),
                    "高度（mm）": normalize_mm_number(t_size),
                    "官网链接": PDF_URL,
                    "数据来源": "Samsung official Power Inductor catalog PDF",
                    "数据状态": "官方目录抽取",
                    "校验时间": TODAY,
                    "校验备注": f"Samsung power inductor catalog page {page_index + 1}",
                    "直径（mm）": "",
                    "脚距（mm）": "",
                    "极性": "",
                    "ESR": "",
                    "纹波电流": "",
                    "寿命（h）": "",
                    "工作温度": "-55 to +125℃ (Including self generated temperature rise)",
                    "阻值@25C": "",
                    "阻值单位": "",
                    "阻值误差": "",
                    "B值": "",
                    "B值条件": "",
                    "共模阻抗": "",
                    "阻抗单位": "",
                    "额定电流": itemp,
                    "DCR": dcr,
                    "回路数": "",
                    "电感值": inductance_value,
                    "电感单位": inductance_unit,
                    "电感误差": tol,
                    "饱和电流": isat,
                    "屏蔽类型": "Magnetically Shielded Type",
                    "阻抗@100MHz": "",
                    "系列说明": f"Samsung {section} Power Inductor",
                    "_model_rule_authority": "Samsung official Power Inductor catalog PDF",
                    "_resistance_ohm": "",
                    "输出频率": "",
                    "频率单位": "",
                    "频差（ppm）": "",
                    "电源电压": "",
                    "输出类型": "",
                    "占空比": "",
                    "频率": "",
                    "负载电容（pF）": "",
                    "驱动电平": "",
                    "_body_size": size_mm,
                }
            )
    if not rows:
        return pd.DataFrame()
    df = pd.DataFrame(rows).fillna("")
    df = df.drop_duplicates(subset=["品牌", "型号", "器件类型"], keep="first").reset_index(drop=True)
    return df


def merge_into_official_csv(new_rows: pd.DataFrame) -> tuple[int, int]:
    if new_rows is None or new_rows.empty:
        return 0, 0

    if OFFICIAL_CSV.exists():
        existing = pd.read_csv(OFFICIAL_CSV, encoding="utf-8-sig").fillna("")
    else:
        existing = pd.DataFrame(columns=list(new_rows.columns))

    columns = list(existing.columns)
    for col in new_rows.columns:
        if col not in columns:
            columns.append(col)

    existing = existing.reindex(columns=columns, fill_value="")
    new_rows = new_rows.reindex(columns=columns, fill_value="")

    incoming_keys = {
        (clean_text(brand), clean_text(model), clean_text(component_type))
        for brand, model, component_type in zip(
            new_rows["品牌"].astype(str),
            new_rows["型号"].astype(str),
            new_rows["器件类型"].astype(str),
        )
        if clean_text(brand) and clean_text(model) and clean_text(component_type)
    }
    if incoming_keys:
        existing = existing[
            ~existing.apply(
                lambda row: (
                    clean_text(row.get("品牌", "")),
                    clean_text(row.get("型号", "")),
                    clean_text(row.get("器件类型", "")),
                )
                in incoming_keys,
                axis=1,
            )
        ]

    merged = pd.concat([existing, new_rows], ignore_index=True).fillna("")
    merged = merged.drop_duplicates(subset=["品牌", "型号", "器件类型"], keep="first").reset_index(drop=True)
    merged.to_csv(OFFICIAL_CSV, index=False, encoding="utf-8-sig")
    return len(existing), len(merged)


def main() -> int:
    if not OFFICIAL_CSV.exists():
        raise SystemExit(f"missing official csv: {OFFICIAL_CSV}")

    rows = extract_rows()
    if rows.empty:
        raise SystemExit("No Samsung power inductor rows were parsed.")

    rows.to_csv(SNAPSHOT_CSV, index=False, encoding="utf-8-sig")
    before, after = merge_into_official_csv(rows)
    print(f"[samsung] rows={len(rows)} merged={before}->{after} snapshot={SNAPSHOT_CSV}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
