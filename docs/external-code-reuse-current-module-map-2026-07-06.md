# 外部开源项目模块复用当前地图

更新记录：

- 2026-07-06 08:31:45 | Codex / GPT-5：把已审查外部项目、已吸收模块、仍值得继续复用的代码模块、暂不建议投入的方向整理成当前开发导航页。

## 这份文档的定位

这不是新的源码审查报告，而是 VKP 继续“榨干外部项目”的当前地图。

细节来源仍然看：

- `docs/vsummary-source-review.md`
- `docs/bilinote-pridewood-source-review.md`
- `docs/ai-video-open-source-survey-2026-07-04.md`
- `docs/external-open-source-reuse-module-inventory-2026-07-06.md`
- `docs/external-code-module-reuse-backlog-2026-07-04.md`
- `docs/external-code-reuse-exhaustion-status-2026-07-05.md`

本文只回答三个问题：

1. 哪些外部能力已经被 VKP 吸收？
2. 还有哪些代码模块值得继续复用？
3. 哪些方向看起来诱人，但不该继续搬？

## 当前结论

VKP 现在不需要再整体迁移一个视频总结项目。更好的路径是继续吸收低耦合模块，把它们接进现有主线：

```text
本地视频
  -> ASR/平台字幕/字幕仲裁
  -> 抽帧/ebook-OCR/屏幕文字恢复
  -> 疑难点 triage/多模态复核
  -> timeline/evidence/review
  -> smart-summary/full-transcript/knowledge-note/content-candidate
  -> workbench/sample-review/content handoff
```

外部项目的价值主要集中在这些局部能力：

- 任务状态、stage cache、run artifact、重试命令；
- 字幕清洗、转写校对、章节编辑；
- 长视频分层记忆、时间定位、citation chunk；
- 本地/云端 VLM 输入预处理；
- 人工抽样评估、内容素材候选筛选。

## 已吸收模块

| 外部来源 | 已吸收模块 | VKP 当前落地 |
| --- | --- | --- |
| vsummary | provider gateway、JSON repair、stage cache、run artifact、timestamp/citation UI | `text_llm_gateway.py`、`stage_cache.py`、`run_artifact_registry.py`、`task_console.py`、`video_workbench.py` |
| PrideWood/BiliNote | 字幕解析清洗、短句合并、转写校对 prompt、章节编辑体验 | `bilinote_transcript_tools.py`、`bilinote_summary_tools.py`、`transcript_correction_pack.py`、`transcript_editor.py`、`smart_summary_section_editor.py` |
| VideoRAG | video chunk、JSONL/SQLite 检索、citation 思路 | `video_rag_pack.py`、`video_rag_search.py`、`video_rag_http.py`、`smart_summary_chapters.py` |
| VTimeLLM | 时间定位、moment grounding、alignment audit | `video_moment_index.py`、`timeline_alignment_audit.py` |
| MovieChat | 长视频 short memory / long memory 分层 | `long_video_memory_pack.py`、`smart_summary_input_pack.py` |
| Qwen-VL / InternVL / LLaVA-OneVision | 单图/多图预处理、dynamic tiling、高分辨率 tile recovery | `vlm_preprocess.py`、`high_res_tile_plan.py`、`tile_result_import_builder.py`、`tile_result_merge.py` |
| FunASR / SenseVoice / WhisperX | 本地 ASR、timestamp sidecar、模型 ready gate、后续 word-level/speaker/punctuation 路线 | `funasr_python_runner.py`、`asr_runner.py`、`asr_environment.py`、`transcript_sidecar.py` |
| Peepshow / VidClaude | 帧证据卡、质量抽样、人审评分 | `vision_review_queue.py`、`multimodal_sample_review.py`、`video_workbench.py` |

## 最近已完成的复用推进

### Citation Digest 闭环

VideoRAG / VTimeLLM / MovieChat 的证据追踪思路已经进入 VKP 的核心输出链：

- `build-smart-summary-chapters` 生成章节级 `citation_digest`。
- `generate-smart-summary-with-codex` 把 citation digest 注入最终 `smart-summary.codex.md` / `smart-summary.md`。
- `export-knowledge-note` 生成 `content-candidate-pack` 时绑定 candidate 的 `evidence_citations`。
- `video-workbench.html` 显示 candidate citation 数、citation 摘要和有无 citation 过滤。
- `multimodal-sample-review.html` 显示内容素材候选的 citation summary、source/time/timeline/text/evidence path。

当前这条链路的意义是：智能总结、内容素材候选、人审抽样不再只是“看起来像总结”，而是能回到时间戳、帧、OCR/ebook、多模态和 review gap 证据。

### Human sample eval 进入工作台

Peepshow / VidClaude 的抽样评估思路已经接入 `video-workbench` 和内容素材交接：

- 工作台能显示内容素材候选可用率、证据充分率、抽样状态。
- 支持过滤：未抽样、证据不足、可继续加工、有 Citation、缺 Citation。
- `content-asset-status` / `batch-content-asset-status` / `content-handoff-pack` 会携带 human sample eval 信号。

这些信号仍然只是 review-only，不能自动批准发布，也不能自动把素材当事实。

## 仍值得继续复用的模块

| 优先级 | 模块 | 参考来源 | 应落地成什么 | 当前判断 |
| --- | --- | --- | --- | --- |
| P0 | run artifact registry 全覆盖 | vsummary stage/task state、BiliNote 任务面板 | 所有长任务都有 run.json、状态、失败 indexes、retry command、artifact path | 最值得继续做，能减少手工复制命令 |
| P0 | provider/VLM 状态进入 workbench | Qwen/InternVL serving、vsummary provider status | 工作台显示本地 VLM / cloud provider smoke 状态和边界，不启动服务、不调用云 | 下一步可做 |
| P1 | smart-summary section 级引用和质量门禁继续增强 | VideoRAG citation、BiliNote 章节编辑 | 每个章节可追踪输入证据、修改状态、质量问题、复写来源 | 已有基础，还能继续提高总结质量 |
| P1 | ASR/字幕仲裁后处理 | BiliNote、WhisperX、SenseVoice | 标点恢复、术语词典、人名/品牌/工具名纠错、说话人/段落化 | 直接影响最终可读性 |
| P1 | 视频 RAG 与工作台搜索联动 | VideoRAG、VTimeLLM | 搜索结果点击跳视频、timeline row、候选素材、citation | 已有本地搜索，可继续打通 UI |
| P1 | 内容素材候选与智能总结双向链接 | BiliNote 笔记结构、vsummary 片段资产 | 从章节跳素材，从素材跳章节/证据/复核项 | 已完成部分 citation，下步是更自然的双向导航 |
| P2 | local VLM serving smoke | Qwen-VL、InternVL、LLaVA-OneVision | 只读检查模型服务、单图/多图/帧组能力、JSON 稳定性 | 可做，但不应该成为默认依赖 |
| P2 | 高分辨率 tile recovery 改进 | InternVL dynamic tiling、Qwen-VL crop/resize | 小字/表格/代码帧局部 tile 恢复和 merge | 对屏幕小字有价值，但需要继续和 ebook/crop/OCR 分工 |

