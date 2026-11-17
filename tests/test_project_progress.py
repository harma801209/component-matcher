from contextlib import closing
import base64
import gzip
import hashlib
from pathlib import Path
import sqlite3
import tempfile
import unittest

from project_progress import (
    DAY, LEGACY_DONE, ORDERED, STOPPED, ProjectError, ProjectStore,
    _deadline, _project_card, _project_status, _project_timeline, save_project_to_snapshot,
)


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
        self.alice.record(project, 4, "progress", "客户不再推进", STOPPED)
        self.assertIsNone(self.entry()["due_at"])
        self.assertIsNone(self.entry()["order_recorded_at"])
        with self.assertRaises(ProjectError):
            self.alice.record(project, 5, "quoted", "结案后不再报价")

    def test_first_order_closes_project_and_disables_reminders(self):
        project = self.alice.create(101, "首单项目", next_action="继续验证")
        self.alice.record(project, 0, "quoted", "发出报价")
        self.assertIsNone(self.entry()["order_recorded_at"])
        self.now += 7 * DAY
        self.admin.remind(project, 1)
        with self.assertRaisesRegex(ProjectError, "只能更新自己"):
            self.admin.record(project, 1, "ordered", "越权登记")
        with self.assertRaisesRegex(ProjectError, "项目已更新"):
            self.alice.record(project, 0, "ordered", "过期表单")
        with self.assertRaisesRegex(ProjectError, "首单登记"):
            self.alice.record(project, 1, "progress", "不能从普通阶段伪造", ORDERED)
        with self.assertRaisesRegex(ProjectError, "事项说明"):
            self.alice.record(project, 1, "ordered", " ")
        self.alice.record(project, 1, "ordered", "收到首张订单 PO-001")
        row = self.entry()
        self.assertEqual(row["stage"], ORDERED)
        self.assertEqual(row["latest_progress"], "收到首张订单 PO-001")
        self.assertEqual(row["order_recorded_at"], self.now)
        self.assertEqual(row["last_progress_at"], self.now)
        self.assertIsNone(row["due_at"])
        self.assertIsNone(row["reminded_due_at"])
        self.assertEqual(row["next_action"], "")
        self.assertEqual(self.admin.overview()[2][0]["stage"], ORDERED)
        self.assertEqual([item["kind"] for item in self.alice.history(project)],
                         ["ordered", "reminder", "quoted", "created"])
        with self.assertRaisesRegex(ProjectError, "已经结案"):
            self.alice.record(project, 2, "ordered", "不重复闭环")
        with self.assertRaisesRegex(ProjectError, "逾期"):
            self.admin.remind(project, 2)

    def test_legacy_completion_does_not_count_as_order_without_confirmation(self):
        old = self.alice.create(101, "历史结案")
        with closing(sqlite3.connect(self.path)) as conn, conn:
            conn.execute("UPDATE member_customer_projects SET stage=?, due_at=NULL WHERE id=?", (LEGACY_DONE, old))
        self.assertEqual(_project_status(self.entry(), self.now)[1], "neutral")
        self.assertIsNone(self.entry()["order_recorded_at"])
        self.alice.record(old, 0, "ordered", "核对历史订单 PO-002")
        self.assertEqual(_project_status(self.entry(), self.now), ("已下单闭环", "done"))

    def test_cards_and_timeline_escape_member_content(self):
        project = self.alice.create(101, "<script>bad</script>", "<img src=bad>", next_action="<b>action</b>")
        markup = _project_card(self.entry(), self.now, detail=True) + _project_timeline(self.alice.history(project))
        for unsafe in ("<script>", "<img", "<b>action"):
            self.assertNotIn(unsafe, markup)
        for safe in ("&lt;script&gt;", "&lt;img src=bad&gt;", "&lt;b&gt;action&lt;/b&gt;"):
            self.assertIn(safe, markup)

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
        cards = next(item.value for item in page.markdown if '<div class="pp-grid"' in item.value)
        self.assertIn("确认样品", cards)
        self.assertNotIn("不应出现在我页面的项目", cards)
        page.selectbox(key="project-progress-1-selected").select(mine).run()
        self.assertFalse(page.exception)
        self.assertTrue(any("补测试结果" in item.value for item in page.markdown if 'class="pp-timeline"' in item.value))
        self.assertFalse(any(button.label == "发送站内提醒" for button in page.button))

    def test_first_order_form_requires_confirmation_and_switches_to_closed_view(self):
        from streamlit.testing.v1 import AppTest

        mine = self.alice.create(101, "首单 UI 测试", next_action="确认样品")
        page = AppTest.from_string(
            "import streamlit as st\n"
            "from project_progress import ProjectStore, render_page\n"
            f"store = ProjectStore({str(self.path)!r}, 1, clock=lambda: {self.now})\n"
            "render_page(st, store, write=lambda action: (action(store), True)[1], register_customer=None)\n",
            default_timeout=30,
        ).run()
        page.selectbox(key="project-progress-1-selected").select(mine).run()
        next(item for item in page.text_area if item.label == "首单说明").input("首单凭据 PO-100")
        next(item for item in page.button if item.label == "确认下单并闭环").click().run()
        self.assertTrue(any("请先确认" in item.value for item in page.warning))
        self.assertIsNotNone(self.entry()["due_at"])
        next(item for item in page.text_area if item.label == "首单说明").input("首单凭据 PO-100")
        next(item for item in page.checkbox if item.label == "我确认客户已开始下单").check()
        next(item for item in page.button if item.label == "确认下单并闭环").click().run()
        self.assertFalse(page.exception)
        self.assertEqual(page.radio(key="project-progress-1-scope").value, "已下单闭环")
        self.assertEqual(self.entry()["stage"], ORDERED)
        self.assertTrue(any("首单凭据 PO-100" in item.value for item in page.markdown if 'class="pp-timeline"' in item.value))
        self.assertFalse(any(item.label in ("确认下单并闭环", "保存跟进") for item in page.button))

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

    def test_first_order_survives_snapshot_restore_after_lost_acknowledgement(self):
        project = self.alice.create(101, "等首单的项目")
        original = self.path.read_bytes()
        remote = self.path.with_name("restored-order.sqlite")
        snapshot = self._snapshot(original, 3)

        def request(method, payload=None):
            if method == "GET":
                return snapshot
            self.assertEqual(payload["expected_version"], 3)
            raw = self._raw(payload)
            remote.write_bytes(raw)
            snapshot.update(self._snapshot(raw, 4))
            return None

        self.assertTrue(save_project_to_snapshot(
            self.alice, lambda store: store.record(project, 0, "ordered", "实际首单 PO-321"), request))
        self.assertEqual(self.path.read_bytes(), original)
        restored = ProjectStore(remote, 1)
        row = restored.overview()[2][0]
        self.assertEqual(row["stage"], ORDERED)
        self.assertIsNone(row["due_at"])
        self.assertEqual(restored.history(project)[0]["note"], "实际首单 PO-321")

    @staticmethod
    def _snapshot(raw, version):
        return {"version": version, "payload_base64": base64.b64encode(raw).decode("ascii"),
                "sha256": hashlib.sha256(raw).hexdigest(), "uncompressed_size": len(raw)}

    @staticmethod
    def _raw(payload):
        data = base64.b64decode(payload["payload_base64"])
        return gzip.decompress(data) if payload["payload_encoding"] == "gzip" else data
