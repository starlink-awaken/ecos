#!/usr/bin/env python3
"""
Filter Scorer — Perception Layer Filter Module (Sprint 2)

Reads SSB PERCEPTION events → quality + relevance scoring → marks for KOS indexing.

Usage:
    # Process all unprocessed PERCEPTION events
    python3 filter_scorer.py --run

    # Process with specific quality threshold
    python3 filter_scorer.py --run --threshold 70

    # Show filter stats
    python3 filter_scorer.py --stats

    # Show recent filter results
    python3 filter_scorer.py --recent

Scoring Dimensions:
  quality_score (0-100):
    - Has title/heading: +20
    - Has structure (lists, tables, sections): +15
    - Document length (200-5000 chars optimal): +20
    - Has metadata/tags/keywords: +15
    - Has numbered/ordered sections: +10
    - File extension (.md > .txt > .pdf > other): +10
    - Readability (no binary garbage): +10
    Threshold: ≥60 → PASS (ready for KOS indexing)

  relevance_score (0-100):
    - Matches known KOS domain keywords: +20-60
    - Has project-specific vocabulary: +10-30
    - Is a recognized type (report/handoff/failure): +10
    Threshold: ≥40 → RELEVANT (prioritize indexing)
"""

import json
import os
import re
import sqlite3
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Optional

# ─── Paths ────────────────────────────────────────────────────────────

ECOS_HOME = Path(os.path.expanduser("~/Workspace/eCOS"))
SSB_DB_PATH = ECOS_HOME / "LADS" / "ssb" / "ecos.db"
TZ = timezone(timedelta(hours=8), "CST")

# Default quality threshold
DEFAULT_QUALITY_THRESHOLD = 60
DEFAULT_RELEVANCE_THRESHOLD = 40

# Domain keywords (derived from KOS 7 domain structure)
DOMAIN_KEYWORDS = {
    "gongwen": [
        "卫健委", "医疗", "卫生", "健康", "医院", "疾控", "医保",
        "公文", "政策", "通知", "报告", "意见", "办法", "条例",
    ],
    "guozhuan": [
        "国转中心", "技术转移", "成果转化", "知识产权", "专利",
        "科技创新", "产业化", "孵化器", "产学研",
    ],
    "projects": [
        "eCOS", "KOS", "Minerva", "SharedBrain", "Hermes",
        "SSB", "LADS", "MCP", "Phase", "Sprint", "Workflow",
    ],
    "knowledge": [
        "Obsidian", "知识库", "笔记", "方法论", "框架",
        "系统设计", "架构", "认知", "贝叶斯", "控制论",
    ],
    "family": [
        "家庭", "生活", "运维", "账单", "备忘",
    ],
    "life_ops": [
        "运维", "配置", "自动化", "cron", "定时",
    ],
}

# File type weights
FILE_TYPE_WEIGHTS = {
    ".md": 10,
    ".txt": 7,
    ".pdf": 5,
    ".json": 6,
    ".yaml": 6,
    ".yml": 6,
}


# ─── Helpers ──────────────────────────────────────────────────────────

def _now() -> str:
    return datetime.now(TZ).isoformat()


