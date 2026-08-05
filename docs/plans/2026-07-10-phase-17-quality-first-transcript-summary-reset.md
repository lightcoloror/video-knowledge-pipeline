# Phase 17：逐字稿与智能总结质量重置

更新：2026-07-10 09:53:18 | Codex / GPT-5

## 目标

Phase 17 不再以新增模块数量作为进度标准，而是建立可重复评测的质量主线：

```text
独立 ASR / 字幕 / OCR / 打标 / 视觉证据
-> 双 ASR 共识与真实冲突索引
-> 证据支持的局部纠错补丁
-> source-arbitrated-transcript.json
-> 标点、断句和段落化
-> corrected-transcript.json
-> full-transcript.md
-> 语义章节 JSON
-> 章节级 LLM 改写
-> 全局编辑
-> smart-summary.md
```

得到大脑逐字稿和总结只能用于离线评测，不进入 VKP 生产纠错证据。

## 已实现

### 质量优先配置

- 新增默认 `processing_profiles.quality`。
- 主 ASR 为 SenseVoice 快速底稿，第二 ASR 计划为 Qwen3-ASR-1.7B，显存失败时只提示显式改用 0.6B。
- 文本 LLM 可配置为自动执行，但必须同时满足：
  - `data_export_allowed=true`。
  - provider 和运行时凭据可用。
  - 预计调用不超过 20 次。
  - 预计输入不超过 120,000 字符。
- API key 只从运行时参数或环境变量读取，不进入配置、manifest 或报告。

### ASR 与共识

- 新增 Qwen3-ASR 官方 Python 包适配器，模型为 `Qwen/Qwen3-ASR-1.7B` / `0.6B`。
- 强制对齐复用 `Qwen/Qwen3-ForcedAligner-0.6B`。
- 长音频先由 ffmpeg 切为 300 秒单声道 16 kHz 音频块，再逐块识别并恢复全片时间偏移。
- 新增 `asr-consensus`，保留主/次 ASR 原始假设，标出一致、冲突、主 ASR 独有、次 ASR 独有窗口。
- 双 ASR 差异已作为 `secondary_asr` 证据进入语义纠错候选，不允许次 ASR 单独覆盖主稿。
- Fun-ASR-Nano 已作为 benchmark challenger 接入 preset，但只有人工基准胜出后才允许进入默认链路。
- WhisperX 保留为 alignment/diarization 分支，不再描述为第二识别器。

### 人工质量基准

- 新增 `quality-benchmark build/run/report` CLI/MCP。
- build 默认按 3 个 bundle 各 8 段生成 24 段人工标注模板。
- 评测字段包括 CER、标点 F1、句界 F1、实体准确率、数字错误、过度纠错率、时间戳中位/P95 误差。
- 输出 `quality-benchmark.json/md/html`。
- 人工参考稿只用于评测，代码不提供将其导入生产证据链的路径。

### 可验证纠错链

- `transcript-evidence-correction-pipeline --quality-profile quality` 采用事实纠错优先顺序：
  1. 本地后处理和 source arbitration。
  2. 双 ASR、字幕、OCR/ebook、青龙打标、视觉、网页上下文的真实冲突检测。
  3. JSON correction patch 生成、验证和高置信写回。
  4. 事实纠正完成后再运行标点/断句可读化。
- 本地 `agent substitute` 明确标记为 heuristic draft，不再声称是语义 LLM。
- 候选召回完整但 conflict index 未覆盖时，状态改为 `candidate_recall_ready_conflict_index_gap`，不得报 ready。
- `smart-summary` input pack 若仍指向旧 transcript，即使 manifest 已出现新纠正版，也不能通过 corrected-input 门禁。

### 语义章节与总结

- 新增 `semantic-chapter-plan`。
- 章节边界综合 transcript 主题变化、VAD 停顿、章节提示词、青龙标签、OCR/视觉变化。
- 动态章节区间：
  - 20 分钟以内：1–5 分钟。
  - 20–90 分钟：4–10 分钟。
  - 90 分钟以上：6–15 分钟，并增加约 30–60 分钟一级篇章。
- `build-smart-summary-chapters` 默认 `--chapter-mode semantic`；旧固定分桶可显式使用 `--chapter-mode fixed`。
- `run-smart-summary-section-llm-rewrite --auto-from-profile` 在数据外发许可和批量门禁通过时自动逐章改写。
- 全片总结仍只消费章节层和课程地图，不直接把 raw ASR 当最终输入。

