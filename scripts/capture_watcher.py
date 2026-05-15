#!/usr/bin/env python3
"""
Capture Watcher — Perception Layer Capture Module (Sprint 2)

Monitored directories → produce SSB PERCEPTION Events.

Usage:
    # Scan all monitored directories
    python3 capture_watcher.py --scan

    # Scan specific directory
    python3 capture_watcher.py --scan ~/knowledge/reports/

    # Register a new monitor directory
    python3 capture_watcher.py --add-watch ~/my-data/ --type external

    # Show seen hashes stats
    python3 capture_watcher.py --stats

Design:
- Each run scans all monitored directories for new/modified files
- SHA256 dedup: a new 'perception_seen' table in SSB SQLite tracks seen hashes
- New files → SSB PERCEPTION Event (type=PERCEPTION)
- Supports incremental mode (only new files) and full mode (re-scan all)
"""

import hashlib
import json
import os
import sqlite3
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Optional

from ecos_common import TZ, SSB_DB_PATH, SSB_DB_DIR, now_iso, get_conn as _get_conn_ecos, CREATE_SSB_EVENTS_SQL

# ─── Paths ────────────────────────────────────────────────────────────

ECOS_HOME = SSB_DB_DIR.parent.parent  # 保持兼容

# Default monitored directories
DEFAULT_MONITOR_DIRS = [
    {
        "path": os.path.expanduser("~/knowledge/reports/"),
        "type": "report",
        "label": "Minerva Reports",
    },
    {
        "path": str(ECOS_HOME / "LADS" / "HANDOFF"),
        "type": "handoff",
        "label": "System Handoffs",
    },
    {
        "path": str(ECOS_HOME / "LADS" / "FAILURES"),
        "type": "failure",
        "label": "System Failures",
    },
]

# File extensions we care about
VALID_EXTENSIONS = {".md", ".txt", ".pdf", ".json", ".yaml", ".yml"}

# Size limits
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB


# ─── Helpers ──────────────────────────────────────────────────────────

def _now() -> str:
    return now_iso()


def _sha256(path: str) -> str:
    """Compute SHA256 of a file, handling large files efficiently."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _classify_file(path: str, watch_type: str) -> str:
    """Classify a file into one of: report, handoff, failure, external, unknown."""
    p = Path(path)
    name = p.name.lower()

    # Override classification based on watch type
    type_classification = {
        "report": "report",
        "handoff": "handoff",
        "failure": "failure",
        "external": "external",
    }
    if watch_type in type_classification:
        return type_classification[watch_type]

    # Detect by content patterns
    if name.startswith("minerva-"):
        return "report"
    if name.startswith("FAIL-"):
        return "failure"
    if "handoff" in name or name == "LATEST.md":
        return "handoff"

    return "external"


def _estimate_readability(path: str) -> dict:
    """Estimate readability metrics without full parsing."""
    try:
        size = os.path.getsize(path)
        with open(path, "rb") as f:
            first_2k = f.read(2048)
        lines = first_2k.decode("utf-8", errors="replace").count("\n") + 1
        has_structure = any(marker in first_2k.decode("utf-8", errors="replace")
                            for marker in ["# ", "## ", "- ", "1. ", "| ", "---"])
        return {
            "size": size,
            "approx_lines": max(lines, 1),
            "has_structure": has_structure,
            "is_readable": size <= MAX_FILE_SIZE,
        }
    except (OSError, UnicodeDecodeError):
        return {"size": 0, "approx_lines": 0, "has_structure": False, "is_readable": False}


# ─── SSB Perception DB ────────────────────────────────────────────────

class PerceptionDB:
    """
    Manages the perception_seen table in SSB SQLite for dedup.
    """

    def __init__(self):
        Path(SSB_DB_PATH).parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self):
        conn = self._get_conn()
        try:
            # Init main SSB table if not exists
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS ssb_events (
                    id            TEXT PRIMARY KEY,
                    seq           INTEGER NOT NULL,
                    timestamp     TEXT NOT NULL,
                    session_id    TEXT DEFAULT '',
                    source_agent  TEXT NOT NULL,
                    source_instance TEXT DEFAULT '',
                    target_scope  TEXT DEFAULT 'ALL',
                    target_hint   TEXT DEFAULT '',
                    event_type    TEXT NOT NULL,
                    event_subtype TEXT DEFAULT '',
                    summary       TEXT NOT NULL,
                    detail        TEXT DEFAULT '',
                    confidence    REAL DEFAULT 1.0,
                    risk_level    TEXT DEFAULT 'LOW',
                    priority      TEXT DEFAULT 'P3',
                    action_req    TEXT DEFAULT 'NONE',
                    deadline      TEXT DEFAULT '',
                    payload_json  TEXT DEFAULT '{}',
                    semantic_json TEXT DEFAULT '{}',
                    created_at    TEXT DEFAULT (datetime('now', 'localtime'))
                );
                
                CREATE INDEX IF NOT EXISTS idx_ssb_type ON ssb_events(event_type);
                CREATE INDEX IF NOT EXISTS idx_ssb_ts ON ssb_events(timestamp DESC);
                CREATE INDEX IF NOT EXISTS idx_ssb_seq ON ssb_events(seq);

                -- Perception dedup tracking
                CREATE TABLE IF NOT EXISTS perception_seen (
                    sha256        TEXT PRIMARY KEY,
                    file_path     TEXT NOT NULL,
                    first_seen    TEXT NOT NULL,
                    last_seen     TEXT NOT NULL,
                    file_size     INTEGER DEFAULT 0,
                    file_mtime    TEXT DEFAULT '',
                    classification TEXT DEFAULT 'external',
                    hit_count     INTEGER DEFAULT 1
                );
                
                CREATE INDEX IF NOT EXISTS idx_perception_class 
                    ON perception_seen(classification);
            """)
            conn.commit()
        finally:
            conn.close()

    def _get_conn(self):
        return _get_conn_ecos()

    def is_seen(self, sha256: str) -> bool:
        conn = self._get_conn()
        try:
            row = conn.execute(
                "SELECT 1 FROM perception_seen WHERE sha256 = ?", (sha256,)
            ).fetchone()
            return row is not None
        finally:
            conn.close()

    def mark_seen(self, sha256: str, file_path: str, classification: str, 
                  file_size: int, file_mtime: str):
        now = _now()
        conn = self._get_conn()
        try:
            conn.execute("""
                INSERT INTO perception_seen 
                (sha256, file_path, first_seen, last_seen, file_size, file_mtime, classification, hit_count)
                VALUES (?, ?, ?, ?, ?, ?, ?, 1)
                ON CONFLICT(sha256) DO UPDATE SET
                    last_seen = excluded.last_seen,
                    file_mtime = excluded.file_mtime,
                    hit_count = hit_count + 1,
                    file_size = excluded.file_size
            """, (sha256, file_path, now, now, file_size, file_mtime, classification))
            conn.commit()
        finally:
            conn.close()

    def get_stats(self) -> dict:
        conn = self._get_conn()
        try:
            total = conn.execute("SELECT COUNT(*) AS c FROM perception_seen").fetchone()["c"]
            by_class = conn.execute(
                "SELECT classification, COUNT(*) AS c FROM perception_seen GROUP BY classification"
            ).fetchall()
            by_hits = conn.execute(
                "SELECT SUM(hit_count) AS c FROM perception_seen"
            ).fetchone()["c"]
            return {
                "total_files_seen": total,
                "total_hits": by_hits or 0,
                "by_classification": {r["classification"]: r["c"] for r in by_class},
            }
        finally:
            conn.close()


