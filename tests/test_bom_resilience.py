from __future__ import annotations

import importlib
import os
import sqlite3
import tempfile
import unittest
from contextlib import closing
from pathlib import Path


class BomJobStoreTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory(prefix="bom-job-store-")
        self.saved_path = os.environ.get("BOM_JOB_DB_PATH")
        os.environ["BOM_JOB_DB_PATH"] = str(Path(self.temp_dir.name) / "jobs.sqlite")
        import bom_job_store
        self.store = importlib.reload(bom_job_store)

    def tearDown(self):
        if self.saved_path is None:
            os.environ.pop("BOM_JOB_DB_PATH", None)
        else:
            os.environ["BOM_JOB_DB_PATH"] = self.saved_path
        self.temp_dir.cleanup()

    def test_job_checkpoint_is_owner_scoped_and_retryable(self):
        job = self.store.create_or_update_job(
            member_key="id:7", run_signature="run-1", file_name="bom.xlsx",
            file_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            file_sha256="abc", file_bytes=b"workbook",
            settings={"mode": "主营品牌自动匹配", "brands": []},
            mappings={"Sheet1": {"model": "型号"}}, total_rows=3,
        )
        self.assertIsNone(self.store.get_job(job["job_id"], member_key="id:8"))
        checkpoint = {"sheet_rows": {"Sheet1": {
            "0": {"状态": "可推荐", "BOM型号": "A"},
            "1": {"状态": "无匹配", "BOM型号": "B"},
            "2": {"状态": "解析失败", "BOM型号": "C"},
        }}}
        self.store.save_checkpoint(job["job_id"], checkpoint, processed_rows=3,
                                   unique_rows=2, status="failed")
        retry = self.store.reset_failed_rows(job["job_id"], member_key="id:7")
        self.assertEqual(list(retry["sheet_rows"]["Sheet1"]), ["0"])
        self.assertEqual(self.store.reset_failed_rows(job["job_id"], member_key="id:8"), {})

    def test_runtime_metric_summary(self):
        self.store.record_metric("bom", duration_ms=2000, total_rows=10,
                                 unique_rows=5, failed_rows=1)
        summary = self.store.metric_summary("bom")
        self.assertEqual(summary["runs"], 1)
        self.assertEqual(summary["dedupe_rate"], 0.5)
        self.assertAlmostEqual(summary["rows_per_second"], 5.0)


class ComponentQualityTests(unittest.TestCase):
    def test_quality_report_groups_missing_critical_fields(self):
        from component_quality import build_quality_report
        with tempfile.TemporaryDirectory(prefix="quality-report-") as temp_dir:
            path = Path(temp_dir) / "components.sqlite"
            with closing(sqlite3.connect(path)) as conn:
                conn.execute(
                    'CREATE TABLE components ("品牌" TEXT, "器件类别" TEXT, "型号" TEXT, '
                    '"尺寸（inch）" TEXT, "容值" TEXT, "容值单位" TEXT, "容值误差" TEXT, "功率" TEXT)'
                )
                conn.executemany('INSERT INTO components VALUES (?, ?, ?, ?, ?, ?, ?, ?)', [
                    ("富捷", "贴片电阻", "FRC0402F1001TS", "0402", "1", "KΩ", "±1%", "1/16W"),
                    ("富捷", "贴片电阻", "FRC0402F1002TS", "0402", "10", "KΩ", "±1%", ""),
                ])
                conn.commit()
            report = build_quality_report(str(path))
            self.assertEqual(report["summary"]["rows"], 2)
            self.assertEqual(report["rows"][0]["incomplete_rows"], 1)
            self.assertEqual(report["rows"][0]["complete_rate"], 0.5)


if __name__ == "__main__":
    unittest.main()
