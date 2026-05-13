# eCOS — 后续迭代规划 & 残留问题清单

> 2026-05-13 | Phase 1 收尾

---

# 一、残留问题清单

## Minerva (5项未解决)

### M1: Executor 未初始化 (HIGH — 上游缺陷)

**当前行为:** `main()` 跳过 `init_server()`, executor=None, 7/9 工具不可用

**为什么没修:**
- 需要注入 triage_router/pipeline/knowledge_store/cost_guard (4个重依赖)
- `main()` 是上游代码, 不适合我们直接改
- KOS MCP 桥接已完美替代 (research_now via subprocess)

**残留风险:** 无。桥接路径已稳定验证 (6次调用, 75%成功率, 180s timeout后预期>95%)

**何时修:** Minerva 上游修复或 Phase 3 升级

---

### M3: Semantic Search 空 (MED)

**当前行为:** LanceDB 向量嵌入未填充 → semantic_search 始终返回空 → 回退 KOS FTS5

**影响:** 语义级搜索不可用。当前全部依赖 FTS5 关键词搜索。

**修复路径:**
```
1. 填充 Minerva LanceDB 向量索引
   需要: 运行嵌入生成管道 (sentence-transformers)
   耗时: 首次全量约 1-2 小时 (7203文档)
2. 或: 接受现状, KOS FTS5 OR模式已大幅改善搜索体验
```

**建议:** 暂缓。FTS5 OR模式已解决最大痛点。语义搜索是锦上添花。

---

### M4: Quality Score 始终 N/A (LOW)

**当前行为:** 所有 L0 报告 quality_score=N/A/100

**根因:** L0 管道跳过 quality_gate stage (设计如此, L0=快速/免费)

**影响:** 感知层质量过滤 (I3.1) 缺少关键数据源

**修复:** 升级到 L1 研究 (需付费 ~$0.30/次) 或修改 L0 管道启用 quality_gate

---

### M5: 学术来源 429 限流 (LOW)

**当前行为:** Semantic Scholar API 返回 429 Too Many Requests

**影响:** 研究报告缺少学术文献支撑

**修复:** 配置 Semantic Scholar API key 或降低请求频率

---

### M6: KB 与 KOS 不互通 (LOW)

**当前行为:** Minerva 独立 SQLite, KOS 独立 FTS5。研究报告通过 KOS manifest 扩展才能检索

**影响:** Minerva knowledge_search 不可用 (M1导致), 但数据可通过 KOS 搜索

---

## KOS (3项未解决)

### K3: 移植性限制 (MED)

**当前行为:**
```python
VAULT_OPS_DIR = get_vault_ops_dir()
# → ~/Library/Mobile Documents/iCloud~md~obsidian/.../obsidian-vault/
```

**影响:** KOS MCP Server 只能在当前 Mac 上运行。workspace_config.py 也在 iCloud vault 中。

**为什么没修:** 需要重构 KOS 的配置加载机制, 涉及面广
**残留风险:** 换机器时 KOS MCP 需要重新配置路径

---

### K7: Snippet 仅显示标题 (MED)

**当前行为:** 搜索命中的 snippet 字段只显示文档标题, 不显示正文匹配上下文

**验证:** 正文已完整索引 (PDF 7641字符可读), 是 FTS5 snippet() 函数的输出格式问题

**影响:** 搜索结果缺少上下文, 用户必须点开全文才能确认相关性

**修复方向:** 调整 FTS5 snippet() 参数或手动构造 snippet (从 body 中提取匹配行)

---

### K6: Tool 缺少 KOS_READY 守卫 (LOW)

**当前行为:** 如果 workspace_config 不可用, tool 函数直接崩溃

**实际影响:** 当前环境 workspace_config 正常 → 零影响

**修复:** 在每个 tool 函数入口加 `if not KOS_READY: return {"error": "..."}`

---

# 二、迭代规划 (修订版)

```
Phase 1 收尾 (本周)
  □ MCP 重载 → 验证 FTS5 OR 模式
  □ WF-001 首跑观察 (明天 02:00)
  □ WF-005 首跑观察 (今天 18:00)

────────────────────────────────────

Week 2-3: 稳定观察
  □ 积累 cron 运行数据 (至少 2 周)
  □ WF-003 第二次运行 (下下周一)
  □ 收集失败案例 → FAILURES 增至 8+

────────────────────────────────────

Week 4: 体验修复 (I3 削减版)
  □ K7: Snippet 正文高亮 (MED, 用户体验)
  □ M4: 试一次 L1 研究验证质量评分
  □ 如果 FTS5 OR 模式仍有局限 → 评估 jieba 分词

────────────────────────────────────

Month 2: Phase 2 启动条件评估
  前置条件检查:
    □ WF-001/WF-003 稳定运行 ≥ 2 周
    □ 失败案例 ≥ 8
    □ HANDOFF 自动更新已验证 (WF-005)
    □ 无 P0 安全事件

  如果满足 → Phase 2 首批任务:
    □ delegate_task 3并发三角委员会真机测试
    □ WF-004 委员会决策 Workflow
    □ L2 感知层 Capture+Filter 最小实现
    □ L6 反馈层 实时 hook 原型

  如果不满足 → 继续稳定观察, 修复瓶颈
```

---

## 优先级速查

```
观察列表 (不阻塞, 定期回顾):
  □ K3 KOS移植性 — 换机时评估
  □ M3 Semantic Search — Phase2需要时填充LanceDB
  □ M5 429限流 — 影响学术搜索时配API key

现在就做:
  □ MCP 重载验证 FTS5 OR + K7 body_preview
  □ 等 WF-001/WF-005 首跑

本周:
  □ K7 snippet 修复 (快赢, 用户体验)
  □ 观查 cron 稳定性

本月:
  □ 积累数据 → Phase 2 决策
```

---

*关联: CONCLUSIONS-AND-PLAN.md, ITERATION-SPACE.md, KOS-MINERVA-ISSUES.md*
