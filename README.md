# video-knowledge-pipeline

独立的视频知识提取工具。目标不是做视频摘要，而是尽量把知识类讲解视频中的语音、屏幕文字、图表、公式、代码、板书、界面状态、操作变化和非文字视觉信息提取成可读、可检索、可复习的资料。

## 当前边界

- 本仓库从 `question-video-knowledge` 抽出“看视频流程”。
- 图文型截图只走文档视觉分支，可继续复用 `ebook_markdown_pipeline`。
- 非纯图文截图走多模态视觉 API。
- 连续变化画面先抽 5-12 帧，再走多帧视觉理解。
- Agent 在线多模态执行使用 bundle/provider/index 级授权；详见 `docs/agent-online-vision-consent.md`。该授权只解决项目门禁，不能覆盖 Agent 平台的数据外发策略。
- ASR 优先本地 SenseVoice/FunASR，避免中文知识视频音频上传云端。
- 面向 OpenClaw/内容资产/朋友圈联动时，本项目只输出结构化素材、时间戳证据和风险提示；所有 `content_assets` 都是 `review_required=true`、`publication_allowed=false`，不能自动生成发布稿或自动发布。

## 架构文档

具体架构图、模块边界、当前整合进度和开源源码审查后的定位见：

- `docs\architecture.md`
- `docs\openclaw-integration.md`
- `docs\volcengine-coding-plan-cline-integration.md`

## 常用命令

```powershell
python -m video_knowledge_pipeline.cli config-status

.\scripts\video-knowledge.ps1 openclaw-bridge-status

.\scripts\video-knowledge.ps1 openclaw-bridge-doctor

.\scripts\video-knowledge.ps1 openclaw-live-smoke `
  --bundle-dir D:\video-knowledge-runs\lesson-001\webui-bundle `
  --write-report

.\scripts\start-openclaw-http-background.ps1

.\scripts\openclaw-http-task.ps1 register

.\scripts\openclaw-http-task.ps1 start

.\scripts\openclaw-http-startup-folder.ps1 status

.\scripts\openclaw-http-startup-folder.ps1 install

.\scripts\video-knowledge.ps1 openclaw-docker-contract-check

.\scripts\video-knowledge.ps1 openclaw-video-plan `
  "https://example.com/video"

.\scripts\video-knowledge.ps1 openclaw-video-ingest `
  D:\path\to\downloaded-or-local.mp4 `
  --workspace D:\video-knowledge-runs\openclaw-lesson-001 `
  --title "课程名"

.\scripts\video-knowledge.ps1 openclaw-video-link `
  "https://example.com/video"

.\scripts\video-knowledge.ps1 openclaw-video-from-vdo-handoff `
  --summary-path D:\path\to\vdo\summary.json `
  --review-checklist-path D:\path\to\vdo\review-checklist.json

.\scripts\video-knowledge.ps1 openclaw-video-ingest-vdo-handoff `
  --summary-path D:\path\to\vdo\summary.json `
  --review-checklist-path D:\path\to\vdo\review-checklist.json

.\scripts\video-knowledge.ps1 content-asset-status `
  D:\video-knowledge-runs\lesson-001\webui-bundle

.\scripts\video-knowledge.ps1 batch-content-asset-status `
  D:\video-knowledge-runs

.\scripts\video-knowledge.ps1 content-handoff-pack `
  D:\video-knowledge-runs

.\scripts\video-knowledge.ps1 video-moment-index `
  D:\video-knowledge-runs\lesson-001\webui-bundle `
  --query "<关键词或疑难点>"

.\scripts\video-knowledge.ps1 long-video-memory-pack `
  D:\video-knowledge-runs\lesson-001\webui-bundle

.\scripts\video-knowledge.ps1 video-rag-pack `
  D:\video-knowledge-runs\lesson-001\webui-bundle `
  --query "<问题或术语>"

.\scripts\video-knowledge.ps1 transcript-source-arbitration `
  D:\video-knowledge-runs\lesson-001\webui-bundle

.\scripts\video-knowledge.ps1 term-arbitration-codex `
  D:\video-knowledge-runs\lesson-001\webui-bundle

.\scripts\video-knowledge.ps1 validate-term-arbitration-codex-result `
  D:\video-knowledge-runs\lesson-001\webui-bundle `
  --input-json D:\video-knowledge-runs\lesson-001\webui-bundle\term-arbitration-codex-result.codex.md

.\scripts\video-knowledge.ps1 term-correction-status `
  D:\video-knowledge-runs\lesson-001\webui-bundle

.\scripts\video-knowledge.ps1 term-correction-closure `
  D:\video-knowledge-runs\lesson-001\webui-bundle `
  --input-json D:\video-knowledge-runs\lesson-001\webui-bundle\term-arbitration-codex-result.codex.md

.\scripts\video-knowledge.ps1 term-correction-impact-report `
  D:\video-knowledge-runs\lesson-001\webui-bundle

.\scripts\video-knowledge.ps1 external-capability-pack `
  D:\video-knowledge-runs\lesson-001\webui-bundle `
  --query "<关键词或问题>"

.\scripts\video-knowledge.ps1 online-model-api-matrix --output-dir D:\video-knowledge-runs\lesson-001\webui-bundle\exports

.\scripts\video-knowledge.ps1 online-model-api summary_rewrite --input-text "<要改写的证据包>"

.\scripts\start-openclaw-http.cmd

sh scripts/openclaw-video-knowledge-call.sh plan "https://example.com/video"

sh scripts/openclaw-video-knowledge-call.sh live-smoke /mnt/used-by-codex/video-knowledge-pipeline/openclaw-runs/lesson-001/webui-bundle

sh scripts/openclaw-video-knowledge-call.sh content-status /mnt/used-by-codex/video-knowledge-pipeline/openclaw-runs/lesson-001/webui-bundle

sh scripts/openclaw-video-knowledge-call.sh batch-content-status /mnt/used-by-codex/video-knowledge-pipeline/openclaw-runs

sh scripts/openclaw-video-knowledge-call.sh content-handoff-pack /mnt/used-by-codex/video-knowledge-pipeline/openclaw-runs

第一轮分析采用独立证据原则：ASR/字幕、抽帧、ebook/OCR 图文结构化、打标器、多模态复核先各自完整产出结果；timeline fuser / triage 后续再做互证、冲突标记和纠错，不用某一路早期结果去限制另一条证据链的完整完成。
详细代码级抽帧策略见 [`docs/frame-sampling-strategy.md`](docs/frame-sampling-strategy.md)。
疑难点补帧使用 `plan-supplemental-frame-sampling` 先生成本地补帧计划，再用 `run-frame-recapture-plan --execute` 执行；这一步只跑本地 ffmpeg，不调用云多模态。
`export-knowledge-note` 同时导出 `exports/smart-summary.md` 和 `exports/smart-summary-codex-prompt.md`：前者对标得到大脑“智能总结”。可用 `build-smart-summary-chapters` 先生成 `exports/smart-summary-chapters.md` / `exports/course-map.md`，章节包会写入 VideoRAG/VTimeLLM-style `citation_digest`，把 transcript、moment、OCR/ebook、视觉、连续片段和 review gap 证据压成可引用表；再用 `smart-summary-section-workflow` / `smart-summary-section-editor` / `smart-summary-section-apply` 做章节级人工或 Codex 修订。`generate-smart-summary-with-codex` 在没有 `--input-md` 时只准备纠正版逐字稿、语义章节、证据包和 LLM 交接状态，不再生成规则拼接的 scaffold；只有带 `codex_final`、`codex_llm_rewrite_final` 或受支持 agent-LLM 标记的 `smart-summary.codex.md` / `smart-summary.llm.md` 才会被最终导出采用。
真正的 LLM 改写层优先走章节级流程：先运行 `postprocess-asr-transcript <webui-bundle>` 把本地 ASR 小碎片合并、生成 `readable-transcript.*`，默认使用 readable 本地标点/断句模式，并写入 `corrected-transcript.*`；再运行 `run-smart-summary-section-llm-rewrite <webui-bundle> --provider-config <json-or-file>`。该命令默认只生成章节请求计划和 `exports/smart-summary-section-llm-rewrite.md`，显式加 `--execute` 才会逐章调用 OpenAI-compatible 文本模型，写出 `exports/smart-summary-section-llm-revisions.json`，并复用 `smart-summary-section-apply` 汇总安装到 `exports/smart-summary.codex.md`。旧的 whole-summary 入口 `prepare-smart-summary-llm-rewrite` / `run-smart-summary-llm-rewrite` 仍保留，适合短视频或手工 Codex 改写；长视频默认不要一次塞完整转写给模型。执行成功后运行 `export-knowledge-note` 刷新最终人类可读文件。provider config/API key 只允许来自运行时参数或环境变量，不写入报告或 manifest。
智能总结的目标结构、质量门槛和多源证据融合策略见 [`docs/smart-summary-best-practices.md`](docs/smart-summary-best-practices.md)。转写语义纠错的完整目标见 [`docs/transcript-semantic-correction-to-smart-summary-goal-2026-07-06.md`](docs/transcript-semantic-correction-to-smart-summary-goal-2026-07-06.md)，更具体的“所有 ASR/字幕疑似错词”通用闭环总纲见 [`docs/all-asr-subtitle-suspect-word-semantic-correction-loop-2026-07-07.md`](docs/all-asr-subtitle-suspect-word-semantic-correction-loop-2026-07-07.md)，规格入口见 [`docs/general-asr-subtitle-semantic-correction-loop-2026-07-06.md`](docs/general-asr-subtitle-semantic-correction-loop-2026-07-06.md)，详细规格版见 [`docs/general-asr-subtitle-semantic-correction-loop-detailed-spec-2026-07-07.md`](docs/general-asr-subtitle-semantic-correction-loop-detailed-spec-2026-07-07.md)：术语/工具名仲裁只是其中一个高优先级子模块，凡是 ASR/字幕中被 OCR、画面、网页简介、上下文或人工标注证明可能出错的词语，都应进入语义纠正并影响纠正版 transcript 与最终智能总结。
vsummary 源码审查和已复用的文本 LLM provider 网关见 [`docs/vsummary-source-review.md`](docs/vsummary-source-review.md)；新增 `text-llm-provider-smoke` 可先做无密钥泄漏的在线/云端文本模型调用计划。

