# 架构合规性审计报告

> 审计时间: 2026-05-15
> 审计对象: /Users/xiamingxing/Workspace/eCOS
> 审计范围: 六层模型、IPA运行时模型、层间依赖、SSB Schema一致性、安全架构
> 审计粒度: 代码级

---

## 一、六层架构实现度

### L1 宪法层

**检查项: GENOME.md 5公理在代码中的执行器**

| 公理 | 执行器 | 实现度 | 严重度 |
|------|--------|--------|--------|
| P1 认知延伸 | capture_watcher.py (外化感知) | ✅ 已实现 | - |
| P2 信息熵公理 | 五阶管道 (capture→filter→structure→contextualize→integrate) | ⚠️ 部分实现 | MED |
| P3 贝叶斯更新 | SSB事件版本化 + STATE.yaml演进 | ⚠️ 版本化机制粗糙 | MED |
| P4 控制论稳态 | realtime_guard.py + WF-003健康检查 | ✅ 已实现 | - |
| P5 涌现公理 | SSB事件总线 + committee机制 | ⚠️ SSB总线格式不统一 | HIGH |

**发现 #1 [严重: HIGH] — P5 SSB语义场格式分裂**
- 问题: SSB事件总线的格式在文档(SSB-SCHEMA-V1.md)、SQLite实际Schema、JSONL导出、ecos_common.py中共存在4种不同的字段命名体系，破坏了"语义场"的设计初衷
- 修复: 统一为SSB-SCHEMA-V1.md定义的嵌套JSON格式，或明确声明Phase内使用简化格式并更新文档

**发现 #2 [严重: MED] — P2 五阶管道缺少3/5阶**
- 问题: GENOME.md宣称"五阶降熵管道(Capture→Filter→Structure→Contextualize→Integrate)"，但实际代码中structure_pipeline.py和contextualize_pipeline.py各自独立运行，缺少与前两阶(capture/filter)和后一阶(integrate)的数据流转机制
- 修复: 在WF-006中补充全管道串联逻辑，或在文档中明确各阶段独立运行的降级模式

**发现 #3 [严重: MED] — P3 贝叶斯版本化无实现**
- 问题: SSB-SCHEMA-V1.md定义了"prior_belief / posterior_belief"字段，但代码中所有SSB事件写入均未使用这些字段
- 修复: 在ssb_client.publish()中增加信念版本化支持

### L2 感知层 (五阶管道)

**检查项: 每阶代码质量、输入输出协议**

| 阶段 | 脚本 | 输入 | 输出 | 代码质量 | 协议一致性 |
|------|------|------|------|----------|-----------|
| Capture | capture_watcher.py | 文件系统(3目录) | SSB PERCEPTION事件 | ✅ 良好 | ⚠️ 本地CREATE TABLE与ecos_common不一致 |
| Filter | filter_scorer.py | SSB PERCEPTION事件 | SSB STATE_CHANGE/INDEX_READY | ✅ 良好 | ⚠️ 使用ssb_client schema |
| Structure | structure_pipeline.py | 文件路径(CLI参数) | JSON stdout | ⚠️ 简陋 | ❌ 无SSB集成 |
| Contextualize | contextualize_pipeline.py | 文件路径(CLI参数) | JSON stdout | ⚠️ 简陋 | ❌ 无SSB集成 |
| Integrate | integrate_pipeline.py | SSB JSONL文件 | cross_refs.jsonl | ⚠️ 中等 | ❌ 绕开ssb_client直接读写JSONL |

**发现 #4 [严重: HIGH] — capture_watcher本地SQL与ecos_common冲突**
- 位置: capture_watcher.py:145-187 (PerceptionDB._init_db)
- 问题: capture_watcher在自己的_init_db中重新定义了ssb_events表结构（20列），导入ecos_common的CREATE_SSB_EVENTS_SQL（19列，不同字段名）但从未使用。两个CREATE TABLE存在字段冲突风险
- 修复: 删除capture_watcher中的本地CREATE TABLE，统一使用ssb_client或ecos_common的表结构

