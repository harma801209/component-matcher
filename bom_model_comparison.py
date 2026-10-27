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


def render_panel(st, original, result, *, key, model_columns, detail=None):
    """Compare the entire active sheet, independent of the main-table filters."""
    choices = column_choices(original, result, model_columns)
    by_key = {item["key"]: item for item in choices}
    selection_key = key + "_columns"
    raw_stored = st.session_state.get(selection_key, [])
    stored = raw_stored if isinstance(raw_stored, list) else []
    valid = list(dict.fromkeys(item for item in stored if item in by_key))[:2]
    if raw_stored != valid:
        st.session_state[selection_key] = valid
    with st.expander("匹配后型号对比", expanded=True):
        selected_keys = st.multiselect(
            "勾选要对比的两个栏位", list(by_key), format_func=lambda value: by_key[value]["label"],
            max_selections=2, key=selection_key, placeholder="例如：原表 · MPN ＋ 系统 · 匹配型号",
        )
        st.caption("对比当前工作表全部物料，不受复核筛选和每页显示影响；忽略空格和大小写，不改动原表、匹配结果或报价。文字一致不代替规格校验。")
        if len(selected_keys) != 2:
            st.info("勾选一个原表型号栏位和一个系统匹配型号栏位后，自动检查是否一致。")
            return None
        if any(value not in by_key for value in selected_keys):
            st.warning("所选栏位已改变，请重新勾选。")
            return None
        try:
            report = compare_columns(original, result, [by_key[value] for value in selected_keys], detail=detail)
        except ValueError as exc:
            st.warning(str(exc))
            return None
        summary = (f"共 {report['total']} 行 · 一致 {report['same']} 行 · "
                   f"不一致 {report['different']} 行 · 缺失型号 {report['missing']} 行")
        if report["different"] or report["missing"]:
            st.warning(summary + "。请核对下方差异说明，不能直接当成同一型号。")
        else:
            st.success(summary + "。所选两栏型号全部一致。")
        issues_only = st.checkbox("仅显示不一致和缺失", value=True, key=key + "_issues_only")
        rows = [row for row in report["rows"] if not issues_only or row["对比状态"] != "一致"]
        if not rows:
            return report
        page_count = max(1, math.ceil(len(rows) / 100))
        page = 1
        if page_count > 1:
            page_key = key + "_page_" + "_".join(selected_keys) + f"_{int(issues_only)}"
            current = st.session_state.get(page_key, 1)
            try:
                current = min(page_count, max(1, int(current)))
            except (TypeError, ValueError):
                current = 1
            st.session_state[page_key] = current
            page = int(st.number_input("对比结果页码", min_value=1, max_value=page_count, step=1, key=page_key))
        start = (page - 1) * 100
        visible = rows[start:start + 100]
        st.caption(f"对比明细第 {start + 1}–{start + len(visible)} 行 / 共 {len(rows)} 行；BOM行号对应原表物料行。")
        st.dataframe(pd.DataFrame(visible), hide_index=True, use_container_width=True,
                     height=min(480, 38 + 56 * len(visible)))
        return report
