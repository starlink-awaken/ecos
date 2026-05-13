# ADR-007: Minerva 研究报告通过独立 KOS Zone 索引

- **状态**: 已接受
- **日期**: 2026-05-13
- **决策者**: 夏铭星 + Hermes/deepseek-v4-pro
- **关联**: FAIL-20260513-003, FAIL-20260513-005, STATE.yaml P3

## 背景

场景验证发现 Minerva 研究产出 (~/knowledge/reports/, 449份报告) 无法通过 KOS 搜索。根因是 KOS minerva zone 仅索引 ~/Workspace/minerva/，不覆盖 reports 目录。

尝试 symlink 方案：`~/Workspace/minerva/reports → ~/knowledge/reports`，但 KOS 索引器使用 `Path.rglob("*")`，不跟随 symlink。

## 决策

在 KOS workspace-manifest.json 中新增独立的 zone + domain 对：

```json
zones.minerva_reports = {
    "absolutePath": "/Users/xiamingxing/knowledge/reports",
    "role": "source",
    "indexable": true,
    ...
}
domains.minerva_reports = {
    "zoneId": "minerva_reports",
    ...
}
```

## 理由

1. KOS manifest 每个 zone 只支持单 `absolutePath`，无法在原 zone 上加多路径
2. 独立 zone+domain 是最小侵入方案——不改变现有 minerva zone 行为
3. WF-001 cron 每日索引自动覆盖新 zone
4. 语义清晰：`domains=minerva_reports` 专门搜索研究报告

## 被否决的方案

| 方案 | 否决理由 |
|------|----------|
| Symlink | KOS 索引器 `rglob` 不跟随 symlink |
| 修改 Minerva 输出路径 | 改上游代码，维护负担 |
| 合并两个目录到父级 | 无共同父目录 |
| 修改 KOS 索引器支持 symlink | 改动大且可能是安全设计 |

## 后果

- 正面: 449份报告立即可搜索，未来产出自动覆盖
- 中性: KOS 域从 6 增至 7
- 风险: 需重启 Hermes 刷新 MCP manifest 缓存

## 验证

重启后 `mcp_kos_search_knowledge(domains="minerva_reports", query="多模态")` → 3条命中 ✅

## 备份

原始 manifest 备份: `workspace-manifest.json.bak.20260513`
