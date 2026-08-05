# VKP ASR 与转写质量主路线（2026-07-08）

## Update Record

- 2026-07-09 23:55:00 | Codex / GPT-5：新增 `readable-transcript-llm-polish` 可选文本 LLM 层，preview-first，显式执行、显式 promote；只处理标点/断句/段落化，不负责事实纠错。
- 2026-07-08 18:25:00 | Codex / GPT-5：落实 SenseVoice/FunASR 完整模式、postprocessed transcript 默认前置、evidence-conflict-index、WhisperX alignment 边界和 5 分钟 ASR A/B 计划。
- 2026-07-08 19:35:00 | Codex / GPT-5：补充 ct-punc 模型缓存门禁、SenseVoice 富标签清洗、重复标点规范化，并重跑 5 分钟样本验证 full+punc 输出。
- 2026-07-08 19:40:00 | Codex / GPT-5：接入 Dolphin 本地 runner 与归一化 adapter；A/B 计划不再把 Dolphin 当占位，未安装时返回 `asr_module_not_ready`。
- 2026-07-08 19:43:00 | Codex / GPT-5：新增 `asr-ab-compare`，把 A/B 运行结果转成主 ASR/第二 ASR/云 ASR 的决策报告，避免只产出 transcript 没有引入判断。
- 2026-07-08 19:53:00 | Codex / GPT-5：修复 OpenAI-compatible ASR URL 拼接，支持 `/api/coding/v3/audio/transcriptions` 这类非 `/v1` base；修复分批 A/B run 覆盖旧 variant 的问题。实测火山 Coding Plan endpoint 对 5 分钟样本云 ASR 返回远端断开，云对照仍未成功。
- 2026-07-08 20:08:00 | Codex / GPT-5：优化 ASR 主路线：得到大脑逐字稿不能作为证据源；Dolphin 改为可配置本地第二 ASR 候选，默认 `small` 且关闭词级时间戳；实测 Windows/TorchCodec 运行时仍失败，因此暂不进入默认链路。
- 2026-07-08 20:32:00 | Codex / GPT-5：把 `evidence-conflict-llm-pack.json` 固化为 LLM 仲裁唯一输入包；完整语义候选包仍可保留审计，但未被真实外部证据支持的启发式风险不再送 LLM。

## 目标

VKP 的逐字稿质量不应该只依赖裸 ASR。主路线改为：

```text
SenseVoice/FunASR 原始 ASR
-> postprocessed-transcript.json
-> evidence-conflict-index
-> LLM 只仲裁真实冲突
-> source-arbitrated-transcript.json
-> corrected-transcript.json
-> full-transcript.md
-> smart-summary.md
```

关键边界：raw ASR 永远保留；高置信纠错才能进入 corrected transcript；低置信内容进入 review，不污染最终稿。

## 优化后的总原则

逐字稿质量改进不要再写成“多来源直接覆盖 ASR”。正确原则是：

1. 原始 ASR 只负责“听见了什么”，永远保留，不直接被覆盖。
2. 自带字幕、外挂字幕、网页标题/简介/章节、青龙打标、OCR/ebook、多模态都只是证据源。
3. 得到大脑逐字稿不能作为 VKP 的自动证据源，因为它本身不是可自动取得、可复现、可审计的视频来源证据。它只适合做离线人工质量对比。
4. 只有真实冲突进入 LLM 仲裁；高置信才写入 `source-arbitrated-transcript.json` 和 `corrected-transcript.json`。
5. `full-transcript.md` 和 `smart-summary.md` 只吃 corrected/postprocessed transcript，不再直接吃 raw ASR。
6. 第二 ASR 只能作为旁路证据源，不能因为一次样本更顺眼就替换主线。

因此主线应是：

```text
raw SenseVoice/FunASR
+ platform/native subtitles
+ web context
+ Qinglong tags/timeline/important moments
+ OCR/ebook screen text
+ multimodal evidence for difficult moments
-> evidence-conflict-index
-> LLM source arbitration
-> source-arbitrated-transcript.json
-> corrected-transcript.json
-> full-transcript.md
-> chapter-level smart-summary.md
```

## 当前默认 ASR

默认继续用本地 SenseVoice/FunASR，原因是：

- 本机已具备 FunASR/SenseVoice 环境，CUDA 可用，`iic/SenseVoiceSmall` 已缓存。
- SenseVoice 支持中文、英文、粤语、日语、韩语等，并包含 ASR、语言识别、情绪和音频事件能力。
- FunAudioLLM/SenseVoice 论文说明 SenseVoice-Small 低延迟，且可使用 ITN/NoITN 控制转写风格；这是课程视频本地批量处理的实用默认选择。

