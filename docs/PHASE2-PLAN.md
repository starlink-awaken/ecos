# eCOS Phase 2 — 详细实施规划

> 版本: v1.0 | 日期: 2026-05-13
> 状态: 规划阶段 (Phase 1 稳定观察中)
> 预计启动: Phase 1 稳定运行 2 周后

---

## 一、Phase 2 定位

```
Phase 1: 单体建立期 — 已完成
  → 1 Agent (Hermes) + 3 Tool (KOS/Minerva/SharedBrain)
  → 文档体系完整, MCP集成, Cron自动化, 宪法执行器就绪

Phase 2: 多 Agent 协作期 — 本规划
  → 3+ Agent 通过 delegate_task 并行协作
  → 真正多角色委员会 (非角色切换)
  → 感知层最小实现, 反馈层实时化
  → SSB 从文件读写升级为消息队列

Phase 3: 蜂群涌现期 — 远期
  → 多用户 + 多 Agent 语义共振
```

---

## 二、启动前置条件

```
检查清单 (Phase 1 稳定运行 2 周后评估):

  □ WF-001 每日索引: 连续运行 ≥ 14 天, 失败率 < 5%
  □ WF-003 健康检查: 运行 ≥ 2 次, 零误报
  □ WF-005 HANDOFF:  自动更新正常运行
  □ 失败案例库: ≥ 8 个有效案例 (当前 6)
  □ 无 P0 安全事件
  □ GENOME 无未授权修改
  □ STATE vs 实际状态: 交叉验证一致

  如果全部通过 → Phase 2 启动
  如果未通过 → 继续稳定观察, 修复瓶颈
```

---

## 三、架构升级

### 3.1 L2 感知层 — 五阶管道最小实现 (Priority: P0)

**当前状态:** 完全未实现。KOS 直接索引原始文件。

**Phase 2 目标:** 实现 Capture + Filter 两阶。

```
Capture 层:
  → 统一信息入口: 所有外部信息经此进入系统
  → 实现: Python watch 目录 + MCP 事件触发
  → 产出: 结构化 Event (PERCEPTION type, SSB Schema v1)

Filter 层:
  → 质量过滤: Minerva 报告 Quality ≥ 60 分才入库
  → 相关性判断: 基于 KOS 已有知识的去重/关联判断
  → 实现: Minerva L1 研究启用 quality_gate + 自定义评分
  → 产出: 带 quality_score + relevance_score 的文档

Structure/Contextualize/Integrate: Phase 3
```

**文件:** `docs/architecture/perception-pipeline-v1.md`
**代码:** `scripts/capture-watcher.py` + `scripts/filter-scorer.py`
**Cron:** 新增 WF-006 感知管道 (每小时)

### 3.2 L6 反馈层 — 实时 Hook 原型 (Priority: P0)

**当前状态:** 仅周末检查 (WF-003), 安全窗口 7 天。

**Phase 2 目标:** 关键操作前实时检查。

```
实时检查项:
  □ 不可逆操作前: 自动验证 IRREVERSIBLE-OPS 清单
  □ GENOME 修改: 操作中如涉及 L0/L1, 立即阻断
  □ 执行偏差: 结果 vs 预期偏差 > 30% → 触发重审

实现方式:
  → 不是系统级 hook, 是 Agent 行为规范
  → 在 PHASE1-TRIANGLE.md 中强制要求
  → WF-003 频率提升: 每周 → 每日
  → 新增 WF-007 实时检查 (每 6h)
```

**文件:** `docs/policy/REALTIME-CHECKS.md`
**修改:** PHASE1-TRIANGLE.md (增加实时检查要求)
**Cron:** WF-003 频率提升 + WF-007 新增

### 3.3 SSB — 文件读写 → 消息队列 (Priority: P1)

**当前状态:** Event Schema v1 完整, 零生产使用。

**Phase 2 目标:** SQLite 消息队列。

