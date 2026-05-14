#!/usr/bin/env python3
"""
Semantic Scorer — lightweight content evaluation (Phase 3 Sprint 2)
Combines with structural score for final quality assessment.

Design:
  - No direct LLM API calls (keeps it simple)
  - Uses heuristics + KOS cross-reference for relevance
  - Structural score × 0.5 + Semantic score × 0.5 = Final
"""
import json, re, sys, sqlite3
from pathlib import Path
from datetime import datetime

DB_PATH = Path(__file__).resolve().parent.parent / "LADS" / "ssb" / "ecos.db"

def score_semantic(text: str, filename: str, structural_score: int = 0) -> dict:
    """Score content semantically using heuristics."""
    reasons = []
    score = 50  # neutral baseline
    
    # 1. Information density (unique words / total words)
    words = re.findall(r'\w+', text.lower())
    unique = len(set(words))
    total = len(words) if words else 1
    density = unique / total
    if density > 0.7:
        score += 20
        reasons.append("high_density")
    elif density < 0.3:
        score -= 20
        reasons.append("low_density")
    
    # 2. Named entity presence (dates, numbers, proper nouns)
    dates = len(re.findall(r'\d{4}[-/]\d{1,2}[-/]\d{1,2}', text))
    numbers = len(re.findall(r'\b\d+\b', text))
    proper = len(re.findall(r'[A-Z][a-z]+ [A-Z][a-z]+', text))
    if dates + numbers + proper > 3:
        score += 15
        reasons.append(f"entities(d={dates},n={numbers},p={proper})")
    
    # 3. Sentiment/opinion markers (vs pure facts)
    opinion_words = ['建议', '推荐', '应该', '必须', '重要', '关键', '风险', '机会',
                     'should', 'must', 'critical', 'important', 'recommend']
    opinions = sum(1 for w in opinion_words if w in text.lower())
    if opinions > 3:
        score += 10
        reasons.append(f"opinions({opinions})")
    
    # 4. Cross-reference with filename expectations
    if 'report' in filename.lower() and len(text) < 500:
        score -= 15
        reasons.append("short_report")
    if 'architecture' in filename.lower() and '架构' not in text and 'architecture' not in text.lower():
        score -= 10
        reasons.append("mismatched_content")
    
    # 5. Technical depth (code blocks, tables, lists)
    code_blocks = len(re.findall(r'```', text)) // 2
    tables = len(re.findall(r'\|.*\|.*\|', text))
    if code_blocks + tables > 2:
        score += 15
        reasons.append(f"technical_depth(c={code_blocks},t={tables})")
    
    final = max(0, min(100, score))
    
    return {
        "semantic_score": final,
        "structural_score": structural_score,
        "combined_score": round(final * 0.5 + structural_score * 0.5),
        "reasons": reasons,
        "scored_at": datetime.now().isoformat()
    }

if __name__ == "__main__":
    if len(sys.argv) > 1:
        path = Path(sys.argv[1])
        if path.exists():
            text = path.read_text()
            result = score_semantic(text, path.name)
            print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        # Test
        test = "建议采用微服务架构。必须注意安全风险。2026-05-14上线。关键指标: 响应时间<100ms。"
        result = score_semantic(test, "architecture-proposal.md", 80)
        print("Test:", json.dumps(result, indent=2, ensure_ascii=False))
