# 外部视频 AI 项目可复用代码模块 Backlog

更新时间：2026-07-04 23:59:00 | Codex / GPT-5

## 目的

本文档记录 VKP 继续从外部开源项目中“榨干”可复用代码模块的优先级。原则不是整体搬运项目，而是拆出低耦合、能增强 VKP 主流程的局部能力：

- VKP 继续负责：本地视频知识化、ASR/OCR/ebook、多模态复核、timeline、证据链、review bundle、human-readable exports。
- 外部项目只作为模块来源：任务管理、UI 交互、字幕清洗、长视频总结、视频 RAG、本地 VLM adapter、视觉预处理。
- 下载后端仍归 `video-download-orchestrator`；VKP 不吸收下载逻辑。
- 云 API 和在线多模态仍走 preflight/确认/小批次策略，不默认大规模外发帧。

## 当前已吸收的模块

| 来源项目 | 已吸收模块 | VKP 落地文件/能力 |
| --- | --- | --- |
| `alpha03123/vsummary` | OpenAI-compatible text gateway、JSON repair、stage cache、atomic artifact write、Windows CUDA DLL discovery、video seek/citation 交互 | `text_llm_gateway.py`、`stage_cache.py`、`cuda_runtime.py`、task console seek/citation |
| `PrideWood/bilinote` | SRT/VTT/plain transcript 解析、字幕清洗、短句合并、转写校对 prompt、mind-map 分块 prompt、transcript editor 工作流 | `bilinote_transcript_tools.py`、`bilinote_summary_tools.py`、`transcript_correction_pack.py`、`transcript_editor.py` |
| `VideoRAG` | 轻量 segment/chunk 检索、JSONL evidence chunks、local HTTP search service | `video_rag_pack.py`、`video_rag_search.py`、`video_rag_http.py` |
| MovieChat / long-video memory 思路 | 长视频分层 memory pack、短/长记忆分离 | `long_video_memory_pack.py` |
| VTimeLLM / temporal grounding 思路 | moment index、时间段定位、query-to-moment 基础结构 | `video_moment_index.py` |
| Qwen / InternVL | 本地 VLM adapter plan、OpenAI-compatible serving smoke | `local_vlm_server_adapter.py` |

## 还值得继续复用的代码模块

### P0：vsummary 任务流水线与 artifact registry

价值：最高工程收益。VKP 已经有 ASR、ebook、OCR、多模态、智能总结、人工审核多条长任务链，当前最缺的是统一的任务状态、失败恢复、批次重试和产物注册。

可复用模块：

- generation use case 的阶段化任务模型；
- staging directory -> stage cache -> atomic commit；
- artifact store 的 JSON/Markdown 成对落盘；
- cancellation/progress callback 的数据结构；
- UI 读取 run state 的字段设计。

建议 VKP 落地：

- 新增统一 `run_artifact_registry` 或扩展现有 `stage_cache`；
- 给 ebook batch、多模态 batch、smart-summary LLM chunk、ASR rerun 接统一 run id；
- 每个 run 输出 `run.json`、`run.md`、`artifacts[]`、`failed_items[]`、`retry_command`；
- task console 显示批次进度、失败原因、重试按钮。

边界：

- 不搬 vsummary 的完整 FastAPI/React/LlamaIndex/LanceDB 栈；
- 不替换 VKP 现有 CLI/MCP/OpenClaw/static bundle 契约。

### P0：BiliNote UI 的任务历史、转录编辑和视频联动

价值：最高用户体验收益。VKP 已有 task console 和 review.html，但还没有达到 BiliNote 那种“视频、字幕、笔记、重生成”一体化手感。

可复用模块：

- 任务历史列表；
- 视频播放时间与 transcript row 高亮；
- 点击 transcript / mind-map node 跳转视频；
- 本地 API 设置页和 localStorage 持久化；
- transcript 编辑后重新保存和重新生成笔记。

建议 VKP 落地：

- 把 task console 与 review 页面进一步合并，形成单个“视频工作台”；
- 左侧任务/批次队列，中间视频和时间轴，右侧 transcript/视觉证据/总结草稿；
- transcript editor 直接嵌入主页面，不再只是独立 HTML；
- API 设置页持久化 provider profile，但只保存非 secret 配置，secret 仍来自 env 或用户显式输入。

边界：

- 不整体搬 React App；
- 保持静态 bundle 可打开；
- 需要后端时只用现有 VKP bridge/CLI/MCP，不引入第二套长期服务。

### P1：VideoRAG 的多粒度 chunk 和可替换检索后端

价值：长视频问答和定位能力。当前 VKP 已有轻量词法检索，但还没有真正的多粒度 RAG 和可替换向量后端。

可复用模块：

- chunk splitter；
- caption/transcript/evidence 多源 chunk schema；
- query -> segment ranking；
- storage abstraction；
- graph/vector backend 的接口层。

建议 VKP 落地：

- 把 `video-rag-chunks.jsonl` 扩展为多层：
  - transcript chunks；
  - visual evidence chunks；
  - chapter chunks；
  - content asset chunks；
  - review gap chunks。
- 增加 optional vector backend adapter，但默认仍用本地 JSONL/词法检索；
- 支持“找某个术语出现在哪些时间段”“这段视频讲了哪些工具”“哪些结论缺视觉证据”。

边界：

- 不默认引入 graph/vector DB 重依赖；
- 不让 RAG 取代 evidence extraction，只做下游检索和问答。

### P1：Qwen-VL / qwen-vl-utils 视频帧预处理

价值：本地多模态输入标准化。VKP 现在已有 provider/adapter，但还缺成熟的视频帧读取、缩放、多图封装、fps/num_frames 控制。

可复用模块：

- image/video loading；
- dynamic resize；
- frame list as video input；
- fps / num_frames 采样参数；
- OpenAI-compatible message payload 组装参考。

建议 VKP 落地：

- 新增 `vlm_preprocess.py`；
- 给 `temporal_frame_groups` 和 `run_multimodal_frame_analysis` 共用图像压缩/缩放/帧组封装；
- 支持本地 VLM 和云 API 使用同一套 image payload planning；
- 对长视频疑难片段只送 5-12 帧，而不是整段视频。

边界：

- 不把 Qwen 模型仓库导入主流程；
- 本地模型继续通过 HTTP/OpenAI-compatible 或明确 subprocess runner 调用。

### P1：InternVL dynamic tiling / high-res frame 处理

价值：补 VKP 当前最弱的“小字、表格、软件界面、PPT 局部细节”。

可复用模块：

- dynamic image tiling；
- high-resolution crop；
- tile-level prompt；
- tile result merge。

建议 VKP 落地：

- ebook/整帧 OCR 返回空、wrapper-only、低信息量时，自动进入 `high_res_tile_plan`；
- 对 PPT、表格、软件界面截图切 tile 后送本地 VLM 或人工审核；
- 每个 tile 保留证据路径和坐标，方便 audit/review。

边界：

- 不用 tile 伪装成 OCR 成功；
- tile 结果也要进入 confidence/review 机制。

### P1：VTimeLLM 时间定位评价模块

价值：解决“时间戳对不上”“审核页面跳到说完而不是开始”等质量问题。

可复用模块：

- temporal grounding 的 start/end 评价；
- temporal IoU；
- query-to-moment 验证；
- predicted segment 与 ASR segment/frame window 的重叠检查。

建议 VKP 落地：

- 新增 `timeline_alignment_audit`；
- 检查每个 review target 的 `review_start` 是否来自 ASR segment start；
- 对 frame time、ASR start/end、青龙打标时间、章节时间做冲突报告；
- 在 review UI 显示“时间戳来源”和“可信度”。

边界：

- 青龙打标器可以提供章节/标签/画面变化信息，但 ASR 句子起点仍优先来自 ASR sidecar。

### P2：WhisperX / FunASR / SenseVoice 后处理能力

价值：提高纠正版逐字稿和最终 smart-summary 的输入质量。

可复用模块：

- word-level alignment；
- VAD chunking；
- speaker diarization；
- punctuation restoration；
- domain term dictionary；
- ASR confidence + segment quality scoring。

建议 VKP 落地：

- `normalized-transcript.json` 保留原始 ASR；
- `corrected-transcript.json` 由术语仲裁、平台字幕、OCR/ebook、多模态证据共同生成；
- smart-summary 默认读取 corrected transcript；
- full-transcript 同时展示原文和纠正状态。

边界：

- 高置信纠错可以进入最终人类可读文件；
- 低置信纠错只能进入 review pack，不能静默覆盖。

### P2：Peepshow / VidClaude 风格帧报告 UI

价值：让多模态/ebook/人工审核批次更可视化。

可复用模块：

- frame grid；
- per-frame status badge；
- OCR / VLM / human note 对照；
- failed/retry/accepted filters；
- evidence path preview。

建议 VKP 落地：

- 在 task console 增加“疑难点队列”页；
- 每个疑难点展示 ASR、OCR/ebook、多模态、人工状态；
- 支持批量重试和单条重试；
- 显示 batch size、total batches、failed indexes。

边界：

- 不把截图当作唯一审核材料；审核页仍应支持视频播放和时间戳跳转。

### P2：BiliNote / vsummary 内容导出交互

价值：改善 smart-summary 和内容素材卡的编辑/确认。

可复用模块：

- summary section rerun；
- chapter card edit；
- export preview；
- mind-map node export；
- citation-aware markdown renderer。

建议 VKP 落地：

- `smart-summary.md` 旁边生成 editable draft state；
- section-level re-generation；
- 每个关键观点保留证据 citation；
- 内容素材卡和朋友圈素材包只输出 `needs_review_inspiration`，不自动发布。

边界：

- 内容素材不是事实结论；
- publication_allowed 仍必须 false。

## 不建议继续投入的整体复用方向

| 方向 | 原因 |
| --- | --- |
| 整体迁移 vsummary 后端 | 与 VKP 现有 CLI/MCP/OpenClaw/static bundle 架构重复，维护成本高 |
| 整体迁移 BiliNote React UI | UI 好，但会打断当前静态 bundle、review.html、task console 的渐进路线 |
| 直接运行 VideoRAG 全套 graph/vector 后端 | 依赖重，当前收益不如先做 JSONL/可替换 adapter |
| 把 Qwen/InternVL/LLaVA 模型代码嵌进 VKP 主流程 | 本地环境复杂，应该先通过 provider/adapter 边界接入 |
| 在 VKP 里重写下载/字幕抓取后端 | 下载和平台访问归 VDO，VKP 只接收 handoff manifest |

## 推荐下一阶段顺序

1. **任务产物管理先行**：把 vsummary-style run/artifact registry 接到 ebook batch、多模态 batch、smart-summary LLM chunk。
2. **主 UI 合并**：吸收 BiliNote 的视频 + transcript + review + summary 工作台交互。
3. **小字视觉增强**：实现 InternVL-style high-res tile plan，作为 ebook/OCR 空结果后的补救分支。
4. **本地 VLM 输入标准化**：实现 Qwen-style `vlm_preprocess.py`，统一本地/云多模态帧组 payload。
5. **时间轴质量审计**：实现 VTime-style `timeline_alignment_audit`，解决审核时间戳错位。
6. **RAG 查询增强**：把 VideoRAG local search 从词法检索扩展为多粒度 chunk + optional vector backend。

## 验收标准

下一轮真正“榨干”外部模块，不应只增加文档，应至少满足：

- 新增 CLI/MCP 入口或 UI 区块；
- 有 bundle 内可读产物；
- 有机器可读 JSON；
- 有失败/重试状态；
- 不写入 secret；
- 不默认外发大量帧；
- 新增或更新测试覆盖。

## Update - 2026-07-04 21:36:27 | Codex GPT-5

### 当前剩余可复用模块判断

本次复盘后的结论：已发现的外部项目并不是要继续“整体搬家”，而是继续把还没落到 VKP 主流程里的低耦合能力拆成可执行模块。当前优先级如下。

| 优先级 | 模块 | 参考来源 | 应进入 VKP 的形态 | 当前状态 |
| --- | --- | --- | --- | --- |
| P1 | 高分辨率 tile / 小字补救 | InternVL dynamic tiling、Qwen-VL 图像预处理 | `high_res_tile_plan`：对 ebook/OCR 空结果、wrapper-only、低信息量截图生成 tile 证据包，后续交给本地 VLM/云 VLM/人工复核 | 基础版已落地：CLI/MCP、tile 写图、run registry、task console 可见；仍可继续接 VLM/tile result merge |
| P1 | 多模态输入预处理统一层 | Qwen-VL utils、InternVL 多图输入 | `vlm_preprocess.py`：统一 resize、压缩、frame group、tile payload，供火山/Gemini/OpenAI-compatible/本地 VLM 共用 | 基础版已落地：semantic/temporal/provider smoke 共用本地 resize/compress/probe metadata；tile payload merge 仍待接 |
| P1 | 时间轴对齐审计 | VTimeLLM temporal grounding | `timeline_alignment_audit`：检查 ASR start/end、抽帧时间、青龙打标时间、review_start 是否冲突 | 基础版已落地：CLI/MCP、JSON/Markdown 报告、run registry、task console “时间错位”指标和推荐命令；仍可继续接 review.html badges/preview 修复建议 |
| P1 | 疑难点队列可视化/重试 | vsummary run registry、Peepshow/VidClaude frame report | 在 task console 中展示 triage 队列、批次大小、失败项、重试命令 | 部分落地，仍可增强 |
| P2 | 多粒度 RAG 检索增强 | VideoRAG | 扩展 `video-rag-pack` 为 transcript/visual/chapter/review-gap/content-asset 多层 chunk，并保留 optional vector backend | 基础版已落地，向量后端未接 |
| P2 | 逐字稿后处理强化 | BiliNote、WhisperX、FunASR/SenseVoice | `corrected-transcript.json` 作为 smart-summary 默认输入；术语、标点、说话人、置信度单独记录 | 部分落地 |
| P2 | 内容编辑/重生成交互 | BiliNote、vsummary | smart-summary section 级编辑/重生成、citation-aware markdown preview | 未完整落地 |

### 决策边界

