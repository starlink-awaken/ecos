# L6 反馈层 — 实时检查规则

> Sprint 4 | 版本: v1.0
> 所属: L6 反馈层 — 宪法执行器子系统

---

## 检查触发点

```
触发时机                    检查内容                      严重度
────                        ────                          ────
不可逆操作执行前              IRREVERSIBLE-OPS 清单          🚨
GENOME.md 写入前              L0/L1 变更 + RFC检查           🚨
delegate_task 创建前          角色隔离 + 工具集限制          ⚠️
Cron 修改前                   新旧prompt对比 + 人类确认     ⚠️
文件删除前 (FAILURES/等)      L0-04 完整性                  🚨
SSB 事件写入失败              重试 + 降级到文件              ❌
```

---

## 规则定义

### R1: 不可逆操作前强制检查

```
触发: Agent 准备执行 IRREVERSIBLE-OPS 清单中的操作
动作:
  1. 读取 IRREVERSIBLE-OPS.md
  2. 判定操作级别 (一级/二级/三级)
  3. 如三级: 阻止执行, 要求人类确认
  4. 如二级: 触发三角模式 (CHAIR+AUDIT)
  5. 写入 SSB: type=CHECK, subtype=IRREVERSIBLE_OPS
  6. 结果写入 STATE.yaml
```

### R2: GENOME 写入守护

```
触发: 任何对 GENOME.md 的写操作
动作:
  1. 阻止直接写入
  2. 如果存在对应 RFC: 允许 (正常流程)
  3. 如果无 RFC: 拒绝, 写入 FAILURES
  4. 写入 SSB: type=CHECK, subtype=GENOME_GUARD
```

### R3: SSB 健康监控

```
触发: 每次 WF-003 运行时
动作:
  1. 检查 SSB 最近24h事件数
  2. < 5 事件 → ⚠️ 警告 (系统可能停滞)
  3. = 0 事件 → 检查 SSB 客户端是否正常
  4. 写入 SSB: type=SIGNAL, subtype=SSB_HEALTH
```

---

## 与现有系统的集成

```
WF-003 日检:
  执行 R3 (SSB健康) ← 已集成

WF-006 时检:
  执行 R3 轻量版 (SSB心跳)

Agent 行为规范:
  R1 (不可逆操作) ← Sprint 4 新增
  R2 (GENOME守护) ← Phase 1 已有 (git diff)
```

---

*创建: 2026-05-14 Sprint 4*