本项目已把 SenseVoice/FunASR 默认计划升级为完整模式：

```text
vad_model=fsmn-vad
punc_model=ct-punc
use_itn=true
merge_vad=true
merge_length_s=15
vad_max_single_segment_time_ms=30000
spk_model=可选，例如 cam++
```

入口：

```powershell
.\scripts\video-knowledge.ps1 plan-asr <workspace> <media> --preset sensevoice
.\scripts\video-knowledge.ps1 plan-asr <workspace> <media> --preset sensevoice --spk-model cam++
```

## 可读转写层

`postprocessed-transcript.json` 现在是主纠错流水线的默认前置步骤。

它做：

- 合并碎段。
- 默认 readable 标点/断句：基于 ASR cue 边界和少量话语标记插入逗号，保留 `conservative` 终止标点模式。
- 长句切段。
- 生成 `postprocessed-transcript.json/.srt` 和 `readable-transcript.json/.srt`。
- 默认写入 `corrected-transcript.json/.srt`，让导出优先使用可读底稿。

它不做：

- 不改事实。
- 不调用 LLM。
- 不覆盖 raw ASR。

入口：

```powershell
.\scripts\video-knowledge.ps1 postprocess-asr-transcript <webui-bundle>
```

## 证据冲突层

新增 `evidence-conflict-index`，解决之前“有数字/步骤词就送审”的噪音问题。

进入 LLM 仲裁的候选必须有具体文本差异，并且来自真实冲突：

- ASR vs 平台字幕/外挂字幕/本地抓取字幕。
- ASR vs OCR/ebook/画面文字。
- ASR vs 多模态画面理解。
- ASR vs 青龙打标器重点、话题、画面状态。
- ASR vs 网页标题、简介、章节。
- ASR vs 术语词典、实体词典。

只标风险、不送 LLM 的情况：

- 单纯出现数字。
- 单纯出现“第一步/第二步”。
- 没有外部证据支持的启发式疑点。

入口：

```powershell
.\scripts\video-knowledge.ps1 evidence-conflict-index <webui-bundle>
```

产物：

- `evidence-conflict-index.json`
- `evidence-conflict-index.md`

流水线会进一步生成 `evidence-conflict-llm-pack.json`。这个文件才是 LLM 仲裁的输入；原始 `transcript-semantic-correction-pack.json` 只保留为审计和候选来源，不直接送审。

## LLM 仲裁层

LLM 不再审全部转写，只审 `evidence-conflict-index` 里的高价值冲突。代码层面已经把后续 LLM draft 指向 `evidence-conflict-llm-pack.json`，确保“含数字/步骤词但无外部证据”的候选不会进入在线仲裁。

推荐入口：

```powershell
.\scripts\video-knowledge.ps1 transcript-evidence-correction-pipeline <webui-bundle>
```

默认不调用在线 LLM。需要真实调用时：

```powershell
.\scripts\video-knowledge.ps1 transcript-evidence-correction-pipeline <webui-bundle> --execute-llm --provider-config <provider.json>
```

高置信自动应用仍需要显式：

```powershell
--auto-apply-high-confidence
```

## WhisperX 的定位

WhisperX 不替代 SenseVoice/FunASR 主 ASR。它只用于：

- word-level alignment。
- 更准的时间戳。
- 说话人分离/diarization 辅助。

入口：

```powershell
.\scripts\video-knowledge.ps1 plan-whisperx-alignment <workspace> <media>
```

## ASR 方案研究结论

截至 2026-07-08，本项目不建议把主 ASR 从 SenseVoice/FunASR 直接换掉。更稳的设计是“一个本地主 ASR + 一个按需第二证据 ASR + 一个 alignment 层 + 一个云端对照组”：

| 方案 | 在 VKP 中的定位 | 适合场景 | 当前结论 |
| --- | --- | --- | --- |
| SenseVoice/FunASR | 默认主 ASR | 中文课程、批量、本地隐私、低成本 | 继续主线，但必须启用 VAD、ITN、标点、合并碎段 |
| Dolphin / Dolphin-CN-Dialect | 第二 ASR 证据源候选 | 口音、方言、SenseVoice 明显听错的片段 | adapter 已接；`small` 权重可下载，但当前 Windows/TorchCodec runtime 失败，暂不进入默认链路 |
| FireRedASR | 后续高精度本地候选 | 普通话/方言/英文混合、想做第二 ASR 质量上限 | 论文和仓库定位很强，但模型大、环境重，先列入 code-review backlog，不抢当前主线 |
| WhisperX | 时间戳/说话人增强 | 需要精准 review_start、字幕对齐、说话人区分 | 做 alignment，不做主 ASR 替换 |
| OpenAI / OpenAI-compatible 云 ASR | 小样本质量对照 | 明确授权上传、疑难片段、评估本地 ASR 上限 | 默认不上传；当前火山 Coding Plan endpoint 云 ASR 未跑通，需换明确支持 audio/transcriptions 的 provider |
| NVIDIA Parakeet/Canary 等英文强模型 | 英文 profile 候选 | 英文会议、英文课程 | 英文很强，中文获客课程不是优先项，可后续作为英文专用 profile |