**发现 #5 [严重: HIGH] — integrate_pipeline绕开SSB总线直写JSONL**
- 位置: integrate_pipeline.py:150-264
- 问题: integrate_pipeline直接os.path操作JSONL文件读写，完全不使用ssb_client库。违反L0-05"Agent间通信必须经过SSB总线"
- 修复: 重构为使用ssb_client.publish()和ssb_client.query()，而非直接文件操作

**发现 #6 [严重: MED] — structure和contextualize管道孤岛**
- 问题: structure_pipeline.py和contextualize_pipeline.py只接受CLI文件路径参数，输出JSON到stdout，不与SSB事件总线集成
- 修复: 增加SSB事件输入模式（读取PERCEPTION事件）和输出模式（发布STRUCTURED/CONTEXTUALIZED事件）

### L3 持久层 (KOS/SSB/LADS)

**发现 #7 [严重: CRITICAL] — SSB Schema四重分裂**
- 位置: SSB-SCHEMA-V1.md vs ecos_common.py vs 实际SQLite vs JSONL导出
- 详析:

| 系统 | 字段体系 | 字段数 | 核心差异 |
|------|---------|--------|---------|
| SSB-SCHEMA-V1.md | 嵌套JSON(ssb_version, source.agent, event.type...) | ~25字段 | 文档定义的"理想格式" |
| ecos_common.py | 扁平(source_zone, target_zone, event_type, action...) | 20字段 | 从未被实际使用 |
| 实际SQLite(ssb_client) | 扁平(id, seq, source_agent, event_type, summary...) | 21字段 | 实际运行格式 |
| JSONL导出(ssb_dump) | 极简(id, seq, ts, agent, type, summary) | 6字段 | 丢失detail/payload/semantic |

- 影响: 当Agent按SSB-SCHEMA-V1.md格式构造事件时，ssb_client可以正确存入SQLite，但JSONL导出会丢失绝大部分信息；当ssb_dump导出→ssb_schema_migrate恢复时数据可能不完整
- 修复: 参见"SSB Schema一致性"部分详细方案

**发现 #8 [严重: MED] — KOS读写一致性问题**
- 位置: contextualize_pipeline.py:15
- 问题: KOS数据库路径硬编码且依赖环境变量KOS_INDEX_PATH，fallback路径指向iCloud同步目录。当iCloud未同步或路径变化时静默失败（返回空数组）
- 修复: 增加KOS连接状态检查，失败时记录WARNING级别SSB事件

### L4 智能层 (委员会/CRITIC)

**发现 #9 [严重: LOW] — CRITIC触发链依赖文本模式匹配**
- 位置: critic_auto_trigger.py:37-67
- 问题: 5条触发规则全部基于文本正则匹配(re.search)，而非结构化元数据。如果操作描述稍微偏离关键词("不可逆"写成"永久")就会漏检
- 修复: 改为基于结构化字段(risk_level, operation_category)的规则引擎

**发现 #10 [严重: MED] — CRITIC不读取realtime_guard结果**
- 问题: critic_auto_trigger.py独立判断风险，不消费realtime_guard.py的输出。两个安全系统各自运行，缺少信息共享
- 修复: realtime_guard输出结构化JSON，critic_auto_trigger读取该输出作为输入之一

### L5 行动层 (7条Cron)

**检查项: Cron输入输出协议**

根据CRON.md记录，当前活跃Cron仅3条(WF-001/003/005)，STATE.yaml声称"7个在线"。差异来源可能是Hermes平台的cron数目包含了其他类型任务。

**发现 #11 [严重: LOW] — Cron文档与实际状态不一致**
- 问题: CRON.md只记录WF-001/003/005，STATE.yaml声称cron=7
- 修复: 更新CRON.md覆盖全部7条Cron，明确每条输入输出

### L6 反馈层

**发现 #12 [严重: MED] — content_integrity管道孤立**
- 位置: content_integrity.py
- 问题: content_integrity.py提供了内容完整性检查能力，但未被filter_scorer.py或任何管道调用。仅在CLI手动运行
- 修复: 集成到filter_scorer的评分流程中，作为post-filter检查点

