# SharedBrain B-OS 接入评估

> Sprint 5 | 2026-05-14

---

## 系统概览

```
SharedBrain B-OS v10.0.0
  → "Hive Consciousness" / Digital Lifeform
  → 7-Chakra 分层 + Z-Microkernel
  → 14 Organs (D_Memory, D_Execution, D_Gateway, ...)
  → MCP Server: organs/D-Gateway/mcp_server/
  → bos:// URI routing
  → Event Bus (DOC_BEFORE_UPDATE, DOC_AFTER_UPDATE)
```

---

## 与 eCOS 的集成点

| B-OS 组件 | eCOS 映射 | 优先级 | 说明 |
|-----------|----------|--------|------|
| MCP Server | Hermes MCP 集成 | P1 | 评估接入 Hermes |
| Event Bus | SSB 后端候选 | P2 | Phase 3 消息队列替代 |
| D_Memory | KOS 补充 | P2 | 因果事实图谱 vs 全文索引 |
| D_KnowledgeIntegration | 感知层深度融合 | P3 | 语义搜索+FactGraph |
| D_Governance | 委员会对齐 | P3 | 角色治理与策略审批 |
| D_Harvest | 感知层 Capture 增强 | P3 | 知识采集管道 |

---

## 接入路径

### P1: MCP Server 接入 Hermes

```
现状: B-OS 有 MCP Server (organs/D-Gateway/mcp_server/)
      Python+bun, SSE transport (port 7421)

方案: config.yaml 新增 sharedbrain MCP server
      transport: HTTP (url: http://localhost:7421/sse)

风险: SSE 传输需验证 Hermes 支持
      需先启动 B-OS daemon
```

### P2: Event Bus → SSB 后端

```
现状: B-OS Event Bus (DOC_BEFORE_UPDATE, DOC_AFTER_UPDATE)
      事件驱动架构

方案: Phase 3 时评估用 B-OS Event Bus 替代 SQLite SSB
      或双写 (SSB → B-OS Event Bus)

当前: SQLite SSB 已足够 Phase 2 使用, 不急于迁移
```

### P3: Knowledge Integration

```
D_Memory: CRDT因果事实图谱
D_KnowledgeIntegration: 语义搜索+FactGraph
D_Harvest: 外部知识采集

方案: 作为 KOS 的补充层, 但需要更深评估
      KOS 已处理全文索引, B-OS 可处理关系推理
```

---

## 建议

```
Phase 2:   评估 MCP Server 接入 (P1)
           不阻塞当前 Sprint

Phase 3:   评估 Event Bus → SSB (P2)
           评估 Knowledge 深度融合 (P3)
```

**当前不接入。** B-OS 是成熟系统但功能与 KOS 有重叠。Phase 2 聚焦委员会升级和反馈层，SharedBrain 作为 Phase 3 的战略储备。
