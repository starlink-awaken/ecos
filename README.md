# eCOS — 外化认知操作系统 (External Cognitive Operating System)

> "不是工具集合，而是认知的基础设施。"

---

## 什么是 eCOS

eCOS 是夏铭星认知增强系统的**顶层架构容器**。它不运行业务逻辑，它运行的是：

- 系统如何感知世界
- 系统如何记忆和遗忘
- 系统如何做决策
- 多个 Agent 如何协作而不冲突
- 系统如何从失败中学习
- 整个体系如何在时间轴上保持连续性

---

## 快速路由（Agent 冷启动必读）

任何 Agent 进入本系统，**必须按顺序读取以下文件**：

```
1. /Users/xiamingxing/Workspace/eCOS/GENOME.md          ← 系统宪法，不变量
2. /Users/xiamingxing/Workspace/eCOS/STATE.yaml          ← 当前运行状态
3. /Users/xiamingxing/Workspace/eCOS/LADS/HANDOFF/LATEST.md  ← 上一个 Agent 的交接
4. /Users/xiamingxing/Workspace/eCOS/agents/committee/CHARTER.md  ← 委员会章程
```

热启动（已有上下文）只需读 STATE.yaml + HANDOFF/LATEST.md。

---

## 目录结构

```
eCOS/
├── README.md               ← 本文件，入口索引
├── GENOME.md               ← 系统基因/宪法（L0 不变量）
├── STATE.yaml              ← 当前系统快照
│
├── docs/
│   ├── philosophy/         ← 第一性原理推导，理论基础
│   ├── architecture/       ← 架构设计文档（六层模型、SSB等）
│   └── decisions/
│       ├── ADR/            ← 架构决策记录（已定稿）
│       └── RFC/            ← 变更提案（讨论中）
│
├── LADS/                   ← 活体架构文档系统
│   ├── HANDOFF/            ← Agent 交接日志（LATEST.md 永远是最新）
│   └── FAILURES/           ← 失败案例库
│
├── agents/
│   ├── committee/          ← Agent 委员会定义和章程
│   └── workflows/          ← 多 Agent 协作 Workflow 定义
│
└── scripts/                ← 维护脚本
```

---

## 核心系统关系

```
eCOS (本项目，架构层)
 ├── SharedBrain B-OS  ~/SharedBrain/      ← 仿生OS，信息存储与路由
 ├── KOS              ~/Workspace/Tools/kos/ ← 知识索引，6域23万文档
 └── Minerva          ~/Workspace/minerva/   ← 深度研究，L0-L4管道
```

eCOS 不替代上述三个系统，它是它们的**宪法和协调层**。

---

*最后更新: 2026-05-13*
*版本: v0.1.0-draft*
