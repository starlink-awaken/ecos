---
fail_id: FAIL-20260513-003
date: "2026-05-13"
severity: LOW
domain: 架构
status: MITIGATED
reported_by: Hermes/deepseek-v4-pro（逻辑推演）
---

# SSB 共享语义总线在 Phase 1 无消费者

## 失败描述

**预期结果：** SSB 共享语义总线作为 eCOS 的神经系统，在 Phase 1 即可承载 Agent 间通信、状态变更广播、信息素场信号。

**实际结果：**
- Phase 1 只有 Hermes 一个 Agent
- KOS/Minerva 被明确为 Tool（MCP 调用），不是 Agent，不消费 SSB 消息
- 只有"一个蚂蚁"时，信息素场不产生任何协作价值
- SSB Event Schema v1 已设计（10 种 Event Type），但所有 Event 的 `target.scope` 只有自己
- 本质上：SSB 是一个设计精美但 Phase 1 零消费者的消息总线

**偏差程度：** 概念到实现的鸿沟——Schema 完整，消费者为零。

## 根因分析（5-Why）

1. Why 1: 为什么 SSB 无消费者？→ 因为只有 1 个 Agent
2. Why 2: 为什么只有 1 个 Agent？→ 因为 Phase 1 是单体建立期，多 Agent 是 Phase 2 的事
3. Why 3: 为什么 Phase 1 就设计了 SSB？→ 因为 SSB 是核心基础设施，提前设计避免后期重构
4. Why 4: 那为什么这是失败？→ 因为它被描绘为"贯穿所有层的神经系统"，但实际上 Phase 1 只是文件读写
5. Why 5: 为什么没在文档中明确这个降级？→ 因为初始设计时没做 Phase-by-Phase 的可用性检查

**根本原因：** 架构文档的"叙事层级"高于"实施层级"，使用了 Phase 3 的能力语言来描述 Phase 1 的状态。

## 影响评估

- 数据损失：否
- 可逆性：完全可逆（文档澄清即可）
- 影响范围：对 SSB 的过度期望 → 已通过 SSB-SCHEMA-V1.md 澄清
- 时间损失：~15 分钟（推演发现+文档修正）

## 纠正措施

**短期：** SSB-SCHEMA-V1.md 明确 Phase 1 退化为文件读写。STATE.yaml 标记 R05。
**中期：** Phase 2 启用 SQLite 消息队列（第一个真正的 SSB 实现）
**长期：** Phase 3 启用 SharedBrain 或消息队列

## 经验萃取

> 不要说"SSB 贯穿所有层"如果当前它只是 STATE.yaml 的写入操作。降级声明必须与升级路径一样清晰。

## 相关文档

- SSB-SCHEMA-V1.md, SUBSYSTEM-IDENTITY.md, RFC-0001, ADR-005
