from __future__ import annotations

import argparse
import json
import re
import sqlite3
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DB_PATH = ROOT / "components.db"
DEFAULT_REGISTRY_PATH = ROOT / "docs" / "passive_series_source_registry.json"
DEFAULT_JSON_OUT = ROOT / "docs" / "passive_series_gap_report.json"
DEFAULT_MD_OUT = ROOT / "docs" / "passive_series_gap_report.md"


GENERIC_SERIES_DESC_PATTERNS = [
    re.compile(pattern, re.I)
    for pattern in [
        r"(?:^|[\s/])MLCC\s+series$",
        r"multilayer\s+varistor\s+series$",
        r"(?:thick|thin)\s+film\s+resistor\s+series$",
        r"chip\s+resistor\s+series$",
        r"power\s+inductor\s+series$",
        r"rf\s+inductor\s+series$",
        r"bead\s+series$",
        r"filter\s+series$",
        r"(?:厚膜|薄膜|合金|绕线|金属氧化膜|碳膜)?电阻系列$",
        r"(?:功率|射频|共模)?电感系列$",
        r"(?:贴片)?压敏电阻系列$",
        r"磁珠系列$",
        r"滤波器系列$",
        r"电容系列$",
    ]
]


def clean_text(value: object) -> str:
    if value is None:
        return ""
    text = str(value).strip()
    if text.lower() in {"", "none", "nan"}:
        return ""
    return text


def normalize_key(value: object) -> str:
    return re.sub(r"\s+", "", clean_text(value)).lower()


def is_passive_component_type(component_type: str) -> bool:
    text = clean_text(component_type)
    if text == "":
        return False
    keywords = ("电阻", "电容", "电感", "磁珠", "滤波", "压敏")
    return any(keyword in text for keyword in keywords)


def series_looks_missing(series: str) -> bool:
    return clean_text(series) == ""


def is_placeholder_series_desc(brand: str, series: str, series_desc: str, component_type: str) -> bool:
    desc = clean_text(series_desc)
    if desc == "":
        return True

    brand_key = normalize_key(brand)
    series_key = normalize_key(series)
    desc_key = normalize_key(desc)
    type_key = normalize_key(component_type)

    if desc_key in {brand_key, series_key, f"{brand_key}{series_key}"}:
        return True

    if series_key and desc_key == f"{series_key}series":
        return True

    if brand_key and series_key and desc_key.startswith(f"{brand_key}{series_key}"):
        if any(pattern.search(desc) for pattern in GENERIC_SERIES_DESC_PATTERNS):
            return True
        if type_key and desc_key.endswith(f"{type_key}系列"):
            return True

    if any(pattern.search(desc) for pattern in GENERIC_SERIES_DESC_PATTERNS):
        semantic_keywords = (
            "车规", "汽车", "抗硫", "抗浪涌", "高功率", "高压", "软端子", "无磁",
            "precision", "automotive", "anti-sulfur", "anti surge", "surge",
            "medical", "soft termination", "high power", "high voltage",
        )
        if not any(keyword in desc.lower() or keyword in desc for keyword in semantic_keywords):
            return True

    return False


def infer_prefix_candidate(model: str, series: str) -> str:
    series_text = clean_text(series)
    if series_text != "":
        return series_text

    compact = re.sub(r"[^A-Za-z0-9]", "", clean_text(model).upper())
    if compact == "":
        return ""

    patterns = [
        r"^([A-Z]{2,8}\d{2,4}[A-Z]{1,4})",
        r"^(\d{4}[A-Z]{1,4})",
        r"^([A-Z]{2,8})",
    ]
    for pattern in patterns:
        match = re.match(pattern, compact)
        if match is not None:
            return clean_text(match.group(1))
    return compact[:8]