- 继续复用代码时，优先复制或改写“小函数/小模块/数据结构/交互模式”，不吸收外部项目的完整后端。
- `video-download-orchestrator` 仍负责下载和平台来源；VKP 不接下载后端。
- `ebook_markdown_pipeline` 仍是图文/文档截图解析主通道；high-res tile 是 ebook/OCR 失败后的补救证据层，不是替代 OCR 的新 OCR 引擎。
- 在线多模态继续只处理疑难点或用户明确允许的大批量；本地抽帧、tile、RAG、时间轴审计可以更充分执行。
- 所有新增模块必须有 CLI/MCP 或 WebUI 可见入口，必须写入 bundle 内 JSON/Markdown 产物，并且进入 run/artifact registry 或对应状态报告。

### 下一步建议

1. `high_res_tile_plan` 基础版已落地；下一步把 tile result merge 接入多模态/人工审核结果。
2. `vlm_preprocess.py` 基础版已落地；下一步把 high-res tile 和 VLM result merge 也接入同一套 payload 规划。
3. `timeline_alignment_audit` 已接入 task console；下一步把审计结果接到 `review.html` 的时间戳 badge 和 preview-only 修复建议里。
4. 继续增强 task console，把疑难点、tile、ebook、多模态、smart-summary、timeline audit run 的失败项、批次大小和 retry command 做成更完整的可视化队列。



## Update - 2026-07-04 22:14:28 | Codex GPT-5

### “还有哪些值得复用代码模块”的当前答案

从已审查的 `vsummary`、`BiliNote`、VideoRAG / MovieChat / VTimeLLM / Qwen-VL / InternVL 等项目看，VKP 目前不缺“再搬一个完整项目”，缺的是把外部项目里成熟的小模块继续接到现有证据链和 UI。当前仍值得继续复用的代码模块按收益排序如下。

| 优先级 | 还值得复用的模块 | 参考项目 / 思路 | VKP 应落地成什么 | 为什么值得做 |
| --- | --- | --- | --- | --- |
| P0 | Review UI 的时间轴对齐提示与修复建议 | VTimeLLM temporal grounding、BiliNote 视频时间轴 UI | `review.html` 中给每条待审 item 增加时间错位 badge、ASR 起点/抽帧时间/打标时间对比、preview-only 修复建议；`prepare-review-session` 增加 `timeline_alignment_issue` 分组 | 直接解决人工审核“点进去时间不对”的痛点，且不需要新模型 |
| P0 | 统一任务队列和失败重试 UI | vsummary task status、BiliNote 任务面板、Peepshow frame report | task console 的 run registry 继续扩展为可见队列：ebook batch、tile、vision queue、smart-summary、timeline audit 都显示状态、失败项、重试命令、批次大小 | 让长视频处理从“跑脚本”变成可操作的生产线 |
| P1 | Tile 结果合并与人工复核回填 | InternVL dynamic tiling、Qwen-VL image preprocessing | `high_res_tile_plan` 后增加 `tile_result_merge`：把 tile OCR/VLM/人工结果回填到 `visual_text`、`structured_visual` 或 review notes | 当前屏幕小字是主要缺口之一；tile 已能生成证据，下一步要能消费结果 |
| P1 | 视频 RAG 的多粒度 chunk 与查询 | VideoRAG | `video-rag-pack` 从单一 transcript chunk 扩展为 transcript / visual / chapter / review-gap / content-asset 多层 JSONL；后续可选接 vector backend | 对长视频、课程复习、找关键片段很有价值，且默认本地可跑 |
| P1 | Smart-summary section 级重生成与证据引用 | BiliNote 总结编辑、vsummary LLM provider/task flow | 给 `smart-summary.md` 生成 section state，支持按章节重写、质量检查、引用 evidence path；Codex 先代替在线 LLM，后续同一接口接云端 LLM | 让智能总结从“生成一次”变成“可迭代编辑”，质量提升空间最大 |
| P2 | Transcript 纠错工作台 | BiliNote transcript parser、FunASR/SenseVoice tags、WhisperX word timestamps | `transcript-editor.html` 继续增强：术语词典、标点、说话人、错词仲裁、疑似错词来源对比 | ASR 是 smart-summary 的主输入，纠错收益会传导到所有人类可读文件 |
| P2 | 本地 VLM adapter smoke 与模型能力矩阵 | Qwen-VL、InternVL、LLaVA-OneVision | 不嵌模型仓库代码，只保留 OpenAI-compatible / subprocess adapter，增加本地模型 smoke、输入规格、能力/显存报告 | 等 OCR/批量闭环稳定后，再低风险启用本地视觉模型 |
| P2 | 内容素材卡编辑和下游交接 UI | BiliNote preview、内容工作流类项目 | `content-material-card` 增加可编辑草稿状态、事实核查清单、朋友圈/内容资产线程 handoff preview | 让 VKP 输出更容易进入后续内容生产，但仍保持 `publication_allowed=false` |

### 当前不该继续投入的复用方向

- 不再整体搬 `vsummary` 后端：VKP 已有 CLI/MCP/OpenClaw/run registry，整体迁移会制造第二套任务系统。
- 不再整体搬 `BiliNote` UI：可以继续吸收交互模式，但 VKP 现在更适合在 `task-console.html` 和 `review.html` 上渐进增强。
- 不把 VideoRAG / MovieChat 的重模型服务作为默认依赖：先复用数据结构、chunk、检索和 memory 思路。
- 不把 Qwen / InternVL / LLaVA 模型源码嵌进主流程：统一走 provider/adapter 边界。
- 不在 VKP 重做下载、平台字幕抓取、登录态处理：继续交给 `video-download-orchestrator` 或外部来源 handoff。

### 下一轮实现顺序

1. **时间轴对齐进入审核页**：把 `timeline-alignment-audit.json` 注入 `review.html` 和 review pack，显示 mismatch badge、ASR 建议起点和 preview-only 修复建议。
2. **tile result merge**：为 high-res tile 输出建立导入格式，把 ebook/OCR 空结果、wrapper-only、低信息量结果转成可回填的视觉证据或人工审核项。
3. **任务队列 UI 继续收拢**：把 ebook、tile、vision-review-queue、smart-summary、timeline audit 的 run artifact 统一展示为可重试批次。
4. **smart-summary section workflow**：把 long-video-memory-pack、chapter pack、corrected transcript 接到 section 级生成/质量检查/重生成。
5. **VideoRAG 多粒度检索**：补 review-gap 和 visual evidence chunk，让“找疑难点/找术语/找画面证据”更稳定。

### 文档化结论

目前已发现过的开源项目里，真正值得继续榨取的不是“更多模型代码”，而是四类工程能力：

- **时间定位与复核体验**：VTimeLLM / BiliNote 给的是时间轴可信度和审核交互；
- **任务状态与失败恢复**：vsummary 给的是长任务可恢复、可重试、可视化；
- **长视频记忆与检索**：VideoRAG / MovieChat 给的是分层 memory 和多粒度 chunk；
- **视觉输入标准化**：Qwen-VL / InternVL 给的是图像缩放、tile、多图输入和本地 VLM adapter 形态。

这些能力都应继续以小模块形式进入 VKP，不改变当前主线：本地 ASR、抽帧、ebook/OCR、疑难点多模态、人工审核、智能总结、内容素材卡。

## Update - 2026-07-04 22:27:35 | Codex GPT-5

### P0 landed: timeline alignment enters review UI and review pack

本轮继续复用 VTimeLLM temporal grounding / BiliNote 时间轴审核交互思路，把 `timeline_alignment_audit` 从独立报告和 task console 指标推进到实际人工审核工作流。

落地内容：

- `refresh-review-html` / bundle export 会读取或生成 `timeline-alignment-audit.json`，并把有问题的 item 作为只读 `timeline_alignment` 元数据注入 HTML 渲染包。
- `review.html` 每条有错位风险的 item 会显示：
  - `time-align:<count>` badge；
  - “时间轴对齐风险”区块；
  - 当前审核跳转、ASR 建议起点、抽帧/截图时间、青龙打标器时间；
  - preview-only 的 `review_start` 修复建议。
- `prepare-review-session` 会读取 `timeline-alignment-audit.json`，把有问题的 item 加入 `timeline_alignment_issue` 原因分组。
- `review-pack.md/json` 与 `review-notes.todo.json` 会保留 alignment 摘要和 `suggested_review_start`，建议状态为 `needs_fix`。
- 仍然不自动修改 `timeline.json`；是否采用 ASR 起点作为 `review_start` 必须由人工核对视频后决定。

修改文件：

```text
src/video_knowledge_pipeline/webui_bridge.py
src/video_knowledge_pipeline/lecture_package.py
src/video_knowledge_pipeline/review_session.py
```

验证：

`````powershell
python -m py_compile src\video_knowledge_pipeline\webui_bridge.py src\video_knowledge_pipeline\lecture_package.py src\video_knowledge_pipeline\review_session.py
$env:PYTHONPATH='src'
python -m video_knowledge_pipeline.cli refresh-review-html outputs\manual-timeline-alignment-smoke-20260704\bundle
python -m video_knowledge_pipeline.cli prepare-review-session outputs\manual-timeline-alignment-smoke-20260704\bundle --limit 0 --group-by reason
```

smoke 结果：

- `refresh-review-html` 返回 `timeline_alignment_issue_count = 1`；
- `review.html` 包含 `time-align:2`、`时间轴对齐风险`、`ASR 建议起点`；
- `review-pack.md` 包含 `timeline_alignment_issue`、`review_start=9.5`、`asr_start=4.25`、`suggested=4.25`；
- `review-notes.todo.json` 包含 `timeline_alignment` 和 `suggested_review_start`。

下一步优先级顺延：进入 P1 `tile_result_merge`，把 high-res tile 的 OCR/VLM/人工结果导入 `visual_text`、`structured_visual` 或 review notes，解决 ebook/OCR 空结果后的证据消费问题。
## 2026-07-04 22:38:08 | Codex / GPT-5：P1 Tile result merge 已落地

`high-res-tile-plan` 之后的结果消费环节已完成基础版：`tile-result-merge` 可以把 high-res tile 的 OCR/VLM/人工结果导入 VKP timeline。

当前状态：

- 已新增 `tile_result_merge.py`，并接入 CLI、MCP、任务控制台、run registry。
- 已验证 preview 和 execute：高置信结果写回 `visual_text` / `structured_visual`；低置信、空结果进入 review target，不清除 blocker。
- 该能力解决的是“tile 已生成但结果无法稳定回填”的问题，不替代 `ebook_markdown_pipeline`、本地 OCR 或多模态执行层。

下一步顺延：

1. 把 `tile-result-import.template.json` 接入本地 VLM / ebook tile OCR 的批量输出，减少人工填 JSON。
2. 在 review pack 中按 `tile_result_needs_review` 分组展示 tile 证据。
3. 在真实长视频 bundle 上跑一批 high-res tile -> 本地/人工结果 -> `tile-result-merge --execute` 的闭环。
## 2026-07-04 22:44:43 | Codex / GPT-5：Tile 复核进入 review pack

`tile_result_merge` 的低质量结果现在不再只停留在 timeline 内部字段，已经进入人工复核闭环：

- `tile_result_needs_review` 作为独立 review reason；
- `review-pack.md` 按“Tile 结果待复核”分组；
- `review-notes.todo.json` 保留 `tile_review_targets`，包括 tile id、置信度、失败原因和证据路径；
- 默认建议人工填写 `corrected_visual_text`，不会把低置信/空 tile 当作 OCR 成功。

下一步仍是：把本地 VLM / ebook tile OCR 的批量输出直接转换成 `tile-result-import.json`，减少人工拼 JSON。

## 2026-07-04 22:50:50 | Codex / GPT-5：Tile result import builder 已落地

`tile-result-import-build` 已接入，用于把本地 OCR/VLM/人工产生的 tile 结果文件转换成 `tile-result-import.json`：

- 支持 `.json` / `.txt` / `.md` 结果文件；
- 按 tile id 或 tile 图片 stem 自动匹配；
- 未匹配结果保持 `pending_result`；
- 输出 Markdown 报告、MCP args，并进入 task console / run registry；
- 下游可直接接 `tile-result-merge`。

这完成了 `high-res-tile-plan -> tile-result-import-build -> tile-result-merge -> review-pack` 的基础闭环。下一步可以把真实本地 VLM 或 ebook tile OCR 输出目录接到这个格式。

## Update - 2026-07-04 23:02:14 | Codex / GPT-5

### Tile result import parser now consumes common OCR/VLM outputs

Continuing the P1 high-res tile reuse track, `tile-result-import-build` has been upgraded from simple `text/confidence` JSON parsing to a real adapter for common tile OCR/VLM output shapes:

- RapidOCR / PaddleOCR style OCR entries: `result`, `ocr_result`, `data`, `items`, `lines`, `blocks`, `rec_texts`, `rec_scores`.
- OpenAI-compatible chat completions: `choices[].message.content` and text content parts.
- Gemini-style outputs: `candidates[].content.parts[].text`.
- VKP / VLM outputs: `visual_understanding` and `structured_visual`.
- Plain `.txt` / `.md` tile result files remain supported.

Confidence handling is explicit:

- OCR entry scores are averaged when available.
- Top-level `confidence` / `score` / `probability` wins.
- `--default-confidence` is applied only to matched result files that do not carry scores, useful for trusted OpenAI/Gemini/manual result folders.
- Pending tile results stay at confidence `0.0` and remain review targets.

Verification smoke:

`````powershell
python -m py_compile src\video_knowledge_pipeline\tile_result_import_builder.py tests\test_tile_result_import_builder.py
$env:PYTHONPATH='src'; python -m video_knowledge_pipeline.cli tile-result-import-build outputs\manual-high-res-tile-smoke-20260704\bundle --results-dir outputs\manual-high-res-tile-smoke-20260704\bundle\tile-results-rich --output-json outputs\manual-high-res-tile-smoke-20260704\bundle\tile-result-import-rich-default-confidence.json --default-confidence 0.72
$env:PYTHONPATH='src'; python -m video_knowledge_pipeline.cli tile-result-merge outputs\manual-high-res-tile-smoke-20260704\bundle --input-json outputs\manual-high-res-tile-smoke-20260704\bundle\tile-result-import-rich-default-confidence.json
```

Smoke result: 4 matched OCR/VLM result files, 2 pending tiles; merge preview produced 4 updates and 2 review targets. A direct Python assertion smoke also passed with 4 matched, 1 pending, 4 updates, 1 review target.

