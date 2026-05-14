# WF-004: 委员会决策会议 (Committee Decision Meeting)

> 所属层: L4 智能层 | 对应 Sprint 3
> 版本: v0.1.0 | 创建: 2026-05-14
> 模式: 2+1 混合模式（CHAIR/Hermes + 2×EXEC并行 + AUDIT串行审查）

---

## 设计意图

WF-004 是 Phase 2 委员会机制的最小可实施方案，在 `delegate_task` 3 并发的硬约束下，平衡**方案多样性**和**审查深度**。

核心逻辑：
- CHAIR 留在 Hermes 层——因为只有 Hermes 能访问 STATE/HANDOFF/FAILURES、能协调、能最终决策
- 2×EXEC 并行出方案——利用并发加速，同一议题多角度
- 1×AUDIT 串行审查——保留委员会「提案+审查」双机制，AUDIT 看到两方案后交叉评审
- 闭环归档——每次会议必须更新 STATE + HANDOFF

详见推演文档 `docs/review/WF-004-DESIGN-REVIEW.md`。

---

## 元数据

```yaml
id: "WF-004"
name: "委员会决策会议"
version: "0.1.0"
trigger: "manual | 高风险操作前置检查"
priority: "P0 | P1"
risk_level: "MED | HIGH | CRITICAL"
committee_required: true

roles:
  required: [CHAIR, EXEC, AUDIT]
  # CHAIR = Hermes（主Agent，不通过delegate_task）
  # EXEC = delegate_task × 2（并行，各自出方案）
  # AUDIT = delegate_task × 1（串行，审查两方案）
```

---

## 输入

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `topic` | string | ✅ | 议题描述（一句话） |
| `context` | string | ✅ | 背景、当前状态、约束条件 |
| `risk_level` | enum | ✅ | MED / HIGH / CRITICAL |
| `constraints` | string[] | ❌ | 已知限制条件（如不可逆操作清单） |
| `urgency` | enum | ❌ | normal / urgent（紧急时跳过归档确认） |

---

## 流程

```
┌─────────────────────────────────────────────────────────┐
│ S01: CHAIR 定义议题（Hermes）                            │
│ → 生成 议题包: topic + context + constraints + checklist │
└──────────────────────┬──────────────────────────────────┘
                       │
           ┌───────────┴───────────┐
           ↓                       ↓
┌─────────────────────┐  ┌─────────────────────┐
│ S02a: EXEC-A方案    │  │ S02b: EXEC-B方案    │
│ delegate_task       │  │ delegate_task       │
│ → 方案: 步骤/工具/  │  │ → 方案: 步骤/工具/  │
│   风险/时间估算      │  │   风险/时间估算      │  ← 并行执行
└──────────┬──────────┘  └──────────┬──────────┘
           │                        │
           └───────────┬────────────┘
                       ↓
┌──────────────────────────────────────────┐
│ S03: AUDIT 审查（delegate_task）          │
│ → 输入: 议题包 + 方案A + 方案B            │
│ → 输出: 审查报告（逐条评审、对比、建议）   │
└──────────────────┬───────────────────────┘
                   ↓
┌──────────────────────────────────────────┐
│ S04: CHAIR 综合决策（Hermes）             │
│ → 对比: 方案A vs 方案B vs AUDIT意见       │
│ → 决策: 选A / 选B / 合并 / 重做          │
│ → HIGH/CRITICAL → 人类确认               │
└──────────────────┬───────────────────────┘
                   ↓
┌──────────────────────────────────────────┐
│ S05: SCRIBE 归档（Hermes）                │
│ → 更新 STATE.yaml                        │
│ → 写入 HANDOFF/LATEST.md                 │
│ → 重要决策 → ADR                         │
│ → 失败/偏差 → FAILURES                   │
└──────────────────────────────────────────┘
```

---

## 步骤详情

### S01: CHAIR 定义议题

**执行者**: Hermes（主Agent）
**前置**: 读取 STATE.yaml + HANDOFF/LATEST.md

输出格式（议题包）：
```yaml
topic: "议题名称"
context: |
  背景描述、当前状态、相关文档链接
constraints:
  - "不可逆操作清单中的第X项"
  - "已知限制条件"
risk_level: "HIGH"
expected_output: "期望的产出形式（方案/决策/分析报告）"
checklist:
  - "是否涉及GENOME L0边界？"
  - "是否需要人类确认？"
  - "是否影响已有cron/Workflow？"
```

