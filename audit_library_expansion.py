import csv
import os
import re
import sqlite3
from datetime import datetime


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "components.db")
REPORT_DIR = os.path.join(BASE_DIR, "reports")
CSV_REPORT_PATH = os.path.join(REPORT_DIR, "library_expansion_audit.csv")
MD_REPORT_PATH = os.path.join(REPORT_DIR, "library_expansion_audit.md")


GENERIC_SERIES_DESC_PATTERNS = [
    re.compile(pattern, re.I)
    for pattern in [
        r"(?:^|[\s/])MLCC\s+series$",
        r"(?:thick|thin)\s+film\s+resistor\s+series$",
        r"chip\s+resistor\s+series$",
        r"(?:功率|射频|共模)?电感系列$",
        r"(?:厚膜|薄膜|合金|绕线|金属氧化膜|碳膜)?电阻系列$",
        r"电容系列$",
    ]
]


def generated_series_description(desc):
    text = clean_text(desc)
    if text == "":
        return False
    if text.endswith("电阻系列") or text.endswith("贴片压敏电阻系列") or text.endswith("热敏电阻系列"):
        return True
    if " 功率:" in text and "电阻系列" in text:
        return True
    return bool(
        re.search(
            r"(?:^|[\s/])(?:[A-Z0-9][A-Z0-9./_-]{1,}|[0-9]{2,5})(?:\s*功率:[^\s]+)?\s*"
            r"(?:贴片|厚膜|薄膜|合金|绕线|碳膜|金属氧化膜|热敏|压敏)?电阻系列$",
            text,
            flags=re.I,
        )
    )


TARGET_MATRIX = [
    ("passive", "MLCC", ["Murata", "TDK", "Samsung", "Taiyo Yuden", "Yageo", "Walsin", "PDC", "Kyocera AVX", "KEMET", "Vishay", "Fenghua", "FH"]),
    ("passive", "贴片电阻", ["Yageo", "Walsin", "PDC", "UNI-ROYAL", "FOJAN", "KOA", "Panasonic", "Samsung", "RALEC", "Ever Ohms"]),
    ("passive", "厚膜电阻", ["Yageo", "Walsin", "PDC", "UNI-ROYAL", "FOJAN", "Vishay", "KOA", "Panasonic", "ROHM", "Samsung", "RALEC", "Ever Ohms"]),
    ("passive", "薄膜电阻", ["Yageo", "Vishay", "KOA", "Panasonic", "Susumu", "Samsung", "UniOhm", "Ever Ohms"]),
    ("passive", "合金电阻", ["Yageo", "Walsin", "PDC", "UNI-ROYAL", "FOJAN", "Vishay", "Isabellenhuette", "Bourns", "Rohm"]),
    ("passive", "热敏电阻", ["Murata", "TDK", "Vishay", "Panasonic", "Semitec", "Mitsubishi", "Sunlord"]),
    ("passive", "贴片压敏电阻", ["TDK", "Murata", "Bourns", "Littelfuse", "Panasonic", "Vishay", "Sunlord", "Yageo"]),
    ("passive", "引线型压敏电阻", ["TDK", "Bourns", "Littelfuse", "Panasonic", "Vishay", "Epcos", "Joyin"]),
    ("passive", "功率电感", ["Murata", "TDK", "Taiyo Yuden", "Sunlord", "Wurth", "Bourns", "Coilcraft", "Sumida", "Panasonic", "Vishay", "Samsung", "Chilisin"]),
    ("passive", "射频电感", ["Murata", "TDK", "Taiyo Yuden", "Sunlord", "Coilcraft", "Wurth", "Vishay", "Chilisin"]),
    ("passive", "磁珠", ["Murata", "TDK", "Taiyo Yuden", "Sunlord", "Wurth", "Laird", "Samsung", "Chilisin"]),
    ("passive", "共模电感", ["Murata", "TDK", "Bourns", "Wurth", "Laird", "Sunlord", "Chilisin", "Coilcraft"]),
    ("passive", "铝电解电容", ["Nichicon", "Rubycon", "Panasonic", "Nippon Chemi-Con", "Jianghai", "Lelon", "Samwha", "Aishi", "CapXon"]),
    ("passive", "薄膜电容", ["KEMET", "WIMA", "Panasonic", "TDK", "Vishay", "Epcos", "CDE", "Nichicon"]),
    ("passive", "晶振", ["Epson", "Abracon", "TXC", "NDK", "Kyocera", "Murata", "KDS"]),
    ("passive", "振荡器", ["Epson", "Abracon", "TXC", "NDK", "Kyocera", "SiTime"]),
    ("semiconductor", "MOSFET", ["Infineon", "onsemi", "STMicroelectronics", "Vishay", "AOSMD", "Diodes Incorporated", "ROHM", "Toshiba", "Nexperia"]),
    ("semiconductor", "二极管", ["Diodes Incorporated", "Vishay", "onsemi", "Nexperia", "STMicroelectronics", "ROHM", "Toshiba", "Littelfuse", "MCC"]),
    ("semiconductor", "三极管", ["Nexperia", "onsemi", "Diodes Incorporated", "ROHM", "Toshiba", "STMicroelectronics", "Rectron"]),
    ("semiconductor", "TVS二极管", ["Diodes Incorporated", "Littelfuse", "Vishay", "onsemi", "Nexperia", "STMicroelectronics", "Bourns"]),
]


