# WF-006: 感知管道 (Perception Pipeline)

> 所属层: L2 感知层 | 对应 Sprint 2
> 版本: v1.0 | 创建: 2026-05-14

---

## 触发

```yaml
trigger: "0 * * * *"  # 每小时
deliver: "local"       # 不推送，写入 SSB
skills: []
prompt: |
  运行感知管道:
  1. 运行 capture_watcher.py --scan (检测新文件)
  2. 运行 filter_scorer.py --run (评分+过滤)
  3. 检查捕获数量和过滤结果
```

## 流程

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│ Capture     │ →   │ Filter      │ →   │ Index Queue │
│ watcher.py  │     │ scorer.py   │     │ (SSB Event) │
└─────────────┘     └─────────────┘     └─────────────┘
     ↓                    ↓                    ↓
 PERCEPTION         quality≥60        STATE_CHANGE
 Event → SSB        + relevance≥40    → INDEX_READY
                    → INDEX_READY     → action_req=EXECUTE
```

## 脚本路径

| 脚本 | 路径 |
|------|------|
| capture_watcher.py | `scripts/capture_watcher.py` |
| filter_scorer.py | `scripts/filter_scorer.py` |

## 监控目录

| 目录 | 类型 | 说明 |
|------|------|------|
| `~/knowledge/reports/` | report | Minerva 研究报告 |
| `~/Workspace/eCOS/LADS/HANDOFF/` | handoff | 系统交接件 |
| `~/Workspace/eCOS/LADS/FAILURES/` | failure | 失败记录 |

## 验证标准

- [ ] capture_watcher 检测新文件 → SSB PERCEPTION Event
- [ ] SHA256 防重 → 同一文件不重复捕获
- [ ] filter_scorer 评分 → quality ≥ 60 触发 INDEX_READY
- [ ] 过滤记录持久化到 SSB (SIGNAL/FILTERED 类型)
- [ ] 每小时 cron 自动运行无报错
