from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import shutil
import sqlite3
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parent
DB_PATH = ROOT / "components.db"
REPORT_JSON = ROOT / "reports" / "key_parameter_coverage.json"
REPORT_MD = ROOT / "reports" / "key_parameter_coverage.md"

PANASONIC_CMC_URL = "https://industrial.panasonic.com/ww/products/pt/noise-filters/models"
VISHAY_NTCS_SOURCES = {
    "0402": "https://www.vishay.com/docs/29003/ntcs0402e3t.pdf",
    "0603": "https://www.vishay.com/docs/29056/ntcs0603e3t.pdf",
    "0805": "https://www.vishay.com/docs/29044/ntcs0805e3t.pdf",
}

VARISTOR_TYPES = {"贴片压敏电阻", "引线型压敏电阻", "引线型压敏电阻（MOV）"}
THERMISTOR_TYPES = {"热敏电阻", "热敏电阻（NTC Thermistor）", "功率热敏电阻（NTC Thermistor）"}
TARGET_TYPES = {
    "MLCC", "铝电解电容", "薄膜电容", "功率电感", "射频电感", "磁珠", "共模电感",
    "晶振", "振荡器", *VARISTOR_TYPES, *THERMISTOR_TYPES,
}

COPY_FIELDS = [
    "尺寸（inch）", "材质（介质）", "容值", "容值单位", "容值误差", "耐压（V）",
    "尺寸（mm）", "脚距（mm）", "阻值@25C", "阻值单位", "阻值误差", "B值", "B值条件",
    "电感值", "电感单位", "电感误差", "额定电流", "DCR", "阻抗@100MHz", "共模阻抗",
    "阻抗单位", "回路数", "频率", "输出频率", "频率单位", "频差（ppm）",
    "负载电容（pF）", "电源电压", "输出类型",
]

TOLERANCE_CODES = {"D": "±0.5%", "F": "±1%", "G": "±2%", "H": "±3%", "J": "±5%", "K": "±10%", "L": "±15%", "M": "±20%"}

VISHAY_NTCS_B_VALUES = {
    "0402": {
        ("472", "M"): "3595", ("103", "L1"): "3490", ("103", "H"): "3950",
        ("153", "H"): "3965", ("223", "M"): "3590", ("333", "M"): "3670",
        ("473", "X"): "4075", ("683", "H"): "3910", ("104", "H"): "3950",
        ("104", "X"): "4311", ("474", "H"): "3807",
    },
    "0603": {
        ("102", "L"): "3170", ("152", "L"): "3280", ("202", "L"): "3420",
        ("222", "M"): "3520", ("272", "M"): "3600", ("472", "H"): "3830",
        ("502", "L"): "3480", ("103", "L"): "3435", ("103", "M"): "3610",
        ("103", "H"): "3960", ("153", "M"): "3600", ("223", "M"): "3730",
        ("333", "H"): "3860", ("473", "H"): "3960", ("683", "H"): "3985",
        ("104", "X"): "4100",
    },
    "0805": {
        ("102", "L"): "3370", ("152", "L"): "3420", ("222", "M"): "3600",
        ("472", "M"): "3500", ("502", "L"): "3480", ("103", "L"): "3430",
        ("103", "M"): "3570", ("103", "H"): "3940", ("153", "M"): "3700",
        ("223", "H"): "3800", ("333", "H"): "3920", ("473", "H"): "3960",
        ("683", "X"): "4100", ("104", "M"): "3590", ("104", "X"): "4100",
        ("334", "H"): "3930", ("474", "X"): "4025", ("684", "X"): "4125",
    },
}

METRIC_TO_INCH = {
    (0.60, 0.30): "0201", (0.85, 0.65): "0302", (1.00, 0.50): "0402",
    (1.25, 1.00): "0504", (1.60, 0.80): "0603", (2.00, 1.00): "0804",
    (2.00, 1.20): "0805", (2.00, 1.25): "0805", (2.50, 2.00): "1008",
    (3.20, 1.60): "1206", (3.20, 2.50): "1210", (4.50, 3.20): "1812",
    (5.00, 2.50): "2010", (5.00, 5.00): "2020", (5.70, 5.00): "2220",
    (6.30, 3.20): "2512",
}

