# 2026-06-11 下一阶段开发计划：视觉缺口闭环

Acting tool/model: Codex (GPT-5)

## 当前判断

`video-knowledge-pipeline` 的主框架已经基本成型：下载/导入、本地 ASR、抽帧、路由、图文截图解析、多模态 provider 层、timeline 融合、WebUI、MCP、acceptance check、Markdown 导出都已有入口。

下一阶段不应继续横向扩模块，而应把真实视频 bundle 的剩余缺口闭环。

当前真实 bundle：

```text
%WORKSPACE_ROOT%\video-knowledge-pipeline\real-tests\feishu-video-retry-live-asr\phase2-review-preview-bundle
```

当前验收状态：

| 项目 | 状态 |
|---|---|
| speech / ASR | ok |
| frames | ok |
| visual_route | ok |
| document_visual | ok |
| screen_text | weak |
| semantic_visual | blocked |
| temporal_visual | blocked |
| acceptance status | provider_blocked |
| semantic_frame_without_analysis | 44 |
| temporal_sequence_without_analysis | 4 |
| provider matrix | no_provider_ready |

Provider matrix 当前结论：

| Provider | 当前状态 | 说明 |
|---|---|---|
| Agnes | provider_unreachable | text ping 可通，但单图/多图请求超时 |
| Gemini | missing_api_key | 未配置可用 key |
| OpenAI | missing_api_key | 未配置可用 key |

## 阶段目标

本阶段目标不是“继续做一个更大的系统”，而是让这个工具对真实知识视频产出可用资料：

1. 剩余 44 个单帧语义缺口和 4 个连续片段缺口有明确处理结果。
2. 每个视觉理解结果都保留证据帧路径。
3. API 不可用时，人工审核能按模板补齐，不需要猜 JSON schema。
4. 导出的 Markdown 具备层级结构、表格、逐字稿、画面说明、总结和缺口说明。
5. MCP / CLI / WebUI 的下一步提示保持一致，agent 可以稳定调用。

## Task 1：补完整人工审核闭环

### 目的

当前 provider 不可用时，系统已经能提示人工审核，但人工填写体验还不够明确。需要把人工审核变成可执行 fallback，而不是只生成一个模板 JSON。

### 工作项

- 完成 `prepare_review_session` 的 `review-fill-guide.md` 输出。
- `review-fill-guide.md` 按缺口分组：
  - `连续片段待补`
  - `单帧视觉待补`
  - `其他人工确认`
- 每个条目包含：
  - timeline index / 时间段
  - route / reason
  - 字幕摘录
  - OCR / structured visual 摘录
  - 证据帧路径和 Markdown 图片引用
  - 可直接复制进 `review-notes.json` 的 JSON 片段
- manifest 增加 `review_fill_guide = review-fill-guide.md`。
- WebUI / status / acceptance 的下一步提示能指向这个文件。

### 验收命令

```powershell
python -m pytest tests\test_video_pipeline_smoke.py::test_prepare_review_session_writes_fillable_template_for_visual_gaps tests\test_video_pipeline_smoke.py::test_prepare_review_session_supports_limit_offset_and_reason_filter -q

.\scripts\video-knowledge.ps1 prepare-review-session %WORKSPACE_ROOT%\video-knowledge-pipeline\real-tests\feishu-video-retry-live-asr\phase2-review-preview-bundle --limit 0
```

### 验收标准

- `review-fill-guide.md` 存在。
- 文档里能看到 `corrected_visual_understanding` 和 `corrected_temporal_visual_understanding` 示例。
- manifest 记录 `review_fill_guide`。
- 不泄露 API key。

## Task 2：修复 provider matrix，拿到至少一个可执行多模态 provider

### 目的

真实视觉理解不能继续卡在 provider 层。下一阶段先不追求所有 provider 都通，只需要至少一个 provider 能稳定完成：

- text ping
- single image JSON
- multi image JSON

### 优先级

1. Agnes：已有 key 配置痕迹，优先排查图像请求超时、base_url、模型名、timeout、代理。
2. Gemini 2.5 Flash：如果补 key 后可用，优先用于多图短片段。
3. OpenAI-compatible：作为稳定兜底。
4. 本地 VLM：暂缓，不在本阶段主线上硬接。

### 工作项

- 增加 provider matrix 的超时参数可配置，例如 `--timeout-seconds 30`。
- Agnes 单独增加更细的错误报告：
  - endpoint
  - model
  - image payload size
  - response status code
  - raw error redacted preview
- 如果 Agnes 的 text ping 成功但图像超时，生成明确结论：
  - `text_only_ok_image_timeout`
  - `model_may_not_support_images`
  - `payload_too_large`
  - `network_timeout`
- provider config 继续只读环境变量或显式参数，不写入 manifest/docs。

### 验收命令