方舟 Coding Plan / Cline 接入见 [`docs/volcengine-coding-plan-cline-integration.md`](docs/volcengine-coding-plan-cline-integration.md)。统一在线模型 API 适配层使用 LiteLLM Proxy（安装 `pip install -e .[online]`）；既有 OpenAI-compatible/Gemini 轻量适配仅保留为显式 legacy 兼容路线，不自动 fallback。版本化 Provider Catalog 覆盖文本、视觉、ASR、OCR 并提供 `litellm_native` 扩展；详见 [`docs/online-model-provider-catalog-2026-07-15.md`](docs/online-model-provider-catalog-2026-07-15.md)。默认只生成计划；真实远程执行必须通过 Trusted Broker、保存的 remote-approved route、consent v2、逐文件 SHA-256 清单和调用/费用上限。API Key 以本机 DPAPI 密文保存，不写入 manifest、报告、MCP 参数或文档。
PrideWood/bilinote 源码审查和已复用模块见 [docs/bilinote-pridewood-source-review.md](docs/bilinote-pridewood-source-review.md)；已落地字幕清洗/合并、转写校对 prompt、长 transcript 分块和 `transcript-correction-pack` CLI/MCP，不复制下载后端或整套 UI。
外部 AI 视频项目的局部能力复用见 [docs/external-project-reuse-implementation-2026-07-04.md](docs/external-project-reuse-implementation-2026-07-04.md)：`video-moment-index` 负责时间定位，`long-video-memory-pack` 负责长视频分层记忆，`video-rag-pack` 输出本地 JSONL 检索包，并会把 `content-candidate-pack` 中的每条候选素材生成独立 `content_candidate` retrieval chunk；`video-rag-search` 提供本地查询并支持 `--retrieval-backend keyword|sqlite|vector`，其中 `keyword` 默认、`sqlite` 写本地持久索引、`vector` 只是未来占位且不会启动服务，`video-rag-service-plan` / `video-rag-serve` 提供显式启动的轻量 HTTP 检索服务，`vlm_preprocess.py` 统一 Qwen/InternVL-style 图像缩放压缩和多图输入准备，`content-candidate-pack` 在 `export-knowledge-note` 时生成带 evidence path 和可选 `Citation Digest` 的内容素材候选 JSON/Markdown；`content-asset-status`、`batch-content-asset-status` 和 `content-handoff-pack` 会在存在 `human-sample-eval.json/md` 时附带候选素材可用率、证据充分率和多模态净帮助率，但这些只是人审质量信号，不允许自动发布或当作事实；`external-capability-pack` 一键汇总长视频分层总结、时间定位、视频 RAG、本地 VLM adapter、内容素材生成五类能力。全部默认本地执行，不下载、不调用云模型、不启动本地 VLM 服务。后续仍值得继续复用的模块、优先级和边界见 [docs/external-code-module-reuse-backlog-2026-07-04.md](docs/external-code-module-reuse-backlog-2026-07-04.md)；更短的入口判断表见 [docs/external-code-reuse-decision-map-2026-07-04.md](docs/external-code-reuse-decision-map-2026-07-04.md)；当前剩余可复用模块的收束清单见 [docs/external-code-reuse-remaining-modules-2026-07-05.md](docs/external-code-reuse-remaining-modules-2026-07-05.md)；“哪些项目已经榨干、哪些模块还值得继续吸收”的当前状态见 [docs/external-code-reuse-exhaustion-status-2026-07-05.md](docs/external-code-reuse-exhaustion-status-2026-07-05.md)；模块级总清单和下一步优先级见 [docs/external-open-source-reuse-module-inventory-2026-07-06.md](docs/external-open-source-reuse-module-inventory-2026-07-06.md)。
继续开发前的最新行动入口见 [docs/external-code-reuse-latest-action-map-2026-07-06.md](docs/external-code-reuse-latest-action-map-2026-07-06.md)：它把近期已经落地的外部项目模块复用、仍值得继续吸收的模块、停止继续搬运的边界和下一步开发顺序收束成一页。更完整的可读索引见 [docs/external-code-reuse-readable-index-2026-07-06.md](docs/external-code-reuse-readable-index-2026-07-06.md)。更细的开发导航见 [docs/external-code-reuse-current-module-map-2026-07-06.md](docs/external-code-reuse-current-module-map-2026-07-06.md)。更偏执行口径的下一步决策表见 [docs/external-code-reuse-next-module-decisions-2026-07-06.md](docs/external-code-reuse-next-module-decisions-2026-07-06.md)。最新的收束版开发导航见 [docs/external-code-reuse-closure-and-next-actions-2026-07-06.md](docs/external-code-reuse-closure-and-next-actions-2026-07-06.md)。需要判断“新外部项目到底复制什么、不复制什么、怎么验收”时，看 [docs/external-code-reuse-practical-playbook-2026-07-06.md](docs/external-code-reuse-practical-playbook-2026-07-06.md)。需要直接进入下一批可复用代码模块队列时，看 [docs/external-code-reuse-next-code-modules-2026-07-06.md](docs/external-code-reuse-next-code-modules-2026-07-06.md)。
BiliNote 转录能力已扩展为 `prepare-transcript-edit-session` / `apply-transcript-edits`：前者生成静态 `transcript-editor.html` 和 `transcript-edits.template.json`，并登记 `prepare_transcript_edit_session` run 等待人工输入；后者显式导入人工审核后的 edits JSON，写出 `human-corrected-transcript.*`，并登记 `apply_transcript_edits` run，不会自动调用 LLM。`bilinote-mind-map-prompt-pack --bundle-dir <webui-bundle>` 会从 bundle 的最佳 transcript sidecar 生成 BiliNote-style 思维导图 JSON prompt pack，写出 `exports/bilinote-mind-map-prompt-pack.*`，并登记 `bilinote_mind_map_prompt_pack` run；它不发起模型调用，也不声称已经生成脑图。
统一视频工作台已新增 `export-video-workbench <webui-bundle>`，生成 `video-workbench.html/json` 和 `mcp-video-workbench.args.json`。它把视频播放器、timeline、task console、review、transcript editor、smart-summary section editor、内容素材候选和关键产物入口合到一个静态页面；内容素材候选面板会读取 `content-candidate-pack` 与 `human-sample-eval`，显示候选可用率/证据充分率，并支持“未抽样 / 抽样证据不足 / 可继续加工 / 有Citation / 缺Citation”过滤；候选包若已存在 `smart-summary-chapters.json`，还会携带章节级 `Citation Digest` 并在工作台候选表格中显示 citation 摘要，方便回链证据。工作台还会读取已有 `vision-provider-smoke.json`、`vision-provider-matrix.json`、`local-vlm-serving-smoke.json`，在 Provider / 本地 VLM 面板显示模型服务和云 provider 的只读状态；这些 smoke 命令会登记 `runs/*/run.json`，所以 task console/workbench 的 vision 队列也能显示 provider/VLM ready、needs_retry 或 needs_execution。工作台还会读取 `run-artifact-registry.json`，在“外部复用能力”面板按 `时间定位 / VTimeLLM`、`长视频 memory / MovieChat`、`VideoRAG 本地检索`、`本地 VLM adapter`、`内容素材能力包` 汇总 ready / action_required / missing 状态、artifact links 和 retry command；并复用 `subqueue-action-plan` 在“下一步调度”面板显示 `action_kind`、`primary_command`、`blocked_reason` 和人工/机器分流。页面不直接写盘、不调用云模型、不启动本地 VLM 服务，真实执行仍走既有 CLI/MCP/preflight。
字幕/ASR 多源仲裁已落地为 `transcript-source-arbitration`：它复用 BiliNote 字幕解析、平台字幕/自带字幕、ASR sidecar、`term-resolution.json` 和可选术语表，生成 `source-arbitrated-transcript.json/srt/md` 与 `transcript-source-arbitration.md`。默认本地执行、不调用 LLM；高置信纠错会 promoted 到 `manifest.corrected_transcript_*`，低置信冲突进入 review rows。`quality_summary.summary_input_policy`、`review_segment_refs` 和 `trusted_segment_indexes` 会被 `smart-summary-input-pack` 读取为 `transcript_quality_policy`，让智能总结层知道哪些转写可直接用、哪些时间段必须先复核；`video-workbench` 也会显示 summary input mode、safe segment count、待复核字幕段和 transcript editor/review/arbitration 命令。
术语/工具名纠错闭环使用 `term-arbitration-codex` 生成 Codex 语义仲裁包；人工或 Codex 回复应先交给 `validate-term-arbitration-codex-result` 预检，再由 `term-correction-closure --input-json` 写入术语词典、纠正版转写和最终导出。`term-correction-status` 是 CLI/MCP/agent 的只读轮询入口；当 Codex 回复无可接受决策或解析失败时，它会返回 `needs_codex_term_validation`，且闭环不会写入 `term-arbitration-glossary.json` 或 `source-arbitrated-transcript.json`。这个入口现在还会返回 `codex_substitute`：包含 `term-arbitration-codex-prompt.md`、`term-arbitration-codex-pack.json`、自动生成的可填写 `term-arbitration-codex-result.codex.md`、预检命令、导入闭环命令和 acceptance rule，方便 Codex 暂时代替在线文本 LLM 做语义判断而不接触云 API。
证据仲裁转写纠错主链路优先使用 `transcript-evidence-correction-pipeline <webui-bundle>` / MCP `transcript_evidence_correction_pipeline`。它把 `SenseVoice/FunASR 原始 ASR + 自带字幕/本地字幕/网页上下文 + 青龙打标器时间轴/话题/画面状态 + OCR/ebook/多模态证据 + 本地 agent/可选在线 LLM 语义仲裁` 串成单一入口，默认执行本地仲裁、语义证据包、本地 agent 可读化和 `transcript-quality-gate`，写出 `source-arbitrated-transcript.*`、`agent-readable-transcript.*`、`transcript-quality-gate.*` 与稳定 `corrected-transcript.*`；`export-knowledge-note` 会再次运行质量门禁，把结果写入 `full-transcript.md` 头部、`export-summary.json` 和 manifest，并且 `smart-summary-input-pack` 会优先使用 human/LLM/corrected transcript，高于旧的 `source-arbitrated-transcript.*` 与 raw/normalized ASR。只有显式 `--execute-readable-llm` 才调用标点/断句 LLM，只有显式 `--promote-readable-llm` 才把在线可读性结果提升为最终 corrected transcript；只有显式 `--execute-llm` 才调用语义仲裁 LLM，只有再加 `--auto-apply-high-confidence` 才把本地校验通过的高置信语义结果写回并刷新 `full-transcript.md` / `smart-summary.md`。如果只想单独跑最终可读化和门禁，可以用 `agent-readable-transcript-rewrite <webui-bundle> --agent-name openclaw --promote` 与 `transcript-quality-gate <webui-bundle>`。详细说明见 `docs/transcript-evidence-correction-pipeline.md`。 跑完后用 `transcript-main-route-status <webui-bundle>` / MCP `transcript_main_route_status` 检查主路线是否闭合：postprocess、conflict index、corrected/source-arbitrated transcript、full-transcript、smart-summary 质量门禁、WhisperX/ASR A-B advisory。

