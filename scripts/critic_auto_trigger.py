#!/usr/bin/env python3
"""
CRITIC Auto-Trigger — 自动触发独立审查 (Phase 4 Sprint 3)

触发规则:
  R1: AUDIT发现MED+风险 → auto CRITIC
  R2: 涉及GENOME.md或L1宪法 → forced CRITIC
  R3: EXEC方案差异度 > 50% → flag CRITIC
  R4: IRREVERSIBLE-OPS Level 3 → forced CRITIC
  R5: 批量操作 (>5 cron/SSB) → flag CRITIC

输出: CRITIC触发决策 + 审查指令
"""

import json
import os
import sys
import re
import time
import yaml
from datetime import datetime

ECOS = os.path.expanduser("~/Workspace/eCOS")
STATE_PATH = os.path.join(ECOS, "STATE.yaml")
SSB = os.path.join(ECOS, "LADS/ssb/ecos.jsonl")
GENOME = os.path.join(ECOS, "GENOME.md")

# ─── Risk Scoring ───
RISK_LEVELS = {
    "LOW":    {"score": 1,  "critic": False, "desc": "低风险"},
    "MED":    {"score": 5,  "critic": True,  "desc": "中风险 — 需CRITIC审查"},
    "HIGH":   {"score": 10, "critic": True,  "desc": "高风险 — 强制CRITIC"},
    "CRITICAL":{"score": 25,"critic": True,  "desc": "严重 — 强制CRITIC+人类确认"},
}

TRIGGER_RULES = {
    "R1_AUDIT_MED": {
        "pattern": r"MED|HIGH|CRITICAL",
        "source": "AUDIT评估",
        "action": "auto_critic",
        "priority": 1,
    },
    "R2_L1_CHANGE": {
        "pattern": r"GENOME\.md|L1|宪法|公理",
        "source": "操作内容",
        "action": "forced_critic",
        "priority": 1,
    },
    "R3_EXEC_DIVERGE": {
        "pattern": r"差异|diverge|alternative",
        "source": "EXEC方案",
        "action": "flag_critic",
        "priority": 2,
    },
    "R4_IRREVERSIBLE_L3": {
        "pattern": r"irreversible|不可逆|Level 3|HUMAN_CONFIRMATION",
        "source": "操作级别",
        "action": "forced_critic",
        "priority": 1,
    },
    "R5_BATCH_OPERATION": {
        "pattern": r"批量|batch|all|全部|创建.*\d+|删除所有",
        "source": "操作规模",
        "action": "flag_critic",
        "priority": 2,
    },
}


def assess_risk(operation: str, context: dict = None) -> dict:
    """评估操作风险并决定是否触发CRITIC"""
    
    triggers = []
    risk_score = 0
    
    for rule_name, rule in TRIGGER_RULES.items():
        if re.search(rule["pattern"], operation, re.IGNORECASE):
            triggers.append({
                "rule": rule_name,
                "source": rule["source"],
                "action": rule["action"],
                "priority": rule["priority"],
            })
            # Score based on action
            if rule["action"] == "forced_critic":
                risk_score += 15
            elif rule["action"] == "auto_critic":
                risk_score += 8
            elif rule["action"] == "flag_critic":
                risk_score += 3
    
    # Determine level
    if risk_score >= 25:
        level = "CRITICAL"
    elif risk_score >= 10:
        level = "HIGH"
    elif risk_score >= 5:
        level = "MED"
    else:
        level = "LOW"
    
    need_critic = level in ("MED", "HIGH", "CRITICAL")
    force_critic = any(t["action"] == "forced_critic" for t in triggers)
    
    return {
        "operation": operation[:120],
        "risk_score": risk_score,
        "risk_level": level,
        "need_critic": need_critic,
        "force_critic": force_critic,
        "triggers": triggers,
        "timestamp": datetime.now().isoformat(),
    }


def generate_critic_instruction(assessment: dict) -> str:
    """生成CRITIC审查指令"""
    if not assessment["need_critic"]:
        return ""
    
    triggers_str = ", ".join(t["rule"] for t in assessment["triggers"])
    force = "🔴 强制" if assessment["force_critic"] else "🟡 建议"
    
    return f"""
CRITIC审查请求 — {assessment['risk_level']} {force}

操作: {assessment['operation'][:80]}
风险评分: {assessment['risk_score']}/25
触发规则: {triggers_str}

请执行独立审查:
  1. 该操作是否符合GENOME.md的5条公理？
  2. 是否属于IRREVERSIBLE-OPS中的不可逆操作？
  3. 是否有更安全的替代方案？
  4. 如果必须执行，需要哪些安全措施？

审查结论: [APPROVE / REJECT / NEED_MORE_INFO]
"""