```
实现:
  → ecos.db (SQLite) — 单文件, 零依赖
  → 表: ssb_events (id, timestamp, source, target, type, payload, semantic)
  → Python 客户端: ssb_client.py (publish/subscribe/query)
  → 集成: Agent 启动时初始化 SSB 连接

消息流:
  HANDOFF 写入 → SSB HANDOFF Event
  FAILURES 写入 → SSB FAILURE Event
  Cron 完成 → SSB STATE_CHANGE Event
  委员会表决 → SSB VOTE/DECISION Event
```

**代码:** `scripts/ssb_client.py` + `scripts/ssb_init.py`
**Schema:** 基于 SSB-SCHEMA-V1.md, Phase 1 的 STATE.yaml/HANDOFF/FAILURES 持久化到 SSB

### 3.4 IPA 运行时实例化 (Priority: P2)

**当前状态:** 文档中描述了 IPA 模型，无运行时代码。

**Phase 2 目标:** IPA 框架在委员会 Workflow 中实例化。

```
委员会 Workflow (WF-004) 映射到 IPA:

  I (Intelligence)  → CHAIR + AUDIT + CRITIC 角色
  P (Persistence)   → KOS 检索 + 失败案例库
  A (Action)        → EXEC 角色 + MCP 工具调用

贝叶斯更新回路:
  先验信念 (P) → 似然度评估 (I) → 行动测试 (A)
       ↑                              ↓
  后验更新 (P) ← 结果评估 (L6 反馈) ←┘
```

---

## 四、委员会升级

### 4.1 从角色切换到真多 Agent (Priority: P0)

**Phase 1:** Hermes 在同一会话内轮流扮演 CHAIR/EXEC/AUDIT
**局限:** 单模型自我批判, 确认偏误风险

**Phase 2 实现:**

```python
# delegate_task 3 并发
delegate_task(tasks=[
    {"goal": "作为 CHAIR, 主持关于 [议题] 的委员会讨论...",
     "context": "当前状态: {STATE.yaml 摘要}...",
     "toolsets": ["terminal", "file", "web"]},
    
    {"goal": "作为 EXEC, 提出关于 [议题] 的执行方案...",
     "context": "需要调用 KOS MCP 获取背景...",
     "toolsets": ["terminal", "file", "web"]},
    
    {"goal": "作为 AUDIT, 独立审查 EXEC 的方案...",
     "context": "对照 GENOME.md 和 IRREVERSIBLE-OPS.md...",
     "toolsets": ["terminal", "file"]},
])
```

**关键差异 vs Phase 1:**
- 3 个独立 Agent 上下文, 互不污染
- AUDIT 可以有不同的"思考路径"
- 真正多角度审查, 非同一模型扮演

**局限 (Phase 2 仍然存在):**
- 3 个 Agent 共享同一个底层 LLM
- 真正的多模型委员会需要 Phase 3

### 4.2 CRITIC 角色引入 (Priority: P1)

```
CRITIC Agent (高风险决策时必须):
  → 唯一职责: 找问题
  → 强制输出: 至少 1 个反对理由
  → 不被 EXEC 和 CHAIR 的观点影响

规模: Phase 2 最多 3 并发 → CHAIR+EXEC+AUDIT 或 CHAIR+EXEC+CRITIC
```

---

## 五、Workflow 扩展

### 新增 Workflow

| ID | 名称 | 触发 | 优先级 | 复杂度 |
|----|------|------|--------|--------|
| WF-002 | Minerva 定期研究 | cron weekly | P1 | 中 |
| WF-004 | 委员会决策会议 | manual | P0 | 高 |
| WF-006 | 感知管道 | cron hourly | P0 | 中 |
| WF-007 | 实时安全检查 | cron 6h | P0 | 低 |

### WF-002: Minerva 定期深度研究