通用 ASR/字幕语义纠错闭环使用 `transcript-semantic-correction-pack` 发现不局限于术语的疑似错词，包括专名、数字、动作、概念、普通 ASR 错词、标点和断句。安全链路是：`transcript-semantic-correction-pack -> transcript-semantic-correction-codex-draft 或 transcript-semantic-correction-llm-draft -> validate-transcript-semantic-correction -> transcript-semantic-correction-closure --refresh-exports -> transcript-semantic-correction-status（不带 --refresh-exports 时仍可按旧链路手动运行 export-knowledge-note -> transcript-semantic-correction-impact-report -> transcript-semantic-readable-impact-report -> transcript-semantic-summary-impact-report）`。Codex 或在线 LLM 只负责判断 evidence pack；VKP 本地校验 JSON、拒绝低置信或高风险数字猜测、把安全决策写入 `source-arbitrated-transcript.*`，并用 impact report 检查 `full-transcript.md` / `smart-summary.md` / 内容素材候选是否仍残留已接受错词。MCP 工具名为 `transcript_semantic_correction_pack`、`transcript_semantic_correction_llm_draft`、`validate_transcript_semantic_correction`、`transcript_semantic_correction_closure`、`transcript_semantic_correction_impact_report`、`transcript_semantic_readable_impact_report`、`transcript_semantic_summary_impact_report`、`transcript_semantic_correction_status`。单视频验收使用 `transcript-semantic-acceptance <bundle_dir>` / MCP `transcript_semantic_acceptance`，它复用 batch acceptance 的 per-bundle 判定逻辑，生成只读 `transcript-semantic-acceptance.json/md`，不跑 ASR、视觉、closure、export 或云调用。 批量验收使用 `transcript-semantic-batch-acceptance <batch_input>` / MCP `transcript_semantic_batch_acceptance`，它只读汇总 3-5 个 bundle 是否真的完成 pack、Codex/LLM/人工判断、closure、export 和 impact，不跑 ASR、不调用云模型；可用 `--limit` / MCP `limit` 控制本次最多检查多少个 bundle。批量重试队列使用 `transcript-semantic-repair-queue <batch_input>` / MCP `transcript_semantic_repair_queue`，默认只生成 `transcript-semantic-repair-queue.json/md`，列出每个 bundle 的 `action_key`、进度、可复制重试命令、是否需要人工或显式 LLM 执行；当 semantic/readable impact 已过但缺少智能总结吸收证明时，会给出 `run_summary_impact`。智能总结吸收纠错的质量证明使用 `transcript-semantic-summary-impact-report <bundle_dir>` / MCP `transcript_semantic_summary_impact_report`：它可选接收 `--baseline-summary-path`，检查已接受纠错在最终 `smart-summary.md` 中是否还有原错词残留、是否命中纠正词、是否能证明总结层真正受益。需要推进队列时用 `transcript-semantic-repair-run <batch_input>` / MCP `transcript_semantic_repair_run`：默认仍是 preview，显式 `--execute-safe-actions` 只执行本地 pack、LLM prompt preview、validate、export、impact/readable-impact 等安全动作；不会调用 ASR/视觉/下载，closure 还需要额外 `--allow-closure`。如果要让 repair-run 批量执行在线/云端文本 LLM 语义判断，必须同时传 `--allow-llm --provider-config <json-or-profile>`，并可用 `--llm-limit` 控制每个 bundle 送入 provider 的候选数；provider config 不写入报告。 当 repair-run 已经把本地可安全项推进完、剩余项需要 Codex/LLM/人工语义判断时，使用 `transcript-semantic-batch-review-pack <batch_input>` / MCP `transcript_semantic_batch_review_pack` 生成跨 bundle 的 `transcript-semantic-batch-review-pack.json/md`、`transcript-semantic-batch-review-notes.todo.json` 和 `transcript-semantic-batch-codex-review-prompt.md`；填好 todo 后用 `transcript-semantic-batch-import-review-notes <review_json>；也可以先用 `transcript-semantic-batch-codex-review-draft <review_pack_json>` / MCP `transcript_semantic_batch_codex_review_draft` 生成保守本地 Codex 草稿，它只自动接受明确已知错词和安全保留项，其余标记为 `needs_more_evidence`，不会调用云模型。` / MCP `transcript_semantic_batch_import_review_notes` 拆回各 bundle 并复用单 bundle 的 import/validate 门禁，closure 仍需后续显式执行。 `openclaw-live-smoke` 也会读取同一批量验收：传 `--bundle-dir` 时检查单 bundle，传 `--semantic-batch-input` / `--semantic-target-bundle-count` 时检查 3-5 bundle，并可用 `--semantic-limit` 限制扫描量，结果写入 `openclaw-live-smoke-report.*`。

Phase 17 质量优先入口已经接入：`processing_profiles.quality` 默认采用 SenseVoice 快速底稿 + Qwen3-ASR-1.7B 独立第二假设（显存失败只提示显式改用 0.6B）+ `Qwen3-ForcedAligner-0.6B`；Qwen 长音频按 300 秒本地分块。`asr-consensus` 保留两套假设并只把真实差异送入证据仲裁，`quality-benchmark build/run/report` 生成 24 段人工评测模板并计算 CER、标点/句界、实体/数字、过度纠错和时间戳指标，`semantic-chapter-plan` 取代默认固定 8 桶，`build-smart-summary-chapters` 默认使用语义章节。`transcript-evidence-correction-pipeline --quality-profile quality` 先做事实纠正、最后再做标点/断句；本地 agent substitute 只标记为启发式草稿。文本 LLM 仅在 profile 中 `data_export_allowed=true`、provider 可用且批量低于 20 次/120,000 字符时自动执行，超限必须 preflight。`export-quality-console` 生成静态质量页并与 task console / video workbench 互跳。实现与未完成的真实 benchmark 边界见 [`docs/plans/2026-07-10-phase-17-quality-first-transcript-summary-reset.md`](docs/plans/2026-07-10-phase-17-quality-first-transcript-summary-reset.md)。

Qwen3 ForcedAligner 已通过本地正式入口实测。Windows 下不要把 WAV 路径直接交给上游 `librosa.load()`；VKP runner 会用 SoundFile 读取并传入官方支持的 `(audio, sample_rate)`，避免本地路径解码卡死。`smart-summary-global-reduce` 对超预算章节 Map 采用按章节均衡压缩，保证首尾和所有章节元数据进入 Reduce；元数据本身仍超预算时返回 `blocked_reduce_input_budget`，不静默删除后半段。

大陆网络安装 Qwen3-ASR 时优先使用官方 README 推荐的 ModelScope，不依赖 Hugging Face Xet：先在 ASR 环境安装 `qwen-asr`，再执行 `modelscope download --model Qwen/Qwen3-ASR-1.7B --local_dir %LOCAL_MODEL_ROOT%\models\Qwen3-ASR-1.7B` 和 ForcedAligner 对应命令。`plan-asr --preset qwen3-asr-1.7b` 会优先发现 `%LOCAL_MODEL_ROOT%\models`，避免重复联网。人工基准构建支持重复传入 `--media-path` 与显式 `--execute-clips`；审核页可直接播放 24 个本地 WAV，并下载填好人工真值的 manifest。`quality-benchmark build-summary-review <manifest>` 会生成旧 VKP、当前 VKP、Get笔记外部对照的匿名 A/B/C 评分页；评分下载后用 `quality-benchmark apply-summary-review <private-json> --scores-json <scores-json>` 解盲并刷新门禁。Get笔记只用于评测，永不进入纠错证据。模型切换门禁固定比较 `qwen3_asr_1_7b`：人工参考、CER、专名错误、数字错误、时间戳与 3 个视频总结盲评任一未完成或不达标时，`model_switch_allowed=false`，继续保留 SenseVoice 为主模型。
平台官方/半官方视频转文字入口线索见 [docs/platform-video-transcript-source-notes.md](docs/platform-video-transcript-source-notes.md)；这些只作为外部 transcript/summary 候选来源，不替代本地 ASR 和证据链。
默认本地视频采样按课程证据优先，且长视频默认均匀覆盖全片：`--sample-interval 5 --max-frames 720 --sample-mode balanced-long-video`。1 小时以内约 5 秒一帧；超过 1 小时时会自动放大实际间隔，例如 5 小时约 25 秒一帧，避免只截前 1 小时。可选 `--sample-mode dense-local` 保持 5 秒密集本地抽帧并自动放大本地帧预算；`--sample-mode triage-first` 用约 70% 预算均匀覆盖全片，剩余预算留给场景变化/字幕语义补点。这个只是本地抽帧/本地 OCR/本地图文结构化证据预算，不代表会把这些帧发送给在线多模态模型；在线视觉仍必须经过 preflight、显式确认和小批次 `--limit`。
.\scripts\video-knowledge.ps1 acceptance-run `
  D:\path\to\lesson.mp4 `
  D:\video-knowledge-runs\lesson-001 `
  --title "课程名" `
  --sample-interval 5 --max-frames 720

