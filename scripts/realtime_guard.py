#!/usr/bin/env python3
"""
Realtime Guard — pre-operation safety check (Phase 3 Sprint 3)
Usage: python3 realtime_guard.py <operation> [--auto-deny]

Checks IRREVERSIBLE-OPS before allowing execution.
Exit 0 = safe, Exit 1 = blocked.
"""
import json, sys, os
from pathlib import Path

IRREVERSIBLE_OPS = {
    "send_message":      {"level": 3, "reason": "消息已抵达用户设备，不可撤回"},
    "himalaya send":     {"level": 3, "reason": "SMTP协议无撤回机制"},
    "xurl post":         {"level": 3, "reason": "已推送至第三方平台"},
    "git push":          {"level": 3, "reason": "已推送至远程，force push有风险"},
    "rm -rf":            {"level": 3, "reason": "无备份则永久丢失"},
    "DROP TABLE":        {"level": 3, "reason": "无备份则永久丢失"},
    "DELETE FROM":       {"level": 2, "reason": "SQL删除，可回滚但需确认"},
    "curl POST":         {"level": 2, "reason": "外部API写操作"},
    "cronjob create":    {"level": 2, "reason": "新建定时任务"},
    "cronjob update":    {"level": 2, "reason": "修改定时任务"},
    "delegate_task":     {"level": 1, "reason": "子Agent可逆"},
    "read_file":         {"level": 0, "reason": "只读操作"},
    "search":            {"level": 0, "reason": "只读操作"},
}

def check(operation: str, auto_deny: bool = False) -> dict:
    """Check if operation is safe. Returns {allowed, level, reason}."""
    op_lower = operation.lower()
    
    # Match
    matched = None
    for pattern, info in sorted(IRREVERSIBLE_OPS.items(), key=lambda x: -len(x[0])):
        if pattern.lower() in op_lower:
            matched = (pattern, info)
            break
    
    if not matched:
        return {"allowed": True, "level": 0, "reason": "No matching rule", "op": operation}
    
    pattern, info = matched
    
    if info["level"] >= 3:
        if auto_deny:
            return {"allowed": False, "level": info["level"], "reason": info["reason"],
                    "op": operation, "blocked_by": "auto-deny (level 3)"}
        return {"allowed": False, "level": info["level"], "reason": info["reason"],
                "op": operation, "requires": "HUMAN_CONFIRMATION"}
    
    if info["level"] == 2:
        return {"allowed": False, "level": info["level"], "reason": info["reason"],
                "op": operation, "requires": "TRIANGLE_CHECK"}
    
    return {"allowed": True, "level": info["level"], "reason": info["reason"], "op": operation}

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: realtime_guard.py <operation> [--auto-deny]")
        sys.exit(1)
    
    op = " ".join(sys.argv[1:]).replace(" --auto-deny", "")
    auto_deny = "--auto-deny" in " ".join(sys.argv[1:])
    
    result = check(op, auto_deny)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    
    if not result["allowed"]:
        sys.exit(1)
