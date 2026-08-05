# 外部开源项目代码复用榨干状态

更新记录：

- 2026-07-05 22:13:05 | Codex / GPT-5：把最近对 vsummary、PrideWood/BiliNote、VideoRAG、MovieChat、VTimeLLM、Qwen/InternVL、Peepshow/VidClaude、FunASR/SenseVoice 等项目的源码审查和 VKP 已落地能力，整理成当前“已榨干程度 / 还能继续复用什么 / 不再建议搬什么”的状态文档。

## 结论

VKP 现在已经不是缺一个完整外部项目来替换，而是进入“外部项目局部模块吸收”阶段。

当前最有价值的外部代码/设计已经基本被拆成 VKP 内部能力：

- vsummary：任务状态、provider gateway、stage cache、视频时间戳交互。
- BiliNote：字幕清洗、转写编辑、章节/总结编辑体验、视频笔记 UI 思路。
- VideoRAG / VTimeLLM / MovieChat：moment index、长视频 short/long memory、可检索 evidence chunks。
- Qwen / InternVL / LLaVA-OneVision：图像预处理、多帧/多图输入、本地 VLM adapter 边界。
- FunASR / SenseVoice / WhisperX：本地中文 ASR、时间戳 sidecar、后续 word-level / speaker / punctuation 路线。
- Peepshow / VidClaude：帧证据报告、人工抽样评分、视觉复核队列。

下一步不应该继续大规模搬整套 UI、后端或模型仓库。更值得做的是把现有已吸收模块串得更顺：`smart-summary-input-pack` 证据化、工作台里的 review/队列闭环、人工抽样评分、以及可选在线/本地 LLM 的同一证据输入层。

## 已基本榨干的模块

| 来源 | 已吸收能力 | VKP 现有落地 | 继续复用判断 |
| --- | --- | --- | --- |
| `alpha03123/vsummary` | OpenAI-compatible 文本网关、JSON repair、stage cache、run artifact、时间戳 seek/citation、Windows CUDA 探测 | `text_llm_gateway.py`、`stage_cache.py`、`run_artifact_registry.py`、`cuda_runtime.py`、`task_console.py`、`video_workbench.py` | 代码价值已主要吸收；后续只参考任务队列 UI 细节，不搬 FastAPI/React/LlamaIndex/LanceDB 全栈 |
| `PrideWood/bilinote` | 字幕解析/清洗/合并、转写校对 prompt、mind-map prompt、transcript editor、章节编辑体验 | `bilinote_transcript_tools.py`、`bilinote_summary_tools.py`、`transcript_correction_pack.py`、`transcript_editor.py`、`smart_summary_section_editor.py` | 核心低耦合能力已吸收；后续继续吸收 UI 交互，不整体迁移 React |
| VideoRAG | segment/chunk schema、JSONL 检索包、本地 query/search、可选 HTTP search service | `video_rag_pack.py`、`video_rag_search.py`、`video_rag_http.py` | 本地词法版已落地；向量库/graph 后端只做 optional adapter，不默认引入重依赖 |
| MovieChat | 长视频 short memory / long memory 分层 | `long_video_memory_pack.py` | 思路已吸收；不接模型代码 |
| VTimeLLM | moment grounding、时间段定位、timestamp quality 思路 | `video_moment_index.py`、`timeline_alignment_audit.py` | 本地索引和审计已落地；后续只增强 UI/评分 |
| Qwen / InternVL | image resize/compress、多图 payload、dynamic tiling/high-res tile | `vlm_preprocess.py`、`high_res_tile_plan.py`、`tile_result_import_builder.py`、`tile_result_merge.py` | 输入层已吸收；模型服务只走 adapter，不 vendor 模型仓库 |
| FunASR / SenseVoice | 本地中文 ASR、timestamp sidecar、模型 ready gate | `funasr_python_runner.py`、`asr_runner.py`、`asr_environment.py`、`transcript_sidecar.py` | 主线已落地；继续补 GPU doctor、标点/说话人/术语后处理 |

## 已吸收但还可加深的模块

### 1. `smart-summary-input-pack` 证据层

现状：

- 已有 `smart-summary.md`、`smart-summary.codex.md`、`smart-summary-codex-prompt.md`、章节编辑和质量门禁。
- 已有 `long-video-memory-pack`、`video-moment-index`、`video-rag-pack`。
- 但智能总结输入仍需要更明确记录“每个章节吃了哪些证据”。

应继续吸收：

- MovieChat 的 long memory 作为章节级背景。
- VideoRAG 的 chunk citation 作为每个观点的 evidence。
- BiliNote 的 chunk prompt 作为章节重写输入。

建议落地：

- 在 `smart-summary-input-pack.json/md` 中给每个章节加入：
  - `transcript_source`
  - `transcript_segment_count`
  - `timeline_indexes`
  - `ocr_items`
  - `visual_items`
  - `temporal_items`
  - `moment_chunks`
  - `review_gaps`
- `generate-smart-summary-with-codex` 和未来在线 LLM 共用这一份证据包。

边界：

- 没跑视觉就写“视觉证据未执行/待复核”，不能伪装成已理解画面。
- 不让规则草稿冒充最终智能总结。

### 2. 工作台里的任务队列闭环

现状：

- `task-console.html` 和 `video-workbench.html` 已经能显示处理队列、任务历史、失败项、retry command。
- ASR、多模态、temporal、screen text recovery、ebook/visual structure、smart summary 等正在逐步接入 run registry。

应继续吸收：

- vsummary 的 stage state / artifact store 细节。
- BiliNote 的任务历史和重生成按钮体验。
- Peepshow/VidClaude 的 frame status card。

建议落地：

- 所有长任务都写 `runs/<task>/run.json/md`。
- 工作台按队列展示：未执行、执行中、失败、需人工、已完成。
- 批量失败项直接显示重试命令和 indexes。

边界：

- 静态页面只展示和复制命令，不绕过 CLI/MCP 的 execute/preflight/confirmation gate。

### 3. 人工抽样评分 UI

现状：

- 已有 `multimodal-sample-review.html`、review pack、video workbench。
- 用户已经提出“要评估多模态对最终人类可读文件准确率的改善”。

应继续吸收：

- Peepshow/VidClaude 的帧证据评分。
- BiliNote 的视频内联审核体验。
- vsummary 的 timestamp seek/citation 体验。

建议落地：

- 生成抽样对比包：
  - ASR only
  - ASR + ebook/OCR
  - ASR + ebook/OCR + multimodal
  - corrected transcript
  - final smart-summary
- 人工评分维度：
  - term accuracy
  - screen text accuracy
  - visual event coverage
  - summary usefulness
  - omission / hallucination
- 输出 `multimodal-impact-report.md/json`。

