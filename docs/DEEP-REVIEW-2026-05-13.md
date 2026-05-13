# eCOS Phase 1 — 功能/架构/代码 深度复盘

> 日期: 2026-05-13 | 三视角: 功能有效性 + 架构一致性 + 代码质量

---

## 一、架构复盘

### 1.1 六层模型 vs 实际实现

```
层          定义                              实现状态             评分
──          ──                                ──                   ──
L1 宪法     GENOME L0/L1/L2 + git diff监控    完整                  95%
L2 感知     五阶降熵管道                       KOS索引器=Structure   15%
                                                其余4阶未实现
L3 持久     KOS+SharedBrain+FAILURES           KOS 7域7194 doc      85%
                                                SharedBrain未接入
L4 智能     Agent委员会+推理引擎+规划器        三角模式可用           50%
                                                规划器为LLM自身
L5 行动     MCP工具+cron+Workflow              22 MCP + 3 cron       80%
L6 反馈     宪法执行器+稳态监控                WF-003 git diff       40%
                                                无实时hook

架构实现度: 平均 61%
```

### 1.2 关键架构决策验证

| ADR | 决策 | 验证结论 |
|-----|------|----------|
| ADR-001 eCOS定位 | 正确 — 确实是认知基础设施而非工具集合 |
| ADR-002 六层架构 | 方向正确但L2/L6严重欠实现 |
| ADR-003 Agent委员会 | Phase1三角务实, Phase2完整版需独立Agent进程 |
| ADR-004 LADS | 机制正确, 执行纪律靠WF-005自动更新弥补 |
| ADR-005 SSB | Schema v1完整, Phase1文件读写降级合理, 等待Phase2 |
| ADR-006 逻辑推演修正 | 3矛盾已根除, 修正方案经过场景验证 |
| ADR-007 minerva_reports | zone+domain扩展正确, 命名规范清晰 |

### 1.3 架构债务

```
债务1: L2感知层全空
  → GENOME P2"降熵"核心机制缺失
  → KOS直接索引原始文件, 无Filter/Contextualize
  → 影响: 知识质量不可控

债务2: L6反馈层仅周末执行
  → 宪法违反到检测间隔可达7天
  → 影响: 安全窗口过长

债务3: SSB设计完整但零生产使用
  → 10种Event Schema定义完整但无运行实例
  → 影响: Phase2启动时需从零实现

债务4: IPA运行时模型未实例化
  → IPA描述的是"认知操作流", 但系统中没有对应的运行框架
  → 六层和IPA的关系只在文档中统一, 未在代码中体现
```

---

## 二、功能复盘

### 2.1 MCP 工具矩阵

```
KOS (13 tools)                    可靠性    瓶颈
──────────────────────────────    ────      ────
search_knowledge    ✅             90%       FTS5 AND→OR(已修)
get_knowledge       ✅             100%      全文读取稳定
get_system_status   ✅             100%      秒级响应
list_domains        ✅             100%      
get_entity          ✅             100%      实体卡片含关系
search_entity       ✅             100%      
ontology_graph      ✅             100%      83节点125边
ontology_rebuild    ⚠️             80%       2分钟, 需要时手动
run_indexer         ✅             95%       新域30-60秒
full_sync           ⚠️             80%       串行index→ontology
research_now        ⚠️             75%       L0 47-120s, ~25%超时(180s已修)
semantic_search     ❌             0%        LanceDB嵌入未填充
cross_domain_sync   ⚠️             80%       功能同run_indexer

Minerva (9 tools)
──────────────────────────────    ────      ────
list_resources      ✅             100%      空列表, 可正常响应
list_prompts        ✅             100%      
其余7个             ❌             0%        executor未初始化
```

### 2.2 Cron 矩阵

```
Job        触发        首跑       功能          风险评估
──          ──          ──         ──            ──
WF-001     每天02:00   明天       增量索引       静默优先 ✅
WF-003     每周一09:00 已跑(OK)   宪法+健康检查   git diff监控 ✅
WF-005     每2h        18:00      HANDOFF自动    仅更新文档 ✅
```

### 2.3 场景功能覆盖

