# 外部开源项目代码复用收束与下一步动作

更新记录：

- 2026-07-06 12:16:02 | Codex / GPT-5：把已经参考、已经吸收、仍值得继续复用、以及不应继续整体搬运的外部代码模块整理成收束版开发导航。

## 定位

这份文档回答一个窄问题：

> 在已经分析并部分复用 vsummary、BiliNote、VideoRAG、MovieChat、VTimeLLM、Qwen-VL、InternVL、LLaVA-OneVision、WhisperX、FunASR/SenseVoice、Peepshow/VidClaude 等项目之后，VKP 还应该继续复用哪些代码模块？

结论：VKP 不需要再找一个完整项目替换自己。现在最有效的方式是继续拆局部能力，接入 VKP 已经成型的主流程：

```text
本地/已下载视频
  -> ASR / 平台字幕 / 自带字幕
  -> 字幕仲裁 / 术语纠错 / 标点段落化
  -> 抽帧 / ebook-OCR / screen text / high-res tile
  -> 疑难点 triage / 多模态复核
  -> timeline / evidence / review
  -> smart-summary / full-transcript / knowledge-note
  -> content candidates / workbench / handoff
```

## 总体判断

| 类别 | 判断 | 后续动作 |
| --- | --- | --- |
| 已基本吸收 | vsummary 的 provider/stage/run/citation；BiliNote 的字幕和编辑体验；VideoRAG/VTimeLLM/MovieChat 的 chunk、moment、memory；Qwen/InternVL 的预处理和 tile 思路 | 不再整体搬运，只继续修细节 |
| 仍值得继续复用 | run artifact 全覆盖、ASR/字幕后处理、high-res tile recovery、视频 RAG 跳转、smart-summary 章节质量闭环、本地 VLM smoke、内容素材互链 | 按 P0/P1/P2 做小模块落地 |
| 不值得继续搬 | 完整 React/FastAPI 后端、重型向量图数据库、模型仓库源码内嵌、下载后端、默认全帧云多模态 | 保留 adapter 或只读参考，不进入主线 |

## 已落地能力索引

| 外部来源 | 已复用能力 | VKP 当前落点 |
| --- | --- | --- |
| vsummary | OpenAI-compatible text gateway、JSON repair、stage cache、run artifact、timestamp/citation UI、CUDA 检测 | `text_llm_gateway.py`、`stage_cache.py`、`run_artifact_registry.py`、`task_console.py`、`video_workbench.py`、`cuda_runtime.py` |
| BiliNote | 字幕解析清洗、短句合并、转写校对 prompt、transcript editor、mind-map/章节编辑体验 | `bilinote_transcript_tools.py`、`bilinote_summary_tools.py`、`transcript_correction_pack.py`、`transcript_editor.py`、`smart_summary_section_editor.py` |
| VideoRAG | retrieval chunk、JSONL/SQLite 本地检索、citation evidence | `video_rag_pack.py`、`video_rag_search.py`、`video_rag_http.py`、`smart_summary_chapters.py` |
| VTimeLLM | moment grounding、时间定位、alignment audit | `video_moment_index.py`、`timeline_alignment_audit.py` |
| MovieChat | long-video short memory / long memory 分层 | `long_video_memory_pack.py`、`smart_summary_input_pack.py` |
| Qwen-VL / InternVL / LLaVA-OneVision | 单图/多图预处理、压缩、dynamic tiling、高分辨率 tile recovery | `vlm_preprocess.py`、`high_res_tile_plan.py`、`tile_result_import_builder.py`、`tile_result_merge.py` |
| FunASR / SenseVoice / WhisperX | 本地 ASR、timestamp sidecar、模型 ready gate、word-level/speaker/punctuation 后处理路线 | `funasr_python_runner.py`、`asr_runner.py`、`asr_environment.py`、`transcript_sidecar.py`、`transcript_source_arbitration.py` |
| Peepshow / VidClaude | 帧证据卡、视觉复核队列、人工抽样评分 | `vision_review_queue.py`、`multimodal_sample_review.py`、`video_workbench.py` |

## 下一步还值得继续复用的模块

