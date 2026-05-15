# eCOS 全面审计报告

> 日期: 2026-05-15 10:51 CST
> 范围: 功能·架构·债务三维度
> 版本: v0.4.0

---

## 第一章：功能审计

### 1.1 脚本清单（按功能分类）

**感知层（6个）:**
| 脚本 | 行数 | 描述 | 测试 |
|------|------|------|------|
| capture_watcher.py | 484 | Capture — 目录监控 + SSB PERCEPTION事件 | ❌ |
| filter_scorer.py | 724 | Filter — 质量+相关性评分 | ❌ (仅filter_attack_test) |
| structure_pipeline.py | 68 | Structure — 文档分类+实体提取 | ❌ |
| contextualize_pipeline.py | 62 | Contextualize — KOS实体匹配 | ❌ |
| integrate_pipeline.py | 264 | Integrate — 跨域关联+知识图谱 | ❌ |
| semantic_scorer.py | 86 | 语义评分辅助（启发式） | ❌ |

**安全层（5个）:**
| 脚本 | 行数 | 描述 | 测试 |
|------|------|------|------|
| realtime_guard.py | 75 | 操作前安全检查（16条规则，3级拦截） | ❌ |
| content_integrity.py | 76 | 内容完整性（反模板化投毒） | ✅ filter_attack_test |
| ssb_auth.py | 75 | HMAC事件签名 | ❌ |
| ssb_integrity.py | 44 | SSB哈希链完整性验证 | ❌ |
| filter_attack_test.py | 117 | 对抗样本验证（8种攻击模式） | ✅ 自身即测试 |

**SSB/运维层（4个）:**
| 脚本 | 行数 | 描述 | 测试 |
|------|------|------|------|
| ssb_client.py | 722 | SSB核心库（双重写入 + 查询） | ❌ |
| ssb_init.py | 216 | SSB初始化/恢复 | ❌ |
| ssb_dump.py | 19 | SSB→JSONL导出 | ❌ |
| ssb_schema_migrate.py | 124 | Schema v1迁移 | ❌ |

**调度层（2个）:**
| 脚本 | 行数 | 描述 | 测试 |
|------|------|------|------|
| ecos_scheduler.py | 277 | Workflow调度引擎（kanban/manual/status） | ❌ |
| wf-008-kanban-ssb-bridge.py | 150 | Kanban↔SSB事件桥接 | ❌ |

**智能层（1个）:**
| 脚本 | 行数 | 描述 | 测试 |
|------|------|------|------|
| critic_auto_trigger.py | 248 | CRITIC自动触发（5条规则） | ❌ |

**基础设施检查（1个）:**
| 脚本 | 行数 | 描述 | 测试 |
|------|------|------|------|
| pre_design_check.py | 57 | 设计前基础设施约束验证 | ❌ |

**汇总:** 19个脚本，总约 4,467 行 Python 代码

### 1.2 测试覆盖统计

| 指标 | 数值 |
|------|------|
| 脚本总数 | 19 |
| 测试文件 | 4（T7/T8/redteam-v3/filter_attack_test） |
| 有独立测试的脚本 | 1（content_integrity.py ← filter_attack_test.py，间接） |
| test/script 比率 | **4/19 = 21%** |
| 单元测试 | **0** |
| 集成测试 | 3（T7崩溃恢复、T8委员会错误、redteam-v3） |
| 对抗测试 | 1（filter_attack_test） |

### 1.3 Cron 作业清单

| ID | 名称 | 频率 | 状态 |
|----|------|------|------|
| WF-001 | KOS每日索引 | daily | 上线 |
| WF-002 | Minerva深度研究 | weekly (Sun) | 上线 |
| WF-003 | 系统健康检查 | daily | 上线 |
| WF-005 | HANDOFF自动更新 | every 2h | 上线 |
| WF-006 | 感知管道 | hourly | 上线 |
| WF-007 | 实时安全检查 | every 6h | 上线 |
| WF-008 | Kanban→SSB桥接 | every 5min | 上线 |

7个 Cron 全部在线运行。

### 1.4 功能审计发现

