# ADR-010: Kanban 调度引擎架构决策

- **状态**: 已接受
- **日期**: 2026-05-15
- **决策者**: 夏同学 + Hermes (Kanban Phase A 验证完成)

## 背景

eCOS Phase 3 需要将委员会决策（WF-004）从手动触发升级为可调度的自动化工作流。其他 Agent 在跨会话中发现了 Hermes Kanban 系统，并验证了"Kanban + SSB 桥接"的技术可行性。

## 决策

采用**三层调度架构**：

```
L3: Kanban 增强（当前可用）
    → 5-step 委员会链（S01→S02→S03→S04→S05）
    → 4 profiles: chair/exec/audit/scribe
    → 链式自动流转（前步done → 后步ready）
    → Hermes kanban daemon 驱动

L2: Schedule YAML（平台无关描述）
    → schedule/WF-004.yaml 定义调度语义
    → ecos_scheduler.py 翻译为具体执行
    → 支持 kanban/manual/status 三种驱动

L1: 纯文件基座（降级模式）
    → 当 Kanban 不可用时回退
    → STATE.yaml + HANDOFF + 手动执行
```

### 桥接架构

```
Kanban DB (Hermes) ←→ WF-008 Bridge (SSB) ←→ eCOS SSB
   任务状态变化           事件同步              可审计
   (created/done)        (STATE_CHANGE)        (4332 events)
```

### 验证结果

- 5 步委员会链完成一次完整循环（全部 done）
- WF-008 桥接同步 21 条事件到 SSB
- 任务链自动流转正常

## 后果

- 正面: 委员会决策可调度、可追踪、可审计
- 正面: 三层架构保证 Kanban 不可用时的降级路径
- 风险: Kanban 链当前闲置，需要实际业务驱动下一轮
- 风险: WF-008 桥接未部署 cron，事件同步依赖手动

## 待办

- WF-008 部署为 cron（每 5 分钟同步）
- SSB 签名启用（新旧事件迁移）
- 下一轮实际委员会决策 → 驱动 Kanban 链
