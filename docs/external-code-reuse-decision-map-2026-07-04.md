# 外部视频 AI 项目代码复用决策地图

更新时间：2026-07-04 23:49:41 | Codex / GPT-5

## 目的

本文档是 VKP 当前“继续榨干外部开源项目可复用模块”的决策入口。它不重复每个源码审查细节，而是给后续开发一个清晰判断：

1. 哪些外部项目的核心价值已经被 VKP 吸收。
2. 哪些模块还值得继续复用。
3. 哪些方向看起来诱人，但不适合继续投入。
4. 后续新增外部项目时，应按什么口径拆模块。

相关详细文档：

- `docs/external-code-reuse-ledger-2026-07-04.md`
- `docs/external-code-module-reuse-backlog-2026-07-04.md`
- `docs/external-project-reuse-implementation-2026-07-04.md`
- `docs/vsummary-source-review.md`
- `docs/bilinote-pridewood-source-review.md`
- `docs/ai-video-open-source-survey-2026-07-04.md`
- `docs/smart-summary-best-practices.md`

## 当前结论

VKP 不需要寻找一个“替代 VKP 的完整开源项目”。目前最有效路线是继续拆分复用局部能力：

- vsummary：任务状态、阶段缓存、provider gateway、视频跳转体验。
- BiliNote：字幕/转写清洗、课程笔记组织、视频 + transcript + summary 工作台交互。
- VideoRAG / MovieChat / VTimeLLM：长视频分层记忆、视频片段检索、时间定位和 evidence citation。
- Qwen-VL / InternVL：本地 VLM 输入预处理、高分辨率 tile、小字/表格/界面细节补救。
- WhisperX / FunASR / SenseVoice：ASR 时间戳、术语纠错、标点、说话人、置信度。

当前 VKP 已经不是“没复用开源项目”的状态，而是已经吸收了一批低耦合模块。剩下值得继续做的不是大搬家，而是把这些模块接得更深、更稳定、更好用。

## 外部项目价值消化状态

| 来源 | 已吸收价值 | 已落地 VKP 模块 | 还值得继续拿 | 消化状态 |
| --- | --- | --- | --- | --- |
| `alpha03123/vsummary` | 文本 LLM gateway、stage cache、run artifact、视频 seek/citation、Windows CUDA 经验 | `text_llm_gateway.py`、`stage_cache.py`、`run_artifact_registry.py`、`cuda_runtime.py`、task console 任务历史 | 更细的 batch progress、取消/恢复、section rerun UI | 主要价值已吸收，剩余是 UI/任务体验深化 |
| `PrideWood/bilinote` | 字幕解析清洗、转写编辑、课程笔记/脑图 prompt、视频工作台交互 | `bilinote_transcript_tools.py`、`bilinote_summary_tools.py`、`transcript_correction_pack.py`、`transcript_editor.py`、`smart_summary_section_editor.py` | 主工作台一体化、转写多源仲裁 UI、章节编辑联动 | 代码模块已吸收一半以上，UI 思路还可继续榨 |
| `VideoRAG` | 视频 chunk schema、证据检索、片段可追溯问答 | `video_rag_pack.py`、`video_rag_search.py`、`video_rag_http.py`、`video_moment_index.py` | 多粒度 chunk、可选向量后端、query -> evidence -> summary citation | 不适合搬重后端，适合继续抽数据结构 |
| `MovieChat` | 长视频 short/long memory 分层 | `long_video_memory_pack.py` | summary 章节生成更深使用 long memory | 核心思想已吸收，不建议接模型源码 |
| `VTimeLLM` | temporal grounding、moment start/end 评价 | `video_moment_index.py`、`timeline_alignment_audit.py`、section citations | 时间戳置信度评分、review jump 纠偏建议 | 核心评价思路已吸收，可继续做质量评分 |
| Qwen-VL / qwen-vl-utils | 图片/视频输入预处理、帧组封装、OpenAI-compatible payload 参考 | `vlm_preprocess.py`、vision provider preprocess | 本地 VLM 服务适配、temporal 多帧 payload 统一 | 预处理价值已吸收，模型部署后置 |
| InternVL | dynamic tiling、高分辨率局部图像理解 | `high_res_tile_plan.py`、`tile_result_import_builder.py`、`tile_result_merge.py` | tile review UI、真实 OCR/VLM 输出 parser 扩展 | 小字补救方向值得继续深化 |
| WhisperX / FunASR / SenseVoice | VAD、时间戳、ASR 置信度、说话人、中文识别 | `asr_runner.py`、`funasr_python_runner.py`、`transcript_sidecar.py`、`cuda_runtime.py` | 多源字幕/ASR 仲裁、标点、术语词典、说话人 | ASR 主链已接，纠错/仲裁还需深化 |
| Peepshow / VidClaude 类帧报告 | frame grid、状态 badge、视觉证据对照 | `vision_review_queue.py`、task console 队列、review 页面局部能力 | 疑难点批次 UI、失败重试、人工标注体验 | 只需吸收交互，不需要搬主流程 |

