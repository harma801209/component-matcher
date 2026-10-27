import unittest
from contextlib import nullcontext

import pandas as pd

from bom_model_comparison import column_choices, compare_columns, model_key, render_panel


FIELDS = {"匹配型号": "自有型号", "匹配型号2": "自有型号2"}


class FakeUI:
    def __init__(self, selected=None, issues_only=True):
        self.session_state = {"check_columns": selected or [], "member_token": "KEEP", "cost_scope": "KEEP"}
        self.issues_only = issues_only
        self.messages = []
        self.tables = []

    def expander(self, *args, **kwargs):
        return nullcontext()

    def multiselect(self, label, options, **kwargs):
        self.asserted_options = [(key, kwargs["format_func"](key)) for key in options]
        self.max_selections = kwargs["max_selections"]
        return self.session_state.get(kwargs["key"], [])

    def caption(self, message):
        self.messages.append(("caption", message))

    def info(self, message):
        self.messages.append(("info", message))

    def warning(self, message):
        self.messages.append(("warning", message))

    def success(self, message):
        self.messages.append(("success", message))

    def checkbox(self, label, **kwargs):
        return self.issues_only

    def number_input(self, label, **kwargs):
        return self.session_state[kwargs["key"]]

    def dataframe(self, frame, **kwargs):
        self.tables.append(frame.copy(deep=True))


