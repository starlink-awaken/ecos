# eCOS Phase 4 — 蜂群智能期 规划

> 2026-05-15 | v0.4.0 | 前置: Phase 3 收尾完成

---

## 一、Phase 4 定位

```
Phase 1: 单体建立    → 1 Agent + 3 Tool
Phase 2: 多Agent协作 → 委员会 + 感知层 + SSB
Phase 3: 蜂群涌现    → 5模型 + 实时防御 + Kanban
Phase 4: 蜂群智能    → 多用户 + 语义共振 + 可测量涌现
```

**Phase 4 的核心区别:** 从"一个人用多个Agent"升级到"多个人共享Agent基础设施"。

---

## 二、产品功能

### 新增功能

| 功能 | 描述 | 优先级 |
|------|------|--------|
| **语义搜索** | LanceDB向量搜索替代FTS5关键词 | P0 |
| **知识融合** | Contextualize+Integrate完成感知五阶 | P0 |
| **CRITIC自动化** | 高风险决策自动触发独立审查 | P1 |
| **共享工作区** | 多人可访问的Kanban+知识视图 | P1 |
| **涌现度量** | 协作效率/决策质量/知识增长量化 | P1 |
| **SharedBrain桥接** | B-OS Event Bus → SSB后端 | P2 |
| **实时Hook** | Hermes tool-call-before集成 | P2 |

---

## 三、技术架构

### LanceDB 语义搜索

```
当前: FTS5 + jieba (关键词匹配)
目标: LanceDB + sentence-transformers (语义理解)

查询 "政务数字化平台" →
  当前: 匹配包含"政务"或"数字化"或"平台"的文档
  目标: 匹配语义相关的文档(含"政府信息化"、"智慧政务"等)

实现:
  1. 填充LanceDB向量 (首次 ~2小时)
  2. KOS MCP semantic_search 启用
  3. 与FTS5混合搜索 (RRF融合)
```

### 感知管道完成

```
当前: Capture → Filter → Structure → Contextualize (4/5)
缺失: Integrate (跨域知识融合)

Integrate 实现:
  新文档入库 → 自动关联已有实体 → 更新知识图谱
  gongwen中政策 → 自动链接guozhuan中平台方案
  Minerva研究报告 → 自动关联KOS历史文档
```

### CRITIC自动化

```
当前: CRITIC手动触发 (高风险决策时)
目标: 自动检测 → 触发独立模型审查

触发条件:
  AUDIT发现MED+风险 → 自动调度CRITIC
  委员会决策涉及L1变更 → 强制CRITIC
  EXEC方案差异度 > 50% → 标记需CRITIC
```

---

## 四、实施计划

### Sprint 1: 语义搜索 (Week 1)
```
□ LanceDB向量填充
□ KOS semantic_search 验证
□ FTS5+LanceDB混合搜索 (RRF)
□ 搜索质量对比 (关键词 vs 语义)
```

### Sprint 2: 感知完成 (Week 2)
```
□ Integrate管道实现
□ 跨域自动链接 (gongwen↔guozhuan)
□ 新文档入库→自动关联→图谱更新
□ 场景验证: 政策文档自动链接平台方案
```

### Sprint 3: CRITIC+度量 (Week 3)
```
□ CRITIC自动触发逻辑
□ 涌现度量框架 (协作效率/决策质量/知识增长)
□ 度量仪表盘 (STATE.yaml扩展)
```

### Sprint 4: 集成+验证 (Week 4)
```
□ SharedBrain桥接评估
□ 端到端场景验证 (Phase 4版)
□ 红蓝对抗 v3
□ 文档更新
```

---

## 五、目标指标

```
Phase 4 目标:
  架构: 82% → 88%
  安全: 78% → 82%
  语义搜索: 启用 (F1 > 0.7)
  感知管道: 五阶完成
  涌现度量: 首次量化
  CRITIC: 自动化触发
```

---

## 六、风险

| 风险 | 缓解 |
|------|------|
| LanceDB填充耗时长 | 分批处理, 后台运行 |
| 语义搜索质量不稳定 | 渐进上线, FTS5保持为主 |
| Hermes实时hook未就绪 | CRITIC降级为WF触发 |
| SharedBrain集成复杂 | 仅评估不强行接入 |

---

*Phase 4 规划完成*
