from __future__ import annotations

import html
import json
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd
import requests


ROOT = Path(__file__).resolve().parent
OFFICIAL_CSV = ROOT / "Inductor" / "official_inductor_expansion.csv"
SNAPSHOT_CSV = ROOT / "Inductor" / "chilisin_inductor_tree_expansion.csv"
SOURCE_URL = "https://www.chilisin.com/en-global/Inductor/index/power?pro_type=2"
STAMP = datetime.now().strftime("%Y-%m-%d %H:%M")
BRAND = "Chilisin"


def clean_text(value: object) -> str:
    if value is None:
        return ""
    try:
        if value != value:
            return ""
    except Exception:
        pass
    text = html.unescape(str(value)).replace("\xa0", " ")
    text = re.sub(r"\s+", " ", text).strip()
    return "" if text.lower() == "nan" else text


def extract_flight_chunk(source_html: str) -> str:
    needle = 'self.__next_f.push([1,"'
    idx = 0
    while True:
        start = source_html.find(needle, idx)
        if start == -1:
            raise RuntimeError("unable to locate Chilisin flight payload")
        start += len(needle)
        i = start
        escaped = False
        buf: list[str] = []
        while i < len(source_html):
            ch = source_html[i]
            if escaped:
                buf.append(ch)
                escaped = False
            elif ch == "\\":
                buf.append(ch)
                escaped = True
            elif ch == '"' and source_html[i + 1 : i + 3] == "])":
                break
            else:
                buf.append(ch)
            i += 1
        decoded = bytes("".join(buf), "utf-8").decode("unicode_escape")
        if "initialDefinitions" in decoded:
            return decoded
        idx = i + 3


def extract_initial_definitions(flight_chunk: str) -> list[dict]:
    key_pos = flight_chunk.find("initialDefinitions")
    if key_pos == -1:
        raise RuntimeError("missing initialDefinitions in Chilisin flight payload")
    start = flight_chunk.find("[", key_pos)
    if start == -1:
        raise RuntimeError("missing initialDefinitions array")

    depth = 0
    in_string = False
    escaped = False
    end = None
    for offset, ch in enumerate(flight_chunk[start:]):
        if in_string:
            if escaped:
                escaped = False
            elif ch == "\\":
                escaped = True
            elif ch == '"':
                in_string = False
        else:
            if ch == '"':
                in_string = True
            elif ch == "[":
                depth += 1
            elif ch == "]":
                depth -= 1
                if depth == 0:
                    end = offset + 1
                    break
    if end is None:
        raise RuntimeError("failed to balance initialDefinitions array")
    return json.loads(flight_chunk[start : start + end])


def walk_leaves(node: dict, path: tuple[str, ...] = ()) -> list[tuple[dict, tuple[str, ...]]]:
    current_path = path + (clean_text(node.get("name", "")),)
    children = node.get("childDefinitions") or []
    if children:
        items: list[tuple[dict, tuple[str, ...]]] = []
        for child in children:
            items.extend(walk_leaves(child, current_path))
        return items
    return [(node, current_path)]


def series_codes(node: dict) -> list[str]:
    codes: list[str] = []
    for image in node.get("seriesImages") or []:
        value = clean_text((image.get("seriesParameterValue") or {}).get("value", ""))
        if value and value not in codes:
            codes.append(value)
    return codes


def classify_node(breadcrumb: str) -> tuple[str, str, str, str]:
    text = breadcrumb.lower()
    leaf = clean_text(breadcrumb.split("->")[-1] if "->" in breadcrumb else breadcrumb)

    if "common mode chokes" in text or "dual mode chokes" in text:
        return "共模电感", "SMT" if "through-hole" not in text else "THT", "Ferrite", leaf
    if "differential mode chokes" in text:
        return "共模电感", "SMT" if "through-hole" not in text else "THT", "Ferrite", leaf
    if "emi filters" in text:
        return "共模电感", "SMT", "", leaf
    if "emi suppression" in text:
        return "磁珠", "SMT", "", leaf
    if "rf signal" in text:
        material = "Ceramic" if "ceramic" in text else ("Ferrite" if "ferrite" in text else "")
        return "射频电感", "SMT" if "through-hole" not in text else "THT", material, leaf
    if "power" in text:
        if "power bead" in text:
            return "磁珠", "SMT" if "through-hole" not in text else "THT", "Ferrite", leaf
        if "molded" in text or "metal composite" in text:
            return "功率电感", "SMT" if "through-hole" not in text else "THT", "Metal Composite", leaf
        if "planar" in text:
            return "功率电感", "SMT", "Ferrite", leaf
        if "toroidal" in text:
            return "功率电感", "SMT" if "through-hole" not in text else "THT", "Ferrite", leaf
        if "drum" in text or "shape" in text or "chip" in text or "multi-layer" in text:
            material = "Ceramic" if "ceramic" in text else ("Ferrite" if "ferrite" in text else "")
            return "功率电感", "SMT" if "through-hole" not in text else "THT", material, leaf
        return "功率电感", "SMT" if "through-hole" not in text else "THT", "", leaf
    return "电感", "SMT", "", leaf


def blank_row(columns: list[str]) -> dict[str, str]:
    return {column: "" for column in columns}


def set_if_present(row: dict[str, str], column_names: list[str], value: str) -> None:
    for name in column_names:
        if name in row:
            row[name] = value
            return


