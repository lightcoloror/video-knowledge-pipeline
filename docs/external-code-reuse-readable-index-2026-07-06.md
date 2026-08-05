# 外部开源项目代码复用可读索引

更新记录：

- 2026-07-06 12:43:32 | Codex / GPT-5：把已经审查和吸收过的外部 AI 视频项目，整理成一份面向后续开发的可读索引，避免继续在多个源码审查和 backlog 文档之间来回跳转。

## 这份文档回答什么

用户的问题是：还有哪些值得复用的代码模块？

当前结论是：VKP 不缺一个“完整替代品”，也不应该整体搬另一个 App。更正确的策略是继续把外部项目中低耦合、能提高准确率和审核效率的局部模块拆出来，接进 VKP 已经成型的链路。

VKP 当前主线是：

```text
本地/已下载视频
  -> ASR / 平台字幕 / 自带字幕
  -> 字幕仲裁 / 术语纠错 / 标点段落化
  -> 抽帧 / ebook-OCR / screen text / high-res tile
  -> 疑难点 triage / 多模态单帧/多帧复核
  -> timeline / evidence / review targets
  -> smart-summary / full-transcript / knowledge-note
  -> content candidates / video-workbench / handoff
```

外部代码复用只应该增强这条主线里的局部节点。

## 一句话结论

下一阶段最值得继续复用的不是“更多视频总结项目”，而是这些模块：

1. 任务状态和重试队列。
2. 字幕/ASR 仲裁质量后处理。
3. ebook/OCR 失败后的 high-res tile recovery。
4. 视频 RAG / moment search / citation 跳转。
5. 智能总结章节级质量闭环。
6. 本地 VLM serving smoke。
7. 内容素材候选和智能总结双向链接。

## 已经基本复用到位的部分

| 来源 | 已吸收的能力 | VKP 落点 | 当前判断 |
| --- | --- | --- | --- |
| `alpha03123/vsummary` | OpenAI-compatible text gateway、JSON repair、stage cache、run artifact、timestamp/citation UI、CUDA 检测 | `text_llm_gateway.py`、`stage_cache.py`、`run_artifact_registry.py`、`task_console.py`、`video_workbench.py`、`cuda_runtime.py` | 核心价值已吸收，不搬整套后端 |
| `PrideWood/bilinote` | 字幕解析清洗、短句合并、转写校对 prompt、mind-map prompt、transcript editor、章节编辑体验 | `bilinote_transcript_tools.py`、`bilinote_summary_tools.py`、`transcript_correction_pack.py`、`transcript_editor.py`、`smart_summary_section_editor.py` | 继续吸收交互细节，不搬整套 React UI |
| VideoRAG | video chunk、JSONL/SQLite 检索、citation evidence | `video_rag_pack.py`、`video_rag_search.py`、`video_rag_http.py`、`smart_summary_chapters.py` | 保留轻量本地 RAG，不默认引入重型向量库 |
| VTimeLLM | moment grounding、时间定位、alignment audit | `video_moment_index.py`、`timeline_alignment_audit.py` | 继续服务时间戳纠偏和 evidence 回跳 |
| MovieChat | 长视频 short memory / long memory 分层 | `long_video_memory_pack.py`、`smart_summary_input_pack.py` | 服务长视频总结输入，不单独做聊天系统 |
| Qwen-VL / InternVL / LLaVA-OneVision | 图像缩放压缩、多图输入、dynamic tiling、高分辨率 tile | `vlm_preprocess.py`、`high_res_tile_plan.py`、`tile_result_import_builder.py`、`tile_result_merge.py` | 不嵌模型源码，只做 adapter 和预处理 |
| FunASR / SenseVoice / WhisperX | 本地 ASR、timestamp sidecar、模型 ready gate、word-level/speaker/punctuation 后处理路线 | `funasr_python_runner.py`、`asr_runner.py`、`asr_environment.py`、`transcript_sidecar.py`、`transcript_source_arbitration.py` | 继续补后处理和质量信号 |
| Peepshow / VidClaude | 帧证据卡、视觉复核队列、人工抽样评分 | `vision_review_queue.py`、`multimodal_sample_review.py`、`video_workbench.py` | 继续强化人审 UI 和指标 |

## 还值得继续复用的模块

### P0：任务状态和重试队列全覆盖

参考来源：

- vsummary 的 stage/task state。
- BiliNote 的任务面板。
- Peepshow / VidClaude 的批次报告。

应该继续落地：

- 每个长任务都写 `runs/<task>/run.json` 和 `run.md`。
- 每条 run 包含 `status`、`artifacts`、`failed_items`、`retry_command`、`next_actions`、`operator_boundary`。
- `task-console.html` / `video-workbench.html` 显示批次大小、总批次数、失败 indexes、报告路径和重试命令。
- `subqueue-action-plan` 给 agent / OpenClaw 返回机器可读下一步计划。

为什么优先级最高：

