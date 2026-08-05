# 外部开源项目下一批可复用代码模块清单

更新记录：

- 2026-07-06 14:56:06 | Codex / GPT-5：把“还有哪些值得复用的代码模块”整理为下一批可执行队列，明确参考来源、VKP 落点、验收方式和停止条件。

## 目的

这份文档回答一个更具体的问题：在已经吸收 vsummary、BiliNote、VideoRAG、VTimeLLM、MovieChat、Qwen/InternVL/LLaVA、Peepshow/VidClaude 的一批能力之后，VKP 还应该继续从这些项目里复用哪些“代码模块”，而不是继续停留在项目介绍层面。

原则仍然是局部复用：

- 不整体迁移外部项目。
- 不引入第二套主后端、第二套主 UI、第二套下载链路。
- 优先复用 schema、prompt、状态机、预处理、切分、索引、UI 交互、失败恢复、质量评价这些低耦合模块。
- 下载继续交给 `video-download-orchestrator`。
- 在线模型调用继续保留 preflight、显式确认、小批次和疑难点优先策略。

## 当前判断

已经不是“缺一个开源项目替换 VKP”的阶段。更像是 VKP 主干已经站住，下一步要继续吸收外部项目里成熟的小器官：

```text
外部项目源码
  -> 拆出低耦合模块
  -> 接入 VKP 已有 CLI/MCP/static bundle/run registry
  -> 不破坏 ASR/OCR/ebook/vision/review/export 主线
  -> 通过真实 bundle 和轻量测试验收
```

## P0：质量抽样独立面板

参考来源：

- Peepshow：帧报告、人工抽样、逐帧质量判断。
- VidClaude：多模态结果和人工评价并排比较。
- vsummary：任务状态和可重试 run artifact。

当前 VKP 已有：

- `multimodal_sample_review.py`
- `human-sample-eval.json/md`
- `runs/multimodal-sample-review/run.json`
- `runs/human-sample-eval/run.json`
- `content-asset-status` 中的候选可用率、证据充分率、多模态净帮助率。

下一步要复用的代码形态：

- 抽样评价 panel schema。
- 人工评分维度展示。
- 未标注、低证据、模型幻觉、需要重跑的分组过滤。
- 从质量抽样回跳到视频时间、timeline、证据帧、内容候选。

VKP 落点：

- `src/video_knowledge_pipeline/video_workbench.py`
- `tests/test_video_workbench.py`

验收标准：

- `video-workbench.html` 有独立“质量抽样”面板，而不是只把指标塞在内容素材候选里。
- 面板显示：
  - sample count；
  - labeled rows；
  - candidate usable rate；
  - evidence sufficient rate；
  - multimodal net help rate；
  - sample review / human eval 报告入口；
  - 未标注和模型问题的下一步命令。
- `video-workbench.json` 保留机器可读 `human_sample_eval` 摘要。

停止条件：

- 用户不用打开多个 Markdown 才能判断“多模态到底有没有改善最终人类可读文件”。
- 质量抽样只作为 review signal，不自动批准发布、不自动当事实、不自动改 timeline。

## P0：剩余长任务 run artifact failed_items 全覆盖

参考来源：

- vsummary：stage/task state、artifact registry、retry queue。
- BiliNote：任务历史。
- Peepshow：失败帧可重试。

当前 VKP 已有：

- `run_artifact_registry.py`
- provider/VLM smoke run artifacts。
- multimodal sample review / human sample eval run artifacts。
- 部分 screen text / high-res tile failed item 命令。

下一步要复用的代码形态：

- 每个 run 的统一状态 schema。
- 每个 failed item 的 item-level retry command。
- artifact path / evidence path / operator boundary。
- UI 队列按 action kind 聚合。

VKP 落点：

- `screen_text_recovery.py`
- `high_res_tile_plan.py`
- `tile_result_import_builder.py`
- `tile_result_merge.py`
- `vision_review_queue.py`
- `smart_summary_section_workflow.py`
- `task_console.py`
- `video_workbench.py`

