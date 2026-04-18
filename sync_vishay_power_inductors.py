from __future__ import annotations

import argparse
import html
import re
import shutil
import sqlite3
import time
from datetime import datetime
from io import StringIO
from pathlib import Path

import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait

import component_matcher_build as cmb
import sync_inductor_official_to_db as sidb


ROOT = Path(__file__).resolve().parent
OFFICIAL_CSV = ROOT / "Inductor" / "official_inductor_expansion.csv"
SNAPSHOT_CSV = ROOT / "Inductor" / "vishay_power_inductor_expansion.csv"
COMPONENTS_DB = ROOT / "components.db"
BRAND = "Vishay(威世)"
STAMP = datetime.now().strftime("%Y-%m-%d %H:%M")

PAGE_CONFIGS = [
    {
        "url": "https://www.vishay.com/en/inductors/ihlp-power-inductors/",
        "page_group": "Commercial/Industrial",
        "special_use": "Commercial/Industrial power inductor",
        "series_fallback": "Vishay commercial/industrial power inductor series",
        "authority": "vishay_ihlp_power_inductors",
    },
    {
        "url": "https://www.vishay.com/en/inductors/ihlp-power-inductors-automotive/",
        "page_group": "Automotive",
        "special_use": "Automotive power inductor",
        "series_fallback": "Vishay automotive power inductor series",
        "authority": "vishay_ihlp_power_inductors_automotive",
    },
]


def clean_text(value: object) -> str:
    if value is None:
        return ""
    try:
        if value != value:  # NaN-safe check
            return ""
    except Exception:
        pass
    text = html.unescape(str(value)).replace("\xa0", " ")
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


def current_from_milliamp(value: object) -> str:
    text = first_number_text(value)
    if not text:
        return ""
    try:
        amp = float(text) / 1000.0
    except Exception:
        return text
    formatted = f"{amp:.4f}".rstrip("0").rstrip(".")
    return formatted if formatted else "0"


def size_code_from_series(series: str, size_class: object) -> str:
    series_text = clean_text(series).upper()
    patterns = [
        r"(?<!\d)(\d{4})(?!\d)",
        r"(?<!\d)(\d{3}W)(?!\d)",
        r"(?<!\d)(\dW\d{2})(?!\d)",
    ]
    for pattern in patterns:
        match = re.search(pattern, series_text)
        if match:
            return match.group(1)

    size_text = clean_text(size_class)
    if not size_text:
        return ""
    if re.fullmatch(r"\d+\.0", size_text):
        size_text = size_text[:-2]
    return size_text


def parse_dimensions(description: str, height_fallback: str) -> tuple[str, str, str]:
    text = clean_text(description)
    if not text:
        return "", "", ""

    last_match = None
    for match in re.finditer(
        r"(\d+(?:\.\d+)?)\s*x\s*(\d+(?:\.\d+)?)(?:\s*x\s*(\d+(?:\.\d+)?(?:\s*/\s*\d+(?:\.\d+)?)?))?",
        text,
        flags=re.I,
    ):
        last_match = match

    if not last_match:
        return "", "", ""

    length = first_number_text(last_match.group(1))
    width = first_number_text(last_match.group(2))
    height = clean_text(last_match.group(3) or height_fallback)
    if height.lower() == "nan":
        height = ""
    return length, width, height


def infer_mount(series: str, description: str) -> str:
    haystack = f"{series} {description}".lower()
    if any(token in haystack for token in ["through-hole", "radial", "edge-wound", "lead", "wire wound"]):
        return "THT"
    return "SMT"


def infer_material(description: str) -> str:
    haystack = clean_text(description).lower()
    if "ferrite" in haystack:
        return "Ferrite"
    if "metal" in haystack:
        return "Metal"
    if "wire-wound" in haystack or "wire wound" in haystack:
        return "Wire Wound"
    return ""


