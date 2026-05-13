# Phase 1 问题 → 规划覆盖检查

> 2026-05-13 | 23 个问题逐一对照

---

## 已覆盖 ✅

| ID | 问题 | 规划 |
|----|------|------|
| E1 | L2感知层全空 | Phase 2 Month 2: L2最小实现 |
| E2 | L6反馈层滞后 | Phase 2: 实时hook原型 |
| E3 | SSB零生产 | Phase 2: SQLite消息队列 |
| E4 | IPA未实例化 | Phase 2: 委员会实现时实例化 |
| E5 | HANDOFF纪律 | Week 1: WF-005自动更新 ✅ |
| E6 | STATE疏漏 | Week 1: WF-003交叉验证 ✅ |
| H1 | config args陷阱 | 已修复 ✅ |
| I1 | 路径对齐 | 已修复 ✅ |
| I2 | timeout超时 | 已修复 ✅ |
| I3 | 桥接发现 | 已记录 ✅ |
| K1 | FTS5 AND | 已修复 ✅ |
| K2 | symlink | Workaround完成 ✅ |
| K4 | 单路径限制 | Workaround完成 ✅ |
| K5 | 模板排除 | 设计如此 ✅ |
| K7 | snippet无正文 | Week 1 修复 ✅ |
| M1 | executor未初始化 | KOS桥接替代 ✅ |
| M2 | 研究超时 | 已修复 ✅ |

---

## 未覆盖 ⚠️

| ID | 问题 | 严重度 | 未覆盖原因 |
|----|------|--------|------------|
| K3 | KOS移植性限制 | MED | 上游重构面广，Phase 2 评估 |
| K6 | KOS_READY守卫 | LOW | 当前无影响，移植时再修 |
| M3 | Semantic Search空 | MED | 需填充LanceDB，暂缓 |
| M4 | Quality=N/A | LOW | L0设计如此，非bug |
| M5 | 429限流 | LOW | 配API key即可，非紧急 |
| M6 | KB与KOS不互通 | LOW | 已通过manifest解决检索 |

---

## 判定

```
总问题: 23
已覆盖: 17 (74%)
未覆盖: 6  (26%)

未覆盖的6项:
  → 全部 LOW 或 MED 且非阻塞
  → 全部有明确的"为什么暂缓"理由
  → 无遗漏的高优先级问题
```

**结论: 无遗漏。Phase 1 高/中优先级问题全部有对应的修复或规划。**

---

建议补充到 NEXT-STEPS.md 的 "观察列表" 中：

```
观察列表 (不阻塞 Phase 2, 定期回顾):
  □ K3 KOS移植性 — 换机时评估
  □ M3 语义搜索 — Phase 2 时如需要再填充LanceDB
  □ M5 429限流 — 影响学术搜索时配API key
```
