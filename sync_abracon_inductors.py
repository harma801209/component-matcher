from __future__ import annotations

from datetime import datetime
from io import StringIO
from pathlib import Path
import html as html_lib
import re
import subprocess
import sys

import pandas as pd
from playwright.sync_api import sync_playwright


ROOT = Path(__file__).resolve().parent
OFFICIAL_CSV = ROOT / "Inductor" / "official_inductor_expansion.csv"
SNAPSHOT_CSV = ROOT / "Inductor" / "abracon_inductor_expansion.csv"
STAMP = datetime.now().strftime("%Y-%m-%d %H:%M")
BRAND = "Abracon"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}

OFFICIAL_COLUMNS = pd.read_csv(OFFICIAL_CSV, nrows=0, encoding="utf-8-sig").columns.tolist()

PAGE_CONFIGS = [
    {
        "url": "https://abracon.com/product-lineup/power-magnetics/inductors/low-profile-molded-inductors",
        "component_type": "功率电感",
        "mount": "SMT",
        "material_hint": "Molded",
        "special_use": "Low Profile Molded Inductors",
    },
    {
        "url": "https://abracon.com/mini-molded-inductors",
        "component_type": "功率电感",
        "mount": "SMT",
        "material_hint": "Molded",
        "special_use": "Mini Molded Inductors",
    },
    {
        "url": "https://abracon.com/automotive-mini-molded-inductors",
        "component_type": "功率电感",
        "mount": "SMT",
        "material_hint": "Molded",
        "special_use": "Automotive Mini Molded Inductors",
    },
    {
        "url": "https://abracon.com/hot-press-molded-inductors",
        "component_type": "功率电感",
        "mount": "SMT",
        "material_hint": "Molded",
        "special_use": "Hot Press Molded Inductors",
    },
    {
        "url": "https://abracon.com/molded-stacked-inductor-solutions-for-high-power-applications",
        "component_type": "功率电感",
        "mount": "SMT",
        "material_hint": "Stacked",
        "special_use": "AMSLA High Power Density Stacked Inductors",
    },
    {
        "url": "https://abracon.com/high-power-density-commercial-inductors",
        "component_type": "功率电感",
        "mount": "SMT",
        "material_hint": "Commercial",
        "special_use": "High Power Density Commercial Inductors",
    },
    {
        "url": "https://abracon.com/ultra-low-profile-wire-wound-inductors",
        "component_type": "功率电感",
        "mount": "SMT",
        "material_hint": "Wire Wound",
        "special_use": "Ultra Low Profile Wire Wound Inductors",
    },
    {
        "url": "https://abracon.com/high-power-density-transportation-inductors",
        "component_type": "功率电感",
        "mount": "SMT",
        "material_hint": "Automotive",
        "special_use": "ASPIAIG-Q High Power Density Inductors",
    },
    {
        "url": "https://abracon.com/extended-temperature-molded-inductors",
        "component_type": "功率电感",
        "mount": "SMT",
        "material_hint": "Molded",
        "special_use": "AMXLA-Q Extended Temperature Molded Inductors",
    },
    {
        "url": "https://abracon.com/product-lineup/power-magnetics/inductors/power-inductors/stacked-assembly-inductors/assembly-inductors",
        "component_type": "功率电感",
        "mount": "SMT",
        "material_hint": "Assembly",
        "special_use": "Assembly Inductors",
    },
    {
        "url": "https://abracon.com/product-lineup/power-magnetics/inductors/power-inductors/low-profile-multilayer-power-inductors",
        "component_type": "功率电感",
        "mount": "SMT",
        "material_hint": "Multilayer",
        "special_use": "High Power 0402 Multilayer Inductors",
    },
    {
        "url": "https://abracon.com/product-lineup/power-magnetics/inductors/power-inductors/trans-inductor-voltage-regulator-tlvr-inductors",
        "component_type": "功率电感",
        "mount": "SMT",
        "material_hint": "TLVR",
        "special_use": "Trans-Inductor Voltage Regulator (TLVR) Inductors",
    },
    {
        "url": "https://abracon.com/product-lineup/power-magnetics/inductors/rf-inductors",
        "component_type": "射频电感",
        "mount": "SMT",
        "material_hint": "",
        "special_use": "RF Inductors",
        "table_labels": [
            "Ceramic Multilayer Inductors",
            "Thin Film Inductors",
            "Ceramic Wirewound Inductors",
            "Air Coil Inductors",
            "Automotive RF Inductors",
        ],
    },
    {
        "url": "https://abracon.com/product-lineup/power-magnetics/inductors/rf-inductors/miniature-ultra-high-q-rf-inductors",
        "component_type": "射频电感",
        "mount": "SMT",
        "material_hint": "Ceramic",
        "special_use": "Ultra Miniature High-Q RF Inductors",
    },
    {
        "url": "https://abracon.com/automotive-rf-wirewound-high-q-inductors",
        "component_type": "射频电感",
        "mount": "SMT",
        "material_hint": "Wire Wound",
        "special_use": "Automotive RF Wirewound High-Q Inductors",
    },
    {
        "url": "https://abracon.com/automotive-rf-wirewound-inductors",
        "component_type": "射频电感",
        "mount": "SMT",
        "material_hint": "Wire Wound",
        "special_use": "Automotive RF Wirewound Inductors",
    },
    {
        "url": "https://abracon.com/automotive-rf-multilayer-inductors",
        "component_type": "射频电感",
        "mount": "SMT",
        "material_hint": "Multilayer",
        "special_use": "Automotive RF Multilayer Inductors",
    },
    {
        "url": "https://abracon.com/product-lineup/power-magnetics/common-mode-chokes",
        "component_type": "共模电感",
        "mount": "SMT",
        "material_hint": "Ferrite",
        "special_use": "Common Mode Chokes",
        "table_labels": [
            "USB Signal-Line Common Mode Chokes",
            "Power Line Common Mode Chokes",
            "Power Line AEC-Q200 Common Mode Chokes",
            "Signal Line Common Mode Chokes",
            "Signal Line AEC-Q200 Common Mode Chokes",
        ],
    },
    {
        "url": "https://abracon.com/commercial-common-mode-chokes",
        "component_type": "共模电感",
        "mount": "SMT",
        "material_hint": "Ferrite",
        "special_use": "Commercial Common Mode Chokes",
    },
    {
        "url": "https://abracon.com/automotive-common-mode-chokes",
        "component_type": "共模电感",
        "mount": "SMT",
        "material_hint": "Ferrite",
        "special_use": "Automotive Common Mode Chokes",
    },
    {
        "url": "https://abracon.com/product-lineup/power-magnetics/common-mode-chokes/usb-mipi-common-mode-chokes",
        "component_type": "共模电感",
        "mount": "SMT",
        "material_hint": "Ferrite",
        "special_use": "USB & MIPI Common Mode Chokes",
    },
    {
        "url": "https://abracon.com/product-lineup/power-magnetics/common-mode-chokes/low-profile-aec-q200-power-line-common-mode-choke",
        "component_type": "共模电感",
        "mount": "SMT",
        "material_hint": "Ferrite",
        "special_use": "Low-profile AEC-Q200 Power Line Common Mode Choke",
    },
    {
        "url": "https://abracon.com/product-lineup/power-magnetics/common-mode-chokes/usb-c-signal-line-common-mode-chokes",
        "component_type": "共模电感",
        "mount": "SMT",
        "material_hint": "Ferrite",
        "special_use": "USB-C Signal-line Common Mode Chokes",
    },
    {
        "url": "https://abracon.com/product-lineup/power-magnetics/ferrite-beads",
        "component_type": "磁珠",
        "mount": "SMT",
        "material_hint": "Ferrite",
        "special_use": "High-Frequency Ferrite Beads",
        "table_labels": [
            "High-Frequency Ferrite Beads",
            "Automotive Ferrite Beads",
        ],
    },
    {
        "url": "https://abracon.com/high-frequency-ferrite-beads",
        "component_type": "磁珠",
        "mount": "SMT",
        "material_hint": "Ferrite",
        "special_use": "High Frequency Ferrite Beads",
    },
    {
        "url": "https://abracon.com/high-current-ferrite-beads",
        "component_type": "磁珠",
        "mount": "SMT",
        "material_hint": "Ferrite",
        "special_use": "High Current Ferrite Beads",
    },
    {
        "url": "https://abracon.com/product-lineup/power-magnetics/ferrite-beads/sub-ghz-frequency-high-power",
        "component_type": "磁珠",
        "mount": "SMT",
        "material_hint": "Ferrite",
        "special_use": "Sub-GHz Frequency - High Power Ferrite Beads",
    },
    {
        "url": "https://abracon.com/product-lineup/power-magnetics/ferrite-beads/sub-ghz-frequency-low-power",
        "component_type": "磁珠",
        "mount": "SMT",
        "material_hint": "Ferrite",
        "special_use": "Sub-GHz Frequency - Low Power Ferrite Beads",
    },
]