边界：

- 人工抽样是质量评估，不默认阻塞每个视频。

### 4. 字幕/ASR/平台字幕多源仲裁后处理

现状：

- `transcript-source-arbitration` 已落地。
- `video-workbench` 已开始展示字幕仲裁冲突。

应继续吸收：

- BiliNote 字幕清洗、短句合并。
- WhisperX word-level timestamp / diarization。
- SenseVoice emotion/event tags。

建议落地：

- 高置信术语纠错进入 corrected transcript。
- 低置信冲突进入 review pack。
- 后续补标点、段落化、说话人、课程术语词典。

边界：

- 平台字幕不默认当真，因为很多平台字幕本身也是 ASR。
- corrected transcript 必须保留来源和置信度。

## 不建议继续搬运的模块

| 方向 | 原因 | 替代做法 |
| --- | --- | --- |
| 整体迁移 vsummary 后端 | VKP 已有 CLI/MCP/OpenClaw/static bundle；再搬 FastAPI/React/LlamaIndex 会形成第二套系统 | 只吸收 provider、stage cache、artifact registry、UI 交互 |
| 整体迁移 BiliNote React UI | UI 好，但会打断当前静态 bundle 和审核包工作流 | 在 `video-workbench.html` 里逐步复刻关键交互 |
| 直接运行 VideoRAG 全套 graph/vector 后端 | 依赖重，当前个人工具收益不如 JSONL/词法检索 | 保留 optional vector backend adapter |
| 把 Qwen/InternVL/LLaVA 模型源码嵌入 VKP | 模型环境和显存依赖复杂，维护成本高 | 用 OpenAI-compatible / HTTP / subprocess adapter |
| 在 VKP 内重写下载/字幕抓取后端 | 下载边界属于 `video-download-orchestrator` | VKP 接收 VDO handoff manifest |
| 把在线多模态作为默认全帧处理 | 成本、隐私、限流、失败恢复都不适合默认全量 | 本地抽帧/OCR/ebook 先跑，多模态只处理疑难点或显式全量模式 |

## 下一步优先顺序

1. **P0：补 `smart-summary-input-pack` evidence trace**
   - 目标：让每个章节总结都能追踪 transcript / OCR / visual / temporal / moment / review gap。
   - 价值：直接提高智能总结质量，也为 Codex/在线 LLM 共用输入打底。

2. **P0：把所有长任务接满 run registry**
   - 目标：ASR、ebook、tile、multimodal、temporal、smart-summary、review queue 都能被工作台看到状态、失败项和重试命令。
   - 价值：长视频批量处理更像生产工具，而不是复制 PowerShell 命令。

3. **P1：强化视频工作台**
   - 目标：一个页面里完成视频播放、时间戳跳转、字幕仲裁、视觉证据、队列重试、智能总结章节编辑。
   - 价值：减少 UI 分裂。

4. **P1：人工抽样评分和多模态收益报告**
   - 目标：回答“多模态到底让最终人类可读文件准确率提高多少”。
   - 价值：决定是否值得对某类视频跑更多多模态。

5. **P2：可选向量 RAG / 本地 VLM service smoke**
   - 目标：只在 JSONL/HTTP/local adapter 已稳定后继续。
   - 价值：增强检索和离线视觉能力，但不是当前瓶颈。

## 判断新外部项目是否还值得看

以后如果再发现新的 AI 视频总结/分析开源项目，先按这个表判断：

| 问题 | 如果答案是是 | 如果答案是否 |
| --- | --- | --- |
| 是否提供 VKP 没有的低耦合模块？ | 拉源码看具体文件 | 不再深入 |
| 是否能不引入重依赖单独复用？ | 做 adapter / wrapper | 只记录思路 |
| 是否改善当前瓶颈：智能总结质量、时间定位、屏幕文字、小字 UI、批次重试、人工评分？ | 排入 backlog | 暂不吸收 |
| 是否要求替换 VKP 架构？ | 默认拒绝 | 可局部借鉴 |
| 是否会绕过下载、云 API、人工复核边界？ | 不接入主线 | 可作为只读参考 |

## 相关文档

- `docs/external-code-module-reuse-backlog-2026-07-04.md`
- `docs/external-code-reuse-ledger-2026-07-04.md`
- `docs/external-code-reuse-decision-map-2026-07-04.md`
- `docs/external-code-reuse-remaining-modules-2026-07-05.md`
- `docs/external-project-reuse-implementation-2026-07-04.md`
- `docs/vsummary-source-review.md`
- `docs/bilinote-pridewood-source-review.md`
- `docs/ai-video-open-source-survey-2026-07-04.md`
- `docs/smart-summary-best-practices.md`

## Update: 2026-07-05 22:28:07 | Codex / GPT-5

### 已落地：smart-summary-input-pack 证据追踪 v1

本轮把外部项目里的长视频分层总结、VideoRAG citation、VTimeLLM time grounding 思路继续向 VKP 内部推进：

- `smart-summary-input-pack.json/md` 新增 `evidence_trace`：
  - `transcript_source` / `transcript_path`；
  - transcript segment count；
  - timeline indexes；
  - OCR/ebook items；
  - single-frame visual understanding items；
  - temporal visual understanding items；
  - moment chunks；
  - review gaps。
- 每个 `transcript_segments[]` 新增 `evidence_inputs`，标明该段是否有 OCR/ebook、单帧理解、连续片段理解、证据路径和复核缺口。
- `smart-summary-chapters.json/md` 的每个 chapter 新增 chapter-level `evidence_trace`，把章节范围内的 transcript、OCR/ebook、visual、temporal、moment 和 review gap 聚合起来。
- Markdown 中新增“证据追踪”区，方便人和 Codex/LLM 在总结前确认输入来源。

这一步对应之前 backlog 的 P1“长视频分层总结输入包”：现在最终 smart summary 的输入不再只是转写文本，而是可以按章节追踪多源证据。未来在线 LLM 或本地 LLM provider 应复用同一个 input pack，而不是另起一套 prompt 数据结构。

验证：

`````powershell
python -m py_compile src\video_knowledge_pipeline\smart_summary_input_pack.py src\video_knowledge_pipeline\smart_summary_chapters.py tests\test_knowledge_export.py
```

并用项目内 `outputs/vkp-smart-input-pack-direct` 构造直接函数验证，确认：

- input pack 写入 `evidence_trace`；
- segment 写入 `evidence_inputs`；
- chapter 写入 chapter-level `evidence_trace`；
- Markdown 包含“证据追踪 / Moment evidence / Review gaps”。

备注：`pytest` 单测命令在当前 Windows 环境仍会被 pytest basetemp cleanup 权限问题拦截，故本轮采用 `py_compile` + 直接函数验证作为有效验证。
## Update: 2026-07-05 22:34:59 | Codex / GPT-5

