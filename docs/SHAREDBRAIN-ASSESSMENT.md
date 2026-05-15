# SharedBrain B-OS 桥接评估

> 2026-05-15 | Phase 4 Sprint 4 | 评估，不强行接入

## 一、SharedBrain 概览

| 维度 | 值 |
|------|-----|
| 项目 | SharedBrain B-OS (Brain Operating System) |
| 路径 | ~/Workspace/SharedBrain/ |
| 架构 | 7-Chakra Fractal Model (L1-L7) |
| 协议 | bos:// URI + BaseMembrane |
| 事件总线 | Z-Microkernel EventBus (30+ EventType) |
| MCP Server | organs/D-Gateway/mcp_server/ |
| 端口 | API:7420 | MCP_SSE:7421 | Health:8080 |

## 二、与 eCOS 的重叠与差异

| 维度 | eCOS | SharedBrain | 重叠度 |
|------|------|-------------|--------|
| 知识库 | KOS (FTS5+LanceDB, 8K docs) | D-Memory (FactGraph) | 高 |
| 事件流 | SSB (JSONL, 4385 events) | EventBus (pub/sub, async) | 高 |
| 安全审计 | realtime_guard + content_integrity | D-Immunity (Intent Shield) | 中 |
| 任务调度 | Cron (7 jobs) + Kanban | D-Execution (Worker Pool) | 中 |
| Agent委员会 | 5模型 (ACP+CLI) | Hive Mind (L7) | 目标相似 |
| 文档治理 | LADS + ADR | D-Logos (context_compiler) | 中 |

## 三、桥接方案评估

### 3.1 SSB ↔ B-OS EventBus (可行性: 高)

```
eCOS SSB (JSONL) → B-OS EventBus (pub/sub)

桥接方式:
  Python adapter: ecos_ssb_event → BosEvent
  事件映射:
    SSB event_type → EventType enum
    SSB agent → source
    SSB timestamp → B-OS timestamp

优势:
  - 双写: eCOS事件可被B-OS消费 (如审计、监控)
  - 实时性: B-OS EventBus是内存级pub/sub，比SSB更快
  - 解耦: B-OS organs可以订阅eCOS事件

风险:
  - 需要B-OS daemon运行
  - EventBus是内存中，SSB是持久化 — 需双写
  - 引入新依赖 (asyncio, B-OS runtime)

建议: Phase 4.5 轻量适配器，仅关键事件双写
```

### 3.2 KOS ↔ D-Memory (可行性: 中)

```
eCOS KOS (sqlite + LanceDB) → B-OS D-Memory (FactGraph)

差异:
  KOS: 静态文档索引 (文件→全文→向量)
  B-OS D-Memory: 运行时事实图 (动态key-value)

挑战:
  - 存储范式不同 (文档 vs 事实)
  - D-Memory是B-OS内部organ，不适合作为KOS后端
  - 同步延迟和一致性问题

建议: 不桥接。保持KOS独立，B-OS通过事件总线消费KOS搜索结果
```

### 3.3 B-OS MCP Server → Hermes (可行性: 高)

```
B-OS MCP Server (端口7421) → Hermes config.yaml

添加方式:
  hermes config add-mcp sharedbrain \
    --command python3 \
    --args /Users/.../SharedBrain/organs/D-Gateway/mcp_server/server.py

可能性:
  - B-OS已有MCP server实现
  - 可暴露D-Memory查询、EventBus订阅等工具
  - 与KOS/Minerva形成eCOS三件套

风险:
  - 需要先验证MCP server是否正常运行
  - 工具集可能与KOS重叠

建议: Phase 4.5 先验证MCP server可用性，再决定是否接入
```

## 四、不接入的理由

| 理由 | 说明 |
|------|------|
| **避免紧耦合** | eCOS和B-OS应保持独立演化，不互为依赖 |
| **复杂度** | B-OS引入asyncio/BaseMembrane/bos://等新范式 |
| **可靠性** | eCOS当前7条Cron稳定运行，不应引入新故障点 |
| **Phase4聚焦** | Phase 4重点是语义搜索和感知管道，非B-OS集成 |

## 五、决策

**结论: 不接入。保持轻量级事件桥接作为Phase 4.5选项。**

方案:
1. SSB→B-OS EventBus: Phase 4.5 做Python适配器（<200行）
2. KOS→D-Memory: 不桥接
3. B-OS MCP: Phase 4.5 验证可用性后决定

## 六、Phase 4.5 计划

```
□ 验证 B-OS MCP server 可用性
□ 写 SSB→EventBus 适配器 (<200行)
□ 选5个关键事件类型双写
□ 验证端到端延迟 < 1s
```
