# eCOS — 现有问题深度分析

> 2026-05-14 | 基于 Phase 1→Phase 2 全部验证数据

---

## 一、问题全景

```
                    总数: 19 个未解决问题

架构债务    ████████ 8    安全漏洞    ████ 4
质量缺陷    ████ 4          集成缺口    ███ 3
```

---

## 二、架构债务深度分析

### D1: L2 感知层 3 阶缺失 (HIGH)

```
已实现:   Capture ✅    Filter ✅
未实现:   Structure ❌   Contextualize ❌   Integrate ❌

根因:
  Capture+Filter 是管道入口，实现相对简单
  Structure 需要: 统一文档 schema、自动分类、格式标准化
  Contextualize 需要: 自动实体关联、跨域语义链接
  Integrate 需要: KOS+Minerva+SharedBrain 三向知识融合
  
  后三阶每一阶都依赖前一阶的产出
  且 Structure 需要 NLP/LLM 能力 → Phase 3

影响:
  知识质量不一致 — Minerva报告和用户文档混在一起
  跨域关联缺失 — gongwen 中政策和 guozhuan 中平台方案无自动链接
  感知层仅完成了"入口"，未完成"降熵"的核心承诺

Phase 3 路径:
  先 Structure (Sprint 1) → Contextualize (Sprint 2) → Integrate (Sprint 3)
```

### D2: L6 反馈层无实时拦截 (MED)

```
已实现:   WF-003 日检 ✅    REALTIME-CHECKS R1-R5 (规则定义) ✅
缺失:     操作前自动拦截 ❌

根因:
  实时 hook 需要系统级拦截机制
  Hermes 的工具调用层没有"操作前检查"的回调点
  当前只能靠 Agent 自觉 + 日检发现

影响:
  不可逆操作仍然可以执行（Agent 可能"忘记"检查 IRREVERSIBLE-OPS）
  安全窗口 24h（日检）而非 0s（实时）
  
Phase 3 路径:
  需要 Hermes 支持 tool-call-before hook
  或通过 custom tool wrapper 实现
```

### D3: SSB 无写入认证 (MED)

```
已实现:   SSB SQLite ✅    文本 dump ✅    git 追踪 ✅
缺失:     写入签名 ❌       访问控制 ❌

根因:
  SQLite 无内置认证机制
  所有 eCOS 脚本运行在同一用户下 → 文件系统权限足够
  加入签名需要密钥管理基础设施

影响:
  任何有文件写入权限的进程可以注入 SSB 事件
  渗透测试证实: 伪造 FAILURE 事件成功写入

Phase 3 路径:
  简单方案: HMAC 签名（共享密钥）
  完整方案: 基于 B-OS 的 Event Bus（已有认证机制）
```

### D4-D8: 其他架构债务 (LOW-MED)

```
D4: IPA 运行时未完整实例化
    当前: WF-004 部分实例化 (I/P/A 映射)
    缺失: 贝叶斯更新回路的形式化

D5: Phase 1→Phase 2 委员会演进不完整
    当前: 三角模式(Phase1) + WF-004(Phase2) 并存
    问题: 两个机制没有明确的"何时用哪个"的决策树

D6: WF-004 依赖单模型
    当前: CHAIR(Hermes) + delegate_task ×3
    问题: 所有 Agent 共享同一 LLM → 审查独立性受限

D7: Cron 配置与 STATE 同步依赖 Agent 纪律
    修复: WF-003 交叉验证 + WF-005 自动更新
    残留: STATE 仍可能滞后

D8: 文档版本化未实施
    GENOME P3 要求"版本化知识, 非覆盖替换"
    当前: KOS 文档覆盖式更新, 无版本历史
```

---

## 三、安全漏洞深度分析

### S1: 感知管道评分可被针对性绕过 (HIGH)

```
漏洞: filter_scorer 纯结构化评分
      渗透测试: 构造标题+表格+列表+分段 → 100分 → 进入KOS

现状:
  filter_scorer.py 评分维度:
    标题: +20    结构: +15    长度: +20
    元数据: +15  编号: +10    扩展名: +10    可读性: +10
  阈值: ≥60 通过

  模板化垃圾文档轻松获得 90-100 分
  但真正的高质量文档也可能只有 50-70 分 (短小精悍)

根因:
  结构化评分是"必要的但不充分的"
  语义评分需要 LLM → 成本 + 延迟
  Phase 2 选择了"快速可用"而非"安全可靠"

Phase 3 方案:
  L1 研究启用 quality_gate (Minerva 已有)
  扩展到 filter_scorer: LLM 内容评估 + 实体一致性检查
  低质量文档标记 trust_level=low (而非直接丢弃)
```

### S2: 多 Agent 伪独立 (HIGH - 硬限制)