### 已落地：smart-summary input/chapter pack 进入 run artifact registry

继续吸收 vsummary 的 stage/run artifact 思路，本轮把智能总结输入层也接入 VKP 统一任务历史：

- `build-smart-summary-input-pack` 现在会登记 `runs/smart-summary-input-pack/run.json/md`。
- `build-smart-summary-chapters` 现在会登记 `runs/smart-summary-chapter-pack/run.json/md`。
- 状态语义：
  - `completed`：证据包已生成且没有显著 review gaps；
  - `needs_review`：证据包已生成，但章节或 timeline 仍有 review gaps；
  - `needs_input`：缺少 transcript 或无法生成章节。
- `run-artifact-registry.json/md` 会把这两个任务纳入任务历史，工作台后续可直接显示智能总结输入包和章节包的状态、失败项和 retry command。

验证：

`````powershell
python -m py_compile src\video_knowledge_pipeline\smart_summary_input_pack.py src\video_knowledge_pipeline\smart_summary_chapters.py tests\test_knowledge_export.py
```

直接函数验证通过：

- `smart_summary_run_registry_direct_test_ok`
- `smart_summary_chapter_pack_direct_test_ok`

备注：仍未跑完整 pytest；当前 Windows 环境的 pytest basetemp cleanup 权限问题尚未消除。
## Update: 2026-07-05 22:45:41 | Codex / GPT-5

### 已落地：smart-summary input/chapter pack 进入任务控制台与处理队列

本轮把上一阶段新增的智能总结输入证据包、章节证据包，从“可由 CLI/MCP 单独生成”推进到“可在任务控制台中被人和 agent 发现、排队、重试”：

- `task-console.html` / `task-console.json` 现在会暴露两个命令：
  - `smart_summary_input_pack`：生成 `exports/smart-summary-input-pack.md`；
  - `smart_summary_chapters`：生成 `exports/smart-summary-chapters.md`。
- 这两个 run type 被归入 `summary_export` 队列组，不再散落在离线脚本里。
- bundle manifest 会写入：
  - `mcp_build_smart_summary_input_pack_args`；
  - `mcp_build_smart_summary_chapters_args`；
  - `smart_summary_input_pack_markdown`；
  - `smart_summary_chapters_markdown`；
  - `smart_summary_course_map_markdown`。
- MCP args audit 已补齐 `build_smart_summary_chapters` 工具映射，避免控制台生成了参数文件但审计报 `unsupported_tool`。

这一步继续吸收 vsummary 的 stage UI / run artifact 思路：智能总结不再只是最终导出动作，而是有独立的输入准备、章节拆分、证据追踪、任务状态和重试入口。

验证：

`````powershell
python -m py_compile src\video_knowledge_pipeline\cli.py src\video_knowledge_pipeline\task_console.py tests\test_task_console.py
```

直接测试通过：

```text
task_console_summary_queue_direct_tests_ok
```

备注：仍未跑完整 pytest；当前 Windows 环境的 pytest basetemp cleanup 权限问题尚未消除。本轮采用 `py_compile` + 直接测试覆盖这次变更。
## Update: 2026-07-05 22:49:08 | Codex / GPT-5

### 已落地：smart-summary 证据包进入统一视频工作台

承接上一轮任务控制台接入，本轮把智能总结输入证据包、章节证据包和课程地图继续接入 `video-workbench.html`，让它们成为主工作台可见的关键产物，而不是只存在于 CLI/MCP 或 task console 中。

新增能力：

- `video-workbench.html/json` 的 artifact cards 现在包含：
  - `smart_summary_input_pack_markdown` -> `exports/smart-summary-input-pack.md`；
  - `smart_summary_chapters_markdown` -> `exports/smart-summary-chapters.md`；
  - `smart_summary_course_map_markdown` -> `exports/course-map.md`。
- `summary_export` 队列可以显示 `smart_summary_chapter_pack` run，包括状态、摘要、artifact 和 retry command。
- 测试 fixture 覆盖了章节证据包 run，确认工作台 HTML 中出现 summary 队列卡片和重试命令。

复用来源：

- vsummary 的 stage/run artifact 可见化；
- BiliNote 的视频工作台内统一查看素材、转写、总结和任务状态；
- VKP 现有静态 bundle / CLI / MCP 边界，没有引入新的长期后端。

验证：

`````powershell
python -m py_compile src\video_knowledge_pipeline\video_workbench.py tests\test_video_workbench.py
```

直接测试通过：

```text
video_workbench_smart_summary_artifacts_tests_ok
```

边界：这一步只让工作台可见和可重试，不自动调用 LLM、不执行云多模态、不改写最终总结。
## Update: 2026-07-05 22:55:11 | Codex / GPT-5

### 已落地：时间轴错位可通过 review notes 人工修正 review_start

继续吸收 VTimeLLM temporal grounding 的时间定位评价思路，本轮把“发现时间错位”推进到“人工确认后可写回”：

- `prepare-review-session` 生成的 `review-notes.todo.json` 对 `timeline_alignment_issue` 条目新增 `corrected_review_start` 填写位。
- 时间错位目标的 `suggested_status` 从笼统 `needs_fix` 改为 `corrected_review_start`，让人知道应该修的是审核跳转秒数。
- `validate-review-notes` 会校验：`status=corrected_review_start` 时必须提供数字型 `corrected_review_start`。
- `apply-review-notes` 导入人工确认值后，会写回 timeline：
  - `review_start`；
  - `review_start_source=human_review_note`；
  - `human_corrected_review_start`；
  - `review_status=corrected_review_start`。
- 自动审计仍只给 preview suggestion，不会直接修改时间；写回必须来自人工 review notes。

验证：

`````powershell
python -m py_compile src\video_knowledge_pipeline\review_session.py tests\test_review_session.py
```

直接测试通过：

```text
timeline_alignment_review_start_correction_test_ok
```

边界：这一步不重新跑 ASR、不调用模型、不自动接受 ASR 起点；只为人工确认后的时间戳修正提供稳定入口。
## Update: 2026-07-05 22:59:07 | Codex / GPT-5

### 已落地：Tile 复核结果可通过 review notes 结构化回填

继续吸收 InternVL dynamic tiling / Qwen-VL 图像预处理后的 tile 级证据消费思路，本轮把 `tile_result_merge` 的低置信/空结果复核目标进一步接到人工审核闭环：

- `review-notes.todo.json` 对 `tile_result_needs_review` 条目新增 `tile_corrections[]` 模板：
  - `tile_id`；
  - `status`；
  - `corrected_text`；
  - `comment`；
  - `confidence`；
  - `reasons`；
  - `evidence_path`。
