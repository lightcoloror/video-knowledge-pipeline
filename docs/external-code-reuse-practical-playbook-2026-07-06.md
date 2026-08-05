# 外部开源项目代码复用作战手册

更新记录：

- 2026-07-06 14:04:55 | Codex / GPT-5：把已审查外部项目中值得吸收的代码模块、VKP 当前落点、继续复用顺序、停止条件和验证口径整理成操作手册。

## 这份文档解决什么问题

这份文档用于回答：

> 发现一个新的 AI 视频总结 / 视频理解 / 视频笔记开源项目时，VKP 应该复制什么、不复制什么、怎么落地、何时停止继续榨。

它不是源码审查报告，也不是功能愿望清单。它是开发时的判断表。

当前结论很明确：VKP 不需要再整体迁移一个完整应用。更高收益的做法是把外部项目拆成低耦合模块，接进 VKP 已有的本地视频知识化主线。

## VKP 当前主线

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

外部代码只应该进入这条主线的局部节点。不要复制一个项目的第二套下载、第二套后端、第二套 UI、第二套数据库、第二套权限边界。

## 一句话判断

| 问题 | 结论 |
| --- | --- |
| 还能不能继续复用外部项目代码？ | 能，但只复用局部能力。 |
| 有没有必要再找完整替代品？ | 暂时没有。VKP 主架构已经成型。 |
| 当前最值得继续吸收的是什么？ | 任务状态/失败重试、字幕仲裁质量、high-res tile、小字 OCR、时间定位、智能总结章节闭环、内容素材 citation。 |
| 最不该继续做什么？ | 整体搬 vsummary/BiliNote/VideoRAG/MovieChat/VLM 项目的主架构。 |

## 已经基本吸收完的外部模块

| 来源 | 已吸收的关键能力 | VKP 落点 | 后续策略 |
| --- | --- | --- | --- |
| `alpha03123/vsummary` | OpenAI-compatible 文本网关、JSON repair、stage cache、run artifact、timestamp/citation UI、CUDA 检测 | `text_llm_gateway.py`、`stage_cache.py`、`run_artifact_registry.py`、`task_console.py`、`video_workbench.py`、`cuda_runtime.py` | 不搬 FastAPI/React/LlamaIndex/LanceDB；只继续补任务状态和 UI 细节 |
| `PrideWood/bilinote` | 字幕解析清洗、短句合并、转写校对 prompt、mind-map prompt、transcript editor、章节编辑体验 | `bilinote_transcript_tools.py`、`bilinote_summary_tools.py`、`transcript_correction_pack.py`、`transcript_editor.py`、`smart_summary_section_editor.py` | 不搬整套 React UI；继续吸收同屏编辑和转写修正体验 |
| VideoRAG | JSONL/SQLite chunk、检索单元、citation evidence | `video_rag_pack.py`、`video_rag_search.py`、`video_rag_http.py`、`smart_summary_chapters.py` | 默认保持本地 keyword/SQLite；vector 只做显式可选 adapter |
| VTimeLLM | moment grounding、时间定位、alignment audit | `video_moment_index.py`、`timeline_alignment_audit.py` | 继续用于 review_start / ASR start / frame time 的冲突审计 |
| MovieChat | 长视频 short memory / long memory 分层 | `long_video_memory_pack.py`、`smart_summary_input_pack.py` | 继续服务 smart-summary 输入，不单独做聊天系统 |
| Qwen/InternVL/LLaVA-OneVision | 图像缩放、压缩、多图/帧组输入、dynamic tiling | `vlm_preprocess.py`、`high_res_tile_plan.py`、`tile_result_import_builder.py`、`tile_result_merge.py` | 不嵌模型源码；只接 provider adapter 或本地服务 smoke |
| FunASR/SenseVoice/WhisperX | 本地 ASR、timestamp sidecar、ready gate、后处理路线 | `funasr_python_runner.py`、`asr_runner.py`、`asr_environment.py`、`transcript_sidecar.py`、`transcript_source_arbitration.py` | 继续补质量信号、说话人、标点、术语纠错 |
| Peepshow/VidClaude | 帧证据卡、批次复核、抽样评分 | `vision_review_queue.py`、`multimodal_sample_review.py`、`video_workbench.py` | 继续强化人审 UI 和质量指标，不把截图当唯一审核材料 |