## 还值得继续复用的代码模块

### P0：字幕 / ASR / 平台字幕多源仲裁

目标：生成更可靠的 `corrected-transcript.json`，让 `smart-summary.md` 和 `full-transcript.md` 都建立在更干净的文字基础上。

可复用来源：

- BiliNote 字幕清洗和 transcript 编辑工作流；
- WhisperX / FunASR 的 segment 时间戳与置信度；
- VKP 已有 `term_resolution.py` 的 OCR/视觉/字幕/ASR 术语投票；
- 平台字幕或 VDO handoff 中的字幕 sidecar。

建议落地：

- 新增 `transcript-source-arbitration`。
- 输入：本地 ASR、平台字幕、自带字幕、corrected transcript、OCR/ebook、视觉理解、术语表。
- 输出：
  - `transcript-source-arbitration.json`
  - `transcript-source-arbitration.md`
  - `source-arbitrated-transcript.json/srt/md`
- 高置信纠错进入最终人类可读文件。
- 低置信冲突进入 review pack，不静默覆盖。

### P0：主工作台一体化

目标：把现在分散的 `task-console.html`、`review.html`、`transcript-editor.html`、`smart-summary-section-editor.html` 变成同一套视频知识工作台的不同面板。

可复用来源：

- BiliNote 的视频 + 字幕 + 笔记联动；
- vsummary 的章节点击跳转；
- Peepshow/VidClaude 的 frame grid 和证据状态。

建议落地：

- 左侧任务队列；
- 中间视频播放器 + 时间轴；
- 右侧 transcript / OCR / 多模态 / summary section / 人工修正；
- 保持静态 HTML bundle 可打开；
- API key 设置页只持久化非 secret provider profile，secret 仍走 env 或手动输入。

### P0：批次队列和重试体验

目标：让 ebook、tile、多模态、smart-summary、ASR 都能像一个生产队列一样显示进度、失败和重试。

可复用来源：

- vsummary run state / stage cache；
- Peepshow frame report；
- BiliNote task history。

建议落地：

- 每个长任务必须有 `runs/<task>/run.json/md`。
- 每个失败项必须有 `failed_items[]`、`retry_command`、`evidence_path`。
- UI 支持设置 batch size、batch count、失败重试、跳过/人工接管。

### P1：小字和图文结构化闭环

目标：ebook/OCR 整帧失败时，不再停在 `ocr_text_empty`，而是自动进入 tile/crop/局部识别/人工复核路径。

可复用来源：

- InternVL dynamic tile；
- RapidOCR/PaddleOCR 输出结构；
- ebook_markdown_pipeline 作为图文型截图主通道。

建议落地：

- `run-visual-structure` 继续优先调用 `ebook_markdown_pipeline`。
- wrapper-only / 空结果 / 低信息量结果自动生成 `high_res_tile_plan`。
- `tile-result-import-build` 继续扩展真实 OCR/VLM JSON parser。
- `tile-result-merge` 只回填高置信文字，低置信进入 review pack。

### P1：smart-summary 章节级质量闭环

目标：让 `smart-summary.md` 真正变成“得到大脑式智能总结”，而不是证据流水账或规则草稿。

可复用来源：

- BiliNote 课程章节/脑图结构；
- vsummary 分段生成和 provider gateway；
- MovieChat long memory；
- VideoRAG citations。

已落地：

- `smart-summary-section-workflow`
- `smart-summary-section-editor`
- `smart-summary-section-apply`
- VideoRAG/moment citations 注入

还可继续：

- section-level Codex/LLM 重写队列；
- 章节级质量评分；
- corrected transcript / long memory / RAG chunks / OCR evidence 的统一输入包；
- section citation 在最终 `smart-summary.md` 里更自然呈现。

