#!/usr/bin/env python3
"""
Contextualize Pipeline — Perception Layer Stage 4 (Sprint 4)
Auto-links new documents to existing KOS entities and projects.
"""
import json, re, sys, sqlite3, os
from pathlib import Path
from datetime import datetime

KOS_DB = Path(os.environ.get(
    "KOS_INDEX_PATH",
    os.path.expanduser("~/Library/Mobile Documents/iCloud~md~obsidian/Documents/99-系统/memory/retrieval/documents-retrieval.sqlite")
))

def _load_entities() -> list:
    """Load known entities from KOS for matching."""
    if not KOS_DB.exists():
        return []
    db = sqlite3.connect(str(KOS_DB))
    rows = db.execute("SELECT entity_id, entity_type, label, description FROM kos_entities").fetchall()
    db.close()
    return [{"id": r[0], "type": r[1], "label": r[2], "desc": r[3] or ""} for r in rows]

def contextualize(filepath: str) -> dict:
    """Find KOS entities mentioned in a document."""
    path = Path(filepath)
    if not path.exists():
        return {"error": f"not found: {filepath}"}
    
    text = path.read_text()[:10000]
    entities = _load_entities()
    
    matches = []
    for e in entities:
        name = e["label"]
        if name and len(name) > 1 and name in text:
            matches.append({
                "entity_id": e["id"],
                "type": e["type"],
                "label": name,
                "match_count": text.count(name)
            })
    
    # Also extract new potential entities
    potential = re.findall(r'(?:数字化|智能|平台|系统|服务|方案|项目)[\u4e00-\u9fff]+', text)
    new_entities = [{"name": p, "status": "new"} for p in list(set(potential))[:5]]
    
    return {
        "file": path.name,
        "known_entities": matches[:10],
        "new_entities": new_entities,
        "total_links": len(matches),
        "contextualized_at": datetime.now().isoformat()
    }

if __name__ == "__main__":
    if len(sys.argv) > 1:
        result = contextualize(sys.argv[1])
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        test = "/Users/xiamingxing/knowledge/reports/20260514-092408_ecos-phase2-多agent协作-委员会-感知层_EN.md"
        result = contextualize(test)
        print(f"Links: {result['total_links']} known + {len(result['new_entities'])} new")
        for m in result["known_entities"][:5]:
            print(f"  → [{m['type']}] {m['label']} (x{m['match_count']})")
