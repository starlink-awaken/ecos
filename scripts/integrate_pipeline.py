#!/usr/bin/env python3
"""
Integrate Pipeline — 感知管道第五阶段 (Phase 4 Sprint 2)

功能:
  1. 检测新入库文档 (SSB events 触发)
  2. 提取实体关键词
  3. 跨域语义搜索匹配
  4. 自动建立跨域关联
  5. 写入知识图谱链接

设计:
  输入: SSB event (doc_created / doc_updated)
  输出: cross-reference link → KOS entity graph
  阈值: similarity > 0.6 → 自动链接, 0.4-0.6 → 候选待审核
"""

import json
import os
import sys
import re
import time
import hashlib
from datetime import datetime
from pathlib import Path
from collections import Counter

ECOS = os.path.expanduser("~/Workspace/eCOS")
SSB = os.path.join(ECOS, "LADS/ssb/ecos.jsonl")
CROSS_REF = os.path.join(ECOS, "LADS/cross_refs.jsonl")
KOS_INDEX = os.path.expanduser(os.environ.get(
    "KOS_INDEX_PATH",
    "~/Library/Mobile Documents/iCloud~md~obsidian/Documents/99-系统/memory/retrieval/documents-retrieval.sqlite"
))

# ─── 1. Entity Extraction ───
def extract_entities(text: str, title: str = "") -> dict:
    """提取文档中的关键实体: 组织、项目、术语、人员"""
    entities = {
        "orgs": [],
        "projects": [],
        "terms": [],
        "people": [],
    }
    
    # Chinese org patterns
    org_patterns = [
        r'(\w+卫生健康委\w*)', r'(\w+卫健委)', r'(\w+信息中心)',
        r'(\w+政务\w+)', r'(\w+平台)', r'(\w+系统)',
        r'(\w+医院)', r'(\w+中心)',
    ]
    for pat in org_patterns:
        matches = re.findall(pat, text)
        entities["orgs"].extend(matches[:3])
    
    # Project patterns
    proj_patterns = [
        r'(项目[：:]\s*[\u4e00-\u9fff]+)', r'([\u4e00-\u9fff]+项目)',
        r'([\u4e00-\u9fff]+平台)', r'([\u4e00-\u9fff]+系统)',
    ]
    for pat in proj_patterns:
        matches = re.findall(pat, text)
        entities["projects"].extend(matches[:3])
    
    # Term extraction (capitalized Chinese tech terms)
    term_patterns = [
        r'(AI[\u4e00-\u9fff]+)', r'([\u4e00-\u9fff]+AI)',
        r'(\w+架构)', r'(\w+方案)', r'(\w+标准)',
    ]
    for pat in term_patterns:
        matches = re.findall(pat, text)
        entities["terms"].extend(matches[:3])
    
    # Deduplicate
    for k in entities:
        entities[k] = list(dict.fromkeys(entities[k]))
    
    return entities


def build_search_query(entities: dict, title: str) -> str:
    """从实体构建跨域搜索查询"""
    parts = []
    if title:
        parts.append(title[:50])
    for cat in ["orgs", "projects", "terms"]:
        parts.extend(entities.get(cat, [])[:2])
    return " ".join(parts[:5])


# ─── 2. Cross-Domain Search ───
def cross_domain_search(query: str) -> list:
    """使用 KOS MCP 跨域搜索 (语义+LanceDB)"""
    import subprocess
    
    try:
        # Use KOS MCP semantic search through CLI
        script = f"""
import sys, json
sys.path.insert(0, '{ECOS}')
sys.path.insert(0, '{ECOS}/../kos')
try:
    from kos_indexer import semantic_search
    results = semantic_search("{query}", limit=5)
    print(json.dumps(results, ensure_ascii=False))
except ImportError:
    # Fallback: read SSB as approximation
    with open('{SSB}') as f:
        events = [json.loads(l) for l in f if l.strip()]
    recent = events[-10:]
    print(json.dumps([{{"doc_id": e.get("seq"), "title": str(e.get("action",""))[:60], 
                       "zone": e.get("zone", "ssb"), "distance": 0.7}} for e in recent]))
"""
        result = subprocess.run(
            ["python3", "-c", script],
            capture_output=True, text=True, timeout=30
        )
        if result.returncode == 0 and result.stdout.strip():
            return json.loads(result.stdout)
    except Exception as e:
        print(f"  ⚠️ cross_search error: {e}", file=sys.stderr)
    return []


