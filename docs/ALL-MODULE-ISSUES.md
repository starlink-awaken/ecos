# eCOS Phase 1 — 全模块问题清单

> 日期: 2026-05-13 | 范围: eCOS/Hermes/KOS/Minerva/集成层

---

## 模块总览

```
┌─────────────────────────────────────────┐
│              eCOS (本项目)                │
│  4 架构债务 · 1 纪律问题 · 1 安全缺口     │
├─────────────────────────────────────────┤
│              Hermes (Agent平台)           │
│  1 配置陷阱                               │
├─────────────────────────────────────────┤
│              集成层                       │
│  2 路径对齐 · 1 协议问题                  │
├──────────────────┬──────────────────────┤
│    KOS (知识OS)   │  Minerva (深度研究)    │
│    7 问题         │  7 问题               │
└──────────────────┴──────────────────────┘
```

---

# 一、eCOS 自身问题

---

## E1: L2 感知层全空 — 五阶管道未实现 (ARCH-DEBT)

**严重度:** HIGH | **类型:** 架构债务

**问题:**
GENOME P2 "信息熵公理"定义的核心降熵机制 (Capture→Filter→Structure→Contextualize→Integrate) 在 Phase 1 完全未实现。当前 KOS 直接索引原始文件，Minerva 报告直接落盘，没有预处理管道。

**现状:**
```
Capture:       ❌  无统一信息捕获入口
Filter:        ❌  无质量过滤，Minerva报告 Quality=N/A 也入库
Structure:     ⚠️  KOS索引器承担，但格式不统一
Contextualize: ❌  新文档不自动关联已有实体/项目
Integrate:     ❌  跨域语义链接未建立
```

**影响:** 知识质量不可控，低质量/Minerva 不可靠报告与高质量用户文档在 KOS 中同等待遇。

**计划:** Phase 2 感知层实现 (迭代 I3)

---

## E2: L6 反馈层滞后 — 无实时宪法执行 (ARCH-DEBT)

**严重度:** MED | **类型:** 架构债务

**问题:**
宪法执行器 (L6) 仅在 WF-003 (每周一) 运行。宪法违反到检测间隔可达 7 天。

**已实现:** git diff GENOME 监控、STATE cron 交叉验证
**缺失:** 无操作前 hook (执行不可逆操作前无自动宪法检查)、无实时告警

**影响:** 安全窗口过长。Agent 可能在周一检查前进行多次宪法违反操作。

**计划:** 迭代 I2 (短期间隔检查) + Phase 2 (实时 hook)

---

## E3: SSB 设计完整但零生产使用 (ARCH-DEBT)

**严重度:** LOW | **类型:** 架构债务

**问题:**
SSB Event Schema v1 定义了 10 种 Event 类型，但 Phase 1 完全退化为文件读写 (STATE.yaml + HANDOFF)。消息总线、事件持久化、信息素场语义均未实现。

**ADB-005 设计:** "异步消息总线，不阻塞 Agent 执行"
**Phase 1 现实:** "STATE.yaml 写入操作"

**计划:** Phase 2 (SQLite 消息队列 → SharedBrain → 消息队列)

---

## E4: IPA 运行时模型未实例化 (ARCH-DEBT)

**严重度:** LOW | **类型:** 架构债务

**问题:**
IPA (Intelligence-Persistence-Action) 三层是运行时模型，但系统中没有对应的运行框架。IPA 和六层的关系仅在文档中描述，未在代码中体现。

**计划:** Phase 2 委员会实现时实例化 IPA 框架

---

## E5: HANDOFF 更新纪律 — Agent 依赖问题 (DISCIPLINE)

**严重度:** MED → MITIGATED | **类型:** 运维

**问题:**
Agent 在阶段完成后未自动更新 HANDOFF。场景验证 S3 发现 HANDOFF 滞后 3.5 小时。

**缓解:** WF-005 (每 2h 自动检查更新) + agent_signature 字段 (P1修复)
**残留:** WF-005 刚上线，效果待验证

---

## E6: STATE.yaml 手动维护容易疏漏 (DISCIPLINE)

**严重度:** LOW → MITIGATED | **类型:** 运维

**问题:**
STATE.yaml 完全依赖 Agent 手动更新。WF-005 部署后 STATE 未同步更新，WF-001 部署时也漏记。

**缓解:** WF-003 交叉验证 (STATE.cron vs 实际 cronjob list)
**残留:** 文件数量、安全评分等字段仍依赖手动

---

# 二、Hermes 问题

---

## H1: hermes config set 的 args 类型陷阱 (TOOL-BUG)

**严重度:** HIGH → FIXED | **类型:** 工具行为

**问题:**
```bash
hermes config set mcp_servers.kos.args '["/path/to/kos-mcp-server.py"]'
```
将 args 存储为 JSON 字符串而非 YAML 列表。导致 MCP Server 解析失败：
```
Input should be a valid list [type=list_type, input_value='["..."]', input_type=str]
```

**修复:** config.yaml 手动编辑为 YAML 列表格式
**根因:** `hermes config set` 的序列化逻辑不支持复杂类型

**教训:** 配置后必须验证，不要假设工具的行为。

---

# 三、集成层问题

---

## I1: Minerva 研究产出路径 vs KOS 索引范围 (PATH-MISMATCH)

**严重度:** MED → FIXED | **类型:** 路径对齐