```
触发: 每周日 03:00
功能: 自动研究预设主题列表
主题:
  1. "政务数字化平台 最新政策 2026"
  2. "医疗信息化 AI应用 趋势"
  3. "技术转移 成果转化 平台模式"
产出: 研究报告 → KOS 自动索引 → 周一早上可检索
成本: L1 级, ~$0.30/次, 每月 ~$1.20
```

### WF-004: 委员会决策会议

```
触发: manual (Agent 判断高风险决策时)
流程: delegate_task 3并发 → CHAIR汇总 → ADR写入
适用: L1 宪法修改提案, 新 Workflow 设计, 安全策略变更
产出: ADR + 决策记录 + STATE更新
```

### WF-006: 感知管道

```
触发: 每小时
功能:
  1. 检查 ~/knowledge/reports/ 新文件
  2. 运行 Filter: Minerva 报告质量评分
  3. 低质量报告 (<60) → 标记不索引
  4. 高质量报告 → 正常走 KOS 索引
```

### WF-007: 实时安全检查

```
触发: 每 6 小时
功能:
  1. GENOME git diff (比 WF-003 更高频)
  2. FAILURES 目录完整性
  3. Cron 任务配置一致性
  4. MCP 连接状态检查
```

---

## 六、集成深化

### 6.1 SharedBrain B-OS 接入 (Priority: P2)

```
当前: 未接入, 仅文档中提及
Phase 2: 评估接入方式
  → SharedBrain 是否有 MCP Server？
  → 如果没有, 通过文件系统集成
  → 用途: SSB 消息持久化候选后端
```

### 6.2 KOS 集成增强 (Priority: P1)

```
□ K3 移植性: jieba 分词评估 (改善中文搜索)
□ 性能优化: 搜索结果 snippet 正文高亮 (K7 已修, 待验证)
```

### 6.3 Minerva 集成增强 (Priority: P2)

```
□ M4: 试一次 L1 研究, 验证 quality_score
□ M5: 配置 Semantic Scholar API key
```

---

## 七、时间线

```
Week 1-2   Phase 1 稳定观察期
           WF-001 验证 · WF-005 验证 · 积累失败案例

Week 3     Phase 2 启动条件评估
           全部通过 → Week 4 启动
           未通过 → 继续观察

Week 4-5   Sprint 1: 架构升级
           感知层 Capture+Filter · 反馈层实时化 · SSB SQLite

Week 6-7   Sprint 2: 委员会
           真多 Agent → WF-004 上线 · CRITIC 角色

Week 8-9   Sprint 3: Workflow 补全
           WF-002 · WF-006 · WF-007 全部上线

Week 10    Sprint 4: 集成 + 验证
           SharedBrain 评估 · KOS 优化 · 端到端场景验证
```

---

## 八、成功指标

```
Phase 2 完成标准:

  □ 3+ Agent 通过 delegate_task 并行决策 ≥ 5 次
  □ 委员会决策不再依赖单模型角色切换
  □ SSB 生产事件 ≥ 100 条
  □ 感知层 Filter 过滤 ≥ 10 条低质量信息
  □ Cron 任务总量 = 7 (新增 4 个)
  □ 失败案例 ≥ 15
  □ KOS 文档 ≥ 8,000
  □ 架构实现度: 61% → 80%
  □ 安全评分: 72% → 85%
```

---

## 九、风险与缓解

| 风险 | 概率 | 缓解 |
|------|------|------|
| delegate_task 3并发不稳定 | MED | 先单Agent测试, 再加并发 |
| Minerva L1 成本超预期 | LOW | 从 $0 开始, 逐步升级 |
| SSB SQLite 性能瓶颈 | LOW | Phase 2 数据量小 (<1000 events/月) |
| 感知层过度工程 | MED | Capture+Filter 最小实现, 其余 Phase 3 |
| Phase 1 cron 不稳定推迟 Phase 2 | LOW | 2周观察期, 容错 |

---

*本规划为草案。Phase 2 启动前需委员会正式审查。*