def load_registry(path: Path) -> tuple[dict, dict[str, dict]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    brand_map: dict[str, dict] = {}
    for item in payload.get("brands", []):
        brand_map[clean_text(item.get("brand", ""))] = item
    return payload, brand_map


def fetch_passive_rows(db_path: Path) -> list[tuple[str, str, str, str, str]]:
    conn = sqlite3.connect(db_path)
    try:
        cursor = conn.execute(
            """
            SELECT 品牌, 器件类型, 型号, 系列, 系列说明
            FROM components
            WHERE TRIM(IFNULL(品牌, '')) <> ''
              AND TRIM(IFNULL(型号, '')) <> ''
            """
        )
        return [(clean_text(a), clean_text(b), clean_text(c), clean_text(d), clean_text(e)) for a, b, c, d, e in cursor.fetchall()]
    finally:
        conn.close()


def build_report(rows: list[tuple[str, str, str, str, str]], registry_by_brand: dict[str, dict]) -> dict:
    total_passive_rows = 0
    unresolved_rows = 0
    brand_totals: Counter[str] = Counter()
    brand_unresolved: Counter[str] = Counter()
    type_unresolved: Counter[str] = Counter()
    brand_type_unresolved: Counter[tuple[str, str]] = Counter()
    unresolved_models: defaultdict[tuple[str, str], list[str]] = defaultdict(list)
    unresolved_prefixes: defaultdict[tuple[str, str], Counter[str]] = defaultdict(Counter)

    for brand, component_type, model, series, series_desc in rows:
        if not is_passive_component_type(component_type):
            continue
        total_passive_rows += 1
        brand_totals[brand] += 1
        unresolved = series_looks_missing(series) or is_placeholder_series_desc(brand, series, series_desc, component_type)
        if not unresolved:
            continue

        unresolved_rows += 1
        brand_unresolved[brand] += 1
        type_unresolved[component_type] += 1
        brand_type_unresolved[(brand, component_type)] += 1

        key = (brand, component_type)
        if len(unresolved_models[key]) < 8:
            unresolved_models[key].append(model)
        prefix = infer_prefix_candidate(model, series)
        if prefix:
            unresolved_prefixes[key][prefix] += 1

    top_brand_rows = []
    for brand, count in brand_unresolved.most_common():
        registry = registry_by_brand.get(brand, {})
        top_brand_rows.append(
            {
                "brand": brand,
                "total_rows": brand_totals[brand],
                "unresolved_rows": count,
                "coverage_rate": round((brand_totals[brand] - count) / brand_totals[brand], 4) if brand_totals[brand] else 0.0,
                "registry_status": clean_text(registry.get("status", "")) or "missing",
                "lookup_method": clean_text(registry.get("lookup_method", "")),
                "official_sources": registry.get("official_sources", []),
                "passive_types": registry.get("passive_types", []),
            }
        )

    by_brand_type = []
    for (brand, component_type), count in brand_type_unresolved.most_common():
        registry = registry_by_brand.get(brand, {})
        prefix_counter = unresolved_prefixes[(brand, component_type)]
        by_brand_type.append(
            {
                "brand": brand,
                "component_type": component_type,
                "unresolved_rows": count,
                "registry_status": clean_text(registry.get("status", "")) or "missing",
                "top_prefixes": [{"prefix": prefix, "count": prefix_count} for prefix, prefix_count in prefix_counter.most_common(12)],
                "sample_models": unresolved_models[(brand, component_type)],
                "lookup_method": clean_text(registry.get("lookup_method", "")),
                "official_sources": registry.get("official_sources", []),
            }
        )

    report = {
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "summary": {
            "total_passive_rows": total_passive_rows,
            "unresolved_rows": unresolved_rows,
            "resolved_rows": total_passive_rows - unresolved_rows,
            "distinct_unresolved_brands": len(brand_unresolved),
            "distinct_unresolved_brand_type_pairs": len(brand_type_unresolved),
        },
        "top_unresolved_brands": top_brand_rows,
        "top_unresolved_component_types": [{"component_type": name, "unresolved_rows": count} for name, count in type_unresolved.most_common()],
        "unresolved_brand_type_pairs": by_brand_type,
    }
    return report


def write_markdown(report: dict, output_path: Path) -> None:
    lines: list[str] = []
    summary = report["summary"]
    lines.append("# Passive Series Gap Report")
    lines.append("")
    lines.append(f"- Generated: `{report['generated_at']}`")
    lines.append(f"- Total passive rows: `{summary['total_passive_rows']:,}`")
    lines.append(f"- Unresolved rows: `{summary['unresolved_rows']:,}`")
    lines.append(f"- Resolved rows: `{summary['resolved_rows']:,}`")
    lines.append(f"- Unresolved brands: `{summary['distinct_unresolved_brands']}`")
    lines.append(f"- Unresolved brand/type pairs: `{summary['distinct_unresolved_brand_type_pairs']}`")
    lines.append("")

    lines.append("## Top Unresolved Brands")
    lines.append("")
    lines.append("| Brand | Unresolved | Total | Coverage | Registry | Lookup Method |")
    lines.append("| --- | ---: | ---: | ---: | --- | --- |")
    for item in report["top_unresolved_brands"][:25]:
        lines.append(
            f"| {item['brand']} | {item['unresolved_rows']:,} | {item['total_rows']:,} | {item['coverage_rate']:.2%} | {item['registry_status']} | {item['lookup_method'] or '-'} |"
        )
    lines.append("")

    lines.append("## Top Unresolved Component Types")
    lines.append("")
    lines.append("| Component Type | Unresolved Rows |")
    lines.append("| --- | ---: |")
    for item in report["top_unresolved_component_types"][:20]:
        lines.append(f"| {item['component_type']} | {item['unresolved_rows']:,} |")
    lines.append("")

    lines.append("## Priority Brand / Type Gaps")
    lines.append("")
    for item in report["unresolved_brand_type_pairs"][:60]:
        lines.append(f"### {item['brand']} / {item['component_type']} / {item['unresolved_rows']:,} rows")
        lines.append("")
        lines.append(f"- Registry status: `{item['registry_status']}`")
        if item["lookup_method"]:
            lines.append(f"- Lookup method: {item['lookup_method']}")
        if item["official_sources"]:
            lines.append("- Official sources:")
            for source in item["official_sources"][:5]:
                url = clean_text(source.get("url", ""))
                kind = clean_text(source.get("kind", "")) or "source"
                if url:
                    lines.append(f"  - `{kind}`: {url}")
        if item["top_prefixes"]:
            prefix_text = ", ".join(f"`{entry['prefix']}` ({entry['count']})" for entry in item["top_prefixes"][:10])
            lines.append(f"- Top unresolved prefixes: {prefix_text}")
        if item["sample_models"]:
            lines.append(f"- Sample models: {', '.join(f'`{model}`' for model in item['sample_models'])}")
        lines.append("")

    output_path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Build a passive-component official-series gap report from the local database.")
    parser.add_argument("--db", default=str(DEFAULT_DB_PATH))
    parser.add_argument("--registry", default=str(DEFAULT_REGISTRY_PATH))
    parser.add_argument("--json-out", default=str(DEFAULT_JSON_OUT))
    parser.add_argument("--md-out", default=str(DEFAULT_MD_OUT))
    args = parser.parse_args()

    db_path = Path(args.db).resolve()
    registry_path = Path(args.registry).resolve()
    json_out = Path(args.json_out).resolve()
    md_out = Path(args.md_out).resolve()

    _, registry_by_brand = load_registry(registry_path)
    rows = fetch_passive_rows(db_path)
    report = build_report(rows, registry_by_brand)

    json_out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    write_markdown(report, md_out)

    print(f"[gap-report] rows={report['summary']['total_passive_rows']:,} unresolved={report['summary']['unresolved_rows']:,}")
    print(f"[gap-report] json={json_out}")
    print(f"[gap-report] md={md_out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
