# ADR-009: 多模型委员会架构决策

- **状态**: 已接受
- **日期**: 2026-05-14
- **决策者**: 夏同学 + Hermes (CHAIR综合)
- **前置**: ADR-003 (Agent委员会), ADR-008 (委员会决策验证)

## 背景

Phase 2 委员会使用单模型角色切换 (CHAIR/EXEC/AUDIT 由同一 Hermes 扮演)。Phase 3 评估发现 Hermes v0.13 delegate_task 不支持 per-task model override，无法在单一 delegate 中指定不同模型。

## 决策

采用 **ACP + CLI 混合架构** 实现多模型委员会：

```
委员会调用方式:
  EXEC-A   = Copilot ACP (--acp --stdio)    → GPT-5.3-Codex (OpenAI)
  EXEC-B   = Claude CLI  (--print)           → Claude (Anthropic)
  AUDIT    = Hermes native delegate_task      → DeepSeek-v4-pro
  CRITIC   = Gemini ACP  (--acp)             → Gemini (Google)
           = Kimi ACP    (acp subcommand)     → Kimi (Moonshot)
  CHAIR    = Hermes native                    → 协调+综合
```

## 架构模式

```
delegate_task(tasks=[
  {"acp_command": "copilot", "acp_args": ["--acp", "--stdio"], ...},  # GPT
  {"acp_command": "gemini",  "acp_args": ["--acp"], ...},            # Gemini
  {...},  # Claude via terminal (串行)
])
```

不依赖 Hermes 平台能力更新。AUDIT/CHAIR 仍使用 native DeepSeek 作为锚点模型。

## 已验证的模型

| 入口 | 命令 | 模型 | Provider | 状态 |
|------|------|------|----------|------|
| Copilot ACP | `copilot --acp --stdio` | GPT-5.3-Codex | OpenAI | ✅ 全自动 |
| Claude CLI | `claude --print` | Claude | Anthropic | ✅ 需terminal权限 |
| Gemini ACP | `gemini --acp` | Gemini | Google | ✅ 全自动 |
| Kimi ACP | `kimi-cli acp` | Kimi | Moonshot | ✅ 全自动 |
| Hermes native | delegate_task | DeepSeek-v4-pro | DeepSeek | ✅ 原生 |
| Codex ACP | (不支持 `--acp`) | — | — | ❌ |

## 委员会流程

```
CHAIR定义议题 → 并行: EXEC-A(ACP)+EXEC-B(CLI)/EXEC-C(ACP) → 汇总 →
CHAIR定义审查 → AUDIT串行 → CRITIC(高风险) → CHAIR综合决策 → ADR
```

耗时: ~2分钟/轮 (ACP 80-90s + CLI 15s + 串行AUDIT ~90s)

## 局限

1. ACP/CLI 子 Agent 无法使用 eCOS 的 KOS MCP 工具 (仅有 Hermes native 可调)
2. Claude CLI 依赖 terminal 权限 (需用户放行)
3. 无 per-task model override → 无法在一个 delegate 中混合模型

## 后果

- 正面: 5模型5provider, 真正独立审查
- 正面: 不依赖 Hermes 版本更新
- 风险: ACP/CLI 不可用时的降级 (→纯DeepSeek三角模式)
- 风险: Gemini/Kimi ACP 长期稳定性未验证

## 被否决方案

| 方案 | 否决理由 |
|------|----------|
| 等待Hermes per-task model | 未知发布时间 |
| 纯串行+手动切换model | 耗时太长 (>10分钟/轮) |
| 通过MCP集成 | 需每个模型写MCP Server |