SUMMARY_KEYWORDS = [
    "inductance",
    "impedance",
    "q factor",
    "q (min)",
    "q (@2.4ghz)",
    "srf",
    "dcr",
    "current rating",
    "rated current",
    "saturation current",
    "temp rise",
    "operating temp",
    "operating temperature",
    "rated voltage",
    "withstanding voltage",
    "package",
    "size",
    "mounting type",
    "composite",
    "type",
    "sub category",
    "frequency range",
]


def clean_text(value: object) -> str:
    if value is None:
        return ""
    try:
        if value != value:
            return ""
    except Exception:
        pass
    text = html_lib.unescape(str(value)).replace("\xa0", " ")
    text = re.sub(r"\s+", " ", text).strip()
    return "" if text.lower() == "nan" else text


def first_number_text(value: object) -> str:
    text = clean_text(value).replace(",", "")
    if not text:
        return ""
    match = re.search(r"[-+]?(?:\d+\.\d+|\d+)", text)
    if not match:
        return ""
    number = match.group(0)
    try:
        parsed = float(number)
    except Exception:
        return number
    formatted = f"{parsed:.4f}".rstrip("0").rstrip(".")
    return formatted if formatted else "0"


def extract_model(raw: object) -> str:
    text = clean_text(raw)
    if not text:
        return ""
    first_segment = re.split(r"\s*\|\s*", text, maxsplit=1)[0]
    first_segment = re.sub(r"^(View Datasheet|Buy Now|Datasheet|Support Docs|Channel Inventory)\s*", "", first_segment, flags=re.I)
    first_segment = first_segment.strip()
    tokens = re.findall(r"[A-Z][A-Z0-9-]{2,}", first_segment.upper())
    if tokens:
        return tokens[0]
    match = re.search(r"[A-Z][A-Z0-9-]{2,}", text.upper())
    return match.group(0) if match else first_segment


