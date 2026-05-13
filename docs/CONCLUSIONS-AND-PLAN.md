# eCOS Phase 1 — 关键结论与迭代方案

> 从 2026-05-13 会话完整历程中提炼

---

## 一、关键结论 (6条)

### C1: 架构先行的投资回报率为正

```
投入: 1小时设计六层架构 + LADS + SSB
产出: 后续4小时所有操作都有明确的"该放哪层"的判断标准
      MCP接入 → L5行动层 ✓
      KOS索引 → L3持久层 ✓
      不可逆规则 → L6反馈层(宪法执行器) ✓
反例: 如果先做功能再补架构，每个决策都需要重新讨论边界
```

**结论: 架构不是文档负担，是决策加速器。**

---

### C2: 逻辑推演是最高效的审查手段

```
3个矛盾在文档里躺了0天（当天写的）
20分钟推演全部暴露
→ 8Agent幻想  → 三角模式
→ 30%阈值    → 布尔+定量分级
→ SSB空转    → 文件读写降级
```

**结论: 任何架构产出完成后，必须走一轮"当前Phase最小可实施"推演。**

---

### C3: 集成层是惊喜制造机

```
惊喜1: hermes config set 把 YAML列表存成JSON字符串
        → 2个MCP全部连接失败 → 1行修复解决

惊喜2: macOS没有timeout命令
        → KOS MCP可用性误判 → FAIL-004误报

惊喜3: KOS索引器不跟随symlink
        → P3方案从symlink切换到manifest扩展

惊喜4: Minerva MCP的main()跳过init_server()
        → "部分可用"不是bug → 发现KOS桥接替代路径
```

**结论: 文件存在 ≠ 可运行。配置完成 ≠ 连接成功。MCP接入必须实际握手验证。**

---

### C4: KOS→Minerva 桥接是正确的架构分层

```
初始假设: Minerva MCP直接接入 → 5个核心工具不可用 → Minerva "有问题"

深入后发现:
  不是问题，是有意设计。
  MCP统一入口 = KOS
  Minerva = 引擎层（被KOS通过子进程调用）
  
  这个分层符合eCOS的六层模型：
  L4智能层(Hermes) → L5行动层(KOS MCP) → L3持久层(KOS DB)
                                          → Minerva CLI(引擎)
```

**结论: 不要只看表面错误。理解上游设计意图后再判断"是bug还是feature"。**

---

### C5: LADS机制正确，执行纪律是瓶颈

```
机制层 ✅
  HANDOFF格式正确
  STATE结构完整
  HISTORY归档正常
  冷启动路由清晰

执行层 ❌
  HANDOFF滞后3.5小时
  STATE遗漏WF-001
  更新触发全靠Agent"记得"
```

**结论: 机制设计对，但缺少强制执行。Phase 2必须考虑自动更新或阶段检查点。**

---

### C6: Phase 1 的实际边界

```
GENOME Phase1目标  →  实际状态

"单体建立期"       →  准确。确实是单Agent(Hermes) + 3个Tool(KOS/Minerva/SharedBrain)
"KOS MCP接入"     →  完成。且扩展到7域，超出预期
"Minerva MCP接入" →  部分。但通过KOS桥接获得了完整研究能力
"SSB Schema v1"   →  完成。10种Event，Phase1退化为文件读写
"委员会章程"      →  完成。Phase1三角 + Phase2完整

Phase1完成度: 100%
Phase2就绪度:  50%（基础设施ready，但建议先跑1-2周验证稳定性）
```

---

## 二、迭代优化方案

```
现在 ────────────────────────────────────────────→ 未来

Week 1-2               Week 3-4               Month 2+
[稳定验证]       →    [优化增强]         →    [Phase 2 启动]
```

### 迭代一: 稳定验证 (本周至下周)

```
目标: 验证自动化工作流正常运行，积累运行数据

□ I1.1 WF-001 首跑观察 (明天 02:00)
        → 检查KOS索引是否正常增量
        → 确认minerva_reports域新报告被自动索引
        → 如有异常 → 写入FAILURES

□ I1.2 WF-003 首跑观察 (下周一 09:00)
        → 检查hermes doctor输出
        → 验证GENOME/STATE/HANDOFF完整性
        → 确认静默模式正常（无异常时不推送）

□ I1.3 RFC-0001 人类确认
        → ACCEPTED → 所有修正正式生效
        → REJECTED → 按反馈重新调整

□ I1.4 ADR-007 写入
        → 记录 minerva_reports zone+domain 方案决策
```

### 迭代二: 纪律强化 (2周后)

```
目标: 解决LADS执行纪律问题

□ I2.1 HANDOFF自动更新检查
        方案: 在WF-005中实现"会话结束前检查HANDOFF是否过期"
              过期>1小时 → 强制更新 → 再结束

□ I2.2 STATE同步检查
        方案: WF-003 健康检查增加"STATE与实际cron/文件数一致性"校验项

□ I2.3 阶段检查清单
        方案: 每个Workflow的on_complete必须包含:
              - update_state: true
              - write_handoff: true
              当前WF-001/WF-003的cron prompt已包含此逻辑
```

### 迭代三: 体验优化 (2-4周)

```
目标: 修复已知体验问题

□ I3.1 KOS中文搜索优化
        当前: FTS5 AND语义，多词搜索命中率低
        方案: KOS MCP search_knowledge 增加 match_mode 参数 (AND/OR)
        或: Agent层面自动拆词→多次检索→结果合并

□ I3.2 Minerva MCP executor初始化
        当前: 5个核心工具不可用
        方案: 修复 Minerva server.py main() 添加 auto-init
        或: 接受现状，继续使用KOS桥接

□ I3.3 WF-002 Minerva深度研究 cron
        当前: research_now仅支持手动调用
        方案: 创建周期性深度研究任务
              如: 每周自动研究"政务数字化平台最新政策"
```

### 迭代四: Phase 2 启动 (1个月后)

```
前置条件:
  ✓ WF-001/WF-003 稳定运行 ≥ 2 周
  ✓ 失败案例库 ≥ 5 个有效案例
  ✓ HANDOFF/STATE 更新纪律已解决
  ✓ RFC-0001 已 ACCEPTED

Phase 2 首批任务:
  □ P2.1 delegate_task 3并发 → 三角委员会实际测试
  □ P2.2 WF-004 委员会决策会议 Workflow 上线
  □ P2.3 KOS本体扩展 (新增域、优化中文搜索)
  □ P2.4 Minerva L1-L2 级别研究启用
```

---

## 三、迭代优先级矩阵

```
                    影响力
                低          高
           ┌──────────┬──────────┐
      低   │ I3.1 KOS │ I1.3 RFC │  先做
           │ 中文搜索 │ 确认     │
费         ├──────────┼──────────┤
      高   │ I3.2     │ I2.1     │  后做
用         │ Minerva  │ HANDOFF  │
           │ executor │ 自动检查 │
           └──────────┴──────────┘
```

**建议执行顺序: I1 → I2 → I3 → I4，每迭代完成做一次 mini-review。**

---

*版本: v1.0*
*产出: 2026-05-13 全面复盘*
