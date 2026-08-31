from __future__ import annotations

import unittest
from unittest.mock import patch

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
from tempfile import TemporaryDirectory
from pathlib import Path

import sync_lcsc_broad_components as sync
from incremental_semiconductor_cache_update import collect_prepared_pairs_by_source_markers


class BroadComponentSyncTests(unittest.TestCase):
    def test_official_timing_row_wins_over_distributor_duplicate(self) -> None:
        with TemporaryDirectory() as temp_dir:
            crystal_dir = Path(temp_dir)
            official_path = crystal_dir / "epson_official.csv"
            lcsc_path = crystal_dir / "lcsc.csv"
            official = pd.DataFrame(
                [
                    {
                        "品牌": "爱普生Epson",
                        "型号": "X1A0001710001",
                        "系列": "FC2012AN",
                        "器件类型": "晶振",
                        "尺寸（inch）": "2012",
                        "频率": "32.768",
                        "频率单位": "KHZ",
                        "负载电容（pF）": "12.5",
                        "ESR": "60kΩ Max",
                        "驱动电平": "0.5µW Max",
                        "型号粒度": "官方逐料号",
                        "数据来源": "Epson official selector",
                    }
                ]
            )
            distributor = pd.DataFrame(
                [
                    {
                        "品牌": "EPSON",
                        "型号": "X1A0001710001",
                        "系列": "FC2012AN",
                        "器件类型": "晶振",
                        "尺寸（inch）": "2012",
                        "频率": "32.768",
                        "频率单位": "KHZ",
                        "ESR": "35kΩ Max",
                        "型号粒度": "专业分销商逐料号",
                        "数据来源": sync.SOURCE_MARKER,
                    }
                ]
            )
            official.to_csv(official_path, index=False, encoding="utf-8-sig")
            normalized = sync.cm.normalize_imported_component_dataframe(
                distributor,
                source_path=str(lcsc_path),
            )

            with patch.object(sync, "CRYSTAL_DIR", crystal_dir):
                merged = sync.merge_authoritative_timing_overlaps(
                    normalized,
                    {lcsc_path.resolve()},
                )

        row = merged.iloc[0]
        self.assertEqual(row["型号"], "X1A0001710001")
        self.assertEqual(row["负载电容（pF）"], "12.5")
        self.assertEqual(row["ESR"], "60kΩ Max")
        self.assertEqual(row["驱动电平"], "0.5µW Max")
        self.assertIn("official", row["数据来源"].lower())

    def test_build_electrolytic_exact_mpn(self) -> None:
        source = {
            "brandNameEn": "Rubycon",
            "productModel": "35ZLH100MEFC6.3X11",
            "productCode": "C109392",
            "catalogName": "Aluminum Electrolytic Capacitors - Through Hole",
            "encapStandard": "Through Hole,D6.3xL11mm",
            "productIntroEn": "100uF 35V Aluminum Electrolytic Capacitors 6000hrs@105℃",
            "productCycle": "normal",
            "pdfUrl": "https://example.test/rubycon.pdf",
            "url": "https://example.test/C109392",
            "minBuyNumber": 10,
            "minPacketNumber": 500,
            "paramVOList": [
                {"paramNameEn": "Capacitance", "paramValueEn": "100uF"},
                {"paramNameEn": "Tolerance", "paramValueEn": "±20%"},
                {"paramNameEn": "Voltage Rating", "paramValueEn": "35V"},
                {"paramNameEn": "Lifetime", "paramValueEn": "6000hrs@105℃"},
                {"paramNameEn": "Operating Temperature", "paramValueEn": "-40℃~+105℃"},
                {"paramNameEn": "Diameter", "paramValueEn": "6.3mm"},
                {"paramNameEn": "Height - Seated (Max)", "paramValueEn": "11mm"},
            ],
        }
        row = sync.build_electrolytic_row(source, "2026-08-01")
        self.assertEqual(row["器件类型"], "铝电解电容")
        self.assertEqual(row["型号"], "35ZLH100MEFC6.3X11")
        self.assertEqual(row["容值"], "100")
        self.assertEqual(row["容值单位"], "UF")
        self.assertEqual(row["耐压（V）"], "35")
        self.assertEqual(row["尺寸（mm）"], "6.3×11")
        self.assertEqual(row["生产状态"], "量产")
        self.assertEqual(row["型号粒度"], "专业分销商逐料号")

    def test_build_crystal_marks_missing_parameters(self) -> None:
        source = {
            "brandNameEn": "EPSON",
            "productModel": "Q13FC13500004",
            "productCode": "C32346",
            "catalogName": "Crystals",
            "encapStandard": "SMD3215-2P",
            "productIntroEn": "Crystal 32.768kHz ±20ppm 12.5pF 70kΩ SMD3215-2P",
            "productCycle": "normal",
            "paramVOList": [
                {"paramNameEn": "Frequency", "paramValueEn": "32.768kHz"},
                {"paramNameEn": "Normal temperature Frequency Tolerance", "paramValueEn": "±20ppm"},
                {"paramNameEn": "Load Capacitance", "paramValueEn": "12.5pF"},
                {"paramNameEn": "Equivalent Series Resistance(ESR)", "paramValueEn": "70kΩ"},
            ],
        }
        row = sync.build_timing_row(source, 1155, "2026-08-01")
        self.assertEqual(row["品牌"], "爱普生Epson")
        self.assertEqual(row["型号"], "Q13FC13500004")
        self.assertEqual(row["频率"], "32.768")
        self.assertEqual(row["频率单位"], "KHZ")
        self.assertEqual(row["资料完整度"], "需确认")
        self.assertIn("工作温度", row["缺失关键参数"])

    def test_rejects_unrelated_product_without_frequency(self) -> None:
        source = {
            "brandNameEn": "SAMSUNG",
            "productModel": "KLUDG4UHDC-B0E1",
            "catalogName": "Oscillators",
            "productIntroEn": "Oscillators RoHS",
            "paramVOList": [],
        }
        self.assertIsNone(sync.build_timing_row(source, 1157, "2026-08-01"))

    def test_frequency_falls_back_to_product_description(self) -> None:
        source = {
            "brandNameEn": "TXC",
            "productModel": "TEST-24M",
            "catalogName": "Oscillators",
            "productIntroEn": "24MHz SMD2520-4P Oscillators RoHS",
            "encapStandard": "SMD2520-4P",
            "paramVOList": [],
        }
        row = sync.build_timing_row(source, 1157, "2026-08-01")
        self.assertIsNotNone(row)
        self.assertEqual(row["输出频率"], "24")
        self.assertEqual(row["频率单位"], "MHZ")

    def test_rejects_specification_text_in_model_column(self) -> None:
        source = {
            "brandNameEn": "SiTime",
            "productModel": "85MHz 25PPM 3.3V",
            "catalogName": "Oscillators",
            "productIntroEn": "85MHz 25ppm 3.3V SMD Oscillator",
            "paramVOList": [],
        }
        self.assertIsNone(sync.build_timing_row(source, 1157, "2026-08-01"))

    def test_keeps_real_ordering_model_with_embedded_frequency(self) -> None:
        self.assertTrue(sync.is_exact_timing_model("SG2520HGN 125.000MHz"))
        self.assertTrue(sync.is_exact_timing_model("DT-26-32.768K 6pF 20PPM"))
        self.assertTrue(sync.is_exact_timing_model("49S-10.7386M-18PF-20PPM"))
        self.assertTrue(sync.is_exact_timing_model("G13270009"))
        self.assertTrue(sync.is_exact_timing_model("83008000301"))
        self.assertTrue(sync.is_exact_timing_model("ECS-.327-12.5-1210-TR"))
        self.assertFalse(sync.is_exact_timing_model("14.31818MHz ±25PPM 1.8V"))
        self.assertFalse(sync.is_exact_timing_model("26MHz/2016/8pF/10PPM"))
        self.assertFalse(sync.is_exact_timing_model("12M 10PF 4P 10PPM"))

    def test_finalize_deduplicates_brand_and_model(self) -> None:
        rows = [
            {"品牌": "EPSON", "型号": "Q13-FC_13500004", "资料完整度": "需确认"},
            {"品牌": "爱普生Epson", "型号": "Q13FC13500004", "资料完整度": "关键参数完整", "备注2": "pdf"},
        ]
        frame = sync.finalize_rows(rows)
        self.assertEqual(len(frame), 1)
        self.assertEqual(frame.iloc[0]["资料完整度"], "关键参数完整")

    def test_collects_all_stale_rows_from_same_source_before_refresh(self) -> None:
        with TemporaryDirectory() as temp_dir:
            cache_path = Path(temp_dir) / "prepared.parquet"
            frame = pd.DataFrame(
                [
                    {"品牌": "SiTime", "型号": "85MHz 25PPM 3.3V", "数据来源": sync.SOURCE_MARKER},
                    {"品牌": "爱普生Epson", "型号": "Q13FC13500004", "数据来源": "official"},
                ]
            )
            pq.write_table(pa.Table.from_pandas(frame, preserve_index=False), cache_path)
            with patch.object(sync.cm, "PREPARED_CACHE_PATH", str(cache_path)):
                pairs = collect_prepared_pairs_by_source_markers({sync.SOURCE_MARKER})

        self.assertEqual(pairs.to_dict("records"), [{"品牌": "SiTime", "型号": "85MHz 25PPM 3.3V"}])


if __name__ == "__main__":
    unittest.main()
