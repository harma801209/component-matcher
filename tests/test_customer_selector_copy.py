"""Render the real customer selector with synthetic profiles and no runtime DBs."""
import ast
from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]
CUSTOMER = "本地演示客户有限公司"


def render_fixture(st):
    member = dict(st.session_state.get("fixture_member", {
        "id": 901, "username": "LOCAL_DEMO", "role": "member",
        "job_title": "其他", "company": "外部演示有限公司", "status": "active",
    }))
    st.session_state.setdefault("fixture_price_resolutions", [])

    def resolve(name):
        st.session_state.fixture_price_resolutions.append(name)
        return "new", "", True

    env = dict(
        st=st, re=re, clean_text=lambda value: str(value or "").strip(),
        MEMBER_JOB_TITLE_PM="PM", MEMBER_JOB_TITLE_SALES="销售", MEMBER_JOB_TITLE_OTHER="其他",
        SALES_COST_CUSTOMER_TYPE_KEY="fixture_customer_type",
        SALES_COST_CUSTOMER_NAME_KEY="fixture_customer_name",
        SALES_CUSTOMER_SELECTION_NAME_KEY="fixture_selection_name",
        COST_CUSTOMER_TYPE_NEW="new", COST_CUSTOMER_TYPE_EXISTING="existing",
        current_member=lambda: member,
        current_member_is_admin=lambda: member["role"] == "admin",
        list_sales_customers=lambda **kwargs: [{"customer_name": CUSTOMER}],
        list_selectable_sales_customers=lambda member_id: [{"customer_name": CUSTOMER}],
        normalize_cost_customer_name=lambda value: str(value or "").strip(),
        normalize_cost_customer_key=lambda value: str(value or "").strip().casefold(),
        render_admin_cost_time_selector=lambda member: True,
        selected_admin_cost_as_of=lambda member: None,
        render_admin_cost_time_summary=lambda *args: None,
        get_cost_price_lookup_signature=lambda *args, **kwargs: "local-fixture-only",
        clear_customer_dependent_session_state=lambda: None,
        select_member_sales_customer=lambda member_id, name: {"customer_name": name},
        resolve_member_customer_price_scope=resolve,
        authorize_cost_customer_context=lambda member, kind, name: (kind, name),
    )
    names = {
        "normalize_member_role", "normalize_member_job_title", "member_company_is_fruition",
        "member_cost_access_level", "member_can_view_cost", "render_sales_cost_customer_selector",
    }
    tree = ast.parse((ROOT / "component_matcher.py").read_text(encoding="utf-8"))
    nodes = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name in names]
    assert len(nodes) == len(names)
    exec(compile(ast.Module(body=nodes, type_ignores=[]), "actual-customer-selector-fixture", "exec"), env)
    prefix = st.session_state.get("fixture_prefix", "sales")
    result = env["render_sales_cost_customer_selector"](prefix)
    st.session_state.fixture_result = result
    st.session_state.fixture_can_view_cost = env["member_can_view_cost"](member)


class CustomerSelectorCopyTests(unittest.TestCase):
    def app(self, prefix="sales", role="member", company="外部演示有限公司", job="其他", old_selection=""):
        from streamlit.testing.v1 import AppTest
        app = AppTest.from_string(
            "import streamlit as st\n"
            "from tests.test_customer_selector_copy import render_fixture\nrender_fixture(st)"
        )
        app.session_state["fixture_prefix"] = prefix
        app.session_state["fixture_member"] = dict(
            id=901, username="LOCAL_DEMO", role=role, company=company, job_title=job, status="active"
        )
        if old_selection:
            owner = "admin" if role == "admin" else "901"
            app.session_state[f"{prefix}_member_sales_customer_selector_{owner}_v3"] = old_selection
        app.run(timeout=30)
        self.assertFalse(app.exception)
        return app

    def assert_no_price_explanation(self, app):
        messages = [item.value for group in (app.success, app.caption, app.info) for item in group]
        messages += app.selectbox[0].options + [app.selectbox[0].proto.help]
        for message in messages:
            self.assertNotIn("不显示价格", message)
            self.assertNotIn("当前公司不属于", message)
            self.assertNotIn("价格来源", message)
        self.assertFalse(app.session_state["fixture_can_view_cost"])
        self.assertEqual(app.session_state["fixture_result"], ("new", "", True))
        self.assertEqual(app.session_state["fixture_price_resolutions"], [])

    def test_external_default_is_neutral_in_search_and_bom(self):
        for prefix in ("sales", "bom"):
            with self.subTest(prefix=prefix):
                app = self.app(prefix)
                self.assertEqual(app.selectbox[0].value, "型号匹配")
                self.assert_no_price_explanation(app)

    def test_external_named_customer_keeps_selection_without_permission_copy(self):
        for prefix in ("sales", "bom"):
            with self.subTest(prefix=prefix):
                app = self.app(prefix)
                app.selectbox[0].select(CUSTOMER).run(timeout=30)
                self.assertFalse(app.exception)
                self.assertEqual(app.selectbox[0].value, CUSTOMER)
                self.assert_no_price_explanation(app)
                self.assertEqual(app.success[0].value, f"当前客户：{CUSTOMER}")

    def test_old_option_label_recovers_to_neutral_option(self):
        app = self.app(old_selection="型号匹配（不显示价格）")
        self.assertEqual(app.selectbox[0].value, "型号匹配")
        self.assert_no_price_explanation(app)

    def test_named_customer_survives_rerender(self):
        app = self.app(old_selection=CUSTOMER)
        app.run(timeout=30)
        self.assertEqual(app.selectbox[0].value, CUSTOMER)
        self.assert_no_price_explanation(app)

    def test_internal_staff_customer_price_copy_is_unchanged(self):
        for job in ("PM", "销售", "其他"):
            with self.subTest(job=job):
                app = self.app(company="富临通演示有限公司", job=job, old_selection=CUSTOMER)
                self.assertTrue(app.session_state["fixture_can_view_cost"])
                self.assertIn("价格来源：通用价格", app.success[0].value)
                self.assertTrue(app.caption)

    def test_administrator_still_has_general_cost_option(self):
        app = self.app(role="admin")
        self.assertEqual(app.selectbox[0].value, "通用成本（不指定客户）")
        self.assertTrue(app.session_state["fixture_can_view_cost"])
        self.assertIn("价格来源：通用价格", app.success[0].value)


if __name__ == "__main__":
    unittest.main()