---

### S02a/b: 双EXEC并行出方案

**执行者**: delegate_task × 2（并行）
**输入**: 议题包（来自S01）
**超时**: 180s

子Agent Prompt 模板：
```
你正在参加Agent委员会决策会议，担任EXEC（执行）角色。

你的任务：
1. 基于以下议题背景，提出一个可执行的具体方案
2. 列出实现步骤（每个步骤需要什么工具/命令）
3. 评估每个步骤的风险等级
4. 给出时间估算
5. 列出你的方案的前提假设

议题包：
{议题包内容}

约束条件（不可违反）：
{constraints}

输出格式（JSON）：
{
  "plan_name": "方案简称",
  "summary": "方案一句话描述",
  "approach": "实现思路",
  "steps": [
    {"step": 1, "action": "具体操作", "risk": "LOW|MED|HIGH", "tool": "需要的工具"}
  ],
  "assumptions": ["假设1", "假设2"],
  "estimated_time": "X分钟",
  "risks": ["风险1", "风险2", "缓解措施"]
}
```

---

### S03: AUDIT 审查

**执行者**: delegate_task × 1（串行，等待S02完成）
**输入**: 议题包 + 方案A + 方案B
**超时**: 180s

子Agent Prompt 模板：
```
你正在参加Agent委员会决策会议，担任AUDIT（审查）角色。

你的任务是独立审查以下两个方案，逐条指出问题。

议题包：
{议题包内容}

方案A：
{方案A}

方案B：
{方案B}

你需要审查的维度：
1. ✅ 合规性 — 是否违反GENOME L0/L1？是否违反eCOS核心规则？
2. ⚠️ 安全性 — 是否有数据泄露、不可逆操作、权限滥用风险？
3. 🔍 可行性 — 步骤是否清晰？依赖是否已满足？工具是否可用？
4. 💡 完整性 — 是否有遗漏的步骤或边界情况？
5. ⚖️ 对比 — A好在哪里？B好在哪里？各自的致命缺陷？

输出格式（JSON）：
{
  "review_a": {
    "verdict": "APPROVE|CONDITIONAL|REJECT",
    "issues": [
      {"severity": "HIGH|MED|LOW", "step": 步骤号, "desc": "问题描述", "suggestion": "修改建议"}
    ],
    "missing": ["遗漏的考虑点"]
  },
  "review_b": {
    "verdict": "APPROVE|CONDITIONAL|REJECT",
    "issues": []
  },
  "comparison": {
    "a_better_at": ["A的优势"],
    "b_better_at": ["B的优势"],
    "recommendation": "推荐A/推荐B/合并A+B/都不推荐"
  }
}
```

---

### S04: CHAIR 综合决策

**执行者**: Hermes（主Agent）
**输入**: 议题包 + 方案A + 方案B + AUDIT审查报告

决策规则：
```
风险等级 CRITICAL:
  → 必须人类确认（推送通知，等待回复）
  → 人类不回复 → 挂起，不执行

风险等级 HIGH + AUDIT 不反对:
  → 可执行，但归档时注明"高风险，AUDIT通过"
  → 执行后必须跟踪结果（写入HANDOFF的next_check）

风险等级 HIGH + AUDIT 反对:
  → 暂停，Hermes 分析争议点
  → 能调和 → 合并修正版
  → 不能调和 → 发起第二轮（S02 re-run，或升级人类）

风险等级 MED + 任何结果:
  → 综合决策，直接执行
  → AUDIT 的 non-blocking 意见作为"建议"记录
```

---

### S05: SCRIBE 归档

**执行者**: Hermes（主Agent）

归档清单：
```
□ 更新 STATE.yaml
   → 记录本次会议ID、时间、决策结果
□ 写入 HANDOFF/LATEST.md
   → 简要总结：议题、决策、待跟踪项
□ 重大决策 → 写入 ADR/
   → 影响架构/策略的决策必须走 ADR
□ 失败/偏差 → 写入 FAILURES/
   → 决策后实际结果偏差 > 30%，或AUDIT反对被覆盖后失败
□ 方案保留 → 写入 docs/decisions/workflow/
   → EXEC 的方案原文作为附录保留（便于追溯）
```

---

## 参与者模板

### delegate_task prompt 汇总

#### EXEC prompt

