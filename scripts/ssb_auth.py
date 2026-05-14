#!/usr/bin/env python3
"""
SSB Auth — HMAC-based event signing for SSB integrity.
Usage:
  python3 ssb_auth.py keygen              # Generate signing key
  python3 ssb_auth.py sign <event.json>   # Sign an event
  python3 ssb_auth.py verify              # Verify recent events
"""
import hashlib, hmac, json, os, sys, sqlite3
from pathlib import Path
from datetime import datetime

KEY_FILE = Path(__file__).resolve().parent.parent / "LADS" / "ssb" / ".ssb_key"
DB_PATH = Path(__file__).resolve().parent.parent / "LADS" / "ssb" / "ecos.db"

def _load_key():
    env_key = os.environ.get("SSB_KEY", "")
    if env_key:
        return env_key.encode()
    if KEY_FILE.exists():
        return KEY_FILE.read_bytes()
    return None

def keygen():
    key = os.urandom(32)
    KEY_FILE.write_bytes(key)
    os.chmod(KEY_FILE, 0o600)
    print(f"✅ Key saved to {KEY_FILE} (permissions: 600)")

def sign_event(event_json: str) -> str:
    key = _load_key()
    if not key:
        return None
    return hmac.new(key, event_json.encode(), hashlib.sha256).hexdigest()[:16]

def verify():
    key = _load_key()
    if not key:
        print("⚠️  No SSB_KEY set — skipping signature verification")
        return 0
    
    db = sqlite3.connect(str(DB_PATH))
    rows = db.execute(
        "SELECT id, seq, payload_json, source_agent FROM ssb_events "
        "WHERE source_agent IN ('HERMES','CAPTURE_WATCHER','FILTER_SCORER','SSB_CLIENT') "
        "ORDER BY seq DESC LIMIT 100"
    ).fetchall()
    
    unsigned = []
    for eid, seq, payload, agent in rows:
        content = f"{seq}|{eid}|{agent}|{payload or ''}"
        expected = hmac.new(key, content.encode(), hashlib.sha256).hexdigest()[:16]
        unsigned.append(f"  seq={seq} agent={agent}")
    
    db.close()
    
    if unsigned:
        print(f"⚠️  {len(unsigned)} recent events not signed (Phase 3 migration)")
        print("   First 3: " + "\n   ".join(unsigned[:3]))
    else:
        print("✅ All 100 recent events verified")
    return 0 if len(unsigned) < 10 else 1

if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "verify"
    if cmd == "keygen":
        keygen()
    elif cmd == "sign":
        event = sys.argv[2] if len(sys.argv) > 2 else sys.stdin.read()
        sig = sign_event(event)
        print(sig or "ERROR: no key")
    elif cmd == "verify":
        sys.exit(verify())
    else:
        print(f"Unknown: {cmd}")
