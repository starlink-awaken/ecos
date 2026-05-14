# eCOS Phase 2 — 多 Agent 协作期 细化实施规划

> 版本: v2.0 | 日期: 2026-05-13
> 状态: **细化完成，待委员会审议**
> 基于: Phase 1 深度验证完成 ✅ (6/6 PASS, 安全72%, 可用性90%)
> 前置修正: Minerva MCP 直连已修复 ✅

---

## 一、Phase 定位与前提检查

### 理论定位

```
Phase 1: 单体建立期                                     [已完成]
  1 Agent(Hermes) → 3 Tool(KOS/Minerva/SharedBrain)
  → 文档体系完整 | MCP集成 | Cron自动化 | 宪法执行器就绪
  → 深度验证6/6 PASS, 失败案例6个, 安全P0+P1全部修复
  → Minerva MCP 直连: ✅ 刚修复, 9工具注册完成

Phase 2: 多 Agent 协作期                                 [本规划]
  3+ Agent 通过 delegate_task 并行协作
  从角色切换 → 真正多Agent委员会
  感知层最小实现 → Capture + Filter
  反馈层实时化 → 前置检查 + 每日健康
  SSB 从文件读写 → 消息队列雏形

Phase 3: 蜂群涌现期                                     [远期]
  多用户 + 多 Agent 语义共振
  SSB 信息素场自动引导协作
  涌现智能可测量
```

### 前提检查清单

| # | 条件 | 状态 | 说明 |
|---|------|------|------|
| 1 | WF-001 每日索引 | ✅ | 已稳定运行 |
| 2 | WF-003 健康检查 | ✅ | 零误报 |
| 3 | WF-005 HANDOFF | ✅ | 自动更新正常 |
| 4 | 失败案例 ≥ 6 | ✅ | 当前 6 个 |
| 5 | 无 P0 安全事件 | ✅ | 全部修复 |
| 6 | GENOME 完整性 | ✅ | 未经授权修改 |
| 7 | STATE 一致性 | ✅ | 与实际状态一致 |
| 8 | Minerva MCP 直连 | ✅ | **本日修复, 9工具** |

**结论：全部通过 → Phase 2 可立即启动** ✅

---

## 二、Phase 2 总体架构升级

### 2.1 核心变化 (vs Phase 1)

| 维度 | Phase 1 | Phase 2 |
|------|---------|---------|
| Agent 数量 | 1 (Hermes 角色切换) | 3-4 (Hermes + 子Agent并行) |
| 委员会 | 三角模式 (同一Agent) | delegate_task 并发 (CHAIR+EXEC+AUDIT/CRITIC) |
| SSB | 文件读写 (HANDOFF+STATE+FAILURES) | 文件读写 + SQLite 事件表 |
| 感知层 | 无 (直接索引原始文件) | Capture + Filter 两阶 |
| 反馈层 | 每周检查 (WF-003) | 每日健康 (WF-003↑) + 前置检查 (WF-007) |
| Cron | 3 个 | 7 个 (新增 4 个) |
| KOS 文档 | ~7,200 | 目标 8,000+ |
| 失败案例 | 6 | 目标 15+ |
| 架构实现度 | ~61% | 目标 80% |
| 安全评分 | 72% | 目标 85% |

### 2.2 新旧组件对比

```diff
+ 新增:
+   scripts/ssb_client.py       — SSB SQLite 客户端
+   scripts/ssb_init.py          — SSB 初始化脚本
+   scripts/capture-watcher.py   — 感知层捕获器
+   scripts/filter-scorer.py     — 感知层过滤器
+   docs/architecture/perception-pipeline-v1.md
+   docs/policy/REALTIME-CHECKS.md
+   agents/workflows/WF-002-minerva-weekly-research.md
+   agents/workflows/WF-004-committee-decision.md
+   agents/workflows/WF-006-perception-pipeline.md
+   agents/workflows/WF-007-realtime-checks.md
+   ecos.db                      — SSB SQLite 数据库文件

~ 修改:
~   agents/committee/PHASE1-TRIANGLE.md  → 增加多Agent并发模式
~   agents/workflows/WF-003-health-check.md  → 频率提升至每日
~   docs/policy/IRREVERSIBLE-OPS.md  → 增加前置检查项
~   STATE.yaml  → 升级到 Phase 2 schema

! Phase 3 保留:
!   SharedBrain B-OS 接入
!   L3-L4 感知管道
!   消息队列 (NATS/Redis)
```