### 质量门禁与 UI

- `transcript-quality-gate` 新增可选人工 reference/baseline，对比 CER、实体、数字、过度纠错、音频覆盖和时间戳误差。
- 新增 `quality-console.html/json`，展示双 ASR、冲突、逐字稿门禁、语义章节、章节 LLM 和总结门禁状态。
- 质量页只复制重试命令；不会直接发送材料、调用云模型或改写 timeline。
- task console 和 video workbench 已增加质量页入口。

## CLI 验收入口

```powershell
# 双 ASR 计划
.\scripts\video-knowledge.ps1 plan-asr <workspace> <media> --preset sensevoice
.\scripts\video-knowledge.ps1 plan-asr <workspace> <media> --preset qwen3-asr-1.7b

# 双 ASR 共识
.\scripts\video-knowledge.ps1 asr-consensus <bundle> <sensevoice.json> <qwen3.json>

# 建立 24 段人工基准
.\scripts\video-knowledge.ps1 quality-benchmark build <output-dir> --bundle-dirs "<bundle1>,<bundle2>,<bundle3>"
.\scripts\video-knowledge.ps1 quality-benchmark run <output-dir>\quality-benchmark-manifest.json

# 质量纠错与语义章节
.\scripts\video-knowledge.ps1 transcript-evidence-correction-pipeline <bundle> --quality-profile quality
.\scripts\video-knowledge.ps1 semantic-chapter-plan <bundle> --chapter-mode semantic
.\scripts\video-knowledge.ps1 build-smart-summary-chapters <bundle> --chapter-mode semantic

# 配置允许时自动章节改写；大批量仍停在 preflight
.\scripts\video-knowledge.ps1 run-smart-summary-section-llm-rewrite <bundle> --auto-from-profile

# 静态质量页
.\scripts\video-knowledge.ps1 export-quality-console <bundle>
```

## 当前未完成的真实验收

- Qwen3-ASR-1.7B 已缓存并完成 24/24 样本的 CPU `bfloat16` 独立识别；GPU 仍因 Windows `os error 1455` 无法加载。Qwen3-ASR-0.6B 与 ForcedAligner 尚未完成同一基准验收，因此仍不切换默认模型。
- 24 段人工真值模板已实现，但真实 3 个视频的人工校对尚未完成，因此不能声称 CER 降低 20% 或实体/数字错误降低 30%。
- Fun-ASR-Nano 仍是 challenger，没有 benchmark 胜出证据。
- 章节级 LLM 自动执行默认因 `data_export_allowed=false` 被阻止；这是预期安全状态，不是 provider 故障。
- 只有人工基准和 3 个完整视频盲评达标后，才允许把 Qwen3-ASR 双识别和新总结链切换为已验收生产默认。

## 源码复用依据

- Qwen3-ASR：复用官方 `Qwen3ASRModel.from_pretrained`、`transcribe` 和 ForcedAligner 接口，不自行实现推理/对齐。
- Chapter-Llama：参考其 ASR 引导章节生成方式，只吸收章节规划边界，不复制完整应用。
- CoE：参考事件链、实体一致性和分层评估方式，当前用于总结质量设计，尚未嵌入其完整评估器。
- 真实源码审查位置：
  - `%WORKSPACE_ROOT%\tool-source-review\Qwen3-ASR`
  - `%WORKSPACE_ROOT%\tool-source-review\CoE`
  - `%WORKSPACE_ROOT%\tool-source-review\Chapter-Llama-HF`
## 2026-07-12 09:05:00 | Codex GPT-5 checkpoint

### Boundary and human-reference correction

- Replaced fixed-duration/postprocessed-cue boundary trust with local FunASR fsmn-vad evidence.
- Added funasr_vad_runner.py; it reuses the installed FunASR AutoModel and cached local VAD model.
- Rebuilt the 24-sample benchmark under openclaw-runs/quality-benchmark-phase17-20260710/benchmark-vad-v1/.
- Verified sample_count=24, audio_clip_count=24, window_alignment_ready=true, and all 24 boundary sources are funasr_fsmn_vad.
- The previous transcript timestamps were estimated from untimed SenseVoice text and could not prove utterance boundaries. This was the cause of several clips ending in the middle of continuous speech.

### Review-text prefill

- Each of the 24 VAD-aligned clips was rerun locally with SenseVoice on CUDA.
- 24/24 samples now use draft_source=sample_clip_sensevoice_full_punc.
- The review page contains 24 audio controls, 24 editable textareas, video timestamp jumps, and mutual pause logic between video and clip audio.
- Batch execution now writes a manifest checkpoint after every attempted sample and refreshes the static review HTML after completion.

