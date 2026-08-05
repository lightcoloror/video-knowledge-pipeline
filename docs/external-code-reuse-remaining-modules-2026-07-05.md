# 外部开源项目剩余可复用模块清单

更新记录：

- 2026-07-05 23:39:42 | Codex / GPT-5：追加模块级榨干清单 v2，明确已落地的 VideoRAG/workbench/citation 能力、仍值得复用的具体代码模块、优先级和不再建议整体迁移的边界。
- 2026-07-05 20:10:50 | Codex / GPT-5：根据已审查的 vsummary、PrideWood/BiliNote、VideoRAG、MovieChat、VTimeLLM、Qwen-VL、InternVL、LLaVA-OneVision、WhisperX、FunASR/SenseVoice、Peepshow/VidClaude 等项目，整理 VKP 还能继续吸收的低耦合代码模块和不再建议整体搬运的方向。

## 结论

VKP 目前不缺“再找一个完整视频总结项目替换自己”，真正还值得榨的是这些项目里已经证明有效的局部模块：

1. 统一视频工作台：把视频播放器、时间轴、转写编辑、OCR/ebook、视觉复核、智能总结章节编辑、任务历史放到同一个静态页面。
2. 批次任务队列：把 ebook、tile、多模态、ASR、smart-summary section rewrite 变成可见、可重试、可分批的队列。
3. 字幕/ASR/平台字幕多源仲裁后处理：已落地 v1，下一步补 UI、标点、说话人、术语词典和 review pack。
4. 长视频分层总结：把 full transcript、chapter pack、moment index、long-video memory、RAG citation 合成稳定 smart-summary 输入包。
5. 视频 RAG 与时间定位：默认本地 JSONL/词法检索，必要时再接向量库；重点是时间戳和证据路径。
6. 本地 VLM adapter：不把模型源码塞进 VKP，只做 OpenAI-compatible / HTTP / subprocess adapter 和输入预处理。
7. 人工抽样评分 UI：量化 ebook、多模态、ASR 仲裁、术语纠错对最终人类可读文件准确率的贡献。

## 已经吸收较充分的模块

| 来源项目 | 已吸收模块 | VKP 当前对应入口 | 继续价值 |
| --- | --- | --- | --- |
| `alpha03123/vsummary` | OpenAI-compatible 文本网关、stage cache、run artifact、Windows CUDA 检测、视频 seek/citation 交互 | `text_llm_gateway.py`、`stage_cache.py`、`run_artifact_registry.py`、`cuda_runtime.py`、`task-console.html` | 主要价值已吸收；后续只继续借任务队列和 UI 细节 |
| `PrideWood/bilinote` | 字幕解析清洗、短句合并、转写校对 prompt、mind-map prompt、transcript editor、章节编辑体验 | `bilinote_transcript_tools.py`、`bilinote_summary_tools.py`、`transcript_correction_pack.py`、`transcript_editor.py`、`smart_summary_section_editor.py` | UI/工作台仍可继续吸收 |
| VideoRAG / VTimeLLM | moment chunk、时间定位、citation schema | `video_moment_index.py`、`video_rag_pack.py`、`video_rag_search.py`、smart-summary citations | 下一步应把 citation 更自然注入最终总结和工作台 |
| Qwen-VL / InternVL | 图像缩放、多图输入、dynamic tiling 思路 | `vlm_preprocess.py`、`high_res_tile_plan.py`、`tile_result_import_builder.py`、`tile_result_merge.py` | 后续适合作为本地 VLM adapter 的输入层 |
| FunASR / SenseVoice | 中文 ASR、本地转写、情绪/事件/时间戳 sidecar | `funasr_python_runner.py`、`asr_runner.py`、`transcript_sidecar.py` | 后续补 GPU/环境 doctor 和说话人/标点后处理 |
| Peepshow / VidClaude | 帧报告、抽样复核、视觉差异检查 | `vision_review_queue.py`、`multimodal_sample_review.py`、`task-console.html` | 适合继续做人工抽样评分 UI |

## 还值得继续复用的代码模块

### P0：统一视频工作台

目标：把当前分散的 `task-console.html`、`review.html`、`transcript-editor.html`、`smart-summary-section-editor.html` 合成一个主入口。

可复用来源：

- BiliNote 的“视频 + 字幕 + 笔记”同屏体验。
- vsummary 的时间戳点击跳转和 citation 展示。
- Peepshow / VidClaude 的帧证据卡片。

建议落地：

- 新增 `export-video-workbench`。
- 产物：`video-workbench.html/json`。
- 页面包含：
  - 本地视频播放器；
  - timeline / transcript row 点击跳转；
  - artifact tabs；
  - review targets；
  - smart-summary section queue；
  - run registry / failed items / retry commands。

边界：

- 静态页面，不直接写盘。
- 不自动调用云 API。
- 所有导入仍走现有 CLI/MCP。

### P0：批次队列与失败重试 UI

目标：把长视频处理从“复制一堆 PowerShell 命令”变成可见生产线。

可复用来源：

- vsummary 的 stage cache / run status / task record。
- BiliNote 的任务面板。
- Peepshow / VidClaude 的 frame batch report。

建议落地：

- 让 `run-artifact-registry` 聚合所有 `runs/*/run.json`。
- `task-console.html` 和未来 `video-workbench.html` 显示：
  - batch size；
  - total batches；
  - succeeded / failed / pending；
  - failed indexes；
  - retry command；
  - last artifact；
  - next action。
- 对 ebook batch、多模态 batch、tile、ASR、smart-summary section rewrite 都统一。

边界：

- UI 只展示和生成命令。
- 真实 API / 长任务仍需显式 `--execute` 或用户确认。

### P0：字幕/ASR/平台字幕多源仲裁后处理

当前状态：`transcript-source-arbitration` v1 已落地。

继续可复用来源：

- BiliNote 字幕清洗和短句合并。
- WhisperX 的 word-level timestamp / speaker diarization 思路。
- FunASR / SenseVoice 的 timestamp、emotion、event tags。

下一步：