---

## 三、Sprint 分解

### ✅ Sprint 1: SSB 升级 — 文件到 SQLite 队列 (已完成)

**优先级**: P0 | **时间**: 2026-05-13 ~ 2026-05-14 (1 天) | **状态**: 完成 ✅

#### 验证结果

| 项目 | 结果 |
|------|------|
| `ssb_client.py` | ✅ 创建, 包含 publish/query/get_state/CLI |
| `ssb_init.py` | ✅ 创建, 包含 --init/--recover/--verify/--stats/--reset |
| SQLite 建表 | ✅ 7 个索引, WAL 模式, 完整性 OK |
| HANDOFF 双写 | ✅ SQLite + LATEST.md + HISTORY 归档 |
| STATE_CHANGE 双写 | ✅ SQLite + STATE.yaml 更新 |
| FAILURE 双写 | ✅ SQLite + FAILURES/ 文件创建 |
| 查询过滤 | ✅ 按 event_type/source/risk/action_req 过滤 |
| 从文件恢复 | ✅ 重建 9 个事件 (1 HANDOFF + 7 FAILURE + 1 STATE_CHANGE) |
| CLI 接口 | ✅ events/stats/query/state/verify/publish 全可用 |

#### 产出文件
- `scripts/ssb_client.py` — SSB 客户端库
- `scripts/ssb_init.py` — SSB 初始化/恢复脚本
- `LADS/ssb/ecos.db` — SQLite 事件库 (9 events, 68KB)

### Sprint 2: 感知层 — Capture + Filter

---

### ✅ Sprint 2: 感知层 — Capture + Filter (已完成)

**优先级**: P0 | **时间**: 2026-05-14 (1 天) | **状态**: 完成 ✅

#### 验证结果

| 项目 | 结果 |
|------|------|
| `scripts/capture_watcher.py` | ✅ 3 目录扫描, SHA256 防重, PERCEPTION Event |
| `scripts/filter_scorer.py` | ✅ quality(0-100) + relevance(0-100) 评分 |
| `agents/workflows/WF-006-perception-pipeline.md` | ✅ 每小时 cron 设计文档 |
| 端到端: 新文件→Capture→Filter→SSB | ✅ quality=60, relevance=50 → INDEX_READY |
| 增量扫描: 515文件, 0重复 | ✅ 防重验证通过 |
| Filter 统计: 41 index-ready, 6 filtered, 0 pending | ✅ 全部处理完毕 |

#### 产出文件
- `scripts/capture_watcher.py` — 捕获器 (3目录监控, SHA256防重, PERCEPTION双写)
- `scripts/filter_scorer.py` — 过滤器 (质量+关联评分, 阈值≥60/≥40)
- `agents/workflows/WF-006-perception-pipeline.md` — WF-006 设计文档
- WF-006 cron 已创建 (每整点)

### ✅ Sprint 3: 委员会升级 — 角色切换到真多 Agent (下一步)

**优先级**: P0 | **时间**: 待启动 | **依赖**: Sprint 1 (SSB for committee events)

#### 目标
三角模式从"同一 Agent 角色切换"升级到 "delegate_task 3 并行 Agent"。

#### 实现

**文件**:
- 修改: `agents/committee/PHASE1-TRIANGLE.md` (增加多 Agent 并行模式)
- 创建: `agents/workflows/WF-004-committee-decision.md`

**delegate_task 3 并行委员会**:

```python
# 委员会会议 (CHAIR 角色执行)
task_results = delegate_task(tasks=[
    {
        "goal": "作为 EXEC, 对议题 [议题] 提出执行方案",
        "context": "议题详情: {议题}\n当前系统状态: {STATE.yaml 摘要}\n可用工具: KOS MCP, Minerva MCP, SSB",
        "toolsets": ["terminal", "file", "web", "search"]
    },
    {
        "goal": "作为 AUDIT, 独立审查 EXEC 的最终方案",
        "context": "审查标准:\n  1. 是否违反 L0/L1 不变量\n  2. 是否漏掉了关键步骤\n  3. 评估方案的风险等级 (LOW/MED/HIGH/CRITICAL)\nEXEC 方案: {EXEC 的产出}",
        "toolsets": ["terminal", "file"]
    },
    {
        "goal": "作为 CRITIC, 对议题 [议题] 寻找至少 2 个不可行理由",
        "context": "CRITIC 职责: 唯一目标就是找问题。\n当前系统状态: {STATE.yaml 摘要}\n已有方案: {EXEC 的产出 (如果有)}\n注意: 你的观点应该独立于 EXEC。",
        "toolsets": ["terminal", "file", "search"]
    },
])
```

