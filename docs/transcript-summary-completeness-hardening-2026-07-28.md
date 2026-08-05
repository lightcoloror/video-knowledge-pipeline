# VKP 逐字稿与智能总结完整性补强（2026-07-28）

更新时间：2026-07-28 12:06:24 +08:00
执行者：Codex / GPT-5.6
工作区基线：`video-knowledge-pipeline@cf9fe4431d3ea33ca0cfc7adfed717cd970579d3`

## 目标与边界

本轮只完善“把视频内容完整提取成逐字稿和智能总结”的证据、质量门与恢复能力。

- 不调用在线 API，不上传视频、音频、帧或文档。
- 不覆盖人工确认内容，不让总结反向改写原始 ASR。
- 不新增第二套 ASR、VAD、FFmpeg、Timeline、Bundle 或验收状态机。
- 优先直接调用已经安装的成熟实现；VKP 只增加薄适配、证据组合、质量门和恢复语义。
- 拉片、一键成片和发布能力不在本轮范围。

## 本轮结论

1. “时间戳铺满整段视频”不等于“所有讲话都被识别”。质量报告现在明确区分 timeline span 与 speech completeness。
2. 本地长媒体分块只有进程成功不够；空文本块先 fail-closed，再由来源哈希绑定的独立 Silero VAD 判断是“无讲话”还是“漏转写”。
3. 第二个生产样本的 5:00–20:00 并非漏掉 15 分钟讲话。完整视频 Silero v5 证据显示该区间没有语音；三个空块现在被解释为 `passed_with_verified_silence`。
4. 两个生产样本的独立 VAD 讲话区间都没有未覆盖缺口。逐字稿仍保留真实风险标签：旧式整段单次 ASR、固定块无重叠、低密度片段待复核。
5. 两份智能总结的自动检查均通过；数字证据已归一化，`unsupported_numbers=[]`。由于没有人工关键点 gold set，生产状态保持 `human_review_required`，不再伪报 `complete`。

## 每项变更的意图、决策、理由、证据和范围