- 在工作台里展示 ASR、平台字幕、自带字幕、corrected transcript 差异。
- 高置信术语纠错写入 corrected transcript。
- 低置信冲突进入 review pack。
- 后处理标点、段落、说话人标签。

边界：

- 不把平台字幕默认当真，因为很多平台字幕也是 ASR。
- corrected transcript 是最终人类可读文件的优先输入，但要保留来源和置信度。

### P1：长视频分层总结输入包

目标：让 `smart-summary.md` 的质量更接近得到大脑的智能总结，而不是规则拼接草稿。

可复用来源：

- MovieChat 的长视频分段记忆。
- vsummary 的分段总结 pipeline。
- BiliNote 的 mind-map prompt chunking。
- VideoRAG 的 chunk citation。

建议落地：

- `smart-summary-input-pack` 汇总：
  - source-arbitrated transcript；
  - full transcript chapter chunks；
  - long-video-memory-pack；
  - video-moment-index citations；
  - OCR/ebook screen text；
  - visual / temporal understanding；
  - review gaps。
- `generate-smart-summary-with-codex` 和未来在线 LLM 共用同一个 input pack。
- section rewrite 和 final install 都通过 quality gate。

边界：

- 没跑视觉就明确标记“视觉证据未执行/待复核”。
- 不让规则草稿伪装成最终智能总结。

### P1：视频 RAG 与时间定位

目标：让用户可以问“这个视频哪里讲某个术语/工具/案例/步骤”，并跳到对应证据。

可复用来源：

- VideoRAG 的 retrieval unit schema。
- VTimeLLM 的时间范围 grounding。
- vsummary 的 citation seek 体验。

建议落地：

- 默认本地 JSONL + 词法检索，不强依赖向量库。
- chunk 类型至少包括：
  - transcript chunk；
  - visual chunk；
  - chapter chunk；
  - review gap chunk；
  - content asset chunk。
- 检索结果固定包含 start/end、timeline indexes、evidence paths、source confidence。

边界：

- RAG 结果只是证据导航，不直接当事实结论。
- 向量库/HTTP 服务只作为可选显式启动项。

### P1：人工抽样评分 UI

目标：回答“多模态到底让最终人类可读文件准确率提高多少”。

可复用来源：

- Peepshow / VidClaude 的抽样帧报告。
- BiliNote 的视频审阅体验。
- vsummary 的章节/片段 citation。

建议落地：

- 新增 sample review pack：
  - ASR only；
  - ASR + ebook/OCR；
  - ASR + ebook/OCR + multimodal；
  - corrected transcript；
  - final summary。
- 人工给每条样本打：
  - term accuracy；
  - screen text accuracy；
  - visual event coverage；
  - summary usefulness；
  - hallucination / omission。
- 输出对比报告：
  - 多模态覆盖前后准确率；
  - ebook/crop 对屏幕文字改善；
  - 仲裁字幕对术语错词改善。

边界：

- 人审是质量评估和可选复核，不作为默认阻塞。
- 不要求每个视频都全量人工标注。

### P2：本地 VLM adapter 能力矩阵

目标：把 Qwen2.5-VL、InternVL、LLaVA-OneVision 等本地模型作为可选 provider，而不是深嵌主流程。

可复用来源：

- Qwen-VL OpenAI-compatible serving。
- InternVL dynamic tiling。
- LLaVA-OneVision 多图/短片段输入。

建议落地：

- `local-vlm-serving-smoke`：
  - 检查服务地址；
  - 模型名；
  - 是否支持单图、多图、短视频帧组；
  - 图片上限；
  - 显存/设备信息；
  - JSON 输出稳定性。
- 主流程只调用 provider adapter。
- 图像预处理继续复用 `vlm_preprocess.py`。

边界：

- 不在 VKP 仓库 vendoring 模型源码。
- 不自动下载大模型。
- 用户显式启动本地服务后再调用。

### P2：内容素材生成模板

目标：把视频知识提取结果安全转成“可审查内容素材候选”，服务朋友圈/内容资产线程。

可复用来源：

- vsummary 的 clips / summary 输出结构。
- BiliNote 的笔记导出。
- VKP 已有 `content-material-card` 和 handoff pack。

建议落地：

- 从 smart-summary sections 和 moment citations 生成：
  - 关键观点卡；
  - 案例卡；
  - 工具/术语卡；
  - 金句候选；
  - 短视频脚本草稿；
  - 朋友圈灵感草稿。
- 每条都保留：
  - evidence path；
  - timestamp；
  - fact_check_status；
  - privacy_level；
  - publication_allowed=false；
  - review_required=true。

边界：

- VKP 不负责自动发布。
- 不把视频讲述内容直接当事实。

## 不再建议继续复用的方向

| 方向 | 判断 |
| --- | --- |
| 整体搬 vsummary 后端 | VKP 已有 CLI/MCP/OpenClaw/static bundle/run registry；整体搬会制造第二套系统 |
| 整体搬 BiliNote React UI | 交互值得学，但整体搬会破坏 VKP 当前 bundle/evidence/review 结构 |
| 默认引入 VideoRAG 图数据库/向量数据库 | 太重，个人工具默认不应依赖常驻服务 |
| 把 Qwen/InternVL/LLaVA 源码嵌入 VKP | 模型环境和生命周期复杂，应保持 provider/adapter 边界 |
| 在 VKP 内做平台下载/登录/抓字幕后端 | 继续交给 VDO；VKP 接收 handoff manifest 和本地 sidecar |
| 默认把大量帧发送云多模态 | 本地抽帧可以密，云视觉仍应疑难点优先、小批次、显式执行 |
| 做自动发布/自动写知识库 | VKP 只产出证据、笔记、候选素材；发布和正式写回必须人工确认 |

## 推荐执行顺序

1. 完成 `export-video-workbench`，作为主工作台入口。
2. 把 run registry / failed items / retry commands 收拢进工作台队列。
3. 把 `transcript-source-arbitration` 的 review rows 接入 transcript editor / review pack。
4. 让 smart-summary 默认消费 source-arbitrated transcript + long memory + moment citations。
5. 做人工抽样评分 UI，量化多模态、ebook/OCR、术语纠错的真实收益。
6. 再做本地 VLM adapter smoke，而不是先部署大模型。
7. 最后再增强内容素材模板，服务下游内容线程。

