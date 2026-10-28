"""Read-only, explicitly selected BOM-model column comparison.

No matching, pricing, account lookup, file writes or persistent data cache lives
here. Row alignment is the same positional alignment used by BOM output.
"""
from __future__ import annotations

import math
import re

import pandas as pd


def text(value):
    if value is None:
        return ""
    try:
        if pd.isna(value):
            return ""
    except (TypeError, ValueError):
        pass
    return str(value).strip()


def model_key(value):
    # Whitespace/case are harmless display differences. Keep punctuation,
    # hyphens, zero/O, numeric precision and every suffix character intact.
    key = re.sub(r"\s+", "", text(value)).upper()
    return "" if key in {"N/A", "-", "—", "未提供", "未匹配", "无匹配"} else key


def column_choices(original, result, model_columns):
    choices = []
    if not isinstance(original, pd.DataFrame) or not isinstance(result, pd.DataFrame):
        return choices
    labels = [text(column) for column in original.columns]
    for position, label in enumerate(labels):
        duplicate = labels.count(label) > 1
        suffix = f"（第 {position + 1} 栏）" if duplicate else ""
        choices.append({"key": f"original:{position}", "source": "original", "position": position,
                        "label": f"原表 · {label or '未命名栏'}{suffix}"})
    for position, (label, internal) in enumerate(model_columns.items()):
        if position and (internal not in result or not result[internal].map(text).ne("").any()):
            continue
        choices.append({"key": f"matched:{position}", "source": "matched", "column": internal,
                        "label": f"系统 · {label}"})
    return choices


def compare_columns(original, result, selected, *, detail=None):
    if len(selected) != 2 or {item.get("source") for item in selected} != {"original", "matched"}:
        raise ValueError("请分别勾选一个原表栏位和一个系统型号栏位。")
    if len(original) != len(result):
        raise ValueError("原表与匹配结果行数不同，暂不能可靠逐行对比，请先完成当前分页匹配。")
    left = next(item for item in selected if item["source"] == "original")
    right = next(item for item in selected if item["source"] == "matched")
    position = left.get("position")
    if not isinstance(position, int) or not 0 <= position < len(original.columns):
        raise ValueError("所选原表栏位已改变，请重新勾选。")
    source = original.iloc[:, position].tolist()
    target = result[right["column"]].tolist() if right["column"] in result else [""] * len(result)
    row_numbers = result["BOM行号"].tolist() if "BOM行号" in result else list(range(2, len(result) + 2))
    report = {"total": len(source), "same": 0, "different": 0, "missing": 0, "rows": [],
              "left_label": left["label"], "right_label": right["label"]}
    explanations = {}
    for position, (raw_left, raw_right) in enumerate(zip(source, target)):
        left_text, right_text = text(raw_left), text(raw_right)
        a, b = model_key(raw_left), model_key(raw_right)
        if not a or not b:
            status = "两栏均为空" if not a and not b else "原型号为空" if not a else "系统型号为空"
            note = "缺少型号，不能判定一致，请人工核对。"
            report["missing"] += 1
        elif a == b:
            status = "一致"
            note = "型号一致（忽略空格和大小写）。"
            report["same"] += 1
        else:
            status = "不一致"
            pair = (a, b)
            if pair not in explanations:
                try:
                    explanation = text(detail(left_text, right_text)) if detail else ""
                except Exception:
                    # An optional explanation must not fail the BOM page or
                    # change its persisted job/output when a parser rejects a code.
                    explanation = "暂无法解析型号差异，请人工核对；原表、匹配结果和报价未改动。"
                explanations[pair] = explanation or "型号文字不同，需人工确认；不能据此判断电气规格是否等效。"
            note = explanations[pair]
            report["different"] += 1
        row_number = row_numbers[position]
        report["rows"].append({"BOM行号": row_number if text(row_number) else position + 2,
                               "对比状态": status, left["label"]: left_text,
                               right["label"]: right_text, "差异说明": note})
    return report


def display_column_choices(frame, original_column_count):
    """Positional IDs keep duplicate source and generated headers distinct."""
    labels = [text(column) for column in frame.columns]
    choices = []
    for position, label in enumerate(labels):
        origin = "原表" if position < original_column_count else "系统"
        suffix = f"（第 {position + 1} 栏）" if labels.count(label) > 1 else ""
        choices.append({"key": f"column:{position}", "position": position,
                        "source": "original" if position < original_column_count else "matched",
                        "label": f"{origin} · {label or '未命名栏'}{suffix}"})
    return choices


def comparison_revision(frame):
    """Invalidate old button events when rows, values or headers change."""
    import hashlib
    import json
    digest = hashlib.sha256(json.dumps([text(col) for col in frame.columns],
                                      ensure_ascii=True).encode("utf-8"))
    # Text conversion follows comparison semantics, including true nulls.
    values = frame.map(text)
    digest.update(pd.util.hash_pandas_object(values, index=False).values.tobytes())
    return digest.hexdigest()


