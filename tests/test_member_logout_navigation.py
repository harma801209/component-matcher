import pathlib
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
MATCHER_PATH = ROOT / "component_matcher.py"


class MemberLogoutNavigationSourceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.matcher = MATCHER_PATH.read_text(encoding="utf-8")

    def test_browser_clear_flag_precedes_session_recovery(self):
        start = self.matcher.index("def render_member_auth_browser_persistence_bridge():")
        end = self.matcher.index("\ndef set_current_member", start)
        bridge = self.matcher[start:end]
        self.assertLess(
            bridge.index('clear_token = bool(st.session_state.pop("_member_auth_clear_browser_token"'),
            bridge.index("current_member()"),
        )
        self.assertIn('if clear_token:', bridge)
        self.assertIn('token = ""', bridge)
        self.assertIn('clear_token_value = clean_text(st.session_state.pop("_member_auth_clear_browser_token_value"', bridge)

    def test_member_navigation_clears_other_page_modes(self):
        start = self.matcher.index("def render_member_entry_button():")
        end = self.matcher.index("\ndef render_bom_entry_button", start)
        member_button = self.matcher[start:end]
        self.assertIn('session_state = getattr(st, "session_state", {})', member_button)
        self.assertIn('member_token = clean_text(session_state.get("_member_auth_token", ""))', member_button)
        self.assertIn('"member": "0"', member_button)
        self.assertIn('"member": "1"', member_button)
        self.assertIn('"admin": "0"', member_button)
        self.assertIn('"bom": "0"', member_button)
        self.assertIn("href_updates[MEMBER_AUTH_QUERY_PARAM] = member_token", member_button)

    def test_bom_navigation_preserves_member_token(self):
        start = self.matcher.index("def render_bom_entry_button():")
        end = self.matcher.index("\ndef render_member_auth_panel", start)
        bom_button = self.matcher[start:end]
        self.assertIn('session_state = getattr(st, "session_state", {})', bom_button)
        self.assertIn('member_token = clean_text(session_state.get("_member_auth_token", ""))', bom_button)
        self.assertIn('"bom": "0"', bom_button)
        self.assertIn('"bom": "1"', bom_button)
        self.assertIn('"member": "0"', bom_button)
        self.assertIn('"admin": "0"', bom_button)
        self.assertIn("href_updates[MEMBER_AUTH_QUERY_PARAM] = member_token", bom_button)

    def test_logout_clears_ui_before_remote_revocation(self):
        start = self.matcher.index("def logout_member():")
        end = self.matcher.index("\ndef is_member_page_requested", start)
        logout = self.matcher[start:end]
        local_clear = logout.index('st.session_state.pop("_member_auth_token"')
        remote_refresh = logout.index("refresh_member_auth_remote_snapshot(force=True)")
        self.assertLess(local_clear, remote_refresh)
        self.assertIn('st.session_state["_member_auth_clear_browser_token"] = True', logout)
        self.assertIn('st.session_state["_member_auth_clear_browser_token_value"] = token', logout)
        self.assertIn('"member": ""', logout)
        self.assertIn('"bom": ""', logout)
        self.assertIn('"admin": ""', logout)


if __name__ == "__main__":
    unittest.main(verbosity=2)
