#!/usr/bin/env python3
"""SSB text dump for git tracking — 完整字段输出 (Phase 4 fix)"""
import sqlite3, json, sys
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "LADS" / "ssb" / "ecos.db"
DUMP_PATH = Path(__file__).resolve().parent.parent / "LADS" / "ssb" / "ecos.jsonl"

def dump():
    db = sqlite3.connect(str(DB_PATH))
    db.row_factory = sqlite3.Row
    rows = db.execute(
        "SELECT id, seq, event_id, timestamp, source_zone, source_agent, "
        "event_type, action, target_zone, target_agent, priority, status, "
        "action_required, confidence, payload_json, payload_size, media_path, "
        "schema_version, agent_signature, created_at "
        "FROM ssb_events ORDER BY seq"
    ).fetchall()
    
    count = 0
    with open(DUMP_PATH, 'w') as f:
        for r in rows:
            event = dict(r)
            # Parse JSON fields
            if event.get("payload_json"):
                try:
                    event["payload_json"] = json.loads(event["payload_json"])
                except:
                    pass
            f.write(json.dumps(event, ensure_ascii=False) + "\n")
            count += 1
    
    db.close()
    print(f"Dumped {count} events to {DUMP_PATH}")

if __name__ == "__main__":
    dump()
