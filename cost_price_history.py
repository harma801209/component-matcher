"""Append-only manual versions and read-only uploaded price snapshots (Shanghai time)."""
import json
import re
from datetime import date, datetime, time, timedelta, timezone

PRICE_TZ = timezone(timedelta(hours=8))


def normalize_as_of(value):
    if value is None or value == "":
        return ""
    try:
        if isinstance(value, datetime):
            parsed = value
        elif isinstance(value, date):
            parsed = datetime.combine(value, time(23, 59, 59))
        else:
            text = str(value).strip().replace("/", "-")
            clock = re.search(r"[T ](\d{2}):", text)
            if clock and int(clock.group(1)) > 23:
                raise ValueError("时刻须为 00:00:00 至 23:59:59。")
            parsed = datetime.fromisoformat(text)
            if len(text) == 10:
                parsed = parsed.replace(hour=23, minute=59, second=59)
        if parsed.tzinfo is not None:
            parsed = parsed.astimezone(PRICE_TZ).replace(tzinfo=None)
        return parsed.strftime("%Y-%m-%d %H:%M:%S")
    except (TypeError, ValueError, OverflowError) as exc:
        raise ValueError("成本时间须为有效日期时间（北京时间）。") from exc


def _dict_rows(cursor):
    names = [column[0] for column in cursor.description]
    return [dict(zip(names, row)) for row in cursor.fetchall()]


def record_manual_version(conn, item_id, recorded_at, event="update"):
    rows = _dict_rows(conn.execute("SELECT * FROM cost_price_manual_items WHERE id=?", (item_id,)))
    if not rows:
        return
    row = rows[0]
    conn.execute(
        "INSERT INTO cost_price_manual_versions(item_id,recorded_at,event,snapshot_json) VALUES(?,?,?,?)",
        (item_id, normalize_as_of(recorded_at), event, json.dumps(row, ensure_ascii=False, sort_keys=True)),
    )


def ensure_manual_history(conn, now_text):
    # Additive only: never replace, delete, or change the existing current records.
    conn.execute("""CREATE TABLE IF NOT EXISTS cost_price_manual_versions (
        id INTEGER PRIMARY KEY AUTOINCREMENT, item_id INTEGER NOT NULL,
        recorded_at TEXT NOT NULL, event TEXT NOT NULL, snapshot_json TEXT NOT NULL)""")
    conn.execute("""CREATE INDEX IF NOT EXISTS idx_cost_manual_versions_time
        ON cost_price_manual_versions(item_id,recorded_at,id)""")
    for row in _dict_rows(conn.execute("""SELECT m.* FROM cost_price_manual_items m
        WHERE NOT EXISTS(SELECT 1 FROM cost_price_manual_versions h WHERE h.item_id=m.id)""")):
        observed = row.get("updated_at") or row.get("created_at") or now_text
        try:
            observed = normalize_as_of(observed)
        except ValueError:
            observed = normalize_as_of(now_text)
        record_manual_version(conn, row["id"], observed, "legacy_observation")


def read_price_snapshot(conn, as_of, customer_type="new", customer_key=""):
    cutoff = normalize_as_of(as_of)
    if not cutoff:
        raise ValueError("历史成本查询必须提供时间。")
    versions = _dict_rows(conn.execute("""SELECT * FROM cost_price_lists
        WHERE uploaded_at<>'' AND uploaded_at<=? AND ((customer_type='new' AND customer_key='')
        OR (customer_type=? AND customer_key=?)) ORDER BY uploaded_at DESC,id DESC""",
        (cutoff, customer_type, customer_key)))
    chosen = {}
    for version in versions:
        chosen.setdefault((version["customer_type"], version["customer_key"]), version)
    items = []
    for version in chosen.values():
        items.extend(_dict_rows(conn.execute("""SELECT i.brand,i.model,i.model_clean,i.spec_text,
            i.cost,i.cost_updated_at,i.moq,i.lead_time,i.raw_json,
            l.customer_type AS list_customer_type,l.customer_name AS list_customer_name,
            l.customer_key AS list_customer_key,l.file_name AS list_file_name,
            l.uploaded_at AS snapshot_at,l.id AS snapshot_list_id,i.id AS item_id
            FROM cost_price_items i JOIN cost_price_lists l ON l.id=i.list_id
            WHERE l.id=? ORDER BY i.id ASC""", (version["id"],))))
    events = _dict_rows(conn.execute("""SELECT h.* FROM cost_price_manual_versions h
        WHERE h.recorded_at<=? AND NOT EXISTS (
            SELECT 1 FROM cost_price_manual_versions newer WHERE newer.item_id=h.item_id
            AND newer.recorded_at<=? AND (newer.recorded_at>h.recorded_at
            OR (newer.recorded_at=h.recorded_at AND newer.id>h.id)))""", (cutoff, cutoff)))
    manual = []
    for event in events:
        row = json.loads(event["snapshot_json"])
        scope = (row.get("customer_type", "new"), row.get("customer_key", ""))
        if row.get("active") and scope in {("new", ""), (customer_type, customer_key)}:
            row["snapshot_at"] = event["recorded_at"]
            row["snapshot_version_id"] = event["id"]
            manual.append(row)
    manual.sort(key=lambda row: (row["snapshot_at"], row["snapshot_version_id"]), reverse=True)
    gaps = []
    # Legacy edits before this feature were not versioned. Fail closed rather than
    # silently substituting a workbook price for an unknown former manual override.
    for event in _dict_rows(conn.execute("""SELECT * FROM cost_price_manual_versions
        WHERE event='legacy_observation' AND recorded_at>?""", (cutoff,))):
        row = json.loads(event["snapshot_json"])
        created = row.get("created_at", "")
        try:
            if not created or normalize_as_of(created) <= cutoff:
                gaps.append(event["item_id"])
        except ValueError:
            gaps.append(event["item_id"])
    context = {
        "as_of": cutoff, "versions": [{key: v[key] for key in
            ("id", "file_name", "uploaded_at", "customer_type", "customer_key")} for v in chosen.values()],
        "manual_history_gaps": gaps,
    }
    return ([] if gaps else items), ([] if gaps else manual), context
