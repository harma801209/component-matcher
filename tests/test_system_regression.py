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
from urllib.parse import parse_qs, urlsplit

import pandas as pd
from openpyxl import Workbook, load_workbook


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
    sheet.append(["Series", "Type / Dimension", "Resistance Range", "New Unit Price/含税成本Kpcs", "", "Package"])
    sheet.append(["", "", "Ω (ohms)", "5%", "1%", ""])
    sheet["D5"] = 0.05
    sheet["E5"] = 0.01
    sheet["D5"].number_format = "0%"
    sheet["E5"].number_format = "0%"
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
                "NO_MATCH_REPORT_DB_PATH",
                "COMPONENT_MATCHER_BUILD_MODE",
                "COMPONENT_MATCHER_STARTUP_MAINTENANCE",
            ]
        }
        os.environ["MEMBER_AUTH_DB_PATH"] = os.path.join(cls.temp_dir, "member.sqlite")
        os.environ["COST_PRICE_DB_PATH"] = os.path.join(cls.temp_dir, "cost.sqlite")
        os.environ["NO_MATCH_REPORT_DB_PATH"] = os.path.join(cls.temp_dir, "reports.sqlite")
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

    def test_00_runtime_database_paths_are_isolated(self):
        temp_root = os.path.normcase(os.path.abspath(self.temp_dir))
        for key in ("MEMBER_AUTH_DB_PATH", "COST_PRICE_DB_PATH", "NO_MATCH_REPORT_DB_PATH"):
            database_path = os.path.normcase(os.path.abspath(self.app[key]))
            self.assertEqual(os.path.commonpath([temp_root, database_path]), temp_root, key)

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

    def test_02b_member_login_returns_to_requesting_page(self):
        app = self.app
        original_functions = {
            name: app[name]
            for name in [
                "set_current_member",
                "is_member_page_requested",
                "is_bom_page_requested",
                "update_query_params",
                "st",
            ]
        }
        member_calls = []
        route_updates = []
        fake_st = type("FakeStreamlit", (), {"session_state": {}})()
        try:
            app["st"] = fake_st
            app["set_current_member"] = lambda member: member_calls.append(member)
            app["update_query_params"] = lambda **updates: route_updates.append(updates)
            app["is_bom_page_requested"] = lambda: False
            app["is_member_page_requested"] = lambda: True
            app["complete_member_login"]({"id": 7})
            self.assertEqual(member_calls, [{"id": 7}])
            self.assertEqual(route_updates, [{"member": "", "admin": ""}])

            app["is_member_page_requested"] = lambda: False
            app["complete_member_login"]({"id": 8})
            self.assertEqual(member_calls[-1], {"id": 8})
            self.assertEqual(len(route_updates), 1)

            fake_st.session_state[app["BOM_PENDING_UPLOAD_WAITING_LOGIN_KEY"]] = True
            app["is_bom_page_requested"] = lambda: True
            app["complete_member_login"]({"id": 9})
            self.assertEqual(
                fake_st.session_state[app["BOM_POST_LOGIN_RESUME_STAGE_KEY"]],
                app["BOM_POST_LOGIN_STAGE_LOGIN_COMPLETE"],
            )
        finally:
            app.update(original_functions)

    def test_02c_pending_search_resumes_once_after_login(self):
        app = self.app
        original_st = app["st"]
        original_current_member = app["current_member"]
        fake_st = type("FakeStreamlit", (), {"session_state": {}})()
        try:
            app["st"] = fake_st
            app["current_member"] = lambda: None
            app["remember_pending_member_search"](" 0402 1% 10K ")
            self.assertEqual(app["resumable_member_search_query"](), "")

            app["current_member"] = lambda: {"id": 7}
            self.assertEqual(app["resumable_member_search_query"](), "0402 1% 10K")
            app["clear_pending_member_search"]()
            self.assertEqual(app["resumable_member_search_query"](), "")
        finally:
            app["st"] = original_st
            app["current_member"] = original_current_member

        resolve_bom_resume = app["resolve_bom_post_login_resume_action"]
        self.assertEqual(resolve_bom_resume(True, "", True, True), "announce_restore")
        self.assertEqual(
            resolve_bom_resume(False, app["BOM_POST_LOGIN_STAGE_LOGIN_COMPLETE"], True, True),
            "announce_restore",
        )
        self.assertEqual(
            resolve_bom_resume(False, app["BOM_POST_LOGIN_STAGE_UPLOAD_RESTORED"], True, True),
            "resume",
        )
        self.assertEqual(resolve_bom_resume(True, "", True, False), "missing_upload")
        self.assertEqual(resolve_bom_resume(True, "", False, True), "")

    def test_02d_compact_search_summary_and_read_only_runtime_snapshot(self):
        app = self.app
        progress_state = app["build_search_progress_state"](
            total_queries=3,
            completed_queries=3,
            stage_text="搜索已完成",
            elapsed_seconds=1.25,
            done=True,
            extra_chips=[{"label": "有结果", "value": "2", "tone": "success"}],
            summary_lines=["已返回可查看结果 2 条", "未找到匹配结果 1 条"],
        )
        summary_html = app["build_search_progress_summary_html"](progress_state)
        self.assertIn('class="search-progress-summary"', summary_html)
        self.assertIn("处理 3/3", summary_html)
        self.assertIn("有结果 2", summary_html)
        self.assertNotIn("bom-progress-track", summary_html)

        original_values = {
            name: app[name]
            for name in [
                "DB_PATH",
                "SEARCH_DB_PATH",
                "STREAMLIT_CLOUD_BUNDLE_MANIFEST_PATH",
                "MEMBER_AUTH_REMOTE_STATE_PATH",
                "RUNTIME_STORE_REMOTE_STATE_DIR",
            ]
        }
        original_release = os.environ.get("COMPONENT_MATCHER_RELEASE_STAMP")
        try:
            main_db = os.path.join(self.temp_dir, "runtime-main.sqlite")
            search_db = os.path.join(self.temp_dir, "runtime-search.sqlite")
            manifest_path = os.path.join(self.temp_dir, "runtime-manifest.json")
            with sqlite3.connect(main_db) as conn:
                conn.execute("CREATE TABLE components (id INTEGER PRIMARY KEY)")
                conn.executemany("INSERT INTO components (id) VALUES (?)", [(1,), (2,), (3,)])
            with sqlite3.connect(search_db) as conn:
                conn.execute("CREATE TABLE search_meta (meta_json TEXT NOT NULL)")
                conn.execute(
                    "INSERT INTO search_meta (meta_json) VALUES (?)",
                    (json.dumps({"table_row_counts": {"components_search_core": 321}}),),
                )
            with open(manifest_path, "w", encoding="utf-8") as handle:
                json.dump(
                    {
                        "build_epoch_ns": 1_700_000_000_000_000_000,
                        "members": [
                            {
                                "path": "cache/components_search.sqlite",
                                "size": 100,
                                "mtime_ns": 1,
                                "sha256": "abcdef1234567890",
                            }
                        ],
                    },
                    handle,
                )
            app["DB_PATH"] = main_db
            app["SEARCH_DB_PATH"] = search_db
            app["STREAMLIT_CLOUD_BUNDLE_MANIFEST_PATH"] = manifest_path
            app["MEMBER_AUTH_REMOTE_STATE_PATH"] = os.path.join(self.temp_dir, "runtime-member-state.json")
            app["RUNTIME_STORE_REMOTE_STATE_DIR"] = self.temp_dir
            os.environ["COMPONENT_MATCHER_RELEASE_STAMP"] = "2026-07-11T18:12:06+08:00"
            snapshot = app["build_runtime_status_snapshot"]()
            self.assertEqual(snapshot["component_rows"], 3)
            self.assertEqual(snapshot["search_rows"], 321)
            self.assertEqual(snapshot["database_version"], "abcdef123456")
            self.assertEqual(snapshot["release_stamp"], "2026-07-11T18:12:06+08:00")
        finally:
            app.update(original_values)
            if original_release is None:
                os.environ.pop("COMPONENT_MATCHER_RELEASE_STAMP", None)
            else:
                os.environ["COMPONENT_MATCHER_RELEASE_STAMP"] = original_release

    def test_03_resistor_value_size_and_power_guards(self):
        app = self.app
        milliohm = app["parse_resistor_spec_query"]("1206 0.01R 1% 1/4W")
        megaohm = app["parse_resistor_spec_query"]("0402 1M 5% 1/16W")
        self.assertAlmostEqual(float(milliohm["_resistance_ohm"]), 0.01)
        self.assertAlmostEqual(float(megaohm["_resistance_ohm"]), 1_000_000.0)

        slash_specs = [
            ("贴片\\1.24K\\±1%\\1/16W\\0402 ROHS", 1_240.0, "1"),
            ("贴片\\499R\\±1%\\1/16W\\0402 ROHS", 499.0, "1"),
            ("贴片\\499K\\±1%\\1/16W\\0402 ROHS", 499_000.0, "1"),
            ("贴片\\51R\\±5%\\1/16W\\0402 ROHS", 51.0, "5"),
        ]
        for query, expected_ohm, expected_tol in slash_specs:
            parsed = app["parse_resistor_spec_query"](query)
            self.assertIsNotNone(parsed, query)
            self.assertEqual(parsed["器件类型"], "贴片电阻", query)
            self.assertEqual(parsed["尺寸（inch）"], "0402", query)
            self.assertEqual(parsed["_power"], "1/16W", query)
            self.assertEqual(app["clean_tol_for_match"](parsed["容值误差"]), expected_tol, query)
            self.assertAlmostEqual(float(parsed["_resistance_ohm"]), expected_ohm, msg=query)
            mode, detected = app["detect_query_mode_and_spec"](pd.DataFrame(), query)
            self.assertEqual(mode, "贴片电阻", query)
            self.assertEqual(detected["器件类型"], "贴片电阻", query)
            self.assertIsNone(detected.get("容值_pf"), query)

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

        brand_candidates = pd.DataFrame(
            [
                {
                    "品牌": "FOJAN(富捷)",
                    "型号": "FRC0402F1002TS",
                    "器件类型": "贴片电阻",
                    "尺寸（inch）": "0402",
                    "材质（介质）": "",
                    "耐压（V）": "",
                    "容值_pf": None,
                    "_resistance_ohm": 10000.0,
                    "容值": "10",
                    "容值单位": "KΩ",
                    "容值误差": "1",
                    "功率": "1/16W",
                },
                {
                    "品牌": "华新科Walsin",
                    "型号": "WR04X1002FTL",
                    "器件类型": "贴片电阻",
                    "尺寸（inch）": "0402",
                    "材质（介质）": "",
                    "耐压（V）": "",
                    "容值_pf": None,
                    "_resistance_ohm": 10000.0,
                    "容值": "10",
                    "容值单位": "KΩ",
                    "容值误差": "1",
                    "功率": "1/16W",
                },
            ]
        )
        prepared_brand = app["prepare_search_dataframe"](app["ensure_component_display_columns"](brand_candidates))
        original_fetch = app["fetch_search_candidate_pairs"]
        app["fetch_search_candidate_pairs"] = lambda _spec: None
        try:
            no_brand = app["run_query_match"](
                prepared_brand,
                "贴片电阻",
                app["parse_resistor_spec_query"]("0402 1% 10K"),
            )
            self.assertEqual(set(no_brand["型号"]), {"FRC0402F1002TS", "WR04X1002FTL"})
            self.assertEqual(no_brand.iloc[0]["品牌"], "FOJAN(富捷)")
            self.assertEqual(app["brand_priority_value"]("FOJAN(富捷)", "贴片电阻"), 1)
            self.assertEqual(app["brand_priority_value"]("信昌PDC", "贴片电阻"), 2)
            self.assertEqual(app["brand_priority_value"]("华新科Walsin", "贴片电阻"), 3)
            self.assertEqual(app["brand_priority_value"]("厚声UNI-ROYAL", "贴片电阻"), 4)

            fojan_source_spec = app["parse_resistor_spec_query"]("0402 1% 10K")
            fojan_source_spec.update({"品牌": "FOJAN(富捷)", "型号": "FRC0402F1002TS"})
            fojan_source_matches = app["run_query_match"](prepared_brand, "料号", fojan_source_spec)
            self.assertEqual(fojan_source_matches.iloc[0]["品牌"], "FOJAN(富捷)")
            self.assertEqual(fojan_source_matches.iloc[0]["型号"], "FRC0402F1002TS")

            walsin_source_spec = app["parse_resistor_spec_query"]("0402 1% 10K")
            walsin_source_spec.update({"品牌": "华新科Walsin", "型号": "WR04X1002FTL"})
            walsin_source_matches = app["run_query_match"](prepared_brand, "料号", walsin_source_spec)
            self.assertEqual(set(walsin_source_matches["品牌"]), {"FOJAN(富捷)"})

            for query in ("富捷 0402 1% 10K", "0402 1% 10K 富捷", "FOJAN 0402 1% 10K"):
                mode, brand_spec = app["detect_query_mode_and_spec"](pd.DataFrame(), query)
                self.assertEqual(mode, "贴片电阻", query)
                self.assertEqual(brand_spec["品牌"], "FOJAN(富捷)", query)
                self.assertTrue(brand_spec.get(app["BRAND_QUERY_FILTER_FLAG"]), query)
                matched_brand = app["run_query_match"](prepared_brand, mode, brand_spec)
                self.assertEqual(set(matched_brand["品牌"]), {"FOJAN(富捷)"}, query)
                self.assertEqual(set(matched_brand["型号"]), {"FRC0402F1002TS"}, query)

            mode, rohm_spec = app["detect_query_mode_and_spec"](
                pd.DataFrame(), "贴片电阻 10K 0603 ±1% 0.25W ESR系列 ROHM"
            )
            self.assertEqual(mode, "厚膜电阻")
            self.assertEqual(rohm_spec["品牌"], "ROHM")
            self.assertTrue(rohm_spec.get(app["BRAND_QUERY_FILTER_FLAG"]))
        finally:
            app["fetch_search_candidate_pairs"] = original_fetch

        fojan_no_power = app["parse_resistor_spec_query"]("0805 910R ±1%")
        self.assertEqual(app["build_fojan_resistor_model_from_spec"](fojan_no_power), "FRC0805F9100TS")
        fojan_low_ohm_no_power = app["parse_resistor_spec_query"]("1206 10mΩ ±1%")
        self.assertEqual(app["build_fojan_resistor_model_from_spec"](fojan_low_ohm_no_power), "FRL1206FR010TS")
        fojan_wrong_power = app["parse_resistor_spec_query"]("1206 10mΩ ±1% 1W")
        self.assertEqual(app["build_fojan_resistor_model_from_spec"](fojan_wrong_power), "")

        real_fojan_row = pd.DataFrame(
            [
                {
                    "品牌": "FOJAN(富捷)",
                    "型号": "FRC0603J102 TS",
                    "器件类型": "厚膜电阻",
                    "_component_type": "厚膜电阻",
                    "系列": "FRC",
                    "系列说明": "普通厚膜贴片电阻",
                    "尺寸（inch）": "0603",
                    "容值": "1",
                    "容值单位": "KΩ",
                    "容值误差": "5",
                    "数据来源": "JLC-SMT官方元器件清单",
                }
            ]
        )
        fallback_fojan_row = pd.DataFrame(
            [
                {
                    "品牌": "FOJAN(富捷)",
                    "型号": "FRC0603J102TS",
                    "器件类型": "厚膜电阻",
                    "_component_type": "厚膜电阻",
                    "系列": "FRC",
                    "系列说明": "普通厚膜贴片电阻",
                    "尺寸（inch）": "0603",
                    "容值误差": "5",
                    "数据来源": "型号编码解析（成本按当前富捷系列规则）",
                }
            ]
        )
        merged_fojan = app["concat_component_frames"]([real_fojan_row, fallback_fojan_row])
        self.assertEqual(merged_fojan["型号"].tolist(), ["FRC0603J102 TS"])

        original_query = "100Ω;50V;±1%;1/16W;0402;RC0402FR-07100RL;无卤"
        exact_yageo = app["prepare_search_dataframe"](
            app["ensure_component_display_columns"](
                pd.DataFrame(
                    [
                        {
                            "品牌": "国巨YAGEO",
                            "型号": "RC0402FR-07100RL",
                            "器件类型": "厚膜电阻",
                            "系列": "RC",
                            "尺寸（inch）": "0402",
                            "材质（介质）": "",
                            "容值_pf": None,
                            "容值": "100",
                            "容值单位": "Ω",
                            "容值误差": "1",
                            "功率": "1/16W",
                            "耐压（V）": "50",
                            "特殊用途": "无卤",
                        }
                    ]
                )
            )
        )
        mode, original_spec = app["detect_query_mode_and_spec"](exact_yageo, original_query)
        original_spec = app["merge_query_text_hints_into_spec"](original_spec, original_query)
        self.assertEqual(app["normalize_special_use"](original_spec["特殊用途"]), "无卤")

        fojan_candidate = app["build_fojan_rule_candidate_from_spec"](original_spec)
        candidate_frame = app["finalize_search_candidate_frames"]([exact_yageo, fojan_candidate])
        fojan_rows = candidate_frame[
            candidate_frame["型号"].astype(str).map(app["clean_model"]).eq("FRC0402F1000TS")
        ]
        self.assertEqual(len(fojan_rows), 1)
        self.assertEqual(app["clean_voltage"](fojan_rows.iloc[0]["耐压（V）"]), "50")
        self.assertEqual(app["normalize_special_use"](fojan_rows.iloc[0]["特殊用途"]), "无卤")

        original_matches = app["run_query_match"](candidate_frame, mode, original_spec)
        self.assertIn(
            "FRC0402F1000TS",
            set(original_matches["型号"].astype(str).map(app["clean_model"])),
        )

        direct_query = "100Ω;50V;±1%;1/16W;0402;"
        direct_spec = app["parse_resistor_spec_query"](direct_query)
        direct_spec = app["merge_query_text_hints_into_spec"](direct_spec, direct_query)
        self.assertEqual(direct_spec["尺寸（inch）"], "0402")
        self.assertEqual(direct_spec["_power"], "1/16W")
        self.assertEqual(app["clean_voltage"](direct_spec["耐压（V）"]), "50")
        self.assertAlmostEqual(float(direct_spec["_resistance_ohm"]), 100.0)
        self.assertEqual(app["build_fojan_resistor_model_from_spec"](direct_spec), "FRC0402F1000TS")

        direct_candidates = app["finalize_search_candidate_frames"](
            [app["build_fojan_rule_candidate_from_spec"](direct_spec)]
        )
        direct_matches = app["run_query_match"](direct_candidates, "贴片电阻", direct_spec)
        self.assertEqual(
            set(direct_matches["型号"].astype(str).map(app["clean_model"])),
            {"FRC0402F1000TS"},
        )
        direct_spec_info = app["build_spec_info_df"](direct_spec)
        self.assertEqual(app["clean_text"](direct_spec_info.iloc[0]["系列"]), "")

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
                    "状态": "可推荐",
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
        self.assertEqual(export.iloc[0]["匹配状态"], "可推荐")
        self.assertEqual(export.iloc[0]["匹配说明"], "x")
        self.assertEqual(
            list(export.columns[-12:]),
            [
                "匹配品牌",
                "匹配型号",
                "匹配成本",
                "成本更新时间",
                "匹配MOQ",
                "匹配L&T",
                "匹配品牌2",
                "匹配型号2",
                "匹配成本2",
                "成本更新时间2",
                "匹配MOQ2",
                "匹配L&T2",
            ],
        )
        candidates = pd.DataFrame(
            [
                {
                    "品牌": "华新科Walsin",
                    "型号": "0402B103K500CT-A",
                    "器件类型": "MLCC",
                    "推荐等级": "完全匹配",
                    "成本": "",
                },
                {
                    "品牌": "华新科Walsin",
                    "型号": "0402B103K500CT-B",
                    "器件类型": "MLCC",
                    "推荐等级": "完全匹配",
                    "成本": "0.018",
                    "MOQ": "5000PCS",
                },
                {
                    "品牌": "信昌PDC",
                    "型号": "CC10B103K500A",
                    "器件类型": "MLCC",
                    "推荐等级": "完全匹配",
                    "成本": "0.020",
                },
            ]
        )
        custom_settings = {"mode": app["BOM_EXPORT_MODE_CUSTOM"], "brands": ["华新科Walsin"]}
        custom_slots = app["build_bom_own_brand_export_slots"](
            candidates,
            spec={"器件类型": "MLCC"},
            export_settings=custom_settings,
        )
        self.assertEqual(custom_slots["自有品牌"], "华新科Walsin")
        self.assertEqual(custom_slots["自有型号"], "0402B103K500CT-B")
        self.assertEqual(custom_slots["自有成本"], "0.018")
        self.assertEqual(custom_slots["自有品牌2"], "")

        auto_slots = app["build_bom_own_brand_export_slots"](
            candidates,
            spec={"器件类型": "MLCC"},
            export_settings={"mode": app["BOM_EXPORT_MODE_AUTO"]},
        )
        self.assertEqual(auto_slots["自有品牌"], "华科")
        self.assertEqual(auto_slots["自有品牌2"], "信昌")
        self.assertIn("芯声微HRE", app["bom_export_brand_options"]())

        generic_slots = app["build_bom_own_brand_export_slots"](
            pd.DataFrame(
                [
                    {
                        "品牌": "村田Murata",
                        "型号": "LQH32PN100MN0L",
                        "器件类型": "功率电感",
                        "推荐等级": "完全匹配",
                        "成本": "0.5",
                    }
                ]
            ),
            spec={"器件类型": "功率电感"},
            export_settings={"mode": app["BOM_EXPORT_MODE_AUTO"]},
        )
        self.assertEqual(generic_slots["自有品牌"], "村田Murata")
        self.assertEqual(generic_slots["自有型号"], "LQH32PN100MN0L")

        signature_a = app["build_bom_workbook_run_signature"](
            UploadedBytes("same.xlsx", b"same"),
            {"Sheet1": {"model": "型号"}},
            export_settings=custom_settings,
        )
        signature_b = app["build_bom_workbook_run_signature"](
            UploadedBytes("same.xlsx", b"same"),
            {"Sheet1": {"model": "型号"}},
            export_settings={"mode": app["BOM_EXPORT_MODE_CUSTOM"], "brands": ["国巨YAGEO"]},
        )
        self.assertNotEqual(signature_a, signature_b)
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

    def test_06b_bom_selected_brand_exports_active_cost(self):
        app = self.app
        original_cost_path = app["COST_PRICE_DB_PATH"]
        try:
            app["COST_PRICE_DB_PATH"] = os.path.join(self.temp_dir, "bom-selected-brand-cost.sqlite")
            app["clear_cost_price_lookup_cache"]()
            cost_upload = UploadedBytes(
                "bom-cost.xlsx",
                dataframe_to_xlsx_bytes(
                    pd.DataFrame(
                        [
                            {
                                "品牌": "村田Murata",
                                "型号": "GRM155R71C224KA12D",
                                "成本": "0.123",
                                "MOQ": "10000PCS",
                                "L&T": "6W",
                            }
                        ]
                    )
                ),
            )
            ok, message, _ = app["import_cost_price_list_from_upload"](cost_upload, "regression")
            self.assertTrue(ok, message)
            result = app["bom_dataframe_from_upload"](
                None,
                pd.DataFrame([{"型号": "GRM155R71C224KA12D"}]),
                {"model": "型号", "spec": None, "name": None, "quantity": None},
                export_settings={
                    "mode": app["BOM_EXPORT_MODE_CUSTOM"],
                    "brands": ["村田Murata"],
                },
            )
            self.assertEqual(len(result), 1)
            self.assertEqual(result.iloc[0]["自有品牌"], "村田Murata", result.to_dict(orient="records"))
            self.assertEqual(result.iloc[0]["自有型号"], "GRM155R71C224KA12D")
            self.assertEqual(result.iloc[0]["自有成本"], "0.123")
            self.assertEqual(result.iloc[0]["自有MOQ"], "10000PCS")
            self.assertEqual(result.iloc[0]["自有L&T"], "6W")
            source_df = pd.DataFrame([{"型号": "GRM155R71C224KA12D"}])
            source_upload = UploadedBytes("selected-brand.xlsx", dataframe_to_xlsx_bytes(source_df))
            source_workbook = app["read_uploaded_bom_workbook"](source_upload)
            export_bytes = app["bom_to_excel_bytes"](
                result,
                source_df,
                source_workbook=source_workbook,
                sheet_results=[
                    {
                        "sheet_name": source_workbook["sheet_frames"][0]["sheet_name"],
                        "source_df": source_df,
                        "result_df": result,
                    }
                ],
            )
            exported_workbook = load_workbook(BytesIO(export_bytes), data_only=False)
            exported_sheet = exported_workbook.active
            headers = [exported_sheet.cell(row=1, column=idx).value for idx in range(1, exported_sheet.max_column + 1)]
            values = {
                headers[idx - 1]: exported_sheet.cell(row=2, column=idx).value
                for idx in range(1, exported_sheet.max_column + 1)
            }
            self.assertEqual(values["匹配状态"], "可推荐")
            self.assertEqual(values["匹配品牌"], "村田Murata")
            self.assertEqual(values["匹配型号"], "GRM155R71C224KA12D")
            self.assertEqual(str(values["匹配成本"]), "0.123")
            exported_workbook.close()
        finally:
            app["COST_PRICE_DB_PATH"] = original_cost_path
            app["clear_cost_price_lookup_cache"]()

    def test_06c_bom_matching_reuses_bounded_cache_and_rich_candidates(self):
        app = self.app
        candidates = app["build_bom_query_candidates"](
            "GRM155R71C224KA12D",
            "0402 220nF 16V X7R 10%",
            "贴片电容",
            extra_values=["车规"],
        )
        sources = [item["source"] for item in candidates]
        self.assertEqual(sources[0], "型号列")
        self.assertLess(sources.index("型号列+规格列+品名列"), sources.index("规格列"))
        self.assertLess(sources.index("规格列+品名列+其他列"), sources.index("品名列"))

        cache = {}
        for index in range(300):
            app["store_bom_query_cache"](cache, f"Q{index}", {"index": index}, limit=256)
        self.assertEqual(len(cache), 256)
        self.assertNotIn("Q0", cache)
        self.assertEqual(app["bom_query_cache_key"](" 0402   10k  1% "), "0402 10K 1%")

        skipped = app["build_bom_upload_result_row"](
            None,
            0,
            {"型号": "MPN3", "规格": "Description", "品名": "项目"},
            {"model": "型号", "spec": "规格", "name": "品名", "quantity": None},
            query_cache={},
        )
        self.assertEqual(skipped["状态"], "已跳过")
        self.assertIn("重复表头", skipped["失败原因"])

        original_enrich_cost = app["enrich_component_cost_columns"]
        enriched_brands = []

        def capture_enrich_cost(frame):
            enriched_brands.extend(frame["品牌"].astype(str).tolist())
            return frame.copy()

        try:
            app["enrich_component_cost_columns"] = capture_enrich_cost
            app["build_bom_own_brand_export_slots"](
                pd.DataFrame(
                    [
                        {"品牌": "华新科Walsin", "型号": "0402B103K500CT", "器件类型": "MLCC"},
                        {"品牌": "信昌PDC", "型号": "FM05X103K500EGG", "器件类型": "MLCC"},
                        {"品牌": "村田Murata", "型号": "GRM155R71H103KA88D", "器件类型": "MLCC"},
                    ]
                ),
                spec={"器件类型": "MLCC"},
                export_settings={"mode": app["BOM_EXPORT_MODE_CUSTOM"], "brands": ["华新科Walsin"]},
            )
        finally:
            app["enrich_component_cost_columns"] = original_enrich_cost
        self.assertEqual(enriched_brands, ["华新科Walsin"])

        original_bom_dataframe = app["bom_dataframe_from_upload"]
        seen_cache_ids = []

        def fake_bom_dataframe(_df, sheet_df, _mapping, **kwargs):
            seen_cache_ids.append(id(kwargs.get("query_cache")))
            return pd.DataFrame(index=sheet_df.index)

        try:
            app["bom_dataframe_from_upload"] = fake_bom_dataframe
            workbook = {
                "sheet_frames": [
                    {"sheet_name": "A", "df": pd.DataFrame([{"型号": "A1"}])},
                    {"sheet_name": "B", "df": pd.DataFrame([{"型号": "B1"}])},
                ]
            }
            app["build_bom_workbook_sheet_results"](
                workbook,
                sheet_mappings={
                    "A": {"model": "型号", "spec": None, "name": None, "quantity": None},
                    "B": {"model": "型号", "spec": None, "name": None, "quantity": None},
                },
            )
        finally:
            app["bom_dataframe_from_upload"] = original_bom_dataframe
        self.assertEqual(len(seen_cache_ids), 2)
        self.assertEqual(seen_cache_ids[0], seen_cache_ids[1])

    def test_07_member_database_remote_snapshot_survives_instance_reset(self):
        app = self.app
        snapshot = {"version": 0, "sha256": "", "payload_base64": "", "updated_at": ""}
        request_counts = {"get": 0, "put": 0}
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
                request_counts["get"] += 1
                self._send(200, snapshot)

            def do_PUT(self):
                if not self._authorized():
                    self._send(401, {"error": "unauthorized"})
                    return
                request_counts["put"] += 1
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
            app["reset_member_auth_remote_refresh_cache"]()
            self.assertIsNotNone(app["get_member_by_username"]("DurableUser"))
            app["ensure_configured_admin_member_account"]()
            app["reset_member_auth_remote_refresh_cache"]()
            requests_before_login = dict(request_counts)
            app["initialize_member_auth_remote_storage"]()
            restored, message = app["authenticate_member"]("DURABLEUSER", "secret1")
            self.assertIsNotNone(restored, message)
            self.assertEqual(request_counts["get"] - requests_before_login["get"], 1)
            self.assertEqual(request_counts["put"] - requests_before_login["put"], 1)
            requests_after_login = dict(request_counts)
            for _ in range(3):
                self.assertIsNotNone(app["get_member_by_session_token"](restored["_session_token"]))
            self.assertEqual(request_counts, requests_after_login)

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
        self.assertEqual(price("FRC0603F0000 TS", 0.0, "1"), "3.10")

        expected_zero_prices = {}
        for rule in app["load_resistor_series_pricing_rules"]():
            if rule.get("series") != "FRC":
                continue
            expected = app["select_resistor_segment_price"](
                rule.get("range", ""),
                rule.get("price_1", ""),
                10.0,
            )
            if expected:
                expected_zero_prices[rule["type_dimension_norm"]] = (expected, rule.get("package", ""))
        self.assertTrue(expected_zero_prices)
        for type_dimension, (expected_cost, expected_moq) in expected_zero_prices.items():
            size, power = type_dimension.split(" ", 1)
            zero_price = app["lookup_resistor_series_pricing"](
                {
                    "\u54c1\u724c": "FOJAN(\u5bcc\u6377)",
                    "\u578b\u53f7": f"FRC{size}F0000TS",
                    "\u5668\u4ef6\u7c7b\u578b": "\u539a\u819c\u7535\u963b",
                    "\u7cfb\u5217": "FRC",
                    "\u5c3a\u5bf8\uff08inch\uff09": size,
                    "\u529f\u7387": power,
                    "_res_ohm": 0.0,
                    "\u5bb9\u503c\u8bef\u5dee": "1",
                }
            )
            self.assertEqual(zero_price["\u6210\u672c"], expected_cost, type_dimension)
            self.assertEqual(zero_price["MOQ"], expected_moq, type_dimension)

        missing_range_model = app["build_rule_fallback_row_from_model"]("FRC0402F5233TS")
        self.assertEqual(len(missing_range_model), 1)
        fallback_row = missing_range_model.iloc[0]
        self.assertEqual(fallback_row["品牌"], "FOJAN(富捷)")
        self.assertEqual(fallback_row["系列"], "FRC")
        self.assertEqual(fallback_row["尺寸（inch）"], "0402")
        self.assertEqual(fallback_row["容值误差"], "1")
        self.assertAlmostEqual(float(fallback_row["_res_ohm"]), 523000.0)
        fallback_display = app["select_component_display_columns"](
            missing_range_model,
            fallback_row.to_dict(),
            prefix_columns=["品牌", "型号", "器件类别", "系列"],
        )
        self.assertEqual(fallback_display.iloc[0]["品牌"], "FOJAN(富捷)")
        self.assertEqual(fallback_display.iloc[0]["成本"], "1.7")
        self.assertEqual(fallback_display.iloc[0]["MOQ"], "10000PCS")

        for invalid_model in (
            "FRC0402F5243TS",
            "FRC0402F9993TS",
            "FRC0402F0003TS",
            "FRL0402F5233TS",
        ):
            self.assertTrue(app["build_rule_fallback_row_from_model"](invalid_model).empty, invalid_model)

        mode, spec = app["detect_query_mode_and_spec"](
            pd.DataFrame(),
            "0402 523K\u03a9 1% 1/16W \u539a\u819c\u7535\u963b",
        )
        self.assertEqual(mode, "\u539a\u819c\u7535\u963b")
        spec_rows = app["load_search_dataframe_for_query"](mode, spec)
        spec_fojan = spec_rows[
            spec_rows["\u54c1\u724c"].astype(str).str.contains("FOJAN|\u5bcc\u6377", case=False, regex=True)
        ]
        self.assertIn(
            "FRC0402F5233TS",
            set(spec_fojan["\u578b\u53f7"].map(app["clean_model"])),
        )
        spec_price = app["lookup_resistor_series_pricing"](spec_fojan.iloc[0].to_dict())
        self.assertEqual(spec_price["\u6210\u672c"], "1.7")

    def test_09_pdc_series_descriptions_do_not_repeat_vendor_and_series(self):
        app = self.app
        profile = app["lookup_official_resistor_series_profile_by_model"](
            "FCF02FV-8062",
            "PSA(信昌电陶)",
        )
        self.assertEqual(profile.get("系列说明"), "通用厚膜贴片电阻/低阻电流检测贴片电阻")

        source = pd.DataFrame(
            [
                {"品牌": "PSA(信昌电陶)", "系列": "FCF", "系列说明": "PDC FCF 通用厚膜贴片电阻/低阻电流检测贴片电阻"},
                {"品牌": "PSA(信昌电陶)", "系列": "FCF", "系列说明": "PDC FCF-E 通用厚膜电流检测贴片电阻"},
                {"品牌": "PSA(信昌电陶)", "系列": "FWF", "系列说明": "PDC FWF 车规厚膜贴片电阻/抗硫化车规厚膜贴片电阻"},
                {"品牌": "华新科Walsin", "系列": "WR", "系列说明": "通用厚膜贴片电阻"},
            ]
        )
        formatted = app["format_display_df"](source)
        self.assertEqual(
            formatted["系列说明"].tolist(),
            [
                "通用厚膜贴片电阻/低阻电流检测贴片电阻",
                "通用厚膜电流检测贴片电阻",
                "车规厚膜贴片电阻/抗硫化车规厚膜贴片电阻",
                "通用厚膜贴片电阻",
            ],
        )

    def test_10_other_passive_specs_do_not_fall_back_to_wrong_models(self):
        app = self.app

        def match(rows, spec):
            frame = pd.DataFrame(rows)
            with sqlite3.connect(app["DB_PATH"]) as conn:
                source_columns = [row[1] for row in conn.execute('PRAGMA table_info("components")')]
            for column in source_columns:
                if column not in frame.columns:
                    frame[column] = ""
            prepared = app["prepare_search_dataframe"](frame)
            original_fetch = app["fetch_search_candidate_pairs"]
            app["fetch_search_candidate_pairs"] = lambda _spec: None
            try:
                return app["match_other_passive_spec"](prepared, spec)
            finally:
                app["fetch_search_candidate_pairs"] = original_fetch

        inductor_rows = [
            {
                "品牌": "Murata",
                "型号": "TEST-INDUCTOR-4R7",
                "器件类型": "功率电感",
                "容值": "4.7",
                "容值单位": "UH",
                "容值误差": "20",
            }
        ]
        self.assertTrue(
            match(
                inductor_rows,
                {"器件类型": "功率电感", "容值": "10", "容值单位": "UH", "容值误差": "20"},
            ).empty
        )
        self.assertEqual(
            match(
                inductor_rows,
                {"器件类型": "功率电感", "容值": "4.7", "容值单位": "UH", "容值误差": "20"},
            )["型号"].tolist(),
            ["TEST-INDUCTOR-4R7"],
        )

        varistor_rows = [
            {
                "品牌": "Littelfuse",
                "型号": "TEST-VARISTOR-470",
                "器件类型": "引线型压敏电阻",
                "耐压（V）": "470",
                "_varistor_voltage": "470",
                "_disc_size": "14D",
            }
        ]
        self.assertTrue(
            match(
                varistor_rows,
                {"器件类型": "引线型压敏电阻", "耐压（V）": "560", "_varistor_voltage": "560", "_disc_size": "14D"},
            ).empty
        )
        self.assertEqual(
            match(
                varistor_rows,
                {"器件类型": "引线型压敏电阻", "耐压（V）": "470", "_varistor_voltage": "470", "_disc_size": "14D"},
            )["型号"].tolist(),
            ["TEST-VARISTOR-470"],
        )

        mov_rows = [
            {
                "品牌": "Bourns",
                "型号": "MOV-14D471K",
                "器件类型": "引线型压敏电阻",
                "耐压（V）": "775",
                "压敏电压": "470",
                "直径（mm）": "14",
            },
            {
                "品牌": "Placeholder",
                "型号": "",
                "器件类型": "引线型压敏电阻",
                "压敏电压": "470",
                "直径（mm）": "14",
            },
        ]
        self.assertEqual(
            match(
                mov_rows,
                {"器件类型": "引线型压敏电阻", "耐压（V）": "470", "_varistor_voltage": "470", "_disc_size": "14D"},
            )["型号"].tolist(),
            ["MOV-14D471K"],
        )
        self.assertTrue(
            match(
                mov_rows,
                {"器件类型": "引线型压敏电阻", "耐压（V）": "775", "_varistor_voltage": "775", "_disc_size": "14D"},
            ).empty
        )

        common_mode_rows = [
            {
                "品牌": "Panasonic",
                "型号": "EXC14CE121U",
                "器件类型": "共模电感",
                "尺寸（inch）": "0302",
                "容值": "1.574",
                "容值单位": "NH",
                "电感值": "1.574",
                "电感单位": "NH",
                "共模阻抗": "120",
                "阻抗单位": "Ω",
            },
            {
                "品牌": "Panasonic",
                "型号": "EXC14CE900U",
                "器件类型": "共模电感",
                "尺寸（inch）": "0302",
                "共模阻抗": "90",
                "阻抗单位": "Ω",
            },
        ]
        self.assertEqual(
            match(
                common_mode_rows,
                {"器件类型": "共模电感", "容值": "120", "容值单位": "OHM"},
            )["型号"].tolist(),
            ["EXC14CE121U"],
        )
        parsed_common_mode = app["parse_inductor_spec_query"]("共模电感 0302 120OHM 100mA")
        self.assertEqual(parsed_common_mode["器件类型"], "共模电感")
        self.assertEqual(parsed_common_mode["尺寸（inch）"], "0302")
        self.assertEqual(parsed_common_mode["容值"], "120")
        self.assertEqual(parsed_common_mode["容值单位"], "Ω")
        self.assertEqual(parsed_common_mode["共模阻抗"], "120")
        self.assertEqual(parsed_common_mode["阻抗单位"], "Ω")
        self.assertEqual(
            match(common_mode_rows, parsed_common_mode)["型号"].tolist(),
            ["EXC14CE121U"],
        )

        crystal_rows = [
            {
                "品牌": "TXC",
                "型号": "TEST-CRYSTAL-16M",
                "器件类型": "晶振",
                "尺寸（inch）": "3225",
                "容值": "16",
                "容值单位": "MHZ",
                "容值误差": "20PPM",
                "负载电容（pF）": "12",
            }
        ]
        self.assertTrue(
            match(
                crystal_rows,
                {
                    "器件类型": "晶振",
                    "尺寸（inch）": "3225",
                    "容值": "16",
                    "容值单位": "MHZ",
                    "容值误差": "20PPM",
                    "负载电容（pF）": "8",
                },
            ).empty
        )
        self.assertEqual(
            match(
                crystal_rows,
                {
                    "器件类型": "晶振",
                    "尺寸（inch）": "3225",
                    "容值": "16",
                    "容值单位": "MHZ",
                    "容值误差": "20PPM",
                    "负载电容（pF）": "12",
                },
            )["型号"].tolist(),
            ["TEST-CRYSTAL-16M"],
        )

    def test_11_mlcc_special_use_terms_are_hard_constraints(self):
        app = self.app
        strict_queries = {
            "47nF 1210 630V 车规电容": "车规",
            "47nF 1210 630V 谐振电容": "谐振",
            "47nF 1210 630V 工业级电容": "工业",
            "47nF 1210 630V 软端电容": "软端子",
            "47nF 1210 630V 柔性端子电容": "软端子",
            "47nF 1210 630V FLEXITERM": "软端子",
            "47nF 1210 630V 车规软端电容": "车规/软端子",
            "47nF 1210 630V 次车规电容": "次车规",
            "47nF 1210 630V 高压电容": "高压",
            "47nF 1210 630V 中压电容": "中压",
            "47nF 1210 630V 抗弯电容": "抗弯",
            "47nF 1210 630V 安规电容": "安规",
            "47nF 1210 630V 高 Q 低损耗电容": "高Q",
            "47nF 1210 630V EMI 滤波电容": "EMI滤波",
        }
        for query_text, expected_class in strict_queries.items():
            with self.subTest(query=query_text):
                parsed = app["parse_spec_query"](query_text)
                self.assertEqual(parsed["特殊用途"], expected_class)
                self.assertTrue(app["mlcc_series_class_requires_filter"](expected_class))
                self.assertFalse(app["mlcc_series_class_matches"]("常规", expected_class))

        self.assertTrue(app["mlcc_series_class_matches"]("车规/软端子", "车规/软端子"))
        self.assertFalse(app["mlcc_series_class_matches"]("车规", "车规/软端子"))
        self.assertFalse(app["mlcc_series_class_matches"]("软端子", "车规/软端子"))

        query = "47nF 1210 630V 谐振电容"
        spec = app["parse_spec_query"](query)
        self.assertEqual(spec["特殊用途"], "谐振")
        self.assertEqual(app["infer_mlcc_series_class_from_spec"](spec), "谐振")
        spec_info = app["build_spec_info_df"](spec)
        self.assertIn("特殊用途", spec_info.columns)
        self.assertEqual(spec_info.iloc[0]["特殊用途"], "谐振")

        rows = pd.DataFrame(
            [
                {
                    "品牌": "ResonantBrand",
                    "型号": "RESONANT-1210-473-630V",
                    "器件类型": "MLCC",
                    "系列": "RZ",
                    "系列说明": "谐振 / Resonant MLCC",
                    "特殊用途": "谐振",
                    "尺寸（inch）": "1210",
                    "材质（介质）": "COG(NPO)",
                    "容值": "47",
                    "容值单位": "NF",
                    "耐压（V）": "630",
                    "_mlcc_series_class": "谐振",
                },
                {
                    "品牌": "GeneralBrand",
                    "型号": "GENERAL-X7R-1210-473-630V",
                    "器件类型": "MLCC",
                    "系列": "C",
                    "系列说明": "常规 / General-purpose MLCC",
                    "特殊用途": "",
                    "尺寸（inch）": "1210",
                    "材质（介质）": "X7R",
                    "容值": "47",
                    "容值单位": "NF",
                    "耐压（V）": "630",
                    "_mlcc_series_class": "常规",
                },
            ]
        )
        with sqlite3.connect(app["DB_PATH"]) as conn:
            source_columns = [row[1] for row in conn.execute('PRAGMA table_info("components")')]
        for column in source_columns:
            if column not in rows.columns:
                rows[column] = ""
        prepared = app["prepare_search_dataframe"](rows)
        original_fetch = app["fetch_search_candidate_pairs"]
        app["fetch_search_candidate_pairs"] = lambda _spec: None
        try:
            matched = app["match_by_partial_spec"](prepared, spec)
        finally:
            app["fetch_search_candidate_pairs"] = original_fetch
        self.assertEqual(matched["型号"].tolist(), ["RESONANT-1210-473-630V"])


    def test_12_runtime_databases_survive_instance_reset(self):
        app = self.app
        snapshots = {
            key: {"version": 0, "sha256": "", "payload_base64": "", "updated_at": ""}
            for key in ("cost-price", "no-match")
        }
        api_secret = "runtime-regression-secret"

        class RuntimeSnapshotHandler(BaseHTTPRequestHandler):
            def log_message(self, *_args):
                return

            def _store(self):
                return parse_qs(urlsplit(self.path).query).get("store", [""])[0]

            def _send(self, status, payload):
                encoded = json.dumps(payload).encode("utf-8")
                self.send_response(status)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(encoded)))
                self.end_headers()
                self.wfile.write(encoded)

            def do_GET(self):
                if self.headers.get("Authorization", "") != f"Bearer {api_secret}":
                    self._send(401, {"error": "unauthorized"})
                    return
                store = self._store()
                self._send(200, {"store": store, **snapshots[store]})

            def do_PUT(self):
                if self.headers.get("Authorization", "") != f"Bearer {api_secret}":
                    self._send(401, {"error": "unauthorized"})
                    return
                store = self._store()
                length = int(self.headers.get("Content-Length", "0"))
                body = json.loads(self.rfile.read(length).decode("utf-8"))
                snapshot = snapshots[store]
                if int(body.get("expected_version") or 0) != int(snapshot["version"]):
                    self._send(409, {"error": "version_conflict", "version": snapshot["version"]})
                    return
                snapshot.update(
                    {
                        "version": snapshot["version"] + 1,
                        "sha256": body["sha256"],
                        "payload_base64": body["payload_base64"],
                        "updated_at": "2026-07-03T00:00:00Z",
                    }
                )
                self._send(200, {"ok": True, "store": store, "version": snapshot["version"], "sha256": snapshot["sha256"]})

        server = ThreadingHTTPServer(("127.0.0.1", 0), RuntimeSnapshotHandler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        saved_env = {
            key: os.environ.get(key)
            for key in ("RUNTIME_STORE_REMOTE_API_URL", "RUNTIME_STORE_REMOTE_API_SECRET", "RUNTIME_STORE_REMOTE_FORCE")
        }
        original_state_dir = app["RUNTIME_STORE_REMOTE_STATE_DIR"]
        original_cost_path = app["COST_PRICE_DB_PATH"]
        original_report_path = app["NO_MATCH_REPORT_DB_PATH"]
        try:
            app["RUNTIME_STORE_REMOTE_STATE_DIR"] = os.path.join(self.temp_dir, "runtime-state")
            app["COST_PRICE_DB_PATH"] = os.path.join(self.temp_dir, "runtime-cost.sqlite")
            app["NO_MATCH_REPORT_DB_PATH"] = os.path.join(self.temp_dir, "runtime-reports.sqlite")
            app["reset_runtime_store_remote_refresh_cache"]()

            ok, message, _ = app["import_cost_price_list_from_upload"](
                UploadedBytes("runtime-cost.xlsx", fojan_quote_xlsx_bytes()),
                "regression",
            )
            self.assertTrue(ok, message)
            self.assertEqual(snapshots["cost-price"]["version"], 0)
            os.environ["RUNTIME_STORE_REMOTE_API_URL"] = f"http://127.0.0.1:{server.server_port}/api/runtime-store/snapshot"
            os.environ["RUNTIME_STORE_REMOTE_API_SECRET"] = api_secret
            os.environ["RUNTIME_STORE_REMOTE_FORCE"] = "1"
            app["reset_runtime_store_remote_refresh_cache"]("cost-price")
            self.assertIsNotNone(app["get_active_cost_price_list"]())
            self.assertGreater(snapshots["cost-price"]["version"], 0)
            app["COST_PRICE_DB_PATH"] = os.path.join(self.temp_dir, "runtime-cost-restored.sqlite")
            app["reset_runtime_store_remote_refresh_cache"]("cost-price")
            restored_cost = app["get_active_cost_price_list"]()
            self.assertIsNotNone(restored_cost)
            self.assertEqual(restored_cost["row_count"], 5)

            ok, message, report_id = app["submit_no_match_report"]("REMOTE-UNMATCHED-PART", reason="regression")
            self.assertTrue(ok, message)
            self.assertGreater(snapshots["no-match"]["version"], 0)
            app["NO_MATCH_REPORT_DB_PATH"] = os.path.join(self.temp_dir, "runtime-reports-restored.sqlite")
            app["reset_runtime_store_remote_refresh_cache"]("no-match")
            restored_reports = app["list_no_match_reports"]("all")
            self.assertEqual([row["id"] for row in restored_reports], [report_id])
            self.assertEqual(restored_reports[0]["query_text"], "REMOTE-UNMATCHED-PART")
        finally:
            app["RUNTIME_STORE_REMOTE_STATE_DIR"] = original_state_dir
            app["COST_PRICE_DB_PATH"] = original_cost_path
            app["NO_MATCH_REPORT_DB_PATH"] = original_report_path
            app["reset_runtime_store_remote_refresh_cache"]()
            for key, value in saved_env.items():
                if value is None:
                    os.environ.pop(key, None)
                else:
                    os.environ[key] = value
            server.shutdown()
            server.server_close()

    def test_13_manufacturer_packaging_moq_is_source_backed(self):
        lookup = self.app["lookup_manufacturer_packaging"]
        cases = [
            ({"品牌": "国巨YAGEO", "型号": "RC0603FR-0710KL", "系列": "RC", "尺寸（inch）": "0603"}, "5000PCS"),
            ({"品牌": "国巨YAGEO", "型号": "RC2010FK-0710KL", "系列": "RC", "尺寸（inch）": "2010"}, "4000PCS"),
            ({"品牌": "国巨YAGEO", "型号": "RT0402BRD0733RL", "系列": "RT", "尺寸（inch）": "0402"}, "10000PCS"),
            ({"品牌": "国巨YAGEO", "型号": "RT0805BRA0710KL", "系列": "RT", "尺寸（inch）": "0805"}, "5000PCS"),
            ({"品牌": "国巨YAGEO", "型号": "RT2512BKB07100KL", "系列": "RT", "尺寸（inch）": "2512"}, "4000PCS"),
            ({"品牌": "国巨YAGEO", "型号": "AA0603FR-071KL", "系列": "AA", "尺寸（inch）": "0603"}, "5000PCS"),
            ({"品牌": "国巨YAGEO", "型号": "AT0603BRC0710KL", "系列": "AT", "尺寸（inch）": "0603"}, "5000PCS"),
            ({"品牌": "国巨YAGEO", "型号": "RE1206BRE07100KL", "系列": "RE", "尺寸（inch）": "1206"}, "5000PCS"),
            ({"品牌": "国巨YAGEO", "型号": "PT2512DK-070R4L", "系列": "PT", "尺寸（inch）": "2512"}, "4000PCS"),
            ({"品牌": "国巨YAGEO", "型号": "AR0805FR-07100KL", "系列": "AR", "尺寸（inch）": "0805"}, "5000PCS"),
            ({"品牌": "国巨YAGEO", "型号": "RL1206FR-070R011L", "系列": "RL", "尺寸（inch）": "1206"}, "5000PCS"),
            ({"品牌": "国巨YAGEO", "型号": "RP0603BRD07100KL", "系列": "RP", "尺寸（inch）": "0603"}, "5000PCS"),
            ({"品牌": "国巨YAGEO", "型号": "AC0603BRE0722KL", "系列": "AC", "尺寸（inch）": "0603"}, "5000PCS"),
            ({"品牌": "国巨YAGEO", "型号": "AC1020FK-07100KL", "系列": "AC", "尺寸（inch）": "1020"}, "4000PCS"),
            ({"品牌": "KOA", "型号": "RN73H1ETTP1000B25", "系列": "RN73H", "尺寸（inch）": "0402"}, "10000PCS"),
            ({"品牌": "KOA", "型号": "RS73F2BRTTD1000B", "系列": "RS73", "尺寸（inch）": "1206"}, "5000PCS"),
            ({"品牌": "KOA", "型号": "WK73R2HTTE1000F", "系列": "WK73R", "尺寸（inch）": "1020"}, "4000PCS"),
            ({"品牌": "威世Vishay", "型号": "CRCW0402100KJNED", "系列": "CRCW", "尺寸（inch）": "0402"}, "10000PCS"),
            ({"品牌": "威世Vishay", "型号": "CRCW06030000Z0EAHP", "系列": "CRCW", "尺寸（inch）": "0603"}, "5000PCS"),
            ({"品牌": "威世Vishay", "型号": "CRCW25120000Z0EG", "系列": "CRCW", "尺寸（inch）": "2512"}, "2000PCS"),
            ({"品牌": "威世Vishay", "型号": "CRCW0201100KFNEI", "系列": "CRCW", "尺寸（inch）": "0201"}, "20000PCS"),
            ({"品牌": "威世Vishay", "型号": "CRCW08050000ZSTA", "系列": "CRCW", "尺寸（inch）": "0805"}, "5000PCS"),
            ({"品牌": "威世Vishay", "型号": "CRCW25120000ZSTH", "系列": "CRCW", "尺寸（inch）": "2512"}, "4000PCS"),
            ({"品牌": "威世Vishay", "型号": "TNPW0402100KBEED", "系列": "TNPW", "尺寸（inch）": "0402"}, "10000PCS"),
            ({"品牌": "威世Vishay", "型号": "TNPW0603100KBETA", "系列": "TNPW", "尺寸（inch）": "0603"}, "5000PCS"),
            ({"品牌": "威世Vishay", "型号": "TNPW1206100KBECN", "系列": "TNPW", "尺寸（inch）": "1206"}, "1000PCS"),
            ({"品牌": "Panasonic", "型号": "ERJ6GEYJ103V", "系列": "ERJ", "尺寸（inch）": "0805"}, "5000PCS"),
            ({"品牌": "Panasonic", "型号": "ERA2AEB102X", "系列": "ERA-2A", "尺寸（inch）": "0402"}, "10000PCS"),
            ({"品牌": "威世Vishay", "型号": "NTCS0402E3103JL1T", "系列": "NTCS0402E", "尺寸（inch）": "0402"}, "10000PCS"),
            ({"品牌": "威世Vishay", "型号": "NTCS0603E3103FMT", "系列": "NTCS0603E", "尺寸（inch）": "0603"}, "4000PCS"),
            ({"品牌": "威世Vishay", "型号": "NTCS0805E3103FLT", "系列": "NTCS0805E", "尺寸（inch）": "0805"}, "4000PCS"),
            ({"品牌": "东电化TDK", "型号": "C1608C0G2E182J080AA", "系列": "C", "尺寸（inch）": "0603"}, "4000PCS"),
            ({"品牌": "国巨YAGEO", "型号": "CC0402KRX7R9BB103", "系列": "CC", "尺寸（inch）": "0402"}, "10000PCS"),
            ({"品牌": "国巨YAGEO", "型号": "CC0201KRX5R7BB104", "系列": "CC", "尺寸（inch）": "0201"}, "15000PCS"),
            ({"品牌": "国巨YAGEO", "型号": "CC0402KPX7R9BB103", "系列": "CC", "尺寸（inch）": "0402"}, "50000PCS"),
            ({"品牌": "国巨YAGEO", "型号": "CC0603JRX7R9BB104", "系列": "CC", "尺寸（inch）": "0603"}, "4000PCS"),
            ({"品牌": "国巨YAGEO", "型号": "CC0603KPX7R7BB104", "系列": "CC", "尺寸（inch）": "0603"}, "15000PCS"),
            ({"品牌": "东电化TDK", "型号": "C0603X7S0J224K030BC", "系列": "C", "尺寸（inch）": "0201"}, "15000PCS"),
            ({"品牌": "东电化TDK", "型号": "C1005X7R1V224K050BC", "系列": "C", "尺寸（inch）": "0402"}, "10000PCS"),
            ({"品牌": "东电化TDK", "型号": "C2012C0G2W221J060AE", "系列": "C", "尺寸（inch）": "0805"}, "4000PCS"),
            ({"品牌": "东电化TDK", "型号": "C2012X5R1V226M125AC", "系列": "C", "尺寸（inch）": "0805"}, "2000PCS"),
            ({"品牌": "东电化TDK", "型号": "NTCG063JF103FTDS", "系列": "NTCG", "尺寸（inch）": "0201"}, "15000PCS"),
            ({"品牌": "东电化TDK", "型号": "NTCG103JF103FTDS", "系列": "NTCG", "尺寸（inch）": "0402"}, "10000PCS"),
            ({"品牌": "东电化TDK", "型号": "NTCG163JF103FTDS", "系列": "NTCG", "尺寸（inch）": "0603"}, "4000PCS"),
            ({"品牌": "村田Murata", "型号": "GRM155R71E472KA01D", "系列": "GRM", "尺寸（inch）": "0402"}, "10000PCS"),
            ({"品牌": "村田Murata", "型号": "GRM155R71E472KA01J", "系列": "GRM", "尺寸（inch）": "0402"}, "50000PCS"),
            ({"品牌": "村田Murata", "型号": "GRM188R11H104KA93D", "系列": "GRM", "尺寸（inch）": "0603"}, "4000PCS"),
            ({"品牌": "村田Murata", "型号": "GCM188R71H273KA55V", "系列": "GCM", "尺寸（inch）": "0603"}, "30000PCS"),
            ({"品牌": "村田Murata", "型号": "GCJ21BR71H104KA01L", "系列": "GCJ", "尺寸（inch）": "0805"}, "3000PCS"),
            ({"品牌": "村田Murata", "型号": "GCJ21BR71H104KA01K", "系列": "GCJ", "尺寸（inch）": "0805"}, "10000PCS"),
            ({"品牌": "三星Samsung", "型号": "CL02A102KP2NNNC", "系列": "CL", "尺寸（inch）": "01005", "高度（mm）": "0.20±0.02"}, "20000PCS"),
            ({"品牌": "三星Samsung", "型号": "CL03A102KA31INC", "系列": "CL", "尺寸（inch）": "0201", "高度（mm）": "0.30±0.03"}, "10000PCS"),
            ({"品牌": "三星Samsung", "型号": "CL05A104JO5NNNC", "系列": "CL", "尺寸（inch）": "0402", "高度（mm）": "0.50±0.05"}, "10000PCS"),
            ({"品牌": "三星Samsung", "型号": "CL10A104KA8NNNC", "系列": "CL", "尺寸（inch）": "0603", "高度（mm）": "0.80±0.10"}, "4000PCS"),
            ({"品牌": "三星Samsung", "型号": "CL21A105KACLNNC", "系列": "CL", "尺寸（inch）": "0805", "高度（mm）": "0.85±0.10"}, "4000PCS"),
            ({"品牌": "三星Samsung", "型号": "CL21A106KOQNNWC", "系列": "CL", "尺寸（inch）": "0805", "高度（mm）": "1.25±0.15"}, "2000PCS"),
            ({"品牌": "三星Samsung", "型号": "RC1005F100CS", "系列": "RC", "尺寸（inch）": "01005"}, "10000PCS"),
            ({"品牌": "三星Samsung", "型号": "RCS1608F100CS", "系列": "RCS", "尺寸（inch）": "0603"}, "5000PCS"),
            ({"品牌": "华新科Walsin", "型号": "WR04W1005FTL", "系列": "WR", "尺寸（inch）": "0402"}, "10000PCS"),
            ({"品牌": "华新科Walsin", "型号": "WR02W1005FAL", "系列": "WR", "尺寸（inch）": "01005"}, "15000PCS"),
            ({"品牌": "华新科Walsin", "型号": "WR18X40R2FTL", "系列": "WR", "尺寸（inch）": "1218"}, "3000PCS"),
            ({"品牌": "华新科Walsin", "型号": "0402B101J100CT", "系列": "常规", "尺寸（inch）": "0402", "高度（mm）": "0.50"}, "10000PCS"),
            ({"品牌": "华新科Walsin", "型号": "0805A106K250CT", "系列": "常规", "尺寸（inch）": "0805", "高度（mm）": "1.25"}, "3000PCS"),
            ({"品牌": "华新科Walsin", "型号": "1210B102J101CT", "系列": "常规", "尺寸（inch）": "1210", "高度（mm）": "2.50"}, "1000PCS"),
            ({"品牌": "华新科Walsin", "型号": "0402N0R1A500CT", "系列": "0402N", "尺寸（inch）": "0402", "高度（mm）": "0.50"}, "10000PCS"),
            ({"品牌": "三星Samsung", "型号": "RU1005FR020CS", "系列": "RU", "尺寸（inch）": "0402"}, "10000PCS"),
            ({"品牌": "三星Samsung", "型号": "RUK1608FR010CS", "系列": "RU", "尺寸（inch）": "0603"}, "5000PCS"),
            ({"品牌": "三星Samsung", "型号": "RUT2012FR100CS", "系列": "RU", "尺寸（inch）": "0805"}, "5000PCS"),
            ({"品牌": "三星Samsung", "型号": "RJ1220FR005CS", "系列": "RJ", "尺寸（inch）": "0508"}, "5000PCS"),
            ({"品牌": "三星Samsung", "型号": "RJ1220FR002CS", "系列": "RJ", "尺寸（inch）": "0508"}, "4000PCS"),
            ({"品牌": "华新科Walsin", "型号": "SH31B101K102CT", "系列": "SH", "尺寸（inch）": "1206", "高度（mm）": "1.60"}, "2000PCS"),
            ({"品牌": "华新科Walsin", "型号": "RF03N0R1A250CT", "系列": "RF", "尺寸（inch）": "0201", "高度（mm）": "0.30"}, "15000PCS"),
            ({"品牌": "华新科Walsin", "型号": "HH21N0R5B101CT", "系列": "HH", "尺寸（inch）": "0805", "高度（mm）": "1.25"}, "3000PCS"),
            ({"品牌": "华新科Walsin", "型号": "MT15N0R5B500CT", "系列": "MT", "尺寸（inch）": "0402", "高度（mm）": "0.50"}, "10000PCS"),
            ({"品牌": "FOJAN(富捷)", "型号": "FRM121WFR010TM", "系列": "FRM", "尺寸（inch）": "1206"}, "5000PCS"),
            ({"品牌": "FOJAN(富捷)", "型号": "FPM253WFR060TM", "系列": "FPM", "尺寸（inch）": "2512"}, "4000PCS"),
        ]
        for row, expected in cases:
            result = lookup(row)
            self.assertEqual(result.get("MOQ"), expected, row["型号"])
            self.assertIn("原厂标准包装数量", result.get("MOQ来源", ""), row["型号"])
            self.assertTrue(result.get("包装数量来源", "").startswith("https://"), row["型号"])

        self.assertEqual(
            lookup({"品牌": "国巨YAGEO", "型号": "RC0603FK-0710KL", "系列": "RC", "尺寸（inch）": "0603"}),
            {},
        )
        self.assertEqual(
            lookup({"品牌": "国巨YAGEO", "型号": "RT2010BRD07100RL", "系列": "RT", "尺寸（inch）": "2010"}),
            {},
        )
        self.assertEqual(
            lookup({"品牌": "KOA", "型号": "SLR1TTE1000D", "系列": "SLR", "尺寸（inch）": "2512"}),
            {},
        )
        self.assertEqual(
            lookup({"品牌": "威世Vishay", "型号": "CRCW08050000Z0EB", "系列": "CRCW", "尺寸（inch）": "0805"}),
            {},
        )
        self.assertEqual(
            lookup({"品牌": "威世Vishay", "型号": "TNPW1206100KBEEN", "系列": "TNPW", "尺寸（inch）": "1206"}),
            {},
        )
        self.assertEqual(
            lookup({"品牌": "村田Murata", "型号": "LQW18AN20NG00#", "系列": "LQW18AN", "尺寸（inch）": "0603"}),
            {},
        )
        self.assertEqual(
            lookup({"品牌": "国巨YAGEO", "型号": "CC0805MRX7R9BB104", "系列": "CC", "尺寸（inch）": "0805"}),
            {},
        )
        self.assertEqual(
            lookup({"品牌": "三星Samsung", "型号": "CL10A105KA8NNND", "系列": "CL", "尺寸（inch）": "0603", "高度（mm）": "0.80±0.10"}),
            {},
        )
        self.assertEqual(
            lookup({"品牌": "三星Samsung", "型号": "RC1608F100AS", "系列": "RC", "尺寸（inch）": "0603"}),
            {},
        )
        self.assertEqual(
            lookup({"品牌": "华新科Walsin", "型号": "WR04W1005FBL", "系列": "WR", "尺寸（inch）": "0402"}),
            {},
        )
        self.assertEqual(
            lookup({"品牌": "华新科Walsin", "型号": "1812B102J101CT", "系列": "常规", "尺寸（inch）": "1812", "高度（mm）": "3.20"}),
            {},
        )
        self.assertEqual(
            lookup({"品牌": "华新科Walsin", "型号": "SH43B103K102CT", "系列": "SH", "尺寸（inch）": "1812", "高度（mm）": "3.20"}),
            {},
        )
        self.assertEqual(
            lookup({"品牌": "华新科Walsin", "型号": "MT15B101K500CT", "系列": "MT", "尺寸（inch）": "0402", "高度（mm）": "0.85"}),
            {},
        )
        original_cost_path = self.app["COST_PRICE_DB_PATH"]
        try:
            isolated_cost_path = os.path.join(self.temp_dir, "manufacturer-packaging-cost.sqlite")
            self.app["COST_PRICE_DB_PATH"] = isolated_cost_path
            self.app["clear_cost_price_lookup_cache"]()
            enriched = self.app["enrich_component_cost_columns"](
                pd.DataFrame([cases[0][0]])
            )
            self.assertEqual(enriched.iloc[0]["MOQ"], "5000PCS")
            self.assertIn("YAGEO", enriched.iloc[0]["MOQ来源"])

            cost_upload = UploadedBytes(
                "purchase-moq.xlsx",
                dataframe_to_xlsx_bytes(
                    pd.DataFrame(
                        [{"品牌": "国巨YAGEO", "型号": "RC0603FR-0710KL", "MOQ": "123PCS"}]
                    )
                ),
            )
            ok, message, _ = self.app["import_cost_price_list_from_upload"](cost_upload, "regression")
            self.assertTrue(ok, message)
            overridden = self.app["enrich_component_cost_columns"](pd.DataFrame([cases[0][0]]))
            self.assertEqual(overridden.iloc[0]["MOQ"], "123PCS")
            self.assertEqual(overridden.iloc[0]["MOQ来源"], "当前启用成本清单")
        finally:
            self.app["COST_PRICE_DB_PATH"] = original_cost_path
            self.app["clear_cost_price_lookup_cache"]()

    def test_14_fojan_alloy_resistor_rules_are_source_scoped(self):
        app = self.app

        parsed_frm = app["parse_resistor_model_rule"](
            "FRM121WFR010TM",
            brand="FOJAN(富捷)",
            component_type="合金电阻",
        )
        self.assertEqual(parsed_frm["器件类型"], "合金电阻")
        self.assertEqual(parsed_frm["系列"], "FRM")
        self.assertEqual(parsed_frm["尺寸（inch）"], "1206")
        self.assertEqual(parsed_frm["容值"], "10")
        self.assertEqual(parsed_frm["容值单位"], "mΩ")
        self.assertEqual(parsed_frm["容值误差"], "1")
        self.assertEqual(parsed_frm["功率"], "1W")

        parsed_fpm = app["parse_resistor_model_rule"](
            "FPM253WFR060TM",
            brand="FOJAN(富捷)",
            component_type="合金电阻",
        )
        self.assertEqual(parsed_fpm["器件类型"], "合金电阻")
        self.assertEqual(parsed_fpm["系列"], "FPM")
        self.assertEqual(parsed_fpm["尺寸（inch）"], "2512")
        self.assertEqual(parsed_fpm["容值"], "60")
        self.assertEqual(parsed_fpm["容值单位"], "mΩ")
        self.assertEqual(parsed_fpm["容值误差"], "1")
        self.assertEqual(parsed_fpm["功率"], "3W")

        mode, spec = app["detect_query_mode_and_spec"](
            pd.DataFrame(),
            "合金电阻 电阻10毫欧 ±1% 1206",
        )
        self.assertEqual(mode, "合金电阻")
        rows = app["load_search_dataframe_for_query"](mode, spec)
        fojan_models = set(
            rows[rows["品牌"].astype(str).str.contains("FOJAN|富捷", case=False, regex=True)]["型号"].map(app["clean_model"])
        )
        self.assertIn("FRM121WFR010TM", fojan_models)
        self.assertNotIn("FRL1206FR010TS", fojan_models)
        display = app["select_component_display_columns"](
            rows[rows["型号"].map(app["clean_model"]).eq("FRM121WFR010TM")],
            spec,
            prefix_columns=["品牌", "型号", "系列"],
        )
        self.assertEqual(display.iloc[0]["MOQ"], "5000PCS")
        self.assertIn("FOJAN", display.iloc[0]["MOQ来源"])

        mode, spec = app["detect_query_mode_and_spec"](
            pd.DataFrame(),
            "富捷 贴片合金电阻 0.06R 2512 3W ±1%",
        )
        self.assertEqual(mode, "合金电阻")
        self.assertEqual(spec["品牌"], "FOJAN(富捷)")
        rows = app["load_search_dataframe_for_query"](mode, spec)
        self.assertEqual(set(rows["品牌"]), {"FOJAN(富捷)"})
        self.assertEqual(set(rows["型号"].map(app["clean_model"])), {"FPM253WFR060TM"})
        display = app["select_component_display_columns"](
            rows,
            spec,
            prefix_columns=["品牌", "型号", "系列"],
        )
        self.assertEqual(display.iloc[0]["MOQ"], "4000PCS")
        self.assertIn("FOJAN FPM", display.iloc[0]["MOQ来源"])

        for query in (
            "贴片合金电阻 0.3Ω ±1% 1206 1W",
            "贴片合金电阻 2512 0.2R ±1%",
        ):
            mode, spec = app["detect_query_mode_and_spec"](pd.DataFrame(), query)
            rows = app["load_search_dataframe_for_query"](mode, spec)
            if rows is None or rows.empty:
                continue
            fojan_rows = rows[rows["品牌"].astype(str).str.contains("FOJAN|富捷", case=False, regex=True)]
            self.assertTrue(fojan_rows.empty, query)


if __name__ == "__main__":
    unittest.main(verbosity=2)
