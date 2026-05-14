# Agent CLI 注册与路由 — 深度分析

> 2026-05-14 | 问题: 是否需要构建 Agent CLI 注册/路由工具？

---

## 一、现有工具评估

### 1.1 OpenWork Orchestrator (v0.13.5) — 已安装

```
定位: "OpenWork host orchestrator for opencode + OpenWork server + opencode-router"
能力:
  ✅ 多 workspace 管理 (daemon模式)
  ✅ 请求审批流程 (approvals)
  ✅ 实例生命周期管理 (instance dispose)
  ❌ 仅支持 OpenCode — 不通用
  ❌ 不支持 Claude/Kimi/Copilot 注册
```

### 1.2 DeepAgents (v0.0.55) — 已安装

```
能力:
  ✅ Agent 管理 (list/reset/--agent选择)
  ✅ Skills 管理
  ✅ MCP 支持
  ❌ 更偏向开发框架 — 非动态注册/路由
  ❌ LangChain 生态绑定
```

### 1.3 当前 eCOS 方案 — delegate_task

```
能力:
  ✅ 已支持 Copilot ACP (GPT-5.3-Codex)
  ✅ 已支持 Claude CLI (terminal调用)
  ✅ 已支持 Kimi ACP
  ✅ 已支持 DeepSeek native

局限:
  ❌ 每次调用需手动指定 acp_command/acp_args
  ❌ 无自动路由 (需Agent人工决策用哪个CLI)
  ❌ 无健康检查 (CLI不可用时无fallback)
  ❌ 无负载均衡 (所有调用走同一条路径)
```

---

## 二、是否需要自建？

### 2.1 自建 vs 复用

```
                    自建Registry        复用OpenWork        复用DeepAgents
                    ────────────        ────────────        ────────────
多CLI支持            ✅ 原生设计         ❌ 仅OpenCode        ⚠️ LangChain绑定
动态注册             ✅ 核心功能         ❌ 静态              ⚠️ 有限
路由策略             ✅ 自定义           ❌ 内置Router        ❌ 无
健康检查             ✅ 可设计           ❓ 未知              ❌ 无
与 eCOS 集成         ✅ 深度集成         ⚠️ 需适配            ❌ 框架不兼容
维护成本             ⚠️ 需要维护         ✅ 社区维护          ✅ 社区维护
```

### 2.2 判断矩阵

```
自建的必要条件 (满足任2条即建议自建):

  1. 现有工具不支持多CLI注册                  ✅ OpenWork仅OpenCode
  2. 路由策略是差异化需求 (非简单轮询)         ✅ eCOS需要模型特性路由
  3. 需要与 eCOS 的 LADS/SSB/宪法层深度集成   ✅ 核心需求
  4. 维护成本 < 从零开发成本                  ❓ 取决于复杂度

结论: 3/4 条件满足 → 建议自建
```

---

## 三、自建设计 — Hermes Agent Registry (HAR)

### 3.1 核心架构

```
                    ┌─────────────────────┐
                    │   HAR Registry       │
                    │   (Python stdlib)    │
                    └──────────┬──────────┘
                               │
          ┌────────────────────┼────────────────────┐
          │                    │                    │
    ┌─────▼─────┐      ┌──────▼──────┐      ┌─────▼─────┐
    │ Copilot   │      │   Claude    │      │   Kimi    │
    │ ACP:GPT   │      │ CLI:Claude  │      │ ACP:Kimi  │
    └───────────┘      └─────────────┘      └───────────┘
```

### 3.2 注册表设计

```yaml
# ~/Workspace/eCOS/config/agents.yaml
agents:
  copilot-gpt:
    name: "Copilot GPT-5.3"
    type: acp
    command: copilot
    args: [--acp, --stdio]
    model_family: openai
    capabilities: [code, analysis, creative]
    reliability: 0.95
    avg_latency_ms: 28000
    
  claude-anthropic:
    name: "Claude Sonnet"
    type: cli
    command: claude
    args_template: "--print '{prompt}'"
    model_family: anthropic
    capabilities: [code, architecture, review]
    reliability: 0.90
    avg_latency_ms: 15000
    
  kimi-moonshot:
    name: "Kimi"
    type: acp
    command: kimi-cli
    args: [acp]
    model_family: moonshot
    capabilities: [chinese, analysis, creative]
    reliability: 0.85
    avg_latency_ms: 34000
```

### 3.3 路由规则

```python
# 智能路由: 根据任务特征选择Agent
def route(task):
    if task.requires_chinese:
        return ["kimi-moonshot", "claude-anthropic"]
    if task.risk_level == "HIGH":
        return ["claude-anthropic", "copilot-gpt"]  # 优先最强审查
    if task.type == "code_review":
        return ["claude-anthropic"]
    # default: 轮询
    return round_robin()
```

### 3.4 与 eCOS 集成

```
L5 行动层:
  delegate_task → HAR.route() → Agent CLI
  
L6 反馈层:
  健康检查 → Agent 不可用 → 自动降级/切换
  
L3 持久层:
  SSB 记录每次路由决策 + Agent性能指标
```

---

## 四、实施建议

### 方案 A: 轻量版 (1天)

```
文件: scripts/agent_registry.py (~200行)

功能:
  ✅ YAML注册表 (手动维护)
  ✅ 健康检查 (ping每个Agent)
  ✅ 简单路由 (轮询 + 中文优先)
  ✅ SSB事件记录

不做:
  ❌ 自动注册发现
  ❌ 复杂路由策略
  ❌ 负载均衡
  ❌ Web UI
```

### 方案 B: 完整版 (1周)

```
功能:
  ✅ 自动发现已安装CLI (which检测)
  ✅ 性能基准测试 (自动测latency)
  ✅ 智能路由 (模型家族+能力+可靠性加权)
  ✅ 失败自动failover
  ✅ Web dashboard
  ✅ MCP server (其他工具可调用)
```

### 推荐: 方案 A (Phase 3 Sprint 1)

理由:
- 当前只有 3 个 Agent CLI 需要管理
- 手动注册足够 (不频繁变更)
- 核心价值在路由决策的质量，而非路由机制的复杂度
- Phase 3 验证通过后可升级到方案 B

---

## 五、决策

```
自建: 是 — 现有工具不满足多CLI+深度eCOS集成需求

方案: 轻量版 HAR (Agent Registry)
       ~200行 Python · YAML配置 · 健康检查 · 简单路由

Phase 3 Sprint 1 产出:
  □ scripts/agent_registry.py
  □ config/agents.yaml
  □ WF-004 升级 → HAR.route() 替代手动 acp_command
```

---

*分析完成: 自建轻量Registry是最优解*
