# VKP 第一优先级改进执行记录（2026-07-31）

- 更新时间：2026-07-31 10:16:58（Asia/Shanghai）
- 执行工具/模型：Codex / GPT-5.6
- 边界：没有调用外部模型 API，没有上传音频、视频、帧或逐字稿；没有覆盖生产逐字稿或 Smart Summary；没有 push。

## 1. Qwen3 ForcedAligner 只读 sidecar 自动注册

| 字段 | 记录 |
| --- | --- |
| 意图 | 让旧 Bundle 在不重跑、不替换规范逐字稿的前提下获得词级时间戳。 |
| 决策 | 在 `run_asr_plan` 成功完成 `qwen3-forced-aligner` 后，只对具有 `manifest.json` 的 Bundle 注册 `qwen3_forced_alignment_json` 与 `asr_alignment_sidecars`；审核渲染仅在 sidecar schema、状态、时间单调性、transcript 路径、SHA/文本身份全部一致时使用。 |
| 理由 | 强制对齐是可重建的只读派生证据，不应成为第二份逐字稿真源；文本身份不一致时必须 fail closed。 |
| 证据 | `src/video_knowledge_pipeline/asr_execution.py`、`src/video_knowledge_pipeline/lecture_package.py`、`src/video_knowledge_pipeline/webui_bridge.py`；关键回归 3/3 通过，较早关联回归 12/12 通过。 |
| 生效范围 | Bundle 审核时间戳投影与 manifest provenance；不改变 canonical transcript、Timeline、摘要或远程路由。 |

## 2. 三个 Bundle 的人工关键点边界

| 字段 | 记录 |
| --- | --- |
| 意图 | 补齐 Smart Summary 的人工关键点召回评估入口，同时杜绝模型或规则自我生成 gold set。 |
| 决策 | 保留现有 `review.html` 勾选、草稿自动保存和 `Save to VKP` 原子写回；只有明确的 `human_key_point_confirmed=true` 才能产生 `exports/human-key-points.json`。本轮不伪造三份人工确认文件。 |
| 理由 | 用户排除人工审核后，系统可以准备入口，但不能把摘要中的候选事实冒充人工金标准。 |
| 证据 | 三个历史 Bundle 均已有 `review.html`、`timeline.json` 和 `smart-summary.codex.md`；均尚无 `review-notes.json` / `human-key-points.json`。`human_keypoint_review.py` 的严格写回门已存在。 |
| 生效范围 | 三个 Bundle 的人工评估准备状态；不影响已有逐字稿和总结正文。 |

## 3. CAM++ / MOSS 说话人 A/B

| 字段 | 记录 |
| --- | --- |
| 意图 | 在同一 300 秒双人窗口比较级联 SenseVoice+CAM++ 与端到端 MOSS，而不是只看是否产生两个 speaker label。 |
| 决策 | CAM++ 保留既有真实结果；MOSS 使用隔离 Python 3.11 GPU venv、本地模型快照和上游 `mtd-subtitle` CLI。发现上游默认 2048 token 会让 300 秒任务在 178.44 秒处成功退出后，直接复用官方 `--max-new-tokens` 参数，VKP 默认 8192、允许 2048–65536 的显式覆盖。 |
| 理由 | 上游 MOSS 要求 Transformers 5，而现有 Qwen/FunASR 环境锁定 Transformers 4.57.6；隔离运行避免破坏生产 ASR。复用上游生成预算比复制推理或后处理更可维护。 |
| 证据 | 模型已从大陆镜像写入 `.local/models/moss-transcribe-diarize`：19 文件、1,833,163,202 字节；权重 SHA-256 `9a0ceb4ab7330357db3ff583dba8d83625d5b733b00e1d55d6970e11b07026c4` 与镜像 LFS 元数据一致。完整 GPU 重跑 147 段、2 位说话人、298.84 秒、说话人覆盖 99.4378%，3916 token、156.51 秒。严格评测：MOSS DER 0.30926667、cpCER 0.32207207、tcpCER 0.45795796；CAM++ 对照 DER 0.24396667、cpCER 0.36036036、tcpCER 0.52852853。 |
| 生效范围 | 只作为本地 A/B 候选，不覆盖正式逐字稿。MOSS 的说话人分离 DER 劣于 CAM++，但说话人归属文字错误率更低；两者均远未达到 0.05 生产门，必须继续保留为评测候选。 |

