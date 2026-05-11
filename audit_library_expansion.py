import csv
import os
import sqlite3
from datetime import datetime


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "components.db")
REPORT_DIR = os.path.join(BASE_DIR, "reports")
CSV_REPORT_PATH = os.path.join(REPORT_DIR, "library_expansion_audit.csv")
MD_REPORT_PATH = os.path.join(REPORT_DIR, "library_expansion_audit.md")


TARGET_MATRIX = [
    ("passive", "MLCC", ["Murata", "TDK", "Samsung", "Taiyo Yuden", "Yageo", "Walsin", "PDC", "Kyocera AVX", "KEMET", "Vishay", "Fenghua", "FH"]),
    ("passive", "贴片电阻", ["Yageo", "Walsin", "PDC", "UNI-ROYAL", "FOJAN", "Vishay", "KOA", "Panasonic", "ROHM", "Samsung", "RALEC", "Ever Ohms"]),
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


def load_type_brand_rows(conn):
    component_types = sorted({item[1] for item in TARGET_MATRIX})
    result = {}
    for component_type in component_types:
        rows = conn.execute(
            "SELECT [品牌], COUNT(*) FROM components WHERE [器件类型] = ? GROUP BY [品牌]",
            [component_type],
        ).fetchall()
        result[component_type] = [(str(brand or ""), int(count or 0)) for brand, count in rows]
    return result


def count_brand_rows(type_brand_rows, component_type, brand):
    tokens = [token.lower() for token in brand_like_clause(brand) if str(token).strip()]
    if not tokens:
        return 0
    count = 0
    for row_brand, row_count in type_brand_rows.get(component_type, []):
        brand_lower = row_brand.lower()
        if any(token in brand_lower for token in tokens):
            count += row_count
    return count


def count_type_rows(type_brand_rows, component_type):
    return sum(row_count for _, row_count in type_brand_rows.get(component_type, []))


def current_brand_count(type_brand_rows, component_type):
    return sum(1 for brand, _ in type_brand_rows.get(component_type, []) if brand.strip())


def build_rows(conn):
    type_brand_rows = load_type_brand_rows(conn)
    rows = []
    for group, component_type, brands in TARGET_MATRIX:
        total = count_type_rows(type_brand_rows, component_type)
        current_brands = current_brand_count(type_brand_rows, component_type)
        for brand in brands:
            brand_rows = count_brand_rows(type_brand_rows, component_type, brand)
            rows.append(
                {
                    "group": group,
                    "component_type": component_type,
                    "target_brand": brand,
                    "brand_rows": brand_rows,
                    "type_rows": total,
                    "type_brand_count": current_brands,
                    "status": "covered" if brand_rows > 0 else "gap",
                }
            )
    return rows


def write_csv(rows):
    os.makedirs(REPORT_DIR, exist_ok=True)
    fieldnames = ["group", "component_type", "target_brand", "brand_rows", "type_rows", "type_brand_count", "status"]
    with open(CSV_REPORT_PATH, "w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_markdown(rows):
    gaps = [row for row in rows if row["status"] == "gap"]
    covered = [row for row in rows if row["status"] == "covered"]
    lines = [
        "# Library Expansion Audit",
        "",
        f"- Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"- Target pairs: {len(rows)}",
        f"- Covered pairs: {len(covered)}",
        f"- Gap pairs: {len(gaps)}",
        "",
        "## Priority Gaps",
        "",
        "| group | component_type | target_brand | type_rows | type_brand_count |",
        "|---|---|---:|---:|---:|",
    ]
    for row in gaps[:120]:
        lines.append(
            f"| {row['group']} | {row['component_type']} | {row['target_brand']} | {row['type_rows']} | {row['type_brand_count']} |"
        )
    lines.extend(["", "## Covered Targets", "", "| group | component_type | target_brand | brand_rows |", "|---|---|---:|---:|"])
    for row in covered[:120]:
        lines.append(f"| {row['group']} | {row['component_type']} | {row['target_brand']} | {row['brand_rows']} |")
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
    gap_count = sum(1 for row in rows if row["status"] == "gap")
    print(f"wrote={CSV_REPORT_PATH}")
    print(f"wrote={MD_REPORT_PATH}")
    print(f"target_pairs={len(rows)} gaps={gap_count}")


if __name__ == "__main__":
    main()