class BomModelComparisonTests(unittest.TestCase):
    def frames(self):
        original = pd.DataFrame({"MPN": ["FRC0402F2200TS", "FRC0402J221 TS", "", "FRC0402J222TS", None]}, index=[5, 9, 12, 20, 40])
        result = pd.DataFrame({"自有型号": ["FRC0402J220 TS", "frc0402j221ts", "FRC0402J220TS", "", pd.NA],
                               "BOM行号": [2, 3, 4, 5, 6]}, index=[1, 4, 8, 13, 21])
        return original, result

    def selected(self, original, result, left="original:0", right="matched:0"):
        by_key = {item["key"]: item for item in column_choices(original, result, FIELDS)}
        return [by_key[left], by_key[right]]

    def test_whitespace_and_case_only_are_ignored(self):
        self.assertEqual(model_key(" FRC0402J220\tTS\n"), "FRC0402J220TS")
        self.assertEqual(model_key("frc0402j220\u00a0TS"), "FRC0402J220TS")
        for a, b in [("RC-123", "RC123"), ("RC/123", "RC123"), ("FRC0O", "FRC00"),
                     ("FPM253WFR002TM", "FPM253WFR002TML")]:
            self.assertNotEqual(model_key(a), model_key(b))

    def test_all_rows_and_blank_sides_are_counted_separately(self):
        original, result = self.frames()
        report = compare_columns(original, result, self.selected(original, result))
        self.assertEqual({key: report[key] for key in ("total", "same", "different", "missing")},
                         {"total": 5, "same": 1, "different": 1, "missing": 3})
        self.assertEqual([row["对比状态"] for row in report["rows"]],
                         ["不一致", "一致", "原型号为空", "系统型号为空", "两栏均为空"])
        self.assertEqual([row["BOM行号"] for row in report["rows"]], [2, 3, 4, 5, 6])

    def test_read_only_preserves_original_output_prices_and_attrs(self):
        original, result = self.frames()
        result["自有成本"] = [1, 2, 3, 4, 5]
        original.attrs["source"] = {"preserve": True}
        result.attrs["metrics"] = {"preserve": True}
        before_original, before_result = original.copy(deep=True), result.copy(deep=True)
        compare_columns(original, result, self.selected(original, result))
        pd.testing.assert_frame_equal(original, before_original)
        pd.testing.assert_frame_equal(result, before_result)
        self.assertEqual(original.attrs, before_original.attrs)
        self.assertEqual(result.attrs, before_result.attrs)

    def test_placeholder_pairs_are_missing_not_consistent(self):
        original = pd.DataFrame({"MPN": ["N/A", "未提供", "—", float("nan")]})
        result = pd.DataFrame({"自有型号": ["N/A", "未提供", "—", None]})
        report = compare_columns(original, result, self.selected(original, result))
        self.assertEqual(report["same"], 0)
        self.assertEqual(report["missing"], 4)

    def test_duplicate_original_headers_and_system_collision_are_unambiguous(self):
        original = pd.DataFrame([["A", "B", "C"]], columns=["MPN", "MPN", "匹配型号"])
        result = pd.DataFrame({"自有型号": ["B"]})
        choices = column_choices(original, result, FIELDS)
        self.assertEqual(len({choice["label"] for choice in choices}), 4)
        report = compare_columns(original, result, self.selected(original, result, "original:1"))
        self.assertEqual(report["same"], 1)
        self.assertIn("第 2 栏", report["left_label"])

    def test_selecting_system_first_still_displays_original_first(self):
        original, result = self.frames()
        selected = self.selected(original, result)
        report = compare_columns(original, result, selected[::-1])
        self.assertEqual(report["left_label"], "原表 · MPN")
        self.assertEqual(report["right_label"], "系统 · 匹配型号")

    def test_multiple_system_slots_have_separate_choices(self):
        original = pd.DataFrame({"MPN": ["B"]})
        result = pd.DataFrame({"自有型号": ["A"], "自有型号2": ["B"]})
        report = compare_columns(original, result, self.selected(original, result, right="matched:1"))
        self.assertEqual(report["same"], 1)
        self.assertEqual(report["right_label"], "系统 · 匹配型号2")

    def test_length_mismatch_and_wrong_origin_fail_closed(self):
        original, result = self.frames()
        with self.assertRaisesRegex(ValueError, "行数不同"):
            compare_columns(original, result.iloc[:2], self.selected(original, result))
        selected = self.selected(original, result)
        with self.assertRaisesRegex(ValueError, "分别勾选"):
            compare_columns(original, result, [selected[0], selected[0]])
        with self.assertRaisesRegex(ValueError, "分别勾选"):
            compare_columns(original, result, [])

    def test_unknown_models_and_multi_value_cells_are_not_equated(self):
        original = pd.DataFrame({"MPN": ["UNKNOWN123", "A; B"]})
        result = pd.DataFrame({"自有型号": ["UNKNOWN124", "B; A"]})
        report = compare_columns(original, result, self.selected(original, result))
        self.assertEqual(report["different"], 2)
        self.assertIn("不能据此判断", report["rows"][0]["差异说明"])

    def test_detail_is_local_to_call_and_decoded_once_per_unique_pair(self):
        original = pd.DataFrame({"MPN": ["A", "a ", "A"]})
        result = pd.DataFrame({"自有型号": ["B", " b", "C"]})
        calls = []
        def detail(a, b):
            calls.append((a, b))
            return "需确认：" + a + " / " + b
        report = compare_columns(original, result, self.selected(original, result), detail=detail)
        self.assertEqual(len(calls), 2)
        self.assertEqual(report["rows"][0]["差异说明"], report["rows"][1]["差异说明"])

    def test_unrecognized_model_parser_error_does_not_fail_comparison(self):
        original = pd.DataFrame({"MPN": ["UNKNOWN123"]})
        result = pd.DataFrame({"自有型号": ["UNKNOWN124"]})
        def broken_detail(a, b):
            raise ValueError("unrecognized code")
        report = compare_columns(original, result, self.selected(original, result), detail=broken_detail)
        self.assertEqual(report["different"], 1)
        self.assertIn("暂无法解析", report["rows"][0]["差异说明"])

    def test_ui_waits_for_selection_then_automatically_warns(self):
        original, result = self.frames()
        ui = FakeUI()
        self.assertIsNone(render_panel(ui, original, result, key="check", model_columns=FIELDS))
        self.assertFalse(ui.tables)
        ui.session_state["check_columns"] = ["original:0", "matched:0"]
        report = render_panel(ui, original, result, key="check", model_columns=FIELDS)
        self.assertEqual(report["total"], 5)
        self.assertTrue(any(kind == "warning" and "不一致 1 行" in message for kind, message in ui.messages))
        self.assertEqual(len(ui.tables[0]), 4)
        self.assertEqual(ui.session_state["member_token"], "KEEP")
        self.assertEqual(ui.session_state["cost_scope"], "KEEP")
        self.assertEqual(ui.max_selections, 2)

    def test_consistent_ui_and_show_all_and_stale_choice_reset(self):
        original = pd.DataFrame({"MPN": ["A", "B"]})
        result = pd.DataFrame({"自有型号": ["a", "b"]})
        ui = FakeUI(["original:0", "matched:0"], issues_only=False)
        report = render_panel(ui, original, result, key="check", model_columns=FIELDS)
        self.assertEqual(report["same"], 2)
        self.assertTrue(any(kind == "success" for kind, message in ui.messages))
        self.assertEqual(len(ui.tables[0]), 2)
        ui.session_state["check_columns"] = ["original:99", "matched:0"]
        self.assertIsNone(render_panel(ui, original, result, key="check", model_columns=FIELDS))
        self.assertEqual(ui.session_state["check_columns"], ["matched:0"])

    def test_comparison_paging_does_not_reduce_summary_coverage(self):
        original = pd.DataFrame({"MPN": ["A"] * 250})
        result = pd.DataFrame({"自有型号": ["B"] * 250})
        ui = FakeUI(["original:0", "matched:0"])
        ui.session_state["check_page_original:0_matched:0_1"] = 99
        report = render_panel(ui, original, result, key="check", model_columns=FIELDS)
        self.assertEqual(report["different"], 250)
        self.assertEqual(len(ui.tables[0]), 50)
        self.assertEqual(ui.tables[0].iloc[0]["BOM行号"], 202)


if __name__ == "__main__":
    unittest.main()