- `validate-review-notes` 现在允许 `status=corrected_visual_text` 使用 `tile_corrections[].corrected_text` 作为有效人工画面文字，不强迫用户再手动拼一整段 `corrected_visual_text`。
- `apply-review-notes` 会把 tile 级人工修正汇总到：
  - `human_corrected_visual_text`；
  - `human_tile_corrections`。
- 原有 `corrected_visual_text` 仍保持兼容；tile 结构化输入只是更细的人工审核入口。

验证：

`````powershell
python -m py_compile src\video_knowledge_pipeline\review_session.py tests\test_review_session.py
```

直接测试通过：

```text
tile_and_timeline_review_direct_tests_ok
```

边界：这一步不运行 OCR/VLM，不把低置信 tile 自动当成功；只有人工在 review notes 中填写 `corrected_text` 后才回填。
## Update: 2026-07-05 23:08:40 | Codex / GPT-5

### 已落地：VideoRAG 多粒度 JSONL chunks

继续吸收 VideoRAG 的多源证据 chunk / 本地检索思路，本轮把 `video-rag-pack` 从单一 moment chunk 扩展为多粒度 JSONL：

- `moment`：原有按时间窗口聚合的 transcript + visual + temporal chunk。
- `visual_evidence`：从 timeline 中抽取 `visual_text`、`human_corrected_visual_text`、`structured_visual`、`visual_understanding`、`temporal_visual_understanding`、`human_tile_corrections`。
- `review_gap`：把 `quality_issues`、`needs_human_review`、`tile_review_targets`、低置信 tile 原因和证据路径变成可检索 chunk。
- `content_asset`：把已导出的 smart summary、key segments、短视频脚本草稿、精华帖草稿、content material card 等作为下游内容资产 chunk。

新增统计：

- `moment_chunks`
- `visual_evidence_chunks`
- `review_gap_chunks`
- `content_asset_chunks`
- `chunks_by_kind`
- `operator_boundary.multi_granularity_jsonl=true`

`video-rag-search` 继续使用本地 JSONL 词法检索，不启动向量库、不调用云模型；搜索结果现在返回 `chunk_kind`，并对 `review_gap` / `content_asset` 给予轻量排序加权。

验证：

`````powershell
python -m py_compile src\video_knowledge_pipeline\video_rag_pack.py src\video_knowledge_pipeline\video_rag_search.py tests\test_external_video_reuse_modules.py
```

直接测试通过：

```text
video_rag_multigranularity_direct_tests_ok
```

边界：这一步只增强本地 JSONL 检索包，不引入 graph/vector DB，不启动 HTTP 服务，不处理新视频，不调用在线模型。
## Update: 2026-07-06 00:46:54 | Codex / GPT-5

### 已落地：content-candidate-pack 内容素材候选包

本轮继续吸收 vsummary 的内容片段/脚本草稿思路、BiliNote 的笔记导出体验、VideoRAG/VTimeLLM 的时间戳证据边界，把 VKP 的内容资产输出从单张 `content-material-card` 扩展为结构化候选包：

- 新增导出产物：
  - `exports/content-candidate-pack.json`
  - `exports/content-candidate-pack.md`
- 导出入口仍然是 `export-knowledge-note`，不新增另一套内容生成系统。
- 候选包从 timeline 中挑选 transcript、OCR/ebook、single-frame visual、temporal visual、人工审核信息较有价值的片段。
- 每条候选包含：
  - timeline index；
  - start/end/time range；
  - candidate types，例如 `case`、`method`、`visual_explainer`、`viewpoint`；
  - viewpoint / case_or_example / reusable_quote；
  - short_video_script_draft；
  - highlight_post_seed；
  - evidence_paths。
- 安全边界固定：
  - `review_required=true`
  - `publication_allowed=false`
  - `allowed_as_fact=false`
  - `allowed_as_inspiration=true`

意义：VKP 给内容资产/朋友圈线程的输出不再只有“整篇总结”和“素材卡索引”，而是有一篮子可审查、可回看证据、可继续改写的局部素材候选。它仍然不是发布稿，也不能跳过人工事实核查、隐私脱敏和合规审核。

代码落地：

- `src/video_knowledge_pipeline/knowledge_note_export.py`
  - `_build_content_candidate_pack`
  - `_render_content_candidate_pack_markdown`
  - candidate typing / quote / script seed helpers
  - `content_assets`、`manifest.json`、`export-summary.json` 索引同步
- `tests/test_knowledge_export.py`
  - 验证 JSON/Markdown 落盘；
  - 验证 export summary 和 manifest 索引；
  - 验证候选包保留 evidence path 和不可发布/不可当事实边界。

验证：

`````powershell
python -m py_compile src\video_knowledge_pipeline\knowledge_note_export.py tests\test_knowledge_export.py
$env:PYTHONPATH='src'; python -c "import importlib.util, shutil; from pathlib import Path; spec=importlib.util.spec_from_file_location('tk','tests/test_knowledge_export.py'); mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); base=Path('outputs/test-content-candidate-pack-direct').resolve(); shutil.rmtree(base, ignore_errors=True); base.mkdir(parents=True, exist_ok=True); mod.test_export_includes_source_channels_demo_notes_and_crop_audit(base); print('content_candidate_pack_direct_test_ok')"
```

下一步：

1. 把 `content-candidate-pack` 接入 `content-asset-status` 和 batch handoff pack 的摘要展示。
2. 让 `video-workbench.html` 显示候选包 tab，并能按 candidate type 过滤。
3. 后续接在线/本地 LLM 时，仍以这个候选包作为 evidence-bound input，不让模型自由生成无证据素材。

## Update: 2026-07-06 00:51:04 | Codex / GPT-5

### 已落地：content-candidate-pack 接入 status / batch / handoff

承接上一轮 content-candidate-pack 导出，本轮把候选包纳入下游可见状态，而不是只把文件写在 `exports/` 里等待人工找：

- content-asset-status 现在会检查：
  - `exports/content-material-card.json/md`；
  - `exports/content-candidate-pack.json/md`；
  - 候选包安全边界：`review_required=true`、`publication_allowed=false`、`allowed_as_fact=false`、`allowed_as_inspiration=true`。
- 如果旧 bundle 只有素材卡、没有候选包，会返回 `content_candidate_pack_needs_reexport`，下一步明确是重新运行 `export-knowledge-note`。
- `batch-content-asset-status` 的 JSON/Markdown 行项目新增：
  - content_candidate_pack_path；
  - content_candidate_pack_markdown_path；
  - content_candidate_count；
  - content_candidate_pack_safe。
- content-handoff-pack 现在会把候选包路径和候选数量交给内容资产/朋友圈线程，但仍保持不可发布、不可当事实。

复用来源对应关系：

