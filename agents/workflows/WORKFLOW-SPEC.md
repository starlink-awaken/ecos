# Workflow 定义规范

> 所有委员会执行的 Workflow 必须按本规范定义。
> 版本: v0.1.0-draft

---

## Workflow 文件命名

```
WF-NNN-workflow-name.md
例：WF-001-kos-daily-index.md
    WF-002-research-deep-dive.md
```

---

## Workflow 模板

```yaml
# Workflow 元数据
id: "WF-NNN"
name: "Workflow 名称"
version: "0.1.0"
trigger: "manual | cron: '0 9 * * *' | event: SSB_EVENT_TYPE"
priority: "P0 | P1 | P2"
risk_level: "LOW | MED | HIGH | CRITICAL"
committee_required: true | false   # HIGH/CRITICAL 必须 true

# 参与角色（委员会）
roles:
  required: [CHAIR, EXEC, AUDIT, SCRIBE]
  optional: [RESEARCH, KOS, CRITIC, PLANNER]

# 输入
inputs:
  - name: param_name
    type: string | number | bool
    required: true | false
    description: "..."

# 步骤定义
steps:
  - id: S01
    name: "步骤名称"
    agent: EXEC | RESEARCH | ...
    action: "具体操作描述"
    tool: "hermes_tool_name | mcp_tool_name"
    on_success: S02
    on_failure: ROLLBACK | ESCALATE | HUMAN_NOTIFY

# 回滚策略
rollback:
  strategy: "FULL | PARTIAL | NONE"
  steps: []   # 回滚步骤

# 完成动作（必须）
on_complete:
  - update_state: true     # 更新 STATE.yaml
  - write_handoff: true    # 更新 HANDOFF/LATEST.md
  - write_adr: false       # 是否产生 ADR
  - write_failure: false   # 是否记录失败（条件触发）
```

---

## 已规划 Workflow 列表

| ID | 名称 | 触发方式 | 状态 |
|----|------|----------|------|
| WF-001 | KOS 每日索引更新 | cron daily | 待设计 |
| WF-002 | Minerva 深度研究 | manual | 待设计 |
| WF-003 | 系统健康检查 | cron weekly | 待设计 |
| WF-004 | 委员会决策会议 | manual | 待设计 |
| WF-005 | HANDOFF 自动更新 | 每次会话结束 | 待设计 |

---

*版本: v0.1.0-draft*
*创建: 2026-05-13*