**关键差异**:
- EXEC + AUDIT + CRITIC 是 3 个独立 Agent 实例，上下文互不污染
- AUDIT 看不到 CRITIC 的输出（真正的独立审查）
- 缺点是 token 消耗增加（3 倍），但决策质量提升

**适用场景判断矩阵**:

| 风险/复杂 | 低复杂 | 中复杂 | 高复杂 |
|-----------|--------|--------|--------|
| 低风险 | 直行 | 三角切换 | 三角切换 |
| 中风险 | 三角切换 | delegate 3并发 | delegate 3并发 |
| 高风险 | delegate 3并发 | delegate+CRITIC | 必须人类介入 |

**验证标准**:
- [ ] WF-004 上线后, delegate 3 并发测试 ≥ 3 次
- [ ] 每个子 Agent 返回结构化的决议/审查/批评
- [ ] EXEC 方案 + AUDIT 审查 + CRITIC 异议可对比
- [ ] EXEC 不能跳过 AUDIT 审查 (CHAIR 调度确保)
- [ ] 委员会产生的 DECISION Event 写入 SSB

---

### Sprint 4: 反馈层升级 + Workflow 补全

**优先级**: P0-P1 | **时间**: Week 4 (Day 16-22) | **依赖**: Sprint 1-3

#### 4a. 反馈层实时化 (P0)

**文件**:
- 创建: `docs/policy/REALTIME-CHECKS.md`
- 修改: `agents/committee/PHASE1-TRIANGLE.md` (增加前置检查要求)
- 修改: `agents/workflows/WF-003-health-check.md` (频率每周→每日)
- 创建: `agents/workflows/WF-007-realtime-checks.md`

**前置检查 (WF-007, 每 6 小时)**:

```
检查项:
  1. GENOME git diff → 检测未授权的 L0/L1 修改
  2. STATE vs 实际 → cron时间、文件数、域数一致性
  3. MCP 连接健康 → 对 KOS/Minerva MCP 发送 ping
  4. FAILURES 完整性 → 最近 N 个事件是否已归档
  5. Cron 配置一致性 → 实际 cronjob vs 期望列表
```

**不可逆操作前置检查**:
修改 `docs/policy/IRREVERSIBLE-OPS.md`，增加：

```markdown
## 执行纪律
执行任何不可逆操作前，Agent 必须:
1. 自我检查: 是否已读取 IRREVERSIBLE-OPS.md?
2. 已读确认: 在 SSB 发布 SIGNAL(IRREVERSIBLE_ACK) 
3. 委员会表决: 高风险操作用 delegate_task 3并发
4. 仅当以上三步都通过才能执行
```

#### 4b. WF-002 Minerva 定期研究 (P1)

**文件**:
- 创建: `agents/workflows/WF-002-minerva-weekly-research.md`

```yaml
trigger: "0 3 * * 0" (每周日 03:00)
skill: mcp_minerva_research_now
topics:
  - "政务数字化平台 最新政策 2026"
  - "医疗信息化 AI应用 趋势"
  - "技术转移 成果转化 平台模式 2026"
level: L1 (约 $0.30/次)
cost: ~$1.20/月
output: 
  - 研究报告写入 ~/knowledge/reports/
  - 自动触发 WF-006 感知管道 → KOS 索引
  - SSB HANDOFF Event 通知用户
```

#### 4c. WF-006 感知管道 (P0, Sprint 2 配套)

**文件**:
- 创建: `agents/workflows/WF-006-perception-pipeline.md`

