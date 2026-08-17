# 正式产物硬门、同源审核继承与医疗保险采访档案

- 更新时间：2026-08-17 13:01:51
- 执行工具 / 模型：Codex (GPT-5.6 Sol)
- 状态：implemented and focused offline validation passed

## 背景证据

`vid-094037/webui-bundle` 同时存在失败的 `transcript-quality-gate.md`、失败的 `smart-summary-quality.md` 和名称看似正式的 `full-transcript.md` / `smart-summary.md`。外部 Agent 可以跳过 VKP 的检查结果，直接读取机器转录并生成成品外观的总结。相同 `video_id=video_c777dbb4ac5a` 的旧 Bundle 已有人工确认人数等审核结果，但新运行未发现或绑定该 lineage。

## CHANGE-RATIONALE-01：正式产物硬门

- 意图：质量失败时，阻止章节 Map、章节修订直接应用、全局 Reduce、整稿 LLM 和手工候选安装写成正式智能总结。
- 决策：新增 `video_knowledge_pipeline.production_artifact_gate.v1`，在三个模型执行入口和 `generate-smart-summary-with-codex --input-md` 前统一判定；失败时返回 `blocked_by_production_artifact_gate`，并记录 `provider_call_performed=false`。
- 理由：检查文件存在但不参与执行授权，无法约束其他 Agent。
- 证据：真实 Bundle 的转录门为 failed，仍可被外部脚本消费；原执行器在 Provider 调用前没有读取该门。
- 生效范围：正式智能总结生成/安装和知识文档导出；不修改原始 ASR、Timeline 或已有人工证据。
- 回滚：删除 production gate 接线即可恢复 legacy 行为；Schema 和门产物本身是只读派生物。

门把状态拆为：`execution_status`、`transcript_quality`、`speaker_review_status`、`semantic_fact_status`、`privacy_status`、`publication_readiness`。执行成功永远不等于发布批准。质量失败时，兼容导出的 `full-transcript.md` / `smart-summary.md` 必须显示 `review-required` 水印，不得继续伪装成成熟成品。

## CHANGE-RATIONALE-02：同源人工审核发现与显式绑定

- 意图：新运行能发现相同源视频的人工纠词、说话人确认、双语字幕、事实和隐私审核。
- 决策：新增 `source_review_lineage.v1`，只接受完整媒体 SHA-256 或 VKP 由 SHA-256 前缀生成的 `video_id`；标题相同不构成同源。发现后先阻断并提示，只有显式 `--apply` 才把路径和 SHA 绑定到当前 manifest。
- 理由：静默复制可能覆盖当前运行，也可能把相似标题的其他视频误当成人工真值。
- 证据：真实新旧 Bundle 的 `video_id` 完全一致，但新 Bundle 的 `review-notes.json` 为空；旧 `speaker-review.json` 只确认 3 人、没有完成角色映射。
- 生效范围：审核 lineage 和上游选择；不复制正文，不覆盖原始 ASR，不把“确认人数”冒充“说话人角色已确认”。
- 回滚：移除 `source-review-lineage.json` 及 manifest 的 `inherited_review_*` 字段即可；源 Bundle 不变。

```powershell
.\scripts\video-knowledge.ps1 source-review-lineage <bundle> --search-root <root>
.\scripts\video-knowledge.ps1 source-review-lineage <bundle> --search-root <root> --apply
```

绑定后每次使用前都会复核 lineage revision、来源身份、人工产物路径和 SHA；任一漂移均 fail-closed。

## CHANGE-RATIONALE-03：医疗保险客户采访档案

- 意图：避免课程模板把个人经历扩写成方法论、医疗建议、保险建议或高频话术。
- 决策：增加显式 `medical-insurance-interview-v1`，强制说话人及角色复核、金额/数字与语义事实复核、隐私复核、个案边界和人工发布批准。
- 理由：采访者问题、假设金额和受访者经历都是事实语义的一部分，不能按课程型总结处理。
- 证据：原章节提示词固定写“课程视频”；全局 Reduce 只用标题是否含“采访”做弱推断。
- 生效范围：转录质量门、章节提示、全局 Reduce 结构、正式产物门；课程档案保持兼容。
- 回滚：把 Bundle 显式改回 `course-or-general-v1`；历史审核产物不会被删除。

```powershell
.\scripts\video-knowledge.ps1 content-profile <bundle> --profile medical-insurance-interview-v1
.\scripts\video-knowledge.ps1 production-artifact-gate <bundle>
```

档案只创建 `needs_human_review` 模板，绝不自动声称审核通过。这里的“事实/金额复核”仅指忠实还原音视频中谁说了什么、数字和否定词是否听对，不做外部医疗或保险事实裁判。采访正文优先使用“事实时间线—受访者原话与感受—已确认信息—待核实事项—隐私与发布边界”；禁止默认生成方法论、面向读者的行动清单、高频话术和可复用表达。

## 兼容边界

- 旧 Bundle 没有转录质量门时，普通课程继续采用 `not_available_legacy_compatible`；严格医疗保险采访档案则按缺失质量证据阻断。
- 普通采访只要求说话人分离；医疗保险采访还要求人工角色绑定。
- 机器草稿仍允许存在，但必须有 `review-required` 水印，不得获得 publication-ready 状态。
- 不调用模型、不上传媒体、不读取密钥；本变更全部是本地控制面和派生审核状态。

## 验证记录

- 2026-08-17 13:32:16，Codex (GPT-5.6 Sol)：门禁、同源 lineage、Schema、CLI、采访结构、知识导出、总结 Map/Reduce、说话人和验收关联回归 `108 passed / 0 failed`。
- 2026-08-17 13:42:07，Codex (GPT-5.6 Sol)：补齐直接 `smart-summary-section-apply` 绕过入口；相关正式安装、Map/Reduce、lineage、导出回归 `92 passed / 0 failed`，其中门禁与直接章节应用专项 `11 passed / 0 failed`。
- Ruff 定向检查：通过；`git diff --check`：通过。
- 真实 Bundle 只读验收：`vid-094037` 返回 `blocked_review_required`，原因精确为 `transcript_quality:failed` 与 `prior_human_review_available_not_bound`；未写生产 Bundle、未调用 Provider。
- 全量离线 pytest：首次 `1743 passed / 8 skipped / 3 failed`。其中本变更造成的 Reduce 3000 字预算失败已修复并复跑通过；剩余 2 项分别来自并发未提交 Provider 预设数量变化，以及本次范围外的既有 DashScope 个人绝对路径，均未混入本提交修复。