**问题 F1: 测试严重不足 [P0]**
- test/script 比率仅 21%
- 19个脚本中仅 1 个有对应测试（间接）
- 0 个单元测试
- 核心组件（ssb_client 722行、filter_scorer 724行、capture_watcher 484行）零测试覆盖
- 风险：任何修改都可能引入回归

**问题 F2: 测试文件命名不规范 [P2]**
- T7、T8 命名无统一前缀
- redteam-v3.py 与 scripts/filter_attack_test.py 功能重叠但位置不同
- 建议：统一命名前缀 test_*

**问题 F3: filter_scorer 724行无人测试 [P1]**
- 感知管道核心过滤器，零测试
- filter_attack_test 只测 content_integrity，不测 filter_scorer
- 历史教训（问题#3）：写了过滤器但没验证就上线

**问题 F4: ssb_client 722行无测试 [P1]**
- SSB 核心库，所有 SSB 脚本依赖它
- 崩溃恢复测试 T7 测的是原子性，不是 ssb_client 本身

---

## 第二章：架构审计

### 2.1 文档结构

架构文档（docs/architecture/）:
- six-layer-model.md — 六层架构详细设计
- IPA-6LAYER-RELATIONSHIP.md — IPA与六层关系
- SSB-SCHEMA-V1.md — SSB事件Schema
- SUBSYSTEM-IDENTITY.md — KOS/Minerva/SharedBrain身份定义
- SHAREDBRAIN-ASSESSMENT.md — SharedBrain评估

ADR（001-010，共10份）:
- ADR-001: eCOS定位
- ADR-002: 六层架构
- ADR-003: Agent委员会
- ADR-004: LADS机制
- ADR-005: SSB语义总线
- ADR-006: 逻辑修正
- ADR-007: Minerva报告区
- ADR-008: 委员会决策加速
- ADR-009: 多模型委员会
- ADR-010: Kanban调度引擎

### 2.2 六层架构实现覆盖度

| 层 | 文档覆盖率 | 代码实现 | 差距 |
|----|-----------|---------|------|
| L1 宪法 | 95% | GENOME.md + git监控 | 无自动化宪法执行pre-hook |
| L2 感知 | 80% | 5阶管道全部有脚本 | Structure(68行)/Contextualize(62行)太薄 |
| L3 持久 | 90% | KOS+SSB+FAILURES | SharedBrain未集成 |
| L4 智能 | 75% | 委员会+CRITIC+多模型 | 委员会闲置，仅测试过1次 |
| L5 行动 | 85% | 7 Cron+MCP 22 tools | WF-002首跑未验证 |
| L6 反馈 | 80% | realtime_guard+integrity+HMAC | 实时hook依赖Hermes支持 |
| **整体** | **85%**（STATE.yaml值） | | |

### 2.3 架构漂移检测

**漂移 D1: Phase版本不一致 [P1]**
- AGENTS.md: "Phase 3 (蜂群涌现期) — CLOSED"
- STATE.yaml: "phase: 4, phase_name: 蜂群智能期 — Phase 4 完成"
- 两处对当前Phase描述矛盾。GENOME.md Phase 3 描述是 2027+，但实际已到 Phase 4

**漂移 D2: SSB设计 vs 实现 [P2]**
- SSB-SCHEMA-V1.md: "异步消息总线，不阻塞Agent执行"
- 实际：SSB 退化为文件读写（SQLite + JSONL 双重写入）
- 虽然文档中 Phase 1 降级方案已说明，但现在实际已是 Phase 4，SSB 有 SQLite 但仍是文件模型，不是真正的消息总线

**漂移 D3: SUBSYSTEM-IDENTITY 过时 [P2]**
- 文档描述 KOS/Minerva 为 Tool（Phase 1身份）
- 当前 Phase 4，Multi-model committee 已将 KOS/Minerva 用作半自主资源
- 文档没有反映这一变化

**漂移 D4: IPA运行时模型未实例化 [P2]**
- IPA-6LAYER-RELATIONSHIP.md 描述贝叶斯更新循环（先验→似然→行动→后验）
- 实际代码中没有任何贝叶斯更新引擎
- IPA 仅在文档层面存在，运行时无对应实例

**漂移 D5: HANDOFF历史 vs STATE.yaml记录不一致 [P2]**
- STATE.yaml: handoff_history: 12
- 实际 HANDOFF/HISTORY/ 目录: 11 个历史文件 + 1 LATEST = 12
- 但 AGENTS.md 显示状态表未更新（仍引用旧的 Phase 3、38+ commits 等）