## 不建议继续投入的方向

| 方向 | 为什么不建议 | VKP 应保持的替代方案 |
| --- | --- | --- |
| 整体搬 vsummary FastAPI/React/LlamaIndex/LanceDB | 会形成第二套后端、第二套 UI、第二套索引，和 VKP CLI/MCP/OpenClaw/static bundle 冲突 | 只吸收 provider、stage、run、citation、UI 交互模式 |
| 整体搬 BiliNote React UI | UI 工作流有参考价值，但 VKP 已有静态 review/workbench，更适合本地 agent 和文件产物 | 在 `video-workbench.html` 复刻关键交互 |
| 默认引入 VideoRAG 重型向量/图数据库 | 维护成本高，个人工具不该默认绑重服务 | 默认 JSONL/keyword/SQLite，vector 只作为显式可选 |
| 把 Qwen/InternVL/LLaVA 模型源码嵌进主流程 | 显存、依赖、模型部署成本高，容易拖垮 VKP 主线 | 统一 provider adapter / OpenAI-compatible / HTTP serving |
| 在 VKP 重做下载/字幕抓取/登录态 | VKP 边界是内容理解，不是下载调度 | 继续复用 `video-download-orchestrator` 和外部 handoff |
| 默认全帧云多模态 | 成本、隐私、限流、失败恢复都不适合作为默认 | 本地抽帧/ebook/OCR/triage 先跑，云多模态只用于疑难点或显式全量模式 |

## 下一步开发建议

如果继续实现，顺序建议是：

1. **run artifact registry 全覆盖**：先让长任务可追踪、可重试、可在 UI 看进度。
2. **provider/VLM 状态进入 workbench**：把本地 VLM / cloud provider smoke 结果显示在工作台，不启动服务。
3. **ASR/字幕后处理增强**：术语、标点、段落化会直接提高 `full-transcript.md` 和 `smart-summary.md`。
4. **视频 RAG 搜索结果与工作台跳转打通**：让“搜索到片段”真正能跳回视频和证据。
5. **高分辨率 tile recovery 与 ebook/crop/OCR 分工再细化**：重点补屏幕小字、表格、代码、课件截图。

判断标准很简单：能直接增强 VKP 的证据链、质量检查、人工审核效率、最终可读文件，就继续复用；如果只是“另一个完整 App 很漂亮”，不搬整体。
## Update: 2026-07-06 08:42:42 | Codex / GPT-5

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
## Update: 2026-07-06 15:45:00 | Codex / GPT-5

### 已落地：ASR / 字幕仲裁质量信号进入 smart-summary 输入包

承接 BiliNote 字幕清洗、WhisperX 时间戳/后处理、SenseVoice 元数据复用方向，本轮把 `transcript-source-arbitration` 从“生成纠正版字幕”推进到“输出可被总结层使用的质量信号”：

- `source-arbitrated-transcript.json` 新增 `quality_summary`。
- `transcript-source-arbitration.json/md` 展示 Arbitration Quality，包括 quality status、平均置信度、高置信术语替换数、低置信冲突数、是否可作为 smart-summary 输入。
- `manifest.json` 写入 `transcript_source_arbitration_quality`，方便后续工具不重复解析报告。
- `smart-summary-input-pack.json/md` 新增 `transcript_arbitration` 区块，读取仲裁报告或 manifest 中的质量摘要。
- `quality_notes` 会区分：未运行仲裁、仍有低置信冲突、已完成高置信术语替换三种状态。

代码落地：

- `src/video_knowledge_pipeline/transcript_source_arbitration.py`
- `src/video_knowledge_pipeline/smart_summary_input_pack.py`
- `tests/test_transcript_source_arbitration.py`
- `tests/test_knowledge_export.py`

验证：

```powershell
python -m py_compile src\video_knowledge_pipeline\transcript_source_arbitration.py src\video_knowledge_pipeline\smart_summary_input_pack.py tests\test_transcript_source_arbitration.py tests\test_knowledge_export.py
$env:PYTHONPATH='src'; python -c "import importlib.util; spec=importlib.util.spec_from_file_location('tta','tests/test_transcript_source_arbitration.py'); mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); mod.test_transcript_source_arbitration_promotes_high_confidence_terms(); print('transcript_arbitration_quality_direct_test_ok')"
$env:PYTHONPATH='src'; python -c "import importlib.util; from pathlib import Path; import shutil; spec=importlib.util.spec_from_file_location('tk','tests/test_knowledge_export.py'); mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); base=Path('outputs/test-smart-summary-input-arbitration-quality').resolve(); shutil.rmtree(base, ignore_errors=True); base.mkdir(parents=True, exist_ok=True); mod.test_smart_summary_input_pack_fuses_terms_punctuation_and_visual_evidence(base); print('smart_summary_input_arbitration_quality_direct_test_ok')"
```

下一步：把同一套 transcript arbitration quality 摘要显示到 `video-workbench.html` 的转写/质量区域，或者继续推进 high-res tile recovery 与 ebook/OCR 的失败分流。
## Update: 2026-07-06 15:58:00 | Codex / GPT-5

### 已落地：字幕/ASR 仲裁质量信号进入 video-workbench

承接上一轮 `transcript-source-arbitration quality_summary`，本轮把同一份质量摘要显示到统一视频工作台：