COVERAGE_GROUPS = {
    "MLCC": (["MLCC"], [("尺寸", ["尺寸（inch）"]), ("介质", ["材质（介质）"]), ("容值", ["容值"]), ("误差", ["容值误差"]), ("耐压", ["耐压（V）"])]),
    "铝电解电容": (["铝电解电容"], [("容值", ["容值"]), ("耐压", ["耐压（V）"]), ("尺寸", ["尺寸（mm）"]), ("ESR", ["ESR"]), ("纹波电流", ["纹波电流"]), ("寿命", ["寿命（h）"])]),
    "热敏电阻": (sorted(THERMISTOR_TYPES), [("R25", ["阻值@25C"]), ("R25误差", ["阻值误差"]), ("B值", ["B值"]), ("尺寸", ["尺寸（inch）", "尺寸（mm）"])]),
    "压敏电阻": (sorted(VARISTOR_TYPES), [("压敏电压", ["压敏电压"]), ("尺寸", ["尺寸（inch）", "尺寸（mm）", "直径（mm）"])]),
    "功率/射频电感": (["功率电感", "射频电感"], [("电感值", ["电感值"]), ("误差", ["电感误差"]), ("额定电流", ["额定电流"]), ("DCR", ["DCR"]), ("尺寸", ["尺寸（inch）", "尺寸（mm）"])]),
    "磁珠": (["磁珠"], [("阻抗", ["阻抗@100MHz"]), ("额定电流", ["额定电流"]), ("DCR", ["DCR"]), ("尺寸", ["尺寸（inch）", "尺寸（mm）"])]),
    "共模电感": (["共模电感"], [("阻抗或电感值", ["共模阻抗", "电感值"]), ("额定电流", ["额定电流"]), ("DCR", ["DCR"]), ("回路数", ["回路数"]), ("尺寸", ["尺寸（inch）", "尺寸（mm）"])]),
    "晶振": (["晶振"], [("频率", ["频率"]), ("频差", ["频差（ppm）"]), ("尺寸", ["尺寸（inch）"]), ("负载电容", ["负载电容（pF）"])]),
    "振荡器": (["振荡器"], [("频率", ["输出频率"]), ("频差", ["频差（ppm）"]), ("尺寸", ["尺寸（inch）"]), ("电源电压", ["电源电压"]), ("输出类型", ["输出类型"])]),
}


def clean(value: object) -> str:
    text = str(value or "").strip()
    return "" if text.lower() in {"nan", "none"} else text


def decode_eia(code: str) -> str:
    if not re.fullmatch(r"\d{3}", code):
        return ""
    return str(int(code[:2]) * (10 ** int(code[2])))


def nominal_varistor_from_model(model: str) -> tuple[str, str, str]:
    upper = clean(model).upper().replace(" ", "")
    patterns = (
        re.compile(r"(?<!\d)(?P<body>0?5|0?7|10|14|20|25|32)D(?P<code>\d{3})(?P<tol>[KLMPSJ])"),
        re.compile(r"(?<!\d)(?P<code>\d{3})(?P<tol>K)?D(?P<body>0?5|0?7|10|14|20|25|32)(?!\d)"),
        re.compile(r"^JVR(?P<body>\d{2})[NSU](?P<code>\d{3})(?P<tol>[KLMP])"),
    )
    for pattern in patterns:
        match = pattern.search(upper)
        if match:
            body = str(int(match.group("body")))
            return decode_eia(match.group("code")), body, TOLERANCE_CODES.get(clean(match.groupdict().get("tol", "")), "")
    return "", "", ""


def first_number(value: object) -> float | None:
    match = re.search(r"\d+(?:\.\d+)?", clean(value).replace(",", ""))
    return float(match.group()) if match else None