| 变更 | 意图 | 决策 | 理由 | 证据 | 生效范围 |
| --- | --- | --- | --- | --- | --- |
| 逐字稿来源完整性 | 不再用时间跨度冒充讲话完整度 | 新增 `transcript_source_completeness`，组合原始 ASR lineage、现有响应质量门和独立 VAD | 长段模型输出可能时间覆盖完整但内容缺失 | 两个生产 Bundle 的旧报告均曾显示 timeline coverage 1.0，但缺少独立讲话覆盖证明 | 只扩展质量报告，不改逐字稿正文 |
| 空块 fail-closed | 防止空文本块被记为成功 | `funasr_chunked_runner` 只有发现实际文本才把块计入成功；时间戳或空列表不能冒充内容 | 子进程退出码只能证明执行完成，不能证明识别到讲话 | 第二样本旧 checkpoint 把 1/2/3 三个空块计作成功 | 未来本地 FunASR 分块执行 |
| 精确局部重跑 | 只重跑缺口且不复用旧假成功 JSON | 显式 `--chunk-indexes` 先移除对应 checkpoint 行和旧 child JSON；局部成功与全片 canonical complete 分开 | 旧结果和本次操作结果必须可区分，避免整片重复耗时 | 1/2/3 精确重跑没有覆盖其余 18 个成功块 | 本地显式 repair 命令 |
| 词时间戳硬门 | 防止越界词时间戳掩盖讲话缺口 | 复用现有 word parser；越界、倒序或不完整时回退到 segment bounds | 不可信词时间戳会制造虚假覆盖 | focused 回归覆盖越界、轻微漂移和累计短缺口 | ASR 响应质量评估 |
| 累计缺口预算 | 防止很多小缺口被逐个忽略 | 复用 `interval_coverage`，增加可选覆盖率和累计未覆盖秒数预算 | 每个小缺口都低于阈值，合计仍可能丢掉大量内容 | focused 回归：3 个 1.9 秒缺口不能得到 0 缺口结论 | 只有显式启用新预算的 ASR 讲话覆盖检查 |
| 独立 VAD 静音闭环 | 区分“无讲话”与“漏转写” | 直接调用已安装 `faster-whisper` 的 `decode_audio`、`VadOptions`、`get_speech_timestamps` 与随包 Silero v5 ONNX；只在输入路径和 SHA-256 完全匹配时采信 | FFmpeg 非静音可能是音乐、噪声或瞬态；强迫 ASR 输出会制造内容 | 第二视频完整 Silero：46 段讲话、4864.032 秒；5:00–20:00 无讲话；三个空块被精确核销 | 只解释 chunk integrity 和 speech coverage；不修改原始 ASR/checkpoint/正文 |
| 媒体时长探测 | 避免隔离 Python 环境把长视频写成 0 秒 | `funasr_python_runner` 复用现有 `media_tools.resolve_media_tool("ffprobe")` | 子环境可以读取 WAV，但其 PATH 未必包含 ffprobe | 第二样本重汇总后时长从错误的 0 恢复为 6259.583667 秒 | 本地 FunASR 元数据，不改模型推理 |
| 数字/范围证据 | 降低总结数字的假阳性失败，也避免错误合并 | 复用现有数字 evidence map；只新增窄范围等价：`一两场/一到两场/一至两场 ↔ 1–2场`，保留原始 mention | 广义中文数字范围会把“二四年”错误解析为 2–4 年 | 回归覆盖 `二四年=24年`、`202 3=2023`、`330 0=3300`，并拒绝 `2–1场` | 总结事实核验，不改正文 |
| 总结依赖逐字稿完整性 | 不让旧总结在逐字稿存在讲话缺口时继续生产通过 | Smart Summary 质量门读取已持久化 transcript quality；未验证或失败时阻断 | 总结质量不能高于其事实来源质量 | 两个生产样本刷新后 `transcript_speech_completeness` 自动检查通过 | Smart Summary 质量报告和 freshness |
| 最终验收聚合 | 防止逐字稿/总结失败但 acceptance 仍显示 complete | `acceptance_check` 只读聚合现有质量产物；旧 Bundle 没有质量文件时保持兼容 | 覆盖率与产物存在性不足以代表内容合格 | 两个生产样本当前均为 `human_review_required`，下一步明确为人工关键点复核 | 有质量产物的新/刷新 Bundle |
| 低响度预处理研究 | 避免误把低电平噪声放大成语音 | 研究并实测 FFmpeg `loudnorm`，但本轮不接入自动生产重跑 | 响度标准化不能证明有人讲话，必须先经过语音 VAD | 10–15 分钟块从 mean -50.5 dB 标准化到 -23.8 dB 后，SenseVoice 和 Silero 仍均为 0 人声 | 保留为候选诊断，不改变默认 ASR |

## 固定上游源码与实际复用