## 当前状态

截至 2026-07-05：

- 外部项目的“完整 App”层基本不值得继续搬。
- 低耦合代码模块已经吸收了一大半。
- 剩余最高价值不是新模型，而是主工作台、批次队列、仲裁转写、长视频总结输入包和人工评分闭环。
- 后续新增外部项目时，应优先判断是否能提供上述局部模块；不能提供低耦合模块的项目只保留为参考，不进入 VKP 主流程。

## Update - 2026-07-05 21:10:49 | Codex / GPT-5

### 代码复用收束版判断

继续“榨干”外部项目时，VKP 不应再按仓库名推进，而应按模块能力推进。一个外部项目只有在能提供下面这些低耦合模块时，才值得继续读源码、搬代码或改写为 VKP 模块：

| 模块能力 | 当前是否已有 VKP 落点 | 还能继续复用什么 | 停止条件 |
| --- | --- | --- | --- |
| 统一视频工作台 | 已有 `video_workbench.py` 初版 | 继续吸收 BiliNote/vsummary 的同屏视频、时间轴、证据、任务队列交互 | 工作台能打开视频、定位片段、查看 evidence flags、review closure、run queue、moment search 后停止搬 UI |
| 批次队列和失败重试 | 已有 `run_artifact_registry.py`、`task_console.py`、处理队列 | 继续把 ebook、tile、多模态、smart-summary section rewrite 全部接入统一 run registry | 所有长任务都有 run id、状态、失败原因、重试命令后停止 |
| 字幕/ASR 多源仲裁 | 已有 `transcript_source_arbitration.py`、`transcript_editor.py`、review closure | 继续补标点、术语词典、说话人、人工纠错关闭状态 | corrected transcript 能稳定作为 final export 优先输入后停止 |
| 长视频智能总结输入包 | 已有 smart-summary section workflow、long memory、moment index | 继续把完整 ASR、章节、moment citation、OCR/vision、review gaps 合成 LLM-ready pack | `smart-summary.md` 不再像规则草稿，能覆盖全片并通过质量门禁后停止 |
| 视频 RAG / 时间定位 | 已有 `video_moment_index.py`、`video_rag_pack.py`、`video_rag_search.py` | 继续把检索入口移入 workbench，并让总结引用 moment citation | 本地词法检索可跳视频、可定位证据、可被 summary 引用后停止默认 RAG 开发 |
| 高分辨率图文/小字补救 | 已有 `high_res_tile_plan.py`、`tile_result_import_builder.py`、`tile_result_merge.py` | 继续复用 InternVL dynamic tiling / Qwen image preprocess 的 tile 生成和输入约束 | tile 结果能被导入、低质结果能进入 review，而不是假装 OCR 成功后停止 |
| 本地 VLM adapter | 已有 `local_vlm_server_adapter.py`、`vlm_preprocess.py` | 继续补 OpenAI-compatible / HTTP / subprocess smoke，不搬模型仓库 | 能诊断服务、单图、多图、短帧组、JSON 输出稳定性后停止 |
| 人工抽样评分 | 已有 `multimodal_sample_review.py`，还需继续完善 | 继续吸收 Peepshow/VidClaude 的抽样评价和对比报告 | 能回答“多模态/OCR/仲裁对最终文件准确率提升多少”后停止 |
| 内容素材候选 | 已有 `content-material-card`、handoff pack | 继续把 moment citation 和 smart-summary sections 生成素材卡 | 下游能拿到不可发布、需复核、带证据路径的 inspiration 后停止 |

### 当前不再建议新增的“大模块”

- 不再找另一个完整“AI 视频总结 App”替换 VKP。VKP 已经形成自己的 ASR/OCR/vision/timeline/review/export 证据链。
- 不再默认引入重型 VideoRAG/图数据库/向量数据库服务。先把本地 JSONL/词法检索和 workbench 跳转做好。
- 不再把本地 VLM 源码 vendoring 到 VKP。模型生命周期交给独立服务，VKP 只保留 adapter。
- 不再把平台下载、登录、字幕抓取后端吸收到 VKP。链接和下载继续由 VDO 负责，VKP 只接收 handoff manifest、本地视频和 sidecar。
- 不再把“全量云多模态”作为默认路线。本地抽帧、ebook/OCR、tile、仲裁可以更充分；云视觉只用于疑难点和显式批次。

### 下一轮最值得继续写代码的顺序

1. `video-workbench.html` 内置 VideoRAG-style moment search，而不是只从 task console iframe 进入。
2. 把 workbench 的 run queue 扩展到 ebook batch、tile merge、多模态 batch、smart-summary section workflow。
3. 把 corrected transcript / source arbitration 的差异视图放进 workbench 主页面。
4. 让 `smart-summary-input-pack` 明确记录各章节引用了哪些 transcript / OCR / vision / moment evidence。
5. 做人工抽样评分闭环，输出 `multimodal-impact-report.md`，专门回答“有没有多模态，对最终人类可读文件准确率改善多大”。

这组顺序和用户的当前目标一致：先把已经吸收的外部模块真正变成人能操作的生产工具，再考虑新增外部项目或本地大模型。
## Update - 2026-07-05 21:17:52 | Codex / GPT-5

### 下一轮顺序状态更新

上一节列出的第 1 项已经落地：`video-workbench.html` 现在内置 VideoRAG-style moment search，复用 `task_console._compact_moment_index` 和 `exports/video-moment-index.json`，点击搜索结果可跳转视频时间点并选中对应 timeline row。

当前推荐顺序更新为：

1. 已完成：`video-workbench.html` 内置 VideoRAG-style moment search。
2. 下一步：把 workbench 的 run queue 扩展到 ebook batch、tile merge、多模态 batch、smart-summary section workflow。
3. 再下一步：把 corrected transcript / source arbitration 的差异视图放进 workbench 主页面。
4. 然后：让 `smart-summary-input-pack` 明确记录各章节引用了哪些 transcript / OCR / vision / moment evidence。
5. 最后：做人工抽样评分闭环，输出 `multimodal-impact-report.md`。

