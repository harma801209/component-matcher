"""Member-scoped customer project tracking. Existing customer records are read-only."""

from contextlib import closing, contextmanager
from datetime import datetime, timedelta, timezone
import sqlite3
import time


DAY = 86_400
CHINA = timezone(timedelta(hours=8))
STAGES = ("接洽中", "选型／送样", "客户验证", "商务跟进", "遇到卡点", "已完成", "已关闭")
CLOSED = STAGES[-2:]
EVENT_LABELS = {
    "created": "新建项目", "quote_request": "登记报价申请", "quoted": "登记已报价",
    "progress": "更新进度", "reminder": "管理员提醒",
}
SCHEMA = """
CREATE TABLE IF NOT EXISTS member_customer_projects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    owner_id INTEGER NOT NULL,
    customer_id INTEGER NOT NULL,
    customer_name TEXT NOT NULL,
    name TEXT NOT NULL,
    name_key TEXT NOT NULL,
    stage TEXT NOT NULL,
    next_action TEXT NOT NULL DEFAULT '',
    created_at INTEGER NOT NULL,
    quoted_at INTEGER,
    last_progress_at INTEGER,
    due_at INTEGER,
    reminded_due_at INTEGER,
    revision INTEGER NOT NULL DEFAULT 0,
    UNIQUE(owner_id, customer_id, name_key)
);
CREATE INDEX IF NOT EXISTS project_progress_owner_due
    ON member_customer_projects(owner_id, due_at);
CREATE TABLE IF NOT EXISTS member_customer_project_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL REFERENCES member_customer_projects(id),
    actor_id INTEGER NOT NULL,
    kind TEXT NOT NULL,
    stage TEXT NOT NULL,
    note TEXT NOT NULL,
    next_action TEXT NOT NULL DEFAULT '',
    created_at INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS project_progress_history
    ON member_customer_project_events(project_id, id DESC);
"""


def _timestamp(value):
    return datetime.fromtimestamp(value, CHINA).strftime("%Y-%m-%d %H:%M") if value is not None else "—"


def _deadline(due, now):
    if due is None:
        return "已结案"
    if now >= due:
        return "已逾期"
    return "24 小时内到期" if due - now <= DAY else "待跟进"


class ProjectError(ValueError):
    """A validation or permission message safe to show to the user."""