- 它直接减少“复制几十条命令”的人工负担。
- 它能让 ASR、ebook、tile、多模态、summary、content candidate 都进入同一个进度视图。
- 它是后续 OpenClaw 调用稳定性的基础。

### P0：ASR / 字幕仲裁质量后处理

参考来源：

- BiliNote 字幕清洗。
- WhisperX word-level timestamp / diarization。
- SenseVoice emotion / event tags。

应该继续落地：

- `transcript-source-arbitration` 输出更完整的 `quality_summary`。
- 标点恢复、段落化、术语词典、人名/品牌/工具名纠错进入纠正版 transcript。
- 高置信纠错自动进入 `corrected_transcript`。
- 低置信冲突进入 review pack。
- `smart-summary-input-pack` 和 `video-workbench` 显示哪些术语可信、哪些需要复核。

为什么重要：

- 最终人类可读文件主要受 transcript 质量影响。
- 很多视频网站字幕本身也是 ASR 生成，不能盲信。
- 术语、人名、工具名错了，智能总结会被带歪。

### P1：high-res tile recovery 与 ebook/OCR 分工

参考来源：

- InternVL dynamic tiling。
- Qwen-VL 图像预处理。
- 本地 `ebook_markdown_pipeline` 图文解析。

应该继续落地：

- 整帧 ebook/OCR 为空、wrapper-only、低信息量时自动标记 `needs_high_res_tile_recovery`。
- 小字、表格、代码、软件界面截图走局部 tile evidence。
- tile 结果保留坐标、来源、置信度、review 状态。
- 有效 tile 结果可以回填 `visual_text` / `structured_visual`；低质结果只进入 review。

边界：

- ebook 仍是图文截图主通道。
- tile 是失败补救和小字增强，不是新的 OCR 引擎。
- 低置信结果不能伪装成已完成提取。

### P1：视频 RAG / moment search / citation 跳转

参考来源：

- VideoRAG retrieval unit。
- VTimeLLM time grounding。
- vsummary timestamp seek / citation UI。

应该继续落地：

- 搜索术语、工具名、案例、方法时，返回时间段、timeline row、证据来源。
- `smart-summary.md` 关键观点回链到 moment chunk。
- content candidate 回链到 transcript、visual evidence、review gap。
- `video-workbench` 搜索结果能跳视频时间、timeline row、素材候选。

为什么重要：

- 这能把“总结文字”变成可追溯的知识资产。
- 不需要默认引入重型向量库；JSONL / keyword / SQLite 足够作为个人工具主线。

### P1：智能总结章节级质量闭环

参考来源：

- BiliNote 章节笔记和 prompt 分块。
- vsummary 分段总结 pipeline。
- MovieChat long memory。
- VideoRAG citation digest。

应该继续落地：

- 每章独立生成、复核、安装。
- 每章保留 transcript、OCR/ebook、visual、temporal、review gap 的 `citation_digest`。
- Codex 和未来在线 LLM 共用同一份 input pack。
- 质量门禁检查完整时长覆盖、避免 ASR 复制粘贴、避免只总结前几分钟。

边界：

- `smart-summary.md` 是成品阅读层。
- `knowledge-note.md` 是证据审计层。
- `full-transcript.md` 是逐字稿层。
- 三层不要混在一起。

### P2：本地 VLM serving smoke

参考来源：

- Qwen-VL OpenAI-compatible serving。
- InternVL dynamic tiling。
- LLaVA-OneVision 多图/短片段输入。

应该继续落地：

- 只读检查本地 VLM 服务地址、模型名、单图、多图、帧组、JSON 输出稳定性。
- smoke 结果进入 `runs/local-vlm-serving-smoke/run.json`。
- `video-workbench` 显示本地 VLM plan / executed / failed 状态。

边界：

- 不自动启动模型服务。
- 不把本地 VLM 变成默认硬依赖。
- 不把模型仓库源码嵌入 VKP 主流程。

### P2：内容素材候选与智能总结双向链接

参考来源：

- vsummary clips / summary 输出结构。
- BiliNote 笔记导出体验。
- VideoRAG evidence path。

应该继续落地：

- 从 smart-summary section 跳到 content candidates。
- 从 content candidate 跳回章节、时间戳、证据帧、review rows。
- 支持素材类型过滤：`method`、`case`、`quote`、`visual_explainer`、`tool`、`workflow`。
- `content-asset-status` / `content-handoff-pack` 保留章节引用。

边界：

- 内容素材仍是 inspiration / evidence，不是事实结论。
- 默认 `review_required=true`、`publication_allowed=false`、`allowed_as_fact=false`。

## 不建议继续搬的模块