边界保持不变：moment search 是本地静态页面能力，不启动 VideoRAG HTTP 服务，不引入向量库，不调用云模型，不把检索结果直接当事实结论。
## Update - 2026-07-05 21:25:18 | Codex / GPT-5

### 下一轮顺序状态更新：run queue 详情已落地

上一节列出的第 2 项已经部分落地：video-workbench.html 的处理队列现在可以点击查看详情。它复用 run_artifact_registry / task_console._build_processing_queue 的数据结构，展示每个队列的 runs、失败项、next actions 和 retry commands。

当前推荐顺序更新为：

1. 已完成：video-workbench.html 内置 VideoRAG-style moment search。
2. 已部分完成：workbench run queue 可点击查看 run / failed item / retry command 详情。
3. 下一步：把更多实际任务类型稳定登记到 run registry，重点是 ebook batch、tile merge、多模态 batch、smart-summary section workflow。
4. 再下一步：把 corrected transcript / source arbitration 的差异视图放进 workbench 主页面。
5. 然后：让 smart-summary-input-pack 明确记录各章节引用了哪些 transcript / OCR / vision / moment evidence。
6. 最后：做人工抽样评分闭环，输出 multimodal-impact-report.md。

边界保持不变：工作台只展示队列和复制命令，不自动执行长任务、不调用云模型、不绕过 preflight / execute / 人工确认边界。
## Update - 2026-07-05 21:30:24 | Codex / GPT-5

### 下一轮顺序状态更新：run queue 路由表已显式化

上一节列出的第 3 项“把更多实际任务类型稳定登记到 run registry”继续推进了一步：任务登记后的分组现在有明确路由表。QUEUE_GROUP_TOKENS 把已复用的外部模块按能力落到固定队列：

- asr_transcript：FunASR/SenseVoice、Whisper、字幕/ASR 仲裁、转写纠错；
- document_ocr：ebook、OCR、screen text recovery、high-res tile、tile import/merge；
- vision：vision review queue、多模态单帧/连续片段、本地 VLM provider smoke；
- timeline_rag：timeline alignment、video moment index、VideoRAG search、long-video memory、supplemental frame；
- summary_export：smart-summary workflow/editor/apply、Codex summary、content asset、external capability pack；
- review：review closure、human review、sample review、impact report。

当前推荐顺序更新为：

1. 已完成：video-workbench.html 内置 VideoRAG-style moment search。
2. 已完成：workbench run queue 可点击查看 run / failed item / retry command 详情。
3. 已部分完成：run queue 路由表已显式覆盖外部复用模块。
4. 下一步：检查实际执行入口是否都调用 register_bundle_run，优先补多模态 batch、ebook batch、tile merge、smart-summary section workflow 的缺口。
5. 再下一步：把 corrected transcript / source arbitration 的差异视图放进 workbench 主页面。
6. 然后：让 smart-summary-input-pack 明确记录各章节引用了哪些 transcript / OCR / vision / moment evidence。
7. 最后：做人工抽样评分闭环，输出 multimodal-impact-report.md。

边界保持不变：队列路由只是本地状态解释层，不执行任务、不调用云模型、不启动本地 VLM 服务。
## Update - 2026-07-05 21:34:58 | Codex / GPT-5

### 剩余可复用模块的执行版清单

这份清单把“还有哪些值得复用的代码模块”翻译成 VKP 后续可以直接开发的入口。原则是：不再搬完整应用，只继续吸收能嵌入 VKP 现有 evidence pipeline 的局部模块。

| 优先级 | 模块 | 借鉴来源 | 需要落到 VKP 的位置 | 完成标准 |
| --- | --- | --- | --- | --- |
| P0 | 真实执行入口统一登记 | vsummary run state / stage cache | `run_artifact_registry.py`、`task_console.py`、`video_workbench.py` | ebook、多模态、temporal、tile、smart-summary section 等长任务都有 run id、状态、失败项、重试命令 |
| P0 | 转写多源仲裁工作台 | BiliNote transcript editor、WhisperX/FunASR timestamps | `transcript_source_arbitration.py`、`transcript_editor.py`、`video_workbench.py` | 用户能在同一页面比较 ASR、平台字幕、自带字幕、纠正版和术语证据 |
| P0 | 智能总结输入包证据化 | BiliNote prompt、vsummary 分段生成、MovieChat long memory、VideoRAG citation | `smart_summary_input_pack.py`、`smart_summary_section_workflow.py` | 每个 summary section 都能追溯 transcript、OCR/ebook、vision、moment evidence 和 review gap |
| P1 | ebook/OCR 空结果自动转 tile/crop | InternVL dynamic tiling、Qwen image preprocess、ebook_markdown_pipeline | `visual_structure.py`、`high_res_tile_plan.py`、`tile_result_import_builder.py`、`tile_result_merge.py` | wrapper-only、空结果、低信息量 OCR 自动进入 tile/crop/多模态/人工审核队列 |
| P1 | 多模态收益抽样报告 | Peepshow/VidClaude evidence card、sample review | `multimodal_sample_review.py`、`vision_review_queue.py` | 输出 `multimodal-impact-report.md`，比较有无多模态对最终人类可读文件准确率的影响 |
| P1 | 视频 RAG 多粒度 chunk | VideoRAG、VTimeLLM | `video_rag_pack.py`、`video_rag_search.py`、`video_moment_index.py`、`video_workbench.py` | 可以按工具名、案例、步骤、结论搜索片段，并跳转视频时间点和 timeline row |
| P2 | 本地 VLM adapter 能力矩阵 | Qwen-VL、InternVL、LLaVA-OneVision | `local_vlm_server_adapter.py`、`vlm_preprocess.py`、`vision_provider_smoke.py` | 不启动模型源码，只 smoke 检查本地服务的单图、多图、短帧组和 JSON 输出能力 |
| P2 | 内容素材候选证据卡 | vsummary citation、VideoRAG evidence、VKP content material card | `knowledge_note_export.py`、`content_asset_status.py`、`content_handoff_pack` 相关入口 | 下游内容线程拿到的每条素材都带时间段、证据路径、事实核查状态和禁止发布标记 |

