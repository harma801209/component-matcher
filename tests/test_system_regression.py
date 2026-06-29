import logging
import json
import os
import runpy
import shutil
import sqlite3
import tempfile
import threading
import time
import unittest
import warnings
from io import BytesIO
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pandas as pd
from openpyxl import Workbook


class UploadedBytes:
    def __init__(self, name, data):
        self.name = name
        self._data = data
        self.size = len(data)

    def getvalue(self):
        return self._data

    def read(self, *args):
        return self._data

    def seek(self, *args):
        return 0


def dataframe_to_xlsx_bytes(frame):
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        frame.to_excel(writer, index=False, sheet_name="报价")
    return output.getvalue()


def fojan_quote_xlsx_bytes():
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "报价"
    sheet.merge_cells("A1:F1")
    sheet["A1"] = "电阻系列产品报价单"
    sheet.append(["TO:", "", "TEL:", "", "Date:2026/6/12", ""])
    sheet.merge_cells("D3:E3")
    sheet.append(["Series", "Type / Dimension", "Resistance Range", "New Unit Price", "", "Package"])
    sheet.append(["", "", "Ω (ohms)", "5%", "1%", ""])
    sheet.append(["FRC", "0603 1/10W", "0R,510R-10M", "2.60", "", "5000PCS"])
    sheet.append(["FRC", "0603 1/10W", "10R-470R", "2.80", "", "5000PCS"])
    sheet.append(["FRC", "0603 1/10W", "1R-9.9R", "3.60", "", "5000PCS"])
    sheet.append(["FRC", "0603 1/10W", "10R-1M", "", "3.10", "5000PCS"])
    sheet.append(["FRC", "0603 1/10W", "1R-9.9R/1M1-10M", "", "3.63 / 3.2", "5000PCS"])
    output = BytesIO()
    workbook.save(output)
    return output.getvalue()


class SystemRegressionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        logging.disable(logging.CRITICAL)
        warnings.filterwarnings("ignore", category=ResourceWarning)
        cls.base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        cls.temp_dir = tempfile.mkdtemp(prefix="component-matcher-regression-")
        cls.saved_env = {
            key: os.environ.get(key)
            for key in [
                "MEMBER_AUTH_DB_PATH",
                "COST_PRICE_DB_PATH",
                "COMPONENT_MATCHER_BUILD_MODE",
                "COMPONENT_MATCHER_STARTUP_MAINTENANCE",
            ]
        }
        os.environ["MEMBER_AUTH_DB_PATH"] = os.path.join(cls.temp_dir, "member.sqlite")
        os.environ["COST_PRICE_DB_PATH"] = os.path.join(cls.temp_dir, "cost.sqlite")
        os.environ["COMPONENT_MATCHER_BUILD_MODE"] = "1"
        os.environ["COMPONENT_MATCHER_STARTUP_MAINTENANCE"] = "0"
        loaded = runpy.run_path(
            os.path.join(cls.base_dir, "component_matcher.py"),
            run_name="component_matcher_regression",
        )
        # runpy returns a snapshot-like mapping. Function globals are the live
        # module namespace that tests must patch when isolating database paths.
        cls.app = loaded["clean_text"].__globals__
        cls.original_paths = {
            "DB_PATH": cls.app["DB_PATH"],
            "SEARCH_DB_PATH": cls.app["SEARCH_DB_PATH"],
            "NO_MATCH_REPORT_DB_PATH": cls.app["NO_MATCH_REPORT_DB_PATH"],
            "COST_PRICE_DB_PATH": cls.app["COST_PRICE_DB_PATH"],
        }

    @classmethod
    def tearDownClass(cls):
        for key, value in cls.saved_env.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value
        shutil.rmtree(cls.temp_dir, ignore_errors=True)

    def test_01_exact_model_categories_and_library_rows(self):
        models = [
            "AC0402KRX7R9BB103",
            "GRM155R71C224KA12D",
            "BBGK00201209202Y00",
            "NCP15XH103F03RC",
        ]
        by_model = self.app["load_component_rows_by_exact_models_from_search_sidecar"](models)
        self.assertEqual(
            set(by_model[self.app["clean_model"](models[0])]["器件类型"].map(self.app["normalize_component_type"])),
            {"MLCC"},
        )
        self.assertEqual(
            set(by_model[self.app["clean_model"](models[1])]["器件类型"].map(self.app["normalize_component_type"])),
            {"MLCC"},
        )
        self.assertEqual(
            set(by_model[self.app["clean_model"](models[2])]["器件类型"].map(self.app["normalize_component_type"])),
            {"磁珠"},
        )
        self.assertEqual(
            set(by_model[self.app["clean_model"](models[3])]["器件类型"].map(self.app["normalize_component_type"])),
            {"热敏电阻"},
        )

        representative_models = [
            "FBF06FT-3R00N",
            "FAF02FVA1001QMH",
            "FPF05FTF1004NM",
            "FPS03FTE10R0NMD",
            "FMF06FTHR010-BH",
            "JAS103F344FB",
            "JFR103F344FB25025CPG",
            "JNR05S030L",
            "JVT10N180M",
            "JVZ10N180M",
        ]
        imported = self.app["load_component_rows_by_exact_models_from_search_sidecar"](representative_models)
        self.assertTrue(
            all(
                not imported[self.app["clean_model"](model)].empty
                for model in representative_models
            )
        )

        fojan_models = [
            "FRC1206P000TS", "FRC0603J100TS", "FRC0402J330TS", "FRC1206J201TS",
            "FRC0402J511TS", "FRC0402J102TS", "FRC0402J222TS", "FRC0402J472TS",
            "FRC0402J103TS", "FRC0805J103TS", "FRC0402J152TS", "FRC0402F1302TS",
            "FRC0402J513TS", "FRC0402P000TS", "FRC0603P000TS", "FRC0402F1003TS",
            "FRC0603J750TS", "FRC0603F8R20TS", "FRC0402F4701TS", "FRC0402J562TS",
            "FRC0402J303TS", "FRC0402J204TS", "FRC0402F2402TS", "FRC0603F3322TS",
            "FRC0603F5362TS", "FRC0603F2702TS", "FRC0603F4701TS", "FRC0402F2000TS",
            "FRC0402F49R9TS", "FRC0402F7502TS", "FRC0603F3R60TS", "FRC0603F1272TS",
            "FRC0603F2432TS", "FRC0402F3R30TS", "FRC0402F3922TS", "FRC0402F5113TS",
            "FRC0603J561TS", "FRC0603F1962TS", "FRC0603F1053TS",
        ]
        fojan_rows = self.app["load_component_rows_by_exact_models_from_search_sidecar"](fojan_models)
        self.assertTrue(
            all(not fojan_rows[self.app["clean_model"](model)].empty for model in fojan_models)
        )
        for model in fojan_models:
            row = fojan_rows[self.app["clean_model"](model)].iloc[0]
            expected_tolerance = "5" if "J" in model[7:9] or "P000" in model else "1"
            self.assertEqual(str(row["_tol"]), expected_tolerance, model)

        spaced_fojan_5_percent_models = [
            "FRC0603J100 TS", "FRC0402J330 TS", "FRC1206J201 TS", "FRC0402J511 TS",
            "FRC0402J102 TS", "FRC0402J222 TS", "FRC0402J472 TS", "FRC0402J103 TS",
            "FRC0805J103 TS", "FRC0402J152 TS", "FRC0402J513 TS", "FRC0603J750 TS",
            "FRC0402J562 TS", "FRC0402J303 TS", "FRC0402J204 TS", "FRC0603J561 TS",
        ]
        for model in spaced_fojan_5_percent_models:
            resolved = self.app["resolve_search_query_dataframe_and_spec"](model)
            self.assertEqual(resolved["mode"], "料号", model)
            self.assertNotEqual(resolved["resolution_path"], "model_token_prefix_lookup", model)
            rows = resolved["query_df"]
            self.assertTrue(
                rows["_model_clean"].astype(str).eq(self.app["clean_model"](model)).any(),
                model,
            )
            self.assertEqual(str(resolved["spec"].get("容值误差", "")), "5", model)

    def test_02_member_auth_approval_profile_and_search_logs(self):
        app = self.app
        app["ensure_configured_admin_member_account"]()
        admin, message = app["authenticate_member"]("TERRY46", "123456")
        self.assertEqual(message, "")
        self.assertEqual(admin["role"], "admin")
        self.assertTrue(admin["password_hash"].startswith("pbkdf2_sha256$"))
        self.assertNotIn("123456", admin["password_hash"])

        ok, message = app["create_member_account"](
            "CaseUser", "secret1", "Case User", "Old Co", "old@example.com", "100"
        )
        self.assertTrue(ok, message)
        pending, message = app["authenticate_member"]("caseuser", "secret1")
        self.assertIsNone(pending)
        self.assertIn("审核", message)
        duplicate_ok, _ = app["create_member_account"]("CASEUSER", "secret1")
        self.assertFalse(duplicate_ok)

        member = app["get_member_by_username"]("CASEuser")
        ok, message = app["approve_member_account_admin"](member["id"])
        self.assertTrue(ok, message)
        member, message = app["authenticate_member"]("CASEUSER", "secret1")
        self.assertIsNotNone(member, message)
        token = member["_session_token"]
        with sqlite3.connect(app["MEMBER_AUTH_DB_PATH"]) as conn:
            conn.execute(
                "UPDATE member_sessions SET expires_at_ts=? WHERE token=?",
                (int(time.time()) + 5, token),
            )
            conn.commit()
        self.assertIsNotNone(app["get_member_by_session_token"](token))
        with sqlite3.connect(app["MEMBER_AUTH_DB_PATH"]) as conn:
            expires_at = conn.execute(
                "SELECT expires_at_ts FROM member_sessions WHERE token=?", (token,)
            ).fetchone()[0]
        self.assertGreaterEqual(expires_at, int(time.time()) + 3590)

        ok, message = app["update_current_member_profile"](
            member["id"], "Case Renamed", "New Co", "new@example.com", "200"
        )
        self.assertTrue(ok, message)
        logs_before = app["list_member_profile_change_logs"](member["id"])
        self.assertGreaterEqual(len(logs_before), 4)
        ok, message = app["change_current_member_password"](
            member["id"], "secret1", "secret2", "secret2"
        )
        self.assertTrue(ok, message)
        logs_after = app["list_member_profile_change_logs"](member["id"])
        self.assertEqual(len(logs_after), len(logs_before))
        self.assertTrue(all("password" not in str(row.get("field_name", "")).lower() for row in logs_after))
        member, message = app["authenticate_member"]("caseuser", "secret2")
        self.assertIsNotNone(member, message)

        app["record_member_search_logs"](
            member,
            ["0402 10K 1% 1/16W", "0402 10K ±1% 1/16W", "0805 X7R 100nF 10% 50V"],
            source="regression",
        )
        summary = app["list_member_search_log_summary"]("", "", "", 300)
        self.assertGreaterEqual(len(summary), 2)
        for period in ["daily", "weekly", "monthly"]:
            trend = app["build_member_search_trend_dataframe"](summary, period=period)
            self.assertFalse(trend.empty)
            self.assertLessEqual(int(trend["排名"].max()), 10)

    def test_03_resistor_value_size_and_power_guards(self):
        app = self.app
        milliohm = app["parse_resistor_spec_query"]("1206 0.01R 1% 1/4W")
        megaohm = app["parse_resistor_spec_query"]("0402 1M 5% 1/16W")
        self.assertAlmostEqual(float(milliohm["_resistance_ohm"]), 0.01)
        self.assertAlmostEqual(float(megaohm["_resistance_ohm"]), 1_000_000.0)

        code_105 = app["parse_resistor_model_rule"]("FRC0402J105 TS", brand="FOJAN(富捷)")
        code_106 = app["parse_resistor_model_rule"]("FRC0402J106 TS", brand="FOJAN(富捷)")
        self.assertAlmostEqual(float(code_105["_resistance_ohm"]), 1_000_000.0)
        self.assertAlmostEqual(float(code_106["_resistance_ohm"]), 10_000_000.0)

        invalid = app["parse_resistor_spec_query"]("0420 10K 1% 1/16W")
        self.assertTrue(invalid.get("_unsupported_component"))
        self.assertEqual(invalid.get("_invalid_size_token"), "0420")
        resolved = app["resolve_search_query_dataframe_and_spec"]("0420 10K 1% 1/16W")
        self.assertEqual(resolved["resolution_path"], "unsupported_or_invalid_spec")
        self.assertTrue(resolved["query_df"].empty)

        candidates = pd.DataFrame(
            [
                {
                    "品牌": "A",
                    "型号": "R-1-16",
                    "器件类型": "贴片电阻",
                    "尺寸（inch）": "0603",
                    "材质（介质）": "",
                    "耐压（V）": "",
                    "容值_pf": None,
                    "容值": "10",
                    "容值单位": "KΩ",
                    "参数值": "10",
                    "参数单位": "KΩ",
                    "_resistance_ohm": 10000.0,
                    "容值误差": "1",
                    "功率": "1/16W",
                },
                {
                    "品牌": "B",
                    "型号": "R-1-10",
                    "器件类型": "贴片电阻",
                    "尺寸（inch）": "0603",
                    "材质（介质）": "",
                    "耐压（V）": "",
                    "容值_pf": None,
                    "容值": "10",
                    "容值单位": "KΩ",
                    "参数值": "10",
                    "参数单位": "KΩ",
                    "_resistance_ohm": 10000.0,
                    "容值误差": "1",
                    "功率": "1/10W",
                },
            ]
        )
        prepared = app["prepare_search_dataframe"](app["ensure_component_display_columns"](candidates))
        spec = app["parse_resistor_spec_query"]("0603 10K 1% 1/16W")
        original_fetch = app["fetch_search_candidate_pairs"]
        app["fetch_search_candidate_pairs"] = lambda _spec: None
        try:
            matched = app["run_query_match"](prepared, "规格", spec)
        finally:
            app["fetch_search_candidate_pairs"] = original_fetch
        self.assertEqual(set(matched["型号"]), {"R-1-16"})

    def test_04_no_match_resolution_persists_and_searches(self):
        app = self.app
        app["NO_MATCH_REPORT_DB_PATH"] = os.path.join(self.temp_dir, "reports.sqlite")
        app["DB_PATH"] = os.path.join(self.temp_dir, "components.sqlite")
        app["SEARCH_DB_PATH"] = os.path.join(self.temp_dir, "search.sqlite")
        spec = {
            "器件类型": "贴片电阻",
            "尺寸（inch）": "0603",
            "_resistance_ohm": 10000.0,
            "容值误差": "5",
            "功率": "1/10W",
            "规格摘要": "10KΩ ±5% 1/10W 0603",
        }
        query = "0603 10K ±5% 1/10W REGRESSION-MISSING"
        ok, message, report_id = app["submit_no_match_report"](
            query, mode="规格参数", spec=spec, reason="regression"
        )
        self.assertTrue(ok, message)
        self.assertTrue(
            app["resolve_no_match_report"](
                report_id,
                resolved_note="regression resolved",
                resolved_brand="FOJAN(富捷)",
                resolved_model="FRC0603J103 TS",
                resolved_component_type="贴片电阻",
            )
        )
        report = app["get_no_match_report_by_id"](report_id)
        self.assertEqual(report["library_status"], "已写入主库和搜索索引")
        with sqlite3.connect(app["DB_PATH"]) as conn:
            row = conn.execute(
                'SELECT 品牌, 型号 FROM components WHERE REPLACE(UPPER(型号), " ", "")=?',
                ("FRC0603J103TS",),
            ).fetchone()
        self.assertIsNotNone(row)
        for lookup in [query, "FRC0603J103 TS"]:
            resolved = app["resolve_no_match_report_as_query"](lookup)
            self.assertIsNotNone(resolved)
            self.assertFalse(resolved["query_df"].empty)

    def test_05_cost_list_updates_only_changed_cost_time(self):
        app = self.app
        app["COST_PRICE_DB_PATH"] = os.path.join(self.temp_dir, "cost-test.sqlite")
        app["clear_cost_price_lookup_cache"]()
        first = pd.DataFrame(
            [
                {
                    "品牌": "FOJAN(富捷)",
                    "型号": "FRC0603J103 TS",
                    "规格参数": "0603 10K 5%",
                    "成本": "1.40",
                    "MOQ": "5000",
                    "L&T": "4W",
                },
                {
                    "品牌": "厚声UNI-ROYAL",
                    "型号": "0603WAJ0103T5E",
                    "规格参数": "0603 10K 5%",
                    "成本": "2.00",
                    "MOQ": "5000",
                    "L&T": "5W",
                },
            ]
        )
        app["current_timestamp_text"] = lambda: "2026-06-28 10:00:00"
        ok, message, _ = app["import_cost_price_list_from_upload"](
            UploadedBytes("cost1.xlsx", dataframe_to_xlsx_bytes(first)), "regression"
        )
        self.assertTrue(ok, message)
        second = first.copy()
        second.loc[0, "成本"] = "1.4"
        second.loc[1, "成本"] = "2.20"
        app["current_timestamp_text"] = lambda: "2026-06-29 11:00:00"
        ok, message, list_id = app["import_cost_price_list_from_upload"](
            UploadedBytes("cost2.xlsx", dataframe_to_xlsx_bytes(second)), "regression"
        )
        self.assertTrue(ok, message)
        by_model = {item["model"]: item for item in app["list_cost_price_items"](list_id, 10)}
        self.assertEqual(by_model["FRC0603J103 TS"]["cost_updated_at"], "2026-06-28 10:00:00")
        self.assertEqual(by_model["0603WAJ0103T5E"]["cost_updated_at"], "2026-06-29 11:00:00")
        entry = app["lookup_active_cost_price_for_row"](
            {"品牌": "FOJAN(富捷)", "型号": "FRC0603J103 TS"}
        )
        self.assertEqual(entry["cost"], "1.4")
        self.assertEqual(entry["moq"], "5000")
        self.assertEqual(entry["lead_time"], "4W")

    def test_06_bom_full_read_export_and_display_columns(self):
        app = self.app
        bom = pd.DataFrame(
            {
                "物料编号": [f"P{i:03d}" for i in range(85)],
                "规格": [f"0603 {i + 1}K 1% 1/10W" for i in range(85)],
                "需求数量": ["1000"] * 85,
            }
        )
        workbook = app["read_uploaded_bom_workbook"](
            UploadedBytes("85rows.xlsx", dataframe_to_xlsx_bytes(bom))
        )
        self.assertEqual(len(workbook["sheet_frames"][0]["df"]), 85)
        result = pd.DataFrame(
            [
                {
                    "自有品牌1": "厚声UNI-ROYAL",
                    "自有型号1": "0603WAF1002T5E",
                    "自有成本1": "0.02",
                    "自有更新时间1": "2026-06-28",
                    "自有MOQ1": "5000",
                    "自有L&T1": "4W",
                    "自有品牌2": "FOJAN(富捷)",
                    "自有型号2": "FRC0603F1002 TS",
                    "自有成本2": "0.018",
                    "自有更新时间2": "2026-06-27",
                    "自有MOQ2": "5000",
                    "自有L&T2": "5W",
                    "BOM行号": 1,
                    "BOM型号": "X",
                    "BOM规格": "0603 10K",
                    "销售结论": "x",
                    "备选型号": "x",
                    "风险提示": "x",
                    "推荐理由": "x",
                    "解析说明": "x",
                    "客户回复型号": "x",
                    "可直接回复客户": "x",
                }
            ]
        )
        export = app["build_bom_matched_export_df"](bom, result)
        self.assertEqual(
            list(export.columns[-12:]),
            [
                "品牌",
                "型号",
                "成本",
                "更新时间",
                "MOQ",
                "L&T",
                "品牌2",
                "型号2",
                "成本2",
                "更新时间2",
                "MOQ2",
                "L&T2",
            ],
        )
        display = app["build_bom_display_df"](result)
        forbidden = {
            "销售结论",
            "备选型号",
            "风险提示",
            "推荐理由",
            "解析说明",
            "客户回复型号",
            "可直接回复客户",
        }
        self.assertTrue(forbidden.isdisjoint(set(display.columns)))

    def test_07_member_database_remote_snapshot_survives_instance_reset(self):
        app = self.app
        snapshot = {"version": 0, "sha256": "", "payload_base64": "", "updated_at": ""}
        api_secret = "regression-secret"

        class SnapshotHandler(BaseHTTPRequestHandler):
            def log_message(self, *_args):
                return

            def _authorized(self):
                return self.headers.get("Authorization", "") == f"Bearer {api_secret}"

            def _send(self, status, payload):
                encoded = json.dumps(payload).encode("utf-8")
                self.send_response(status)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(encoded)))
                self.end_headers()
                self.wfile.write(encoded)

            def do_GET(self):
                if not self._authorized():
                    self._send(401, {"error": "unauthorized"})
                    return
                self._send(200, snapshot)

            def do_PUT(self):
                if not self._authorized():
                    self._send(401, {"error": "unauthorized"})
                    return
                length = int(self.headers.get("Content-Length", "0"))
                body = json.loads(self.rfile.read(length).decode("utf-8"))
                if int(body.get("expected_version") or 0) != int(snapshot["version"]):
                    self._send(409, {"error": "version_conflict", "version": snapshot["version"]})
                    return
                snapshot.update(
                    {
                        "version": snapshot["version"] + 1,
                        "sha256": body["sha256"],
                        "payload_base64": body["payload_base64"],
                        "updated_at": "2026-06-29T00:00:00Z",
                    }
                )
                self._send(200, {"ok": True, "version": snapshot["version"], "sha256": snapshot["sha256"]})

        server = ThreadingHTTPServer(("127.0.0.1", 0), SnapshotHandler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        saved_env = {key: os.environ.get(key) for key in ["MEMBER_AUTH_REMOTE_API_URL", "MEMBER_AUTH_REMOTE_API_SECRET", "MEMBER_AUTH_REMOTE_FORCE"]}
        original_state_path = app["MEMBER_AUTH_REMOTE_STATE_PATH"]
        try:
            os.environ["MEMBER_AUTH_REMOTE_API_URL"] = f"http://127.0.0.1:{server.server_port}/api/member-store/snapshot"
            os.environ["MEMBER_AUTH_REMOTE_API_SECRET"] = api_secret
            os.environ["MEMBER_AUTH_REMOTE_FORCE"] = "1"
            app["MEMBER_AUTH_REMOTE_STATE_PATH"] = os.path.join(self.temp_dir, "remote_state.json")
            ok, message = app["create_member_account"]("DurableUser", "secret1", "Durable User")
            self.assertTrue(ok, message)
            member = app["get_member_by_username"]("durableuser")
            app["approve_member_account_admin"](member["id"])
            self.assertGreaterEqual(snapshot["version"], 1)

            with sqlite3.connect(app["MEMBER_AUTH_DB_PATH"]) as conn:
                conn.execute("DELETE FROM members WHERE lower(username)=lower('DurableUser')")
                conn.commit()
            with sqlite3.connect(app["MEMBER_AUTH_DB_PATH"]) as conn:
                self.assertIsNone(
                    conn.execute(
                        "SELECT id FROM members WHERE lower(username)=lower('DurableUser')"
                    ).fetchone()
                )
            self.assertIsNotNone(app["get_member_by_username"]("DurableUser"))
            restored, message = app["authenticate_member"]("DURABLEUSER", "secret1")
            self.assertIsNotNone(restored, message)

            stale_path = os.path.join(self.temp_dir, "member-stale.sqlite")
            shutil.copy2(app["MEMBER_AUTH_DB_PATH"], stale_path)
            ok, message = app["create_member_account"]("OtherInstanceUser", "secret2")
            self.assertTrue(ok, message)
            original_db_path = app["MEMBER_AUTH_DB_PATH"]
            app["MEMBER_AUTH_DB_PATH"] = stale_path
            try:
                usernames = {row["username"] for row in app["list_members_for_admin"]()}
                self.assertIn("OtherInstanceUser", usernames)
            finally:
                app["MEMBER_AUTH_DB_PATH"] = original_db_path
        finally:
            app["MEMBER_AUTH_REMOTE_STATE_PATH"] = original_state_path
            for key, value in saved_env.items():
                if value is None:
                    os.environ.pop(key, None)
                else:
                    os.environ[key] = value
            server.shutdown()
            server.server_close()

    def test_08_fojan_matrix_quote_imports_tolerance_price_rules(self):
        app = self.app
        app["COST_PRICE_DB_PATH"] = os.path.join(self.temp_dir, "fojan-cost.sqlite")
        app["clear_cost_price_lookup_cache"]()
        upload = UploadedBytes("fojan-quote.xlsx", fojan_quote_xlsx_bytes())
        items, error = app["build_cost_price_items_from_workbook"](upload)
        self.assertEqual(error, "")
        self.assertEqual(len(items), 5)
        self.assertEqual({item["brand"] for item in items}, {"FOJAN(富捷)"})

        ok, message, _ = app["import_cost_price_list_from_upload"](upload, "regression")
        self.assertTrue(ok, message)
        lookup = app["load_active_cost_price_lookup"]()

        def price(model, resistance_ohm, tolerance):
            return app["lookup_active_cost_price_for_row"](
                {
                    "品牌": "FOJAN(富捷)",
                    "型号": model,
                    "器件类型": "贴片电阻",
                    "尺寸（inch）": "0603",
                    "功率": "1/10W",
                    "_resistance_ohm": resistance_ohm,
                    "容值误差": tolerance,
                },
                lookup=lookup,
            ).get("cost", "")

        self.assertEqual(price("FRC0603J100 TS", 10.0, "5"), "2.80")
        self.assertEqual(price("FRC0603J103 TS", 10000.0, "5"), "2.60")
        self.assertEqual(price("FRC0603F1002 TS", 10000.0, "1"), "3.10")
        self.assertEqual(price("FRC0603F8R20 TS", 8.2, "1"), "3.63")


if __name__ == "__main__":
    unittest.main(verbosity=2)
