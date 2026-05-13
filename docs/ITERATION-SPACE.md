# eCOS Phase 1 — 剩余迭代空间

> 2026-05-13 | 基于: 场景验证+红蓝对抗+架构审视

---

## 未实现的设计 vs 当前状态

```
GENOME 定义                              Phase 1 实现

L2 感知层 五阶管道                        ❌ 未实现
  Capture→Filter→Structure→               KOS索引器承担了Structure角色
  Contextualize→Integrate                 但Capture/Filter/Integrate缺失

L6 反馈层 宪法执行器                       ⚠️ 部分实现
  三类稳态监控                             仅WF-003(每周), 非实时
  宪法执行器                               仅git diff, 无操作前hook

SSB Event Schema v1                       ⚠️ 设计完成
  10种Event                               0种在生产中使用
                                          退化为文件读写(STATE+HANDOFF)

Agent委员会                                ⚠️ 三角模式可用
  完整8角色                                仅Phase1三角, 非真正多Agent

Workflow                                  ⚠️ 2/5上线
  WF-001 每日索引 ✅
  WF-002 Minerva研究 ❌
  WF-003 健康检查 ✅
  WF-004 委员会决策 ❌
  WF-005 HANDOFF自动 ❌
```

---

## 迭代空间

### I3: 感知层实现 (L2 — 最大空白)

```
当前: KOS直接索引原始文件，无预处理管道
      Minerva报告直接落盘，无质量过滤

空间:
  □ I3.1 Capture钩子: Minerva报告产出后自动触发质量评分
  □ I3.2 Filter规则: 低质量报告(<60分)标记但不索引
  □ I3.3 Structure标准: 统一所有入库文档的metadata schema
  □ I3.4 Contextualize: 新文档自动关联已有实体/项目
  □ I3.5 Integrate: 跨域语义链接(如gongwen中政策 ↔ guozhuan中平台)

价值: 高 — 这是GENOME P2"降熵"的核心实现
成本: 中 — 需要KOS索引器扩展
```

### I4: Workflow 补全

```
□ WF-002 Minerva定期深度研究
   触发: cron weekly
   内容: 自动研究预设主题(数字化平台/医疗信息化/AI趋势)
   产出: 自动落盘→KOS索引→摘要推送
   价值: 高 — 知识库自动增长

□ WF-004 委员会决策会议
   触发: manual(高风险决策时)
   流程: CHAIR→EXEC→AUDIT三角模式
   产出: ADR+决策记录
   价值: 中 — 标准化决策流程

□ WF-005 HANDOFF自动更新
   触发: 会话结束/每隔N小时
   流程: 读STATE→生成HANDOFF→归档旧版→写入新版
   产出: 永不过期的HANDOFF
   价值: 高 — 解决最大执行纪律问题(P1)
```

### I5: 安全深化 (红蓝对抗遗留)

```
□ I5.1 Cron修改确认
   当前: cronjob update 无需人类确认
   修复: WF-003检测cron变更→异常→推送确认
   价值: 高 — 防御A6攻击

□ I5.2 KOS trust_level利用
   当前: trust_level字段存在但未使用
   改进: Minerva报告(trust=auto)→低权重
         用户文档(trust=managed)→高权重
         搜索结果按trust_level排序
   价值: 中 — 防御A5知识投毒

□ I5.3 MCP调用日志
   当前: 无结构化日志
   改进: 所有MCP调用→SSB Event日志→审计
   价值: 中 — L0-02可追溯

□ I5.4 STATE自动快照
   当前: 手动更新STATE
   改进: WF-005或cron定期自动快照→git commit
   价值: 中 — 审计链完整性
```

### I6: 体验优化

```
□ I6.1 KOS FTS5 OR模式
   当前: 仅AND语义
   改进: kos-mcp-server.py 加 match_mode参数
   价值: 高 — 中文搜索可用性提升50%+

□ I6.2 Minerva语义搜索填充
   当前: semantic_search返回空
   改进: 填充LanceDB嵌入→启用向量搜索
   价值: 中 — 语义级搜索

□ I6.3 研究质量自动评估
   当前: Minerva报告 quality_score=N/A
   改进: 启用quality_gate stage→质量评分
   价值: 低 — 锦上添花
```

---

## 优先级矩阵

```
                    影响力
                高          中          低
           ┌──────────┬──────────┬──────────┐
      高   │ I4.WF005 │          │          │ 先做
           │ HANDOFF  │          │          │
费         │ 自动     │          │          │
      ─────┼──────────┼──────────┼──────────┤
      中   │ I3.1-3.5 │ I5.1     │ I5.2     │
用         │ 感知层   │ Cron确认 │ trust    │
           │ I6.1     │ I5.4     │          │
      ─────┼──────────┼──────────┼──────────┤
      低   │ I4.WF002 │ I4.WF004 │ I6.3     │
           │ 定期研究 │ 委员会   │ 质量评估 │
           └──────────┴──────────┴──────────┘
```

---

## 建议执行顺序

```
本周:    I4.WF005 HANDOFF自动更新 (解决P1最大痛点)
         I5.1 Cron修改确认

下周:    I6.1 KOS FTS5 OR模式
         I4.WF002 Minerva定期研究

本月:    I3 感知层基础实现 (Capture+Filter)
         I5.2 trust_level利用
```

---

*与 CONCLUSIONS-AND-PLAN.md 四迭代路线对齐*
