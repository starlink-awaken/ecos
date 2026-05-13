# KOS/Minerva/SharedBrain 身份定义

> Phase 1 中三个子系统的角色边界
> 版本: v0.1.0
> 创建: 2026-05-13（逻辑推演后补文档）

---

## 核心问题

eCOS 文档中存在术语歧义：KOS/Minerva 是"Agent"还是"Tool"？统称"子系统"回避了这个关键问题。

**Agent**：具有独立决策能力、可主动发起通信、拥有自身目标状态的实体。
**Tool**：被动调用、无独立决策权、通过 API/MCP 暴露能力的资源。

---

## Phase 1 身份定义

| 系统 | Phase 1 身份 | 通信方式 | 说明 |
|------|-------------|----------|------|
| KOS | **Tool (MCP)** | Hermes → MCP 调用 | 被动检索，不做决策 |
| Minerva | **Tool (MCP)** | Hermes → MCP 调用 | 被动研究，不做决策 |
| SharedBrain B-OS | **Storage Backend** | Hermes → API/文件读写 | SSB 持久化候选 |
| Hermes | **唯一的 Agent** | — | 唯一决策者，Phase1 没有多 Agent |

**关键推论：**
- Phase 1 中 **不存在"Agent 间通信"**。L0-05 在当前阶段无操作对象。
- SSB 在 Phase 1 退化为 STATE.yaml + HANDOFF.md 的文件读写。
- 委员会的 8 角色在 Phase 1 降级为 Hermes 的**角色切换模式**（见 PHASE1-TRIANGLE.md）。

---

## Phase 2 身份升级

| 系统 | Phase 2 身份 | 变化 |
|------|-------------|------|
| KOS | Tool → **半自主 Agent** | 可主动推送知识更新、索引变更通知 |
| Minerva | Tool → **半自主 Agent** | 可主动发起研究任务、报告产出 |
| SharedBrain | Storage → **SSB 消息总线的持久化层** | — |

---

## 判断标准：何时升级为 Agent？

系统满足以下条件时，考虑从 Tool 升级为 Agent：
1. 有独立的感知能力（不依赖 Hermes 推送信息）
2. 有独立的目标状态（能判断自己该做什么）
3. 能主动向 SSB 写入消息

**当前三个系统均不满足上述条件。Phase 1 保持 Tool 身份。**

---

## 边界规则

1. **MCP 调用 ≠ Agent 通信**：Hermes 调用 KOS 的 MCP 工具是工具调用，不走 SSB。
2. **文件读写 ≠ Agent 通信**：Hermes 更新 STATE.yaml 是持久化操作，不走 SSB。
3. **当前唯一的"Agent 通信"是 HANDOFF 交接**：上一个 Hermes 会话 → HANDOFF → 下一个 Hermes 会话。这是 SSB 在 Phase 1 的最简实现。

---

*参考 ADR-005*