验收标准：

- 常见失败都有：
  - `reason`
  - `timeline_index`
  - `evidence_paths`
  - `suggested_next_tool`
  - `suggested_retry_command`
  - `operator_boundary`
- `task-console.html` 和 `video-workbench.html` 不再只显示 run-level 失败，而能显示 item-level 下一步。

停止条件：

- 用户不用回聊天记录里找命令。
- Agent 可以从 `run-artifact-registry.json` 自动生成下一批修复计划。

## P0：BiliNote-style 视频同屏编辑体验

参考来源：

- BiliNote：视频、字幕、笔记、章节、重新生成的一体化交互。
- vsummary：timestamp citation seek。

当前 VKP 已有：

- `review.html`
- `task-console.html`
- `video-workbench.html`
- `transcript-editor.html`
- `smart-summary-section-editor.html`
- browser 内视频播放和时间跳转基础能力。

下一步要复用的代码形态：

- 同屏视频播放器。
- transcript row 高亮。
- 点击字幕跳视频。
- 点击总结章节跳证据。
- 编辑 transcript 后触发重新生成 input pack / section workflow 的按钮。

VKP 落点：

- `video_workbench.py`
- `transcript_editor.py`
- `smart_summary_section_editor.py`

验收标准：

- `video-workbench.html` 能承载视频、时间轴、转写、视觉证据、内容候选、章节总结入口。
- 点击时间戳跳到 ASR segment start，而不是帧窗口结束或句子结束。
- 编辑仍通过导出 JSON -> CLI/MCP apply，不让静态页面直接写盘。

停止条件：

- 不复制 BiliNote 整套 React app。
- VKP 静态 bundle 仍可离线打开。

## P1：章节级智能总结工作流继续吸收

参考来源：

- vsummary：分阶段总结、provider 层、JSON repair。
- BiliNote：章节笔记、mind-map prompt。
- MovieChat：长视频 memory。
- VideoRAG：citation digest。

当前 VKP 已有：

- `smart_summary_chapters.py`
- `smart_summary_codex.py`
- `smart_summary_input_pack.py`
- `smart_summary_section_workflow.py`
- `smart_summary_section_editor.py`
- `smart_summary_section_apply.py`
- `long_video_memory_pack.py`
- `video_rag_pack.py`

下一步要复用的代码形态：

- map-reduce / chapter-reduce 总结调度。
- 每章独立生成、复核、安装。
- LLM JSON 输出 repair。
- 章节质量门禁。
- 章节 citation coverage 评价。

VKP 落点：

- `smart_summary_section_workflow.py`
- `smart_summary_section_apply.py`
- `knowledge_note_export.py`
- `video_workbench.py`

验收标准：

- 每章有独立状态：draft / generated / installed / needs_review / failed。
- 每章有 transcript、OCR/ebook、visual、temporal、content candidate、review gap 的 citation coverage。
- 失败章节进入 run registry，带 retry command。
- `smart-summary.md` 不再回退成机械 ASR 摘抄。

停止条件：

- `smart-summary.md` 是阅读层。
- `knowledge-note.md` 是证据审计层。
- `full-transcript.md` 是逐字稿层。
- 三层边界清楚。

## P1：VideoRAG 搜索和跳转继续增强

参考来源：

- VideoRAG：多粒度 retrieval unit。
- VTimeLLM：query-to-moment grounding。
- vsummary：引用点击跳视频。

当前 VKP 已有：

- `video_moment_index.py`
- `video_rag_pack.py`
- `video_rag_search.py`
- `video_rag_http.py`
- content candidate 与 moment/RAG chunk 互链。

下一步要复用的代码形态：

- transcript / visual / chapter / content candidate / review gap 多类型 chunk schema。
- query result ranking。
- 搜索结果到视频播放器、timeline row、章节、内容候选的多目标跳转。
- 可替换 retrieval backend 接口。

VKP 落点：

- `video_rag_pack.py`
- `video_rag_search.py`
- `video_rag_http.py`
- `video_workbench.py`