- vsummary：片段/脚本草稿的 staged handoff 思路；
- BiliNote：笔记导出作为下游复用素材，而不是只做一次性摘要；
- VideoRAG / VTimeLLM：候选素材必须保留时间段和 evidence path。

代码落地：

- src/video_knowledge_pipeline/content_asset_status.py
- src/video_knowledge_pipeline/content_asset_batch.py
- `tests/test_knowledge_export.py`

验证：

```powershell
python -m py_compile src\video_knowledge_pipeline\content_asset_status.py src\video_knowledge_pipeline\content_asset_batch.py tests\test_knowledge_export.py
$env:PYTHONPATH='src'; python -c "import importlib.util, shutil; from pathlib import Path; spec=importlib.util.spec_from_file_location('tk','tests/test_knowledge_export.py'); mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); base=Path('outputs/test-content-asset-status-candidate-pack').resolve(); shutil.rmtree(base, ignore_errors=True); base.mkdir(parents=True, exist_ok=True); mod.test_content_asset_status_reports_export_required_and_ready(base); mod.test_batch_content_asset_status_and_handoff_pack_only_use_safe_ready_cards(base); print('content_asset_candidate_status_direct_tests_ok')"
```
下一步：把候选包接进 `video-workbench.html` 的内容资产/素材候选 tab，支持按 case/method/visual_explainer/viewpoint 过滤，并显示 evidence path。

## Update: 2026-07-06 00:54:53 | Codex / GPT-5

### 已落地：content-candidate-pack 进入统一视频工作台

本轮把内容素材候选包从纯文件产物继续推进到可见 UI：`export-video-workbench` 现在会读取 `exports/content-candidate-pack.json/md`，并在 `video-workbench.html` 左侧新增“内容素材候选”面板。

工作台现在能显示：

- 候选数；
- `review_required`、`publication_allowed`、`allowed_as_fact`、`allowed_as_inspiration`；
- 每条候选的 ID、时间范围、candidate types、观点种子、evidence path；
- 一键打开 `content-candidate-pack.md` 到右侧内嵌面板。

同时 `video-workbench.json` 增加 `content_candidates`，给 OpenClaw/其他 agent 读取时使用，不需要解析 HTML。

复用来源对应关系：

- BiliNote：视频笔记工作台里直接展示可复用笔记素材；
- vsummary：内容片段与 evidence citation 同屏；
- Peepshow/VidClaude：候选项以证据卡片/状态面板进入人工复核视野。

代码落地：

- src/video_knowledge_pipeline/video_workbench.py
- `tests/test_video_workbench.py`

验证：

```powershell
python -m py_compile src\video_knowledge_pipeline\video_workbench.py tests\test_video_workbench.py
$env:PYTHONPATH='src'; python -c "import importlib.util; spec=importlib.util.spec_from_file_location('tvw','tests/test_video_workbench.py'); mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); mod.test_export_video_workbench_writes_static_workspace(); print('video_workbench_content_candidates_direct_test_ok')"
```
下一步：如果继续榨外部项目，优先把 content-candidate-pack 接入 sample review / impact report，让用户能人工评分“这条素材是否可用、是否准确、是否因为多模态/ebook 变好”。

## Update: 2026-07-06 07:37:56 | Codex / GPT-5

### 已落地：content-candidate-pack 接入 multimodal sample review / human eval

本轮继续吸收 Peepshow / VidClaude 的人工抽样评分思路，以及 vsummary / VideoRAG 的“内容片段必须带时间和证据路径”做法，把内容素材候选包纳入抽样验收闭环。

新增能力：

- `multimodal-sample-review` 会读取 `exports/content-candidate-pack.json`。
- 抽样选择新增 `content_candidate` bucket，候选素材会优先进入人工抽样池。
- 每条样本会显示：candidate id、candidate types、观点种子、案例/示例、可复用话术、fact status、evidence paths。
- 标注 JSON 新增两个维度：
  - `content_candidate_usable`：这条素材是否值得继续加工；
  - `content_candidate_evidence_sufficient`：证据是否足够支撑后续改写。
- `validate-multimodal-sample-notes` / `human-sample-eval` 新增：
  - content candidate usable rate；
  - content candidate evidence sufficiency rate。

复用来源对应关系：

- Peepshow / VidClaude：抽样评分表、失败分类、人类可读质量门槛；
- vsummary：视频片段到脚本/素材候选的 staged handoff；
- VideoRAG / VTimeLLM：候选素材必须绑定时间段和 evidence path，不允许脱离证据自由生成；
- BiliNote：最终笔记/素材应进入可人工浏览的工作台，而不是散落成孤立 JSON。

代码落地：

- `src/video_knowledge_pipeline/multimodal_sample_review.py`
- `tests/test_multimodal_sample_review.py`
- `README.md`
- `AGENT_DISCOVERY.md`

验证：

```powershell
python -m py_compile src\video_knowledge_pipeline\multimodal_sample_review.py tests\test_multimodal_sample_review.py
$env:PYTHONPATH='src'; python -c "import importlib.util; from pathlib import Path; import shutil; spec=importlib.util.spec_from_file_location('tm','tests/test_multimodal_sample_review.py'); mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); base=Path('outputs/test-multimodal-sample-content-candidate-1').resolve(); shutil.rmtree(base, ignore_errors=True); base.mkdir(parents=True, exist_ok=True); mod.test_multimodal_sample_review_writes_static_ui_and_notes_template(base); print('sample_review_content_candidate_direct_test_ok')"
$env:PYTHONPATH='src'; python -c "import importlib.util; from pathlib import Path; import shutil; spec=importlib.util.spec_from_file_location('tm','tests/test_multimodal_sample_review.py'); mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); base=Path('outputs/test-multimodal-sample-content-candidate-2').resolve(); shutil.rmtree(base, ignore_errors=True); base.mkdir(parents=True, exist_ok=True); mod.test_validate_multimodal_sample_notes_summarizes_human_labels(base); print('sample_review_content_candidate_validation_direct_test_ok')"
```

下一步仍值得继续复用的模块：

1. 把 `content_candidate_usable` / evidence sufficiency 结果反馈到 `content-handoff-pack`，让下游只看到“已抽样通过/待复核”的素材。
2. 给 `video-workbench.html` 增加 candidate type 过滤和“只看证据不足候选”。
3. 把 smart-summary section citations 和 content candidate 互相链接，形成“章节总结 -> 可复用素材 -> 证据帧/时间戳”的闭环。
## Update: 2026-07-06 07:48:12 | Codex / GPT-5

### 已落地：human-sample-eval 进入 content handoff 质量信号

