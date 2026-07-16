from __future__ import annotations

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
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
            "frequencyAging": "3",
            "turnoverTemp": "+25&deg;C +/-5&deg;C",
            "parabolicCoef": "-0.04",
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
        self.assertEqual(row["25℃老化（ppm）"], "±3ppm")
        self.assertEqual(row["拐点温度"], "+25℃ ±5℃")
        self.assertEqual(row["抛物线系数（ppm/℃²）"], "-0.04ppm/℃²")
        self.assertEqual(row["型号粒度"], "官方逐料号")

    def test_build_mhz_crystal_row_maps_temperature_aging_and_overtone(self):
        product = {
            "pn": "Q22FA12800007",
            "model": "FA-128",
            "dimensionL": "2.0",
            "dimensionW": "1.6",
            "dimensionH": "0.5",
            "frequencyMin": "38.400000",
            "loadCap": "10",
            "frequencyTol25C": "+/-15",
            "frequencyTolTempRange": "+/-15",
            "25CAging": "+/-1ppm",
            "overtoneOrder": "Fundamental",
            "tempRange": "-20 to +85",
        }
        row = epson_sync.build_product_row(
            product,
            "xtal_mhz.json",
            epson_sync.SOURCE_SPECS["xtal_mhz.json"],
            "2026-07-17 00:00:00",
        )

        self.assertEqual(row["频率温度特性（ppm）"], "±15ppm")
        self.assertEqual(row["25℃老化（ppm）"], "±1ppm")
        self.assertEqual(row["泛音阶次"], "基频（Fundamental）")
        self.assertEqual(row["工作温度"], "-20~+85°C")

    def test_runtime_cache_preparation_keeps_multibrand_timing_rows(self):
        epson_frame = pd.DataFrame(
            [
                {
                    "品牌": "爱普生Epson",
                    "型号": "Q22FA12800007",
                    "系列": "FA-128",
                    "器件类型": "晶振",
                    "尺寸（inch）": "2016",
                    "容值": "38.4",
                    "容值单位": "MHz",
                }
            ]
        )
        companion_frame = pd.DataFrame(
            [
                {
                    "品牌": "Abracon",
                    "型号": "ABM11N-40.0000MHZ-8-D2X-T3",
                    "系列": "ABM11N",
                    "器件类型": "晶振",
                    "尺寸（inch）": "2016",
                    "容值": "40",
                    "容值单位": "MHz",
                }
            ]
        )
        with TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            epson_path = temp_root / "epson.csv"
            companion_path = temp_root / "multibrand.csv"
            companion_frame.to_csv(companion_path, index=False, encoding="utf-8-sig")
            with mock.patch.object(
                epson_sync,
                "MULTIBRAND_TIMING_SOURCE",
                companion_path,
            ):
                normalized, prepared, companion_rows = (
                    epson_sync.prepare_runtime_cache_frame(
                        epson_frame,
                        epson_path,
                    )
                )

        self.assertEqual(len(normalized), 1)
        self.assertEqual(companion_rows, 1)
        self.assertEqual(
            set(prepared["型号"].tolist()),
            {
                "Q22FA12800007",
                "ABM11N-40.0000MHZ-8-D2X-T3",
            },
        )

    def test_timing_query_parses_metric_package_and_ppm(self):
        spec = cm.parse_timing_spec_query("晶振 16MHz 3.2x2.5mm 10pF ±10ppm")

        self.assertIsNotNone(spec)
        self.assertEqual(spec["器件类型"], "晶振")
        self.assertEqual(spec["尺寸（inch）"], "3225")
        self.assertEqual(spec["容值"], "16")
        self.assertEqual(spec["容值单位"], "MHZ")
        self.assertEqual(spec["容值误差"], "10")
        self.assertEqual(spec["负载电容（pF）"], "10")

    def test_timing_query_parses_detailed_crystal_requirements(self):
        spec = cm.parse_timing_spec_query(
            "晶振 38.4MHz 2016 10pF ±15ppm "
            "-20~85℃ 温度特性±15ppm 老化±1ppm 基频"
        )

        self.assertEqual(spec["容值误差"], "15")
        self.assertEqual(spec["工作温度"], "-20~85℃")
        self.assertEqual(spec["频率温度特性（ppm）"], "±15ppm")
        self.assertEqual(spec["25℃老化（ppm）"], "±1ppm")
        self.assertEqual(spec["泛音阶次"], "FUNDAMENTAL")

    def test_timing_query_parses_32khz_turnover_and_parabolic_coefficient(self):
        spec = cm.parse_timing_spec_query(
            "晶振 32.768kHz 3215 7pF ±20ppm -40~85℃ "
            "老化±3ppm 拐点温度+25±5℃ 抛物线系数-0.04"
        )

        self.assertEqual(spec["拐点温度"], "+25℃ ±5℃")
        self.assertEqual(spec["抛物线系数（ppm/℃²）"], "-0.04ppm/℃²")

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
                    "工作温度": "-40~85℃",
                    "25℃老化（ppm）": "±3ppm",
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
                    "工作温度": "-40~85℃",
                    "25℃老化（ppm）": "±3ppm",
                },
            ]
        )
        normalized = cm.normalize_imported_component_dataframe(rows)
        prepared = cm.prepare_search_dataframe(normalized)
        spec = cm.parse_timing_spec_query(
            "振荡器 25MHz 3225 3.3V CMOS ±25ppm -40~85℃ 老化±3ppm"
        )

        with mock.patch.object(cm, "fetch_search_candidate_pairs", return_value=None):
            matched = cm.match_other_passive_spec(prepared, spec)

        self.assertEqual(
            matched["型号"].tolist(),
            ["X1G0051810011", "ASV-25.000MHZ"],
        )
        self.assertTrue(matched["推荐等级"].eq("完全匹配").all())

    def test_sparse_timing_query_is_not_labeled_complete(self):
        rows = pd.DataFrame(
            [
                {
                    "品牌": "爱普生Epson",
                    "型号": "Q22FA12800007",
                    "系列": "FA-128",
                    "器件类型": "晶振",
                    "尺寸（inch）": "2016",
                    "容值": "38.4",
                    "容值单位": "MHz",
                    "容值误差": "15",
                    "负载电容（pF）": "10",
                    "工作温度": "-20~85℃",
                    "频率温度特性（ppm）": "±15ppm",
                    "25℃老化（ppm）": "±1ppm",
                    "泛音阶次": "基频（Fundamental）",
                }
            ]
        )
        prepared = cm.prepare_search_dataframe(
            cm.normalize_imported_component_dataframe(rows)
        )
        spec = cm.parse_timing_spec_query("晶振 38.4MHz 2016 10pF ±15ppm")

        with mock.patch.object(cm, "fetch_search_candidate_pairs", return_value=None):
            matched = cm.match_other_passive_spec(prepared, spec)

        self.assertEqual(matched["推荐等级"].tolist(), ["部分参数匹配"])

    def test_detailed_crystal_match_rejects_known_parameter_conflicts(self):
        rows = pd.DataFrame(
            [
                {
                    "品牌": "爱普生Epson",
                    "型号": "Q22FA12800007",
                    "系列": "FA-128",
                    "器件类型": "晶振",
                    "尺寸（inch）": "2016",
                    "容值": "38.4",
                    "容值单位": "MHz",
                    "容值误差": "15",
                    "负载电容（pF）": "10",
                    "工作温度": "-20~85℃",
                    "频率温度特性（ppm）": "±15ppm",
                    "25℃老化（ppm）": "±1ppm",
                    "泛音阶次": "基频（Fundamental）",
                },
                {
                    "品牌": "Example",
                    "型号": "CONFLICT-38M4",
                    "系列": "CONFLICT",
                    "器件类型": "晶振",
                    "尺寸（inch）": "2016",
                    "容值": "38.4",
                    "容值单位": "MHz",
                    "容值误差": "15",
                    "负载电容（pF）": "10",
                    "工作温度": "-20~70℃",
                    "频率温度特性（ppm）": "±30ppm",
                    "25℃老化（ppm）": "±5ppm",
                    "泛音阶次": "三次泛音（3rd Overtone）",
                },
            ]
        )
        prepared = cm.prepare_search_dataframe(
            cm.normalize_imported_component_dataframe(rows)
        )
        spec = cm.parse_timing_spec_query(
            "晶振 38.4MHz 2016 10pF ±15ppm "
            "-20~85℃ 温度特性±15ppm 老化±1ppm 基频"
        )

        with mock.patch.object(cm, "fetch_search_candidate_pairs", return_value=None):
            matched = cm.match_other_passive_spec(prepared, spec)

        self.assertEqual(matched["型号"].tolist(), ["Q22FA12800007"])
        self.assertEqual(matched["推荐等级"].tolist(), ["完全匹配"])

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