### 直接停止的模块

以下方向不再进入“继续榨取”队列，除非用户明确改变架构目标：

- 完整替换 VKP 的视频总结应用。
- 默认运行图数据库、向量数据库或长期视频 RAG 服务。
- 把本地 VLM 模型仓库源码直接嵌入 VKP。
- 把平台下载、登录态、验证码处理、字幕抓取后端并入 VKP。
- 把大量本地视频帧默认发送云端多模态模型。
- 自动发布、自动写正式知识库、自动事实定稿。

### 下一步开发建议

下一步最小闭环不是继续找新仓库，而是先让已吸收模块“看得见、可重试、可衡量”：

1. 补实际执行入口的 `register_bundle_run` 覆盖。
2. 在 `video-workbench.html` 显示 run queue 的真实执行状态和失败项。
3. 接入转写仲裁差异视图。
4. 让智能总结章节消费 evidence input pack。
5. 做多模态收益抽样报告，回答“多模态到底改善多少”。

这几个完成后，再评估是否需要继续查新的开源项目。否则继续找项目会变成堆素材，而不是提高 VKP 的生产能力。
## Update - 2026-07-05 21:44:53 | Codex / GPT-5

### 执行版清单进度：视觉 batch 已进入 run registry

P0 “真实执行入口统一登记”继续推进：

- 已补：run_multimodal_frame_analysis -> run_type=multimodal_frame_analysis。
- 已补：run_temporal_visual_analysis -> run_type=temporal_visual_analysis。
- 已有：visual_structure_ebook、high_res_tile_plan、tile_result_import_builder、tile_result_merge、smart_summary_section_workflow 等此前已经接入 registry。

当前意义：video-workbench.html 的处理队列不再只能看到 queue shell，视觉 batch 的 preview / preflight blocker / execution failure / retry command 都可以通过 run-artifact-registry.json 汇总展示。

下一步继续：

1. 复核 ASR runner、screen text recovery、transcript arbitration 是否也都稳定登记 run。
2. 把 corrected transcript / source arbitration 差异视图放入工作台。
3. 让 smart-summary input pack 记录每章消费的 transcript / OCR / vision / moment evidence。
## Update - 2026-07-05 21:53:57 | Codex / GPT-5

### 执行版清单进度：screen text recovery 已进入 run registry

P0 “真实执行入口统一登记”继续推进：

- 已补：run_screen_text_recovery -> run_type=screen_text_recovery。
- 状态口径：
  - preview：
eeds_execution；
  - crop-only：
eeds_execution，因为还没有 OCR/人工确认；
  - OCR 空结果：
eeds_review，不清除 blocker；
  - crop/OCR 失败：
eeds_retry；
  - 全部选中项有效更新：completed。

当前意义：ebook/OCR 失败后的 crop/OCR 补救现在能在 video-workbench.html / task-console 的 document OCR 队列里显示为可重试任务，而不是只散落为 screen-text-recovery.md 报告。

下一步继续：

1. 复核 ASR runner 是否也要登记为 asr_transcript 队列 run。
2. 把 transcript source arbitration 的差异视图放进工作台。
3. 让 smart-summary input pack 记录每章消费的 transcript / OCR / vision / moment evidence。
## Update - 2026-07-05 22:00:13 | Codex / GPT-5

### 执行版清单进度：ASR run plan 已进入 run registry

P0 “真实执行入口统一登记”继续推进：

- 已补：run_asr_plan -> run_type=asr_run_plan。
- 只在目标 project 是 VKP bundle 时登记，避免普通 ASR smoke 目录被误写成 bundle。
- 状态口径：
  - preview：
eeds_execution；
  - ok：completed；
  - 模型缓存/命令/runner 未准备：
eeds_input；
  - failed/timeout/output_missing/normalize_failed：
eeds_retry。

当前意义：ASR、screen text recovery、多模态、temporal、ebook/tile、smart-summary section workflow 这些主要长任务已经逐步收束到统一 run registry，video-workbench.html 的队列可以更接近真实生产状态。

下一步继续：

1. 把 transcript source arbitration 的差异视图放入 video-workbench.html。
2. 让 smart-summary input pack 记录每章消费的 transcript / OCR / vision / moment evidence。
3. 做多模态收益抽样报告，量化最终人类可读文件改善幅度。
## Update - 2026-07-05 22:08:50 | Codex / GPT-5

### 执行版清单进度：transcript arbitration 差异视图进入工作台

P0 “BiliNote UI 的任务历史、转录编辑和视频联动”继续推进：

- 已补：video-workbench.html 读取 transcript-source-arbitration.json；
- 已补：工作台左栏显示字幕/ASR 仲裁摘要和待复核冲突；
- 已补：timeline row 标记 transcript_source_conflict；
- 已补：点击仲裁冲突行可跳转对应 timeline/video 时间点，并筛选冲突行。

当前意义：用户不必在 transcript-source-arbitration.md、review pack、timeline 之间来回找错词；工作台可以直接回答“这句纠正版从哪里来、哪个来源支持、置信度多少、为什么还要复核”。

下一步继续：

1. 让 smart-summary input pack 记录每章消费的 source-arbitrated transcript / OCR / vision / moment evidence。
2. 做多模态收益抽样报告，量化最终人类可读文件改善幅度。
3. 把 transcript arbitration 的人工修正入口进一步联动到 transcript editor / review notes。
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
## Update: 2026-07-05 23:13:42 | Codex / GPT-5

### 当前仍值得继续复用的代码模块收束

基于已审查和已吸收的 `vsummary`、`BiliNote`、VideoRAG、MovieChat、VTimeLLM、Qwen/InternVL-style VLM 工程，以及 Peepshow/VidClaude 类帧审核界面，本项目下一步不适合再整体搬一个完整开源项目。更高收益的方向是继续把外部项目的局部能力接入 VKP 已有的 timeline、evidence、review、workbench 和 CLI/MCP 边界。

#### P0：把 VideoRAG 多粒度 chunk 接进统一视频工作台

当前状态：