### P0：run artifact registry 全覆盖

复用来源：vsummary stage/task state、BiliNote 任务面板、Peepshow/VidClaude 批次报告。

要继续做的事：

- 每个长任务都有 `runs/<task>/run.json` 和 `run.md`。
- 每条 run 固定包含：`status`、`artifacts`、`failed_items`、`retry_command`、`next_actions`、`operator_boundary`。
- `task-console.html` / `video-workbench.html` 能看到批次大小、总批次数、失败 indexes、重试命令和报告路径。
- `subqueue-action-plan` 可以把这些 run 汇总成 agent 可执行的下一步计划。

当前优先补齐对象：

1. `export-knowledge-note` 本身的 run artifact。
2. ebook / visual structure 批次的 failed item 明细。
3. tile OCR / tile VLM import / merge 的低置信失败项。
4. vision review queue / multimodal batch 的 retry queue。
5. smart-summary section workflow 的章节级失败项。

停止条件：常见失败不需要回聊天记录里找命令，UI 和 JSON 里能直接看下一步。

### P0：ASR / 字幕仲裁后处理继续增强

复用来源：BiliNote 字幕清洗、WhisperX word-level timestamp / diarization、SenseVoice emotion/event tags。

要继续做的事：

- 标点恢复和段落化进入纠正版 transcript。
- 课程术语、人名、品牌、工具名词典进入 `transcript-source-arbitration`。
- 高置信术语自动进入 corrected transcript。
- 低置信冲突进入 review pack，不直接污染最终总结。
- `smart-summary-input-pack` 和 `video-workbench` 显示仲裁质量摘要。

停止条件：`full-transcript.md` 不再只是 ASR 原文流水账，`smart-summary.md` 能明确知道哪些术语可相信、哪些需要复核。

### P1：high-res tile recovery 与 ebook/OCR 分工

复用来源：InternVL dynamic tiling、Qwen-VL 图像预处理、ebook_markdown_pipeline 图文解析。

要继续做的事：

- 整帧 ebook/OCR 返回空、wrapper-only、低信息量时，自动标记 tile plan 或多模态复核。
- 小字、表格、代码、软件界面截图走局部 tile evidence。
- tile 结果必须保留坐标、来源、置信度、review 状态。
- 有效 tile 可以回填 `visual_text` / `structured_visual`；低质 tile 只能进入 review。

停止条件：屏幕小字不再只有“ocr empty”，而是有明确机器补救路径和人工复核路径。

### P1：视频 RAG / moment search / citation 跳转互链

复用来源：VideoRAG retrieval unit、VTimeLLM time grounding、vsummary timestamp seek/citation UI。

要继续做的事：

- `smart-summary.md` 的关键观点能回链到 moment chunk。
- content candidate 能回链到 transcript、visual evidence、review gap。
- `video-workbench` 搜索结果点击后跳视频时间、timeline row、候选素材。
- 支持按术语、工具名、方法、案例、结论查时间段和证据来源。

停止条件：不用重型向量库，也能完成本地定位、证据回跳和人工复核导航。

### P1：smart-summary 章节级质量闭环

复用来源：BiliNote 章节笔记、vsummary 分段总结、MovieChat long memory、VideoRAG citation digest。

要继续做的事：

- 每章独立生成、复核、安装。
- 每章保留 transcript、OCR/ebook、visual、temporal、review gap 的 citation digest。
- Codex 和未来在线 LLM 共用同一份 input pack。
- 质量门禁检查覆盖完整时长、避免 ASR 复制粘贴、避免只总结前几分钟。

停止条件：`smart-summary.md` 是成品阅读层，`knowledge-note.md` 是证据审计层，两者不混。

### P2：本地 VLM serving smoke

复用来源：Qwen-VL OpenAI-compatible serving、InternVL dynamic tiling、LLaVA-OneVision 多图/短片段输入。

要继续做的事：

- 只读检查 provider 地址、模型名、单图/多图/帧组能力、JSON 输出稳定性。
- smoke 结果进入 `runs/local-vlm-serving-smoke/run.json`。
- `video-workbench` 显示本地 VLM plan/executed/failed 状态。

