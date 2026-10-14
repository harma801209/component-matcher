"""Native Chrome account navigation/logout checks with isolated local records.

--public uses an explicitly supplied QA login, never creates/edits members or
costs. Only the QA session itself is signed out. Credentials/tokens are not
printed or written to evidence.
"""
import argparse
import json
import logging
import os
import platform
import runpy
import sqlite3
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from urllib.parse import parse_qs, urlencode, urlsplit

platform._wmi = None
logging.disable(logging.CRITICAL)
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT.parent / "ocr-diagnostic-20261014/account-navigation"
OUT.mkdir(parents=True, exist_ok=True)
sys.path.insert(0, str(ROOT))
parser = argparse.ArgumentParser()
parser.add_argument("--public", action="store_true")
args = parser.parse_args()
prefix = "formal" if args.public else "local"
server = None
log = None
fixture = None
try:
    if args.public:
        url = "https://fruition-component.pages.dev/"
        username = os.environ["WORKBENCH_QA_USERNAME"]
        password = os.environ["WORKBENCH_QA_PASSWORD"]
    else:
        fixture = tempfile.TemporaryDirectory(prefix="account-nav-fixture-", ignore_cleanup_errors=True)
        for key, name in [("MEMBER_AUTH_DB_PATH", "members.sqlite"), ("COST_PRICE_DB_PATH", "costs.sqlite"), ("NO_MATCH_REPORT_DB_PATH", "reports.sqlite"), ("BOM_JOB_DB_PATH", "jobs.sqlite")]:
            os.environ[key] = str(Path(fixture.name) / name)
        os.environ.update(COMPONENT_MATCHER_BUILD_MODE="1", COMPONENT_MATCHER_STARTUP_MAINTENANCE="0", MEMBER_AUTH_REMOTE_FORCE="0", RUNTIME_STORE_REMOTE_FORCE="0")
        module = runpy.run_path(str(ROOT / "component_matcher.py"), run_name="account_nav_isolated_fixture")
        app = module["clean_text"].__globals__
        password = "IsolatedNavigationFixture!"
        username = "FixtureAdmin"
        for name, role in [(username, "admin"), ("FixtureMember", "member")]:
            ok, message = app["create_member_account"](name, password, company="富临通", phone="00000000000", job_title="其他")
            assert ok, message
            with sqlite3.connect(os.environ["MEMBER_AUTH_DB_PATH"]) as conn:
                conn.execute("UPDATE members SET role=?,status='active' WHERE username=?", (role, name))
        log = (OUT / "local-server.log").open("w", encoding="utf-8")
        server = subprocess.Popen([sys.executable, "-c", "import platform;platform._wmi=None;from streamlit.web import cli;cli.main()", "run", "component_matcher.py", "--server.port=8542", "--server.headless=true", "--browser.gatherUsageStats=false"], cwd=ROOT, env=os.environ.copy(), stdout=log, stderr=log, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        url = "http://127.0.0.1:8542/"

    with sync_playwright() as p:
        browser = p.chromium.launch(channel="chrome", headless=True)
        page = browser.new_page(viewport={"width": 1440, "height": 1000})
        errors = []
        page.on("pageerror", lambda e: errors.append(str(e)))

        def frame():
            if not args.public:
                return page.main_frame
            deadline = time.monotonic() + 90
            while time.monotonic() < deadline:
                for f in page.frames:
                    if "fruition-componentmatche.streamlit.app" in f.url:
                        return f
                page.wait_for_timeout(250)
            raise AssertionError("app frame missing")

        def go(query):
            deadline = time.monotonic() + 45
            while True:
                try:
                    page.goto(url + "?" + urlencode(query), wait_until="domcontentloaded", timeout=90000)
                    break
                except Exception:
                    assert time.monotonic() < deadline, "app server failed to start"
                    page.wait_for_timeout(500)
            f = frame()
            f.locator(".wb-sidebar").wait_for(timeout=90000)
            return f

        def visibility(f, admin, signed_in):
            assert f.locator(".wb-nav").get_by_role("link", name="管理后台", exact=True).count() == int(admin)
            assert f.locator(".wb-nav a").count() == 4 + int(admin)
            assert f.locator(".wb-logout").count() == int(signed_in)
            assert f.locator(".wb-user-link").count() == int(signed_in)

        f = go({"admin": 1})
        visibility(f, False, False)
        assert f.locator(".admin-stat-card").count() == 0
        page.screenshot(path=str(OUT / (prefix + "-guest.png")))

        def login(name):
            f = go({"member": 1})
            f.get_by_role("textbox", name="账号", exact=True).first.fill(name)
            f.get_by_role("textbox", name="密码", exact=True).first.fill(password)
            f.get_by_role("button", name="登录", exact=True).click()
            f.locator(".wb-user-link").wait_for(timeout=90000)
            href = f.locator(".wb-logout").get_attribute("href")
            token = parse_qs(urlsplit(href).query)["member_token"][0]
            return f, token

        def logout(f, token):
            f.locator(".wb-logout").click()
            f = frame()
            f.locator(".wb-login-button").wait_for(timeout=90000)
            visibility(f, False, False)
            page.reload(wait_until="domcontentloaded", timeout=90000)
            f = frame()
            f.locator(".wb-login-button").wait_for(timeout=90000)
            visibility(f, False, False)
            f = go({"admin": 1, "member_token": token})
            visibility(f, False, False)
            assert f.locator(".admin-stat-card").count() == 0, "revoked session regained backend access"

        if not args.public:
            f, ordinary_token = login("FixtureMember")
            for mode in ["search", "bom", "training", "member", "admin"]:
                f = go({mode: 1, "member_token": ordinary_token})
                visibility(f, False, True)
                if mode == "admin":
                    assert f.locator(".admin-stat-card").count() == 0
                assert f.get_by_text("成本时间", exact=True).count() == 0
            logout(f, ordinary_token)
            with sqlite3.connect(os.environ["MEMBER_AUTH_DB_PATH"]) as conn:
                assert conn.execute("SELECT COUNT(*) FROM member_sessions WHERE token=?", (ordinary_token,)).fetchone()[0] == 0

        f, token = login(username)
        visibility(f, True, True)
        metrics = {}
        if args.public:
            for module, label in [("member_management", "会员总数"), ("customers", "客户公司"), ("cost_price", "当前清单")]:
                f = go({"admin": 1, "admin_module": module, "member_token": token})
                f.locator(".admin-stat-card").filter(has_text=label).wait_for(timeout=90000)
                visibility(f, True, True)
                metrics[module] = f.locator(".admin-stat-card").all_inner_texts()
            assert any("会员总数\n7\n" in q for q in metrics["member_management"])
            assert any("历史清单\n15\n" in q for q in metrics["cost_price"])
            assert any("2227" in q for q in metrics["cost_price"])
        for mode in ["search", "bom", "training", "member", "admin"]:
            f = go({mode: 1, "member_token": token})
            visibility(f, True, True)
        f = go({"training": 1, "member_token": token})
        bottom = f.locator(".wb-logout").bounding_box()
        rail = f.locator(".wb-sidebar").bounding_box()
        assert bottom and rail and abs(bottom["y"] + bottom["height"] - rail["y"] - rail["height"]) < 1
        first = f.locator(".wb-nav a").first.bounding_box()
        header = f.locator(".wb-header").bounding_box()
        assert first and header and abs(first["height"] - header["height"]) < .01
        page.screenshot(path=str(OUT / (prefix + "-admin-desktop.png")))
        page.set_viewport_size({"width": 390, "height": 844})
        assert f.locator(".wb-logout").is_visible()
        page.screenshot(path=str(OUT / (prefix + "-admin-mobile.png")))
        logout(f, token)
        assert not errors, errors
        (OUT / (prefix + "-acceptance.json")).write_text(json.dumps({"public": args.public, "admin_only": True, "ordinary_hidden": not args.public, "logout_revokes_and_refresh_stays_out": True, "bottom_pinned": True, "header_aligned": True, "metrics": metrics, "errors": errors}, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps({"status": "passed", "public": args.public, "ordinary_roles": "isolated" if not args.public else "unit/local coverage", "logout": "revoked; refresh and replay denied", "metrics": metrics, "errors": errors}, ensure_ascii=False), flush=True)
        browser.close()
finally:
    if server:
        server.terminate()
        server.wait(timeout=20)
    if log:
        log.close()
    if fixture:
        fixture.cleanup()
