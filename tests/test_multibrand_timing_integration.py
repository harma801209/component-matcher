from __future__ import annotations

import unittest
from unittest import mock

import pandas as pd

import component_matcher as cm
import sync_official_timing_brands as timing_sync


class MultiBrandTimingIntegrationTests(unittest.TestCase):
    def test_frequency_profile_preserves_range_and_discrete_option(self):
        profile = timing_sync.frequency_profile("24 to 54/76.8", "MHz")

        self.assertEqual(profile["unit"], "MHZ")
        self.assertEqual(profile["minimum"], "24")
        self.assertEqual(profile["maximum"], "54")
        self.assertEqual(profile["options"], "|76.8|")

    def test_series_range_matches_but_requires_configuration(self):
        rows = pd.DataFrame(
            [
                {
                    "品牌": "TXC",
                    "型号": "7M",
                    "系列": "7M",
                    "器件类型": "晶振",
                    "尺寸（inch）": "3225",
                    "容值": "",
                    "容值单位": "MHz",
                    "容值误差": "20",
                    "频率单位": "MHz",
                    "频率下限": "8",
                    "频率上限": "80",
                    "频差选项": "|20|30|",
                    "负载电容选项": "|8|10|12|",
                    "型号粒度": "官方系列范围",
                }
            ]
        )
        prepared = cm.prepare_search_dataframe(
            cm.normalize_imported_component_dataframe(rows)
        )
        spec = cm.parse_timing_spec_query("晶振 16MHz 3225 10pF ±20ppm")

        with mock.patch.object(cm, "fetch_search_candidate_pairs", return_value=None):
            matched = cm.match_other_passive_spec(prepared, spec)

        self.assertEqual(matched["型号"].tolist(), ["7M"])
        self.assertEqual(matched["推荐等级"].tolist(), ["需确认配置"])

    def test_exact_part_level_row_can_be_complete_match(self):
        rows = pd.DataFrame(
            [
                {
                    "品牌": "Abracon",
                    "型号": "ABM8-16.000MHZ-10-1-U-T",
                    "系列": "ABM8",
                    "器件类型": "晶振",
                    "尺寸（inch）": "3225",
                    "容值": "16",
                    "容值单位": "MHz",
                    "容值误差": "10",
                    "负载电容（pF）": "10",
                    "工作温度": "-40~85℃",
                    "频率温度特性（ppm）": "±10ppm",
                    "25℃老化（ppm）": "±1ppm",
                    "泛音阶次": "基频（Fundamental）",
                    "型号粒度": "官方逐料号",
                }
            ]
        )
        prepared = cm.prepare_search_dataframe(
            cm.normalize_imported_component_dataframe(rows)
        )
        spec = cm.parse_timing_spec_query(
            "晶振 16MHz 3225 10pF ±10ppm "
            "-40~85℃ 温度特性±10ppm 老化±1ppm 基频"
        )

        with mock.patch.object(cm, "fetch_search_candidate_pairs", return_value=None):
            matched = cm.match_other_passive_spec(prepared, spec)

        self.assertEqual(matched["推荐等级"].tolist(), ["完全匹配"])

    def test_lightweight_sidecar_row_preserves_timing_range_fields(self):
        record = cm.build_lightweight_component_row_from_search_sidecar(
            {
                "品牌": "KDS大真空",
                "型号": "DSX1210A",
                "_model_clean": "DSX1210A",
                "_component_type": "晶振",
            },
            {
                "品牌": "KDS大真空",
                "型号": "DSX1210A",
                "_component_type": "晶振",
                "_size": "1210",
                "_unit_upper": "MHZ",
                "_value_num": None,
                "频率下限": 32.0,
                "频率上限": 80.0,
                "频差选项": "|10|",
                "型号粒度": "官方系列范围",
            },
            include_model_rule=False,
        )

        self.assertEqual(record["频率下限"], "32.0")
        self.assertEqual(record["频率上限"], "80.0")
        self.assertEqual(record["频差选项"], "|10|")
        self.assertEqual(record["型号粒度"], "官方系列范围")

    def test_timing_display_includes_configuration_and_official_fields(self):
        crystal_columns = dict(cm.get_component_display_schema("晶振"))
        oscillator_columns = dict(cm.get_component_display_schema("振荡器"))

        for column in [
            "型号粒度",
            "频率下限",
            "频率上限",
            "频率选项",
            "频差选项",
            "储存温度",
            "AEC等级",
            "官方规格编号",
            "封装数量",
        ]:
            self.assertIn(column, crystal_columns)
            self.assertIn(column, oscillator_columns)
        self.assertIn("负载电容选项", crystal_columns)
        self.assertIn("频率温度特性（ppm）", crystal_columns)
        self.assertIn("泛音阶次", crystal_columns)
        self.assertIn("电压选项", oscillator_columns)
        self.assertIn("长期稳定度", oscillator_columns)
        self.assertIn("相位噪声", oscillator_columns)

    def test_official_timing_row_wins_over_legacy_brand_alias(self):
        rows = pd.DataFrame(
            [
                {
                    "品牌": "Kyocera",
                    "型号": "CX3225SB16000D0GLLCC",
                    "器件类型": "晶振",
                    "系列": "CX3225SB",
                },
                {
                    "品牌": "京瓷Kyocera",
                    "型号": "CX3225SB16000D0GLLCC",
                    "器件类型": "晶振",
                    "系列": "CX3225SB",
                    "型号粒度": "官方逐料号",
                    "规格摘要": "16MHz / 8pF / ±20ppm",
                },
            ]
        )

        prioritized = cm.prioritize_component_rows_for_lookup(rows)
        deduplicated = cm.deduplicate_component_matches(prioritized)

        self.assertEqual(len(deduplicated), 1)
        self.assertEqual(deduplicated.iloc[0]["品牌"], "京瓷Kyocera")
        self.assertEqual(deduplicated.iloc[0]["型号粒度"], "官方逐料号")


if __name__ == "__main__":
    unittest.main()
