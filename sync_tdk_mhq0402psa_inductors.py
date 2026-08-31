from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parent
OFFICIAL_CSV = ROOT / "Inductor" / "official_inductor_expansion.csv"
SNAPSHOT_CSV = ROOT / "Inductor" / "tdk_mhq0402psa_expansion.csv"
TDK_PRODUCT_URL = "https://product.tdk.com/en/search/inductor/inductor/smd/info?part_no={part}"
TDK_CATALOG_URL = (
    "https://product.tdk.com/en/system/files/dam/doc/product/inductor/inductor/smd/catalog/"
    "inductor_commercial_high-frequency_mhq0402psa_en.pdf"
)
TODAY = datetime.now().strftime("%Y-%m-%d")

BRAND = "东电化TDK"
SERIES = "MHQ0402PSA"
SERIES_DESC = "TDK MHQ-PSA series high Q multilayer ceramic inductor (EIA 01005)"
SPECIAL_USE = "High Q RF Chip Inductor"
SIZE_INCH = "01005"
SIZE_MM = "0.4 x 0.2 x 0.2 mm"
LENGTH_MM = "0.4"
WIDTH_MM = "0.2"
HEIGHT_MM = "0.2"
MATERIAL = "CERAMIC"
MOUNTING = "SMT"
PACKAGE_CODE = "01005"
COMPONENT_TYPE = "射频电感"


SERIES_SPECS = [
    ("0.2", "600mA", "20mΩ typ / 150mΩ max"),
    ("0.3", "600mA", "40mΩ typ / 150mΩ max"),
    ("0.4", "600mA", "40mΩ typ / 150mΩ max"),
    ("0.5", "600mA", "40mΩ typ / 150mΩ max"),
    ("0.6", "600mA", "50mΩ typ / 150mΩ max"),
    ("0.7", "600mA", "60mΩ typ / 150mΩ max"),
    ("0.8", "600mA", "60mΩ typ / 150mΩ max"),
    ("0.9", "600mA", "80mΩ typ / 150mΩ max"),
    ("1.0", "600mA", "70mΩ typ / 150mΩ max"),
    ("1.1", "500mA", "110mΩ typ / 150mΩ max"),
    ("1.2", "500mA", "150mΩ typ / 200mΩ max"),
    ("1.3", "400mA", "130mΩ typ / 200mΩ max"),
    ("1.4", "400mA", "180mΩ typ / 300mΩ max"),
    ("1.5", "400mA", "150mΩ typ / 200mΩ max"),
    ("1.6", "400mA", "150mΩ typ / 300mΩ max"),
    ("1.7", "400mA", "210mΩ typ / 400mΩ max"),
    ("1.8", "400mA", "140mΩ typ / 400mΩ max"),
    ("1.9", "400mA", "140mΩ typ / 400mΩ max"),
    ("2.0", "400mA", "170mΩ typ / 400mΩ max"),
    ("2.1", "400mA", "230mΩ typ / 400mΩ max"),
    ("2.2", "400mA", "160mΩ typ / 400mΩ max"),
    ("2.3", "300mA", "230mΩ typ / 400mΩ max"),
    ("2.4", "300mA", "250mΩ typ / 400mΩ max"),
    ("2.5", "300mA", "230mΩ typ / 400mΩ max"),
    ("2.6", "300mA", "220mΩ typ / 400mΩ max"),
    ("2.7", "300mA", "240mΩ typ / 400mΩ max"),
    ("2.8", "250mA", "230mΩ typ / 400mΩ max"),
    ("2.9", "250mA", "320mΩ typ / 600mΩ max"),
    ("3.0", "250mA", "280mΩ typ / 600mΩ max"),
    ("3.1", "250mA", "340mΩ typ / 650mΩ max"),
    ("3.2", "250mA", "330mΩ typ / 650mΩ max"),
    ("3.3", "250mA", "300mΩ typ / 650mΩ max"),
    ("3.4", "200mA", "220mΩ typ / 650mΩ max"),
    ("3.5", "200mA", "270mΩ typ / 650mΩ max"),
    ("3.6", "200mA", "290mΩ typ / 650mΩ max"),
    ("3.7", "200mA", "310mΩ typ / 750mΩ max"),
    ("3.8", "200mA", "310mΩ typ / 750mΩ max"),
    ("3.9", "200mA", "320mΩ typ / 750mΩ max"),
    ("4.0", "200mA", "400mΩ typ / 800mΩ max"),
    ("4.1", "200mA", "400mΩ typ / 800mΩ max"),
    ("4.2", "200mA", "400mΩ typ / 800mΩ max"),
    ("4.3", "200mA", "400mΩ typ / 800mΩ max"),
    ("4.7", "200mA", "380mΩ typ / 800mΩ max"),
]


def find_column(columns: list[str], keyword: str) -> str:
    for column in columns:
        if column == keyword or keyword in column:
            return column
    raise KeyError(f"missing column for keyword: {keyword}")


def value_to_part_suffix(value: str) -> str:
    whole, frac = value.split(".", 1)
    return f"{whole}N{frac}"


def tolerance_options(value: str) -> list[tuple[str, str]]:
    if value in {"4.3", "4.7"}:
        return [("H", "±3%"), ("J", "±5%")]
    return [("B", "±0.1nH"), ("C", "±0.2nH"), ("S", "±0.3nH")]


def blank_row(columns: list[str]) -> dict[str, str]:
    return {column: "" for column in columns}


