import pathlib
import unittest
import ast
from types import SimpleNamespace
from urllib.parse import urlencode, parse_qs, urlsplit

from precision_theme import render_header, CSS


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

    def test_admin_navigation_is_hidden_for_guests_and_all_other_roles(self):
        links = [("search", "元器件搜索", "?"), ("member", "会员中心", "?member=1"), ("admin", "管理后台", "?admin=1")]
        for member in [None, {"role": "member"}, {"role": "pm"}, {"role": "sales"}, {"display_name": "管理员"}, {"role": "admin"}]:
            with self.subTest(member=member):
                output = []
                render_header(SimpleNamespace(markdown=lambda value, **kw: output.append(value)), "", "search", links, member, logout_href="?member_logout=1&member_token=owned")
                nav = output[0].split('<nav class="wb-nav"', 1)[1].split('</nav>', 1)[0]
                self.assertEqual("管理后台" in nav, bool(member and member.get("role") == "admin"))
                self.assertEqual('class="wb-logout"' in output[0], bool(member))
                if member:
                    self.assertIn('href="?member_logout=1&amp;member_token=owned"', output[0])
                    self.assertIn('aria-label="退出登录"', output[0])
                    self.assertGreater(output[0].index('class="wb-logout"'), output[0].index('</nav>'))

    def test_logout_visible_on_every_member_page_but_never_for_guest(self):
        for active in ["search", "bom", "training", "member", "admin"]:
            for member in [None, {"role": "member"}, {"role": "admin"}]:
                output = []
                render_header(SimpleNamespace(markdown=lambda value, **kw: output.append(value)), "", active, [], member, logout_href="?member_logout=1")
                self.assertEqual(output[0].count('class="wb-logout"'), int(bool(member)))
        self.assertIn('.wb-logout {margin-top:auto;', CSS)
        self.assertIn('@media(max-width:760px) {.wb-logout {margin-top:0;', CSS)

    def test_real_workbench_links_use_verified_role_and_existing_logout_route(self):
        tree = ast.parse(self.matcher)
        start = next(n.lineno for n in tree.body if isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "workbench_active" for t in n.targets))
        end = next(n.end_lineno for n in tree.body if isinstance(n, ast.Expr) and isinstance(n.value, ast.Call) and isinstance(n.value.func, ast.Name) and n.value.func.id == "render_workbench_header")
        block = ast.Module(body=[n for n in tree.body if start <= n.lineno <= end], type_ignores=[])
        code = compile(block, str(MATCHER_PATH), "exec")
        for role in [None, "member", "pm", "sales", "admin"]:
            rendered = []
            member = {"role": role, "username": "fixture"} if role else None
            env = dict(st=SimpleNamespace(session_state={"_member_auth_token": "owned"}), logo_b64="", os=SimpleNamespace(getenv=lambda key: ""), requested_page_mode=lambda: "training", current_member=lambda: member, current_member_is_admin=lambda: role == "admin", clean_text=lambda text: str(text or "").strip(), get_query_param_value=lambda key: "", MEMBER_AUTH_QUERY_PARAM="member_token", MEMBER_LOGOUT_QUERY_PARAM="member_logout", ADMIN_BACKEND_MODULE_QUERY_PARAM="admin_module", build_app_href=lambda **kw: "?" + urlencode(kw), render_workbench_header=lambda *a, **kw: rendered.append((a, kw)))
            exec(code, env)
            keys = [key for key, _, _ in env["workbench_links"]]
            self.assertEqual("admin" in keys, role == "admin")
            self.assertEqual(keys[:4], ["search", "bom", "training", "member"])
            href = rendered[0][1]["logout_href"]
            if role:
                query = parse_qs(urlsplit(href).query)
                self.assertEqual(query["member_logout"], ["1"])
                self.assertEqual(query["member_token"], ["owned"])
            else:
                self.assertIsNone(href)


if __name__ == "__main__":
    unittest.main(verbosity=2)