- `export-video-workbench` 的 `transcript_arbitration` payload 新增 `quality_summary`。
- 字幕仲裁面板显示：低置信冲突数、已改写片段数、高置信术语数、仲裁质量状态、平均置信度。
- 原有 review rows / changed rows / 点击定位逻辑保持不变。
- 这一步只读展示已有报告，不重新仲裁、不修改 transcript、不调用 LLM。

代码落地：

- `src/video_knowledge_pipeline/video_workbench.py`
- `tests/test_video_workbench.py`

验证：

```powershell
python -m py_compile src\video_knowledge_pipeline\video_workbench.py tests\test_video_workbench.py
$env:PYTHONPATH='src'; python -c "import importlib.util; spec=importlib.util.spec_from_file_location('tvw','tests/test_video_workbench.py'); mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); mod.test_export_video_workbench_writes_static_workspace(); print('video_workbench_transcript_arbitration_quality_direct_test_ok')"
```

下一步：继续沿 backlog 推进 high-res tile recovery 与 ebook/OCR 失败分流，或者把 run artifact registry 剩余长任务状态再补齐。
## Update: 2026-07-06 16:18:00 | Codex / GPT-5

### 已落地：ebook/OCR 低质结果进入 high-res tile recovery 分流

承接 InternVL dynamic tiling、Qwen-VL 图像预处理和 ebook_markdown_pipeline 图文解析分工，本轮把 whole-frame ebook/OCR 的低质结果接到本地 high-res tile 证据链：

- `frame_recapture._quality_issues` 对 `ocr_wrapper_only`、`ocr_text_empty`、`ocr_text_low_information` 额外标记 `needs_high_res_tile_recovery`。
- `run-visual-structure` 的 run failed_items 对可 tile 恢复的 ebook blocker 写入：
  - `suggested_next_tool=high_res_tile_plan`
  - `suggested_retry_command=... high-res-tile-plan --indexes <index> --execute-tiles`
  - `suggested_next_reason`
- `high-res-tile-plan` 现在读取 timeline item 顶层 `ebook_pipeline_status`，不再只读 `structured_visual.ebook_pipeline_status`。
- tile plan item 会携带 compact `ebook_pipeline_status`，并把 `needs_high_res_tile_recovery` 放入 reasons。
- 这一步仍然只做本地 tile 证据准备，不运行 OCR/VLM，不调用云，不把低质 OCR 当成功。

代码落地：

- `src/video_knowledge_pipeline/frame_recapture.py`
- `src/video_knowledge_pipeline/visual_structure.py`
- `src/video_knowledge_pipeline/high_res_tile_plan.py`
- `tests/test_screen_text_recovery.py`

验证：

```powershell
python -m py_compile src\video_knowledge_pipeline\frame_recapture.py src\video_knowledge_pipeline\visual_structure.py src\video_knowledge_pipeline\high_res_tile_plan.py tests\test_screen_text_recovery.py
$env:PYTHONPATH='src'; python -c "import importlib.util; from pathlib import Path; import shutil; import pytest; spec=importlib.util.spec_from_file_location('tstr','tests/test_screen_text_recovery.py'); mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); base=Path('outputs/test-ebook-to-tile-recovery').resolve(); shutil.rmtree(base, ignore_errors=True); base.mkdir(parents=True, exist_ok=True); monkey=pytest.MonkeyPatch(); mod.test_visual_structure_rejects_synthetic_ebook_wrapper(monkey, base); monkey.undo(); print('ebook_to_high_res_tile_recovery_direct_test_ok')"
```

下一步：把 `needs_high_res_tile_recovery` / high-res tile failed_items 显示到 `task-console.html` 或 `video-workbench.html` 的队列筛选里，让人能直接从 UI 看到“ebook 低质 -> tile 计划/执行/导入”的接力状态。
## Update: 2026-07-06 16:28:00 | Codex / GPT-5

### 已落地：high-res tile recovery 信号进入 video-workbench 筛选

承接 ebook/OCR 低质结果到 high-res tile recovery 的分流，本轮把 `needs_high_res_tile_recovery` 变成工作台可见的证据标记：

- `video-workbench` timeline row 的 `evidence_flags` 会包含 `needs_high_res_tile_recovery`。
- 证据状态面板的 tile issue 统计会把 `needs_high_res_tile_recovery` 计入待处理项。
- 证据状态工具栏新增“筛高分辨率Tile”，并保留“筛 Tile 结果”。
- 这一步只读展示已有 quality issue，不执行 tile、不运行 OCR/VLM、不调用云。

代码落地：

- `src/video_knowledge_pipeline/video_workbench.py`
- `tests/test_video_workbench.py`

验证：

```powershell
python -m py_compile src\video_knowledge_pipeline\video_workbench.py tests\test_video_workbench.py
$env:PYTHONPATH='src'; python -c "import importlib.util; spec=importlib.util.spec_from_file_location('tvw','tests/test_video_workbench.py'); mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); mod.test_export_video_workbench_writes_static_workspace(); print('video_workbench_high_res_tile_filter_direct_test_ok')"
```

下一步：继续把 tile recovery 的 run artifacts 和 tile-result-merge 质量信号更自然地接进 smart-summary evidence trace / content candidates，或者继续补剩余长任务的 run registry 覆盖。
## Update: 2026-07-06 09:24:25 | Codex / GPT-5

### 已落地：high-res tile 证据进入 smart-summary 与内容候选

承接 `tile-result-merge` 和 high-res tile recovery，本轮把成功合并的 tile 证据从“复核工具内部状态”推进到最终人类可读输出的证据层：

- `smart-summary-input-pack` 的 `evidence_trace` 新增 `tile_items`，并统计 `summary.high_res_tile_items`。
- `timeline` 中 `tile_result_merges[action=merge]` 会被识别为 `has_high_res_tile`，并保留 tile evidence path。
- `smart-summary-chapters` 的章节 evidence trace / citation digest 新增 `source_type=high_res_tile`。
- `content-candidate-pack.json` 会继承 `high_res_tile` citation 和 tile evidence path，让内容素材候选能追溯到局部高清截图证据。
- `tile_review_targets` 和 tile merge evidence path 都会进入 evidence path 汇总，避免主笔记只有文字没有证据。
- 这一步不运行 OCR/VLM、不调用云，只把已经导入/合并的本地 tile 结果正确传播到 summary/candidate 输出。

