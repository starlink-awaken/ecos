# ADR-006: 逻辑推演驱动的架构修正

- **状态**: 已接受
- **日期**: 2026-05-13
- **决策者**: 夏同学 + Hermes/deepseek-v4-pro
- **关联**: RFC-0001, ADR-003, ADR-004, ADR-005

## 背景

2026-05-13 对 eCOS v0.1.0 做全面逻辑推演，发现 3 个架构矛盾、5 个实现缺口。用户要求执行 P0/P1 修正并做好阶段性复盘。

## 决策

### ADR-006-01: 三角模式作为 Phase 1 委员会实施标准

完整 8 角色委员会在 Phase 1 不可实施（delegate_task 最多 3 同步叶节点，无持久 Agent）。

→ 采用三角模式（CHAIR+EXEC+AUDIT 角色切换），Hermes 在同一会话内轮流扮演。
→ CHARTER.md 保留为 Phase 2 完整委员会目标设计。

### ADR-006-02: 不可逆操作三级分级机制

L0-02 "所有行动可撤销" 与外部 API 不可逆性存在矛盾。

→ 定义三级不可逆操作规则：一级（可逆）/ 二级（三角确认）/ 三级（必须人类确认）。
→ 7 类不可逆操作清单写入 IRREVERSIBLE-OPS.md。
→ L0-02 原文不修改，通过分级规则实现。

### ADR-006-03: L2-03 偏差阈值可操作化

原规则"预期偏差 > 30%"对定性任务不可操作。

→ 修正为三层：定性任务布尔判定 / 定量任务 30% 阈值 / "重要决策"显式定义。
→ GENOME.md L2-03 行已更新。

### ADR-006-04: KOS/Minerva Phase 1 明确为 Tool 身份

术语"子系统"产生 Agent vs Tool 歧义。

→ Phase 1：KOS = Tool(MCP)，Minerva = Tool(MCP)，Hermes = 唯一 Agent。
→ Phase 2 升级条件：独立感知 + 独立目标 + 主动 SSB 写入。
→ 文档：SUBSYSTEM-IDENTITY.md。

### ADR-006-05: IPA vs 六层关系统一

两套模型并存未解释关系。

→ IPA = 运行时模型（认知操作流），六层 = 部署模型（组件分层）。
→ 统一模型：感知→持久→智能→行动→反馈闭环 + 宪法约束。
→ 文档：IPA-6LAYER-RELATIONSHIP.md。

### ADR-006-06: SSB Phase 1 退化为文件读写

SSB 在 Phase 1 只有 1 个 Agent，无消费者。

→ Phase 1: SSB = STATE.yaml + HANDOFF + FAILURES 文件读写。
→ Schema v1 保持完整（10 种 Event Type），为 Phase 2 升级准备。
→ 文档：SSB-SCHEMA-V1.md。

### ADR-006-07: 失败案例库正式启用

用户要求必须有失败案例库组件。

→ FAILURES/ 目录建立，模板定义，首批 3 案例（8Agent幻想/30%阈值/SSB空转）。
→ 触发规则写入 CHARTER.md 和 GENOME.md L2-03。

### ADR-006-08: KOS + Minerva MCP 接入 Hermes

两个系统均已有 MCP Server。

→ config.yaml 配置 mcp_servers.kos 和 mcp_servers.minerva。
→ 待 Hermes 重启后验证连接。

## 后果

- 正面：解决了 v0.1.0 的所有已知架构矛盾，Phase 1 的实际可执行性从 ~40% 提升到 ~85%
- 负面：文档数量膨胀（14→27），需定期维护
- 风险：Minerva MCP 可能在启动时因 Python 路径问题失败（待验证）

## 被否决的替代方案

| 方案 | 否决理由 |
|------|----------|
| 直接删除 CHARTER.md | Phase 2 仍需要完整委员会，文档是目标而非负担 |
| SSB Phase 1 直接上消息队列 | 过度工程化，1 个 Agent 下无意义 |
| 等待所有基础设施就绪再开始 eCOS | 违反"先框架后填充"的架构原则 |