# ─── Capture Core ─────────────────────────────────────────────────────

class CaptureWatcher:
    """
    Capture Watcher: scans directories, detects new files, produces PERCEPTION Events.
    """

    def __init__(self):
        self.db = PerceptionDB()

    def _publish_perception(self, file_path: str, classification: str, 
                             sha256: str, size: int, mtime: str,
                             is_new: bool, readability: dict):
        """Publish a PERCEPTION event to the SSB SQLite database."""
        p = Path(file_path)
        subtype = "NEW" if is_new else "RESCAN"
        
        conn = self.db._get_conn()
        try:
            # Generate event
            event_id = f"perception-{sha256[:12]}"
            now = _now()
            
            summary = f"{'NEW' if is_new else 'SCAN'}: {classification} - {p.name}"
            detail = json.dumps({
                "path": file_path,
                "sha256": sha256,
                "size": size,
                "mtime": mtime,
                "detected_at": now,
                "classification": classification,
                "readability": readability,
                "full_path": str(p.resolve()),
            }, ensure_ascii=False)
            
            action_req = "EXECUTE" if (is_new and readability.get("is_readable") and 
                                        readability.get("has_structure")) else "NONE"
            
            # Get next seq
            last_seq = conn.execute("SELECT COALESCE(MAX(seq), 0) AS s FROM ssb_events").fetchone()["s"]
            seq = last_seq + 1
            
            conn.execute("""
                INSERT INTO ssb_events 
                (id, seq, timestamp, session_id,
                 source_agent, source_instance,
                 target_scope, target_hint,
                 event_type, event_subtype,
                 summary, detail, confidence, risk_level, priority,
                 action_req, deadline, payload_json, semantic_json)
                VALUES (?, ?, ?, ?,
                        ?, ?,
                        ?, ?,
                        ?, ?,
                        ?, ?, ?, ?, ?,
                        ?, ?, ?, ?)
            """, (
                event_id, seq, now, "",
                "CAPTURE_WATCHER", f"sprint2-{classification}",
                "SSB_PERSIST", "",
                "PERCEPTION", subtype,
                summary, detail,
                0.9, "LOW", "P2",
                action_req, "",
                json.dumps({"summary": summary, "detail": detail, "action_required": action_req, 
                           "confidence": 0.9, "risk_level": "LOW", "priority": "P2"}, ensure_ascii=False),
                json.dumps({"intent": f"capture {classification} document", 
                           "state_change": f"new_{classification}_detected"}, ensure_ascii=False),
            ))
            conn.commit()
            
            return event_id, subtype, action_req
        finally:
            conn.close()

    def scan(self, scan_path: Optional[str] = None, incremental: bool = True) -> dict:
        """
        Scan directories for new/modified files.
        
        Args:
            scan_path: If set, scan only this directory. Otherwise scan all defaults.
            incremental: If True, only detect NEW files (not previously seen).
                         If False, re-scan all files and emit PERCEPTION(RESCAN).
        
        Returns:
            dict with scan results
        """
        results = {
            "directories_scanned": [],
            "files_scanned": 0,
            "files_new": 0,
            "files_rejected": 0,
            "events_published": 0,
            "errors": [],
        }

        # Determine which directories to scan
        if scan_path:
            dirs_to_scan = [{"path": scan_path, "type": "external", "label": "Manual Scan"}]
        else:
            dirs_to_scan = DEFAULT_MONITOR_DIRS

        for watch in dirs_to_scan:
            watch_path = watch["path"]
            watch_type = watch["type"]
            watch_label = watch.get("label", watch_type)

            if not os.path.isdir(watch_path):
                results["errors"].append(f"Directory not found: {watch_path}")
                continue

            results["directories_scanned"].append(watch_label)

            # Walk the directory
            for root, dirs, files in os.walk(watch_path):
                # Skip hidden dirs
                dirs[:] = [d for d in dirs if not d.startswith(".")]
                
                for filename in sorted(files):
                    if filename.startswith("."):
                        continue
                    if filename == "TEMPLATE.md":
                        continue

                    filepath = os.path.join(root, filename)
                    ext = Path(filename).suffix.lower()

                    # Filter by extension
                    if ext not in VALID_EXTENSIONS:
                        results["files_rejected"] += 1
                        continue

                    results["files_scanned"] += 1

                    try:
                        stat = os.stat(filepath)
                        size = stat.st_size
                        mtime = datetime.fromtimestamp(stat.st_mtime, TZ).isoformat()

                        if size > MAX_FILE_SIZE:
                            results["files_rejected"] += 1
                            continue

                        sha = _sha256(filepath)

                        if incremental and self.db.is_seen(sha):
                            # Update seen timestamp (file may have been modified)
                            classification = _classify_file(filepath, watch_type)
                            self.db.mark_seen(sha, filepath, classification, size, mtime)
                            continue

                        # New file (or full scan)
                        classification = _classify_file(filepath, watch_type)
                        readability = _estimate_readability(filepath)
                        is_new = incremental or not self.db.is_seen(sha)

                        eid, subtype, action_req = self._publish_perception(
                            filepath, classification, sha, size, mtime, 
                            is_new, readability
                        )

                        # Mark as seen
                        self.db.mark_seen(sha, filepath, classification, size, mtime)

                        results["files_scanned"] += 1
                        if is_new:
                            results["files_new"] += 1
                        results["events_published"] += 1

                    except (OSError, PermissionError) as e:
                        results["errors"].append(f"{filepath}: {e}")
                        continue

        return results

    def stats(self) -> dict:
        return self.db.get_stats()


