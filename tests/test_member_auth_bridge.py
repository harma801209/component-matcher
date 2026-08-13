import pathlib
import re
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
MATCHER_PATH = ROOT / "component_matcher.py"
WORKER_PATH = ROOT / "cloudflare-pages-proxy" / "dist" / "_worker.js"


class MemberAuthBridgeSourceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.matcher = MATCHER_PATH.read_text(encoding="utf-8")
        cls.worker = WORKER_PATH.read_text(encoding="utf-8")

    def test_component_bridge_targets_only_the_formal_shell(self):
        self.assertIn(
            'MEMBER_AUTH_OUTER_SHELL_ORIGIN = "https://fruition-component.pages.dev"',
            self.matcher,
        )
        self.assertIn('}}, outerShellOrigin);', self.matcher)
        bridge_block = re.search(
            r"function notifyOuterShell\(.*?\n\s*}}\n",
            self.matcher,
            re.DOTALL,
        )
        self.assertIsNotNone(bridge_block)
        self.assertNotIn('}}, "*");', bridge_block.group(0))

    def test_component_validates_the_session_before_persisting_it(self):
        function_start = self.matcher.index("def render_member_auth_browser_persistence_bridge():")
        function_end = self.matcher.index("\ndef set_current_member", function_start)
        bridge_function = self.matcher[function_start:function_end]
        self.assertLess(bridge_function.index("current_member()"), bridge_function.index("const token ="))

    def test_stale_logged_out_bridge_cannot_clear_a_newer_login(self):
        function_start = self.matcher.index("def render_member_auth_browser_persistence_bridge():")
        function_end = self.matcher.index("\ndef set_current_member", function_start)
        bridge_function = self.matcher[function_start:function_end]
        self.assertIn("function clearSavedToken(notifyShell, expectedToken)", bridge_function)
        self.assertIn("if (expectedToken && savedToken && savedToken !== expectedToken) return;", bridge_function)
        self.assertIn("clearSavedToken(true, clearTokenValue);", bridge_function)
        self.assertIn("clearSavedToken(false, savedToken);", bridge_function)
        self.assertIn(
            'if (notifyShell && expectedToken) notifyOuterShell("clear", expectedToken, 0);',
            bridge_function,
        )
        self.assertIn('function clearToken(expectedToken = "")', self.worker)
        self.assertIn(
            "if (expectedToken && savedToken && savedToken !== expectedToken) return false;",
            self.worker,
        )
        self.assertIn('const clearTokenValue = String(payload.token || "");', self.worker)
        self.assertIn("if (!tokenPattern.test(clearTokenValue)) return;", self.worker)
        self.assertIn("clearToken(clearTokenValue);", self.worker)

    def test_shell_uses_a_random_channel_and_rejects_other_messages(self):
        self.assertIn('const authBridgeChannel = crypto.randomUUID', self.worker)
        self.assertIn('frameUrl.searchParams.set(bridgeChannelParam, authBridgeChannel);', self.worker)
        self.assertIn('if (payload.channel !== authBridgeChannel) return;', self.worker)
        self.assertIn('channel: bridgeChannel,', self.matcher)

    def test_shell_removes_member_token_from_the_visible_url(self):
        self.assertIn('outerUrl.searchParams.delete("member_token");', self.worker)
        self.assertIn('history.replaceState(null, "", outerUrl.pathname + outerUrl.search + outerUrl.hash);', self.worker)
        current_member_start = self.matcher.index("def current_member():")
        current_member_end = self.matcher.index("\ndef render_member_auth_browser_persistence_bridge", current_member_start)
        current_member_function = self.matcher[current_member_start:current_member_end]
        self.assertIn('if query_token != "" and token == query_token:', current_member_function)
        self.assertIn('update_query_params(**{MEMBER_AUTH_QUERY_PARAM: ""})', current_member_function)

    def test_member_customer_selector_is_private_and_supports_new_customers(self):
        profile_start = self.matcher.index("def update_current_member_profile(")
        profile_end = self.matcher.index("\ndef change_current_member_password", profile_start)
        profile_function = self.matcher[profile_start:profile_end]
        self.assertIn("客户绑定只能由后台管理员维护", profile_function)

        selector_start = self.matcher.index("def render_sales_cost_customer_selector(")
        selector_end = self.matcher.index("\ndef cost_price_item_change_key", selector_start)
        selector_function = self.matcher[selector_start:selector_end]
        self.assertNotIn("list_sales_customers", selector_function)
        self.assertIn("list_member_sales_customers", selector_function)
        self.assertIn('new_customer_option = "新客户"', selector_function)
        self.assertIn("save_member_sales_customer", selector_function)
        self.assertIn("price_access_enabled", selector_function)
        self.assertIn("注册/营业执照公司全称", selector_function)

    def test_old_single_customer_field_is_not_rendered(self):
        center_start = self.matcher.index("def render_member_center_page(")
        center_end = self.matcher.index("\ndef render_member_admin_management_page", center_start)
        center_function = self.matcher[center_start:center_end]
        self.assertNotIn('{"字段": "客户名称"', center_function)
        self.assertNotIn('st.text_input(\n                "客户名称"', center_function)

        admin_start = center_end + 1
        admin_end = self.matcher.index("\ndef render_member_search_logs_admin_page", admin_start)
        admin_function = self.matcher[admin_start:admin_end]
        self.assertNotIn('edit_customer_name = st.text_input', admin_function)
        self.assertIn("list_member_sales_customers", admin_function)
        self.assertIn("set_member_sales_customer_price_access", admin_function)

    def test_formal_entry_blocks_search_engine_indexing_and_referrers(self):
        self.assertIn('dispatchPath === "/robots.txt"', self.worker)
        self.assertIn('"User-agent: *\\nDisallow: /\\n"', self.worker)
        self.assertIn('headers.set("referrer-policy", "no-referrer")', self.worker)
        self.assertIn(
            'headers.set("x-robots-tag", "noindex, nofollow, noarchive, nosnippet")',
            self.worker,
        )
        self.assertIn('<meta name="robots" content="noindex,nofollow,noarchive,nosnippet" />', self.worker)
        self.assertIn('referrerpolicy="no-referrer"', self.worker)

    def test_admin_exit_clears_page_modes_in_the_formal_shell(self):
        self.assertIn('source: "fruition-route"', self.matcher)
        self.assertIn('action: "clear-page-modes"', self.matcher)
        self.assertIn('if (payload.source === "fruition-route")', self.worker)
        self.assertIn('for (const name of ["admin", "member", "bom"])', self.worker)
        self.assertIn('history.replaceState(null, "", routeUrl.pathname + routeUrl.search + routeUrl.hash);', self.worker)

    def test_member_session_persists_for_twelve_hours(self):
        self.assertIn("MEMBER_AUTH_SESSION_TTL_SECONDS = 12 * 60 * 60", self.matcher)
        self.assertIn("const ttlMs = 12 * 60 * 60 * 1000;", self.worker)

    def test_member_snapshot_api_keeps_version_history(self):
        self.assertIn("member_auth_snapshot_history", self.worker)
        self.assertIn('searchParams.get("version")', self.worker)
        self.assertIn("INSERT OR REPLACE INTO member_auth_snapshot_history", self.worker)
        self.assertIn(
            'DELETE FROM member_auth_snapshot_history WHERE version < ?',
            self.worker,
        )
        self.assertIn("Math.max(1, nextVersion - 19)", self.worker)

    def test_runtime_snapshot_api_separates_cost_and_no_match_stores(self):
        self.assertIn('dispatchPath === "/api/runtime-store/snapshot"', self.worker)
        self.assertIn('new Set(["cost-price", "no-match"])', self.worker)
        self.assertIn("runtime_store_snapshots", self.worker)
        self.assertIn("runtime_store_snapshot_history", self.worker)
        self.assertIn("PRIMARY KEY (store_key, version)", self.worker)
        self.assertIn(
            'DELETE FROM runtime_store_snapshot_history WHERE store_key = ? AND version < ?',
            self.worker,
        )

    def test_member_auth_controls_do_not_use_nested_forms(self):
        function_start = self.matcher.index("def render_member_auth_panel(")
        function_end = self.matcher.index("\ndef render_member_center_page", function_start)
        auth_panel = self.matcher[function_start:function_end]
        self.assertNotIn('st.form("member_login_form"', auth_panel)
        self.assertNotIn('st.form("member_register_form"', auth_panel)
        self.assertNotIn("st.form_submit_button", auth_panel)
        self.assertIn('key="member_login_submit"', auth_panel)
        self.assertIn('key="member_register_submit"', auth_panel)


if __name__ == "__main__":
    unittest.main(verbosity=2)
