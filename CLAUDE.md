# CLAUDE.md — Claude/Codex Agent 入口

> 本文件与 AGENTS.md 内容一致。部分工具 (Claude Code, Codex, Cursor) 优先读取 CLAUDE.md。

---

## 项目: eCOS — 外化认知操作系统

**性质:** 认知基础设施层，由文档+规范+配置+Workflow组成，非传统软件。

## 进入后必须执行的读取顺序

```
1. GENOME.md                     ← 系统宪法
2. STATE.yaml                    ← 当前快照
3. LADS/HANDOFF/LATEST.md        ← 上一个 Agent 的交接
4. docs/policy/IRREVERSIBLE-OPS.md  ← 安全边界
```

## 核心规则

- L0 公理永不可变
- 不可逆操作 (发邮件/Git push/公开消息) 必须人类确认
- 失败必须写入 `LADS/FAILURES/`
- 阶段完成后必须更新 `STATE.yaml` + `LADS/HANDOFF/LATEST.md`
- 强制读取顺序是冷启动的最低要求

## 当前状态

- **Phase**: 1 (已完成) | **MCP**: 22 tools | **KOS**: 7域7203文档
- **Cron**: WF-001(索引) · WF-003(巡检) · WF-005(HANDOFF)
- **委员会**: Phase1 用三角模式 (PHASE1-TRIANGLE.md)
- **安全评分**: 72%

## 用户

夏铭星 · 房卫健委+国转中心 · 中文 · 直接高效 · 理论优先

## 详细文档

见 [AGENTS.md](AGENTS.md) — 完整导航和规则说明。
