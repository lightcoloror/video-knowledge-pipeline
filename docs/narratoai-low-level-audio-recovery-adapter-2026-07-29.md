# NarratoAI 低电平音频候选恢复适配

更新时间：2026-07-29 00:23:42 +08:00

执行者：Codex / GPT-5.6

## 结论

VKP 已把固定上游 NarratoAI 的两遍 FFmpeg EBU R128 `loudnorm`
算法适配为一个本地、可审计、fail-closed 的候选恢复入口：

```powershell
$env:PYTHONPATH='src'

python -m video_knowledge_pipeline.audio_loudness_recovery plan <音频或分块>

python -m video_knowledge_pipeline.audio_loudness_recovery prepare <音频或分块>
```

`prepare` 最多生成一个新的 16 kHz、单声道、16-bit PCM WAV 副本和一份
JSON 报告。同名候选已经存在时默认返回 `candidate_output_exists`；只有显式加入
`--overwrite-candidate` 才会重建，且报告会区分 `exists` 与
`produced_this_run`。它永远不会：

- 覆盖原始音频；
- 自动重跑 ASR；
- 把“非静音”当成“有人讲话”；
- 下载模型、上传文件或调用在线 API；
- 在两遍 `loudnorm` 失败后退回简单增益、pydub 或 MP3 重编码。

即使副本生成成功，终态也是
`candidate_requires_speech_vad`，并保持：

```json
{
  "candidate_only": true,
  "speech_proven": false,
  "asr_retry_authorized": false
}
```

必须再由独立语音 VAD 或人工听审证明存在讲话，才能进入已有的精确局部
ASR 重跑链。

## 固定上游与源码实测

| 项目 | 值 |
| --- | --- |
| 上游 | `linyqh/NarratoAI` |
| 本地源码 | `%WORKSPACE_ROOT%\source-reviews\shot-breakdown-wave-20260721\narratoai` |
| 固定 commit | `0a5dcf5f21f7f40ca77bc38ea6d1d3fd52e32c26` |
| 深读模块 | `app/services/audio_normalizer.py` |
| 复用算法 | 第一遍 `loudnorm=I=-23:TP=-1:LRA=7:print_format=json`；第二遍绑定 `measured_I/LRA/TP/thresh` |
| 拒绝模块 | MoviePy、pydub、numpy RMS、简单增益 fallback、MP3 fallback |

源码复核发现，上游在拿不到 loudnorm 测量值或 FFmpeg 失败时，会退回
pydub 简单增益；输出还固定为 44.1 kHz 立体声。VKP 没有复制这些行为：

- ASR 候选副本固定为 16 kHz 单声道 PCM，减少再次解码和格式差异；
- 第一遍和第二遍都先用 FFmpeg 的单声道格式协商，保证测量与最终输出一致；
- loudnorm JSON 缺字段、字段非数值或出现 `-inf` 时直接失败；
- 只有完整、有限的测量值才允许第二遍；
- 候选文件先写同目录临时 WAV，格式、采样率、声道和 sample width
  通过后再原子安装；
- 渲染前后比较原始音频 SHA-256，源文件发生变化时拒绝安装候选。

## 五字段变更记录

| 变更 | 意图 | 决策 | 理由 | 证据 | 生效范围 |
| --- | --- | --- | --- | --- | --- |
| `audio_loudness_recovery.py` | 为低电平但可能含讲话的失败块提供可恢复副本 | 适配 NarratoAI 两遍 loudnorm；新增 `plan/prepare` 独立前门 | 复用成熟算法，同时不把第三方编辑运行时引入 VKP | 固定源码逐行复核；FFmpeg 本机滤镜帮助确认全部测量字段 | 本地候选音频和 JSON 报告；不改 ASR 默认路线 |
| 近静音硬门 | 防止把静音或底噪放大成“语音” | 先复用 `audio_silence_probe`；活动不足 2 秒或不足 1% 时终止 | 响度归一化只能改变增益，不能证明讲话存在 | 3 秒纯静音 smoke 得到 `near_silence_blocked` 且未生成 WAV | loudnorm 第一遍之前；不修改 VAD 或 chunk manifest |
| 低电平候选状态 | 防止候选副本被误当成修复完成 | 所有输出保持 `speech_proven=false`、`asr_retry_authorized=false` | 非静音也可能只是音乐、噪声或音效 | 3 秒低电平 440 Hz 正弦波生成副本后仍要求 speech VAD | 调度器和人工复核；不能直接进入 canonical transcript |
| 固定 WAV 契约 | 降低本地 ASR 再解码差异 | 第二遍输出 16 kHz、mono、PCM s16le，并在原子安装前用 stdlib `wave` 验证 | VKP 本地 ASR 与说话人链已统一消费 16 kHz mono | 合成低电平 smoke 输出 96,078 bytes，格式门通过 | 新候选 sidecar；源音频字节不变 |
| fail-closed fallback | 避免算法失败时静默放大 | 显式拒绝上游 pydub 简单增益和 MP3 fallback | 简单增益容易放大噪声，也缺少测量 provenance | 无 loudnorm JSON 的离线回归返回 `loudness_measurements_invalid` | 所有候选恢复执行；无 local/cloud fallback |

