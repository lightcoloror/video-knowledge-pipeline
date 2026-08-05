# sherpa-onnx 说话人分离证据适配

更新时间：2026-07-28 22:48:04（Asia/Shanghai）
执行工具/模型：Codex（GPT-5.6）
状态：适配合同与离线回归已实现；本地 CLI、模型权重和真实音频试验尚未安装/执行。

## 结论

VKP 现在有一条独立于 ASR 引擎的本地说话人证据路线：

```text
现有带时间戳逐字稿
        +
16 kHz 单声道 WAV
        ↓
sherpa-onnx 官方 speaker-diarization CLI
        ↓
start/end/speaker 区间
        ↓
WhisperX 最大时间重叠分配规则
        ↓
speaker-assigned-transcript.candidate.json
```

该路线不会修改原始 ASR 文本、段落 ID、顺序、时间戳或现有说话人标签。输出始终是候选证据，必须经过人工或既有仲裁质量门后才能提升为最终逐字稿。

## 固定上游

### sherpa-onnx

- 仓库：`k2-fsa/sherpa-onnx`
- 本地源码：`%WORKSPACE_ROOT%\source-reviews\picinterpreter-offline-asr-20260728\sherpa-onnx`
- commit：`75e1fc31e747194c546787ec7b40a7e0b390dc4b`
- 许可证：Apache-2.0
- 复用入口：官方 `sherpa-onnx-offline-speaker-diarization` CLI
- 复用范围：Pyannote segmentation ONNX、3D-Speaker embedding ONNX、fast clustering、说话人区间输出
- 未复制：模型推理、聚类算法、音频读取和模型下载逻辑

源码证据：

- `sherpa-onnx/csrc/sherpa-onnx-offline-speaker-diarization.cc`
- `sherpa-onnx/csrc/offline-speaker-diarization.cc`
- `sherpa-onnx/csrc/offline-speaker-segmentation-model-config.cc`
- `sherpa-onnx/csrc/speaker-embedding-extractor.cc`
- `sherpa-onnx/csrc/offline-speaker-diarization-result.cc`

官方 CLI 同时注册 `segmentation.provider` 和 `embedding.provider`，允许 `cpu/cuda/coreml`，并稳定输出：

```text
0.125 -- 1.750 speaker_00
1.750 -- 3.000 speaker_01
```

### WhisperX

- 仓库：`m-bain/whisperX`
- 本地源码：`%WORKSPACE_ROOT%\video-creation-source-review\sources\whisperX`
- commit：`5f2f9d4320dd93a7d12f5ba2495eef7e0a5af963`
- 许可证：BSD-2-Clause
- 参考入口：`whisperx/diarize.py::assign_word_speakers`
- 参考范围：按 ASR 段与说话人区间的交集时长选择主说话人
- VKP 改造：独立实现轻量最大重叠分配；默认禁止 nearest fill；增加覆盖率、主导率、冲突和未覆盖状态

## 变动 1：官方 CLI 薄适配器

- **意图**：给任意 VKP 带时间戳逐字稿补充本地说话人证据，不要求更换 ASR 模型。
- **决策**：只计划和调用 sherpa-onnx 官方 CLI；使用精确 CLI、音频、逐字稿和两个 ONNX 文件哈希。
- **理由**：说话人分离是独立证据层，不应为了获得 speaker label 再跑一套完整 ASR，也不应在 VKP 重写成熟模型推理。
- **证据**：固定 sherpa-onnx 源码的官方 CLI 已实现 segmentation → embedding → clustering → interval 输出。
- **生效范围**：`src/video_knowledge_pipeline/speaker_diarization_evidence.py`；不影响 SenseVoice、FunASR、MOSS 或在线 ASR 默认路由。

安全边界：

- 默认 `provider=cuda`，同时传给 segmentation 与 embedding。
- 不自动回退 CPU；CUDA 不可用时本次运行失败并保留证据。
- 不自动下载 CLI 或模型。
- 仅接受经本地校验的 16 kHz 单声道 WAV；音频转换继续使用 VKP 既有 FFmpeg 出口，不新增第二套媒体处理器。
- 文件哈希变化后执行前阻断。

