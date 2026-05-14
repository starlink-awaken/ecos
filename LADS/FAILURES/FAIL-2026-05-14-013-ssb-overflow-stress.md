---
fail_id: FAIL-2026-05-14-013-ssb-overflow-stress
date: "2026-05-14"
severity: MED
domain: 加速验证
status: OPEN
reported_by: 加速验证脚本
---

# Ssb Overflow Stress

## 失败描述
**加速验证场景:** 553 events triggered slow query performance (>2s)
**模拟时间:** 2026-05-14T09:52:21.122992
**验证目标:** 快速积累失败案例至 15

## 根因
系统压力测试中自然产生的失败模式。

## 经验萃取
> 加速验证暴露: 553 events triggered slow query performance (>2s)
