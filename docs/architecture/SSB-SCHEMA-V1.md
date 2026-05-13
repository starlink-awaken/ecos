# SSB Event Schema v1

> 共享语义总线（Shared Semantic Bus）事件格式定义
> 版本: v0.1.0-draft
> 状态: 初稿，待 RFC-0001 讨论
> 创建: 2026-05-13
> 关联: ADR-005, CHARTER.md

---

## 设计原则

1. **异步优先**：消息不应阻塞 Agent 执行
2. **可回溯**：所有消息持久化，支持事后审计
3. **语义化**：消息承载语义而非原始数据——每条消息回答 Why，不仅 What
4. **信息素场**：消息留在总线上的时间足够长，让其他 Agent 感知到系统状态变化
5. **Phase 1 最简实现**：Phase 1 中 SSB 退化为文件读写，Schema 保持完整以便 Phase 2 升级

---

## Event 结构

```json
{
  "ssb_version": "1.0",
  "event_id": "uuid-v4",
  "timestamp": "2026-05-13T11:37:50+08:00",
  "session_id": "uuid-v4 (committee session or hermes session)",
  "source": {
    "agent": "HERMES | CHAIR | EXEC | AUDIT | SCRIBE | RESEARCH | KOS | CRITIC | PLANNER | HUMAN | SYSTEM",
    "instance": "hermes-main | delegate-task-001 | cron-job-003"
  },
  "target": {
    "scope": "ALL | ROLE:<role> | AGENT:<instance> | SSB_PERSIST",
    "routing_hint": "optional routing info"
  },
  "event": {
    "type": "SIGNAL | PROPOSAL | CRITIQUE | VOTE | DECISION | ACTION_START | ACTION_RESULT | STATE_CHANGE | FAILURE | HANDOFF | PERCEPTION",
    "subtype": "optional more specific type"
  },
  "payload": {
    "summary": "one-line human-readable summary",
    "detail": "full message content",
    "confidence": 0.85,
    "risk_level": "LOW | MED | HIGH | CRITICAL",
    "priority": "P0 | P1 | P2 | P3",
    "references": [
      {
        "type": "ADR | RFC | WORKFLOW | HANDOFF | FAILURE | GENOME | URL | FILE",
        "id": "ADR-001",
        "path": "/Users/xiamingxing/Workspace/eCOS/docs/decisions/ADR/ADR-001-ecos-positioning.md"
      }
    ],
    "action_required": "NONE | ACK | DECIDE | EXECUTE | HUMAN_APPROVAL",
    "deadline": "optional ISO8601 if action required by deadline"
  },
  "semantic": {
    "intent": "what the source intends by this message",
    "state_change": "what state change this message represents",
    "prior_belief": "optional, for Bayesian update events",
    "posterior_belief": "optional, for Bayesian update events",
    "tags": ["tag1", "tag2"]
  }
}
```

---

## Event Type 枚举

### SIGNAL — 信息素信号
Agent 向总线广播当前状态，不要求响应。类似于蚂蚁留下的信息素。

```json
{
  "event": {"type": "SIGNAL", "subtype": "HEARTBEAT | CAPABILITY | STATUS"},
  "payload": {
    "summary": "KOS daily indexing completed",
    "detail": "Indexed 1,247 new documents, 3 conflicts resolved",
    "confidence": 1.0,
    "risk_level": "LOW",
    "action_required": "NONE"
  }
}
```

### PROPOSAL — 提案
Agent 提出一个方案供讨论或决策。

```json
{
  "event": {"type": "PROPOSAL"},
  "payload": {
    "summary": "Propose adding cron job for daily KOS index update",
    "detail": "WF-001 would run at 02:00 CST daily...",
    "action_required": "DECIDE",
    "deadline": "2026-05-15T00:00:00+08:00"
  }
}
```

### CRITIQUE — 批评/审查
AUDIT 或 CRITIC 对提案的独立评估。

```json
{
  "event": {"type": "CRITIQUE"},
  "payload": {
    "summary": "WF-001 proposal risks: no rollback strategy defined",
    "detail": "If indexing fails mid-run, KOS database may be in inconsistent state...",
    "confidence": 0.90,
    "risk_level": "MED",
    "action_required": "ACK"
  }
}
```

### VOTE — 表决
委员会成员的投票。

```json
{
  "event": {"type": "VOTE", "subtype": "APPROVE | REJECT | ABSTAIN"},
  "payload": {
    "summary": "CHAIR votes APPROVE on WF-001 after CRITIQUE addressed",
    "confidence": 0.75,
    "action_required": "NONE"
  }
}
```

