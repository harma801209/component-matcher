"""Header-driven comparison must remain a read-only, explicitly clicked action."""
import unittest
from pathlib import Path

import pandas as pd

from bom_model_comparison import (
    compare_display_columns, display_column_choices, comparison_revision,
    render_table, selected_display_columns,
)


class HeaderUI:
    def __init__(self, issues_only=True):
        self.session_state = {"member_token": "KEEP", "cost_scope": "KEEP"}
        self.messages, self.tables = [], []
        self.issues_only = issues_only

    def caption(self, value): self.messages.append(("caption", value))
    def info(self, value): self.messages.append(("info", value))
    def warning(self, value): self.messages.append(("warning", value))
    def success(self, value): self.messages.append(("success", value))
    def checkbox(self, *args, **kwargs): return self.issues_only
    def number_input(self, *args, **kwargs): return self.session_state[kwargs["key"]]
    def dataframe(self, frame, **kwargs): self.tables.append(frame.copy(deep=True))


class HeaderComparisonTests(unittest.TestCase):
    def frame(self):
        return pd.DataFrame({"描述": ["22R 5%", "1K 5%"],
                             "MPN": ["FRC0402F2200TS", "FRC0402J102TS"],
                             "匹配型号": ["FRC0402J220 TS", "frc0402j102 ts"],
                             "匹配成本": ["1.66", "1.66"]})

    def event(self, frame, columns=None):
        return {"revision": comparison_revision(frame),
                "columns": columns or ["column:1", "column:2"], "request": 1}

    def test_each_visible_header_has_a_positional_choice(self):
        frame = self.frame()
        choices = display_column_choices(frame, 2)
        self.assertEqual(len(choices), 4)
        self.assertEqual(choices[1]["label"], "原表 · MPN")
        self.assertEqual(choices[2]["label"], "系统 · 匹配型号")
        self.assertEqual(choices[3]["position"], 3)

    def test_duplicate_headers_have_unambiguous_labels_and_keys(self):
        frame = pd.DataFrame([["A", "B", "C"]], columns=["MPN", "MPN", "MPN"])
        choices = display_column_choices(frame, 2)
        self.assertEqual(len({item["key"] for item in choices}), 3)
        self.assertEqual(len({item["label"] for item in choices}), 3)
        selected = selected_display_columns(self.event(frame, ["column:1", "column:2"]), frame, choices)
        report = compare_display_columns(frame, selected)
        self.assertEqual(report["different"], 1)
        self.assertEqual(report["rows"][0][choices[1]["label"]], "B")

    def test_click_compares_full_sheet_not_page_or_current_view(self):
        frame = pd.DataFrame({"MPN": ["A"] * 250, "匹配型号": ["B"] * 250})
        choices = display_column_choices(frame, 1)
        selected = selected_display_columns(self.event(frame, ["column:0", "column:1"]), frame, choices)
        report = compare_display_columns(frame, selected, row_numbers=list(range(8, 258)))
        self.assertEqual(report["total"], 250)
        self.assertEqual(report["different"], 250)
        self.assertEqual(report["rows"][-1]["BOM行号"], 257)

    def test_explicit_button_event_required_and_untrusted_events_fail_closed(self):
        frame = self.frame()
        choices = display_column_choices(frame, 2)
        for event in (None, [], {}, {"columns": ["column:1", "column:2"]},
                      self.event(frame, ["column:1"]), self.event(frame, ["column:1", "column:1"]),
                      self.event(frame, ["column:1", "column:90"]),
                      self.event(frame, [[], "column:1"])):
            self.assertIsNone(selected_display_columns(event, frame, choices))

    def test_stale_result_or_source_event_cannot_reuse_an_old_report(self):
        frame = self.frame()
        event = self.event(frame)
        choices = display_column_choices(frame, 2)
        frame.iloc[0, 2] = "FRC0402J221TS"
        self.assertIsNone(selected_display_columns(event, frame, choices))
        self.assertNotEqual(event["revision"], comparison_revision(frame))

    def test_model_difference_details_and_row_numbers_preserved(self):
        frame = self.frame()
        choices = display_column_choices(frame, 2)
        selected = selected_display_columns(self.event(frame), frame, choices)
        report = compare_display_columns(frame, selected, detail=lambda a, b: "误差不同，需核对", row_numbers=[6, 9])
        self.assertEqual((report["same"], report["different"]), (1, 1))
        self.assertEqual(report["rows"][0]["BOM行号"], 6)
        self.assertIn("误差不同", report["rows"][0]["差异说明"])

    def test_two_original_headers_can_be_selected_without_remapping(self):
        frame = self.frame()
        choices = display_column_choices(frame, 2)
        selected = selected_display_columns(self.event(frame, ["column:0", "column:1"]), frame, choices)
        report = compare_display_columns(frame, selected)
        self.assertEqual(report["different"], 2)
        self.assertEqual(report["left_label"], "原表 · 描述")
        self.assertEqual(report["right_label"], "原表 · MPN")

    def test_selecting_system_first_keeps_original_first_in_explanation(self):
        frame = self.frame()
        choices = display_column_choices(frame, 2)
        selected = selected_display_columns(self.event(frame, ["column:2", "column:1"]), frame, choices)
        report = compare_display_columns(frame, selected)
        self.assertEqual(report["left_label"], "原表 · MPN")
        self.assertEqual(report["right_label"], "系统 · 匹配型号")

    def test_paging_and_show_all_do_not_reduce_worksheet_counts(self):
        frame = pd.DataFrame({"MPN": ["A"] * 250, "匹配型号": ["B"] * 250})
        ui = HeaderUI(issues_only=False)
        ui.session_state["check_page_column:0_column:1_0"] = 99
        report = render_table(ui, frame, table_html="TABLE", original_column_count=1,
                              visible_columns=list(frame.columns), key="check",
                              component=lambda **kwargs: self.event(frame, ["column:0", "column:1"]))
        self.assertEqual(report["different"], 250)
        self.assertEqual(len(ui.tables[0]), 50)
        self.assertEqual(ui.tables[0].iloc[0]["BOM行号"], 202)

    def test_consistent_report_is_only_shown_after_click(self):
        frame = pd.DataFrame({"MPN": ["A", "B"], "匹配型号": ["a", " b "]})
        ui = HeaderUI(issues_only=False)
        report = render_table(ui, frame, table_html="TABLE", original_column_count=1,
                              visible_columns=list(frame.columns), key="check",
                              component=lambda **kwargs: self.event(frame, ["column:0", "column:1"]))
        self.assertEqual(report["same"], 2)
        self.assertTrue(any(kind == "success" for kind, _ in ui.messages))
        self.assertEqual(len(ui.tables[0]), 2)

    def test_renderer_waits_for_button_then_warns_without_changing_data(self):
        frame = self.frame()
        before = frame.copy(deep=True)
        ui, calls = HeaderUI(), []
        event = None
        def component(**kwargs):
            calls.append(kwargs)
            return event
        self.assertIsNone(render_table(ui, frame, table_html="TABLE", original_column_count=2,
                                       visible_columns=list(frame.columns), key="check", component=component))
        self.assertFalse(ui.tables)
        event = self.event(frame)
        report = render_table(ui, frame, table_html="TABLE", original_column_count=2,
                              visible_columns=list(frame.columns), key="check", component=component)
        self.assertEqual(report["different"], 1)
        self.assertEqual(len(ui.tables[0]), 1)
        self.assertTrue(any(kind == "warning" for kind, _ in ui.messages))
        self.assertEqual(len(calls[-1]["headers"]), 4)
        pd.testing.assert_frame_equal(frame, before)
        self.assertEqual(ui.session_state["member_token"], "KEEP")
        self.assertEqual(ui.session_state["cost_scope"], "KEEP")

    def test_hidden_columns_are_not_sent_as_header_choices(self):
        frame = self.frame()
        ui, calls = HeaderUI(), []
        def component(**kwargs): calls.append(kwargs)
        render_table(ui, frame, table_html="TABLE", original_column_count=2,
                     visible_columns=["MPN", "匹配型号"], key="check", component=component)
        self.assertEqual([item["key"] for item in calls[0]["headers"]], ["column:1", "column:2"])
        self.assertNotIn("匹配成本", str(calls[0]["headers"]))
        self.assertIsNone(render_table(ui, frame, table_html="TABLE", original_column_count=2,
                                       visible_columns=["MPN", "匹配型号"], key="check",
                                       component=lambda **kwargs: self.event(frame, ["column:1", "column:3"])))

    def test_component_has_real_checkboxes_and_click_only_message(self):
        source = (Path(__file__).resolve().parents[1] / "bom_comparison_table" / "index.html").read_text(encoding="utf-8")
        self.assertIn("input.type='checkbox'", source)
        self.assertIn('型号比对</button>', source)
        self.assertEqual(source.count("send('streamlit:setComponentValue'"), 1)
        self.assertIn("run.onclick=", source)
        self.assertIn("event.source!==window.parent", source)
        self.assertIn("event.origin!==window.location.origin", source)
        self.assertNotIn("},'*')", source)
        self.assertIn("if(wrap&&!changed)", source)
        self.assertNotIn("localStorage", source)
        self.assertNotIn("fetch(", source)


if __name__ == "__main__":
    unittest.main()
