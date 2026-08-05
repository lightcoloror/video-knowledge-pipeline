# 外部 AI 视频项目局部能力复用实现记录

Update: 2026-07-04 20:35:00 | Codex / GPT-5

## 本轮目标

把外部 AI 视频总结/分析项目拆成 VKP 可复用的局部能力，而不是整体搬运模型工程或 Web app。

本轮已拉取真实源码：

```text
%WORKSPACE_ROOT%\tool-source-review\MovieChat
%WORKSPACE_ROOT%\tool-source-review\VTimeLLM
%WORKSPACE_ROOT%\tool-source-review\VideoRAG
```

## 源码层观察

### MovieChat

源码重点：

- `MovieChat\models\moviechat+.py`
- `inference.py`

可复用思想：

- 长视频不能直接塞进一次上下文。
- 先形成 short memory，再压缩成长视频 long memory。
- 长记忆需要保留时间顺序和证据边界。

VKP 不复用其模型代码，因为它强依赖重模型、GPU、Q-former、视觉 token 管线；但复用它的长视频 memory layering 思想。

### VTimeLLM

源码重点：

- `vtimellm\eval\metric.py`
- `vtimellm\eval\eval.py`
- `vtimellm\train\dataset.py`

可复用思想：

- 视频理解结果必须带时间边界。
- 查询或事件描述应该能落到 `start/end` moment。
- 评估时要关注 temporal IoU / timestamp coverage，而不是只看摘要文字。

VKP 不直接接入 VTimeLLM 模型，先把“query-to-moment”做成 timeline 本地索引能力。

### VideoRAG

源码重点：

- `VideoRAG-algorithm\videorag\videorag.py`
- `VideoRAG-algorithm\videorag\_op.py`
- `VideoRAG-algorithm\videorag\_videoutil\caption.py`
- `VideoRAG-algorithm\videorag\_splitter.py`
- `VideoRAG-algorithm\videorag\base.py`

可复用思想：

- 视频先切 segment。
- 每个 segment 同时保留 caption、transcript、frame times。
- 查询时同时走文本知识和视觉片段证据。
- 输出回答前要能追溯到 retrieved segment。

VKP 当前不引入其 graph/vector storage 依赖，先把 unified timeline 转成可检索 moment index。

## 本轮已落地模块

### `video_moment_index`

文件：

```text
src/video_knowledge_pipeline/video_moment_index.py
```

能力：

- 从 `timeline.json` 构造本地 video moment chunks。
- 每个 chunk 保留：
  - 时间范围
  - timeline indexes
  - corrected transcript / transcript
  - visual text / ebook / OCR
  - single-frame multimodal understanding
  - temporal visual understanding
  - tags
  - evidence paths
- 支持轻量 query ranking，作为 VTimeLLM/VideoRAG 思路的本地版。

产物：

```text
exports/video-moment-index.json
exports/video-moment-index.md
mcp-video-moment-index.args.json
```

CLI：

```powershell
.\scripts\video-knowledge.ps1 video-moment-index <bundle-dir> `
  --query "Browserbase CDP" `
  --target-window-seconds 300 `
  --top-k 8
```

MCP：

```text
video_moment_index
video_moment_index_tool
```

### `long_video_memory_pack`

文件：

```text
src/video_knowledge_pipeline/long_video_memory_pack.py
```

能力：

- 复用 `video_moment_index` 的 chunks。
- 生成 short memories。
- 按时间顺序合并成长视频 long memories。
- 输出 final memory map，供 `smart-summary` 或 Codex/LLM 改写使用。
- 明确列出缺少视觉/连续片段证据的低置信边界。

产物：

```text
exports/long-video-memory-pack.json
exports/long-video-memory-pack.md
mcp-long-video-memory-pack.args.json
```

CLI：

```powershell
.\scripts\video-knowledge.ps1 long-video-memory-pack <bundle-dir> `
  --target-window-seconds 300 `
  --long-group-size 6