| 不建议方向 | 原因 | VKP 替代路线 |
| --- | --- | --- |
| vsummary 整套 FastAPI / React / LlamaIndex / LanceDB | 会形成第二套后端、第二套 UI、第二套索引 | 只吸收 provider、stage、run、citation、UI 交互 |
| BiliNote 整套 React UI | UI 好，但整体搬会破坏 VKP 静态 bundle / CLI / MCP / OpenClaw 结构 | 在 `video-workbench.html` 复刻关键交互 |
| VideoRAG 重型 graph / vector 后端 | 依赖重，维护成本高 | 默认 JSONL / keyword / SQLite，vector 只做可选 |
| Qwen / InternVL / LLaVA 模型源码内嵌 | 显存、环境、部署复杂 | provider adapter + preprocess + smoke |
| 下载/字幕抓取后端 | VKP 边界是内容理解，不负责下载 | 继续交给 `video-download-orchestrator` |
| 默认全帧云多模态 | 成本、隐私、限流、失败恢复不适合默认 | 本地抽帧/ebook/OCR/triage 先跑，云多模态只补疑难点或显式全量模式 |

## 判断新项目是否值得继续拉源码

看到新的 AI 视频总结/分析项目时，先按这五个问题判断：

1. 它是否提供 VKP 当前没有的低耦合模块？
2. 它是否能不引入重依赖单独复用？
3. 它是否改善当前瓶颈：智能总结质量、时间定位、小字 OCR、批次重试、人审评分？
4. 它是否要求替换 VKP 主架构？如果是，默认拒绝整体迁移，只拆模块。
5. 它是否绕过下载、云 API、人工复核边界？如果是，不进主线。

## 当前推荐开发顺序

1. 把剩余长任务全部接进 run artifact registry 和 subqueue action plan。
2. 增强 ASR/字幕仲裁后处理，重点是术语、标点、段落化、说话人。
3. 完善 high-res tile recovery 与 ebook/OCR 失败分流。
4. 打通 VideoRAG / moment search / citation 到 workbench 的跳转。
5. 继续提升 smart-summary 章节级质量闭环。
6. 做本地 VLM serving smoke，但保持可选。
7. 把内容素材候选和智能总结章节互链做成更自然的 UI 导航。

## 文档入口

如果只想知道下一步怎么开发，读本文即可。

需要细节时再看：

- `docs/external-code-reuse-ledger-2026-07-04.md`
- `docs/external-code-module-reuse-backlog-2026-07-04.md`
- `docs/external-code-reuse-current-module-map-2026-07-06.md`
- `docs/external-code-reuse-next-module-decisions-2026-07-06.md`
- `docs/external-code-reuse-closure-and-next-actions-2026-07-06.md`
- `docs/external-open-source-reuse-module-inventory-2026-07-06.md`
- `docs/vsummary-source-review.md`
- `docs/bilinote-pridewood-source-review.md`
- `docs/ai-video-open-source-survey-2026-07-04.md`
- `docs/smart-summary-best-practices.md`
## Update: 2026-07-06 12:43:32 | Codex / GPT-5

### 已落地：BiliNote mind-map prompt pack 进入 bundle / run / UI 队列

承接 PrideWood/BiliNote 的思维导图 prompt 和 transcript 分块思路，本轮把原来的纯 transcript prompt 生成器补成 bundle-aware 的本地产物生成模块：

- 新增 bundle 入口：`bilinote-mind-map-prompt-pack --bundle-dir <webui-bundle>`。
- 从 bundle 的最佳 transcript sidecar 读取完整转写，不依赖用户手工粘贴 transcript。
- 写出：
  - `exports/bilinote-mind-map-prompt-pack.json`
  - `exports/bilinote-mind-map-prompt-pack.md`
  - `mcp-bilinote-mind-map-prompt-pack.args.json`
- 更新 `manifest.json` 对应索引。
- 登记 `run_type=bilinote_mind_map_prompt_pack`，进入 `runs/bilinote-mind-map-prompt-pack/run.json/md` 和 `run-artifact-registry`。
- `task-console` 将它归入“总结 / 导出 -> 总结输入包”，而不是落到其他任务。
- MCP 暴露 `bilinote_mind_map_prompt_pack` / `bilinote_mind_map_prompt_pack_tool`。

边界：

- 只生成 prompt pack，不调用 LLM。
- 不声称已经生成脑图。
- 发送给 Codex 或在线文本模型前仍应人工确认 transcript 和术语。

代码落地：

- `src/video_knowledge_pipeline/bilinote_mind_map_prompt_pack.py`
- `src/video_knowledge_pipeline/cli.py`
- `src/video_knowledge_pipeline/mcp_server.py`
- `src/video_knowledge_pipeline/task_console.py`
- `tests/test_bilinote_summary_tools.py`
- `tests/test_task_console.py`

## Update: 2026-07-06 12:58:32 | Codex / GPT-5

### 已落地：VideoRAG content candidate retrieval chunks

承接 VideoRAG 的 retrieval-unit 思路和 VKP 已有 `content-candidate-pack`，本轮把“内容素材候选”从导出文件进一步接进本地 RAG 检索层：

- `video-rag-pack` 现在会读取 `exports/content-candidate-pack.json`，把每条候选素材生成独立 `content_candidate` JSONL chunk。
- 每个候选 chunk 保留：
  - `candidate_id`
  - `candidate_types`
  - `fact_status`
  - `review_required`
  - `publication_allowed`
  - `allowed_as_fact`
  - `citation_count`
  - `summary_chapter_refs`
  - `evidence_paths`