Pytest note: a targeted pytest file was added, but this Windows session still blocks pytest temp/cache directories with `PermissionError: [WinError 5]`. The test file compiles and the same function path was verified through direct Python smoke.


## Update - 2026-07-04 23:07:52 | Codex / GPT-5

### P0/P1 continued: task console processing queue

Continuing the vsummary/BiliNote/Peepshow-style task UI reuse track, `task-console.html` now includes a derived **处理队列** section in addition to the raw “任务历史” list.

The queue is built only from local run artifacts:

- `run-artifact-registry.json`
- `runs/*/run.json`

It does not start ASR, OCR, ebook, vision, download, or cloud API work. It groups existing VKP runs into operator-friendly lanes:

- ASR / 转写
- 图文 OCR / ebook
- 多模态复核
- 时间轴 / RAG
- 总结 / 导出
- 人工审核
- 其他任务

Each lane shows:

- status: `empty`, `ready`, or `action_required`;
- run count and status counts;
- failed item preview;
- next actions;
- prioritized retry command copied from the runs that actually need action;
- `runs/.../run.md` links.

This makes the existing high-res tile chain easier to operate: `high-res-tile-plan -> tile-result-import-build -> tile-result-merge -> review pack` now appears as one actionable OCR/ebook queue rather than scattered reports.

Verification smoke:

`````powershell
python -m py_compile src\video_knowledge_pipeline\task_console.py tests\test_task_console.py
$env:PYTHONPATH='src'; python -m video_knowledge_pipeline.cli export-task-console outputs\manual-high-res-tile-smoke-20260704\bundle --no-refresh
rg -n -e "处理队列" -e "runs/tile-result-merge/run.md" -e "queue-retry" outputs\manual-high-res-tile-smoke-20260704\bundle\task-console.html
```

Smoke result: `task-console.json` contains `processing_queue.schema = video_knowledge_pipeline.task_processing_queue.v1`; the OCR/ebook lane is `action_required`, links to `runs/tile-result-merge/run.md`, and prioritizes `tile-result-merge --execute` as the retry command.

Pytest note: `tests/test_task_console.py` was updated, but this Windows session still blocks pytest temporary/cache directory traversal with `PermissionError: [WinError 5]`. The same export path was verified through CLI smoke and compiled successfully.

## Update - 2026-07-04 23:16:30 | Codex / GPT-5

### 已落地：智能总结章节工作流

P1 “Smart-summary section 级重生成与证据引用”已完成第一版本地闭环。

复用来源：

- BiliNote 的章节化课程笔记/脑图组织思路；
- vsummary 的 staged artifact、run status、failed item、retry command 思路；
- MovieChat/long-video memory 的长视频分层 memory pack 作为章节证据输入。

VKP 落地：

- `src/video_knowledge_pipeline/smart_summary_section_workflow.py`
- CLI: `smart-summary-section-workflow`
- MCP: `smart_summary_section_workflow` / `smart_summary_section_workflow_tool`
- Task Console: 新增“智能总结章节工作流”命令与“总结 / 导出”队列联动
- Manifest/MCP args: `smart_summary_section_workflow_markdown`、`mcp_smart_summary_section_workflow_args`

下一步仍值得继续榨干的模块：

1. **BiliNote UI 交互**：把章节工作流和 transcript/video 同屏编辑做进一个工作台，而不是多个 HTML 页面跳转。
2. **vsummary staged generation**：让 `smart-summary-section-todo.json` 支持按章节逐个安装 revised markdown，类似 staged output commit。
3. **VideoRAG evidence citation**：章节重写时自动带上可点击 moment index / RAG chunk citation。
4. **本地/在线 LLM provider 统一**：Codex-first 已有，后续在线 LLM 只接同一 input pack 和 quality gate，不另起总结管线。
5. **人工抽样评分 UI**：对 smart-summary 的章节准确率、覆盖率、可读性做人工标注，用于比较有无多模态/ebook 的改善。

## Update - 2026-07-04 23:25:45 | Codex / GPT-5

### 已落地：章节修订 staged apply

P1 “vsummary staged generation / BiliNote section editing”继续推进：`smart-summary-section-workflow` 之后新增 `smart-summary-section-apply`，让章节级修订不再停留在 TODO JSON，而是能安装为 `exports/smart-summary.codex.md` 并进入既有质量门禁。

落地文件/入口：

- `src/video_knowledge_pipeline/smart_summary_section_apply.py`
- CLI: `smart-summary-section-apply`
- MCP: `smart_summary_section_apply` / `smart_summary_section_apply_tool`
- Task Console: “导入章节修订为智能总结”命令与“章节修订导入”产物链接
- Run artifact: `runs/smart-summary-section-apply/run.json`

这一步榨取的外部项目能力：

- vsummary 的 staged output / atomic install / run status 思路；
- BiliNote 的章节编辑和重新生成交互；
- VKP 现有 smart-summary quality gate，避免分叉成另一个总结系统。

下一步顺序调整：

1. **UI 同屏编辑**：在 task console 或 review workspace 中显示 section TODO、视频/转写、章节修订输入框和 apply 按钮。
2. **VideoRAG citation 注入**：章节修订时自动带上 moment index / RAG chunk citation。
3. **章节 apply 后关闭旧 workflow 状态**：当 section apply 通过质量门禁时，把旧 `smart-summary-section-workflow` 的 needs_retry 状态降噪，避免队列继续显示已处理旧缺口。
4. **人工抽样评分 UI**：对 smart-summary sections 做准确率/覆盖率/可读性评分。

## Update - 2026-07-04 23:31:16 | Codex / GPT-5

### 仍值得继续复用的外部代码模块清单

本节把“还有哪些值得复用的代码模块”固化为后续开发 backlog。判断标准不是仓库名是否热门，而是：能否直接增强 VKP 的视频知识化主线，能否作为局部模块接入，是否避免重写已有工具。

| 优先级 | 可复用模块 | 主要参考来源 | 当前 VKP 状态 | 下一步代码动作 | 边界 |
| --- | --- | --- | --- | --- | --- |
| P0 | 章节级智能总结编辑器 | BiliNote 章节/笔记编辑、vsummary staged task | 已完成第一版：smart-summary-section-workflow、smart-summary-section-editor、smart-summary-section-apply | 后续增强：citation 注入、章节质量评分、apply 后关闭旧 workflow 噪音 | 静态页面不直接写盘，不自动调用云 LLM |
| P0 | 任务队列和失败重试 UI 收拢 | vsummary task status、BiliNote 任务面板、Peepshow frame report | task-console.html 已有 run registry 和处理队列 | 把 ebook batch、多模态 batch、tile、timeline audit、smart-summary section 的 failed items 展示为统一 retry queue，支持批次大小、失败原因、下一条命令 | UI 只展示和生成命令，不绕过 execute/preflight 边界 |
| P0 | 字幕/ASR 多源仲裁 | BiliNote transcript parser、WhisperX、FunASR/SenseVoice | 已有 transcript sidecar、纠错包和 aligned timeline | 增强 corrected-transcript.json：平台字幕、自带字幕、本地 ASR、术语词典、OCR/视觉证据共同投票，输出可追溯替换原因 | 高置信可进入人类可读文件；低置信进入 review，不直接覆盖原始证据 |
| P1 | VideoRAG 引用注入 | VideoRAG / RAGFlow-style chunk citation | 已有 `video-rag-pack/search`/serve 和 moment index | 在 smart-summary section workflow 中给每章自动挂 moment_id、transcript chunk、frame evidence citation，导出 citation-aware Markdown | 本地检索优先；HTTP serve 必须显式启动 |
| P1 | 长视频分层记忆 map-reduce | MovieChat、vsummary summary pipeline、BiliNote 分块脑图 | 已有 long-video-memory-pack、smart-summary-chapters | 让 generate-smart-summary-with-codex 默认消费 short/long memory + chapter pack，而不是单纯规则草稿；后续同接口接在线 LLM | 不把规则摘要伪装成最终智能总结 |
| P1 | 高分辨率 tile OCR/VLM 闭环 | InternVL dynamic tiling、Qwen-VL 图像预处理、Peepshow frame report | 已有 high-res-tile-plan、tile-result-import-build、tile-result-merge | 增加 tile editor/review 页面，支持按 tile 导入本地 OCR/VLM/人工结果，失败项进入 review pack | tile 结果低置信/空结果不能清 blocker |
| P1 | 本地 VLM adapter 标准化 | Qwen2.5-VL、InternVL、LLaVA-OneVision | 已有 vlm_preprocess.py 和 local_vlm_server_adapter.py | 增加 OpenAI-compatible/local subprocess 两类 adapter smoke；统一多图 frame group 请求 schema | 不默认部署大模型；只接 adapter 和 smoke |
| P1 | 时间定位评估与错位检测 | VTimeLLM、TimeChat、VideoChatGPT temporal QA | 已有 timeline-alignment-audit | 增加 “ASR segment start / frame time / tagger time / human review time” 的 conflict score，给 review UI 标出时间戳不可靠片段 | 不用固定偏移修时间戳；必须保留来源 |
| P2 | 在线/本地 LLM provider 统一文本层 | vsummary LiteLLM/provider gateway | 已有 text_llm_gateway.py，Codex-first 流程已成形 | 新增 generate-smart-summary-with-llm --provider-config --execute，复用同一 input pack、section workflow 和 quality gate | API key 只读环境变量/显式 config，不写入产物 |
| P2 | 人工抽样评分 UI | Peepshow report、BiliNote review workflow | 已有 multimodal sample review 和 review pack | 增加 summary section 评分：准确率、覆盖率、可读性、视觉证据贡献、有无多模态差异 | 评分是评估层，不直接修改总结 |
| P2 | 内容素材生成模板 | vsummary clips/summary、BiliNote note export、VKP content card | 已有 content material card、handoff pack | 把 smart-summary sections 映射成素材候选：关键观点、案例、金句、短视频脚本草稿，并保留 evidence path | 只能作为 inspiration，不自动发布，不当事实结论 |

#### 不建议继续整体搬运的部分

- vsummary / BiliNote 的下载、账号、平台路由：VKP 已明确不做下载后端，继续交给 video-download-orchestrator。
- BiliNote 的整套前端/后端应用壳：可吸收交互模式，但 VKP 当前更适合静态 review/task console + CLI/MCP。
- VideoRAG 的完整服务化栈：VKP 只需要本地 JSONL pack、检索和 citation；长期服务必须显式启动。
- 本地 VLM 仓库训练/推理主工程：只接 adapter，不把大型模型仓库嵌入 VKP 主流程。

#### 下一步建议顺序

1. 已完成 smart-summary-section-editor.html 第一版；下一步把 VideoRAG/moment citation 注入章节编辑器和 workflow。
2. 再把 VideoRAG citation 注入 section workflow，让每章修订都有可追溯证据。
3. 然后补字幕/ASR 多源仲裁，把 corrected transcript 作为 smart-summary 默认输入。
4. 最后补人工抽样评分 UI，用来量化 ebook、多模态、纠错对最终人类可读文件的改善。
## Update - 2026-07-04 23:40:12 | Codex / GPT-5

### 已落地：Smart-summary section editor UI

P0 “章节级智能总结编辑器”完成第一版。它把 BiliNote 的章节编辑体验、vsummary 的 staged revision/install 思路、VKP 的 transcript/evidence/quality gate 合成到一个静态 HTML 工作台里。

新增入口：

`````powershell
.\scripts\video-knowledge.ps1 smart-summary-section-editor <webui-bundle>
```

MCP：

- `smart_summary_section_editor`
- `smart_summary_section_editor_tool`

新增产物：

- `smart-summary-section-editor.html`
- `smart-summary-section-editor.json`
- `exports/smart-summary-section-revisions.template.json`
- `mcp-smart-summary-section-editor.args.json`
- `runs/smart-summary-section-editor/run.json`
- `runs/smart-summary-section-editor/run.md`

能力边界：

- 静态页面，同屏展示章节队列、视频播放器/本地文件选择、逐字稿片段、章节证据、rewrite prompt、章节修订 textarea。
- 页面只通过浏览器下载/复制 `smart-summary-section-revisions.json`，不直接写回 bundle。
- 最终写回仍必须走 `smart-summary-section-apply --input-json <revision-json>`，复用既有 `smart-summary.codex.md` 安装和 quality gate。
- 不调用云 LLM，不处理媒体，不绕过人工审核。

任务控制台集成：

- `task-console.html` 新增命令“智能总结章节编辑器”。
- 产物区新增“智能总结章节编辑器”链接。
- run registry 中新增 `smart_summary_section_editor`，显示为 `completed`，并保留下一步动作：编辑章节、下载 revision JSON、运行 apply。

验证：

`````powershell
python -m py_compile src\video_knowledge_pipeline\smart_summary_section_editor.py src\video_knowledge_pipeline\cli.py src\video_knowledge_pipeline\mcp_server.py src\video_knowledge_pipeline\task_console.py tests\test_smart_summary_section_editor.py
$env:PYTHONPATH='src'; python -m pytest -q tests\test_smart_summary_section_editor.py
$env:PYTHONPATH='src'; python -m video_knowledge_pipeline.cli smart-summary-section-editor outputs\manual-smart-summary-registry-smoke-20260704\bundle
$env:PYTHONPATH='src'; python -m video_knowledge_pipeline.cli mcp-call smart_summary_section_editor outputs\manual-smart-summary-registry-smoke-20260704\bundle\mcp-smart-summary-section-editor.args.json
$env:PYTHONPATH='src'; python -m video_knowledge_pipeline.cli export-task-console outputs\manual-smart-summary-registry-smoke-20260704\bundle --no-refresh
```

结果：

- Targeted pytest: `1 passed`，只有 `.pytest_cache` 权限 warning。
- CLI/MCP smoke 均生成 4 个章节的 editor payload。
- `task-console.html` 能显示 `smart-summary-section-editor.html` 链接、命令和 run artifact。

下一步优先级更新：

1. **字幕/ASR 多源仲裁**：让 corrected transcript 成为 smart-summary 默认输入，减少错词对总结层的污染。
2. **citation 交互增强**：把 `video_moment_index` citation 做成可点击的 timeline/video 跳转，并支持 RAG query rerank。
3. **章节 apply 后关闭旧 workflow 状态**：如果 editor/apply 已完成且质量门禁通过，降低旧 workflow `needs_retry` 噪音。
4. **人工抽样评分 UI**：量化 smart-summary section 的准确率、覆盖率、可读性，以及 ebook/多模态对最终文档质量的贡献。
## Update - 2026-07-04 23:46:55 | Codex / GPT-5