def infer_screening(description: str) -> str:
    haystack = clean_text(description).lower()
    if "shield" in haystack:
        return "Shielded"
    if "unshield" in haystack:
        return "Unshielded"
    return ""


def format_summary(
    ind_min: str,
    ind_max: str,
    current_a: str,
    sat_current: str,
    size_code: str,
    size_mm: str,
    work_temp: str,
) -> str:
    parts: list[str] = []
    if ind_min and ind_max and ind_min != ind_max:
        parts.append(f"L={ind_min}~{ind_max}uH")
    elif ind_min:
        parts.append(f"L={ind_min}uH")
    elif ind_max:
        parts.append(f"L={ind_max}uH")
    if current_a:
        parts.append(f"Irms={current_a}A")
    if sat_current:
        parts.append(f"Isat={sat_current}A")
    if size_code:
        parts.append(f"Case={size_code}")
    if size_mm:
        parts.append(size_mm)
    if work_temp:
        parts.append(f"Temp={work_temp}")
    return " | ".join(parts)


def resolve_chrome_driver() -> str | None:
    candidates: list[Path] = []
    home = Path.home()
    for base in [
        home / ".cache" / "selenium" / "chromedriver" / "win64",
        home / ".wdm" / "drivers" / "chromedriver" / "win64",
    ]:
        if base.exists():
            candidates.extend(sorted(base.glob("*/chromedriver.exe"), reverse=True))
            candidates.extend(sorted(base.glob("*/chromedriver-win32/chromedriver.exe"), reverse=True))
    for path in candidates:
        if path.exists():
            return str(path)
    return None


