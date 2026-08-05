# VKP 本地媒体执行回执与视频创作候选桥

更新时间：2026-07-23 12:36:26 +08:00
执行工具/模型：Codex / GPT-5.6

## 结论

本轮没有引入第二套 ASR、FFmpeg、Timeline、索引、状态机或审核服务。VKP 只增加三类薄适配：

1. 为已经完成的 CrispASR 执行生成 `speech_execution_receipt.v1`。
2. 为既有 VKP FFmpeg 单一出口的已完成调用生成 `ffmpeg_execution_receipt.v1`。
3. 将视频创作侧 `rough_cut_finalize_receipt.v1` 作为候选证据导入，且强制保留 transcript、OCR、temporal provenance 或明确的已知缺口。

视频创作仓继续只读消费；VKP Timeline、Bundle、run registry 仍是真源。

## 固定上游与状态

| 模块 | 固定版本/commit | VKP 状态 | 决策 |
| --- | --- | --- | --- |
| CrispASR | `v0.8.18` / `9deefe8f47273722415e4b4be5d87361b96177c9` | contract implemented；真实 benchmark pending | 仅为既有执行生成回执；不部署第二 ASR |
| VKP FFmpeg outlet | VKP 既有 `media_tools` 与调用链 | receipt adapter implemented | 记录真实 argv、可执行文件哈希、硬件 profile 与显式 fallback |
| rough-cut finalize | 视频创作仓现有 v1 contract | candidate import implemented | 不覆盖 Timeline；人工确认后才可交 videocut-kit |
| llama.cpp | `b8644` / `39b27f0da0271c06986cb31b68bc0fe68e780616` | candidate only | 仅登记本地多模态 evidence provider；不安装/启动/下载 |
| sqlite-vec | `v0.1.7` / `633eecf5067ab12ef331b3c4500c765f8e6d6da0` | candidate only | 先过 Recall@5/10、filtered recall、adjacent coverage；不得成为索引真源 |

## 稳定入口

只读查看候选状态：

```powershell
.\scripts\video-knowledge-local-media-contract.ps1 provider-status
```

三个写入命令都读取一个本地 JSON request；未给 `--write` 时只校验和预览，不落盘：

```powershell
.\scripts\video-knowledge-local-media-contract.ps1 speech-receipt --request <speech-request.json> --write
.\scripts\video-knowledge-local-media-contract.ps1 ffmpeg-receipt --request <ffmpeg-request.json> --write
.\scripts\video-knowledge-local-media-contract.ps1 rough-cut-import --request <rough-cut-request.json> --write
```

request 使用函数参数同名字段。所有输入必须位于 `bundle_dir` 或显式 `allowed_roots` 下。命令不启动 ASR、FFmpeg、模型、网络服务，也不下载或上传文件。

## Speech receipt 约束

- 只接受固定 CrispASR 版本/commit。
- 绑定 binary、model、input audio、arbitrated transcript、word timestamps 和可选 SRT 的 raw SHA-256；JSON 同时绑定 canonical SHA-256。
- 必须提供可见 attempts；GPU 失败后 CPU 重试必须是最后一项，并记录每次耗时。
- 必须记录 chunk、overlap、LCS 去重和标点分段。
- 必须绑定一个已接受/完成的 VKP arbitration JSON；仅填写布尔值不能生成回执。
- 输出转写仍由 VKP 仲裁为权威结果；原始证据不被覆盖。

## FFmpeg receipt 约束

- 只接受既有 outlet ID：`video_creation_pipeline.single_ffmpeg_outlet`。
- `actual_argv` 保存真实可执行路径和完整参数；`command` 同步生成视频创作契约要求的 `ffmpeg` 标准 argv。
- 绑定 FFmpeg 二进制、所有输入与输出 artifact hash。
- NVENC/QSV/AMF/CPU 等 profile 必须显式记录 requested/selected backend。
- fallback 必须显式说明原因；禁止静默 fallback、local/cloud fallback、原地修改源媒体和自动发布。
- builder 只生成回执，不运行 FFmpeg。

## Rough-cut 候选导入约束

- 校验 finalize receipt 自身哈希、嵌套 artifact freshness、人工确认和非执行边界。
- transcript、OCR、temporal 三个 provenance channel 必须各自包含 artifact，或填写明确 gap reason。
- 导入副本位于 `exports/video-creation-contracts`，同时注册 `rough_cut_candidate_import` run。
- 不写或改 Timeline、manifest 真源、人工标签、素材元数据或发布状态。
- `ready_for_boundary_refinement` 只表示可以进入 videocut-kit 的人工确认后边界精修，不表示可渲染或发布。

## 复用与拒绝

已复用：

- VKP `canonical_json`、`file_hash`、`storage.write_json`、`run_artifact_registry`；
- 视频创作侧已经稳定的 receipt schema 与 validator 约束；
- 既有 videocut-kit 边界精修责任边界。