代码落地：

- `src/video_knowledge_pipeline/smart_summary_input_pack.py`
- `src/video_knowledge_pipeline/smart_summary_chapters.py`
- `tests/test_knowledge_export.py`

验证：

```powershell
python -m py_compile src\video_knowledge_pipeline\smart_summary_input_pack.py src\video_knowledge_pipeline\smart_summary_chapters.py tests\test_knowledge_export.py
$env:PYTHONPATH='src'; python -c "import importlib.util; from pathlib import Path; import shutil; spec=importlib.util.spec_from_file_location('tk','tests/test_knowledge_export.py'); mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); base=Path('outputs/test-smart-summary-tile-evidence').resolve(); shutil.rmtree(base, ignore_errors=True); base.mkdir(parents=True, exist_ok=True); mod.test_smart_summary_input_pack_fuses_terms_punctuation_and_visual_evidence(base); print('smart_summary_tile_evidence_direct_test_ok')"
```

下一步：继续把外部项目复用链路里剩余的可吸收模块落实到“可见状态 + 可执行队列 + 最终导出影响”，优先考虑 run artifact registry 对长任务状态的统一展示，或把 tile import/merge 的批量失败重试做进任务控制台。

## Update: 2026-07-06 09:29:47 | Codex / GPT-5

### P0/P1 continued: tile pending results enter retry queue

承接 vsummary task status / BiliNote task panel 的复用方向，本轮把 high-res tile 结果导入链路里的 pending tile 从“报告里的统计数字”推进到可操作任务队列：

- `tile-result-import-build` 现在会把没有找到 `.json/.txt/.md` 输出文件的 tile 写入 run `failed_items`。
- 只要存在 `pending_results`，对应 run 状态为 `needs_input`，不再把“部分匹配、部分缺失”的导入任务标成 completed。
- failed item 会保留 `timeline index`、`tile_id`、`tile_path` 和下一步提示，task console 的 `document_ocr` 队列能直接显示这些 pending tile。
- task console 可显示并复制 `tile-result-import-build` 的 retry command，避免人工在报告和命令之间来回翻。
- 这一步仍是本地 glue/UI 改进，不运行 OCR/VLM，不调用云，也不把 pending tile 当成成功证据。

代码落地：

- `src/video_knowledge_pipeline/tile_result_import_builder.py`
- `tests/test_tile_result_import_builder.py`
- `tests/test_task_console.py`

验证：

```powershell
python -m py_compile src\video_knowledge_pipeline\tile_result_import_builder.py src\video_knowledge_pipeline\task_console.py tests\test_tile_result_import_builder.py tests\test_task_console.py
$env:PYTHONPATH='src'; python -c "import importlib.util; from pathlib import Path; import shutil; spec=importlib.util.spec_from_file_location('ttile','tests/test_tile_result_import_builder.py'); mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); base=Path('outputs/test-tile-result-import-pending').resolve(); shutil.rmtree(base, ignore_errors=True); base.mkdir(parents=True, exist_ok=True); mod.test_tile_result_import_build_consumes_common_ocr_and_vlm_shapes(base); print('tile_result_import_pending_direct_test_ok')"
$env:PYTHONPATH='src'; python -c "import importlib.util; from pathlib import Path; import shutil; spec=importlib.util.spec_from_file_location('ttask','tests/test_task_console.py'); mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); base=Path('outputs/test-task-console-tile-pending').resolve(); shutil.rmtree(base, ignore_errors=True); base.mkdir(parents=True, exist_ok=True); mod.test_export_task_console_writes_human_ui_and_agent_json(base); print('task_console_tile_pending_direct_test_ok')"
```

下一步优先级顺延为：继续把更多长任务的 run artifacts 补到 `failed_items / retry_command / next_actions`，或者把 task console 的 `document_ocr` 队列进一步拆成 ebook、screen-text crop、high-res tile 三个子队列。

## Update: 2026-07-06 09:35:08 | Codex / GPT-5

### P0 continued: document OCR queue split into ebook / crop / high-res tile subqueues

承接 vsummary task status、BiliNote task panel 和 Peepshow frame report 的复用方向，本轮把 task console 里的 `document_ocr` 大队列拆成可读的子队列，减少长视频处理时“所有 OCR 问题都挤在一张卡里”的操作成本：

- `processing_queue.groups[document_ocr]` 新增 `subqueues`。
- 子队列固定为：
  - `ebook`：整帧图文 / visual-structure / ebook_markdown_pipeline。
  - `screen_text_crop`：screen-text recovery、crop 和轻量 OCR 补救。
  - `high_res_tile`：high-res tile plan、tile result import、tile merge、pending tile。
  - `other_document_ocr`：未能细分的 OCR run。
- 每个子队列都有独立的 `run_count`、`action_required`、`failed_count`、`failed_items_preview`、`retry_commands`、`next_actions`。
- `task-console.html` 的 OCR 队列卡片会显示子队列、小型失败项预览和子队列重试命令。
- 这一步只整理已有 run registry 状态，不执行 OCR、ebook、VLM 或云 API。

代码落地：

- `src/video_knowledge_pipeline/task_console.py`
- `tests/test_task_console.py`

验证：

```powershell
python -m py_compile src\video_knowledge_pipeline\task_console.py tests\test_task_console.py
$env:PYTHONPATH='src'; python -c "import importlib.util; from pathlib import Path; import shutil; spec=importlib.util.spec_from_file_location('ttask','tests/test_task_console.py'); mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); base=Path('outputs/test-task-console-ocr-subqueues').resolve(); shutil.rmtree(base, ignore_errors=True); base.mkdir(parents=True, exist_ok=True); mod.test_export_task_console_writes_human_ui_and_agent_json(base); print('task_console_ocr_subqueues_direct_test_ok')"
```

下一步优先级顺延为：继续把其他大队列拆成同样可操作的子队列，优先是 `vision` 队列里的 semantic / temporal / provider smoke / local VLM smoke，或者继续补更多长任务的 `failed_items / retry_command / next_actions`。

## Update: 2026-07-06 09:39:57 | Codex / GPT-5

### P0 continued: vision queue split into triage / semantic / temporal / provider / local VLM subqueues

