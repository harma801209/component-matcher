from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parent
OFFICIAL_CSV = ROOT / "Inductor" / "official_inductor_expansion.csv"
SNAPSHOT_CSV = ROOT / "Inductor" / "tdk_wurth_power_inductor_expansion.csv"
TODAY = datetime.now().strftime("%Y-%m-%d")

TDK_PRODUCT_URL = "https://product.tdk.com/en/search/inductor/inductor/smd/info?part_no={part}"
WURTH_PDF_URL = "https://www.we-online.com/components/products/datasheet/74479777310A.pdf"


def blank_row(columns: list[str]) -> dict[str, str]:
    return {column: "" for column in columns}


def build_tdk_row(columns: list[str], part_no: str, current: str, dcr: str, note: str) -> dict[str, str]:
    row = blank_row(columns)
    url = TDK_PRODUCT_URL.format(part=part_no)
    row.update(
        {
            "品牌": "东电化TDK",
            "型号": part_no,
            "系列": "MLZ",
            "尺寸（inch）": "0805",
            "容值": "10.0",
            "容值单位": "UH",
            "容值误差": "20",
            "特殊用途": "Power Inductor",
            "备注1": note,
            "备注2": url,
            "备注3": "TDK official product page | MLZ2012 family | 2.00 x 1.25 x 1.25 mm",
            "器件类型": "功率电感",
            "安装方式": "SMT",
            "封装代码": "2012/0805",
            "尺寸（mm）": "2.00 x 1.25 x 1.25 mm",
            "规格摘要": f"10uH ±20% 0805 {current} DCR {dcr}",
            "生产状态": "Active",
            "长度（mm）": "2.00",
            "宽度（mm）": "1.25",
            "高度（mm）": "1.25",
            "官网链接": url,
            "数据来源": "TDK official product page",
            "数据状态": "官方网页抽取",
            "校验时间": TODAY,
            "校验备注": f"TDK MLZ2012 {part_no} official page",
            "额定电流": current,
            "DCR": dcr,
            "电感值": "10",
            "电感单位": "UH",
            "电感误差": "20",
            "系列说明": "TDK MLZ2012 power inductor series",
            "_model_rule_authority": "tdk_mlz2012_official",
        }
    )
    return row


def build_wurth_row(columns: list[str]) -> dict[str, str]:
    row = blank_row(columns)
    row.update(
        {
            "品牌": "Wurth Elektronik",
            "型号": "74479777310A",
            "系列": "WE-PMI",
            "尺寸（inch）": "0805",
            "容值": "10.0",
            "容值单位": "UH",
            "容值误差": "20",
            "特殊用途": "Low RDC Power Inductor",
            "备注1": "L=10uH | IR=600mA | IR2=900mA | ISAT=120mA typ",
            "备注2": WURTH_PDF_URL,
            "备注3": "WE-PMI official datasheet | Low RDC | DCR 300mΩ typ / 375mΩ max | f_res 35MHz",
            "器件类型": "功率电感",
            "安装方式": "SMT",
            "封装代码": "WE-PMI",
            "尺寸（mm）": "2.00 x 1.20 x 1.25 mm",
            "规格摘要": "10uH ±20% 0805 600mA DCR 300mΩ typ / 375mΩ max",
            "生产状态": "Active",
            "长度（mm）": "2.00",
            "宽度（mm）": "1.20",
            "高度（mm）": "1.25",
            "官网链接": WURTH_PDF_URL,
            "数据来源": "Wurth official datasheet",
            "数据状态": "官方网页抽取",
            "校验时间": TODAY,
            "校验备注": "WE-PMI Power Multilayer Inductor order code 74479777310A",
            "额定电流": "600mA",
            "饱和电流": "120mA",
            "DCR": "300mΩ typ / 375mΩ max",
            "电感值": "10",
            "电感单位": "UH",
            "电感误差": "20",
            "系列说明": "Wurth WE-PMI Power Multilayer Inductor",
            "_model_rule_authority": "wurth_we_pmi_official",
        }
    )
    return row


def merge_rows(existing: pd.DataFrame, incoming: pd.DataFrame) -> pd.DataFrame:
    if existing.empty:
        return incoming
    if incoming.empty:
        return existing
    work = existing.copy().fillna("")
    new_rows = incoming.copy().fillna("")
    if {"品牌", "型号", "器件类型"}.issubset(work.columns):
        keep_mask = ~(
            work["品牌"].astype(str).isin(["东电化TDK", "Wurth Elektronik"])
            & work["型号"].astype(str).isin(new_rows["型号"].astype(str).tolist())
            & work["器件类型"].astype(str).eq("功率电感")
        )
        work = work.loc[keep_mask].copy()
    merged = pd.concat([work, new_rows], ignore_index=True)
    merged = merged.drop_duplicates(subset=["品牌", "型号", "器件类型"], keep="last").reset_index(drop=True)
    return merged


def main() -> int:
    if not OFFICIAL_CSV.exists():
        raise SystemExit(f"missing official csv: {OFFICIAL_CSV}")

    existing = pd.read_csv(OFFICIAL_CSV, encoding="utf-8-sig").fillna("")
    columns = list(existing.columns)
    rows = pd.DataFrame(
        [
            build_tdk_row(columns, "MLZ2012M100WT000", "350mA", "470mΩ typ / 611mΩ max",
                          "10uH ±20% | Rated current (temperature rise) 350mA | DC resistance 470mΩ typ / 611mΩ max"),
            build_tdk_row(columns, "MLZ2012M100HT000", "300mA", "680mΩ typ / 884mΩ max",
                          "10uH ±20% | Rated current (temperature rise) 300mA | Rated current (L change) 200mA | DC resistance 680mΩ typ / 884mΩ max"),
            build_tdk_row(columns, "MLZ2012N100LT000", "500mA", "300mΩ typ / 390mΩ max",
                          "10uH ±20% | Rated current (temperature rise) 500mA | Rated current (L change) 110mA | DC resistance 300mΩ typ / 390mΩ max"),
            build_wurth_row(columns),
        ],
        columns=columns,
    ).fillna("")

    snapshot = rows.copy()
    snapshot.to_csv(SNAPSHOT_CSV, index=False, encoding="utf-8-sig")

    merged = merge_rows(existing, rows)
    merged = merged.reindex(columns=columns).fillna("")
    merged.to_csv(OFFICIAL_CSV, index=False, encoding="utf-8-sig")

    print(f"tdk_wurth_rows={len(rows)} merged_total={len(merged)} snapshot={SNAPSHOT_CSV}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
