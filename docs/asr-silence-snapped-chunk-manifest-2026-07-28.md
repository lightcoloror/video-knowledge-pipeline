# VKP 精确音频分块清单与静音边界吸附

更新时间：2026-07-28 19:33:57 +08:00
执行者：Codex / GPT-5.6

## 结论

VKP 的本地 FunASR/SenseVoice 分块路线现在可以为每个块保存精确的源媒体
`start_seconds`、`end_seconds`、`duration_seconds` 与 overlap，并可显式选择
`silence_snap`，把等分切点吸附到附近静音中点。

默认仍为 `fixed_duration`，因此既有调用行为不变。静音吸附必须由操作者显式选择：

```powershell
$env:PYTHONPATH = "src"
python -m video_knowledge_pipeline.funasr_chunked_runner `
  --input <media> `
  --output <raw-asr-output.json> `
  --model <local-model-path> `
  --device cuda `
  --chunk-seconds 300 `
  --chunk-boundary-mode silence_snap
```

稳定产物为 `<raw-asr-output-stem>-chunk-manifest.json`。清单 revision 会进入
checkpoint；边界、源文件身份或策略变化后，旧的不等长块 checkpoint 不会被静默复用。

## 固定上游与复用边界

- 上游：Subtitle Edit
- 仓库：`https://github.com/SubtitleEdit/subtitleedit.git`
- 本地源码：
  `%WORKSPACE_ROOT%\video-creation-source-review\sources\subtitleedit`
- 固定 commit：`1517bb5c23e1c4072ea829edbc8d08e27cf79289`
- 复用入口：
  `src/ui/Features/Video/SpeechToText/OpenAiCompatible/OpenAiSttChunker.cs`
- 上游测试：
  `tests/UI/Features/Video/SpeechToText/OpenAiCompatible/OpenAiSttChunkerTests.cs`

实际吸收：

1. 近似等分后，为每个内部切点在 inclusive `±10s` 内选最近且尚未使用的静音中点。
2. 没有可靠静音时退回等分边界。
3. 边界必须严格递增。
4. 未匹配的尾部 `silence_start` 不作为切点。
5. 逐窗口调用 FFmpeg 提取音频，而不是重新实现解码器。

没有复制 Subtitle Edit 的 C# 实现、UI、任务状态机或 ASR 运行时。VKP 只实现
Python 薄适配、清单、checkpoint identity 与现有 FunASR runner 的编排胶水。

## 变更决策

| 变更 | 意图 | 决策 | 理由 | 证据 | 生效范围 |
| --- | --- | --- | --- | --- | --- |
| `audio_chunk_manifest.v1` | 让不等长块可准确回到原媒体时间轴 | 为每块持久化 index、artifact、精确 start/end/duration、前后 overlap、边界来源和内容寻址 revision | `index × chunk_seconds` 只能描述固定等长块；静音吸附后会制造错误偏移与错误缺口 | runner 回归用 0–280、280–600 秒清单验证第二块句子从 280000 ms 开始 | 本地分块计划、checkpoint、局部重跑和下游归一化；不改正文 |
| Subtitle Edit 静音边界 | 减少在话语中间硬切造成的漏字、重复字和说话人断裂 | 显式 `silence_snap` 适配上游最近静音中点算法；无静音时 fail-safe 等分 | 成熟字幕工具已用该策略和测试约束处理长音频 chunk | Python 映射测试覆盖上游等分、最近未使用静音、inclusive 边界、单调性和尾部未配对静音 | 仅本地音频切块；默认路线不变 |
| 逐窗口 FFmpeg 提取 | 让请求的源窗口与每个独立 artifact 一一对应 | 使用项目既有 `media_tools.resolve_media_tool("ffmpeg")`，逐块执行 `-ss/-t`、mono、16 kHz | segment muxer 会出现 packet 边界取整，且一个命令的失败不易精确归属到块 | 120 秒真实合成音频 smoke 得到 43/35/42 秒三个 16 kHz mono WAV | 本地临时音频 artifact；不新增第二 FFmpeg owner |
| 边界语义 | 防止把采样取整误读为源窗口 overlap | 清单明确 `boundary_semantics=requested_source_media_window`，overlap 表示请求源窗口的交叠，不冒充探测后的容器时长 | WAV/编码 packet 可有微小采样取整；来源窗口仍是唯一时间真源 | 合成 smoke 的第二静音中点为 78.000031 秒，解码 WAV 时长按采样精度为 35 秒 | 清单解释、审计与重跑 identity |
| checkpoint revision | 防止旧固定分块结果混入新静音分块 | checkpoint 绑定 manifest revision；旧无 revision checkpoint 只对默认 fixed route 保持兼容 | 不同边界的 chunk index 指向不同内容，复用会造成静默错稿 | 回归验证 revision 写入 checkpoint、失败块 gap 为 280–600 秒、retry 保留 `silence_snap` | FunASR 可恢复执行；不改变 provider/model |
| 默认兼容 | 避免未经样本验证就改变生产路线 | CLI 默认 `fixed_duration`；`silence_snap` 为 opt-in | 单样本边界正确不等于在所有课程、音乐、噪声素材上都更好 | 仍需 8–12 条短/中/长/超长视频盲测缺段、重复、耗时和人工修正成本 | 现有任务完全兼容；新策略需显式选择 |