因此，逐字稿质量提升的优先级不是“盲目换 ASR”，而是：

1. 先把 SenseVoice full mode 跑稳：VAD、ITN、标点、合并碎段、GPU。
2. 把平台字幕/外挂字幕/网页上下文/OCR/多模态/青龙打标全部纳入证据层。
3. 只把真实冲突送 LLM 仲裁，得到 `source-arbitrated-transcript.json`。
4. 对 5 分钟样本跑 A/B，再决定是否引入第二 ASR；Dolphin 当前不满足默认引入条件。
5. 对需要精准跳转和人工审核的视频，再跑 WhisperX alignment 改时间戳，不用它重写全部文本。
6. 如果要继续寻找更强本地 ASR，优先审 FireRedASR，再考虑 Dolphin-CN-Dialect/Paraformer 热词增强；不要把英文 Parakeet 当中文主线。

## 优化后的落地顺序

下一步不要把“换 ASR”当作唯一手段。更稳的顺序是：

1. **主 ASR 固定**：SenseVoice/FunASR full mode 继续做默认主线，启用 VAD、ITN、ct-punc、合并碎段、GPU。
2. **先后处理再仲裁**：所有导出先走 `postprocessed-transcript.json`，再走 `source-arbitrated-transcript.json`；`full-transcript.md` 和 `smart-summary.md` 不再直接吃 raw ASR。
3. **证据先收齐**：平台字幕、外挂字幕、网页标题/简介/章节、青龙打标、OCR/ebook、多模态只作为 evidence source，不直接覆盖。
4. **只审真实冲突**：`transcript-semantic-correction-pack.json` 可以宽松收集疑点，但真正送 LLM 的只有 `evidence-conflict-llm-pack.json`。
5. **第二 ASR 做旁路**：第二 ASR 的输出只进入证据冲突层，用来发现 SenseVoice 可能听错的词，不直接替换主 transcript。
6. **时间戳单独增强**：需要精确 review_start 时再跑 WhisperX alignment 或其他 alignment，不用它重写全文。

## 更适合的 ASR 方案判断

当前更合理的候选排序：

| 优先级 | 方案 | 为什么 | VKP 处理方式 |
| --- | --- | --- | --- |
| P0 | SenseVoice/FunASR full mode | 本机已跑通；官方支持 VAD、ITN、ct-punc、speaker diarization；中文课程吞吐好 | 默认主 ASR |
| P1 | FireRedASR2S | 新版一体化 ASR/VAD/LID/Punc，中文普通话、20+ 方言/口音、英文、code-switching；README 报告 FireRedPunc 明显强于 FunASR-Punc | 下一个 code-review + 5 分钟 A/B 候选 |
| P1 | WhisperX | word-level timestamp、forced alignment、diarization 辅助成熟 | alignment 层，不替换 ASR 文本 |
| P2 | Dolphin / Dolphin-CN-Dialect | 东方语言、中文方言、hotword 支持；适合口音/方言/专名热词旁路 | 第二 ASR 证据源；Windows/TorchCodec 稳定前不默认 |
| P2 | OpenAI `gpt-4o-transcribe` / `gpt-4o-transcribe-diarize` | 云端质量对照、可做说话人 diarized_json；但默认不能上传私有长音频 | 明确授权后小样本 A/B 或疑难片段复核 |
| P3 | `whisper-1` / faster-whisper | 生态成熟，timestamp/word 输出方便；但中文课程不是当前最强默认 | fallback 或英文/跨语种 profile |

依据链接：

- SenseVoice: https://github.com/FunAudioLLM/SenseVoice
- FunASR: https://github.com/modelscope/FunASR
- FireRedASR2S: https://github.com/FireRedTeam/FireRedASR2S
- FireRedASR: https://github.com/FireRedTeam/FireRedASR
- Dolphin: https://github.com/DataoceanAI/Dolphin
- WhisperX: https://github.com/m-bain/whisperX
- OpenAI Speech to text: https://developers.openai.com/api/docs/guides/speech-to-text