.\scripts\video-knowledge.ps1 acceptance-bundle-run `
  D:\video-knowledge-runs\lesson-001\webui-bundle `
  --title "课程名"

.\scripts\video-knowledge.ps1 acceptance-bundle-run `
  D:\video-knowledge-runs\lesson-001\webui-bundle `
  --execute-vision `
  --confirm-vision-calls <preflight_calls> `
  --confirm-vision-indexes "<preflight_indexes>"

.\scripts\video-knowledge.ps1 bundle-next-action `
  D:\video-knowledge-runs\lesson-001\webui-bundle

.\scripts\video-knowledge.ps1 bundle-advance `
  D:\video-knowledge-runs\lesson-001\webui-bundle

.\scripts\video-knowledge.ps1 bundle-advance `
  D:\video-knowledge-runs\lesson-001\webui-bundle `
  --execute `
  --confirm-vision-calls <preflight_calls> `
  --confirm-vision-indexes "<preflight_indexes>"

.\scripts\video-knowledge.ps1 prepare-local-video-run `
  D:\path\to\lesson.mp4 `
  D:\video-knowledge-runs\lesson-001 `
  --title "课程名"

.\scripts\video-knowledge.ps1 prepare-local-video-run `
  D:\path\to\lesson.mp4 `
  D:\video-knowledge-runs\lesson-001 `
  --title "课程名" `
  --build-initial-bundle `
  --sample-interval 5 --max-frames 720

.\scripts\video-knowledge.ps1 asr-env-status `
  --output-dir D:\video-knowledge-runs\asr-env-check `
  --write

.\scripts\video-knowledge.ps1 asr-smoke `
  D:\path\to\lesson.mp4 `
  --output-dir D:\video-knowledge-runs\asr-smoke `
  --duration-seconds 30

.\scripts\video-knowledge.ps1 batch-run `
  D:\path\to\batch-manifest.json `
  --resume

.\scripts\video-knowledge.ps1 batch-repair-run `
  D:\path\to\batch-acceptance-summary.json

.\scripts\video-knowledge.ps1 batch-repair-run `
  D:\path\to\batch-acceptance-summary.json `
  --allow-ocr `
  --execute `
  --limit 1

.\scripts\video-knowledge.ps1 run-screen-text-recovery `
  D:\path\to\webui-bundle `
  --execute-crops

python -m video_knowledge_pipeline.cli test-vision-provider `
  --provider-config '{"provider":"gemini","model":"gemini-2.5-flash"}'

python -m video_knowledge_pipeline.cli vision-execution-preflight `
  D:\path\to\webui-bundle

python -m video_knowledge_pipeline.cli vision-execution-preflight `
  D:\path\to\webui-bundle `
  --semantic-indexes "2,5" `
  --semantic-limit 0 `
  --no-temporal

python -m video_knowledge_pipeline.cli controlled-execution-check `
  D:\path\to\webui-bundle

python -m video_knowledge_pipeline.cli acceptance-check `
  D:\path\to\webui-bundle

python -m video_knowledge_pipeline.cli prepare-review-session `
  D:\path\to\webui-bundle `
  --limit 0

python -m video_knowledge_pipeline.cli review-closure-status `
  D:\path\to\webui-bundle

python -m video_knowledge_pipeline.cli validate-review-notes `
  D:\path\to\webui-bundle

python -m video_knowledge_pipeline.cli apply-review-notes `
  D:\path\to\webui-bundle

python -m video_knowledge_pipeline.cli vision-provider-smoke `
  --provider agnes `
  --bundle-dir D:\path\to\webui-bundle

python -m video_knowledge_pipeline.cli vision-provider-matrix `
  --providers "local_qwen_vl,volcengine_coding_plan,gemini,openai,agnes" `
  --bundle-dir D:\path\to\webui-bundle

python -m video_knowledge_pipeline.cli local-vlm-adapter-plan

python -m video_knowledge_pipeline.cli run-video-frame-router `
  D:\path\to\webui-bundle

python -m video_knowledge_pipeline.cli run-multimodal-frame-analysis `
  D:\path\to\webui-bundle `
  --limit 19 `
  --provider-config '{"provider":"gemini","model":"gemini-2.5-flash"}'

python -m video_knowledge_pipeline.cli run-multimodal-frame-analysis `
  D:\path\to\webui-bundle `
  --execute `
  --limit 19 `
  --indexes "2,5" `
  --confirm-vision-calls <preflight_calls> `
  --confirm-vision-indexes "<preflight_indexes>"

python -m video_knowledge_pipeline.cli run-temporal-frame-groups `
  D:\path\to\webui-bundle `
  --execute `
  --frame-count 8

python -m video_knowledge_pipeline.cli run-temporal-visual-analysis `
  D:\path\to\webui-bundle `
  --execute `
  --frame-count 8 `
  --indexes "58,59" `
  --confirm-vision-calls <preflight_calls> `
  --confirm-vision-indexes "<preflight_indexes>"

python -m video_knowledge_pipeline.cli export-knowledge-note `
  D:\path\to\webui-bundle `
  --title "课程名"

python -m video_knowledge_pipeline.cli content-asset-status `
  D:\path\to\webui-bundle

python -m video_knowledge_pipeline.cli batch-content-asset-status `
  D:\path\to\bundle-parent

python -m video_knowledge_pipeline.cli content-handoff-pack `
  D:\path\to\bundle-parent

python -m video_knowledge_pipeline.cli vision-analysis-run-log `
  D:\path\to\webui-bundle

python -m video_knowledge_pipeline.cli vision-analysis-restore-plan `
  D:\path\to\webui-bundle `
  --run-id "semantic_frame-..."

python -m video_knowledge_pipeline.cli vision-analysis-apply-restore `
  D:\path\to\webui-bundle `
  --plan-json D:\path\to\webui-bundle\vision-restore-plan.json

.\scripts\video-knowledge.ps1 plan-asr `
  D:\path\to\workspace `
  D:\path\to\lesson.mp4 `
  --preset sensevoice `
  --model iic/SenseVoiceSmall

.\scripts\video-knowledge.ps1 plan-whisperx-alignment `
  D:\path\to\workspace `
  D:\path\to\lesson.mp4 `
  --language zh
```

`acceptance-run` 是本地视频的推荐验收入口。它会串起：

- `prepare-local-video-run`：准备本地运行目录，默认建立初始 `webui-bundle`
- `run-video-frame-router`：画面类型路由
- `run-visual-structure`：图文截图解析分支，复用 `ebook_markdown_pipeline`；命令行直接调用默认仍可预览，任务控制台和新 bundle 的 MCP args 会按统一 `ebook_pipeline` 配置生成稳定执行命令
- `high-res-tile-plan`：InternVL-style 高分辨率 tile 证据包；当 ebook/OCR 返回空、wrapper-only、低信息量，或 PPT/表格/软件界面小字需要补救时，默认只规划 tile，显式 `--execute-tiles` 才在 bundle 内写 `high-res-tiles\`
- `tile-result-import-build`：把 high-res tile plan 与已有 `.json` / `.txt` / `.md` tile 结果文件归一化为 `tile-result-import.json`，不执行 OCR/VLM
- `tile-result-merge`：消费 high-res tile 的 OCR/VLM/人工结果；默认 preview，显式 `--execute` 才写回 `visual_text` / `structured_visual`，空结果、wrapper-only、低置信结果只进入复核，不清除 blocker
- `vlm_preprocess.py`：Qwen/InternVL-style VLM 输入准备共享层；单帧、多帧组和 provider smoke 共用它做本地缩放、JPEG 压缩、字节数统计和证据路径保留
- `timeline-alignment-audit`：VTimeLLM-style 时间轴审计；检查 ASR 起止、抽帧/截图时间、青龙打标时间和 review_start 是否冲突，只写报告不改 timeline
- `run-temporal-frame-groups`：连续片段 5-12 帧证据组，显式 `--execute-temporal-groups` 才真实抽帧
- `vision-execution-preflight`：真实视觉执行门禁，会在 temporal frame groups 之后运行，确保同一轮新生成的帧组也纳入确认批次
- `run-multimodal-frame-analysis`：多模态单帧理解，默认只预览，显式 `--execute-vision` 且确认匹配后才调用 API
- `run-temporal-visual-analysis`：连续片段理解，显式 `--execute-vision` 才调用 API
- `audit-knowledge-coverage`、`bundle-status-report`、`export-knowledge-note`

它会写出：

- `acceptance-report.md`：人类可读验收报告
- `acceptance-run.json`：agent 可读结构化状态

默认不上传音频、不调用云端视觉 API。图文截图解析使用统一 `ebook_pipeline` profile 控制推荐执行参数：`execute_default/include_routes/limit/timeout_seconds`；它只调用本机 `ebook_markdown_pipeline`，不替代多模态理解。多模态候选批量和帧组数量默认读取统一 `vision_execution` profile，命令行显式传入 `--semantic-limit`、`--temporal-limit`、`--frame-count` 时才覆盖配置。即使传入 `--execute-vision`，验收流程也会先运行 `vision-execution-preflight`；provider/key 和候选批次通过后，还必须传入匹配的 `--confirm-vision-calls` 与 `--confirm-vision-indexes` 才会真正调用模型。

OpenClaw/Telegram 调用入口是 `openclaw-video-plan`、`openclaw-video-ingest`、`openclaw-video-link`，也可以启动 `scripts\start-openclaw-http.cmd` 后通过 `http://host.docker.internal:8931/call` 调用同名 `openclaw_video_*` 工具。HTTP host/port/path 来自统一配置 `config\video-knowledge-pipeline.json -> services.openclaw_http`，不要在 Docker/Telegram 脚本里另存一份端口。视频链接识别、下载规划、真实下载边界全部复用 `%WORKSPACE_ROOT%\video-download-orchestrator`；本项目只接收 URL 规划结果或本地媒体路径并生成知识化 workspace / `webui-bundle`。默认 `openclaw-video-link` 只规划，不下载；真实下载必须显式传入 `--allow-download --actor-id <telegram-user-id> --confirm-download`，并仍由 `video-download-orchestrator openclaw-execute` 执行。