## 验证

### 上游源码与测试映射

已完整阅读固定 commit 的 `OpenAiSttChunker.cs` 和对应 C# 测试。当前机器没有
`.NET` SDK（`dotnet` 不可用），所以没有伪报上游测试已运行；相同输入/输出约束已
映射为 VKP Python 离线测试。

### VKP 回归

- 分块清单、边界、checkpoint 与局部重跑：`18 passed`。
- ASR pipeline、讲话完整性、静音核销、FunASR 分块扩大集合：`81 passed,
  1 third-party warning`。
- Ruff、compileall、CLI help、scoped `git diff --check`：通过。

### 真实 FFmpeg smoke

输入是本地生成的 120 秒合成音频：

- 42 秒音调
- 2 秒静音
- 33 秒音调
- 2 秒静音
- 41 秒音调

目标块长 40 秒。实际源窗口：

| 块 | 源窗口 | 请求时长 | ffprobe 时长 | 音频格式 |
| --- | --- | --- | --- | --- |
| 0 | 0–43.000000 | 43.000000 | 43.000000 | 16000 Hz / mono |
| 1 | 43.000000–78.000031 | 35.000031 | 35.000000 | 16000 Hz / mono |
| 2 | 78.000031–120.000000 | 41.999969 | 42.000000 | 16000 Hz / mono |

测试目录随后已删除；没有真实用户媒体、模型、网络、上传或 provider 调用。

## 剩余验证与边界

1. 在 8–12 条短/中/长/超长真实样本上同时跑固定边界和静音边界，盲测缺段、
   重复字、边界人工修正数、GPU 峰值与完成时间。
2. 本轮 overlap 仍为 `0`，没有假装已实现重叠窗口/LCS 去重。需要重叠时，应复用
   已接入的 WhisperStreaming timestamped agreement，再单独定义 overlap manifest。
3. `silencedetect` 失败时清单明确记录 `ffmpeg_failed` 并退回等分；不会自动改成
   远程 ASR、自动上传或跨 provider fallback。
4. 静音边界改善“在哪里切”，不证明 ASR 内容完整；最终仍必须经过独立 VAD、
   transcript completeness 和人工关键点质量门。

## 2026-07-30 overlap-save 升级

- 执行者：Codex（GPT-5）
- 时间：2026-07-30 11:56:51
- 意图：降低五分钟分块在边界处随机漏词、断句或重复的风险。
- 决策：正式 SenseVoice/FunASR 计划显式使用 5 秒重叠；每块同时记录不重叠的 `core_start_seconds/core_end_seconds` 与实际提取窗口。规范结果按句子时间中点归属唯一核心块，原始含上下文块继续保存在 `chunk_results`。
- 理由：重叠是解码上下文，不应让相同内容在规范逐字稿出现两次；无时间戳结果无法安全裁剪，必须标记 `review_required`，不能静默合并。
- 证据：窗口语义适配固定 CrispASR commit `9deefe8f47273722415e4b4be5d87361b96177c9` 的 `src/core/crispasr_lcs.h`；边界一致性继续复用已接入的 WhisperStreaming/SimulStreaming LocalAgreement。新增固定边界、静音吸附、唯一核心归属、无时间戳降级和正式计划默认参数测试。
- 生效范围：本地 FunASR 长媒体 CLI 和由 `asr_runner/asr_execution` 生成或升级的正式计划。直接调用 `run_funasr_chunked()` 的旧嵌入代码默认仍为零重叠，调用方可显式传入；Qwen ASR/ForcedAligner 不受影响。
- 剩余真实证据：仍需对短、中、长、超长 8–12 条真实样本记录缺段率、重复字、边界人工修正数、GPU 峰值和完成时间；在盲测完成前不得声称长期稳定性已经证明。
## 2026-07-30 精确句级时间戳、边界证据与执行遥测

