from __future__ import annotations

import sqlite3
from contextlib import closing
from pathlib import Path


BRAND_COLUMNS = ("品牌", "brand")
TYPE_COLUMNS = ("器件类别", "_component_type", "component_type")
MODEL_COLUMNS = ("型号", "model")
COMPLETENESS_COLUMNS = ("资料完整度", "data_completeness")
MISSING_COLUMNS = ("缺失关键参数", "missing_key_parameters")
CATEGORY_FIELDS = {
    "电阻": ("尺寸（inch）", "容值", "容值单位", "容值误差", "功率"),
    "MLCC": ("尺寸（inch）", "材质（介质）", "容值", "容值单位", "容值误差", "耐压（V）"),
    "晶振": ("尺寸（inch）", "频率", "负载电容（pF）", "频率容差", "工作温度"),
    "振荡器": ("尺寸（inch）", "频率", "额定电压（V）", "频率容差", "工作温度", "输出逻辑"),
    "铝电解": ("容值", "容值单位", "容值误差", "耐压（V）", "安装方式", "工作温度", "直径(mm)", "高度(mm)"),
}


def _quote(name: str) -> str:
    return '"' + str(name).replace('"', '""') + '"'


def _first_existing(columns: set[str], choices) -> str:
    return next((name for name in choices if name in columns), "")


def _table_columns(conn: sqlite3.Connection, table_name: str) -> set[str]:
    return {str(row[1]) for row in conn.execute(f"PRAGMA table_info({_quote(table_name)})")}


def _resolve_table(conn: sqlite3.Connection, preferred: str = "") -> str:
    tables = {str(row[0]) for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    return next((name for name in (preferred, "components_search_core", "components_search", "components") if name and name in tables), "")


def _category_field_columns(category: str, columns: set[str]) -> list[str]:
    selected = []
    for marker, fields in CATEGORY_FIELDS.items():
        if marker.upper() in str(category or "").upper():
            selected.extend(field for field in fields if field in columns)
    return list(dict.fromkeys(selected))


def build_quality_report(database_path: str, table_name: str = "", limit: int = 500) -> dict:
    path = Path(database_path)
    empty = {"summary": {"rows": 0, "groups": 0, "complete_rate": 0.0}, "rows": []}
    if not path.exists():
        return empty
    with closing(sqlite3.connect(str(path), timeout=30)) as conn:
        table = _resolve_table(conn, table_name)
        if not table:
            return empty
        columns = _table_columns(conn, table)
        brand_col = _first_existing(columns, BRAND_COLUMNS)
        type_col = _first_existing(columns, TYPE_COLUMNS)
        model_col = _first_existing(columns, MODEL_COLUMNS)
        completeness_col = _first_existing(columns, COMPLETENESS_COLUMNS)
        missing_col = _first_existing(columns, MISSING_COLUMNS)
        if not type_col or not model_col:
            return empty
        brand_expr = f"COALESCE(NULLIF(TRIM({_quote(brand_col)}), ''), '未标品牌')" if brand_col else "'未标品牌'"
        type_expr = f"COALESCE(NULLIF(TRIM({_quote(type_col)}), ''), '未分类')"
        model_missing_expr = f"TRIM(COALESCE({_quote(model_col)}, '')) = ''"
        source_missing_parts = [model_missing_expr]
        if completeness_col:
            source_missing_parts.append(f"LOWER(TRIM(COALESCE({_quote(completeness_col)}, ''))) IN ('incomplete','partial','不完整','需确认')")
        if missing_col:
            source_missing_parts.append(f"TRIM(COALESCE({_quote(missing_col)}, '')) <> ''")
        source_missing_expr = " OR ".join(source_missing_parts)
        query = f"""
            SELECT {brand_expr} AS brand_name, {type_expr} AS type_name,
                   COUNT(*) AS row_count,
                   SUM(CASE WHEN {model_missing_expr} THEN 1 ELSE 0 END) AS missing_model,
                   SUM(CASE WHEN {source_missing_expr} THEN 1 ELSE 0 END) AS source_incomplete
            FROM {_quote(table)} GROUP BY brand_name, type_name
            ORDER BY source_incomplete DESC, row_count DESC LIMIT ?
        """
        names = ("brand", "component_type", "rows", "missing_model", "source_incomplete")
        groups = [dict(zip(names, row)) for row in conn.execute(query, (max(1, min(int(limit or 500), 5000)),))]
        critical_missing_by_group = {}
        critical_fields_by_type = {}
        for component_type in {str(item["component_type"]) for item in groups}:
            fields = _category_field_columns(component_type, columns)
            critical_fields_by_type[component_type] = fields
            if not fields:
                continue
            conditions = [f"TRIM(COALESCE({_quote(field)}, '')) = ''" for field in fields]
            detail_query = f"""
                SELECT {brand_expr}, SUM(CASE WHEN {' OR '.join(conditions)} THEN 1 ELSE 0 END)
                FROM {_quote(table)} WHERE {type_expr}=? GROUP BY {brand_expr}
            """
            for brand_name, missing_count in conn.execute(detail_query, (component_type,)):
                critical_missing_by_group[(str(brand_name), component_type)] = int(missing_count or 0)
        report_rows = []
        for item in groups:
            component_type = str(item["component_type"])
            fields = critical_fields_by_type.get(component_type, [])
            missing = critical_missing_by_group.get((str(item["brand"]), component_type), int(item["source_incomplete"] or 0))
            total = int(item["rows"] or 0)
            missing = max(missing, int(item["missing_model"] or 0))
            item["critical_fields"] = "、".join(fields) or "型号/来源完整度"
            item["incomplete_rows"] = missing
            item["complete_rate"] = max(0.0, 1.0 - missing / total) if total else 0.0
            report_rows.append(item)
    total_rows = sum(int(item["rows"] or 0) for item in report_rows)
    incomplete_rows = sum(int(item["incomplete_rows"] or 0) for item in report_rows)
    return {"summary": {"rows": total_rows, "groups": len(report_rows),
                         "complete_rate": max(0.0, 1.0 - incomplete_rows / total_rows) if total_rows else 0.0},
            "rows": report_rows}
