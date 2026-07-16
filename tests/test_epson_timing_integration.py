from __future__ import annotations

import unittest
from unittest import mock

import pandas as pd

import component_matcher as cm
import sync_epson_parametric_products as epson_sync


class EpsonTimingIntegrationTests(unittest.TestCase):
    def test_decimal_text_preserves_integer_trailing_zeroes(self):
        self.assertEqual(epson_sync.decimal_text("50"), "50")
        self.assertEqual(epson_sync.decimal_text("100"), "100")
        self.assertEqual(epson_sync.decimal_text("32.768000"), "32.768")

    def test_build_crystal_product_row_uses_official_product_number(self):
        product = {
            "pn": "Q13FC13500002",
            "model": "FC-135",
            "dimensionL": "3.2",
            "dimensionW": "1.5",
            "dimensionH": "0.9",
            "frequencyMin": "32.768000",
            "loadCapPf": "7",
            "frequencyTol25C": "+/-20",
            "operatingTempRange": "-40 to +85",
            "esrMax": "70",
            "driveLevel": "0.5",
            "pdf_switch": "1",
            "aecq200": "No",
        }
        row = epson_sync.build_product_row(
            product,
            "xtal_32khz.json",
            epson_sync.SOURCE_SPECS["xtal_32khz.json"],
            "2026-07-16 12:00:00",
        )

        self.assertEqual(row["品牌"], "爱普生Epson")
        self.assertEqual(row["型号"], "Q13FC13500002")
        self.assertEqual(row["系列"], "FC-135")
        self.assertEqual(row["器件类型"], "晶振")
        self.assertEqual(row["尺寸（inch）"], "3215")
        self.assertEqual(row["容值"], "32.768")
        self.assertEqual(row["容值单位"], "kHz")
        self.assertEqual(row["容值误差"], "20")
        self.assertEqual(row["负载电容（pF）"], "7")

    def test_timing_query_parses_metric_package_and_ppm(self):
        spec = cm.parse_timing_spec_query("晶振 16MHz 3.2x2.5mm 10pF ±10ppm")

        self.assertIsNotNone(spec)
        self.assertEqual(spec["器件类型"], "晶振")
        self.assertEqual(spec["尺寸（inch）"], "3225")
        self.assertEqual(spec["容值"], "16")
        self.assertEqual(spec["容值单位"], "MHZ")
        self.assertEqual(spec["容值误差"], "10")
        self.assertEqual(spec["负载电容（pF）"], "10")

    def test_timing_voltage_range_accepts_supported_nominal_voltage(self):
        self.assertTrue(cm.timing_voltage_allows("1.62~3.63", "3.3"))
        self.assertTrue(cm.timing_voltage_allows("3.135~3.465", "3.3"))
        self.assertFalse(cm.timing_voltage_allows("1.71~1.89", "3.3"))

    def test_cross_brand_timing_match_prioritizes_epson(self):
        rows = pd.DataFrame(
            [
                {
                    "品牌": "Abracon",
                    "型号": "ASV-25.000MHZ",
                    "系列": "ASV",
                    "器件类型": "振荡器",
                    "尺寸（inch）": "3225",
                    "容值": "25",
                    "容值单位": "MHz",
                    "容值误差": "25",
                    "耐压（V）": "3.3",
                    "电源电压": "3.3",
                    "输出类型": "CMOS",
                },
                {
                    "品牌": "爱普生Epson",
                    "型号": "X1G0051810011",
                    "系列": "SG-8101CG",
                    "器件类型": "振荡器",
                    "尺寸（inch）": "3225",
                    "容值": "25",
                    "容值单位": "MHz",
                    "容值误差": "25",
                    "耐压（V）": "1.62~3.63",
                    "电源电压": "1.62~3.63",
                    "输出类型": "CMOS",
                },
            ]
        )
        normalized = cm.normalize_imported_component_dataframe(rows)
        prepared = cm.prepare_search_dataframe(normalized)
        spec = cm.parse_timing_spec_query("振荡器 25MHz 3225 3.3V CMOS ±25ppm")

        with mock.patch.object(cm, "fetch_search_candidate_pairs", return_value=None):
            matched = cm.match_other_passive_spec(prepared, spec)

        self.assertEqual(
            matched["型号"].tolist(),
            ["X1G0051810011", "ASV-25.000MHZ"],
        )
        self.assertTrue(matched["推荐等级"].eq("完全匹配").all())

    def test_candidate_loader_merges_database_and_search_sidecar_rows(self):
        database_rows = pd.DataFrame(
            [
                {
                    "品牌": "爱普生Epson",
                    "型号": "FC135R",
                    "器件类型": "晶振",
                    "_component_type": "晶振",
                }
            ]
        )
        sidecar_rows = pd.DataFrame(
            [
                {
                    "品牌": "爱普生Epson",
                    "型号": "Q13FC13500002",
                    "器件类型": "晶振",
                    "_component_type": "晶振",
                }
            ]
        )
        connection = mock.MagicMock()

        with (
            mock.patch.object(cm.os.path, "exists", return_value=True),
            mock.patch.object(cm, "is_public_mode", return_value=False),
            mock.patch.object(cm, "is_streamlit_cloud_runtime", return_value=False),
            mock.patch.object(cm.sqlite3, "connect", return_value=connection),
            mock.patch.object(cm.pd, "read_sql_query", return_value=database_rows),
            mock.patch.object(
                cm,
                "load_search_sidecar_rows_by_brand_model_pairs",
                return_value=sidecar_rows,
            ),
            mock.patch.object(cm, "prepare_search_dataframe", side_effect=lambda frame: frame),
        ):
            merged = cm.load_component_rows_by_brand_model_pairs(
                [
                    ("爱普生Epson", "FC135R"),
                    ("爱普生Epson", "Q13FC13500002"),
                ],
                preferred_component_type="晶振",
            )

        self.assertEqual(
            set(merged["型号"].tolist()),
            {"FC135R", "Q13FC13500002"},
        )


if __name__ == "__main__":
    unittest.main()