# ─── CLI ──────────────────────────────────────────────────────────────

def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Capture Watcher — eCOS Perception Layer"
    )
    parser.add_argument("--scan", nargs="?", const=True, default=False,
                        help="Scan monitored directories (optionally specify a path)")
    parser.add_argument("--incremental", action="store_true", default=True,
                        help="Incremental mode: only detect NEW files (default: True)")
    parser.add_argument("--full", action="store_true",
                        help="Full re-scan: emit PERCEPTION for ALL files, not just new")
    parser.add_argument("--stats", action="store_true",
                        help="Show perception seen stats")
    parser.add_argument("--json", action="store_true",
                        help="Output as JSON")

    args = parser.parse_args()

    watcher = CaptureWatcher()

    if args.full:
        args.incremental = False

    if args.scan:
        scan_path = args.scan if isinstance(args.scan, str) else None
        results = watcher.scan(scan_path=scan_path, incremental=args.incremental)
        if args.json:
            print(json.dumps(results, ensure_ascii=False, indent=2))
        else:
            print(f"📁 Directories scanned: {len(results['directories_scanned'])}")
            print(f"📄 Files scanned:       {results['files_scanned']}")
            print(f"🆕 Files new:           {results['files_new']}")
            print(f"❌ Files rejected:      {results['files_rejected']}")
            print(f"📨 Events published:    {results['events_published']}")
            if results["errors"]:
                print(f"\n⚠️  Errors ({len(results['errors'])}):")
                for err in results["errors"][:5]:
                    print(f"   • {err}")
        return

    if args.stats:
        stats = watcher.stats()
        if args.json:
            print(json.dumps(stats, ensure_ascii=False, indent=2))
        else:
            print(f"Perception Seen Files")
            print(f"  Total: {stats['total_files_seen']}")
            print(f"  Hits:  {stats['total_hits']}")
            for cls, count in stats.get("by_classification", {}).items():
                print(f"  • {cls}: {count}")
        return

    parser.print_help()


if __name__ == "__main__":
    main()