- 执行者：Codex（GPT-5）
- 时间：2026-07-30 12:49:00 +08:00
- 意图：让五分钟分块后的规范逐字稿具备真实句级时间范围，并能区分稳定完成、近 OOM 和边界待复核。
- 决策：直接复用固定 FunASR 1.3.30 官方 CLI 的 `sentence_timestamp=True`、`output_timestamp=True`、`return_time_stamps=True`；规范合并继续按 core-window midpoint 唯一归属。句子切分不同导致 LocalAgreement 低时，允许固定 CrispASR/NeMo LCS 的高置信边界证据消除假性降级。无时间戳才使用 LCS 前缀裁剪降级路线。checkpoint 升级为 v2 并绑定完整执行契约 revision；子进程记录 elapsed/GPU peak，stdout 仅发小型执行回执。
- 理由：旧结果每五分钟只有一个粗段，整体文本虽可比较，但所有局部窗口质量门均失真；同时整份原始结果被再次打印到 stdout，造成重复内存、日志和 UI 负担。
- 证据：30 秒真实本地 GPU smoke 从 1 个粗段变为 11 个句级段、146 个 token 时间戳；真实 `short-01` 从 3 个粗段变为 368 个句级段。精确参考绑定后整体内容差异为 2.077989%，无长内容缺失；局部比较由错误的 19/19 全失败恢复为 12/19 通过、7 个只需定向复核。3/3 块完成，边界 LCS 分别匹配 43/51 个单位，合并状态为 `completed`。定向回归当前 12 passed。
- 生效范围：本地 FunASR/SenseVoice child runner、五分钟分块 checkpoint、规范化逐字稿和评估遥测；不改变模型、ASR 正文真源、远程 provider、授权或上传行为。

当前基准产物：

- 清单：`.local/asr-overlap-silence-benchmark-20260730/benchmark-manifest.json`
- 首条时间戳逐字稿：`.local/asr-overlap-silence-benchmark-20260730/runs/short-01/transcripts/transcript_2153fd1a277d/normalized-transcript.json`
- 首条精确评估：`.local/asr-overlap-silence-benchmark-20260730/runs/short-01/comparison-timestamped.json`

剩余边界：该结果只证明第一条短样本。短/中/长/超长其余 7 条仍须单 GPU 串行完成；局部窗口差异高于 5% 表示“需要抽听复核”，不能自动等同于缺段，也不能用参考稿反向纠正候选逐字稿。
## 2026-07-30 15:12:17 +08:00 | Codex / GPT-5.6 — 8 样本重叠边界与可恢复评测收口

