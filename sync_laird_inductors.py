from __future__ import annotations

from datetime import datetime
from io import StringIO
from pathlib import Path
from urllib.parse import urljoin
from concurrent.futures import ThreadPoolExecutor, as_completed
import html as html_lib
import re
import subprocess
import sys

import pandas as pd
import requests


ROOT = Path(__file__).resolve().parent
OFFICIAL_CSV = ROOT / "Inductor" / "official_inductor_expansion.csv"
SNAPSHOT_CSV = ROOT / "Inductor" / "laird_inductor_power_and_signal_expansion.csv"
ROOT_URL = "https://www.laird.com/products/inductive-components-inductors-for-power-and-signal-lines"
STAMP = datetime.now().strftime("%Y-%m-%d %H:%M")
BRAND = "Laird(莱尔德)"
OFFICIAL_COLUMNS = pd.read_csv(OFFICIAL_CSV, nrows=0, encoding="utf-8-sig").columns.tolist()
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}


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


def extract_links(page_html: str, base_url: str) -> list[str]:
    links: list[str] = []
    seen: set[str] = set()
    for href in re.findall(r'href="([^"]+)"', page_html, flags=re.I):
        absolute = urljoin(base_url, html_lib.unescape(href))
        if absolute in seen:
            continue
        seen.add(absolute)
        links.append(absolute)
    return links


def discover_category_pages(session: requests.Session) -> list[str]:
    root_html = session.get(ROOT_URL, timeout=120).text
    category_pages: list[str] = []
    for link in extract_links(root_html, ROOT_URL):
        if link.startswith(ROOT_URL + "/") and not link.endswith("#") and not link.endswith("#main-content"):
            if link not in category_pages:
                category_pages.append(link)
    return category_pages


def discover_series_pages(session: requests.Session, category_pages: list[str]) -> list[str]:
    series_pages: list[str] = []
    seen: set[str] = set()
    for category_page in category_pages:
        page_html = session.get(category_page, timeout=120).text
        for link in extract_links(page_html, category_page):
            if not link.startswith(ROOT_URL + "/"):
                continue
            if link.endswith("#") or link.endswith("#main-content"):
                continue
            if link in category_pages:
                continue
            if link in seen:
                continue
            seen.add(link)
            series_pages.append(link)
    return series_pages


def page_mode_from_url(url: str) -> tuple[str, str, str, str]:
    path = url.split("://", 1)[-1].split("/", 1)[-1].lower()
    if "wire-wound-surface-mount-ceramic-chip-inductor" in path:
        return "射频电感", "SMT", "Ceramic", ""
    if "wire-wound-smt-power-inductor" in path:
        return "功率电感", "SMT", "", ""
    if "molded-smt-power-inductor" in path:
        return "功率电感", "SMT", "Metal Composite", "Magnetically Shielded Type"
    return "功率电感", "SMT", "", ""


def series_slug_from_url(url: str) -> str:
    return url.rstrip("/").split("/")[-1].upper()


def series_code_from_url(url: str) -> str:
    slug = series_slug_from_url(url)
    match = re.search(r"(\d{3,6})$", slug)
    return match.group(1) if match else slug


def find_table(tables: list[pd.DataFrame]) -> pd.DataFrame | None:
    for table in tables:
        columns = [clean_text(col) for col in table.columns]
        if any(col == "Part Number" for col in columns):
            table = table.copy().fillna("")
            table.columns = columns
            return table
    return None