```powershell
.\scripts\video-knowledge.ps1 vision-provider-matrix %WORKSPACE_ROOT%\video-knowledge-pipeline\real-tests\feishu-video-retry-live-asr\phase2-review-preview-bundle --providers agnes,gemini,openai --timeout-seconds 30
```

### 验收标准

- 至少一个 provider 的 `safe_to_execute = true`。
- 如果没有 provider 可用，报告必须能解释原因，而不是只有 timeout。
- `acceptance-check` 的 `next_action` 与 provider matrix 保持一致。

## Task 3：跑真实单帧语义理解

### 目的

先处理现有 `semantic_frame` / `mixed` 缺口，不再只停留在预览。

### 工作项

- 用 provider matrix 推荐 provider 执行 `run_multimodal_frame_analysis`。
- 支持分批执行，例如 `--limit 5`、`--offset`、`--resume`。
- 每批执行后刷新：
  - timeline
  - `knowledge-coverage.json`
  - `acceptance-check.json`
  - WebUI review bundle
- 输出人类可读对比表：
  - 时间段
  - 字幕
  - OCR/图文解析
  - 模型画面理解
  - 证据帧
  - 遗漏风险

### 验收命令

```powershell
.\scripts\video-knowledge.ps1 run-multimodal-frame-analysis %WORKSPACE_ROOT%\video-knowledge-pipeline\real-tests\feishu-video-retry-live-asr\phase2-review-preview-bundle --execute --limit 5

.\scripts\video-knowledge.ps1 acceptance-check %WORKSPACE_ROOT%\video-knowledge-pipeline\real-tests\feishu-video-retry-live-asr\phase2-review-preview-bundle
```

### 验收标准

- `items_with_visual_understanding` 增加。
- `semantic_frame_without_analysis` 下降。
- 结果不覆盖 ASR、OCR、人工修正。
- 每条结果有 `evidence_frame_path` 或等价证据引用。

## Task 4：跑真实连续片段理解

### 目的

连续变化型视频不能只靠单帧。需要对剩余 `temporal_sequence` 缺口跑 5-12 帧短片段理解。

### 工作项

- 先生成真实帧组：

```powershell
.\scripts\video-knowledge.ps1 run-temporal-frame-groups %WORKSPACE_ROOT%\video-knowledge-pipeline\real-tests\feishu-video-retry-live-asr\phase2-review-preview-bundle --execute --frame-count 8 --limit 5
```

- 再执行多图理解：

```powershell
.\scripts\video-knowledge.ps1 run-temporal-visual-analysis %WORKSPACE_ROOT%\video-knowledge-pipeline\real-tests\feishu-video-retry-live-asr\phase2-review-preview-bundle --execute --frame-count 8 --limit 5
```

- 输出字段必须包含：
  - event_sequence
  - state_changes
  - operation_steps
  - before_after
  - possible_missing_points
  - evidence_frame_paths

### 验收标准

- `items_with_temporal_understanding` 增加。
- `temporal_sequence_without_analysis` 下降到 0，或全部进入人工审核。
- 报告能说明“视频中发生了什么变化”，而不只是描述每张截图。

## Task 5：强化图文截图解析分支

### 目的

当前 `screen_text = weak`，但它不是主阻塞项。等 provider 主线跑通后，再补图文型截图解析质量。

### 工作项

- 保持原则：OCR/图文截图优先复用 `ebook_markdown_pipeline`，不要回到 Peepshow OCR 主线。
- 给 `document_visual` 候选生成批处理包：
  - frame image
  - source timeline index
  - MCP command
  - import target path
- 调用顺序：
  - `process_material`
  - `get_job_status`
  - `read_artifact`
  - 导入 `run_visual_structure_plan`
- 失败时只记录缺口，不用弱 OCR 静默覆盖。

### 验收标准

- `structured_visual` 增加。
- `screen_text` 从 `weak` 变成可解释状态。
- 图文解析结果保留原截图路径。

## Task 6：把导出的知识文档打磨成人类可读成品

### 目的

用户明确要求输出不是碎片 JSON，而是带层级 Markdown 的知识资料：

- 逐字稿：说了什么、演示了什么
- 层级整理：主题、概念、论证、案例、步骤
- 表格：适合比较和结构化的内容
- 图片保留：必须用图片/表格/公式表达的内容不能硬转文字
- 总结：视频概要和复习版

### 工作项

- `exports/knowledge-note.md` 调整为固定结构：

```markdown
# 视频知识整理

## 1. 视频概要
## 2. 核心问题和主线
## 3. 分层知识结构
## 4. 时间轴详解
## 5. 逐字稿与画面说明
## 6. 表格、公式、代码、板书保留区
## 7. 讲者强调和隐含信息
## 8. 待人工复核的问题
## 9. 可复习卡片/问题清单
```