## 状态机

```text
planned
  ├─ ffmpeg/media/silence probe 失败 → failed
  ├─ 近静音/活动不足             → near_silence_blocked
  └─ 有足够非静音活动
       ├─ loudnorm 测量无效       → loudness_measurements_invalid
       ├─ 响度不低                → normalization_not_needed
       ├─ 仅分析                  → low_level_candidate_detected
       └─ 显式生成副本            → candidate_requires_speech_vad
                                      ├─ speech VAD/人工否定：停止
                                      └─ speech VAD/人工确认：才可建立精确 ASR retry plan
```

`ok=true` 只表示本地诊断流程正常结束，不表示存在讲话，也不表示逐字稿完整。
机器消费者必须读取 `status`、`speech_proven` 和
`asr_retry_authorized`，不能只看 `ok`。

## 验证

离线 focused：

```text
24 passed, 2 skipped, 1 warning
```

扩大到 ASR/VAD/说话人相关集合：

```text
75 passed, 3 skipped, 1 warning
```

覆盖：

- loudnorm 混合日志 JSON 解析；
- 非有限测量值拒绝；
- plan 不执行 FFmpeg；
- 近静音不进入 loudnorm；
- 正常响度不生成副本；
- 低电平只生成候选；
- 16 kHz mono PCM 契约；
- 原始 SHA-256 保持；
- 既有候选默认不覆盖，且不会被误报为本次输出；
- pydub/简单增益 fallback 明确拒绝；
- 四个人工确认词和说话人最终导出回归。

静态验证：

```text
Ruff: passed
compileall: passed
```

真实本地 FFmpeg 合成 smoke：

| 样本 | 结果 | 候选 WAV | `speech_proven` | `asr_retry_authorized` |
| --- | --- | --- | --- | --- |
| 3 秒纯静音 | `near_silence_blocked` | 未生成 | `false` | `false` |
| 3 秒低电平 440 Hz 正弦波 | `candidate_requires_speech_vad` | 已生成 | `false` | `false` |

smoke 产物位于：

`%WORKSPACE_ROOT%\video-knowledge-pipeline\.local\loudness-smoke-v2-20260729`

## 与用户确认的原意/说话人要求

本适配不改文字纠错或说话人链。当前既有回归继续保证：

- `根排期来的嘛` → `根据排期来的嘛`
- `会义纪要` → `会议纪要`
- `发了一分材料` → `发了一份材料`
- `星合系统` → `星河系统`

这些是当前录音的人工作证实，不是全局自动替换规则。未来录音只生成
review candidate；只有 `human_confirmed` 才正式应用。逐字稿必须继续保留
`说话人1/说话人2` 等匿名 cluster；不要求也不允许本模块猜测真实姓名或角色。

系统只还原音视频原意，不对“条款最优”等外部现实事实做真假审查；如果原话如此，
逐字稿应忠实保留。智能总结只能把它表述为录音中的说法，不能篡改原意。

## 剩余缺口

1. 尚未对真实失败分块运行本候选恢复；应先对精确 chunk 做 `plan`，
   再由操作者决定是否本地 `prepare`。
2. 候选生成后仍需复用既有 Silero/faster-whisper speech VAD 或人工听审；
   本模块故意不新增第二套 VAD。
3. 只有 speech VAD 确认、精确 source/chunk SHA 绑定和局部 ASR 结果质量门
   同时通过，才能合并逐字稿。
4. 不应把此入口设为全媒体默认预处理；它只服务低电平失败块。

