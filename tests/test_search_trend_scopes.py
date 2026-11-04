"""Statistics regressions with synthetic events, never production search logs."""
import ast
from contextlib import closing
from datetime import datetime, timedelta
from functools import lru_cache
from pathlib import Path
import re
import sqlite3
import tempfile
import time
import unittest

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]


@lru_cache(maxsize=2)
def source_nodes(source_stamp):
    del source_stamp
    return tuple(ast.parse((ROOT / "component_matcher.py").read_text(encoding="utf-8")).body)


def actual_functions(names, **extra):
    source_stat = (ROOT / "component_matcher.py").stat()
    nodes = [n for n in source_nodes((source_stat.st_mtime_ns, source_stat.st_size)) if isinstance(n, ast.FunctionDef) and n.name in names]
    assert len(nodes) == len(names), names - {n.name for n in nodes}
    for node in nodes:
        node.decorator_list = []
    env = dict(pd=pd, re=re, datetime=datetime, timedelta=timedelta, time=time, closing=closing,
               clean_text=lambda value: str(value or "").strip(),
               normalize_component_type=lambda value: str(value or "").strip(),
               CHIP_RESISTOR_COMPONENT_TYPES={"贴片电阻", "厚膜电阻", "薄膜电阻", "合金电阻"})
    env.update(extra)
    exec(compile(ast.Module(body=nodes, type_ignores=[]), "actual-search-trend-tests", "exec"), env)
    return env


