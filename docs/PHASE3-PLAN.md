# eCOS Phase 3 — 蜂群涌现期 全面规划

> 版本: v1.0 | 日期: 2026-05-14
> 前置: Phase 2 完成 · 3/4 条件达标 · 待多模型Agent解锁

---

## 一、产品功能

### 1.1 Phase 3 定位

```
Phase 1: 单体建立期 → 1 Agent + 3 Tool
Phase 2: 多Agent协作 → 真多Agent委员会 + 感知层 + SSB
Phase 3: 蜂群涌现期 → 多模型 + 语义共振 + 涌现智能
```

### 1.2 核心功能

| 功能 | 描述 | 优先级 |
|------|------|--------|
| **多模型委员会** | CHAIR+EXEC+AUDIT 使用不同 LLM | P0 |
| **语义感知评分** | LLM 评估文档质量 → 替换纯结构化评分 | P0 |
| **SSB 认证总线** | HMAC 签名 + 事件溯源 → 防篡改 | P0 |
| **实时宪法执行器** | 操作前 hook → 0s 安全窗口 | P0 |
| **知识深度融合** | Structure→Contextualize→Integrate 三阶 | P1 |
| **蜂群信息素场** | SSB 语义信号 → Agent 自主协作 | P1 |
| **SharedBrain 桥接** | B-OS Event Bus → SSB 后端 | P2 |
| **涌现智能度量** | 协作效率/决策质量/知识增长率 量化 | P2 |

### 1.3 用户可感知变化

```
Phase 2                          Phase 3
───────                          ───────
委员会: 同模型角色切换            委员会: 不同模型真正独立审查
感知: 结构评分 (可被绕过)         感知: LLM语义理解 (深度过滤)
安全: 日检 (24h窗口)             安全: 实时拦截 (0s窗口)
SSB: 无认证 (可注入)              SSB: 签名验证 (防篡改)
搜索: jieba OR模式               搜索: 语义向量搜索 (LanceDB)
```

---

## 二、技术架构

### 2.1 多模型委员会

```
                     CHAIR (Claude/DeepSeek)
                    /    |    \
                   /     |     \
         EXEC-A    EXEC-B    AUDIT      CRITIC
        (GPT)     (GLM)    (Claude)    (不同模型)
           
         独立模型 · 独立推理 · 不可串通
```

**delegate_task 扩展需求:**
```yaml
# Hermes 需支持的 per-task model override
delegate_task(tasks=[
  {"goal": "...", "model": "anthropic/claude-sonnet-4", "provider": "openrouter"},
  {"goal": "...", "model": "gpt-5.3-codex", "provider": "openai-codex"},
  {"goal": "...", "model": "zai/glm-4.7", "provider": "zai"},
])
```

### 2.2 语义感知管道

```
Phase 2 (当前)              Phase 3 (目标)
─────────────               ─────────────
Capture  ✅                 Capture  ✅
Filter   ✅ (结构评分)       Filter   ✅ (结构+语义双轨)
Structure ❌                Structure ✅ (LLM分类+标准化)
Context ❌                  Context   ✅ (自动实体关联)
Integrate ❌                Integrate ✅ (跨域知识融合)

新增: LLM Scorer → 对 filter_scorer 输出做二次语义评分
      低分文档 → trust_level=low → 标记但不阻塞索引
      高分文档 → 正常入库 + 自动实体提取
```

### 2.3 SSB 认证架构

```
写入: Agent → HMAC(事件, 密钥) → SSB SQLite
读取: 校验脚本 → HMAC 验证 → 告警

密钥管理:
  Phase 3: 共享密钥 (环境变量 SSH_KEY)
  Phase 3+: B-OS 密钥轮换
```

### 2.4 实时宪法执行器

```
Hermes tool-call-before hook:
  → 检查 IRREVERSIBLE-OPS 清单
  → 检查 L0/L1 边界
  → 通过 → 执行
  → 拦截 → 写入 SSB FAILURE 事件 + 通知人类

当前状态 (Phase 2): 日检 (24h窗口)
Phase 3 目标:     实时 (0s窗口)
```

