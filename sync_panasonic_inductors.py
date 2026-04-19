from __future__ import annotations

from datetime import datetime
from io import BytesIO
from pathlib import Path
import html as html_lib
import io
import re
import subprocess
import sys
import zipfile

import pandas as pd
from pypdf import PdfReader
from playwright.sync_api import sync_playwright


ROOT = Path(__file__).resolve().parent
OFFICIAL_CSV = ROOT / "Inductor" / "official_inductor_expansion.csv"
SNAPSHOT_CSV = ROOT / "Inductor" / "panasonic_inductor_expansion.csv"
PCC_ZIP_URL = "https://industrial.panasonic.com/content/data/CC/files/PCC_Spara.zip"
COMMON_ZIP_URL = "https://industrial.panasonic.com/content/data/CC/files/Common_Spara.zip"
PCC_ZIP_CACHE = ROOT / "cache" / "panasonic_PCC_Spara.zip"
COMMON_ZIP_CACHE = ROOT / "cache" / "panasonic_Common_Spara.zip"
POWER_MODEL_PAGE = "https://industrial.panasonic.com/ww/products/pt/automotive-inductors/models/{part}"
COMMON_MODEL_PAGE = "https://industrial.panasonic.com/ww/products/pt/noise-filters/models/{part}"
BRAND = "Panasonic(松下)"
STAMP = datetime.now().strftime("%Y-%m-%d %H:%M")
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}

OFFICIAL_COLUMNS = pd.read_csv(OFFICIAL_CSV, nrows=0, encoding="utf-8-sig").columns.tolist()


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


def download_zip(url: str) -> zipfile.ZipFile:
    cache_path = PCC_ZIP_CACHE if url == PCC_ZIP_URL else COMMON_ZIP_CACHE if url == COMMON_ZIP_URL else None
    if cache_path is not None and cache_path.exists():
        return zipfile.ZipFile(cache_path)

    last_error: Exception | None = None
    for attempt in range(1, 4):
        with sync_playwright() as p:
            print(f"[panasonic] browser start attempt={attempt} url={url}", flush=True)
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(user_agent=HEADERS["User-Agent"])
            try:
                print(f"[panasonic] request start attempt={attempt} url={url}", flush=True)
                response = context.request.get(url, timeout=600000)
                if response.status != 200:
                    raise RuntimeError(f"Panasonic zip request failed: HTTP {response.status}")
                print(f"[panasonic] request ok attempt={attempt} url={url} bytes={len(response.body())}", flush=True)
                return zipfile.ZipFile(BytesIO(response.body()))
            except Exception as exc:
                last_error = exc
                if attempt < 3:
                    continue
            finally:
                browser.close()
    raise RuntimeError(f"failed to download Panasonic zip {url}: {last_error}")


def derive_power_series(part_number: str) -> str:
    part = clean_text(part_number).upper()
    if re.match(r"^ETQP", part):
        return re.sub(r"[A-Z]{3}$", "", part)
    return part


def derive_common_series(part_number: str) -> str:
    part = clean_text(part_number).upper()
    return re.sub(r"\d+[A-Z]$", "", part)


def value_with_unit(value: object, unit: str) -> tuple[str, str]:
    number = first_number_text(value)
    return number, unit if number else ""


def parse_power_pdf(pdf_bytes: bytes, source_url: str, archive_name: str) -> dict[str, str] | None:
    reader = PdfReader(io.BytesIO(pdf_bytes))
    if not reader.pages:
        return None
    text = clean_text(reader.pages[0].extract_text() or "")
    normalized = re.sub(r"\s+", " ", text)

    match = re.search(
        r"(?P<size>\d+(?:\.\d+)?mm square)\s+(?P<part>[A-Z0-9]+)\s+(?P<L1>[0-9.]+)u\s+(?P<C1>[0-9.]+)p\s+(?P<R2>[0-9.]+)\s+(?P<R1>[0-9.]+)",
        normalized,
        flags=re.I,
    )
    if not match:
        part_match = re.search(r"\b([A-Z]{3,}[A-Z0-9]{4,})\b", normalized)
        if not part_match:
            return None
        part_number = clean_text(part_match.group(1))
        size_mm = ""
        l1 = c1 = r2 = r1 = ""
    else:
        part_number = clean_text(match.group("part"))
        size_mm = clean_text(match.group("size"))
        l1 = first_number_text(match.group("L1"))
        c1 = first_number_text(match.group("C1"))
        r2 = first_number_text(match.group("R2"))
        r1 = first_number_text(match.group("R1"))

    series = derive_power_series(part_number)
    title = "Power Choke Coils for Automotive application"
    summary_parts = []
    if l1:
        summary_parts.append(f"L1={l1}uH")
    if c1:
        summary_parts.append(f"C1={c1}pF")
    if r2:
        summary_parts.append(f"R2={r2}Ω")
    if r1:
        summary_parts.append(f"R1={r1}Ω")
    if size_mm:
        summary_parts.append(size_mm)
    summary_parts.append(title)

    row = {column: "" for column in OFFICIAL_COLUMNS}
    row.update(
        {
            "品牌": BRAND,
            "型号": part_number,
            "系列": series,
            "特殊用途": "Automotive",
            "备注1": f"Source archive: {archive_name}",
            "备注2": f"Model PDF: {part_number}",
            "备注3": f"Power model page: {POWER_MODEL_PAGE.format(part=part_number)}",
            "器件类型": "功率电感",
            "安装方式": "SMT",
            "封装代码": series,
            "尺寸（mm）": size_mm,
            "规格摘要": " | ".join(summary_parts),
            "生产状态": "Production",
            "官网链接": POWER_MODEL_PAGE.format(part=part_number),
            "数据来源": "Panasonic official PCC_Spara zip",
            "数据状态": "官方PDF抽取",
            "校验时间": STAMP,
            "校验备注": f"Panasonic PCC_Spara | {archive_name}",
            "电感值": l1,
            "电感单位": "uH" if l1 else "",
            "系列说明": title,
            "_model_rule_authority": "panasonic_pcc_spara",
            "_body_size": size_mm,
        }
    )
    return row


