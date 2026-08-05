# 外部开源项目可复用模块下一步决策表

更新记录：

- 2026-07-06 15:20:00 | Codex / GPT-5：把已审查外部项目中仍值得吸收的代码模块整理成下一步执行决策表，明确复用位置、验收标准和停止条件。

## 定位

这份文档不是新的项目调研，也不是“再找一个完整视频总结工具替代 VKP”。它用于回答一个更窄的问题：

> 在已经参考过 vsummary、BiliNote、VideoRAG、MovieChat、VTimeLLM、Qwen-VL、InternVL、LLaVA-OneVision、WhisperX、FunASR/SenseVoice、Peepshow/VidClaude 之后，VKP 还应该继续复用哪些代码模块？

当前结论：

- 不再建议整体搬迁任何一个完整应用。
- 继续吸收低耦合模块，接入 VKP 已有的 ASR、OCR/ebook、多模态复核、timeline、review、smart-summary、workbench 和 CLI/MCP/OpenClaw 边界。
- 复用重点从“有没有功能”转向“能否提高最终人类可读文件的准确率、可追溯性和审核效率”。

## 当前 VKP 主线

```text
本地/已下载视频
  -> ASR / 平台字幕 / 自带字幕
  -> transcript source arbitration / 术语纠错 / 标点和段落化
  -> 抽帧 / ebook-OCR / screen text recovery / high-res tile
  -> 疑难点 triage / 多模态单帧或多帧复核
  -> timeline / evidence / review targets
  -> smart-summary / full-transcript / knowledge-note / content candidates
  -> video-workbench / sample review / content handoff
```

外部代码只应该被复用到这条主线的局部节点中。

## 已经基本吸收完的模块

| 外部来源 | 已吸收能力 | VKP 落点 | 后续策略 |
| --- | --- | --- | --- |
| `alpha03123/vsummary` | OpenAI-compatible 文本网关、JSON repair、stage cache、run artifact、timestamp/citation UI、CUDA 检测 | `text_llm_gateway.py`、`stage_cache.py`、`run_artifact_registry.py`、`task_console.py`、`video_workbench.py`、`cuda_runtime.py` | 不搬整套 FastAPI/React/LlamaIndex/LanceDB；只继续补任务状态和 UI 细节 |
| `PrideWood/bilinote` | 字幕解析清洗、短句合并、转写校对 prompt、mind-map prompt、transcript editor、章节编辑体验 | `bilinote_transcript_tools.py`、`bilinote_summary_tools.py`、`transcript_correction_pack.py`、`transcript_editor.py`、`smart_summary_section_editor.py` | 不搬整套 React UI；继续吸收同屏编辑和转写修正体验 |
| VideoRAG | JSONL/SQLite chunk、检索单元、citation evidence | `video_rag_pack.py`、`video_rag_search.py`、`video_rag_http.py`、`smart_summary_chapters.py` | 默认保持本地 keyword/SQLite；向量库只作为可选 adapter |
| VTimeLLM | moment grounding、时间定位、alignment audit | `video_moment_index.py`、`timeline_alignment_audit.py` | 继续用于 review_start / ASR start / frame time 的冲突审计 |
| MovieChat | 长视频 short memory / long memory 分层 | `long_video_memory_pack.py`、`smart_summary_input_pack.py` | 继续服务 smart-summary 输入，不单独做聊天系统 |
| Qwen/InternVL/LLaVA-OneVision | 图像缩放、压缩、多图/帧组输入、dynamic tiling | `vlm_preprocess.py`、`high_res_tile_plan.py`、`tile_result_import_builder.py`、`tile_result_merge.py` | 不嵌模型源码；只接 provider adapter 或本地服务 smoke |
| FunASR/SenseVoice/WhisperX | 本地 ASR、timestamp sidecar、ready gate、后处理路线 | `funasr_python_runner.py`、`asr_runner.py`、`asr_environment.py`、`transcript_sidecar.py`、`transcript_source_arbitration.py` | 继续补质量信号、说话人、标点、术语纠错 |
| Peepshow/VidClaude | 帧证据卡、批次复核、抽样评分 | `vision_review_queue.py`、`multimodal_sample_review.py`、`video_workbench.py` | 继续强化人审 UI 和质量指标，不把截图当唯一审核材料 |

## 仍值得继续复用的模块

### P0：ASR / 字幕仲裁质量信号进入总结输入

参考来源：

- BiliNote 的字幕清洗和段落化。
- WhisperX 的 word-level timestamp / diarization 思路。
- SenseVoice 的 emotion/event tags 与本地 ASR 元数据。

应该复用的具体点：

- transcript source arbitration 不只产出纠正版文本，还要产出质量摘要。
- 质量摘要应包括：来源数量、改动段落数、低置信冲突数、高置信术语替换数、平均置信度、需要人工复核的原因。
- `smart-summary-input-pack` 应读取这些信号，告诉 Codex/LLM 哪些术语可以信，哪些地方只能作为待复核内容。
- `video-workbench` 应展示 ASR/字幕来源冲突，而不是只展示最后合并文本。

VKP 接入点：

- `transcript_source_arbitration.py`
- `smart_summary_input_pack.py`
- `video_workbench.py`
- `transcript_editor.py`

验收标准：

- `source-arbitrated-transcript.json` 中有结构化 `quality_summary`。
- `smart-summary-input-pack.json/md` 中能看到 transcript arbitration quality。
- 最终 `smart-summary.md` 不把低置信纠错当成确定事实。

停止条件：

- 高置信纠错可以自动进入纠正版逐字稿。
- 低置信冲突稳定进入 review pack。
- 工作台能显示冲突来源、时间段和下一步动作。

### P0：run artifact registry 全覆盖

参考来源：

- vsummary 的 stage/task state。
- BiliNote 的任务历史。
- Peepshow/VidClaude 的 frame batch report。

应该复用的具体点：

- 每个长任务都有 `runs/<task>/run.json`。
- 每条 run 包含 status、artifacts、failed_items、retry_command、operator_boundary。
- 失败重试不再靠用户复制几十条 PowerShell 命令。

VKP 接入点：

- `run_artifact_registry.py`
- `task_console.py`
- `video_workbench.py`
- 各执行模块：ASR、ebook、screen-text、tile、多模态、temporal、smart-summary、content-candidate。

验收标准：

- `task-console.html` 和 `video-workbench.html` 能显示所有关键长任务的状态。
- 每个 failed item 都有可执行或可复制的 retry command。
- preview / needs_execution / completed / needs_retry / needs_review / needs_input 语义一致。

停止条件：

- 常用任务不需要回聊天里找命令。
- UI 可以看出哪一批成功、哪一批失败、失败原因是什么。

### P1：高分辨率 tile recovery 与 ebook/OCR 分工

参考来源：

- InternVL dynamic tiling。
- Qwen-VL/qwen-vl-utils 的图像预处理。
- 现有 `ebook_markdown_pipeline` 的图文解析能力。

应该复用的具体点：

- 整帧 OCR/ebook 为空、wrapper-only、低信息量时，自动进入 tile plan。
- 小字、表格、代码、软件界面截图使用局部 tile 证据。
- tile 输出不能直接伪装成 OCR 成功，必须保留坐标、来源、置信度和 review 状态。

VKP 接入点：

- `high_res_tile_plan.py`
- `tile_result_import_builder.py`
- `tile_result_merge.py`
- `visual_structure.py`
- `screen_text_recovery.py`

验收标准：

- blocker 能区分：ebook 失败、tile 待跑、tile 低置信、需要多模态、需要人工。
- `extraction-audit.md` 能列出 tile 坐标和证据路径。
- 有效 tile 结果能回填 `visual_text` / `structured_visual`，低质结果进入 review。

停止条件：

- 屏幕小字和表格类缺口不再只显示“ocr empty”，而是有明确下一步：tile、VLM、人工。

### P1：视频 RAG / moment search / citation 跳转互链

参考来源：

- VideoRAG 的 retrieval unit。
- VTimeLLM 的 time grounding。
- vsummary 的 timestamp seek 和 citation UI。

应该复用的具体点：

- `smart-summary.md` 的关键观点能回链到 moment chunk。
- content candidates 能回链到 transcript / visual evidence / review gap。
- workbench 搜索结果点击后能跳视频时间、timeline row、候选素材。

VKP 接入点：

- `video_rag_pack.py`
- `video_rag_search.py`
- `video_moment_index.py`
- `smart_summary_chapters.py`
- `content_candidate_pack`
- `video_workbench.py`

验收标准：

- 用户能搜索一个术语或工具名，看到它出现的时间段、证据来源和是否进入总结/素材候选。
- summary section、content candidate、timeline row 之间可以双向跳转。

停止条件：

- 不需要引入重型向量库也能完成本地定位和证据回跳。

### P1：智能总结章节级重写质量闭环

参考来源：

- BiliNote 的章节笔记和 prompt 分块。
- vsummary 的分段总结 pipeline。
- MovieChat 的 long memory。
- VideoRAG 的 citation digest。

应该复用的具体点：

- 每章独立生成、独立复核、独立安装。
- 每章保留 transcript、OCR/ebook、visual、temporal、review gap 的 citation digest。
- Codex 或在线 LLM 都复用同一份 input pack，不另起一套 prompt 数据结构。

VKP 接入点：

- `smart_summary_input_pack.py`
- `smart_summary_chapters.py`
- `smart_summary_section_workflow.py`
- `smart_summary_section_editor.py`
- `smart_summary_section_apply.py`
- `smart_summary_codex.py`

验收标准：

- `smart-summary.md` 覆盖完整视频，不偏向前几分钟。
- 分段总结不是 ASR 复制粘贴。
- 每章能显示引用覆盖和低置信边界。

停止条件：

- `smart-summary.md` 可以作为成品阅读层，`knowledge-note.md` 保留证据审计层，二者不混淆。

### P2：本地 VLM serving smoke

参考来源：

- Qwen-VL OpenAI-compatible serving。
- InternVL dynamic tiling。
- LLaVA-OneVision 多图/短片段输入。

应该复用的具体点：

- 只读检查 provider 是否可用。
- 检查单图、多图、帧组、JSON 输出稳定性。
- 不自动启动模型服务，不把本地 VLM 变成默认依赖。

VKP 接入点：

- `local_vlm_server_adapter.py`
- `vision_provider_smoke.py`
- `vision_api.py`
- `vlm_preprocess.py`
- `video_workbench.py`

验收标准：

- workbench 能显示本地 VLM plan/executed/failed 状态。
- smoke 结果进入 `runs/local-vlm-serving-smoke/run.json`。
- 不泄露 API key，不启动长任务。

停止条件：

- 用户能明确知道本地 VLM 是否可试、支持哪些输入形态、下一步命令是什么。

### P2：内容素材候选与智能总结双向链接

参考来源：

- vsummary 的 clips / summary 输出结构。
- BiliNote 的笔记导出体验。
- VideoRAG 的 evidence path。

应该复用的具体点：

- 从 smart-summary section 跳到 content candidates。
- 从 content candidate 跳回章节、时间戳、证据帧、review rows。
- 素材类型区分 method、case、quote、visual_explainer、tool、workflow。

VKP 接入点：

- `knowledge_note_export.py`
- `content_asset_status.py`
- `content_asset_batch.py`
- `content_handoff_pack`
- `video_workbench.py`

验收标准：

- 下游线程拿到的素材仍是 `review_required=true`、`publication_allowed=false`。
- 每条素材都带时间段、证据路径、事实核查状态和禁止发布标记。

停止条件：

- 内容资产线程能直接消费 evidence / inspiration，但不能误以为是事实结论或发布稿。

## 不再建议继续复用的方向

| 方向 | 停止理由 |
| --- | --- |
| 整体迁移 vsummary 后端 | VKP 已有 CLI/MCP/OpenClaw/static bundle/run registry；整体搬会产生第二套系统 |
| 整体迁移 BiliNote UI | VKP 的静态 bundle 更适合本地文件审查和 agent 调用；只复刻关键交互 |
| 默认引入重型向量库或图数据库 | 个人工具维护成本过高；默认 JSONL/keyword/SQLite 足够 |
| 把 Qwen/InternVL/LLaVA 源码嵌入主流程 | 依赖、显存、模型下载和环境复杂度过高；应走 provider adapter |
| 在 VKP 重做下载/登录/字幕抓取后端 | 下载和平台权限边界属于 `video-download-orchestrator` 或平台侧工具 |
| 默认全帧云多模态 | 成本、隐私、限流和失败恢复都不适合默认；云模型只补疑难点或显式全量模式 |

## 下一步执行顺序

1. ASR / 字幕仲裁质量信号进入 `smart-summary-input-pack` 和 `video-workbench`。
2. run artifact registry 继续补齐剩余长任务。
3. high-res tile recovery 与 ebook/OCR 分工继续细化。
4. video RAG / moment search / citation 跳转互链继续增强。
5. smart-summary section 级质量闭环继续提高成品总结质量。
6. local VLM serving smoke 保持可选检查，不进入默认主流程。
7. content candidate 与 smart-summary 双向链接，服务下游内容素材线程。

## 判断一个新开源项目是否还值得拉源码

只有同时满足以下条件，才继续拉源码审查：

1. 它提供 VKP 当前缺的低耦合模块。
2. 它能接入现有 timeline/evidence/review/export，不要求替换主架构。
3. 它能改善当前瓶颈：最终总结质量、时间定位、屏幕文字、批次重试、人工评分、内容素材证据链。
4. 它不会绕过下载授权、云 API preflight、人工复核、隐私脱敏和禁止自动发布边界。
5. 它的代码可以被拆成小模块，而不是只能整体运行。

如果不满足，就只记录设计思路，不继续搬代码。


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