Docker/OpenClaw 容器里可用 `scripts/openclaw-video-knowledge-call.sh` 或 `examples/openclaw/openclaw_video_knowledge_call.py`。它会读取 `VKP_API_BASE`，并把 `/mnt/used-by-codex/...` 翻译回宿主机 `%WORKSPACE_ROOT%\...` 后再调用 HTTP bridge。

验收报告会区分：

- `Workflow`：这次调度是否跑通。
- `Content` / `Status`：当前知识包是否还需要机器动作或人工复核。
- `Bundle Next Action`：下一步推荐工具、MCP args 和是否需要人工。

如果已经有 `webui-bundle`，用 `acceptance-bundle-run` 续跑后半段验收，不会重新准备视频或重新生成 bundle。

验收后继续推进时：

- `bundle-next-action`：只看下一步安全动作。
- `bundle-advance`：执行或预览一个安全动作，默认不调用云端、不做真实 OCR/抽帧；即使显式 `--execute`，多模态也按统一配置里的小批量 profile 运行，当前默认是 `multimodal_limit=19` / `temporal_limit=3` / `frame_count=8`。
- `bundle-advance-queue`：连续推进到阻塞或达到步数上限。
- `bundle-advance-log`：查看推进历史。
- `controlled-execution-check`：机器可读地检查 preflight、批次确认、视觉审计和恢复链路是否齐备。
- `vision-execution-preflight`：真实视觉执行前检查 provider、候选规模、预计 API 调用数、写入字段和恢复链路。
- `vision-provider-smoke`：provider 不确定时先做文本、单图、多图 JSON smoke，报告不保存 API key，并显示脱敏请求 URL、endpoint 类型、代理环境是否存在和证据图片选择情况。
- `vision-provider-matrix`：当单个 provider 卡住时，一次比较多个 provider profile；PowerShell 里逗号列表要加引号，例如 `--providers "local_qwen_vl,volcengine_coding_plan,gemini,openai,agnes"`。
- `acceptance-check`：统一验收状态，汇总 provider、coverage、review lifecycle、export freshness 和下一步。
- `prepare-review-session`：生成可编辑的人工审核模板、`review-pack.md/json`、`review-notes.todo.json` 和 `review-closure-status.md/json`；`--limit 0` 表示列出全部开放目标，`--group-by reason|suggested_status|route` 可切换分组。
- `review-closure-status`：统计人工复核 total/open/closed、无效导入行、按原因分组和下一批推荐命令。
- `validate-review-notes`：导入前校验审核 JSON，阻止未知/重复 index 或空 correction 字段误清 blocker。
- `apply-review-notes`：把已校验的人工审核结果非破坏式写回 timeline、coverage、导出、acceptance、status、review HTML 和复核进度。
- `vision-analysis-run-log`：查看单帧/连续帧视觉执行历史，包括每次写入 timeline 的受控字段 diff。
- `vision-analysis-restore-plan`：根据某次视觉执行审计生成恢复计划，默认只写人工审核文件，不直接修改 `timeline.json`。
- `vision-analysis-apply-restore`：执行已审核的恢复计划；默认 dry-run，真正写回必须同时传 `--execute` 和匹配的 `--confirm-run-id`。

视觉 API 执行有门禁：如果 `bundle-advance --execute`、`acceptance-run --execute-vision`、`acceptance-bundle-run --execute-vision`、`run-multimodal-frame-analysis --execute` 或 `run-temporal-visual-analysis --execute` 准备触发单帧或连续帧视觉 API，会先自动运行 `vision-execution-preflight`。如果 provider key、候选规模或恢复链路检查不通过，流程会返回 `vision_preflight_blocked` / `vision_provider_not_ready` 和 preflight 报告路径，不会调用模型，也不会生成一批失败的模型调用结果。preflight 通过后还必须显式传入匹配的 `--confirm-vision-calls` 和 `--confirm-vision-indexes`，否则返回 `vision_confirmation_required`。

真实执行视觉 API 前，先运行 `vision-execution-preflight`。它会写 `vision-execution-preflight.json/md`，并在 manifest 中登记 `mcp-vision-execution-preflight.args.json`。报告会列出 provider/key 状态、单帧/连续帧候选数、预计 API 调用数、将写入的 timeline 字段、审计/恢复产物、阻塞项，以及需要复制到 `bundle-advance --execute` 的确认值；不保存 API key。

如果要人工指定单帧批次，用 `--semantic-indexes ... --no-temporal` 运行 preflight，或在 `run-multimodal-frame-analysis --execute --indexes` 中直接指定。连续片段批次同理，用 `--temporal-indexes ... --no-semantic` 或 `run-temporal-visual-analysis --execute --indexes`。底层执行器会把 `--indexes` 透传给 preflight，确认值和实际候选 index 必须一致；已存在 `visual_understanding` / `temporal_visual_understanding` 的片段会被跳过，避免重复覆盖。注意 `--semantic-limit 0` / `--temporal-limit 0` 表示该分支全量候选，不是关闭分支；关闭分支请用 `--no-semantic` / `--no-temporal`。

preflight 会为 direct 执行器写确认版 MCP args，例如 `mcp-run-multimodal-frame-analysis-confirmed.args.json` 和 `mcp-run-temporal-visual-analysis-confirmed.args.json`，并在 Markdown 的 commands 区给出已填入确认值的 CLI 命令。这些文件只保存候选 index、limit、frame_count、确认值和脱敏 provider/model 配置，不保存 API key；如果 base_url 带疑似 key/token query，也不会写入确认 args。`bundle-advance` 的确认值必须由它自己的下一步动作 gate 产生；全局 preflight 不生成 confirmed `bundle-advance` args，避免在 index filter 或跨分支批次下误跑。

本机人工或普通命令行也可以直接运行 MCP args 文件：`.\scripts\video-knowledge.ps1 mcp-call <tool_name> <args.json>`。这个本地前门会读取 JSON、调用同名项目函数，并过滤不适用于该函数的多余字段；它不是云端 MCP server，也不会绕过 `execute`、preflight、确认值或 API key 门禁。

真实执行前可以先跑 `.\scripts\video-knowledge.ps1 mcp-audit-bundle <webui-bundle>`。它不会调用模型或修改 timeline，只静态检查 manifest 中登记的 MCP args 文件是否存在、工具是否受支持、JSON 是否可读、必需参数是否齐全，以及哪些字段会被本地桥接过滤。

每次 `run-multimodal-frame-analysis` 或 `run-temporal-visual-analysis` 执行/导入都会追加 `vision-analysis-runs.jsonl`，并刷新人类可读的 `vision-analysis-runs.md`。审计记录只保存 provider/model/执行状态、候选 index、报告路径和 `visual_understanding` / `temporal_visual_understanding` / `quality_issues` / `integrated_visual` 等受控字段的变更摘要及已过滤的结构化 before/after 值；不保存 API key、prompt 或模型原始响应。需要撤销某次模型写入时，先运行 `vision-analysis-restore-plan` 生成 `vision-restore-plan.json/md` 供人工审核；确认无误后再运行 `vision-analysis-apply-restore --execute --confirm-run-id <run_id>`。恢复执行会写 `vision-restore-runs.jsonl/md`，并刷新 coverage、quality audit 和 repair status。

视觉 run audit 还会保存脱敏的 `execution_control`：preflight 路径、expected/received confirmation、是否 confirmed、门禁状态。这样即使是直接调用 `run-multimodal-frame-analysis --execute` 或 `run-temporal-visual-analysis --execute`，事后也能看出这次模型调用是被哪一次确认放行的。

通过 `run-multimodal-frame-analysis --execute`、`run-temporal-visual-analysis --execute` 或 `bundle-advance --execute` 成功完成视觉写入后，返回值会包含 `vision_restore_hint`，其中包括本次 `run_id`、`vision-analysis-restore-plan` 命令，以及恢复计划审核后的 dry-run / execute 命令。`bundle-advance-runs.jsonl/md` 也会保留对应的 `vision_restore_plan_command`，方便 agent 从统一推进入口继续生成恢复计划。

`bundle-status-report` 会汇总可控真实执行链条：preflight 是否存在、最近是否停在确认 gate、视觉 run audit 是否存在、是否已有恢复计划/恢复执行记录，以及最近 run 的 restore-plan 命令。它会读取 `vision-analysis-runs.jsonl` 里的 `execution_control`，所以直接调用多模态/连续帧执行器时触发的确认门禁也会被状态报告识别。

