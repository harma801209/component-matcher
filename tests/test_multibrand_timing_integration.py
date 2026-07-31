from __future__ import annotations

import unittest
from unittest import mock

import pandas as pd

import component_matcher as cm
import sync_official_timing_brands as timing_sync


class MultiBrandTimingIntegrationTests(unittest.TestCase):
    def test_lcsc_exact_timing_rows_import_traceable_part_parameters(self):
        products = [
            {
                "productCode": "C431166",
                "productModel": "3S30000079",
                "catalogName": "Crystals",
                "productIntroEn": "Crystal 30MHz ±10ppm 12pF 40Ω SMD3225-4P",
                "encapStandard": "SMD3225-4P",
                "productCycle": "normal",
                "minPacketNumber": 3000,
                "url": "https://www.lcsc.com/product-detail/C431166.html",
                "pdfUrl": "https://datasheet.example/3S30000079.pdf",
                "paramVOList": [
                    {
                        "paramNameEn": "Frequency",
                        "paramValueEn": "30MHz",
                    },
                    {
                        "paramNameEn": "Normal temperature Frequency Tolerance",
                        "paramValueEn": "±10ppm",
                    },
                    {
                        "paramNameEn": "Frequency Stability",
                        "paramValueEn": "±10ppm",
                    },
                    {
                        "paramNameEn": "Operating Temperature",
                        "paramValueEn": "-20℃~+70℃",
                    },
                    {
                        "paramNameEn": "Load Capacitance",
                        "paramValueEn": "12pF",
                    },
                    {
                        "paramNameEn": "Equivalent Series Resistance(ESR)",
                        "paramValueEn": "40Ω",
                    },
                ],
            }
        ]

        def fake_query(_session, **kwargs):
            if kwargs["brand_id"] == 12049 and kwargs["catalog_id"] == 1155:
                return {"totalPage": 1, "dataList": products}
            return {"totalPage": 0, "dataList": []}

        with (
            mock.patch.object(
                timing_sync,
                "LCSC_TIMING_BRANDS",
                {12049: {"brand": "YL惠伦", "catalogs": (1155, 1157)}},
            ),
            mock.patch.object(timing_sync, "lcsc_query_page", side_effect=fake_query),
        ):
            rows = timing_sync.build_lcsc_timing_rows(
                mock.Mock(),
                "2026-07-31 10:00:00",
            )

        self.assertEqual(len(rows), 1)
        row = rows[0]
        self.assertEqual(row["品牌"], "YL惠伦")
        self.assertEqual(row["型号"], "3S30000079")
        self.assertEqual(row["型号粒度"], "专业分销商逐料号")
        self.assertEqual(row["频率"], "30")
        self.assertEqual(row["频率单位"], "MHZ")
        self.assertEqual(row["频差（ppm）"], "10")
        self.assertEqual(row["频率温度特性（ppm）"], "10")
        self.assertEqual(row["负载电容（pF）"], "12")
        self.assertEqual(row["ESR"], "40Ω")
        self.assertEqual(row["尺寸（inch）"], "3225")
        self.assertEqual(row["封装数量"], "3000")
        self.assertEqual(row["官方规格编号"], "C431166")
        self.assertIn("附原厂规格书", row["校验备注"])

    def test_official_exact_row_wins_over_distributor_duplicate(self):
        official = timing_sync.base_row(
            品牌="KDS大真空",
            型号="1P224000AA0Z",
            型号粒度="官方逐料号",
            数据来源="https://www.kds.info/",
            生产状态="量产",
        )
        distributor = timing_sync.base_row(
            品牌="KDS大真空",
            型号="1P224000AA0Z",
            型号粒度="专业分销商逐料号",
            数据来源="https://www.lcsc.com/product-detail/C51904733.html",
            生产状态="量产",
        )

        result = timing_sync.finalize_rows([distributor, official])

        self.assertEqual(len(result), 1)
        self.assertEqual(result.iloc[0]["数据来源"], "https://www.kds.info/")

    def test_lcsc_product_description_corrects_32768_frequency_unit(self):
        profile = timing_sync.explicit_frequency_profile(
            "Crystal 32.768kHz ±20ppm 7pF SMD3215-2P"
        )

        self.assertIsNotNone(profile)
        self.assertEqual(profile["exact"], "32.768")
        self.assertEqual(profile["unit"], "KHZ")

    def test_lcsc_refresh_replaces_only_old_distributor_rows(self):
        existing = pd.DataFrame(
            [
                {
                    "品牌": "TKD泰晶",
                    "型号": "SF32WK32768D71T005",
                    "型号粒度": "专业分销商逐料号",
                },
                {
                    "品牌": "TKD泰晶",
                    "型号": "SX-3225",
                    "型号粒度": "官方系列范围",
                },
                {
                    "品牌": "NDK",
                    "型号": "NX3225SA",
                    "型号粒度": "官方系列范围",
                },
            ]
        )

        result = timing_sync.remove_replaced_existing_rows(
            existing,
            {"lcsc_timing"},
        )

        self.assertNotIn("SF32WK32768D71T005", result["型号"].tolist())
        self.assertIn("SX-3225", result["型号"].tolist())
        self.assertIn("NX3225SA", result["型号"].tolist())

    def test_ndk_official_detailed_fields_are_imported(self):
        oscillator_source = {
            "Model": "NZ2520SDA",
            "Specification number": "EXS00A-CS00001",
            "Nominal frequency": "25 MHz",
            "Package size(LxW)": "2.5 x 2.0",
            "Package size(H)": "0.8",
            "Overall frequency tolerance Max.": "±50",
            "Supply voltage": "3.3V",
            "Operating temperature rang": "-40 to +85",
            "Output specification": "CMOS",
            "Current consumption Max.": "3.5",
            "Start-up time Max.": "4",
            "Enable/Disable function, STB function": "STB function",
            "Long-term frequency stability Max.": "±5",
            "Terminal（Number/ Form)": "4",
            "[Phase noise Typ.,10Hz]": "-120",
            "[Phase noise Typ.,1kHz]": "-153",
        }

        class Response:
            @staticmethod
            def raise_for_status():
                return None

            @staticmethod
            def json():
                return {"status": "ok", "data": [oscillator_source]}

        class Session:
            @staticmethod
            def post(_url, data=None, timeout=240):
                return Response()

        category = {
            "大分類": "osc",
            "小分類": "spxo",
            "大分類名": "Crystal Oscillators",
            "小分類名": "SPXO",
        }
        with mock.patch.object(timing_sync, "ndk_categories", return_value=[category]):
            rows = timing_sync.build_ndk_rows(Session(), "2026-07-30 21:00:00")

        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["频差（ppm）"], "50")
        self.assertEqual(rows[0]["消耗电流"], "3.5")
        self.assertEqual(rows[0]["启动时间"], "4")
        self.assertEqual(rows[0]["使能/待机功能"], "STB function")
        self.assertEqual(rows[0]["长期稳定度"], "±5")
        self.assertEqual(rows[0]["终端/脚位"], "4")
        self.assertIn("10Hz: -120dBc/Hz", rows[0]["相位噪声"])
        self.assertNotIn("频差", timing_sync.timing_parameter_completeness(rows[0])[1])

    def test_ndk_khz_crystal_turnover_and_parabolic_fields_are_imported(self):
        crystal_source = {
            "Model": "NX1610SA",
            "Specification number": "EXS00A-MU00001",
            "Nominal frequency": "32.768 kHz",
            "Package size(LxW)": "1.6 x 1.0",
            "Package size(H)": "0.5",
            "Frequency tolerance": "±20",
            "Load capacitance": "7",
            "Equivalent series resistance": "90000",
            "Level of drive": "0.1",
            "Operating temperature rang": "-40 to +85",
            "Turnover temperature": "+25±5",
            "Parabolic coefficient": "-0.04 Max",
            "Terminal（Number/ Form)": "2",
        }

        class Response:
            @staticmethod
            def raise_for_status():
                return None

            @staticmethod
            def json():
                return {"status": "ok", "data": [crystal_source]}

        class Session:
            @staticmethod
            def post(_url, data=None, timeout=240):
                return Response()

        category = {
            "大分類": "crystal",
            "小分類": "khz",
            "大分類名": "Crystal Units",
            "小分類名": "Tuning Fork Crystal Units (kHz range)",
        }
        with mock.patch.object(timing_sync, "ndk_categories", return_value=[category]):
            rows = timing_sync.build_ndk_rows(Session(), "2026-07-30 21:00:00")

        self.assertEqual(rows[0]["拐点温度"], "+25±5")
        self.assertEqual(rows[0]["抛物线系数（ppm/℃²）"], "-0.04 Max")
        self.assertEqual(rows[0]["终端/脚位"], "2")

    def test_kds_split_frequency_ranges_are_merged_to_full_series_range(self):
        source = pd.DataFrame(
            [
                {
                    "Model": "DSX321G",
                    "Size (L×W) [mm]": "3.2 x 2.5",
                    "Frequency [MHz]": "7.9 to 12",
                    "Frequency Tolerance [×10-6]": "20",
                    "Load Capacitance [pF]": "8, 10, 12",
                },
                {
                    "Model": "DSX321G",
                    "Size (L×W) [mm]": "3.2 x 2.5",
                    "Frequency [MHz]": "12 to 64",
                    "Frequency Tolerance [×10-6]": "20",
                    "Load Capacitance [pF]": "8, 10, 12",
                },
            ]
        )

        with (
            mock.patch.object(
                timing_sync,
                "KDS_SOURCES",
                {"https://example.invalid/kds": "晶振"},
            ),
            mock.patch.object(
                timing_sync,
                "read_official_tables",
                return_value=[source],
            ),
        ):
            rows = timing_sync.build_kds_rows(mock.Mock(), "2026-07-30 21:00:00")

        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["频率下限"], "7.9")
        self.assertEqual(rows[0]["频率上限"], "64")

    def test_kds_official_part_number_is_imported_as_exact_row(self):
        source = pd.DataFrame(
            [
                {
                    "Model": "DSB1612SDN",
                    "Part No.": "7EG02600A2C",
                    "Size (L×W) [mm]": "1.6 x 1.2",
                    "Frequency [MHz]": "26",
                    "Output": "Clipped sine",
                    "Supply Voltage [V]": "1.8",
                    "Freq. Temp. Characteristics [×10-6]": "0.5",
                    "Operating Temp. Range [℃]": "-30 to +85",
                    "Voltage Control": "-",
                    "Stand-by Function": "-",
                },
                {
                    "Model": "DSX321G",
                    "Part No.": "-",
                    "Size (L×W) [mm]": "3.2 x 2.5",
                    "Frequency [MHz]": "12 to 64",
                    "Frequency Tolerance [×10-6]": "20",
                    "Load Capacitance [pF]": "8, 10, 12",
                },
            ]
        )

        with (
            mock.patch.object(
                timing_sync,
                "KDS_SOURCES",
                {"https://example.invalid/kds": "振荡器"},
            ),
            mock.patch.object(
                timing_sync,
                "read_official_tables",
                return_value=[source],
            ),
        ):
            rows = timing_sync.build_kds_rows(mock.Mock(), "2026-07-30 21:00:00")

        exact = next(row for row in rows if row["型号"] == "7EG02600A2C")
        self.assertEqual(exact["系列"], "DSB1612SDN")
        self.assertEqual(exact["型号粒度"], "官方逐料号")
        self.assertEqual(exact["官方规格编号"], "7EG02600A2C")
        self.assertEqual(exact["输出频率"], "26")
        self.assertFalse(any(row["型号"] == "-" for row in rows))

    def test_tkd_official_product_table_is_parsed_as_series_range(self):
        markup = """
        <div class="table-row">
          <div class="col-root-class">高频晶体MHz</div>
          <div class="col-class">SEAM封装 MHz</div>
          <div class="col-series"><a href="/sx-3225/">SX-3225</a></div>
          <div class="col-size">3.2 x 2.5</div>
          <div class="col-freq">8MHz ~ 200MHz</div>
          <div class="col-accuracy">±10ppm(可定制)</div>
          <div class="col-zd_product_title3">±10ppm(可定制)</div>
          <div class="col-temp">-40 ~ +85℃</div>
          <div class="col-load">6pF, 10pF, 12pF, 16pF</div>
          <div class="col-feature">高稳定性，低老化率</div>
        </div>
        """

        class Response:
            content = markup.encode("utf-8")

            @staticmethod
            def raise_for_status():
                return None

        class Session:
            @staticmethod
            def get(_url, timeout=90):
                return Response()

        with mock.patch.object(
            timing_sync,
            "TKD_SOURCES",
            {"https://www.sztkd.com/seam_package_crystal_mhz/": "晶振"},
        ):
            rows = timing_sync.build_tkd_rows(Session(), "2026-07-30 21:00:00")

        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["品牌"], "TKD泰晶")
        self.assertEqual(rows[0]["型号"], "SX-3225")
        self.assertEqual(rows[0]["尺寸（inch）"], "3225")
        self.assertEqual(rows[0]["频率下限"], "8")
        self.assertEqual(rows[0]["频率上限"], "200")
        self.assertEqual(rows[0]["负载电容选项"], "|6|10|12|16|")
        self.assertEqual(rows[0]["型号粒度"], "官方系列范围")

    def test_huilun_official_series_rows_are_available_but_not_fake_exact_parts(self):
        rows = timing_sync.build_huilun_rows("2026-07-30 21:00:00")
        frame = pd.DataFrame(rows).set_index("型号")

        self.assertIn("9C", frame.index)
        self.assertIn("1S", frame.index)
        self.assertIn("9Y", frame.index)
        self.assertEqual(frame.loc["9C", "尺寸（inch）"], "2016")
        self.assertEqual(frame.loc["9C", "频率下限"], "1")
        self.assertEqual(frame.loc["9C", "频率上限"], "60")
        self.assertEqual(frame.loc["9C", "型号粒度"], "官方系列范围")

    def test_official_timing_series_decoders_do_not_invent_missing_frequency(self):
        ndk = cm.parse_model_rule("NX3225SA")
        kds = cm.parse_model_rule("DSX321G")
        tkd = cm.parse_model_rule("SX-3225", brand="泰晶")
        huilun = cm.parse_model_rule("9CABC", brand="惠伦")

        self.assertEqual(ndk["品牌"], "NDK")
        self.assertEqual(ndk["尺寸（inch）"], "3225")
        self.assertEqual(kds["品牌"], "KDS大真空")
        self.assertEqual(tkd["品牌"], "TKD泰晶")
        self.assertEqual(huilun["品牌"], "YL惠伦")
        for parsed in [ndk, kds, tkd, huilun]:
            self.assertNotIn("频率", parsed)
            self.assertNotIn("输出频率", parsed)
            self.assertIn("完整订购参数待确认", parsed["数据状态"])

    def test_timing_sidecar_filter_allows_tighter_frequency_tolerance(self):
        where_clauses = []
        params = []

        cm.append_timing_tolerance_candidate_filter(where_clauses, params, "20")

        self.assertEqual(len(where_clauses), 1)
        self.assertIn("CAST(_tol AS REAL) <= ?", where_clauses[0])
        self.assertEqual(params, ["20", 20.0, "%|20|%"])

    def test_other_brand_exact_crystal_can_match_tighter_official_epson_pn(self):
        rows = pd.DataFrame(
            [
                {
                    "品牌": "Abracon",
                    "型号": "ABM11N-40.0000MHZ-8-D2X-T3",
                    "系列": "ABM11N",
                    "器件类型": "晶振",
                    "尺寸（inch）": "2016",
                    "容值": "40",
                    "容值单位": "MHz",
                    "容值误差": "20",
                    "负载电容（pF）": "8",
                    "工作温度": "-40~+85°C",
                    "频率温度特性（ppm）": "±20ppm",
                    "泛音阶次": "基频（Fundamental）",
                    "ESR": "50Ω Max",
                    "型号粒度": "官方逐料号",
                },
                {
                    "品牌": "爱普生Epson",
                    "型号": "Q22FA12800697",
                    "系列": "FA-128",
                    "器件类型": "晶振",
                    "尺寸（inch）": "2016",
                    "容值": "40",
                    "容值单位": "MHz",
                    "容值误差": "10",
                    "负载电容（pF）": "8",
                    "工作温度": "-40~+85°C",
                    "频率温度特性（ppm）": "±20ppm",
                    "25℃老化（ppm）": "±1ppm",
                    "泛音阶次": "基频（Fundamental）",
                    "ESR": "50Ω Max",
                    "型号粒度": "官方逐料号",
                    "官方规格编号": "Q22FA12800697",
                },
            ]
        )
        prepared = cm.prepare_search_dataframe(
            cm.normalize_imported_component_dataframe(rows)
        )
        mode, spec = cm.detect_query_mode_and_spec(
            prepared,
            "ABM11N-40.0000MHZ-8-D2X-T3",
        )

        with mock.patch.object(cm, "fetch_search_candidate_pairs", return_value=None):
            matched = cm.match_other_passive_spec(prepared, spec)

        self.assertEqual(mode, "料号")
        self.assertIn("Q22FA12800697", matched["型号"].tolist())

    def test_official_exact_pn_sorts_before_epson_series_template(self):
        rows = pd.DataFrame(
            [
                {
                    "品牌": "爱普生Epson",
                    "型号": "FA-128",
                    "系列": "FA-128",
                    "器件类型": "晶振",
                    "尺寸（inch）": "2016",
                    "容值": "40",
                    "容值单位": "MHz",
                    "容值误差": "10",
                    "负载电容（pF）": "8",
                    "工作温度": "-40~+85°C",
                    "频率温度特性（ppm）": "±20ppm",
                    "泛音阶次": "基频（Fundamental）",
                    "型号粒度": "官方系列模板",
                },
                {
                    "品牌": "爱普生Epson",
                    "型号": "Q22FA12800697",
                    "系列": "FA-128",
                    "器件类型": "晶振",
                    "尺寸（inch）": "2016",
                    "容值": "40",
                    "容值单位": "MHz",
                    "容值误差": "10",
                    "负载电容（pF）": "8",
                    "工作温度": "-40~+85°C",
                    "频率温度特性（ppm）": "±20ppm",
                    "泛音阶次": "基频（Fundamental）",
                    "型号粒度": "官方逐料号",
                    "官方规格编号": "Q22FA12800697",
                },
            ]
        )
        prepared = cm.prepare_search_dataframe(
            cm.normalize_imported_component_dataframe(rows)
        )
        spec = cm.parse_timing_spec_query(
            "晶振 40MHz 2016 8pF ±10ppm -40~85°C 温度特性±20ppm 基频"
        )

        with mock.patch.object(cm, "fetch_search_candidate_pairs", return_value=None):
            matched = cm.match_other_passive_spec(prepared, spec)

        self.assertEqual(matched.iloc[0]["型号"], "Q22FA12800697")
        self.assertEqual(matched.iloc[1]["推荐等级"], "需确认配置")

    def test_sitime_sit9121_official_ordering_code_is_decoded(self):
        parsed = cm.parse_model_rule("SIT9121AI-2D3-33E125.000000")

        self.assertIsNotNone(parsed)
        self.assertEqual(parsed["品牌"], "SiTime")
        self.assertEqual(parsed["器件类型"], "振荡器")
        self.assertEqual(parsed["系列"], "SiT9121")
        self.assertEqual(parsed["输出频率"], "125")
        self.assertEqual(parsed["频率单位"], "MHZ")
        self.assertEqual(parsed["容值误差"], "±50ppm")
        self.assertEqual(parsed["电源电压"], "3.3")
        self.assertEqual(parsed["输出类型"], "LVDS")
        self.assertEqual(parsed["尺寸（inch）"], "7050")
        self.assertEqual(parsed["工作温度"], "-40~85℃")
        self.assertEqual(parsed["数据状态"], "SiTime官方逐料号页面已核验")

    def test_sitime_sit9121_datasheet_decoded_frequency_is_searchable(self):
        model = "SIT9121AI-2D3-33E120.000000"
        exact_map = cm.load_component_rows_by_exact_models_from_database([model])
        exact_rows = exact_map[cm.clean_model(model)]

        self.assertEqual(len(exact_rows), 1)
        self.assertEqual(exact_rows.iloc[0]["型号"], model)
        self.assertEqual(exact_rows.iloc[0]["输出频率"], "120")
        self.assertEqual(
            exact_rows.iloc[0]["数据状态"],
            "SiTime官方数据手册订购码解码",
        )
        mode, spec = cm.detect_query_mode_and_spec(exact_rows, model)
        self.assertEqual(mode, "料号")
        self.assertEqual(spec["器件类型"], "振荡器")
        self.assertEqual(spec["容值"], "120")

    def test_sitime_exact_row_survives_index_candidate_filter(self):
        model = "SIT9121AI-2D3-33E125.000000"
        exact_rows = cm.load_component_rows_by_exact_models_from_database([model])[
            cm.clean_model(model)
        ]
        mode, spec = cm.detect_query_mode_and_spec(exact_rows, model)

        with mock.patch.object(
            cm,
            "fetch_search_candidate_pairs",
            return_value=[("Abracon", "ASG-D-V-A-125.000MHZ")],
        ):
            scoped = cm.scope_search_dataframe(exact_rows, spec)

        self.assertEqual(mode, "料号")
        self.assertEqual(scoped["型号"].tolist(), [model])

    def test_sitime_sit9121_rejects_unsupported_frequency_gap(self):
        self.assertIsNone(cm.parse_model_rule("SIT9121AI-2D3-33E210.000000"))

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
