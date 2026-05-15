#!/usr/bin/env python3
"""
WF-008: Kanban → SSB Bridge — sync Kanban task events to SSB event bus.
Usage:
  python3 wf-008-kanban-ssb-bridge.py           # Incremental sync
  python3 wf-008-kanban-ssb-bridge.py --dry-run  # Preview
  python3 wf-008-kanban-ssb-bridge.py --full     # Full sync
"""
import hashlib, json, os, sqlite3, sys, time, uuid
from datetime import datetime, timezone, timedelta
from pathlib import Path

ECOS = Path(__file__).resolve().parent.parent
KANBAN_DB = Path(os.path.expanduser("~/.hermes/kanban/boards/ecos/kanban.db"))
SSB_DB = ECOS / "LADS" / "ssb" / "ecos.db"
STATE_FILE = ECOS / "LADS" / "ssb" / ".kanban_bridge_state"
TZ = timezone(timedelta(hours=8), "CST")

EVENT_MAP = {
    "task_created": ("TASK_CREATED", "New task created"),
    "task_started": ("TASK_STARTED", "Task started"),
    "task_completed": ("TASK_COMPLETED", "Task completed"),
    "task_cancelled": ("TASK_CANCELLED", "Task cancelled"),
    "task_archived": ("TASK_ARCHIVED", "Task archived"),
    "task_moved": ("TASK_MOVED", "Task moved"),
    "task_assigned": ("TASK_ASSIGNED", "Task assigned"),
    "comment_added": ("COMMENT_ADDED", "Comment added"),
}
RISK_MAP = {"running": "HIGH", "blocked": "HIGH", "ready": "MED", "done": "LOW", "archived": "LOW"}


def _load_state():
    if STATE_FILE.exists():
        return int(STATE_FILE.read_text().strip() or 0)
    return 0

def _save_state(eid):
    STATE_FILE.write_text(str(eid))

def _next_seq(db):
    return (db.execute("SELECT COALESCE(MAX(seq),0)+1 FROM ssb_events").fetchone()[0])

def _insert_ssb(db, seq, event_type, summary, agent, detail="", risk="LOW"):
    now = datetime.now(TZ).strftime("%Y-%m-%dT%H:%M:%S+08:00")
    eid = str(uuid.uuid4())[:8]
    db.execute("""
        INSERT OR IGNORE INTO ssb_events
        (seq, event_id, timestamp, source_agent, event_type, action,
         payload_json, priority, status, schema_version)
        VALUES (?, ?, ?, 'KANBAN_BRIDGE', ?, ?, ?,
                CASE WHEN ?='HIGH' THEN 10 WHEN ?='MED' THEN 5 ELSE 0 END,
                'active', '1.0')
    """, (seq, eid, now, event_type, summary,
          json.dumps({"detail": detail, "risk": risk}), risk, risk))
    return eid


def sync(dry_run=False, full=False):
    if not KANBAN_DB.exists():
        print(f"❌ Kanban DB not found: {KANBAN_DB}")
        return 1
    SSB_DB.parent.mkdir(parents=True, exist_ok=True)

    last_id = 0 if full else _load_state()
    count = 0
    kdb = sdb = None

    try:
        kdb = sqlite3.connect(str(KANBAN_DB))
        kdb.row_factory = sqlite3.Row

        events = kdb.execute(
            "SELECT id, task_id, kind, payload, created_at "
            "FROM task_events WHERE id > ? ORDER BY id", (last_id,)
        ).fetchall()

        if not events:
            print("✅ No new Kanban events to sync.")
            return 0

        tasks = {r["id"]: r["title"] for r in kdb.execute("SELECT id, title FROM tasks").fetchall()}
        sdb = sqlite3.connect(str(SSB_DB))

        for ev in events:
            eid = ev["id"]; task_id = ev["task_id"]; event = ev["kind"]
            data_raw = ev["payload"]

            event_type, default_summary = EVENT_MAP.get(event, ("SIGNAL", f"Kanban {event}"))
            title = tasks.get(task_id, task_id)
            summary = f"[Kanban] {default_summary}: {title}"

            try:
                data = json.loads(data_raw) if data_raw else {}
            except (json.JSONDecodeError, TypeError):
                data = {}

            detail = json.dumps(data, ensure_ascii=False) if data else ""
            risk = RISK_MAP.get(data.get("to_status", ""), "LOW")

            if dry_run:
                print(f"  [DRY-RUN] id={eid} event={event:12s} task={task_id:14s} summary={summary}")
            else:
                seq = _next_seq(sdb)
                _insert_ssb(sdb, seq, event_type, summary, task_id, detail, risk)
                count += 1

            last_id = max(last_id, eid)

        if not dry_run:
            sdb.commit()
            _save_state(last_id)
            print(f"✅ Synced {count} new Kanban events to SSB (last_id={last_id})")
        else:
            print(f"   Dry-run: {len(events)} events would sync.")

        return 0

    finally:
        for conn in (sdb, kdb):
            if conn:
                try: conn.close()
                except: pass


if __name__ == "__main__":
    dry_run = "--dry-run" in sys.argv
    full = "--full" in sys.argv
    sys.exit(sync(dry_run, full))