### P1：视频 RAG 多粒度检索

目标：让用户能问“这个视频哪里讲某个工具/术语/案例/步骤”，并跳回证据片段。

可复用来源：

- VideoRAG 的 chunk schema 和 retrieval pipeline；
- VTimeLLM 的 moment grounding；
- VKP 已有 timeline 和 evidence paths。

建议落地：

- 拆成 transcript chunks、visual chunks、chapter chunks、review-gap chunks、content-asset chunks。
- 默认本地 JSONL/词法检索。
- 可选接向量后端，但不默认引入。

### P2：本地 VLM adapter 能力矩阵

目标：让 Qwen2.5-VL、InternVL、LLaVA-OneVision 等本地模型能作为可选 provider，而不是混入主流程。

可复用来源：

- Qwen-VL OpenAI-compatible serving；
- InternVL dynamic tile；
- LLaVA-OneVision 多帧输入模式。

建议落地：

- `local-vlm-serving-smoke` 输出显存、模型、输入规格、是否支持多图/视频片段。
- 和云 API 使用同一个 `vlm_preprocess.py`。
- 只在用户显式启动本地服务后调用。

## 不再建议继续榨的方向

| 方向 | 原因 |
| --- | --- |
| 整体搬 vsummary 后端 | 与 VKP 现有 CLI/MCP/OpenClaw/static bundle 重叠，维护成本高 |
| 整体搬 BiliNote React App | UI 值得学，但整体搬会破坏 VKP 当前静态 bundle 和 evidence 结构 |
| 把 VideoRAG 图数据库/向量数据库作为默认依赖 | 太重，默认个人工具不应先引入服务依赖 |
| 把 Qwen/InternVL/LLaVA 源码嵌进 VKP | 环境和模型生命周期复杂，应该保持 provider/adapter 边界 |
| 在 VKP 内重写下载、登录、平台字幕抓取 | 下载/平台访问归 VDO，VKP 只接收 handoff manifest 和本地 sidecar |
| 默认把大量帧发给云多模态 | 本地抽帧可以密，云视觉仍应疑难点优先、小批次、显式执行 |

## 新外部项目的复用判断清单

遇到新的 AI 视频项目时，先按以下顺序判断：

1. 是否有低耦合模块能直接复用。
2. 是否能输出 VKP bundle 内的 JSON/Markdown artifact。
3. 是否能保留证据路径和时间戳。
4. 是否能通过 CLI/MCP 或静态 UI 接入。
5. 是否不要求默认启动长期服务。
6. 是否不默认调用云模型、不上传大量帧。
7. 是否不绕过人工审核、事实核查、发布边界。

只要一个项目主要价值是“完整 App 壳、登录下载、重模型服务、发布系统”，就不要整体搬。只拆里面的数据结构、UI 交互、任务状态、prompt/schema、adapter 边界。

## 推荐下一步实现顺序

1. `transcript-source-arbitration`：先把 ASR/平台字幕/自带字幕/OCR/术语表综合成更可靠的 corrected transcript。
2. 主工作台一体化：把视频、时间轴、转写、OCR、多模态、summary section 合到一个静态页面。
3. 批次队列重试增强：所有长任务都能显示 batch size、总批数、失败索引和重试按钮。
4. 小字 tile 闭环增强：ebook 空结果自动进入 tile plan/import/merge/review。
5. smart-summary section LLM/Codex 重写流程深化：让最终总结层真正吃 corrected transcript、long memory、RAG citations。
6. 本地 VLM adapter smoke：为后续离线多模态做环境和质量基线。

## 当前状态一句话

外部开源项目的主要可复用价值已经被拆出大半；接下来最值得做的不是继续找“更大的项目”，而是把已吸收的模块在 VKP 内部串成更可靠的生产闭环：更准的转写、更强的工作台、更稳的批次队列、更细的视觉证据、更好的智能总结。
## Update - 2026-07-05 00:03:35 | Codex / GPT-5

`transcript-source-arbitration` is now implemented as the first P0 module from this decision map.

Decision status change:

- “字幕 / ASR / 平台字幕多源仲裁” moves from recommended next implementation to landed v1.
- The next most valuable reuse target is now the unified video workspace: merge task console, review page, transcript editor, smart-summary section editor, and evidence panels into one static operator surface.
- Batch queue/retry work remains co-priority because every long-running local branch now has more artifacts to show and retry.

