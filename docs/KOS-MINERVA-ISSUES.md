# KOS & Minerva 问题详析

> 日期: 2026-05-13 | 基于 Phase 1 完整测试 + 代码审查

---

# 一、Minerva 问题

---

## M1: MCP Server Executor 未初始化 (HIGH)

**现象:** 9 个 MCP 工具中 7 个返回 "Minerva MCP server not initialized"

**根因:**
```python
# server.py:32 — executor 全局变量为 None
executor: ResearchExecutor | None = None

# server.py:35-42 — 所有核心工具调这个检查
def _ensure_executor():
    if executor is not None:
        return executor
    raise RuntimeError("Minerva MCP server not initialized.")

# server.py:244-248 — init_server() 存在但从未被调用
def init_server(executor_instance: ResearchExecutor):
    global executor
    executor = executor_instance

# server.py:250 — main() 入口跳过了初始化
def main():
    mcp.run()  # ← 直接跑, 不调 init_server()
```

**影响:**
```
可用:   list_resources, list_prompts (FastMCP 自带的)
不可用: research_now, research_schedule, research_watch,
         knowledge_search, knowledge_ingest,
         read_resource, get_prompt (以上全部调 _ensure_executor)
```

**修复方向:**
- main() 中添加 executor 自动初始化
- 或通过 CLI 参数控制是否加载完整 executor
- 当前 eCOS 绕过此问题: 使用 KOS MCP research_now → Minerva CLI 子进程

**责任方:** Minerva 上游 (非 eCOS 引入)

---

## M2: Research Pipeline 超时 (~25% 概率) (MED → FIXED)

**现象:** KOS MCP research_now 偶尔返回 TimeoutError (120s 限制)

**根因:**
- Minerva L0 管道: decompose→search→entity_extract→deep_read→cross_analyze→counter_argument→quality_gate→verify→output
- Search 阶段: 5-15s (DDG·Scholar·arXiv·Metaso·Exa 并行)
- Output 阶段: 40-85s (LLM 生成结构化报告)
- 总计: 47-120s, 部分查询超过旧 120s 限制

**实测数据 (6次调用):**
```
47s  ✅  多模态 智能体
54s  ✅  2026年AI Agent技术趋势
95s  ✅  房山区 智慧医疗 AI 2025
120s ❌  2025-2026 政务数字化平台建设趋势 多模态 智能体 (首次超时)
47s  ✅  政务数字化平台 多模态 2025 (重试成功)
120s ❌  政务服务平台 AI智能体 政策问答 (超时)
```

**修复:** KOS MCP timeout: 120s → 180s (config.yaml)

**残留风险:** output 阶段可能超过 180s 如果 LLM 生成特别长

---

## M3: Semantic Search 返回空 (MED)

**现象:** `mcp_kos_semantic_search(query="信息化项目管理经验")` → 0 results

**根因:**
```python
# kos-mcp-server.py:294-306
def tool_semantic_search(query, limit=10):
    if MINERVA_EXE:
        r = sp.run([sys.executable, "-m", "minerva.search.engine", ...])
        if r.returncode == 0:
            return ...  # Minerva LanceDB
    # Fallback to KOS FTS5
    return tool_search_knowledge(query, limit=limit)
```

Minerva LanceDB 嵌入向量未填充, 返回非零 → 回退到 KOS FTS5 → AND语义下多词匹配为空。

**修复方向:**
- 填充 Minerva LanceDB 向量索引
- 或直接使用 KOS FTS5 (当前 OR 模式修复后改善)

---

## M4: Quality Score 始终 N/A (LOW)

**现象:** 所有研究报告 quality_score=N/A/100

**根因:** Minerva L0 管道跳过了 quality_gate stage
- L1+ 管道才启用 quality_gate
- L0 是快速/免费模式, 质量评估被视为"optional"

**影响:** 无法自动判断研究质量, I3.1(感知层质量过滤)需要此数据

---

## M5: 学术来源被限流 (LOW)

**现象:** 日志中出现 `429 Client Error for api.semanticscholar.org`

**根因:** Semantic Scholar API 无认证密钥时限流严格
- IP-based rate limiting
- 影响: entity_extraction 和 deep_read 阶段缺少学术文献

---

## M6: Knowledge Base 未共享 (LOW)

**现象:** Minerva 维护独立的 SQLite+LanceDB+Neo4j, 与 KOS 不互通

**根因:** Minerva KB 路径: `~/minerva/knowledge.db`, KOS DB: Obsidian vault 内

**影响:** Minerva 研究报告不包含在 Minerva 自己的 knowledge_search 范围内 (只有通过 KOS manifest 扩展才能检索)

---

# 二、KOS 问题

---

## K1: FTS5 中文搜索 AND 语义 (HIGH → FIXED)