机器对比产物位于 `.local/moss-campp-ab-20260731/transcripts/asr-ab-sample/asr-ab-comparison.json` 和 `.local/moss-campp-ab-20260731/moss-transcript-stability-evaluation.json`。本次没有人工匿名听审，因此不能仅凭机器指标提升生产默认路线。

## 4. 模型网关容量约束

| 字段 | 记录 |
| --- | --- |
| 意图 | 最大化稳定并行，同时防止在未知账号配额下突发撞 429。 |
| 决策 | 所有 29 个已启用远程 profile 默认 `max_parallel_requests=1`；Groq 精确模型使用官方已核实额度：`qwen/qwen3.6-27b` 30 RPM / 8K TPM，Whisper 两条 profile 为 20 RPM。ASR/OCR 的容量门不再要求虚构 TPM，文本/视觉仍要求 RPM+TPM+并发。 |
| 理由 | Google、Mistral、SiliconFlow、Ark 的实际额度依账号/项目/层级变化，不能把公共示例冒充本账号额度；音频供应商通常发布 ASH/ASD 而非 TPM。 |
| 证据 | Groq 官方：`https://console.groq.com/docs/rate-limits`；Gemini 官方明确要求在 AI Studio 查看 active limits：`https://ai.google.dev/gemini-api/docs/rate-limits`。设置备份：`.local/model-api-settings.before-capacity-20260731.json`；变更前 SHA-256 `781ba546252a831c375c12d3a9150f8a1872da12dd444e1e2b63fe8f04a0dee0`，变更后 `b08c1172b2e76276029291acab19b1556c5480b016f5adaaea78ccdefa428df2`。网关回归 21/21 通过。 |
| 生效范围 | LiteLLM deployment 限流和本地 render/doctor；没有 provider 请求。容量字段变化会形成新的 route revision，后续远程任务应使用新 consent。 |

当前仍有 6 条生产 route 缺本账号真实 RPM/TPM：Mistral OCR、Gemini text/vision、Ark DeepSeek text、SiliconFlow PaddleOCR-VL vision、SiliconFlow GLM-4.5V vision。它们已被并发 1 保护，但 `capacity_policy_ready` 正确保持 false。

## 5. 本地多模态 Lane C

| 字段 | 记录 |
| --- | --- |
| 意图 | 用与 Lane A/B 完全相同的 `temporal-6x8-fixed-20260719`（6 组 × 8 帧）完成本地 OpenAI-compatible 多模态比较。 |
| 决策 | 只接受 LM Studio `127.0.0.1:1234` 的本地模型；禁止自动切换到在线模型或不同样本。 |
| 理由 | 换样本会改变 OCR 密度和时序难度，跨本地/远程 fallback 会破坏比较身份。 |
| 证据 | Lane A/B 已在 `.local/model-gateway-abc-20260730`；本轮 TCP 探针确认 1234 未监听，`lms status` 显示 server OFF。 |
| 生效范围 | 固定 48 帧 A/B/C 验收；没有启动远程调用，没有伪造 Lane C。 |

操作者只需在 LM Studio 加载 `Qwen3 VL 8B Q4_K_M` 并开启 Local Server（1234）。服务可用后，VKP 可继续生成 `lane-c-proxy-local.json` 和离线 comparison。

## 验证汇总

- Qwen sidecar 关键回归：3 passed。
- MOSS readiness / adapter / cache / generation budget 定向回归：18 passed，53 deselected，1 warning。
- 网关 capacity 回归：21 passed。
- `python -m compileall -q src`：通过。
- `git diff --check`（本轮相关文件）：通过。
- 外部模型调用：0；媒体上传：0；MOSS 模型下载：1,833,163,202 字节（大陆镜像）；本地 GPU MOSS 推理：2 次（首轮截断诊断、修复后完整重跑）；LM Studio Lane C 调用：0。