def infer_inch_from_mm(value: object) -> str:
    nums = [float(item) for item in re.findall(r"\d+(?:\.\d+)?", clean(value))]
    if len(nums) < 2:
        return ""
    length, width = nums[0], nums[1]
    for (metric_length, metric_width), inch in METRIC_TO_INCH.items():
        if abs(length - metric_length) <= 0.08 and abs(width - metric_width) <= 0.08:
            return inch
    return ""


def append_note(existing: object, note: str) -> str:
    current = clean(existing)
    if note in current:
        return current
    return f"{current} | {note}" if current else note


def ensure_columns(conn: sqlite3.Connection) -> None:
    columns = {row[1] for row in conn.execute('PRAGMA table_info("components")')}
    for column in ("压敏电压", "钳位电压"):
        if column not in columns:
            conn.execute(f'ALTER TABLE components ADD COLUMN "{column}" TEXT')


def update_row(conn: sqlite3.Connection, rowid: int, patch: dict[str, object], changed: set[int], dry_run: bool) -> None:
    patch = {key: clean(value) for key, value in patch.items() if clean(value) != ""}
    if not patch:
        return
    if not dry_run:
        assignments = ", ".join(f'"{key}" = ?' for key in patch)
        conn.execute(f'UPDATE components SET {assignments} WHERE rowid = ?', [*patch.values(), rowid])
    changed.add(rowid)


def backfill_unique_model_values(conn: sqlite3.Connection, changed: set[int], dry_run: bool) -> int:
    placeholders = ",".join("?" for _ in TARGET_TYPES)
    frame = pd.read_sql_query(
        f'SELECT rowid, 型号, 器件类型, {",".join(f"[{field}]" for field in COPY_FIELDS)} FROM components WHERE 器件类型 IN ({placeholders})',
        conn,
        params=sorted(TARGET_TYPES),
    ).fillna("")
    updates = 0
    for field in COPY_FIELDS:
        populated = frame[frame[field].astype(str).str.strip().ne("")][["型号", field]].drop_duplicates()
        counts = populated.groupby("型号")[field].nunique()
        safe_models = set(counts[counts.eq(1)].index)
        if not safe_models:
            continue
        values = populated[populated["型号"].isin(safe_models)].drop_duplicates("型号").set_index("型号")[field].to_dict()
        missing = frame[frame[field].astype(str).str.strip().eq("") & frame["型号"].isin(safe_models)]
        if field == COPY_FIELDS[0]:
            component_type_column = frame.columns[2]
            missing = missing[~missing[component_type_column].isin(VARISTOR_TYPES)]
        for row in missing.itertuples(index=False):
            update_row(conn, int(row.rowid), {field: values[row.型号]}, changed, dry_run)
            updates += 1
    return updates


def backfill_varistors(conn: sqlite3.Connection, changed: set[int], dry_run: bool) -> int:
    placeholders = ",".join("?" for _ in VARISTOR_TYPES)
    rows = conn.execute(
        f'SELECT rowid, 型号, [耐压（V）], [压敏电压], [钳位电压], [容值误差], [直径（mm）], [尺寸（mm）], 封装代码, 数据来源, 数据状态, 校验备注, _model_rule_authority FROM components WHERE 器件类型 IN ({placeholders})',
        sorted(VARISTOR_TYPES),
    ).fetchall()
    count = 0
    for row in rows:
        rowid, model, voltage, nominal, clamp, tolerance, diameter, size_mm, package, source, status, note, authority = row
        decoded, body, decoded_tolerance = nominal_varistor_from_model(model)
        if not decoded:
            continue
        patch: dict[str, str] = {}
        if clean(nominal) == "":
            patch["压敏电压"] = decoded
        existing_voltage = first_number(voltage)
        if clean(clamp) == "" and existing_voltage is not None and abs(existing_voltage - float(decoded)) > 1e-9:
            patch["钳位电压"] = clean(voltage)
        if body:
            if clean(diameter) == "":
                patch["直径（mm）"] = body
            if clean(size_mm) == "":
                patch["尺寸（mm）"] = f"{body}D"
            if clean(package) == "":
                patch["封装代码"] = f"{body}D"
        if clean(tolerance) == "" and decoded_tolerance:
            patch["容值误差"] = decoded_tolerance
        if clean(source) == "":
            patch["数据来源"] = "标准MOV型号编码规则"
        if clean(status) == "":
            patch["数据状态"] = "型号编码规则推导"
        patch["校验备注"] = append_note(note, f"MOV型号编码解析：标称压敏电压={decoded}V，盘径={body or '未编码'}mm")
        if clean(authority) == "":
            patch["_model_rule_authority"] = "standard_mov_nominal_code"
        if patch:
            update_row(conn, int(rowid), patch, changed, dry_run)
            count += 1
    return count