承接上一轮 `content-candidate-pack` 接入抽样审核，本轮把 `human-sample-eval.json/md` 的结果继续传递到内容素材状态和交接包。这样下游内容资产/朋友圈线程拿到素材候选时，不只知道“有候选包”，还能看到这批候选是否经过人工抽样、候选素材可用率和证据充分率是多少。

新增能力：

- `content-asset-status` 会自动读取 bundle 根目录的 `human-sample-eval.json/md`，并输出：
  - `human_sample_eval_status`；
  - `human_sample_eval_labeled_rows`；
  - `human_sample_eval_content_candidate_usable_rate`；
  - `human_sample_eval_content_candidate_evidence_sufficient_rate`；
  - `human_sample_eval_multimodal_net_help_rate`。
- `batch-content-asset-status` 的 Markdown 表格新增 Sample eval、Candidate usable、Candidate evidence 三列。
- `content-handoff-pack` 的每条素材新增 human sample eval 报告路径和关键比率。
- 没有 `human-sample-eval` 不阻塞素材作为 `needs_review_inspiration` 交接；它只显示 `not_available`。
- 有抽样报告也不会改变安全边界：仍然 `publication_allowed=false`、`allowed_as_fact=false`，只能作为人审灵感素材。

复用来源对应关系：

- Peepshow / VidClaude：人工抽样评分变成可传递的质量信号；
- vsummary：内容素材交接包携带 staged task status / review status；
- VideoRAG：素材候选继续保留 evidence path，抽样结果不替代证据本身。

代码落地：

- `src/video_knowledge_pipeline/content_asset_status.py`
- `src/video_knowledge_pipeline/content_asset_batch.py`
- `tests/test_knowledge_export.py`
- `README.md`
- `AGENT_DISCOVERY.md`

验证：

```powershell
python -m py_compile src\video_knowledge_pipeline\content_asset_status.py src\video_knowledge_pipeline\content_asset_batch.py tests\test_knowledge_export.py
$env:PYTHONPATH='src'; python -c "import importlib.util, shutil; from pathlib import Path; spec=importlib.util.spec_from_file_location('tk','tests/test_knowledge_export.py'); mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); base=Path('outputs/test-content-asset-human-eval').resolve(); shutil.rmtree(base, ignore_errors=True); (base/'status').mkdir(parents=True, exist_ok=True); (base/'batch').mkdir(parents=True, exist_ok=True); mod.test_content_asset_status_reports_export_required_and_ready(base/'status'); mod.test_batch_content_asset_status_and_handoff_pack_only_use_safe_ready_cards(base/'batch'); print('content_asset_human_eval_direct_tests_ok')"
```

下一步：把这些 human sample eval 信号显示到 `video-workbench.html` 的内容素材候选面板，并支持“只看未抽样 / 抽样证据不足 / 可继续加工”的过滤。
## Update: 2026-07-06 07:51:40 | Codex / GPT-5

### 新增模块级总清单入口

新增 `docs/external-open-source-reuse-module-inventory-2026-07-06.md`，用于替代聊天里的临时判断，成为后续继续吸收外部项目代码模块的首选入口。

如果只是判断“某个外部项目还有没有值得复用的代码”，先读这个总清单；如果需要看源码审查细节，再回到 `vsummary-source-review.md`、`bilinote-pridewood-source-review.md`、`ai-video-open-source-survey-2026-07-04.md` 和实现流水账。
## Update: 2026-07-06 07:59:34 | Codex / GPT-5

### 已落地：human-sample-eval 进入 video-workbench 内容素材候选面板

本轮把上一阶段的 `content-candidate-pack` 与 `human-sample-eval` 质量信号继续推进到统一视频工作台：

- `export-video-workbench` 现在会把 `content_candidates` 写入 `video-workbench.json`。
- `video-workbench.html` 左栏新增/强化“内容素材候选”面板，显示：候选数、抽样状态、候选可用率、证据充分率、review/publication/fact/inspiration 边界。
- 候选表格新增抽样状态列，并给每条候选写入 `review_filters`。
- 静态页面支持过滤：全部、只看未抽样、抽样证据不足、可继续加工。
- 面板可直接打开 `content-candidate-pack.md` 和 `human-sample-eval.md`。
- 这些信号仍然是 review-only，不会把素材变成可发布，也不会把素材当事实。

代码落地：

- `src/video_knowledge_pipeline/video_workbench.py`
- `tests/test_video_workbench.py`

验证：

```powershell
python -m py_compile src\video_knowledge_pipeline\video_workbench.py tests\test_video_workbench.py
$env:PYTHONPATH='src'; python -c "import importlib.util; spec=importlib.util.spec_from_file_location('tvw','tests/test_video_workbench.py'); mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); mod.test_export_video_workbench_writes_static_workspace(); print('video_workbench_human_eval_candidate_filters_direct_test_ok')"
```

下一步优先级顺延为：smart-summary evidence trace 继续加深，所有长任务接满 run artifact registry，并把 citation 更自然地注入 `smart-summary.md` / content candidates。
## Update: 2026-07-06 08:06:11 | Codex / GPT-5

### 已落地：smart-summary chapter citation digest v1

承接 MovieChat 长视频分层记忆、VideoRAG citation chunk、VTimeLLM time grounding 的复用方向，本轮把章节级证据追踪从“计数和原始列表”推进到可直接给 Codex/在线 LLM 使用的 `citation_digest`：

- `build-smart-summary-chapters` 现在会在每个 chapter 中写入 `citation_digest`。
- digest 来源包括：
  - transcript 片段；
  - moment chunks；
  - OCR/ebook 图文证据；
  - 单帧视觉理解；
  - 连续片段理解；
  - review gaps。
- `chapter.evidence_trace.summary.citation_digest_items` 会记录 digest 条数。
- `smart-summary-chapters.md` 新增 `Citation Digest` 表格，字段包括 Type、Time、Timeline、Evidence、Text。
- 这一步仍然本地执行，不调用 LLM，不修改 raw transcript，不把未复核内容当事实。

代码落地：

- `src/video_knowledge_pipeline/smart_summary_chapters.py`
- `tests/test_knowledge_export.py`

验证：

```powershell
python -m py_compile src\video_knowledge_pipeline\smart_summary_chapters.py tests\test_knowledge_export.py
$env:PYTHONPATH='src'; python -c "import importlib.util, tempfile; from pathlib import Path; spec=importlib.util.spec_from_file_location('tk','tests/test_knowledge_export.py'); mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); base=Path('outputs/test-smart-summary-citation-digest').resolve(); import shutil; shutil.rmtree(base, ignore_errors=True); base.mkdir(parents=True, exist_ok=True); mod.test_smart_summary_input_pack_fuses_terms_punctuation_and_visual_evidence(base); print('smart_summary_citation_digest_direct_test_ok')"
```

