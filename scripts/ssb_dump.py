#!/usr/bin/env python3
"""SSB text dump for git tracking — detects binary-level tampering."""
import sqlite3, json, sys
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "LADS" / "ssb" / "ecos.db"
DUMP_PATH = Path(__file__).resolve().parent.parent / "LADS" / "ssb" / "ecos.jsonl"

def dump():
    db = sqlite3.connect(str(DB_PATH))
    rows = db.execute("SELECT id, seq, timestamp, source_agent, event_type, summary FROM ssb_events ORDER BY seq").fetchall()
    with open(DUMP_PATH, 'w') as f:
        for r in rows:
            f.write(json.dumps({"id": r[0], "seq": r[1], "ts": r[2], "agent": r[3], "type": r[4], "summary": r[5]}, ensure_ascii=False) + "\n")
    print(f"Dumped {len(rows)} events to {DUMP_PATH}")
    db.close()

if __name__ == "__main__":
    dump()