验收标准：

- 工作台搜索“工具名 / 价格 / 步骤 / 结论 / 案例”能定位到对应时间段。
- 搜索结果能显示来源类型、证据路径、关联内容候选。
- 默认仍用 JSONL / keyword / SQLite；vector 只是显式可选。

停止条件：

- 不引入默认重型向量库。
- 检索只做定位和复核辅助，不替代证据抽取。

## P1：ASR / 字幕后处理继续吸收

参考来源：

- BiliNote：字幕清洗、短句合并、转写校对 prompt。
- WhisperX：word-level timestamp、diarization。
- SenseVoice：event tag、emotion、speaker hint。

当前 VKP 已有：

- `bilinote_transcript_tools.py`
- `bilinote_summary_tools.py`
- `transcript_source_arbitration.py`
- `transcript_correction_pack.py`
- `transcript_editor.py`

下一步要复用的代码形态：

- 标点恢复。
- 段落化。
- 说话人分离。
- 术语词典。
- 工具名/人名/品牌名纠错。
- low-confidence conflict review rows。

VKP 落点：

- `transcript_source_arbitration.py`
- `transcript_correction_pack.py`
- `transcript_editor.py`
- `smart_summary_input_pack.py`
- `knowledge_note_export.py`

验收标准：

- `corrected-transcript.json` 明确区分：
  - 原始 ASR；
  - 高置信纠错；
  - 低置信疑问；
  - 人工确认。
- `smart-summary-input-pack` 默认读取可信纠正版，排除或标记低置信段。
- `full-transcript.md` 能显示纠错状态，而不是只有原始 ASR。

停止条件：

- 高置信名词可以进入最终人类可读文件。
- 低置信名词只能进入 review，不静默覆盖。

## P1：高分辨率 tile / 局部小字恢复

参考来源：

- InternVL dynamic tiling。
- Qwen-VL image preprocess。
- OCR wrapper-only / empty result recovery。

当前 VKP 已有：

- `high_res_tile_plan.py`
- `tile_result_import_builder.py`
- `tile_result_merge.py`
- `vlm_preprocess.py`
- `screen_text_recovery.py`

下一步要复用的代码形态：

- 自适应 tile 切分。
- tile 坐标和证据路径。
- tile-level OCR/VLM prompt。
- tile result merge。
- wrapper-only / empty / low-information 自动分流。

VKP 落点：

- `high_res_tile_plan.py`
- `tile_result_import_builder.py`
- `tile_result_merge.py`
- `visual_structure.py`
- `video_workbench.py`

验收标准：

- ebook/OCR 低质结果不会被当成功。
- tile plan 能清楚列出为什么切、切哪里、下一步用 OCR/VLM/人工。
- merge 后保留 tile 坐标、证据路径、confidence、review status。

停止条件：

- 小字恢复成为图文结构化失败后的标准补救路径。
- 不把 tile 结果直接伪装成完整 OCR。

## P2：本地 VLM adapter 实机化

参考来源：

- Qwen-VL OpenAI-compatible serving。
- InternVL serving / dynamic tiling。
- LLaVA-OneVision 多图和短视频帧组。

当前 VKP 已有：

- `local_vlm_server_adapter.py`
- `vlm_preprocess.py`
- `vision_provider_smoke.py`
- `vision_environment.py`
- provider / local VLM workbench status。

下一步要复用的代码形态：

- OpenAI-compatible 单图、多图、帧组 payload。
- JSON 输出 repair。
- health / model list / capability check。
- 用户手动启动服务后的 smoke。

VKP 落点：

- `local_vlm_server_adapter.py`
- `vision_api.py`
- `vision_provider_smoke.py`
- `video_workbench.py`

验收标准：

- 能告诉用户本机 VLM 是否可用、支持单图还是多图、最大图片尺寸、是否能稳定 JSON。
- plan-only 不伪装成 executed。
- smoke 结果进入 run registry 和 workbench。

停止条件：

