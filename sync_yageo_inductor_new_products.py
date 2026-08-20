from __future__ import annotations

from datetime import datetime
from pathlib import Path
import html as html_lib
import json
import re
import subprocess
import sys

import pandas as pd
import requests


ROOT = Path(__file__).resolve().parent
OFFICIAL_CSV = ROOT / "Inductor" / "official_inductor_expansion.csv"
SNAPSHOT_CSV = ROOT / "Inductor" / "yageo_inductor_new_product_intros_expansion.csv"
GRAPHQL_URL = "https://yageogroup.com/api/graphql?version=1&direct=true"
STAMP = datetime.now().strftime("%Y-%m-%d %H:%M")

BRAND_ALLOWLIST = {"KEMET", "PULSE"}
GROUP_RULES = [
    ("Common Mode Chokes", "共模电感", "Common Mode Choke"),
    ("Power", "功率电感", "Power Inductor"),
]
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
    "Content-Type": "application/json",
}
OFFICIAL_COLUMNS = pd.read_csv(OFFICIAL_CSV, nrows=0, encoding="utf-8-sig").columns.tolist()


QUERY = """
query Q($defaultLanguage: String!, $first: Int, $after: Int) {
  getResourceLibraryNewProductIntroductionItemListing(
    defaultLanguage: $defaultLanguage
    first: $first
    after: $after
    sortBy: ["publicationDate"]
    sortOrder: ["DESC"]
  ) {
    edges {
      node {
        id
        name
        body
        features
        quickFacts
        brand {
          ... on object_Brand {
            name
            __typename
          }
          __typename
        }
        productGroup {
          ... on object_ProductGroup {
            name
            __typename
          }
          __typename
        }
        publicationDate
        __typename
      }
      __typename
    }
    __typename
  }
}
"""


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


def normalize_range_text(text: str) -> str:
    cleaned = clean_text(text)
    cleaned = cleaned.replace("–", "-").replace("—", "-").replace("~", " ~ ")
    cleaned = re.sub(r"\s+", " ", cleaned)
    return cleaned


def extract_group_names(product_group: object) -> list[str]:
    names: list[str] = []
    if isinstance(product_group, list):
        for item in product_group:
            if isinstance(item, dict):
                name = clean_text(item.get("name", ""))
                if name and name not in names:
                    names.append(name)
    elif isinstance(product_group, dict):
        name = clean_text(product_group.get("name", ""))
        if name:
            names.append(name)
    return names


def classify_group(group_names: list[str]) -> tuple[str, str, str]:
    joined = " | ".join(group_names).lower()
    for needle, component_type, special_use in GROUP_RULES:
        if needle.lower() in joined:
            return component_type, "SMT", special_use
    return "", "", ""


def extract_series_code(name: str, body: str) -> str:
    name = clean_text(name)
    body = clean_text(body)
    candidates: list[str] = []

    if name:
        first_token = name.split()[0]
        if re.match(r"^[A-Z0-9-]{3,}$", first_token):
            candidates.append(first_token)

    for pattern in [
        r"\b[A-Z]{2,}\d{3,}[A-Z0-9-]*\b",
        r"\b[A-Z]{2,}\d{2,}\b",
    ]:
        for match in re.findall(pattern, body):
            if match not in candidates:
                candidates.append(match)

    for candidate in candidates:
        if re.search(r"\d", candidate):
            return candidate
    return candidates[0] if candidates else name.split()[0] if name else ""