| 上游 | 本地源码与固定 commit | 源码级结论 | VKP 状态 |
| --- | --- | --- | --- |
| SYSTRAN/faster-whisper | `%WORKSPACE_ROOT%\video-creation-source-review\sources\faster-whisper` @ `ed9a06cd89a93e47838f564998a6c09b655d7f43` | 直接复用已安装包的 Silero VAD API 与随包 ONNX；参考词异常、VAD padding 和分段输出；未复制推理实现 | **已实现 / 直接调用成熟模块** |
| m-bain/whisperX | `%WORKSPACE_ROOT%\video-creation-source-review\sources\whisperX` @ `5f2f9d4320dd93a7d12f5ba2495eef7e0a5af963` | 保留原 ASR 与 alignment sidecar、失败不覆盖正文的设计符合 VKP provenance | **设计已吸收；运行时不新增** |
| OpenMOSS/MOSS-Transcribe-Diarize | `%WORKSPACE_ROOT%\source-reviews\radar-intake-2026-07-18\MOSS-Transcribe-Diarize` @ `eda4b9f13f1574765a80438c9797780a9bd48112` | 复用 `mtd-subtitle` CLI / `segments.json` 合同；缺 runtime 时 fail-closed | **适配合同已存在；真实模型 trial 另行处理** |
| Jianf-Wang/stable-ts | `%WORKSPACE_ROOT%\source-reviews\vkp-transcript-summary-wave-20260728\stable-ts` @ `e312072cc024ae9fceb25b057d7d18524873a02b` | 适合停顿抑制、时间戳稳定与词级对齐；当前环境没有其 `openai-whisper` runtime，因此不假装已部署 | **候选 / 源码 compile 通过 / runtime blocked** |
| Subtitle Edit | `%WORKSPACE_ROOT%\video-creation-source-review\sources\subtitleedit` @ `1517bb5c23e1c4072ea829edbc8d08e27cf79289` | `OpenAiSttChunker` 的静音中点边界适合 P1；当前 VKP 的 `index × 300` 偏移必须先升级成精确 start/end manifest | **设计候选；未贸然接入** |
| NarratoAI | `%WORKSPACE_ROOT%\source-reviews\shot-breakdown-wave-20260721\narratoai` @ `0a5dcf5f21f7f40ca77bc38ea6d1d3fd52e32c26` | 两遍 FFmpeg EBU R128 loudnorm 可复用；拒绝其无 VAD 门控的 pydub 简单增益 fallback | **诊断 smoke 完成；自动生产路径暂拒绝** |
| LlamaIndex TreeSummarize | `%WORKSPACE_ROOT%\reference-repos\bookwiki-mainline\llama_index` @ `d8d7ffbb119a481147856392bba5bca549283030` | 递归 map/reduce 适合长视频“章节事实包 → 全局总结”；本轮不引入版本不匹配的新依赖 | **架构已吸收；VKP 继续使用现有章节/Reduce 产物** |

## 源码运行与测试证据

- `stable-ts`：本地 `compileall` 通过；真实 runtime 因缺少其 `openai-whisper` 依赖而明确 blocked，没有自动下载。
- LlamaIndex `TreeSummarize`：对本地固定文本做离线递归归并 smoke 通过。
- `faster-whisper` 1.1.1：两个完整生产视频均实际运行随包 Silero v5；模型资产 SHA-256 写入 `silero-vad-candidate.json`。
- FunASR 低响度 A/B：对副本执行 FFmpeg `loudnorm` 后再次运行本地 SenseVoice GPU；结果仍为空。随后 Silero 对原块和标准化块均为 0 人声，因此拒绝自动把响度标准化升级为生产修复。
- 回归测试：
  - ASR、独立 VAD、局部修复：`15 passed`。
  - FunASR 与统一媒体工具解析：`58 passed, 1 warning`。
  - 本轮此前聚焦集合：ASR `33 passed`，逐字稿/总结 `68 passed`，验收 `9 passed, 1 warning`，总结完整性/数字 `36 passed`。

## 两个生产 Bundle 的当前状态

| Bundle | 逐字稿 | 独立讲话覆盖 | 智能总结 | 最终验收 |
| --- | --- | --- | --- | --- |
| `每天都有客户主动咨询的秘诀` | `warning`，timeline span 1.0；旧式整段单次 ASR | Silero 20 段、2474.240 秒；coverage gap 0；speech completeness verified | 自动检查通过；压缩率 0.284555；数字一致；缺人工关键点 gold set | `human_review_required` |
| `2026年7月24日全国大早会` | `warning`，timeline span 1.0；18 个有字块 + 3 个 VAD 证实静音块 | Silero 46 段、4864.032 秒；5:00–20:00 无讲话；coverage gap 0 | 自动检查通过；压缩率 0.202667；数字一致；缺人工关键点 gold set | `human_review_required` |

生产证据路径：