- 意图：在批量处理剩余视频前，用短、中、长、超长分层样本验证 5 分钟分块、5 秒重叠、静音吸附和检查点恢复是否真正保留内容。
- 决策：直接复用 FunASR 已输出的逐字符时间戳，把跨核心窗口的长句裁到唯一归属；原始 chunk 与边界仲裁证据保持不变。新增显式 `--rebuild-from-checkpoint`，只读取精确 v2 checkpoint 与 chunk manifest，不探测媒体、不执行子模型、不改写检查点。
- 理由：旧“整句中点归属”在约 30 秒长句跨过 5 秒重叠区时会保留重复前缀；移动硬盘暂时不可读时，已经成功的 108 个 chunk 也不应被迫重新推理。
- 证据：8/8 运行完成，108/108 chunk 成功，失败 chunk 0，possible_long_form_loss 0；7 个有效参考绑定中 6 个通过 5% 内容距离门。long-01 修复后 content distance 从 0.06601631 降为 0.06436461，仍需局部盲审；xlong-01 因参考时长绑定无效而不作 ASR 质量结论。联合离线回归 34/34 通过。
- 生效范围：仅 FunASR chunk canonical merge、显式检查点重建和本地评测。正常 ASR 仍要求真实媒体可读；参考稿仍是 evaluation-only，禁止进入 prompt、热词、路由或纠错。
- 产物：`.local/asr-overlap-silence-benchmark-20260730/benchmark-result.json`、`benchmark-result.md`，以及复用现有 `quality_benchmark_arbitration` 生成的 11 个窗口匿名复核包 `blind-review-20260730/quality-benchmark-arbitration-pack.json`。
- 当前缺口：移动硬盘 E: 在生成音频复核片段时返回 Windows 483 硬件错误，因此匿名文本包已就绪，但 11 个窗口仍需按 `review-source-index.private.json` 的媒体路径与时间范围听音确认；在完成前不批量重跑剩余 24 个视频。

## 2026-07-31 01:47:37 +08:00 | Codex / GPT-5.6 — 盲审音频包恢复

- 意图：解除 11 个高差异窗口的人工盲审阻断，同时避免再次随机读取出现硬件错误的移动盘完整视频。
- 决策：不重新抽取视频。复用同一轮正式 ASR 已保存在 D 盘的 5 分钟 WAV chunk、`core_start_seconds/core_end_seconds` 与 overlap 契约；每个复核窗口按 core 区间切片，跨块窗口使用 FFmpeg 音频 concat 无重叠拼接。
- 理由：源视频当前能枚举目录项，但读取首 32 字节仍在 30 秒内超时；已有 chunk 是绑定源媒体和 SHA-256 的可追溯本地证据，足以还原这 11 个听音窗口。复用它们比强行读取移动盘更稳定，也不会重跑 ASR。
- 证据：`blind-review-20260730/audio-clips` 已生成 11/11 个 16 kHz 单声道 PCM WAV，失败 0，总计 8,000,854 字节；ffprobe 时长逐项等于计划窗口，范围 16–35 秒。每个文件均已计算 SHA-256。移动盘直读尝试生成 0/11，已停止；缓存 chunk 路线完成 11/11。
- 生效范围：仅 `.local/asr-overlap-silence-benchmark-20260730/blind-review-20260730` 的人工评估证据；不修改候选逐字稿、参考稿、生产 Bundle、模型路由或授权。
- 剩余缺口：音频包已可听，但 A/B 选择仍必须由人工依据音频完成；参考稿继续只用于评估，不能进入 ASR prompt、热词或纠错证据。

## 2026-08-18 `run-asr-plan` checkpoint resume and idempotent rerun

- Updated by: Codex (GPT-5.6 Sol), 2026-08-18 19:03:40 +08:00.
- Intent: let an interrupted ultra-long local Qwen ASR plan continue from durable successful chunks and still produce the final raw JSON after an outer timeout.
- Decision: keep `qwen3_asr_python_runner` as the only chunk state machine. `run-asr-plan` now validates and reports its checkpoint, delegates partial continuation to that runner, rebuilds a missing final output from a complete checkpoint without loading a model, and reuses a matching completed output byte-for-byte. New semantic contracts bind context by SHA-256 rather than copying its text. `--no-resume` is the explicit opt-out.
- Reason: an outer process timeout can preserve dozens of valid chunk results while withholding the final JSON. Restarting all chunks wastes hours and creates unnecessary output drift; a second checkpoint implementation would create conflicting truth.
- Evidence: synthetic regressions cover partial continuation metadata, complete-checkpoint recovery without child execution, byte-stable completed reruns, explicit fresh execution, semantic-contract drift rejection, and legacy checkpoint compatibility. No real media, local model, Provider, upload, network, or publication is involved.
- Effective scope: local Qwen full-ASR plans and their derived raw output/run evidence. Canonical transcript arbitration, Timeline, other ASR engines, model selection, retry limits, and media files are unchanged.
- Rollback: remove the top-level checkpoint inspection/restoration helpers and CLI flag, then stop writing the new `execution_contract`; legacy checkpoint fields remain readable and no source media or canonical transcript requires rollback.
