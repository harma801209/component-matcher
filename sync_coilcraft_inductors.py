from __future__ import annotations

from datetime import datetime
from pathlib import Path
import html
import re
import subprocess
import sys

import fitz
import pandas as pd
import requests


ROOT = Path(__file__).resolve().parent
OFFICIAL_CSV = ROOT / "Inductor" / "official_inductor_expansion.csv"
SNAPSHOT_CSV = ROOT / "Inductor" / "coilcraft_inductor_expansion.csv"
CACHE_DIR = ROOT / "cache"
STAMP = datetime.now().strftime("%Y-%m-%d %H:%M")
BRAND = "Coilcraft"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}

OFFICIAL_COLUMNS = pd.read_csv(OFFICIAL_CSV, nrows=0, encoding="utf-8-sig").columns.tolist()

PDF_CONFIGS = [
    {
        "code": "xal7050",
        "series_code": "XAL7050",
        "pdf_url": "https://www.coilcraft.com/pdfs/xal7050.pdf",
        "family_label": "Shielded Power Inductors",
        "material_fallback": "Composite",
        "component_type": "功率电感",
        "mount": "SMT",
        "inductance_unit": "µH",
        "expected_tokens": 7,
        "parser_kind": "power_dual_dcr",
        "part_regex": r"^XAL7050-[A-Z0-9_]+$",
    },
    {
        "code": "xal4020",
        "series_code": "XAL4020",
        "pdf_url": "https://www.coilcraft.com/pdfs/xal4020.pdf",
        "family_label": "Shielded Power Inductors",
        "material_fallback": "Composite",
        "component_type": "功率电感",
        "mount": "SMT",
        "inductance_unit": "µH",
        "expected_tokens": 7,
        "parser_kind": "power_dual_dcr",
        "part_regex": r"^XAL4020-[A-Z0-9_]+$",
    },
    {
        "code": "xel4020",
        "series_code": "XEL4020",
        "pdf_url": "https://www.coilcraft.com/pdfs/xel4020.pdf",
        "family_label": "Shielded Power Inductors",
        "material_fallback": "Composite",
        "component_type": "功率电感",
        "mount": "SMT",
        "inductance_unit": "µH",
        "expected_tokens": 7,
        "parser_kind": "power_dual_dcr",
        "part_regex": r"^XEL4020-[A-Z0-9_]+$",
    },
    {
        "code": "xfl4020",
        "series_code": "XFL4020",
        "pdf_url": "https://www.coilcraft.com/pdfs/xfl4020.pdf",
        "family_label": "Shielded Power Inductors",
        "material_fallback": "Composite",
        "component_type": "功率电感",
        "mount": "SMT",
        "inductance_unit": "µH",
        "expected_tokens": 7,
        "parser_kind": "power_dual_dcr",
        "part_regex": r"^XFL4020-[A-Z0-9_]+$",
    },
    {
        "code": "xgl4020",
        "series_code": "XGL4020",
        "pdf_url": "https://www.coilcraft.com/pdfs/xgl4020.pdf",
        "family_label": "Shielded Power Inductors",
        "material_fallback": "Composite",
        "component_type": "功率电感",
        "mount": "SMT",
        "inductance_unit": "µH",
        "expected_tokens": 7,
        "parser_kind": "power_dual_dcr",
        "part_regex": r"^XGL4020-[A-Z0-9_]+$",
    },
    {
        "code": "lps6235",
        "series_code": "LPS6235",
        "pdf_url": "https://www.coilcraft.com/pdfs/lps6235.pdf",
        "family_label": "Shielded Power Inductors",
        "material_fallback": "Ferrite",
        "component_type": "功率电感",
        "mount": "SMT",
        "inductance_unit": "µH",
        "expected_tokens": 8,
        "parser_kind": "lps6235",
        "part_regex": r"^LPS6235-[A-Z0-9_]+$",
    },
    {
        "code": "lpo6013",
        "series_code": "LPO6013",
        "pdf_url": "https://www.coilcraft.com/pdfs/lpo6013.pdf",
        "family_label": "SMT Power Inductors",
        "material_fallback": "Ferrite",
        "component_type": "功率电感",
        "mount": "SMT",
        "inductance_unit": "µH",
        "expected_tokens": 5,
        "parser_kind": "lpo6013",
        "part_regex": r"^LPO6013-[A-Z0-9_]+$",
    },
    {
        "code": "mss7341",
        "series_code": "MSS7341",
        "pdf_url": "https://www.coilcraft.com/pdfs/mss7341.pdf",
        "family_label": "Shielded Power Inductors",
        "material_fallback": "Ferrite",
        "component_type": "功率电感",
        "mount": "SMT",
        "inductance_unit": "µH",
        "expected_tokens": 10,
        "parser_kind": "mss7341",
        "part_regex": r"^MSS7341-[A-Z0-9_]+$",
    },
    {
        "code": "ser2000",
        "series_code": "SER2000",
        "pdf_url": "https://www.coilcraft.com/pdfs/ser2000.pdf",
        "family_label": "Shielded Power Inductors",
        "material_fallback": "Ferrite",
        "component_type": "功率电感",
        "mount": "SMT",
        "inductance_unit": "µH",
        "expected_tokens": 8,
        "parser_kind": "ser2000",
        "part_regex": r"^SER\d{4}-[A-Z0-9_]+$",
    },
]


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