## Update - 2026-07-05 20:10:50 | Codex / GPT-5

`docs/external-code-reuse-remaining-modules-2026-07-05.md` is now the compact execution map for remaining external-code reuse modules.

Decision status:

- Already absorbed enough: provider gateway, stage cache, run registry, transcript cleanup, transcript editor, smart-summary section editor, moment citations, high-res tile plan/import/merge.
- Keep building: unified video workbench, batch retry UI, transcript arbitration UI/post-processing, long-video summary input pack, video RAG/time grounding, local VLM adapter smoke, human sampling score UI.
- Avoid: full app migration, default vector DB, vendored model repos, VKP-side download/login/platform scraping, default cloud multimodal full-frame processing.

Use the remaining-modules document before adding a new open-source dependency or copying code from another video AI project.
## Update - 2026-07-05 21:34:58 | Codex / GPT-5

### 外部项目可复用模块的当前收束结论

本轮复盘后的判断是：VKP 已经不缺“找一个更完整的视频总结项目来替换自己”的方向，真正还值得继续榨取的是低耦合模块，并且必须落到现有 bundle / timeline / evidence / review / export 数据结构里。

#### 已经基本榨干的模块

| 来源 | 已吸收模块 | VKP 当前落点 | 继续搬运价值 |
| --- | --- | --- | --- |
| `alpha03123/vsummary` | LLM gateway、stage cache、run/artifact registry、视频时间戳跳转、CUDA runtime 经验 | `text_llm_gateway.py`、`stage_cache.py`、`run_artifact_registry.py`、`video_workbench.py`、`cuda_runtime.py` | 低。后续只继续吸收 UI 任务体验，不搬后端 |
| `PrideWood/bilinote` | 字幕清洗、转写纠错 prompt、脑图/课程笔记 prompt、视频笔记工作台交互 | `bilinote_transcript_tools.py`、`bilinote_summary_tools.py`、`transcript_correction_pack.py`、`transcript_editor.py`、`smart_summary_section_editor.py` | 中。UI 联动和 transcript review 体验还能继续吸收 |
| `VideoRAG` | 视频片段 chunk、证据检索、本地 moment search | `video_moment_index.py`、`video_rag_pack.py`、`video_rag_search.py`、`video_workbench.py` | 中。继续做多粒度 chunk 和 summary citation，不默认引入向量库 |
| `MovieChat` | 长视频 short/long memory 分层 | `long_video_memory_pack.py`、smart summary input | 中。继续让智能总结更深消费 long memory |
| `VTimeLLM` | 时间定位、片段 start/end 评价、moment grounding | `timeline_alignment_audit.py`、`video_moment_index.py`、review jump 逻辑 | 中。继续做时间戳置信度和审核跳转纠偏 |
| Qwen-VL / InternVL / LLaVA-OneVision | 多图/短帧组输入、图像预处理、高分辨率 tile 思路、本地 VLM provider 边界 | `vlm_preprocess.py`、`high_res_tile_plan.py`、`tile_result_import_builder.py`、`tile_result_merge.py`、`local_vlm_server_adapter.py` | 中。继续强化 adapter smoke 和 tile parser，不 vendoring 模型源码 |
| FunASR / SenseVoice / WhisperX / faster-whisper | 本地 ASR、时间戳、VAD、CUDA/CPU runtime 判断、多源转写基础 | `funasr_python_runner.py`、`asr_runner.py`、`transcript_sidecar.py`、`transcript_source_arbitration.py` | 中。继续做标点、术语、说话人和多源仲裁 |
| Peepshow / VidClaude 类项目 | 帧证据卡、失败 badge、人工抽样评价 | `vision_review_queue.py`、`multimodal_sample_review.py`、`video_workbench.py`、task console queue | 中。继续做人工评分闭环和批次失败重试 UI |

#### 还值得继续复用的代码模块

这些不是“再找项目”，而是继续把已发现项目里尚未完全落地的局部能力实现到 VKP：

1. **run registry 覆盖所有真实执行入口**
   - 来源：vsummary 的 task/stage artifact 思路。
   - 目标：ebook batch、多模态 batch、temporal batch、tile merge、smart-summary section workflow 都登记 `run_type/status/failed_items/retry_command/artifacts`。
   - 验收：workbench 处理队列能看到每个长任务的状态、失败项、重试命令。

