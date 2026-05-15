# eCOS 审计清零修复计划

> 2026-05-15 | 前置: 全面审计报告 (AUDIT-REPORT-2026-05-15.md)
> 目标: 所有 P0/P1/P2 清零 → 再审计 → 验证通过

## 当前状态 vs 目标

```
指标              当前           目标
─────────────────────────────────────
测试覆盖率        21% (0单元)    ≥50% (核心脚本全覆盖)
代码重复          ~200行         0 (抽取共享模块)
签名验证          失效           所有SSB事件可验证
文档一致性        AGENTS≠STATE   所有入口文档一致
委员会            闲置           完成1次实际业务循环
注释率            5.7%           ≥15%
架构漂移          5处            0 (文档与实现对齐)
```

## 修复分4阶段

```
Phase A: P0 + 关键P1 (ssb_auth, 核心测试, AGENTS同步)
Phase B: 代码质量 (抽取共享模块, 去重, 注释)
Phase C: 架构对齐 (文档同步, 管道薄点, 路径修复)
Phase D: 再审计 + 清零验证
```

## 文件清单

### Phase A (创建/修改)
- 创建: `tests/test_ssb_client.py`
- 创建: `tests/test_filter_scorer.py`
- 创建: `tests/test_realtime_guard.py`
- 修改: `scripts/ssb_auth.py` → 修复verify()
- 修改: `AGENTS.md` → 同步STATE.yaml
- 修改: `GENOME.md` → 更新Phase描述
- 修改: `.gitignore` → 添加backup排除

### Phase B (创建/修改)
- 创建: `scripts/ecos_common.py` → 共享模块
- 修改: `scripts/ssb_client.py` → 导入共享模块
- 修改: `scripts/filter_scorer.py` → 导入共享模块
- 修改: `scripts/capture_watcher.py` → 导入共享模块

### Phase C (修改)
- 修改: `scripts/contextualize_pipeline.py` → 移除硬编码路径
- 修改: `scripts/integrate_pipeline.py` → 移除硬编码路径
- 修改: `docs/SUBSYSTEM-IDENTITY.md` → 更新Phase4身份
- 修改: `docs/ALL-MODULE-ISSUES.md` → 更新至Phase4
- 创建: `docs/DEPRECATED.md` → 过期文档索引

### Phase D (验证)
- 运行: `critic_auto_trigger.py --metrics`
- 运行: `ssb_schema_migrate.py` (幂等验证)
- 运行: 新测试套件
- 运行: 红蓝对抗 v4

## 依赖图

```
Phase A ──→ Phase B ──→ Phase C ──→ Phase D
  │            │            │
  ├─ ssb_auth  ├─ ecos_common ├─ 路径修复
  ├─ 测试      ├─ 去重        ├─ 文档同步
  └─ AGENTS    └─ 注释        └─ 过期标记
```

## 风险矩阵

| 风险 | 概率 | 影响 | 缓解 |
|------|------|------|------|
| ssb_auth修复破坏现有事件 | LOW | HIGH | 备份+幂等 |
| 共享模块引入循环导入 | MED | MED | 单向依赖设计 |
| AGENTS.md更新遗漏字段 | MED | LOW | 对比STATE.yaml逐项检查 |
| 测试编写耗时过长 | HIGH | LOW | 仅核心3个脚本 |

## 回滚条件

1. 任何测试失败无法修复 → 回滚该Phase
2. ssb_auth修复导致签名不兼容 → 回滚并标记为Phase 4.5
3. 共享模块导致3+脚本import错误 → 回滚，保持独立

## 验证清单

| Phase | 检查项 | 预期 |
|-------|--------|------|
| A | test_ssb_client 运行 | 5+ tests pass |
| A | test_filter_scorer 运行 | 3+ tests pass |
| A | test_realtime_guard 运行 | 8+ tests pass |
| A | ssb_auth verify() 实际比对 | 签名验证有效 |
| A | AGENTS.md matches STATE.yaml | 所有数字一致 |
| B | 共享模块导入无错误 | import ecos_common OK |
| B | 重复代码消除 | grep 确认无重复建表SQL |
| C | 硬编码路径替换 | 无 /Users/xiamingxing 绝对路径 |
| C | 过期文档索引 | DEPRECATED.md 列出10+篇 |
| D | 全量测试通过 | 16+ tests pass |
| D | 涌现度量正常 | diversity>0.3, resilience=1.0 |
| D | 红蓝v4 安全评分 | ≥82% |

---

## 执行方式

**采用: Subagent-Driven Development (推荐)**

- 每Phase一个子Agent独立执行
- Phase间做Review Gate
- 全部完成后统一再审计

---

*计划完成: 2026-05-15 11:00 CST*