def extract_tokens(line: str) -> list[str]:
    text = clean_text(line)
    if not text:
        return []
    text = re.sub(r"±\s*\d+(?:[.,]\d+)?%", "", text)
    return re.findall(r"[-+]?\d+(?:[.,]\d+)?", text)


def download_pdf(config: dict) -> bytes | None:
    cache_path = CACHE_DIR / f"coilcraft_{config['code']}.pdf"
    if cache_path.exists():
        return cache_path.read_bytes()

    response = requests.get(config["pdf_url"], headers=HEADERS, timeout=90)
    if response.status_code != 200:
        print(f"[coilcraft] skip {config['series_code']} status={response.status_code}", flush=True)
        return None
    content_type = response.headers.get("content-type", "")
    if "pdf" not in content_type.lower() and not response.content.startswith(b"%PDF"):
        print(f"[coilcraft] skip {config['series_code']} content_type={content_type}", flush=True)
        return None
    cache_path.write_bytes(response.content)
    return response.content


def extract_title_line(text: str, fallback: str) -> str:
    for raw_line in text.splitlines():
        line = clean_text(raw_line)
        if not line:
            continue
        if "Power Inductors" in line or "Chip Inductors" in line:
            return line
    return fallback


def extract_core_material(text: str, fallback: str) -> str:
    match = re.search(r"Core material\s+([A-Za-z][A-Za-z -]*)", text, flags=re.I)
    if match:
        return clean_text(match.group(1)) or fallback
    return fallback


def parse_pdf_rows(config: dict, pdf_bytes: bytes) -> pd.DataFrame:
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    collected: list[dict[str, object]] = []
    preview_texts: list[str] = []
    part_prefix = "SER" if config["series_code"] == "SER2000" else f"{config['series_code']}-"

    for page_index in range(doc.page_count):
        text = doc.load_page(page_index).get_text("text")
        if page_index < 2:
            preview_texts.append(text)

        in_table = False
        current: dict[str, object] | None = None
        for raw_line in text.splitlines():
            line = clean_text(raw_line)
            if not line:
                continue

            if not in_table:
                if re.search(r"Part number", line, flags=re.I):
                    in_table = True
                continue

            if re.search(r"Part number", line, flags=re.I):
                continue

            if line.startswith(part_prefix) and "-" in line:
                parts = line.split(maxsplit=1)
                part = clean_text(parts[0]).rstrip("_")
                if current and current.get("tokens"):
                    collected.append(current)
                current = {
                    "model": part,
                    "tokens": [],
                    "page": page_index + 1,
                }
                if len(parts) > 1:
                    tokens = extract_tokens(parts[1])
                    if tokens:
                        current["tokens"].extend(tokens)
                        if len(current["tokens"]) >= config["expected_tokens"]:
                            collected.append(current)
                            current = None
                continue

            if current is None:
                continue

            tokens = extract_tokens(line)
            if not tokens:
                continue
            current["tokens"].extend(tokens)
            if len(current["tokens"]) >= config["expected_tokens"]:
                collected.append(current)
                current = None

        if current and current.get("tokens"):
            collected.append(current)

    preview = "\n".join(preview_texts)
    title_line = extract_title_line(preview, f"Coilcraft {config['series_code']}")
    core_material = extract_core_material(preview, config["material_fallback"])

    rows: list[dict[str, str]] = []
    for item in collected:
        tokens = list(item["tokens"])[: config["expected_tokens"]]
        if len(tokens) < config["expected_tokens"]:
            continue
        row = build_row(config, clean_text(item["model"]), tokens, title_line, core_material, int(item["page"]))
        rows.append(row)

    if not rows:
        return pd.DataFrame()
    df = pd.DataFrame(rows).fillna("")
    df = df.drop_duplicates(subset=["品牌", "型号", "器件类型"], keep="first").reset_index(drop=True)
    return df


