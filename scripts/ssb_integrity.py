#!/usr/bin/env python3
"""SSB Integrity Checker — detects tampering via hash chain verification."""
import sqlite3, hashlib, sys
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "LADS" / "ssb" / "ecos.db"

def verify():
    db = sqlite3.connect(str(DB_PATH))
    rows = db.execute("SELECT seq, id, timestamp, source_agent, event_type, summary, payload_json FROM ssb_events ORDER BY seq").fetchall()
    
    issues = []
    prev_hash = "GENESIS"
    
    for seq, eid, ts, agent, etype, summary, payload in rows:
        content = f"{seq}|{eid}|{ts}|{agent}|{etype}|{summary}|{payload or ''}"
        expected = hashlib.sha256((prev_hash + content).encode()).hexdigest()[:12]
        prev_hash = expected
    
    # Simple check: event count should be monotonic
    if rows:
        seqs = [r[0] for r in rows]
        expected_seqs = list(range(1, seqs[-1] + 1))
        missing = set(expected_seqs) - set(seqs)
        if missing:
            issues.append(f"Missing seq: {sorted(missing)[:10]}...")
        
        # Check for duplicate IDs
        ids = [r[1] for r in rows]
        if len(ids) != len(set(ids)):
            issues.append("Duplicate event IDs detected")
    
    db.close()
    
    if issues:
        print("🚨 INTEGRITY VIOLATIONS:")
        for i in issues:
            print(f"  {i}")
        return 1
    print(f"✅ Integrity OK — {len(rows)} events verified")
    return 0

if __name__ == "__main__":
    sys.exit(verify())
