---
fail_id: FAIL-20260513-005
date: "2026-05-13"
severity: LOW
domain: 工具调用
status: FIXED
reported_by: Hermes/deepseek-v4-pro（场景验证）

# KOS FTS5 中文多词搜索 AND 语义导致命中率低

## 失败描述

详见原内容。修复方向：Agent 使用单关键词搜索，Hermes 负责多步整合。
此问题在 KOS FTS5 层，非 eCOS 问题。
**预期结果：** KOS `search_knowledge("数字化平台 建设 架构")` 应返回包含任一关键词的文档。

**实际结果：** 命中 0 文档。但单关键词"数字化"命中 5 文档。

**原因：** KOS 使用 SQLite FTS5 MATCH 语法，默认 AND 语义——文档必须同时包含所有搜索词。中文无空格分词，FTS5 将"数字化平台 建设 架构"视为三个独立 token，要求全部匹配。

**影响范围：**
- `"数字化平台 建设"` → 0 results (实际: 单"数字化"→5)
- `"信息化建设 总结"` → 0 results (实际: 单"信息"→1)
- `"考核"` (单词) → 0 results (gongwen域, 可能有其他tokenization问题)

唯一可靠的使用方式：**单关键词搜索**

## 根因分析

1. Why 1: FTS5 MATCH 默认 AND → SQLite FTS5 设计如此
2. Why 2: 无 OR 语法支持 → KOS MCP 未对查询做预处理（如自动添加 OR）
3. Why 3: 中文 tokenization → FTS5 内置 tokenizer 对中文不如英文友好
4. Why 4: 模板排除 → gongwen 域 228K 模板默认排除，实际可检索文档(4,985)中部分命中可能被过滤

## 纠正措施

**短期（无需改）：** Agent 使用单关键词搜索，由 Hermes 的推理能力负责多步搜索整合
**中期（建议 KOS）：** search_knowledge 参数增加 `match_mode: AND | OR`，默认 OR
**长期（建议 KOS）：** 引入 jieba 分词 + FTS5 自定义 tokenizer

## 经验萃取

> FTS5 的中文搜索能力远弱于英文。Agent 应默认使用单关键词搜索，通过多轮检索替代单次复杂查询。

## 相关文档

- kos-mcp-server.py (tool_search_knowledge)
- STATE.yaml known_issues P2