### Qwen3-ASR checkpoint

- Qwen3-ASR 1.7B is present at %LOCAL_MODEL_ROOT%\models\Qwen3-ASR-1.7B.
- Benchmark execution disables inline forced alignment so recognition and alignment are separate memory stages.
- Even with low_cpu_mem_usage=true, max_inference_batch_size=1, and no ForcedAligner, model loading still fails with Windows os error 1455 (page file too small).
- This failure is explicit in candidate_run_failures; no silent fallback or default-model switch occurs.
- Qwen3-ASR 0.6B is not currently cached locally. Network/model download remains outside this checkpoint.

### Verification

- 28 passed in 7.46s across Phase 17 benchmark, VAD boundary, clip prefill, Qwen staged-plan, SenseVoice, Faster-Whisper, WhisperX, and runtime-profile tests.
- git diff --check completed without whitespace errors.
- Current benchmark status remains needs_human_reference; the old 24 annotations are retained as legacy comparison only because the new VAD windows differ.
### Measured draft change

- Old aligned-v2 drafts: punctuation density 55.17 per 1000 characters; boundary source was not recorded and readiness was based on generated transcript cue edges.
- New VAD benchmark drafts: punctuation density 91.60 per 1000 characters; 24/24 boundaries are backed by funasr_fsmn_vad and 24/24 drafts come from the actual extracted clip.
- This is a measurable readability and boundary-provenance improvement, but it is not yet a CER improvement claim. CER still requires the updated human references.

## 2026-07-12 10:04:55 | Codex GPT-5 checkpoint

### Independent double-ASR benchmark

- Qwen3-ASR-1.7B completed 24/24 VAD-aligned sample clips using explicit CPU `bfloat16` fallback.
- SenseVoice full+punc and Qwen3-ASR-1.7B are preserved as independent hypotheses; neither overwrites the other.
- The benchmark report now contains per-sample disagreement evidence and a prioritized review queue.
- Current mean normalized edit ratio between the two hypotheses is `0.030951` across 24 samples.

### Numeric-conflict noise reduction

- Added unit-aware comparison for Arabic and Chinese numeric forms.
- Equivalent forms such as `两百万元` and `200万元`, or `二四年` and `24年`, no longer create false numeric conflicts.
- Real conflicts such as `200万元` versus `300万元` remain high priority.
- On the real 24-sample benchmark, high-priority numeric conflicts decreased from 12 to 9 without suppressing genuine differing values.

### Verification

- `32 passed in 8.32s` across the focused Phase 17 benchmark and ASR set; the full repository regression after shared production integration also passed: `498 passed in 136.74s`.
- Python AST parsing passed for the changed benchmark and runner modules.
- `git diff --check` passed with only existing LF/CRLF conversion warnings.
- Benchmark status remains `needs_human_reference`: all 24 old annotations are retained as editable legacy seeds, but the corrected VAD-aligned windows still require confirmation before CER can be claimed.
- Summary blind review remains `0/3`; no smart-summary quality claim is made yet.
### Production correction integration

- Extracted the unit-aware numeric logic into `numeric_normalization.py` and reused it in both `quality_benchmark.py` and `transcript_semantic_correction.py`.
- Fixed compound-unit tokenization so `200万元` remains one fact value instead of being truncated to `200万`.
- OCR/visual/subtitle evidence wrappers such as `课件`, `画面`, `字幕`, `显示`, and `讲师` are now ignored as candidate terms.
- Production semantic correction no longer creates a visual conflict for equivalent forms such as `两百万元` versus `200万元`, while `两百万元` versus `300万元` still creates a number correction candidate.
- Focused production tests: `74 passed`; final full regression: `498 passed in 136.74s`.
## 2026-07-12 10:24:29 | Codex GPT-5 checkpoint

### Boundary-extension review seed

- Added a review-only merge stage for the rebuilt VAD windows.
- When legacy human text aligns with the current punctuated clip ASR, the editable seed keeps the legacy corrected span and adds only the ASR prefix/suffix outside it.
- When alignment is too weak, the editable seed uses the complete current clip ASR; the legacy human text remains available in a separate comparison panel and is not mixed automatically.
- No generated seed is counted as human reference until the reviewer exports it as `reference_text`.

### Real 24-sample result