def _get_conn():
    conn = sqlite3.connect(str(SSB_DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    return conn


def _read_file_content(file_path: str) -> str:
    """Read file content safely."""
    try:
        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            return f.read(5000)  # First 5000 chars for scoring
    except (OSError, UnicodeDecodeError):
        return ""


# ─── Quality Scorer ───────────────────────────────────────────────────

class QualityScorer:
    """
    Scores a document's quality on 0-100 scale.
    """
    
    def score(self, file_path: str) -> dict:
        """Score a document and return detailed breakdown."""
        content = _read_file_content(file_path)
        if not content:
            return {"total": 0, "breakdown": {"readable": 0}, "summary": "Unreadable"}

        p = Path(file_path)
        ext = p.suffix.lower()
        
        breakdown = {}
        score = 0

        # 1. File type weight (max 10)
        ext_score = FILE_TYPE_WEIGHTS.get(ext, 2)
        breakdown["file_type"] = ext_score
        score += ext_score

        # 2. Has title/heading (max 20)
        has_h1 = bool(re.search(r'^#\s+\S', content, re.MULTILINE))
        has_h2 = bool(re.search(r'^##\s+\S', content, re.MULTILINE))
        has_heading = has_h1 or has_h2
        title_score = 20 if has_heading else (10 if has_h1 else 0)
        breakdown["has_heading"] = title_score
        breakdown["_h1"] = has_h1
        breakdown["_h2"] = has_h2
        score += title_score

        # 3. Has structure elements (max 15)
        has_list = bool(re.search(r'^[\-\*]\s', content, re.MULTILINE))
        has_table = "|" in content and "-|-" in content
        has_sections = bool(re.search(r'^---$', content, re.MULTILINE))
        has_code = bool(re.search(r'```', content))
        
        structure_score = 0
        if has_list: structure_score += 5
        if has_table: structure_score += 5
        if has_sections or has_code: structure_score += 5
        breakdown["structure"] = structure_score
        breakdown["_list"] = has_list
        breakdown["_table"] = has_table
        breakdown["_code"] = has_code or has_sections
        score += structure_score

        # 4. Document length (max 20)
        length = len(content)
        if 500 <= length <= 3000:
            length_score = 20
        elif 200 <= length < 500:
            length_score = 15
        elif 3000 < length <= 5000:
            length_score = 15
        elif 10000 < length:
            length_score = 5  # Too long, likely raw data
        elif length < 200:
            length_score = 10
        else:
            length_score = 10
        breakdown["length"] = length_score
        breakdown["_char_count"] = length
        score += length_score

        # 5. Has metadata/tags (max 15)
        has_tags = bool(re.search(r'(tags|labels|categories|type)\s*[:：]', content, re.IGNORECASE))
        has_metadata = bool(re.search(r'^---\s*$', content, re.MULTILINE))  # YAML front matter
        has_version = bool(re.search(r'version|v\d+\.\d+', content, re.IGNORECASE))
        
        meta_score = 0
        if has_tags: meta_score += 5
        if has_metadata: meta_score += 5
        if has_version: meta_score += 5
        breakdown["metadata"] = meta_score
        breakdown["_tags"] = has_tags
        breakdown["_yaml_front"] = has_metadata
        breakdown["_version"] = has_version
        score += meta_score

        # 6. Ordered/logical structure (max 10)
        has_ordered = bool(re.search(r'^\d+\.\s', content, re.MULTILINE))
        has_section_numbers = bool(re.search(r'^#+\s+\d+[\.\s)]', content, re.MULTILINE))
        logical_score = 0
        if has_ordered: logical_score += 5
        if has_section_numbers: logical_score += 5
        breakdown["logical"] = logical_score
        breakdown["_ordered"] = has_ordered
        breakdown["_numbered_sections"] = has_section_numbers
        score += logical_score

        # 7. Content quality (max 10)
        # Penalize if too much repeated text or very short lines
        lines = content.split("\n")
        non_empty = [l for l in lines if l.strip()]
        if len(non_empty) > 3:
            avg_line_length = sum(len(l) for l in non_empty) / max(len(non_empty), 1)
            if avg_line_length < 10:
                quality_score = 3  # Sparse content
            elif avg_line_length > 200:
                quality_score = 5  # Probably code/data dump
            else:
                quality_score = 10  # Normal prose
        else:
            quality_score = 3
            avg_line_length = 0
        
        breakdown["content_quality"] = quality_score
        breakdown["_avg_line_length"] = round(avg_line_length, 1) if len(lines) > 3 else 0
        score += quality_score

        # Cap at 100
        total = min(score, 100)

        return {
            "total": total,
            "breakdown": breakdown,
            "summary": self._summarize(total, breakdown),
        }

    def _summarize(self, total: int, breakdown: dict) -> str:
        if total >= 85:
            return "Excellent"
        elif total >= 70:
            return "Good"
        elif total >= 60:
            return "Adequate"
        elif total >= 40:
            return "Low"
        else:
            return "Poor"


# ─── Relevance Scorer ─────────────────────────────────────────────────

class RelevanceScorer:
    """
    Scores a document's relevance to KOS domains on 0-100 scale.
    """
    
    def score(self, file_path: str, classification: str) -> dict:
        content = _read_file_content(file_path)
        if not content:
            return {"total": 0, "domains_matched": [], "summary": "Unreadable"}

        content_lower = content.lower()
        domains_matched = {}
        
        for domain, keywords in DOMAIN_KEYWORDS.items():
            matches = [kw for kw in keywords if kw.lower() in content_lower]
            if matches:
                domains_matched[domain] = matches

        # Calculate score
        score = 0
        
        # 1. Classification bonus (max 10)
        if classification in ("report", "handoff", "failure"):
            score += 10
        
        # 2. Domain match score (max 60)
        if domains_matched:
            total_matches = sum(len(m) for m in domains_matched.values())
            unique_domains = len(domains_matched)
            # Up to 60 points: 20 per domain * number of domains, capped
            domain_score = min(unique_domains * 20, 60)
            score += domain_score
        
        # 3. Project-specific vocabulary (max 30)
        project_terms = [
            "ecos", "kos", "minerva", "ssb", "lads", "hermes", "mcp",
            "phase", "sprint", "workflow", "agent", "committee",
            "perception", "feedback", "docker", "pipeline",
        ]
        project_matches = [t for t in project_terms if t in content_lower]
        project_score = min(len(project_matches) * 5, 30)
        score += project_score

        total = min(score, 100)

        return {
            "total": total,
            "domains_matched": list(domains_matched.keys()),
            "keywords_found": {k: len(v) for k, v in domains_matched.items()},
            "summary": self._summarize(total),
        }

    def _summarize(self, total: int) -> str:
        if total >= 70:
            return "Highly relevant"
        elif total >= 40:
            return "Somewhat relevant"
        else:
            return "Low relevance"


# ─── Filter Pipeline ──────────────────────────────────────────────────

class FilterPipeline:
    """
    Main filter pipeline: reads PERCEPTION events → scores → marks.
    """

    def __init__(self):
        self.quality_scorer = QualityScorer()
        self.relevance_scorer = RelevanceScorer()

    def process(self, threshold: int = DEFAULT_QUALITY_THRESHOLD,
                limit: int = 50) -> dict:
        """
        Process unprocessed PERCEPTION events.
        
        Looks for PERCEPTION events with action_required=EXECUTE
        that have NOT yet been processed by the filter.
        """
        stats = {
            "events_read": 0,
            "events_scored": 0,
            "passed_quality": 0,
            "passed_relevance": 0,
            "passed_both": 0,
            "filtered_out": 0,
            "errors": [],
        }

        conn = _get_conn()
        try:
            # Find PERCEPTION events marked for EXECUTE
            rows = conn.execute("""
                SELECT id, seq, timestamp, payload_json
                FROM ssb_events
                WHERE event_type = 'PERCEPTION'
                  AND action_req = 'EXECUTE'
                ORDER BY seq ASC
                LIMIT ?
            """, (limit,)).fetchall()

            stats["events_read"] = len(rows)

            for row in rows:
                try:
                    payload = json.loads(row["payload_json"])
                    detail = json.loads(payload.get("detail", "{}")) if isinstance(payload.get("detail"), str) else payload.get("detail", {})
                except (json.JSONDecodeError, TypeError):
                    # If payload_json is a plain string
                    detail = {}

                file_path = detail.get("path", "")
                classification = detail.get("classification", "external")

                if not file_path or not os.path.exists(file_path):
                    # File might have been deleted
                    self._mark_filtered(conn, row["id"], "FILE_MISSING",
                                        "File no longer exists", row["seq"])
                    stats["filtered_out"] += 1
                    continue

                stats["events_scored"] += 1

                # Quality score
                quality = self.quality_scorer.score(file_path)
                quality_pass = quality["total"] >= threshold

                # Relevance score
                relevance = self.relevance_scorer.score(file_path, classification)
                relevance_pass = relevance["total"] >= DEFAULT_RELEVANCE_THRESHOLD

                # Decision
                if quality_pass and relevance_pass:
                    self._mark_index_ready(conn, row["id"], row["seq"],
                                           quality, relevance)
                    stats["passed_both"] += 1
                elif quality_pass:
                    self._mark_quality_pass(conn, row["id"], row["seq"],
                                            quality, relevance)
                    stats["passed_quality"] += 1
                elif relevance_pass:
                    self._mark_relevance_pass(conn, row["id"], row["seq"],
                                              quality, relevance)
                    stats["passed_relevance"] += 1
                else:
                    self._mark_filtered(conn, row["id"], "QUALITY",
                                        f"quality={quality['total']}/relevance={relevance['total']}",
                                        row["seq"], quality, relevance)
                    stats["filtered_out"] += 1

                # Mark original PERCEPTION event as processed
                new_action_req = "INDEX_QUEUED" if (quality_pass and relevance_pass) else "NONE"
                conn.execute(
                    "UPDATE ssb_events SET action_req = ? WHERE id = ?",
                    (new_action_req, row["id"])
                )

            conn.commit()
        finally:
            conn.close()

        return stats

    def _mark_index_ready(self, conn, original_id: str, seq: int,
                          quality: dict, relevance: dict):
        """Mark document as ready for KOS indexing."""
        now = _now()
        new_id = f"index-queued-{original_id[:24]}-seq{seq}"
        
        detail = json.dumps({
            "source_event": original_id,
            "quality_score": quality["total"],
            "quality_breakdown": quality["breakdown"],
            "quality_summary": quality["summary"],
            "relevance_score": relevance["total"],
            "relevance_domains": relevance["domains_matched"],
            "relevance_summary": relevance["summary"],
            "decision": "INDEX",
            "threshold_quality": 60,
            "threshold_relevance": 40,
        }, ensure_ascii=False)

        new_seq = seq + 1
        conn.execute("""
            INSERT INTO ssb_events 
            (id, seq, timestamp, session_id,
             source_agent, source_instance,
             event_type, event_subtype,
             summary, detail, confidence, risk_level, priority,
             action_req, deadline, payload_json, semantic_json)
            VALUES (?, ?, ?, ?,
                    ?, ?,
                    ?, ?,
                    ?, ?, ?, ?, ?,
                    ?, ?, ?, ?)
        """, (
            new_id, new_seq, now, "",
            "FILTER_SCORER", "sprint2",
            "STATE_CHANGE", "INDEX_READY",
            f"Index ready: quality={quality['total']}, relevance={relevance['total']}",
            detail, 0.85, "LOW", "P2",
            "EXECUTE", "",
            json.dumps({"summary": "Ready for indexing", "detail": detail,
                       "confidence": 0.85, "risk_level": "LOW", "priority": "P2",
                       "action_required": "EXECUTE"}, ensure_ascii=False),
            json.dumps({"intent": f"queue for KOS indexing",
                       "state_change": "from_perception_to_index_ready"}, ensure_ascii=False),
        ))

    def _mark_quality_pass(self, conn, original_id: str, seq: int,
                           quality: dict, relevance: dict):
        """Quality passed but relevance too low — still record for audit."""
        now = _now()
        new_id = f"quality-pass-{original_id[:20]}-seq{seq}"
        
        detail = json.dumps({
            "source_event": original_id,
            "quality_score": quality["total"],
            "quality_summary": quality["summary"],
            "relevance_score": relevance["total"],
            "relevance_summary": relevance["summary"],
            "decision": "HOLD",  # Quality OK but relevance low — might still index later
        }, ensure_ascii=False)

        new_seq = seq + 1
        conn.execute("""
            INSERT INTO ssb_events 
            (id, seq, timestamp, session_id,
             source_agent, source_instance,
             event_type, event_subtype,
             summary, detail, confidence, risk_level, priority,
             action_req, deadline, payload_json, semantic_json)
            VALUES (?, ?, ?, ?,
                    ?, ?,
                    ?, ?,
                    ?, ?, ?, ?, ?,
                    ?, ?, ?, ?)
        """, (
            new_id, new_seq, now, "",
            "FILTER_SCORER", "sprint2",
            "SIGNAL", "FILTERED_QUALITY_OK",
            f"Quality OK ({quality['total']}) but relevance low ({relevance['total']}) — held",
            detail, 0.7, "LOW", "P3",
            "NONE", "",
            json.dumps({"summary": "Quality OK, low relevance", "detail": detail,
                       "confidence": 0.7, "risk_level": "LOW", "priority": "P3",
                       "action_required": "NONE"}, ensure_ascii=False),
            json.dumps({"intent": "audit trail for held documents"}, ensure_ascii=False),
        ))

    def _mark_relevance_pass(self, conn, original_id: str, seq: int,
                             quality: dict, relevance: dict):
        """Relevance passed but quality too low."""
        now = _now()
        new_id = f"relevance-pass-{original_id[:20]}-seq{seq}"
        
        detail = json.dumps({
            "source_event": original_id,
            "quality_score": quality["total"],
            "quality_summary": quality["summary"],
            "relevance_score": relevance["total"],
            "relevance_summary": relevance["summary"],
            "decision": "HOLD",
        }, ensure_ascii=False)

        new_seq = seq + 1
        conn.execute("""
            INSERT INTO ssb_events 
            (id, seq, timestamp, session_id,
             source_agent, source_instance,
             event_type, event_subtype,
             summary, detail, confidence, risk_level, priority,
             action_req, deadline, payload_json, semantic_json)
            VALUES (?, ?, ?, ?,
                    ?, ?,
                    ?, ?,
                    ?, ?, ?, ?, ?,
                    ?, ?, ?, ?)
        """, (
            new_id, new_seq, now, "",
            "FILTER_SCORER", "sprint2",
            "SIGNAL", "FILTERED_RELEVANCE_OK",
            f"Relevance OK ({relevance['total']}) but quality low ({quality['total']}) — held",
            detail, 0.7, "LOW", "P3",
            "NONE", "",
            json.dumps({"summary": "Low quality", "detail": detail,
                       "confidence": 0.7, "risk_level": "LOW", "priority": "P3",
                       "action_required": "NONE"}, ensure_ascii=False),
            json.dumps({"intent": "audit trail for held documents"}, ensure_ascii=False),
        ))

    def _mark_filtered(self, conn, original_id: str, reason: str,
                       detail_str: str, seq: int,
                       quality: Optional[dict] = None,
                       relevance: Optional[dict] = None):
        """Mark document as filtered out (did not pass threshold)."""
        now = _now()
        new_id = f"filtered-{reason[:8].lower()}-{original_id[:20]}-seq{seq}"
        
        detail = json.dumps({
            "source_event": original_id,
            "reason": reason,
            "detail": detail_str,
            "quality_score": quality["total"] if quality else None,
            "relevance_score": relevance["total"] if relevance else None,
            "decision": "SKIP",
        }, ensure_ascii=False)

        new_seq = seq + 1
        conn.execute("""
            INSERT INTO ssb_events 
            (id, seq, timestamp, session_id,
             source_agent, source_instance,
             event_type, event_subtype,
             summary, detail, confidence, risk_level, priority,
             action_req, deadline, payload_json, semantic_json)
            VALUES (?, ?, ?, ?,
                    ?, ?,
                    ?, ?,
                    ?, ?, ?, ?, ?,
                    ?, ?, ?, ?)
        """, (
            new_id, new_seq, now, "",
            "FILTER_SCORER", "sprint2",
            "SIGNAL", "FILTERED",
            f"Filtered: {reason} — {detail_str}",
            detail, 0.8, "LOW", "P3",
            "NONE", "",
            json.dumps({"summary": f"Filtered out: {reason}", "detail": detail,
                       "confidence": 0.8, "risk_level": "LOW", "priority": "P3",
                       "action_required": "NONE"}, ensure_ascii=False),
            json.dumps({"intent": "audit trail for filtered documents",
                       "tags": ["filtered", reason.lower()]}, ensure_ascii=False),
        ))

    def stats(self) -> dict:
        """Show filter pipeline statistics."""
        conn = _get_conn()
        try:
            # Total decisions
            index_ready = conn.execute(
                "SELECT COUNT(*) AS c FROM ssb_events WHERE id LIKE 'index-queued-%'"
            ).fetchone()["c"]
            filtered = conn.execute(
                "SELECT COUNT(*) AS c FROM ssb_events WHERE id LIKE 'filtered-%'"
            ).fetchone()["c"]
            quality_pass = conn.execute(
                "SELECT COUNT(*) AS c FROM ssb_events WHERE id LIKE 'quality-pass-%'"
            ).fetchone()["c"]
            relevance_pass = conn.execute(
                "SELECT COUNT(*) AS c FROM ssb_events WHERE id LIKE 'relevance-pass-%'"
            ).fetchone()["c"]

            # Perception events
            total_perception = conn.execute(
                "SELECT COUNT(*) AS c FROM ssb_events WHERE event_type = 'PERCEPTION'"
            ).fetchone()["c"]
            pending_filter = conn.execute(
                "SELECT COUNT(*) AS c FROM ssb_events WHERE event_type = 'PERCEPTION' "
                "AND action_req = 'EXECUTE'"
            ).fetchone()["c"]

            return {
                "total_perception_events": total_perception,
                "pending_filter": pending_filter,
                "index_ready": index_ready,
                "filtered_out": filtered,
                "quality_pass_held": quality_pass,
                "relevance_pass_held": relevance_pass,
            }
        finally:
            conn.close()


# ─── CLI ──────────────────────────────────────────────────────────────

def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Filter Scorer — eCOS Perception Layer Filter"
    )
    parser.add_argument("--run", action="store_true",
                        help="Process pending PERCEPTION events")
    parser.add_argument("--threshold", type=int, default=DEFAULT_QUALITY_THRESHOLD,
                        help=f"Quality threshold (default: {DEFAULT_QUALITY_THRESHOLD})")
    parser.add_argument("--stats", action="store_true",
                        help="Show filter pipeline statistics")
    parser.add_argument("--recent", type=int, default=10,
                        help="Show N recent decisions")
    parser.add_argument("--json", action="store_true",
                        help="Output as JSON")

    args = parser.parse_args()

    pipeline = FilterPipeline()

    if args.run:
        results = pipeline.process(threshold=args.threshold)
        if args.json:
            print(json.dumps(results, ensure_ascii=False, indent=2))
        else:
            total = (results.get("passed_both", 0) + 
                    results.get("passed_quality", 0) + 
                    results.get("passed_relevance", 0) + 
                    results.get("filtered_out", 0))
            print(f"📄 Events read:      {results['events_read']}")
            print(f"🔍 Events scored:    {results['events_scored']}")
            print(f"✅ Index ready:      {results['passed_both']} (quality+relevance both pass)")
            print(f"📊 Quality pass:     {results['passed_quality']} (quality OK, relevance low)")
            print(f"📊 Relevance pass:   {results['passed_relevance']} (relevance OK, quality low)")
            print(f"❌ Filtered out:     {results['filtered_out']}")
            if results['errors']:
                print(f"\n⚠️  Errors ({len(results['errors'])}):")
                for err in results['errors'][:5]:
                    print(f"   • {err}")
        return

    if args.stats:
        stats = pipeline.stats()
        if args.json:
            print(json.dumps(stats, ensure_ascii=False, indent=2))
        else:
            print("Filter Pipeline Statistics")
            print(f"  PERCEPTION events:       {stats['total_perception_events']}")
            print(f"  Pending filter:          {stats['pending_filter']}")
            print(f"  Index ready:             {stats['index_ready']}")
            print(f"  Filtered out:            {stats['filtered_out']}")
            print(f"  Quality OK (low relev):  {stats['quality_pass_held']}")
            print(f"  Relevance OK (low qual): {stats['relevance_pass_held']}")
        return

    if args.recent:
        conn = _get_conn()
        try:
            rows = conn.execute("""
                SELECT seq, event_type, event_subtype, summary, timestamp
                FROM ssb_events
                WHERE event_type IN ('STATE_CHANGE', 'SIGNAL')
                  AND (event_subtype = 'INDEX_READY'
                       OR event_subtype LIKE 'FILTERED%'
                       OR id LIKE 'quality-pass-%'
                       OR id LIKE 'relevance-pass-%')
                ORDER BY seq DESC
                LIMIT ?
            """, (args.recent,)).fetchall()
            
            if args.json:
                results = [{"seq": r["seq"], "type": r["event_type"],
                           "subtype": r["event_subtype"], "summary": r["summary"],
                           "timestamp": r["timestamp"]} for r in rows]
                print(json.dumps(results, ensure_ascii=False, indent=2))
            else:
                print(f"Recent {len(rows)} filter decisions:")
                for r in rows:
                    print(f"  #{r['seq']:>4} | {r['event_subtype']:<20} | {r['summary'][:65]}")
        finally:
            conn.close()
        return

    parser.print_help()


if __name__ == "__main__":
    main()