- `video-rag-search` 的命中结果会返回 `candidate_id`、`candidate_types`、`summary_chapter_refs`，所以可以直接搜方法、工具名、案例、话术，例如“手套越薄”。
- `video-rag-pack` summary 新增 `content_candidate_chunks`，方便 batch/report/UI 判断候选素材是否进入检索层。
- 原有 `content_asset` chunk 同时保留，`smart-summary.md`、`key-segments.md`、`content-material-card.*` 等成品资产仍作为资产级 retrieval unit。

这一步的边界仍是本地轻量 RAG：

- 不启动向量库。
- 不调用云模型。
- 不把候选素材标成事实。
- 不允许自动发布。

验收口径：

```powershell
python -m py_compile src\video_knowledge_pipeline\video_rag_pack.py src\video_knowledge_pipeline\video_rag_search.py tests\test_external_video_reuse_modules.py

$env:PYTHONPATH='src'; python -c "import importlib.util, shutil; from pathlib import Path; spec=importlib.util.spec_from_file_location('t','tests/test_external_video_reuse_modules.py'); mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); root=Path('outputs/test-video-rag-content-candidate-direct').resolve(); shutil.rmtree(root, ignore_errors=True); (root/'pack').mkdir(parents=True, exist_ok=True); (root/'search').mkdir(parents=True, exist_ok=True); mod.test_video_rag_pack_writes_jsonl_retrieval_units(root/'pack'); mod.test_video_rag_search_reads_jsonl_and_writes_search_artifacts(root/'search'); print('video_rag_content_candidate_chunks_direct_tests_ok')"

$env:PYTHONPATH='src'; python -m video_knowledge_pipeline.cli video-rag-pack outputs\test-video-rag-content-candidate-direct\pack\bundle --query "手套越薄" --no-write
```

本轮验证结果：

- `py_compile` 通过。
- 直接调用两条 VideoRAG 测试函数通过。
- CLI smoke 返回 `content_candidate_chunks=1`、`content_asset_chunks=6`，并生成 `content_candidate` retrieval unit。

## Update: 2026-07-06 18:05:00 | Codex GPT-5

### P0 continued: external reuse RAG / memory / capability runs now register artifacts

承接 vsummary task status / run artifact registry 的复用方向，本轮把已经吸收进 VKP 的 VideoRAG、MovieChat、VTimeLLM 和 external capability pack 入口补齐 run artifact 登记，让 task console / subqueue-action-plan 在真实 bundle 上能看到这些长任务的状态、产物和重试命令。

新增覆盖的公开入口：

- `video-moment-index` -> `runs/video-moment-index/run.json`
- `long-video-memory-pack` -> `runs/long-video-memory-pack/run.json`
- `video-rag-pack` -> `runs/video-rag-pack/run.json`
- `video-rag-search` -> `runs/video-rag-search/run.json`
- `video-rag-service-plan` -> `runs/video-rag-service/run.json`
- `external-capability-pack` -> `runs/external-capability-pack/run.json`

状态规则：

- 成功生成本地产物：`completed`。
- 没有 timeline/moment/chunk 输入：`needs_input`，写入 `failed_items`。
- `video-rag-search --retrieval-backend vector` 仍是未来占位，会 fallback 到 keyword，并登记为 `needs_review`。
- `video-rag-service-plan` 只生成本地 HTTP 服务计划，不启动服务，所以登记为 `needs_execution`。

边界：

- 不启动 VideoRAG HTTP 服务。
- 不调用云模型。
- 不处理新视频。
- 不引入向量库或 graph DB。
- 只是把本地执行状态写进 `run-artifact-registry`，供 UI/MCP/OpenClaw 读取。

代码落地：

- `src/video_knowledge_pipeline/external_reuse_run_artifacts.py`
- `src/video_knowledge_pipeline/video_moment_index.py`
- `src/video_knowledge_pipeline/long_video_memory_pack.py`
- `src/video_knowledge_pipeline/video_rag_pack.py`
- `src/video_knowledge_pipeline/video_rag_search.py`
- `src/video_knowledge_pipeline/video_rag_http.py`
- `src/video_knowledge_pipeline/external_capability_pack.py`
- `tests/test_external_video_reuse_modules.py`

验证：