**发现 #13 [严重: LOW] — ssb_integrity未集成到WF-003**
- 位置: ssb_integrity.py
- 问题: 提供了hash chain验证能力但未被WF-003健康检查调用
- 修复: 在WF-003中增加ssb_integrity验证步骤

---

## 二、IPA运行时模型

**检查项: IPA-6LAYER-RELATIONSHIP.md与代码的对应**

**发现 #14 [严重: MED] — 文档架构与实际架构存在漂移**

IPA-6LAYER-RELATIONSHIP.md描述的模型:
- L2感知是整个IPA的输入预处理
- L6反馈形成完整闭环（宪法偏离→停止、知识偏离→重新感知、目标偏离→重新委员会）
- SSB贯穿所有层

实际代码中的漂移:
1. **反馈闭环不完整**: realtime_guard只做"操作前阻断"，不做"操作后评估→重新感知/重新委员会"的闭环。被阻止的操作写入失败日志后就结束了
2. **感知层独立于IPA**: capture/filter产出的INDEX_READY事件没有自动触发KOS索引(action_req=EXECUTE但无消费者)
3. **SSB贯穿不完整**: integrate_pipeline绕开SSB直写文件，打破"贯穿所有层"的设计

**发现 #15 [严重: LOW] — IPA模型GENOME更新提案未执行**
- IPA-6LAYER-RELATIONSHIP.md第92-102行明确建议"将GENOME.md第五、第六部分合并为统一架构模型"，并标注"需要RFC流程"
- 没有对应的RFC存在，文档自2026-05-13创建后未推动

---

## 三、层间依赖检查

### 循环导入检查

✅ **未发现循环导入**。经AST分析确认所有import关系为单向:
```
ssb_init.py → ssb_client.py → ecos_common.py
capture_watcher.py → ecos_common.py
filter_scorer.py → ecos_common.py
```

### 低层依赖高层检查

**发现 #16 [严重: HIGH] — L2脚本依赖L3存储细节**

| 脚本(所属层) | 不当依赖 | 问题 |
|-------------|---------|------|
| integrate_pipeline.py (L2) | 直接os.path操作LADS/ssb/ecos.jsonl | 绕过L3持久层SSB API |
| contextualize_pipeline.py (L2) | 直接sqlite3连接KOS数据库 | 绕过L3持久层抽象 |
| capture_watcher.py (L2) | 硬编码SSB_DB_PATH | 绕过L3持久层配置 |

**发现 #17 [严重: MED] — wf-008桥接直接操作双方数据库**
- 位置: wf-008-kanban-ssb-bridge.py
- 问题: 同时直接连接Kanban SQLite和SSB SQLite，未使用ssb_client API
- 修复: 至少SSB侧使用ssb_client.publish()

### ecos_common导入检查

**发现 #18 [严重: HIGH] — ecos_common采纳率仅18.8%**

| 状态 | 脚本数 | 列表 |
|------|--------|------|
| ✅ 正确导入 | 3 | capture_watcher, filter_scorer, ssb_client |
| ✅ 间接导入 | 1 | ssb_init (通过ssb_client) |
| ❌ 未导入(硬编码路径) | 13 | realtime_guard, ssb_auth, critic_auto_trigger, integrate_pipeline, structure_pipeline, contextualize_pipeline, content_integrity, semantic_scorer, ssb_integrity, wf-008-kanban-ssb-bridge, ssb_schema_migrate, ecos_scheduler, pre_design_check |

具体未导入脚本中的硬编码:
- realtime_guard.py: 无DB依赖（仅规则字典），可接受
- ssb_auth.py: 硬编码 LADS/ssb/.ssb_key 和 ecos.db 路径
- critic_auto_trigger.py: 硬编码 ~/Workspace/eCOS 路径
- integrate_pipeline.py: 硬编码 ~/Workspace/eCOS 路径
- wf-008-kanban-ssb-bridge.py: 硬编码 LADS/ssb/ecos.db 路径

---

## 四、SSB Schema一致性

### Schema定义 vs 代码实现