def parse_series_html(url: str, html: str) -> pd.DataFrame:
    tables = pd.read_html(StringIO(html))
    table = find_table(tables)
    if table is None or table.empty:
        return pd.DataFrame()

    component_type, mount, material, shield_type = page_mode_from_url(url)
    series_slug = series_slug_from_url(url)
    series_code = series_code_from_url(url)
    part_name = clean_text(table.iloc[0].get("Part Name", "")) if "Part Name" in table.columns else ""

    current_col = ""
    for candidate in ("HEAT RATED CURRENT (Irms) (A) Typ.", "Rated Current (A) Max"):
        if candidate in table.columns:
            current_col = candidate
            break

    sat_col = ""
    for candidate in ("Saturation Current(Isat) (A) Typ .", "Saturation Current (A) Typ.", "Saturation Current"):
        if candidate in table.columns:
            sat_col = candidate
            break

    q_col = "Q (MIN)" if "Q (MIN)" in table.columns else ""
    srf_col = "SRF MHZ(REF)" if "SRF MHZ(REF)" in table.columns else ""

    rows: list[dict[str, str]] = []
    for _, src in table.iterrows():
        part_number = clean_text(src.get("Part Number", ""))
        if not part_number:
            continue

        inductance = first_number_text(src.get("Inductance (µH)", ""))
        current = first_number_text(src.get(current_col, "")) if current_col else ""
        saturation = first_number_text(src.get(sat_col, "")) if sat_col else ""
        dcr = first_number_text(src.get("DCR (Ω) Max", ""))
        q_min = first_number_text(src.get(q_col, "")) if q_col else ""
        srf = first_number_text(src.get(srf_col, "")) if srf_col else ""
        length = first_number_text(src.get("Length (mm)", ""))
        width = first_number_text(src.get("Width(mm)", src.get("Width (mm)", "")))
        height = first_number_text(src.get("Height/Thickness (mm)", ""))
        size_mm = " x ".join([value for value in (length, width, height) if value])
        summary_parts: list[str] = []
        if inductance:
            summary_parts.append(f"L={inductance}uH")
        if current:
            summary_parts.append(f"I={current}A")
        if saturation and saturation != current:
            summary_parts.append(f"Isat={saturation}A")
        if dcr:
            summary_parts.append(f"DCR={dcr}Ω")
        if q_min:
            summary_parts.append(f"Qmin={q_min}")
        if srf:
            summary_parts.append(f"SRF={srf}MHz")
        if size_mm:
            summary_parts.append(size_mm)

        row = {column: "" for column in OFFICIAL_COLUMNS}
        row.update(
            {
                "品牌": BRAND,
                "型号": part_number,
                "系列": series_slug,
                "材质（介质）": material,
                "特殊用途": part_name or ("Power Inductor" if component_type == "功率电感" else "Chip Inductor"),
                "备注1": f"Part Name: {part_name}" if part_name else "",
                "备注2": f"Source: {series_slug}",
                "备注3": f"Laird series page: {url}",
                "器件类型": component_type,
                "安装方式": mount,
                "封装代码": series_code,
                "尺寸（mm）": size_mm,
                "规格摘要": " | ".join(summary_parts),
                "生产状态": "Production",
                "长度（mm）": length,
                "宽度（mm）": width,
                "高度（mm）": height,
                "官网链接": url,
                "数据来源": "Laird official series table",
                "数据状态": "官方网页抽取",
                "校验时间": STAMP,
                "校验备注": f"Laird {series_slug}",
                "额定电流": current,
                "DCR": dcr,
                "电感值": inductance,
                "电感单位": "uH" if inductance else "",
                "饱和电流": saturation,
                "屏蔽类型": shield_type,
                "系列说明": part_name or f"Laird {series_code}",
                "_model_rule_authority": url,
                "_body_size": size_mm,
            }
        )
        rows.append(row)

    if not rows:
        return pd.DataFrame()
    df = pd.DataFrame(rows).fillna("")
    df = df.drop_duplicates(subset=["品牌", "型号", "器件类型"], keep="first").reset_index(drop=True)
    return df


def fetch_and_parse_series_page(url: str) -> tuple[str, pd.DataFrame]:
    html = requests.get(url, headers=HEADERS, timeout=45).text
    return url, parse_series_html(url, html)


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

    session = requests.Session()
    session.headers.update(HEADERS)

    category_pages = discover_category_pages(session)
    series_pages = discover_series_pages(session, category_pages)

    frames: list[pd.DataFrame] = []
    with ThreadPoolExecutor(max_workers=8) as executor:
        future_map = {executor.submit(fetch_and_parse_series_page, url): url for url in series_pages}
        for future in as_completed(future_map):
            url = future_map[future]
            try:
                _, frame = future.result()
            except Exception as exc:
                print(f"[laird] skip {url}: {exc}")
                continue
            if not frame.empty:
                frames.append(frame)

    if not frames:
        raise SystemExit("No Laird inductor rows were parsed.")

    rows = pd.concat(frames, ignore_index=True).fillna("")
    rows = rows.drop_duplicates(subset=["品牌", "型号", "器件类型"], keep="first").reset_index(drop=True)
    rows.to_csv(SNAPSHOT_CSV, index=False, encoding="utf-8-sig")
    before, after = merge_into_official_csv(rows)
    refresh_runtime(SNAPSHOT_CSV)
    print(f"[laird] series_pages={len(series_pages)} rows={len(rows)} merged={before}->{after} snapshot={SNAPSHOT_CSV}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