```powershell
python -m py_compile src\video_knowledge_pipeline\external_reuse_run_artifacts.py src\video_knowledge_pipeline\video_moment_index.py src\video_knowledge_pipeline\long_video_memory_pack.py src\video_knowledge_pipeline\video_rag_pack.py src\video_knowledge_pipeline\video_rag_search.py src\video_knowledge_pipeline\video_rag_http.py src\video_knowledge_pipeline\external_capability_pack.py tests\test_external_video_reuse_modules.py

$env:PYTHONPATH='src'; python -c "import importlib.util, shutil; from pathlib import Path; spec=importlib.util.spec_from_file_location('t','tests/test_external_video_reuse_modules.py'); mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); root=Path('outputs/test-external-reuse-run-artifacts-direct').resolve(); shutil.rmtree(root, ignore_errors=True); root.mkdir(parents=True, exist_ok=True); mod.test_video_moment_index_builds_queryable_evidence_chunks(root/'moment'); mod.test_long_video_memory_pack_groups_short_memories(root/'memory'); mod.test_video_rag_pack_writes_jsonl_retrieval_units(root/'ragpack'); mod.test_video_rag_search_reads_jsonl_and_writes_search_artifacts(root/'search'); mod.test_video_rag_http_response_serves_health_and_search(root/'http'); mod.test_external_capability_pack_groups_reusable_local_capabilities(root/'capability'); print('external_reuse_run_artifacts_direct_tests_ok')"
```

下一步优先级顺延为：继续把 task console 的 `subqueue-action-plan` 用这些真实 run artifacts 做端到端 smoke，或者补 `video-workbench` 对这些 run 的显式入口/状态筛选。

## Update: 2026-07-06 18:35:00 | Codex / GPT-5

### video-workbench 已接入外部复用能力总览

现在 `export-video-workbench <webui-bundle>` 会生成 `video-workbench.json.external_reuse_status`，并在 `video-workbench.html` 左栏显示“外部复用能力”面板。它把之前分散在 VideoRAG、MovieChat、VTimeLLM、本地 VLM adapter、vsummary/BiliNote 内容素材能力里的 run artifacts，按能力聚合成一个状态表。

面板按 5 类能力显示：

| 能力 | 参考来源 | VKP 当前入口 | 状态含义 |
| --- | --- | --- | --- |
| 时间定位 / VTimeLLM | VTimeLLM、VideoRAG | `video-moment-index`、`timeline-alignment-audit` | 片段索引和时间轴证据是否已生成 |
| 长视频 memory / MovieChat | MovieChat | `long-video-memory-pack` | 长视频分层 memory 是否已生成 |
| VideoRAG 本地检索 | VideoRAG | `video-rag-pack`、`video-rag-search`、`video-rag-service-plan` | 本地检索包是否 ready，HTTP 服务是否还需显式启动 |
| 本地 VLM adapter | Qwen-VL、InternVL、LLaVA-OneVision | `local-vlm-serving-smoke`、`vision-provider-smoke` | 本地/云视觉 provider 是否完成 smoke 或仍需执行 |
| 内容素材能力包 | vsummary、BiliNote、VKP content assets | `external-capability-pack`、`content-candidate-pack`、`smart-summary` | 内容素材候选、章节链接和外部能力包是否可交接 |

使用口径：

- `ready`：已有本地 run artifact，且没有 action-required 状态。
- `action_required`：存在 `needs_input`、`needs_review`、`needs_execution`、`needs_retry`、`failed`、`blocked` 等状态，需要人工或 agent 执行下一步。
- `missing`：当前 bundle 还没有跑过该能力。

重要边界：这个面板只是统一展示和复制命令，不自动执行，不调用云模型，不启动本地模型服务，也不把内容素材标成可发布事实。
## Update: 2026-07-06 19:05:00 | Codex / GPT-5

### subqueue-action-plan 现在是 agent 可读的下一步调度单

`subqueue-action-plan <webui-bundle>` 现在不只是列出子队列和 retry command，还会为每个子队列生成调度语义：

| 字段 | 用途 |
| --- | --- |
| `action_status` | 真实动作状态：`needs_input`、`needs_review`、`needs_retry`、`needs_execution` 等 |
| `action_kind` | 调度分类：人工输入、人工复核、可重试、显式执行、阻塞/失败 |
| `priority` | 排序字段，让人工/阻塞项优先浮出来 |
| `primary_command` | 第一条可复制命令 |
| `blocked_reason` | 最短问题原因，来自 failed item 或 next action |
| `machine_action_available` | agent 是否可以继续走机器动作 |
| `operator_review_required` | 是否必须人介入 |

这吸收的是 vsummary task status / retry queue 的核心思路，但保留 VKP 的安全边界：只读计划，不执行命令，不启动服务，不调用云模型。它适合给 OpenClaw、MCP agent、task console、video-workbench 当“下一步做什么”的统一数据源。

## Update: 2026-07-06 19:35:00 | Codex / GPT-5

### video-workbench 现在直接显示下一步调度

`export-video-workbench <webui-bundle>` 现在会把 `subqueue-action-plan` 的同一份调度语义写入 `video-workbench.json.subqueue_action_plan`，并在 `video-workbench.html` 左栏显示“下一步调度”。

这意味着主工作台、task console、CLI/MCP 都共享同一套判断：哪些子队列需要人工输入、哪些需要人工复核、哪些可以机器重试、哪些只是显式执行计划。页面只展示和复制命令，不会执行命令、不调用云、不启动服务。
## Update: 2026-07-06 21:45:50 | Codex / GPT-5

### vision-review-queue 的批次队列现在能告诉 agent 具体下一步