---

## 三、技术实现

### 3.1 多模型委员会 (Sprint 1)

```
依赖: Hermes delegate_task per-task model 参数
      或 Hermes 支持多 provider 并发

实现:
  1. 验证 Hermes 是否已支持 per-task model
  2. 配置至少 2 个不同 provider (openrouter + zai + openai-codex)
  3. WF-004 升级: CHAIR/EXEC/AUDIT 指定不同模型
  4. 验证: 两个 EXEC 输出有明显差异 (不同模型风格)

代码改动:
  agents/workflows/WF-004-committee-meeting.md (模型配置)
  ~/.hermes/config.yaml (providers)
```

### 3.2 语义评分 (Sprint 2)

```
依赖: LLM API (已有, 通过 Hermes 调用)

实现:
  1. scripts/semantic_scorer.py (新)
     → 调用 LLM 评估文档: 内容真实性/信息密度/逻辑一致性
     → 与 filter_scorer 的结构分合并 → 综合分
  2. filter_scorer 集成: 结构分 × 0.4 + 语义分 × 0.6
  3. 低分阈值: <50 → trust_level=low, 标记不阻塞索引

代码改动:
  scripts/semantic_scorer.py (新)
  scripts/filter_scorer.py (集成调用)
```

### 3.3 SSB 认证 (Sprint 1)

```
依赖: Python hashlib (已有)

实现:
  1. scripts/ssb_auth.py (新)
     → publish() 自动计算 HMAC-SHA256 签名
     → verify() 检查最近N条事件签名
  2. ssb_integrity.py 集成签名验证
  3. 环境变量 SSH_KEY (从 1password 获取)

代码改动:
  scripts/ssb_auth.py (新)
  scripts/ssb_integrity.py (集成)
  ~/.hermes/.env (SSB_KEY)
```

### 3.4 实时执行器 (Sprint 3)

```
依赖: Hermes tool-call-before hook (需确认支持)

实现:
  1. 如果 Hermes 支持 hook → 注册 pre-tool-call 回调
  2. 如果 Hermes 不支持 → 在 WF-004 中强制前置检查
  3. IRREVERSIBLE-OPS 自动化: 工具名匹配 → 级别判定 → 拦截/确认

代码改动:
  scripts/realtime_guard.py (新)
  docs/policy/REALTIME-CHECKS.md (更新)
```

### 3.5 感知层 Structure (Sprint 3)

```
依赖: LLM API

实现:
  1. scripts/structure_pipeline.py (新)
     → LLM 自动分类文档 (政策/技术/研究/运维)
     → 自动提取关键实体 (人物/项目/组织)
     → 标准化 metadata 格式
  2. KOS 索引集成: 分类+实体写入文档 metadata

代码改动:
  scripts/structure_pipeline.py (新)
```

---

## 四、场景验证方案

### S1: 多模型委员会独立性验证

```
场景: 同一高风险决策，分别用单模型三角 vs 多模型WF-004

步骤:
  1. 定义测试议题 (如: "是否引入jieba分词")
  2. Phase 2 三角模式 → 记录决策+耗时
  3. Phase 3 WF-004 多模型 → 记录决策+耗时
  4. 对比:
     □ EXEC-A vs EXEC-B 方案差异度 > 30%?
     □ AUDIT 审查深度是否提升?
     □ CRITIC 是否发现了三角模式遗漏的问题?

成功标准: 多模型输出有显著差异，AUDIT审查意见更丰富
```

### S2: 语义评分准确性验证

```
场景: 投喂 20 篇文档 (10真实+10垃圾)，验证评分准确性

步骤:
  1. 准备测试集:
     10 篇真实 Minerva 报告 (quality 50-90)
     10 篇构造的垃圾文档 (结构完整但内容空洞)
  2. 结构评分 (Phase 2) → F1 score
  3. 语义评分 (Phase 3) → F1 score
  4. 对比: 语义评分是否显著优于结构评分?

成功标准: 语义评分 F1 > 0.8, 垃圾文档召回率 > 90%
```