def load_panasonic_cmc_table() -> pd.DataFrame:
    tables = pd.read_html(PANASONIC_CMC_URL)
    for table in tables:
        if {"Parts no", "Impedance [Common Mode] (Ω)", "Rated Current [DC] (mA)"}.issubset(set(table.columns)):
            return table.fillna("")
    raise RuntimeError("Panasonic official common-mode table was not found")


def backfill_panasonic_cmc(conn: sqlite3.Connection, changed: set[int], dry_run: bool) -> int:
    table = load_panasonic_cmc_table()
    count = 0
    for item in table.to_dict("records"):
        model = clean(item.get("Parts no", ""))
        existing = conn.execute(
            'SELECT rowid, [尺寸（inch）], 校验备注 FROM components WHERE 器件类型="共模电感" AND 型号=?',
            (model,),
        ).fetchall()
        if not existing:
            continue
        size_lw = clean(item.get("Size [L×W] (mm)", "")).replace("0.+85", "0.85")
        height = clean(item.get("Height (mm)", ""))
        numbers = re.findall(r"\d+(?:\.\d+)?", size_lw)
        length = numbers[0] if len(numbers) >= 1 else ""
        width = numbers[1] if len(numbers) >= 2 else ""
        size_mm = "×".join(part for part in (length, width, height) if part)
        impedance = clean(item.get("Impedance [Common Mode] (Ω)", ""))
        current = clean(item.get("Rated Current [DC] (mA)", ""))
        dcr = clean(item.get("DC Resistance [max.] (Ω)", ""))
        circuits = clean(item.get("Number of circuit", ""))
        for rowid, inch, note in existing:
            patch = {
                "共模阻抗": impedance,
                "阻抗单位": "Ω",
                "额定电流": f"{current}mA" if current else "",
                "DCR": f"{dcr}Ω max" if dcr else "",
                "回路数": circuits,
                "尺寸（mm）": size_mm,
                "长度（mm）": length,
                "宽度（mm）": width,
                "高度（mm）": height,
                "尺寸（inch）": clean(inch) or infer_inch_from_mm(size_lw),
                "官网链接": f"https://industrial.panasonic.com/ww/products/pt/noise-filters/models/{model}",
                "数据来源": "Panasonic official Common Mode Noise Filters model table",
                "数据状态": "官方网页规格",
                "校验时间": dt.date.today().isoformat(),
                "校验备注": append_note(note, "Panasonic官方型号表逐型号补全"),
            }
            update_row(conn, int(rowid), patch, changed, dry_run)
            count += 1
    return count