`vision-review-queue` 的运行产物不再只是说“还有视觉理解没跑完”。它现在会把每个 pending / failed index 映射回具体批次，并写入 `runs/vision-review-queue/run.json.failed_items`。

这对 UI 和 agent 的意义是：

| 以前 | 现在 |
| --- | --- |
| 只能看到视觉队列需要重试 | 能看到哪个 batch、哪些 indexes、为什么需要跑 |
| retry command 可能只是整队列脚本 | 优先给第一个可执行批次的 `-Execute` 命令 |
| pending 和 failed 不好区分 | `visual_understanding_pending` 与 `visual_understanding_failed_or_incomplete` 分开 |
| task console 的 blocked reason 容易泛泛 | 可以显示 `Batch N pending indexes: ...` |

边界仍然很清楚：页面和 JSON 只提供复制命令，不会自动调用火山/OpenAI/Gemini 等云视觉 API。真正发送帧仍要由人或被授权的 agent 执行带 `-Execute` 的批次脚本。

已验证：`py_compile` 通过，`vision_review_queue` 和 `task_console` 相关直接测试通过。
## Update: 2026-07-06 22:20:00 | Codex / GPT-5

### smart-summary 章节工作流现在是“待输入”，不是“重跑”

`smart-summary-section-workflow` 现在更像 BiliNote/vsummary 那种章节级任务队列：如果某些章节需要重写，它不会再把状态伪装成普通 `needs_retry`，而是登记为 `needs_input`。

现在每个待修订章节都会进入 `runs/smart-summary-section-workflow/run.json.failed_items`，带有章节 id、标题、时间范围、修订原因、citation 数量、rewrite prompt 摘要、todo 文件、编辑器入口和 apply 命令。

这对操作台的意义：

| 以前 | 现在 |
| --- | --- |
| 看到 section workflow 需要 retry | 看到章节修订需要输入 |
| 主命令可能只是重跑 workflow | 主命令指向 `smart-summary-section-editor` |
| agent 不知道下一步是人工/LLM 写章节 | `subqueue-action-plan` 标记为 `operator_input_required` |
| 章节待办散在 markdown/json 里 | run artifact 里有可读 action item |

边界仍然保持：不调用 LLM、不自动改写总结、不自动 apply，只把下一步操作做清楚。
## Update: 2026-07-06 22:55:00 | Codex / GPT-5

### ebook/图文解析失败现在有更具体的恢复动作

`run-visual-structure --execute-ebook-pipeline` 的失败项现在不只是写一个 blocker。每条失败 item 会带上证据路径和下一步动作。

| blocker 类型 | 下一步 |
| --- | --- |
| `umi_ocr_missing` / pipeline unavailable / timeout | 修本地 `ebook_markdown_pipeline` 后，对同一个 index 重跑 `run-visual-structure` |
| `ocr_wrapper_only` / `ocr_text_empty` / `ocr_text_low_information` | 先走 `high-res-tile-plan` 生成局部 tile 证据 |
| tile 仍无可靠结果 | 进入多模态 triage 或人工 review |

新增字段包括 `evidence_paths`、`ebook_retry_command`、`tile_recovery_command`、`multimodal_triage_command`、`review_command`。这让 document OCR / ebook 队列以后可以从 UI 或 agent 里直接看见“下一步该点哪条链”。

边界不变：不自动跑 ebook、tile、VLM 或云 API；空 OCR 和 wrapper-only 不会被当作成功。
## Update: 2026-07-06 23:25:00 | Codex / GPT-5

### task console 现在能看见 failed item 里的具体下一步命令

上一轮 ebook/图文解析失败项已经写入了 `ebook_retry_command`、`tile_recovery_command`、`multimodal_triage_command`、`review_command` 等字段；这轮把这些字段接进 `task-console` 和 `subqueue-action-plan`。

效果是：

| 以前 | 现在 |
| --- | --- |
| 控制台只显示 `index / reason / detail` | 控制台还能显示 `next:<tool>` 和 evidence 数量 |
| 子队列优先复制 run-level retry command | 子队列优先复制 failed item 的具体命令 |
| ebook blocker 虽然有补救字段，但 agent 不容易读到 | `document_ocr:ebook.primary_command` 可直接指向 high-res tile 或同 index ebook retry |

边界仍然保持：task console 只读，不自动执行任何命令。

## Update: 2026-07-06 14:04:55 | Codex / GPT-5

### 已文档化：外部代码复用作战手册

新增 `docs/external-code-reuse-practical-playbook-2026-07-06.md`，作为“以后看到新的 AI 视频项目要怎么拆、怎么复用、什么时候停止”的操作手册。

这份手册把当前结论收束为：

- 不再整体迁移 vsummary、BiliNote、VideoRAG、MovieChat 或 VLM 项目的完整架构。
- 继续吸收低耦合模块：run artifact、字幕仲裁质量、high-res tile、小字 OCR、时间定位、智能总结章节闭环、内容素材 citation。
- 每个复用模块都要落到 VKP 的 timeline/evidence/review/workbench/CLI-MCP 边界里。
- 默认不下载、不云端全量多模态、不自动发布、不把低置信结果伪装成事实。