def brand_like_clause(brand):
    aliases = {
        "Yageo": ["Yageo", "国巨"],
        "Walsin": ["Walsin", "华新科", "华科"],
        "PDC": ["PDC", "PSA", "信昌"],
        "UNI-ROYAL": ["UNI-ROYAL", "Uniroyal", "厚声"],
        "FOJAN": ["FOJAN", "富捷"],
        "Murata": ["Murata", "村田"],
        "Taiyo Yuden": ["Taiyo", "太阳诱电"],
        "Kyocera AVX": ["Kyocera", "AVX"],
        "Wurth": ["Wurth", "Würth"],
        "Jianghai": ["Jianghai", "江海"],
        "Nippon Chemi-Con": ["Nippon", "Chemi-Con", "NCC"],
        "AOSMD": ["AOSMD", "Alpha & Omega", "AOS"],
    }
    tokens = aliases.get(brand, [brand])
    return tokens


def clean_text(value):
    return str(value or "").strip()


def normalize_key(value):
    return re.sub(r"\s+", "", clean_text(value)).lower()


def brand_token_matches(row_brand, token):
    brand_lower = clean_text(row_brand).lower()
    token_lower = clean_text(token).lower()
    if not token_lower:
        return False
    if re.fullmatch(r"[a-z0-9]{1,4}", token_lower):
        return bool(re.search(rf"(^|[^a-z0-9]){re.escape(token_lower)}([^a-z0-9]|$)", brand_lower))
    return token_lower in brand_lower


SEMANTIC_SERIES_TOKENS = (
    "通用",
    "普通",
    "车规",
    "汽车",
    "工业",
    "高功率",
    "高压",
    "抗硫",
    "抗浪涌",
    "高精",
    "低阻",
    "电流检测",
    "高q",
    "高频",
    "薄膜型",
    "绕线型",
    "多层",
    "金属合金",
    "一体成型",
    "低dcr",
    "低esr",
    "低阻抗",
    "低背",
    "宽温",
    "高纹波",
    "长寿命",
    "小型化",
    "高温",
    "径向引线",
    "浪涌",
    "热保护",
    "esd",
    "基板自立",
    "螺栓端子",
    "音频",
    "共模",
    "emi",
    "磁珠",
    "混合电解",
    "general",
    "automotive",
    "industrial",
    "high power",
    "high voltage",
    "anti-sulfur",
    "anti surge",
    "precision",
    "current sense",
)


def series_desc_has_semantic_token(desc):
    text = clean_text(desc)
    lower_text = text.lower()
    return any(token in text or token in lower_text for token in SEMANTIC_SERIES_TOKENS)