def normalize_unit(raw: str, kind: str) -> str:
    text = clean_text(raw)
    lowered = text.lower().replace("µ", "u").replace("μ", "u").replace("Ω", "Ω")
    if kind == "inductance":
        if "nh" in lowered:
            return "nH"
        if "uh" in lowered:
            return "uH"
        if "mh" in lowered:
            return "mH"
        if "ph" in lowered:
            return "pH"
    elif kind in {"current", "rating"}:
        if "ma" in lowered:
            return "mA"
        if re.search(r"\b[a]\b", lowered):
            return "A"
    elif kind in {"dcr", "impedance"}:
        if "mohm" in lowered or "mω" in lowered or "mΩ" in lowered:
            return "mΩ"
        if "ohm" in lowered or "ω" in lowered or "Ω" in lowered:
            return "Ω"
    elif kind == "voltage":
        return "V"
    return ""


def value_with_unit(raw: object, kind: str) -> tuple[str, str]:
    text = clean_text(raw)
    if not text:
        return "", ""
    number = first_number_text(text)
    return number, normalize_unit(text, kind)


def parse_dimensions(text: str) -> tuple[str, str, str]:
    cleaned = clean_text(text)
    if not cleaned:
        return "", "", ""
    match = re.search(
        r"(\d+(?:\.\d+)?)\s*x\s*(\d+(?:\.\d+)?)(?:\s*x\s*(\d+(?:\.\d+)?))?",
        cleaned,
        flags=re.I,
    )
    if not match:
        return "", "", ""
    length = first_number_text(match.group(1))
    width = first_number_text(match.group(2))
    height = first_number_text(match.group(3)) if match.group(3) else ""
    return length, width, height


