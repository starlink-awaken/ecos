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
| WF-001 | KOS 每日索引更新 | cron daily | 已上线 |
| WF-002 | Minerva 深度研究 | cron weekly | 已上线（周日首跑） |
| WF-003 | 系统健康检查 | cron daily | 已上线 |
| WF-004 | 委员会决策会议 | manual/schedule | 已设计（含 Kanban 调度） |
| WF-005 | HANDOFF 自动更新 | every 2h | 已上线 |
| WF-006 | 感知管道 | cron hourly | 已上线 |
| WF-007 | 实时安全检查 | cron every 6h | 已上线 |
| WF-008 | Kanban→SSB 事件桥接 | cron every 5min | 已实现，待部署 |

---

## 手动模式（Manual Mode）模板

每个 WF 文档必须包含此章节，确保不依赖 Agent 平台时也能执行。

```markdown
## 手动模式（降级/兜底时使用）

### 前置条件
- [ ] 读取 STATE.yaml 确认当前 Phase
- [ ] 读取 HANDOFF/LATEST.md 确认上次交接状态
- [ ] 检查 `schedule/{WF-ID}.yaml` 获取步骤描述

### 执行信息
- **WF-ID**: {WF-NNN}
- **步骤数**: N
- **调度驱动**: `python3 scripts/ecos_scheduler.py {WF-ID} --driver manual`

### 操作步骤

执行调度器输出操作手册：

```bash
cd ~/Workspace/eCOS
python3 scripts/ecos_scheduler.py {WF-ID} --driver manual
```

按手册逐条执行。每完成一步确认预期输出。

### 预期产出
- [ ] 各步骤中间产物
- [ ] STATE.yaml 更新（如有）
- [ ] HANDOFF/LATEST.md 更新
- [ ] SSB 事件记录

### 故障处理
- Kanban 可用但 Profile 不可用: `python3 scripts/ecos_scheduler.py {WF-ID} --driver manual` 代替
- Kanban 完全不可用: 直接读 SQLite 确认当前状态（见 AGENTS.md 兜底操作）
- 所有平台不可用: 纯人工执行 WORKFLOW-SPEC.md 中的步骤定义
```

---

*版本: v0.1.0-draft*
*创建: 2026-05-13*
