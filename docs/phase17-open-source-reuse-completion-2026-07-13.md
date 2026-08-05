# Phase 17 开源代码复用改进完成报告

## 2026-07-13 07:00:03 | Codex（GPT-5）

- Scope: transcribe-critic 差异仲裁、Qwen3 ForcedAligner、PySceneDetect、语义章节 Map 到 Global Reduce、CoE 风格一致性、DeepVideoDiscovery/VideoLucy 风格粗到细回看。
- Method: 优先复用本机已审查的真实上游源码和官方运行包，VKP 只补 adapter、数据契约、CLI/MCP、质量门禁与测试。
- Boundary: 本轮没有调用外部 API，没有上传视频、音频、逐字稿或帧；真实模型验证仅使用本地 CUDA 和本地短音频。

## 一、逐项目标完成审计

| 目标 | 实现证据 | 接口证据 | 验证证据 | 状态 |
| --- | --- | --- | --- | --- |
| transcribe-critic 风格差异定位、聚类、匿名仲裁、局部补丁 | `src/video_knowledge_pipeline/asr_diff_adjudication.py`；保留 raw hypothesis，变化需要证据，`adjudicated_no_change` 不计失败 | CLI `asr-diff-adjudication`、`apply-asr-diff-adjudication`；同名 MCP | positioned diff、cluster、匿名 A/B、证据门禁、局部 patch 和数字 tokenizer 测试通过 | 完成 |
| Qwen3 ForcedAligner 时间戳 | `src/video_knowledge_pipeline/qwen3_forced_aligner_runner.py`；官方 `Qwen3ForcedAligner.align()`；SoundFile tuple 绕过 Windows `librosa.load()` 卡死 | `plan-asr --preset qwen3-forced-aligner` -> `run-asr-plan --execute`；alignment 自动保持 sidecar | 1 秒与 10 秒 smoke 均成功；正式入口 `cuda:0`、`bfloat16`、`sdpa`、coverage 1.0、monotonic true | 完成 |
| PySceneDetect 章节与补帧边界 | `scene_detection_adapter.py` 调用 `AdaptiveDetector` / `ContentDetector`，失败时明确 ffmpeg fallback；orchestrator 与 semantic chapter 消费边界 | CLI/MCP `scene-detection` | 三段合成视频识别出 1.0 秒、2.0 秒切点，backend=`pyscenedetect` | 完成 |
| vsummary 风格语义章节 Map -> Global Reduce | `smart_summary_global_reduce.py` 只消费完整章节 Map 和 course map，不读取 raw ASR；不完整 Map 阻断 | CLI/MCP `smart-summary-global-reduce`；`quality_finalize` 接入 | 超预算 8,311 字在 3,000 字预算下均衡为 2,899 字，六章全部保留；元数据超预算时阻断，不丢末章 | 完成 |
| CoE 风格实体/事件一致性且允许证据不足 | `summary_consistency.py` 检查 entity、number、event；`unknown` 不提升为事实，明确数字冲突阻断 | CLI/MCP `summary-consistency-check`；`quality_finalize` 接入 | fixture 验证“四步”对“三步”被阻断，UnknownTool 保持 unknown；真实长视频检测到 10 个数字冲突和 2 个证据不足项 | 完成 |
| DeepVideoDiscovery/VideoLucy 风格粗到细回看 | `video_evidence_query.py` 复用本地 VideoRAG，生成 coarse hits、fine candidates、证据路径和确认状态机 | CLI/MCP `video-evidence-query-plan`、`apply-video-evidence-confirmation` | 五小时 bundle 本地查询得到 8 个 coarse hits、3 个 fine candidates；无证据项进入 recapture/needs_more_evidence；confirmed 必须附证据 | 完成 |

## 二、关键修复

### 2.1 ForcedAligner Windows 卡死

上游 `normalize_audios()` 在接收本地路径时会调用 `librosa.load()`。当前 Windows 环境中，1 秒 WAV 会持续占用 CPU 且数分钟不返回；相同文件通过 `soundfile.read()` 约 0.1 秒完成。VKP 仍使用上游模型和对齐算法，只把输入改成官方支持的 `(numpy.ndarray, sample_rate)`。

真实结果：

- 1 秒：`hello` -> `0.00-0.24s`。
- 10 秒：`hello / 大 / 家 / 好` -> `0.98-1.94s`。
- 正式产物：`%WORKSPACE_ROOT%\qwen-aligner-integration-smoke\transcripts\asr_run_9127eb1a3e8d\raw-asr-output.json`。
- `run-asr-plan` 对 `asr_mode=alignment` 自动跳过 transcript normalization，不覆盖主逐字稿。

### 2.2 Global Reduce 后段丢失

旧实现对完整 prompt 使用 `text[:max_input_chars]`，可能完整删除后半视频章节。新实现：

1. 先构造完整章节 Map。
2. 超预算时为每章均衡分配字符预算。
3. 每章固定保留 section ID、标题、时间范围、头部与尾部内容。
4. 输出 `full_input_chars`、`all_sections_included`、`prompt_within_budget`、`clipped_section_ids`。
5. 章节元数据仍无法放入预算时返回 `blocked_reduce_input_budget`，不执行模型调用，也不删除后段。

### 2.3 ASR diff tokenizer

修正数字正则退化：`100.5` 现在保持为一个 token，空白不参与 diff，避免数字冲突被拆散或时间估计偏移。

## 三、验证结果

- 六项能力组合测试：`75 passed in 69.75s`。
- 全仓回归：`528 passed in 145.95s`。
- Python 源码与测试语法编译：`236` 个文件通过。
- `git diff --check`：无空白错误；仅有既有 LF/CRLF 提示。
- Secret scan：边界修正后 `0` 个真实 key 形态命中。
- Git tracked media scan：`0` 个视频、音频或字幕文件。
- README、AGENT_DISCOVERY、Phase 17 计划和开源最佳实践文档已同步。

## 四、仍需后续质量评测但不影响功能完成

- 在 24 段 current-window gold 上运行 ForcedAligner，计算时间戳中位误差和 P95。
- 用 24 段金标量化 ASR diff 局部补丁对 CER、专名、数字和过度纠错率的净收益。
- 对三个完整视频完成语义章节与智能总结匿名盲评。
- 在更多五小时视频上测量粗到细回看减少的人工浏览时间和云多模态调用数。

这些是质量晋级和默认模型切换门禁，不代表上述六个功能接口缺失。未达到指标前，SenseVoice 仍保持主 ASR，得到大脑仍只作外部产品对照。