## 继续复用的优先级

### P0：run artifact registry 全覆盖

复用来源：vsummary stage/task state、BiliNote 任务历史、Peepshow/VidClaude 批次报告。

继续落地：

- 所有长任务写 `runs/<task>/run.json` 和 `run.md`。
- `failed_items` 必须有具体失败原因、证据路径、下一步工具、重试命令。
- `task-console.html`、`video-workbench.html`、`subqueue-action-plan` 都读取同一套 run artifact。

停止条件：常见失败不需要回聊天记录翻命令；UI 和 JSON 里能直接看下一步。

### P0：ASR / 字幕仲裁质量信号

复用来源：BiliNote 字幕清洗、WhisperX word-level timestamp / diarization、SenseVoice emotion/event tags。

继续落地：

- `transcript_source_arbitration.py` 输出 `quality_summary`。
- 高置信术语纠错进入 corrected transcript。
- 低置信冲突进入 review pack。
- `smart-summary-input-pack` 和 `video-workbench` 显示字幕来源冲突和质量摘要。

停止条件：`smart-summary.md` 能区分可信术语、疑似错词和待人工复核内容。

### P1：high-res tile recovery 与 ebook/OCR 分工

复用来源：InternVL dynamic tiling、Qwen-VL 图像预处理、ebook_markdown_pipeline 图文解析。

继续落地：

- 整帧 ebook/OCR 返回空、wrapper-only、低信息量时，自动转入 tile plan 或多模态复核。
- 小字、表格、代码、软件界面截图走局部 tile evidence。
- tile 结果必须保留坐标、来源、置信度、review 状态。

停止条件：屏幕小字不再只是 `ocr empty`，而是有机器补救路径和人工复核路径。

### P1：时间定位 / VideoRAG / citation 跳转

复用来源：VideoRAG retrieval unit、VTimeLLM time grounding、vsummary timestamp seek/citation UI。

继续落地：

- `smart-summary.md` 的关键观点回链到 moment chunk。
- content candidate 回链到 transcript、visual evidence、review gap。
- `video-workbench` 搜索结果点击后跳视频时间、timeline row、候选素材。
- 支持按术语、工具名、方法、案例、结论查时间段和证据来源。

停止条件：不用重型向量库，也能完成本地定位、证据回跳和人工复核导航。

### P1：smart-summary 章节级质量闭环

复用来源：BiliNote 章节笔记、vsummary 分段总结、MovieChat long memory、VideoRAG citation digest。

继续落地：

- 每章独立生成、复核、安装。
- 每章保留 transcript、OCR/ebook、visual、temporal、review gap 的 citation digest。
- Codex、在线 LLM、本地 LLM 共用同一份 input pack。
- 质量门禁检查完整时长覆盖、避免 ASR 大段复制、避免只总结前几分钟。

停止条件：`smart-summary.md` 是成品阅读层，`knowledge-note.md` 是证据审计层，两者边界稳定。

### P2：本地 VLM serving smoke

复用来源：Qwen-VL OpenAI-compatible serving、InternVL dynamic tiling、LLaVA-OneVision 多图/短片段输入。

继续落地：

- 只读检查 provider 地址、模型名、单图/多图/帧组能力、JSON 输出稳定性。
- smoke 结果进入 `runs/local-vlm-serving-smoke/run.json`。
- `video-workbench` 显示本地 VLM plan/executed/failed 状态。

停止条件：用户能知道本机 VLM 是否可用、支持什么输入、下一步命令是什么；VKP 不把本地 VLM 变成默认硬依赖。

### P2：内容素材候选与智能总结双向链接

复用来源：vsummary clips/summary 输出、BiliNote 笔记导出、VideoRAG evidence path。

继续落地：

