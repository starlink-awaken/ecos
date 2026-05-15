#!/usr/bin/env python3
"""
WF-008: Kanban → SSB 事件桥接

从 Kanban DB 读取未同步的事件，写入 eCOS SSB。
可 cron 定时执行（建议每5分钟）。

Usage:
  python3 wf-008-kanban-ssb-bridge.py          # 同步增量
  python3 wf-008-kanban-ssb-bridge.py --full   # 全量同步（含历史）
  python3 wf-008-kanban-ssb-bridge.py --dry-run # 预览不下发
"""

import sqlite3, json, hashlib, os, sys, time
from pathlib import Path
from datetime import datetime, timezone, timedelta

ECOS_ROOT = Path(__file__).resolve().parent.parent
SSB_DB = ECOS_ROOT / "LADS" / "ssb" / "ecos.db"
KANBAN_DB = Path.home() / ".hermes" / "kanban" / "boards" / "ecos" / "kanban.db"
STATE_FILE = ECOS_ROOT / "LADS" / "ssb" / ".kanban_bridge_state"

# 时区
TZ = timezone(timedelta(hours=8))

# ─── 事件类型映射 ─────────────────────────────

EVENT_MAP = {
    "created":    ("STATE_CHANGE", "Kanban task created"),
    "promoted":   ("STATE_CHANGE", "Kanban task promoted"),
    "claimed":    ("ACTION_START", "Kanban task claimed"),
    "completed":  ("ACTION_RESULT", "Kanban task completed"),
    "blocked":    ("SIGNAL", "Kanban task blocked"),
    "unblocked":  ("SIGNAL", "Kanban task unblocked"),
    "commented":  ("PROPOSAL", "Kanban comment"),
    "archived":   ("STATE_CHANGE", "Kanban task archived"),
}

RISK_MAP = {
    "ready":    "LOW",
    "todo":     "LOW",
    "running":  "MED",
    "blocked":  "MED",
    "done":     "LOW",
    "triage":   "LOW",
}

def _load_state():
    """Load last-synced event ID."""
    if STATE_FILE.exists():
        return int(STATE_FILE.read_text().strip())
    return 0

def _save_state(eid: int):
    STATE_FILE.write_text(str(eid))

def _next_seq(db):
    """Generate next SSB seq number."""
    row = db.execute("SELECT COALESCE(MAX(seq), 0) + 1 FROM ssb_events").fetchone()
    return row[0]

def _insert_ssb(db, seq, event_type, summary, agent, detail="", risk="LOW"):
    """Insert SSB event."""
    now = datetime.now(TZ).strftime("%Y-%m-%dT%H:%M:%S+08:00")
    eid = hashlib.sha256(f"{seq}|{now}|{summary}".encode()).hexdigest()[:16]
    db.execute("""
        INSERT OR IGNORE INTO ssb_events
        (id, seq, timestamp, session_id, source_agent, source_instance,
         target_scope, event_type, summary, detail, risk_level, payload_json)
        VALUES (?, ?, ?, '', 'KANBAN_BRIDGE', 'WF-008', 'ALL', ?, ?, ?, ?, '{}')
    """, (eid, seq, now, event_type, summary, detail, risk))
    return eid

def sync(dry_run=False, full=False):
    """Sync unsynced Kanban events to SSB."""
    if not KANBAN_DB.exists():
        print(f"❌ Kanban DB not found: {KANBAN_DB}")
        return 1
    if not SSB_DB.parent.exists():
        SSB_DB.parent.mkdir(parents=True, exist_ok=True)

    last_id = 0 if full else _load_state()
    count = 0

    kdb = sqlite3.connect(str(KANBAN_DB))
    kdb.row_factory = sqlite3.Row

    # Read Kanban events since last sync
    events = kdb.execute(
        "SELECT id, task_id, kind, payload, created_at "
        "FROM task_events WHERE id > ? ORDER BY id",
        (last_id,)
    ).fetchall()

    if not events:
        print("✅ No new Kanban events to sync.")
        kdb.close()
        return 0

    # Read task titles for context
    tasks = {r["id"]: r["title"] for r in kdb.execute("SELECT id, title FROM tasks").fetchall()}

    sdb = sqlite3.connect(str(SSB_DB))

    for ev in events:
        eid = ev["id"]
        task_id = ev["task_id"]
        event = ev["kind"]
        data_raw = ev["payload"]
        ts_raw = ev["created_at"]

        event_type, default_summary = EVENT_MAP.get(event, ("SIGNAL", f"Kanban {event}"))
        title = tasks.get(task_id, task_id)
        summary = f"[Kanban] {default_summary}: {title}"

        try:
            data = json.loads(data_raw) if data_raw else {}
        except (json.JSONDecodeError, TypeError):
            data = {}

        # Detail from data payload
        detail = json.dumps(data, ensure_ascii=False) if data else ""
        risk = RISK_MAP.get(data.get("to_status", ""), "LOW")

        if dry_run:
            print(f"  [DRY-RUN] id={eid} event={event:12s} task={task_id:14s} summary={summary}")
        else:
            seq = _next_seq(sdb)
            _insert_ssb(sdb, seq, event_type, summary, task_id, detail, risk)
            count += 1

        last_id = max(last_id, eid)

    sdb.commit()
    sdb.close()
    kdb.close()

    if not dry_run:
        _save_state(last_id)
        print(f"✅ Synced {count} new Kanban events to SSB (last_id={last_id})")
        print(f"   Run `python3 scripts/ssb_dump.py | tail -5` to verify.")
    else:
        print(f"   Dry-run: {len(events)} events would sync.")

    return 0

if __name__ == "__main__":
    dry_run = "--dry-run" in sys.argv
    full = "--full" in sys.argv
    sys.exit(sync(dry_run, full))
