from dataclasses import replace
import unittest

from standard_part_advice import CASES, _comparison_html, filter_advice


class StandardPartAdviceTests(unittest.TestCase):
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