## 第二 ASR 候选

### Dolphin / Dolphin-CN-Dialect

调研结论：Dolphin 值得进入 A/B，但不直接替换默认主线。

依据：

- Dolphin 面向东亚、南亚、东南亚和中东语言，论文称支持 40 种东方语言，并支持 22 种中文方言。
- Dolphin-CN-Dialect 进一步聚焦中文和方言场景，支持流式和非流式推理，并引入 hotword 支持。

适合 VKP 的原因：

- 如果课程视频有明显口音、方言、普通话不标准，Dolphin 可能比 SenseVoice 更值得做第二路证据。
- 它应作为“第二 ASR 证据源”，用于 conflict index，而不是直接覆盖 SenseVoice。

### OpenAI / OpenAI-compatible 云 ASR

定位：质量对照组或疑难样本复核，不默认上传。

使用边界：

- 只在明确允许时调用。
- 优先抽 5 分钟样本做 A/B，不上传整段长视频。
- 输出只作为外部证据，仍需进入 source arbitration / semantic correction。

## 5 分钟 ASR A/B 计划

新增入口：

```powershell
.\scripts\video-knowledge.ps1 asr-ab-sample-plan <workspace> <media> --sample-start-seconds 0 --duration-seconds 300
```

它会生成：

- 5 分钟样本切片命令。
- `sensevoice_basic`：SenseVoice + VAD，但不启用 ITN/标点。
- `sensevoice_full_punc`：SenseVoice + VAD + ITN + ct-punc。
- `dolphin`：候选第二本地 ASR，已接入 `dolphin_python_runner`，本机缺包时快速返回 `asr_module_not_ready`。
- `openai_cloud_asr`：云 ASR 样本计划，默认不上传。

比较指标：

- 专名/术语错误。
- 数字、金额、时间、步骤数错误。
- 标点和段落可读性。
- 时间戳偏移。
- 说话人标签可用性。
- 是否能作为 conflict evidence 改善最终 `full-transcript.md`。

`asr-ab-sample-run` 只输出 `asr-ab-sample-run.json/md` 和各变体 normalized transcript；它不会写 `corrected-transcript.json`，不会进入最终逐字稿，必须经过 source arbitration / evidence conflict / LLM 仲裁后才能影响最终稿。

新增比较入口：

```powershell
.\scripts\video-knowledge.ps1 asr-ab-compare <asr-ab-sample-run.json>
```

它会生成：

- `asr-ab-comparison.json`
- `asr-ab-comparison.md`

比较报告只做决策辅助：推荐主 ASR、判断是否足以引入第二 ASR、判断云 ASR 对照是否缺失。它仍然不会推广任何 transcript。

## 2026-07-08 5 分钟本地 A/B 实测

样本视频：`%MEDIA_ROOT%\1.客户特点、成交基本原则、获取信任的相关动作.mp4`。

样本产物：

- A/B 运行报告：`%WORKSPACE_ROOT%\video-knowledge-pipeline\openclaw-runs\asr-ab\customer-trust-5min\transcripts\asr-ab-sample\asr-ab-sample-run.md`
- A/B JSON：`%WORKSPACE_ROOT%\video-knowledge-pipeline\openclaw-runs\asr-ab\customer-trust-5min\transcripts\asr-ab-sample\asr-ab-sample-run.json`
- A/B 比较报告：`%WORKSPACE_ROOT%\video-knowledge-pipeline\openclaw-runs\asr-ab\customer-trust-5min\transcripts\asr-ab-sample\asr-ab-comparison.md`
- 样本视频：`%WORKSPACE_ROOT%\video-knowledge-pipeline\openclaw-runs\asr-ab\customer-trust-5min\transcripts\asr-ab-sample\1.客户特点、成交基本原则、获取信任的相关动作.sample-0-300.mp4`

结果：

| 变体 | 状态 | 观察 |
| --- | --- | --- |
| `sensevoice_basic` | `ok` | 5 分钟样本成功，本地 `.conda-lecture-asr` 执行，18 段，1516 字符，标点数 0。说明主 SenseVoice/VAD 可用，但裸输出可读性差。 |
| `sensevoice_full_punc` | `ok` | `ct-punc` 已缓存并跑通；19 段，1658 字符，清洗后标点数 137。相对 basic 的无标点裸输出，阅读性明显提升。 |
| `dolphin` | `asr_module_not_ready` | Dolphin adapter 已接入，但当前 `.conda-lecture-asr` 未安装 `dolphin` Python 包。未安装时快速失败，不下载、不替换主 ASR。 |
| `openai_cloud_asr` | 执行失败 | 已按显式 cloud A/B 对 5 分钟样本尝试一次 OpenAI-compatible ASR；火山 Coding Plan endpoint 返回远端断开连接，未产出 normalized transcript。 |