后续继续开发前，先看这份 playbook，再决定是否拉新源码或继续补现有模块。
## Update: 2026-07-06 14:04:55 | Codex / GPT-5

### 已落地：screen-text / high-res tile / tile import-merge 失败项动作字段

承接 vsummary 的 run artifact / retry queue 思路，以及 InternVL/Qwen-style high-res tile recovery，本轮把屏幕文字和 tile OCR/VLM 补救链路的失败项继续细化：

- `screen_text_recovery` 的 `crop_failed` / `ocr_text_empty` 失败项现在带有：
  - `suggested_next_tool`
  - `suggested_retry_command`
  - `tile_recovery_command`
  - `multimodal_triage_command`
  - `review_command`
  - `evidence_paths`
- `high_res_tile_plan` 的 `tile_plan_failed` / `tile_write_failed` 失败项现在带有同 index 重试命令、review 命令和 evidence paths。
- `tile_result_import_build` 的 `tile_result_pending` 失败项现在带有 tile result import、tile result merge、review 命令和 tile evidence path。
- `tile_result_merge` 的低置信、空结果、wrapper-only review target 现在也会进入 run artifact failed_items，并带回 import/merge/review 命令。
- `task_console` / `subqueue-action-plan` 已接入 `tile_result_import_command` 和 `tile_result_merge_command`，因此 document OCR / high-res tile 子队列会优先展示具体 item-level 命令，而不是退回 run-level retry。

这一步的目标不是执行 OCR/VLM，而是让 UI 和 agent 都能知道下一步该走：重跑 crop、生成 high-res tile、导入 tile 结果、合并 tile 结果，还是进入人工复核。

边界保持不变：不自动调用云多模态，不把空 OCR 当成功，不自动清除 blocker。
## Update: 2026-07-06 14:04:55 | Codex / GPT-5

### 已落地：ASR/字幕仲裁质量信号进入 smart-summary 输入层

承接 BiliNote 字幕清洗、WhisperX word-level/speaker 质量路线、SenseVoice 元数据路线，本轮把已有 `transcript-source-arbitration` 从“纠正版转写产物”继续推进为“总结层可读取的质量策略”：

- `transcript_source_arbitration.quality_summary` 新增：
  - `summary_input_policy`
  - `review_required`
  - `safe_segment_count`
  - `trusted_segment_indexes`
  - `review_segment_refs`
- `summary_input_policy` 会明确告诉后续 Codex/在线 LLM：
  - 是否能使用纠正版 transcript；
  - 是否必须排除待复核片段；
  - 当前是 `clean`、`corrected_clean`、`partial_with_review_gaps` 还是 `missing_transcript`。
- `transcript_source_arbitration` 的 run artifact failed items 现在会把低置信冲突带上 time range、confidence、transcript editor 命令和 review 命令。
- `smart_summary_input_pack` 新增顶层 `transcript_quality_policy`，并在 Markdown 的“字幕/ASR 仲裁质量”区块显示 summary input mode、可否使用纠正版、是否必须排除 review segments、安全片段数和待复核片段表。
- `smart_summary_input_pack` 的 run artifact 也会把 transcript arbitration review refs 作为 `transcript_arbitration_review` failed items 暴露给 task console / subqueue-action-plan。

这一步让智能总结输入层不再只知道“有一份纠正版转写”，而是知道哪些词和段落可以放心用、哪些段落必须复核后才能当事实。
## Update: 2026-07-06 14:04:55 | Codex / GPT-5

### 已落地：字幕仲裁质量策略进入 video-workbench

承接上一轮 `transcript_quality_policy`，本轮把 ASR/字幕仲裁质量从 smart-summary 输入层继续推进到统一视频工作台：

- `video-workbench.json.transcript_arbitration` 现在暴露：
  - `summary_input_policy`
  - `review_segment_refs`
  - `next_commands`
- `review_segment_refs` 会作为 workbench 的字幕仲裁卡片优先数据源，保留 time range、reason、confidence、original/corrected text。
- 字幕仲裁面板新增“总结输入”指标，显示 policy mode 和 safe segment count。
- 面板会显示策略 guidance，并给出可复制命令：
  - `prepare-transcript-edit-session`
  - `prepare-review-session`
  - `transcript-source-arbitration`
- 这一步继续复用 BiliNote 的同屏转写编辑体验和 vsummary 的 run/action 可见化思路，让用户不用打开 JSON 才知道哪些字幕段会污染最终智能总结。

边界保持：workbench 仍是静态本地页面，只展示和复制命令，不自动修改转写、不调用 LLM、不覆盖 review 边界。
## Update: 2026-07-06 15:05:00 | Codex / GPT-5

### 已落地：content candidate 与 moment/RAG chunk 互链进入 video-workbench

