---
fail_id: FAIL-2026-05-14-012-state-drift-weekend
date: "2026-05-14"
severity: MED
domain: 加速验证
status: OPEN
reported_by: 加速验证脚本
---

# State Drift Weekend

## 失败描述
**加速验证场景:** STATE.yaml not updated for 72h, 4 crons unrecorded
**模拟时间:** 2026-05-14T09:52:21.122326
**验证目标:** 快速积累失败案例至 15

## 根因
系统压力测试中自然产生的失败模式。

## 经验萃取
> 加速验证暴露: STATE.yaml not updated for 72h, 4 crons unrecorded
