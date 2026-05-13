---
id: WF-003
name: 系统健康检查
version: "0.1.0"
trigger: "cron: '0 9 * * 1' (每周一 09:00 CST)"
priority: P1
risk_level: LOW
committee_required: false
---

# WF-003 系统健康检查

## 目的

定期验证 eCOS 基础设施完整性，确保关键文件未损坏、Hermes 服务正常运行。

## 角色

无委员会。单 Agent（Hermes cron 子会话）直行。

## 步骤

```
S01: hermes doctor → 检查输出中的错误/警告
S02: 验证 GENOME.md 存在 + 大小 > 1KB
S03: 验证 STATE.yaml 可解析
S04: 验证 HANDOFF/LATEST.md 存在 + 大小 > 500B
S05: 验证 docs/decisions/ADR/ 下所有文件存在
```

## 输出规则

- 正常：**静默**（不消耗用户注意力）
- 异常：简要报告 + 推送通知
- 严重：紧急通知

## 部署

| 属性 | 值 |
|------|-----|
| cron job ID | 2d970b4c12af |
| 下次运行 | 2026-05-18 09:00 CST |
| 重复 | 每周一 |
| 交付 | 当前会话自动推送 |

## 回滚

cronjob remove 2d970b4c12af

---

*创建: 2026-05-13 三角模式测试产出*