2. **工作台内置转写仲裁差异视图**
   - 来源：BiliNote transcript editor + VKP `transcript-source-arbitration`。
   - 目标：在 `video-workbench.html` 里直接看 ASR、平台字幕、自带字幕、纠正版、术语冲突和证据来源。
   - 验收：高置信纠错进入最终 transcript；低置信冲突进入 review pack。

3. **smart-summary input pack 证据化**
   - 来源：BiliNote 章节总结、vsummary 分段生成、MovieChat long memory、VideoRAG citations。
   - 目标：每个智能总结章节明确引用完整 ASR、纠正版 transcript、OCR/ebook、vision、moment evidence、review gaps。
   - 验收：`smart-summary.md` 覆盖全片，且不再像规则草稿或证据流水账。

4. **tile / crop / ebook 失败闭环**
   - 来源：InternVL dynamic tiling、Qwen image preprocess、ebook_markdown_pipeline。
   - 目标：ebook wrapper-only / 空结果 / 低信息量结果自动进入 tile/crop、多模态或人工审核，而不是假装 OCR 成功。
   - 验收：小字和图文 blocker 有明确机器重试路径或人工复核路径。

5. **人工抽样评分与多模态收益报告**
   - 来源：Peepshow/VidClaude 证据卡和人工评分体验。
   - 目标：抽样比较无多模态、有多模态、ebook/OCR、人工标注对最终人类可读文件的准确率影响。
   - 验收：输出 `multimodal-impact-report.md`，能回答“多模态到底改善多少”。

6. **本地 VLM adapter smoke 矩阵**
   - 来源：Qwen-VL / InternVL / LLaVA-OneVision serving 形态。
   - 目标：不把模型源码塞进 VKP，只检测本地 OpenAI-compatible / HTTP 服务是否能跑单图、多图、短帧组、JSON 输出。
   - 验收：`local-vlm-serving-smoke` 能给出可用性、显存/模型、输入规格、失败原因。

#### 不再建议投入的复用方向

- 不整体搬 vsummary 的 FastAPI/React/LlamaIndex/LanceDB 后端。
- 不整体搬 BiliNote 的 React App。
- 不默认启动 VideoRAG 图数据库、向量数据库或长期服务。
- 不把 Qwen/InternVL/LLaVA 模型源码 vendoring 到 VKP。
- 不把 VDO 的下载、登录、平台字幕抓取职责并入 VKP。
- 不默认把大量帧发送到云多模态模型；本地抽帧可以密，云视觉仍只用于疑难点、小批次、显式执行。

### 当前开发优先级

1. 先补所有实际执行入口的 `register_bundle_run`，让工作台队列真实可信。
2. 再把转写仲裁差异视图放进 `video-workbench.html`。
3. 然后让 `smart-summary-input-pack` 明确记录每章使用的 transcript/OCR/vision/moment evidence。
4. 接着补 tile/crop/ebook 失败闭环。
5. 最后做人工抽样评分和 `multimodal-impact-report.md`。

## Update - 2026-07-15 10:20:35 +08:00 | Codex / GPT-5

### MediaKit CLI 决策入口

MediaKit CLI 的 VKP 专用源码级复用登记见 `docs/mediakit-cli-vkp-reuse-registry-2026-07-15.md`。

当前决策：只把能力注册、异步任务状态机、错误归一化、上传前处理和安全产物写入作为可复用模块；把 `segment-scenes` / `analyze-video-storyline` 等作为候选远程媒体服务能力。不得把 MediaKit 伪装成 LiteLLM deployment，不得复用自动 local/cloud fallback，也不得在单独 allowlist、consent v2、计费确认和操作者授权前执行真实上传。

### videocut-kit 剪辑交接决策

将 `snap_boundaries`、能量静音恢复和 artifact validation 适配为 VKP 本地确定性后处理；将 Timeline/Smart Summary 转为 `StoryboardScene` 候选，并只接受人工确认的偏好差异证据。

已实现于 `video_edit_review_pack.py`；状态继续登记到 VKP run registry，审核继续使用现有 Workbench，最终媒体处理继续使用既有单一 FFmpeg/render 出口。禁止复制上游状态机、审核服务或自动执行创作判断。FCPXML 仅在出现真实编辑器往返验收样本后再做薄适配。