**现象:**
```
search_knowledge("场景验证测试") → 0 results
search_knowledge("场景")         → 3 results
search_knowledge("数字化平台 建设") → 0 results
search_knowledge("数字化")       → 5 results
```

**根因:**
```python
# KOS MCP 原始代码: query 直接传入 SQLite FTS5 MATCH
sql = """SELECT ... FROM documents_fts WHERE documents_fts MATCH ?"""
params = [query]  # FTS5 MATCH 默认 AND 语义
```

SQLite FTS5 MATCH 语法:
- `"场景验证测试"` → 作为一个整体 token 搜索 → 该 token 不在索引中
- `"场景"` → 单 token 搜索 → 命中

**修复 (已实施):**
```python
# +8 行补丁: 默认 OR 模式
if match_mode == "OR" and " OR " not in query:
    tokens = query.split()
    if len(tokens) > 1:
        query = " OR ".join(tokens)
# "场景验证测试" → "场景 OR 验证 OR 测试" → FTS5 MATCH OR
```

**局限:** `query.split()` 对中文按空格分词, 无空格的中文短语仍会被当作整体。需要中文分词器 (jieba) 才能根本解决。

---

## K2: 索引器不跟随 Symlink (MED → WORKAROUND)

**现象:** `ln -s ~/knowledge/reports ~/Workspace/minerva/reports` 后, 索引器扫描 510 文件 (不含 reports/ 中 449 份)

**根因:**
```python
# kos-indexer.py:640
for f in zone_path.rglob("*"):  # Path.rglob() 不跟随 symlink
```

Python Path.rglob() 默认不跟随符号链接 (安全设计, 防止循环遍历)。

**影响:** 无法通过 symlink 将外部目录纳入 KOS 索引范围

**Workaround (已实施):** manifest 新增 minerva_reports zone + domain

---

## K3: MCP Server 移植性限制 (MED)

**根因:**
```python
# kos-mcp-server.py:21-22
from config import get_vault_ops_dir
VAULT_OPS_DIR = get_vault_ops_dir()
# → /Users/xiamingxing/Library/Mobile Documents/iCloud~md~obsidian/...
```

KOS MCP server 硬编码了 Obsidian iCloud vault 路径。workspace_config 模块也在该路径中。

**影响:** KOS MCP Server 只能在当前 Mac 上运行, 不可移植到其他机器或容器。

**修复方向:** workspace_config 应作为独立 Python 包安装, 而非硬编码路径。

---

## K4: Zone 单路径限制 (LOW → WORKAROUND)

**现象:** 每个 zone 仅支持一个 `absolutePath` 或 `relativePath`

**根因:** Manifest Schema 设计: zone 配置无 secondaryPaths 字段

**Workaround (已实施):** 新增独立 zone+domain (minerva_reports)
- 优点: 语义清晰, 搜索时可单独指定域
- 缺点: KOS 域数量膨胀 (6→7, 未来可能更多)

---

## K5: Gongwen 模板排除 (LOW)

**根因:**
```python
# workspace-manifest.json → indexing.searchDefaultExclude
# 228K 公文模板默认不参与搜索
```

**影响:** gongwen 域 4985 文档中, 模板占多数但默认不搜。需加 `include_templates=true` 才搜。

**状态:** 合理的设计, 不是 bug

---

## K6: Tool 缺少 KOS_READY 守卫 (LOW)

**根因:**
```python
KOS_READY = False
try:
    from workspace_config import get_workspace_manifest, ...
    KOS_READY = True
except ImportError:
    pass  # ← 静默, 但后续 tool 函数直接调用未检查
```

`tool_list_domains()`, `tool_search_knowledge()` 等直接调用 `get_workspace_manifest()`, 未检查 KOS_READY。

**实际影响:** 当前环境 workspace_config 可用 → 无影响。但如果移植到新环境会崩溃而非优雅降级。

---

## K7: Snippet 仅显示标题 (MED)

**现象:** KOS 搜索结果的 snippet 字段只展示文档标题, 不显示正文匹配上下文

**根因:** FTS5 snippet() 函数的表结构或 tokenization 配置导致正文命中未高亮

**影响:** 搜索结果可发现文档, 但用户看不到正文匹配片段, 降低了搜索结果的可信度

**验证:** 正文已完整索引 (gongwen PDF 7641 字符可读), 但 snippet 未展示

---

# 问题汇总

```
         Minerva                  KOS
         ────────                 ───
HIGH:    1 (executor)             1 (FTS5 AND → FIXED)
MED:     2 (timeout→FIXED,        3 (symlink, 移植性, snippet)
         semantic_search空)
LOW:     3 (quality=N/A,          3 (单路径→WORKAROUND,
         限流, KB拆分)            模板排除, 守卫缺失)
```

---

*关联: DEEP-REVIEW-2026-05-13.md*
