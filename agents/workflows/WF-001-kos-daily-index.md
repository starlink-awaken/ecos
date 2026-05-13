---
id: WF-001
name: KOS 每日索引更新
version: "0.1.0"
trigger: "cron: '0 2 * * *' (每日 02:00 CST)"
priority: P1
risk_level: LOW
committee_required: false
---

# WF-001 KOS 每日索引更新

## 目的

每日凌晨增量索引 KOS 所有知识域，确保新增/修改文档可被检索。

## 角色

单 Agent（Hermes 通过 KOS MCP 调用），无需委员会。

## 前提

KOS MCP Server 已通过 Hermes 验证可用（mcp_servers.kos）。

## 步骤

```
S01: 通过 MCP 调用 run_indexer(incremental=true)
S02: 验证索引结果（doc_count 变化）
S03: 如有新文档 → 推送摘要通知
S04: 无变化 → 静默
```

## 部署

使用 Hermes cronjob 工具创建：

```
prompt: 调用 mcp_kos_full_sync 或 mcp_kos_run_indexer 执行增量索引
schedule: 0 2 * * *
toolsets: [terminal]
note: 待 KOS MCP 被 Hermes 识别后部署
```

## 依赖

- KOS MCP Server 在 config.yaml 中配置
- Hermes 重启后 MCP 工具注册成功

## 回滚

cronjob remove <job_id>

---

*创建: 2026-05-13*
*状态: 设计完成，待 MCP 可用后部署*