- `%WORKSPACE_ROOT%\video-knowledge-output\每天都有客户主动咨询的秘诀\webui-bundle\silero-vad-candidate.json`
- `%WORKSPACE_ROOT%\video-knowledge-output\每天都有客户主动咨询的秘诀\webui-bundle\transcript-quality-gate.json`
- `%WORKSPACE_ROOT%\video-knowledge-output\每天都有客户主动咨询的秘诀\webui-bundle\exports\smart-summary-quality.json`
- `%WORKSPACE_ROOT%\video-knowledge-output\2026年7月24日全国大早会\webui-bundle\silero-vad-candidate.json`
- `%WORKSPACE_ROOT%\video-knowledge-output\2026年7月24日全国大早会\webui-bundle\transcript-quality-gate.json`
- `%WORKSPACE_ROOT%\video-knowledge-output\2026年7月24日全国大早会\webui-bundle\exports\smart-summary-quality.json`

## 仍需完成

1. 为知识视频建立人工关键点 gold set，盲测 Smart Summary 召回率；在此之前不能把自动检查通过等同于生产合格。
2. 对旧式整段单次 ASR 的视频逐步迁移到可恢复分块路线；独立 VAD 已能发现讲话缺口，但不能提供第二份识别文本。
3. P1 适配 Subtitle Edit 的静音边界吸附前，先把 chunk manifest 升级为精确 start/end/overlap，禁止继续用 `index × chunk_seconds` 推算不等长块偏移。
4. 在 8–12 条短/中/长/超长样本上记录缺段率、边界去重准确率、GPU 峰值、完成时长和人工修正时间，再决定是否扩大批量。
5. 将“章节事实包（时间范围 + evidence_id + source_kind）→ 全局 Reduce”进一步显式化；继续复用现有章节产物和 LlamaIndex TreeSummarize 的递归思路，不新增第二套总结状态机。

## 增量：无时间戳分块的绝对时间轴与 VAD 条件密度

更新时间：2026-07-28 12:42:15 +08:00
执行者：Codex / GPT-5.6

生产复核发现第二个样本的旧 `normalized-transcript.json` 生成于分块偏移适配完成之前。FunASR 对每个 5 分钟块只返回文字、没有句级时间戳；旧产物把各块文字错误地铺到整段 6259.583667 秒媒体上，导致片段大范围重叠，并制造 320/326 个 `low_text_density` 假阳性和一条近整片重跑窗口。

| 变更 | 意图 | 决策 | 理由 | 证据 | 生效范围 |
| --- | --- | --- | --- | --- | --- |
| 分块绝对时间轴 | 让无时间戳 FunASR 结果仍能回到真实 5 分钟来源窗口 | 复用 runner 已保存的 `chunk_offset_seconds`、`chunk_seconds` 和 `source_record_index`；仅在各自来源窗口内按字符比例生成粗时间 | 旧式“按整片时长分配”会让不同分块互相重叠，无法导航或局部重跑 | 第二样本修复前 320/326 个低密度告警；修复后 326 段单调覆盖 0–6259.583667 秒，正文和 ID 完全一致 | 只影响无原生句/词时间戳的 FunASR/SenseVoice 分块归一化；不改变正文 |
| 粗时间 provenance | 防止估算时间冒充词级对齐 | 每段写入 `timing_estimation`、`character_proportional_within_source_window`、`precision=coarse` 和来源窗口 | 字符比例只能提供导航与分块归属，不能证明逐字发生时刻 | 本地 `asr_adapter` 回归验证来源窗口和 transformation 均可追溯 | Timeline 导航、质量报告和候选重跑；不声称词级准确 |
| VAD 条件文本密度 | 避免按整块静音时长误判漏转写，同时仍能发现真实稀疏讲话 | 对粗时间段不运行句级 `low_text_density`；改为按来源窗口聚合，并复用既有 `interval_coverage` 计算“字符数 / 独立 Silero 讲话秒数” | 成熟项目以 VAD/真实词时间/对齐结果判断讲话区间；字符数除以整块墙钟时长会把长静音误判为缺字 | faster-whisper/WhisperX/stable-ts 源码均采用 VAD 或对齐时间；第二样本 18 个有字窗口为 3.424658–6.172093 字符/讲话秒，无失败窗口 | 仅有来源哈希匹配的独立 VAD 时评估；没有 VAD 时标记 `not_evaluated`，不自动整片重跑 |
| 生产产物安全刷新 | 消除旧错误时间轴但保持权威文字不变 | 先生成候选并验证 326 个 ID/正文逐项相同，再替换时间与 provenance；随后重建 source arbitration、总结输入包、章节应用、质量门、acceptance 和知识笔记 | 直接覆盖正文会破坏人工/模型纠错链；只修时间证据可安全回流 | 修复报告记录旧/新 SHA、326 段时间变化、`text_identity=true`；Smart Summary 自动检查通过、fresh、`unsupported_numbers=[]` | 仅 `2026年7月24日全国大早会` Bundle；原产物有独立备份 |