- `video-rag-pack` 已能生成 `exports/video-rag-chunks.jsonl`。
- JSONL 已包含 `moment`、`visual_evidence`、`review_gap`、`content_asset` 四类 chunk。
- `video-rag-search` 已能本地检索这些 chunk。
- `video-workbench.html` 目前已有“片段搜索”，但主要消费 `video-moment-index.json`，还没有把多粒度 RAG chunks 作为同一搜索源展示。

需要复用/吸收的外部思路：

- VideoRAG 的 retrieval unit / evidence chunk；
- BiliNote 的单页操作台；
- vsummary 的 artifact-first 工作流；
- VKP 现有 review gap 和 content asset 索引。

建议落地：

- `export-video-workbench` 读取 `exports/video-rag-chunks.jsonl`。
- `video-workbench.json` 增加 `video_rag_chunks`，做轻量 compact，避免把原始大 JSON 全塞进页面。
- `video-workbench.html` 的“片段搜索”同时搜索：
  - moment chunk；
  - visual evidence chunk；
  - review gap chunk；
  - content asset chunk。
- 搜索结果显示 `chunk_kind`、时间范围、关键词、证据路径和关联 timeline index。
- 点击结果时优先跳到对应 timeline 行和视频时间点；没有 timeline index 的 content asset 只展示证据路径。

边界：仍是静态本地搜索，不启动 VideoRAG 完整服务、不接 graph/vector DB、不调用云模型。

#### P1：把 VideoRAG citation 注入智能总结章节工作流

当前状态：

- smart summary section workflow 已有章节证据包和 section editor。
- moment citation 已部分接入，但多粒度 RAG chunk citation 还没有充分用于每章改写。

建议落地：

- 每个章节生成 `candidate_citations[]`：来自 transcript chunk、visual evidence、review gap、content asset。
- `smart-summary-section-editor.html` 显示每章的证据引用，不让 Codex/LLM 改写脱离证据。
- `smart-summary.codex.md` 末尾保留“证据覆盖与待复核”小节。

边界：citation 用于辅助总结，不把 review_gap 当事实。

#### P1：长期视频的 memory pack 与 RAG 查询联动

当前状态：

- `long-video-memory-pack` 已吸收 MovieChat 的 short/long memory 思路。
- `video-rag-pack/search` 已提供本地检索。

建议落地：

- `long-video-memory-pack` 输出的章节/主题 memory 也写入 `video-rag-chunks.jsonl` 的 chapter/memory chunk。
- 长视频查询先命中 chapter/memory，再展开到 moment/visual/review gap。
- workbench 搜索结果按 chunk 层级展示：chapter -> moment -> evidence。

边界：不默认引入向量库；如果后续需要，再做 optional vector backend adapter。

#### P2：本地 VLM adapter 的真实服务化 smoke

当前状态：

- 已有 `local_vlm_server_adapter`、`vlm_preprocess.py`、Qwen/InternVL-style 图片压缩/多图 payload 准备。
- 尚未把本地 VLM 作为稳定默认执行路径。

建议落地：

- 保持 OpenAI-compatible HTTP adapter 为主接口。
- 新增只读 smoke：检查本地 VLM 服务是否在线、模型名、最大图像数、最大边长、是否支持多图。
- VKP 主流程只调用 adapter，不耦合模型仓库内部代码。

边界：不默认拉模型、不默认启动模型服务；本地 VLM 只是在线 API 的可替代分支。

#### P2：人工抽样评分与多模态效果评估闭环

当前状态：

- 已有 `multimodal-sample-review.html` 和抽样对比报告。
- 用户关注“多模态对最终人类可读文件准确率到底改善多少”。

建议落地：

- 抽样页面增加评分字段：术语准确、画面事实、步骤完整、时间戳准确、是否需要保留图片。
- 评分结果写回 bundle 的 `human-sample-eval.json`。
- `smart-summary` 导出时引用抽样评分摘要，区分“已抽样确认”和“未视觉确认”。

边界：人工抽样是质量评估，不应阻塞默认导出；除非用户把某个 bundle 标记为发布级。

#### P3：可替换检索后端 adapter

当前状态：

- `video-rag-search` 是 JSONL 词法检索，足够本地可解释。

建议落地：

- 定义 `retrieval_backend=keyword|sqlite|vector`。
- 默认 keyword。
- sqlite/vector 只作为可选加速和语义召回，不改变 JSONL 主证据格式。

边界：不要把 VideoRAG 的完整 graph/vector 后端变成硬依赖。

### 当前判断

已经值得吸收的开源模块并没有“全部榨干”，但剩余价值主要集中在这些薄层：

1. 检索和引用层：VideoRAG / RAGFlow-style chunk citation。
2. 长视频记忆层：MovieChat-style short/long memory 与章节索引。
3. 操作台层：BiliNote / vsummary 的任务状态、artifact、重试命令聚合。
4. 视觉适配层：Qwen/InternVL-style 图片预处理和 OpenAI-compatible 本地 VLM adapter。
5. 质量评估层：人工抽样评分、低置信复核、证据覆盖报告。

不建议继续做的事：

- 整体迁移 vsummary、BiliNote、VideoRAG、MovieChat 或某个 VLM 项目的完整架构。
- 默认启动长期服务或默认调用云模型。
- 把 review gap / AI draft / OCR 低置信结果直接当事实写进最终总结。

下一步最小可执行项：先完成 `video-workbench.html` 片段搜索对 `video-rag-chunks.jsonl` 的读取和展示。这一步能立刻把已经生成的多粒度证据、疑难点和内容资产候选放到人类可用 UI 里。
## Update: 2026-07-05 23:27:52 | Codex / GPT-5

### 状态更新：P0 VideoRAG chunks 接入工作台已完成

上一节的“下一步最小可执行项”已经完成：`export-video-workbench` 现在会读取 `exports/video-rag-chunks.jsonl`，并把多粒度 RAG chunks 注入 `video-workbench.json.video_rag_chunks`；`video-workbench.html` 的“片段搜索”也已经能同时搜索 moment、visual evidence、review gap 和 content asset。

当前剩余优先级更新为：