- `20/24` samples use `legacy_reference_plus_boundary_asr`.
- `4/24` samples use `current_clip_asr_with_legacy_unmerged`.
- `24/24` samples have editable prefilled text, playable clip audio, source-video navigation, SenseVoice/Qwen comparison, and the legacy annotation panel.
- The benchmark remains correctly blocked at `needs_human_reference`; this change reduces review effort but does not manufacture CER evidence.

### Verification

- Focused review-seed tests: `19 passed`.
- Full repository regression: `500 passed in 109.83s`.
- The regenerated review page contains 24 textareas, 20 safe-merge notices, 4 full-ASR fallback notices, and 24 legacy-reference panels.
## 2026-07-12 10:42:16 | Codex GPT-5 checkpoint

### Three-video anonymous summary review

- Added `summary_blind_review.py` with local build, anonymous scoring export, private label mapping, and score application.
- The review compares three roles for each video: old VKP baseline, current improved VKP candidate, and Get笔记 external reference.
- Public A/B/C content removes model names, product names, generation metadata, artifact indexes, and Windows absolute paths.
- Get笔记 remains evaluation-only and is never imported into transcript correction or production evidence.
- Applying scores refreshes `quality-benchmark.json/md/html` and records both candidate-minus-baseline improvement and candidate-to-reference readability gap.

### Interfaces

```powershell
.\scripts\video-knowledge.ps1 quality-benchmark build-summary-review <quality-benchmark-manifest.json>
.\scripts\video-knowledge.ps1 quality-benchmark apply-summary-review <summary-blind-review.private.json> --scores-json <summary-blind-review-scores.json>
```

MCP uses `quality_benchmark(action="build-summary-review")` and `quality_benchmark(action="apply-summary-review", scores_json=...)`.

### Real artifact and verification

- Real review page: `openclaw-runs/quality-benchmark-phase17-20260710/benchmark-vad-v1/summary-blind-review.html`.
- It contains 3 video items, 9 anonymized versions, and 54 criterion selectors.
- Public HTML contains no `SenseVoice`, `得到大脑`, `%WORKSPACE_ROOT%`, or artifact-source headings.
- Focused CLI/MCP/review tests: `47 passed`.
- Full repository regression: `502 passed in 120.51s`.
- Playwright browser launch was unavailable in the managed process (`spawn EPERM`); static DOM contract validation passed. No long-lived service was started.

## 2026-07-13 07:00:03 | Codex GPT-5 checkpoint

### Qwen3 ForcedAligner runtime closure

- Root cause was isolated to the upstream local-path decoder: `normalize_audios()` called `librosa.load()` on Windows and remained CPU-bound for minutes, while the same WAV loaded through `soundfile.read()` in about 0.1 seconds.
- VKP now extracts mono 16 kHz WAV as before, reads it with SoundFile, and passes the official `(numpy.ndarray, sample_rate)` input to `Qwen3ForcedAligner.align()`.
- Direct 1-second smoke returned `hello` at `0.00-0.24s`.
- The 10-second mixed-language smoke returned `hello / 大 / 家 / 好` at `0.98-1.94s`.
- The formal `plan-asr -> run-asr-plan` path completed with `cuda:0`, `bfloat16`, `sdpa`, timestamp coverage `1.0`, and monotonic timestamps.
- Runtime artifact: `%WORKSPACE_ROOT%\qwen-aligner-integration-smoke\transcripts\asr_run_9127eb1a3e8d\raw-asr-output.json`.
- Remaining benchmark boundary: these smokes prove runtime capability, not the 24-sample median/P95 timestamp target.

### Semantic Map to Global Reduce closure

- Removed whole-prompt tail truncation, which could silently remove late chapters from long videos.
- Over-budget prompts now allocate content budget per semantic chapter while preserving every chapter ID, title, time range, and head/tail evidence.
- The result reports `full_input_chars`, `all_sections_included`, `prompt_within_budget`, and `clipped_section_ids`.
- If chapter metadata alone cannot fit the configured budget, execution stops with `blocked_reduce_input_budget`; it never drops late chapters to force a call.
- Regression fixture reduced 8,311 input characters to 2,899 under a 3,000-character budget while retaining all six chapter IDs, the first chapter opening, and the final chapter ending.

## 2026-07-13 11:27:00 | Codex GPT-5 checkpoint

### 字符锁定标点与断句 A/B