def parse_quickfacts(quickfacts: str) -> dict[str, str]:
    text = normalize_range_text(quickfacts)
    data = {
        "rated_voltage": "",
        "rated_current_low": "",
        "rated_current_high": "",
        "inductance_low": "",
        "inductance_high": "",
        "inductance_unit": "",
        "dcr_low": "",
        "dcr_high": "",
        "dcr_unit": "",
        "temperature": "",
        "size": "",
    }

    m = re.search(r"Rated Voltage:\s*([0-9.]+)\s*V", text, flags=re.I)
    if m:
        data["rated_voltage"] = first_number_text(m.group(1))

    m = re.search(r"Rated Current Range:\s*([0-9.]+)\s*(?:-|~|to)\s*([0-9.]+)\s*A", text, flags=re.I)
    if m:
        data["rated_current_low"] = first_number_text(m.group(1))
        data["rated_current_high"] = first_number_text(m.group(2))

    m = re.search(r"Irms\s*\(A\):\s*([0-9.]+)\s*(?:-|~|to)\s*([0-9.]+)\s*A", text, flags=re.I)
    if m:
        data["rated_current_low"] = first_number_text(m.group(1))
        data["rated_current_high"] = first_number_text(m.group(2))

    m = re.search(r"Inductance Range:\s*([0-9.]+)\s*(?:-|~|to)\s*([0-9.]+)\s*([mnuµ]?H)", text, flags=re.I)
    if m:
        data["inductance_low"] = first_number_text(m.group(1))
        data["inductance_high"] = first_number_text(m.group(2))
        data["inductance_unit"] = clean_text(m.group(3)).lower().replace("h", "H").replace("uH", "uH")

    m = re.search(r"Inductance:\s*([0-9.]+)\s*([mnuµ]?H)\s*(?:-|~|to)\s*([0-9.]+)\s*([mnuµ]?H)", text, flags=re.I)
    if m:
        data["inductance_low"] = first_number_text(m.group(1))
        data["inductance_high"] = first_number_text(m.group(3))
        data["inductance_unit"] = clean_text(m.group(2)).replace("µ", "u")

    m = re.search(r"DCR:\s*([0-9.]+)\s*(?:-|~|to)\s*([0-9.]+)\s*([mnuµ]?Ω)", text, flags=re.I)
    if m:
        data["dcr_low"] = first_number_text(m.group(1))
        data["dcr_high"] = first_number_text(m.group(2))
        data["dcr_unit"] = clean_text(m.group(3))

    m = re.search(r"Operating Voltage:\s*~?\s*([0-9.]+)\s*V", text, flags=re.I)
    if m:
        data["rated_voltage"] = first_number_text(m.group(1))

    m = re.search(r"Operating Temperature(?: Range)?:\s*([^$]+?)(?:Size:|Inductance:|Irms|Rated Voltage:|$)", text, flags=re.I)
    if m:
        data["temperature"] = clean_text(m.group(1))

    m = re.search(r"Size:\s*([^$]+?)(?:Inductance:|Irms|Operating Voltage:|Operating Temperature Range:|$)", text, flags=re.I)
    if m:
        data["size"] = clean_text(m.group(1))

    return data


def fetch_items() -> list[dict]:
    payload = {
        "operationName": "Q",
        "variables": {"defaultLanguage": "en", "first": 100, "after": 0},
        "query": QUERY,
    }
    response = requests.post(GRAPHQL_URL, headers=HEADERS, json=payload, timeout=120)
    response.raise_for_status()
    edges = response.json()["data"]["getResourceLibraryNewProductIntroductionItemListing"]["edges"]
    items: list[dict] = []
    for edge in edges:
        node = edge.get("node") if isinstance(edge, dict) else None
        if not node:
            continue
        items.append(node)
    return items