def selected_display_columns(event, frame, choices, *, revision=None):
    if not isinstance(event, dict) or not event.get("request"):
        return None
    if event.get("revision") != (revision or comparison_revision(frame)):
        return None
    keys = event.get("columns")
    if not isinstance(keys, list) or len(keys) != 2 or not all(isinstance(key, str) for key in keys):
        return None
    by_key = {item["key"]: item for item in choices}
    if keys[0] == keys[1] or any(key not in by_key for key in keys):
        return None
    return [by_key[key] for key in keys]


def compare_display_columns(frame, selected, *, detail=None, row_numbers=None):
    """Compare two explicitly selected displayed columns, without remapping BOM."""
    if len(selected) != 2:
        raise ValueError("请勾选两个不同的栏位。")
    if selected[0].get("source") == "matched" and selected[1].get("source") == "original":
        selected = selected[::-1]
    if selected[0].get("source") == selected[1].get("source"):
        detail = None
    positions = [item.get("position") for item in selected]
    if (any(not isinstance(pos, int) or not 0 <= pos < len(frame.columns) for pos in positions)
            or positions[0] == positions[1]):
        raise ValueError("所选栏位已改变，请重新勾选。")
    left = pd.DataFrame({"value": frame.iloc[:, positions[0]].tolist()})
    right = pd.DataFrame({"value": frame.iloc[:, positions[1]].tolist()})
    if row_numbers is not None:
        if len(row_numbers) != len(frame):
            raise ValueError("原表行号与结果行数不同，请先完成当前工作表匹配。")
        right["BOM行号"] = list(row_numbers)
    pair = [{"source": "original", "position": 0, "label": selected[0]["label"]},
            {"source": "matched", "column": "value", "label": selected[1]["label"]}]
    return compare_columns(left, right, pair, detail=detail)


def header_choices(choices, columns, visible_columns):
    remaining = list(enumerate(columns))
    visible = []
    for column in visible_columns:
        found = next(((index, value) for index, value in remaining if value == column), None)
        if found is None:
            continue
        index, _ = found
        visible.append(choices[index])
        remaining = [item for item in remaining if item[0] != index]
    return visible


def header_component():
    from pathlib import Path
    import streamlit.components.v1 as components
    # Version the frontend identity so already-open BOM fragments load new assets
    # without browser refresh, loss of uploads or a new authentication session.
    return components.declare_component("bom_header_compare_v2", path=str(Path(__file__).with_name("bom_comparison_table")))


def render_table(st, frame, *, table_html, original_column_count, visible_columns,
                 key, detail=None, row_numbers=None, component=None,
                 visible_row_positions=None, table_renderer=None):
    """One component owns the controls, report and annotated result table."""
    choices = display_column_choices(frame, original_column_count)
    headers = header_choices(choices, list(frame.columns), visible_columns)
    revision = comparison_revision(frame)
    # On a component event, Streamlit updates this keyed widget value before
    # rerunning the script. Read it first so the same render receives its report.
    event = st.session_state.get(key + "_table")
    selected = selected_display_columns(event, frame, headers, revision=revision)
    report, payload, error = None, None, ""
    positions = list(range(len(frame))) if visible_row_positions is None else list(visible_row_positions)
    if selected is not None:
        try:
            report = compare_display_columns(frame, selected, detail=detail, row_numbers=row_numbers)
            issues = [index for index, row in enumerate(report["rows"]) if row["对比状态"] != "一致"]
            issues_only = event.get("issues_only") is True and table_renderer is not None
            page_count = max(1, math.ceil(len(issues) / 100)) if issues_only else 1
            try:
                page = min(page_count, max(1, int(event.get("page", 1))))
            except (ValueError, TypeError, OverflowError):
                page = 1
            if issues_only:
                positions = issues[(page - 1) * 100:page * 100]
                # Filter the complete worksheet, not just the main visible page.
                # Restrict to the same authorized/visible columns as before.
                view = frame.iloc[positions, [item["position"] for item in headers]].copy()
                table_html = table_renderer(view)
            if any(type(pos) is not int or not 0 <= pos < len(frame) for pos in positions):
                raise ValueError("当前显示行与原表未对齐，请重新加载结果后比对。")
            payload = {name: report[name] for name in ("total", "same", "different", "missing", "left_label", "right_label")}
            payload.update(columns=list(event["columns"]), request=event["request"],
                           issues_only=issues_only, can_filter=table_renderer is not None,
                           page=page, page_count=page_count, view_count=len(positions),
                           rows=[{"row_number": text(report["rows"][pos]["BOM行号"]),
                                  "status": report["rows"][pos]["对比状态"],
                                  "note": report["rows"][pos]["差异说明"]} for pos in positions])
        except ValueError as exc:
            report, error = None, str(exc)
    invoke = component or header_component()
    invoke(table_html=table_html, headers=headers, revision=revision, report=payload, error=error,
           key=key + "_table", default=None)
    return report