承接 vsummary task status、BiliNote task panel 和 provider status 面板的复用方向，本轮把 task console 里的 `vision` 大队列拆成可操作子队列，避免疑难点、多模态单帧、连续片段、provider smoke 和本地 VLM smoke 混在一起：

- `processing_queue.groups[vision]` 新增 `subqueues`。
- 子队列固定为：
  - `review_triage`：vision review triage、候选帧/片段队列。
  - `semantic_frame`：单帧多模态、semantic frame、visual understanding。
  - `temporal_sequence`：连续片段、多帧 frame group、temporal visual。
  - `provider_smoke`：vision provider smoke、provider matrix、preflight。
  - `local_vlm`：本地 VLM serving smoke、本地 Qwen/InternVL/LLaVA adapter 状态。
  - `other_vision`：未能细分的视觉 run。
- 每个子队列都有独立的 `run_count`、`action_required`、`failed_count`、`failed_items_preview`、`retry_commands`、`next_actions`。
- `task-console.html` 会在 vision 卡片里显示“视觉子队列”和各子队列的重试命令。
- 这一步只整理已有 run registry 状态，不执行多模态、不启动本地 VLM、不调用云 API。

代码落地：

- `src/video_knowledge_pipeline/task_console.py`
- `tests/test_task_console.py`

验证：

```powershell
python -m py_compile src\video_knowledge_pipeline\task_console.py tests\test_task_console.py
$env:PYTHONPATH='src'; python -c "import importlib.util; from pathlib import Path; import shutil; spec=importlib.util.spec_from_file_location('ttask','tests/test_task_console.py'); mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); base=Path('outputs/test-task-console-vision-subqueues').resolve(); shutil.rmtree(base, ignore_errors=True); base.mkdir(parents=True, exist_ok=True); mod.test_processing_queue_groups_external_reuse_run_types(); mod.test_export_task_console_writes_human_ui_and_agent_json(base); print('task_console_vision_subqueues_direct_test_ok')"
```

下一步优先级顺延为：继续把 `summary_export` 队列拆成 smart-summary input / chapter workflow / section apply / content candidate，或者把更多长任务补齐 `failed_items / retry_command / next_actions`。

## Update: 2026-07-06 09:43:47 | Codex / GPT-5

### P0 continued: summary/export queue split into input / workflow / apply / export / content subqueues

承接 vsummary staged generation、BiliNote section editing 和 VKP content candidate handoff 的复用方向，本轮把 task console 里的 `summary_export` 大队列拆成可操作子队列，让智能总结和内容素材导出链路能看到“卡在输入包、章节工作流、章节导入、知识导出还是内容候选”：

- `processing_queue.groups[summary_export]` 新增 `subqueues`。
- 子队列固定为：
  - `summary_input`：smart-summary input pack、chapter pack、long-video memory、course map。
  - `section_workflow`：smart-summary section workflow、section editor、章节修订 TODO。
  - `section_apply`：section apply、Codex 改写结果安装、质量门禁。
  - `knowledge_export`：knowledge-note、full-transcript、smart-summary、extraction audit 导出。
  - `content_candidate`：content candidate pack、content material card、external capability pack、handoff。
  - `other_summary_export`：未能细分的 summary/export run。
- 每个子队列都有独立的 `run_count`、`action_required`、`failed_count`、`failed_items_preview`、`retry_commands`、`next_actions`。
- `task-console.html` 会在 summary/export 卡片中显示“总结/导出子队列”和各子队列重试命令。
- 这一步只整理已有 run registry 状态，不调用 LLM、不生成新总结、不自动发布内容素材。

代码落地：

- `src/video_knowledge_pipeline/task_console.py`
- `tests/test_task_console.py`

验证：

```powershell
python -m py_compile src\video_knowledge_pipeline\task_console.py tests\test_task_console.py
$env:PYTHONPATH='src'; python -c "import importlib.util; from pathlib import Path; import shutil; spec=importlib.util.spec_from_file_location('ttask','tests/test_task_console.py'); mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); base=Path('outputs/test-task-console-summary-subqueues').resolve(); shutil.rmtree(base, ignore_errors=True); base.mkdir(parents=True, exist_ok=True); mod.test_processing_queue_groups_external_reuse_run_types(); mod.test_export_task_console_writes_human_ui_and_agent_json(base); print('task_console_summary_subqueues_direct_test_ok')"
```

下一步优先级顺延为：继续把 `review` 队列拆成 review pack / transcript arbitration / sample eval / closure status，或者把更多长任务补齐 `failed_items / retry_command / next_actions`。
## Update: 2026-07-06 09:56:29 | Codex / GPT-5

### P0 continued: review queue split into pack / arbitration / sample / closure / import subqueues

承接 BiliNote task panel、Peepshow frame review 和 VKP review pack 的复用方向，本轮把 task console 里的 `review` 大队列拆成可操作子队列，让人工审核相关 run 不再混成一团：

- `processing_queue.groups[review]` 新增 `subqueues`。
- 子队列固定为：
  - `review_pack`：prepare-review-session、review pack、review notes 校验和导入准备。
  - `transcript_arbitration`：字幕/ASR 来源仲裁、低置信冲突和人工确认。
  - `sample_eval`：multimodal sample review、human sample eval、impact report。
  - `closure_status`：review closure status、open/closed 进度和关闭审计。
  - `manual_import`：human review import、人工修正写回和安全导入。
  - `other_review`：未能细分的审核 run。
- 每个子队列都有独立的 `run_count`、`action_required`、`failed_count`、`failed_items_preview`、`retry_commands`、`next_actions`。
- `task-console.html` 会在 review 卡片中显示“审核子队列”和各子队列重试命令。
- 这一步只整理已有 run registry 状态，不自动关闭人工审核、不绕过 `review-notes.json -> validate -> apply`，也不执行云 API 或写回知识库。

代码落地：

- `src/video_knowledge_pipeline/task_console.py`
- `tests/test_task_console.py`

验证：

```powershell
python -m py_compile src\video_knowledge_pipeline\task_console.py tests\test_task_console.py
$env:PYTHONPATH='src'; python -c "import importlib.util; from pathlib import Path; import shutil; spec=importlib.util.spec_from_file_location('ttask','tests/test_task_console.py'); mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); base=Path('outputs/test-task-console-review-subqueues').resolve(); shutil.rmtree(base, ignore_errors=True); base.mkdir(parents=True, exist_ok=True); mod.test_processing_queue_groups_external_reuse_run_types(); mod.test_export_task_console_writes_human_ui_and_agent_json(base); print('task_console_review_subqueues_direct_test_ok')"
```