1. **P1：VideoRAG citation 注入智能总结章节工作流**：章节改写时自动附带 moment / visual evidence / review gap citation，防止智能总结脱离证据。
2. **P1：长期视频 memory pack 与 RAG 查询联动**：把 `long-video-memory-pack` 的章节/主题 memory 写入 RAG chunks，形成 chapter -> moment -> evidence 的层级检索。
3. **P2：人工抽样评分与多模态效果评估闭环**：把人工评分写回 bundle，用于回答“多模态到底提升了多少准确率”。
4. **P2：本地 VLM adapter smoke**：继续保持 adapter 化，不默认启动模型服务。
5. **P3：可替换检索后端**：keyword 默认，sqlite/vector 只作为 optional backend。

验证入口见 `docs/external-code-module-reuse-backlog-2026-07-04.md` 的“已落地：统一视频工作台接入 VideoRAG 多粒度 chunks”。
## Update: 2026-07-05 23:35:57 | Codex / GPT-5

### 状态更新：P1 VideoRAG citation 注入已完成

`smart-summary-section-workflow` 已从 moment-only citation 升级为 composite citation：每章同时接收 `video_moment_index` 和 `video_rag_chunks` 的证据引用。`review_gap` 会以 `fact_status=review_gap_not_fact` 标记，避免章节重写把缺口当成事实。

当前剩余优先级更新为：

1. **P1：长期视频 memory pack 与 RAG 查询联动**：把 `long-video-memory-pack` 的章节/主题 memory 写入 RAG chunks，形成 chapter -> moment -> evidence 的层级检索。
2. **P2：人工抽样评分与多模态效果评估闭环**：把人工评分写回 bundle，用于回答“多模态到底提升了多少准确率”。
3. **P2：本地 VLM adapter smoke**：继续保持 adapter 化，不默认启动模型服务。
4. **P3：可替换检索后端**：keyword 默认，sqlite/vector 只作为 optional backend。

验证入口见 `docs/external-code-module-reuse-backlog-2026-07-04.md` 的“已落地：智能总结章节工作流接入多粒度 VideoRAG citations”。
## 模块级榨干清单 v2：下一步还能复用什么

更新时间：2026-07-05 23:39:42 | Codex / GPT-5

这一轮结论需要从“还有哪个开源项目值得搬”切换成“还有哪些低耦合代码模块值得继续吸收”。VKP 已经形成自己的主结构：ASR / 字幕仲裁、抽帧、ebook/OCR、视觉复核、timeline、review bundle、smart summary、workbench、CLI/MCP/OpenClaw。继续整体迁移 vsummary、BiliNote、VideoRAG、MovieChat 或某个 VLM 项目，收益会低于维护成本。

### 当前已完成的吸收层

| 层级 | 已吸收来源 | VKP 落地形态 | 当前状态 |
| --- | --- | --- | --- |
| 任务与产物管理 | vsummary | `runs/*/run.json`、`run-artifact-registry`、`task-console.html`、失败项和 retry command | 已可用，仍可继续增强 UI |
| 视频工作台 | BiliNote、vsummary、Peepshow/VidClaude | `video-workbench.html/json`，播放器、timeline、artifact、队列、片段搜索同屏 | 已可用 |
| 字幕与转写后处理 | BiliNote、FunASR/SenseVoice | `bilinote_transcript_tools.py`、`transcript_source_arbitration.py`、`transcript_correction_pack.py`、`transcript_editor.py` | 已可用，标点/说话人/术语词典仍可补 |
| 时间定位 | VTimeLLM | `video_moment_index.py`、`timeline_alignment_audit.py`、review notes 修正 `review_start` | 已可用 |
| 长视频记忆 | MovieChat | `long_video_memory_pack.py`，章节/主题 memory | 已有基础，下一步要和 RAG 查询联动 |
| 视频 RAG | VideoRAG | `video_rag_pack.py`、`video_rag_search.py`、`video_rag_http.py`、JSONL 多粒度 chunks | 已可用，下一步补 memory chunk 和可选后端 |
| 智能总结证据引用 | VideoRAG、RAGFlow-style citation、BiliNote section editing | `smart_summary_section_workflow.py`、`smart_summary_section_editor.py`，moment + RAG citations | 已可用 |
| 图像预处理与 tile | Qwen-VL、InternVL | `vlm_preprocess.py`、`high_res_tile_plan.py`、`tile_result_import_builder.py`、`tile_result_merge.py` | 已可用，后续接本地 VLM smoke |
| 多模态效果评估 | Peepshow/VidClaude | `multimodal_sample_review.py`、人工抽样复核页面 | 有基础，评分闭环未完整落地 |

### 仍值得继续吸收的代码模块

| 优先级 | 模块 | 参考来源 | 应该复用的具体点 | VKP 接入方式 | 完成标准 |
| --- | --- | --- | --- | --- | --- |
| P1 | long-video memory -> RAG chunk | MovieChat + VideoRAG | 把章节 memory、主题 memory 写成可检索 retrieval unit | `video-rag-pack` 自动读取/生成 `long-video-memory-pack`，新增 `chapter_memory` / `theme_memory` chunk | 搜索能显示 `chapter -> moment -> evidence` 层级 |
| P1 | RAG 查询层级展示 | VideoRAG | query 先命中章节/主题，再展开到具体片段和证据 | `video-rag-search` / `video-workbench` 增加 memory 层级字段和排序 | 查询结果能说明命中的是章节、片段、证据还是缺口 |
| P1 | smart-summary section 质量闭环 | BiliNote + vsummary | 按章节 staged rewrite、质量检查、引用覆盖 | `smart-summary-section-workflow` + `smart-summary-section-apply` + run registry | 每章能看引用、改写、安装、回滚或重试 |
| P2 | 人工抽样评分 | Peepshow/VidClaude | 抽样评分表、失败分类、术语/画面/时间戳准确率 | `multimodal-sample-review.html` 写回 `human-sample-eval.json` | 能回答“多模态提高了多少准确率” |
| P2 | 本地 VLM service smoke | Qwen2.5-VL、InternVL、LLaVA-OneVision | HTTP/OpenAI-compatible service check、多图能力、最大边长、模型名 | `local-vlm-serving-smoke` 只读检查，不默认启动模型 | 本地 VLM 可作为火山/OpenAI/Gemini 的替代 provider |
| P2 | 高分辨率 OCR/tile 结果消费 | InternVL dynamic tiling、Qwen-VL preprocessing | tile-level evidence merge、低置信复核、保留图片理由 | 已有 `tile-result-import-build/merge`，继续接 UI 和 review pack | 小字和图文结构 blocker 能分流到 ebook、tile OCR/VLM、人审 |
| P3 | 可替换检索后端 | VideoRAG / RAGFlow / LlamaIndex 思路 | keyword / sqlite / vector backend 抽象 | 保持 JSONL 为主证据，新增 optional backend adapter | 默认 keyword 不变，vector 只作为可选加速 |
| P3 | 内容资产素材卡生成增强 | vsummary chapters + BiliNote note export | 高光片段、复用话术、短视频脚本草稿的 citation | `content-material-card`、`key-segments`、`highlight-post-drafts` | 仍保持 `publication_allowed=false`，只给下游灵感材料 |