- VKP 支持本地 VLM，但不把它作为默认硬依赖。
- 模型源码不嵌进主流程。

## P2：内容素材生成与复核 UI 继续吸收

参考来源：

- vsummary：导出预览和 citation。
- BiliNote：章节卡片、脑图节点。
- Peepshow/VidClaude：人工质量标签。

当前 VKP 已有：

- `content-candidate-pack.json/md`
- `content-material-card.json/md`
- `content_asset_status.py`
- `content_asset_batch.py`
- `content_handoff_pack`
- content candidate 与 moment/RAG 互链。

下一步要复用的代码形态：

- chapter card edit。
- content candidate review status。
- content candidate -> smart-summary section 双向引用。
- 内容素材质量抽样面板。

VKP 落点：

- `knowledge_note_export.py`
- `content_asset_status.py`
- `content_asset_batch.py`
- `video_workbench.py`
- `multimodal_sample_review.py`

验收标准：

- 每条候选素材显示：来源章节、时间段、证据路径、是否抽样、是否可继续加工、是否仍需事实核查。
- 输出给内容资产/朋友圈线程仍是 `needs_review_inspiration`。
- `publication_allowed=false`、`allowed_as_fact=false` 不被 UI 或 batch 改掉。

停止条件：

- VKP 只输出证据和灵感素材，不生成最终发布稿。

## 明确不再继续榨的方向

| 方向 | 停止理由 |
| --- | --- |
| vsummary 完整 FastAPI / React / LlamaIndex / LanceDB | 与 VKP 主架构重复，会制造第二套服务和索引 |
| BiliNote 完整 React UI | 工作流可借鉴，但整体迁移会打断静态 bundle / MCP / OpenClaw 路线 |
| VideoRAG 默认重型 graph/vector 后端 | 维护成本高，当前 JSONL/keyword/SQLite 更适合个人工具 |
| Qwen/InternVL/LLaVA 模型源码内嵌 | 依赖和显存复杂，应该通过 adapter/HTTP 接入 |
| 下载/字幕抓取后端 | VKP 不做下载，继续接 VDO handoff |
| 默认全量云多模态 | 成本、隐私、限流和失败恢复都不适合作为默认路径 |

## 推荐实现顺序

1. 质量抽样独立面板进入 `video-workbench`。
2. 剩余长任务 run artifact failed_items 全覆盖。
3. BiliNote-style 视频同屏编辑继续合并。
4. 章节级智能总结工作流继续吸收。
5. VideoRAG 搜索跳转和 content candidate 双向回链增强。
6. ASR/字幕后处理进入 `corrected-transcript` 和 summary input policy。
7. high-res tile / 局部小字恢复继续完善。
8. 本地 VLM adapter smoke 实机化。
9. 内容素材候选复核 UI 增强。

## 验收命令模板

每吸收一个模块，至少跑：

```powershell
python -m py_compile src\video_knowledge_pipeline\<changed>.py tests\<changed_test>.py
$env:PYTHONPATH='src'; python -c "<direct test function smoke>"
git diff --check -- src\video_knowledge_pipeline\<changed>.py tests\<changed_test>.py docs\<updated>.md
```

如果涉及真实 bundle，再加：

```powershell
.\scripts\video-knowledge.ps1 export-video-workbench <webui-bundle>
.\scripts\video-knowledge.ps1 run-artifact-registry <webui-bundle>
.\scripts\video-knowledge.ps1 content-asset-status <webui-bundle>
```

## 与现有文档关系

- 本文档是“下一批可直接落地的代码模块队列”。
- `docs/external-code-reuse-latest-action-map-2026-07-06.md` 是最新一页行动入口。
- `docs/external-code-reuse-readable-index-2026-07-06.md` 是完整叙事索引。
- `docs/external-code-module-reuse-backlog-2026-07-04.md` 是长 backlog 和历史更新记录。
- `docs/external-code-reuse-practical-playbook-2026-07-06.md` 是以后评估新外部项目的操作手册。
