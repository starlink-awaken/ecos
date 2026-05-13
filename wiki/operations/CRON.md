# Cron 任务

> 当前活跃的自动化工作流

| ID | 名称 | 触发 | 下次运行 | 状态 |
|----|------|------|----------|------|
| WF-001 | KOS 每日索引 | daily 02:00 | 2026-05-14 | scheduled |
| WF-003 | 系统健康检查 | weekly Mon 09:00 | 2026-05-18 | scheduled (last: OK) |
| WF-005 | HANDOFF 自动更新 | every 2h | 2026-05-13 18:00 | scheduled |

## 详情

### WF-001 — KOS 每日索引
- **文件:** `agents/workflows/WF-001-kos-daily-index.md`
- **功能:** 每日增量索引所有 KOS 域
- **静默:** 无异常不推送

### WF-003 — 系统健康检查 + 宪法执行器
- **文件:** `agents/workflows/WF-003-health-check.md`
- **功能:** hermes doctor + GENOME git diff + STATE cron 交叉验证
- **告警:** 发现异常推送通知

### WF-005 — HANDOFF 自动更新
- **文件:** `agents/workflows/` (待补充)
- **功能:** 每2h检查 HANDOFF 是否过期(>4h)，自动更新
- **静默:** <4h不推送

## 运维命令

```bash
# 查看所有 cron
hermes cronjob list

# 手动运行
hermes cronjob run <job_id>

# 暂停/恢复
hermes cronjob pause <job_id>
hermes cronjob resume <job_id>
```
