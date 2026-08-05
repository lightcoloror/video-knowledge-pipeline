# Smart Summary 人工关键点审核写回

- 更新时间：2026-07-28 21:28:42
- 执行工具 / 模型：Codex（GPT-5.6）
- 状态：已实现并完成离线 focused 回归

## 结论

VKP 复用现有 `review.html → loopback review service → bundle write lock`
链路，增加了独立的 Smart Summary 人工关键点写回。审核者必须明确勾选
“本段是总结必须覆盖的关键点”，再点击“保存到 VKP”，该条目才会写入
`exports/human-key-points.json`。模型候选、自动摘要和普通审核备注都不能自行
成为人工 goldset。

这条链路同时保持以下来源忠实边界：

- `活医保 → 佛医保`
- `送了一外险 → 送了意外险`
- `根情况来的嘛 → 根据情况来的嘛`
- `民亚保险 → 明亚保险`
- 上述纠正只在人工确认后应用，不作为跨录音全局替换规则。
- 总结任务只还原音视频中表达的原意；不把外部事实核查混入来源忠实度质量门。
- 最终逐字稿必须保留不同说话人的标签；没有可靠角色证据时保留
  `说话人1 / 说话人2`，不猜测姓名或身份。

## 变更 1：复用既有审核 UI 和本地写回服务

- 意图：让审核者在播放视频、跳转时间戳和修正逐字稿的同一界面选择总结关键点。
- 决策：在既有时间线卡片中增加关键点确认、关键点原意和显式语义别名字段；
  继续复用浏览器 `localStorage` 草稿、CSRF、Bundle revision 和“保存到 VKP”按钮。
- 理由：避免再造第二套审核 UI、服务或状态机，也避免把模型摘要当成人工标准答案。
- 证据：
  - `src/video_knowledge_pipeline/lecture_package.py`
  - `src/video_knowledge_pipeline/review_http.py`
  - `src/video_knowledge_pipeline/review_writeback.py`
- 生效范围：仅本地审核元数据；不调用模型、不上传文件、不改 provider 路由。

## 变更 2：显式人工确认生成独立 goldset

- 意图：为 Smart Summary 的“人工关键点召回率”提供独立、可追溯的标准答案。
- 决策：只有 `human_key_point_confirmed=true` 且绑定有效 Timeline index、
  非空关键点文字的行才写入；条目记录时间范围、Timeline evidence ID、
  ASR segment ID、Timeline 与规范化逐字稿的 SHA-256。
- 理由：候选事实或模型输出不能评估自己；人工 goldset 必须与源证据独立绑定。
- 证据：
  - `src/video_knowledge_pipeline/human_keypoint_review.py`
  - `src/video_knowledge_pipeline/smart_summary_keypoint_eval.py`
  - `src/video_knowledge_pipeline/retrieval_goldset.py` 中既有
    `human_confirmed + source SHA` 模式
- 生效范围：`exports/human-key-points.json` 和 Manifest 中对应指针；
  不覆盖 Timeline、逐字稿或 Smart Summary 正文。

## 变更 3：普通审核保持向后兼容

- 意图：新增人工关键点功能不能阻断原有逐字稿、OCR 或视觉审核。
- 决策：审核 payload 没有明确确认的关键点时，关键点写回立即返回
  `not_updated`，不读取或校验无关 goldset。
- 理由：可选质量评估资料不应成为普通审核流程的新强制依赖。
- 证据：
  - `test_non_keypoint_review_is_a_noop_even_with_unrelated_bad_goldset`
- 生效范围：所有未填写人工关键点的既有审核 payload，行为保持不变。

## 变更 4：说话人和来源原意优先

- 意图：最终逐字稿和总结准确呈现谁说了什么，而不是产出无来源角色的润色稿。
- 决策：ASR / diarization 的 speaker 字段沿分段、纠错、导出全链保留；
  人工纠错只能改文字，不能跨 speaker 边界合并。来源中的观点按“说话人表达”
  保留，不额外判断其现实真伪。
- 理由：这次任务是录音内容还原；外部事实核验是另一种可选任务，不能污染
  source-fidelity 评价。
- 证据：
  - `src/video_knowledge_pipeline/transcript_speakers.py`
  - `tests/test_transcript_speaker_source_fidelity.py`
  - `tests/test_speaker_final_reading_export_e2e.py`
- 生效范围：逐字稿、章节摘要输入、最终合并阅读文档；无可靠映射时只使用匿名
  speaker ID。

## 变更 5：最终阅读文档采用已确认人工修正

- 意图：让审核页已正式保存的整段逐字稿修正真正进入最终合并阅读文档。
- 决策：reader 投影依次选择 `human_corrected_transcript`、审核 payload 修正、
  规范化 canonical 文本；机器原稿和 canonical JSON 均不被覆盖。
- 理由：人工确认应影响交付阅读稿，同时机器证据仍需保留以供审计和回滚。
- 证据：`test_apply_review_notes_roundtrip_preserves_machine_outputs_and_exports`。
- 生效范围：最终 reader Markdown 的“说了什么”；不改变 ASR、Timeline、模型输出、
  provider、授权或上传状态。

## 验证

执行：

```powershell
$env:PYTHONPATH='src'
python -m pytest -q -p no:cacheprovider `
  tests\test_human_keypoint_review_writeback.py `
  tests\test_review_writeback.py `
  tests\test_smart_summary_keypoint_eval.py `
  tests\test_transcript_speaker_source_fidelity.py `
  tests\test_speaker_final_reading_export_e2e.py `
  --basetemp .local\test-tmp\human-keypoint-review-20260728a
```

结果：`23 passed, 1 warning`。警告来自 Jieba 对已弃用
`pkg_resources` API 的第三方依赖，不影响本次断言。

扩大后的审核、speaker 边界、reader 与知识导出回归：`73 passed, 1 warning`。
两组无重复用例合计 `96 passed`；没有调用模型、网络或上传。
