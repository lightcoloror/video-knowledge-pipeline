# 外部开源项目可复用模块总清单

更新记录：

- 2026-07-06 07:51:40 | Codex / GPT-5：基于已拉源码和已落地实现，整理 VKP 当前还能继续从外部项目吸收的代码模块、已基本榨干的部分、下一步落地优先级和不可越过的边界。

## 这份文档解决什么问题

用户问题是：还有哪些值得复用的代码模块？

结论不是“再找一个视频总结项目整体替换 VKP”，而是继续做模块级吸收。VKP 已经形成自己的主架构：本地视频 -> ASR / 字幕 / 抽帧 / ebook-OCR / 多模态复核 / timeline / review / smart-summary / content assets。外部项目的价值主要是把成熟的局部能力拆出来，接进这条流水线。

## 总体判断

| 状态 | 判断 | 下一步 |
| --- | --- | --- |
| 已基本榨干 | vsummary 的 provider/stage/run/citation 思路；BiliNote 的字幕清洗、转写编辑、章节编辑；VideoRAG/VTimeLLM 的本地时间定位；Qwen/InternVL 的图像预处理思路 | 不再整体迁移，只继续小修小补 |
| 还能继续榨 | 工作台过滤与队列、human sample eval 可视化、smart-summary evidence trace、citation 注入最终总结、ASR 后处理、可选本地 VLM smoke | 按 P0/P1 排入实现 |
| 暂不值得榨 | 整套 React/FastAPI 后端、重型向量图数据库、模型仓库源码内嵌、下载后端、默认全帧云多模态 | 只保留 adapter 或只读参考 |

## 已吸收的外部模块和 VKP 对应实现

| 来源项目/方向 | 已复用模块 | VKP 文件或入口 | 复用程度 |
| --- | --- | --- | --- |
| `alpha03123/vsummary` | OpenAI-compatible 文本模型网关、JSON repair、stage cache、run artifact、时间戳 seek/citation、Windows CUDA 检测 | `text_llm_gateway.py`、`stage_cache.py`、`run_artifact_registry.py`、`cuda_runtime.py`、`task_console.py`、`video_workbench.py` | 高 |
| `PrideWood/bilinote` | SRT/VTT/plain transcript 解析、字幕清洗、短句合并、转写校对 prompt、mind-map prompt、转写编辑器、章节编辑体验 | `bilinote_transcript_tools.py`、`bilinote_summary_tools.py`、`transcript_correction_pack.py`、`transcript_editor.py`、`smart_summary_section_editor.py` | 高 |
| VideoRAG | 视频 chunk schema、本地 JSONL 检索、可选 HTTP search service | `video_rag_pack.py`、`video_rag_search.py`、`video_rag_http.py` | 中高 |
| VTimeLLM / moment grounding | 时间段定位、moment index、时间轴错位审计 | `video_moment_index.py`、`timeline_alignment_audit.py` | 中高 |
| MovieChat | short memory / long memory 长视频分层记忆 | `long_video_memory_pack.py` | 中 |
| Qwen-VL / InternVL / LLaVA-OneVision | 图像压缩缩放、多图输入、dynamic tiling、高分辨率 tile 证据包 | `vlm_preprocess.py`、`high_res_tile_plan.py`、`tile_result_import_builder.py`、`tile_result_merge.py` | 中高 |
| FunASR / SenseVoice / WhisperX | 本地中文 ASR、timestamp sidecar、模型 ready gate、后续 word-level/speaker/punctuation 路线 | `funasr_python_runner.py`、`asr_runner.py`、`asr_environment.py`、`transcript_sidecar.py` | 中高 |
| Peepshow / VidClaude | 抽样帧报告、视觉复核、人工质量评估 | `vision_review_queue.py`、`multimodal_sample_review.py`、`task_console.py` | 中 |

## 仍值得继续复用的代码模块

### P0：human sample eval 进入统一工作台

当前状态：`content-candidate-pack` 已进入 `multimodal-sample-review`，`human-sample-eval` 已进入 `content-asset-status`、`batch-content-asset-status`、`content-handoff-pack`。

下一步：

- `video-workbench.html` 的内容素材候选面板显示 human sample eval 状态。
- 支持过滤：全部、未抽样、抽样证据不足、可继续加工。
- 每条 candidate 显示 candidate usable / evidence sufficient 信号。
- 仍保持 review-only：这些信号不能把素材变成可发布，也不能把素材当事实。

复用来源：Peepshow / VidClaude 的抽样评估表，vsummary 的 staged handoff，BiliNote 的同屏审阅。

### P0：smart-summary evidence trace 继续加深

当前状态：已有 `smart-summary-input-pack`、`smart-summary-chapters`、`course-map`、section workflow、Codex rewrite、质量门禁。

下一步：

- 每个章节明确记录：transcript source、timeline indexes、OCR/ebook evidence、visual evidence、temporal evidence、moment chunks、review gaps。
- `smart-summary.codex.md` 和未来在线 LLM provider 共用同一个 input pack。
- 最终 `smart-summary.md` 的观点尽量带 citation/time range，但不要变成证据流水账。

复用来源：MovieChat 的长视频记忆、VideoRAG 的 citation chunk、BiliNote 的 chunk prompt。

### P0：所有长任务接满 run artifact registry

当前状态：ASR、ebook、tile、多模态、temporal、screen text recovery、smart-summary 一部分任务已经进入 `runs/*/run.json`。