## 变动 2：说话人区间映射

- **意图**：把独立 diarization 区间安全地映射到已有逐字稿段落。
- **决策**：采用 WhisperX 的“最大交集时长”思路；同时要求最低时间覆盖率与最低主导率。
- **理由**：时间交集是可追溯证据；“距离最近的说话人”会把静音或未覆盖区错误贴给某个人。
- **证据**：固定 WhisperX 源码将最近填充设计为可选项；VKP 明确关闭该选项。
- **生效范围**：仅生成 `speaker-assigned-transcript.candidate.json`，原逐字稿保持字节不变。

默认质量门：

- `min_coverage_ratio=0.50`
- `min_dominance_ratio=0.60`
- 多说话人接近均分：`ambiguous_overlap`
- 完全无交集：`uncovered`
- 原稿已有说话人且候选冲突：`existing_conflicts_with_candidate`
- 禁止静默覆盖已有 speaker
- 禁止拆段、合段、重排或更改文本

## 变动 3：稳定 CLI

- **意图**：让操作者和自动流程有明确、可审计的本地入口。
- **决策**：提供模块 CLI 及 `scripts/speaker-diarization-evidence.ps1` 稳定包装入口，分为 `plan` 与 `run`；`run` 默认仍为 preview，必须显式 `--execute`。
- **理由**：当前主 `cli.py` 有大量并发修改；独立模块前门避免覆盖其他 owner 成果，也保持执行边界清晰。
- **证据**：计划 JSON 保存精确命令、输入哈希、模型哈希、provider、上游 commit 和阻断项。
- **生效范围**：仅此说话人适配器。

稳定包装入口会设置 `PYTHONPATH`；模块入口仍可供自动化直接调用。

计划：

```powershell
.\scripts\speaker-diarization-evidence.ps1 plan `
  '<bundle>' '<16k-mono.wav>' '<timed-transcript.json>' `
  --command-path '<sherpa-onnx-offline-speaker-diarization.exe>' `
  --segmentation-model '<pyannote-segmentation-model.onnx>' `
  --embedding-model '<3dspeaker-embedding.onnx>' `
  --provider cuda
```

预览：

```powershell
.\scripts\speaker-diarization-evidence.ps1 run `
  '<bundle>\transcripts\speaker-diarization\sherpa-onnx-plan.json'
```

执行：

```powershell
.\scripts\speaker-diarization-evidence.ps1 run `
  '<bundle>\transcripts\speaker-diarization\sherpa-onnx-plan.json' `
  --execute
```

## 验证

离线 fixture 回归：

```powershell
python -m pytest -q tests\test_speaker_diarization_evidence.py `
  --basetemp C:\tmp\vkp-speaker-diarization-20260728-2250 `
  -p no:cacheprovider
```

结果：`5 passed`。

覆盖：

- 官方 CLI 混合 stdout 解析；
- 最大重叠分配；
- ambiguous / uncovered / existing conflict；
- CUDA 参数与禁止 CPU fallback；
- 音频、逐字稿、模型的精确 SHA-256 锁定；
- 输入变化后 fail-closed；
- fake execution 生成候选逐字稿且原稿字节不变。

## 当前真实运行缺口

以下条件尚不成立，因此不能把该路线误报为“已可生产运行”：

- `sherpa-onnx-offline-speaker-diarization` 本地 CLI 未发现；
- Pyannote segmentation ONNX 未发现；
- 3D-Speaker embedding ONNX 未发现；
- 未用真实 CUDA runtime 验证两个 provider 均为 `cuda`；
- 未对真实双人中文录音测 DER、说话人切换误差、RTF 和显存；
- 未完成候选 speaker 到最终逐字稿的人审提升流程。

下一阶段需用户另行同意下载本地运行包和模型。下载后只做一段脱敏短音频 A/B；验收至少记录：

- speaker count 是否正确；
- DER 或人工说话人区间错误率；
- ASR 段落的 speaker 覆盖率/歧义率；
- GPU provider 是否真实生效；
- RTF、峰值显存、失败恢复；
- MOSS、sherpa-onnx 与现有无 speaker 路线的对比。