### 已落地：VideoRAG / moment citation 注入章节工作流

P1 “VideoRAG citation 注入”完成第一版。VKP 现在会把 `video-moment-index` 的本地 moment chunk 自动注入到智能总结章节工作流和章节编辑器里。

复用来源：

- VideoRAG 的 “retrieval unit / chunk citation” 思路；
- VTimeLLM / temporal QA 的 “时间范围是引用的一部分” 思路；
- VKP 已有 `video_moment_index.py`，不新增向量库、不启动 HTTP RAG 服务。

落地行为：

- `smart-summary-section-workflow` 会加载 `exports/video-moment-index.json`；如果不存在，会本地调用 `build_video_moment_index` 生成。
- 每个 section 根据章节 start/end 与 moment chunk 时间范围重叠匹配 citation。
- citation 写入：
  - `section.citations`
  - `section.evidence.citations`
  - `exports/smart-summary-section-todo.json` 的每条 row
  - `rewrite_prompt` 中的“证据引用”行
  - `smart-summary-section-editor.html` 的证据面板
- citation 字段包括：`citation_id`、`chunk_index`、`time_range`、`start/end`、`timeline_indexes`、`snippet`、`visual_snippet`、`temporal_snippet`、`evidence_paths`、`source=video_moment_index`。

边界：

- 本地 only，不调用云模型。
- 没有 timeline / moment index 时优雅降级，记录 unavailable，不阻塞 section workflow。
- citation 是证据导航和改写依据，不直接把片段内容当事实结论。

验证：

`````powershell
python -m py_compile src\video_knowledge_pipeline\smart_summary_section_workflow.py src\video_knowledge_pipeline\smart_summary_section_editor.py tests\test_smart_summary_section_citations.py tests\test_smart_summary_section_editor.py
$env:PYTHONPATH='src'; python -m pytest -q tests\test_smart_summary_section_citations.py tests\test_smart_summary_section_editor.py
$env:PYTHONPATH='src'; python -m video_knowledge_pipeline.cli smart-summary-section-workflow outputs\manual-smart-summary-registry-smoke-20260704\bundle --target-chapters 3
$env:PYTHONPATH='src'; python -m video_knowledge_pipeline.cli smart-summary-section-editor outputs\manual-smart-summary-registry-smoke-20260704\bundle
$env:PYTHONPATH='src'; python -m video_knowledge_pipeline.cli mcp-call smart_summary_section_editor outputs\manual-smart-summary-registry-smoke-20260704\bundle\mcp-smart-summary-section-editor.args.json
```

结果：

- Targeted pytest: `2 passed`，只有 `.pytest_cache` 权限 warning。
- smoke bundle 的 workflow/editor/todo/HTML 均出现 `moment-0001` 和 `citations`。
- MCP editor call 成功，`ignored_args=[]`。

下一步优先级更新：

1. **字幕/ASR 多源仲裁**：平台字幕、自带字幕、本地 ASR、术语词典、OCR/视觉证据共同投票，生成更可靠 `corrected-transcript.json`。
2. **citation 交互增强**：把 citation 做成可点击时间段，联动视频播放器和 transcript row。
3. **章节 apply 后关闭旧 workflow 状态**：如果 editor/apply 已完成且质量门禁通过，降低旧 workflow `needs_retry` 噪音。
4. **人工抽样评分 UI**：量化 smart-summary section 的准确率、覆盖率、可读性，以及 ebook/多模态对最终文档质量的贡献。
## Update - 2026-07-05 00:03:35 | Codex / GPT-5

### P0 completed: transcript-source-arbitration

The P0 “字幕 / ASR / 平台字幕多源仲裁” item has a first production-shaped implementation:

- Reads ASR/normalized transcript, platform/self subtitles, previous corrected sidecars, timeline fallback, `term-resolution.json`, and optional glossary aliases.
- Uses conservative source scoring and overlap checks to avoid blindly trusting platform subtitles, because many platform subtitles are also ASR-derived.
- Writes `source-arbitrated-transcript.json/srt/md` and promotes it to `manifest.corrected_transcript_*` by default.
- Writes `transcript-source-arbitration.json/md` with sources, changed segments, alternatives, and review rows.
- Registers a run artifact so task console can show it in the processing queue.

Remaining follow-up for this track:

1. Add a richer transcript arbitration UI inside the unified video workspace.
2. Add optional punctuation restoration / speaker labels after source arbitration.
3. Feed arbitration review rows into the same review pack closure path used by OCR/vision gaps.
4. Compare `source-arbitrated-transcript` against real long-video smart-summary quality.

Next backlog item should move to the main workspace / batch queue integration rather than reimplementing transcript arbitration again.

## Update - 2026-07-05 20:10:50 | Codex / GPT-5

### 文档化：剩余外部代码模块复用清单

新增收束文档：`docs/external-code-reuse-remaining-modules-2026-07-05.md`。

该文档把“还有哪些值得复用的代码模块”固定为下一阶段判断入口，避免继续围绕完整开源 App 重复评估。当前结论：

- 继续复用的重点是低耦合模块，不是整体搬 vsummary、BiliNote、VideoRAG 或本地 VLM 项目。
- P0 仍是统一视频工作台、批次队列/失败重试 UI、字幕/ASR/平台字幕多源仲裁后处理。
- P1 是长视频分层总结输入包、视频 RAG/时间定位、人工抽样评分 UI。
- P2 是本地 VLM adapter 能力矩阵和内容素材模板增强。
- 不建议继续榨的方向包括：整体后端/React UI 迁移、默认引入向量库/图数据库、嵌入大模型源码、在 VKP 内重写下载/登录/抓字幕、默认云多模态全量跑帧。

推荐继续实现顺序已经在新文档中更新：先完成 `export-video-workbench`，再收拢 run registry/failed items/retry commands，然后把 `transcript-source-arbitration` review rows 接进 transcript editor/review pack。
## Update - 2026-07-05 20:28:30 | Codex / GPT-5

### P0 landed: unified video workbench v1

Backlog 对应：`docs/external-code-reuse-remaining-modules-2026-07-05.md` 的 P0 “统一视频工作台”。

本轮把 BiliNote 的“视频 + 字幕/笔记同屏”、vsummary 的时间戳跳转/产物入口、Peepshow/VidClaude 的证据卡片思路，落成 VKP 自己的静态工作台，而不是整体搬外部 UI。

新增入口：

`````powershell
.\scripts\video-knowledge.ps1 export-video-workbench <webui-bundle>
```

MCP：

- `export_video_workbench`
- `export_video_workbench_tool`

新增产物：

- `video-workbench.html`
- `video-workbench.json`
- `mcp-video-workbench.args.json`
- `runs/video-workbench/run.json`
- `runs/video-workbench/run.md`

能力边界：

- 静态本地 HTML，不直接写回 bundle，不调用云 API，不处理媒体。
- 页面内聚合任务控制台、审核页、转写编辑器、智能总结章节编辑器、字幕/ASR 多源仲裁、智能总结、逐字稿、知识笔记、任务产物索引和片段索引。
- 支持选择本地视频文件后点击 timeline row 跳转播放时间点。
- 真实导入、执行、多模态调用仍走既有 CLI/MCP/preflight/confirm 边界。

Task console 集成：

- `task-console.html` 新增命令“打开视频知识工作台”。
- 产物区新增“视频知识工作台”链接。
- `export-task-console` 会写出 `mcp-video-workbench.args.json` 并把 `mcp_video_workbench_args` 写入 manifest。

验证：

`````powershell
python -m py_compile src\video_knowledge_pipeline\video_workbench.py src\video_knowledge_pipeline\cli.py src\video_knowledge_pipeline\mcp_server.py src\video_knowledge_pipeline\task_console.py tests\test_video_workbench.py
$env:PYTHONPATH='src'; python -m video_knowledge_pipeline.cli export-video-workbench outputs\manual-video-workbench-smoke\bundle
$env:PYTHONPATH='src'; python -m video_knowledge_pipeline.cli mcp-call export_video_workbench outputs\manual-video-workbench-smoke\bundle\mcp-video-workbench.args.json
$env:PYTHONPATH='src'; python -m video_knowledge_pipeline.cli mcp-audit-bundle outputs\manual-video-workbench-smoke\bundle
```

结果：

- py_compile 通过。
- CLI / mcp-call 均成功生成 `video-workbench.html/json`，timeline_count=2。
- `mcp-audit-bundle` 结果 `status=ok`，14/14 OK，包含 `mcp_video_workbench_args -> export_video_workbench`。
- 新增 pytest `tests/test_video_workbench.py` 的测试主体显示 `.. [100%]`，但当前 Windows pytest session finish 在本机临时目录/清理阶段卡住，需要手动停止 pytest 进程；直接 CLI/MCP smoke 已覆盖核心行为。

下一步：继续 P0/P1 交界任务，把 run registry / failed items / retry commands 在工作台里做成更强的统一队列，然后把 `transcript-source-arbitration` review rows 接入 transcript editor / review pack。
## Update - 2026-07-05 20:33:10 | Codex / GPT-5

### P0 continued: workbench batch queue and retry panel

在 `video-workbench.html` 第一版基础上，本轮继续吸收 vsummary 的 run status / retry command、BiliNote 的任务面板和 Peepshow/VidClaude 的失败项预览思路，把 `task-console.py` 已有的 processing queue 逻辑复用进统一工作台。

落地变化：

- `export-video-workbench` 现在读取并刷新 `run-artifact-registry.json`。
- `video-workbench.json` 新增：
  - `run_registry`
  - `processing_queue`
- `video-workbench.html` 左栏新增“处理队列”：
  - 显示 run_count / action_required_count；
  - 按 ASR/转写、图文 OCR/ebook、多模态复核、时间轴/RAG、总结/导出、人工审核、其他任务分组；
  - 显示每组状态、runs、失败项预览；
  - 显示 retry command，并提供复制按钮。
- `video_workbench` 自身 run 会登记到 `runs/video-workbench/run.json`，并在登记后重新刷新 registry，使工作台 JSON/HTML 看到最新 run 状态。

验证：

`````powershell
python -m py_compile src\video_knowledge_pipeline\video_workbench.py tests\test_video_workbench.py
$env:PYTHONPATH='src'; python -c "import importlib.util; spec=importlib.util.spec_from_file_location('tvw','tests/test_video_workbench.py'); mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); mod.test_export_video_workbench_writes_static_workspace(); mod.test_task_console_links_video_workbench(); print('video_workbench_tests_ok')"
$env:PYTHONPATH='src'; python -m video_knowledge_pipeline.cli export-video-workbench outputs\test-video-workbench\bundle
$env:PYTHONPATH='src'; python -m video_knowledge_pipeline.cli mcp-call export_video_workbench outputs\test-video-workbench\bundle\mcp-video-workbench.args.json
$env:PYTHONPATH='src'; python -m video_knowledge_pipeline.cli mcp-audit-bundle outputs\test-video-workbench\bundle
```

结果：

- Direct test runner: `video_workbench_tests_ok`。
- CLI smoke: `processing_queue.action_required_count=1`，`run_registry.run_count=2`，包含 `video-workbench` 和 `timeline-alignment-audit`。
- MCP call: `ignored_args=[]`。
- MCP audit: `status=ok`，14/14 OK。

边界：队列面板只展示 run registry / failed items / retry command，不自动执行命令，不绕过 preflight、execute 和人工确认边界。
## Update - 2026-07-05 20:44:25 | Codex / GPT-5

### P0/P1 continued: transcript arbitration enters review pack and editor

承接 P0 “字幕/ASR/平台字幕多源仲裁后处理”，本轮把 `transcript-source-arbitration` 的低置信冲突从单独报告推进到人工复核工作流里，但保持导入边界清楚：字幕仲裁纠错仍通过 transcript editor / `apply-transcript-edits`，不塞进 timeline 的 `apply-review-notes`。

落地变化：

- `prepare-review-session` 会把 `transcript-source-arbitration.json` 中的 `review_rows` 转成 `target_type=transcript_arbitration` 的 review target。
- 新增 review reason：
  - `transcript_source_conflict`
  - `low_arbitration_confidence`
- `review-pack.md/json` 新增“字幕/ASR 仲裁待复核”分组。
- `review-notes.todo.json` 会跳过 transcript arbitration target，避免用户把字幕纠错误导入 timeline review notes。
- `prepare-transcript-edit-session` 会把对应仲裁冲突挂到转写段落上。
- `transcript-editor.html` 现在高亮显示：
  - 仲裁待复核 badge；
  - chosen source / original / suggested；
  - ASR、平台字幕等 alternatives。

验证：

`````powershell
python -m py_compile src\video_knowledge_pipeline\review_session.py src\video_knowledge_pipeline\transcript_editor.py tests\test_transcript_arbitration_review_integration.py
$env:PYTHONPATH='src'; python -c "import importlib.util; spec=importlib.util.spec_from_file_location('tari','tests/test_transcript_arbitration_review_integration.py'); mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); mod.test_review_pack_includes_transcript_arbitration_targets(); mod.test_transcript_editor_shows_arbitration_conflicts(); print('transcript_arbitration_review_tests_ok')"
rg -n -e "transcript_source_conflict" -e "low_arbitration_confidence" -e "仲裁待复核" outputs\test-transcript-arbitration-review\bundle\review-pack.md outputs\test-transcript-arbitration-review\bundle\review-pack.json outputs\test-transcript-arbitration-review\bundle\transcript-editor.html
rg -n -e "transcript_source_conflict" -e "low_arbitration_confidence" outputs\test-transcript-arbitration-review\bundle\review-notes.todo.json
```

结果：

- Direct test runner: `transcript_arbitration_review_tests_ok`。
- `review-pack.md/json` 能看到 `transcript_source_conflict`、`low_arbitration_confidence`。
- `transcript-editor.html` 能看到 `仲裁待复核` 和 alternatives。
- `review-notes.todo.json` 对上述两个 reason 无匹配，符合“字幕纠错走 transcript editor”的边界。

下一步：把 transcript arbitration 的关闭状态和 transcript editor 的保存结果联动起来。理想形态是：`apply-transcript-edits` 写入人工纠正版后，`review-closure-status` 能识别对应仲裁 target 已关闭或已被人工接受。
## Update - 2026-07-05 20:52:57 | Codex / GPT-5