def build_row(columns: list[str], value: str, current: str, dcr_text: str, tolerance_code: str, tolerance_text: str) -> dict[str, str]:
    model = f"MHQ0402PSA{value_to_part_suffix(value)}{tolerance_code}T000"
    part_url = TDK_PRODUCT_URL.format(part=model)
    row = blank_row(columns)

    c_brand = find_column(columns, "品牌")
    c_model = find_column(columns, "型号")
    c_series = find_column(columns, "系列")
    c_size_inch = find_column(columns, "尺寸（inch）")
    c_material = find_column(columns, "材质（介质）")
    c_value = find_column(columns, "容值")
    c_value_unit = find_column(columns, "容值单位")
    c_value_tol = find_column(columns, "容值误差")
    c_use = find_column(columns, "特殊用途")
    c_note1 = find_column(columns, "备注1")
    c_note2 = find_column(columns, "备注2")
    c_note3 = find_column(columns, "备注3")
    c_type = find_column(columns, "器件类型")
    c_mount = find_column(columns, "安装方式")
    c_package = find_column(columns, "封装代码")
    c_size_mm = find_column(columns, "尺寸（mm）")
    c_summary = find_column(columns, "规格摘要")
    c_status = find_column(columns, "生产状态")
    c_length = find_column(columns, "长度（mm）")
    c_width = find_column(columns, "宽度（mm）")
    c_height = find_column(columns, "高度（mm）")
    c_home = find_column(columns, "官网链接")
    c_source = find_column(columns, "数据来源")
    c_state = find_column(columns, "数据状态")
    c_time = find_column(columns, "校验时间")
    c_check = find_column(columns, "校验备注")
    c_ind_value = find_column(columns, "电感值")
    c_ind_unit = find_column(columns, "电感单位")
    c_ind_tol = find_column(columns, "电感误差")
    c_current = find_column(columns, "额定电流")
    c_dcr = find_column(columns, "DCR")
    c_series_desc = find_column(columns, "系列说明")

    row[c_brand] = BRAND
    row[c_model] = model
    row[c_series] = SERIES
    row[c_size_inch] = SIZE_INCH
    row[c_material] = MATERIAL
    row[c_value] = value
    row[c_value_unit] = "NH"
    row[c_value_tol] = tolerance_text
    row[c_use] = SPECIAL_USE
    row[c_note1] = f"L={value}nH | Imax={current} | DCR={dcr_text}"
    row[c_note2] = part_url
    row[c_note3] = TDK_CATALOG_URL
    row[c_type] = COMPONENT_TYPE
    row[c_mount] = MOUNTING
    row[c_package] = PACKAGE_CODE
    row[c_size_mm] = SIZE_MM
    row[c_summary] = (
        f"MHQ0402PSA | {SIZE_MM} | L={value}nH {tolerance_text} | "
        f"{current} | {dcr_text}"
    )
    row[c_status] = "Active"
    row[c_length] = LENGTH_MM
    row[c_width] = WIDTH_MM
    row[c_height] = HEIGHT_MM
    row[c_home] = part_url
    row[c_source] = "TDK official catalog PDF"
    row[c_state] = "官方抽取"
    row[c_time] = TODAY
    row[c_check] = "TDK MHQ0402PSA official catalog PDF"
    row[c_ind_value] = value
    row[c_ind_unit] = "NH"
    row[c_ind_tol] = tolerance_text
    row[c_current] = current
    row[c_dcr] = dcr_text
    row[c_series_desc] = SERIES_DESC

    return row


def merge_rows(existing: pd.DataFrame, new_rows: pd.DataFrame) -> pd.DataFrame:
    if existing.empty:
        return new_rows
    if new_rows.empty:
        return existing
    work = existing.copy().fillna("")
    incoming = new_rows.copy().fillna("")
    key_cols = ["品牌", "型号", "器件类型"]
    if not set(key_cols).issubset(work.columns):
        return pd.concat([work, incoming], ignore_index=True)
    work = work[
        ~(
            work["品牌"].astype(str).eq(BRAND)
            & work["型号"].astype(str).isin(incoming["型号"].astype(str).tolist())
            & work["器件类型"].astype(str).eq(COMPONENT_TYPE)
        )
    ]
    combined = pd.concat([work, incoming], ignore_index=True)
    return combined


def main() -> int:
    if not OFFICIAL_CSV.exists():
        raise SystemExit(f"missing official csv: {OFFICIAL_CSV}")

    existing = pd.read_csv(OFFICIAL_CSV, encoding="utf-8-sig").fillna("")
    columns = list(existing.columns)

    rows = []
    for value, current, dcr_text in SERIES_SPECS:
        for tolerance_code, tolerance_text in tolerance_options(value):
            rows.append(build_row(columns, value, current, dcr_text, tolerance_code, tolerance_text))

    df = pd.DataFrame(rows, columns=columns).fillna("")
    df = df.drop_duplicates(subset=["品牌", "型号", "器件类型"], keep="first").reset_index(drop=True)
    df.to_csv(SNAPSHOT_CSV, index=False, encoding="utf-8-sig")

    merged = merge_rows(existing, df)
    merged = merged.reindex(columns=columns).fillna("")
    merged.to_csv(OFFICIAL_CSV, index=False, encoding="utf-8-sig")

    print(f"tdk_mhq0402psa_rows={len(df)} merged_total={len(merged)} snapshot={SNAPSHOT_CSV}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
