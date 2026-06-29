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

    def test_shell_uses_a_random_channel_and_rejects_other_messages(self):
        self.assertIn('const authBridgeChannel = crypto.randomUUID', self.worker)
        self.assertIn('frameUrl.searchParams.set(bridgeChannelParam, authBridgeChannel);', self.worker)
        self.assertIn('if (payload.channel !== authBridgeChannel) return;', self.worker)
        self.assertIn('channel: bridgeChannel,', self.matcher)

    def test_shell_removes_member_token_from_the_visible_url(self):
        self.assertIn('outerUrl.searchParams.delete("member_token");', self.worker)
        self.assertIn('history.replaceState(null, "", outerUrl.pathname + outerUrl.search + outerUrl.hash);', self.worker)

    def test_member_snapshot_api_keeps_version_history(self):
        self.assertIn("member_auth_snapshot_history", self.worker)
        self.assertIn('searchParams.get("version")', self.worker)
        self.assertIn("INSERT OR REPLACE INTO member_auth_snapshot_history", self.worker)

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