def infer_material(record: dict[str, str], config: dict[str, str], page_label: str) -> str:
    for key in record:
        key_text = key.lower()
        if "composite" in key_text or key_text == "type":
            value = clean_text(record[key])
            if value:
                return value

    title_text = f"{page_label} {config.get('special_use', '')} {config.get('material_hint', '')}".lower()
    if "wire wound" in title_text:
        return "Wire Wound"
    if "multilayer" in title_text:
        return "Ceramic"
    if "thin film" in title_text:
        return "Thin Film"
    if "air coil" in title_text:
        return "Air Coil"
    if "ferrite beads" in title_text or config.get("component_type") in {"磁珠", "共模电感"}:
        return "Ferrite"
    if "molded" in title_text or "stacked" in title_text or "commercial" in title_text or "transportation" in title_text or "extended temperature" in title_text:
        return "Metal Alloy"
    hint = clean_text(config.get("material_hint", ""))
    if hint:
        return hint
    return ""


def infer_mount(record: dict[str, str], config: dict[str, str]) -> str:
    for key, value in record.items():
        key_text = key.lower()
        value_text = clean_text(value).lower()
        if "mounting type" in key_text or "mount" in key_text:
            if "through" in value_text:
                return "THT"
            if "surface" in value_text or "smt" in value_text:
                return "SMT"
    return clean_text(config.get("mount", "")) or "SMT"


def infer_status(record: dict[str, str]) -> str:
    for key in record:
        key_text = key.lower()
        if key_text in {"inventory", "part status"}:
            value = clean_text(record[key])
            if value:
                return value
    return "Production"


def find_value(record: dict[str, str], keywords: list[str]) -> str:
    for key, value in record.items():
        key_text = key.lower()
        if any(keyword in key_text for keyword in keywords):
            cleaned = clean_text(value)
            if cleaned:
                return cleaned
    return ""


def build_summary(page_label: str, record: dict[str, str]) -> str:
    parts = [page_label]
    for key, value in record.items():
        key_text = key.lower()
        if any(keyword in key_text for keyword in SUMMARY_KEYWORDS):
            cleaned = clean_text(value)
            if cleaned:
                parts.append(f"{clean_text(key)}={cleaned}")
        if len(parts) >= 10:
            break
    return " | ".join(parts)


def normalize_header(header: str) -> str:
    text = clean_text(header)
    text = text.replace("Click to configure columns", "")
    text = text.replace("  ", " ")
    if text == "Click to configure columnsPart":
        return "Part"
    if text == "Click to configure columnsPart Number":
        return "Part Number"
    return text


def extract_tables(page_html: str) -> list[list[list[str]]]:
    # This keeps the parsing resilient against the site’s client-side table rendering.
    tables = page_html
    return []


def load_page_tables(url: str) -> tuple[str, list[list[list[str]]]]:
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(user_agent=HEADERS["User-Agent"])
        try:
            page.goto(url, wait_until="domcontentloaded", timeout=120000)
            page.wait_for_selector("table", timeout=60000)
            page.wait_for_timeout(5000)
            title = page.title()
            tables = page.evaluate(
                """() => Array.from(document.querySelectorAll('table')).map(table =>
                    Array.from(table.querySelectorAll('tr')).map(tr =>
                        Array.from(tr.querySelectorAll('th,td')).map(cell =>
                            (cell.innerText || '').replace(/\\s+/g, ' ').trim()
                        )
                    )
                )"""
            )
            return title, tables
        finally:
            browser.close()


def table_rows_to_records(table_rows: list[list[str]]) -> list[dict[str, str]]:
    if len(table_rows) < 2:
        return []
    headers = [normalize_header(cell) for cell in table_rows[0]]
    if not any(headers):
        return []
    records: list[dict[str, str]] = []
    for row in table_rows[1:]:
        values = [clean_text(cell) for cell in row]
        if not any(values):
            continue
        if len(values) < len(headers):
            values = values + [""] * (len(headers) - len(values))
        elif len(values) > len(headers):
            values = values[: len(headers)]
        record = {headers[idx]: values[idx] for idx in range(len(headers))}
        records.append(record)
    return records