### P0/P1 continued: transcript arbitration closure status

承接上一轮“transcript arbitration enters review pack and editor”，本轮补齐关闭闭环：人工通过 transcript editor 导出 `transcript-edits.json` 并运行 `apply-transcript-edits` 后，`review-closure-status` 可以识别对应字幕/ASR 仲裁冲突已经关闭。

落地变化：

- `review_session.py` 的 transcript arbitration target 会读取 `human-corrected-transcript.json`。
- 如果该 sidecar 来源是 `human_transcript_editor`，且包含对应 segment index 的人工纠正文，则：
  - transcript arbitration target 标记 `closed=true`；
  - `review_status=corrected_transcript`；
  - `transcript_arbitration.human_corrected_text` 记录人工纠正文；
  - evidence paths 同时保留仲裁报告和人工纠正版 transcript。
- `review_closure_status` 现在基于 `all_targets` 统计非 timeline review target 的关闭状态。
- `review-closure-status.json/md` 新增：
  - `closed_by_reason`
  - `closed_targets`
  - Markdown 的 “Closed By Reason” 表。

验证：

`````powershell
python -m py_compile src\video_knowledge_pipeline\review_session.py src\video_knowledge_pipeline\transcript_editor.py tests\test_transcript_arbitration_review_integration.py
$env:PYTHONPATH='src'; python -c "import importlib.util; spec=importlib.util.spec_from_file_location('tari','tests/test_transcript_arbitration_review_integration.py'); mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); mod.test_review_pack_includes_transcript_arbitration_targets(); mod.test_transcript_editor_shows_arbitration_conflicts(); print('transcript_arbitration_closure_tests_ok')"
```

顺序 smoke 结果：

```json
{"open_by_reason":{"pending_review":1},"closed_by_reason":{"low_arbitration_confidence":1,"transcript_source_conflict":1},"closed_targets":1}
```

这一步把 BiliNote-style transcript editor、ASR/字幕多源仲裁和 VKP review closure 连接起来。后续再做 UI 时，`video-workbench.html` 可以直接读取 `review-closure-status.json` 显示“字幕仲裁已关闭/未关闭”。
## Update - 2026-07-05 20:57:42 | Codex / GPT-5

### P0 continued: workbench review closure panel

承接统一视频工作台和字幕仲裁关闭闭环，本轮把 `review-closure-status.json` 接入 `video-workbench.html`，让用户在主工作台左栏直接看到复核整体进度和字幕/ASR 仲裁冲突的 open/closed 状态。

落地变化：

- `export-video-workbench` 读取 `review-closure-status.json` 并写入 `video-workbench.json.review_closure`。
- `video-workbench.html` 左栏新增“复核闭环”面板：
  - Open / Closed 总数；
  - 字幕仲裁待复核；
  - 字幕仲裁已关闭；
  - 快捷按钮：查看关闭报告、打开转写编辑。
- `artifact_cards` 新增：
  - `review_closure_status -> review-closure-status.md`
  - `review_pack -> review-pack.md`
- 字幕仲裁 open/closed 数量从 `transcript_source_conflict` 和 `low_arbitration_confidence` reason 中归并，避免用户只在报告深处才能看到状态。

验证：

`````powershell
python -m py_compile src\video_knowledge_pipeline\video_workbench.py tests\test_video_workbench.py
$env:PYTHONPATH='src'; python -c "import importlib.util; spec=importlib.util.spec_from_file_location('tvw','tests/test_video_workbench.py'); mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); mod.test_export_video_workbench_writes_static_workspace(); mod.test_task_console_links_video_workbench(); print('video_workbench_closure_panel_tests_ok')"
$env:PYTHONPATH='src'; python -m video_knowledge_pipeline.cli export-video-workbench outputs\test-video-workbench\bundle
rg -n -e "复核闭环" -e "字幕仲裁待复核" -e "review_closure" outputs\test-video-workbench\bundle\video-workbench.html outputs\test-video-workbench\bundle\video-workbench.json
```

结果：

- Direct test runner: `video_workbench_closure_panel_tests_ok`。
- CLI smoke 成功生成 `video-workbench.html/json`。
- 产物中能看到 `review_closure.transcript_arbitration.open=1`、`closed=2`，HTML 中能看到“复核闭环”和“字幕仲裁待复核”。

边界：工作台仍是静态本地 HTML，只读展示 closure/report 链接，不自动写入、不自动执行 `apply-transcript-edits`，也不调用云服务。
## Update - 2026-07-05 21:02:44 | Codex / GPT-5

### P0/P1 continued: workbench evidence status panel

继续收拢统一视频工作台：本轮把 VTimeLLM-style 时间错位审计、InternVL/Qwen-style tile 小字补救、VideoRAG/VTime-style 片段索引这三类已落地报告，汇总成 `video-workbench.html` 左栏的“证据状态”面板。

落地变化：

- `export-video-workbench` 新增 `evidence_status`：
  - `timeline_alignment`：读取 `timeline-alignment-audit.json`，统计 issue_count / item_count；
  - `tile_review`：从原始 `timeline.json` 统计 `tile_review_targets` 和 `tile_result_needs_review`；
  - `video_moment_index`：读取 `exports/video-moment-index.json`，统计 chunk_count / duration_seconds。
- `video-workbench.html` 新增“证据状态”面板：
  - 时间错位；
  - Tile 待复核；
  - 片段索引；
  - 覆盖时长。
- 新增快速入口：
  - 时间审计 -> `timeline-alignment-audit.md`；
  - 片段索引 -> `exports/video-moment-index.md`；
  - 复核包 -> `review-pack.md`。
- `artifact_cards` 新增 `timeline_alignment_audit_report`，并继续保留 review pack / review closure / moment index 链接。

验证：

`````powershell
python -m py_compile src\video_knowledge_pipeline\video_workbench.py tests\test_video_workbench.py
$env:PYTHONPATH='src'; python -c "import importlib.util; spec=importlib.util.spec_from_file_location('tvw','tests/test_video_workbench.py'); mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); mod.test_export_video_workbench_writes_static_workspace(); mod.test_task_console_links_video_workbench(); print('video_workbench_evidence_status_tests_ok')"
$env:PYTHONPATH='src'; python -m video_knowledge_pipeline.cli export-video-workbench outputs\test-video-workbench\bundle
rg -n -e "证据状态" -e "时间错位" -e "Tile 待复核" -e "evidence_status" outputs\test-video-workbench\bundle\video-workbench.html outputs\test-video-workbench\bundle\video-workbench.json
```

结果：

- Direct test runner: `video_workbench_evidence_status_tests_ok`。
- CLI smoke 成功生成 `video-workbench.html/json`。
- 产物中能看到 `evidence_status`、`证据状态`、`时间错位`、`Tile 待复核`。

边界：该面板只读汇总已有报告和 timeline 字段，不生成新 OCR/多模态结果，不调用云模型，不自动修正时间戳或 tile 结果。
## Update - 2026-07-05 21:07:31 | Codex / GPT-5

### P0/P1 continued: workbench evidence filters and row details

承接上一轮“证据状态”面板，本轮把状态数字变成可操作入口：工作台可以从时间错位 / Tile 待复核直接筛选 timeline row，并在详情区显示对应证据摘要。

落地变化：

- `export-video-workbench` 在生成 timeline rows 前读取 `timeline-alignment-audit.json`，按 timeline index 关联 alignment 元数据。
- `video-workbench.json.timeline[]` 新增：
  - `evidence_flags`：如 `timeline_alignment_issue`、`tile_result_needs_review`、`needs_human_review`；
  - `timeline_alignment`：issues、review_start、asr_first_start、frame_time、suggested_review_start、asr_excerpt；
  - `tile_review_targets`：tile_id、confidence、reasons、evidence_path。
- `video-workbench.html` 增强：
  - “筛时间错位”按钮会设置过滤词 `timeline_alignment_issue`；
  - “筛 Tile”按钮会设置过滤词 `tile_result_needs_review`；
  - timeline row 显示 evidence flags badge；
  - 详情区新增“证据标记 / 时间对齐 / Tile 复核”。
- 这一步继续复用 VTimeLLM-style alignment、InternVL/Qwen-style tile recovery、Peepshow-style evidence row 展示思路，不新增模型或后端。

验证：

`````powershell
python -m py_compile src\video_knowledge_pipeline\video_workbench.py tests\test_video_workbench.py
$env:PYTHONPATH='src'; python -c "import importlib.util; spec=importlib.util.spec_from_file_location('tvw','tests/test_video_workbench.py'); mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); mod.test_export_video_workbench_writes_static_workspace(); mod.test_task_console_links_video_workbench(); print('video_workbench_evidence_filter_tests_ok')"
$env:PYTHONPATH='src'; python -m video_knowledge_pipeline.cli export-video-workbench outputs\test-video-workbench\bundle
rg -n -e "setFilter\('timeline_alignment_issue'\)" -e "setFilter\('tile_result_needs_review'\)" -e "证据标记" -e "Tile 复核" -e "tile_result_needs_review" outputs\test-video-workbench\bundle\video-workbench.html outputs\test-video-workbench\bundle\video-workbench.json
```

结果：

- Direct test runner: `video_workbench_evidence_filter_tests_ok`。
- CLI smoke 成功生成 `video-workbench.html/json`。
- 产物中能看到筛选按钮、证据标记、Tile 复核和 row 级 `tile_result_needs_review`。

边界：点击筛选只改变静态页面过滤，不写回 timeline，不自动修正时间戳，不执行 tile OCR/VLM。
## Update - 2026-07-05 21:17:52 | Codex / GPT-5

### P0/P1 continued: VideoRAG moment search embedded in workbench

本轮继续把外部项目的局部能力收束进统一视频工作台：video-workbench.html 现在直接内置 VideoRAG-style 片段搜索，不再要求用户先打开 task console iframe 再搜片段。

复用点：

- 复用 task_console._compact_moment_index 的 compact chunk 数据结构；
- 继续消费 exports/video-moment-index.json，不新增向量库、不启动 HTTP RAG 服务；
- 借鉴 vsummary 的 citation seek 体验：搜索结果点击后跳转播放器时间点，并选中对应 timeline row；
- 保持静态本地 HTML，不写盘、不调用云、不执行命令。

新增/修改：

- src/video_knowledge_pipeline/video_workbench.py
  - export_video_workbench 输出 moment_index 到 video-workbench.json；
  - 新增 片段搜索 panel；
  - 新增 renderMomentSearch()、selectMoment()、
earestRow() 前端逻辑；
  - 点击 moment result 会跳视频、选择对应 timeline row，并保留证据路径和关键词。
- tests/test_video_workbench.py
  - fixture 的 video-moment-index.json 增加关键词、snippet、证据路径；
  - 覆盖 moment_index payload、搜索 UI、关键词和 JS hook。

验证：

```powershell
python -m py_compile src\video_knowledge_pipeline\video_workbench.py tests\test_video_workbench.py
$env:PYTHONPATH='src'; python -c "import importlib.util; spec=importlib.util.spec_from_file_location('tvw','tests/test_video_workbench.py'); mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); mod.test_export_video_workbench_writes_static_workspace(); mod.test_task_console_links_video_workbench(); print('video_workbench_moment_search_tests_ok')"
$env:PYTHONPATH='src'; python -m video_knowledge_pipeline.cli export-video-workbench outputs\test-video-workbench\bundle
rg -n -e "片段搜索" -e "momentSearchInput" -e "renderMomentSearch" -e "selectMoment" -e "moment_index" outputs\test-video-workbench\bundle\video-workbench.html outputs\test-video-workbench\bundle\video-workbench.json
git diff --check -- src\video_knowledge_pipeline\video_workbench.py tests\test_video_workbench.py
`

结果：

- Direct test runner: video_workbench_moment_search_tests_ok。
- CLI smoke 成功生成 video-workbench.html/json。
- 产物中能看到 片段搜索、momentSearchInput、renderMomentSearch、selectMoment、moment_index。
- git diff --check 对本次代码/测试文件无报错。

后续继续榨取：

- 把 workbench 的 run queue 扩展到 ebook batch、tile merge、多模态 batch、smart-summary section workflow。
- 把 corrected transcript / source arbitration 差异视图放进 workbench 主页面。
- 让 smart-summary-input-pack 记录每章使用了哪些 transcript / OCR / vision / moment evidence。
## Update - 2026-07-05 21:25:18 | Codex / GPT-5

### P0 continued: workbench queue cards become actionable run details

本轮继续复用 vsummary 的 run status / retry command 和 BiliNote 的任务面板思路，把 video-workbench.html 的处理队列从摘要卡片推进到可操作的队列详情。

落地变化：

- src/video_knowledge_pipeline/video_workbench.py
  - 左栏 queue card 增加 data-queue-key 和 selectQueue()；
  - 点击 ASR、ebook/OCR、多模态、时间轴/RAG、总结导出、人工审核等队列后，右侧详情区显示：
    - 队列说明；
    - status / run_count / action_required / failed_count；
    - runs 列表；
    - failed items；
    - next actions；
    - 最多 3 条 retry command，并可复制。
  - 修复 workbench moment search 的 MOMENT_INDEX 前端常量声明，避免浏览器运行时报错。
- tests/test_video_workbench.py
  - 覆盖 selectQueue、QUEUE_GROUPS、data-queue-key=\"document_ocr\"、queue-detail-retry、队列：。

验证：

```powershell
python -m py_compile src\video_knowledge_pipeline\video_workbench.py tests\test_video_workbench.py
$env:PYTHONPATH='src'; python -c "import importlib.util; spec=importlib.util.spec_from_file_location('tvw','tests/test_video_workbench.py'); mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); mod.test_export_video_workbench_writes_static_workspace(); mod.test_task_console_links_video_workbench(); print('video_workbench_queue_detail_tests_ok')"
$env:PYTHONPATH='src'; python -m video_knowledge_pipeline.cli export-video-workbench outputs\test-video-workbench\bundle
rg -n -e "selectQueue" -e "QUEUE_GROUPS" -e "data-queue-key" -e "queue-detail-retry" -e "队列：" outputs\test-video-workbench\bundle\video-workbench.html outputs\test-video-workbench\bundle\video-workbench.json
git diff --check -- src\video_knowledge_pipeline\video_workbench.py tests\test_video_workbench.py
`

