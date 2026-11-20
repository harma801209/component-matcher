from contextlib import closing
import base64
import gzip
import hashlib
from pathlib import Path
import re
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

    def test_register_and_create_are_independent_entries(self):
        from streamlit.testing.v1 import AppTest

        page = AppTest.from_string(
            "import streamlit as st\nfrom project_progress import ProjectStore, render_page\n"
            f"s = ProjectStore({str(self.path)!r}, 1)\n"
            "render_page(st,s,write=lambda a:(a(s),True)[1],register_customer=None,join_key=lambda n:n)",
            default_timeout=60,
        ).run()
        self.assertFalse(page.exception)
        panels = {panel.label: panel for panel in page.expander}
        self.assertEqual([b.label for b in panels["报备客户"].button], ["报备客户", "提交协同申请"])
        create = panels["新增项目"]
        self.assertEqual([b.label for b in create.button], ["保存新项目"])
        next(w for w in create.text_input if w.label == "项目名称").input("独立入口项目")
        create.button[0].click().run()
        self.assertFalse(page.exception)
        self.assertEqual(self.entry()["name"], "独立入口项目")

    def test_group_edit_is_owner_scoped_and_does_not_merge_customers(self):
        first = self.alice.create(101, "同名项目")
        second = self.bob.create(201, "同名项目")
        self.alice.set_customer_group(101, "  ACME   集团  ")
        self.bob.set_customer_group(201, "ACME 集团")
        with self.assertRaisesRegex(ProjectError, "名下客户"):
            self.alice.set_customer_group(201, "越权")
        with self.assertRaisesRegex(ProjectError, "名下客户"):
            self.admin.set_customer_group(201, "越权")
        with self.assertRaisesRegex(ProjectError, "120"):
            self.alice.set_customer_group(101, "A" * 121)
        rows = {row["id"]: row for row in self.admin.overview()[2]}
        self.assertEqual(rows[first]["group_name"], rows[second]["group_name"])
        self.assertNotEqual(rows[first]["customer_id"], rows[second]["customer_id"])
        self.assertEqual(self.entry()["group_name"], "ACME 集团")
        self.alice.set_customer_group(101, "")
        self.assertEqual(self.entry()["group_name"], "")
        self.assertEqual(self.bob.overview()[2][0]["group_name"], "ACME 集团")

    def test_registration_and_group_have_one_transaction(self):
        def upsert(conn):
            conn.execute("INSERT INTO member_sales_customers VALUES (103,1,'新客户')")
            return True, "", {"id": 103}

        self.alice.register_customer(upsert, "测试集团")
        self.assertEqual({row["id"]: row["group_name"] for row in self.alice.overview()[1]}[103], "测试集团")
        self.alice.register_customer(lambda conn: (True, "", {"id": 103}), "")
        self.assertEqual({row["id"]: row["group_name"] for row in self.alice.overview()[1]}[103], "测试集团")

        def inconsistent_save(conn):
            conn.execute("INSERT INTO member_sales_customers VALUES (104,1,'不应留下的客户')")
            return True, "", {"id": 201}

        with self.assertRaisesRegex(ProjectError, "名下客户"):
            self.alice.register_customer(inconsistent_save, "测试集团")
        self.assertNotIn(104, {row["id"] for row in self.alice.overview()[1]})

    def test_unconfirmed_registration_never_appears_in_local_customer_choices(self):
        self.alice.overview()  # Initialize schema before comparing the local replica's bytes.
        original = self.path.read_bytes()
        for committed in (False, True):
            with self.subTest(committed=committed):
                snapshot = self._snapshot(original, 7)
                staged_writes = []

                def request(method, payload=None):
                    if method == "GET":
                        return snapshot
                    staged_writes.append(payload)
                    if committed:
                        snapshot.update(self._snapshot(self._raw(payload), 8))
                    return None

                def upsert(conn):
                    conn.execute("INSERT INTO member_sales_customers VALUES (103,1,'报备验证客户')")
                    return True, "", {"id": 103}

                saved = save_project_to_snapshot(
                    self.alice, lambda target: target.register_customer(upsert, "验证集团"), request,
                )
                self.assertEqual(saved, committed)
                self.assertEqual(len(staged_writes), 1)
                self.assertEqual(self.path.read_bytes(), original)
                self.assertNotIn(103, {row["id"] for row in self.alice.overview()[1]})
                if committed:
                    confirmed = self.path.with_name("confirmed-company.sqlite")
                    confirmed.write_bytes(self._raw(staged_writes[0]))
                    customers = ProjectStore(confirmed, 1).overview()[1]
                    self.assertEqual({row["id"]: row["group_name"] for row in customers}[103], "验证集团")

    def test_competing_customer_claim_is_rejected_after_snapshot_retry(self):
        source = (Path(__file__).resolve().parents[1] / "component_matcher.py").read_text(encoding="utf-8")
        normalization = source[source.index("def normalize_cost_customer_name("):
                               source.index("def normalize_sales_customer_code(")]
        registration = source[source.index("def save_member_sales_customer("):
                              source.index("def select_member_sales_customer(")]
        env = dict(sqlite3=sqlite3, re=re, clean_text=lambda value: str(value or "").strip(),
                   current_timestamp_text=lambda: "2026-11-18 09:00")
        exec(normalization + registration, env)
        save = env["save_member_sales_customer"]
        with closing(sqlite3.connect(self.path)) as conn, conn:
            conn.executescript("""
                ALTER TABLE member_sales_customers ADD COLUMN customer_key TEXT NOT NULL DEFAULT '';
                ALTER TABLE member_sales_customers ADD COLUMN price_access_enabled INTEGER NOT NULL DEFAULT 0;
                ALTER TABLE member_sales_customers ADD COLUMN created_at TEXT NOT NULL DEFAULT '';
                ALTER TABLE member_sales_customers ADD COLUMN updated_at TEXT NOT NULL DEFAULT '';
                ALTER TABLE member_sales_customers ADD COLUMN last_selected_at TEXT NOT NULL DEFAULT '';
                UPDATE member_sales_customers SET customer_key=customer_name;
            """)
        original = self.path.read_bytes()
        snapshot = self._snapshot(original, 9)
        remote = self.path.with_name("other-claim.sqlite")
        remote.write_bytes(original)
        writes = []

        def register(store, name, group):
            store.register_customer(
                lambda conn: save(store.actor_id, name, sync_remote=False, connection=conn, exclusive_claim=True),
                group,
            )

        def request(method, payload=None):
            if method == "GET":
                return snapshot
            writes.append(payload["expected_version"])
            register(ProjectStore(remote, 2), "同一客户有限公司", "A 集团")
            snapshot.update(self._snapshot(remote.read_bytes(), 10))
            return {"conflict": True, "version": 10}

        with self.assertRaisesRegex(ProjectError, "已由其他会员报备"):
            save_project_to_snapshot(
                self.alice, lambda store: register(store, "同一 客户有限公司", "B 集团"), request,
            )
        self.assertEqual(writes, [9])
        self.assertEqual(self.path.read_bytes(), original)
        other = ProjectStore(remote, 2)
        register(other, "同一客户有限公司", "")
        customers = [row for row in ProjectStore(remote, 3).overview()[1] if "同一" in row["customer_name"]]
        self.assertEqual([(row["owner_id"], row["group_name"]) for row in customers], [(2, "A 集团")])

    def _enable_claim_keys(self):
        with closing(sqlite3.connect(self.path)) as conn, conn:
            conn.execute("ALTER TABLE member_sales_customers ADD COLUMN customer_key TEXT")
            conn.execute("UPDATE member_sales_customers SET customer_key=customer_name")

    def test_collaboration_requires_review_and_never_grants_price_or_peer_projects(self):
        self._enable_claim_keys()
        private = self.alice.create(101, "原销售项目")
        # A customer picker in another business module can create a duplicate
        # member-specific sales row. It cannot stand in for project approval.
        with closing(sqlite3.connect(self.path)) as conn, conn:
            conn.execute("INSERT INTO member_sales_customers VALUES(202,2,'甲客户','甲客户')")
        with self.assertRaises(ProjectError):
            self.bob.create(202, "不应提前加入")
        with self.assertRaises(ProjectError):
            self.bob.request_join("甲客户", "华东", "  ")
        self.bob.request_join("甲客户", "华东", "对接研发")
        req = self.bob.join_requests()[0]
        self.assertEqual(self.alice.join_requests(), [])
        self.assertEqual(req["status"], "待审批")
        with self.assertRaises(ProjectError):
            self.bob.request_join("甲客户", "华东", "重复")
        with self.assertRaises(ProjectError):
            self.bob.review_join(req["id"], True)
        with self.assertRaises(ProjectError):
            self.bob.create(101, "未批项目")
        with self.assertRaises(ProjectError):
            self.admin.review_join(req["id"], False)
        self.admin.review_join(req["id"], False, "请补充分工")
        self.bob.request_join("甲客户", "华东", "负责新产品验证")
        second = self.bob.join_requests()[0]["id"]
        self.admin.review_join(second, True, "同意独立跟进")
        with self.assertRaises(ProjectError):
            self.admin.review_join(second, False, "重复处理")
        self.assertEqual([r["status"] for r in self.bob.join_requests()], ["已批准","已退回"])
        collab = self.bob.create(101, "协同销售项目")
        self.assertEqual([r["id"] for r in self.alice.overview()[2]], [private])
        self.assertEqual([r["id"] for r in self.bob.overview()[2]], [collab])
        self.assertEqual({r["customer_id"] for r in self.admin.overview()[2]}, {101})
        with self.assertRaises(ProjectError):
            self.bob.history(private)
        with self.assertRaises(ProjectError):
            self.bob.set_customer_group(101,"改集团")
        with closing(sqlite3.connect(self.path)) as conn:
            self.assertEqual(conn.execute("SELECT COUNT(*) FROM member_sales_customers").fetchone()[0],4)

    def test_collaboration_ui_approval_and_authoritative_snapshot(self):
        from streamlit.testing.v1 import AppTest
        self._enable_claim_keys()
        self.alice.overview()
        snap = self._snapshot(self.path.read_bytes(),2)
        def request(method,payload=None):
            if method=="GET":
                return snap
            snap.update(self._snapshot(self._raw(payload),snap["version"]+1))
            return None  # ambiguous ack: recover from the persisted receipt
        self.assertTrue(save_project_to_snapshot(self.bob, lambda s:s.request_join("甲客户","二部","采购窗口"), request))
        path=self.path.with_name("restored-join.sqlite")
        from base64 import b64decode
        raw=b64decode(snap["payload_base64"])
        path.write_bytes(gzip.decompress(raw) if snap.get("payload_encoding")=="gzip" else raw)
        admin_page=AppTest.from_string(
            "import streamlit as st\nfrom project_progress import ProjectStore,render_page\n"
            f"s=ProjectStore({str(path)!r},3)\n"
            "render_page(st,s,write=lambda a:(a(s),True)[1],register_customer=None,join_key=lambda n:n)\n",
            default_timeout=30).run()
        self.assertFalse(admin_page.exception)
        next(b for b in admin_page.button if b.label=="批准协同").click().run()
        self.assertFalse(admin_page.exception)
        self.assertEqual(ProjectStore(path,2).join_requests()[0]["status"],"已批准")
        self.assertIn(101,[r["id"] for r in ProjectStore(path,2).overview()[1]])
        self.assertEqual(self.bob.join_requests(),[])

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

    def test_admin_can_filter_group_across_owners_and_member_can_edit_own_group(self):
        from streamlit.testing.v1 import AppTest

        self.alice.create(101, "集团甲项目")
        self.alice.create(102, "无集团项目")
        self.bob.create(201, "集团乙项目")
        self.alice.set_customer_group(101, "ACME")
        self.bob.set_customer_group(201, "ａｃｍｅ")

        def page_for(member_id):
            return AppTest.from_string(
                "import streamlit as st\n"
                "from project_progress import ProjectStore, render_page\n"
                f"store = ProjectStore({str(self.path)!r}, {member_id}, clock=lambda: {self.now})\n"
                "render_page(st, store, write=lambda action: (action(store), True)[1], register_customer=None)\n",
                default_timeout=30,
            ).run()

        admin_page = page_for(3)
        group = admin_page.selectbox(key="project-progress-3-group")
        self.assertEqual(len(group.options), 2)
        group.select("acme").run()
        self.assertFalse(admin_page.exception)
        cards = next(item.value for item in admin_page.markdown if '<div class="pp-grid"' in item.value)
        self.assertIn("集团甲项目", cards)
        self.assertIn("集团乙项目", cards)
        self.assertNotIn("无集团项目", cards)
        self.assertTrue(any("2 条客户报备" in item.value for item in admin_page.text))

        member_page = page_for(1)
        self.assertFalse(any(item.label == "筛选集团" for item in member_page.selectbox))
        self.assertTrue(any(item.label == "关联客户" for item in member_page.selectbox))
        member_page.selectbox(key="project-progress-1-edit-group-customer").select(101).run()
        next(item for item in member_page.text_input if item.label == "集团名称（选填）").input("新集团")
        next(item for item in member_page.button if item.label == "保存集团").click().run()
        self.assertFalse(member_page.exception)
        self.assertEqual({row["id"]: row["group_name"] for row in self.alice.overview()[1]}[101], "新集团")

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
