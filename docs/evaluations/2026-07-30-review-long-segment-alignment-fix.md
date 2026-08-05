# 审核页长逐字稿分段安全对齐结论

- 更新时间：2026-07-30 23:40:00
- 执行工具 / 模型：Codex（GPT-5.6）
- 状态：严格安全门已确认；撤销不可靠的长段文本匹配例外

## 变更记录

- 意图：让审核卡片只显示能由时间范围可靠绑定的 canonical 逐字稿，避免把跨越多个视觉窗口的长 ASR 段误挂到局部画面。
- 决策：必须先通过 temporal overlap reliability，再允许文本匹配参与选择；不再使用“文本相似即可跨越时间门”的例外。
- 理由：10–30 秒 canonical cue 可能同时覆盖多个 2–4 秒视觉窗口。仅凭局部文本包含关系无法证明整段内容属于某一张审核卡片，会制造错误的时间戳和证据归属。
- 证据：正向、反向、canonical coverage 与 workflow refresh 共 8 项离线回归通过；三条真实 Bundle 的安全对齐数为 22/73、74/80、72/80。
- 生效范围：审核 HTML 的 canonical transcript 投影与跳转起点；不修改 Timeline、canonical transcript、ASR 分段、Smart Summary、生产 Bundle、模型路由或授权。

## 安全结果

| Bundle | Timeline 项 | 可靠 canonical 对齐 | 明确缺失 |
|---|---:|---:|---:|
| `3-scheme-principles` | 73 | 22 | 51 |
| `2-scheme-explanation-closing` | 80 | 74 | 6 |
| `1-customer-trust` | 80 | 72 | 8 |

此前试验性“长段文本匹配例外”会把第一条提高到 53/73，但其中 31 项没有足够精确的时间边界证明，属于假阳性风险，因此不能作为生产结果保留。

## 验证

`tests/test_review_long_segment_alignment.py`、`tests/test_review_canonical_transcript.py`、`tests/test_review_html_canonical_coverage.py`、`tests/test_lecture_workflow_canonical_review_refresh.py` 的定向离线回归为 `8 passed`；语法/未定义名称 Ruff 硬检查与 `compileall` 通过；完整离线回归为 `1526 passed, 3 skipped, 1 warning`。

## 后续最小补强

复用现有词级或字符级时间戳，把长 cue 切为带 `source_segment_ids` 的局部只读投影；无法精确切分的 51 项继续标记 `canonical_alignment_missing`，仅允许局部人工听审，不在显示层猜测。

## 2026-07-31 词时间戳局部投影增量

- 更新时间：2026-07-31 01:10:00
- 执行工具 / 模型：Codex（GPT-5.6）
- 意图：让跨越多个短视觉窗口的长 canonical cue 在已有词时间戳时安全进入审核页，减少人工逐段听审。
- 决策：复用 VKP 既有 `read_asr_word_timestamps`；只有词序列规范化后与完整 canonical cue 完全一致，才按词中点把局部词分配给视觉窗口，并保留 `review_transcript_source_segment_ids`。没有词时间戳、时间戳不完整或词序列与 canonical 文本不一致时继续 fail-closed。
- 理由：词级时间证据可以证明局部话语的实际发生时间；文本相似或宽松时间重叠不能提供同等级证明，也不能替代对纠正后 canonical 文本的完整性检查。
- 证据：正向局部投影、缺失时间戳和不完整词序列反例均通过；审核、canonical coverage、review session 与 knowledge export 关联离线回归 `69 passed`，语法硬检查与 compileall 通过。
- 生效范围：只读审核页的 transcript excerpt、跳转起点和来源片段 provenance；不修改 canonical transcript、原始词时间戳、Timeline、Smart Summary、生产 Bundle 或模型路由。

当前三条历史验收 Bundle 的 canonical 文件均未携带词时间戳，因此安全对齐计数仍为 `22/73`、`74/80`、`72/80`。这不是回归；要改善旧 Bundle，必须先通过本地 ForcedAligner 生成并注册完整 sidecar，不能退回文本猜测。