# ─── Emergence Metrics ───
def compute_emergence_metrics() -> dict:
    """计算涌现度量指标"""
    
    # Read SSB
    with open(SSB) as f:
        events = [json.loads(l) for l in f if l.strip()]
    
    # Time window: last 24h vs last 7d
    now = time.time()
    day_ago = now - 86400
    week_ago = now - 604800
    
    # Handle mixed timestamp formats (float epoch or ISO string)
    def _ts(e):
        ts = e.get("timestamp", 0)
        if isinstance(ts, (int, float)):
            return float(ts)
        try:
            from datetime import datetime
            return datetime.fromisoformat(str(ts).replace('Z', '+00:00')).timestamp()
        except:
            return 0.0

    recent_events = [e for e in events if _ts(e) > day_ago]
    week_events = [e for e in events if _ts(e) > week_ago]
    
    # Metrics
    agents = set(e.get("agent", "?") for e in week_events)
    event_types = set(e.get("event_type", "?") for e in week_events)
    
    # Collaboration: unique agent interactions
    agent_pairs = set()
    for i, e1 in enumerate(week_events):
        for e2 in week_events[i+1:i+10]:
            a1, a2 = e1.get("agent"), e2.get("agent")
            if a1 and a2 and a1 != a2:
                agent_pairs.add(tuple(sorted([a1, a2])))
    
    # Decision quality: errors / total
    errors = [e for e in week_events if "error" in str(e.get("action", "")).lower()
              or "fail" in str(e.get("action", "")).lower()]
    
    # Knowledge growth: new doc events
    doc_events = [e for e in week_events 
                  if "doc" in str(e.get("event_type", "")).lower()
                  or "knowledge" in str(e.get("event_type", "")).lower()]
    
    return {
        "timestamp": datetime.now().isoformat(),
        "time_window": "7d",
        "collaboration": {
            "total_events_7d": len(week_events),
            "total_events_24h": len(recent_events),
            "unique_agents": len(agents),
            "agent_interactions": len(agent_pairs),
            "agents_list": sorted(agents),
        },
        "decision_quality": {
            "total_actions": len(week_events),
            "errors": len(errors),
            "error_rate": round(len(errors) / max(len(week_events), 1), 4),
        },
        "knowledge_growth": {
            "doc_events_7d": len(doc_events),
            "events_per_day": round(len(week_events) / 7, 1),
        },
        "emergence_score": {
            "diversity": round(len(agents) / 10, 2),  # 0-1
            "interaction_density": round(len(agent_pairs) / max(len(agents)**2, 1), 2),
            "error_resilience": round(1 - len(errors) / max(len(week_events), 1), 2),
            "knowledge_velocity": round(len(doc_events) / 7, 1),
        }
    }


def update_state_metrics(metrics: dict):
    """将涌现度量写入STATE.yaml"""
    state_path = os.path.join(ECOS, "STATE.yaml")
    
    with open(state_path) as f:
        state = yaml.safe_load(f) or {}
    
    state["emergence"] = {
        "diversity": metrics["emergence_score"]["diversity"],
        "interaction_density": metrics["emergence_score"]["interaction_density"],
        "error_resilience": metrics["emergence_score"]["error_resilience"],
        "knowledge_velocity": metrics["emergence_score"]["knowledge_velocity"],
        "updated": datetime.now().isoformat(),
    }
    
    with open(state_path, "w") as f:
        yaml.dump(state, f, allow_unicode=True, default_flow_style=False)
    
    return state


# ─── CLI ───
if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--check", type=str, help="检查操作是否需要CRITIC")
    p.add_argument("--metrics", action="store_true", help="计算涌现度量")
    p.add_argument("--update-state", action="store_true", help="更新STATE.yaml")
    args = p.parse_args()
    
    if args.check:
        result = assess_risk(args.check)
        print(json.dumps(result, indent=2, ensure_ascii=False))
        if result["need_critic"]:
            print(generate_critic_instruction(result))
    
    if args.metrics:
        metrics = compute_emergence_metrics()
        print(json.dumps(metrics, indent=2, ensure_ascii=False))
        
        if args.update_state:
            update_state_metrics(metrics)
            print("\n✅ STATE.yaml 已更新涌现度量")