结果：

- Direct test runner: video_workbench_queue_detail_tests_ok。
- CLI smoke 成功生成 video-workbench.html/json。
- 产物中能看到 selectQueue、QUEUE_GROUPS、data-queue-key、queue-detail-retry、队列：。
- git diff --check 对本次代码/测试文件无报错。

边界：工作台仍然只是静态本地 UI；它展示和复制命令，不自动执行 ebook、tile、多模态、ASR 或 smart-summary 任务。
## Update - 2026-07-05 21:30:24 | Codex / GPT-5

### P0 continued: explicit queue routing for reused external modules

本轮继续把 vsummary-style run registry 和 BiliNote-style task panel 做实：task_console._run_queue_group 不再只靠几组隐式关键词，而是新增 QUEUE_GROUP_TOKENS 路由表，把已经复用和计划继续复用的外部模块稳定归到正确队列。

落地变化：

- src/video_knowledge_pipeline/task_console.py
  - 新增 QUEUE_GROUP_TOKENS；
  - 覆盖 ASR / transcript、document OCR / ebook / tile、vision / multimodal / local VLM、timeline / VideoRAG / memory、summary / content asset、review / sample review；
  - multimodal_sample_review / impact_report / human_review 优先归入 review，避免被普通 multimodal token 误归入视觉执行队列。
- tests/test_task_console.py
  - 新增 test_processing_queue_groups_external_reuse_run_types；
  - 覆盖实际 run_type：visual_structure_ebook、high_res_tile_plan、tile_result_merge、vision_review_queue、multimodal_frame_analysis、temporal_visual_analysis、`local_vlm_serving_smoke`、video_moment_index、video_rag_search、long_video_memory_pack、smart_summary_section_workflow、smart_summary_codex、external_capability_pack、review_closure_status、multimodal_sample_review 等。

验证：

```powershell
python -m py_compile src\video_knowledge_pipeline\task_console.py tests\test_task_console.py
$env:PYTHONPATH='src'; python -c "import importlib.util; spec=importlib.util.spec_from_file_location('ttc','tests/test_task_console.py'); mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); mod.test_processing_queue_groups_external_reuse_run_types(); print('queue_group_external_reuse_tests_ok')"
$env:PYTHONPATH='src'; python -c "import importlib.util, shutil; from pathlib import Path; spec=importlib.util.spec_from_file_location('ttc','tests/test_task_console.py'); mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); mod.test_processing_queue_groups_external_reuse_run_types(); d=Path('outputs/test-task-console-direct').resolve(); shutil.rmtree(d, ignore_errors=True); d.mkdir(parents=True, exist_ok=True); mod.test_export_task_console_writes_human_ui_and_agent_json(d); print('task_console_queue_group_tests_ok')"
$env:PYTHONPATH='src'; python -c "import importlib.util; spec=importlib.util.spec_from_file_location('tvw','tests/test_video_workbench.py'); mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); mod.test_export_video_workbench_writes_static_workspace(); mod.test_task_console_links_video_workbench(); print('video_workbench_after_queue_group_tests_ok')"
`

结果：

- queue_group_external_reuse_tests_ok
- task_console_queue_group_tests_ok
- video_workbench_after_queue_group_tests_ok

边界：这一步只改本地 run 分组和 UI 队列可解释性，不执行任何 ebook/OCR、多模态、ASR、VLM 或云调用。
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
## Update: 2026-07-05 23:25:41 | Codex / GPT-5

### 已落地：统一视频工作台接入 VideoRAG 多粒度 chunks

承接 `video-rag-pack` 的多粒度 JSONL，本轮把 `exports/video-rag-chunks.jsonl` 接入 `export-video-workbench` 和 `video-workbench.html` 的“片段搜索”。

新增能力：

- `export-video-workbench` 现在读取 `exports/video-rag-chunks.jsonl`，压缩为 `video-workbench.json.video_rag_chunks`。
- `video_rag_chunks` 保留：
  - `id`；
  - `chunk_kind`；
  - `text`；
  - `start/end` 与 `start_time/end_time`；
  - `timeline_indexes`；
  - `tags/keywords`；
  - `evidence_paths`；
  - `has_visual_evidence` / `has_temporal_evidence`。
- `video-workbench.html` 的“片段搜索”现在统一搜索两类来源：
  - `video-moment-index.json` 的 moment chunks；
  - `video-rag-chunks.jsonl` 的 `moment`、`visual_evidence`、`review_gap`、`content_asset` 等多粒度 chunks。
- 搜索结果显示 chunk 类型 badge、时间范围、关键词/标签、关联 timeline index 和证据路径。
- 点击搜索结果会优先跳到对应 timeline 行和视频时间点；没有 timeline index 的内容资产 chunk 仍可显示证据路径。
- 工作台 artifact cards 新增：
  - `video_rag_pack_markdown` -> `exports/video-rag-pack.md`；
  - `video_rag_search_markdown` -> `exports/video-rag-search.md`。

复用来源：

- VideoRAG 的 retrieval unit / evidence chunk 思路；
- BiliNote 的单页视频操作台；
- vsummary 的 artifact-first 产物入口；
- VKP 已有 review gap、visual evidence、content asset 数据结构。

验证：

`````powershell
python -m py_compile src\video_knowledge_pipeline\video_workbench.py tests\test_video_workbench.py
$env:PYTHONPATH='src'; python -c "import importlib.util; spec=importlib.util.spec_from_file_location('tvw','tests/test_video_workbench.py'); mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); mod.test_export_video_workbench_writes_static_workspace(); mod.test_task_console_links_video_workbench(); print('video_workbench_rag_chunk_search_tests_ok')"
$env:PYTHONPATH='src'; python -m video_knowledge_pipeline.cli export-video-workbench outputs\test-video-workbench\bundle
git diff --check -- src\video_knowledge_pipeline\video_workbench.py tests\test_video_workbench.py docs\external-code-reuse-remaining-modules-2026-07-05.md
```

结果：

- `py_compile` 通过。
- Direct test runner: `video_workbench_rag_chunk_search_tests_ok`。
- CLI smoke 成功生成 `video-workbench.html/json`，JSON 中包含 `video_rag_chunks`，artifact cards 包含视频 RAG 包/查询。
- `git diff --check` 对本轮相关文件无报错。

边界：这一步仍是静态本地 UI 和 JSONL 本地搜索，不启动 VideoRAG 完整服务，不接 graph/vector DB，不调用云模型，不处理新视频。
## Update: 2026-07-05 23:35:41 | Codex / GPT-5

### 已落地：智能总结章节工作流接入多粒度 VideoRAG citations

承接上一轮 `video-rag-chunks.jsonl` 接入工作台，本轮把多粒度 VideoRAG chunks 继续接入 `smart-summary-section-workflow` 和 `smart-summary-section-editor`。

新增能力：

- `smart-summary-section-workflow` 现在会读取 `exports/video-rag-chunks.jsonl`。
- 如果 JSONL 不存在，workflow 会本地调用 `video-rag-pack` 生成，不调用云模型、不启动向量库。
- 每个章节的 `citations` 现在由两类来源合并：
  - `video_moment_index`：原有 moment citation，继续优先保留；
  - `video_rag_chunks`：新增 `visual_evidence`、`review_gap`、`content_asset` 等多粒度 chunk citation。
- `citation_source` 新增：
  - `video_rag_chunk_count`；
  - `video_rag_chunks_by_kind`；
  - `video_rag_jsonl`。
- citation 字段新增/补齐：
  - `chunk_kind`；
  - `chunk_id`；
  - `tags`；
  - `keywords`；
  - `fact_status`。
- `review_gap` citation 明确标记为 `fact_status=review_gap_not_fact`，用于提醒章节重写时这是缺口/风险，不是事实证据。
- `smart-summary-section-editor.html` 的 citation 列表现在显示 source、chunk_kind 和 `fact_status` badge。

复用来源：

- VideoRAG 的多粒度 retrieval unit / evidence citation；
- RAGFlow-style citation-aware rewrite 输入；
- BiliNote/vsummary 的章节编辑和本地证据旁路；
- VKP 已有 review gap、visual evidence、content asset JSONL 结构。

验证：

`````powershell
python -m py_compile src\video_knowledge_pipeline\smart_summary_section_workflow.py src\video_knowledge_pipeline\smart_summary_section_editor.py tests\test_smart_summary_section_citations.py tests\test_smart_summary_section_editor.py
$env:PYTHONPATH='src'; python -c "import importlib.util; spec=importlib.util.spec_from_file_location('tc','tests/test_smart_summary_section_citations.py'); mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); mod.test_smart_summary_section_workflow_injects_moment_citations(); mod.test_smart_summary_section_workflow_builds_video_rag_chunks_when_missing(); print('smart_summary_section_rag_citation_tests_ok')"
$env:PYTHONPATH='src'; python -c "import importlib.util; spec=importlib.util.spec_from_file_location('te','tests/test_smart_summary_section_editor.py'); mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); mod.test_smart_summary_section_editor_writes_static_review_ui(); print('smart_summary_section_editor_citation_badge_test_ok')"
```

结果：

- `py_compile` 通过。
- Direct test runner: `smart_summary_section_rag_citation_tests_ok`。
- Direct test runner: `smart_summary_section_editor_citation_badge_test_ok`。

边界：这一步仍是本地 JSONL citation 注入；不调用在线 LLM、不启动 VideoRAG 完整服务、不接 graph/vector DB、不把 review gap 当事实。
## Update: 2026-07-05 23:51:10 | Codex / GPT-5

### 已落地：long-video memory pack 接入 VideoRAG chunks

继续吸收 MovieChat 的 short/long memory 和 VideoRAG 的 retrieval unit 思路，本轮把 long-video-memory-pack 从独立产物推进到可检索证据层：

- `video-rag-pack` 现在会优先读取 `exports/long-video-memory-pack.json`，若不存在则本地生成，不调用云模型、不启动向量库。
- `exports/video-rag-chunks.jsonl` 新增四类 memory chunk：
  - short_memory：局部时间窗记忆，保留 timeline indexes、moment index、证据路径；
  - chapter_memory：跨多个 short memory 的章节记忆，保留 child_memory_ids 和 child_moment_indexes；
  - 	heme_memory：按章节压缩出的主题路线图，方便先命中主题再展开片段；
  - memory_boundary：低置信/缺视觉证据边界，标记 `fact_status=memory_boundary_review_gap`，不当事实使用。
- `video-rag-search` 返回 memory 层级字段：memory_level、memory_id、parent_memory_id、child_memory_ids、child_moment_indexes、`fact_status`。
- 搜索排序对 chapter_memory / 	heme_memory 给轻量加权，让长视频查询能先命中章节/主题，再展开到具体片段和证据。
- 搜索 Markdown 报告会显示 memory 层级、子 memory、子 moment 和 fact status。

验证：

```powershell
python -m py_compile src\video_knowledge_pipeline\video_rag_pack.py src\video_knowledge_pipeline\video_rag_search.py tests\test_external_video_reuse_modules.py
$env:PYTHONPATH='src'; python -c "import importlib.util, shutil; from pathlib import Path; spec=importlib.util.spec_from_file_location('t','tests/test_external_video_reuse_modules.py'); mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); base=Path('outputs/test-video-rag-memory-direct').resolve(); shutil.rmtree(base, ignore_errors=True); (base/'a').mkdir(parents=True, exist_ok=True); (base/'b').mkdir(parents=True, exist_ok=True); mod.test_video_rag_pack_writes_jsonl_retrieval_units(base/'a'); mod.test_video_rag_search_reads_jsonl_and_writes_search_artifacts(base/'b'); print('video_rag_memory_direct_tests_ok')"
`

结果：

- py_compile 通过。
- Direct test runner: ideo_rag_memory_direct_tests_ok。

边界：这一步仍是本地 JSONL 检索增强；不启动 VideoRAG 完整服务、不接 graph/vector DB、不调用在线模型、不重新处理真实视频。
## Update: 2026-07-06 00:00:22 | Codex / GPT-5

### 已落地：video-workbench 展示 memory -> moment -> evidence 层级

承接 long-video memory 写入 VideoRAG chunks，本轮把 memory 层级继续接进统一视频工作台：

- `export-video-workbench` 的 `video-workbench.json.video_rag_chunks[]` 现在保留：
  - `memory_level`；
  - `memory_id`；
  - `parent_memory_id`；
  - `child_memory_ids`；
  - `child_moment_indexes`；
  - `fact_status`。
- `video-workbench.html` 的片段搜索会把 `chapter_memory` / `theme_memory` 命中显示为层级线：
  - `memory=chapter/L001 -> child memory=M0001,M0002 -> child moment=1,2`。
- 搜索文本也会索引 memory id、parent memory、child memory、child moment 和 fact status。
- 点击 memory 命中仍会跳到对应视频时间点，并优先选中关联 timeline row。
- `review_gap` / `memory_boundary` 仍只作为待复核或风险，不作为事实证据。

验证：

`````powershell
python -m py_compile src\video_knowledge_pipeline\video_workbench.py tests\test_video_workbench.py
$env:PYTHONPATH='src'; python -c "import importlib.util; spec=importlib.util.spec_from_file_location('tvw','tests/test_video_workbench.py'); mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); mod.test_export_video_workbench_writes_static_workspace(); print('video_workbench_memory_hierarchy_direct_test_ok')"
```

结果：

- `py_compile` 通过。
- Direct test runner: `video_workbench_memory_hierarchy_direct_test_ok`。

边界：这一步仍是静态本地 UI；不启动 VideoRAG 服务、不接向量库、不调用云模型、不处理新视频。
## Update: 2026-07-06 00:15:00 | Codex / GPT-5

### 已落地：人工抽样评分与多模态效果评估闭环

继续吸收 Peepshow / VidClaude 的人工抽样评价思路，本轮把 `multimodal-sample-review` 从“标注页面 + 汇总报告”推进到稳定的人类质量评估产物：

- `multimodal-sample-review.html` 新增五个评分维度：
  - 术语/工具名准确；
  - 画面事实准确；
  - 步骤/流程完整；
  - 时间戳准确；
  - 是否必须保留图片。
- `multimodal-sample-review.todo.json` 和导出的 notes JSON 会包含这些字段。
- `validate-multimodal-sample-notes` 继续生成 `multimodal-sample-review-summary.md/json`，并新增：
  - `human-sample-eval.json`；
  - `human-sample-eval.md`。