class ProjectStore:
    def __init__(self, path, actor_id, *, clock=time.time):
        self.path = path
        self.actor_id = int(actor_id)
        self.clock = clock

    @contextmanager
    def _connection(self, write=False):
        with closing(sqlite3.connect(self.path, timeout=15)) as conn, conn:
            conn.row_factory = sqlite3.Row
            actor = conn.execute(
                "SELECT id, role FROM members WHERE id=? AND status='active'",
                (self.actor_id,),
            ).fetchone()
            if actor is None:
                raise ProjectError("当前会员不可用，请重新登录。")
            conn.executescript(SCHEMA)
            if write:
                conn.execute("BEGIN IMMEDIATE")
                actor = conn.execute(
                    "SELECT id, role FROM members WHERE id=? AND status='active'",
                    (self.actor_id,),
                ).fetchone()
                if actor is None:
                    raise ProjectError("当前会员不可用，请重新登录。")
            yield conn, str(actor["role"]).strip().lower() == "admin"

    def overview(self):
        with self._connection() as (conn, admin):
            owner = () if admin else (self.actor_id,)
            scope = "" if admin else " AND m.id=?"
            owner_name = "COALESCE(NULLIF(m.display_name,''),m.username) AS owner_name"
            customers = conn.execute(
                f"""SELECT c.id, c.member_id AS owner_id, c.customer_name, {owner_name}
                    FROM member_sales_customers c JOIN members m ON m.id=c.member_id
                    WHERE c.customer_name<>'' {scope}
                    ORDER BY c.customer_name, m.id, c.id""", owner,
            ).fetchall()
            projects = conn.execute(
                f"""SELECT p.*, COALESCE(c.customer_name,p.customer_name) AS visible_customer,
                           {owner_name}, m.status AS owner_status,
                           (SELECT e.note FROM member_customer_project_events e
                            WHERE e.project_id=p.id AND e.kind IN ('created','progress')
                            ORDER BY e.id DESC LIMIT 1) AS latest_progress,
                           (SELECT e.kind FROM member_customer_project_events e
                            WHERE e.project_id=p.id AND e.kind IN ('quote_request','quoted')
                            ORDER BY e.id DESC LIMIT 1) AS quote_event
                    FROM member_customer_projects p JOIN members m ON m.id=p.owner_id
                    LEFT JOIN member_sales_customers c ON c.id=p.customer_id AND c.member_id=p.owner_id
                    WHERE 1=1 {scope}
                    ORDER BY p.due_at IS NULL, p.due_at, p.id DESC""", owner,
            ).fetchall()
        return admin, [dict(row) for row in customers], [dict(row) for row in projects]

    def history(self, project_id):
        with self._connection() as (conn, admin):
            row = self._project(conn, project_id)
            if row["owner_id"] != self.actor_id and not admin:
                raise ProjectError("此项目不可查看。")
            return [dict(event) for event in conn.execute(
                """SELECT kind, stage, note, next_action, created_at FROM member_customer_project_events
                   WHERE project_id=? ORDER BY id DESC""", (project_id,),
            )]

    def _project(self, conn, project_id):
        row = conn.execute(
            """SELECT p.*, m.status AS owner_status FROM member_customer_projects p
               JOIN members m ON m.id=p.owner_id WHERE p.id=?""", (project_id,),
        ).fetchone()
        if row is None:
            raise ProjectError("此项目不可查看。")
        return row

    def _event(self, conn, project_id, kind, stage, note, now, next_action=""):
        conn.execute(
            """INSERT INTO member_customer_project_events
               (project_id, actor_id, kind, stage, note, created_at, next_action)
               VALUES (?,?,?,?,?,?,?)""",
            (project_id, self.actor_id, kind, stage, note, now, next_action),
        )

    def create(self, customer_id, name, note="", quote_request=False, next_action=""):
        name = " ".join(name.split())
        note = note.strip()
        next_action = next_action.strip()
        if not name or len(name) > 120 or len(note) > 1000 or len(next_action) > 300:
            raise ProjectError("请填写项目名称（最多 120 字），说明最多 1000 字，下一步最多 300 字。")
        now = int(self.clock())
        with self._connection(write=True) as (conn, _):
            customer = conn.execute(
                "SELECT customer_name FROM member_sales_customers WHERE id=? AND member_id=?",
                (customer_id, self.actor_id),
            ).fetchone()
            if customer is None:
                raise ProjectError("请先报备该客户，或选择你名下的客户。")
            result = conn.execute(
                """INSERT INTO member_customer_projects
                   (owner_id, customer_id, customer_name, name, name_key, stage, created_at, due_at, next_action)
                   VALUES (?,?,?,?,?,?,?,?,?) ON CONFLICT(owner_id,customer_id,name_key) DO NOTHING""",
                (self.actor_id, customer_id, customer["customer_name"], name,
                 name.casefold(), STAGES[0], now, now + 14 * DAY, next_action),
            )
            if not result.rowcount:
                raise ProjectError("该客户已有同名项目，请打开原项目更新。")
            project_id = result.lastrowid
            self._event(conn, project_id, "created", STAGES[0], note, now, next_action)
            if quote_request:
                self._event(conn, project_id, "quote_request", STAGES[0], "", now)
            return project_id

    def record(self, project_id, revision, kind, note, stage=None, next_action=""):
        note = note.strip()
        next_action = next_action.strip()
        if kind not in ("quote_request", "quoted", "progress") or not note or len(note) > 1000:
            raise ProjectError("请填写本次事项说明（1–1000 字）。")
        now = int(self.clock())
        with self._connection(write=True) as (conn, _):
            project = self._project(conn, project_id)
            if project["owner_id"] != self.actor_id:
                raise ProjectError("只能更新自己名下的项目。")
            if project["revision"] != revision:
                raise ProjectError("项目已更新，请重新选择后提交。")
            if project["stage"] in CLOSED:
                raise ProjectError("项目已经结案，不能追加进度。")
            due, quoted, progress = project["due_at"], project["quoted_at"], project["last_progress_at"]
            next_stage = project["stage"]
            planned = project["next_action"]
            if kind == "quoted":
                # A new quote may tighten the deadline; it must not erase an overdue obligation.
                due = min(due, now + 7 * DAY)
                quoted = now
            elif kind == "progress":
                if stage not in STAGES:
                    raise ProjectError("请选择有效的项目阶段。")
                if stage not in CLOSED and not 1 <= len(next_action) <= 300:
                    raise ProjectError("请补充下一步计划（1–300 字）。")
                next_stage, progress = stage, now
                planned = "" if stage in CLOSED else next_action
                due = None if stage in CLOSED else now + (7 if quoted is not None else 14) * DAY
            conn.execute(
                """UPDATE member_customer_projects SET stage=?, quoted_at=?, last_progress_at=?,
                   due_at=?, next_action=?, revision=revision+1 WHERE id=?""",
                (next_stage, quoted, progress, due, planned, project_id),
            )
            self._event(conn, project_id, kind, next_stage, note, now, planned if kind == "progress" else "")

    def remind(self, project_id, revision, note=""):
        note = note.strip()
        if len(note) > 500:
            raise ProjectError("提醒说明最多 500 字。")
        now = int(self.clock())
        with self._connection(write=True) as (conn, admin):
            if not admin:
                raise ProjectError("只有管理员可以发送提醒。")
            project = self._project(conn, project_id)
            due = project["due_at"]
            if project["revision"] != revision:
                raise ProjectError("项目已更新，请重新查看。")
            if due is None or due > now or project["owner_status"] != "active":
                raise ProjectError("只有当前有效且逾期的项目可以发送提醒。")
            if project["reminded_due_at"] == due:
                raise ProjectError("这个跟进周期已发过提醒。")
            self._event(conn, project_id, "reminder", project["stage"], note or "请补充项目进度和下一步计划。", now)
            conn.execute("UPDATE member_customer_projects SET reminded_due_at=? WHERE id=?", (due, project_id))