```
漏洞: delegate_task 创建的 3 个 Agent 共享同一 LLM
      渗透测试未实际执行 (无法绕过的硬限制)

根因:
  Hermes delegate_task 不支持 per-task model override
  所有子 Agent 继承父会话的 model/provider
  即使支持, 单 provider 的多模型切换也不等于真正的独立审查

影响:
  A3(多Agent串通) 无法防御
  CRITIC 角色的审查独立性受限
  WF-004 的"真多Agent"实际上是"真多Context, 同Model"

Phase 3 需求:
  delegate_task 支持 per-task model 参数
  至少 2 个不同的 provider/model 可用于委员会
  理想: CHAIR(deepseek) + EXEC(claude) + AUDIT(不同claude实例)
```

### S3-S4: 其他安全风险

```
S3: Minerva 调度无审批 (MED → MITIGATED)
    问题: research_schedule/watch 可被滥用
    修复: R4 规则定义, 要求人类确认
    残留: 规则依赖 Agent 遵守

S4: jieba 依赖风险 (LOW)
    问题: jieba 词典可被替换 → 搜索操纵
    现有防护: 需要文件系统权限
    建议: 词典文件加入 git 追踪
```

---

## 四、质量缺陷深度分析

### Q1: Minerva 研究稳定性 (MED → FIXED)

```
问题: L0 研究 ~25% 超时 (120s)
修复: timeout → 180s
验证: 后续调用均在 180s 内完成

残留风险:
  output 阶段极端情况 (LLM 生成极长报告) 可能超过 180s
  Semantic Scholar 429 限流 (LOW)
```

### Q2: KOS 中文搜索 (MED → FIXED, 待验证)

```
问题: "数字化平台建设" → 0 结果
修复链:
  Phase 1: split() + OR (基础改善)
  Phase 2: jieba 分词 → "数字化 OR 平台 OR 建设"
           已集成, 降级到 split() 兜底

待验证: MCP 重载后实际搜索效果
```

### Q3: KOS 移植性 (MED)

```
问题: VAULT_OPS_DIR 硬编码 iCloud 路径
影响: KOS MCP 不可移植到其他机器
方案: 重构为环境变量或配置文件 → Phase 3
```

### Q4: WF-001 交付率 (LOW)

```
问题: Weixin delivery rate limited
      WF-001 运行成功, 但通知未送达
影响: 不影响功能, 仅影响通知
方案: 改 deliver 方式 或接受静默
```

---

## 五、集成缺口分析

### I1: SharedBrain B-OS (评估完成, 待接入)

```
B-OS v10.0.0 → MCP Server · Event Bus · Knowledge Graph
与 eCOS 重叠: D_Memory (vs KOS), D_KnowledgeIntegration (vs 感知层)
互补: D_Governance (委员会对齐), Event Bus (SSB 后端)

接入路径:
  Phase 2: 不接入 (避免功能重叠混乱)
  Phase 3: SSB → B-OS Event Bus 迁移
          评估 D_KnowledgeIntegration 作为感知层增强
```

### I2: KOS-Minerva 语义搜索 (待填充)

```
KOS semantic_search → 依赖 Minerva LanceDB
LanceDB 嵌入未填充 → 始终返回空

方案: Phase 3 填充嵌入 或接受 FTS5 OR 模式
优先级: 低 (FTS5+OR+jieba 已解决主要痛点)
```

### I3: 感知管道 → KOS 索引链路

```
已实现: capture_watcher → filter_scorer → SSB → KOS indexer ✅
缺失:   自动触发链路 (当前依赖 WF-006 cron, 非事件驱动)

Phase 3: SSB PERCEPTION 事件 → 自动触发 KOS 索引
         (当前每小时检查, 可优化为实时)
```

---

## 六、问题优先级矩阵

```
         紧急度
        高      中      低
    ┌────────┬────────┬────────┐
  高│ S1感知 │ D1感知 │ S2多Agent
    │ 评分   │ 3阶    │ 伪独立  │
影  ├────────┼────────┼────────┤
  中│        │ D2实时 │ D3 SSB  │
    │        │ 拦截   │ 认证    │
响  ├────────┼────────┼────────┤
  低│        │ Q3移植 │ Q4交付 │
    │        │ I1 BOS │ I2语义 │
    └────────┴────────┴────────┘
```

---

## 七、Phase 3 关键路径

```
Phase 3 必须解决 (阻塞项):
  1. 多模型 Agent → 解锁 S2 + 委员会真实独立性
  2. L2 Structure → 感知层管道继续推进
  3. SSB 认证 → 防御 S1 的深度攻击

Phase 3 应该解决:
  4. 实时拦截 (D2)
  5. 语义评分 (S1)
  6. SharedBrain 接入评估 (I1)

Phase 3 可以延后:
  7. KOS 移植性 (Q3)
  8. Semantic Search (I2)
```

---

*深度分析完成: 19问题 → 7个Phase3必须解决*
