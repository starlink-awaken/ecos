# eCOS Phase 2 — 红蓝队对抗分析 v2

> 日期: 2026-05-14 | Phase 1→Phase 2 攻击面变化

---

## 攻击面变化

```
Phase 1 (3 攻击面)              Phase 2 (7 攻击面)
─────────────────               ─────────────────
MCP 工具链                       MCP 工具链 (Minerva 9/9)
HANDOFF 信任                     HANDOFF 信任
Cron 劫持                        Cron 劫持 (3→5 jobs)
                                 SSB SQLite 投毒 ← 新增
                                 感知管道投毒 ← 新增
                                 多Agent 串通 ← 新增
                                 jieba 依赖风险 ← 新增
```

---

## 一轮：红队攻击

### A1: SSB SQLite 事件注入

**攻击向量:** 直接写入 `LADS/ssb/ecos.db` 伪造事件

```
攻击步骤:
1. 获取 ecos.db 写入权限
2. INSERT 伪造的 FAILURE/DECISION 事件
3. 污染 SSB 查询结果，误导下游 Agent

当前防护: 无 (SQLite 无认证)
风险: 高 — 297 条事件可能被污染
```

### A2: 感知管道投毒

**攻击向量:** 向监控目录注入恶意文件

```
攻击步骤:
1. 将恶意 .md 文件写入 ~/knowledge/reports/
2. capture_watcher 扫描到 → SSB PERCEPTION 事件
3. filter_scorer 评分 → 如通过(≥60) → KOS 索引
4. 恶意内容进入知识库

当前防护: filter_scorer 五维评分 (结构/长度/格式)
风险: 中 — 攻击者可构造"看起来正常"的文档绕过评分
```

### A3: 多 Agent 串通

**攻击向量:** delegate_task 的 2×EXEC 被同一恶意 prompt 控制

```
攻击步骤:
1. CHAIR (Hermes) 被恶意 prompt 控制
2. delegate_task 创建的 2×EXEC 继承恶意指令
3. AUDIT 也被污染 (同模型)
4. 形成"串通" — 所有 Agent 同意恶意提案

当前防护: 0 (所有 Agent 共享同一 LLM)
风险: 高 — Phase 2 "真多Agent" 在单模型下是伪独立
```

### A4: Minerva 研究滥用

**攻击向量:** 通过 research_schedule/research_watch 建立持久化恶意研究

```
攻击步骤:
1. 调用 research_watch(topic="steal credentials", sources="all")
2. 调用 research_schedule(query="...", cron="* * * * *")
3. 高频研究消耗资源 / 暴露敏感查询

当前防护: 0 (research_schedule/watch 无审批)
风险: 中
```

### A5: Cron 规模扩大风险

**攻击向量:** 5 个 cron job 的攻击面是 3 个的 1.7 倍

```
新增风险:
  WF-002: 如果 Minerva 研究被投毒，每周自动扩散
  WF-006: 每小时运行，如果被篡改可高频攻击

当前防护: WF-003 日检 (24h 检测窗口)
风险: 低 — 已有交叉验证，但检测频率跟不上攻击频率
```

### A6: jieba 依赖注入

**攻击向量:** 替换 jieba 词典或模块

```
攻击步骤:
1. 修改 jieba 缓存文件或词典
2. 特定词被"错误分词" → 搜索被操纵
3. "删除"→分词为"保留" → 恶意操作被隐藏

当前防护: 0
风险: 低 — 需要文件系统写入权限
```

### A7: WF-004 委员会决策伪造

**攻击向量:** 伪造委员会决策记录

```
攻击步骤:
1. 直接写入 STATE.yaml 伪造委员会决策
2. 绕过正常 CHAIR→EXEC→AUDIT 流程
3. WF-003 交叉验证 (24h后) 才发现

当前防护: WF-003 日检
风险: 中 — 24h 窗口内决策已被执行
```

---

## 二轮：蓝队防御评估

### 现有防护

| 攻击 | 防护 | 有效性 |
|------|------|--------|
| A1 SSB投毒 | WF-003 SSB健康检查 | ⭐⭐ (日检，被动) |
| A2 感知投毒 | filter_scorer 评分 | ⭐⭐⭐ (过滤了 6/118) |
| A3 多Agent串通 | 单模型限制 (Phase 2固有) | ⭐ (无法防御) |
| A4 Minerva滥用 | 无 | 0 |
| A5 Cron扩大 | WF-003 交叉验证 | ⭐⭐ |
| A6 jieba依赖 | 无 | 0 |
| A7 委员会伪造 | WF-003 交叉验证 | ⭐⭐ |

### 新缺口

```
缺口1: SSB 无写入认证
  → 任何有文件系统权限的进程可写 ecos.db
  → 需要: SSB 写入签名或至少 git 版本控制

缺口2: 多Agent 伪独立 (Phase 2 硬限制)
  → delegate_task 3 Agent 共享同一 LLM
  → → A3 无法防御，直到 Phase 3 引入多模型

缺口3: Minerva 研究无审批
  → research_schedule/watch 可被滥用
  → 需要: 调用前人类确认

缺口4: 感知管道评分可被针对
  → 攻击者可构造"看起来高分"的垃圾文档
  → 需要: 内容语义评分 (当前仅有结构评分)
```

---

## 三轮：修复建议

```
P0 (立即):
  □ A4: Minerva research_schedule/watch 调用前确认
  □ A7: WF-003 加委员会决策完整性校验

P1 (本周):
  □ A1: SSB ecos.db 加入 git 追踪 (检测篡改)
  □ A2: filter_scorer 加内容语义评分

P2 (Phase 3):
  □ A3: 多模型 Agent 引入 → 真正独立审查
  □ A6: jieba 词典完整性校验
```

---

## 评分对比

```
维度          Phase 1    Phase 2    变化
──            ────────   ────────    ────
宪法安全      60%        70%        +10% (日检+实时规则)
数据安全      75%        70%        -5%  (SSB无认证)
操作安全      55%        60%        +5%  (CRITIC角色)
连续性安全    40%        65%        +25% (SSB+HANDOFF自动化)
知识安全      55%        60%        +5%  (感知管道过滤)

综合评分      57%        65%        +8%
```

---

## 最大风险

```
🥇 A3 多Agent串通 — HIGH, 无法防御 (Phase 2 硬限制)
    → 缓解: 标注此限制, Phase 3 引入多模型

🥈 A1 SSB投毒 — HIGH, 检测窗口 24h
    → 缓解: git 追踪 + 写入签名

🥉 A2 感知投毒 — MED, 可被针对
    → 缓解: 语义评分增强
```

---

*红蓝对抗 v2 完成: 2026-05-14*
