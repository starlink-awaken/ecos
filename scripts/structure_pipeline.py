#!/usr/bin/env python3
"""
Structure Pipeline — Perception Layer Stage 3 (Sprint 2)
Auto-classifies documents, extracts entities, normalizes metadata.
"""
import json, re, sys
from pathlib import Path
from datetime import datetime

CATEGORIES = {
    "policy":    ["政策", "规划", "方案", "通知", "意见", "报告", "规定"],
    "technical": ["架构", "系统", "平台", "代码", "API", "数据库", "部署"],
    "research":  ["研究", "分析", "趋势", "综述", "报告", "实验"],
    "ops":       ["运维", "监控", "日志", "告警", "备份", "巡检"],
}

def classify(text: str, filename: str) -> str:
    """Auto-classify document by content + filename."""
    scores = {cat: 0 for cat in CATEGORIES}
    for cat, keywords in CATEGORIES.items():
        for kw in keywords:
            if kw in text or kw in filename:
                scores[cat] += 1
    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else "general"

def extract_entities(text: str) -> list:
    """Extract potential entities: projects, people, orgs."""
    entities = []
    # Project patterns: "XX平台", "XX系统", "XX项目"
    projects = re.findall(r'[\u4e00-\u9fff]+(?:平台|系统|项目|方案|工具)', text)
    for p in set(projects):
        entities.append({"type": "project", "name": p})
    # Date patterns
    dates = re.findall(r'(?:20\d{2}[-/]\d{1,2}[-/]\d{1,2})', text)
    for d in set(dates):
        entities.append({"type": "date", "name": d})
    return entities[:10]

def structure(filepath: str) -> dict:
    """Run full structure pipeline on a document."""
    path = Path(filepath)
    if not path.exists():
        return {"error": f"not found: {filepath}"}
    
    text = path.read_text()[:5000]  # first 5K chars for analysis
    
    return {
        "file": path.name,
        "category": classify(text, path.name),
        "entities": extract_entities(text),
        "size_kb": round(path.stat().st_size / 1024, 1),
        "structured_at": datetime.now().isoformat(),
        "source": "structure_pipeline"
    }

if __name__ == "__main__":
    if len(sys.argv) > 1:
        result = structure(sys.argv[1])
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        # Test with a known document
        test = "/Users/xiamingxing/knowledge/reports"
        reports = list(Path(test).glob("*.md"))
        if reports:
            r = structure(str(reports[-1]))
            print(f"Test ({reports[-1].name}):")
            print(json.dumps(r, indent=2, ensure_ascii=False))