def backfill_vishay_ntcs(conn: sqlite3.Connection, changed: set[int], dry_run: bool) -> int:
    rows = conn.execute(
        'SELECT rowid, 型号, 校验备注 FROM components WHERE 品牌 LIKE "%Vishay%" AND 器件类型 LIKE "%热敏%" AND 型号 LIKE "NTCS%E3%"'
    ).fetchall()
    count = 0
    pattern = re.compile(r"^NTCS(?P<size>0402|0603|0805)E3(?P<code>\d{3})(?P<tol>[FGHJ])(?P<curve>L1|L|M|H|X)T", re.I)
    dimensions = {"0402": ("1.0", "0.5", "0.5"), "0603": ("1.6", "0.8", "0.8"), "0805": ("2.0", "1.25", "0.8")}
    for rowid, model, note in rows:
        match = pattern.match(clean(model).upper())
        if not match:
            continue
        size = match.group("size")
        code = match.group("code")
        curve = match.group("curve")
        b_value = VISHAY_NTCS_B_VALUES.get(size, {}).get((code, curve), "")
        if not b_value:
            continue
        length, width, height = dimensions[size]
        patch = {
            "阻值@25C": decode_eia(code),
            "阻值单位": "Ω",
            "阻值误差": TOLERANCE_CODES[match.group("tol")],
            "B值": b_value,
            "B值条件": "25/85",
            "尺寸（inch）": size,
            "封装代码": size,
            "尺寸（mm）": f"{length}×{width}×{height}",
            "长度（mm）": length,
            "宽度（mm）": width,
            "高度（mm）": height,
            "安装方式": "贴片",
            "官网链接": VISHAY_NTCS_SOURCES[size],
            "数据来源": "Vishay official NTCS datasheet ordering table",
            "数据状态": "官方PDF规格表/命名规则",
            "校验时间": dt.date.today().isoformat(),
            "校验备注": append_note(note, f"Vishay NTCS官方订购表：R25={decode_eia(code)}Ω，B25/85={b_value}K"),
            "_model_rule_authority": "vishay_ntcs_official_pdf",
        }
        update_row(conn, int(rowid), patch, changed, dry_run)
        count += 1
    return count


def backfill_metric_sizes(conn: sqlite3.Connection, changed: set[int], dry_run: bool) -> int:
    placeholders = ",".join("?" for _ in TARGET_TYPES)
    rows = conn.execute(
        f'SELECT rowid, [尺寸（mm）] FROM components WHERE 器件类型 IN ({placeholders}) AND TRIM(COALESCE([尺寸（inch）], ""))="" AND TRIM(COALESCE([尺寸（mm）], ""))<>""',
        sorted(TARGET_TYPES),
    ).fetchall()
    count = 0
    for rowid, size_mm in rows:
        inch = infer_inch_from_mm(size_mm)
        if inch:
            update_row(conn, int(rowid), {"尺寸（inch）": inch, "尺寸来源": "已记录毫米尺寸换算"}, changed, dry_run)
            count += 1
    return count


def coverage_snapshot(conn: sqlite3.Connection) -> dict[str, object]:
    result: dict[str, object] = {"generated_at": dt.datetime.now().isoformat(timespec="seconds"), "groups": []}
    columns = {row[1] for row in conn.execute('PRAGMA table_info("components")')}
    for group, (types, fields) in COVERAGE_GROUPS.items():
        placeholders = ",".join("?" for _ in types)
        total = int(conn.execute(f'SELECT COUNT(*) FROM components WHERE 器件类型 IN ({placeholders})', types).fetchone()[0])
        field_rows = []
        for label, alternatives in fields:
            available = [column for column in alternatives if column in columns]
            if not available:
                filled = 0
            else:
                predicate = " OR ".join(f'TRIM(COALESCE("{column}", ""))<>""' for column in available)
                filled = int(conn.execute(f'SELECT COUNT(*) FROM components WHERE 器件类型 IN ({placeholders}) AND ({predicate})', types).fetchone()[0])
            field_rows.append({"field": label, "filled": filled, "total": total, "coverage": round(filled / total, 6) if total else 0})
        result["groups"].append({"group": group, "total": total, "fields": field_rows})
    return result


