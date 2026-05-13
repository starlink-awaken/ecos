# 贡献指南

> eCOS 欢迎人类和 Agent 贡献者。本文档定义贡献规范和流程。

---

## 谁可以贡献

| 角色 | 权限 | 流程 |
|------|------|------|
| **人类 (夏同学)** | L0/L1 变更审批 | 直接决策 |
| **Master Agent (Hermes)** | L2 政策配置, 召集委员会 | 记录 ADR |
| **子 Agent (cron/delegate)** | 执行 Workflow, 报告问题 | 写入 FAILURES |
| **外部贡献者** | 提交 RFC | RFC 流程 |

---

## 贡献类型

### 文档修改

```
小修改 (错别字/格式):  直接 patch → 提交
中等修改 (新增章节):  提交 RFC → 讨论 → 合并
重大修改 (L1 变更):   RFC + 人类确认 → 合并
L0 变更:              禁止
```

### 代码修改

```
kos-mcp-server.py:     提交 patch → 评估上游兼容性 → 合并
workspace-manifest.json: 备份 → 修改 → 验证索引 → 合并
config.yaml:           直接修改 → 验证 MCP 连接 → 合并
```

### Workflow 新增

```
1. 在 agents/workflows/ 创建设计文档 (按 WF-NNN 编号)
2. 通过三角委员会审查
3. 部署 cron job
4. 更新 STATE.yaml
```

---

## 提交规范

### Commit 消息

```
<类型>: <简短描述>

类型:
  feat     新功能
  fix      修复
  docs     文档
  refactor 重构
  review   复盘报告
  security 安全加固

示例:
  feat: KOS FTS5 OR模式
  fix: HANDOFF 滞后3.5h
  security: GENOME git diff 监控
```

### 分支规范

```
main       — 稳定分支 (Phase 1 当前)
phase-2    — Phase 2 开发分支 (未来)
```

---

## 审查流程

### 文档审查

```
1. 逻辑推演 (必须)
   → 新架构文档必须经过一轮推演
   → 检查: 是否违反 L0/L1？是否可在当前 Phase 实施？

2. 三角委员会 (高风险变更)
   → CHAIR → EXEC → AUDIT 三轮审查

3. 人类确认 (L1 变更)
   → 不可跳过
```

### 代码审查

```
1. 语法检查 (python3 -c "import ast; ast.parse(...)")
2. 功能测试 (实际调用验证)
3. 上游兼容性评估 (如果是修改上游代码)
```

---

## 失败记录规范

任何 Agent 发现以下情况**必须**写入 FAILURES/：

```
1. 决策后结果偏差 > 30% (定量) 或 失败 (定性)
2. 触发 L0 不变量边界
3. AUDIT 反对但被覆盖且最终失败
4. 数据丢失或不可逆操作错误
5. Workflow 异常终止

模板: LADS/FAILURES/TEMPLATE.md
```

---

## 沟通渠道

| 事项 | 渠道 |
|------|------|
| 提案讨论 | RFC (docs/decisions/RFC/) |
| 决策记录 | ADR (docs/decisions/ADR/) |
| Agent 交接 | HANDOFF (LADS/HANDOFF/LATEST.md) |
| 紧急事项 | Hermes 推送 + 人类直接联系 |

---

*最后更新: 2026-05-13*