下一步：把 chapter `citation_digest` 注入 `generate-smart-summary-with-codex` 的最终改写提示和 `smart-summary.md` 的关键观点引用，形成“章节总结 -> citation digest -> 原始证据”的闭环。
## Update: 2026-07-06 08:12:07 | Codex / GPT-5

### 已落地：chapter citation_digest 注入 Codex 智能总结

本轮把上一条“下一步”完成：`generate-smart-summary-with-codex` 现在会读取 `build-smart-summary-chapters` 产生的章节级 `citation_digest`，并在最终 `exports/smart-summary.codex.md` / `exports/smart-summary.md` 中生成 `## 证据引用 / Citation Digest` 区块。

落地效果：

- final smart summary 不再只是一段总结文本，而是带有可回链的证据导航。
- citation 来源覆盖 transcript、moment、OCR/ebook、单帧视觉、多帧 temporal、review gap。
- `quality_issues` 已纳入 review gap 识别，所以 `semantic_frame_without_analysis` 这类缺口会进入 Citation Digest，而不是被漏掉。
- run registry 允许 input pack / chapter pack 保持 `needs_review`，但 `smart_summary_codex` run 必须是 `completed` 才算最终总结生成成功。
- 这一步仍然本地执行，不调用在线 LLM/API；后续接在线 LLM 时应复用同一 citation/evidence pack，而不是另起一套总结输入。

代码落地：

- `src/video_knowledge_pipeline/smart_summary_codex.py`
- `src/video_knowledge_pipeline/smart_summary_input_pack.py`
- `tests/test_knowledge_export.py`

验证：

```powershell
python -m py_compile src\video_knowledge_pipeline\smart_summary_codex.py src\video_knowledge_pipeline\smart_summary_input_pack.py tests\test_knowledge_export.py
$env:PYTHONPATH='src'; python -c "import importlib.util; from pathlib import Path; spec=importlib.util.spec_from_file_location('tk','tests/test_knowledge_export.py'); mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); base=Path('outputs/test-smart-summary-codex-citation').resolve(); import shutil; shutil.rmtree(base, ignore_errors=True); base.mkdir(parents=True, exist_ok=True); mod.test_generate_smart_summary_with_codex_auto_generates_local_final(base); print('smart_summary_codex_citation_digest_direct_test_ok')"
```

下一步优先级顺延为：把 run artifact registry 覆盖到更多长任务、把 Citation Digest 更自然地用于 content candidates 和人工抽样评估说明。
## Update: 2026-07-06 08:18:30 | Codex / GPT-5

### 已落地：Citation Digest 进入 content-candidate-pack

承接 VideoRAG/RAGFlow-style citation chunk 和上一轮 smart-summary chapter `citation_digest`，本轮把证据引用继续下沉到内容素材候选包：

- `export-knowledge-note` 生成 `content-candidate-pack.json/md` 时，会读取同一输出目录中的 `smart-summary-chapters.json`。
- 每条内容素材候选会按 `timeline_index` 绑定最多 8 条 `evidence_citations`。
- citation 字段保留 `source_type`、`time`、`timeline_indexes`、`text`、`evidence_paths`，用于证据导航，不复制整章内容。
- 候选包新增 `citation_digest_candidate_count` 和单条 `citation_digest_status`。
- `content-candidate-pack.md` 新增 `证据引用 / Citation Digest` 小节，让人工抽样和内容资产交接不必打开 JSON 才能看证据来源。
- 没有运行 `build-smart-summary-chapters` 时，候选仍可生成，但 Markdown 会明确标记 citation `not_available`，不会伪装成已证据化。
- 所有候选继续保持 `review_required=true`、`publication_allowed=false`、`allowed_as_fact=false`，只是更容易复核，不自动变成事实或发布稿。

代码落地：

- `src/video_knowledge_pipeline/knowledge_note_export.py`
- `tests/test_knowledge_export.py`

验证：

```powershell
python -m py_compile src\video_knowledge_pipeline\knowledge_note_export.py tests\test_knowledge_export.py
$env:PYTHONPATH='src'; python -c "import importlib.util; from pathlib import Path; spec=importlib.util.spec_from_file_location('tk','tests/test_knowledge_export.py'); mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); base=Path('outputs/test-content-candidate-citations').resolve(); import shutil; shutil.rmtree(base, ignore_errors=True); base.mkdir(parents=True, exist_ok=True); mod.test_export_includes_source_channels_demo_notes_and_crop_audit(base); print('content_candidate_citation_digest_direct_test_ok')"
```

下一步优先级顺延为：继续把 run artifact registry 覆盖到更多长任务，或把 content-candidate 的 citation/eval 信号进一步显示到 workbench 候选详情与人工抽样说明中。
## Update: 2026-07-06 08:24:57 | Codex / GPT-5

### 已落地：Citation Digest 进入 video-workbench 内容候选详情

承接上一轮 `content-candidate-pack` 已携带 `evidence_citations`，本轮把 citation/eval 信号继续推进到统一视频工作台，让人工抽样和内容资产筛选不用再只打开 JSON：

- `export-video-workbench` 的 `content_candidates` payload 现在会保留每条候选的 `citation_count`、`citation_summary`、`citation_digest_status` 和压缩后的 `evidence_citations`。
- 内容候选过滤器新增 `citation_ready` / `citation_missing`。
- `video-workbench.html` 内容素材候选面板新增 `Citation候选` 指标、`有Citation` / `缺Citation` 过滤按钮，以及候选表格里的 `Citation` 列。
- 这一步把“章节总结 -> Citation Digest -> 内容素材候选 -> 人工抽样/筛选”的链路做成可见 UI，而不是只停留在导出文件。
- Citation 仍然只是证据导航：候选继续保持 review-only，不允许自动发布，也不允许当作事实结论。

代码落地：

- `src/video_knowledge_pipeline/video_workbench.py`
- `tests/test_video_workbench.py`

验证：

```powershell
python -m py_compile src\video_knowledge_pipeline\video_workbench.py tests\test_video_workbench.py
$env:PYTHONPATH='src'; python -c "import importlib.util; spec=importlib.util.spec_from_file_location('tvw','tests/test_video_workbench.py'); mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); mod.test_export_video_workbench_writes_static_workspace(); print('video_workbench_candidate_citation_filters_direct_test_ok')"
```

下一步优先级顺延为：继续把 run artifact registry 覆盖到更多长任务，或把人工抽样说明里也显示 candidate citation/eval 线索。
## Update: 2026-07-06 08:28:42 | Codex / GPT-5

### 已落地：candidate Citation 进入 multimodal-sample-review 人工抽样说明

承接上一轮 `content-candidate-pack` 和 `video-workbench` 已显示 candidate citation，本轮把同一证据线索继续传递到人工抽样标注界面：

