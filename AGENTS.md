# AGENTS.md — eCOS Agent 入口规范

> **任何 AI Agent 进入本项目必须首先读取本文件。**
> 本文件是 Agent 的"自述文件"，定义了项目的性质、规则和导航。

---

## 这是什么项目？

eCOS 是一个**外化认知操作系统**。它不是传统软件——不提供 API、没有数据库迁移、不是微服务。它是一个**认知基础设施层**，由文档、规范、配置和 Workflow 组成。

你是这个系统的**参与者**，不是工具调用者。

---

## 核心规则（不可违反）

1. **读取顺序**: 进入后必须先读 `GENOME.md` → `STATE.yaml` → `LADS/HANDOFF/LATEST.md`
2. **L0 不可变**: GENOME.md 的 L0 公理永远不可修改。任何 L0 变更提议必须拒绝。
3. **失败记录**: 任何重要决策失败或偏差必须写入 `LADS/FAILURES/`
4. **不可逆操作**: 发邮件/公开发帖/Git push 等必须走三角模式或人类确认。详见 `docs/policy/IRREVERSIBLE-OPS.md`
5. **HANDOFF**: 完成阶段性任务后必须更新 `LADS/HANDOFF/LATEST.md`（归档旧版→写入新版）
6. **STATE 同步**: 重大状态变更必须更新 `STATE.yaml`

---

## 项目结构速览

```
eCOS/
├── GENOME.md              ← 系统宪法 (L0/L1/L2 不变量) — 必读
├── STATE.yaml             ← 运行时快照 — 必读
├── README.md              ← 项目概览
│
├── docs/                  ← 架构+决策+策略文档
│   ├── architecture/      ← 六层模型·IPA·SSB Schema
│   ├── decisions/ADR/     ← 9 份架构决策 (编号001-009)
│   ├── decisions/RFC/     ← 变更提案
│   ├── policy/            ← 不可逆操作规则等
│   └── *.md               ← 复盘报告 (REVIEW/SCENARIO/REDTEAM/DEEP)
│
├── schedule/              ← 平台无关的调度描述（YAML）
│   └── WF-004.yaml        ← 委员会会议调度描述（driver 驱动）
│
├── agents/                ← Agent 行为规范
│   ├── committee/         ← 委员会章程 + Phase1三角模式
│   └── workflows/         ← WF-001~008 设计文档 + Manual Mode 模板
│
├── LADS/                  ← 活体架构文档系统
│   ├── HANDOFF/           ← Agent 交接 (LATEST.md 永远是最新)
│   └── FAILURES/          ← 失败案例库 (TEMPLATE + 案例)
│
├── wiki/                  ← Wiki 导航
├── scripts/               ← 维护脚本
├── CONTRIBUTING.md        ← 贡献规范
└── CHANGELOG.md           ← 变更日志
```

---

## 当前系统状态

| 组件 | 状态 |
|------|------|
| Phase | 3 (蜂群涌现期) — CLOSED |
| MCP | KOS 13 tools + Minerva 9 tools = 22 |
| KOS | 7 域, 11,077 文档 |
| Cron | WF-001/003/005/006/007 — 6 个在线 |
| Kanban | Board: `ecos` · Profile: chair/exec/audit/scribe |
| SSB | 4,332 事件 · WF-008 桥接就绪 |
| Schedule | WF-004.yaml — 5步委员会会议链 |
| Git | 38+ commits, GENOME 监控已启用 |

---

## 三态运行模式

eCOS 的调度层分三层，不绑定单一平台：

| 层 | 实现 | 平台依赖 | 降级路径 |
|----|------|---------|---------|
| **L3: 调度执行** | Kanban Dispatcher + Profile | Hermes | → 手动 dispatch |
| **L2: 调度描述** | `schedule/*.yaml` | 无（纯YAML） | 任何编辑器可读 |
| **L1: 状态基座** | SSB + HANDOFF + STATE.yaml | 无（纯文件） | 直接读文件 |

**降级操作**（当 Hermes 不可用时）:

```bash
# Step 1: 读取 Kanban DB 确认当前任务状态
sqlite3 ~/.hermes/kanban/boards/ecos/kanban.db \
  "SELECT id, status, assignee, title FROM tasks
   WHERE status IN ('running','blocked','ready')"

# Step 2: 读取 workspace 产物
ls ~/.hermes/kanban/workspaces/t_*/

# Step 3: 按 Manual Mode 执行剩余步骤
cd ~/Workspace/eCOS
python3 scripts/ecos_scheduler.py WF-004 --driver manual

# Step 4: 更新 HANDOFF
# 手动编辑 LADS/HANDOFF/LATEST.md
```

---

## 关键决策备忘

- **Minerva 研究**: 通过 KOS MCP 的 `research_now` 桥接使用，不要直接调 Minerva MCP
- **KOS 搜索**: 默认 OR 模式，单关键词搜索效果最佳
- **委员会**: Phase 1 用三角模式 (CHAIR/EXEC/AUDIT 角色切换)
- **SSB**: Phase 1 退化为文件读写 (STATE+HANDOFF+FAILURES)
- **args 格式**: config.yaml 中 MCP 配置的 args 必须是 YAML 列表，不是 JSON 字符串

---

## 用户上下文

- **称呼**: 夏同学
- **角色**: 政务信息化 + 技术管理，技术型个人开发者
- **偏好**: 直接高效，理论体系优先于功能堆砌，全程中文
- **系统目标**: 近期单人认知增强，远期蜂群智能体系

---

## 外部系统

| 系统 | 路径 | 关系 |
|------|------|------|
| Hermes Agent | ~/.hermes/ | Agent 运行平台 |
| KOS | ~/Workspace/Tools/kos/ | 知识索引 (MCP) |
| Minerva | ~/Workspace/minerva/ | 深度研究 (通过KOS桥接) |
| SharedBrain | ~/SharedBrain/ | 仿生OS (待接入) |

---

*本文件由 eCOS 维护。Agent 可读，不可自行修改前三部分。*