def build_rows(columns: list[str]) -> pd.DataFrame:
    response = requests.get(
        SOURCE_URL,
        timeout=120,
        headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0.0.0 Safari/537.36",
            "Accept-Language": "en-US,en;q=0.9",
        },
    )
    response.raise_for_status()
    flight_chunk = extract_flight_chunk(response.text)
    definitions = extract_initial_definitions(flight_chunk)

    seen_models: set[str] = set()
    rows: list[dict[str, str]] = []
    for root in definitions:
        for node, _path in walk_leaves(root):
            breadcrumb = clean_text(node.get("nameBreadcrumb", ""))
            if not breadcrumb:
                continue
            if breadcrumb.startswith("Engineering Kits"):
                continue
            if "Inductors" not in breadcrumb and not breadcrumb.startswith("EMC") and "EMI" not in breadcrumb:
                continue

            part_count = clean_text(node.get("partCount", ""))
            codes = series_codes(node)
            if not codes:
                continue

            component_type, mount, material, leaf_name = classify_node(breadcrumb)
            series_desc = f"Chilisin official tree: {breadcrumb}"
            summary = f"{component_type} | {leaf_name} | codes={len(codes)}"
            if part_count:
                summary = f"{summary} | parts={part_count}"

            for code in codes:
                if code in seen_models:
                    continue
                seen_models.add(code)

                row = blank_row(columns)
                set_if_present(row, ["品牌"], BRAND)
                set_if_present(row, ["型号"], code)
                set_if_present(row, ["系列"], leaf_name)
                set_if_present(row, ["尺寸（inch）"], "")
                set_if_present(row, ["材质（介质）"], material)
                set_if_present(row, ["容值"], "")
                set_if_present(row, ["容值单位"], "")
                set_if_present(row, ["容值误差"], "")
                set_if_present(row, ["耐压（V）"], "")
                set_if_present(row, ["特殊用途"], leaf_name)
                set_if_present(row, ["备注1"], "Chilisin official tree")
                set_if_present(row, ["备注2"], f"partCount={part_count}" if part_count else "")
                set_if_present(row, ["备注3"], breadcrumb)
                set_if_present(row, ["器件类型"], component_type)
                set_if_present(row, ["安装方式"], mount)
                set_if_present(row, ["封装代码"], "")
                set_if_present(row, ["尺寸（mm）"], "")
                set_if_present(row, ["规格摘要"], summary)
                set_if_present(row, ["生产状态"], "Production")
                set_if_present(row, ["长度（mm）"], "")
                set_if_present(row, ["宽度（mm）"], "")
                set_if_present(row, ["高度（mm）"], "")
                set_if_present(row, ["官网链接"], SOURCE_URL)
                set_if_present(row, ["数据来源"], "Chilisin official Next.js tree")
                set_if_present(row, ["数据状态"], "官方网页抽取")
                set_if_present(row, ["校验时间"], STAMP)
                set_if_present(row, ["校验备注"], f"breadcrumb={breadcrumb} | partCount={part_count}")
                set_if_present(row, ["额定电流"], "")
                set_if_present(row, ["DCR"], "")
                set_if_present(row, ["电感值"], "")
                set_if_present(row, ["电感单位"], "")
                set_if_present(row, ["电感误差"], "")
                set_if_present(row, ["饱和电流"], "")
                set_if_present(row, ["屏蔽类型"], "")
                set_if_present(row, ["系列说明"], series_desc)
                set_if_present(row, ["_model_rule_authority"], "chilisin_inductor_tree")
                rows.append(row)

    if not rows:
        return pd.DataFrame(columns=columns)

    frame = pd.DataFrame(rows, columns=columns).fillna("")
    frame = frame.drop_duplicates(subset=["品牌", "型号", "器件类型"], keep="first").reset_index(drop=True)
    return frame


def merge_official_csv(new_rows: pd.DataFrame) -> int:
    if not OFFICIAL_CSV.exists():
        raise SystemExit(f"missing official csv: {OFFICIAL_CSV}")
    existing = pd.read_csv(OFFICIAL_CSV, encoding="utf-8-sig").fillna("")
    if existing.empty:
        merged = new_rows.copy()
    else:
        brand_mask = existing["品牌"].astype(str).str.contains("Chilisin", case=False, na=False)
        remaining = existing[~brand_mask].copy()
        merged = pd.concat([remaining, new_rows], ignore_index=True)
        merged = merged.drop_duplicates(subset=["品牌", "型号", "器件类型"], keep="last").reset_index(drop=True)
        merged = merged.reindex(columns=list(existing.columns)).fillna("")
    merged.to_csv(OFFICIAL_CSV, index=False, encoding="utf-8-sig")
    return int(len(merged))


def refresh_database() -> None:
    subprocess.run([sys.executable, str(ROOT / "sync_inductor_official_to_db.py")], check=True)


def main() -> int:
    if not OFFICIAL_CSV.exists():
        raise SystemExit(f"missing official csv: {OFFICIAL_CSV}")

    existing_columns = pd.read_csv(OFFICIAL_CSV, nrows=0, encoding="utf-8-sig").columns.tolist()
    new_rows = build_rows(existing_columns)
    if new_rows.empty:
        raise SystemExit("no Chilisin inductor rows were extracted")

    new_rows.to_csv(SNAPSHOT_CSV, index=False, encoding="utf-8-sig")
    merged_total = merge_official_csv(new_rows)
    refresh_database()

    print(f"chilisin_rows={len(new_rows)} merged_total={merged_total} snapshot={SNAPSHOT_CSV}")
    print(new_rows.loc[:, ["品牌", "型号", "器件类型", "系列", "系列说明"]].head(10).to_string(index=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
