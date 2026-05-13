# RFC-0001: 逻辑推演修正 — 多组件变更

| 字段 | 值 |
|------|-----|
| 编号 | RFC-0001 |
| 标题 | 逻辑推演修正：三角模式、不可逆操作、L2-03 偏差阈值、SSB Schema v1 |
| 状态 | DISCUSSION |
| 日期 | 2026-05-13 |
| 提案者 | Hermes/deepseek-v4-pro + 夏同学 |
| 讨论期 | 默认 48h，截止 2026-05-15 11:37 CST |
| 关联 ADR | ADR-003, ADR-004, ADR-005 |

---

## 1. 动机

2026-05-13 对 eCOS v0.1.0 做全面逻辑推演，发现：
- 3 个架构矛盾（委员会8Agent vs 单Agent、L0-02可撤销 vs 外部API、30%偏差阈值不可操作化）
- 5 个实现缺口（RFC流程、SSB Schema、KOS/Minerva身份、IPA/六层关系、HANDOFF归档）
- 委员会在 Phase 1 无法实施（delegate_task 最多3个同步叶节点，无持久Agent）

上述问题如不修正，将导致系统在 Phase 1 处于"设计可用、实际不可用"的尴尬状态。

---

## 2. 提案

### 2.1 委员会降级为三角模式（影响 CHARTER.md）

Phase 1 放棄 8 角色完整委员会，改用三角模式（CHAIR+EXEC+AUDIT 角色切换）：
- Hermes 在同一会话内轮流扮演三个角色
- 低风险任务走快速流程（≤10分钟）
- 高风险任务仍走完整委员会流程（但 Phase 1 无独立Agent，受单模型限制）
- 不影响 CHARTER.md 的 Phase 2 目标设计

**新增文件:** `agents/committee/PHASE1-TRIANGLE.md`
**修改文件:** `CHARTER.md`（顶部增加 Phase 1 提示）

### 2.2 不可逆操作分级确认（影响 L0-02 实施）

定义三级不可逆操作规则：
- 一级（完全可逆）：直接执行
- 二级（需确认可逆）：三角模式确认
- 三级（不可逆）：必须人类确认

7 类不可逆操作清单：邮件发送、公开发帖、Git push、数据删除、API写操作、通知推送、云存储写。

**新增文件:** `docs/policy/IRREVERSIBLE-OPS.md`

### 2.3 GENOME.md L2-03 偏差阈值可操作化（影响 GENOME.md）

原文："任何重要决策失败或预期偏差 > 30%"
修正：定性任务用布尔判定（失败即归档），定量任务用 30% 阈值。定义"重要决策"为涉及 L0/L1 变更、不可逆操作、或委员会决议。

**修改文件:** `GENOME.md` L2-03 行（已执行）

### 2.4 KOS/Minerva Phase 1 身份明确（影响架构理解）

Phase 1 中 KOS = Tool(MCP)，Minerva = Tool(MCP)，Hermes = 唯一 Agent。
不存在多 Agent 通信，L0-05 在 Phase 1 无操作对象。
Phase 2 身份可能升级条件：独立感知能力 + 独立目标状态 + 主动 SSB 写入。

**新增文件:** `docs/architecture/SUBSYSTEM-IDENTITY.md`

### 2.5 IPA 与六层关系统一（影响文档体系）

IPA 三层 = 运行时模型（认知操作流），六层 = 部署模型（组件分层）。
统一模型：感知(六层L2)→持久(P)→智能(I)→行动(A)→反馈(六层L6)，宪法(六层L1)约束全部。

**新增文件:** `docs/architecture/IPA-6LAYER-RELATIONSHIP.md`

### 2.6 SSB Event Schema v1（影响 ADR-005 实施）

定义 10 种 Event Type（SIGNAL/PROPOSAL/CRITIQUE/VOTE/DECISION/ACTION_START/ACTION_RESULT/STATE_CHANGE/FAILURE/HANDOFF/PERCEPTION），完整 JSON Schema。
Phase 1 中 SSB 退化为 STATE.yaml+HANDOFF+FAILURES 文件读写。Phase 2 升级路径：SQLite → SharedBrain → 消息队列。

**新增文件:** `docs/architecture/SSB-SCHEMA-V1.md`

### 2.7 RFC 流程和模板（影响运维体系）

RFC 生命周期：DRAFT→DISCUSSION→ACCEPTED/REJECTED/SUPERSEDED，5 步流程，紧急模式 2 小时。

**新增文件:** `docs/decisions/RFC/TEMPLATE.md`, `docs/decisions/RFC/PROCESS.md`

### 2.8 HANDOFF 历史归档机制（影响 LADS 可靠性）

每次覆盖 LATEST.md 前先归档到 HISTORY/ 目录，防止历史丢失。

**修改文件:** `LADS/HANDOFF/LATEST.md`

---

## 3. 影响范围

| 层级 | 影响 | 说明 |
|------|------|------|
| L0 不变量 | 否 | 不变量本身未变 |
| L1 宪法 | 否 | 六层架构、委员会原则未变 |
| L2 政策 | 是 | L2-03 已修正 |
| GENOME.md | 是 | L2-03 已修正 |
| STATE.yaml | 是 | 已刷新 |
| CHARTER.md | 是 | 顶部提示 |
| SSB Schema | 是 | v1 初稿 |
| Workflow | 否 | 尚未有运行中的 WF |
| KOS | 否 | 身份明确但未改变代码 |
| Minerva | 否 | 同上 |

---

## 4. 替代方案

| 替代方案 | 否决理由 |
|----------|----------|
| 保持 8 角色完整委员会不变 | Phase 1 无法实施，delegate_task 只支持 3 个叶子节点 |
| 直接删除 CHARTER.md 改为三角模式 | CHARTER.md 是 Phase 2 的合法目标，应保留 |
| SSB 在 Phase 1 直接上消息队列 | 过度工程化，Phase 1 只有 1 个 Agent，消息队列无意义 |

---

## 5. 风险

| 风险 | 概率 | 影响 | 缓解 |
|------|------|------|------|
| 三角模式受单模型自我批判能力限制 | HIGH | MED | Phase 2 引入多模型/独立 Agent |
| Minerva MCP 启动可能失败（Python 路径） | MED | MED | 首次启动后检查日志，必要时调整 command |
| 新增文件过多，未来维护负担 | LOW | LOW | 已按目录分类；定期清理过时文档 |

---

## 6. 讨论记录

| 日期 | 发言者 | 内容 |
|------|--------|------|
| 2026-05-13 | Hermes | 提案提交，所有变更已在文档中实施。等待人类确认。 |

---

## 7. 决策

| 日期 | 决策者 | 结果 | 理由 |
|------|--------|------|------|
| — | — | 待定 | — |