- `multimodal-sample-review` 读取内容素材候选时，会把候选的 `evidence_citations` 压缩进样本行。
- 样本行新增 `content_candidate_evidence_citations` 和 `content_candidate_citation_summary`。
- `multimodal-sample-review.html` 的“内容素材候选”块会显示 Citation summary、citation source/time/timeline/text/evidence path。
- `frame_paths` 会合并 candidate evidence path 与 citation evidence path，方便人工回看证据帧。
- 这一步服务于人工抽样：帮助判断“这条内容素材是否可用、证据是否足够”，不自动关闭复核、不写回 timeline、不批准发布。

代码落地：

- `src/video_knowledge_pipeline/multimodal_sample_review.py`
- `tests/test_multimodal_sample_review.py`

验证：

```powershell
python -m py_compile src\video_knowledge_pipeline\multimodal_sample_review.py tests\test_multimodal_sample_review.py
$env:PYTHONPATH='src'; python -c "import importlib.util; from pathlib import Path; import shutil; spec=importlib.util.spec_from_file_location('tm','tests/test_multimodal_sample_review.py'); mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); base=Path('outputs/test-sample-review-candidate-citations').resolve(); shutil.rmtree(base, ignore_errors=True); base.mkdir(parents=True, exist_ok=True); mod.test_multimodal_sample_review_writes_static_ui_and_notes_template(base); print('sample_review_candidate_citation_direct_test_ok')"
```

下一步优先级顺延为：继续把 run artifact registry 覆盖到更多长任务，或把本地 VLM smoke/provider 状态显示到 workbench provider 面板。## Update: 2026-07-06 08:31:45 | Codex / GPT-5

### 已文档化：当前模块复用地图

新增 docs/external-code-reuse-current-module-map-2026-07-06.md，作为继续开发前的短入口。该文档把外部项目复用状态整理为四类：

- 已吸收模块：vsummary、BiliNote、VideoRAG、VTimeLLM、MovieChat、Qwen/InternVL/LLaVA、FunASR/SenseVoice、Peepshow/VidClaude 已进入 VKP 的对应文件和入口。
- 仍值得继续复用模块：run artifact registry 全覆盖、provider/VLM 状态进入 workbench、ASR/字幕后处理、视频 RAG UI 跳转、内容素材与智能总结互链、高分辨率 tile recovery。
- 不建议继续搬的方向：整套 vsummary/BiliNote 后端 UI、重型向量/图数据库、模型源码内嵌、下载后端、默认全帧云多模态。
- 下一步顺序：先做 run artifact registry 全覆盖，再做 provider/VLM 状态面板，然后补 ASR/字幕后处理和 RAG/workbench 跳转。

这个文档用于替代聊天里的临时判断。后续如果继续吸收新外部项目，先更新这张地图，再决定是否进入 backlog 或实现。## Update: 2026-07-06 08:42:42 | Codex / GPT-5

### 已落地：Provider / 本地 VLM smoke 状态进入 video-workbench

承接 Qwen/InternVL/LLaVA 的 provider-adapter 思路和 vsummary 的 provider status 面板，本轮把已有 smoke 产物接入统一视频工作台：

- `export-video-workbench` 新增 provider_status payload。
- 工作台侧栏新增 Provider / 本地 VLM 面板。
- 面板读取已有 `vision-provider-smoke.json`、`vision-provider-matrix.json`、`local-vlm-serving-smoke.json`。
- 显示 provider smoke 状态、推荐 provider、本地 VLM plan/executed 状态、capability matrix 计数和报告入口。
- artifact 入口新增 `vision_provider_smoke`、`vision_provider_matrix`、`local_vlm_serving_smoke`。
- 这一步是纯只读状态展示：不启动 Qwen/InternVL 服务、不调用云 provider、不修改 timeline。

代码落地：

- src/video_knowledge_pipeline/video_workbench.py
- 	ests/test_video_workbench.py

验证：

`powershell
python -m py_compile src\video_knowledge_pipeline\video_workbench.py tests\test_video_workbench.py
$env:PYTHONPATH='src'; python -c "import importlib.util; spec=importlib.util.spec_from_file_location('tvw','tests/test_video_workbench.py'); mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); mod.test_export_video_workbench_writes_static_workspace(); print('video_workbench_provider_status_direct_test_ok')"
`

下一步优先级顺延为：继续把 run artifact registry 覆盖到剩余长任务，或者把 ASR/字幕仲裁后处理质量信号继续接进工作台和智能总结输入包。
## Update: 2026-07-06 08:50:24 | Codex / GPT-5

### 已落地：Provider / 本地 VLM smoke 接入 run artifact registry

承接 vsummary 的 stage/task state 和上一轮 workbench Provider / 本地 VLM 面板，本轮把 provider readiness 检查也纳入 `runs/*/run.json`：

- `vision-provider-smoke` 成功时登记 `run_type=vision_provider_smoke` / `status=completed`；provider 不可用时登记 `needs_retry` 和失败原因。
- `vision-provider-matrix` 成功推荐 provider 时登记 `run_type=vision_provider_matrix` / `status=completed`；没有 provider ready 时登记 `needs_retry`。
- `local-vlm-serving-smoke` 在 plan-only 模式登记 `run_type=local_vlm_serving_smoke` / `status=needs_execution`，明确表示本地模型服务尚未真实 smoke；execute 成功才是 `completed`。
- run artifacts 只保存报告路径、MCP args、脱敏状态和 operator boundary，不保存 API key，不启动本地模型服务，不修改 timeline。
- 这些 run 会被 `run-artifact-registry`、`task-console.html` 和 `video-workbench.html` 的 vision 队列拾取，形成 provider/VLM 状态可见、可重试的闭环。

代码落地：

- `src/video_knowledge_pipeline/vision_provider_smoke.py`
- `src/video_knowledge_pipeline/local_vlm_server_adapter.py`
- `tests/test_vision_providers.py`
- `tests/test_external_video_reuse_modules.py`

验证：

```powershell
python -m py_compile src\video_knowledge_pipeline\vision_provider_smoke.py src\video_knowledge_pipeline\local_vlm_server_adapter.py tests\test_vision_providers.py tests\test_external_video_reuse_modules.py
$env:PYTHONPATH='src'; python -c "... test_vision_provider_smoke_writes_no_secret_report_and_bundle_args ... test_vision_provider_matrix_recommends_first_ready_provider_and_writes_no_secret ..."
$env:PYTHONPATH='src'; python -c "... test_local_vlm_serving_smoke_defaults_to_plan_only ..."
```

下一步优先级顺延为：继续补 ASR/字幕后处理质量信号进入工作台，或把 VideoRAG 搜索结果到 timeline/content candidate 的跳转做得更细。
