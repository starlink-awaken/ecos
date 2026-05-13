# eCOS — External Cognitive Operating System

> 不是工具集合，而是认知的基础设施。

[![Phase](https://img.shields.io/badge/phase-1%20完成-brightgreen)](#)
[![Version](https://img.shields.io/badge/version-0.1.0--draft-blue)](#)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![Docs](https://img.shields.io/badge/docs-wiki-orange)](./docs/)

eCOS 是一个**外化认知操作系统**——为 AI Agent 提供持久记忆、知识检索、深度研究、多角色协作和宪法约束的基础设施层。它不运行业务逻辑，它运行的是认知的底层机制。

---

## 为什么需要 eCOS？

| 人类认知限制 | eCOS 的解决方案 |
|-------------|----------------|
| 工作记忆 7±2 组块 | 持久层：KOS 索引 7,200+ 文档，可并行检索 |
| 遗忘曲线（24h 遗忘 70%） | LADS 机制：Agent 间无缝交接，永不遗忘 |
| 单通道注意力 | MCP 工具链：22 个工具并行调用 |
| 确认偏误 | Agent 委员会：多角色审查 + CRITIC 专职挑错 |
| 决策不透明 | ADR + RFC：所有重大决策归档可追溯 |

---

## 架构概览

```
┌─────────────────────────────────────────┐
│  L6 反馈层   宪法执行器 · 稳态监控        │
├─────────────────────────────────────────┤
│  L5 行动层   22 MCP工具 · 3 Cron · API   │
├─────────────────────────────────────────┤
│  L4 智能层   Agent委员会 · SSB路由       │
├─────────────────────────────────────────┤
│  L3 持久层   KOS(7域,7203文档) · 失败库  │
├─────────────────────────────────────────┤
│  L2 感知层   五阶降熵管道 (Phase 2)       │
├─────────────────────────────────────────┤
│  L1 宪法层   GENOME.md L0/L1/L2 不变量   │
└─────────────────────────────────────────┘
```

**核心集成：** Hermes (Agent) ←→ KOS MCP (13 tools) ←→ Minerva CLI (研究引擎)

---

## 快速开始

### 前置条件

- [Hermes Agent](https://github.com/NousResearch/hermes-agent) v0.13+
- Python 3.11+
- KOS 知识索引系统
- Minerva 深度研究引擎 (可选)

### 安装

```bash
git clone https://github.com/your-org/ecos.git ~/Workspace/eCOS
cd ~/Workspace/eCOS
```

### Agent 冷启动

任何 Agent 进入本系统，按顺序读取：

```
1. GENOME.md                    ← 系统宪法
2. STATE.yaml                   ← 当前快照
3. agents/committee/PHASE1-TRIANGLE.md  ← 决策规范
4. docs/policy/IRREVERSIBLE-OPS.md      ← 安全边界
```

### MCP 配置

在 `~/.hermes/config.yaml` 中添加：

```yaml
mcp_servers:
  kos:
    command: python3
    args:
      - /Users/xiamingxing/Workspace/Tools/kos/kos-mcp-server.py
    timeout: 180
  minerva:
    command: /Users/xiamingxing/Workspace/minerva/.venv/bin/python3
    args:
      - -m
      - minerva.mcp_server.server
```

---

## 项目结构

```
eCOS/
├── README.md                   ← 本文件
├── GENOME.md                   ← 系统宪法 (L0 不变量)
├── STATE.yaml                  ← 运行时快照
├── LICENSE                     ← MIT
├── CHANGELOG.md                ← 变更日志
├── CONTRIBUTING.md             ← 贡献指南
│
├── docs/
│   ├── architecture/           ← 架构设计文档
│   ├── decisions/ADR/          ← 架构决策记录 (7篇)
│   ├── decisions/RFC/          ← 变更提案
│   ├── philosophy/             ← 第一性原理推导
│   ├── policy/                 ← 操作策略
│   └── reviews/                ← 复盘报告
│
├── agents/
│   ├── committee/              ← Agent 委员会定义
│   └── workflows/              ← Workflow 设计文档
│
├── LADS/
│   ├── HANDOFF/                ← Agent 交接日志
│   └── FAILURES/               ← 失败案例库 (6篇)
│
└── scripts/                    ← 维护脚本
```

---

## 核心概念

| 概念 | 文档 | 说明 |
|------|------|------|
| **六层架构** | [six-layer-model.md](docs/architecture/six-layer-model.md) | 宪法→感知→持久→智能→行动→反馈 |
| **IPA 运行时** | [IPA-6LAYER-RELATIONSHIP.md](docs/architecture/IPA-6LAYER-RELATIONSHIP.md) | Intelligence-Persistence-Action 认知循环 |
| **LADS 连续性** | [ADR-004](docs/decisions/ADR/ADR-004-lads-mechanism.md) | 活体架构文档系统 |
| **Agent 委员会** | [CHARTER.md](agents/committee/CHARTER.md) | 多角色协作决策机制 |
| **SSB 语义总线** | [SSB-SCHEMA-V1.md](docs/architecture/SSB-SCHEMA-V1.md) | Agent 间通信协议 |
| **不可逆操作** | [IRREVERSIBLE-OPS.md](docs/policy/IRREVERSIBLE-OPS.md) | 三级分级确认规则 |

---

## 当前状态

| 指标 | 值 |
|------|-----|
| Phase | 1 (单体建立期) |
| MCP 工具 | 22 (KOS 13 + Minerva 9) |
| KOS 域 | 7 (7,203 文档) |
| Cron 任务 | 3 (索引·巡检·HANDOFF) |
| ADR 归档 | 7 |
| 失败案例 | 6 |
| 架构实现度 | 61% |
| 安全评分 | 72% |

详见 [STATE.yaml](STATE.yaml)

---

## 贡献

欢迎贡献！详见 [CONTRIBUTING.md](CONTRIBUTING.md)。

所有变更需遵循：
- L0 不变量：任何修改不得违反 GENOME.md 的公理
- RFC 流程：重大变更须提交 RFC 并获得人类确认
- 失败记录：所有失败必须写入 FAILURES/

---

## 许可证

MIT License — 详见 [LICENSE](LICENSE)

---

*"系统不运行业务逻辑，系统运行的是认知的底层机制。"*
