#!/usr/bin/env python3
"""
SSB Schema V1 迁移
- 为旧事件补全 timestamp, event_type, schema_version 字段
- 幂等: 已有字段不覆盖
- 安全: 自动备份原文件
"""
import json, os, sys, shutil, time
from datetime import datetime, timedelta

SSB_PATH = os.path.expanduser("~/Workspace/eCOS/LADS/ssb/ecos.jsonl")
BACKUP = SSB_PATH + f".backup.{int(time.time())}"

# Agent → event_type 推断映射
AGENT_TYPE_MAP = {
    "CAPTURE_WATCHER": "CAPTURE_PERCEPTION",
    "FILTER_SCORER": "FILTER_SCORED",
    "KANBAN_BRIDGE": "KANBAN_SYNC",
    "INTEGRATE_PIPELINE": "INTEGRATE_RUN",
}

# ─── Backup ───
shutil.copy2(SSB_PATH, BACKUP)
print(f"📦 备份: {BACKUP}")

# ─── Read ───
with open(SSB_PATH) as f:
    lines = f.readlines()

events = []
for line in lines:
    line = line.strip()
    if not line:
        continue
    try:
        events.append(json.loads(line))
    except json.JSONDecodeError:
        print(f"  ⚠️ 跳过损坏行: {line[:60]}")
        events.append({"raw": line, "_corrupt": True})

# ─── Migrate ───
T0 = datetime(2026, 5, 8, 0, 0, 0)  # Phase 1 开始日期
INTERVAL = timedelta(minutes=2)  # 每个事件间隔2分钟
BASE_SEQ = 1000

stats = {
    "total": len(events),
    "added_timestamp": 0,
    "added_event_type": 0,
    "added_schema": 0,
    "corrupt": 0,
    "skipped": 0,
}

migrated = []

for i, event in enumerate(events):
    if event.get("_corrupt"):
        migrated.append(json.dumps(event, ensure_ascii=False))
        stats["corrupt"] += 1
        continue
    
    modified = False
    
    # 1. Add schema_version
    if "schema_version" not in event:
        event["schema_version"] = "1.0"
        stats["added_schema"] += 1
        modified = True
    
    # 2. Add timestamp (from seq order)
    if "timestamp" not in event or not event.get("timestamp"):
        seq = event.get("seq", 0)
        if isinstance(seq, int) and seq > 0:
            offset = max(0, seq - BASE_SEQ)
            event["timestamp"] = (T0 + offset * INTERVAL).timestamp()
        else:
            event["timestamp"] = (T0 + i * INTERVAL).timestamp()
        stats["added_timestamp"] += 1
        modified = True
    
    # 3. Normalize event_type
    if not event.get("event_type") or event.get("event_type") == "?":
        agent = event.get("agent", "")
        event["event_type"] = AGENT_TYPE_MAP.get(agent, "UNKNOWN")
        stats["added_event_type"] += 1
        modified = True
    
    if modified:
        stats["skipped"] += 0  # keep counting, don't double-count
    migrated.append(json.dumps(event, ensure_ascii=False))

# ─── Write ───
with open(SSB_PATH, "w") as f:
    f.write("\n".join(migrated) + "\n")

# ─── Verify ───
with open(SSB_PATH) as f:
    verify_lines = f.readlines()

verify_events = [json.loads(l) for l in verify_lines if l.strip()]

# Check coverage
ts_count = sum(1 for e in verify_events if e.get("timestamp", 0) > 0)
schema_count = sum(1 for e in verify_events if e.get("schema_version") == "1.0")
et_count = sum(1 for e in verify_events if e.get("event_type") and e.get("event_type") != "?")

print(f"\n📊 迁移统计:")
print(f"  总事件:   {stats['total']}")
print(f"  +timestamp: {stats['added_timestamp']}")
print(f"  +event_type: {stats['added_event_type']}")
print(f"  +schema:   {stats['added_schema']}")
print(f"  损坏:      {stats['corrupt']}")

print(f"\n✅ 验证:")
print(f"  timestamp覆盖: {ts_count}/{len(verify_events)} ({ts_count/len(verify_events)*100:.1f}%)")
print(f"  schema覆盖: {schema_count}/{len(verify_events)} ({schema_count/len(verify_events)*100:.1f}%)")
print(f"  event_type正常: {et_count}/{len(verify_events)} ({et_count/len(verify_events)*100:.1f}%)")

# Show samples
print(f"\n📋 迁移后Sample:")
for e in verify_events[:3]:
    print(f"  seq={e.get('seq')} agent={e.get('agent')} type={e.get('event_type')} "
          f"schema={e.get('schema_version')}")
