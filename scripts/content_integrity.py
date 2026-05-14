#!/usr/bin/env python3
"""
Content Integrity Checker — detects templated/boilerplate content that passes structural scoring.
Runs as post-filter, marks suspicious documents.
"""
import re, json, sys
from pathlib import Path

def check_integrity(text: str) -> dict:
    """Score content authenticity. Returns {suspicious: bool, score: 0-100, reasons: []}"""
    reasons = []
    score = 100
    
    # 1. Generic section headers (no real content)
    generic_headers = ['introduction', 'background', 'methodology', 'results', 'conclusion',
                       '附录', '参考资料', '免责声明']
    found_generic = sum(1 for h in generic_headers if h.lower() in text.lower())
    if found_generic >= 3:
        score -= 30
        reasons.append(f"generic_headers({found_generic})")
    
    # 2. Placeholder/boilerplate patterns
    boilerplate = [
        r'further research is needed',
        r'automatically generated',
        r'this document provides',
        r'comprehensive analysis of',
        r'lorem ipsum',
    ]
    for bp in boilerplate:
        if re.search(bp, text, re.IGNORECASE):
            score -= 15
            reasons.append(f"boilerplate({bp[:30]})")
    
    # 3. Content density (too many headers vs body)
    headers = len(re.findall(r'^#+\s', text, re.MULTILINE))
    lines = text.count('\n')
    if headers > 3 and lines < 20:
        score -= 20
        reasons.append(f"low_density(h={headers},l={lines})")
    
    # 4. Named sections with no substantive content
    empty_sections = re.findall(r'^#{1,3}\s+(.+?)$\s*(?=^#{1,3}\s|\Z)', text, re.MULTILINE)
    for sec in empty_sections:
        if len(sec) > 20 and any(w in sec.lower() for w in ['analysis','methodology','conclusion','protocol']):
            score -= 10
            reasons.append(f"empty_section({sec[:30]})")
    
    return {
        "suspicious": score < 50,
        "integrity_score": max(0, min(100, score)),
        "reasons": reasons[:5]
    }

if __name__ == "__main__":
    if len(sys.argv) > 1:
        path = Path(sys.argv[1])
        text = path.read_text()
        result = check_integrity(text)
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        # Test: attack doc pattern
        test = """# Comprehensive Analysis
## Introduction
This document provides a thorough examination.
## Methodology
- Item 1: Data
- Item 2: Analysis
## Results
| Metric | Value |
|--------|-------|
| Score | 95 |
## Conclusion
Further research is needed."""
        result = check_integrity(test)
        print("Test (boilerplate):", json.dumps(result, indent=2, ensure_ascii=False))
