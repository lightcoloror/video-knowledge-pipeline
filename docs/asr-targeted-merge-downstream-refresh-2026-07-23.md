# 局部 ASR 合并后的下游失效与重建

更新时间：2026-07-23 11:59:16
执行工具 / 模型：Codex / GPT-5.6

## 决策

局部 ASR 结果成功写入 `source-arbitrated-transcript.json` 后，VKP 必须自动执行同一条本地下游闭环：

1. 记录修复前、修复后的 canonical transcript SHA-256。
2. 把现有 Smart Summary 标记为失效，并按内容哈希归档旧摘要供审计。
3. 重建完整逐字稿、Smart Summary 输入包、知识笔记和内容候选产物。
4. 复用 `quality-finalize` 的预览模式重建语义章节与章节总结任务，不自动调用模型。
5. 刷新知识覆盖审计和 `review.html`。
6. 重新运行 canonical transcript 质量门和 Smart Summary 质量门。
7. 最后刷新 Quality Console、Task Console 和 Video Workbench。

## 状态语义

- `completed`：本地重建无异常，逐字稿与新摘要的最终质量门都通过。
- `needs_summary_regeneration`：逐字稿质量通过，本地产物已经重建，但仍需通过既有 consent/provider route 生成新摘要。
- `degraded`：本地步骤异常或逐字稿质量门未通过；已成功写回的局部 ASR 不回滚。

`full_pipeline_production_qualified` 只有在逐字稿与摘要两个最终质量门都通过时才为 `true`。

旧摘要不能通过修改时间规避失效。`smart-summary-quality-check` 会比较当前摘要 SHA-256 与
`exports/smart-summary-invalidation.json` 中记录的旧摘要哈希；内容仍相同即返回
`summary_invalidated_after_transcript_update`。

## 稳定入口

局部 ASR 合并默认自动刷新：

```powershell
python -m video_knowledge_pipeline.asr_targeted_retry_merge `
  <bundle> <authorization-plan.json> <execution-report.json> --write
```

只在测试或故障隔离时显式禁用：

```powershell
python -m video_knowledge_pipeline.asr_targeted_retry_merge `
  <bundle> <authorization-plan.json> <execution-report.json> `
  --write --no-refresh-downstream
```

对既有 Bundle 单独补跑：

```powershell
.\scripts\video-knowledge.ps1 refresh-transcript-downstream <bundle>
```

预览而不写入：

```powershell
.\scripts\video-knowledge.ps1 refresh-transcript-downstream <bundle> --no-write
```

## 安全边界

- 编排器不访问网络，不上传文件，不读取 API Key。
- 编排器不会静默启动文本模型，也不会 local/cloud fallback。
- 新 Smart Summary 仍必须经过现有 provider gateway、route revision 和 consent。
- Timeline、Bundle 和 run registry 继续作为现有真源；本次没有新增第二套状态机或审核服务。
- 旧摘要归档只用于审计，不允许作为生产摘要继续发布。

## 产物

- `exports/smart-summary-invalidation.json`
- `exports/smart-summary-invalidation.md`
- `exports/invalidated-summaries/<sha12>-<filename>`
- `transcript-downstream-refresh.json`
- `transcript-downstream-refresh.md`

Manifest 同步记录下游刷新状态、摘要是否需要重生成和整链生产质量状态。