### 2.4 IPA统一模型 vs 实际部署

| IPA层 | 对应六层 | 文档描述 | 实际部署 |
|-------|---------|---------|---------|
| A (Action) | L5 行动层 | 执行、工具调用、外部交互 | ✅ 7 Cron + 22 MCP tools |
| I (Intelligence) | L4 智能层 | 推理、规划、Agent委员会 | ⚠️ 委员会仅测试1次，闲置 |
| P (Persistence) | L3 持久层 | 记忆、知识图谱、向量索引 | ✅ KOS 7域 + SSB + FAILURES |
| (缺失) | L1 宪法 | IPA不显式建模 | ✅ GENOME.md完整 |
| (缺失) | L2 感知 | IPA假定输入已结构化 | ⚠️ 5阶管道实现但薄 |
| (缺失) | L6 反馈 | IPA无负反馈回路 | ⚠️ 实时hook未自动化 |

### 2.5 架构审计发现

**问题 A1: GENOME.md 版本冻结 [P1]**
- GENOME.md 版本标记为 v0.1.0-draft，创建于 2026-05-13
- Phase 已从 1 演进到 4，但 GENOME.md 未更新 Phase 路径描述
- Phase 1 的目标日期（2026 Q3）已过去，但文档仍指向未来

**问题 A2: 委员会闲置 [P1]**
- ADR-003/008/009 详细设计了委员会机制
- WF-004 设计完整（5步委员会链）
- ADR-010 验证过 1 次循环
- 但当前委员会处于闲置状态，零实际业务驱动

**问题 A3: 感知管道薄点 [P2]**
- Structure 68行、Contextualize 62行 vs Capture 484行、Filter 724行
- 管道前两阶和后两阶深度不匹配
- Integrate 264行但直接硬编码 KOS 路径，缺乏抽象

**问题 A4: SharedBrain 未集成 [P3]**
- 架构文档多处引用 SharedBrain 作为 "SSB持久化候选"
- 实际零集成，所有文档描述为"待评估/待接入"
- 不是紧急问题，但架构图上存在未实现的组件

---

## 第三章：债务审计

### 3.1 文档量统计

| 类别 | 数量 |
|------|------|
| .md 文档 | 101 |
| .py 脚本 | 22 (scripts 19 + tests 3) |
| .yaml 配置 | 4 |
| 总文件（不含.git） | 140 |
| ADR | 10 |
| 失败案例 | 16 (15 + 1 TEMPLATE) |
| HANDOFF 历史 | 12 (11 + 1 LATEST) |
| doc/script 比率 | **101/22 = 4.59** |
| test/script 比率 | **4/19 = 0.21** |

### 3.2 债务来源分析

从 ALL-MODULE-ISSUES.md (2026-05-13) 解析的 23 个问题：

| 模块 | HIGH | MED | LOW | 已解决 |
|------|------|-----|-----|--------|
| eCOS | 1 | 2 | 2 | 2/5 |
| Hermes | 1 | 0 | 0 | 1/1 |
| 集成层 | 0 | 2 | 1 | 3/3 |
| KOS | 1 | 3 | 3 | 5/7 |
| Minerva | 1 | 2 | 4 | 1/7（桥接绕过） |
| **总计** | **4** | **9** | **10** | **12/23** |

4个 HIGH 严重度中 3 个已修复（H1/H1 args 陷阱、K1 FTS AND 语义、M1 executor），剩 E1（L2感知层全空）。

E1 当前状态: 从 Phase 1 全空到 Phase 4 的 5 阶管道已全部有脚本实现。但质量参差——Structure(68行)和Contextualize(62行)过薄。

### 3.3 失败案例库分析

15个失败案例（按日期）:

**2026-05-13 (6个) — Phase 1/2 阶段:**
- FAIL-001: committee-overdesign（委员会8角色设计过度）
- FAIL-002: threshold-not-actionable（安全评分阈值不可执行）
- FAIL-003: ssb-no-consumers（SSB无消费者）
- FAIL-004: kos-mcp-workspace-config（工作区配置错误）
- FAIL-005: kos-fts5-chinese-and（中文AND搜索失效）
- FAIL-006: irreversible-ops-intercepted（不可逆操作被拦截）