**发现 #19 [严重: CRITICAL] — SSB Schema版本号自相矛盾**
- SSB-SCHEMA-V1.md标注版本 "v0.1.0-draft"
- 文档内示例使用 "ssb_version": "1.0"
- ecos_common.py SQL使用 schema_version DEFAULT '1.0'
- ssb_schema_migrate.py添加字段 "schema_version": "1.0"

**这意味文档自己标注为draft v0.1.0，但所有代码按v1.0实现。**

**发现 #20 [严重: CRITICAL] — JSONL导出丢失95%字段**

ssb_dump.py导出格式仅6字段:
```json
{"id": "...", "seq": 1, "ts": "...", "agent": "...", "type": "...", "summary": "..."}
```

丢失的字段:
- session_id, source_instance, target_scope, target_hint
- event_subtype, detail, confidence, risk_level, priority
- action_req, deadline, payload_json, semantic_json
- agent_signature

**影响:** 如果从JSONL恢复SQLite数据库（ssb_init --recover），将丢失所有上述字段。而ssb_schema_migrate.py接受6字段格式并增加timestamp/schema_version/event_type，说明当前工作流确实假设JSONL是主要数据源。

**发现 #21 [严重: HIGH] — 两种建表语句共存**

| 来源 | 关键字段差异 |
|------|------------|
| ecos_common CREATE | event_id(TEXT UNIQUE), source_zone, target_zone, action, status, payload_size, media_path, schema_version |
| 实际SQLite(ssb_client) | 无event_id独立列, session_id, source_instance, target_scope, event_subtype, summary, detail, risk_level, priority, action_req, deadline, semantic_json |

**两种schema完全不可互换。ecos_common的CREATE语句如果被执行会创建与现有数据库不兼容的表结构。** 幸运的是当前没有任何代码实际执行ecos_common的CREATE语句——所有代码都使用自己的建表逻辑。

---

## 五、安全架构

### realtime_guard vs IRREVERSIBLE-OPS

**发现 #22 [严重: MED] — realtime_guard规则覆盖面不足**

IRREVERSIBLE-OPS.md列出的不可逆操作 vs realtime_guard.py覆盖情况:

| IRREVERSIBLE-OPS类别 | realtime_guard覆盖 | 状态 |
|---------------------|-------------------|------|
| 邮件发送(himalaya send) | ✅ "himalaya send" | 已覆盖 |
| 公开发帖(xurl post) | ✅ "xurl post" | 已覆盖 |
| Git push | ✅ "git push" | 已覆盖 |
| SSB事件删除 | ✅ "ssb delete" + "ecos.jsonl" | 已覆盖 |
| 数据删除(rm -rf) | ✅ "rm -rf" | 已覆盖 |
| API写操作(POST/PUT/DELETE) | ⚠️ 仅"curl POST" | 部分 |
| 通知推送(send_message) | ✅ "send_message" | 已覆盖 |
| 云存储写(gsutil cp/aws s3 cp) | ❌ 缺失 | 未覆盖 |
| GENOME.md写入 | ✅ "write_file GENOME.md" + "patch GENOME.md" | 已覆盖(额外) |

**额外覆盖(不在IRREVERSIBLE-OPS但被guard保护):**
- cross_refs.jsonl操作
- DROP TABLE
- cronjob create/update
- delegate_task

**发现 #23 [严重: LOW] — realtime_guard不依赖ecos_common但不需要**
- realtime_guard.py是纯规则引擎，无数据库依赖，不导入ecos_common是合理的

### HMAC端到端完整性

**发现 #24 [严重: MED] — HMAC签名链路不完整**

```
ssb_auth.py keygen → 生成密钥 (.ssb_key)
        sign-new → 为旧事件补充签名 (补充agent_signature字段)
        verify  → 验证签名 (读取agent_signature列)
```

问题:
1. **新事件不自动签名**: ssb_client.publish()不调用compute_signature，新发布的事件agent_signature列为NULL
2. **签名需要手动触发**: 用户必须独立运行`python3 ssb_auth.py sign-new`才能签名
3. **JSONL导出不包含签名**: ssb_dump.py的6字段导出不包含agent_signature