def build_rows() -> pd.DataFrame:
    rows: list[dict[str, str]] = []
    for config in PAGE_CONFIGS:
        url = config["url"]
        page_title, tables = load_page_tables(url)
        page_label = clean_text(config.get("special_use", "")) or page_title.split("|", 1)[-1].strip()
        table_labels = config.get("table_labels", [])
        for table_idx, table_rows in enumerate(tables):
            records = table_rows_to_records(table_rows)
            if not records:
                continue
            table_label = table_labels[table_idx] if table_idx < len(table_labels) else page_label
            for record in records:
                model = find_value(record, ["part number", "series", "part"])
                if not model:
                    first_header = next(iter(record.keys()), "")
                    model = clean_text(record.get(first_header, ""))
                model = extract_model(model)
                if not model:
                    continue

                inductance_raw = find_value(record, ["inductance"])
                impedance_raw = find_value(record, ["impedance"])
                dcr_raw = find_value(record, ["dcr", "dc resistance"])
                current_raw = find_value(record, ["current rating", "irms", "rated current"])
                sat_raw = find_value(record, ["saturation current"])
                temp_rise_raw = find_value(record, ["temp rise"])
                temp_raw = find_value(record, ["operating temp", "operating temperature", "otr"])
                rated_voltage_raw = find_value(record, ["rated voltage", "operating voltage"])
                withstanding_voltage_raw = find_value(record, ["withstanding voltage"])
                q_raw = find_value(record, ["q factor", "q (min)", "q (@2.4ghz)"])
                srf_raw = find_value(record, ["srf"])
                size_raw = find_value(record, ["size", "package size", "package / case", "l x w x h", "size (l x w x h)"])
                mounting_raw = find_value(record, ["mounting type"])
                inventory_raw = find_value(record, ["inventory", "part status"])
                sub_category_raw = find_value(record, ["sub category"])
                composite_raw = find_value(record, ["composite"])
                type_raw = find_value(record, ["type"])
                length_raw = find_value(record, ["length"])
                width_raw = find_value(record, ["width"])
                height_raw = find_value(record, ["height", "height-seated"])

                if not size_raw and any([length_raw, width_raw, height_raw]):
                    dims = [clean_text(length_raw), clean_text(width_raw), clean_text(height_raw)]
                    dims = [d for d in dims if d]
                    size_raw = " x ".join(dims)
                length_mm, width_mm, height_mm = parse_dimensions(size_raw)

                inductance_val, inductance_unit = value_with_unit(inductance_raw, "inductance") if inductance_raw else ("", "")
                current_val, current_unit = value_with_unit(current_raw, "current") if current_raw else ("", "")
                sat_val, sat_unit = value_with_unit(sat_raw, "current") if sat_raw else ("", "")
                dcr_val, dcr_unit = value_with_unit(dcr_raw, "dcr") if dcr_raw else ("", "")
                impedance_val, impedance_unit = value_with_unit(impedance_raw, "impedance") if impedance_raw else ("", "")
                rated_voltage_val, rated_voltage_unit = value_with_unit(rated_voltage_raw, "voltage") if rated_voltage_raw else ("", "")
                withstanding_val, withstanding_unit = value_with_unit(withstanding_voltage_raw, "voltage") if withstanding_voltage_raw else ("", "")

                material = infer_material(record, config, table_label)
                mount = infer_mount(record, config)
                status = infer_status(record)
                summary = build_summary(table_label, record)

                row = {column: "" for column in OFFICIAL_COLUMNS}
                row.update(
                    {
                        "品牌": BRAND,
                        "型号": model,
                        "系列": model,
                        "特殊用途": clean_text(sub_category_raw) or table_label,
                        "备注1": f"Page: {page_title}",
                        "备注2": f"Table: {table_idx}",
                        "备注3": f"Source: {url}",
                        "器件类型": config["component_type"],
                        "安装方式": mount,
                        "封装代码": model,
                        "材质（介质）": composite_raw or type_raw or material,
                        "尺寸（mm）": clean_text(size_raw),
                        "规格摘要": summary,
                        "生产状态": status,
                        "长度（mm）": length_mm,
                        "宽度（mm）": width_mm,
                        "高度（mm）": height_mm,
                        "官网链接": url,
                        "数据来源": "Abracon official product lineup",
                        "数据状态": "官方网页抽取",
                        "校验时间": STAMP,
                        "校验备注": f"Abracon | {page_label} | table {table_idx}",
                        "电感值": inductance_val,
                        "电感单位": inductance_unit,
                        "额定电流": current_val,
                        "DCR": dcr_raw or dcr_val,
                        "饱和电流": sat_raw or sat_val,
                        "阻抗@100MHz": impedance_raw if config["component_type"] == "磁珠" else "",
                        "阻抗单位": impedance_unit if config["component_type"] == "磁珠" else "",
                        "共模阻抗": impedance_raw if config["component_type"] == "共模电感" else "",
                        "系列说明": table_label,
                        "_model_rule_authority": "abracon_product_lineup",
                        "_body_size": clean_text(size_raw),
                    }
                )

                if rated_voltage_val:
                    row["电源电压"] = rated_voltage_val
                if withstanding_val:
                    row["耐压（V）"] = withstanding_val
                if q_raw:
                    row["备注3"] = f"{row['备注3']} | Q={q_raw}"
                if srf_raw:
                    row["备注3"] = f"{row['备注3']} | SRF={srf_raw}"
                if temp_raw:
                    row["工作温度"] = temp_raw
                elif temp_rise_raw:
                    row["工作温度"] = temp_rise_raw
                if current_unit:
                    row["备注2"] = f"{row['备注2']} | current_unit={current_unit}"
                if sat_unit and sat_unit != current_unit:
                    row["备注2"] = f"{row['备注2']} | sat_unit={sat_unit}"
                if dcr_unit:
                    row["备注2"] = f"{row['备注2']} | dcr_unit={dcr_unit}"
                if impedance_val:
                    if config["component_type"] == "共模电感":
                        row["共模阻抗"] = impedance_raw or impedance_val
                        row["阻抗单位"] = impedance_unit or "Ω"
                    elif config["component_type"] == "磁珠":
                        row["阻抗@100MHz"] = impedance_raw or impedance_val
                        row["阻抗单位"] = impedance_unit or "Ω"

                rows.append(row)
    if not rows:
        return pd.DataFrame()
    df = pd.DataFrame(rows).fillna("")
    df = df.drop_duplicates(subset=["品牌", "型号", "器件类型"], keep="first").reset_index(drop=True)
    return df