- 导出时标注每段来源：
  - ASR
  - OCR / structured visual
  - multimodal visual
  - temporal visual
  - human review
- 对 provider 缺口不要假装已完成，要在 `待人工复核的问题` 列出。

### 验收命令

```powershell
.\scripts\video-knowledge.ps1 export-knowledge-note %WORKSPACE_ROOT%\video-knowledge-pipeline\real-tests\feishu-video-retry-live-asr\phase2-review-preview-bundle --title "feishu-video-retry"
```

### 验收标准

- `exports/knowledge-note.md` 不需要打开 raw timeline 也能阅读。
- `exports/full-transcript.md` 包含逐字稿和画面说明。
- `exports/export-summary.json` 记录 coverage 和缺口。

## Task 7：WebUI / MCP / CLI 保持同一闭环

### 目的

本项目要同时给人和 agent 用，不能只修 CLI。

### 工作项

- WebUI 首页和 review 页显示同一套下一步：
  - provider matrix
  - semantic frame analysis
  - temporal visual analysis
  - prepare review session
  - export knowledge note
- MCP args 文件全部可审计。
- `bundle-next-action` 与 `acceptance-check.next_action` 一致。
- 如果 provider 不可用，UI 明确提示人工审核路径和 `review-fill-guide.md`。

### 验收命令

```powershell
.\scripts\video-knowledge.ps1 mcp-audit-bundle %WORKSPACE_ROOT%\video-knowledge-pipeline\real-tests\feishu-video-retry-live-asr\phase2-review-preview-bundle
```

### 验收标准

- MCP audit 全部通过。
- UI 不再出现 ASR、OCR、多模态混淆文案。
- agent 能从 status/acceptance 直接拿到下一步 MCP 工具和 args。

## Task 8：全量回归和敏感信息扫描

### 工作项

```powershell
python -m pytest -q

.\scripts\video-knowledge.ps1 acceptance-check %WORKSPACE_ROOT%\video-knowledge-pipeline\real-tests\feishu-video-retry-live-asr\phase2-review-preview-bundle

.\scripts\video-knowledge.ps1 mcp-audit-bundle %WORKSPACE_ROOT%\video-knowledge-pipeline\real-tests\feishu-video-retry-live-asr\phase2-review-preview-bundle

rg -n -e "sk-" -e "AGNES_API_KEY=" -e "OPENAI_API_KEY=" -e "GEMINI_API_KEY=" %WORKSPACE_ROOT%\video-knowledge-pipeline
```

### 验收标准

- 全量测试通过。
- acceptance 不再卡在不可解释状态。
- 真实 bundle 的剩余缺口全部是：
  - 已完成；
  - 或明确人工审核；
  - 或明确 provider/network 阻塞。
- repo 文档和生成报告不含 API key。

## 不做事项

本阶段暂不做：

- 从零开发本地 VLM 推理框架。
- 把 Qwen2.5-VL / InternVL / LLaVA-OneVision 深度嵌入主流程。
- 用 Peepshow OCR 替代 `ebook_markdown_pipeline`。
- 把完整视频直接上传给云端视频理解 API 作为主方案。
- 为了过验收伪造视觉理解结果。

## 推荐执行顺序

1. Task 1：人工审核闭环补完。
2. Task 2：provider matrix 修复到至少一个可执行 provider。
3. Task 3：真实跑 5 条单帧语义理解，确认质量。
4. Task 4：真实跑 1-5 组连续片段理解，确认质量。
5. Task 6：更新导出 Markdown 结构。
6. Task 7：WebUI / MCP / CLI 同步。
7. Task 8：全量测试、acceptance、MCP audit、敏感信息扫描。
8. Task 5：补图文截图解析质量，作为第二优先级。

## 完成定义

本阶段完成时，以下命令应给出可接受结果：

```powershell
python -m pytest -q

.\scripts\video-knowledge.ps1 acceptance-check %WORKSPACE_ROOT%\video-knowledge-pipeline\real-tests\feishu-video-retry-live-asr\phase2-review-preview-bundle

.\scripts\video-knowledge.ps1 export-knowledge-note %WORKSPACE_ROOT%\video-knowledge-pipeline\real-tests\feishu-video-retry-live-asr\phase2-review-preview-bundle --title "feishu-video-retry"

.\scripts\video-knowledge.ps1 mcp-audit-bundle %WORKSPACE_ROOT%\video-knowledge-pipeline\real-tests\feishu-video-retry-live-asr\phase2-review-preview-bundle
```

并且：

- `semantic_frame_without_analysis` 从 44 明显下降，最好为 0。
- `temporal_sequence_without_analysis` 从 4 下降到 0。
- `knowledge-note.md` 是人类可读的分层 Markdown，而不是 timeline dump。
- 任何未完成项都有明确原因和下一步，不再是模糊 blocked。