def parse_common_sub(sub_bytes: bytes, archive_name: str) -> dict[str, str] | None:
    text = sub_bytes.decode("utf-8", errors="replace")
    title_match = re.search(r"^\*\s*(Common mode Noise Filters|2 mode Filters)\s*$", text, flags=re.I | re.M)
    title = clean_text(title_match.group(1)) if title_match else "Common mode Noise Filters"
    part_match = re.search(r"Parts No\.?\s*([A-Z0-9]+)", text, flags=re.I)
    subckt_match = re.search(r"\.SUBCKT\s+([A-Z0-9]+)", text, flags=re.I)
    part_number = clean_text(part_match.group(1) if part_match else (subckt_match.group(1) if subckt_match else ""))
    if not part_number:
        return None

    params = {
        key.upper(): clean_text(value)
        for key, value in re.findall(r"^\s*\.PARAM\s+([A-Za-z0-9_]+)\s*=\s*([^\r\n]+)", text, flags=re.I | re.M)
    }
    series = derive_common_series(part_number)

    size_hint = ""
    inductance_value = ""
    inductance_unit = ""
    for candidate in ("LT1", "LT", "TRANS_IND", "TRANS_IND1"):
        if candidate in params:
            inductance_value = first_number_text(params[candidate])
            if "n" in params[candidate].lower():
                inductance_unit = "nH"
            elif "u" in params[candidate].lower():
                inductance_unit = "uH"
            elif "p" in params[candidate].lower():
                inductance_unit = "pH"
            break

    summary_parts = [title]
    for key in ("CT1", "RT21", "RT1", "LT1", "RT", "RT2", "Trans_R1", "Trans_R2", "LT", "Trans_Ind", "Trans_Ind1", "Trans_Ind2", "K1_2", "K1", "K2", "C1", "C3", "R1", "R2", "R3", "CG", "CG2", "CB1", "CB2", "Trans_C1", "Trans_C2"):
        if key in params and params[key]:
            summary_parts.append(f"{key}={params[key]}")

    row = {column: "" for column in OFFICIAL_COLUMNS}
    row.update(
        {
            "品牌": BRAND,
            "型号": part_number,
            "系列": series,
            "特殊用途": "EMI/Noise filter" if "2 mode" not in title.lower() else "2 mode filter",
            "备注1": f"Source archive: {archive_name}",
            "备注2": f"Top title: {title}",
            "备注3": f"Model page: {COMMON_MODEL_PAGE.format(part=part_number)}",
            "器件类型": "共模电感",
            "安装方式": "SMT",
            "封装代码": series,
            "尺寸（mm）": size_hint,
            "规格摘要": " | ".join(summary_parts),
            "生产状态": "Production",
            "官网链接": COMMON_MODEL_PAGE.format(part=part_number),
            "数据来源": "Panasonic official Common_Spara zip",
            "数据状态": "官方SPICE抽取",
            "校验时间": STAMP,
            "校验备注": f"Panasonic Common_Spara | {archive_name}",
            "电感值": inductance_value,
            "电感单位": inductance_unit,
            "系列说明": title,
            "_model_rule_authority": "panasonic_common_spara",
            "_body_size": size_hint,
        }
    )
    return row


def collect_power_rows(zf: zipfile.ZipFile) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for name in sorted(n for n in zf.namelist() if n.lower().endswith(".pdf")):
        folder = Path(name).parent.name
        pdf_bytes = zf.read(name)
        row = parse_power_pdf(pdf_bytes, f"{PCC_ZIP_URL}#{name}", folder)
        if row:
            rows.append(row)
    return rows


def collect_common_rows(zf: zipfile.ZipFile) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for name in sorted(n for n in zf.namelist() if n.lower().endswith(".sub")):
        folder = Path(name).parent.name
        sub_bytes = zf.read(name)
        row = parse_common_sub(sub_bytes, folder)
        if row:
            rows.append(row)
    return rows


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
    print("[panasonic] downloading power zip", flush=True)
    power_zip = download_zip(PCC_ZIP_URL)
    print("[panasonic] downloading common zip", flush=True)
    common_zip = download_zip(COMMON_ZIP_URL)

    rows = []
    print("[panasonic] parsing power rows", flush=True)
    rows.extend(collect_power_rows(power_zip))
    print("[panasonic] parsing common rows", flush=True)
    rows.extend(collect_common_rows(common_zip))

    if not rows:
        raise SystemExit("no Panasonic inductor rows found")

    df = pd.DataFrame(rows).fillna("")
    df = df.drop_duplicates(subset=["品牌", "型号", "器件类型"], keep="first").reset_index(drop=True)
    print(f"[panasonic] parsed rows={len(df)}", flush=True)
    print("[panasonic] writing snapshot", flush=True)
    df.to_csv(SNAPSHOT_CSV, index=False, encoding="utf-8-sig")

    print("[panasonic] merging official csv", flush=True)
    before_count, after_count = merge_into_official_csv(df)
    print("[panasonic] refreshing db/cache", flush=True)
    run_db_refresh()

    print(f"snapshot_rows={len(df)} official_before={before_count} official_after={after_count}")
    print(f"snapshot={SNAPSHOT_CSV}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
