"""Member-scoped customer project tracking. Existing customer records are read-only."""

from contextlib import closing, contextmanager
from datetime import datetime, timedelta, timezone
import base64
import binascii
import gzip
import hashlib
from html import escape
from io import BytesIO
from pathlib import Path
import sqlite3
from tempfile import TemporaryDirectory
import time
from unicodedata import normalize
from uuid import uuid4
import zlib


DAY = 86_400
CHINA = timezone(timedelta(hours=8))
STAGES = ("接洽中", "选型／送样", "客户验证", "商务跟进", "遇到卡点")
ORDERED = "客户已下单"
STOPPED = "已关闭"
LEGACY_DONE = "已完成"
CLOSED = (ORDERED, STOPPED, LEGACY_DONE)
EVENT_LABELS = {
    "created": "新建项目", "quote_request": "登记报价申请", "quoted": "登记已报价",
    "progress": "更新进度", "reminder": "管理员提醒", "ordered": "客户已下单 · 项目闭环",
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
CREATE TABLE IF NOT EXISTS member_customer_project_receipts (
    operation_id TEXT PRIMARY KEY,
    actor_id INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS member_customer_project_groups (
    customer_id INTEGER PRIMARY KEY REFERENCES member_sales_customers(id) ON DELETE CASCADE,
    group_name TEXT NOT NULL DEFAULT ''
);
"""


def _timestamp(value):
    return datetime.fromtimestamp(value, CHINA).strftime("%Y-%m-%d %H:%M") if value is not None else "—"


def _deadline(due, now):
    if due is None:
        return "已结案"
    if now >= due:
        return "已逾期"
    return "24 小时内到期" if due - now <= DAY else "待跟进"


def _group_name(value):
    name = " ".join(value.split())
    if len(name) > 120:
        raise ProjectError("集团名称不能超过 120 字。")
    return name


def _group_key(value):
    return normalize("NFKC", value).casefold()


class ProjectError(ValueError):
    """A validation or permission message safe to show to the user."""


class ProjectStore:
    def __init__(self, path, actor_id, *, clock=time.time, operation_id=None):
        self.path = path
        self.actor_id = int(actor_id)
        self.clock = clock
        self.operation_id = operation_id

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
            if write and self.operation_id is not None:
                conn.execute(
                    "INSERT INTO member_customer_project_receipts(operation_id, actor_id) VALUES (?,?)",
                    (self.operation_id, self.actor_id),
                )

    def overview(self):
        with self._connection() as (conn, admin):
            owner = () if admin else (self.actor_id,)
            scope = "" if admin else " AND m.id=?"
            owner_name = "COALESCE(NULLIF(m.display_name,''),m.username) AS owner_name"
            customers = conn.execute(
                f"""SELECT c.id, c.member_id AS owner_id, c.customer_name,
                           COALESCE(g.group_name,'') AS group_name, {owner_name}
                    FROM member_sales_customers c JOIN members m ON m.id=c.member_id
                    LEFT JOIN member_customer_project_groups g ON g.customer_id=c.id
                    WHERE c.customer_name<>'' {scope}
                    ORDER BY c.customer_name, m.id, c.id""", owner,
            ).fetchall()
            projects = conn.execute(
                f"""SELECT p.*, COALESCE(c.customer_name,p.customer_name) AS visible_customer,
                           COALESCE(g.group_name,'') AS group_name, {owner_name}, m.status AS owner_status,
                           (SELECT e.note FROM member_customer_project_events e
                            WHERE e.project_id=p.id AND e.kind IN ('created','progress','ordered')
                            ORDER BY e.id DESC LIMIT 1) AS latest_progress,
                           (SELECT e.created_at FROM member_customer_project_events e
                            WHERE e.project_id=p.id AND e.kind='ordered'
                            ORDER BY e.id DESC LIMIT 1) AS order_recorded_at,
                           (SELECT e.kind FROM member_customer_project_events e
                            WHERE e.project_id=p.id AND e.kind IN ('quote_request','quoted')
                            ORDER BY e.id DESC LIMIT 1) AS quote_event
                    FROM member_customer_projects p JOIN members m ON m.id=p.owner_id
                    LEFT JOIN member_sales_customers c ON c.id=p.customer_id AND c.member_id=p.owner_id
                    LEFT JOIN member_customer_project_groups g ON g.customer_id=c.id
                    WHERE 1=1 {scope}
                    ORDER BY p.due_at IS NULL, p.due_at, p.id DESC""", owner,
            ).fetchall()
        return admin, [dict(row) for row in customers], [dict(row) for row in projects]

    def _set_group(self, conn, customer_id, name):
        if conn.execute(
            "SELECT 1 FROM member_sales_customers WHERE id=? AND member_id=?",
            (customer_id, self.actor_id),
        ).fetchone() is None:
            raise ProjectError("只能编辑你名下客户的所属集团。")
        conn.execute(
            """INSERT INTO member_customer_project_groups(customer_id,group_name) VALUES (?,?)
               ON CONFLICT(customer_id) DO UPDATE SET group_name=excluded.group_name""",
            (customer_id, name),
        )

    def set_customer_group(self, customer_id, group_name):
        name = _group_name(group_name)
        with self._connection(write=True) as (conn, _):
            self._set_group(conn, customer_id, name)

    def register_customer(self, upsert, group_name=""):
        """Commit the customer record and any supplied group together."""
        name = _group_name(group_name)
        with self._connection(write=True) as (conn, _):
            ok, message, customer = upsert(conn)
            if not ok or customer is None:
                raise ProjectError(message or "未能报备客户。")
            if name:
                self._set_group(conn, customer["id"], name)

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
        if kind not in ("quote_request", "quoted", "progress", "ordered") or not note or len(note) > 1000:
            raise ProjectError("请填写本次事项说明（1–1000 字）。")
        now = int(self.clock())
        with self._connection(write=True) as (conn, _):
            project = self._project(conn, project_id)
            if project["owner_id"] != self.actor_id:
                raise ProjectError("只能更新自己名下的项目。")
            if project["revision"] != revision:
                raise ProjectError("项目已更新，请重新选择后提交。")
            if project["stage"] in CLOSED and not (kind == "ordered" and project["stage"] == LEGACY_DONE):
                raise ProjectError("项目已经结案，不能追加进度。")
            due, quoted, progress = project["due_at"], project["quoted_at"], project["last_progress_at"]
            reminded = project["reminded_due_at"]
            next_stage = project["stage"]
            planned = project["next_action"]
            if kind == "quoted":
                # A new quote may tighten the deadline; it must not erase an overdue obligation.
                due = min(due, now + 7 * DAY)
                quoted = now
            elif kind == "ordered":
                next_stage, progress, planned, due, reminded = ORDERED, now, "", None, None
            elif kind == "progress":
                if stage not in (*STAGES, STOPPED):
                    raise ProjectError("请选择有效的项目阶段；客户已下单请使用首单登记。")
                if stage != STOPPED and not 1 <= len(next_action) <= 300:
                    raise ProjectError("请补充下一步计划（1–300 字）。")
                next_stage, progress = stage, now
                planned = "" if stage == STOPPED else next_action
                due = None if stage == STOPPED else now + (7 if quoted is not None else 14) * DAY
                if stage == STOPPED:
                    reminded = None
            conn.execute(
                """UPDATE member_customer_projects SET stage=?, quoted_at=?, last_progress_at=?,
                   due_at=?, reminded_due_at=?, next_action=?, revision=revision+1 WHERE id=?""",
                (next_stage, quoted, progress, due, reminded, planned, project_id),
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
            if project["stage"] in CLOSED or due is None or due > now or project["owner_status"] != "active":
                raise ProjectError("只有当前有效且逾期的项目可以发送提醒。")
            if project["reminded_due_at"] == due:
                raise ProjectError("这个跟进周期已发过提醒。")
            self._event(conn, project_id, "reminder", project["stage"], note or "请补充项目进度和下一步计划。", now)
            conn.execute("UPDATE member_customer_projects SET reminded_due_at=? WHERE id=?", (due, project_id))


def _verified_snapshot(response):
    if not isinstance(response, dict):
        raise ProjectError("无法读到最新的共享项目资料，未提交保存。")
    limit = 64 * 1024 * 1024
    try:
        version = int(response["version"])
        encoding = response.get("payload_encoding") or "identity"
        packed = base64.b64decode(response["payload_base64"], validate=True)
        if encoding == "gzip":
            with gzip.GzipFile(fileobj=BytesIO(packed)) as archive:
                raw = archive.read(limit + 1)
        elif encoding == "identity":
            raw = packed
        else:
            raise ValueError
        size = int(response.get("uncompressed_size") or 0)
        if (version < 1 or not raw.startswith(b"SQLite format 3\x00")
                or len(raw) > limit or (size and size != len(raw))
                or hashlib.sha256(raw).hexdigest() != response.get("sha256")):
            raise ValueError
    except (KeyError, ValueError, TypeError, EOFError, OSError, binascii.Error, zlib.error) as exc:
        raise ProjectError("无法校验共享项目资料，未提交保存。") from exc
    return version, raw


def _has_receipt(path, operation_id, actor_id):
    uri = path.resolve().as_uri() + "?mode=ro"
    with closing(sqlite3.connect(uri, uri=True)) as conn:
        exists = conn.execute(
            "SELECT 1 FROM sqlite_schema WHERE type='table' AND name='member_customer_project_receipts'"
        ).fetchone()
        return bool(exists and conn.execute(
            "SELECT 1 FROM member_customer_project_receipts WHERE operation_id=? AND actor_id=?",
            (operation_id, actor_id),
        ).fetchone())


def save_project_to_snapshot(store, action, request):
    """Write against the authoritative version; never publish a live local DB."""
    operation_id = uuid4().hex
    with TemporaryDirectory(prefix="project-save-") as folder:
        for attempt in range(3):
            version, base = _verified_snapshot(request("GET"))
            path = Path(folder) / f"attempt-{attempt}.sqlite"
            path.write_bytes(base)
            if _has_receipt(path, operation_id, store.actor_id):
                return True
            with closing(sqlite3.connect(path)) as conn:
                conn.execute("PRAGMA journal_mode=DELETE")
            staged = ProjectStore(path, store.actor_id, clock=store.clock, operation_id=operation_id)
            action(staged)
            raw = path.read_bytes()
            compressed = gzip.compress(raw, compresslevel=6, mtime=0)
            packed, encoding = (compressed, "gzip") if len(compressed) < len(raw) else (raw, "identity")
            if len(raw) > 64 * 1024 * 1024 or len(packed) > 2_000_000:
                raise ProjectError("共享项目存储已达到容量限制，本次没有提交。请联系管理员。")
            digest = hashlib.sha256(raw).hexdigest()
            reply = request("PUT", {
                "expected_version": version, "sha256": digest,
                "payload_base64": base64.b64encode(packed).decode("ascii"),
                "payload_encoding": encoding, "uncompressed_size": len(raw),
            })
            if isinstance(reply, dict) and reply.get("ok") is True and reply.get("sha256") == digest:
                return True
            if isinstance(reply, dict) and reply.get("conflict") is True:
                continue
            # A missing acknowledgement can follow a successful write. Confirm
            # by receipt, even if a different writer has since advanced the snapshot.
            try:
                _, latest = _verified_snapshot(request("GET"))
                check = Path(folder) / "confirmation.sqlite"
                check.write_bytes(latest)
                return _has_receipt(check, operation_id, store.actor_id)
            except (ProjectError, OSError, sqlite3.Error):
                return False
    raise ProjectError("有其他记录正在同步，本次未保存。请稍后再提交。")


WORKSPACE_STYLE = """
<style>
.pp-hero,.pp-metric,.pp-card,.pp-timeline{color:#183253;box-sizing:border-box}
.pp-hero{padding:clamp(19px,3.2vw,38px);border:1px solid #cfdbef;border-radius:20px;
 background:radial-gradient(ellipse at 100% 0%,#dce9ff,transparent 62%),linear-gradient(115deg,#fff,#edf5ff)}
.pp-hero h2{margin:.38em 0 .22em;font-size:clamp(1.75rem,3vw,2.45rem);letter-spacing:-.03em;color:#112b4d}
.pp-hero p{margin:0;color:#3d5476}
.pp-eyebrow,.pp-chip{display:inline-block;border-radius:999px;font-size:.79rem;font-weight:700;
 line-height:1.3;padding:.35rem .66rem;color:#244a85;background:#e6efff;max-width:100%;overflow-wrap:anywhere}
.pp-eyebrow{letter-spacing:.06em}
.pp-metrics,.pp-grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:12px;margin:12px 0 5px}
.pp-grid{grid-template-columns:repeat(2,minmax(0,1fr));margin:4px 0 10px}
.pp-metric,.pp-card{background:#fff;border:1px solid #d6e1f1;border-radius:15px;padding:15px 17px;min-width:0}
.pp-metric dt,.pp-card small,.pp-timeline time{color:#4e6280}
.pp-metric dd{font-size:1.8rem;font-weight:760;line-height:1.25;margin:.3rem 0 0;color:#142f55}
.pp-metric[data-tone="attention"] dd{color:#944400}.pp-metric[data-tone="done"] dd{color:#08624d}
.pp-card{border-left:3px solid #8daff2}
.pp-card[data-tone="attention"]{border-left-color:#cb782a}
.pp-card[data-tone="done"]{border-left-color:#36a08a}
.pp-card[data-tone="neutral"]{border-left-color:#a0aec1}
.pp-card h3{font-size:1.07rem;color:#152d50;margin:.28rem 0 .55rem;overflow-wrap:anywhere}
.pp-card p{margin:.53rem 0 0;overflow-wrap:anywhere}
.pp-card small{display:block;overflow-wrap:anywhere}
.pp-chip + .pp-chip{margin-left:.35rem}
.pp-chip[data-tone="attention"]{background:#fff0db;color:#854204}
.pp-chip[data-tone="done"]{background:#dcf6ee;color:#075f4b}
.pp-chip[data-tone="neutral"]{background:#eaf0f7;color:#465b79}
.pp-card .pp-next{color:#304d77}.pp-grid .pp-next{display:-webkit-box;-webkit-box-orient:vertical;-webkit-line-clamp:2;overflow:hidden}
.pp-timeline{list-style:none;padding:0 0 0 20px;margin:6px 0 12px;border-left:2px solid #d3e2f8}
.pp-timeline li{position:relative;padding:11px 14px;margin:0 0 10px;border:1px solid #d6e1f1;border-radius:12px;background:#fff;overflow-wrap:anywhere}
.pp-timeline li::before{content:"";position:absolute;width:9px;height:9px;left:-27px;top:15px;border:2px solid #6590de;border-radius:50%;background:#fff}
.pp-timeline li[data-order="yes"]::before{background:#19836c;border-color:#19836c}
.pp-timeline time{display:block;font-size:.82rem}
.pp-timeline p{margin:.35rem 0 0;white-space:pre-wrap}
@media(max-width:820px){.pp-metrics{grid-template-columns:repeat(2,minmax(0,1fr))}.pp-grid{grid-template-columns:1fr}}
</style>
"""


def _active_project(row):
    return row["stage"] not in CLOSED and row["due_at"] is not None


def _project_status(row, now):
    if row["stage"] == ORDERED:
        return "已下单闭环", "done"
    if not _active_project(row):
        return ("历史结案 · 未登记下单" if row["stage"] == LEGACY_DONE else "已关闭 · 未登记下单"), "neutral"
    status = _deadline(row["due_at"], now)
    return status, "attention" if status != "待跟进" else "normal"


def _project_card(row, now, *, admin=False, detail=False):
    status, tone = _project_status(row, now)
    customer = escape(row["visible_customer"])
    owner = f" · {escape(row['owner_name'])}" if admin else ""
    group = f" · {escape(row['group_name'])}" if row["group_name"] else ""
    stage = (
        f'<span class="pp-chip" data-tone="neutral">{escape(row["stage"])}</span>'
        if _active_project(row) else ""
    )
    quote = {"quote_request": "已申请报价", "quoted": "已报价"}.get(row["quote_event"], "未报价")
    reminder = " · 已发提醒" if _active_project(row) and row["reminded_due_at"] == row["due_at"] else ""
    deadline = (
        f"下次跟进 {_timestamp(row['due_at'])}{reminder}" if _active_project(row) else
        f"首单登记 {_timestamp(row['order_recorded_at'])}" if row["stage"] == ORDERED else "不再提醒"
    )
    progress = f'<p><strong>最近记录：</strong>{escape(row["latest_progress"] or "—")}</p>' if detail else ""
    next_action = f'<p class="pp-next"><strong>下一步：</strong>{escape(row["next_action"] or "待补充")}</p>' if _active_project(row) else ""
    return (
        f'<article class="pp-card" data-tone="{tone}"><small>{customer}{group}{owner}</small>'
        f'<h3>{escape(row["name"])}</h3><span class="pp-chip" data-tone="{tone}">{status}</span>'
        f'{stage}<p><small>{quote} · {deadline}</small></p>{next_action}{progress}</article>'
    )


def _project_timeline(events):
    items = []
    for event in events:
        ordered = "yes" if event["kind"] == "ordered" else "no"
        description = f'<p>{escape(event["note"])}</p>' if event["note"] else ""
        action = f'<p><strong>下一步：</strong>{escape(event["next_action"])}</p>' if event["next_action"] else ""
        label = EVENT_LABELS.get(event["kind"], "项目记录")
        items.append(
            f'<li data-order="{ordered}"><time>{_timestamp(event["created_at"])} · 北京时间</time>'
            f'<strong>{label}</strong> · {escape(event["stage"])}{description}{action}</li>'
        )
    return '<ol class="pp-timeline" aria-label="项目时间线">' + "".join(items) + "</ol>"


def render_page(st, store, *, write, register_customer):
    """The app supplies the verified actor and the existing snapshot sync boundary."""
    prefix = f"project-progress-{store.actor_id}"
    focus_order = st.session_state.pop(prefix + "-focus-order", None)
    if focus_order is not None:
        st.session_state[prefix + "-scope"] = "已下单闭环"
        st.session_state[prefix + "-selected"] = focus_order
    st.markdown(WORKSPACE_STYLE, unsafe_allow_html=True)
    notice = st.session_state.pop(prefix + "-success", None)
    if notice:
        st.success(notice)

    def submit(action, success, *, order_project=None):
        try:
            synced = write(action)
        except ProjectError as exc:
            st.warning(str(exc))
            return
        if not synced:
            st.error("保存未获服务器确认。请稍后刷新核对记录，再决定是否重新提交。")
            return
        st.session_state[prefix + "-success"] = success
        if order_project is not None:
            st.session_state[prefix + "-focus-order"] = order_project
        st.rerun()

    def render_order_form(project_id, revision):
        st.caption("客户已经实际下单时登记。报价、送样或下单意向不算闭环。登记后将停止跟进提醒。")
        with st.form(f"{prefix}-order-{project_id}-{revision}"):
            order_note = st.text_area("首单说明", max_chars=1000, placeholder="例如：客户已发首张订单，订单号 PO-123。")
            confirmed = st.checkbox("我确认客户已开始下单")
            if st.form_submit_button("确认下单并闭环", type="primary"):
                if not confirmed:
                    st.warning("请先确认客户已开始下单。")
                else:
                    submit(lambda target: target.record(project_id, revision, "ordered", order_note),
                           "首单已登记，项目已闭环，不再发送跟进提醒。", order_project=project_id)

    admin, customers, projects = store.overview()
    now = int(store.clock())
    own_customers = [row for row in customers if row["owner_id"] == store.actor_id]
    active = [row for row in projects if _active_project(row)]
    overdue = [row for row in active if _deadline(row["due_at"], now) == "已逾期"]
    reminders = [row for row in overdue if row["reminded_due_at"] == row["due_at"]]
    stats = (
        ("报备客户", len(customers), "normal"), ("跟进中", len(active), "normal"),
        ("已逾期", len(overdue), "attention"),
        ("已下单闭环", sum(row["stage"] == ORDERED for row in projects), "done"),
    )
    scope_label = "团队总览" if admin else "我的项目"
    metrics = "".join(f'<div class="pp-metric" data-tone="{tone}"><dt>{label}</dt><dd>{value}</dd></div>'
                      for label, value, tone in stats)
    st.markdown(
        f'<section class="pp-hero" aria-labelledby="pp-heading"><span class="pp-eyebrow">项目工作台 · {scope_label}</span>'
        '<h2 id="pp-heading">项目跟进</h2><p>从客户接洽、选型验证，到首单闭环。</p></section>'
        f'<dl class="pp-metrics" aria-label="项目概览">{metrics}</dl>', unsafe_allow_html=True,
    )
    st.caption("未报价每 14 天更新，已报价每 7 天更新。报价申请不等于已报价，重复报价不能延长已到期的跟进。")
    if reminders and not admin:
        st.warning("管理员已提醒补进度。打开对应项目可查看提醒说明。")
        st.text("、".join(row["name"] for row in reminders[:5]))
    elif reminders:
        st.caption(f"当前有 {len(reminders)} 个逾期项目已发送提醒。")
    with st.expander("报备客户／手动新建项目"):
        st.markdown("#### 第一步 · 报备客户")
        st.caption("填写客户公司全名。已由其他会员报备的客户不能重复报备；自己已报备的客户可直接建项目。")
        with st.form(prefix + "-customer"):
            company = st.text_input("客户公司全名", max_chars=120)
            group_name = st.text_input("所属集团（选填）", max_chars=120,
                                       placeholder="无集团归属可留空")
            if st.form_submit_button("报备客户"):
                try:
                    ok, message, _ = register_customer(company, group_name)
                    if ok:
                        st.session_state[prefix + "-success"] = "客户已报备，可在清单中添加项目。"
                        st.rerun()
                    else:
                        st.warning(message)
                except ProjectError as exc:
                    st.warning(str(exc))
        st.markdown("#### 第二步 · 手动新建项目")
        if own_customers:
            choices = {row["id"]: row["customer_name"] for row in own_customers}
            with st.form(prefix + "-new"):
                customer_id = st.selectbox("关联客户", list(choices), format_func=choices.__getitem__)
                name = st.text_input("项目名称", max_chars=120)
                note = st.text_area("项目背景／当前情况", max_chars=1000)
                next_action = st.text_input("下一步计划（可选）", max_chars=300)
                quote_request = st.checkbox("同时登记报价申请")
                if st.form_submit_button("保存新项目", type="primary"):
                    submit(lambda target: target.create(customer_id, name, note, quote_request, next_action), "项目已保存。")
        else:
            st.caption("报备客户后即可添加项目。")

    if own_customers:
        with st.expander("补填／修改客户集团"):
            by_id = {row["id"]: row for row in own_customers}
            edit_id = st.selectbox("选择客户", list(by_id), key=prefix + "-edit-group-customer",
                                   format_func=lambda key: by_id[key]["customer_name"])
            with st.form(f"{prefix}-edit-group-{edit_id}"):
                group_name = st.text_input("集团名称（选填）", value=by_id[edit_id]["group_name"],
                                           max_chars=120, help="留空并保存可取消该客户的集团归属。")
                if st.form_submit_button("保存集团"):
                    submit(lambda target: target.set_customer_group(edit_id, group_name), "客户集团资料已保存。")

    if not customers and not projects:
        st.info("暂无客户或项目。已报备的客户会自动出现在这里。")
        return

    st.subheader("客户与项目")
    scope = st.radio("项目状态", ("跟进中", "已下单闭环", "其他结案", "全部项目"),
                     horizontal=True, key=prefix + "-scope")
    owners = {row["owner_id"]: row["owner_name"] for row in [*customers, *projects]}
    if admin:
        owner_col, group_col, customer_col, search_col = st.columns([1, 1.15, 1.15, 1.4])
        selected_owner = owner_col.selectbox(
            "负责会员", [None, *sorted(owners)], key=prefix + "-owner",
            format_func=lambda key: "所有会员" if key is None else f"{owners[key]}（#{key}）",
        )
        groups = {}
        for row in customers:
            if row["group_name"] and (selected_owner is None or row["owner_id"] == selected_owner):
                groups.setdefault(_group_key(row["group_name"]), row["group_name"])
        selected_group = group_col.selectbox(
            "筛选集团", [None, *sorted(groups)], key=prefix + "-group",
            format_func=lambda key: "所有集团" if key is None else groups[key],
        )
    else:
        customer_col, search_col = st.columns(2)
        selected_owner = None
        selected_group = None

    def in_customer_scope(row):
        return ((selected_owner is None or row["owner_id"] == selected_owner)
                and (selected_group is None or _group_key(row["group_name"]) == selected_group))

    customer_labels = {
        (row["owner_id"], row["id"]): row["customer_name"] for row in customers
        if in_customer_scope(row)
    }
    customer_labels.update({
        (row["owner_id"], row["customer_id"]): row["visible_customer"] for row in projects
        if in_customer_scope(row)
    })
    customer_groups = {(row["owner_id"], row["id"]): row["group_name"] for row in customers}
    customer = customer_col.selectbox(
        "筛选客户", [None, *customer_labels], key=prefix + "-filter",
        format_func=lambda key: "所有客户" if key is None else (
            f"{customer_labels[key]} · {owners[key[0]]}（#{key[0]}）" if admin else customer_labels[key]
        ),
    )
    query = search_col.text_input("查找项目", placeholder="输入项目名或客户名", key=prefix + "-query").strip().casefold()
    selected_customers = [key for key in customer_labels if customer is None or key == customer]
    if selected_group is not None:
        grouped = [row for row in projects if in_customer_scope(row)]
        group_active = sum(_active_project(row) for row in grouped)
        group_ordered = sum(row["stage"] == ORDERED for row in grouped)
        st.text(f"{groups[selected_group]} · {len(customer_labels)} 条客户报备 · "
                f"{group_active} 个跟进中 · {group_ordered} 个已下单闭环")
    if selected_customers:
        counts = {}
        for row in projects:
            key = (row["owner_id"], row["customer_id"])
            current, ordered = counts.get(key, (0, 0))
            counts[key] = current + _active_project(row), ordered + (row["stage"] == ORDERED)
        with st.expander(f"查看客户清单（{len(selected_customers)} 家）", expanded=not projects):
            st.dataframe([
                {"客户": customer_labels[key], "所属集团": customer_groups.get(key) or "—",
                 **({"负责会员": owners[key[0]]} if admin else {}),
                 "跟进中": counts.get(key, (0, 0))[0], "已下单闭环": counts.get(key, (0, 0))[1]}
                for key in selected_customers
            ], hide_index=True)
    only_overdue = scope in ("跟进中", "全部项目") and st.checkbox("仅看逾期项目", key=prefix + "-overdue")
    visible_keys = set(selected_customers)

    def in_scope(row):
        if scope == "跟进中":
            return _active_project(row)
        if scope == "已下单闭环":
            return row["stage"] == ORDERED
        if scope == "其他结案":
            return not _active_project(row) and row["stage"] != ORDERED
        return True

    visible = {row["id"]: row for row in projects
               if (row["owner_id"], row["customer_id"]) in visible_keys
               and in_scope(row)
               and (not query or query in row["name"].casefold() or query in row["visible_customer"].casefold())
               and (not only_overdue or (_active_project(row) and _deadline(row["due_at"], now) == "已逾期"))}
    if not visible:
        st.info("当前筛选下没有项目。")
        return
    rows = list(visible.values())
    page_size = 8
    pages = (len(rows) + page_size - 1) // page_size
    page = st.selectbox("项目列表页", range(1, pages + 1), key=prefix + "-page") if pages > 1 else 1
    offset = max(page - 1, 0) * page_size
    st.caption(f"共 {len(rows)} 个项目 · 显示 {offset + 1}–{min(offset + page_size, len(rows))} 个")
    st.markdown(
        '<div class="pp-grid" aria-label="项目清单">'
        + "".join(_project_card(row, now, admin=admin) for row in rows[offset:offset + page_size]) + "</div>",
        unsafe_allow_html=True,
    )
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
    st.markdown(_project_card(row, now, admin=admin, detail=True), unsafe_allow_html=True)
    if row["owner_id"] == store.actor_id and _active_project(row):
        follow_tab, order_tab = st.tabs(("更新跟进", "首单闭环"))
        with follow_tab:
            kind = st.selectbox("本次事项", ["progress", "quote_request", "quoted"],
                                format_func=EVENT_LABELS.__getitem__, key=f"{prefix}-kind-{project_id}")
            with st.form(f"{prefix}-record-{project_id}-{revision}-{kind}"):
                current = STAGES.index(row["stage"]) if row["stage"] in STAGES else 0
                stage = st.selectbox("当前阶段", (*STAGES, STOPPED), index=current,
                                     format_func=lambda value: "关闭项目（不计入下单闭环）" if value == STOPPED else value
                                     ) if kind == "progress" else None
                note = st.text_area("本次进展（可写遇到的卡点）" if kind == "progress" else "报价事项说明", max_chars=1000)
                next_action = st.text_input("下一步计划（关闭项目无需填写）", value=row["next_action"],
                                            max_chars=300) if kind == "progress" else ""
                if kind == "quote_request":
                    st.caption("这是站内申请记录，不会自动向客户发报价。")
                if st.form_submit_button("保存跟进", type="primary"):
                    submit(lambda target: target.record(project_id, revision, kind, note, stage, next_action), "项目记录已保存。")
        with order_tab:
            render_order_form(project_id, revision)
    elif row["owner_id"] == store.actor_id and row["stage"] == LEGACY_DONE:
        with st.expander("补登历史首单"):
            render_order_form(project_id, revision)
    if admin and row["owner_status"] == "active" and _active_project(row) and _deadline(row["due_at"], now) == "已逾期":
        if row["reminded_due_at"] == row["due_at"]:
            st.caption("本轮已发送站内提醒。")
        else:
            with st.form(f"{prefix}-remind-{project_id}-{revision}"):
                note = st.text_input("提醒说明（可选）", max_chars=500)
                if st.form_submit_button("发送站内提醒"):
                    submit(lambda target: target.remind(project_id, revision, note), "已向该会员发送站内提醒。")
    st.markdown("#### 项目时间线")
    st.markdown(_project_timeline(store.history(project_id)), unsafe_allow_html=True)