def get_value(tokens: list[str], index: int) -> str:
    return clean_text(tokens[index]) if 0 <= index < len(tokens) else ""


def build_spec_bundle(kind: str, tokens: list[str]) -> dict[str, str]:
    if kind == "power_dual_dcr":
        inductance = get_value(tokens, 0)
        dcr = f"{get_value(tokens, 1)} / {get_value(tokens, 2)}"
        srf = get_value(tokens, 3)
        isat = get_value(tokens, 4)
        irms = get_value(tokens, 5)
        irms_40 = get_value(tokens, 6)
        detail = f"Inductance={inductance} | DCR={dcr} | SRF={srf} | Isat={isat} | Irms20={irms} | Irms40={irms_40}"
        return {
            "inductance": inductance,
            "dcr": dcr,
            "isat": isat,
            "current": irms,
            "height": "",
            "detail": detail,
            "summary_tail": f"Isat {isat} A | Irms {irms} A / {irms_40} A",
        }
    if kind == "lps6235":
        inductance = get_value(tokens, 0)
        dcr = get_value(tokens, 1)
        srf = get_value(tokens, 2)
        isat10 = get_value(tokens, 3)
        isat20 = get_value(tokens, 4)
        isat30 = get_value(tokens, 5)
        irms20 = get_value(tokens, 6)
        irms40 = get_value(tokens, 7)
        detail = (
            f"Inductance={inductance} | DCR={dcr} | SRF={srf} | "
            f"Isat10={isat10} | Isat20={isat20} | Isat30={isat30} | "
            f"Irms20={irms20} | Irms40={irms40}"
        )
        return {
            "inductance": inductance,
            "dcr": dcr,
            "isat": isat10,
            "current": irms20,
            "height": "",
            "detail": detail,
            "summary_tail": f"Isat {isat10}/{isat20}/{isat30} A | Irms {irms20} A / {irms40} A",
        }
    if kind == "lpo6013":
        inductance = get_value(tokens, 0)
        dcr = get_value(tokens, 1)
        srf = get_value(tokens, 2)
        isat = get_value(tokens, 3)
        irms = get_value(tokens, 4)
        detail = f"Inductance={inductance} | DCR={dcr} | SRF={srf} | Isat={isat} | Irms={irms}"
        return {
            "inductance": inductance,
            "dcr": dcr,
            "isat": isat,
            "current": irms,
            "height": "",
            "detail": detail,
            "summary_tail": f"Isat {isat} A | Irms {irms} A",
        }
    if kind == "mss7341":
        inductance = get_value(tokens, 0)
        tolerance = get_value(tokens, 1)
        dcr = f"{get_value(tokens, 2)} / {get_value(tokens, 3)}"
        srf = get_value(tokens, 4)
        isat10 = get_value(tokens, 5)
        isat20 = get_value(tokens, 6)
        isat30 = get_value(tokens, 7)
        irms20 = get_value(tokens, 8)
        irms40 = get_value(tokens, 9)
        detail = (
            f"Inductance={inductance} | Tol={tolerance} | DCR={dcr} | SRF={srf} | "
            f"Isat10={isat10} | Isat20={isat20} | Isat30={isat30} | "
            f"Irms20={irms20} | Irms40={irms40}"
        )
        return {
            "inductance": inductance,
            "dcr": dcr,
            "isat": isat10,
            "current": irms20,
            "height": "",
            "detail": detail,
            "summary_tail": f"Isat {isat10}/{isat20}/{isat30} A | Irms {irms20} A / {irms40} A",
        }
    if kind == "ser2000":
        inductance = get_value(tokens, 0)
        dcr = f"{get_value(tokens, 1)} / {get_value(tokens, 2)}"
        srf = get_value(tokens, 3)
        isat = get_value(tokens, 4)
        irms20 = get_value(tokens, 5)
        irms40 = get_value(tokens, 6)
        height = get_value(tokens, 7)
        detail = (
            f"Inductance={inductance} | DCR={dcr} | SRF={srf} | "
            f"Isat={isat} | Irms20={irms20} | Irms40={irms40} | Height={height}"
        )
        return {
            "inductance": inductance,
            "dcr": dcr,
            "isat": isat,
            "current": irms20,
            "height": height,
            "detail": detail,
            "summary_tail": f"Isat {isat} A | Irms {irms20} A / {irms40} A | Height {height} mm",
        }
    raise ValueError(f"unsupported parser kind: {kind}")