```

MCP：

```text
long_video_memory_pack
long_video_memory_pack_tool
```

## 测试

新增测试：

```text
tests/test_external_video_reuse_modules.py
```

验证内容：

- moment index 能生成 queryable evidence chunks。
- long video memory pack 能按短记忆聚合成长记忆。
- 产物路径写入 manifest。

已通过：

```powershell
python -m pytest -q tests\test_external_video_reuse_modules.py --basetemp %WORKSPACE_ROOT%\vkp-pytest-tmp-external
```

结果：

```text
2 passed
```

## 下一步拆用方向

优先继续三条线：

1. 把 `long-video-memory-pack` 接入 `smart-summary-codex-prompt.md`，让最终智能总结直接吃 short/long memory，而不是只吃规则草稿。
2. 把 `video-moment-index` 接入人工审核 UI：搜索术语或疑难点时跳到相关时间窗。
3. 借鉴 VideoRAG，把 moment index 扩展为本地 RAG 包：JSONL chunks + evidence paths + optional vector backend，但默认不引入重依赖。

不建议短期做：

- 直接嵌 MovieChat/VTimeLLM 模型代码。
- 直接运行 VideoRAG 的整套 graph/vector storage。
- 把 VKP 改造成外部项目的 Web app。

## Update: 2026-07-04 23:10:00 | Codex / GPT-5

### 已继续落地：片段索引进入任务控制台

本轮把 `video_moment_index` 接入 `task-console.html`，让人工审核和 agent 调度不再只能看静态 Markdown：

- `export-task-console` 会基于现有 `timeline.json` 生成/刷新本地 `exports/video-moment-index.json` 与 `exports/video-moment-index.md`。
- `task-console.html` 新增“片段搜索”区域，可搜索术语、工具名、疑难点、字幕关键词。
- 搜索结果显示：时间范围、timeline indexes、关键词、摘要片段、是否已有视觉证据、是否已有连续片段证据。
- 命令区新增：
  - `video_moment_index`
  - `video_moment_search`
  - `long_video_memory_pack`
- MCP audit / local MCP call 已识别：
  - `mcp_video_moment_index_args -> video_moment_index`
  - `mcp_long_video_memory_pack_args -> long_video_memory_pack`

这一步对应上一节“把 `video-moment-index` 接入人工审核 UI”的第一版：先在任务控制台里做可搜索时间窗；后续如果要和 `review.html` 的逐条审核深度联动，再把搜索结果跳转到具体 review row。

### 验证

```powershell
python -m py_compile src\video_knowledge_pipeline\task_console.py src\video_knowledge_pipeline\cli.py
python -m pytest -q tests\test_task_console.py tests\test_external_video_reuse_modules.py --basetemp %WORKSPACE_ROOT%\vkp-pytest-moment-ui
```

结果：

```text
4 passed, 1 warning
```

warning 是 pytest cache 写入 `.pytest_cache` 的权限问题，不影响功能测试。
## Update: 2026-07-04 23:45:00 | Codex / GPT-5

### 已继续拆成局部能力复用：五类能力包

本轮新增两个稳定入口，不搬外部项目整套工程，只复用其可操作思想：

### `video_rag_pack`

文件：

```text
src/video_knowledge_pipeline/video_rag_pack.py
```

复用方向：

- 对标 VideoRAG 的 segment retrieval，但不引入 graph/vector storage 重依赖。
- 从 VKP `video_moment_index` 生成 JSONL retrieval units。
- 每个 chunk 保留 transcript、视觉文本、多模态理解、连续片段理解、时间戳、timeline indexes、evidence paths。

产物：

```text
exports/video-rag-pack.json
exports/video-rag-pack.md
exports/video-rag-chunks.jsonl
mcp-video-rag-pack.args.json
```

CLI：

```powershell
.\scripts\video-knowledge.ps1 video-rag-pack <bundle-dir> --query "<问题或术语>"
```

MCP：

```text
video_rag_pack
video_rag_pack_tool
```

### `external_capability_pack`

文件：

```text
src/video_knowledge_pipeline/external_capability_pack.py
```

作用：

一键生成外部项目局部能力复用总包，覆盖：

1. 长视频分层总结：`long-video-memory-pack`，借鉴 MovieChat short/long memory。
2. 时间定位：`video-moment-index`，借鉴 VTimeLLM query-to-moment。
3. 视频 RAG：`video-rag-pack`，借鉴 VideoRAG segment evidence retrieval。
4. 本地 VLM adapter：复用现有 OpenAI-compatible provider 层，不导入模型仓库代码；同时输出 `local-vlm-adapter-plan.json/md`。
5. 内容素材生成：复用 `export-knowledge-note` / `content-material-card`，并把 `key-segments.md`、`short-video-script-drafts.md`、`highlight-post-drafts.md` 一并列入总包；保持 `review_required=true`、`publication_allowed=false`。

产物：

```text
exports/external-capability-pack.json
exports/external-capability-pack.md
mcp-external-capability-pack.args.json
```

CLI：

```powershell
.\scripts\video-knowledge.ps1 external-capability-pack <bundle-dir> --query "<关键词或问题>"
```

MCP：

```text
external_capability_pack
external_capability_pack_tool
```

### UI/任务控制台接入

`task-console.html` 新增命令和产物链接：

- `video_rag_pack`
- `external_capability_pack`

这两个默认都是本地/预览安全能力：不下载视频、不调用云模型、不启动本地模型服务。

### 验证

```powershell
python -m py_compile src\video_knowledge_pipeline\video_rag_pack.py src\video_knowledge_pipeline\external_capability_pack.py src\video_knowledge_pipeline\cli.py src\video_knowledge_pipeline\mcp_server.py src\video_knowledge_pipeline\task_console.py
python -m pytest -q tests\test_external_video_reuse_modules.py tests\test_task_console.py --basetemp %WORKSPACE_ROOT%\vkp-pytest-external-capabilities
```

结果：

```text
7 passed, 1 warning
```

warning 仍是 pytest cache 写入 `.pytest_cache` 的权限问题，不影响功能测试。本次新增覆盖 CLI 主入口、MCP args 审计/调用、任务控制台链接、本地 VLM Markdown 产物、完整内容素材路径。
## 2026-07-04 继续榨取：vsummary 阶段缓存与 CUDA runtime

Update: 2026-07-04 23:59:00 | Codex / GPT-5

### `stage_cache`

来源：`alpha03123/vsummary` 的 `generation/stage_cache.py` 与 artifact store 原子写入思路。

VKP 落地：

```text
src/video_knowledge_pipeline/stage_cache.py
```

复用点：

- 用 `source_path + size + mtime` 生成 source fingerprint。
- 用 `stage + identity + source_fingerprint` 判断缓存是否可复用。
- 支持 JSON、Markdown/text、任意文件的原子写入和恢复。
- 保持本地安全边界：不启动进程、不调用云、不改变主流程默认行为。

后续适合接入：

- ASR rerun：缓存音频抽取、raw ASR、normalized transcript。
- ebook/OCR batch：缓存图文截图解析结果。
- smart-summary：缓存 chunk summary、全局 summary、LLM 原始输出。
- 内容素材生成：缓存 key segments / script drafts 的中间草稿。

### `cuda_runtime`

来源：`alpha03123/vsummary` 的 `faster_whisper_transcriber.py` Windows CUDA DLL discovery。

VKP 落地：

```text
src/video_knowledge_pipeline/cuda_runtime.py
src/video_knowledge_pipeline/asr_environment.py
```

复用点：

- 发现 pip 安装的 NVIDIA 包：`nvidia.cublas`、`nvidia.cudnn`、`nvidia.cuda_nvrtc`、`nvidia.cuda_runtime`。
- 找到每个包的 `bin/` 目录。
- 提供 dry-run 状态：`cuda_dll_discovery_status()`。
- 提供显式注册：`ensure_windows_cuda_dll_dirs(register=True)`，用于后续 faster-whisper fallback runner。
- `asr-env-status` 现在会带出 `cuda_dll` 诊断字段，默认不改 PATH、不注册 DLL。

### 验证

```powershell
python -m py_compile src\video_knowledge_pipeline\stage_cache.py src\video_knowledge_pipeline\cuda_runtime.py src\video_knowledge_pipeline\asr_environment.py tests\test_stage_cache_and_cuda_runtime.py tests\test_asr_pipeline.py
python -m pytest -q tests\test_stage_cache_and_cuda_runtime.py tests\test_asr_pipeline.py::test_asr_env_status_reports_readiness_and_actionable_next_steps --basetemp %WORKSPACE_ROOT%\vkp-pytest-stage-cache-cuda
```

结果：

```text
4 passed, 1 warning
```

warning 仍是 pytest cache 写入 `.pytest_cache` 的权限问题，不影响功能测试。

### 仍未直接搬的模块

- vsummary 的完整 FastAPI/React/LlamaIndex/LanceDB 栈：太重，容易和 VKP 的 CLI/MCP/static bundle 架构冲突。
- BiliNote 的完整 React UI：继续吸收交互模式，不整体移植。
- MovieChat/VTimeLLM/VideoRAG 的模型或服务运行时：当前先复用数据结构和局部能力；模型服务后续走 provider/adapter。

## Update - 2026-07-04 19:15:57 | Codex GPT-5

本轮继续把外部项目能力拆成可复用的局部模块，而不是整套搬 UI 或重依赖后端：

### vsummary / VTime-style seek and citation

- task-console.html 新增视频定位与 citation 区域。
- 片段搜索结果现在可以点击播放，跳到 chunk start 时间，右侧显示当前 citation、timeline indexes、snippet 和 evidence paths。
- 浏览器不能直接读取 ile:// 视频时，页面提供“选择本地视频文件”兜底。
- 保持静态 HTML，不引入后端。

### VideoRAG local retrieval service v1

- 新增 src/video_knowledge_pipeline/video_rag_search.py。
- 新增 CLI/MCP：video-rag-search / video_rag_search。
- 读取或自动生成 exports/video-rag-chunks.jsonl，输出：
  - exports/video-rag-search.json
  - exports/video-rag-search.md
  - mcp-video-rag-search.args.json
- 当前是本地词法检索，不启动 vector DB，不调用云模型；后续可替换为向量/图检索服务。

### BiliNote mind-map prompt structure

- ilinote_summary_tools.py 新增：
  - uild_mind_map_prompt_messages
  - uild_mind_map_prompt_pack
- 复用 BiliNote 的 transcript chunking 思路，补出 mind-map JSON 节点 prompt；默认只生成 prompt，不调用 LLM。

### Qwen / InternVL local serving smoke

- local_vlm_server_adapter.py 新增 local_vlm_serving_smoke。
- 新增 CLI/MCP：local-vlm-serving-smoke / local_vlm_serving_smoke。
- 默认 plan-only，不启动模型服务、不改 timeline；--execute 只对已经运行的本地 OpenAI-compatible VLM server 做 smoke。

### Verification

`powershell
python -m py_compile src\video_knowledge_pipeline\cli.py src\video_knowledge_pipeline\mcp_server.py src\video_knowledge_pipeline\task_console.py src\video_knowledge_pipeline\video_rag_search.py src\video_knowledge_pipeline\local_vlm_server_adapter.py src\video_knowledge_pipeline\bilinote_summary_tools.py
python -m pytest -q tests\test_external_video_reuse_modules.py tests\test_bilinote_summary_tools.py tests\test_task_console.py --basetemp %WORKSPACE_ROOT%\pytest-cache-files-vkp\external-reuse-current-verify --tb=short
`

Result: 13 passed, 1 warning。warning 是项目 .pytest_cache 权限噪音，不影响本轮测试结论。

## Update - 2026-07-04 19:27:05 | Codex GPT-5

### BiliNote transcript editor reuse

- Added prepare-transcript-edit-session / prepare_transcript_edit_session.
- Writes static ranscript-editor.html, ranscript-edit-session.json, ranscript-edits.template.json, and MCP args.
- Added pply-transcript-edits / pply_transcript_edits for reviewed human edits.
- Import writes human-corrected-transcript.json, .srt, .md and updates the stable corrected transcript manifest keys.
- Boundary: no LLM call, no timeline mutation, import only after explicit reviewed JSON.

### VideoRAG local HTTP service

- Added video-rag-service-plan / video_rag_service_plan.
- Added explicit video-rag-serve for a local-only HTTP server.
- Endpoints: /health, /search?q=<query>&top_k=8, /chunks.
- Boundary: no cloud call, no vector backend by default, no service start unless the operator runs the serve command.

### Verification addendum

`powershell
python -m pytest -q tests\test_external_video_reuse_modules.py tests\test_bilinote_summary_tools.py tests\test_task_console.py tests\test_transcript_editor.py --basetemp %WORKSPACE_ROOT%\pytest-cache-files-vkp\reuse-current-2 --tb=short
`

Result: 15 passed, 1 warning. The warning is the existing .pytest_cache permission noise.

## Update - 2026-07-04 23:59:00 | Codex GPT-5

新增后续可复用代码模块 backlog：

```text
docs/external-code-module-reuse-backlog-2026-07-04.md
```

该文档把 vsummary、PrideWood/BiliNote、VideoRAG、MovieChat、VTimeLLM、Qwen/InternVL、WhisperX/FunASR/SenseVoice、Peepshow/VidClaude 中仍值得吸收的局部模块拆成 P0/P1/P2：

- P0：vsummary-style 任务产物管理；BiliNote-style 视频工作台 UI。
- P1：VideoRAG 多粒度检索；Qwen-VL 帧预处理；InternVL high-res tiling；VTimeLLM 时间定位评价。
- P2：ASR 后处理；帧报告 UI；内容导出交互。

结论仍是 selective reuse：继续复用低耦合模块和交互模式，不整体搬外部后端、模型运行时或下载逻辑。

## Update - 2026-07-04 21:12:00 | Codex GPT-5

### P0 landed: vsummary-style run/artifact registry foundation

Backlog 对应：`docs/external-code-module-reuse-backlog-2026-07-04.md` 的 P0 “vsummary 任务流水线与 artifact registry”。

新增模块：

```text
src/video_knowledge_pipeline/run_artifact_registry.py
```

新增能力：

- `register_bundle_run(...)`：给任意 bundle 任务登记一条 run。
- `build_run_artifact_registry(...)`：扫描 `runs/*/run.json`，生成统一索引。
- 每条 run 写入：
  - `runs/<run-id>/run.json`
  - `runs/<run-id>/run.md`
- bundle 级索引写入：
  - `run-artifact-registry.json`
  - `run-artifact-registry.md`
  - `mcp-run-artifact-registry.args.json`

CLI/MCP：

```powershell
.\scripts\video-knowledge.ps1 run-artifact-registry <webui-bundle>
```

MCP tools：

```text
run_artifact_registry
run_artifact_registry_tool
```

首个接入点：`vision-review-queue`。

现在每次生成疑难点多模态批次队列时，会同步登记：

```text
runs/vision-review-queue/run.json
runs/vision-review-queue/run.md
run-artifact-registry.json
run-artifact-registry.md
```

登记内容包括：

- run status：`completed` / `needs_execution` / `needs_retry`
- artifacts：queue json/md/html/run script/MCP args
- failed items：失败或不完整的 timeline indexes
- retry command：可复制的 PowerShell 批次重试入口
- operator boundary：默认仅生成命令，真实云视觉调用仍需 operator 执行 `-Execute`

边界保持不变：

- 不启动服务。
- 不处理视频。
- 不调用云 API。
- 不写入 secret。
- 不替换现有 CLI/MCP/OpenClaw/static bundle 契约。

验证：

```powershell
python -m py_compile src\video_knowledge_pipeline\run_artifact_registry.py src\video_knowledge_pipeline\vision_review_queue.py src\video_knowledge_pipeline\cli.py src\video_knowledge_pipeline\mcp_server.py tests\test_run_artifact_registry.py tests\test_vision_review_queue.py
```

通过。

手工 smoke：创建最小 bundle，运行 `vision_review_queue` 后确认：

- `run-artifact-registry.json` 存在；
- `runs/vision-review-queue/run.json` 存在；
- manifest 登记 `run_artifact_registry_json`、`run_artifact_registry_report`、`mcp_run_artifact_registry_args`；
- CLI `run-artifact-registry --no-write` 可读取并输出 registry。

pytest 说明：本轮尝试运行 `tests/test_run_artifact_registry.py tests/test_vision_review_queue.py`，但当前 Windows sandbox 下 pytest 创建的 `--basetemp` 目录会变成不可枚举目录，导致 pytest setup/sessionfinish 报 `PermissionError: Access is denied`。因此本轮以 `py_compile` + 手工 smoke 作为有效验证，后续在可见 PowerShell 或清理 pytest temp ACL 后再跑完整 pytest。

## Update - 2026-07-04 21:19:56 | Codex GPT-5

### P0 continued: BiliNote-style task history in task console

Backlog 对应：`docs/external-code-module-reuse-backlog-2026-07-04.md` 的 P0 “BiliNote 任务工作台/任务历史 UI 局部复用”。

本轮没有搬运 BiliNote 的整套 UI，而是吸收它更适合 VKP 的局部能力：

- 用一个静态控制台集中展示任务状态；
- 每个任务保留可追踪的 run 记录；
- 失败项、未执行项和重试命令直接暴露给人和 agent；
- UI 只做本地查看、复制命令和跳转，不绕过人工确认边界。

代码落点：

```text
src/video_knowledge_pipeline/task_console.py
tests/test_task_console.py
```

新增控制台数据：

- `task-console.json.run_registry`
- 从 bundle 内 `run-artifact-registry.json` 读取：
  - `run_count`
  - `status_counts`
  - 最近 20 条 runs
  - 每条 run 的 artifact count、failed count、retry command、report path

新增控制台 UI：

- `task-console.html` 增加“任务历史”区块；
- 无 run 时显示 `run-artifact-registry` 刷新命令；
- 有 run 时按卡片展示：
  - run title / type / status
  - artifact 数量
  - failed item 数量
  - run report 链接
  - 可复制 retry command

这一步的意义：

- `vision-review-queue` 生成的疑难点批次不再只是散落的 json/md/html/ps1；
- 它会进入统一 run registry；
- task console 直接显示这批任务是否 `needs_execution`、`needs_retry` 或 `completed`；
- 后续 ebook batch、ASR run、OCR crop recovery、smart summary generation 都可以复用同一个 run registry + task console 展示模型。

保留边界：

- 不自动执行云多模态；
- 不自动重试失败批次；
- 不启动长期服务；
- 不处理真实视频；
- 不写入 secret；
- `review.html` 仍然是详细人工审核界面，`task-console.html` 是轻量任务控制台。

验证：

```powershell
python -m py_compile src\video_knowledge_pipeline\task_console.py tests\test_task_console.py
```

已通过。

测试断言已覆盖：

- 导出的 `task-console.json` 包含 `run_registry`；
- `task-console.html` 包含“任务历史”；
- 已登记 run 的标题和 retry command 会出现在页面中。

后续复用方向：

- ebook/图文结构化批处理接入 run registry；
- ASR 本地 runner 接入 run registry；
- smart-summary / Codex summary generation 接入 run registry；
- task console 增加按 status 过滤、批次进度条、失败重试分组。

验证补充：

```powershell
python -m pytest -q tests\test_task_console.py tests\test_run_artifact_registry.py
```

本轮仍未能在当前 Codex 托管 shell 中完成 pytest。失败发生在 pytest fixture 创建 `tmp_path` 前，根因是 `%USERPROFILE%\AppData\Local\Temp\pytest-of-%USERNAME%` 目录 `os.scandir` 被 Windows 拒绝访问，同时 `.pytest_cache` 也不可写；业务断言尚未执行。当前有效验证为：`py_compile`、`export-task-console` smoke、HTML 关键字检查、`git diff --check`。

## Update - 2026-07-04 21:27:31 | Codex GPT-5

### P0 continued: ebook/visual-structure batch registered as run artifact

Backlog 对应：`docs/external-code-module-reuse-backlog-2026-07-04.md` 的推荐下一阶段第 1 项：“任务产物管理先行：把 vsummary-style run/artifact registry 接到 ebook batch、多模态 batch、smart-summary LLM chunk”。

本轮把 `run_artifact_registry` 从多模态队列继续扩展到 ebook/图文结构化批处理。

代码落点：

```text
src/video_knowledge_pipeline/visual_structure.py
tests/test_screen_text_recovery.py
```

新增行为：

- 每次运行 `run-visual-structure` 都会登记一条 run：
  - `runs/visual-structure-ebook/run.json`
  - `runs/visual-structure-ebook/run.md`
  - `run-artifact-registry.json/md`
- run type：`visual_structure_ebook`
- run title：`Visual structure ebook batch`
- artifacts 包含：
  - `visual-structure-report.md`
  - `visual-structure-handoff.md`
  - `visual-structure-handoff.json`
  - `visual-structure-input-template.json`
- failed items 记录 ebook 失败帧：
  - timeline index
  - blocker / quality reason
  - image path
  - output dir
  - artifact path

状态语义：

| 状态 | 含义 |
| --- | --- |
| `not_needed` | 当前没有候选图文帧 |
| `needs_execution` | 有候选，但本轮只是 preview，尚未执行 ebook pipeline |
| `completed` | 已执行 ebook pipeline 且没有 blocker |
| `needs_retry` | 已执行 ebook pipeline，但存在 `umi_ocr_missing`、`ocr_wrapper_only`、`ocr_text_empty`、低信息量或其他 blocker |

关键修正：

- preview 产生的 `needs_execution` run，其 retry command 会自动补上 `--execute-ebook-pipeline`，让 task console 复制出来的是“下一步执行命令”，不是重复 preview。
- `ocr_wrapper_only`、空结果、低信息量结果仍不会清除 screen text blocker，只会进入 failed items / review / retry 机制。

这一步吸收的外部项目能力：

- vsummary-style run/artifact registry：任务可追踪、产物可索引、失败可重试；
- BiliNote-style task console：人类 UI 可以看到 ebook 批次状态，而不是只看散落的报告文件。

手工 smoke：

```powershell
python -m video_knowledge_pipeline.cli run-visual-structure outputs\manual-visual-structure-registry-smoke-20260704\bundle --limit 1
python -m video_knowledge_pipeline.cli export-task-console outputs\manual-visual-structure-registry-smoke-20260704\bundle --no-refresh
```

确认结果：

- `run_artifact.status = needs_execution`
- `retry_command` 包含 `--execute-ebook-pipeline`
- `task-console.html` 的“任务历史”显示 `Visual structure ebook batch`、`needs_execution` 和复制命令。

验证：

```powershell
python -m py_compile src\video_knowledge_pipeline\visual_structure.py tests\test_screen_text_recovery.py
```

已通过。

pytest 限制同前：当前托管 shell 的 pytest 临时目录 ACL 仍阻止 fixture 创建，业务断言无法执行；本轮以 py_compile + CLI smoke + HTML 关键字检查作为有效验证。

## Update - 2026-07-04 21:32:18 | Codex GPT-5

### P0 continued: smart-summary Codex generation registered as run artifact

Backlog 对应：`docs/external-code-module-reuse-backlog-2026-07-04.md` 的推荐下一阶段第 1 项：“任务产物管理先行：把 vsummary-style run/artifact registry 接到 ebook batch、多模态 batch、smart-summary LLM chunk”。

本轮把 `run_artifact_registry` 继续扩展到智能总结生成层，重点覆盖 `generate-smart-summary-with-codex`。

代码落点：

```text
src/video_knowledge_pipeline/smart_summary_codex.py
tests/test_knowledge_export.py
```

新增行为：

- 每次运行 `generate-smart-summary-with-codex` 都会登记一条 run：
  - `runs/smart-summary-codex/run.json`
  - `runs/smart-summary-codex/run.md`
  - `run-artifact-registry.json/md`
- run type：`smart_summary_codex`
- run title：`Smart summary Codex generation`
- artifacts 包含：
  - `exports/smart-summary.codex.md`
  - `exports/smart-summary-codex-prompt.md`
  - `exports/smart-summary-codex-status.json/md`
  - `exports/smart-summary-quality.json/md`
  - `exports/smart-summary-input-pack.md`
  - `exports/long-video-memory-pack.md`
  - `exports/smart-summary-chapters.md`
  - `exports/course-map.md`

状态语义：

| 状态 | 含义 |
| --- | --- |
| `needs_execution` | 尚未生成或安装 `smart-summary.codex.md` |
| `completed` | Codex/LLM 智能总结存在，且 `smart-summary-quality` 通过 |
| `needs_retry` | Codex/LLM 智能总结存在，但质量门禁未通过 |

失败项：

- 质量门禁未通过的 check 会进入 `failed_items`；
- 例如 `overview_readable`、`time_coverage`、`balanced_sections`、`visual_boundary` 等；
- task console 可直接显示失败数量和重试命令。

边界保持：

- 当前实现仍是 `codex_first_llm_layer`；
- 不调用在线 LLM；
- 不处理音视频媒体；
- 后续接在线/云端 LLM 时必须复用同一 evidence pack 和 quality gate；
- run registry 只记录状态、产物和重试命令，不自动发布、不写知识库。

手工 smoke：

```powershell
python -m video_knowledge_pipeline.cli export-knowledge-note outputs\manual-smart-summary-registry-smoke-20260704\bundle --title "Smart Summary Registry Smoke"
python -m video_knowledge_pipeline.cli generate-smart-summary-with-codex outputs\manual-smart-summary-registry-smoke-20260704\bundle
```

确认结果：

- `run_artifact.run_type = smart_summary_codex`
- `run_artifact.status = completed`
- `failed_items = []`
- registry 包含 `status_counts.completed = 1`
- artifacts 覆盖 Codex summary、prompt、quality、input pack、long memory pack、chapter pack。

验证：

```powershell
python -m py_compile src\video_knowledge_pipeline\smart_summary_codex.py tests\test_knowledge_export.py
```

已通过。

pytest 限制同前：当前托管 shell 的 pytest 临时目录 ACL 仍阻止 fixture 创建，业务断言无法执行；本轮以 py_compile + CLI smoke 作为有效验证。

## Update - 2026-07-04 21:36:27 | Codex GPT-5

### Documentation snapshot: remaining external-code reuse modules

本次文档化对应用户追问：“还有哪些值得复用的代码模块”。结论已经同步到：

```text
docs/external-code-module-reuse-backlog-2026-07-04.md
```

核心判断如下：

- P0 的 vsummary-style run/artifact registry 已经开始落地，并已接入：
  - `vision-review-queue`
  - `run-visual-structure` / ebook batch
  - `generate-smart-summary-with-codex`
  - `task-console.html` 的任务历史区
- BiliNote-style transcript 清洗、转写校对、transcript editor、mind-map prompt pack 已经作为低耦合模块进入 VKP。
- VideoRAG / MovieChat / VTimeLLM / Qwen / InternVL 的第一层能力已经拆出，但仍有几个值得继续实施的模块：
  - `high_res_tile_plan`：InternVL-style dynamic tiling，用来补 ebook/OCR 对小字、表格、软件界面失败的证据缺口；
  - `vlm_preprocess.py`：Qwen/InternVL-style 图像和帧组预处理统一层，让云 VLM 和本地 VLM 共用 resize/compress/payload planning；
  - `timeline_alignment_audit`：VTime-style temporal grounding audit，用来检查 ASR 起止、抽帧时间、青龙打标时间、review_start 的冲突；
  - task console 疑难点队列：吸收 Peepshow/VidClaude/vsummary 的批次状态、失败项、重试命令展示；
  - VideoRAG 多粒度 chunk：把 transcript、visual evidence、chapter、review gap、content asset 拆成可检索层。

当前建议执行顺序：

1. `high_res_tile_plan`：先解决最痛的小字/图文结构化 blocker。
2. `vlm_preprocess.py`：统一 tile、单帧、多帧组的多模态 payload。
3. `timeline_alignment_audit`：把人工审核时间戳错位问题做成可测的质量报告。
4. task console queue：把疑难点诊断、批次处理、失败重试固化进 UI。
5. VideoRAG 多粒度增强：在证据链稳定后再扩展检索/问答。

重要边界：这些模块继续采用 selective reuse，不迁移外部项目完整后端、不替换 VKP CLI/MCP/OpenClaw/static bundle 架构、不把下载逻辑吸收到 VKP、不默认大批量外发私有视频帧。

## Update - 2026-07-04 21:44:30 | Codex GPT-5

### P1 landed: InternVL-style high-res tile plan

Backlog 对应：`docs/external-code-module-reuse-backlog-2026-07-04.md` 的 P1 “InternVL dynamic tiling / high-res frame 处理”。

本轮新增 `high-res-tile-plan`，把 InternVL dynamic tiling 的核心思想落成 VKP 本地证据包：对 ebook/OCR 空结果、wrapper-only、低信息量，以及 PPT、表格、软件界面、小字 UI 等 detail-heavy frame，先生成局部 high-resolution tile，再交给本地 VLM、定向云 VLM 或人工复核。

代码落点：

```text
src/video_knowledge_pipeline/high_res_tile_plan.py
src/video_knowledge_pipeline/cli.py
src/video_knowledge_pipeline/mcp_server.py
README.md
AGENT_DISCOVERY.md
```

新增入口：

```powershell
.\scripts\video-knowledge.ps1 high-res-tile-plan <webui-bundle>
.\scripts\video-knowledge.ps1 high-res-tile-plan <webui-bundle> --execute-tiles --limit 30 --tile-size 768 --max-tiles-per-image 12
```

MCP / agent 入口：

```text
run_high_res_tile_plan
high_res_tile_plan_tool
mcp-high-res-tile-plan.args.json
```

产物：

```text
high-res-tile-plan.json
high-res-tile-plan.md
mcp-high-res-tile-plan.args.json
high-res-tiles/timeline-0001/tile-01.jpg
runs/high-res-tile-plan/run.json
runs/high-res-tile-plan/run.md
run-artifact-registry.json/md
```

状态语义：

| 状态 | 含义 |
| --- | --- |
| `not_needed` | 当前没有高分辨率 tile 候选 |
| `needs_execution` | 已找到候选，但本轮只是 preview，尚未写 tile 图片 |
| `completed` | 已写出 tile 图片且没有失败 |
| `needs_retry` | 源图缺失、Pillow 不可用或 tile 写入失败 |

边界保持：

- 本工具只做本地 tile 证据准备；
- 不调用云 API；
- 不启动本地 VLM；
- 不执行 OCR；
- 不把 tile 当作 OCR 成功；
- 不覆盖 `visual_text`、`structured_visual` 或多模态理解结果。

手工 smoke：

```powershell
$env:PYTHONPATH='src'
python -m video_knowledge_pipeline.cli high-res-tile-plan outputs\manual-high-res-tile-smoke-20260704\bundle --limit 1 --tile-size 640 --max-tiles-per-image 6
python -m video_knowledge_pipeline.cli high-res-tile-plan outputs\manual-high-res-tile-smoke-20260704\bundle --execute-tiles --limit 1 --tile-size 640 --max-tiles-per-image 6
python -m video_knowledge_pipeline.cli export-task-console outputs\manual-high-res-tile-smoke-20260704\bundle --no-refresh
```

确认结果：

- preview：`tiles_planned = 6`、`tiles_written = 0`、run status = `needs_execution`；
- execute：`tiles_planned = 6`、`tiles_written = 6`、`tiles_failed = 0`、run status = `completed`；
- `task-console.html` 的“任务历史”显示 `High-res tile plan`、`completed`、`high_res_tile_plan`。

验证：

```powershell
python -m py_compile src\video_knowledge_pipeline\high_res_tile_plan.py src\video_knowledge_pipeline\cli.py src\video_knowledge_pipeline\mcp_server.py
```

已通过。

测试文件说明：本轮尝试通过 `apply_patch` 新增 `tests/test_high_res_tile_plan.py` 时被当前 Codex sandbox 审批层拒绝；没有绕过该拒绝。当前有效验证为 py_compile + CLI smoke + task console/registry 产物检查。后续需要用户明确允许后补单元测试文件。

## Update - 2026-07-04 22:04:00 | Codex GPT-5

### P1 landed: Qwen/InternVL-style VLM preprocess boundary

Backlog 对应：`docs/external-code-module-reuse-backlog-2026-07-04.md` 的 P1 “Qwen-VL / qwen-vl-utils 视频帧预处理”。

本轮新增 `vlm_preprocess.py`，把原先散落在 provider smoke、单帧多模态、连续帧多模态里的 image probe / resize / JPEG 压缩逻辑抽成共享本地预处理边界。

代码落点：

```text
src/video_knowledge_pipeline/vlm_preprocess.py
src/video_knowledge_pipeline/vision_provider_smoke.py
src/video_knowledge_pipeline/multimodal_frame_analyzer.py
src/video_knowledge_pipeline/temporal_visual_analyzer.py
tests/test_vision_providers.py
README.md
AGENT_DISCOVERY.md
```

新增行为：

- `prepare_vlm_image_inputs(...)` 统一输出：
  - `schema = video_knowledge_pipeline.vlm_preprocess.v1`
  - `source_image_paths`
  - `prepared_image_paths`
  - `total_source_bytes`
  - `total_prepared_bytes`
  - per-image `items[]`，包含顺序、role、mime、source/prepared path、bytes、error；
- `prepare_image_probe(...)` 保持旧 `image_probe` 字段兼容：
  - `image_paths`
  - `source_image_paths`
  - `total_probe_bytes`
  - `max_edge`
  - `jpeg_quality`
- `vision_provider_smoke` 的私有 `_prepare_image_probe` 变成 wrapper；
- `run_multimodal_frame_analysis` 和 `run_temporal_visual_analysis` 直接使用共享 `prepare_image_probe`。

边界保持：

- 只做本地图像选择、缩放、压缩和 metadata；
- 不调用云 API；
- 不启动本地 VLM；
- 不生成 base64 报告；
- 不改变 preflight/confirm 机制；
- 不扩大默认在线多模态调用范围。

验证：

```powershell
python -m py_compile src\video_knowledge_pipeline\vlm_preprocess.py src\video_knowledge_pipeline\vision_provider_smoke.py src\video_knowledge_pipeline\multimodal_frame_analyzer.py src\video_knowledge_pipeline\temporal_visual_analyzer.py
```

已通过。

后续增强：把 `high-res-tile-plan` 的 tile 结果、单帧、多帧组统一交给 `vlm_preprocess.py` 生成 provider-neutral payload plan，并补 tile result merge / confidence / review 写回。

Smoke supplement:

```powershell
$env:PYTHONPATH='src'
python -m video_knowledge_pipeline.cli vision-provider-smoke --provider fixture --output-dir outputs\manual-vlm-preprocess-smoke-20260704\smoke --single-image outputs\manual-vlm-preprocess-smoke-20260704\large.jpg --image-probe-max-edge 320 --image-probe-jpeg-quality 55
```

确认结果：`image_probe.schema = video_knowledge_pipeline.vlm_preprocess.v1`，`status = ok`，源图 `15627` bytes 压缩到 `703` bytes，fixture provider smoke `safe_to_execute = true`。

pytest 状态：`python -m pytest tests\test_vision_providers.py -q -k vlm_preprocess` 仍被本机 pytest basetemp/`.pytest_cache` ACL 拒绝，业务代码用 py_compile + direct smoke + provider smoke 验证。
## Update - 2026-07-04 21:57:46 | Codex GPT-5

### P1 landed: VTime-style timeline alignment audit

Backlog 对应：`docs/external-code-module-reuse-backlog-2026-07-04.md` 的 P1 “VTimeLLM 时间定位评价模块”。

本轮新增 `timeline-alignment-audit`，把 VTimeLLM / temporal grounding 的关键思想落成 VKP 的本地质量审计：不直接改时间轴，而是检查 ASR 起止、抽帧/截图时间、青龙打标时间和人工审核 `review_start` 之间是否冲突。它主要解决两类实际问题：审核页跳到一句话说完的位置，而不是开始位置；以及 ASR、打标器、抽帧窗口彼此不一致导致人工复核困难。

代码落点：

```text
src/video_knowledge_pipeline/timeline_alignment_audit.py
src/video_knowledge_pipeline/cli.py
src/video_knowledge_pipeline/mcp_server.py
tests/test_multimodal_sample_review.py
README.md
AGENT_DISCOVERY.md
```

CLI 入口：

```powershell
.\scripts\video-knowledge.ps1 timeline-alignment-audit <webui-bundle> --tolerance-seconds 2
```

MCP / agent 入口：

```text
timeline_alignment_audit
mcp-timeline-alignment-audit.args.json
```

产物：

```text
timeline-alignment-audit.json
timeline-alignment-audit.md
mcp-timeline-alignment-audit.args.json
```

审计项：

- `missing_asr_overlap`：timeline item 没有匹配到 ASR segment；
- `review_start_outside_segment`：审核跳转时间不在当前段落时间范围内；
- `review_start_mismatch`：审核跳转时间和匹配到的 ASR 起点差距超过容差；
- `frame_time_outside_segment`：抽帧/截图时间落在段落窗口外；
- `tagger_time_conflict`：青龙打标时间与 ASR/段落窗口明显冲突。

边界保持：

- 只读审计，不修改 `timeline.json`；
- 不调用云 API；
- 不处理视频、不抽帧；
- 不替代人工判断，只给出可复核的问题列表和 evidence fields。

Smoke：

```powershell
$env:PYTHONPATH='src'
python -m video_knowledge_pipeline.cli timeline-alignment-audit outputs\manual-timeline-alignment-smoke-20260704\bundle --tolerance-seconds 2
python -m video_knowledge_pipeline.cli mcp-call timeline_alignment_audit outputs\manual-timeline-alignment-smoke-20260704\bundle\mcp-timeline-alignment-audit.args.json
```

确认结果：测试 bundle 中成功识别 `review_start_mismatch = 1`、`tagger_time_conflict = 1`，并写出 JSON/Markdown/MCP args。

后续增强：`task-console.html` 已接入 `timeline-alignment-audit.json`；下一步把结果接入 `review.html`，在时间戳旁显示 mismatch badge，并生成“使用 ASR segment start 修复 review_start”的 preview-only 修复建议。
## Update - 2026-07-04 22:09:58 | Codex GPT-5

### P1 continued: timeline alignment audit enters task console

本轮把 `timeline-alignment-audit` 从独立报告推进到 vsummary/BiliNote-style 可见任务流：

- `timeline_alignment_audit` 现在登记 run artifact：`runs/timeline-alignment-audit/run.json/md`。
- run status 语义：
  - `completed`：有 transcript，且当前容差下没有时间错位；
  - `needs_review`：发现 `review_start_mismatch`、`tagger_time_conflict`、`frame_time_outside_segment` 等冲突；
  - `needs_input`：缺少 normalized/corrected transcript sidecar，无法做 ASR 对齐审计。
- `export-task-console` 会本地运行一次 timeline audit，刷新 manifest/MCP args，并把结果写进：
  - `task-console.json -> timeline_alignment`
  - `status.timeline_alignment_issue_count`
  - `task-console.html` 指标卡“时间错位”
  - 关键产物链接 `timeline-alignment-audit.md`
  - 下一步命令 `timeline_alignment`
  - 任务历史 `Timeline alignment audit`

新增/修改文件：

```text
src/video_knowledge_pipeline/timeline_alignment_audit.py
src/video_knowledge_pipeline/task_console.py
tests/test_task_console.py
README.md
AGENT_DISCOVERY.md
docs/external-code-module-reuse-backlog-2026-07-04.md
docs/external-project-reuse-implementation-2026-07-04.md
```

验证：

```powershell
$env:PYTHONPATH='src'
python -m py_compile src\video_knowledge_pipeline\timeline_alignment_audit.py src\video_knowledge_pipeline\task_console.py tests\test_task_console.py
python -m video_knowledge_pipeline.cli export-task-console outputs\manual-timeline-alignment-smoke-20260704\bundle --no-refresh
```

manual smoke 结果：`timeline_alignment_issue_count = 1`，`timeline_alignment.status = needs_review`，`task-console.html` 包含“时间错位”和“时间轴对齐审计”，`run_registry.run_count = 1` 且包含 `timeline-alignment-audit`。

另有一个无 transcript 的独立 smoke：`timeline_alignment.status = needs_input`，与预期一致。

pytest 状态：`tests/test_task_console.py` 仍被本机 `%USERPROFILE%\AppData\Local\Temp\pytest-of-%USERNAME%` ACL 拒绝，未进入测试体；业务逻辑用 py_compile + CLI/manual smoke 验证。

## Update - 2026-07-04 22:14:28 | Codex GPT-5

### Documentation: remaining reusable modules after external project review

已把“还有哪些值得继续复用的代码模块”整理进：

```text
docs/external-code-module-reuse-backlog-2026-07-04.md
```

本次文档化后的判断是：VKP 已经不应继续追求整体搬运外部项目，而应继续吸收低耦合模块和交互模式。当前最值得继续落地的不是新模型仓库，而是能进入现有 bundle / timeline / review / task console 的工程能力。

#### 下一步最高优先级

1. `review.html` 时间轴对齐提示：读取 `timeline-alignment-audit.json`，给每条 item 显示时间错位 badge、ASR 起点、抽帧时间、青龙打标时间和 preview-only 修复建议。
2. `prepare-review-session` 时间轴分组：把 `timeline_alignment_issue` 作为人工复核原因，进入 `review-pack.md/json` 和 `review-notes.todo.json`。
3. `tile_result_merge`：把 high-res tile 的 OCR/VLM/人工结果导入 `visual_text`、`structured_visual` 或 review notes，解决 ebook/OCR 空结果后的消费问题。
4. task console 队列继续收拢：ebook batch、tile、vision-review-queue、smart-summary、timeline audit 都应以 run artifact 展示状态、失败项、重试命令和批次大小。
5. smart-summary section workflow：基于 corrected transcript、long-video-memory-pack、chapter pack 做章节级重生成和质量门禁。

#### 复用边界

- `vsummary`：继续复用任务状态、provider 网关、失败恢复思想，不整体迁移后端。
- `BiliNote`：继续复用 transcript 清洗、分块、编辑/预览交互，不整体迁移 React UI。
- VideoRAG / MovieChat：继续复用 memory/chunk/RAG 数据结构，不默认运行重模型服务。
- Qwen / InternVL / LLaVA：继续复用图像预处理、tile、多图输入和 adapter 形态，不嵌模型源码。
- VTimeLLM：继续复用时间定位评价思路，落成 VKP 本地审计和 review UI 提示。

#### 验收口径

后续每吸收一个外部模块，都应至少满足：

- 有 CLI/MCP 或静态 WebUI 入口；
- 有 bundle 内 JSON/Markdown 产物；
- 有 run artifact 或状态报告；
- 不默认调用云端模型；
- 不自动修改原始 timeline，除非通过显式导入/人工审核；
- 真实失败项能进入 retry 或 review pack。

## Update - 2026-07-04 22:27:35 | Codex GPT-5

### Implementation: timeline alignment review workflow

承接 backlog P0，本轮把时间轴对齐审计接入实际审核工作流，而不再只停留在报告/控制台层。

代码改动：

- `webui_bridge.py`
  - `refresh-review-html` 和新 bundle HTML 渲染前执行/读取 `timeline_alignment_audit`；
  - 将有问题的 item 作为只读 `timeline_alignment` 注入渲染包；
  - 返回 `timeline_alignment_issue_count` 和 `timeline_alignment_report`。
- `lecture_package.py`
  - `review.html` item 增加 `time-align` chip；
  - 新增“时间轴对齐风险”区块，展示当前跳转、ASR 建议起点、抽帧时间、打标器时间、建议 `review_start`；
  - 页面只提示，不写回 timeline。
- `review_session.py`
  - `prepare-review-session` 读取 `timeline-alignment-audit.json`；
  - 新增 `timeline_alignment_issue` reason/group/filter；
  - review target、review pack、todo JSON 保留 alignment 摘要；
  - 建议状态为 `needs_fix`。

验证 bundle：

```text
outputs/manual-timeline-alignment-smoke-20260704/bundle
```

关键验收证据：

- `review.html` 搜索到 `时间轴对齐风险`；
- `review-pack.md` 搜索到 `timeline_alignment_issue`；
- `review-notes.todo.json` 搜索到 `suggested_review_start`；
- 编译检查通过。

边界：该功能不直接修正时间戳。它只把 ASR / 抽帧 / 打标器冲突显性化，给人工审核一个可信修复入口。
## 2026-07-04 22:38:08 | Codex / GPT-5：P1 landed - Tile result merge

本轮把 P1 `tile_result_merge` 从 backlog 落到 VKP 主流程，补上 `high-res-tile-plan` 之后的结果消费环节。

新增能力：

- `src/video_knowledge_pipeline/tile_result_merge.py`
  - 输入 `tile-result-import.json`，支持 `tile_results` / `results` / `items` 三种列表字段。
  - 接收本地 OCR、本地 VLM、已批准云 VLM 或人工标注产生的 tile 结果。
  - 默认 preview，只生成 `tile-result-merge.json/md`、`tile-result-import.template.json`、`mcp-tile-result-merge.args.json`。
  - 显式 `--execute` 才写回 `timeline.json`。
- 写回规则：
  - 高置信、非空、非 wrapper-only 的结果写入 `visual_text`，并把结构化结果追加到 `structured_visual`。
  - 仅在有真实文字或结构化结果时清除 `missing_visual_text`、`visual_text_empty`、`ocr_text_empty`、`ocr_wrapper_only`、`structured_visual_without_structure`。
  - 空结果、低置信、wrapper-only、failed/error/parse_failed 结果进入 `tile_review_targets`，保留 `missing_visual_text`，并标记 `needs_human_review=true`。
- CLI / MCP / UI：
  - CLI：`tile-result-merge <webui-bundle> --input-json <tile-result-import.json> [--execute] [--min-confidence 0.65]`
  - MCP：`tile_result_merge_tool` / `run_tile_result_merge`
  - `task-console.html` 增加“Tile 结果合并”命令和 `tile-result-merge.md` 产物链接。
  - run registry 登记 `tile_result_merge`，失败/复核项进入 failed items，便于 UI 后续重试。

验收 smoke：

```powershell
$env:PYTHONPATH='src'
python -m video_knowledge_pipeline.cli tile-result-merge outputs\manual-tile-result-merge-smoke-20260704\bundle --input-json outputs\manual-tile-result-merge-smoke-20260704\bundle\tile-import.json
python -m video_knowledge_pipeline.cli tile-result-merge outputs\manual-tile-result-merge-smoke-20260704\bundle --input-json outputs\manual-tile-result-merge-smoke-20260704\bundle\tile-import.json --execute
python -m video_knowledge_pipeline.cli export-task-console outputs\manual-tile-result-merge-smoke-20260704\bundle --no-refresh
```

结果：

- `index=0` 的高置信 tile 结果写回 `visual_text` 和 `structured_visual`，OCR blocker 被清除。
- `index=1` 的低置信空结果进入 `tile_review_targets`，保留 `missing_visual_text` / `ocr_text_empty`，并新增 `tile_result_needs_review`。
- `tile-result-merge.md/json`、`tile-result-import.template.json`、`mcp-tile-result-merge.args.json`、`runs/tile-result-merge/run.json` 已生成。
- `task-console.html` 的命令区和产物区能显示 Tile 结果合并入口。

边界：该模块不运行 OCR、不调用云 API、不启动模型服务，只消费已产出的 tile 结果；低质量结果不会被计为 OCR 成功。
## 2026-07-04 22:44:43 | Codex / GPT-5：Tile review targets enter review pack

本轮继续推进 P1 `tile_result_merge` 后半段：把低置信、空结果、wrapper-only 的 tile 结果接入人工复核包，而不是只停留在 `timeline.json` 的 `quality_issues`。

落地内容：

- `prepare-review-session` 识别 `tile_result_needs_review` 与 `tile_review_targets`。
- `review_targets.by_reason` 新增 `tile_result_needs_review` 统计。
- `review-pack.md` 新增独立分组“Tile 结果待复核”。
- review pack 表格新增 `Tile review` 列，展示 tile id、置信度、失败原因、证据路径。
- `review-notes.todo.json` 每条 row 保留 `tile_review_targets`，方便人工回填 `corrected_visual_text`。
- 建议状态：tile 低置信/空结果默认建议 `corrected_visual_text`，动作提示强调先核对 tile 证据图。

验证：

```powershell
$env:PYTHONPATH='src'
python -m video_knowledge_pipeline.cli prepare-review-session outputs\manual-tile-result-merge-smoke-20260704\bundle --limit 0 --group-by reason
```

smoke 结果：

- `review_targets.by_reason.tile_result_needs_review = 1`。
- `review-pack.md` 包含“Tile 结果待复核”和 `tile=0001-01; conf=0.32; reasons=tile_result_low_confidence,tile_result_empty`。
- `review-notes.todo.json` 包含 `tile_review_targets` 和 evidence path `high-res-tiles/timeline-0001/tile-01.jpg`。

边界：仍然不自动接受低置信 tile 结果；只有人工补入 `corrected_visual_text` 或重新导入高置信 tile 结果后，才能关闭该缺口。

## 2026-07-04 22:50:50 | Codex / GPT-5：Tile result import builder

本轮继续完成 P1 tile 分支的“减少人工拼 JSON”环节：新增 `tile-result-import-build`，把 high-res tile plan 和已有的本地 OCR/VLM/人工结果文件转换为标准 `tile-result-import.json`。

新增能力：

- `src/video_knowledge_pipeline/tile_result_import_builder.py`
  - 读取 `high-res-tile-plan.json`。
  - 可选读取 `--results-dir` 下的 `.json` / `.txt` / `.md` tile 结果文件。
  - 按 `tile_id` 或 tile 图片 stem 匹配结果。
  - 输出 `tile-result-import.json`、`tile-result-import.md`、`mcp-tile-result-import-build.args.json`。
  - 未匹配到结果的 tile 标为 `pending_result`，不会假装 OCR/VLM 成功。
- CLI / MCP / UI：
  - CLI：`tile-result-import-build <webui-bundle> --results-dir <tile-results-dir>`
  - MCP：`tile_result_import_build_tool` / `build_tile_result_import`
  - `task-console.html` 新增“Tile 导入包生成”，并在产物区链接 `tile-result-import.md`。
  - run registry 登记 `tile_result_import_build`。

验证：

```powershell
$env:PYTHONPATH='src'
python -m video_knowledge_pipeline.cli tile-result-import-build outputs\manual-high-res-tile-smoke-20260704\bundle --results-dir outputs\manual-high-res-tile-smoke-20260704\bundle\tile-results
python -m video_knowledge_pipeline.cli tile-result-merge outputs\manual-high-res-tile-smoke-20260704\bundle --input-json outputs\manual-high-res-tile-smoke-20260704\bundle\tile-result-import.json
python -m video_knowledge_pipeline.cli export-task-console outputs\manual-high-res-tile-smoke-20260704\bundle --no-refresh
```

smoke 结果：

- 6 个 tile 中匹配到 2 个本地结果文件，4 个保持 `pending_result`。
- `tile-result-merge` preview 能消费生成的 import：2 条 updates，4 条 review targets。
- `task-console.html` 显示“Tile 导入包生成”和“Tile 结果合并”，run registry 中包含 `tile_result_import_build`。

边界：该模块不执行 OCR/VLM、不调用云 API，只把已有结果归一化为 VKP import schema。

## Update - 2026-07-05 20:28:30 | Codex / GPT-5

### P0 landed: unified video workbench v1

Backlog 对应：`docs/external-code-reuse-remaining-modules-2026-07-05.md` 的 P0 “统一视频工作台”。

本轮把 BiliNote 的“视频 + 字幕/笔记同屏”、vsummary 的时间戳跳转/产物入口、Peepshow/VidClaude 的证据卡片思路，落成 VKP 自己的静态工作台，而不是整体搬外部 UI。

新增入口：

```powershell
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

```powershell
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

```powershell
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

### P0/P1 continued: BiliNote-style transcript arbitration review path

本轮继续吸收 BiliNote 转写编辑器、WhisperX/FunASR 多源时间文本证据和 VKP 自己的 review pack 机制，把 `transcript-source-arbitration` 的低置信字幕/ASR 冲突接到人可操作的审核界面。

实现要点：

- `review_session.py`
  - 从 `manifest.transcript_source_arbitration_json` 或默认 `transcript-source-arbitration.json` 读取仲裁报告。
  - 把 `review_rows` 映射成 `target_type=transcript_arbitration`。
  - 新增 `transcript_source_conflict` / `low_arbitration_confidence` reason、分组 label 和建议状态 `corrected_transcript`。
  - `review-pack.md/json` 展示这些冲突；`review-notes.todo.json` 明确跳过它们。
- `transcript_editor.py`
  - 在 `prepare-transcript-edit-session` 中附加 `arbitration_review` 到对应 segment。
  - `transcript-editor.html` 高亮冲突行，显示 chosen/original/suggested/alternatives，便于人工在同一个转写编辑工作台里修正。
- `tests/test_transcript_arbitration_review_integration.py`
  - 覆盖 review pack 中出现仲裁 target；
  - 覆盖 `review-notes.todo.json` 不接收 transcript arbitration target；
  - 覆盖 transcript editor 显示仲裁冲突。

验证命令：

```powershell
python -m py_compile src\video_knowledge_pipeline\review_session.py src\video_knowledge_pipeline\transcript_editor.py tests\test_transcript_arbitration_review_integration.py
$env:PYTHONPATH='src'; python -c "import importlib.util; spec=importlib.util.spec_from_file_location('tari','tests/test_transcript_arbitration_review_integration.py'); mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); mod.test_review_pack_includes_transcript_arbitration_targets(); mod.test_transcript_editor_shows_arbitration_conflicts(); print('transcript_arbitration_review_tests_ok')"
```

验收结果：

- `transcript_arbitration_review_tests_ok`
- fixture bundle 的 `review-pack.md/json` 包含仲裁冲突。
- fixture bundle 的 `transcript-editor.html` 包含 `仲裁待复核`。
- `review-notes.todo.json` 不包含 `transcript_source_conflict` / `low_arbitration_confidence`。

边界：这不是让 `apply-review-notes` 修改字幕。字幕纠错仍走 transcript editor 和 `apply-transcript-edits`；review pack 只负责把“需要看哪段字幕冲突”暴露给人。
## Update - 2026-07-05 20:52:57 | Codex / GPT-5

### P0/P1 continued: transcript arbitration closure after human edits

本轮继续把外部项目的转写编辑经验落到 VKP 的实际闭环里：不只是把字幕/ASR 仲裁冲突展示给人，还要在人通过 transcript editor 修完后，让 review closure 能识别“这个冲突已经处理过”。

实现细节：

- `review_session._transcript_arbitration_review_targets` 新增读取 `human-corrected-transcript.json`。
- 只接受 `source=human_transcript_editor` 的 sidecar 作为关闭依据，避免把自动仲裁结果误当成人审关闭。
- 按 `segment.index` 匹配仲裁 row 和人工纠正版 segment。
- 关闭后的 target 保留：
  - `closed=true`
  - `review_status=corrected_transcript`
  - `transcript_arbitration.human_corrected_text`
  - 仲裁报告和人工纠正版 transcript 证据路径。
- `review_closure_status` 新增非 timeline target 的关闭统计：`closed_by_reason`、`closed_targets`。
- `review-closure-status.md` 新增 “Closed By Reason” 表，方便用户看到字幕仲裁冲突已经关闭。

验证：

- `py_compile` 通过。
- Direct test runner 输出：`transcript_arbitration_closure_tests_ok`。
- 顺序 smoke 输出：`closed_by_reason` 中 `low_arbitration_confidence=1`、`transcript_source_conflict=1`，`open_by_reason` 不再包含这两个 reason。

边界：自动仲裁、source-arbitrated transcript、LLM corrected transcript 都不会直接关闭该 target；必须是 `apply-transcript-edits` 产生的 human sidecar。
## Update - 2026-07-05 20:57:42 | Codex / GPT-5

### P0 continued: BiliNote-style workbench review closure panel

本轮继续吸收 BiliNote 的“一个页面看任务和复核进度”体验，把 VKP 已有 `review-closure-status` 接到统一 `video-workbench.html`。这一步不是新增审核规则，而是把上一步已经完成的 transcript arbitration closure 放到用户真正会打开的主工作台里。

实现要点：

- `video_workbench.py`
  - 新增 `_review_closure_summary`：读取 `review-closure-status.json`，抽取 summary、open_by_reason、closed_by_reason。
  - 新增 `_review_closure_panel_html`：渲染 Open/Closed、字幕仲裁待复核、字幕仲裁已关闭。
  - `export_video_workbench` 输出 `review_closure` 到 JSON payload。
  - artifact list 增加 `review_closure_status` 和 `review_pack`。
- `tests/test_video_workbench.py`
  - fixture 增加 `review-closure-status.json/md` 和 `review-pack.md`。
  - 覆盖 HTML 与 JSON 中的 closure panel / transcript arbitration counts。

验证：

- `py_compile` 通过。
- Direct test runner 输出：`video_workbench_closure_panel_tests_ok`。
- CLI smoke `export-video-workbench outputs\test-video-workbench\bundle` 成功。
- grep 产物确认 `复核闭环`、`字幕仲裁待复核`、`review_closure` 出现在 HTML/JSON 中。

边界：仍然是静态 UI。按钮只打开报告或转写编辑器，不绕过人工导入边界。
## Update - 2026-07-05 21:02:44 | Codex / GPT-5

### P0/P1 continued: workbench evidence status from VTimeLLM/VideoRAG/tile reports

本轮继续把外部项目拆出来的局部能力往主工作台收束：VTimeLLM 的时间定位质量、VideoRAG 的片段索引、InternVL/Qwen-style tile 小字补救不再只是散落在各自报告里，而是在 `video-workbench.html` 里形成一个只读“证据状态”总览。

实现要点：

- `video_workbench.py`
  - 新增 `_evidence_status_summary`，读取 `timeline-alignment-audit.json`、`exports/video-moment-index.json` 和原始 `timeline.json` 的 tile review 字段。
  - 新增 `_evidence_status_panel_html`，显示时间错位、Tile 待复核、片段索引、覆盖时长。
  - `export_video_workbench` 输出 `evidence_status` 到 `video-workbench.json`。
  - artifact list 增加 `timeline_alignment_audit_report`。
- `tests/test_video_workbench.py`
  - fixture 增加 alignment / moment / tile 状态；
  - 覆盖 JSON summary 和 HTML 文案。

验证：

- `py_compile` 通过。
- Direct test runner 输出：`video_workbench_evidence_status_tests_ok`。
- CLI smoke + grep 确认 `evidence_status` 和“证据状态”面板写入产物。

边界：不新增检索后端、不启动 HTTP RAG、不触发 tile OCR/VLM，只消费已有报告作为 operator dashboard。
## Update - 2026-07-05 21:07:31 | Codex / GPT-5

### P0/P1 continued: evidence-status-to-row workflow in workbench

本轮把工作台从“显示证据状态”推进到“点击状态定位具体片段”。实现上继续复用已有报告和 timeline 字段，不重建 VTimeLLM、VideoRAG 或 tile 处理后端。

实现要点：

- `video_workbench.py`
  - 新增 `_timeline_alignment_by_index`、`_compact_alignment`、`_compact_tile_targets`；
  - `_timeline_row` 输出 `evidence_flags`、`timeline_alignment`、`tile_review_targets`；
  - evidence panel 按钮调用 `setFilter()` 过滤 timeline rows；
  - 详情区显示证据标记、时间对齐和 Tile 复核。
- `tests/test_video_workbench.py`
  - 覆盖 row-level flags、alignment metadata、tile target metadata；
  - 覆盖 HTML 中的筛选按钮和详情字段。

验证：

- `py_compile` 通过。
- Direct test runner 输出：`video_workbench_evidence_filter_tests_ok`。
- CLI smoke + grep 确认按钮和 row-level evidence 字段进入产物。

边界：静态 UI 筛选，不写盘、不调用 API、不自动修复证据。
## Update - 2026-07-05 21:17:52 | Codex / GPT-5

### P0/P1 continued: VideoRAG moment search embedded in workbench

本轮继续把外部项目的局部能力收束进统一视频工作台：ideo-workbench.html 现在直接内置 VideoRAG-style 片段搜索，不再要求用户先打开 task console iframe 再搜片段。

复用点：

- 复用 	ask_console._compact_moment_index 的 compact chunk 数据结构；
- 继续消费 xports/video-moment-index.json，不新增向量库、不启动 HTTP RAG 服务；
- 借鉴 vsummary 的 citation seek 体验：搜索结果点击后跳转播放器时间点，并选中对应 timeline row；
- 保持静态本地 HTML，不写盘、不调用云、不执行命令。

新增/修改：

- src/video_knowledge_pipeline/video_workbench.py
  - xport_video_workbench 输出 moment_index 到 ideo-workbench.json；
  - 新增 片段搜索 panel；
  - 新增
enderMomentSearch()、selectMoment()、
earestRow() 前端逻辑；
  - 点击 moment result 会跳视频、选择对应 timeline row，并保留证据路径和关键词。
- 	ests/test_video_workbench.py
  - fixture 的 ideo-moment-index.json 增加关键词、snippet、证据路径；
  - 覆盖 moment_index payload、搜索 UI、关键词和 JS hook。

验证：

`powershell
python -m py_compile src\video_knowledge_pipeline\video_workbench.py tests\test_video_workbench.py
$env:PYTHONPATH='src'; python -c "import importlib.util; spec=importlib.util.spec_from_file_location('tvw','tests/test_video_workbench.py'); mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); mod.test_export_video_workbench_writes_static_workspace(); mod.test_task_console_links_video_workbench(); print('video_workbench_moment_search_tests_ok')"
$env:PYTHONPATH='src'; python -m video_knowledge_pipeline.cli export-video-workbench outputs\test-video-workbench\bundle
rg -n -e "片段搜索" -e "momentSearchInput" -e "renderMomentSearch" -e "selectMoment" -e "moment_index" outputs\test-video-workbench\bundle\video-workbench.html outputs\test-video-workbench\bundle\video-workbench.json
git diff --check -- src\video_knowledge_pipeline\video_workbench.py tests\test_video_workbench.py
`

结果：

- Direct test runner: ideo_workbench_moment_search_tests_ok。
- CLI smoke 成功生成 ideo-workbench.html/json。
- 产物中能看到 片段搜索、momentSearchInput、
enderMomentSearch、selectMoment、moment_index。
- git diff --check 对本次代码/测试文件无报错。

后续继续榨取：

- 把 workbench 的 run queue 扩展到 ebook batch、tile merge、多模态 batch、smart-summary section workflow。
- 把 corrected transcript / source arbitration 差异视图放进 workbench 主页面。
- 让 smart-summary-input-pack 记录每章使用了哪些 transcript / OCR / vision / moment evidence。
## Update - 2026-07-05 21:25:18 | Codex / GPT-5

### P0 continued: workbench queue cards become actionable run details

本轮继续复用 vsummary 的 run status / retry command 和 BiliNote 的任务面板思路，把 ideo-workbench.html 的处理队列从摘要卡片推进到可操作的队列详情。

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
- 	ests/test_video_workbench.py
  - 覆盖 selectQueue、QUEUE_GROUPS、data-queue-key=\"document_ocr\"、queue-detail-retry、队列：。

验证：

`powershell
python -m py_compile src\video_knowledge_pipeline\video_workbench.py tests\test_video_workbench.py
$env:PYTHONPATH='src'; python -c "import importlib.util; spec=importlib.util.spec_from_file_location('tvw','tests/test_video_workbench.py'); mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); mod.test_export_video_workbench_writes_static_workspace(); mod.test_task_console_links_video_workbench(); print('video_workbench_queue_detail_tests_ok')"
$env:PYTHONPATH='src'; python -m video_knowledge_pipeline.cli export-video-workbench outputs\test-video-workbench\bundle
rg -n -e "selectQueue" -e "QUEUE_GROUPS" -e "data-queue-key" -e "queue-detail-retry" -e "队列：" outputs\test-video-workbench\bundle\video-workbench.html outputs\test-video-workbench\bundle\video-workbench.json
git diff --check -- src\video_knowledge_pipeline\video_workbench.py tests\test_video_workbench.py
`

结果：

- Direct test runner: ideo_workbench_queue_detail_tests_ok。
- CLI smoke 成功生成 ideo-workbench.html/json。
- 产物中能看到 selectQueue、QUEUE_GROUPS、data-queue-key、queue-detail-retry、队列：。
- git diff --check 对本次代码/测试文件无报错。

边界：工作台仍然只是静态本地 UI；它展示和复制命令，不自动执行 ebook、tile、多模态、ASR 或 smart-summary 任务。
## Update - 2026-07-05 21:30:24 | Codex / GPT-5

### P0 continued: explicit queue routing for reused external modules

本轮继续把 vsummary-style run registry 和 BiliNote-style task panel 做实：	ask_console._run_queue_group 不再只靠几组隐式关键词，而是新增 QUEUE_GROUP_TOKENS 路由表，把已经复用和计划继续复用的外部模块稳定归到正确队列。

落地变化：

- src/video_knowledge_pipeline/task_console.py
  - 新增 QUEUE_GROUP_TOKENS；
  - 覆盖 ASR / transcript、document OCR / ebook / tile、vision / multimodal / local VLM、timeline / VideoRAG / memory、summary / content asset、review / sample review；
  - multimodal_sample_review / impact_report / human_review 优先归入
eview，避免被普通 multimodal token 误归入视觉执行队列。
- 	ests/test_task_console.py
  - 新增 	est_processing_queue_groups_external_reuse_run_types；
  - 覆盖实际 run_type：isual_structure_ebook、high_res_tile_plan、	ile_result_merge、ision_review_queue、multimodal_frame_analysis、	emporal_visual_analysis、local_vlm_serving_smoke、ideo_moment_index、ideo_rag_search、long_video_memory_pack、smart_summary_section_workflow、smart_summary_codex、xternal_capability_pack、
eview_closure_status、multimodal_sample_review 等。

验证：

`powershell
python -m py_compile src\video_knowledge_pipeline\task_console.py tests\test_task_console.py
$env:PYTHONPATH='src'; python -c "import importlib.util; spec=importlib.util.spec_from_file_location('ttc','tests/test_task_console.py'); mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); mod.test_processing_queue_groups_external_reuse_run_types(); print('queue_group_external_reuse_tests_ok')"
$env:PYTHONPATH='src'; python -c "import importlib.util, shutil; from pathlib import Path; spec=importlib.util.spec_from_file_location('ttc','tests/test_task_console.py'); mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); mod.test_processing_queue_groups_external_reuse_run_types(); d=Path('outputs/test-task-console-direct').resolve(); shutil.rmtree(d, ignore_errors=True); d.mkdir(parents=True, exist_ok=True); mod.test_export_task_console_writes_human_ui_and_agent_json(d); print('task_console_queue_group_tests_ok')"
$env:PYTHONPATH='src'; python -c "import importlib.util; spec=importlib.util.spec_from_file_location('tvw','tests/test_video_workbench.py'); mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); mod.test_export_video_workbench_writes_static_workspace(); mod.test_task_console_links_video_workbench(); print('video_workbench_after_queue_group_tests_ok')"
`

结果：

- queue_group_external_reuse_tests_ok
- 	ask_console_queue_group_tests_ok
- ideo_workbench_after_queue_group_tests_ok

边界：这一步只改本地 run 分组和 UI 队列可解释性，不执行任何 ebook/OCR、多模态、ASR、VLM 或云调用。
## Update - 2026-07-05 21:44:53 | Codex / GPT-5

### P0 continued: multimodal and temporal vision runs registered as artifacts

本轮继续落实 vsummary-style run/artifact registry：多模态单帧和连续片段视觉分析不再只是写 multimodal-frame-analysis-report.md / 	emporal-visual-analysis-report.md，也会登记到
uns/ 和
un-artifact-registry.json/md，让 	ask-console / ideo-workbench 的队列能看到真实执行状态。

落地变化：

- src/video_knowledge_pipeline/multimodal_frame_analyzer.py
  - 新增共享 _register_vision_analysis_run；
  -
un_multimodal_frame_analysis 完成报告、vision analysis audit 后登记
un_type=multimodal_frame_analysis；
  - registry 状态区分
ot_needed、
eeds_execution、
eeds_input、
eeds_retry、completed；
  - artifacts 包含 report、input template、vision-analysis-runs、run audit；
  - operator boundary 明确 preview-first、云调用需要 xecute 和 confirmation、API key 不落盘。
- src/video_knowledge_pipeline/temporal_visual_analyzer.py
  - 复用同一登记 helper；
  -
un_temporal_visual_analysis 登记
un_type=temporal_visual_analysis；
  - temporal batch 的失败项和重试命令进入统一 run registry。
- 	ests/test_vision_pipeline.py
  - 	est_router_and_multimodal_limit 断言 preview 写入 multimodal_frame_analysis run registry；
  - 	est_temporal_frame_groups_limit_and_temporal_visual_requires_group 断言 temporal preview 写入 	emporal_visual_analysis run registry 和 retry command。

验证：

`powershell
python -m py_compile src\video_knowledge_pipeline\multimodal_frame_analyzer.py src\video_knowledge_pipeline\temporal_visual_analyzer.py tests\test_vision_pipeline.py
$env:PYTHONPATH='src'; python -c "import importlib.util; from pathlib import Path; spec=importlib.util.spec_from_file_location('tvp','tests/test_vision_pipeline.py'); mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); mod.test_router_and_multimodal_limit(Path('tmp-codex-run-registry-check/case3').resolve()); mod.test_temporal_frame_groups_limit_and_temporal_visual_requires_group(Path('tmp-codex-run-registry-check/case4').resolve()); print('vision_run_registry_direct_tests_ok')"
`

结果：ision_run_registry_direct_tests_ok。

边界：这一步只登记本地任务状态和产物，不发起云视觉调用，不改变 preflight / confirmation / execute 边界。
## Update - 2026-07-05 21:53:57 | Codex / GPT-5

### P0 continued: screen text recovery registered as retryable run

本轮继续落实 vsummary-style run/artifact registry 到 ebook/OCR 弱项闭环：
un_screen_text_recovery 现在会登记为
un_type=screen_text_recovery，让工作台和 task console 能看到 crop/OCR 恢复任务的 preview、下一步、失败项和重试命令。

落地变化：

- src/video_knowledge_pipeline/screen_text_recovery.py
  - 新增
egister_bundle_run 接入；
  - preview 状态登记为
eeds_execution，提醒继续 --execute-crops / --execute-ocr；
  - crop-only 状态仍登记为
eeds_execution，避免误把“只生成 crop”当成文字已恢复；
  - OCR 空结果或低信息量结果进入
eeds_review / failed_items，不清除 screen-text blocker；
  - artifacts 包含 screen-text-recovery.md/json、MCP args、OCR backfill report、OCR import。
- 	ests/test_screen_text_recovery.py
  - 	est_screen_text_recovery_generates_crops_and_preserves_source_frame 断言 preview 和 crop-only run 都写入
un-artifact-registry.json /
uns/screen-text-recovery/run.json。

验证：

`powershell
python -m py_compile src\video_knowledge_pipeline\screen_text_recovery.py tests\test_screen_text_recovery.py
$env:PYTHONPATH='src'; python -c "import importlib.util; from pathlib import Path; spec=importlib.util.spec_from_file_location('tst','tests/test_screen_text_recovery.py'); mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); mod.test_screen_text_recovery_generates_crops_and_preserves_source_frame(Path('tmp-codex-screen-text-registry/case1').resolve()); print('screen_text_recovery_registry_direct_test_ok')"
`

结果：screen_text_recovery_registry_direct_test_ok。

边界：这一步只登记本地 crop/OCR 恢复状态，不执行云视觉、不改变 ebook_markdown_pipeline 作为图文截图主通道的边界。
## Update - 2026-07-05 22:00:13 | Codex / GPT-5

### P0 continued: local ASR run plans registered as artifacts

本轮继续落实 vsummary-style run/artifact registry 到本地 ASR 链路：
un_asr_plan 现在在目标目录是 VKP bundle 时，会登记为
un_type=asr_run_plan，让工作台和 task console 能看到 ASR preview、执行状态、失败原因和重试命令。

落地变化：

- src/video_knowledge_pipeline/asr_execution.py
  - _write_asr_log 统一调用 _register_run_if_bundle；
  - 仅当 project/manifest.json 存在时登记 run，避免污染普通 ASR smoke / 非 bundle workspace；
  - 状态口径：preview ->
eeds_execution，ok -> completed，model/cache/command 问题 ->
eeds_input，失败/超时/缺输出/normalize 失败 ->
eeds_retry；
  - artifacts 包含 ASR run report、ASR run log、raw output、normalized transcript json/srt；
  - operator boundary 明确 local-only、audio stays local、模型下载需要 env 开关。
- 	ests/test_asr_pipeline.py
  - 新增 	est_run_asr_plan_registers_bundle_preview_run，验证 bundle preview run 会写入
uns/asr-run-plan/run.json 和
un-artifact-registry.json。

验证：

`powershell
python -m py_compile src\video_knowledge_pipeline\asr_execution.py tests\test_asr_pipeline.py
$env:PYTHONPATH='src'; python -c "import importlib.util; from pathlib import Path; spec=importlib.util.spec_from_file_location('tasr','tests/test_asr_pipeline.py'); mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); mod.test_run_asr_plan_registers_bundle_preview_run(Path('tmp-codex-asr-registry/case1').resolve()); print('asr_run_registry_direct_test_ok')"
`

结果：sr_run_registry_direct_test_ok。

边界：这一步只登记本地 ASR plan/run 状态，不执行模型、不下载模型、不上传音频。
## Update - 2026-07-05 22:08:50 | Codex / GPT-5

### P0 continued: transcript arbitration visible in video workbench

本轮继续吸收 BiliNote transcript editor / vsummary timestamp seek 的交互思路，把 	ranscript_source_arbitration 从独立报告推进到主工作台可见层。ideo-workbench.html 现在能直接显示字幕/ASR 仲裁摘要、待复核冲突、原文/纠正文、候选来源，并能点击冲突行定位到对应 timeline/video 时间。

落地变化：

- src/video_knowledge_pipeline/video_workbench.py
  - 新增 	ranscript_arbitration payload，读取 	ranscript-source-arbitration.json/md；
  - timeline row 增加 	ranscript_arbitration compact info；
  - 有仲裁冲突的 timeline row 增加 	ranscript_source_conflict evidence flag；
  - 左栏新增“字幕仲裁”面板，展示待复核冲突数、已改写片段数、原文/纠正文、chosen source、confidence、alternatives；
  - 新增 selectArbitration(index, seconds)，点击仲裁卡可定位视频和 timeline，并自动筛选 	ranscript_source_conflict。
- 	ests/test_video_workbench.py
  - fixture 新增 	ranscript-source-arbitration.json/md；
  - 覆盖 workbench JSON 中的 	ranscript_arbitration、timeline evidence flag、HTML 中的“筛字幕冲突”和 selectArbitration。

验证：

`powershell
python -m py_compile src\video_knowledge_pipeline\video_workbench.py tests\test_video_workbench.py
$env:PYTHONPATH='src'; python -c "import importlib.util; spec=importlib.util.spec_from_file_location('tvw','tests/test_video_workbench.py'); mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); mod.test_export_video_workbench_writes_static_workspace(); print('video_workbench_transcript_arbitration_direct_test_ok')"
rg -n -e "字幕仲裁" -e "筛字幕冲突" -e "selectArbitration" -e "transcript_source_conflict" outputs\test-video-workbench\bundle\video-workbench.html outputs\test-video-workbench\bundle\video-workbench.json
`

结果：ideo_workbench_transcript_arbitration_direct_test_ok，生成的 HTML/JSON 均包含仲裁面板和冲突标记。

边界：这一步只增强静态本地工作台，不运行 ASR、不改 transcript、不调用云模型、不自动接受仲裁结果。
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

```powershell
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

```powershell
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

```powershell
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

```powershell
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

```powershell
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

```powershell
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

```powershell
python -m py_compile src\video_knowledge_pipeline\video_rag_pack.py src\video_knowledge_pipeline\video_rag_search.py tests\test_external_video_reuse_modules.py
```

直接测试通过：

```text
video_rag_multigranularity_direct_tests_ok
```

边界：这一步只增强本地 JSONL 检索包，不引入 graph/vector DB，不启动 HTTP 服务，不处理新视频，不调用在线模型。
## Update: 2026-07-06 12:34:00 | Codex / GPT-5

### P0 continued: export-knowledge-note registered as run artifact

继续吸收 vsummary 的 stage/run artifact 思路，本轮把最终导出动作也接入 VKP 统一任务历史。`export-knowledge-note` 不再只是写出 Markdown/JSON 文件；它会登记一条 `knowledge_note_export` run，供 task console、video workbench、MCP/agent 读取。

新增能力：

- `export-knowledge-note` 写入 `runs/knowledge-note-export/run.json/md`。
- run artifacts 包含：
  - `knowledge-note.md`
  - `full-transcript.md`
  - `smart-summary.md`
  - `smart-summary-codex-prompt.md`
  - `smart-summary-input-pack.md`
  - `long-video-memory-pack.md`
  - `extraction-audit.md`
  - `export-summary.json`
  - `content-material-card.json/md`
  - `content-candidate-pack.json/md`
- 状态语义：
  - `completed`：关键导出文件存在，content candidates 已有章节链接。
  - `needs_review`：导出成功，但 content candidates 尚未和 smart-summary chapters 建立互链。
  - `needs_input`：关键导出文件缺失，或没有生成内容素材候选。
- `failed_items` 会记录 `missing_export_artifact`、`content_candidate_missing`、`content_candidate_chapter_refs_missing`。
- `retry_command` 固定为 `export-knowledge-note <bundle>`。
- `next_actions` 会提示先跑 `build-smart-summary-chapters`，再重新导出以补章节互链。

代码落地：

- `src/video_knowledge_pipeline/knowledge_note_export.py`
- `tests/test_knowledge_note_export_run_registry.py`
- `tests/test_task_console.py`
- `README.md`
- `AGENT_DISCOVERY.md`

验证：

```powershell
python -m py_compile src\video_knowledge_pipeline\knowledge_note_export.py src\video_knowledge_pipeline\task_console.py tests\test_knowledge_note_export_run_registry.py tests\test_task_console.py
$env:PYTHONPATH='src'; python -c "import importlib.util, shutil; from pathlib import Path; spec=importlib.util.spec_from_file_location('t','tests/test_knowledge_note_export_run_registry.py'); mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); base=Path('outputs/test-knowledge-note-export-run-registry-direct').resolve(); shutil.rmtree(base, ignore_errors=True); base.mkdir(parents=True, exist_ok=True); mod.test_export_knowledge_note_registers_needs_review_without_chapter_links(base); mod.test_export_knowledge_note_registers_completed_with_chapter_links(base); print('knowledge_note_export_run_registry_direct_tests_ok')"
$env:PYTHONPATH='src'; python -c "import importlib.util; spec=importlib.util.spec_from_file_location('ttc','tests/test_task_console.py'); mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); mod.test_processing_queue_groups_external_reuse_run_types(); print('task_console_knowledge_export_group_direct_test_ok')"
```

边界：这一步不重新跑 ASR、ebook、OCR、多模态或下载；只把已有最终导出动作登记为可追踪、可重试、可进入 summary/export 队列的本地 run artifact。
## Update: 2026-07-06 12:58:00 | Codex / GPT-5

### P0 continued: transcript-correction-pack registered as run artifact

继续吸收 BiliNote 的转写纠错 prompt / 分块工作流和 vsummary 的 run artifact 思路，本轮把 `transcript-correction-pack` 接入 VKP 统一任务历史。

新增能力：

- `transcript-correction-pack` 写入 `runs/transcript-correction-pack/run.json/md`。
- run artifacts 包含：
  - `exports/transcript-correction-pack.json`
  - `exports/transcript-correction-pack.md`
  - `exports/transcript-correction-llm-messages.json`
  - `llm-corrected-transcript.json/srt/md`
- 状态语义：
  - `needs_execution`：默认 preview，只生成 correction pack/messages，等待人工导入 JSON 或显式执行 provider。
  - `needs_input`：没有 transcript，或 `execute=true` 但缺 provider config。
  - `needs_retry`：provider 调用失败。
  - `needs_review`：纠错 payload 被接受但没有实际改动，需人工判断。
  - `completed`：导入或执行后的 corrected transcript 已生成。
- `operator_boundary` 明确：默认本地 preview；`execute=true` 可能调用文本 LLM；不会覆盖 term-resolution 的 corrected transcript。

代码落地：

- `src/video_knowledge_pipeline/transcript_correction_pack.py`
- `tests/test_transcript_correction_pack.py`
- `README.md`
- `AGENT_DISCOVERY.md`

验证：

```powershell
python -m py_compile src\video_knowledge_pipeline\transcript_correction_pack.py tests\test_transcript_correction_pack.py
$env:PYTHONPATH='src'; python -c "import importlib.util, shutil; from pathlib import Path; spec=importlib.util.spec_from_file_location('tcp','tests/test_transcript_correction_pack.py'); mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); base=Path('outputs/test-transcript-correction-pack-run-registry-direct').resolve(); shutil.rmtree(base, ignore_errors=True); (base/'preview').mkdir(parents=True, exist_ok=True); (base/'imported').mkdir(parents=True, exist_ok=True); mod.test_transcript_correction_pack_preview_writes_messages_and_manifest(base/'preview'); mod.test_transcript_correction_pack_imports_json_without_overwriting_term_resolution(base/'imported'); print('transcript_correction_pack_run_registry_direct_tests_ok')"
```

边界：这一步不调用 LLM、不修正真实视频字幕、不改写最终 transcript；只把现有纠错包工作流登记为可追踪、可重试、可进入 ASR/转写队列的本地 run artifact。
## Update: 2026-07-06 13:20:00 | Codex / GPT-5

### P0 continued: BiliNote-style transcript editor registered as run artifacts

继续吸收 BiliNote 的“视频/转写同屏人工编辑”体验和 vsummary 的 run artifact 思路，本轮把 `prepare-transcript-edit-session` 与 `apply-transcript-edits` 接入 VKP 统一任务历史。

新增能力：

- `prepare-transcript-edit-session` 写入 `runs/prepare-transcript-edit-session/run.json/md`。
  - `needs_input`：静态编辑器已经生成，等待人工保存 `transcript-edits.json`。
  - `needs_execution`：preview/no-write 模式。
- `apply-transcript-edits` 写入 `runs/apply-transcript-edits/run.json/md`。
  - `completed`：人工 edits 已导入，并生成 `human-corrected-transcript.json/srt/md`。
  - `needs_review`：edits 导入了但没有任何片段变化，需要人工确认是否可接受。
  - `needs_input`：没有原始 transcript segment。
- run artifacts 包含：
  - `transcript-edit-session.json`
  - `transcript-editor.html`
  - `transcript-edits.template.json`
  - `mcp-prepare-transcript-edit-session.args.json`
  - `mcp-apply-transcript-edits.args.json`
  - `human-corrected-transcript.json/srt/md`
- 这两个 run 会进入 ASR/转写队列中的 transcript editor 子队列。

代码落地：

- `src/video_knowledge_pipeline/transcript_editor.py`
- `tests/test_transcript_editor.py`
- `tests/test_task_console.py`
- `README.md`
- `AGENT_DISCOVERY.md`

验证：

```powershell
python -m py_compile src\video_knowledge_pipeline\transcript_editor.py tests\test_transcript_editor.py tests\test_task_console.py
$env:PYTHONPATH='src'; python -c "import importlib.util, shutil; from pathlib import Path; spec=importlib.util.spec_from_file_location('te','tests/test_transcript_editor.py'); mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); base=Path('outputs/test-transcript-editor-run-registry-direct').resolve(); shutil.rmtree(base, ignore_errors=True); base.mkdir(parents=True, exist_ok=True); mod.test_prepare_transcript_edit_session_and_apply_human_edits(base); print('transcript_editor_run_registry_direct_test_ok')"
$env:PYTHONPATH='src'; python -c "import importlib.util; spec=importlib.util.spec_from_file_location('ttc','tests/test_task_console.py'); mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); mod.test_processing_queue_groups_external_reuse_run_types(); print('task_console_transcript_editor_group_direct_test_ok')"
```

边界：这一步不调用 LLM，不自动改 transcript；只有用户导入 reviewed edits JSON 后才生成 `human-corrected-transcript.*`。