- 24 段基线继续采用 SenseVoice full + ct-punc。
- 第二次本地标点模型使 punctuation F1 从 `0.642910` 降至 `0.604538`，sentence-boundary F1 从 `0.480581` 降至 `0.371801`，不晋级。
- stripped-input Codex 标点候选降至 `0.261392 / 0.131489`，不晋级。
- 保留基线字符的 Codex 候选保持 CER 不变，punctuation F1 `0.665597 -> 0.653716`，sentence-boundary F1 `0.509095 -> 0.509858`，净收益不足，不晋级。
- 结论：保留 SenseVoice + ct-punc，不以“新增了模块”代替质量证据。

### 实体词库、别名、拼音混淆与动态热词

- 仲裁同时兼容 `canonical/aliases` 与 `canonical_term/raw_mentions`。
- 经确认的两字以上中文别名可以高置信归一化，例如 `米娅/名娅 -> 明亚`；单字别名、仅拼音相似、动态词和 `review_required` 词不得自动写回。
- 本地获客领域词库包含已由本地来源确认的 `明亚领航计划`、`明亚保险`、`明亚`、`王彩娥`、`趣研学`、`小红书`。Get笔记评测文本不进入生产词库。
- ContextualParaformer 热词在 24 段中改善 5 段、19 段不变、0 段恶化，但总 CER 仍差于 SenseVoice，因此只作为已知实体定向复听器。

### 双 ASR 剩余真实冲突

- 排除同一 ASR 的 corrected/normalized/SRT/timeline 派生副本；等价 JSON/SRT 去重，timeline ASR 只作无文件转写时的 fallback。
- 24 段中，`200` 个原始差异过滤为 `158` 个真实内容差异，聚合为 `133` 个复核簇。
- 自动排除：语气词等价 20、数字格式等价 12、实体词库已解 10。
- 产物：
  - `openclaw-runs/quality-benchmark-phase17-20260710/benchmark-vad-v1/aligned-human-review-20260712/quality-benchmark-residual-conflicts.json`
  - `openclaw-runs/quality-benchmark-phase17-20260710/benchmark-vad-v1/aligned-human-review-20260712/quality-benchmark-residual-conflicts.md`
  - `openclaw-runs/quality-benchmark-phase17-20260710/benchmark-vad-v1/aligned-human-review-20260712/quality-benchmark-residual-conflicts.todo.json`

### 三视频纠正版总结与匿名盲评

- 三份候选总结由纠正版逐字稿候选生成，压缩率分别为 `20.11%`、`16.04%`、`19.70%`；均覆盖完整视频时长并保留视觉证据不足边界。
- 正式盲评比较旧 VKP、改进候选和 Get笔记外部对照。Get笔记是原“得到大脑”更名后的产品，始终仅用于评测。
- 独立评分任务只读取公开 A/B/C JSON，未读取 private mapping。

| 视频 | 旧 VKP | 改进候选 | Get笔记对照 | 胜出 |
| --- | ---: | ---: | ---: | --- |
| 首次沟通高频问题 | 1.666667 | 4.500000 | 3.666667 | 候选 |
| 活动获客 | 1.833333 | 4.666667 | 3.000000 | 候选 |
| 小红书获客闭环 | 1.833333 | 4.833333 | 3.333333 | 候选 |

- 候选相对旧 VKP 平均提升 `+2.888889/5`，超过 `+0.5` 目标。
- Get笔记可读性差距为 `0.0`，低于 `0.3` 上限；候选平均可读性领先 `+1.333333`。
- 正式产物：
  - `openclaw-runs/quality-benchmark-phase17-20260710/benchmark-vad-v1/aligned-human-review-20260712/summary-phase17-blind-manifest.json`
  - `openclaw-runs/quality-benchmark-phase17-20260710/benchmark-vad-v1/aligned-human-review-20260712/summary-phase17-blind-20260713/summary-blind-review.html`
  - `openclaw-runs/quality-benchmark-phase17-20260710/benchmark-vad-v1/aligned-human-review-20260712/summary-phase17-blind-20260713/summary-blind-review-scores.json`
  - `openclaw-runs/quality-benchmark-phase17-20260710/benchmark-vad-v1/aligned-human-review-20260712/summary-phase17-blind-20260713/summary-blind-review-result.md`

### 最终验证

- 全量回归：`569 passed, 1 warning in 137.70s`。
- `git diff --check` 通过，仅有既有 LF/CRLF 转换提示。
- Git 未跟踪视频、音频、字幕、`openclaw-runs` 或 `real-tests` 产物。
- secret scan 只命中占位符和扫描示例，未新增真实密钥。