def write_report(before: dict[str, object], after: dict[str, object], stats: dict[str, int]) -> None:
    REPORT_JSON.parent.mkdir(parents=True, exist_ok=True)
    payload = {"before": before, "after": after, "backfill_stats": stats}
    REPORT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    before_groups = {item["group"]: item for item in before["groups"]}
    lines = ["# Key Parameter Coverage", "", f"- Generated: `{after['generated_at']}`", "", "## Backfill", ""]
    for key, value in stats.items():
        lines.append(f"- {key}: `{value}`")
    lines.extend(["", "## Coverage", "", "| Group | Field | Before | After |", "|---|---|---:|---:|"])
    for after_group in after["groups"]:
        prior = {item["field"]: item for item in before_groups[after_group["group"]]["fields"]}
        for field in after_group["fields"]:
            old = prior[field["field"]]
            lines.append(f"| {after_group['group']} | {field['field']} | {old['filled']}/{old['total']} ({old['coverage']:.2%}) | {field['filled']}/{field['total']} ({field['coverage']:.2%}) |")
    REPORT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def backup_database() -> Path:
    stamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup = DB_PATH.with_name(f"{DB_PATH.name}.key_parameter_{stamp}.bak")
    shutil.copy2(DB_PATH, backup)
    return backup


def load_changed_rows(conn: sqlite3.Connection, rowids: set[int]) -> pd.DataFrame:
    frames = []
    ordered = sorted(rowids)
    for offset in range(0, len(ordered), 700):
        chunk = ordered[offset : offset + 700]
        placeholders = ",".join("?" for _ in chunk)
        frames.append(pd.read_sql_query(f"SELECT * FROM components WHERE rowid IN ({placeholders})", conn, params=chunk))
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()


def refresh_caches(changed_rows: pd.DataFrame) -> None:
    if changed_rows.empty:
        return
    import component_matcher as cm
    from incremental_semiconductor_cache_update import refresh_search_sidecar_rows
    from sync_selected_cache_rows import stream_replace_prepared_rows

    prepared = cm.prepare_search_dataframe(changed_rows)
    removed, inserted = stream_replace_prepared_rows(prepared)
    counts = refresh_search_sidecar_rows(prepared)
    print(f"cache_prepared_removed={removed}")
    print(f"cache_prepared_inserted={inserted}")
    print(f"cache_search_core_rows={counts.get(cm.COMPONENTS_SEARCH_CORE_TABLE, 0)}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Backfill source-verifiable key passive component parameters.")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--no-backup", action="store_true")
    parser.add_argument("--skip-cache", action="store_true")
    parser.add_argument("--audit-only", action="store_true")
    args = parser.parse_args()

    if not DB_PATH.exists():
        raise FileNotFoundError(DB_PATH)
    if args.audit_only:
        with sqlite3.connect(DB_PATH, timeout=120) as conn:
            ensure_columns(conn)
            current = coverage_snapshot(conn)
        if REPORT_JSON.exists():
            previous = json.loads(REPORT_JSON.read_text(encoding="utf-8"))
            before = previous.get("before", current)
            stats = previous.get("backfill_stats", {})
        else:
            before = current
            stats = {}
        write_report(before, current, stats)
        print(json.dumps({"audit_only": True, "groups": len(current["groups"])}, ensure_ascii=False))
        return 0
    if not args.dry_run and not args.no_backup:
        print(f"backup={backup_database()}")

    changed: set[int] = set()
    with sqlite3.connect(DB_PATH, timeout=120) as conn:
        conn.execute("PRAGMA busy_timeout=120000")
        if args.dry_run:
            conn.execute("BEGIN")
        ensure_columns(conn)
        before = coverage_snapshot(conn)
        stats = {
            "unique_model_values": backfill_unique_model_values(conn, changed, args.dry_run),
            "varistor_model_codes": backfill_varistors(conn, changed, args.dry_run),
            "panasonic_common_mode": backfill_panasonic_cmc(conn, changed, args.dry_run),
            "vishay_ntcs": backfill_vishay_ntcs(conn, changed, args.dry_run),
            "metric_sizes": backfill_metric_sizes(conn, changed, args.dry_run),
        }
        if args.dry_run:
            conn.rollback()
            after = before
            changed_rows = pd.DataFrame()
        else:
            conn.commit()
            after = coverage_snapshot(conn)
            changed_rows = load_changed_rows(conn, changed)

    if not args.dry_run:
        write_report(before, after, stats)
        if not args.skip_cache:
            refresh_caches(changed_rows)
    print(json.dumps({"dry_run": args.dry_run, "changed_rows": len(changed), **stats}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
