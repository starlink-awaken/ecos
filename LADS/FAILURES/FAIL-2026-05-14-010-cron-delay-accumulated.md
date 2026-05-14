---
fail_id: FAIL-2026-05-14-010-cron-delay-accumulated
date: "2026-05-14"
severity: MED
domain: 加速验证
status: OPEN
reported_by: 加速验证脚本
---

# Cron Delay Accumulated

## 失败描述
**加速验证场景:** WF-001 delayed 45min due to KOS indexer lock contention
**模拟时间:** 2026-05-14T09:52:21.122036
**验证目标:** 快速积累失败案例至 15

## 根因
系统压力测试中自然产生的失败模式。

## 经验萃取
> 加速验证暴露: WF-001 delayed 45min due to KOS indexer lock contention