def render_page(st, store, *, write, register_customer):
    """The app supplies the verified actor and the existing snapshot sync boundary."""
    prefix = f"project-progress-{store.actor_id}"
    notice = st.session_state.pop(prefix + "-success", None)
    if notice:
        st.success(notice)

    def submit(action, success):
        try:
            synced = write(action)
        except ProjectError as exc:
            st.warning(str(exc))
            return
        if not synced:
            st.error("保存未获服务器确认。请稍后刷新核对记录，再决定是否重新提交。")
            return
        st.session_state[prefix + "-success"] = success
        st.rerun()

    admin, customers, projects = store.overview()
    now = int(store.clock())
    own_customers = [row for row in customers if row["owner_id"] == store.actor_id]
    overdue = [row for row in projects if _deadline(row["due_at"], now) == "已逾期"]
    reminders = [row for row in overdue if row["reminded_due_at"] == row["due_at"]]
    st.caption("未报价项目每 14 天更新；登记已报价后每 7 天更新。报价申请不等于已报价，已到期的进度不能靠再次报价延期。")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("报备客户", len(customers))
    c2.metric("跟进中项目", sum(row["due_at"] is not None for row in projects))
    c3.metric("逾期项目", len(overdue))
    c4.metric("当前已提醒" if admin else "待处理提醒", len(reminders))
    if reminders and not admin:
        st.warning("管理员已提醒补进度。打开对应项目可查看提醒说明。")
        st.text("、".join(row["name"] for row in reminders[:5]))
    with st.expander("报备客户／新建项目"):
        with st.form(prefix + "-customer"):
            company = st.text_input("客户公司全名", max_chars=120)
            if st.form_submit_button("报备客户"):
                try:
                    ok, message, _ = register_customer(company)
                    if ok:
                        st.session_state[prefix + "-success"] = "客户已报备，可在清单中添加项目。"
                        st.rerun()
                    else:
                        st.warning(message)
                except ProjectError as exc:
                    st.warning(str(exc))
        if own_customers:
            choices = {row["id"]: row["customer_name"] for row in own_customers}
            with st.form(prefix + "-new"):
                customer_id = st.selectbox("所属客户", list(choices), format_func=choices.__getitem__)
                name = st.text_input("项目名称", max_chars=120)
                note = st.text_area("项目背景／当前情况", max_chars=1000)
                next_action = st.text_input("下一步计划（可选）", max_chars=300)
                quote_request = st.checkbox("同时登记报价申请")
                if st.form_submit_button("保存新项目", type="primary"):
                    submit(lambda: store.create(customer_id, name, note, quote_request, next_action), "项目已保存。")
        else:
            st.caption("报备客户后即可添加项目。")

    if not customers and not projects:
        st.info("暂无客户或项目。已报备的客户会自动出现在这里。")
        return

    owners = {row["owner_id"]: row["owner_name"] for row in [*customers, *projects]}
    selected_owner = st.selectbox("负责会员", [None, *sorted(owners)], key=prefix + "-owner",
                                  format_func=lambda key: "所有会员" if key is None else f"{owners[key]}（#{key}）") if admin else None
    customer_labels = {
        (row["owner_id"], row["id"]): row["customer_name"] for row in customers
        if selected_owner is None or row["owner_id"] == selected_owner
    }
    customer_labels.update({
        (row["owner_id"], row["customer_id"]): row["visible_customer"] for row in projects
        if selected_owner is None or row["owner_id"] == selected_owner
    })
    st.subheader("客户清单与项目")
    customer = st.selectbox(
        "筛选客户", [None, *customer_labels], key=prefix + "-filter",
        format_func=lambda key: "所有客户" if key is None else (
            f"{customer_labels[key]} · {owners[key[0]]}（#{key[0]}）" if admin else customer_labels[key]
        ),
    )
    selected_customers = [key for key in customer_labels if customer is None or key == customer]
    if selected_customers:
        counts = {}
        for row in projects:
            key = (row["owner_id"], row["customer_id"])
            counts[key] = counts.get(key, 0) + 1
        with st.expander(f"查看客户清单（{len(selected_customers)} 家）", expanded=not projects):
            st.dataframe([
                {"客户": customer_labels[key], **({"负责会员": owners[key[0]]} if admin else {}),
                 "项目数": counts.get(key, 0)} for key in selected_customers
            ], hide_index=True)
    only_overdue = st.checkbox("仅看逾期项目", key=prefix + "-overdue")
    visible_keys = set(selected_customers)
    visible = {row["id"]: row for row in projects
               if (row["owner_id"], row["customer_id"]) in visible_keys
               and (not only_overdue or _deadline(row["due_at"], now) == "已逾期")}
    if not visible:
        st.info("当前筛选下没有项目。")
        return
    st.dataframe([
        {"客户": row["visible_customer"], **({"负责会员": row["owner_name"]} if admin else {}),
         "项目": row["name"], "阶段": row["stage"],
         "最近进展": row["latest_progress"] or "—", "下一步": row["next_action"] or "—",
         "最近更新": _timestamp(row["last_progress_at"]), "下次更新期限": _timestamp(row["due_at"]),
         "跟进状态": _deadline(row["due_at"], now),
         "报价": {"quote_request": "已申请", "quoted": "已报价"}.get(row["quote_event"], "未报价"),
         "提醒": "已提醒" if row["due_at"] is not None and row["due_at"] == row["reminded_due_at"] else "—"}
        for row in visible.values()
    ], hide_index=True)
    project_id = st.selectbox(
        "打开项目", [None, *visible], key=prefix + "-selected",
        format_func=lambda key: "选择项目查看时间线" if key is None else
        f"{visible[key]['visible_customer']} · {visible[key]['name']}（#{key}）",
    )
    if project_id not in visible:
        return
    row = visible[project_id]
    revision = row["revision"]
    st.subheader("项目详情")
    st.text(row["name"])
    if row["owner_id"] == store.actor_id and row["due_at"] is not None:
        kind = st.selectbox("本次事项", ["progress", "quote_request", "quoted"],
                            format_func=EVENT_LABELS.__getitem__, key=f"{prefix}-kind-{project_id}")
        with st.form(f"{prefix}-record-{project_id}-{revision}-{kind}"):
            stage = st.selectbox("当前阶段", STAGES, index=STAGES.index(row["stage"])) if kind == "progress" else None
            note = st.text_area("本次进展（可写遇到的卡点）" if kind == "progress" else "报价事项说明", max_chars=1000)
            next_action = st.text_input("下一步计划（结案无需填写）", value=row["next_action"], max_chars=300) if kind == "progress" else ""
            if kind == "quote_request":
                st.caption("这是站内申请记录，不会自动向客户发报价。")
            if st.form_submit_button("保存记录", type="primary"):
                submit(lambda: store.record(project_id, revision, kind, note, stage, next_action), "项目记录已保存。")
    if admin and row["owner_status"] == "active" and _deadline(row["due_at"], now) == "已逾期":
        if row["reminded_due_at"] == row["due_at"]:
            st.caption("本轮已发送站内提醒。")
        else:
            with st.form(f"{prefix}-remind-{project_id}-{revision}"):
                note = st.text_input("提醒说明（可选）", max_chars=500)
                if st.form_submit_button("发送站内提醒"):
                    submit(lambda: store.remind(project_id, revision, note), "已向该会员发送站内提醒。")
    st.markdown("#### 项目时间线")
    st.dataframe([
        {"时间（北京时间）": _timestamp(event["created_at"]), "事项": EVENT_LABELS[event["kind"]],
         "阶段": event["stage"], "说明": event["note"] or "—", "下一步": event["next_action"] or "—"}
        for event in store.history(project_id)
    ], hide_index=True)