**问题:**
Minerva 研究产出: `~/knowledge/reports/` (硬编码在 stages.py)
KOS minerva zone: `~/Workspace/minerva/` (manifest 配置)
→ 不在同一棵树下，KOS 搜索不到研究报告

**尝试:** symlink → 被 rglob() 忽略
**最终方案:** KOS manifest 新增 minerva_reports zone + domain

**修复文件:** workspace-manifest.json (+18 行)

---

## I2: KOS MCP Timeout vs Minerva Pipeline 耗时 (TIMEOUT-MISMATCH)

**严重度:** MED → FIXED | **类型:** 超时配置

**问题:**
KOS MCP 旧 timeout=120s，Minerva L0 管道 47-120s。约 25% 查询超时。

**修复:** timeout: 120s → 180s (config.yaml mcp_servers.kos.timeout)

---

## I3: Minerva MCP → KOS MCP 桥接发现 (ARCH-FINDING)

**严重度:** INFO | **类型:** 架构理解

**发现:**
Minerva MCP 的 7/9 工具不可用不是"我们的集成问题"，而是 Minerva 的有意设计——MCP 统一入口是 KOS，Minerva 是引擎层。

**正确的调用路径:**
```
Hermes → KOS MCP research_now → Minerva CLI (子进程)
```

**验证:** KOS MCP research_now 完全可用 (47-95s, 5源, $0)

---

# 四、KOS 问题

---

## K1: FTS5 AND 语义 — 中文多词搜索失效 (HIGH → FIXED)

```
"场景验证测试" → 0 results (AND: 三个token必须同时出现)
"场景"         → 3 results (单词)
```

**根因:** SQLite FTS5 MATCH 默认 AND 语义 + 中文无空格无法分词

**修复:** kos-mcp-server.py +8 行: match_mode 参数, 默认 OR
```python
tokens = query.split()
query = " OR ".join(tokens)  # "场景 OR 验证 OR 测试"
```

**局限:** `split()` 按空格分, 无空格的中文短语仍是整体。需 jieba 分词才能根本解决。

---

## K2: rglob() 不跟随 Symlink (MED → WORKAROUND)

**根因:** `Path.rglob("*")` 安全设计，不跟随符号链接。

**Workaround:** manifest 扩展 (新 zone+domain) 替代 symlink 方案

---

## K3: 硬编码 Obsidian Vault 路径 — 移植性限制 (MED)

```python
VAULT_OPS_DIR = get_vault_ops_dir()
# → ~/Library/Mobile Documents/iCloud~md~obsidian/.../obsidian-vault/
```

**影响:** KOS MCP Server 只能在此 Mac 上运行。workspace_config 模块也在该路径中。

---

## K4: Zone 单 absolutePath 限制 (LOW → WORKAROUND)

每个 zone 仅一个路径。解决方案: 新增 minerva_reports zone+domain。

---

## K5: 228K 公文模板默认排除 (LOW — 设计如此)

gongwen 域 indexable=true 但 228K 模板默认不参与搜索。需显式 `include_templates=true`。

---

## K6: Tool 缺少 KOS_READY 守卫 (LOW)

workspace_config 不可用时, tool 函数无优雅降级, 直接崩溃。

---

## K7: Snippet 仅显示标题 — 正文命中未高亮 (MED)

**现象:** 搜索命中但 snippet 字段只展示文档标题，不显示正文匹配片段。

**验证:** 正文已完整索引 (gongwen PDF 7641字符可搜索到)，但 snippet() 未输出上下文。

---

# 五、Minerva 问题

---

## M1: MCP Server Executor 未初始化 (HIGH)

```
main() → mcp.run()  # 跳过 init_server()
executor = None      # 7个核心工具全部返回 "not initialized"
```

**可用:** list_resources, list_prompts (框架自带)
**不可用:** research_now, research_schedule, research_watch, knowledge_search, knowledge_ingest, read_resource, get_prompt

**绕过:** KOS MCP research_now → Minerva CLI 子进程

---

## M2: L0 Pipeline 耗时波动大 (MED → FIXED)

实测: 47-120s。~25% 超旧 120s 限制。
修复: KOS MCP timeout → 180s

---

## M3: LanceDB 向量嵌入未填充 (MED)

semantic_search 返回空。需运行嵌入生成管道。

---

## M4: Quality Gate 在 L0 被跳过 (LOW)

所有 L0 报告 quality_score=N/A。L1+ 才启用 quality_gate。

---

## M5: Semantic Scholar API 429 限流 (LOW)

无认证密钥, IP 限流严格。学术来源缺失。

---

## M6: 独立知识库与 KOS 不互通 (LOW)

Minerva 维护独立 SQLite+LanceDB+Neo4j, 研究报告需通过 KOS manifest 扩展才能被搜索。

---

## M7: ResearchExecutor 构造依赖重 (LOW)

```python
ResearchExecutor(triage_router, pipeline, knowledge_store, cost_guard)
# 4 个必需参数, 不能空构造
```

即使用 wrapper 方案也需要大量初始化代码。

---

# 汇总

```
模块         HIGH    MED     LOW     已修复/Workaround
──           ──      ──      ──      ──
eCOS         1       2       2       2/5
Hermes       1       0       0       1/1
集成层       0       2       1       3/3
KOS          1       3       3       5/7
Minerva      1       2       4       1/7 (桥接绕过)

总计         4       9       10      12/23 已解决
```

---

*关联: DEEP-REVIEW-2026-05-13.md, KOS-MINERVA-ISSUES.md, REDTEAM-ANALYSIS-2026-05-13.md*