```yaml
trigger: "0 * * * *" (每小时)
function:
  1. 运行 capture-watcher.py (扫描目录 + 检测新文件)
  2. 对新文件运行 filter-scorer.py (quality + relevance)
  3. 高质量文件 → 触发 KOS 索引
  4. 全部产出写入 SSB
```

#### 4d. KOS 集成增强 (P1)

```yaml
K3 中文搜索优化:
  评估: jieba 分词 + FTS5 tokenizer 测试
  实现: 如果效果提升 > 20%, 集成到 KOS MCP
  回退: Agent 层面拆词→多词搜索→结果合并

K7 验证:
  body_preview: 在 MCP 搜索结果中显示正文前 100 字
  状态: 已经被修复, 需要实际验证
```

**验证标准**:
- [ ] WF-007 运行 ≥ 10 次, 零误报
- [ ] IRREVERSIBLE-OPS.md 前置检查被执行 ≥ 2 次
- [ ] WF-002 运行成功, 产生研究报告并被索引
- [ ] WF-006 运行成功, 过滤记录可审计
- [ ] KOS 中文搜索 FTS5 OR mode 验证通过

---

## 四、时间线总览

```
Week 1     Sprint 1: SSB SQLite
           ssb_client.py · ssb_init.py · ecos.db 双写保障
           [Day 1-5]

Week 2     Sprint 2: 感知层 Capture + Filter
           capture-watcher.py · filter-scorer.py · WF-006 
           [Day 6-10]

Week 3     Sprint 3: 委员会升级
           WF-004 delegate 3并发 · CRITIC 引入 · 决策矩阵
           [Day 11-15]

Week 4     Sprint 4: 反馈层 + Workflow 补全
           WF-007 · WF-002 · KOS 优化 · 端到端验证
           [Day 16-22]

Week 5     缓冲 + 端到端场景验证
           Phase 2 完整 7 Cron 运行 · 全场景测试
           [Day 23-28]
```

---

## 五、成功指标

```
Phase 2 完成标准 (全部通过):

  □ SSB 生产事件 ≥ 100 条 (SQLite + 文件同步)
  □ 3+ Agent 通过 delegate_task 并行决策 ≥ 5 次
  □ 委员会决策不再依赖单模型角色切换
  □ 感知层 Filter 过滤 ≥ 10 条低质量信息
  □ WF-007 运行 ≥ 10 次, 零误报
  □ Cron 任务总量 = 7 (现有 3 + 新增 4)
  □ 失败案例 ≥ 15 (现有 6 + 新增 9+)
  □ KOS 文档 ≥ 8,000 (现有 ~7,200)
  □ 架构实现度: ~61% → 80%
  □ 安全评分: 72% → 85%
  □ 无 P0/P1 安全事件
  □ 场景端到端验证通过 (至少 3 个跨层场景)
```

---

## 六、风险与缓解

| 风险 | 概率 | 影响 | 缓解措施 |
|------|------|------|----------|
| delegate_task 3并发不稳定 | MED | HIGH | Sprint 3 前做 ≥ 3 次单 Agent 基线测试; 失败则降级回三角切换 |
| SSB 双写导致不一致 | LOW | MED | 文件为主, SQLite 重建幂等; 每次重建前备份 |
| 感知层过度工程 | MED | MED | 只做 Capture+Filter, 明确约定 Phase 3 才做 Structure/Integrate |
| Minerva L1 成本超预期 | LOW | LOW | L1 ~$0.30/次, 月预算 $50 内可跑 150+ 次, 不是问题 |
| WF-007 误报过多 | LOW | MED | 逐条放宽阈值; 误报超过 3 次需重新设计检查项 |
| KOS 中文搜索无效果 | MED | LOW | jieba+FTS5 测试无改善就回退到 Agent 层拆词方案, 不阻塞 Phase 2 |
| Cron 任务太多导致混乱 | MED | LOW | SSB 统一 Event 日志, WF-003 每日验证全部 cron 健康状态 |
| Phase 1 cron 突发不稳定 | LOW | MED | 过渡期保持 WF-001/WF-003/WF-005 不变, 新增 4 个独立启动 |

---

## 七、端到端验证场景

Phase 2 完成前, 以下 3 个跨层场景必须全部通过:

### S1: 感知→过滤→索引 (L2→L3)
```
1. 用户放置一个新 .md 文件到 ~/knowledge/reports/
2. capture-watcher 在 1 小时内检测到 (WF-006)
3. filter-scorer 给出 quality + relevance 评分
4. quality ≥ 60 → 自动进入 KOS 索引
5. 用户问\"刚才放的文件里有什么\" → Hermes 能检索到内容
```

### S2: 委员会→决策→执行 (L4→L5→L6)
```
1. Hermes 识别到高风险决策 (如\"修改 GENOME L1\")
2. 触发 WF-004, delegate 3 并发: EXEC+AUDIT+CRITIC
3. CRITIC 提出反对, AUDIT 给出合规评估
4. CHAIR 汇总 → DECISION Event → SSB
5. 执行后: STATE.yaml 更新, FAILURES (如有) 归档
6. WF-007 后续运行中能验证决策符合性
```

### S3: SSB 查询→状态恢复 (跨会话)
```
1. Phase 2 运行 7 天后
2. SSB 包含 ≥ 100 条 Event (PROPOSAL/DECISION/FAILURE/STATE_CHANGE)
3. 新建一个空会话 (模拟冷启动)
4. ssb_client.query(action_required=DECIDE) → 返回待处理决策
5. ssb_client.query(event_type=FAILURE) → 全部已归档
6. ssb_client.get_state() → 匹配最新 STATE.yaml
```

---

## 八、Rollback 条件

任何以下情况发生, 暂停 Phase 2, 回退到 Phase 1:

1. **SSB 数据不一致**: SQLite 和文件之间的差异超过 3 次 (无法自动修复)
2. **delegate_task 连续失败 3 次**: 多 Agent 委员会不可行
3. **KOS 索引中断超过 24 小时**: 持久层故障
4. **用户明确要求暂停**: 终极否决权

回退步骤:
```
1. 保留 SSB SQLite 作为只读归档 (不再写入)
2. 恢复文件读写作为唯一 SSB 实现
3. WF-004/WF-006/WF-007 暂停, 保留 WF-001/WF-003/WF-005
4. 委员会降级回 Phase 1 三角角色切换模式
5. 记录 FAILURE → 写入 FAILURES/
6. 更新 STATE.yaml: phase=1, rollback_reason=\"[原因]\"
```

---

## 九、实施指令 (给执行的 Agent)

### 执行顺序

```
严格按 Sprint 1→2→3→4 顺序执行

Sprint 1 (SSB):  不依赖其他 Sprint
Sprint 2 (感知): 依赖 Sprint 1 (SSB 存 PERCEPTION Event)
Sprint 3 (委员会): 依赖 Sprint 1 (SSB 存 DECISION Event)
Sprint 4 (反馈): 依赖 Sprint 1-3
```

### 每个 Sprint 的启动条件

| Sprint | 前置条件 | 验证方法 |
|--------|----------|----------|
| 1 | 无 | — |
| 2 | Sprint 1 验证全部通过 | ssb_client.publish(PERCEPTION) → SQLite 有记录 |
| 3 | Sprint 1 验证全部通过 | delegate_task 能正常返回结果 |
| 4 | Sprint 2+3 验证通过 | Capture+Filter + Committee 稳定运行 |

### 文件创建/修改清单

```
创建 (10 个文件):
  scripts/ssb_client.py
  scripts/ssb_init.py
  scripts/capture-watcher.py
  scripts/filter-scorer.py
  docs/architecture/perception-pipeline-v1.md
  docs/policy/REALTIME-CHECKS.md
  agents/workflows/WF-002-minerva-weekly-research.md
  agents/workflows/WF-004-committee-decision.md
  agents/workflows/WF-006-perception-pipeline.md
  agents/workflows/WF-007-realtime-checks.md

修改 (3 个文件):
  agents/committee/PHASE1-TRIANGLE.md (多Agent并行章节追加)
  agents/workflows/WF-003-health-check.md (频率: 每周→每日)
  docs/policy/IRREVERSIBLE-OPS.md (前置检查追加)

创建 (1 数据库):
  LADS/ssb/ecos.db (SQLite)
```

---

*版本: v2.0*
*基于: Phase 2 草案 v1.0 + Phase 1 实际数据 + Minerva MCP 修复状态*
*等待委员会审议 → ACCEPT → 开始 Sprint 1*
