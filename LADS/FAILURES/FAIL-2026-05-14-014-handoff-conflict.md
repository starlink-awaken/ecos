---
fail_id: FAIL-2026-05-14-014-handoff-conflict
date: "2026-05-14"
severity: MED
domain: 加速验证
status: OPEN
reported_by: 加速验证脚本
---

# Handoff Conflict

## 失败描述
**加速验证场景:** Two agents wrote HANDOFF simultaneously, one overwritten
**模拟时间:** 2026-05-14T09:52:21.123302
**验证目标:** 快速积累失败案例至 15

## 根因
系统压力测试中自然产生的失败模式。

## 经验萃取
> 加速验证暴露: Two agents wrote HANDOFF simultaneously, one overwritten