停止条件：用户能知道本机 VLM 是否可用、支持什么输入、下一步命令是什么；但 VKP 不把本地 VLM 变成默认硬依赖。

### P2：内容素材候选与智能总结双向链接

复用来源：vsummary clips/summary 输出、BiliNote 笔记导出、VideoRAG evidence path。

要继续做的事：

- 从 smart-summary section 跳到 content candidates。
- 从 content candidate 跳回章节、时间戳、证据帧、review rows。
- 支持素材类型过滤：`method`、`case`、`quote`、`visual_explainer`、`tool`、`workflow`。
- `content-asset-status` / `content-handoff-pack` 保留章节引用。

停止条件：下游内容线程可以按章节消费素材，但所有素材仍是 `review_required=true`、`publication_allowed=false`、`allowed_as_fact=false`。

## 不要继续整体搬运的方向

| 方向 | 不搬原因 | VKP 替代路线 |
| --- | --- | --- |
| vsummary 完整 FastAPI/React/LlamaIndex/LanceDB | 会形成第二套后端、第二套 UI、第二套索引 | 只吸收 provider、stage、run、citation、UI 交互模式 |
| BiliNote 完整 React UI | 工作流可借鉴，但 VKP 静态 bundle 更适合本地文件、MCP、OpenClaw | 在 `video-workbench.html` 复刻关键交互 |
| VideoRAG 重型 graph/vector 后端 | 个人工具维护成本高，依赖重 | 默认 JSONL/keyword/SQLite，vector 只做显式可选 |
| Qwen/InternVL/LLaVA 模型源码嵌入主流程 | 显存、依赖、模型部署复杂 | 统一 provider adapter / OpenAI-compatible / HTTP serving |
| 下载/字幕抓取后端 | VKP 边界是内容理解，不负责下载 | 继续交给 `video-download-orchestrator` 和 handoff |
| 默认全帧云多模态 | 成本、隐私、限流和失败恢复都不适合作为默认 | 本地抽帧/ebook/OCR/triage 先跑，云多模态只用于疑难点或显式全量模式 |

## 新外部项目是否值得拉源码的判断表

看到新的 AI 视频总结/分析项目时，先按这张表判断：

| 问题 | 是 | 否 |
| --- | --- | --- |
| 是否提供 VKP 当前没有的低耦合模块？ | 拉源码看具体文件 | 只记录名称，不投入 |
| 是否能不引入重依赖单独复用？ | 做 adapter 或小模块 | 不进主线 |
| 是否能改善当前瓶颈：总结质量、时间定位、小字 OCR、批次重试、人审评分？ | 排入 backlog | 暂停 |
| 是否要求替换 VKP 主架构？ | 默认拒绝整体迁移 | 可继续拆模块 |
| 是否绕过下载、云 API、人工复核边界？ | 不接入 | 可继续评估 |

## 当前推荐开发顺序

1. `export-knowledge-note` 和剩余长任务接满 run artifact registry。
2. ASR/字幕仲裁后处理：标点、术语、段落化、说话人。
3. high-res tile recovery 与 ebook/OCR 失败分流。
4. VideoRAG / moment search / citation 跳转进入 workbench。
5. smart-summary 章节级质量闭环继续增强。
6. 本地 VLM serving smoke 作为可选能力，不默认启用。

## 相关文档

- `docs/external-code-reuse-ledger-2026-07-04.md`
- `docs/external-code-module-reuse-backlog-2026-07-04.md`
- `docs/external-code-reuse-remaining-modules-2026-07-05.md`
- `docs/external-code-reuse-exhaustion-status-2026-07-05.md`
- `docs/external-open-source-reuse-module-inventory-2026-07-06.md`
- `docs/external-code-reuse-current-module-map-2026-07-06.md`
- `docs/external-code-reuse-next-module-decisions-2026-07-06.md`
- `docs/external-project-reuse-implementation-2026-07-04.md`
- `docs/vsummary-source-review.md`
- `docs/bilinote-pridewood-source-review.md`
- `docs/ai-video-open-source-survey-2026-07-04.md`
- `docs/smart-summary-best-practices.md`