生产证据：

- 时间修复报告：`%WORKSPACE_ROOT%\video-knowledge-pipeline\.local\asr-timing-repair-20260728\timing-repair-report.json`
- 修复前备份：`%WORKSPACE_ROOT%\video-knowledge-pipeline\.local\asr-timing-repair-20260728\normalized-transcript.before-chunk-offset-repair.json`
- 刷新后的逐字稿质量：`%WORKSPACE_ROOT%\video-knowledge-output\2026年7月24日全国大早会\webui-bundle\transcript-quality-gate.json`
- 刷新后的总结质量：`%WORKSPACE_ROOT%\video-knowledge-output\2026年7月24日全国大早会\webui-bundle\exports\smart-summary-quality.json`
- 最终合并文档：`%WORKSPACE_ROOT%\video-knowledge-output\2026年7月24日全国大早会\webui-bundle\exports\knowledge-note.md`

离线回归：分块偏移、粗时间 provenance、VAD 条件密度、真实稀疏讲话与静音核销相关集合 `37 passed`。生产刷新后逐字稿质量 `fail_count=0`、`retry_windows=0`；总结压缩率 `0.202667`、证据快照 `fresh`。唯一生产阻断仍是没有人工关键点 gold set；系统保持 `human_review_required`，不伪报完成。

### 下游仲裁 provenance 回归修复

更新时间：2026-07-28 12:48:29 +08:00
执行者：Codex / GPT-5.6

| 意图 | 决策 | 理由 | 证据 | 生效范围 |
| --- | --- | --- | --- | --- |
| 防止正确的粗时间标记在仲裁后丢失 | `transcript_source_arbitration` 透传基础 `TranscriptCue.transformations`，继续复用同一个逐字稿仲裁器，不新增 sidecar 状态机 | 仲裁决定正文来源，不应抹掉时间证据来源；否则 export 内部刷新会把粗时间重新当真实 300 秒讲话 | 真实 Bundle 在第一次导出后重现 1 个 `low_text_density`；补丁后仲裁稿保留 `timing_estimation`，导出后仍为 `response_quality=passed`、`review_segments=0`、`retry_windows=0` | 本地 `source-arbitrated-transcript.json` 的 provenance；正文投票、置信度、SRT、在线路由均不变 |

新增端到端离线回归从 normalized transcript 经过 source arbitration 再进入 `assess_asr_response`，证明 VAD 条件密度仍可识别粗时间。验证批次：逐字稿/ASR/验收 `91 passed`，总结 canonical/freshness/export `41 passed`，仲裁 provenance `15 passed`；Ruff、compileall 与 scoped diff check 均通过。

最终生产状态：

- 逐字稿：`warning`，但 `fail_count=0`、讲话完整性由独立 VAD 验证、18 个有字窗口密度通过、无局部重跑窗口。剩余警告是固定分块没有 overlap、时间精度为 coarse，以及少量标点边界提示。
- 智能总结：自动质量检查通过，压缩率 `0.202667`，数字证据无缺口，证据快照 `fresh`。
- 验收：`human_review_required`，只因逐字稿的已知非致命警告和未提供人工关键点 gold set；不再存在机器可执行的假性缺段修复。