def series_semantics_ready(brand, component_type, series, series_desc):
    brand_key = normalize_key(brand)
    type_key = normalize_key(component_type)
    series_key = normalize_key(series)
    desc = clean_text(series_desc)
    desc_key = normalize_key(desc)
    has_semantic_token = series_desc_has_semantic_token(desc)

    if not series_key or not desc:
        return False
    if desc_key in {brand_key, series_key, f"{brand_key}{series_key}"}:
        return False
    if brand_key and series_key and desc_key.startswith(f"{brand_key}{series_key}"):
        if type_key and desc_key.endswith(f"{type_key}系列") and not has_semantic_token:
            return False
        if any(pattern.search(desc) for pattern in GENERIC_SERIES_DESC_PATTERNS) and not has_semantic_token:
            return False
    if generated_series_description(desc) or any(pattern.search(desc) for pattern in GENERIC_SERIES_DESC_PATTERNS):
        if not has_semantic_token:
            return False
    return True


def load_type_brand_rows(conn):
    component_types = sorted({item[1] for item in TARGET_MATRIX})
    placeholders = ",".join(["?"] * len(component_types))
    sql = (
        "SELECT [器件类型], [品牌], [系列], [系列说明] "
        f"FROM components WHERE [器件类型] IN ({placeholders})"
    )
    result = {}
    for component_type, brand, series, series_desc in conn.execute(sql, component_types):
        type_stats = result.setdefault(str(component_type or ""), {})
        row_brand = str(brand or "")
        brand_stats = type_stats.setdefault(row_brand, {"rows": 0, "semantic_ready_rows": 0})
        brand_stats["rows"] += 1
        if series_semantics_ready(row_brand, component_type, series, series_desc):
            brand_stats["semantic_ready_rows"] += 1
    return result


def count_brand_rows(type_brand_rows, component_type, brand):
    tokens = [token for token in brand_like_clause(brand) if str(token).strip()]
    if not tokens:
        return 0
    count = 0
    for row_brand, stats in type_brand_rows.get(component_type, {}).items():
        if any(brand_token_matches(row_brand, token) for token in tokens):
            count += int(stats.get("rows", 0))
    return count


def count_brand_semantic_rows(type_brand_rows, component_type, brand):
    tokens = [token for token in brand_like_clause(brand) if str(token).strip()]
    if not tokens:
        return 0
    count = 0
    for row_brand, stats in type_brand_rows.get(component_type, {}).items():
        if any(brand_token_matches(row_brand, token) for token in tokens):
            count += int(stats.get("semantic_ready_rows", 0))
    return count


def count_type_rows(type_brand_rows, component_type):
    return sum(int(stats.get("rows", 0)) for stats in type_brand_rows.get(component_type, {}).values())


def current_brand_count(type_brand_rows, component_type):
    return sum(1 for brand in type_brand_rows.get(component_type, {}) if brand.strip())


def build_rows(conn):
    type_brand_rows = load_type_brand_rows(conn)
    rows = []
    for group, component_type, brands in TARGET_MATRIX:
        total = count_type_rows(type_brand_rows, component_type)
        current_brands = current_brand_count(type_brand_rows, component_type)
        for brand in brands:
            brand_rows = count_brand_rows(type_brand_rows, component_type, brand)
            semantic_ready_rows = count_brand_semantic_rows(type_brand_rows, component_type, brand)
            semantic_gap_rows = max(brand_rows - semantic_ready_rows, 0)
            if brand_rows <= 0:
                semantic_status = "brand_gap"
            elif semantic_ready_rows <= 0:
                semantic_status = "series_gap"
            elif semantic_gap_rows > 0:
                semantic_status = "partial_series"
            else:
                semantic_status = "ready"
            rows.append(
                {
                    "group": group,
                    "component_type": component_type,
                    "target_brand": brand,
                    "brand_rows": brand_rows,
                    "semantic_ready_rows": semantic_ready_rows,
                    "semantic_gap_rows": semantic_gap_rows,
                    "semantic_coverage_rate": round(semantic_ready_rows / brand_rows, 4) if brand_rows else 0.0,
                    "type_rows": total,
                    "type_brand_count": current_brands,
                    "brand_status": "covered" if brand_rows > 0 else "gap",
                    "semantic_status": semantic_status,
                }
            )
    return rows