承接 VideoRAG retrieval unit、VTimeLLM moment grounding 和 vsummary timestamp seek/citation UI，本轮把内容素材候选与片段索引/本地 RAG chunk 的关系做成 workbench 可见字段：

- `export-video-workbench` 现在会按 `timeline_index` 和 candidate citation timeline，把每条 content candidate 关联到：
  - `video-moment-index.json` 中的 moment chunk；
  - `video-rag-chunks.jsonl` 中 timeline 重叠的 review gap、chapter memory、theme memory、content asset chunk。
- `video-workbench.json` 的候选素材新增：
  - `moment_links`
  - `moment_link_count`
  - `moment_link_summary`
- `content_candidates.filter_counts` 新增：
  - `moment_linked`
  - `moment_missing`
- `video-workbench.html` 内容素材候选面板新增：
  - `片段互链` 指标；
  - `已关联片段 / 缺片段` 过滤按钮；
  - `关联片段` 表格列；
  - 可点击 `moment #...` / RAG chunk 按钮，复用页面已有 `selectSearchChunk` 跳转到对应片段、timeline row 和视频时间。

这一步不引入向量库、不启动服务、不修改 `content-candidate-pack.json` 原始导出，只在 workbench 导出层生成轻量互链视图。它把“素材候选 -> 章节 citation -> moment/RAG -> 时间轴/视频”的回跳链路补了一格。

代码落地：

- `src/video_knowledge_pipeline/video_workbench.py`
- `tests/test_video_workbench.py`

验证：

```powershell
python -m py_compile src\video_knowledge_pipeline\video_workbench.py tests\test_video_workbench.py
$env:PYTHONPATH='src'; python -c "import importlib.util; spec=importlib.util.spec_from_file_location('tvw','tests/test_video_workbench.py'); mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); mod.test_export_video_workbench_writes_static_workspace(); print('video_workbench_candidate_moment_links_direct_test_ok')"
```

下一步优先级顺延：继续补 run artifact registry 剩余长任务覆盖，或者把 ASR/字幕后处理从质量摘要推进到标点、术语词典、段落化、说话人。
## Update: 2026-07-06 15:32:00 | Codex / GPT-5

### P0 continued: multimodal sample review and human sample eval now register run artifacts

承接 Peepshow/VidClaude 的人工抽样评估思路，以及 vsummary 的 run artifact / retry queue，本轮把 `multimodal-sample-review` 和 `validate-multimodal-sample-notes` 从“只生成独立报告”推进到“进入统一任务队列”：

- `multimodal-sample-review` 现在登记 `runs/multimodal-sample-review/run.json`。
- 初始抽样页生成后，run 状态为 `needs_input`，因为需要人工标注。
- run artifacts 包含：
  - `multimodal-sample-review.json`
  - `multimodal-sample-review.todo.json`
  - `multimodal-sample-review.md`
  - `multimodal-sample-review.html`
  - PotPlayer playlist / timestamps
  - MCP args
- 每个待标注样本会进入 `failed_items`，reason 为 `human_sample_label_required`，并带：
  - timeline index
  - sample type
  - time range / review start
  - evidence frame paths
  - review HTML
  - validate notes 的 suggested retry command
- `validate-multimodal-sample-notes` 现在登记 `runs/human-sample-eval/run.json`。
- 根据人工标注汇总状态映射 run status：
  - `ready` -> `completed`
  - `not_started` / `needs_more_labels` -> `needs_input`
  - `needs_model_review` -> `needs_review`
  - `invalid` -> `needs_retry`
- `human_sample_eval` run 的 failed items 会明确区分：未标注样本、无效标注行、模型幻觉/重大多模态错误待复核。

这一步让“多模态到底有没有提升最终人类可读文件”这件事进入 task console / video-workbench / subqueue-action-plan 可见队列，而不是散落在单独 HTML 和 Markdown 里。

代码落地：

- `src/video_knowledge_pipeline/multimodal_sample_review.py`
- `tests/test_multimodal_sample_review.py`

验证：

```powershell
python -m py_compile src\video_knowledge_pipeline\multimodal_sample_review.py tests\test_multimodal_sample_review.py
$env:PYTHONPATH='src'; python -c "import importlib.util; from pathlib import Path; import shutil; spec=importlib.util.spec_from_file_location('tmsr','tests/test_multimodal_sample_review.py'); mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); base=Path('outputs/test-multimodal-sample-run-artifacts').resolve(); shutil.rmtree(base, ignore_errors=True); base.mkdir(parents=True, exist_ok=True); mod.test_multimodal_sample_review_writes_static_ui_and_notes_template(base / 'case1'); mod.test_validate_multimodal_sample_notes_summarizes_human_labels(base / 'case2'); mod.test_task_console_links_multimodal_sample_review(base / 'case3'); print('multimodal_sample_review_run_artifacts_direct_test_ok')"
```

下一步优先级顺延为：继续补剩余真实执行器的 failed_items 质量，或者把 `human_sample_eval` 的状态进一步显示到 `video-workbench` 的 Provider/内容候选之外的“质量抽样”专栏。