class SearchTrendScopesTests(unittest.TestCase):
    def test_generic_chip_name_does_not_assert_thick_film_process(self):
        tree = ast.parse((ROOT / "component_matcher.py").read_text(encoding="utf-8"))
        names = {"normalize_component_keyword_compact", "alias_token_matches", "alias_boundary_patterns",
                 "matches_component_alias", "detect_resistor_subtype_hint"}
        nodes = []
        for node in tree.body:
            if isinstance(node, ast.FunctionDef) and node.name in names:
                node.decorator_list = []
                nodes.append(node)
            elif isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "COMPONENT_ALIAS_TOKENS" for t in node.targets):
                nodes.append(node)
        env = dict(re=re, clean_text=lambda value: str(value or "").strip(),
                   looks_like_varistor_context=lambda text: False,
                   detect_fojan_alloy_series_hint=lambda text: "")
        exec(compile(ast.Module(body=nodes, type_ignores=[]), "actual-resistor-alias-tests", "exec"), env)
        for text, kind in (("贴片电阻 0402 10K", "贴片电阻"), ("CHIP RESISTOR 0402 10K", "贴片电阻"),
                           ("RES 0402 10K", "贴片电阻"), ("THICK FILM CHIP RESISTOR", "厚膜电阻"),
                           ("THIN FILM CHIP RESISTOR", "薄膜电阻")):
            self.assertEqual(env["detect_resistor_subtype_hint"](text), kind)

    def test_period_bounds_are_complete_including_leap_month_and_year_boundary(self):
        env = actual_functions({"member_search_trend_period_bounds"})
        bounds = env["member_search_trend_period_bounds"]
        for period, label, expected in (
            ("daily", "2026-10-08", ("2026-10-08", "2026-10-08")),
            ("weekly", "2026-10-05 至 2026-10-11", ("2026-10-05", "2026-10-11")),
            ("monthly", "2024-02", ("2024-02-01", "2024-02-29")),
            ("monthly", "2026-12", ("2026-12-01", "2026-12-31")),
            ("total", "所有", ("", "")),
        ):
            self.assertEqual(bounds(label, period), expected)
        for label, period in (("bad", "daily"), ("2026-13", "monthly"),
                              ("2026-10-05 至 2026-10-09", "weekly")):
            with self.assertRaises(ValueError):
                bounds(label, period)

    def trends(self, rows, period):
        kinds = {"generic query": "贴片电阻", "thick query": "厚膜电阻",
                 "thin query": "薄膜电阻", "alloy query": "合金电阻"}
        names = {"member_search_trend_rows_signature", "member_search_trend_period_label",
                 "member_search_trend_type_family", "member_search_trend_type_summary",
                 "_build_member_search_trend_base_dataframe_cached", "build_member_search_trend_dataframe"}
        env = actual_functions(
            names, clean_model=lambda value: str(value).upper(), startup_trace=lambda *args: None,
            member_search_trend_database_signature=lambda: "synthetic-no-db",
            infer_member_search_trend_spec=lambda query, model_cache=None: (
                "0402/10kΩ/±1%/1/16W", kinds[query]),
        )
        return env["build_member_search_trend_dataframe"](rows, period)

    def test_cross_day_week_month_counts_and_type_summary_are_order_independent(self):
        rows = [dict(search_date=day, query_text=query, search_count=count) for day, query, count in (
            ("2026-10-08", "generic query", 1), ("2026-10-09", "thick query", 2),
            ("2026-10-20", "thin query", 4), ("2026-11-03", "alloy query", 8),
        )]
        for period, key, expected in (("daily", "2026-10-08", 1),
                                      ("weekly", "2026-10-05 至 2026-10-11", 3),
                                      ("monthly", "2026-10", 7), ("total", "所有", 15)):
            forward = self.trends(rows, period)
            backward = self.trends(list(reversed(rows)), period)
            self.assertEqual(int(forward.loc[forward["周期"].eq(key), "搜索次数"].iloc[0]), expected)
            self.assertEqual(forward["器件类型"].tolist(), backward["器件类型"].tolist())
        label = self.trends(rows, "total")["器件类型"].iloc[0]
        for word in ("贴片电阻", "厚膜", "薄膜", "合金", "工艺未明确"):
            self.assertIn(word, label)

    def test_unknown_chip_process_is_not_presented_as_confirmed_thick_film(self):
        env = actual_functions({"member_search_trend_type_summary"})
        self.assertEqual(env["member_search_trend_type_summary"](["贴片电阻"]), "贴片电阻·工艺未明确")
        self.assertEqual(env["member_search_trend_type_summary"](["厚膜电阻"]), "电阻·厚膜")
        self.assertEqual(env["member_search_trend_type_summary"](["薄膜电阻"]), "电阻·薄膜")

    def test_process_only_record_does_not_assert_chip_mounting(self):
        env = actual_functions({"member_search_trend_type_family", "member_search_trend_type_summary"})
        self.assertEqual(env["member_search_trend_type_family"]("薄膜电阻"), "电阻")
        label = env["member_search_trend_type_summary"](["薄膜电阻"])
        self.assertNotIn("贴片", label)  # Also valid for an axial MFR identity.

    def test_period_raw_summary_counts_distinct_members_across_dates(self):
        with tempfile.TemporaryDirectory(prefix="trend-period-sql-") as folder:
            path = str(Path(folder) / "events.sqlite")
            with closing(sqlite3.connect(path)) as conn:
                conn.execute("CREATE TABLE member_search_logs(search_date TEXT,query_key TEXT,query_text TEXT,query_type TEXT,member_id INTEGER,created_at TEXT)")
                conn.executemany("INSERT INTO member_search_logs VALUES (?,?,?,?,?,?)", [
                    ("2026-10-08", "Q1", "0402 10K", "规格", 1, "2026-10-08 10:00:00"),
                    ("2026-10-09", "Q1", "0402 10K", "规格", 1, "2026-10-09 10:00:00"),
                    ("2026-10-09", "Q1", "0402 10K", "规格", 2, "2026-10-09 11:00:00"),
                    ("2026-10-10", "Q2", "0402 1K", "规格", 3, "2026-10-10 11:00:00"),
                    ("2026-11-03", "Q1", "0402 10K", "规格", 3, "2026-11-03 10:00:00"),
                ])
                conn.commit()
            env = actual_functions(
                {"list_member_search_log_summary"}, sqlite3=sqlite3, MEMBER_AUTH_DB_PATH=path,
                refresh_member_auth_remote_snapshot=lambda: None, ensure_member_auth_schema=lambda: None,
                build_member_search_log_where=lambda start, end, keyword: (
                    "WHERE search_date>=? AND search_date<=?", [start, end]),
                member_row_to_dict=dict,
            )
            daily = env["list_member_search_log_summary"]("2026-10-01", "2026-10-31", limit=None)
            self.assertEqual(len(daily), 3)
            monthly = env["list_member_search_log_summary"](
                "2026-10-01", "2026-10-31", limit=None, aggregate_dates=True)
            self.assertEqual(len(monthly), 2)
            self.assertEqual(monthly[0]["query_key"], "Q1")
            self.assertEqual(monthly[0]["search_count"], 3)
            self.assertEqual(monthly[0]["member_count"], 2)

    def test_summary_table_has_selected_period_not_a_fixed_daily_label(self):
        env = actual_functions({"member_search_summary_dataframe"})
        rows = [dict(search_date="2026-10-08", query_text="0402 10K", search_count=3, member_count=2)]
        result = env["member_search_summary_dataframe"](rows, period="monthly", period_label="2026-10")
        self.assertNotIn("日期", result.columns)
        self.assertEqual(result["月份"].iloc[0], "2026-10")


if __name__ == "__main__":
    unittest.main()
