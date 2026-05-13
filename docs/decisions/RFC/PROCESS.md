# RFC 流程 (Request for Comments)

> eCOS 变更提案的标准流程
> 版本: v0.1.0
> 创建: 2026-05-13

---

## 一、什么需要走 RFC

**必须走 RFC：**
- 任何涉及 L1 宪法层的变更（影响 GENOME.md L1 部分）
- 新增/删除/修改 ADR 的实质性内容
- SSB Event Schema 的 breaking change
- Agent 委员会章程的结构性变更
- 新增或删除系统层（六层模型的增减）

**建议走 RFC（非强制）：**
- 新 Workflow 设计（用 RFC 获取多角度评审）
- L2 政策层的大幅调整
- 失败案例库的结构变更

**不需要 RFC：**
- STATE.yaml 字段更新（Workflow 完成后的例行更新）
- HANDOFF 交接写入
- 失败案例的新增写入
- L2 政策的小幅参数调整（如调整法定人数）

---

## 二、RFC 生命周期

```
DRAFT ──→ DISCUSSION ──→ ACCEPTED
              │               │
              └──────────────→ REJECTED
              │
              └──────────────→ SUPERSEDED（被新RFC替代）
```

**状态说明：**
| 状态 | 含义 | 允许操作 |
|------|------|----------|
| DRAFT | 提案草稿 | 编辑、补充 |
| DISCUSSION | 公开讨论中 | 添加讨论记录 |
| ACCEPTED | 已接受 | 锁定，内容不可改 |
| REJECTED | 已拒绝 | 锁定，理由归档 |
| SUPERSEDED | 被替代 | 锁定，指向新 RFC |

---

## 三、流程步骤

```
Step 1: 提案编写
  → 提案者（Agent 或人类）按 TEMPLATE.md 编写 RFC
  → 自检：是否真的需要 RFC？（参考第一节）

Step 2: 提交讨论
  → 状态改为 DISCUSSION
  → 通知相关方（Hermes + 人类）
  → 设定讨论截止时间（默认 48h，紧急 2h）
  → 涉及 L0 变更时必须提升到 DISCUSSION 并通知人类

Step 3: 讨论期
  → 委员会三角模式（CHAIR+EXEC+AUDIT）讨论
  → 至少 2/3 角色参与讨论
  → 所有意见写入 RFC 的「讨论记录」区

Step 4: 决策
  → 讨论期结束后，由 CHAIR 提出决策建议
  → 人类拥有最终否决权
  → 状态改为 ACCEPTED 或 REJECTED
  → ACCEPTED 的实施按影响范围更新相关文档

Step 5: 归档
  → SCRIBE 更新 STATE.yaml
  → 实施变更
  → 如变更产生新 ADR，写入 ADR/
```

---

## 四、紧急 RFC 流程

触发条件：系统异常、安全漏洞、L0 边界突破。

```
1. 任何 Agent 可发起紧急 RFC
2. 讨论期压缩到 2 小时
3. 必须通知人类
4. 人类可选择加速批准或暂停
```

---

## 五、编号规则

```
RFC-0001 起编号，永不重复。
SUPERSEDED 的 RFC 不回收编号。
编号手动分配，写入文件名：RFC-0001-title.md
```

---

## 六、当前 RFC 列表

| 编号 | 标题 | 状态 | 日期 |
|------|------|------|------|
| — | 尚无 RFC | — | — |