- `human-sample-eval` 汇总：
  - term accuracy accept rate；
  - visual fact accuracy accept rate；
  - step completeness accept rate；
  - timestamp accuracy accept rate；
  - keep image required rate；
  - multimodal added key info rate；
  - hallucination/error rate；
  - human-sampled multimodal net help proxy。
- `task-console.html` 和 `video-workbench.html` 都会把 `human-sample-eval.md` 作为可打开 artifact。

验证：

`````powershell
python -m py_compile src\video_knowledge_pipeline\multimodal_sample_review.py src\video_knowledge_pipeline\task_console.py src\video_knowledge_pipeline\video_workbench.py tests\test_multimodal_sample_review.py
$env:PYTHONPATH='src'; python -c "import importlib.util, shutil; from pathlib import Path; spec=importlib.util.spec_from_file_location('tm','tests/test_multimodal_sample_review.py'); mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); base=Path('outputs/test-multimodal-sample-eval-direct').resolve(); shutil.rmtree(base, ignore_errors=True); base.mkdir(parents=True, exist_ok=True); mod.test_multimodal_sample_review_writes_static_ui_and_notes_template(base/'a'); mod.test_task_console_links_multimodal_sample_review(base/'b'); mod.test_validate_multimodal_sample_notes_summarizes_human_labels(base/'c'); mod.test_validate_multimodal_sample_notes_reports_invalid_rows(base/'d'); print('multimodal_sample_eval_direct_tests_ok')"
```

结果：

- `py_compile` 通过。
- Direct test runner: `multimodal_sample_eval_direct_tests_ok`。

边界：这一步只是人工抽样质量评估，不直接写 timeline，不自动发布，不调用云模型。它回答的是“人工抽样下的多模态收益”，不是严格随机实验因果估计。
### 状态更新：P2 本地 VLM adapter smoke 已增强

本轮继续吸收 Qwen2.5-VL / InternVL / LLaVA-OneVision 的服务化接入经验，但仍不把模型仓库代码嵌进 VKP：

- `local-vlm-serving-smoke` 现在输出本地 VLM 能力矩阵：OpenAI-compatible endpoint、文本 JSON、单图 JSON、多图 JSON、短帧组 JSON。
- 默认 preview 只写计划和报告，不启动模型服务、不修改 timeline、不调用云端。
- 新增输入规格字段：`max_images`、`image_probe_max_edge`、`image_probe_jpeg_quality`、`short_frame_group_target_count`。
- 当 bundle 有 `temporal_frame_paths` 时，会选取同一片段的短帧组作为本地 VLM smoke 样本证据。
- 写入 `local-vlm-serving-smoke.md/json`、`mcp-local-vlm-serving-smoke.args.json`，并登记到 bundle `manifest.json`。
- CLI / MCP 均支持 `image_probe_max_edge`、`image_probe_jpeg_quality`、`frame_group_count` 参数。

这一步把“本地 VLM 可否替代云多模态”的检查变成了可审计产物。下一步优先级顺延到 P3 可替换检索后端，或者继续把本地 VLM smoke 状态显示到 workbench 的 provider 面板。

### 状态更新：P3 可替换检索后端 v1 已落地

继续吸收 VideoRAG 的 retrieval backend 分层思路，本轮没有引入重型向量库，而是在现有本地 JSONL 检索上增加可替换后端参数：

- `video-rag-search` 新增 `retrieval_backend=keyword|sqlite|vector`。
- 默认仍是 `keyword`，直接读 `exports/video-rag-chunks.jsonl`。
- `sqlite` 会写 `exports/video-rag-index.sqlite`，用 stdlib SQLite 持久化 chunks，再复用当前可解释词法排序。
- `vector` 目前只作为 future adapter 占位，明确回退 keyword，不启动向量服务。
- CLI 新增 `--retrieval-backend`，MCP 新增 `video_rag_search` / `video_rag_search_tool`。
- `mcp-video-rag-search.args.json` 会记录实际后端，manifest 增加 `video_rag_search_backend` 和可选 `video_rag_sqlite_index`。

这一步让 VideoRAG 检索层具备“默认轻、本地持久、未来可换向量”的结构。下一步可以把 SQLite/backend 状态显示到 `video-workbench.html` 的片段搜索面板，或继续补内容素材候选模板。

### 状态更新：VideoRAG backend 状态接入 workbench

承接 P3 可替换检索后端，本轮把检索后端状态从 CLI/JSON 推进到人类可用的 `video-workbench.html`：

- `export-video-workbench` 新增 `video_workbench.json.video_rag_status`。
- 状态字段包括：`retrieval_backend`、`requested_retrieval_backend`、`backend_status`、`sqlite_index_exists`、`search_report_exists`、`no_vector_backend_started`。
- “片段搜索”面板会显示当前检索后端、SQLite index 是否已生成、search report 是否存在、是否未启动向量后端。
- 这一步不改变搜索逻辑、不启动服务、不调用云；只是把 VideoRAG backend 的可审计状态放到统一工作台里。

验证：

`````powershell
python -m py_compile src\video_knowledge_pipeline\video_workbench.py tests\test_video_workbench.py
$env:PYTHONPATH='src'; python -c "import importlib.util; spec=importlib.util.spec_from_file_location('tvw','tests/test_video_workbench.py'); mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); mod.test_export_video_workbench_writes_static_workspace(); print('video_workbench_rag_backend_status_direct_test_ok')"
```

结果：

- `py_compile` 通过。
- Direct test runner: `video_workbench_rag_backend_status_direct_test_ok`。

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

### 已文档化：外部开源项目模块级复用总清单

新增 `docs/external-open-source-reuse-module-inventory-2026-07-06.md`，作为后续判断“还有哪些值得复用的代码模块”的最新入口。

这份总清单把已审查项目拆成三类：

- 已基本榨干：vsummary provider/stage/run/citation、BiliNote 字幕/编辑、VideoRAG/VTimeLLM 时间定位、Qwen/InternVL 图像预处理等；
- 还能继续榨：human sample eval 工作台可视化、smart-summary evidence trace、run artifact registry 全覆盖、ASR 仲裁后处理、citation 注入最终总结、本地 VLM smoke；
- 不建议继续搬：整套 React/FastAPI 后端、重型 graph/vector 后端、模型源码内嵌、下载后端、默认全帧云多模态。

当前推荐下一步仍是：把 `human-sample-eval` 信号显示到 `video-workbench.html` 的内容素材候选面板，并支持“未抽样 / 证据不足 / 可继续加工”过滤。
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

下一步优先级顺延为：继续把 run artifact registry 覆盖到更多长任务，或把本地 VLM smoke/provider 状态显示到 workbench provider 面板。## Update: 2026-07-06 08:42:42 | Codex / GPT-5

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
## Update - 2026-07-06 18:05:00 | Codex GPT-5

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

### P0 continued: video-workbench external reuse capability status panel

承接上一轮 external reuse run artifact 登记，本轮把这些已经吸收进 VKP 的外部开源项目能力直接接进统一视频工作台。现在 `export-video-workbench` 不只显示 timeline、内容素材候选、Provider / 本地 VLM 状态，也会在 `video-workbench.html` 左栏显示“外部复用能力”面板。

新增 `video-workbench.json.external_reuse_status`：

- `schema = video_knowledge_pipeline.external_reuse_workbench_status.v1`
- `status / ready_count / action_required_count / missing_count`
- `capabilities[]` 按能力而不是按文件列出：
  - `time_localization`：VTimeLLM / VideoRAG 风格的时间定位、片段索引和时间轴审计。
  - `long_video_memory`：MovieChat 风格的长视频 memory pack。
  - `video_rag`：VideoRAG 本地 JSONL/SQLite 检索包、查询报告和显式 HTTP service plan。
  - `local_vlm_adapter`：Qwen/InternVL/LLaVA-style 本地 VLM adapter / provider smoke。
  - `content_capability`：vsummary + BiliNote + VKP content assets 的素材能力包。
- 每类能力会汇总：`run_count`、`action_required`、`failed_count`、`status_counts`、`retry_commands`、相关 artifact links。

工作台 UI 行为：

- 显示 ready / action_required / missing 状态。
- 直接链接相关产物，例如 `video-rag-service-plan.md`、`external-capability-pack.md`、`video-moment-index.md`。
- 显示第一条 retry command，支持复制。
- 可跳到对应处理队列查看更细的 run / failed_items。

边界：

- 这是只读工作台展示，不执行命令。
- 不启动 VideoRAG HTTP 服务。
- 不启动本地 VLM。
- 不调用云 provider。
- 不处理新视频。

代码落地：

- `src/video_knowledge_pipeline/video_workbench.py`
- `tests/test_video_workbench.py`

验证：

```powershell
python -m py_compile src\video_knowledge_pipeline\video_workbench.py tests\test_video_workbench.py

$env:PYTHONPATH='src'; python -c "import importlib.util; spec=importlib.util.spec_from_file_location('tvw','tests/test_video_workbench.py'); mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); mod.test_export_video_workbench_writes_static_workspace(); print('video_workbench_external_reuse_status_direct_test_ok')"
```

本轮验证结果：

- `py_compile` 通过。
- 直接调用 `test_export_video_workbench_writes_static_workspace()` 通过。
- 生成的 `video-workbench.html` 包含“外部复用能力”、`时间定位 / VTimeLLM`、`长视频 memory / MovieChat`、`VideoRAG 本地检索`、`内容素材能力包`、`start video rag service`、`retry external capability pack`。

下一步优先级顺延为：继续补真实执行器的 run artifact `failed_items / retry_command / next_actions`，尤其是 ebook 批次、tile OCR、vision review queue、smart-summary section workflow，使外部复用面板和处理队列在真实 bundle 上更接近“一眼知道下一步做什么”。
## Update: 2026-07-06 19:05:00 | Codex / GPT-5

### P0 continued: subqueue-action-plan gains scheduler-grade action semantics

承接 vsummary task status / run artifact registry 的复用方向，本轮把 `subqueue-action-plan` 从“把 retry command 列出来”推进成更适合 UI、MCP、OpenClaw/agent 读取的只读调度单。

新增字段：

- `action_status`：从子队列 `status_counts` 中抽取真实动作状态，例如 `needs_input`、`needs_review`、`needs_retry`、`needs_execution`，避免只看到笼统的 `action_required`。
- `action_kind`：把状态翻译成调度语义：
  - `operator_input_required`
  - `human_review_required`
  - `retry_available`
  - `explicit_execution_required`
  - `blocked_or_failed`
  - `retry_command_missing`
  - `execution_plan_missing`
- `priority`：调度排序字段，阻塞/人工输入/复核优先于普通重试，显式执行项后置。
- `primary_command`：该子队列第一条可复制命令。
- `blocked_reason`：从 `failed_items_preview` 或 next action 中抽取最短原因。
- `safe_execution_hint`：告诉人和 agent 这条是人工输入、人工复核、可复制执行，还是需要先看 run.md。
- `machine_action_available` / `operator_review_required`：机器可继续执行和人工必须介入的布尔分流。

这一步保留边界：

- `subqueue-action-plan` 仍然不执行任何命令。
- 不启动 ASR、ebook、OCR、VLM、VideoRAG service。
- 不调用云 provider。
- 不绕过每个命令自己的 `--execute` / preflight / 人工确认边界。

代码落地：

- `src/video_knowledge_pipeline/task_console.py`
- `tests/test_task_console.py`

验证：

```powershell
python -m py_compile src\video_knowledge_pipeline\task_console.py tests\test_task_console.py

$env:PYTHONPATH='src'; python -c "import importlib.util, shutil; from pathlib import Path; spec=importlib.util.spec_from_file_location('ttc','tests/test_task_console.py'); mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); d=Path('outputs/test-task-console-action-plan-direct').resolve(); shutil.rmtree(d, ignore_errors=True); d.mkdir(parents=True, exist_ok=True); mod.test_export_task_console_writes_human_ui_and_agent_json(d); print('task_console_action_plan_direct_test_ok')"

$env:PYTHONPATH='src'; python -m video_knowledge_pipeline.cli subqueue-action-plan outputs\test-task-console-action-plan-direct\bundle --no-refresh
```

本轮验证结果：

- `py_compile` 通过。
- 直接调用 task console 测试通过。
- CLI smoke 成功输出 28 条子队列动作，能区分 `operator_input_required`、`human_review_required`、`retry_available`、`explicit_execution_required`。

下一步优先级顺延为：把这些 action semantics 接到 `video-workbench` 或 OpenClaw live smoke 的下一步展示，或者继续补真实执行器的 run artifact 质量，让 `blocked_reason` 和 `primary_command` 更贴近真实视频处理现场。

## Update: 2026-07-06 19:35:00 | Codex / GPT-5

### P0 continued: video-workbench reuses subqueue action plan as the next-step panel

承接上一轮 `subqueue-action-plan` 的调度语义，本轮把同一份 agent-readable action plan 接入 `video-workbench.html/json`，让统一视频工作台也能直接显示“下一步调度”，而不是只在 task console 里可见。

落地内容：

- `export-video-workbench` 现在复用 task console 的 `_build_subqueue_action_plan(processing_queue)`。
- `video-workbench.json` 新增 `subqueue_action_plan`，字段与 CLI/MCP `subqueue-action-plan` 保持一致：
  - `action_status`
  - `action_kind`
  - `priority`
  - `primary_command`
  - `blocked_reason`
  - `safe_execution_hint`
  - `machine_action_available`
  - `operator_review_required`
- `video-workbench.html` 左栏新增“下一步调度”面板，展示最高优先级的子队列动作、原因、安全提示和首选命令复制按钮。

复用原则：

- 不在 workbench 里复制第二套调度规则。
- task console、CLI/MCP、video-workbench 共用同一份 subqueue action plan 逻辑。
- workbench 仍然是静态只读 UI，不执行命令，不调用云模型，不启动 VideoRAG、本地 VLM 或 ASR。

代码落地：

- `src/video_knowledge_pipeline/video_workbench.py`
- `tests/test_video_workbench.py`

验证：

```powershell
python -m py_compile src\video_knowledge_pipeline\video_workbench.py tests\test_video_workbench.py src\video_knowledge_pipeline\task_console.py tests\test_task_console.py

$env:PYTHONPATH='src'; python -c "import importlib.util; spec=importlib.util.spec_from_file_location('tvw','tests/test_video_workbench.py'); mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); mod.test_export_video_workbench_writes_static_workspace(); print('video_workbench_subqueue_action_plan_direct_test_ok')"
```

