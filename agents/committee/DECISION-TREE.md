# 委员会决策树 — 何时用三角模式 vs WF-004

> Sprint 5 | 解决 D5: 两套委员会机制并存但无明确决策树

---

## 决策流程

```
高风险操作 / 复杂决策?

    否 → 三角模式 (Phase 1)
          CHAIR/EXEC/AUDIT 角色切换
          耗时 < 5 分钟
          适用: 日常决策、文档修改、MED风险以下

    是 → 涉及 L0/L1 或 CRITICAL 风险?

             否 → WF-004 标准模式
                  CHAIR + 2×EXEC并行 + AUDIT串行
                  耗时 ~3 分钟
                  适用: HIGH风险、新Workflow设计

             是 → WF-004 强化模式
                  CHAIR + 2×EXEC并行 + AUDIT串行 + CRITIC
                  耗时 ~5 分钟
                  适用: L0/L1变更、安全策略、CRITICAL风险
```

## 触发条件速查

| 场景 | 模式 | 角色 | 耗时 |
|------|------|------|------|
| 文档修改、参数调整 | 三角 | CHAIR+EXEC+AUDIT | <5min |
| 新 Workflow 设计 | WF-004标准 | +2×EXEC | ~3min |
| 安全策略变更 | WF-004强化 | +CRITIC | ~5min |
| L0/L1 宪法变更 | WF-004强化 | +CRITIC + 人类确认 | ~5min+ |
| 不可逆操作(三级) | 三角+人类确认 | CHAIR+AUDIT | <2min+ |

## 与现有文件的关系

- 三角模式: `agents/committee/PHASE1-TRIANGLE.md`
- WF-004: `agents/workflows/WF-004-committee-meeting.md`
- 本文件: 决策路由表 (Agent 入口)