### 不再建议继续榨的部分

| 方向 | 原因 |
| --- | --- |
| 整体搬 vsummary 后端 | VKP 已有 CLI/MCP/OpenClaw、run registry 和静态 bundle，整体搬会形成第二套后端和任务系统 |
| 整体搬 BiliNote UI | BiliNote 的界面思想已吸收；VKP 的 evidence/review/timeline 字段更复杂，整套 UI 适配成本高 |
| 默认运行 VideoRAG graph/vector 后端 | 当前 JSONL 本地检索足够可解释；重后端应作为 optional backend，不做默认依赖 |
| 默认部署 Qwen/InternVL/LLaVA 本地模型 | 模型部署成本高，先保留 adapter/smoke；真实执行由用户选择 provider |
| 把 review gap 当事实来源 | review gap 只能提示风险和待复核，不能直接进入最终事实总结 |
| 把云多模态变成默认全量处理 | 默认应是本地抽帧、ebook/OCR、规则/triage；云模型只处理疑难点或用户明确允许的批次 |

### 下一步最小执行顺序

1. 先做 `long-video memory -> RAG chunk`：把 `chapter_memory` / `theme_memory` 写进 `video-rag-chunks.jsonl`。
2. 再改 `video-rag-search` 和 `video-workbench`：搜索结果按 `chapter/memory -> moment -> evidence` 展示。
3. 再补人工抽样评分闭环：让多模态前后差异从主观感觉变成可统计的评分表。
4. 最后才考虑 optional vector backend 或本地 VLM service smoke。

这个顺序的好处是：完全复用已有 VKP 数据结构，不启动新服务，不调用云模型，也不需要重新处理真实视频；但能立刻提升长视频复习、定位、总结改写和人工复核效率。
## Update: 2026-07-05 23:51:10 | Codex / GPT-5

### 状态更新：P1 long-video memory -> RAG chunk 已完成

上一节“下一步最小执行顺序”的第 1 项已经落地：`video-rag-pack` 会把 long-video-memory-pack 的 short/long memory 写入 `exports/video-rag-chunks.jsonl`，并让 `video-rag-search` 暴露 memory 层级字段。

新增 chunk kind：

- short_memory
- chapter_memory
- 	heme_memory
- memory_boundary

新增查询层级字段：

- memory_level
- memory_id
- parent_memory_id
- child_memory_ids
- child_moment_indexes
- `fact_status`

当前剩余优先级更新为：

1. **P1：workbench 层级展示**：video-workbench.html 搜索结果目前能读 RAG chunks，但还应把 memory hit 展示成 chapter/theme -> moment -> evidence 的层级树。
2. **P2：人工抽样评分与多模态效果评估闭环**：把人工评分写回 bundle，用于回答“多模态到底提升了多少准确率”。
3. **P2：本地 VLM adapter smoke**：继续保持 adapter 化，不默认启动模型服务。
4. **P3：可替换检索后端**：keyword 默认，sqlite/vector 只作为 optional backend。

验证入口见 docs/external-code-module-reuse-backlog-2026-07-04.md 的“已落地：long-video memory pack 接入 VideoRAG chunks”。
## Update: 2026-07-06 00:00:22 | Codex / GPT-5

### 状态更新：P1 workbench 层级展示已完成

上一节剩余优先级的第 1 项已经完成：`video-workbench.html` 现在不仅能搜索 `video-rag-chunks.jsonl`，还会展示 memory hit 的层级关系。

已完成：

- `video-workbench.json.video_rag_chunks[]` 保留 memory 层级字段。
- 搜索结果显示 `memory_level / memory_id / parent_memory_id / child_memory_ids / child_moment_indexes / fact_status`。
- `chapter_memory` / `theme_memory` 能以 `chapter/theme -> moment -> evidence` 的形式辅助长视频定位。

当前剩余优先级更新为：

1. **P2：人工抽样评分与多模态效果评估闭环**：把人工评分写回 bundle，用于回答“多模态到底提升了多少准确率”。
2. **P2：本地 VLM adapter smoke**：继续保持 adapter 化，不默认启动模型服务。
3. **P3：可替换检索后端**：keyword 默认，sqlite/vector 只作为 optional backend。

验证入口见 `docs/external-code-module-reuse-backlog-2026-07-04.md` 的“已落地：video-workbench 展示 memory -> moment -> evidence 层级”。
## Update: 2026-07-06 00:15:00 | Codex / GPT-5

### 状态更新：P2 人工抽样评分闭环已完成

上一节剩余优先级的第 1 项已经完成：`multimodal-sample-review.html` 现在能采集术语、画面事实、步骤完整、时间戳、是否保留图片等人工评分，并由 `validate-multimodal-sample-notes` 写出 `human-sample-eval.md/json`。

当前剩余优先级更新为：

1. **P2：本地 VLM adapter smoke**：继续保持 adapter 化，不默认启动模型服务。
2. **P3：可替换检索后端**：keyword 默认，sqlite/vector 只作为 optional backend。

验证入口见 `docs/external-code-module-reuse-backlog-2026-07-04.md` 的“已落地：人工抽样评分与多模态效果评估闭环”。
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