如果 agent 需要直接判断能否进入真实视觉执行，用 `controlled-execution-check`。它会输出 checklist、`ready_for_real_vision_execution` 和下一步建议，并写 `controlled-execution-check.json/md`。检查清单会区分“有视觉审计记录”和“最近 run 确实写入了可恢复的 timeline 字段”；确认后空跑、解析失败或没有写入的 run 不会被误判为可恢复成果。

连续片段理解有前置顺序：如果时间片是 `temporal_sequence` / `mixed` 但还没有 `temporal_frame_paths`，`bundle-next-action` 会先推荐 `run_temporal_frame_groups`，不会直接跳到 `run_temporal_visual_analysis`。

`prepare-local-video-run` 是更底层的本地视频准备入口。它会生成：

- `video-knowledge-run.md`：人类可读的运行报告和下一步
- `video-knowledge-run.json`：agent 可读的结构化状态
- `source\video-source-provenance.md/json`：视频来源记录
- `transcripts\<asr_run_id>\asr-run-plan.json`：本地 SenseVoice/FunASR ASR 计划
- `transcripts\<asr_run_id>\raw-asr-output.json`：执行后统一保存的 ASR 原始输出
- `transcripts\<asr_run_id>\asr-run-report.md`：执行预览/执行结果报告

默认只规划 ASR；加 `--execute-asr` 才会真正执行本地 ASR。

## 统一配置源

项目运行端口和本地服务入口统一读取：

- `config\video-knowledge-pipeline.json`

当前包含：

- `review_webui`：静态 WebUI bundle 入口，默认是 `webui-bundle\review.html`。
- `task-console.html`：每个 WebUI bundle 里的轻量任务控制台，集中展示 ASR、OCR/ebook、疑难点 triage、多模态复核、导出和审核页入口，并读取 `run-artifact-registry.json` / `runs/*/run.json` 显示“处理队列”和“任务历史”、失败项、下一步动作和重试命令；`review.html` 仍是详细审核主界面。
- `ebook_markdown_pipeline_http`：图文截图解析 HTTP bridge 的 host/port/path。
- `mcp`：本项目 MCP 的 stdio 入口说明。
- `vision_execution`：多模态执行的非密钥默认 profile，包括 provider、model、单帧批量上限、连续片段批量上限和帧组数量。

CLI、MCP、验收流程、bundle 推进器、生成的 WebUI bundle manifest、图文截图解析报告和测试都通过 `video_knowledge_pipeline.config` 读取同一个配置。临时切换配置时只设置 `VIDEO_KNOWLEDGE_PIPELINE_CONFIG` 指向另一个 JSON 文件，不要在脚本或文档里复制端口或视觉批量默认值。

`vision_execution` 只能保存非密钥配置，例如：

```json
{
  "provider": "gemini",
  "model": "gemini-2.5-flash",
  "multimodal_limit": 19,
  "temporal_limit": 3,
  "frame_count": 8
}
```

API key 仍然只从环境变量或显式 `--provider-config` 读取，不要写进配置、manifest、报告或文档。CLI/MCP 显式传入的 provider、model、limit 会覆盖统一配置。

视觉 provider 解析优先级是：

1. 显式 `--provider-config`
2. `LECTURE_VISION_PROVIDER` / `LECTURE_VISION_MODEL` / `LECTURE_VISION_BASE_URL`
3. `vision_execution`
4. provider 内置默认值

因此直接运行 `run-multimodal-frame-analysis`、`run-temporal-frame-groups`、`run-temporal-visual-analysis`、`test-vision-provider` 时，不传 provider/limit/frame-count 也会默认读取同一个 `vision_execution`。如果确实要全量候选，显式传 `--limit 0`。

`config-status` 会返回：

- `config_path`：实际读取的配置文件。
- `service_urls`：从配置解析出的 HTTP 服务 URL。
- `vision_execution`：当前生效的非密钥视觉执行 profile。
- `validation`：必需服务是否齐全、端口是否合法、路径格式是否正确。

SenseVoice/FunASR 本地执行会先检查 Python 环境、ASR 包、命令入口、ffmpeg、CUDA/CPU、模型缓存和模型下载门禁。`asr-env-status --write` 会生成：

- `asr-environment.json`
- `asr-environment.md`
- `asr-env.ps1`
- `mcp-asr-environment-status.args.json`

模型没有准备好时，真实执行会返回 `asr_model_not_ready`，避免任务静默卡在首次下载。确认要允许首次下载时再设置：

```powershell
$env:LECTURE_ASR_ALLOW_MODEL_DOWNLOAD="1"
```

短片段验证用：

```powershell
.\scripts\video-knowledge.ps1 asr-smoke D:\path\to\lesson.mp4 --duration-seconds 30
```

默认会截取本地短音频并调用本地 ASR；只想预览命令和报告时加 `--no-execute`。这个命令不上传音频，音频只留在本机；首次模型下载仍由 `LECTURE_ASR_ALLOW_MODEL_DOWNLOAD` 控制。

云 ASR 可选分支使用 `plan-cloud-asr -> run-cloud-asr-plan --execute`。`plan-cloud-asr` 只写上传计划，默认不上传音频；`run-cloud-asr-plan --execute` 才会调用 `online-model-api asr`，并把返回的 OpenAI-style `segments` 归一化为 `normalized-transcript.json` / `.srt`。它适合作为 SenseVoice/FunASR 的质量对照或疑难音频补救，不是默认批量路径。

WhisperX 不是默认中文 ASR 主线，而是精细时间轴增强分支。需要词级时间戳、说话人对齐或后续和截图/演示动作做更细粒度匹配时，用：

```powershell
.\scripts\video-knowledge.ps1 plan-whisperx-alignment D:\path\to\workspace D:\path\to\lesson.mp4 --language zh
```

执行后会把 WhisperX 自己命名的 JSON 镜像为稳定的 `raw-asr-output.json`，并在 `normalized-transcript.json` 的 segment metadata 中保留 `alignment=word_level`、`word_count` 和 `words` 词级时间戳。

加 `--build-initial-bundle` 会继续复用现有 `add_video -> build_lecture_package -> export_webui_bundle` 链路，抽帧并生成初始 `webui-bundle\task-console.html` 和 `webui-bundle\review.html`。如果 ffmpeg/ffprobe 或视频文件有问题，错误会写进 `video-knowledge-run.md/json`，准备流程不会直接中断。

刷新任务控制台：

```powershell
.\scripts\video-knowledge.ps1 export-task-console D:\path\to\webui-bundle
```

一键打开最近的任务控制台：

```powershell
.\scripts\open-task-console.cmd
```

打开指定 bundle：

```powershell
.\scripts\open-task-console.ps1 -BundleDir D:\path\to\webui-bundle
```

这个控制台只生成状态、链接和可复制命令，不会自动执行 ASR、云视觉、下载或发布。
疑难点多模态队列用于把 `vision-review-triage` 挑出的高风险帧批量排队，生成进度页、批次命令和重试命令：

```powershell
.\scripts\video-knowledge.ps1 vision-review-queue D:\path\to\webui-bundle --min-score 10 --batch-size 10 --max-items 0
```

- `--min-score`：只排疑难分数达到阈值的帧。
- `--batch-size`：每批多少张图。
- `--max-items`：总共排多少张；`0` 表示全部符合条件的疑难项。想控制批次数时，用 `batch-size * 批次数` 作为这个值。

产物包括 `vision-review-queue.html/json/md` 和 `vision-review-queue-run.ps1`。HTML 页面只显示进度、失败项和复制/重试命令；真正发送到云端多模态 API 仍需人工在 PowerShell 执行带 `-Execute` 的命令。
`vision-review-queue` 同时会登记一条 vsummary-style run artifact：`runs/vision-review-queue/run.json/md`，并刷新 `run-artifact-registry.json/md`。刷新 `task-console.html` 后，“任务历史”面板会展示该批次的状态、报告、失败数和 retry command；`failed_items` 会细化到每个 pending/failed index，带有 `batch_id`、`batch_status`、`pending_indexes`、`suggested_next_tool` 和批次级 `suggested_retry_command`，供 `subqueue-action-plan` / `video-workbench` 生成更具体的下一步调度。也可以单独运行 `run-artifact-registry <webui-bundle>` 重建索引；该命令只读/写本地索引，不执行 ASR、ebook、多模态或下载。
`transcript-correction-pack` 会登记 `transcript_correction_pack` run artifact，把 BiliNote-style 转写纠错 prompt/messages、导入后的 `llm-corrected-transcript.*`、preview/缺 provider/导入完成状态和重试命令放进 ASR/转写队列；`run-visual-structure` 会登记 `visual_structure_ebook` run artifact，ebook blocker failed items 会携带证据路径、同 index ebook 重跑命令、high-res tile recovery、多模态 triage 和人工 review fallback；`run-screen-text-recovery`、`high-res-tile-plan`、`tile-result-import-build`、`tile-result-merge` 的 failed items 也会携带 crop/tile evidence paths、同 index 重试、tile import/merge 和 review 命令；`video-moment-index`、`long-video-memory-pack`、`video-rag-pack`、`video-rag-search`、`video-rag-service-plan` 和 `external-capability-pack` 会登记对应 run artifact，让时间轴/RAG/外部能力队列能显示 completed、needs_input、needs_review 或 needs_execution；`timeline-alignment-audit` 会登记 `timeline_alignment_audit` run artifact；`build-smart-summary-input-pack` 会登记 `smart_summary_input_pack` run artifact；`build-smart-summary-chapters` 会登记 `smart_summary_chapter_pack` run artifact；`smart-summary-section-workflow` 会登记 `smart_summary_section_workflow` run artifact，待修订章节会作为 `needs_input` action items 写入 failed_items，并指向 `smart-summary-section-editor` / `smart-summary-section-apply`；`smart-summary-section-editor` 会登记 `smart_summary_section_editor` run artifact，并生成同屏章节编辑 HTML；`smart-summary-section-apply` 会登记 `smart_summary_section_apply` run artifact，并把章节修订安装成 `exports/smart-summary.codex.md` 后复用既有质量门禁；`generate-smart-summary-with-codex` 也会登记 `smart_summary_codex` run artifact；`export-knowledge-note` 会登记 `knowledge_note_export` run artifact，把 `knowledge-note.md`、`full-transcript.md`、`smart-summary.md`、`content-candidate-pack`、`content-material-card` 等最终导出产物、缺章节链接和重试命令放进 summary/export 队列。刷新 `task-console.html` 后，“任务历史”和“处理队列”可同时查看 ebook 批次、高分辨率 tile 证据包、时间轴错位审计、智能总结章节重写队列、Codex 智能总结质量门禁、失败项和重试命令。控制台指标区会显示“时间错位”，关键产物区会链接 `timeline-alignment-audit.md`。`subqueue-action-plan` 会把这些子队列进一步整理成 agent 可读调度单，包含 `action_status`、`action_kind`、`priority`、`primary_command`、`blocked_reason`、`machine_action_available` 和 `operator_review_required`，并优先从 failed item 的 `suggested_retry_command` / `tile_recovery_command` / `ebook_retry_command` / `review_command` 等字段抽取具体下一步命令，但仍然只读，不执行命令。