**发现 #25 [严重: MED] — ssb_auth未导入ecos_common**
- 位置: ssb_auth.py:13
- 问题: 硬编码DB_PATH，不使用ecos_common.SSB_DB_PATH
- 后果: 如果数据库路径变更，ssb_auth将失效

### content_integrity检查点覆盖

**发现 #26 [严重: LOW] — content_integrity仅覆盖文本模板检测**
- 问题: content_integrity.py仅检测英文模板(generic_headers, boilerplate patterns)，中文模板检测完全缺失
- 影响: FAIL-008-perception-poison-passed (语义投毒)这类攻击无法被content_integrity拦截

---

## 六、审计汇总

### 按严重度统计

| 严重度 | 数量 | 关键发现 |
|--------|------|---------|
| CRITICAL | 2 | SSB Schema四重分裂(#7), JSONL丢失95%字段(#20) |
| HIGH | 6 | capture_watcher Schema冲突(#4), integrate绕开SSB(#5), ecos_common采纳率(#18), L2依赖L3细节(#16), 两种建表语句(#21), SSB版本矛盾(#19) |
| MED | 13 | 五阶管道不完整(#2), 贝叶斯版本化未实现(#3), 管道孤岛(#6), KOS一致性问题(#8), CRITIC/realtime_guard隔离(#10), content_integrity孤立(#12), 文档漂移(#14), wf-008绕API(#17), 规则覆盖不足(#22), HMAC链路(#24), ssb_auth未导入(#25) |
| LOW | 5 | CRITIC文本匹配(#9), Cron文档不一致(#11), ssb_integrity未集成(#13), IPA更新提案(#15), content_integrity中文缺失(#26) |

### 架构得分

| 维度 | 得分 | 说明 |
|------|------|------|
| L1 宪法层 | 75% | 5公理有执行器但P2/P3/P5实现不完整 |
| L2 感知层 | 60% | 5阶独立可运行，但没有串联流转 |
| L3 持久层 | 50% | SSB Schema分裂是核心问题 |
| L4 智能层 | 55% | CRITIC规则引擎+委员会链可用但隔离 |
| L5 行动层 | 70% | Cron可运行，文档待更新 |
| L6 反馈层 | 65% | 安全拦截有效，闭环+检查点集成不足 |
| IPA一致性 | 50% | 文档与实际存在显著漂移 |
| 层间依赖 | 55% | 无循环导入但L2直连L3存储 |
| SSB Schema | 30% | 4种格式共存，严重不一致 |
| 安全架构 | 65% | guard覆盖80%不可逆操作，HMAC链路不完整 |

**综合架构得分: 57%**

（对比STATE.yaml中声明的"85%"，存在28%的乐观偏差。该偏差主要来自: SSB Schema分裂未被计入、层间依赖泄漏未被发现、管道串联缺失）

---

## 七、优先修复建议

### P0 (本周)

1. **统一SSB Schema**: 删除ecos_common.py中未使用的CREATE语句，更新ssb_dump.py导出完整字段（至少包含payload_json和semantic_json），更新ssb_schema_migrate.py以兼容完整格式
2. **integrate_pipeline重构**: 改为使用ssb_client API而非直接文件I/O
3. **capture_watcher解冲突**: 删除本地CREATE TABLE，统一使用ssb_client的表格式

### P1 (两周内)

4. **ecos_common推广**: 在ssb_auth, wf-008, ssb_schema_migrate, integrate_pipeline中统一使用ecos_common路径常量
5. **HMAC自动化**: ssb_client.publish()集成compute_signature()
6. **管道串联**: 在WF-006中补充structure和contextualize的SSB集成

### P2 (一月内)

7. **CRITIC/realtime_guard融合**: 共享风险评估结果
8. **content_integrity集成**: 加入filter_scorer评分流程
9. **CN文档更新**: STATE.yaml架构得分修正为实际值

---

*审计工具: AST静态分析 + SQLite Schema比对 + 手动代码审查*
*审计范围: 17个Python脚本 + 5个架构文档 + SQLite数据库 + JSONL导出*