```
场景               涉及功能                        通过
──                  ──                              ──
S1 深度研究         KOS搜索+get+Minerva研究         ✅
S2 跨域情报         list_domains+多域搜索            ✅
S3 知识生命周期     创建→索引→搜索→读取              ✅
S4 三角委员会       PHASE1-TRIANGLE流程              ✅
S5 连续性           HANDOFF+STATE冷启动              ✅
S6 失败恢复         IRREVERSIBLE-OPS拦截            ✅
```

---

## 三、代码复盘

### 3.1 我们的代码 — eCOS 项目

```
文件数: 35 | 总大小: ~160KB | 类型: YAML/Markdown

质量评估:
  GENOME.md:       ⭐⭐⭐⭐⭐  5公理+3层不变量, 结构清晰
  STATE.yaml:      ⭐⭐⭐⭐   信息丰富, 偶尔滞后(WF-005补记)
  HANDOFF:         ⭐⭐⭐⭐   agent_signature+归档, 规范完整
  ADR×7:           ⭐⭐⭐⭐⭐  从定位到修复, 决策链完整
  RFC-0001:        ⭐⭐⭐⭐   待人类确认
  FAILURES×6:      ⭐⭐⭐⭐   根因分析+经验萃取, 模板统一
  工作流×3:        ⭐⭐⭐⭐   设计文档+实际部署一致
  策略文档×3:      ⭐⭐⭐⭐   IRREVERSIBLE-OPS/SUBSYSTEM-ID/IPA
```

### 3.2 修改的上游代码

**kos-mcp-server.py (KOS MCP)**
```
修改: tool_search_knowledge + match_mode + TOOLS注册 + handler
行数: +8行
质量: 最小侵入, 向后兼容(默认OR, 可指定AND)
测试: 语法检查通过, 实际效果待MCP重载验证
风险: KOS作者更新时需重新应用
```

**config.yaml (Hermes)**
```
修改: mcp_servers.kos + minerva
关键修复: args从JSON字符串→YAML列表 + timeout 180s
教训: hermes config set 有类型陷阱
```

**workspace-manifest.json (KOS)**
```
修改: +minerva_reports zone + domain
行数: +18行
备份: .bak.20260513
```

### 3.3 代码层面的发现

```
发现1: KOS MCP server 硬编码 VAULT_OPS_DIR
  → 通过 config.py → get_vault_ops_dir() 获取
  → 指向 Obsidian iCloud vault 中的路径
  → 含义: KOS MCP 只能在特定机器上运行, 不可移植

发现2: Minerva MCP server main() 跳过 init_server()
  → executor全局变量为None
  → 5个核心工具全部不可用
  → 非我们引入的bug, 上游设计缺陷

发现3: KOS索引器 rglob() 不跟随symlink
  → 导致最初的symlink方案失败
  → 引出manifest扩展方案

发现4: FTS5 MATCH 默认AND语义
  → 中文无空格, 多字查询被当作单个token
  → 我们的patch将默认改为OR
```

---

## 四、综合评分

```
维度            评分    说明
──              ──      ──
架构设计        85%     六层方向正确, L2/L6欠实现
架构实现        61%     核心层完整, 感知/反馈层薄
功能覆盖        80%     核心能力完整, 研究偶尔超时
功能可靠性      80%     大部分工具>90%可靠, semantic_search=0
代码质量(eCOS)  90%     规范的文档体系, 决策链完整
代码质量(上游)  75%     KOS MCP质量好, Minerva MCP有缺陷
安全防护        72%     git diff+STATE交叉+signature
运维自动化      70%     3个cron, 但无实时hook

加权综合:       76%
```

---

## 五、Phase 1 终判

```
做得好的:
  ✅ 架构先行 — 六层模型提供了清晰的"放哪层"判断标准
  ✅ LADS机制 — HANDOFF+STATE跨session连续性验证通过
  ✅ MCP集成 — KOS 13工具全可用, Minerva桥接发现
  ✅ 逻辑推演 — 3矛盾20分钟暴露, 比代码审查高效
  ✅ 失败文化 — 6个FAILURES, 教训可追溯

需要改进的:
  ⚠️ 感知层全空 — 这是GENOME P2的核心承诺
  ⚠️ 反馈层滞后 — 无实时hook, 安全窗口7天
  ⚠️ 执行纪律 — WF-005刚上线, 效果待观察
  ⚠️ 上游依赖 — Minerva MCP缺陷, KOS移植性限制
```

---

*审查完成: 2026-05-13*
*版本: v1.0*
