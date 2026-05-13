# eCOS Wiki

> 外化认知操作系统 — 完整知识库

---

## 快速导航

### 🏗️ 架构
- [六层架构模型](architecture/six-layer-model) — 宪法→感知→持久→智能→行动→反馈
- [IPA 运行时模型](architecture/IPA-6LAYER) — Intelligence-Persistence-Action 认知循环
- [SSB 语义总线](architecture/SSB-SCHEMA-V1) — Agent 间通信协议
- [子系统身份定义](architecture/SUBSYSTEM-IDENTITY) — KOS/Minerva/SharedBrain 角色

### 📜 宪法与决策
- [GENOME.md](constitution/GENOME) — 系统宪法 (L0/L1/L2 不变量)
- [ADR 索引](decisions/ADR-INDEX) — 7 份架构决策记录
- [RFC 流程](decisions/RFC-PROCESS) — 变更提案规范

### 🤖 Agent 系统
- [Agent 委员会章程](agents/CHARTER) — Phase 2 完整模式
- [Phase 1 三角模式](agents/PHASE1-TRIANGLE) — 当前可用模式
- [Workflow 规范](agents/WORKFLOW-SPEC) — 工作流定义标准

### 🔒 安全策略
- [不可逆操作规则](policy/IRREVERSIBLE-OPS) — 三级分级确认
- [红蓝对抗报告](reviews/REDTEAM) — 攻击面与防御

### 📊 运维
- [STATE.yaml](operations/STATE) — 当前系统快照
- [Cron 任务](operations/CRON) — WF-001/003/005
- [HANDOFF 交接](operations/HANDOFF) — Agent 连续性机制

### 📝 复盘与审查
- [Phase 1 全面复盘](reviews/PHASE1-REVIEW)
- [场景验证报告](reviews/SCENARIO-VERIFICATION)
- [深度复盘](reviews/DEEP-REVIEW)
- [全模块问题清单](reviews/ALL-ISSUES)

### 🔧 开发
- [贡献指南](development/CONTRIBUTING)
- [变更日志](development/CHANGELOG)
- [迭代规划](development/NEXT-STEPS)

---

## 系统状态

| 指标 | 值 |
|------|-----|
| Phase | 1 (单体建立期) |
| MCP 工具 | 22 |
| KOS 域 | 7 (7,203 文档) |
| Cron | 3 active |
| 安全评分 | 72% |
| 架构实现度 | 61% |

*最后更新: 2026-05-13 | [查看完整状态](operations/STATE)*
