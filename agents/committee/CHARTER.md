# Agent 委员会章程 (Agent Committee Charter)

> 版本: v0.1.0-draft
> 状态: 草案，待首次运行后修订
> 所属层: L4 智能层
>
> **Phase 1 提示**：当前处于单体建立期，完整 8 角色委员会尚不可实施。
> Phase 1 请使用三角模式（CHAIR+EXEC+AUDIT 角色切换），详见 [PHASE1-TRIANGLE.md](PHASE1-TRIANGLE.md)。
> 本文档为 Phase 2 完整委员会的目标设计。

---

## 一、设立目的

单一 Agent 存在以下固有缺陷：
- 视角单一，易产生确认偏误
- 无法自我验证高风险决策
- 长对话后上下文漂移
- 专业领域覆盖不全

Agent 委员会通过**结构化多角色协作**解决上述问题，同时通过 Workflow 机制确保**决策可复现、结果可审计、知识可持久**。

---

## 二、委员会角色定义

### 核心角色（常设）

| 角色 | 代号 | 职责 | 触发条件 |
|------|------|------|----------|
| 主持人 Agent | CHAIR | 主持议程，协调发言，形成决议 | 每次委员会会议 |
| 执行 Agent | EXEC | 具体任务执行，调用工具 | 有行动任务时 |
| 审查 Agent | AUDIT | 独立审核执行计划和结果，提出异议 | 每次高风险操作 |
| 记录 Agent | SCRIBE | 记录会议过程，更新 ADR/STATE | 每次委员会会议 |

### 专业角色（按需召集）

| 角色 | 代号 | 职责 | 触发条件 |
|------|------|------|----------|
| 研究 Agent | RESEARCH | 调用 Minerva，提供深度背景 | 需要研究支撑时 |
| 知识 Agent | KOS | 检索 KOS，提供历史文档参考 | 需要知识检索时 |
| 批评 Agent | CRITIC | 专职提出反对意见和潜在失败 | 重大决策必召 |
| 规划 Agent | PLANNER | 分解任务，设计 Workflow | 复杂多步任务时 |

---

## 三、委员会工作流程

### 标准流程（Standard Workflow）

```
Phase 0: 召集
  → CHAIR 宣布议题，确认参与 Agent
  → 读取 STATE.yaml + HANDOFF/LATEST.md

Phase 1: 背景同步（≤5分钟）
  → SCRIBE 汇报当前状态
  → RESEARCH/KOS 提供背景（如需）

Phase 2: 方案生成
  → EXEC 提出执行方案
  → PLANNER 分解步骤（如需）

Phase 3: 批评与风险识别
  → CRITIC 必须发言，指出潜在失败
  → AUDIT 评估方案合规性（对照 GENOME.md）

Phase 4: 表决
  → 法定人数：≥ 3 个角色参与，或 2/3 多数赞成
  → 人类可随时 veto

Phase 5: 执行与监控
  → EXEC 执行，AUDIT 监控
  → 偏差 > 30% 触发重新委员会

Phase 6: 归档
  → SCRIBE 更新 STATE.yaml
  → 写入 HANDOFF/LATEST.md
  → 失败/重大偏差写入 FAILURES/
  → 重要决策写入 ADR/
```

### 快速流程（Fast Track，低风险任务）

```
CHAIR + EXEC + AUDIT 三角模式
无需表决，AUDIT 不反对即通过
全程 ≤ 10 分钟
完成后仍需更新 STATE.yaml
```

### 紧急流程（Emergency，系统异常）

```
任何 Agent 均可触发
直接人类通知（Hermes 推送）
暂停所有非紧急 Workflow
等待人类指令
```

---

## 四、SSB 通信协议（委员会内部）

> **Phase 2 更新**: 当前使用 "Hermes 作为消息总线" 模式 — CHAIR(Hermes) 接收所有 Agent 输出，通过 delegate_task 的 context 参数传递信息，结果汇总后写入 SSB SQLite。完整 SSB Event 总线为 Phase 3 目标。

```yaml
ssb_event:
  id: "uuid-v4"
  timestamp: "ISO8601"
  from_agent: "CHAIR|EXEC|AUDIT|..."
  to_agent: "ALL|specific_role"
  session_id: "committee-session-uuid"
  type: "PROPOSAL|CRITIQUE|VOTE|DECISION|ACTION|RESULT"
  payload:
    content: "..."
    confidence: 0.0-1.0      # 贝叶斯置信度
    risk_level: "LOW|MED|HIGH|CRITICAL"
    references: []            # 引用的 ADR/文档
```

---

## 五、失败案例触发规则

以下情况**必须**写入 FAILURES/ 目录：

1. 委员会决策后结果偏差 > 30%
2. 执行过程中触发 L0 不变量边界
3. AUDIT 发出反对但被多数覆盖，且最终失败
4. 任何导致数据丢失或不可逆操作的错误
5. Workflow 执行中途异常终止

失败案例格式见：`FAILURES/TEMPLATE.md`

---

## 六、与 Hermes 的关系

Hermes 是**主 Agent（Master Agent）**，拥有：
- 召集和解散委员会的权限
- L2 政策层的配置权
- 最终向人类汇报的责任

Hermes 不是独裁者，重大决策必须走委员会流程。

---

*版本: v0.1.0-draft*
*创建: 2026-05-13*
