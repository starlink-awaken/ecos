# eCOS 深度审计 — 执行摘要 (代码+架构+债务)

> 2026-05-15 | 3个并行子Agent | 代码粒度审查

---

## 一、核心发现：6个致命Bug

| # | 脚本 | Bug | 影响 |
|---|------|-----|------|
| F1 | ssb_client.py:458 | `subscribe()` 完全不可用 — 函数返回空列表 | 消费者无法获取事件 |
| F2 | ssb_client.py:492 | `load_state()` 手写YAML解析器不可靠 | 静默数据损坏 |
| F3 | wf-008-bridge.py:62 | INSERT列数与实际Schema不匹配 | 运行时崩溃 |
| F4 | ssb_dump.py:11 | dump仅输出6/20+字段 | 无法用于恢复 |
| F5 | integrate_pipeline.py:96 | query拼接到subprocess代码中 | 任意代码执行 |
| F6 | filter_scorer.py:344 | SELECT→UPDATE无事务保护 | 并发重复处理 |

## 二、架构一致性：57%

SSB Schema 四重分裂（文档/ecos_common/SQLite/JSONL各不同），ecos_common采纳率仅18.8%。STATE.yaml声称85%存在28%乐观偏差。

详见：docs/ARCHITECTURE-COMPLIANCE-AUDIT-2026-05-15.md

## 三、技术债务：52.8/100 (C+)

- 测试：3500行代码仅5%覆盖，16脚本零测试
- 文档：103篇，59%无frontmatter，46处断裂wiki链接
- 路径：5脚本硬编码 `~/Workspace/eCOS`
- 依赖：无requirements.txt、无.env.example
- 数据：日均1400事件增长，无自动化备份

## 四、修复优先级

| 优先级 | 项目 | 工时 |
|--------|------|------|
| **P0** | 修复6个致命Bug | 18h |
| **P0** | 统一SSB Schema | 6h |
| **P0** | 统一路径约定 | 6h |
| **P0** | 创建依赖声明+配置模板 | 3h |
| **P1** | ecos_common+ssb_client核心测试 | 12h |
| **P1** | 手动测试→pytest迁移 | 8h |
| **P2** | filter+capture测试 | 16h |
| **P2** | 合并重叠文档+frontmatter | 14h |
| **P3** | 数据备份自动化 | 6h |
| **总计** | | **~114人时** |

---

*深度审计时间: 2026-05-15 11:30 CST | 3 Agent × ~400s*