def merge_into_official_csv(new_rows: pd.DataFrame) -> tuple[int, int]:
    if new_rows is None or new_rows.empty:
        return 0, 0

    existing = pd.read_csv(OFFICIAL_CSV, encoding="utf-8-sig", low_memory=False).fillna("")
    columns = list(existing.columns)
    for column in new_rows.columns:
        if column not in columns:
            columns.append(column)

    existing = existing.reindex(columns=columns, fill_value="")
    new_rows = new_rows.reindex(columns=columns, fill_value="")

    incoming_keys = {
        (clean_text(brand), clean_text(model), clean_text(component_type))
        for brand, model, component_type in zip(
            new_rows["品牌"].astype(str),
            new_rows["型号"].astype(str),
            new_rows["器件类型"].astype(str),
        )
    }
    if incoming_keys:
        existing_keys = list(
            zip(
                existing["品牌"].astype(str).map(clean_text),
                existing["型号"].astype(str).map(clean_text),
                existing["器件类型"].astype(str).map(clean_text),
            )
        )
        keep_mask = [key not in incoming_keys for key in existing_keys]
        existing = existing.loc[keep_mask].copy()

    merged = pd.concat([existing, new_rows], ignore_index=True)
    merged = merged.drop_duplicates(subset=["品牌", "型号", "器件类型"], keep="last").reset_index(drop=True)
    merged.to_csv(OFFICIAL_CSV, index=False, encoding="utf-8-sig")
    return len(existing), len(merged)


def run_db_refresh() -> None:
    subprocess.run(
        [sys.executable, str(ROOT / "sync_inductor_incremental_refresh.py"), str(SNAPSHOT_CSV)],
        cwd=ROOT,
        check=True,
    )


def main() -> int:
    print("[abracon] loading pages", flush=True)
    df = build_rows()
    if df.empty:
        raise SystemExit("no Abracon rows found")

    print(f"[abracon] parsed rows={len(df)}", flush=True)
    print("[abracon] writing snapshot", flush=True)
    df.to_csv(SNAPSHOT_CSV, index=False, encoding="utf-8-sig")

    print("[abracon] merging official csv", flush=True)
    before_count, after_count = merge_into_official_csv(df)
    print("[abracon] refreshing db/cache", flush=True)
    run_db_refresh()

    print(f"snapshot_rows={len(df)} official_before={before_count} official_after={after_count}")
    print(f"snapshot={SNAPSHOT_CSV}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