最新归一化产物：

- `sensevoice_full_punc` 清洗版 JSON：`%WORKSPACE_ROOT%\video-knowledge-pipeline\openclaw-runs\asr-ab\customer-trust-5min\transcripts\transcript_e5bec223ddd4\normalized-transcript.json`
- `sensevoice_full_punc` 清洗版 SRT：`%WORKSPACE_ROOT%\video-knowledge-pipeline\openclaw-runs\asr-ab\customer-trust-5min\transcripts\transcript_e5bec223ddd4\normalized-transcript.srt`

实测结论：

1. `sensevoice_full_punc` 已经比 `sensevoice_basic` 更适合作为 postprocessed/corrected transcript 的输入，因为它至少提供了标点、ITN 和可读段落。
2. 仍然不能直接把它当最终逐字稿：样本里还能看到术语错词、段落边界不自然、个别短噪音段，例如开头极短片段。
3. 下一步重点应是语义证据仲裁：把平台字幕、网页上下文、青龙打标、OCR/ebook、多模态证据合进 conflict index，再用 LLM 只审真实冲突。
4. Dolphin 已有本地 adapter，`dataoceanai-dolphin`、`small` 权重和 `torchcodec` 已安装/下载；但当前 Windows/TorchCodec 动态库加载仍失败，所以 Dolphin 暂时只保留为候选，不进入默认第二 ASR。云 ASR 仍作为显式上传的质量对照组。


A/B 比较报告当前结论：

- 状态：`primary_asr_ready_second_asr_pending`。
- 主 ASR 推荐：`sensevoice_full_punc`。
- 第二 ASR 推荐：`do_not_introduce_second_asr_by_default_yet`。原因是 Dolphin adapter 已有，但本机样本尚未成功跑通。
- 云 ASR 推荐：`optional_quality_reference_missing`。原因是同一样本云 ASR 尝试失败，尚未形成可比较 transcript。

因此当前不能声称“已经完成第二 ASR 引入决策”，只能说主 ASR 路线已经足够明确，第二 ASR 仍需 FireRedASR/Dolphin/云 ASR 任一方案样本成功后，再比较术语、数字和专名错误。


云 ASR 实测边界：

- 只上传了既定 5 分钟 A/B 样本，没有上传整段视频。
- provider config/key 仅来自运行时环境，未写入 plan、manifest 或报告。
- `asr_transcriptions_url` 已修复：当 base URL 是 `https://ark.cn-beijing.volces.com/api/coding/v3` 时，ASR endpoint 现在生成 `.../api/coding/v3/audio/transcriptions`，不会错误拼成 `.../api/coding/v3/v1/audio/transcriptions`。
- 当前失败状态说明火山 Coding Plan 未能作为 ASR 对照组完成样本转写；后续若要完成云 ASR A/B，需要换成明确支持 `audio/transcriptions` 的 OpenAI-compatible ASR provider，或使用官方 OpenAI ASR key/base。
- A/B run 已支持分批合并：先跑本地，再跑 cloud/Dolphin，不会覆盖已有 variant 行。

## 对智能总结的影响

`smart-summary.md` 必须只吃 corrected transcript，不再直接吃 raw ASR。

正确输入：

```text
corrected-transcript.json
+ OCR/ebook 结构化内容
+ 多模态疑难帧结果
+ 青龙打标章节/重点
+ review gap
-> smart-summary-input-pack
-> 章节级 LLM 改写
-> smart-summary.md
```

如果 `postprocessed-transcript.json` 或 `corrected-transcript.json` 不存在，智能总结只能标记为 draft，不应伪装成最终成品总结。

## 参考来源

- FunAudioLLM / SenseVoice: https://arxiv.org/abs/2407.04051
- Dolphin ASR: https://arxiv.org/abs/2503.20212
- Dolphin GitHub: https://github.com/DataoceanAI/Dolphin
- Dolphin-CN-Dialect: https://arxiv.org/abs/2605.08961
- WhisperX GitHub: https://github.com/m-bain/whisperX
- WhisperX paper: https://arxiv.org/abs/2303.00747
- OpenAI Speech to Text docs: https://platform.openai.com/docs/guides/speech-to-text
- NVIDIA Parakeet model card: https://huggingface.co/nvidia/parakeet-tdt-0.6b-v2