def set_value(row: dict[str, str], key: str, value: str) -> None:
    if key in row and value:
        row[key] = value


def set_first_available(row: dict[str, str], keys: list[str], value: str) -> None:
    if not value:
        return
    for key in keys:
        if key in row:
            row[key] = value
            return


def build_row(
    config: dict,
    model: str,
    tokens: list[str],
    title_line: str,
    core_material: str,
    page_no: int,
) -> dict[str, str]:
    spec = build_spec_bundle(config["parser_kind"], tokens)
    model = clean_text(model).rstrip("_")
    row = {column: "" for column in OFFICIAL_COLUMNS}

    summary = (
        f"Coilcraft {config['series_code']} | {spec['inductance']} {config['inductance_unit']} | "
        f"DCR {spec['dcr']} | {spec['summary_tail']} | {core_material}"
    )

    set_value(row, "品牌", BRAND)
    set_value(row, "型号", model)
    set_value(row, "系列", config["series_code"])
    set_value(row, "材质（介质）", core_material)
    set_value(row, "特殊用途", config["family_label"])
    set_value(row, "备注1", title_line)
    set_value(row, "备注2", f"Values: {' | '.join(tokens)}")
    set_value(row, "备注3", f"PDF: {config['pdf_url']} | page={page_no}")
    set_value(row, "器件类型", config["component_type"])
    set_value(row, "安装方式", config["mount"])
    set_value(row, "封装代码", config["series_code"])
    set_value(row, "规格摘要", summary)
    set_value(row, "生产状态", "Production")
    set_value(row, "官网链接", config["pdf_url"])
    set_value(row, "数据来源", "Coilcraft official PDF")
    set_value(row, "数据状态", "官方PDF抽取")
    set_value(row, "校验时间", STAMP)
    set_value(row, "校验备注", f"series={config['series_code']} | page={page_no}")
    set_value(row, "电感值", spec["inductance"])
    set_value(row, "电感单位", config["inductance_unit"])
    set_value(row, "额定电流", spec["current"])
    set_value(row, "DCR", spec["dcr"])
    set_value(row, "饱和电流", spec["isat"])
    set_value(row, "高度（mm）", spec["height"])
    set_value(row, "_model_rule_authority", f"coilcraft_{config['code']}")
    set_value(row, "_body_size", config["series_code"])
    set_value(row, "系列说明", title_line)
    return row


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

    brand_mask = existing["品牌"].astype(str).str.contains("Coilcraft", case=False, na=False)
    remaining = existing.loc[~brand_mask].copy()
    merged = pd.concat([remaining, new_rows], ignore_index=True)
    merged = merged.drop_duplicates(subset=["品牌", "型号", "器件类型"], keep="last").reset_index(drop=True)
    merged = merged.reindex(columns=columns, fill_value="")
    merged.to_csv(OFFICIAL_CSV, index=False, encoding="utf-8-sig")
    return len(remaining), len(merged)


def run_db_refresh() -> None:
    subprocess.run(
        [sys.executable, str(ROOT / "sync_inductor_incremental_refresh.py"), str(SNAPSHOT_CSV)],
        cwd=ROOT,
        check=True,
    )


def main() -> int:
    print("[coilcraft] loading pdfs", flush=True)
    rows: list[pd.DataFrame] = []
    CACHE_DIR.mkdir(exist_ok=True)

    for config in PDF_CONFIGS:
        print(f"[coilcraft] fetch {config['code']}", flush=True)
        pdf_bytes = download_pdf(config)
        if not pdf_bytes:
            continue
        df = parse_pdf_rows(config, pdf_bytes)
        if df.empty:
            print(f"[coilcraft] no rows for {config['series_code']}", flush=True)
            continue
        print(f"[coilcraft] parsed {config['series_code']} rows={len(df)}", flush=True)
        rows.append(df)

    if not rows:
        raise SystemExit("no Coilcraft rows were parsed")

    df = pd.concat(rows, ignore_index=True).fillna("")
    df = df.drop_duplicates(subset=["品牌", "型号", "器件类型"], keep="first").reset_index(drop=True)

    print(f"[coilcraft] writing snapshot rows={len(df)}", flush=True)
    df.to_csv(SNAPSHOT_CSV, index=False, encoding="utf-8-sig")

    print("[coilcraft] merging official csv", flush=True)
    before_count, after_count = merge_into_official_csv(df)
    print("[coilcraft] refreshing db/cache", flush=True)
    run_db_refresh()

    print(f"snapshot_rows={len(df)} official_before={before_count} official_after={after_count}")
    print(f"snapshot={SNAPSHOT_CSV}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