## 2026-07-29 00:57:47 | Codex / GPT-5.6：独立 speech VAD 与精确重试 lineage

| 变更 | 意图 | 决策 | 理由 | 证据 | 生效范围 |
| --- | --- | --- | --- | --- | --- |
| `audio_loudness_recovery_validation.py` | 防止“放大后有声”被直接当成“有人讲话”并自动重跑 ASR | 直接复用固定 `faster-whisper@ed9a06cd89a93e47838f564998a6c09b655d7f43` 的 Silero VAD，通过现有 `silero_vad_candidate.run_silero_vad_candidate` 建立独立语音证据；只有达到最小时长和占比才生成局部重试计划 | FFmpeg 非静音、响度或波形能量都不能区分讲话、音乐、噪声和测试正弦波 | 固定上游 `VadOptions/get_speech_timestamps` 源码已核对；真实 JFK 语音样本得到 11.0 秒语音、ratio 1.0，低电平正弦波得到 `no_speech_detected`；22 项 focused 与 54 项扩展回归通过 | 仅本地 candidate 校验和 retry plan；不执行 ASR、不改逐字稿、不上传、不 fallback |
| `audio_chunk_manifest.py` | 让局部重试准确绑定原媒体、精确 chunk 和时间偏移 | 在 manifest 中记录父媒体及每个 chunk 的 `bytes + SHA-256`，revision 由稳定 source/strategy/detection/chunk identity 共同计算 | 原 revision 只含路径、大小、mtime 和窗口；内容变化或旧 chunk 重用时约束不够强 | 篡改 revision、父媒体变化、缺 chunk SHA、重绑 chunk SHA 均 fail-closed；真实 manifest 的 recorded/computed revision 一致 | 新生成的 `audio_chunk_manifest.v1`；旧缺哈希 manifest 不能用于低电平候选自动规划，但仍可由原旧流程只读消费 |
| `audio_loudness_recovery_retry_plan.v1` | 把可恢复语音块安全交给既有目标 ASR 链 | retry plan 固定 candidate SHA、父媒体 SHA、manifest SHA/revision、chunk index、局部/全局语音区间和 offset；显式要求 secondary evidence 与质量门 | 候选音频本身不是 canonical transcript，也不能绕过现有局部 ASR 仲裁 | 真实本地 smoke 产物 `jfk-chunk-validation-v2.json` 为 `targeted_retry_planned`，且 `automatic_execution=false`、`canonical_transcript_modified=false` | 仅规划；后续仍须显式本地 ASR、注册为第二证据并重新跑完整性/质量门 |
| 原意纠错与 speaker 合同 | 保证恢复链不会改变本录音的人工确认语义或丢失说话人 | 继续使用现有 human-confirmed 纠错与匿名 speaker 合同：`根据排期来的嘛`、`会议纪要`、`发了一份材料`、`星河系统`；未来录音只生成 review candidate | 词句修复是当前录音的来源忠实度判断，不是全局词典；说话人归属是对话逐字稿的必需证据 | `test_transcript_speaker_source_fidelity.py` 与最终 reader E2E 在 54 项扩展套件中通过 | 当前录音可正式写回；其他录音不得静默替换。总结只还原录音原意，不做外部事实真假审查 |

稳定前门：

```powershell
$env:PYTHONPATH = 'src'
python -m video_knowledge_pipeline.audio_loudness_recovery_validation `
  '<recovery-report.json>' `
  --execute-vad `
  --chunk-manifest '<audio-chunk-manifest.json>' `
  --chunk-index 0
```

关键终态：

- `vad_required`：尚无独立 VAD，禁止 ASR；
- `no_speech_detected` / `speech_evidence_below_threshold`：停止，不生成 retry；
- `speech_candidate_confirmed`：有 speech，但缺父时间线 lineage，仍不能合并；
- `targeted_retry_planned`：只生成精确计划，仍不自动执行；
- `invalid_*_lineage`：哈希、revision、时间边界或路径不一致，fail-closed。

真实本地证据：

`%WORKSPACE_ROOT%\video-knowledge-pipeline\.local\loudness-vad-smoke-20260729\jfk-chunk-validation-v2.json`

验证结果：focused `22 passed`；扩展 ASR/VAD/分块/说话人源忠实度 `54 passed, 1 third-party warning`；Ruff 与 compileall 通过。全程无外部模型、网络、上传或 canonical transcript 写入。
