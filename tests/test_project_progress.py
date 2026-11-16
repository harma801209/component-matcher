from contextlib import closing
import base64
import gzip
import hashlib
from pathlib import Path
import sqlite3
import tempfile
import unittest

from project_progress import DAY, ProjectError, ProjectStore, _deadline, save_project_to_snapshot


class ProjectProgressTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.path = Path(directory.name) / "isolated-member.sqlite"
        with closing(sqlite3.connect(self.path)) as conn, conn:
            conn.executescript("""
                CREATE TABLE members (id INTEGER PRIMARY KEY, username, display_name, role, status);
                CREATE TABLE member_sales_customers (id INTEGER PRIMARY KEY, member_id, customer_name);
                INSERT INTO members VALUES (1,'alice','销售甲','member','active'),
                    (2,'bob','销售乙','member','active'), (3,'admin','审核人','admin','active'),
                    (4,'disabled','','admin','disabled');
                INSERT INTO member_sales_customers VALUES (101,1,'甲客户'), (102,1,'无项目客户'),
                    (201,2,'乙客户');
            """)
        self.now = 1_800_000_000
        self.alice = ProjectStore(self.path, 1, clock=lambda: self.now)
        self.bob = ProjectStore(self.path, 2, clock=lambda: self.now)
        self.admin = ProjectStore(self.path, 3, clock=lambda: self.now)

    def entry(self):
        return self.alice.overview()[2][0]

    def test_registrations_list_without_projects_and_members_are_isolated(self):
        admin, customers, projects = self.alice.overview()
        self.assertFalse(admin)
        self.assertEqual({c["customer_name"] for c in customers}, {"甲客户", "无项目客户"})
        self.assertFalse(projects)
        own_project = self.alice.create(101, "控制板", "客户准备试产", next_action="发工程样品")
        other_project = self.bob.create(201, "驱动板")
        self.assertEqual([p["id"] for p in self.alice.overview()[2]], [own_project])
        self.assertEqual(self.entry()["next_action"], "发工程样品")
        self.assertEqual(self.entry()["latest_progress"], "客户准备试产")
        self.assertEqual({p["id"] for p in self.admin.overview()[2]}, {own_project, other_project})
        self.assertEqual(self.admin.history(own_project)[0]["kind"], "created")
        with self.assertRaises(ProjectError):
            self.alice.create(201, "别人的客户")
        with self.assertRaises(ProjectError):
            self.alice.history(other_project)
        with self.assertRaises(ProjectError):
            self.admin.record(own_project, 0, "progress", "替别的会员写", "已完成")
        with self.assertRaises(ProjectError):
            self.alice.create(101, "  控制板  ")
        with self.assertRaises(ProjectError):
            ProjectStore(self.path, 4).overview()

    def test_14_days_before_quote_and_7_after_actual_quote(self):
        started = self.now
        project = self.alice.create(101, "传感器板", quote_request=True)
        self.assertEqual(self.entry()["due_at"], started + 14 * DAY)
        self.assertEqual(self.entry()["quote_event"], "quote_request")
        self.now += 2 * DAY
        self.alice.record(project, 0, "progress", "已确认需求", "选型／送样", "发样品给客户")
        self.assertEqual(self.entry()["due_at"], self.now + 14 * DAY)
        self.assertEqual(self.entry()["next_action"], "发样品给客户")
        self.now += DAY
        self.alice.record(project, 1, "quoted", "已发给客户")
        self.assertEqual(self.entry()["quoted_at"], self.now)
        self.assertEqual(self.entry()["due_at"], self.now + 7 * DAY)
        self.assertEqual(self.entry()["latest_progress"], "已确认需求")
        self.now += 8 * DAY
        due = self.entry()["due_at"]
        self.alice.record(project, 2, "quoted", "发送修订报价")
        self.assertEqual(self.entry()["due_at"], due)
        self.assertEqual(_deadline(due, self.now), "已逾期")
        self.alice.record(project, 3, "progress", "送样完成", "客户验证", "下周确认测试")
        self.assertEqual(self.entry()["due_at"], self.now + 7 * DAY)
        self.alice.record(project, 4, "progress", "客户验收", "已完成")
        self.assertIsNone(self.entry()["due_at"])
        with self.assertRaises(ProjectError):
            self.alice.record(project, 5, "quoted", "结案后不再报价")

    def test_reminder_targets_owner_once_per_cycle_and_rejects_stale_update(self):
        project = self.alice.create(101, "逾期项目")
        with self.assertRaises(ProjectError):
            self.admin.remind(project, 0)
        self.now += 14 * DAY
        with self.assertRaises(ProjectError):
            self.bob.remind(project, 0)
        self.admin.remind(project, 0, "请补交验证结果")
        self.assertEqual(self.entry()["reminded_due_at"], self.entry()["due_at"])
        self.assertEqual(self.alice.history(project)[0]["note"], "请补交验证结果")
        with self.assertRaises(ProjectError):
            self.admin.remind(project, 0)
        with self.assertRaises(ProjectError):
            self.alice.record(project, 0, "progress", "找到问题", "遇到卡点")
        self.alice.record(project, 0, "progress", "找到问题", "遇到卡点", "约测试工程师复测")
        self.assertNotEqual(self.entry()["due_at"], self.entry()["reminded_due_at"])
        self.now += 14 * DAY
        with self.assertRaises(ProjectError):
            self.admin.remind(project, 0)
        self.admin.remind(project, 1)
        self.assertEqual([r["kind"] for r in self.alice.history(project)],
                         ["reminder", "progress", "reminder", "created"])

    def test_member_page_renders_project_and_private_reminder(self):
        from streamlit.testing.v1 import AppTest

        mine = self.alice.create(101, "我的项目", next_action="确认样品")
        self.bob.create(201, "不应出现在我页面的项目")
        self.now += 14 * DAY
        self.admin.remind(mine, 0, "补测试结果")
        page = AppTest.from_string(
            "import streamlit as st\n"
            "from project_progress import ProjectStore, render_page\n"
            f"store = ProjectStore({str(self.path)!r}, 1, clock=lambda: {self.now})\n"
            "render_page(st, store, write=lambda action: (action(store), True)[1], register_customer=None)\n",
            default_timeout=30,
        ).run()
        self.assertFalse(page.exception)
        self.assertTrue(any("管理员已提醒" in item.value for item in page.warning))
        self.assertIn("确认样品", page.dataframe[-1].value["下一步"].tolist())
        self.assertNotIn("不应出现在我页面的项目", page.dataframe[-1].value["项目"].tolist())
        page.selectbox(key="project-progress-1-selected").select(mine).run()
        self.assertFalse(page.exception)
        self.assertIn("补测试结果", page.dataframe[-1].value["说明"].tolist())
        self.assertFalse(any(button.label == "发送站内提醒" for button in page.button))

    def test_shared_save_retries_conflict_without_losing_other_writer_changes(self):
        initial = self.path.read_bytes()
        remote = self.path.with_name("remote.sqlite")
        remote.write_bytes(initial)
        version = 5
        attempted_versions = []

        def request(method, payload=None):
            nonlocal version
            if method == "GET":
                return self._snapshot(remote.read_bytes(), version)
            attempted_versions.append(payload["expected_version"])
            if len(attempted_versions) == 1:
                ProjectStore(remote, 2).create(201, "其他会员先保存")
                version += 1
                return {"conflict": True, "version": version}
            self.assertEqual(payload["expected_version"], version)
            remote.write_bytes(self._raw(payload))
            return {"ok": True, "sha256": payload["sha256"], "version": version + 1}

        self.assertTrue(save_project_to_snapshot(
            self.alice, lambda store: store.create(101, "测试", "测试项目", quote_request=True), request))
        self.assertEqual(attempted_versions, [5, 6])
        self.assertEqual(self.path.read_bytes(), initial)
        restored = ProjectStore(remote, 1)
        rows = restored.overview()[2]
        self.assertEqual([row["name"] for row in rows], ["测试"])
        self.assertEqual([e["kind"] for e in restored.history(rows[0]["id"])], ["quote_request", "created"])
        self.assertEqual(ProjectStore(remote, 2).overview()[2][0]["name"], "其他会员先保存")

    def test_shared_save_handles_lost_response_and_never_replays_uncertain_request(self):
        for committed in (False, True):
            with self.subTest(committed=committed):
                original = self.path.read_bytes()
                base = self._snapshot(original, 5)
                snapshot = base.copy()
                writes = []

                def request(method, payload=None):
                    if method == "GET":
                        return snapshot
                    writes.append(payload)
                    if committed:
                        snapshot.update(self._snapshot(self._raw(payload), 7))
                    return None

                self.assertEqual(save_project_to_snapshot(
                    self.alice, lambda store: store.create(101, "测试", quote_request=True), request), committed)
                self.assertEqual(len(writes), 1)
                self.assertEqual(self.path.read_bytes(), original)

    @staticmethod
    def _snapshot(raw, version):
        return {"version": version, "payload_base64": base64.b64encode(raw).decode("ascii"),
                "sha256": hashlib.sha256(raw).hexdigest(), "uncompressed_size": len(raw)}

    @staticmethod
    def _raw(payload):
        data = base64.b64decode(payload["payload_base64"])
        return gzip.decompress(data) if payload["payload_encoding"] == "gzip" else data