def resolve_chrome_binary() -> str | None:
    candidates = [
        Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe"),
        Path(r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"),
        Path(r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"),
        Path(r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"),
    ]
    for path in candidates:
        if path.exists():
            return str(path)
    return None


def build_driver() -> webdriver.Chrome:
    options = Options()
    chrome_binary = resolve_chrome_binary()
    if chrome_binary:
        options.binary_location = chrome_binary
    options.add_argument("--headless=new")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--window-size=1600,2200")
    options.add_argument("--lang=en-US")
    driver_path = resolve_chrome_driver()
    if driver_path:
        return webdriver.Chrome(service=Service(driver_path), options=options)
    return webdriver.Chrome(options=options)


def accept_cookie_banner(driver: webdriver.Chrome) -> None:
    for label in ("Accept Necessary Cookies only", "Accept All Cookies"):
        buttons = driver.find_elements(By.XPATH, f"//button[contains(normalize-space(.), '{label}')]")
        if buttons:
            driver.execute_script("arguments[0].click();", buttons[0])
            time.sleep(1)
            return


def extract_parametric_table(driver: webdriver.Chrome) -> pd.DataFrame:
    tables = pd.read_html(StringIO(driver.page_source))
    candidates = [table for table in tables if table.shape[1] >= 8 and len(table) > 0]
    if not candidates:
        raise RuntimeError("No parametric table found on Vishay page")
    table = max(candidates, key=len).copy()
    table = table.iloc[:, :10].fillna("")
    return table


def collect_page_rows(
    driver: webdriver.Chrome,
    page_group: str,
    special_use: str,
    page_url: str,
    series_fallback: str,
    authority: str,
) -> pd.DataFrame:
    table = extract_parametric_table(driver)
    rows: list[dict[str, str]] = []
    for _, row in table.iterrows():
        series = clean_text(row.iloc[0])
        if not series:
            continue

        description = clean_text(row.iloc[2]) if len(row) > 2 else ""
        ind_min = first_number_text(row.iloc[3]) if len(row) > 3 else ""
        ind_max = first_number_text(row.iloc[4]) if len(row) > 4 else ""
        current_a = current_from_milliamp(row.iloc[5]) if len(row) > 5 else ""
        sat_current = first_number_text(row.iloc[6]) if len(row) > 6 else ""
        size_code = size_code_from_series(series, row.iloc[7] if len(row) > 7 else "")
        height_hint = clean_text(row.iloc[8]) if len(row) > 8 else ""
        work_temp = clean_text(row.iloc[9]) if len(row) > 9 else ""
        length, width, height = parse_dimensions(description, height_hint)
        size_mm = " x ".join([part for part in [length, width, height] if part]) + " mm" if any([length, width, height]) else ""
        mount = infer_mount(series, description)
        material = infer_material(description)
        shield = infer_screening(description)
        series_desc = description or series_fallback
        summary = format_summary(ind_min, ind_max, current_a, sat_current, size_code, size_mm, work_temp)

        rows.append(
            {
                "品牌": BRAND,
                "型号": series,
                "系列": series,
                "尺寸（inch）": "",
                "材质（介质）": material,
                "容值": "",
                "容值单位": "",
                "容值误差": "",
                "耐压（V）": "",
                "特殊用途": special_use,
                "备注1": f"PageGroup={page_group}",
                "备注2": page_url,
                "备注3": description or series_fallback,
                "器件类型": "功率电感",
                "安装方式": mount,
                "封装代码": size_code,
                "尺寸（mm）": size_mm,
                "规格摘要": summary,
                "生产状态": "Production",
                "长度（mm）": length,
                "宽度（mm）": width,
                "高度（mm）": height,
                "工作温度": work_temp,
                "官网链接": page_url,
                "数据来源": "Vishay official parametric table",
                "数据状态": "官方网页抽取",
                "校验时间": STAMP,
                "校验备注": f"Vishay {page_group} parametric table",
                "额定电流": current_a,
                "DCR": "",
                "电感值": ind_min or ind_max,
                "电感单位": "uH" if (ind_min or ind_max) else "",
                "电感误差": "",
                "饱和电流": sat_current,
                "屏蔽类型": shield,
                "系列说明": series_desc,
                "_model_rule_authority": authority,
            }
        )

    df = pd.DataFrame(rows).fillna("")
    if df.empty:
        return df
    return df.drop_duplicates(subset=["器件类型", "品牌", "型号"], keep="first").reset_index(drop=True)


def click_next_page(driver: webdriver.Chrome) -> bool:
    buttons = [
        btn
        for btn in driver.find_elements(By.TAG_NAME, "button")
        if "Next" in clean_text(btn.text) and btn.is_displayed()
    ]
    if not buttons:
        return False
    next_btn = buttons[0]
    if not next_btn.is_enabled():
        return False
    driver.execute_script("arguments[0].click();", next_btn)
    time.sleep(1.4)
    return True


def collect_url_rows(url: str, page_group: str, special_use: str, series_fallback: str, authority: str) -> pd.DataFrame:
    driver = build_driver()
    try:
        driver.get(url)
        WebDriverWait(driver, 20).until(lambda d: len(d.find_elements(By.CSS_SELECTOR, "tbody tr")) > 0)
        accept_cookie_banner(driver)

        all_rows: list[pd.DataFrame] = []
        while True:
            table_rows = collect_page_rows(driver, page_group, special_use, url, series_fallback, authority)
            if not table_rows.empty:
                all_rows.append(table_rows)
            if not click_next_page(driver):
                break

        if not all_rows:
            return pd.DataFrame()
        combined = pd.concat(all_rows, ignore_index=True).fillna("")
        return combined
    finally:
        driver.quit()


def merge_into_official_csv(new_rows: pd.DataFrame) -> tuple[int, int]:
    if new_rows is None or new_rows.empty:
        return 0, 0

    if OFFICIAL_CSV.exists():
        existing = pd.read_csv(OFFICIAL_CSV, encoding="utf-8-sig", low_memory=False).fillna("")
    else:
        existing = pd.DataFrame(columns=list(new_rows.columns))

    columns = list(existing.columns)
    for column in new_rows.columns:
        if column not in columns:
            columns.append(column)

    existing = existing.reindex(columns=columns, fill_value="")
    new_rows = new_rows.reindex(columns=columns, fill_value="")

    incoming_keys = {
        (clean_text(row.get("器件类型", "")), clean_text(row.get("品牌", "")), clean_text(row.get("型号", "")))
        for _, row in new_rows.iterrows()
    }
    if incoming_keys:
        existing = existing[
            ~existing.apply(
                lambda row: (
                    clean_text(row.get("器件类型", "")),
                    clean_text(row.get("品牌", "")),
                    clean_text(row.get("型号", "")),
                )
                in incoming_keys,
                axis=1,
            )
        ]

    merged = pd.concat([existing, new_rows], ignore_index=True).fillna("")
    merged = merged.drop_duplicates(subset=["器件类型", "品牌", "型号"], keep="first").reset_index(drop=True)
    merged.to_csv(OFFICIAL_CSV, index=False, encoding="utf-8-sig")
    return len(existing), len(merged)


def update_database_and_caches(module, new_rows: pd.DataFrame) -> tuple[int, int, bool, bool]:
    if new_rows is None or new_rows.empty:
        return 0, 0, False, False
    if not COMPONENTS_DB.exists():
        raise SystemExit(f"missing components db: {COMPONENTS_DB}")

    conn = sqlite3.connect(str(COMPONENTS_DB), timeout=60)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    conn.execute("PRAGMA temp_store=MEMORY")
    db_columns = [row[1] for row in conn.execute("PRAGMA table_info(components)").fetchall()]

    updated_rows = new_rows.fillna("").reindex(columns=db_columns, fill_value="")
    deleted, inserted = sidb.replace_rows(conn, updated_rows, db_columns)
    db_subset = sidb.load_official_rows_from_db(conn, updated_rows)
    conn.close()

    search_refreshed = sidb.refresh_search_sidecar_subset(module, db_subset)
    prepared_refreshed = sidb.refresh_prepared_cache_subset(module, db_subset)
    return deleted, inserted, search_refreshed, prepared_refreshed


def main() -> int:
    parser = argparse.ArgumentParser(description="Extend Vishay power inductor coverage from official parametric tables.")
    parser.add_argument("--skip-db", action="store_true", help="Only update the official CSV snapshot, skip DB/cache refresh.")
    args = parser.parse_args()

    all_rows = []
    for config in PAGE_CONFIGS:
        print(f"[vishay] scraping {config['url']} ...", flush=True)
        rows = collect_url_rows(
            config["url"],
            config["page_group"],
            config["special_use"],
            config["series_fallback"],
            config["authority"],
        )
        print(f"[vishay] {config['page_group']}: {len(rows)} rows", flush=True)
        if not rows.empty:
            all_rows.append(rows)

    if not all_rows:
        raise SystemExit("No Vishay rows were parsed.")

    df = pd.concat(all_rows, ignore_index=True).fillna("")
    df = df.drop_duplicates(subset=["器件类型", "品牌", "型号"], keep="first").reset_index(drop=True)
    df = df.sort_values(by=["器件类型", "系列", "型号"], kind="stable").reset_index(drop=True)
    df.to_csv(SNAPSHOT_CSV, index=False, encoding="utf-8-sig")
    before, after = merge_into_official_csv(df)
    print(f"[vishay] wrote snapshot: {SNAPSHOT_CSV}")
    print(f"[vishay] merged official csv: {before} -> {after}")

    if args.skip_db:
        print("[vishay] skipped DB/cache refresh by request")
        return 0

    module = cmb._load_component_matcher()
    deleted, inserted, search_refreshed, prepared_refreshed = update_database_and_caches(module, df)
    print(
        f"[vishay] db deleted={deleted} inserted={inserted} "
        f"search_refreshed={search_refreshed} prepared_refreshed={prepared_refreshed}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
