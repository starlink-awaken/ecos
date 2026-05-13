# ADR-005: SSB 共享语义总线作为 Agent 间通信标准

- **状态**: 已接受（Schema 设计 pending）
- **日期**: 2026-05-13
- **决策者**: 夏铭星 + Hermes

## 背景

多 Agent 协作需要标准化的通信协议。若允许 Agent 间私下直接通信，会导致：
- 决策过程不透明，无法审计
- 语义不一致，理解偏差累积
- 难以实现蜂群涌现（无共享信息素场）

## 决策

建立 **SSB（Shared Semantic Bus，共享语义总线）**：

**设计原则：**
- 信息素场模型：类比蚂蚁的信息素，Agent 向 SSB 写入语义标记，其他 Agent 感知并响应
- 不编程协作行为，让协作从语义共享中自然涌现
- 所有委员会消息必须经过 SSB，不允许私下绕过

**Event Schema（草案，待正式设计）：**
```yaml
ssb_event:
  id: uuid-v4
  timestamp: ISO8601
  from_agent: string
  to_agent: ALL | role_name
  session_id: uuid
  type: PROPOSAL|CRITIQUE|VOTE|DECISION|ACTION|RESULT|SIGNAL
  payload:
    content: string
    confidence: float(0-1)   # 贝叶斯置信度
    risk_level: LOW|MED|HIGH|CRITICAL
    references: []
```

**P0 任务：** 设计完整的 SSB Event Schema v1，包括：
- 完整 Event 类型枚举
- 路由规则
- 持久化策略
- 与 SharedBrain B-OS 的集成方式

## 后果

- 正面：全透明通信，支持蜂群涌现，可审计
- 风险：SSB 成为单点瓶颈，Schema 设计不当影响所有 Agent
- 缓解：SSB 设计为异步消息总线，不阻塞 Agent 执行；Schema 通过 RFC 流程评审
