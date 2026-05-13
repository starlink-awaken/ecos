# Changelog

All notable changes to eCOS will be documented in this file.

---

## [0.1.0-draft] — 2026-05-13

### Added
- **GENOME.md**: 系统宪法 (5公理 + 3层不变量 + 6层架构 + 3阶段路线)
- **STATE.yaml**: 运行时状态快照
- **LADS 机制**: HANDOFF 交接 + FAILURES 失败库 + HISTORY 归档
- **六层架构文档**: 宪法/感知/持久/智能/行动/反馈 详细设计
- **IPA 统一模型**: 三层运行时与六层部署的关系说明
- **SSB Event Schema v1**: 10种 Event 类型定义
- **Agent 委员会章程**: Phase 1 三角模式 + Phase 2 完整8角色
- **ADR-001 ~ 007**: 从定位到报告索引的7份架构决策
- **RFC-0001**: 逻辑推演修正提案 (DISCUSSION)
- **IRREVERSIBLE-OPS.md**: 三级不可逆操作规则
- **SUBSYSTEM-IDENTITY.md**: KOS/Minerva/SharedBrain Phase 1 身份定义
- **README.md**: 开源级项目文档
- **CONTRIBUTING.md**: 贡献规范与流程
- **LICENSE**: MIT

### Integrated
- **KOS MCP**: 13 tools, 7 domains, 7,203 documents
- **Minerva MCP**: 9 tools (2 usable direct, full via KOS bridge)
- **Minerva Reports Zone**: 449 reports indexed via manifest extension
- **Cron WF-001**: KOS 每日索引 (daily 02:00)
- **Cron WF-003**: 系统健康检查 + 宪法执行器 (weekly Mon 09:00)
- **Cron WF-005**: HANDOFF 自动更新 (every 2h)

### Fixed (post initial design)
- **FTS5 AND→OR**: KOS MCP 中文搜索从 AND 改为 OR 语义
- **Config args trap**: hermes config set YAML 列表修复
- **Minerva timeout**: KOS MCP timeout 120s→180s
- **L2-03 threshold**: 30% 偏差阈值改为定性/定量分级
- **HANDOFF agent_signature**: 防欺骗字段
- **Git baseline**: GENOME 篡改检测 (WF-003)
- **Snippet→body_preview**: 搜索结果正文预览 (K7)

### Security
- **P0**: WF-003 宪法执行器 (GENOME git diff + STATE cron 交叉验证)
- **P1**: HANDOFF agent_signature + 写入规范
- **Red Team Analysis**: 8 attack vectors, 4 defense gaps, 72% score

### Documented
- **场景验证报告**: 6/6 通过 (S1-S6)
- **红蓝对抗报告**: 攻击面 + 防御分析
- **深度复盘**: 功能/架构/代码 三视角
- **全模块问题清单**: 23 issues across 5 modules
- **迭代规划**: Phase 1→Phase 2 路线图

---

## [Unreleased]

### Planned for next
- K7 body_preview 生效验证 (waiting MCP reload)
- WF-001/WF-005 首跑观察
- Phase 2 启动条件评估

---

*格式基于 [Keep a Changelog](https://keepachangelog.com/)*
