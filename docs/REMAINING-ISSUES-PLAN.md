# 遗留问题解决方案

> 2026-05-15 | 白盒审计发现 | 2个P1问题

---

## 问题1: 委员会闲置 (94.7%事件未触发委员会)

### 现状

| 指标 | 值 |
|------|-----|
| 设计文档 | CHARTER + TRIANGLE + DECISION-TREE + WF-004 |
| ADR决策 | 3份 (003/008/009) |
| 委员会SSB事件 | 仅20条 (全部Phase 2/3验证) |
| CRITIC触发率 | 0% (3个真实提案均判定LOW) |

### 根因

委员会是一个**被动机制**——只在"有人调用"时才运行。当前：
1. CRITIC规则过于宽松：真实架构提案（如Phase规划、DB迁移）被判为LOW
2. 没有定期触发点：7条Cron中无一条调用委员会
3. 没有业务事件的自动升级：SSB中HIGH风险事件出现时无人通知委员会

### 方案

**方案A: CRITIC规则语义化 (立即可做, 30min)**

当前CRITIC靠关键词匹配（"MED","GENOME","不可逆"），真实提案巧妙避开了这些词。改为语义规则：

```python
# 新增触发条件
R6_ARCHITECTURE_CHANGE: 匹配 "架构|迁移|Phase|规划|重构"
R7_HIGH_SSB_VOLUME:    24h事件数 > 阈值 → 触发审查
R8_COMMITTEE_PERIODIC: 每周自动触发 (WF-009 cron)
```

**方案B: 委员会定期审查 (本周可做, 2h)**

新增 WF-009 cron: 每周一 09:00 自动运行委员会审查
- 读取本周SSB事件摘要
- 读取涌现度量变化
- 读取FAILURES新增案例
- CRITIC独立审查
- EXEC提出改进建议
- CHAIR决定优先级
- 写入HANDOFF

**方案C: 事件驱动触发 (Phase 5)**

当SSB中出现以下事件时自动通知委员会：
- FAILURE事件 (seq > 阈值)
- SECURITY事件 (HIGH/CRITICAL)
- STATE.drift > 30%
- 新ADR提案

**推荐**: A + B 并行（立即可做，本周完成）

---

## 问题2: JSONL旧事件无HMAC签名 (94.7%缺口)

### 现状

| 指标 | 值 |
|------|-----|
| DB签名率 | 239/4516 (5.3%) |
| JSONL签名率 | 229/4506 (5.1%) |
| JSONL有签名字段 | 100% (字段存在但值为null) |

### 根因

`ssb_auth.py sign-new` 每次只签50个事件。我们运行了3次 = 150个，其余4277个未签名。
DB和JSONL的10个差异来自最新测试事件（publish到DB但未dump到JSONL）。

### 方案

**方案: 全量签名 + JSONL重dump (立即可做, 10min)**

```bash
# Step 1: 对DB中所有未签名事件签名
python3 scripts/ssb_auth.py sign-new --all

# Step 2: 重新dump到JSONL (包含签名)
python3 scripts/ssb_dump.py

# Step 3: 验证一致性
# DB signed == JSONL signed
# DB count == JSONL count
# ssb_integrity verify 通过
```

需要修改 `ssb_auth.py` 增加 `--all` 参数支持全量签名。

### 验证

| 检查 | 命令 |
|------|------|
| DB全量签名 | `ssb_auth verify` → verified=4516 |
| JSONL与DB一致 | `wc -l ecos.jsonl` == DB count |
| 哈希链完整 | `ssb_integrity.py` → OK |
| 篡改检测 | 修改1个事件 → verify检测到 |

---

## 执行计划

| 步骤 | 内容 | 时间 |
|------|------|------|
| 1 | 修改 ssb_auth.py 支持 `--all` | 5min |
| 2 | 执行全量签名 + JSONL重dump | 2min |
| 3 | 修改 CRITIC 规则 (R6-R8) | 15min |
| 4 | 创建 WF-009 委员会周检 cron | 10min |
| 5 | 端到端验证 | 5min |

**总计: ~40min**