下一步优先级顺延为：把 `asr_transcript` 或 `timeline_rag` 队列继续拆成同级子队列，或者把更多长任务补齐 `failed_items / retry_command / next_actions`，让控制台能成为真正的批处理操作台。
## Update: 2026-07-06 10:03:37 | Codex / GPT-5

### P0 continued: ASR/transcript queue split into local ASR / env / subtitle / arbitration / correction / editor subqueues

承接 AI-Video-Transcriber 参数面板、BiliNote 字幕/转写工作流和 vsummary task status 的复用方向，本轮把 task console 里的 `asr_transcript` 大队列拆成可操作子队列，让长视频转写链路能区分“模型没准备好、字幕没导入、来源冲突、术语纠错、人工编辑”这些不同问题：

- `processing_queue.groups[asr_transcript]` 新增 `subqueues`。
- 子队列固定为：
  - `local_asr`：FunASR/SenseVoice、faster-whisper、WhisperX、本地 ASR runner 和 normalized transcript 落盘。
  - `asr_env`：asr-env-status、模型缓存、CUDA/GPU、ffmpeg 和本地 ASR 环境门禁。
  - `subtitle_import`：平台字幕、自带字幕、caption/subtitle sidecar 导入。
  - `source_arbitration`：ASR、自带字幕、网页简介和其他 transcript source 的冲突仲裁。
  - `transcript_correction`：术语词典、错词修正、corrected transcript 和 correction pack。
  - `transcript_editor`：transcript editor、编辑会话、人工改稿和 apply transcript edits。
  - `other_asr_transcript`：未能细分的转写 run。
- 每个子队列都有独立的 `run_count`、`action_required`、`failed_count`、`failed_items_preview`、`retry_commands`、`next_actions`。
- `task-console.html` 会在 ASR 卡片中显示“ASR 子队列”和各子队列重试命令。
- 修正了一个队列可见性问题：`processing_queue` 现在基于全量 run registry 构建，不再被 `run_registry.runs[:20]` 预览截断；HTML 任务历史仍然可以自己限制展示数量。
- 这一步只整理已有 run registry 状态，不执行 ASR、不下载模型、不调用云 API，也不自动改写最终逐字稿。

代码落地：

- `src/video_knowledge_pipeline/task_console.py`
- `tests/test_task_console.py`

验证：

```powershell
python -m py_compile src\video_knowledge_pipeline\task_console.py tests\test_task_console.py
$env:PYTHONPATH='src'; python -c "import importlib.util; from pathlib import Path; import shutil; spec=importlib.util.spec_from_file_location('ttask','tests/test_task_console.py'); mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); base=Path('outputs/test-task-console-asr-subqueues').resolve(); shutil.rmtree(base, ignore_errors=True); base.mkdir(parents=True, exist_ok=True); mod.test_processing_queue_groups_external_reuse_run_types(); mod.test_export_task_console_writes_human_ui_and_agent_json(base); print('task_console_asr_subqueues_direct_test_ok')"
```

下一步优先级顺延为：把 `timeline_rag` 队列拆成 timeline alignment / moment index / VideoRAG / long-video memory / recapture 子队列，或者继续补更多 run artifact 的 `failed_items / retry_command / next_actions`。
## Update: 2026-07-06 10:06:40 | Codex / GPT-5

### P0 continued: timeline/RAG queue split into alignment / moment / VideoRAG / memory / recapture subqueues

承接 Peepshow frame report、vsummary task status 和 VideoRAG 类项目的复用方向，本轮把 task console 里的 `timeline_rag` 大队列拆成可操作子队列，让长视频处理时能区分“时间轴错位、片段索引、RAG 检索、长视频 memory、补帧/重采样”这些不同问题：

- `processing_queue.groups[timeline_rag]` 新增 `subqueues`。
- 子队列固定为：
  - `timeline_alignment`：timeline alignment audit、ASR/抽帧/打标时间错位和时间戳修正。
  - `moment_index`：video moment index、片段搜索和可跳转时间点索引。
  - `video_rag`：video-rag pack、search、HTTP service plan 和本地视频检索入口。
  - `long_video_memory`：long-video memory pack、分层课程记忆和跨段上下文索引。
  - `recapture`：frame recapture、supplemental frame sampling 和疑难片段补帧。
  - `other_timeline_rag`：未能细分的 timeline/RAG run。
- 每个子队列都有独立的 `run_count`、`action_required`、`failed_count`、`failed_items_preview`、`retry_commands`、`next_actions`。
- `task-console.html` 会在 timeline/RAG 卡片中显示“时间轴/RAG 子队列”和各子队列重试命令。
- 这一步只整理已有 run registry 状态，不启动 VideoRAG 服务、不重建索引、不执行补帧，也不处理真实视频。

代码落地：

- `src/video_knowledge_pipeline/task_console.py`
- `tests/test_task_console.py`

验证：

```powershell
python -m py_compile src\video_knowledge_pipeline\task_console.py tests\test_task_console.py
$env:PYTHONPATH='src'; python -c "import importlib.util; from pathlib import Path; import shutil; spec=importlib.util.spec_from_file_location('ttask','tests/test_task_console.py'); mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); base=Path('outputs/test-task-console-timeline-subqueues').resolve(); shutil.rmtree(base, ignore_errors=True); base.mkdir(parents=True, exist_ok=True); mod.test_processing_queue_groups_external_reuse_run_types(); mod.test_export_task_console_writes_human_ui_and_agent_json(base); print('task_console_timeline_subqueues_direct_test_ok')"
```

下一步优先级顺延为：继续把 run artifact 的 `failed_items / retry_command / next_actions` 补到更多真实执行器，或者开始把这些子队列接到任务控制台 UI 的批量筛选/重试按钮。
## Update: 2026-07-06 10:14:30 | Codex / GPT-5

### P0 continued: task console subqueue action panel and copyable command bundles

承接 vsummary task status、BiliNote 参数/任务面板和 Peepshow frame review 的 UI 复用方向，本轮把前面已经拆出来的子队列接成一个真正可操作的“子队列行动面板”：

- `task-console.json` 新增 `subqueue_action_plan`，从 `processing_queue.groups[*].subqueues` 汇总所有非空子队列。
- 每条 action row 保留：
  - `group_key` / `group_label`
  - `subqueue_key` / `label`
  - `status`、`run_count`、`action_required`、`failed_count`
  - `retry_commands` 和 `command_bundle`
  - `failed_items_preview`、`next_actions`
- `task-console.html` 的处理队列上方新增“子队列行动面板”：
  - 显示每个需要关注的子队列。
  - 支持“只看这个子队列”筛选。
  - 支持复制该子队列的命令包。
  - 支持“显示全部”恢复视图。
- 子队列 DOM 增加 `data-subqueue-full-key`，让前端筛选能定位到具体子队列，例如 `asr_transcript:local_asr`、`timeline_rag:video_rag`。
- 这一步仍然只做 UI/JSON 调度层，不执行命令、不启动服务、不下载模型、不调用云 API。它的作用是把已复用/已整合的外部项目能力变成可被人和 agent 一眼操作的队列面板。

代码落地：

- `src/video_knowledge_pipeline/task_console.py`
- `tests/test_task_console.py`

验证：

```powershell
python -m py_compile src\video_knowledge_pipeline\task_console.py tests\test_task_console.py
$env:PYTHONPATH='src'; python -c "import importlib.util; from pathlib import Path; import shutil; spec=importlib.util.spec_from_file_location('ttask','tests/test_task_console.py'); mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); base=Path('outputs/test-task-console-subqueue-action-panel').resolve(); shutil.rmtree(base, ignore_errors=True); base.mkdir(parents=True, exist_ok=True); mod.test_processing_queue_groups_external_reuse_run_types(); mod.test_export_task_console_writes_human_ui_and_agent_json(base); print('task_console_subqueue_action_panel_direct_test_ok')"
```

下一步优先级顺延为：把更多真实执行器的 run artifact 补齐 `failed_items / retry_command / next_actions`，让这个行动面板在真实 bundle 上更有料；或者把 action plan 暴露成独立 CLI/MCP 只读入口，方便 OpenClaw/agent 直接读取下一步队列。
## Update: 2026-07-06 10:32:00 | Codex / GPT-5

### P0 continued: subqueue action plan exposed through CLI / MCP / HTTP bridge

承接 vsummary task status、BiliNote task workflow 和 Peepshow review queue 的复用方向，本轮把“子队列行动面板”从静态 UI 内部数据提升成独立 agent 接口，方便 OpenClaw、MCP agent 或命令行脚本直接读取下一步队列，而不用解析完整 `task-console.json`。

新增能力：

- CLI：`python -m video_knowledge_pipeline.cli subqueue-action-plan <bundle_dir> --no-refresh --no-write`
- MCP：`subqueue_action_plan` / `subqueue_action_plan_tool`
- OpenClaw HTTP bridge：`/call` 工具 `subqueue_action_plan`
- 写入产物：
  - `subqueue-action-plan.json`
  - `mcp-subqueue-action-plan.args.json`
- manifest 索引：
  - `subqueue_action_plan_json`
  - `mcp_subqueue_action_plan_args`

边界：

- 只读取/汇总已有 run registry 和 task console 状态。
- 不执行 ASR、OCR、VLM、下载、VideoRAG service 或云 API。
- 返回里固定标记 `operator_boundary.no_process_started=true`、`no_cloud_call=true`、`review_only=true`。
- 这个接口的作用是把已经复用进 VKP 的外部能力变成稳定调度入口：人类看 UI，agent 看 JSON/MCP/HTTP。

代码落地：

- `src/video_knowledge_pipeline/task_console.py`
- `src/video_knowledge_pipeline/cli.py`
- `src/video_knowledge_pipeline/mcp_server.py`
- `src/video_knowledge_pipeline/openclaw_http.py`
- `tests/test_task_console.py`

验证：

```powershell
python -m py_compile src\video_knowledge_pipeline\task_console.py src\video_knowledge_pipeline\cli.py src\video_knowledge_pipeline\mcp_server.py src\video_knowledge_pipeline\openclaw_http.py tests\test_task_console.py
$env:PYTHONPATH='src'; python -c "import importlib.util; from pathlib import Path; import shutil; spec=importlib.util.spec_from_file_location('ttask','tests/test_task_console.py'); mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); base=Path('outputs/test-task-console-subqueue-action-plan-cli-mcp').resolve(); shutil.rmtree(base, ignore_errors=True); base.mkdir(parents=True, exist_ok=True); mod.test_processing_queue_groups_external_reuse_run_types(); mod.test_export_task_console_writes_human_ui_and_agent_json(base); print('task_console_subqueue_action_plan_cli_mcp_direct_test_ok')"
$env:PYTHONPATH='src'; python -m video_knowledge_pipeline.cli subqueue-action-plan outputs\test-task-console-subqueue-action-plan-cli-mcp\bundle --no-refresh --no-write
```

下一步优先级顺延为：继续把真实执行器的 run artifact 补齐 `failed_items / retry_command / next_actions`，尤其是 ebook 批次、tile OCR、vision review queue、smart summary section workflow；这样 `subqueue_action_plan` 输出会越来越像一个真正可执行的“下一步调度表”。
## Update: 2026-07-06 16:52:00 | Codex / GPT-5

### P1 continued: smart-summary chapters and content candidates now cross-link

承接 VideoRAG citation graph、vsummary clips/summary 输出结构和 BiliNote 笔记导出体验，本轮把 `smart-summary-chapters` 与 `content-candidate-pack` 从“候选只读取章节 citation”推进到双向链接：

- `content-candidate-pack.json` 的每条候选新增：
  - `summary_chapter_refs`
  - `summary_chapter_ref_count`
- `evidence_citations` 继承章节来源信息，保留 `summary_chapter_ref`，让素材候选能追溯到智能总结章节。
- `export-knowledge-note` 生成候选包后，会把候选反写到 `smart-summary-chapters.json/md`：
  - `content_candidate_pack_linked=true`
  - `linked_content_candidate_count`
  - 每章新增 `linked_content_candidates`