时间轴错位排查可运行：

```powershell
.\scripts\video-knowledge.ps1 timeline-alignment-audit <webui-bundle> --tolerance-seconds 2
```
多模态效果抽样审核用于判断“多模态是否真的提升了最终人类可读文件”：

```powershell
.\scripts\video-knowledge.ps1 multimodal-sample-review D:\path\to\webui-bundle --sample-size 48
# 在 multimodal-sample-review.html 标注后，把导出的 JSON 保存为 multimodal-sample-review-notes.json
.\scripts\video-knowledge.ps1 validate-multimodal-sample-notes D:\path\to\webui-bundle --notes-json D:\path\to\webui-bundle\multimodal-sample-review-notes.json
```

产物包括 `multimodal-sample-review.html/json/md/todo.json`、`potplayer-review-playlist.m3u8`、`potplayer-review-chapters.txt`、`potplayer-review-timestamps.md/csv`、`potplayer-jump.ps1`、`multimodal-sample-review-summary.md/json` 和 `human-sample-eval.md/json`。抽样标注会统计术语/工具名准确、画面事实准确、步骤完整、时间戳准确、是否必须保留图片、多模态补充关键信息率、多模态错误/幻觉率、净帮助率 proxy，以及 `content-candidate-pack` 里内容素材候选的可继续加工率和证据充分率；如果候选包携带 `evidence_citations`，抽样页会在内容素材候选块显示 Citation summary 和证据路径。这个流程只做人工抽样汇总，不直接改 timeline，也不把内容素材候选当成可发布稿。

抽样页会优先从 `manifest.json` / `source-artifacts.json` 找原视频路径，并在页面顶部提供内嵌 HTML5 视频播放器。点击每条样本的“在页面播放器打开”会跳到对应时间戳、高亮该条，并自动把 `video_checked` 标为 `yes`；如果浏览器不允许直接读取 `file://` 视频，先点“选择本地视频文件”加载原视频。长视频人工审核也可以用 `potplayer-review-playlist.m3u8` 或 `potplayer-review-timestamps.md/csv`，把待审核时间戳作为整包导入/打开；网页里的逐条 PotPlayer 命令只是兜底。找不到原视频时可重新生成：

```powershell
.\scripts\video-knowledge.ps1 multimodal-sample-review D:\path\to\webui-bundle --sample-size 48 --media-path "C:\path\to\video.mp4"
# PotPlayer 不在默认路径时：
.\scripts\video-knowledge.ps1 multimodal-sample-review D:\path\to\webui-bundle --sample-size 48 --potplayer-path "C:\Program Files\DAUM\PotPlayer\PotPlayerMini64.exe"
```

真正执行多模态 API 前，需要设置环境变量：

本地 Qwen-VL / 本地 VLM 走现有 OpenAI-compatible API 接入层，不把模型仓库代码嵌入 VKP。默认 profile 是 `local_qwen_vl`，请求 `http://127.0.0.1:8000/v1/chat/completions`，模型名 `Qwen/Qwen2.5-VL-3B-Instruct`；本地服务默认不要求 API key，如果你的服务设置了鉴权，再填 `LOCAL_QWEN_VL_API_KEY`。

```powershell
$env:LECTURE_VISION_PROVIDER="local_qwen_vl"
$env:LECTURE_VISION_BASE_URL="http://127.0.0.1:8000/v1"
$env:LECTURE_VISION_MODEL="Qwen/Qwen2.5-VL-3B-Instruct"
# 可选：$env:LOCAL_QWEN_VL_API_KEY="..."

.\scripts\video-knowledge.ps1 vision-env-status --provider local_qwen_vl
.\scripts\video-knowledge.ps1 vision-provider-smoke --provider local_qwen_vl --bundle-dir D:\path\to\webui-bundle --image-probe-max-edge 512 --image-probe-jpeg-quality 55
.\scripts\video-knowledge.ps1 local-vlm-serving-smoke --provider local_qwen_vl --bundle-dir D:\path\to\webui-bundle --max-images 8 --frame-group-count 8 --image-probe-max-edge 512
```

`local-vlm-serving-smoke` 默认只生成计划，不启动模型、不改 timeline；它会写出 `local-vlm-serving-smoke.md/json`、`mcp-local-vlm-serving-smoke.args.json`，并报告 OpenAI-compatible endpoint、文本 JSON、单图 JSON、多图 JSON、短帧组 JSON 的能力矩阵。只有加 `--execute` 才会调用已经运行的本地 VLM 服务。

通用本地 OpenAI-compatible VLM 可以用 `local_vlm`，通过 `LOCAL_VLM_BASE_URL` / `LOCAL_VLM_MODEL` / `LOCAL_VLM_API_KEY` 覆盖。

```powershell
$env:LECTURE_VISION_PROVIDER="gemini"
$env:GEMINI_API_KEY="..."
$env:LECTURE_VISION_MODEL="gemini-2.5-flash"
```

或：

```powershell
$env:LECTURE_VISION_PROVIDER="openai_compatible"
$env:OPENAI_API_KEY="..."
$env:LECTURE_VISION_MODEL="gpt-4o-mini"
```

Agnes AI 走 OpenAI-compatible 分支：

```powershell
$env:LECTURE_VISION_PROVIDER="agnes"
$env:AGNES_API_KEY="..."
$env:LECTURE_VISION_MODEL="agnes-1.5-flash"
```

火山方舟 Coding Plan 也走 OpenAI-compatible 分支，并兼容 `semantic-merge` 项目的 `LLM_*` 配置：

```powershell
$env:LECTURE_VISION_PROVIDER="volcengine_coding_plan"
$env:ARK_API_KEY="..."
$env:LECTURE_VISION_BASE_URL="https://ark.cn-beijing.volces.com/api/coding/v3"
$env:LECTURE_VISION_MODEL="doubao-seed-2.0-pro"
```

或复用已有 OpenAI-compatible 三变量：

```powershell
$env:LECTURE_VISION_PROVIDER="volcengine_coding_plan"
$env:LLM_API_KEY="..."
$env:LLM_BASE_URL="https://ark.cn-beijing.volces.com/api/coding/v3"
$env:LLM_MODEL="doubao-seed-2.0-pro"
```

也可以把本机密钥放在不会入库的 `.local\vision.env` 或 `.local\video-knowledge.env`：

```powershell
LECTURE_VISION_PROVIDER=volcengine_coding_plan
ARK_API_KEY=<your key>
LECTURE_VISION_BASE_URL=https://ark.cn-beijing.volces.com/api/coding/v3
LECTURE_VISION_MODEL=doubao-seed-2.0-pro
```

`scripts\video-knowledge.ps1` 会在当前进程里读取这两个文件，只解析 `LECTURE_*`、`GEMINI_API_KEY`、`GOOGLE_API_KEY`、`OPENAI_API_KEY`、`AGNES_API_KEY`、`ARK_API_KEY`、`VOLCENGINE_API_KEY`、`LOCAL_QWEN_VL_*`、`LOCAL_VLM_*` 和 `LLM_API_KEY/LLM_BASE_URL/LLM_MODEL`，不会执行脚本内容，也不会把密钥写入生成物。

生成或检查本地视觉配置模板：

```powershell
.\scripts\video-knowledge.ps1 vision-env-status --provider local_qwen_vl
.\scripts\video-knowledge.ps1 vision-env-status --provider local_qwen_vl --write-template
.\scripts\video-knowledge.ps1 vision-env-status --provider volcengine_coding_plan --model doubao-seed-2.0-pro
```

模板里的 `<your key>` 不会被当成已配置密钥；填入真实 key 后再运行 `vision-env-status` 应显示 `api_key_configured: true`。

`test-vision-provider` 是非持久化连通性检查：会测试文本 ping，以及可选的单图/多图 JSON 输出解析，不会把 API key 写入 manifest、报告或文档。

`batch-run` 会额外写出跨视频质量看板：

- `batch-acceptance-summary.json`
- `batch-acceptance-summary.md`

看板汇总每个 bundle 的 acceptance status、screen text 状态、semantic/temporal 缺口、人工复核数量、导出新鲜度和下一步动作。manifest item 可以附加 `expected_content_type`、`priority`、`notes`，不影响旧的 `media_path` / `bundle_dir`。

