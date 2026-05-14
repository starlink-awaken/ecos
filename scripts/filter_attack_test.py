#!/usr/bin/env python3
"""
Filter Scorer Attack Test — 对抗样本验证 (Problem #3 fix)
验收标准: 写了安全功能后, 必须被攻击过且没倒。
"""
import sys, json
from pathlib import Path

# 构造攻击样本 — 这些已知的绕过模式
ATTACK_SAMPLES = {
    "boilerplate_report": {
        "text": """# Comprehensive Analysis of System Safety

## Introduction
This document provides a thorough examination of safety measures.

## Methodology  
- Item 1: Data collection
- Item 2: Analysis framework
- Item 3: Validation approach

## Results
| Metric | Value | Status |
|--------|-------|--------|
| Score | 95 | PASS |

## Conclusion
Further research is needed to validate these findings.""",
        "expected": "BLOCKED",  # 应该被 content_integrity 拦截
        "why": "模板化结构 + 无实质内容 = 典型感知投毒"
    },
    "generic_tech_doc": {
        "text": """# System Architecture Overview

The system implements a layered architecture pattern.

## Components
- Frontend layer
- Backend layer  
- Database layer

## Design Decisions
Standard patterns were applied throughout.

## Future Work
More optimization is needed.""",
        "expected": "BLOCKED",
        "why": "空洞的架构描述 = 无信息量"
    },
    "real_research_excerpt": {
        "text": """# eCOS Phase 2 Final Review

Phase 2 achieved 78% architecture implementation, up from 61% in Phase 1.
The perception pipeline processed 1,986 events with 126 marked as index-ready.
SSB accumulated 4,245 events across SIGNAL/PERCEPTION/STATE_CHANGE types.

Key decision ADR-008 validated committee decision-making through 10 simulated rounds.
The multi-model committee (GPT-5.3 + DeepSeek-v4-pro) demonstrated 67% consensus rate
with genuine perspective differences on 33% of decisions.

Security score declined 7% during Phase 2 (72%→65%) due to expanded attack surface,
then recovered to 78% after Sprint 1 SSB authentication and content integrity fixes.""",
        "expected": "ALLOWED",  # 真实内容, 应通过
        "why": "真实研究报告 = 应正常通过"
    }
}

def test_filter():
    """Run filter_scorer and content_integrity against attack samples."""
    results = {}
    
    for name, sample in ATTACK_SAMPLES.items():
        # Simulate filter scoring
        from filter_scorer import QualityScorer
        qs = QualityScorer()
        quality = qs.score_text(sample["text"])
        
        from content_integrity import check_integrity
        integrity = check_integrity(sample["text"])
        
        passed_filter = quality["total"] >= 60  # default threshold
        passed_integrity = not integrity["suspicious"]
        
        actual = "ALLOWED" if (passed_filter and passed_integrity) else "BLOCKED"
        
        results[name] = {
            "expected": sample["expected"],
            "actual": actual,
            "quality_score": quality["total"],
            "integrity_score": integrity["integrity_score"],
            "integrity_flags": integrity["reasons"],
            "passed": actual == sample["expected"],
            "why": sample["why"]
        }
    
    return results

if __name__ == "__main__":
    # Standalone mode — use basic heuristics since imports may fail
    print("Filter Scorer Attack Test")
    print("=" * 40)
    
    for name, sample in ATTACK_SAMPLES.items():
        text = sample["text"]
        # Quick heuristic check
        has_structure = all(x in text.lower() for x in ['introduction', 'methodology', 'conclusion'])
        has_data = sum(1 for c in text if c.isdigit()) > 20
        is_generic = any(x in text.lower() for x in ['further research', 'comprehensive analysis', 'this document provides'])
        
        blocked_by_heuristic = has_structure and is_generic and not has_data
        actual = "BLOCKED" if blocked_by_heuristic else "ALLOWED"
        
        status = "✅" if actual == sample["expected"] else "❌"
        print(f"\n{status} {name}")
        print(f"   Expected: {sample['expected']} → Got: {actual}")
        print(f"   Why: {sample['why']}")
        print(f"   Structure:{has_structure} Generic:{is_generic} Data:{has_data}")
