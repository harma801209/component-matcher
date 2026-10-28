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

    def test_global_issues_share_the_main_table_and_keep_summary_coverage(self):
        frame = pd.DataFrame({"MPN": ["A"] * 250, "匹配型号": ["B"] * 250})
        ui, calls, views = HeaderUI(), [], []
        ui.session_state["check_table"] = {**self.event(frame, ["column:0", "column:1"]), "issues_only": True, "page": 99}
        def renderer(view):
            views.append(view)
            return "FILTERED"
        report = render_table(ui, frame, table_html="TABLE", original_column_count=1,
                              visible_columns=list(frame.columns), key="check",
                              component=lambda **kwargs: calls.append(kwargs), table_renderer=renderer,
                              visible_row_positions=[0, 1])
        self.assertEqual(report["different"], 250)
        self.assertEqual(len(views[0]), 50)
        self.assertEqual(calls[0]["table_html"], "FILTERED")
        self.assertEqual(calls[0]["report"]["rows"][0]["row_number"], "202")
        self.assertEqual(calls[0]["report"]["page"], 3)
        self.assertFalse(ui.tables)
        self.assertFalse(ui.messages)

    def test_consistent_report_is_only_shown_after_click(self):
        frame = pd.DataFrame({"MPN": ["A", "B"], "匹配型号": ["a", " b "]})
        ui = HeaderUI(issues_only=False)
        calls = []
        ui.session_state["check_table"] = self.event(frame, ["column:0", "column:1"])
        report = render_table(ui, frame, table_html="TABLE", original_column_count=1,
                              visible_columns=list(frame.columns), key="check",
                              component=lambda **kwargs: calls.append(kwargs))
        self.assertEqual(report["same"], 2)
        self.assertEqual(calls[0]["report"]["same"], 2)
        self.assertFalse(calls[0]["report"]["issues_only"])
        self.assertFalse(ui.messages)
        self.assertFalse(ui.tables)

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
        ui.session_state["check_table"] = event
        report = render_table(ui, frame, table_html="TABLE", original_column_count=2,
                              visible_columns=list(frame.columns), key="check", component=component)
        self.assertEqual(report["different"], 1)
        self.assertFalse(ui.tables)
        self.assertFalse(ui.messages)
        self.assertEqual(calls[-1]["report"]["different"], 1)
        self.assertEqual(calls[-1]["report"]["rows"][0]["status"], "不一致")
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
        ui.session_state["check_table"] = self.event(frame, ["column:1", "column:3"])
        self.assertIsNone(render_table(ui, frame, table_html="TABLE", original_column_count=2,
                                       visible_columns=["MPN", "匹配型号"], key="check",
                                       component=lambda **kwargs: self.event(frame, ["column:1", "column:3"])))

    def test_only_visible_rows_receive_annotations_until_global_filter_is_enabled(self):
        frame = self.frame()
        ui, calls = HeaderUI(), []
        ui.session_state["check_table"] = self.event(frame)
        render_table(ui, frame, table_html="TABLE", original_column_count=2,
                     visible_columns=list(frame.columns), visible_row_positions=[1], key="check",
                     component=lambda **kwargs: calls.append(kwargs))
        self.assertEqual(calls[0]["report"]["total"], 2)
        self.assertEqual(len(calls[0]["report"]["rows"]), 1)
        self.assertEqual(calls[0]["report"]["rows"][0]["status"], "一致")

    def test_all_consistent_issues_view_keeps_headers_and_no_duplicate_result_grid(self):
        frame = pd.DataFrame({"MPN": ["A"], "匹配型号": ["a"]})
        ui, calls, views = HeaderUI(), [], []
        ui.session_state["check_table"] = {**self.event(frame, ["column:0", "column:1"]), "issues_only": True}
        def renderer(view): views.append(view); return "HEADERS ONLY"
        render_table(ui, frame, table_html="TABLE", original_column_count=1,
                     visible_columns=list(frame.columns), key="check", table_renderer=renderer,
                     component=lambda **kwargs: calls.append(kwargs))
        self.assertEqual(len(views[0]), 0)
        self.assertEqual(calls[0]["report"]["rows"], [])
        self.assertEqual(calls[0]["report"]["total"], 1)
        self.assertFalse(ui.messages)
        self.assertFalse(ui.tables)

    def test_hidden_columns_are_not_exposed_in_filtered_rows(self):
        frame = self.frame()
        ui, views = HeaderUI(), []
        ui.session_state["check_table"] = {**self.event(frame), "issues_only": True}
        def renderer(view): views.append(view); return "FILTERED"
        render_table(ui, frame, table_html="TABLE", original_column_count=2,
                     visible_columns=["MPN", "匹配型号"], key="check", table_renderer=renderer,
                     component=lambda **kwargs: None)
        self.assertEqual(list(views[0].columns), ["MPN", "匹配型号"])
        self.assertEqual(len(views[0]), 1)

    def test_bad_annotation_alignment_fails_in_the_same_component(self):
        frame = self.frame()
        ui, calls = HeaderUI(), []
        ui.session_state["check_table"] = self.event(frame)
        self.assertIsNone(render_table(ui, frame, table_html="TABLE", original_column_count=2,
                                      visible_columns=list(frame.columns), visible_row_positions=[99], key="check",
                                      component=lambda **kwargs: calls.append(kwargs)))
        self.assertIn("未对齐", calls[0]["error"])
        self.assertIsNone(calls[0]["report"])
        self.assertFalse(ui.messages)

    def test_component_has_real_checkboxes_and_click_only_message(self):
        source = (Path(__file__).resolve().parents[1] / "bom_comparison_table" / "index.html").read_text(encoding="utf-8")
        self.assertIn("input.type='checkbox'", source)
        self.assertIn('型号比对</button>', source)
        self.assertEqual(source.count("send('streamlit:setComponentValue'"), 1)
        self.assertIn("run.onclick=", source)
        self.assertIn('id="compare-result"', source)
        self.assertIn('id="compare-issues"', source)
        self.assertIn("details.className='compare-note'", source)
        self.assertIn("details.open=expandedRows.has", source)
        self.assertIn("event.source!==window.parent", source)
        self.assertIn("event.origin!==window.location.origin", source)
        self.assertNotIn("},'*')", source)
        self.assertIn("if(wrap&&!changed)", source)
        self.assertNotIn("localStorage", source)
        self.assertNotIn("fetch(", source)

    def test_top_scrollbar_is_before_the_table_and_keyboard_accessible(self):
        source = (Path(__file__).resolve().parents[1] / "bom_comparison_table" / "index.html").read_text(encoding="utf-8")
        self.assertLess(source.index('id="table-top-scroll"'), source.index('id="table-root"'))
        self.assertIn('aria-label="表格顶部横向滚动条" tabindex="0"', source)
        self.assertIn("topSpacer.style.width=wrap.scrollWidth", source)
        self.assertIn("topScroll.style.width=wrap.clientWidth", source)
        self.assertIn("topScroll.hidden=!overflow", source)

    def test_scroll_sync_is_bidirectional_local_and_rebound_on_table_replacement(self):
        source = (Path(__file__).resolve().parents[1] / "bom_comparison_table" / "index.html").read_text(encoding="utf-8")
        self.assertIn("wrap.scrollLeft=topScroll.scrollLeft", source)
        self.assertIn("topScroll.scrollLeft=wrap.scrollLeft", source)
        self.assertIn("wrap.addEventListener('scroll'", source)
        self.assertIn("topScroll.addEventListener('scroll'", source)
        self.assertIn("updateTopScroll();", source)
        self.assertIn("topScroll.getBoundingClientRect().height", source)
        self.assertIn("Math.abs(wrap.scrollLeft-topScroll.scrollLeft)>.5", source)
        self.assertEqual(source.count("send('streamlit:setComponentValue'"), 1)

    def test_primary_button_states_override_the_existing_important_table_theme(self):
        source = (Path(__file__).resolve().parents[1] / "bom_comparison_table" / "index.html").read_text(encoding="utf-8")
        self.assertIn("background:#1555e8!important", source)
        self.assertIn("color:#fff!important", source)
        self.assertIn("#compare-run:disabled", source)
        self.assertIn("background:#eaf0f7!important", source)
        self.assertIn("grid-template-columns:minmax(0,1fr) auto", source)
        self.assertIn("class=\"compare-fields\"", source)

    def test_frontend_version_loads_new_assets_without_refreshing_the_browser(self):
        from unittest.mock import patch
        from bom_model_comparison import header_component
        with patch("streamlit.components.v1.declare_component", return_value="COMPONENT") as declare:
            self.assertEqual(header_component(), "COMPONENT")
        self.assertEqual(declare.call_args.args[0], "bom_header_compare_v2")
        self.assertTrue(declare.call_args.kwargs["path"].endswith("bom_comparison_table"))


if __name__ == "__main__":
    unittest.main()
