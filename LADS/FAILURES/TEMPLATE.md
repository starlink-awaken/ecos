# 失败案例模板

> 每个失败案例单独一个文件，命名格式：FAIL-YYYYMMDD-NNN-标题.md

---

## 元数据

```yaml
fail_id: "FAIL-YYYYMMDD-NNN"
date: "YYYY-MM-DD"
severity: "LOW|MED|HIGH|CRITICAL"
domain: "架构|决策|执行|工具调用|Workflow|其他"
status: "OPEN|ANALYZED|RESOLVED|ACCEPTED"
reported_by: "Agent名称或人类"
```

---

## 失败描述

**预期结果：**
（描述期望发生什么）

**实际结果：**
（描述实际发生了什么）

**偏差程度：**
（量化或定性描述偏差）

---

## 根因分析（5-Why）

1. Why 1:
2. Why 2:
3. Why 3:
4. Why 4:
5. Why 5:

**根本原因：**

---

## 影响评估

- 数据损失：是/否
- 可逆性：可逆/不可逆/部分可逆
- 影响范围：
- 时间损失：

---

## 纠正措施

**短期（立即执行）：**

**中期（本周内）：**

**长期（架构层面）：**

---

## 经验萃取（下一个 Agent 必读）

> 用一句话总结这个失败教会了系统什么

---

## 相关文档

- 相关 ADR:
- 相关 RFC:
- 相关 Workflow:
