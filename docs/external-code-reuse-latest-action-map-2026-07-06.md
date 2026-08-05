# 外部开源项目代码复用最新行动图

更新记录：

- 2026-07-06 14:35:55 | Codex / GPT-5：把近期已经落地的外部项目模块复用进展、当前仍值得继续吸收的模块、停止继续搬运的边界和下一步开发顺序收束为最新行动入口。

## 这份文档的用途

这份文档是 VKP 继续吸收外部开源项目代码时的最新入口。它不替代源码审查报告，也不重新展开每个项目的背景，只回答四个问题：

1. 外部项目里已经被 VKP 吸收了什么？
2. 最近又落地了哪些模块？
3. 还有哪些模块值得继续复用？
4. 哪些方向应该停止继续搬运？

当前结论：VKP 不需要整体迁移另一个视频总结应用。最有价值的路线是继续拆出低耦合模块，接进 VKP 已经成型的本地视频知识化主线。

```text
本地/已下载视频
  -> ASR / 平台字幕 / 自带字幕
  -> 字幕仲裁 / 术语纠错 / 标点段落化
  -> 抽帧 / ebook-OCR / screen text / high-res tile
  -> 疑难点 triage / 多模态复核
  -> timeline / evidence / review
  -> smart-summary / full-transcript / knowledge-note
  -> content candidates / video-workbench / sample review / handoff
```

## 最新状态

| 类别 | 状态 | 判断 |
| --- | --- | --- |
| vsummary 方向 | provider、JSON repair、stage cache、run artifact、citation/seek、CUDA 检测已吸收 | 不搬整套 FastAPI/React/LlamaIndex/LanceDB，只继续补任务状态和 UI 细节 |
| BiliNote 方向 | 字幕解析清洗、转写校对 prompt、章节编辑、transcript editor 已吸收 | 不搬整套 React UI，只继续吸收同屏编辑体验 |
| VideoRAG / VTimeLLM / MovieChat 方向 | moment index、video RAG pack/search、chapter citation digest、long-video memory 已吸收 | 继续增强 evidence trace、搜索跳转和章节引用 |
| Qwen / InternVL / LLaVA 方向 | VLM preprocess、high-res tile plan、tile import/merge、本地 VLM smoke 已吸收 | 只做 adapter、预处理、smoke，不嵌模型源码 |
| FunASR / SenseVoice / WhisperX 方向 | 本地 ASR、sidecar、transcript arbitration、quality summary 已吸收 | 继续做标点、术语、段落、说话人后处理 |
| Peepshow / VidClaude 方向 | multimodal sample review、vision review queue、内容候选抽样信号已吸收 | 继续强化人审 UI、失败重试和质量指标 |

## 最近已落地的复用推进

### 1. Citation Digest 闭环

已把 VideoRAG、VTimeLLM、MovieChat 的证据追踪思路接进智能总结和内容素材链路：

- `build-smart-summary-chapters` 生成章节级 `citation_digest`。
- `generate-smart-summary-with-codex` 把 citation digest 注入 `smart-summary.codex.md` / `smart-summary.md`。
- `export-knowledge-note` 把 citation digest 下沉到 `content-candidate-pack`。
- `video-workbench.html` 显示候选素材的 citation 状态和过滤。
- `multimodal-sample-review.html` 显示候选素材的 citation summary 和证据路径。

意义：智能总结、内容素材、人审抽样都能回到时间戳、timeline、OCR/ebook、多模态和 review gap 证据。

### 2. Provider / 本地 VLM smoke 进入工作台和 run registry

已把 Qwen/InternVL/LLaVA 的 provider adapter 思路和 vsummary 的 provider status 面板接进 VKP：

- `video-workbench.html` 显示 provider smoke、provider matrix、本地 VLM plan/executed/failed 状态。
- `vision-provider-smoke`、`vision-provider-matrix`、`local-vlm-serving-smoke` 会登记到 `runs/*/run.json`。
- plan-only 的本地 VLM smoke 明确标记为 `needs_execution`，不伪装成已执行。

边界：只读展示，不启动本地模型服务，不调用云模型，不保存 API key。

### 3. ASR / 字幕仲裁质量信号进入总结输入和工作台

已把 BiliNote 字幕清洗、WhisperX 时间戳后处理、SenseVoice 元数据路线推进为结构化质量信号：

- `source-arbitrated-transcript.json` 新增 `quality_summary`。
- `transcript-source-arbitration.md` 显示质量状态、平均置信度、高置信术语替换、低置信冲突。
- `smart-summary-input-pack` 读取 transcript arbitration quality。
- `video-workbench.html` 显示低置信冲突、已改写片段、高置信术语和仲裁质量状态。

边界：高置信纠错可进入 corrected transcript；低置信冲突只能进入 review，不静默污染最终总结。

### 4. ebook/OCR 低质结果进入 high-res tile recovery

已把 InternVL dynamic tiling、Qwen-VL 图像预处理和 ebook/OCR 分工接进失败分流：

- `ocr_wrapper_only`、`ocr_text_empty`、`ocr_text_low_information` 会标记 `needs_high_res_tile_recovery`。
- `run-visual-structure` failed items 会给出 `high-res-tile-plan --indexes ... --execute-tiles` 重试建议。
- `high-res-tile-plan` 会读取 timeline 顶层 `ebook_pipeline_status`。
- tile plan item 会保留低质 OCR 状态、reasons、证据路径。

边界：tile 是低质图文结果的补救路径，不把空 OCR 或 wrapper-only 当成功。

## 仍值得继续复用的模块

### P0：run artifact registry 全覆盖

参考来源：vsummary stage/task state、BiliNote 任务历史、Peepshow/VidClaude 批次报告。

下一步应补齐：

- `screen-text-recovery`、`high-res-tile-plan`、`tile-result-import/merge`、`vision-review-queue`、`smart-summary-section-workflow` 的 run artifact 覆盖。
- 每个 failed item 都应有：失败原因、证据路径、下一步工具、retry command、operator boundary。
- `task-console.html`、`video-workbench.html`、`subqueue-action-plan` 读取同一套状态。

停止条件：常见失败不需要回聊天记录里找命令，UI 和 JSON 都能直接告诉用户下一步。

### P0：ASR / 字幕后处理继续增强

参考来源：BiliNote 字幕清洗、WhisperX word-level timestamp / diarization、SenseVoice event tags。

下一步应补齐：

- 标点恢复。
- 课程术语词典。
- 人名、品牌、工具名纠错。
- 段落化和说话人分离。
- `full-transcript.md` 同时体现原文、纠正状态和低置信标记。

停止条件：`smart-summary.md` 能区分可信术语、疑似错词和待复核内容；`full-transcript.md` 不再只是 ASR 原始流水账。

### P1：VideoRAG / moment search / citation 跳转互链

参考来源：VideoRAG retrieval unit、VTimeLLM time grounding、vsummary timestamp seek/citation UI。

下一步应补齐：

- workbench 搜索结果点击后跳视频时间、timeline row、content candidate。
- smart-summary section 能跳到 moment chunk 和候选素材。
- content candidate 能跳回章节、时间戳、证据帧、review rows。

停止条件：不用默认引入重型向量库，也能完成本地定位、证据回跳和人工复核导航。

### P1：smart-summary 章节级质量闭环

参考来源：BiliNote 章节笔记、vsummary 分段总结、MovieChat long memory、VideoRAG citation digest。

下一步应补齐：

- 每章独立生成、复核、安装。
- 每章保留 transcript、OCR/ebook、visual、temporal、review gap 的引用覆盖。
- Codex、在线 LLM、本地 LLM 共用同一份 input pack。
- 质量门禁检查完整时长覆盖、避免 ASR 大段复制、避免只总结前几分钟。

停止条件：`smart-summary.md` 是成品阅读层，`knowledge-note.md` 是证据审计层，二者边界稳定。

### P2：本地 VLM serving smoke 实机化

参考来源：Qwen-VL OpenAI-compatible serving、InternVL dynamic tiling、LLaVA-OneVision 多图/短片段输入。

下一步应补齐：

- 只读检查 provider 地址、模型名、单图、多图、帧组能力、JSON 输出稳定性。
- smoke 结果进入 run registry，并在 workbench 展示。
- 支持用户手动启动本地 VLM 后再执行 smoke。

停止条件：用户能知道本机 VLM 是否可用、支持什么输入、下一步命令是什么；VKP 不把本地 VLM 变成默认硬依赖。

## 不应继续整体搬运的方向

| 方向 | 不搬原因 | VKP 替代路线 |
| --- | --- | --- |
| vsummary 完整 FastAPI / React / LlamaIndex / LanceDB | 会形成第二套后端、第二套 UI、第二套索引 | 只吸收 provider、stage、run、citation、UI 交互 |
| BiliNote 完整 React UI | 工作流可借鉴，但 VKP 静态 bundle 更适合本地文件、MCP、OpenClaw | 在 `video-workbench.html` 复刻关键交互 |
| VideoRAG 重型 graph/vector 后端 | 个人工具维护成本高，依赖重 | 默认 JSONL / keyword / SQLite，vector 只做显式可选 |
| Qwen/InternVL/LLaVA 模型源码嵌入主流程 | 显存、依赖、模型部署复杂 | provider adapter / OpenAI-compatible / HTTP serving |
| 下载/字幕抓取后端 | VKP 边界是内容理解，不负责下载 | 继续交给 `video-download-orchestrator` 和 handoff |
| 默认全帧云多模态 | 成本、隐私、限流和失败恢复都不适合作为默认 | 本地抽帧/ebook/OCR/triage 先跑，云多模态只补疑难点或显式全量模式 |

## 后续看新项目时的判断表

| 判断项 | 如果是 | 如果否 |
| --- | --- | --- |
| 是否提供 VKP 当前没有的低耦合模块？ | 拉源码看具体文件 | 只记录项目名，不投入 |
| 是否能不引入重依赖单独复用？ | 做 adapter 或小模块 | 不进主线 |
| 是否改善当前瓶颈：总结质量、时间定位、小字 OCR、批次重试、人审评分？ | 排入 backlog | 暂停 |
| 是否要求替换 VKP 主架构？ | 默认拒绝整体迁移 | 可继续拆模块 |
| 是否绕过下载、云 API、人工复核边界？ | 不接入 | 可继续评估 |

## 当前推荐开发顺序

1. 继续补齐剩余长任务的 run artifact registry，尤其是 screen text、tile、vision review、summary section workflow。
2. 把 ASR/字幕后处理做深：标点、术语、段落化、说话人。
3. 打通 VideoRAG / moment search / content candidate / smart-summary section 的互链和 workbench 跳转。
4. 继续强化 smart-summary 章节级质量门禁。
5. 本地 VLM serving smoke 做成可选实机验收，不默认启用。

## 阅读顺序

如果只想知道下一步怎么做，先读本文。

如果要看细节，再读：

- `docs/external-code-reuse-practical-playbook-2026-07-06.md`
- `docs/external-code-reuse-current-module-map-2026-07-06.md`
- `docs/external-code-reuse-next-module-decisions-2026-07-06.md`
- `docs/external-open-source-reuse-module-inventory-2026-07-06.md`
- `docs/external-code-module-reuse-backlog-2026-07-04.md`
- `docs/vsummary-source-review.md`
- `docs/bilinote-pridewood-source-review.md`
- `docs/ai-video-open-source-survey-2026-07-04.md`
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

下一步优先级顺延为：继续补剩余真实执行器的 failed_items 质量，或者把 `human_sample_eval` 的状态进一步显示到 `video-workbench` 的 Provider/内容候选之外的“质量抽样”专栏。## Update: 2026-07-06 14:56:06 | Codex / GPT-5

### 已文档化：下一批可直接复用的代码模块队列

新增 `docs/external-code-reuse-next-code-modules-2026-07-06.md`，把“还有哪些值得复用的代码模块”从聊天判断整理成可执行队列。

该文档按模块而不是按项目罗列，当前优先级为：

1. 质量抽样独立面板进入 `video-workbench`。
2. 剩余长任务 run artifact failed_items 全覆盖。
3. BiliNote-style 视频同屏编辑继续合并。
4. 章节级智能总结工作流继续吸收。
5. VideoRAG 搜索跳转和 content candidate 双向回链增强。
6. ASR/字幕后处理进入 `corrected-transcript` 和 summary input policy。
7. high-res tile / 局部小字恢复继续完善。
8. 本地 VLM adapter smoke 实机化。
9. 内容素材候选复核 UI 增强。

每个模块都写明了参考来源、可复用代码形态、VKP 落点、验收标准和停止条件。它是后续继续“榨干”外部项目代码时的执行入口，不替代源码审查报告，也不鼓励整体搬迁外部项目。