明确拒绝：

- 复制视频创作仓状态机或 private Python runtime；
- 在视频创作仓运行第二套 ASR；
- 新建第二套 FFmpeg orchestration；
- 自动 local/cloud fallback、上传、发布；
- llama.cpp 或 sqlite-vec 覆盖 Timeline、人工标签、元数据或 run registry；
- 未经真实 benchmark 就宣称 CrispASR、llama.cpp、sqlite-vec 已部署或生产可用。

## 验证与剩余缺口

已完成：

- 15 个相关 focused 离线测试；
- 完整离线回归 `1224 passed, 1 warning`；
- Ruff focused、`python -m compileall -q src` 与 `git diff --check` 通过；
- VKP 生成的 speech/FFmpeg receipt 已通过视频创作仓现有 validator；
- provider-status 稳定入口可运行。

剩余真实 benchmark：

1. CrispASR GPU 成功、GPU 失败转 CPU、长媒体分块、overlap/LCS 去重及词时间戳完整性。
2. NVENC/QSV/AMF/CPU 各 execution profile 的真实 FFmpeg 回执。
3. 一份真实 `rough_cut_finalize_receipt.v1` 与 VKP transcript/OCR/temporal provenance 的端到端导入。
4. llama.cpp 本地视觉候选质量/延迟/显存对比。
5. sqlite-vec Recall@5、Recall@10、filtered recall、相邻镜头覆盖率与延迟门。

这些 benchmark 需要用户另行授权实际执行；本轮没有运行模型、FFmpeg、网络调用、上传或发布。

## 2026-07-23 本地真实验证增量

执行者：Codex（GPT-5）；时间：2026-07-23 13:17:02（Asia/Shanghai）。本节只记录本地执行，不包含上传、外部 API 或模型下载。

- FFmpeg 5 秒 1280×720 合成样本：CPU/libx264、NVENC、AMF 实际编码成功；QSV 因 Intel MFX session `-9` 失败，随后经显式操作者策略选择 CPU 成功，未发生静默 fallback。
- 四份实际 `ffmpeg_execution_receipt.v1` 均通过 VKP 与视频创作仓 validator。
- `prepare-cloud-asr-audio` 新增可选 `--receipt-bundle-dir`：沿用原 FFmpeg 调用，成功后自动生成并注册回执；默认不提供时保持原行为。正式 CLI 已对 5 秒本地样本验证成功。
- rough-cut 导入与 sqlite-vec 指标门的现有 fixture/contract 测试通过；它们不等于真实人工 rough-cut receipt 或真实索引质量 benchmark。
- CrispASR 固定源码目录存在，但 `ggml` 与 `c2pa-audio` 子模块未初始化，且没有真实中文模型与已构建二进制，因此不能宣称 GPU、CPU retry、长媒体或词时间戳 benchmark 已完成。
- llama.cpp 固定源码仍仅为候选；随后操作者启动 LM Studio，已用其本地 OpenAI-compatible 服务完成 Qwen3 VL 8B Q4_K_M 与 Qwen3.5 9B Q4_K_M 的真实视觉对比。LM Studio 没有暴露其内部 llama.cpp 精确 commit，因此该结果不能冒充固定 `b8644` 源码 benchmark。
- sqlite-vec 固定源码缺生成头、vendor/发布扩展，Python 环境也未安装 `sqlite_vec`；真实 Recall@5/10、filtered recall、adjacent coverage 仍等待运行时与人工 goldset。

### LM Studio 本地视觉实测

执行者：Codex（GPT-5）；时间：2026-07-23 15:08:34（Asia/Shanghai）。样本为既有 `temporal-frames/0006` 的一张 PPT 帧与完整 8 帧组，所有请求仅发送到 `127.0.0.1:1234`。

| 模型 | 量化 | 单帧 | 8 帧 temporal | 观察 |
| --- | --- | ---: | ---: | --- |
| Qwen3 VL 8B | Q4_K_M | 2.96 s / 1140 tokens | 8.39 s / 7776 tokens | OCR 与稳定画面事实准确；未把手势变化写入 `temporal_changes` |
| Qwen3.5 9B | Q4_K_M | 6.37 s / 1426 tokens | 3.03 s / 7777 tokens | `reasoning_effort=none` 后能识别 PPT 不变与手势变化；版式更细，但存在“主讲时间→发布时间”和坐姿推断等轻微风险 |

加载后显存占用约 9.0–10.7 GB，均在 RTX 5070 Ti Laptop 12 GB 上稳定完成。Qwen3.5 9B 若不关闭 reasoning，会出现单帧 JSON 截断、8 帧正文为空，因此本地契约必须显式设置 `reasoning_effort=none`。当前建议：Qwen3 VL 8B 用作快速单帧默认候选；Qwen3.5 9B 用作疑难帧/temporal 候选，并保留严格 Schema 校验。