### DECISION — 决策
委员会形成的最终决议。

```json
{
  "event": {"type": "DECISION"},
  "payload": {
    "summary": "Committee approves WF-001 with rollback amendment",
    "detail": "Votes: CHAIR=APPROVE, EXEC=APPROVE, AUDIT=APPROVE. Amendment: add rollback step before indexing.",
    "action_required": "EXECUTE",
    "references": [
      {"type": "RFC", "id": "RFC-0001"},
      {"type": "WORKFLOW", "id": "WF-001"}
    ]
  }
}
```

### ACTION_START / ACTION_RESULT — 执行追踪
行动开始和结果。

```json
{
  "event": {"type": "ACTION_START"},
  "payload": {
    "summary": "Starting cron job creation for WF-001",
    "action_required": "NONE"
  }
}
```

```json
{
  "event": {"type": "ACTION_RESULT", "subtype": "SUCCESS | PARTIAL | FAILURE"},
  "payload": {
    "summary": "WF-001 cron job created successfully, schedule: 0 2 * * *",
    "confidence": 1.0,
    "risk_level": "LOW",
    "action_required": "NONE"
  }
}
```

### STATE_CHANGE — 状态变更
系统状态发生变化。

```json
{
  "event": {"type": "STATE_CHANGE"},
  "payload": {
    "summary": "STATE.yaml updated after WF-001 deployment",
    "detail": "T05 marked completed, T06 moved to in_progress"
  },
  "semantic": {
    "state_change": "WF-001 from DRAFT to DEPLOYED"
  }
}
```

### FAILURE — 失败事件
失败发生时自动生成。

```json
{
  "event": {"type": "FAILURE", "subtype": "BOOLEAN | DEVIATION | BOUNDARY | DATA_LOSS | WORKFLOW"},
  "payload": {
    "summary": "Hermes attempted email send without human confirmation (L0-02 violation blocked)",
    "detail": "Pre-action check caught missing confirmation. Blocked before execution.",
    "confidence": 1.0,
    "risk_level": "HIGH",
    "action_required": "HUMAN_APPROVAL"
  }
}
```

### HANDOFF — 交接
Agent 会话结束时的上下文交接。

```json
{
  "event": {"type": "HANDOFF"},
  "payload": {
    "summary": "Hermes session ending. Handoff written.",
    "detail": "Next agent should prioritize P0 tasks in STATE.yaml",
    "action_required": "NONE",
    "references": [
      {"type": "HANDOFF", "id": "LATEST"}
    ]
  }
}
```

### PERCEPTION — 感知事件
感知层管道产出的结构化信息。

```json
{
  "event": {"type": "PERCEPTION"},
  "payload": {
    "summary": "New document detected: KOS-Product-Plan-2026-05-12.md",
    "detail": "Captured from ~/Documents/, classified as KOS-related, ready for indexing",
    "action_required": "EXECUTE"
  }
}
```

---

## Phase 1 最小化实现

Phase 1 中，SSB 退化为以下机制：

```
HANDOFF/LATEST.md   ←→  Agent 间唯一的总线消息（HANDOFF Event）
STATE.yaml          ←→  系统状态变更记录（STATE_CHANGE Event）
FAILURES/           ←→  失败事件归档（FAILURE Event）
```

即在 Phase 1 中，不实现真正的消息总线。上述三类文件读写就是 SSB 的全部内容。Schema 保持完整，为 Phase 2 的消息队列/总线实现做准备。

---

## Phase 2 升级路径

1. 选择消息队列后端（SQLite 简单方案 / NATS / Redis Streams）
2. 实现 SSB Client 库（Python），支持 Event 序列化/反序列化
3. Agent 启动时注入 SSB Client
4. 从文件读写迁移到消息队列
5. 保持 Schema 兼容，增加 Event History 查询能力

---

## 与 SharedBrain 的关系

SharedBrain B-OS 是 SSB 持久化的候选后端。选项：

| 方案 | 存储 | 查询 | 复杂度 |
|------|------|------|--------|
| 文件（Phase 1） | STATE.yaml + HANDOFF | grep/rg | 极低 |
| SQLite（Phase 2 初） | events 表 | SQL | 低 |
| SharedBrain B-OS（Phase 2 晚） | BOS-URI 路由 | BOS API + MCP | 中 |
| 消息队列（Phase 3） | NATS/Redis Streams | Stream 查询 | 高 |

---

*版本: v0.1.0-draft*
*关联: ADR-005*