# ─── 3. Link Creation ───
def create_link(source_zone: str, source_doc: str,
                target_zone: str, target_doc: str,
                score: float, entities: dict) -> dict:
    """创建跨域关联记录"""
    link_id = hashlib.md5(
        f"{source_zone}::{source_doc}->{target_zone}::{target_doc}".encode()
    ).hexdigest()[:12]
    
    return {
        "link_id": link_id,
        "source": {"zone": source_zone, "doc": source_doc},
        "target": {"zone": target_zone, "doc": target_doc},
        "score": round(score, 4),
        "entities": entities,
        "status": "auto" if score > 0.6 else "candidate",
        "created": datetime.now().isoformat(),
        "pipeline": "integrate_v1",
    }


# ─── 4. Main Pipeline ───
def run_integrate(limit: int = 10, dry_run: bool = False):
    """主流程: 检查最近SSB事件 → 对新文档建立跨域链接"""
    
    # Read recent SSB events
    with open(SSB) as f:
        events = [json.loads(l) for l in f if l.strip()]
    
    # Find recent doc_created / doc_updated events
    doc_events = [
        e for e in events[-200:]
        if e.get("event_type") in ("DOC_CREATED", "DOC_UPDATED", "doc_created", "doc_updated")
        or "doc" in str(e.get("action", "")).lower()
    ][-limit:]
    
    print(f"Integrate Pipeline v1.0")
    print(f"  SSB总量: {len(events)}, 最近文档事件: {len(doc_events)}")
    
    if not doc_events:
        # Fallback: process most recent events that have content
        doc_events = events[-20:]
        print(f"  ⚠️ 无文档事件，使用最近20个事件作为样本")
    
    links_created = []
    
    for i, event in enumerate(doc_events):
        action = event.get("action", "")
        agent = event.get("agent", "unknown")
        zone = event.get("zone", "unknown")
        
        # Extract entities
        entities = extract_entities(action, "")
        all_keywords = []
        for cat in ["orgs", "projects", "terms"]:
            all_keywords.extend(entities.get(cat, []))
        
        if not all_keywords:
            continue
        
        query = build_search_query(entities, action[:60])
        
        # Cross-domain search
        matches = cross_domain_search(query)
        
        for match in matches:
            target_zone = match.get("zone", "unknown")
            if target_zone == zone:
                continue  # skip same zone
            
            score = 1.0 - match.get("distance", 0.5)  # convert distance to similarity
            
            if score < 0.4:
                continue  # too low
            
            link = create_link(zone, action[:60], target_zone,
                              match.get("title", match.get("doc_id", "?")),
                              score, entities)
            links_created.append(link)
    
    # De-duplicate by link_id
    seen = set()
    unique_links = []
    for link in links_created:
        if link["link_id"] not in seen:
            seen.add(link["link_id"])
            unique_links.append(link)
    
    # Output
    auto_links = [l for l in unique_links if l["status"] == "auto"]
    candidate_links = [l for l in unique_links if l["status"] == "candidate"]
    
    print(f"\n  发现跨域关联: {len(auto_links)} 自动 + {len(candidate_links)} 候选")
    
    for link in auto_links[:5]:
        print(f"  🔗 [{link['status']}] {link['source']['zone']} ←→ {link['target']['zone']}: "
              f"score={link['score']:.3f} {link['source']['doc'][:40]}")
    
    for link in candidate_links[:3]:
        print(f"  🔍 [候选] {link['source']['zone']} ←→ {link['target']['zone']}: "
              f"score={link['score']:.3f}")
    
    # Write links
    if not dry_run and unique_links:
        with open(CROSS_REF, "a") as f:
            for link in unique_links:
                f.write(json.dumps(link, ensure_ascii=False) + "\n")
        print(f"\n  ✅ 写入 {len(unique_links)} 条跨域关联 → {CROSS_REF}")
    
    # SSB event for this run
    ssb_event = {
        "seq": f"integrate_{int(time.time())}",
        "agent": "INTEGRATE_PIPELINE",
        "event_type": "INTEGRATE_RUN",
        "action": f"created {len(auto_links)} auto + {len(candidate_links)} candidate links",
        "links_total": len(unique_links),
        "timestamp": time.time(),
    }
    
    return {
        "total_links": len(unique_links),
        "auto_links": len(auto_links),
        "candidates": len(candidate_links),
        "ssb_event": ssb_event,
    }


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--limit", type=int, default=20, help="处理最近N个文档事件")
    p.add_argument("--dry-run", action="store_true", help="不写入文件")
    p.add_argument("--once", action="store_true", help="单次运行")
    args = p.parse_args()
    
    result = run_integrate(limit=args.limit, dry_run=args.dry_run)
    
    # Write SSB event
    with open(SSB, "a") as f:
        f.write(json.dumps(result["ssb_event"], ensure_ascii=False) + "\n")
    
    print(f"\n  Pipeline完成: {result['total_links']} 链接, "
          f"{result['auto_links']} 自动, {result['candidates']} 候选")