**2026-05-14 (9个) — Phase 2/3 阶段:**
- FAIL-003: test-failure-for-ssb-validation（SSB验证测试失败）
- FAIL-007: SSB-injection-detected（SSB注入攻击被检测）
- FAIL-008: perception-poison-passed（感知投毒绕过滤）
- FAIL-009: committee-deadlock（委员会死锁）
- FAIL-010: cron-delay-accumulated（Cron延迟累积）
- FAIL-011: minerva-timeout-chain（Minerva超时链）
- FAIL-012: state-drift-weekend（STATE周末漂移）
- FAIL-013: ssb-overflow-stress（SSB溢出压力）
- FAIL-014: handoff-conflict（HANDOFF并发冲突）

**根因模式:**
1. 设计未考虑实施约束 → FAIL-001, FAIL-002
2. 安全功能未做对抗测试 → FAIL-008
3. 跨系统集成假设未验证 → FAIL-003, FAIL-004, FAIL-005, FAIL-011
4. 运行时边界条件 → FAIL-009, FAIL-010, FAIL-012, FAIL-013, FAIL-014

### 3.4 问题教训对应关系

从 PROBLEMS-LESSONS-ITERATIONS.md 的 5 大教训:

| # | 教训 | 是否已解决 | 遗留 |
|----|------|-----------|------|
| 1 | 架构设计不做实施约束检查 | ✅ pre_design_check.py | 习惯未养成，需强制执行 |
| 2 | hermes config set args陷阱 | ✅ 手动修复+文档记录 | 工具行为本身未修复 |
| 3 | 过滤器有效性验证滞后 | ✅ content_integrity.py | 仅此一处修复，其他安全功能仍未对抗测试 |
| 4 | 跨Agent依赖未提前考虑 | ✅ WF-005自动化 | delegate_task能力边界仍未正式文档化 |
| 5 | 安全评分与功能评分矛盾 | ✅ 沟通问题已记录 | 下次架构变更仍需提前告知 |

### 3.5 债务审计发现

**问题 D1: 文档爆炸 [P1]**
- 101个 .md 文档，doc/script 比 4.59:1
- 大量复盘文档（REVIEW × 5、REDTEAM × 3、RETROSPECTIVE × 2、PHASE-PLAN × 4）
- 许多文档内容重叠（如 REDTEAM v1/v2/v3 和 SCENARIO-VERIFICATION）
- 风险：新 Agent 读取负担重，关键信息淹没在历史记录中

**问题 D2: 过期文档未标记 [P1]**
- FINAL-RETROSPECTIVE.md 描述 Phase 1→Phase 3，已是 Phase 4
- Phase 1/2/3 各阶段计划文档已过时但仍存在
- 没有文档过期/归档机制
- 建议：增加 DEPRECATED.md 索引或使用 frontmatter status 字段

**问题 D3: STATE.yaml 与 AGENTS.md 不同步 [P1]**
- STATE.yaml: Phase 4, 7 cron, 18 scripts, 59 commits, 131 files
- AGENTS.md: Phase 3 CLOSED, 6 cron, 38+ commits
- AGENTS.md 是 Agent 入口必读文档，信息陈旧导致新 Agent 获取错误上下文

**问题 D4: jieba_dict.txt 版本管理问题 [P3]**
- scripts/jieba_dict.txt：5,071,852 字节（~5MB）
- 这是一个字典文件，不是脚本，不应在 scripts/ 中
- 未检验是否应提交到 Git（5MB 大文件）

**问题 D5: ALL-MODULE-ISSUES 未更新 [P2]**
- 最后更新: 2026-05-13
- Phase 3→4 期间新问题未记录
- 修复率 12/23 基于 Phase 1/2 数据，实际可能已变化

---

## 第四章：汇总

### 4.1 优先级矩阵

| 优先级 | 问题数 | 关键项 |
|--------|--------|--------|
| P0 | 1 | F1: 测试严重不足 |
| P1 | 7 | F3/F4: 核心脚本无测试; D1: Phase版本不一致; A1: GENOME版本冻结; A2: 委员会闲置; D1: 文档爆炸; D2: 过期文档; D3: STATE与AGENTS不同步 |
| P2 | 6 | F2/D2-D5/A3: 命名规范/架构漂移/感知管道薄点等 |
| P3 | 2 | A4: SharedBrain未集成; D4: jieba_dict位置问题 |