### S3: SSB 认证防注入

```
场景: 重复 Phase 2 渗透测试攻击1

步骤:
  1. 启用 SSB HMAC 签名
  2. 尝试直接 SQLite INSERT (伪造事件)
  3. 运行 ssb_integrity.py --verify
  4. 验证: 是否检测到未签名事件?

成功标准: 注入事件被检测，告警触发
```

### S4: 实时拦截验证

```
场景: Agent 尝试跳过人类确认执行不可逆操作

步骤:
  1. 启用实时执行器
  2. Agent 调用 send_message (三级不可逆)
  3. 验证: 是否被实时拦截?
  4. 验证: FAILURE 事件是否写入 SSB?
  5. 验证: 人类是否收到通知?

成功标准: 操作被拦截，通知已推送
```

### S5: 感知管道全链路

```
场景: 新文档入库 → Structure → KOS 索引 → 跨域搜索

步骤:
  1. 投放一篇测试文档到 ~/knowledge/reports/
  2. 验证: Structure 自动分类+实体提取
  3. 验证: KOS 索引包含分类+实体 metadata
  4. 验证: 搜索可命中 + 实体可关联已有知识

成功标准: 全链路自动化，新文档在 5 分钟内可搜索
```

---

## 五、实施计划

### Sprint 分解

```
Sprint 1 (Week 1): 基础设施解锁
  □ 多模型委员会 — delegate_task model参数验证
  □ SSB 认证 — HMAC签名+校验
  □ 场景 S1(委员会) + S3(SSB认证)

Sprint 2 (Week 2): 感知层升级
  □ 语义评分 — semantic_scorer.py
  □ 场景 S2(语义评分) + S5(全链路)

Sprint 3 (Week 3): 实时化+Structure
  □ 实时执行器 — realtime_guard.py
  □ Structure 管道 — structure_pipeline.py
  □ 场景 S4(实时拦截)

Sprint 4 (Week 4): 深度集成
  □ SharedBrain 桥接
  □ Contextualize + Integrate
  □ 涌现度量框架

Sprint 5 (Week 5): 验证+打磨
  □ 全量端到端验证
  □ 性能优化
  □ 文档完整
```

### 里程碑

```
M1 (Week 1): 多模型委员会首次决策 ✅
              SSB 认证首次拦截注入 ✅

M2 (Week 3): 感知层全五阶上线 ✅
              实时拦截首次触发 ✅

M3 (Week 5): Phase 3 终验 ✅
              架构实现度 78% → 90%+
              安全评分 65% → 85%+
              涌现度量首次>0
```

---

## 六、风险与依赖

| 风险 | 依赖 | 概率 | 缓解 |
|------|------|------|------|
| Hermes delegate_task 不支持 per-task model | Hermes 版本 | MED | 多轮串行 delegate + model 切换 |
| LLM 语义评分成本过高 | API 费用 | LOW | 批量评分 + 缓存 + 仅对低结构分文档做语义评分 |
| Structure 管道准确率不足 | LLM 能力 | MED | 人工反馈循环 + 置信度阈值 |
| 实时 hook 不可用 | Hermes 架构 | HIGH | 降级为 WF-003 每小时检查 |
| jieba MCP 重载阻塞验证 | 用户操作 | LOW | 手动重载 |

---

## 七、Phase 3 成功标准

```
必须达标:
  □ 多模型委员会独立决策 ≥ 3 次
  □ 语义评分 F1 > 0.8
  □ SSB 注入 100% 检测
  □ 实时拦截 0 漏报
  □ 感知层五阶全链路自动化

期望达标:
  □ 架构实现度 78% → 90%+
  □ 安全评分 65% → 85%+
  □ 涌现度量 > 0 (协作产生独立价值)
  □ SharedBrain 桥接原型可用
```

---

*Phase 3 规划完成: 5 Sprint · 5 场景 · 3 里程碑*