`batch-repair-run` 读取 `batch-acceptance-summary.json` 或旧 batch manifest，把每个 bundle 的 `next_action` 串到已有工具：

- 默认只预览，写出 `batch-repair-run.json`、`batch-repair-run.md`、`batch-human-review.md`。
- `--allow-asr` 只允许生成/刷新本地 SenseVoice/FunASR ASR 计划，不默认上传音频。
- `--allow-vision` 允许走现有视觉 preflight/确认链；没有确认值时不会直接调用 API。
- `--allow-ocr --execute` 才会对 screen-text 弱项执行 crop/OCR，空结果会进入 `batch-human-review.md`。

推荐循环：`batch-run --resume -> batch-repair-run -> acceptance-check -> export-knowledge-note`，直到 bundle 进入 `accepted_with_known_gaps` 或生成明确人工复核任务。

屏幕小字恢复用：

```powershell
.\scripts\video-knowledge.ps1 run-screen-text-recovery D:\path\to\webui-bundle
.\scripts\video-knowledge.ps1 run-screen-text-recovery D:\path\to\webui-bundle --execute-crops
.\scripts\video-knowledge.ps1 run-screen-text-recovery D:\path\to\webui-bundle --execute-crops --execute-ocr
```

默认只预览；`--execute-crops` 才在 `ocr-crops\` 写裁剪图；`--execute-ocr` 才尝试本地 CaptiOCR/Tesseract fallback，并且只导入非空有效文字。图文型截图仍优先使用 `run-visual-structure -> ebook_markdown_pipeline`，不要把 fallback OCR 当成主图文解析工具。若 ebook/OCR 整帧结果为空、wrapper-only 或低信息量，先用 `high-res-tile-plan --execute-tiles` 生成局部 tile 证据，再交给本地 VLM、定向云 VLM 或人工复核；得到 tile OCR/VLM/人工结果后，可先用 `tile-result-import-build --results-dir <tile-results-dir>` 生成导入包，再用 `tile-result-merge --input-json <tile-result-import.json> --execute` 回填，低质量结果不会被当作 OCR 成功。`tile-result-import-build` 现在可直接解析常见 OCR/VLM JSON：RapidOCR/PaddleOCR 风格 `result` / `ocr_result` / `rec_texts`，OpenAI-compatible `choices[].message.content`，Gemini `candidates[].content.parts[].text`，以及 VKP `visual_understanding` / `structured_visual`；不带置信度的模型结果可用 `--default-confidence` 显式指定，否则仍进入复核。

`export-knowledge-note` 会把 timeline、ASR、OCR/图文解析、多模态单帧理解和连续片段理解合并成 Obsidian 友好的 Markdown：

- `exports\knowledge-note.md`：人类可读知识库笔记
- `exports\full-transcript.md`：完整转写
- `exports\extraction-audit.md`：提取审计、缺口和证据路径
- `exports\export-summary.json`：导出覆盖摘要和缺口索引

## MCP

```powershell
python -m video_knowledge_pipeline.mcp_server
```

优先给 agent 调用的工具：

- `acceptance_run_tool`
- `acceptance_bundle_run_tool`
- `batch_video_knowledge_run_tool`
- `bundle_next_action_tool`
- `bundle_advance_tool`
- `bundle_advance_queue_tool`
- `bundle_advance_log_tool`
- `run_video_frame_router_tool`
- `run_multimodal_frame_analysis_tool`
- `run_temporal_frame_groups_tool`
- `run_temporal_visual_analysis_tool`
- `run_visual_structure_tool`
- `run_ocr_backfill_tool`（备用 OCR 回填；图文截图主通道是 `run_visual_structure_tool` -> `ebook_markdown_pipeline`）
- `run_screen_text_recovery_tool`
- `config_status`
- `asr_env_status`
- `plan_asr`
- `plan_whisperx_alignment_tool`
- `run_asr_plan_tool`
- `asr_smoke_tool`
- `test_vision_provider_tool`
- `local_vlm_adapter_plan_tool`
- `export_knowledge_note_tool`
- `run_artifact_registry_tool`

## 开源源码审查

ASR 和本地多模态候选的真实源码审查记录见：

- `docs\open-source-asr-vlm-code-review.md`

当前结论：

- SenseVoice/FunASR 已接入为本地 ASR 主线。
- 本地 ASR 默认 GPU-first：未设置 `LECTURE_ASR_DEVICE` 时会探测 ASR venv，CUDA 可用则使用 `cuda`，否则回落 `cpu`；faster-whisper fallback 在 GPU 上默认 `float16`，CPU 上默认 `int8`，并保持 VAD、`condition_on_previous_text=false`。
- Qwen2.5-VL/Qwen3-VL、InternVL、LLaVA-NeXT 只作为本地 VLM adapter 候选，不直接嵌入主流程。
- 图文截图仍走 `run_visual_structure` -> `ebook_markdown_pipeline`，多模态视觉理解走 provider 层。

## 下一步

- 对本地视频先运行 `prepare-local-video-run`，确认 `video-knowledge-run.md`。
- 执行或检查本地 SenseVoice/FunASR ASR。
- 用 Gemini 2.5 Flash 或 OpenAI 视觉 API 跑 19 帧 `semantic_frame`，人工看质量。
- 如果想减少流程胶水，可评估 Twelve Labs 作为整段视频索引/问答分支。
- 后续接 Qwen2.5-VL 或 InternVL，作为离线多模态分支。


## Update - 2026-07-04 22:53:57 | Codex / GPT-5

外部开源项目代码复用总账已整理到 [docs/external-code-reuse-ledger-2026-07-04.md](docs/external-code-reuse-ledger-2026-07-04.md)。它汇总了 vsummary、BiliNote、VideoRAG、MovieChat、VTimeLLM、Qwen-VL、InternVL 等项目已被 VKP 吸收的模块、当前落地入口、仍值得继续复用的能力，以及不建议继续整体搬运的方向。

逐字稿、强制对齐、语义章节和智能总结的跨项目源码最佳实践见 [docs/open-source-transcript-summary-best-practices-2026-07-12.md](docs/open-source-transcript-summary-best-practices-2026-07-12.md)。该文档区分已吸收模块、待复用代码和禁止照搬的实现，并以当前 24 段人工金标作为改进基线。 六项源码复用能力的代码、接口、真实运行证据和回归结果见 [docs/phase17-open-source-reuse-completion-2026-07-13.md](docs/phase17-open-source-reuse-completion-2026-07-13.md)。

.\scripts\video-knowledge.ps1 transcript-semantic-correction-pack D:\video-knowledge-runs\lesson-001\webui-bundle
.\scripts\video-knowledge.ps1 transcript-semantic-candidate-discovery-pack D:\video-knowledge-runs\lesson-001\webui-bundle --limit 40
.\scripts\video-knowledge.ps1 transcript-semantic-candidate-discovery-codex-draft D:\video-knowledge-runs\lesson-001\webui-bundle --limit 40 --max-suggestions 40
.\scripts\video-knowledge.ps1 import-transcript-semantic-candidate-suggestions D:\video-knowledge-runs\lesson-001\webui-bundle --input-json D:\video-knowledge-runs\lesson-001\webui-bundle\transcript-semantic-candidate-suggestions.codex.md

### Offline quality routing

Use offline-quality-route <webui-bundle> --benchmark-manifest <manifest> / MCP offline_quality_route to inspect existing ASR, punctuation, segmentation, OCR, vision, and benchmark-review artifacts without executing any model. It writes a local quality report, a proposal-only fallback route, and a review-page machine summary. Review HTML existence never means content has been reviewed; ASR prefill is not counted as a human reference. All proposed actions keep auto_execute=false and cloud_allowed=false. See docs/offline-quality-routing.md.

## Quality-first execution chain (2026-07-11)

The stable quality route is documented in [docs/quality-improvement-execution-chain-2026-07-11.md](docs/quality-improvement-execution-chain-2026-07-11.md).

- `punctuation-model-stage`: local FunASR ct-punc through the ASR venv subprocess, with a strict character lock before promotion.
- `quality-benchmark execute-variants`: resumable local SenseVoice/Qwen3-ASR/Fun-ASR-Nano benchmark execution; no silent model fallback and no default switch without human-reference gains.
- `transcript-evidence-correction-pipeline --secondary-asr-json ...`: preserves the second ASR as conflict evidence and sends only real multi-source deltas into semantic arbitration.
- `quality-finalize`: corrected transcript gate -> semantic chapters -> chapter LLM rewrite -> aggregate install -> final summary quality check.
- `targeted-visual-evidence`: triage -> ebook_markdown_pipeline -> crop OCR -> high-resolution tiles -> only unresolved indexes become online-preflight or human-review candidates.

All commands are preview-first where model/network execution is involved. GET Note (the product renamed from 得到大脑) remains evaluation-only and is never imported as correction evidence.
## Unified model task gateway

All production text, vision, and cloud/local-service ASR model tasks now route through `model_task_gateway` and the existing provider adapters. Audit coverage with:

```powershell
.\scripts\video-knowledge.ps1 model-task-coverage-audit --output-dir docs
```

Use `run-term-arbitration-model` and `run-bilinote-mind-map-model` for preview-first automatic execution of the two former prompt-only workflows. Provider configuration is runtime-only; network calls still require `--execute`. Native whole-video upload remains deferred in favor of temporal frame groups. See `docs/model-task-gateway.md`.
## License

VKP is licensed under the [GNU Affero General Public License v3.0 only](LICENSE) (`AGPL-3.0-only`). Third-party libraries, browser assets, model runtimes, datasets, source-review checkouts, and optional services retain their own licenses and notices; see [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md). Security issues and sensitive-data handling are covered by [SECURITY.md](SECURITY.md).