def write_csv(rows):
    os.makedirs(REPORT_DIR, exist_ok=True)
    fieldnames = [
        "group",
        "component_type",
        "target_brand",
        "brand_rows",
        "semantic_ready_rows",
        "semantic_gap_rows",
        "semantic_coverage_rate",
        "type_rows",
        "type_brand_count",
        "brand_status",
        "semantic_status",
    ]
    with open(CSV_REPORT_PATH, "w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_markdown(rows):
    brand_gaps = [row for row in rows if row["brand_status"] == "gap"]
    covered = [row for row in rows if row["brand_status"] == "covered"]
    ready = [row for row in rows if row["semantic_status"] == "ready"]
    series_gaps = [row for row in rows if row["semantic_status"] == "series_gap"]
    partial_series = [row for row in rows if row["semantic_status"] == "partial_series"]
    lines = [
        "# Library Expansion Audit",
        "",
        f"- Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"- Target pairs: {len(rows)}",
        f"- Brand-covered pairs: {len(covered)}",
        f"- Brand-gap pairs: {len(brand_gaps)}",
        f"- Series-semantics ready pairs: {len(ready)}",
        f"- Series-semantics partial pairs: {len(partial_series)}",
        f"- Series-semantics gap pairs: {len(series_gaps)}",
        "",
        "## Priority Series-Semantics Gaps",
        "",
        "| group | component_type | target_brand | brand_rows | semantic_ready_rows | semantic_gap_rows | semantic_coverage |",
        "|---|---|---:|---:|---:|---:|---:|",
    ]
    for row in (series_gaps + partial_series)[:120]:
        lines.append(
            f"| {row['group']} | {row['component_type']} | {row['target_brand']} | {row['brand_rows']} | "
            f"{row['semantic_ready_rows']} | {row['semantic_gap_rows']} | {row['semantic_coverage_rate']:.2%} |"
        )
    lines.extend(
        [
            "",
            "## Brand Gaps",
            "",
            "| group | component_type | target_brand | type_rows | type_brand_count |",
            "|---|---|---:|---:|---:|",
        ]
    )
    for row in brand_gaps[:120]:
        lines.append(
            f"| {row['group']} | {row['component_type']} | {row['target_brand']} | {row['type_rows']} | {row['type_brand_count']} |"
        )
    lines.extend(
        [
            "",
            "## Series-Semantics Ready Targets",
            "",
            "| group | component_type | target_brand | brand_rows | semantic_ready_rows |",
            "|---|---|---:|---:|---:|",
        ]
    )
    for row in ready[:120]:
        lines.append(
            f"| {row['group']} | {row['component_type']} | {row['target_brand']} | {row['brand_rows']} | {row['semantic_ready_rows']} |"
        )
    with open(MD_REPORT_PATH, "w", encoding="utf-8") as handle:
        handle.write("\n".join(lines) + "\n")


def main():
    if not os.path.exists(DB_PATH):
        raise SystemExit(f"missing database: {DB_PATH}")
    conn = sqlite3.connect(DB_PATH)
    try:
        rows = build_rows(conn)
    finally:
        conn.close()
    write_csv(rows)
    write_markdown(rows)
    gap_count = sum(1 for row in rows if row["brand_status"] == "gap")
    semantic_gap_count = sum(1 for row in rows if row["semantic_status"] in {"series_gap", "partial_series"})
    print(f"wrote={CSV_REPORT_PATH}")
    print(f"wrote={MD_REPORT_PATH}")
    print(f"target_pairs={len(rows)} brand_gaps={gap_count} semantic_gap_pairs={semantic_gap_count}")


if __name__ == "__main__":
    main()
