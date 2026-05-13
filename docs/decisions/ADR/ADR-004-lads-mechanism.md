# ADR-004: LADS 五组件系统连续性机制（含失败案例库）

- **状态**: 已接受
- **日期**: 2026-05-13
- **决策者**: 夏同学 + Hermes

## 背景

Agent 存在间断性（对话结束即失忆），不同 Agent 未来可能并行运行，需要一套机制保障系统连续性，让任何新 Agent 都能快速接续之前的工作。

## 决策

建立 **LADS（活体架构文档系统）**，五个组件：

| 组件 | 文件 | 职责 |
|------|------|------|
| GENOME | GENOME.md | 系统宪法，L0不变量，永不过时 |
| STATE | STATE.yaml | 当前快照，每次 Workflow 后更新 |
| ADR | docs/decisions/ADR/ | 已定稿的架构决策记录 |
| RFC | docs/decisions/RFC/ | 讨论中的变更提案 |
| HANDOFF | LADS/HANDOFF/LATEST.md | Agent 间交接，冷启动必读 |
| **FAILURES** | **LADS/FAILURES/** | **失败案例库（用户要求新增）** |

**冷启动标准读取集**：README → GENOME → STATE → HANDOFF/LATEST（约11分钟）
**热启动读取集**：STATE → HANDOFF/LATEST（约3分钟）

失败案例库触发规则：
1. 决策后结果偏差 > 30%
2. 触发 L0 不变量边界
3. AUDIT 反对但被覆盖且最终失败
4. 数据丢失或不可逆操作错误
5. Workflow 异常终止

## 后果

- 正面：任何 Agent 可从文档重建上下文，失败经验不丢失
- 风险：文档维护负担，SCRIBE 角色必须严格执行
- 缓解：STATE.yaml 和 HANDOFF 通过 Workflow 自动更新