本轮验证结果：

- `py_compile` 通过。
- 直接调用 `test_export_video_workbench_writes_static_workspace()` 通过。
- fixture 证明 `video-workbench.json.subqueue_action_plan` 能识别 `timeline_rag:video_rag` 为 `explicit_execution_required`，`summary_export:content_candidate` 为 `operator_input_required`。
- 生成的 `video-workbench.html` 包含“下一步调度”、`explicit_execution_required`、`operator_input_required`、`复制首选命令`。

下一步优先级顺延为：继续提高真实执行器 run artifact 的质量，优先补 ebook/tile/vision/smart-summary section 的 `failed_items`、`blocked_reason` 和 `primary_command` 质量，让调度面板在真实长视频 bundle 上更像生产队列。
## Update: 2026-07-06 21:45:50 | Codex / GPT-5

### P0 continued: vision-review-queue run artifact now carries batch-level action items

承接 vsummary task status / retry queue 的复用方向，本轮把 `vision-review-queue` 的运行产物从“队列有失败/可重试”推进成“每个待处理索引都能回到具体批次和命令”。

新增/强化内容：

- `runs/vision-review-queue/run.json.failed_items` 现在会记录所有 pending indexes，而不只是已经失败的 indexes。
- 每条 failed/action item 带上：
  - `index`
  - `batch_id`
  - `batch_status`
  - `reason`
  - `pending_indexes`
  - `suggested_next_tool`
  - `suggested_retry_command`
- 失败过或解析不完整的视觉结果标记为 `visual_understanding_failed_or_incomplete`。
- 从未执行过的候选标记为 `visual_understanding_pending`。
- run artifact 的 `retry_command` 优先指向第一个 `pending/partial/failed` 批次的真实 `-Execute` 命令，而不是只兜底指向整队列 run script。
- `task-console` / `subqueue-action-plan` 因此可以显示更具体的 `blocked_reason` 和 `primary_command`，例如 `Batch 1 pending indexes: 3,1`。

边界保持不变：

- `vision-review-queue` 只生成队列、报告、HTML、PowerShell 命令和 run artifact。
- 不自动发送帧到云 provider。
- 真正调用多模态仍必须运行带 `-Execute` 的批次脚本，且 provider/env key 不写进产物。

代码落地：

- `src/video_knowledge_pipeline/vision_review_queue.py`
- `tests/test_vision_review_queue.py`

验证：

```powershell
python -m py_compile src\video_knowledge_pipeline\vision_review_queue.py tests\test_vision_review_queue.py src\video_knowledge_pipeline\task_console.py tests\test_task_console.py

$env:PYTHONPATH='src'; python -c "import importlib.util, shutil; from pathlib import Path; spec=importlib.util.spec_from_file_location('tvq','tests/test_vision_review_queue.py'); mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); d=Path('outputs/test-vision-review-queue-run-artifact-direct').resolve(); shutil.rmtree(d, ignore_errors=True); d.mkdir(parents=True, exist_ok=True); mod.test_vision_review_queue_batches_pending_and_failed_items(d); mod.test_task_console_links_vision_review_queue(d / 'console'); print('vision_review_queue_run_artifact_quality_direct_tests_ok')"
```

本轮验证结果：

- `py_compile` 通过。
- 直接调用 `test_vision_review_queue_batches_pending_and_failed_items()` 通过。
- 直接调用 `test_task_console_links_vision_review_queue()` 通过。
- 样例 run artifact 证明：`failed_items` 同时包含 `visual_understanding_failed_or_incomplete` 和 `visual_understanding_pending`，并带有批次级 `suggested_retry_command`。

下一步优先级顺延为：继续补 ebook / tile OCR / smart-summary section workflow 的 run artifact failed items，让所有真实执行器都能被 task console、video-workbench、MCP agent 用同一种方式调度。
## Update: 2026-07-06 22:20:00 | Codex / GPT-5

### P0 continued: smart-summary section workflow now registers section-level input actions

承接 BiliNote 章节编辑和 vsummary staged generation 的复用方向，本轮把 `smart-summary-section-workflow` 的 run artifact 从“需要重试”调整为更准确的“章节修订需要输入”。

改动点：

- 当章节需要重写时，run status 从 `needs_retry` 改为 `needs_input`。
- 每个待重写章节会写入 `runs/smart-summary-section-workflow/run.json.failed_items`，字段包括：
  - `section_id` / `chapter_index`
  - `title`
  - `time_range`
  - `reason=section_revision_pending`
  - `reasons`
  - `citation_count`
  - `rewrite_prompt_preview`
  - `todo_json`
  - `workflow_markdown`
  - `editor_html`
  - `suggested_next_tool=smart_summary_section_editor`
  - `suggested_retry_command`
  - `suggested_apply_command`
- run artifact 的 `retry_command` 在有待修订章节时优先指向：

```powershell
.\scripts\video-knowledge.ps1 smart-summary-section-editor <webui-bundle>
```

而不是简单重跑 `smart-summary-section-workflow`。

为什么这样更合理：

- 章节缺质量不是“机器重试”就一定能解决，而是需要 Codex/LLM/人工提供修订文本。
- `subqueue-action-plan` 现在会把 summary/export 的 `section_workflow` 识别成 `operator_input_required`。
- task console / video-workbench 后续能直接显示“打开章节编辑器 -> 下载/保存修订 JSON -> apply -> generate smart summary”的生产线动作。

边界：

- 不调用在线 LLM。
- 不改写 `smart-summary.md`。
- 不自动应用章节修订。
- 只把待修订章节和下一步命令写入本地 run artifact。

代码落地：

- `src/video_knowledge_pipeline/smart_summary_section_workflow.py`
- `tests/test_smart_summary_section_citations.py`
- `tests/test_task_console.py`

验证：

```powershell
python -m py_compile src\video_knowledge_pipeline\smart_summary_section_workflow.py tests\test_smart_summary_section_citations.py src\video_knowledge_pipeline\task_console.py tests\test_task_console.py

$env:PYTHONPATH='src'; python -c "import importlib.util; spec=importlib.util.spec_from_file_location('tcit','tests/test_smart_summary_section_citations.py'); mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); mod.test_smart_summary_section_workflow_injects_moment_citations(); mod.test_smart_summary_section_workflow_builds_video_rag_chunks_when_missing(); print('smart_summary_section_workflow_action_items_direct_tests_ok')"

$env:PYTHONPATH='src'; python -c "import importlib.util, shutil; from pathlib import Path; spec=importlib.util.spec_from_file_location('ttask','tests/test_task_console.py'); mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); base=Path('outputs/test-task-console-section-workflow-action').resolve(); shutil.rmtree(base, ignore_errors=True); base.mkdir(parents=True, exist_ok=True); mod.test_export_task_console_writes_human_ui_and_agent_json(base); print('task_console_section_workflow_direct_test_ok')"
```

本轮验证结果：

- `py_compile` 通过。
- smart-summary section workflow citation/action item 直接测试通过。
- task console 直接测试通过，`summary_export:section_workflow` 会被识别为 `operator_input_required`。

下一步优先级顺延为：继续补 ebook 批次和 visual-structure ebook run artifact 的 failed/action items，让图文解析分支也能像 vision queue、tile queue、section workflow 一样给出具体可操作命令。
## Update: 2026-07-06 22:55:00 | Codex / GPT-5

### P0 continued: visual-structure ebook blockers now expose concrete recovery actions

承接 `ebook_markdown_pipeline` 复用和 high-res tile recovery 的方向，本轮把 `run-visual-structure --execute-ebook-pipeline` 的 run artifact failed items 从“有 blocker”推进成“每个 blocker 都有下一步动作”。

新增/强化字段：

- `evidence_paths`：保留 frame、ebook output dir、artifact path。
- `ebook_retry_command`：对同一个 timeline index 重新运行 `run-visual-structure --execute-ebook-pipeline --indexes <index>`。
- `review_command`：进入 `prepare-review-session --group-by reason`。
- tile 可恢复 blocker（`ocr_wrapper_only`、`ocr_text_empty`、`ocr_text_low_information`）额外带：
  - `suggested_next_tool=high_res_tile_plan`
  - `tile_recovery_command`
  - `multimodal_triage_command`
- 非 tile blocker（例如 `umi_ocr_missing`、`ebook_pipeline_unavailable`、timeout、artifact missing）带：
  - `suggested_next_tool=run_visual_structure_plan`
  - `suggested_retry_command` 指向修复 ebook pipeline 后的同 index 重跑命令。

这一步让 document OCR / ebook 子队列更接近可操作生产线：

```text
ebook blocker -> 修 ebook 后单 index 重跑 / high-res tile / 多模态 triage / 人工 review
```

边界：

- 不运行真实 ebook pipeline。
- 不运行 tile OCR/VLM。
- 不调用云多模态。
- 不把 wrapper-only / 空 OCR 当作成功。
- 只是把下一步动作写进本地 `runs/visual-structure-ebook/run.json`。

代码落地：

- `src/video_knowledge_pipeline/visual_structure.py`
- `tests/test_screen_text_recovery.py`

验证：

```powershell
python -m py_compile src\video_knowledge_pipeline\visual_structure.py tests\test_screen_text_recovery.py

$env:PYTHONPATH='src'; python -c "import importlib.util, shutil; from pathlib import Path; spec=importlib.util.spec_from_file_location('tst','tests/test_screen_text_recovery.py'); mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); Monkey=type('Monkey',(),{'setattr':lambda self,obj,name,value:setattr(obj,name,value)}); monkey=Monkey(); base=Path('outputs/test-visual-structure-ebook-action-items').resolve(); shutil.rmtree(base, ignore_errors=True); (base/'one').mkdir(parents=True, exist_ok=True); (base/'two').mkdir(parents=True, exist_ok=True); mod.test_visual_structure_classifies_umi_ocr_missing_blocker(monkey, base/'one'); mod.test_visual_structure_rejects_synthetic_ebook_wrapper(monkey, base/'two'); print('visual_structure_ebook_action_items_direct_tests_ok')"
```

本轮验证结果：

- `py_compile` 通过。
- `umi_ocr_missing` blocker 现在包含 `suggested_next_tool=run_visual_structure_plan`、同 index ebook retry command、evidence path 和 review command。
- `ocr_wrapper_only` blocker 继续指向 `high_res_tile_plan`，同时保留 ebook retry、multimodal triage 和 review fallback。
- 直接测试通过。

下一步优先级顺延为：继续把 `screen_text_recovery` / crop OCR 或 `high_res_tile_plan` 的 action items 接得更细，或者把这些新 action fields 显示到 task-console/document_ocr 子队列的 HTML 详情里。
## Update: 2026-07-06 23:25:00 | Codex / GPT-5

### P0 continued: task console now surfaces failed-item action commands

承接上一轮 `visual_structure_ebook` failed item 增强，本轮把这些 action fields 接入 `task-console` 和 `subqueue-action-plan`，避免下一步命令只藏在 `runs/*/run.json`。

改动点：

- `_compact_failed_items` 不再只保留 `index/reason/detail`，还会保留：
  - `suggested_next_tool`
  - `suggested_next_reason`
  - `suggested_retry_command`
  - `ebook_retry_command`
  - `tile_recovery_command`
  - `multimodal_triage_command`
  - `review_command`
  - `suggested_apply_command`
  - `evidence_path_count`
  - `first_evidence_path`
- `_group_retry_commands` 会优先收集 failed item 里的具体命令，再退回 run-level `retry_command`。
- `document_ocr:ebook` 子队列的 `primary_command` 可以直接变成具体的 high-res tile / ebook retry 命令。
- HTML 失败项标签会显示 `next:<tool>` 和 evidence 数量，例如 `next:high_res_tile_plan / evidence:2`。

这一步吸收的是 vsummary task queue / BiliNote task panel 的核心操作感：队列里不仅有状态，还要有可以复制的下一步动作。

边界：

- task console 仍然只读。
- 不运行 ebook、OCR、tile、VLM 或云 API。
- 只是让 UI/MCP/OpenClaw 能从同一份 action plan 读到具体命令。

代码落地：

- `src/video_knowledge_pipeline/task_console.py`
- `tests/test_task_console.py`

验证：

```powershell
python -m py_compile src\video_knowledge_pipeline\task_console.py tests\test_task_console.py

$env:PYTHONPATH='src'; python -c "import importlib.util, shutil; from pathlib import Path; spec=importlib.util.spec_from_file_location('ttask','tests/test_task_console.py'); mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); base=Path('outputs/test-task-console-failed-action-fields').resolve(); shutil.rmtree(base, ignore_errors=True); base.mkdir(parents=True, exist_ok=True); mod.test_export_task_console_writes_human_ui_and_agent_json(base); print('task_console_failed_action_fields_direct_test_ok')"
```

本轮验证结果：

- `py_compile` 通过。
- task console 直接测试通过。
- fixture 证明 `document_ocr:ebook.primary_command` 会优先使用 failed item 的 `suggested_retry_command`，而不是泛泛的 run retry command。
- HTML 中能显示 `next:high_res_tile_plan`。

下一步优先级顺延为：继续把 `screen_text_recovery` / crop OCR 和 `high_res_tile_plan` 的 failed/action items 补到同样粒度，或把 task console 的 action command bundle 做成更适合批量复制/重试的按钮组。

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

新增 `docs/external-code-reuse-next-code-modules-2026-07-06.md`，作为本 backlog 的执行级补充。它不再按外部项目泛泛罗列，而是按 VKP 下一批可落地模块拆分：

1. 质量抽样独立面板；
2. 剩余长任务 run artifact failed_items 全覆盖；
3. BiliNote-style 视频同屏编辑体验；
4. 章节级智能总结工作流；
5. VideoRAG 搜索跳转和 content candidate 双向回链；
6. ASR/字幕后处理；
7. high-res tile / 局部小字恢复；
8. 本地 VLM adapter 实机 smoke；
9. 内容素材候选复核 UI。

每项都写明参考来源、可复用代码形态、VKP 落点、验收标准和停止条件。后续继续实现外部代码复用时，优先从该执行队列取下一项，而不是重新扩大搜索范围或整体搬迁外部项目。