### 4.2 关键指标快照

```
指标                     当前值         健康度
──────────────────────────────────────────────
脚本数                    19            ✅
测试覆盖率                21%           🔴 P0
Cron在线率                100% (7/7)    ✅
失败案例                  15            ✅ 
HANDOFF历史               12            ✅
ADR决策                  10            ✅
doc/script比率            4.59:1        🟡 P1
架构实现度                85%           🟡
安全评分                  82%           🟡
文档一致性                ⚠️ 多冲突      🔴 P1
委员会活跃度              闲置           🟡 P1
```

### 4.3 建议行动路线

**立即（本周）:**
1. [P0] 为 ssb_client.py 编写核心功能测试（发布/查询/恢复）
2. [P0] 为 filter_scorer.py 编写质量评分测试
3. [P1] 同步 AGENTS.md 与 STATE.yaml 状态信息
4. [P1] 更新 GENOME.md Phase 描述（或标记为需要 RFC）

**短期（本月）:**
5. [P1] 为核心脚本添加测试，目标 test/script ≥ 50%
6. [P1] 驱动一次委员会实际业务（如 Phase 5 规划）
7. [P1] 建立文档过期标记机制
8. [P2] 补充 Structure 和 Contextualize 管道实现

**中期（下季度）:**
9. [P2] 解决 SSB 设计 vs 实现漂移（真正的消息总线或更新文档）
10. [P2] 实例化 IPA 运行时模型
11. [P2] 更新 SUBSYSTEM-IDENTITY 反映 Phase 4 身份
12. [P3] 评估 SharedBrain 集成可行性并更新架构图

---

*审计完成: 2026-05-15 10:55 CST*
*工具: read_file × 24, search_files × 10, terminal × 1*

---

## 第五章：代码质量 + 安全审计（补充）

### 5.1 代码重复 [P1]

发现大量代码重复，主要集中在:

1. **SSB 建表SQL重复** — capture_watcher.py, ssb_client.py, filter_scorer.py 三文件各定义相同的 ssb_events CREATE TABLE（约18行逐行相同）
2. **SQL INSERT重复** — 19列INSERT语句在 capture_watcher.py 和 filter_scorer.py 中重复出现至少5次（30行×5=150行）
3. **DB连接模式重复** — `_get_conn()` (sqlite3.connect + row_factory + WAL) 在3个文件中各自实现
4. **`_now()` 辅助函数** — 在4个文件中重复定义

建议: 抽取 `ecos_common.py` 共享模块，包含建表SQL、连接工厂、时间工具。

### 5.2 ssb_auth.py 签名验证未完成 [P1]

`verify()` 函数计算了预期 HMAC 签名，但从未与存储值比较——只做存在性检查。**签名验证实际无效。**

### 5.3 硬编码路径 [P2]

- contextualize_pipeline.py: `/Users/xiamingxing/Library/Mobile Documents/iCloud~md~obsidian/...`
- integrate_pipeline.py: 同上
- 移植性差，建议使用环境变量 `ECOS_HOME` 或 `~/.ecos/config`

### 5.4 密钥安全 [✅]

- 无硬编码密钥/Token
- .ssb_key 0600权限，已在 .gitignore 排除
- 无自定义加密实现

### 5.5 注释率 [P2]

整体注释率 5.7%（行业推荐 20-30%）。realtime_guard.py 76行仅2行注释。

### 5.6 .gitignore 遗漏 [P2]

`ecos.jsonl.backup.*` 备份文件未被排除，可能被意外提交。

---

### 更新后优先级矩阵

| 级别 | 数量 | 关键项 |
|------|------|--------|
| P0 | 1 | 测试严重不足（21%, 0单元测试） |
| P1 | 9 | +代码重复200行 / ssb_auth签名失效 / AGENTS-STATE不一致 |
| P2 | 8 | +硬编码路径 / 注释率低 / .gitignore遗漏 |
| P3 | 2 | SharedBrain未集成 / jieba_dict位置 |