## 增量：精确 chunk manifest 与 Subtitle Edit 静音边界

更新时间：2026-07-28 19:33:57 +08:00
执行者：Codex / GPT-5.6

此前“先升级精确 start/end/overlap，再适配 Subtitle Edit”的 P1 已完成代码和
离线/真实 FFmpeg 验证；本段状态覆盖本文早先的“设计候选”描述，但保留历史记录。

| 变更 | 意图 | 决策 | 理由 | 证据 | 生效范围 |
| --- | --- | --- | --- | --- | --- |
| 精确分块清单 | 让不等长块可准确归一化和局部重跑 | 新增内容寻址 `audio_chunk_manifest.v1`，保存精确源窗口与 overlap | `index × chunk_seconds` 在静音吸附后会产生错误时间轴 | 0–280/280–600 runner 回归验证 offset、gap、checkpoint 和 retry identity | 本地 FunASR 分块、归一化与恢复；不改正文 |
| 静音边界 | 避免硬切话语 | 适配 Subtitle Edit @ `1517bb5c23e1c4072ea829edbc8d08e27cf79289` 的最近未使用静音中点算法；显式 opt-in | 成熟字幕工具已有源码与测试约束，VKP 不自建第二算法/FFmpeg owner | 真实 120 秒合成音频吸附为 0–43、43–78.000031、78.000031–120；三块均 16 kHz mono | `--chunk-boundary-mode silence_snap`；默认 fixed 不变 |
| 兼容和失败语义 | 不让旧 checkpoint 或探测失败静默污染新路线 | revision 绑定；旧 revisionless checkpoint 只兼容 fixed；silencedetect 失败明确记录并等分 | 不同边界下同一 index 不是同一内容 | 扩大 ASR 回归 `81 passed, 1 warning`；Ruff/compileall/CLI/diff check 通过 | 本地 checkpoint 与审计，不触发模型、网络或 fallback |

完整的五字段决策、上游源码路径、测试映射、真实 smoke 和剩余 8–12 条样本门见
`docs/asr-silence-snapped-chunk-manifest-2026-07-28.md`。

## 状态更新：章节事实包 → Global Reduce 已显式化

更新时间：2026-07-28 20:20:27 +08:00
执行者：Codex / GPT-5.6

本文“仍需完成”第 5 项现已完成；本段覆盖早先的待办状态，但保留历史文字。

| 变更 | 意图 | 决策 | 理由 | 证据 | 生效范围 |
| --- | --- | --- | --- | --- | --- |
| 章节事实包 | 把章节时间和证据链带入全局总结 | 复用现有 Workflow citations，生成内容寻址 `smart_summary_chapter_fact_pack.v1` | 章节 Markdown 会丢 `evidence_id/source_kind/fact_status` | 18 focused、42 expanded tests；两个真实 Bundle no-write smoke | Global Reduce 输入和审计，不改章节/逐字稿真源 |
| TreeSummarize repack | 不丢晚段且控制上下文 | 吸收 LlamaIndex 固定源码的叶节点 repack/递归 Reduce；章节 evidence group 只在提示中去重，完整成员仍落盘 | 11 章重复证据 ID 曾产生 9 万字符以上输入 | 真实 11 章输入降为 57,945 chars，全部章节保留 | Reduce prompt，不引入 LlamaIndex 生产依赖 |
| review-gap 输出门 | 防止缺证据候选被模型提升 | `review_gap_not_fact` 不进 eligible set；待复核原文出现在确定栏目即质量失败 | 仅靠提示不能形成确定性保证 | 正/反两组输出门测试通过 | Reduce candidate 安装前；不做外部事实核查 |

完整决策、上游源码运行边界、合同和验证：
`docs/smart-summary-chapter-fact-pack-global-reduce-2026-07-28.md`。