- `smart-summary-chapters.md` 新增 `Linked Content Candidates` 小节，章节可以回看关联素材候选。
- `video-workbench` 的 content candidate payload/表格新增章节引用字段，方便 UI 中看素材属于哪一章。
- 这一步只做本地 evidence graph / export link，不生成发布稿，不事实确认，不自动写入下游内容系统。

代码落地：

- `src/video_knowledge_pipeline/smart_summary_chapters.py`
- `src/video_knowledge_pipeline/knowledge_note_export.py`
- `src/video_knowledge_pipeline/video_workbench.py`
- `tests/test_knowledge_export.py`
- `tests/test_video_workbench.py`

验证：

```powershell
python -m py_compile src\video_knowledge_pipeline\smart_summary_chapters.py src\video_knowledge_pipeline\knowledge_note_export.py src\video_knowledge_pipeline\video_workbench.py tests\test_knowledge_export.py tests\test_video_workbench.py
$env:PYTHONPATH='src'; python -c "import importlib.util; from pathlib import Path; import shutil; spec=importlib.util.spec_from_file_location('tk','tests/test_knowledge_export.py'); mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); base=Path('outputs/test-summary-candidate-bidirectional-links').resolve(); shutil.rmtree(base, ignore_errors=True); base.mkdir(parents=True, exist_ok=True); mod.test_smart_summary_input_pack_fuses_terms_punctuation_and_visual_evidence(base); print('summary_candidate_bidirectional_links_direct_test_ok')"
$env:PYTHONPATH='src'; python -c "import importlib.util; spec=importlib.util.spec_from_file_location('tvw','tests/test_video_workbench.py'); mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); mod.test_export_video_workbench_writes_static_workspace(); print('video_workbench_candidate_chapter_refs_direct_test_ok')"
```

下一步优先级顺延为：继续补 run artifact registry 剩余长任务的 `failed_items / retry_command / next_actions`，或者把 `summary_chapter_refs` 扩展到 `content_asset_status` / `content_handoff_pack` 的批量交接表，让下游内容线程也能按章节消费素材。
## Update: 2026-07-06 17:18:00 | Codex / GPT-5

### P1 continued: content asset status and handoff now carry smart-summary chapter links

承接上一轮 `smart-summary chapters <-> content candidates` 双向链接，本轮把章节引用继续传到下游内容资产状态和交接包，让内容资产/朋友圈线程可以按章节消费素材，而不是只拿一篮子候选。

新增能力：

- `content-asset-status` 读取 `content-candidate-pack.json` 中的 `summary_chapter_refs`，输出：
  - `content_candidate_chapter_ref_count`
  - `content_candidate_linked_chapter_count`
  - `content_candidate_linked_chapters`
  - `content_candidate_chapter_refs_available`
- `batch-content-asset-status` 的 item 继承这些字段，批量 Markdown 新增 `Chapters` 列。
- `content-handoff-pack` 的 item 继承章节字段，Markdown 新增 `Smart Summary Chapter Links` 小节。
- 交接包仍保持原安全边界：`publication_allowed=false`、`allowed_as_fact=false`、`review_required=true`，章节链接只用于证据导航和素材分组，不代表事实确认或可发布。

代码落地：

- `src/video_knowledge_pipeline/content_asset_status.py`
- `src/video_knowledge_pipeline/content_asset_batch.py`
- `tests/test_knowledge_export.py`

验证：

```powershell
python -m py_compile src\video_knowledge_pipeline\content_asset_status.py src\video_knowledge_pipeline\content_asset_batch.py tests\test_knowledge_export.py
$env:PYTHONPATH='src'; python -c "import importlib.util; from pathlib import Path; import shutil; spec=importlib.util.spec_from_file_location('tk','tests/test_knowledge_export.py'); mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); base=Path('outputs/test-content-asset-chapter-status').resolve(); shutil.rmtree(base, ignore_errors=True); base.mkdir(parents=True, exist_ok=True); mod.test_content_asset_status_reports_export_required_and_ready(base); print('content_asset_chapter_status_direct_test_ok')"
$env:PYTHONPATH='src'; python -c "import importlib.util; from pathlib import Path; import shutil; spec=importlib.util.spec_from_file_location('tk','tests/test_knowledge_export.py'); mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); base=Path('outputs/test-content-handoff-chapter-links').resolve(); shutil.rmtree(base, ignore_errors=True); base.mkdir(parents=True, exist_ok=True); mod.test_batch_content_asset_status_and_handoff_pack_only_use_safe_ready_cards(base); print('content_handoff_chapter_links_direct_test_ok')"
```

下一步优先级顺延为：继续补 run artifact registry 剩余长任务的 `failed_items / retry_command / next_actions`，或者把章节链接也显示到 `video-workbench` 的内容素材筛选/跳转交互中。
## Update: 2026-07-06 17:35:00 | Codex / GPT-5

### P1 continued: video-workbench can filter content candidates by smart-summary chapter link status

承接上一轮 `summary_chapter_refs` 进入 content asset / handoff，本轮把同一字段做进 `video-workbench` 的内容素材候选筛选 UI，补齐“章节 -> 素材候选 -> 证据路径”的人工审查手感：

- `video-workbench` 的 content candidate review filters 新增：
  - `chapter_linked`
  - `chapter_missing`
- `filter_counts` 新增对应计数，方便判断素材候选是否已经挂到智能总结章节。
- 内容素材候选表保留章节列，并新增筛选按钮：
  - `已关联章节`
  - `缺章节`
- 这一步只改静态工作台的本地筛选和 JSON payload，不重新导出素材、不调用 LLM、不写下游内容系统。

代码落地：

- `src/video_knowledge_pipeline/video_workbench.py`
- `tests/test_video_workbench.py`

验证：

```powershell
python -m py_compile src\video_knowledge_pipeline\video_workbench.py tests\test_video_workbench.py
$env:PYTHONPATH='src'; python -c "import importlib.util; spec=importlib.util.spec_from_file_location('tvw','tests/test_video_workbench.py'); mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); mod.test_export_video_workbench_writes_static_workspace(); print('video_workbench_chapter_candidate_filter_direct_test_ok')"
```

下一步优先级顺延为：继续补 run artifact registry 剩余长任务的 `failed_items / retry_command / next_actions`，让 task console 的行动面板在真实 bundle 上更完整。