def build_rows() -> pd.DataFrame:
    rows: list[dict[str, str]] = []
    items = fetch_items()
    for item in items:
        brand_name = clean_text((item.get("brand") or {}).get("name", ""))
        if brand_name not in BRAND_ALLOWLIST:
            continue

        group_names = extract_group_names(item.get("productGroup"))
        component_type, mount, special_use = classify_group(group_names)
        if not component_type:
            continue

        body = clean_text(item.get("body", ""))
        features = clean_text(item.get("features", ""))
        quickfacts = clean_text(item.get("quickFacts", ""))
        series_code = extract_series_code(item.get("name", ""), body)
        parsed = parse_quickfacts(quickfacts)

        if brand_name == "KEMET" and component_type != "共模电感":
            continue
        if brand_name == "PULSE" and component_type != "功率电感":
            continue

        material = ""
        if "nanocrystalline" in body.lower():
            material = "Nanocrystalline"
        elif "ferrite" in body.lower():
            material = "Ferrite"

        shield_type = ""
        if "shielded" in body.lower() or "shield" in special_use.lower():
            shield_type = "Magnetically Shielded Type"

        current_high = parsed["rated_current_high"] or parsed["rated_current_low"]
        inductance_low = parsed["inductance_low"]
        inductance_high = parsed["inductance_high"]
        inductance_unit = parsed["inductance_unit"].replace("uh", "uH").replace("mh", "mH").replace("nh", "nH")
        dcr_low = parsed["dcr_low"]
        dcr_high = parsed["dcr_high"]
        dcr_unit = parsed["dcr_unit"]
        voltage = parsed["rated_voltage"]
        temperature = parsed["temperature"]
        size_text = parsed["size"]

        summary_parts: list[str] = []
        if inductance_low and inductance_high:
            summary_parts.append(f"L={inductance_low}~{inductance_high}{inductance_unit}")
        elif inductance_high:
            summary_parts.append(f"L={inductance_high}{inductance_unit}")
        if parsed["rated_current_low"] and parsed["rated_current_high"]:
            summary_parts.append(f"Irms={parsed['rated_current_low']}~{parsed['rated_current_high']}A")
        elif current_high:
            summary_parts.append(f"Irms={current_high}A")
        if dcr_low and dcr_high:
            summary_parts.append(f"DCR={dcr_low}~{dcr_high}{dcr_unit}")
        if voltage:
            summary_parts.append(f"V={voltage}V")
        if temperature:
            summary_parts.append(temperature)
        if size_text:
            summary_parts.append(size_text)
        if features:
            summary_parts.append(features)

        row = {column: "" for column in OFFICIAL_COLUMNS}
        row.update(
            {
                "品牌": brand_name,
                "型号": series_code,
                "系列": series_code,
                "材质（介质）": material,
                "特殊用途": special_use or clean_text(item.get("name", "")),
                "备注1": f"Body: {body[:180]}" if body else "",
                "备注2": f"Features: {features}" if features else "",
                "备注3": f"YAGEO resource intro | groups={'; '.join(group_names)}",
                "器件类型": component_type,
                "安装方式": mount,
                "封装代码": series_code,
                "尺寸（mm）": size_text,
                "规格摘要": " | ".join(summary_parts),
                "生产状态": "Production",
                "官网链接": "https://yageogroup.com/browse/products?search=inductor",
                "数据来源": "YAGEO Group resource library new-product introduction",
                "数据状态": "官方资源库抽取",
                "校验时间": STAMP,
                "校验备注": clean_text(item.get("name", "")),
                "额定电流": current_high,
                "DCR": dcr_high or dcr_low,
                "电感值": inductance_high or inductance_low,
                "电感单位": inductance_unit,
                "电感误差": "",
                "饱和电流": "",
                "屏蔽类型": shield_type,
                "系列说明": clean_text(item.get("name", "")),
                "_model_rule_authority": "https://yageogroup.com/api/graphql?version=1&direct=true",
                "_body_size": size_text,
            }
        )
        rows.append(row)

    df = pd.DataFrame(rows).fillna("")
    if not df.empty:
        df = df.drop_duplicates(subset=["品牌", "型号", "器件类型"], keep="first").reset_index(drop=True)
    return df


def merge_into_official_csv(new_rows: pd.DataFrame) -> tuple[int, int]:
    if new_rows is None or new_rows.empty:
        return 0, 0

    existing = pd.read_csv(OFFICIAL_CSV, encoding="utf-8-sig").fillna("")
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


def refresh_runtime(snapshot_csv: Path) -> None:
    subprocess.run(
        [sys.executable, str(ROOT / "sync_inductor_incremental_refresh.py"), str(snapshot_csv)],
        cwd=ROOT,
        check=True,
    )


def main() -> int:
    if not OFFICIAL_CSV.exists():
        raise SystemExit(f"missing official csv: {OFFICIAL_CSV}")

    rows = build_rows()
    if rows.empty:
        raise SystemExit("No YAGEO inductor rows were parsed.")

    rows.to_csv(SNAPSHOT_CSV, index=False, encoding="utf-8-sig")
    before, after = merge_into_official_csv(rows)
    refresh_runtime(SNAPSHOT_CSV)
    print(f"[yageo] rows={len(rows)} merged={before}->{after} snapshot={SNAPSHOT_CSV}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