下一步：

- 每个长任务都登记状态：preview、needs_execution、running、completed、needs_retry、needs_review、needs_input。
- 工作台显示 batch size、total batches、失败 indexes、retry command、artifact path。
- 失败重试不需要用户复制几十条命令。

复用来源：vsummary 的 stage/task state，BiliNote 的任务面板，Peepshow/VidClaude 的 frame batch report。

### P1：字幕/ASR/平台字幕仲裁后处理

当前状态：`transcript-source-arbitration` 已落地，高置信纠错可以 promoted 到 corrected transcript，低置信进入 review。

下一步：

- 标点恢复。
- 课程术语词典。
- 人名/品牌/工具名纠错。
- 说话人/段落化。
- 工作台里展示不同来源的差异，而不是只看最终合并结果。

复用来源：BiliNote 字幕清洗，WhisperX word-level timestamp / diarization，SenseVoice emotion/event tags。

### P1：视频 RAG 与 citation 注入最终输出

当前状态：已有 `video-rag-pack`、`video-rag-search`、`video-rag-http`、`video-moment-index`。

下一步：

- 让 `smart-summary.md` 的关键观点能回链到 moment chunk。
- 让 content candidate 能回链到对应 transcript/visual evidence。
- 工作台搜索结果点击后跳转视频、timeline row、候选素材。

复用来源：VideoRAG 的 retrieval unit，VTimeLLM 的 time grounding，vsummary 的 seek/citation UI。

### P1：内容素材候选与智能总结互链

当前状态：`content-candidate-pack` 已在 `export-knowledge-note` 时生成，content handoff 已能携带候选包和 sample eval 信号。

下一步：

- 从 smart-summary 章节反向链接到 content candidates。
- 从 content candidates 链接到章节、时间戳、证据帧、review rows。
- 加入素材类型过滤：method、case、quote、visual_explainer、tool、workflow。

复用来源：BiliNote 笔记结构、vsummary 片段资产、VideoRAG evidence path。

### P2：本地 VLM adapter smoke

当前状态：已有 `vlm_preprocess.py`、高分辨率 tile 计划、OpenAI-compatible / HTTP provider 边界。

下一步：

- `local-vlm-serving-smoke` 检查模型服务地址、模型名、单图/多图/帧组能力、显存/设备、JSON 输出稳定性。
- 不把 Qwen/InternVL/LLaVA 模型源码嵌入 VKP。
- 只作为 provider adapter 接入。

复用来源：Qwen-VL OpenAI-compatible serving，InternVL dynamic tiling，LLaVA-OneVision 多图/短片段输入。

## 不建议继续直接复用的模块

| 模块 | 不建议原因 | 替代方案 |
| --- | --- | --- |
| vsummary 整套 FastAPI/React/LlamaIndex/LanceDB | 会形成第二套系统，和 VKP CLI/MCP/OpenClaw/static bundle 冲突 | 只吸收 provider/stage/cache/UI 思路 |
| BiliNote 整套 React UI | UI 好，但 VKP 当前静态 bundle 更适合 agent 调用和本地审核 | 在 `video-workbench.html` 中复刻关键交互 |
| VideoRAG 全量 graph/vector 后端 | 重依赖，维护成本高 | 默认 JSONL/keyword/sqlite，vector optional |
| Qwen/InternVL/LLaVA 模型源码 | 模型环境重，显存和依赖复杂 | provider adapter + preprocess |
| 下载/字幕抓取后端 | VKP 边界是内容理解，不负责下载 | 继续交给 `video-download-orchestrator` |
| 默认全帧云多模态 | 成本、隐私、限流、失败恢复都不适合默认 | 本地抽帧/ebook/OCR/triage 先跑，云多模态只补疑难点或显式全量模式 |

## 后续判断新项目是否值得拉源码

先问五个问题：

1. 它是否提供 VKP 还没有的低耦合模块？
2. 它是否能不引入重依赖单独复用？
3. 它是否改善当前瓶颈：智能总结质量、时间定位、屏幕文字、小字 UI、批次重试、人工评分？
4. 它是否要求替换 VKP 主架构？如果是，默认拒绝，只记录思路。
5. 它是否会绕过下载、云 API、人工复核边界？如果是，不接入主线。

## 当前推荐下一步

优先级最高的是：把 `human-sample-eval` 信号接入 `video-workbench.html` 的内容素材候选面板。原因是这一步直接把“多模态、ebook、ASR 仲裁到底有没有改善最终产物”变成可见、可过滤、可复核的质量信号。

之后再做：

1. smart-summary evidence trace 完善；
2. run artifact registry 全覆盖；
3. citation 注入 smart-summary / content candidates；
4. ASR/字幕仲裁后处理增强；
5. optional local VLM smoke。

## 相关文档

- `docs/external-code-reuse-ledger-2026-07-04.md`
- `docs/external-code-module-reuse-backlog-2026-07-04.md`
- `docs/external-code-reuse-remaining-modules-2026-07-05.md`
- `docs/external-code-reuse-exhaustion-status-2026-07-05.md`
- `docs/external-project-reuse-implementation-2026-07-04.md`
- `docs/vsummary-source-review.md`
- `docs/bilinote-pridewood-source-review.md`
- `docs/ai-video-open-source-survey-2026-07-04.md`
- `docs/smart-summary-best-practices.md`
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
