---
fail_id: FAIL-20260513-004
fail_id: FAIL-20260513-004
date: "2026-05-13"
severity: LOW
domain: 工具调用
status: RESOLVED (FALSE_POSITIVE)
reported_by: Hermes/deepseek-v4-pro

# KOS MCP Server 测试误报 — macOS 工具链差异

## 失败描述

**原始判断：** KOS MCP Server 启动失败，workspace_config 模块缺失导致不可用。

**重新验证结果：**
- KOS MCP Server v1.2.0 在正确工作目录下完全可用
- 13 个工具全部注册：search_knowledge, get_knowledge, get_system_status, list_domains, cross_domain_sync, get_entity, search_entity, ontology_rebuild, ontology_graph, run_indexer, full_sync, research_now, semantic_search
- 原始测试失败原因：macOS 缺少 `timeout` 命令（Linux 工具），且测试时未设置正确的 cwd

**根因：** 测试工具链差异（macOS vs Linux），非 KOS 问题。正确验证流程：`cd ~/Workspace/Tools/kos && echo '...' | python3 kos-mcp-server.py`

## 经验萃取

> macOS 开发环境中缺少 Linux 工具（如 timeout）。验证 MCP Server 时应使用 Python subprocess 或 gtimeout（brew install coreutils），而非 timeout。

## 相关文档

- kos-mcp-server.py

## 影响评估

- 数据损失：否
- 可逆性：可逆（修复依赖或重写配置加载）
- 影响范围：KOS MCP 接入完全阻塞，Hermes 无法使用 KOS 13 个 MCP 工具
- 时间损失：诊断 10 分钟

## 纠正措施

**短期（建议）：**
1. 找到或创建 `workspace_config` 模块（需确认 KOS 作者意图）
2. 或：修改 `kos-mcp-server.py`，为每个 tool 函数添加 KOS_READY 守卫，优雅返回错误而非崩溃
3. 或：为 MCP Server 提供独立的配置加载方式（不依赖 obsidian-vault）

**中期：** workspace_config 应作为 KOS 安装的一部分，不应依赖外部路径

**长期：** MCP Server 应支持 config 参数传入，支持 standalone 部署

## 经验萃取

> 文件存在 ≠ 可运行。MCP Server 接入必须做实际启动测试，不能只看代码。

## 相关文档

- /Users/xiamingxing/Workspace/Tools/kos/kos-mcp-server.py:25 (workspace_config import)
- STATE.yaml, config.yaml mcp_servers.kos