## 状态更新：分块局部修复语义已闭环

更新时间：2026-07-28 22:04:05 +08:00
执行者：Codex / GPT-5.6

| 变更 | 意图 | 决策 | 理由 | 证据 | 生效范围 |
| --- | --- | --- | --- | --- | --- |
| 空结果硬门 | 防止时间戳或空句数组冒充逐字稿 | 只接受顶层正文或 `sentence_info/words` 中实际非空文字；空结果继续使用既有精确重跑路线 | 子进程返回 0 只证明执行结束，不证明讲话内容被覆盖 | `test_timestamps_without_transcript_text_remain_unverified_empty` | 未来本地 FunASR 分块结果；不改历史正文 |
| 遗留子结果隔离 | 防止失败进程读取上一次同名 JSON 并假成功 | 复用确定性块路径，但每次启动上游 child runner 前只删除该块旧输出 | 局部重跑按同一 index 复用路径，旧文件必须与新 attempt 隔离 | `test_failed_child_cannot_reuse_stale_json` | 当前待跑块；不删除 checkpoint 中其他成功块 |
| 局部完成与整片完成分离 | 让精确修复成功但仍有其他缺块时不误报整片完成或操作失败 | 使用 `partial_targeted_completed`、`canonical_complete`、`unresolved_chunk_indexes` 三个独立字段 | 操作是否成功与媒体是否完整是两个状态维度 | 两阶段 fixture 先部分完成，再精确重跑一个块，剩余缺口保持可见 | `--chunk-indexes` 局部修复和机器消费报告 |
| 进度终态一致 | 防止 UI/调度器把局部修复成功显示为失败 | 将 `partial_targeted_completed` 映射为 progress `completed`，消息明确整片仍未完整 | 人类日志、JSON payload 与 JSONL 事件必须表达同一状态 | `tests/test_chunk_repair_semantics.py` 联合 runner 回归 | 本地进度协议；不改变 canonical 质量门 |

本轮只读差异复核确认这些最小修复已经存在于当前并行工作树，因此没有重复编写或覆盖实现。离线验证 `tests/test_chunk_repair_semantics.py` 与 `tests/test_funasr_chunked_runner.py` 合计 `8/8` 通过。实现继续复用 VKP 单一分块 runner、checkpoint、manifest 和进度协议，不新增第二套 ASR/状态机。


## 状态更新：低响度诊断已升级为候选恢复前门

更新时间：2026-07-29 00:23:42 +08:00

执行者：Codex / GPT-5.6

本文早先“低响度仅研究、不接入生产”的安全结论继续成立；新增的是显式、
candidate-only 的本地前门，而不是自动生产预处理。

| 变更 | 意图 | 决策 | 理由 | 证据 | 生效范围 |
| --- | --- | --- | --- | --- | --- |
| 两遍 loudnorm 适配 | 让低电平失败块可以生成一致副本供后续证实 | 复用 NarratoAI 固定源码算法；只输出 16 kHz mono PCM sidecar | 不应重复手工命令，也不应引入其编辑运行时 | 24 focused、75 expanded ASR/VAD/speaker tests；真实 FFmpeg silence/sine smoke | 显式 `audio_loudness_recovery prepare` |
| 近静音与语音边界 | 不把底噪放大成内容 | 近静音先阻断；低电平候选仍保持 `speech_proven=false` 和 `asr_retry_authorized=false` | 响度、非静音都不是 speech evidence | 纯静音未生成候选；非语音正弦波即使生成候选仍被阻断于 ASR 之前 | 不改 Silero/FunASR VAD、逐字稿或默认 route |
| fallback 拒绝 | 失败可见且可恢复 | 无完整测量即失败，不使用上游 pydub/simple gain/MP3 fallback | 静默增益会放大噪声并丢 provenance | invalid-measurement 回归 | 所有低电平候选运行 |

完整适配记录：
`docs/narratoai-low-level-audio-recovery-adapter-2026-07-29.md`。