- 从 smart-summary section 跳到 content candidates。
- 从 content candidate 跳回章节、时间戳、证据帧、review rows。
- 支持素材类型过滤：`method`、`case`、`quote`、`visual_explainer`、`tool`、`workflow`。
- `content-asset-status` / `content-handoff-pack` 保留章节引用。

停止条件：下游内容线程可以按章节消费素材，但所有素材仍是 `review_required=true`、`publication_allowed=false`、`allowed_as_fact=false`。

## 新项目源码是否值得拉取的判断表

| 判断项 | 如果是 | 如果否 |
| --- | --- | --- |
| 是否有 VKP 没有的低耦合模块？ | 拉源码看具体文件 | 只记录项目名，不投入 |
| 是否能不引入重依赖单独复用？ | 做 adapter 或小模块 | 不进主线 |
| 是否改善当前瓶颈：总结质量、时间定位、小字 OCR、批次重试、人审评分？ | 排入 backlog | 暂停 |
| 是否要求替换 VKP 主架构？ | 默认拒绝整体迁移 | 可继续拆模块 |
| 是否绕过下载、云 API、人工复核边界？ | 不接入 | 可继续评估 |

## 不建议继续直接复用的方向

| 方向 | 不搬原因 | VKP 替代路线 |
| --- | --- | --- |
| vsummary 完整 FastAPI/React/LlamaIndex/LanceDB | 会形成第二套后端、第二套 UI、第二套索引 | 只吸收 provider、stage、run、citation、UI 交互模式 |
| BiliNote 完整 React UI | 工作流可借鉴，但 VKP 静态 bundle 更适合本地文件、MCP、OpenClaw | 在 `video-workbench.html` 复刻关键交互 |
| VideoRAG 重型 graph/vector 后端 | 个人工具维护成本高，依赖重 | 默认 JSONL/keyword/SQLite，vector 只做显式可选 |
| Qwen/InternVL/LLaVA 模型源码嵌入主流程 | 显存、依赖、模型部署复杂 | 统一 provider adapter / OpenAI-compatible / HTTP serving |
| 下载/字幕抓取后端 | VKP 边界是内容理解，不负责下载 | 继续交给 `video-download-orchestrator` 和 handoff |
| 默认全帧云多模态 | 成本、隐私、限流和失败恢复都不适合作为默认 | 本地抽帧/ebook/OCR/triage 先跑，云多模态只用于疑难点或显式全量模式 |

## 当前推荐开发顺序

1. 补齐 `screen-text-recovery`、`high-res-tile-plan`、`tile-result-import/merge` 的 failed item action fields。
2. 让 `task-console` 和 `video-workbench` 对这些 action fields 展示统一 retry/next action。
3. 给 ASR/字幕仲裁补 `quality_summary`，并接入 smart-summary input pack。
4. 继续增强 `smart-summary-section-workflow` 的章节级质量门禁和引用覆盖。
5. 把 content candidate、smart-summary section、VideoRAG moment search 做成更强互链。
6. 做本地 VLM serving smoke 的真实适配，但保持可选能力，不默认启用。

## 开发时的验收口径

每次吸收一个外部模块，至少验证：

- 是否有本地 CLI/MCP 或静态 UI 入口。
- 是否写入 run artifact 或可审计产物。
- 是否有失败项和 retry command。
- 是否保留 evidence path / time range / source channel。
- 是否不会自动下载、自动上传云、多模态全量外发、自动发布。
- 是否能被 `task-console.html`、`video-workbench.html` 或 `subqueue-action-plan` 看见。

## 相关文档

- `docs/external-code-reuse-readable-index-2026-07-06.md`
- `docs/external-code-reuse-current-module-map-2026-07-06.md`
- `docs/external-code-reuse-next-module-decisions-2026-07-06.md`
- `docs/external-open-source-reuse-module-inventory-2026-07-06.md`
- `docs/external-code-module-reuse-backlog-2026-07-04.md`
- `docs/external-code-reuse-remaining-modules-2026-07-05.md`
- `docs/vsummary-source-review.md`
- `docs/bilinote-pridewood-source-review.md`
- `docs/ai-video-open-source-survey-2026-07-04.md`