```
你正在担任 Agent 委员会的 EXEC（执行）角色。

议题: {topic}
背景: {context}
约束: {constraints}

请基于以上议题，提出一个可执行的方案。输出 JSON 格式。
```

#### AUDIT prompt

```
你正在担任 Agent 委员会的 AUDIT（审查）角色。

议题: {topic}
背景: {context}

以下有两个方案需要你独立审查：

方案A: {plan_a}
方案B: {plan_b}

请从合规性、安全性、可行性、完整性四个维度审查，并对比两个方案。

输出 JSON 格式。
```

---

## 回滚策略

```yaml
rollback:
  strategy: "PARTIAL"
  # 委员会决策本身可回滚（改为另一方案），但执行后可能不可逆
  steps:
    - "如执行未开始 → 退回 S04，选择另一方案"
    - "如执行已开始（工具已调用） → 评估中断成本，必要时走 HUMAN_NOTIFY"
    - "不可逆操作执行后 → 写入 FAILURES，不可回滚"
```

---

## 触发条件

**必须触发：**
- 涉及L0边界操作（GENOME.md修改提议）
- 涉及不可逆操作清单中的任何一项
- 新 Workflow 首次上线
- 异常率/错误率显著升高（CHAIR自主判定）

**建议触发：**
- 复杂多步任务（≥5 步骤，或涉及多个外部系统）
- 用户明确要求"多角度评估"
- 两个以上组件之间的决策冲突

**不需要触发（直行）：**
- 简单信息查询
- 常规 cron 维护（WF-001/003/005/006）
- 单一工具调用

---

## 最小原型验证记录

> **日期**: 2026-05-14 | **议题**: "KOS是否需要添加jieba中文分词"
> **验证者**: Hermes | **状态**: ✅ 通过

### 验证数据

| 步骤 | 执行者 | 耗时 | 结果 |
|------|--------|------|------|
| S01 议题定义 | CHAIR(Hermes) | 30s | 议题包生成 ✅ |
| S02a EXEC-A | delegate_task | 37s | 方案: 轻量分词桥接 ✅ |
| S02b EXEC-B | delegate_task | 54s | 方案: Semantic+Bigram双路径 ✅ |
| S03 AUDIT | delegate_task | 90s | A: CONDITIONAL / B: REJECT ✅ |
| S04 决策 | CHAIR(Hermes) | 10s | 综合决策 ✅ |
| S05 归档 | CHAIR(Hermes) | 20s | STATE+HANDOFF ✅ |

### 验证结论

- ✅ **并行2×EXEC 可同时跑通** → 同一议题产生两份有差异的方案（A轻量快速vs B系统改造）
- ✅ **AUDIT 能看到两份方案的完整内容** → 跨delegate_task上下文传递正常
- ✅ **完整流程 ≤ 10 分钟** → 实际约2.5分钟（含归档）
- ⚠️ **HIGH/CRITICAL 风险触发** → 本次议题为MED，未测试；理论设计完整
- ✅ **归档步骤完整** → STATE + HANDOFF 双更新
- ✅ **方案质量** → AUDIT发现了FTS5不可ALTER、LanceDB未安装等关键事实约束，深度达标

### 发现的问题

1. EXEC方案B的Time Estimation严重低估（90min→实际3h+），建议子Agent prompt中增加"验证依赖状态后再估算"要求
2. AUDIT对剩余上下文（如当前Phase/Sprint状态）的感知依赖于议题包中的context字段传递完整性
3. 归档步骤目前靠CHAIR手动执行，可考虑在WF-004中嵌入STATE/HANDOFF更新模板

---

## 验证标准

---

## 与现有文档的关系

| 文档 | 关系 |
|------|------|
| PHASE1-TRIANGLE.md | WF-004 是三角模式的升级替代。低风险任务继续用三角模式，高风险走WF-004 |
| CHARTER.md | WF-004 是 CHARTER.md 在 Phase 2 初期的最小实施方案 |
| FAIL-20260513-001 | 本工作流的设计受该失败案例驱动——避免再次过度设计 |
| IRREVERSIBLE-OPS.md | HIGH/CRITICAL 风险必须走 IRREVERSIBLE-OPS 的人类确认流程 |
| WORKFLOW-SPEC.md | 遵循工作流定义规范 v0.1.0-draft |

---

*版本: v0.1.0*
*创建: 2026-05-14*
