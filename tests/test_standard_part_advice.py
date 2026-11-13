from contextlib import nullcontext
from dataclasses import replace
import ast
import os
from pathlib import Path
import sys
from types import ModuleType, SimpleNamespace
import unittest
from unittest.mock import patch

from standard_part_advice import CASES, _comparison_html, filter_advice, normalize_lookup_model, part_summary


class StandardPartAdviceTests(unittest.TestCase):
    def test_deployed_route_with_stale_advice_module_still_renders_and_wires_lookup(self):
        root = Path(__file__).resolve().parents[1]
        path = root / "component_matcher.py"
        tree = ast.parse(path.read_text(encoding="utf-8"))
        loader = next(n for n in tree.body if isinstance(n, ast.FunctionDef)
                      and n.name == "load_standard_advice_runtime")
        route = next(n for n in tree.body if isinstance(n, ast.If)
                     and isinstance(n.test, ast.Compare)
                     and ast.unparse(n.test) == "workbench_active == 'standard_advice'")
        old = ModuleType("standard_part_advice")
        # Reproduce the exact warm-worker interface from the production error.
        old.render_page = lambda st: None
        outputs = []
        lookups = []
        def lookup(model, *, advice_runtime):
            lookups.append(model)
            self.assertEqual(advice_runtime["normalize_lookup_model"](model), model)
            return ()

        st = SimpleNamespace(
            info=lambda value: outputs.append(value),
            subheader=lambda value: outputs.append(value),
            warning=lambda value: outputs.append(value),
            session_state={},
            form=lambda *args, **kwargs: nullcontext(),
            spinner=lambda *args, **kwargs: nullcontext(),
            text_input=lambda *args, **kwargs: "frc0402f1001 ts",
            form_submit_button=lambda *args, **kwargs: True,
        )
        def stop_at_case_filters(*args):
            raise StopIteration
        st.columns = stop_at_case_filters
        namespace = {"BASE_DIR": str(root), "os": os, "workbench_active": "standard_advice",
                     "workbench_member": {"id": 5}, "workbench_login_href": "?member=1",
                     "st": st, "load_standard_advice_part": lookup,
                     "open_standard_advice_match": lambda model: None}
        with patch.dict(sys.modules, {"standard_part_advice": old}):
            with self.assertRaises(StopIteration):
                exec(compile(ast.Module(body=[loader, route], type_ignores=[]), str(path), "exec"), namespace)
            self.assertIs(sys.modules["standard_part_advice"], old)
        self.assertIn("按料号查库", outputs)
        self.assertIn("设计案例筛选", outputs)
        self.assertEqual(lookups, ["FRC0402F1001TS"])

    def test_cases_have_unique_keys_and_engineering_checks(self):
        self.assertEqual(len({case.key for case in CASES}), len(CASES))
        self.assertGreaterEqual(len({case.category for case in CASES}), 8)
        for case in CASES:
            self.assertTrue(all((case.original, case.candidate, case.why, case.checks,
                                 case.risks, case.verify, case.stop)), case.key)
            if case.source:
                self.assertTrue(case.source[1].startswith("https://"))

    def test_filters_combine_category_impact_and_model(self):
        self.assertEqual([case.key for case in filter_advice("陶瓷电容", "需重算", "grm188r71h104ka93d")], ["mlcc-100n"])
        self.assertEqual(filter_advice("陶瓷电容", "需改板", "GRM188R71H104KA93D"), ())
        self.assertIn("power-l", [case.key for case in filter_advice(keyword="3.9 uH")])
        self.assertEqual(filter_advice(keyword="不存在的料号XYZ"), ())

    def test_comparison_escapes_case_text(self):
        html = _comparison_html([replace(CASES[0], candidate="<b>候选 & 检查</b>")])
        self.assertIn("&lt;b&gt;候选 &amp; 检查&lt;/b&gt;", html)
        self.assertNotIn("<b>候选", html)

    def test_lookup_normalizes_a_single_full_model_and_only_exposes_specs(self):
        self.assertEqual(normalize_lookup_model(" ｆｒｃ0402f1001 ts "), "FRC0402F1001TS")
        for invalid in ("", "A", "FRC0402F1001TS\nGRM033R60J105ME15D", "0603 1k ±1%"):
            self.assertEqual(normalize_lookup_model(invalid), "")
        row = {"型号": "FRC0402F1001TS", "容值": 1, "容值单位": "KΩ",
               "成本": "100", "客户": "不应显示", "_model_clean": "FRC0402F1001TS"}
        result = part_summary(row, lambda value: "" if value is None else str(value))
        self.assertEqual(result, {"型号": "FRC0402F1001TS", "参数值": "1 KΩ"})
        self.assertEqual(filter_advice(keyword="FRC0402F1001TS"), ())

    def test_part_lookup_is_separate_from_case_filter_and_retains_member_scope(self):
        from streamlit.testing.v1 import AppTest

        page = AppTest.from_string(
            "import streamlit as st\n"
            "from standard_part_advice import render_page\n"
            "def lookup(model):\n"
            "    st.session_state['calls'] = st.session_state.get('calls', 0) + 1\n"
            "    if model == 'OFFLINE': return None\n"
            "    if model != 'FRC0402F1001TS': return ()\n"
            "    return ({'型号': model, '品牌': 'FOJAN(富捷)', '参数值': '1 KΩ'},)\n"
            "def open_match(model): st.session_state['opened'] = model\n"
            "render_page(st, lookup_part=lookup, member_id=st.session_state.get('member'), "
            "login_href='?member=1', open_match=open_match)\n",
            default_timeout=30,
        ).run()
        self.assertFalse(any(item.label == "原器件料号" for item in page.text_input))
        self.assertTrue(any("登录后查询" in item.value for item in page.markdown))
        page.session_state["member"] = 5
        page.run()
        submit = lambda: next(button for button in page.button if button.label == "查询料号")
        page.text_input(key="standard_advice_lookup_model").set_value("frc0402f1001 ts")
        page.text_input(key="standard_advice_keyword").set_value("不存在的案例")
        submit().click().run()
        self.assertFalse(page.exception)
        self.assertIn("FOJAN(富捷) · FRC0402F1001TS", [item.value for item in page.text])
        self.assertIn("参数值：1 KΩ", [item.value for item in page.text])
        self.assertTrue(any("没有符合筛选" in item.value for item in page.warning))
        page.button(key="standard_advice_open_match").click().run()
        self.assertEqual(page.session_state["opened"], "FRC0402F1001TS")
        self.assertEqual(page.session_state["calls"], 1)
        page.session_state["member"] = 6
        page.run()
        self.assertFalse(page.text)
        for model, message in (("UNKNOWN0001", "库内没有找到"), ("OFFLINE", "器件库暂不可用")):
            page.text_input(key="standard_advice_lookup_model").set_value(model)
            submit().click().run()
            self.assertTrue(any(message in item.value for item in page.warning))
            self.assertFalse(page.text)

    def test_streamlit_page_compares_before_selection_and_updates_details(self):
        from streamlit.testing.v1 import AppTest

        page = AppTest.from_string(
            "import streamlit as st\n"
            "from standard_part_advice import render_page\n"
            "render_page(st)\n",
            default_timeout=30,
        ).run()
        self.assertFalse(page.exception)
        self.assertIn("不是等效替代", page.info[0].value)
        comparison = next(item.value for item in page.markdown if 'role="table"' in item.value)
        for heading in ("应用场景", "原规格", "常规候选", "改动程度", "关键风险"):
            self.assertIn(f">{heading}</th>", comparison)
        self.assertEqual(comparison.count('scope="row"'), len(CASES))
        self.assertIn(CASES[0].original, comparison)
        self.assertIn(CASES[0].candidate, comparison)
        self.assertIn(CASES[0].risks, comparison)
        page.selectbox(key="standard_advice_case").select("mlcc-100n").run()
        mlcc = next(case for case in CASES if case.key == "mlcc-100n")
        self.assertFalse(page.exception)
        self.assertTrue(any(mlcc.checks in item.value for item in page.markdown))
        self.assertTrue(any(mlcc.verify in item.value for item in page.markdown))
        self.assertTrue(any(mlcc.source[1] in item.value for item in page.markdown))
        page.selectbox(key="standard_advice_category").select("陶瓷电容")
        page.selectbox(key="standard_advice_impact").select("需改板")
        page.run()
        self.assertFalse(page.exception)
        self.assertIn("显示 1 /", page.caption[0].value)
        self.assertEqual(page.selectbox(key="standard_advice_case").value, "mlcc-area")
        comparison = next(item.value for item in page.markdown if 'role="table"' in item.value)
        self.assertEqual(comparison.count('scope="row"'), 1)
        self.assertNotIn(mlcc.title, comparison)
        self.assertTrue(any("不能直接套用" in item.value for item in page.warning))
        page.text_input(key="standard_advice_keyword").set_value("不存在的料号XYZ").run()
        self.assertIn("没有符合", page.warning[0].value)
        self.assertFalse(any('role="table"' in item.value for item in page.markdown))
