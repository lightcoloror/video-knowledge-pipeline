# MediaKit CLI 可复用模块与源码登记

## Update Record

- 2026-07-15 10:20:35 +08:00 | Codex / GPT-5 | 首次建立 VKP 专用的 MediaKit CLI 模块、源码和安全边界登记。
- 2026-07-15 17:00:46 +08:00 | Codex / GPT-5 | 完成 P0.5 内容寻址媒体 route、完整目的地集合锁定、consent v2 复用、原子预留和只读 Broker preflight；真实执行仍关闭。
- 2026-07-15 15:51:03 +08:00 | Codex / GPT-5 | 完成 P0 离线能力目录、`mediakit_async_v1`、有界 fake-loopback client、设置 UI/Broker 发现面与安全回归。

## 1. 文档目的

本文把 `volcengine/mediakit-cli` 中值得 VKP 复用的模块落实到具体源码文件、关键符号和计划落点，避免只保留“值得参考”的概念判断。

本文是源码复用决策和后续实现依据，不代表已经安装、部署或接入 MediaKit，也不代表已经允许向其云端上传视频、音频或图片。

## 2. 固定证据快照

| 项目 | 值 |
| --- | --- |
| 官方仓库 | [volcengine/mediakit-cli](https://github.com/volcengine/mediakit-cli) |
| 审阅版本 | [v0.2.0](https://github.com/volcengine/mediakit-cli/releases/tag/v0.2.0) |
| 固定 commit | [`e0538f5e08150ce21d0dd5be5caeb23f5298c952`](https://github.com/volcengine/mediakit-cli/commit/e0538f5e08150ce21d0dd5be5caeb23f5298c952) |
| 本地只读源码快照 | `%WORKSPACE_ROOT%\ai-video-tools-20260708\sources\mediakit-cli` |
| 既有完整审阅 | `%WORKSPACE_ROOT%\ai-video-tools-20260708\火山引擎AI-MediaKit-CLI与Skill源码审阅.md` |
| 许可证 | MIT；如后续复制实质代码，保留上游版权与许可声明 |
| 上游漂移核对 | 2026-07-15 查询到 `main=279e5bb97e97c6875ae2c6891c2c3fa9a43f39c0`；它是包含 release commit 的合并提交，Git tree 仍为 `e9b40b73ef691e7bbf5a38c9af4e06d699d62beb`，与 v0.2.0 相同 |

所有下方 GitHub 源码链接都固定到 release commit，避免未来 `main` 变化后证据失真。

## 3. VKP 定位结论

MediaKit 不进入 LiteLLM 模型 deployment，也暂不作为 VKP 核心依赖。它的合理位置是独立的候选远程媒体能力供应商：

```text
VKP 任务层
├─ 模型任务 → LiteLLM Proxy
│  ├─ text
│  ├─ frame / temporal vision
│  ├─ standard ASR
│  └─ image / document OCR
└─ 媒体服务任务 → Media Capability Adapter
   ├─ video_ocr
   ├─ video_asr
   ├─ scene_segmentation
   ├─ storyline
   └─ highlight_detection
```

MediaKit 的本地 FFmpeg 功能不重复并入 VKP。VKP 已有抽帧、探测、裁剪和音频处理管线；重复接入会增加运行时、错误模型和产物路径的不一致。

## 4. 可复用基础模块登记

复用级别定义：

- `选择性移植`：可以按 VKP 数据结构改写少量算法或结构，并保留上游归属。
- `契约借鉴`：只复用协议和状态机思想，不复制实现。
- `负面样本`：明确记录不能照搬的逻辑。

| ID | 上游模块和关键代码 | 可复用内容 | 复用级别 | VKP 计划落点 | 必须改造的边界 |
| --- | --- | --- | --- | --- | --- |
| MK-REG-01 | [`internal/commands/registry.go`](https://github.com/volcengine/mediakit-cli/blob/e0538f5e08150ce21d0dd5be5caeb23f5298c952/internal/commands/registry.go#L22-L55)：`DomainMeta`、`ParamMeta`、`CapabilityMeta`；同文件 [`buildCapabilitySchema`](https://github.com/volcengine/mediakit-cli/blob/e0538f5e08150ce21d0dd5be5caeb23f5298c952/internal/commands/registry.go#L3240-L3311)、`buildOutputSchema`、`buildAsyncCloudSchema` | 能力目录、参数元数据、同步/异步属性、输入/输出 Schema 自省 | 选择性移植 | 计划新增 `media_capability_registry.py`；供 CLI、MCP 和设置 UI 共用 | VKP Schema 必须额外公开 `location`、`route_id`、`route_revision`、是否需要 consent、artifact 类型和费用状态；Schema 不能根据运行时状态暗中改成另一个位置 |
| MK-API-01 | [`internal/cloud/api_info.go`](https://github.com/volcengine/mediakit-cli/blob/e0538f5e08150ce21d0dd5be5caeb23f5298c952/internal/cloud/api_info.go#L7-L48)：能力名到 method/path 的静态映射 | 将供应商 task name 与 HTTP method/path 分离 | 选择性移植 | 计划新增 `mediakit_adapter.py` 内的固定 capability map | 不接受 Agent 提交任意 URL；endpoint、协议和 destination 必须来自已验证 route snapshot |
| MK-ASYNC-01 | [`internal/cloud/executor.go`](https://github.com/volcengine/mediakit-cli/blob/e0538f5e08150ce21d0dd5be5caeb23f5298c952/internal/cloud/executor.go#L18-L310)：`Execute`、`splitQueryTaskOptions`、`maybePollQueryTask`、`isTerminalTaskStatus`；[`query_task.md`](https://github.com/volcengine/mediakit-cli/blob/e0538f5e08150ce21d0dd5be5caeb23f5298c952/skills/byted-mediakit-shared/reference/query_task.md) | `submit → task_id/request_id → poll → terminal result` 异步任务协议；兼容 `canceled/cancelled` | 选择性移植 | 计划新增 `media_task_protocol.py` 和 `media_task_store.py` | 禁止无限轮询；必须有总超时、最大次数、退避、可取消状态和持久审计；VKP 统一终态使用 `succeeded/failed/cancelled/timeout`，保留原始供应商状态为 evidence |
| MK-RESP-01 | [`internal/cloud/response.go`](https://github.com/volcengine/mediakit-cli/blob/e0538f5e08150ce21d0dd5be5caeb23f5298c952/internal/cloud/response.go#L11-L175) 与 [`executor.go`](https://github.com/volcengine/mediakit-cli/blob/e0538f5e08150ce21d0dd5be5caeb23f5298c952/internal/cloud/executor.go#L172-L310) 的同步、异步、任务查询和业务失败归一化 | 区分 HTTP 错误、业务 `success=false` 和异步失败终态 | 选择性移植 | `media_task_protocol.py` 的 normalized result/error | 不把供应商返回整体写入 Timeline；先脱敏并规范化，原始响应只能进入受控审计证据，不能记录 API Key、上传签名或临时 URL 查询参数 |
| MK-UPLOAD-01 | [`internal/cloud/media_inputs.go`](https://github.com/volcengine/mediakit-cli/blob/e0538f5e08150ce21d0dd5be5caeb23f5298c952/internal/cloud/media_inputs.go#L15-L197)：媒体字段识别、本地路径判断、materialize；[`media_upload.go`](https://github.com/volcengine/mediakit-cli/blob/e0538f5e08150ce21d0dd5be5caeb23f5298c952/internal/cloud/media_upload.go#L11-L109)：申请上传地址和流式上传 | 把“本地 artifact”与“供应商可消费引用”分成两个阶段；上传前先解析精确文件 | 契约借鉴 | `mediakit_adapter.py` 的独立 preflight/submit 阶段 | 当前不移植自动上传代码。必须先检查 allowed root、artifact SHA-256、route revision、consent v2、文件大小和真实上传域名；上传地址返回后还要再次验证 scheme/host，不能只信 API 主域名 |
| MK-CACHE-01 | [`internal/cloud/upload_cache.go`](https://github.com/volcengine/mediakit-cli/blob/e0538f5e08150ce21d0dd5be5caeb23f5298c952/internal/cloud/upload_cache.go#L20-L215)：文件身份、TTL、锁和原子缓存写入 | 避免同一媒体在幂等重试时重复上传；锁保护并发 | 契约借鉴 | 未来 `media_upload_receipts` 审计存储 | 上游以绝对路径、size、mtime 匹配，不足以满足 VKP consent；VKP 必须以 artifact SHA-256、destination、route revision、consent id 和过期时间共同命中，且不得把带签名上传 URL 持久化 |
| MK-OUT-01 | [`internal/output/writer.go`](https://github.com/volcengine/mediakit-cli/blob/e0538f5e08150ce21d0dd5be5caeb23f5298c952/internal/output/writer.go#L11-L134)：`ResolvePath`、`WriteFileAtomic`、symlink-aware path resolution | 受控根目录、拒绝越界、临时文件后 rename 的原子产物写入 | 契约借鉴 | 复核并复用 VKP 现有安全路径/原子 JSON writer；不新建平行工具 | VKP 根目录由 Broker/runtime policy 决定，而不是当前工作目录；Windows junction/reparse point 也必须纳入真实路径校验 |
| MK-SEC-01 | [`internal/local/admission/policy.go`](https://github.com/volcengine/mediakit-cli/blob/e0538f5e08150ce21d0dd5be5caeb23f5298c952/internal/local/admission/policy.go#L5-L135) 与 [`internal/local/core/security.go`](https://github.com/volcengine/mediakit-cli/blob/e0538f5e08150ce21d0dd5be5caeb23f5298c952/internal/local/core/security.go#L16-L208) | 能力依赖白名单、参数校验、结果脱敏、输出路径约束 | 契约借鉴 | Broker 的 allowed roots/capabilities/loopback 验证和本地执行审计 | 不复制 FFmpeg 参数白名单本身；只吸收“能力声明与执行前验证分离”的模式 |
| MK-MODE-01 | [`internal/modes/resolver.go`](https://github.com/volcengine/mediakit-cli/blob/e0538f5e08150ce21d0dd5be5caeb23f5298c952/internal/modes/resolver.go#L15-L279)：`CapabilityRuntimeMeta`、`Decision`、`resolveDecision` | 能力可发现的 local/cloud 标签值得借鉴 | 负面样本 | 路由配置 v2 的 `location`、`route_pools`、`task_routes` | 不复用 `local-first/cloud-first` 自动跨位置降级。VKP 本地池与远程池永不互相自动 fallback；位置切换必须由用户显式选择并重新匹配 consent |

## 5. 可复用高层媒体能力登记

这些能力是媒体服务任务，不是 OpenAI-compatible 模型端点。它们不能伪装成 `/v1/chat/completions`、`/v1/audio/transcriptions` 或 `/v1/ocr` deployment。

| VKP 任务 | MediaKit 能力及源码 | 价值 | 优先级 | VKP 规范化产物 | 决策 |
| --- | --- | --- | --- | --- | --- |
| `scene_segmentation` | [`segment-scenes` registry](https://github.com/volcengine/mediakit-cli/blob/e0538f5e08150ce21d0dd5be5caeb23f5298c952/internal/commands/registry.go#L1464-L1538)、[能力说明](https://github.com/volcengine/mediakit-cli/blob/e0538f5e08150ce21d0dd5be5caeb23f5298c952/skills/byted-mediakit-video/reference/segment-scenes.md) | 在 VLM 前筛选镜头/片段，降低帧数、调用量和费用；教育类视频也可直接使用 | P0，首选 PoC | `segments[]`：start/end、score、source task、artifact hash、candidate evidence | 候选接入；必须显式远程 route 和单独 consent |
| `storyline` | [`analyze-video-storyline` registry](https://github.com/volcengine/mediakit-cli/blob/e0538f5e08150ce21d0dd5be5caeb23f5298c952/internal/commands/registry.go#L1540-L1588)、[能力说明](https://github.com/volcengine/mediakit-cli/blob/e0538f5e08150ce21d0dd5be5caeb23f5298c952/skills/byted-mediakit-video/reference/analyze-video-storyline.md) | whole-video 结构化理解，可补 VKP 当前 deferred 的全片剧情/结构分析 | P1，第二 PoC | 按时间排序的 clips/highlights，转换为候选 Timeline rows 和 Bundle evidence | 只作候选证据，不直接覆盖既有 Timeline 或 Smart Summary |
| `highlight_detection` | [`analyze-video-highlights` registry](https://github.com/volcengine/mediakit-cli/blob/e0538f5e08150ce21d0dd5be5caeb23f5298c952/internal/commands/registry.go#L1590-L1663)、[能力说明](https://github.com/volcengine/mediakit-cli/blob/e0538f5e08150ce21d0dd5be5caeb23f5298c952/skills/byted-mediakit-video/reference/analyze-video-highlights.md) | 返回时间戳、评分、OCR 和画面描述，可辅助内容候选和抽样视觉分析 | P2 | `highlights[]`：start/end、score、text、visual description、evidence | 上游模型偏短剧/小游戏；教育视频泛化需先评测，不能作为首个验收能力 |
| `video_ocr` | [`video-ocr` registry](https://github.com/volcengine/mediakit-cli/blob/e0538f5e08150ce21d0dd5be5caeb23f5298c952/internal/commands/registry.go#L1040-L1088)、[能力说明](https://github.com/volcengine/mediakit-cli/blob/e0538f5e08150ce21d0dd5be5caeb23f5298c952/skills/byted-mediakit-video/reference/video-ocr.md) | 整段视频到带时间戳文本，补充图片/文档 OCR 不覆盖的连续字幕检测 | P2 | `visual_text_segments[]`：start/end/text/mode/source artifact hash | 必须保留独立任务类型；不得静默转成现有图片/文档 `/v1/ocr`，本地 ebook Markdown OCR 路线保持原样 |
| `video_asr` | [`asr-subtitles` registry](https://github.com/volcengine/mediakit-cli/blob/e0538f5e08150ce21d0dd5be5caeb23f5298c952/internal/commands/registry.go#L1090-L1182)、[能力说明](https://github.com/volcengine/mediakit-cli/blob/e0538f5e08150ce21d0dd5be5caeb23f5298c952/skills/byted-mediakit-video/reference/asr-subtitles.md) | 带时间戳、可选说话人和置信度的远程媒体 ASR | P2 | 独立 ASR sidecar，保留 provider、language、speaker/confidence 和 source hash | 标准在线 ASR 仍优先走 `/v1/audio/transcriptions`；MediaKit 只作为显式媒体服务路线，绝不直接覆盖原始 ASR |

## 6. `mediakit_async_v1` 建议契约

### 提交请求

```json
{
  "schema_version": "mediakit_async_v1",
  "task": "scene_segmentation",
  "execution_location": "remote",
  "route_id": "media-remote-approved",
  "route_revision": "sha256:...",
  "deployment": "volcengine-mediakit",
  "artifact_paths": ["%WORKSPACE_ROOT%\\...\\video.mp4"],
  "artifact_hashes": ["sha256:..."],
  "consent_id": "...",
  "parameters": {}
}
```

Broker 只接收受控 task 和 artifact；供应商 endpoint、API Key、上传 URL 均不能由 Agent 参数提供。

### 统一状态结果

```json
{
  "ok": true,
  "task": "scene_segmentation",
  "status": "succeeded",
  "provider_status": "completed",
  "task_id": "...",
  "request_id": "...",
  "route_id": "media-remote-approved",
  "route_revision": "sha256:...",
  "deployment": "volcengine-mediakit",
  "latency_ms": 0,
  "usage": null,
  "estimated_cost": null,
  "content": {},
  "evidence": [],
  "consent_id": "..."
}
```

VKP 统一状态：`submitted`、`running`、`succeeded`、`failed`、`cancelled`、`timeout`。供应商原始状态只保留在 `provider_status`。

## 7. 明确不复用的代码与行为

| 上游行为 | 不复用原因 | VKP 规则 |
| --- | --- | --- |
| `local-first` 本地不可用后自动降级云端；`cloud-first` 无凭据后自动降级本地 | 跨位置执行会改变数据外发边界和 consent 范围 | 本地池和远程池永不自动互相 fallback |
| `MEDIAKIT_API_KEY` 可来自明文配置、shell export 或命令初始化流程 | 不符合 VKP `secret_ref + DPAPI + 子进程环境注入` 决策 | 密钥不进 YAML、JSON、日志、MCP 参数、聊天或 Bundle |
| 发现本地媒体路径后自动申请上传地址并上传 | 在目的地集合、artifact hash、调用次数和 consent 未验证前发生外发 | `preflight → consent reservation → upload target host validation → submit` 必须分步审计 |
| 把 API 主域名视为唯一目的地 | 预签名上传 URL 可能指向其他域名 | 接入前实测并登记控制面和上传面的全部实际 host；任一新增 host 都使 route revision 和 consent 失效 |
| 本地 FFmpeg handler、依赖探测和自动安装建议 | VKP 已有稳定 FFmpeg 管线；重复实现会产生双轨 | 继续使用 VKP 当前视频处理入口，不 vendoring MediaKit 本地处理器 |
| 把 `video-ocr` 当作图片/文档 OCR | artifact、调用计数和结果语义不同 | 保持 `video_ocr` 独立任务和逐视频调用计数 |
| 无上限 `poll_complete` 循环 | Agent 任务可能长期占用且不可恢复 | 必须有 timeout、max attempts、持久状态与恢复命令 |

## 8. 分阶段实现登记

### P0：只实现离线契约，不接真实供应商

1. [x] 新增 `media_capability_registry.py`，登记 5 个能力、Schema、位置和异步属性。
2. [x] 新增 `media_task_protocol.py`，实现精确本地 artifact/hash 校验、参数白名单、状态归一化、终态、错误和候选证据结构。
3. [x] 新增 `media_async_client.py`，用 fake loopback server 覆盖 submit、poll、completed、failed、cancelled、timeout、429/5xx 和部分结果。
4. [x] 证明 `local_only`、非 loopback endpoint 和篡改后的 provider path 都在 socket 前阻断，且不发生远程 fallback。
5. [x] 设置 UI、只读 CLI 和 Trusted Broker 能力发现只显示候选能力及“未获 allowlist/consent”；没有创建真实 execute 工具。

P0 已实现路径：

- `src/video_knowledge_pipeline/artifact_validation.py`：复用给模型 runtime 与媒体协议的本地路径、allowed roots 和 SHA-256 证据校验。
- `src/video_knowledge_pipeline/media_capability_registry.py`：固定 5 项 MediaKit 能力、submit/poll path、参数 Schema 和未授权状态。
- `src/video_knowledge_pipeline/media_task_protocol.py`：`mediakit_async_v1` plan/result、供应商状态归一化、临时 URL/secret 脱敏和 candidate-only evidence。
- `src/video_knowledge_pipeline/media_async_client.py`：仅允许带端口的 HTTP loopback 测试传输；拒绝任意远程 endpoint，限制 polling 次数、间隔和总超时。
- `tests/test_media_capability_adapter.py`：覆盖固定 registry、artifact/hash、参数拒绝、成功/失败/取消/超时、429/5xx、部分结果、零 socket 阻断和 whole-video deferred 回归。

只读发现命令：

```powershell
.\scripts\video-knowledge.ps1 media-capability-status
```

该命令不读取媒体文件、不联网、不生成 consent，也不改变配置。`model_connector_capabilities` 使用同一份 registry 返回候选目录，但没有 MediaKit execute MCP 工具。

### P0.5：媒体 route、consent v2 与只读执行前门

已完成：

1. `media_route_settings.py` 生成按任务内容寻址的 route revision；控制面固定为 `amk.cn-beijing.volces.com`，上传目的地必须是操作者登记的 HTTPS origin。
2. 通用 `model_connector_consent.v2` 现在兼容独立媒体任务，并继续复用精确 artifact SHA-256、逐文件 upload manifest、有效期、调用/费用上限和原子 reservation。
3. route snapshot 和 consent 同时锁定 `authorized_deployments` 与 `authorized_destinations`；控制面或任一上传 origin 变化都会在联网前失配。
4. Trusted Broker 新增只读 `media_connector_preflight_tool`；它只核验本地 route、consent、allowlist 和凭据是否就绪，不上传、不 reservation、不执行。
5. 现有 `execute_consented_model_task_tool` 明确拒绝媒体 consent，避免把媒体协议误送到 LiteLLM/model adapter。
6. 真实 MediaKit execute CLI/MCP 仍不存在；`native_video_segment` 仍保持 deferred。

只读入口：

```powershell
.\scripts\video-knowledge.ps1 media-route-status --task scene_segmentation
.\scripts\video-knowledge.ps1 media-connector-preflight <consent.json> --route-revision <exact-revision>
```

操作者配置与创建授权使用独立前门，默认 preview/configure 不写，只有显式 `--write` 才保存 route settings：

```powershell
.\scripts\media-connector-consent.ps1 configure `
  --upload-destination https://<audited-upload-origin> `
  --write

.\scripts\media-connector-consent.ps1 create <root-dir> `
  --task scene_segmentation `
  --artifact <exact-video-path> `
  --max-estimated-cost-usd <limit> `
  --confirm-data-export
```

以上命令不会执行 MediaKit；创建 consent 前仍要求 Broker allowlist 同时包含控制面和全部上传 origin。示例中的上传 origin 不能照抄，必须来自真实上传流程的独立审查证据。

### P1：单能力、操作者授权 PoC

首选 `segment-scenes`；若固定教育视频样本的切分价值不足，再选 `analyze-video-storyline`。

PoC 前置条件全部满足才可执行：

- Broker allowlist 明确包含 `amk.cn-beijing.volces.com` 及实测上传 host；
- consent v2 锁定 route id/revision、deployment、artifact SHA-256、调用次数和有效期；
- 用户确认 API 计费边界和固定样本；
- 由操作者明确授权真实 smoke；
- 结果只写 candidate evidence，不自动覆盖 Timeline/Bundle/Smart Summary。

### 停止条件

出现以下任一情况，停止继续集成：

- 上传域名无法提前审查或运行时会任意变化；
- API 无法返回可持久追踪的 task id/request id；
- 教育视频样本的场景/故事线质量不高于 VKP 现有本地切分与 temporal 证据；
- 费用或延迟无法记录；
- 必须绕过 Broker、consent 或 Agent 平台策略才能工作。

## 9. 验收口径

- 能力注册与 Agent/MCP Schema 可由同一份 registry 生成。
- 远程请求不能接受任意 URL、任意 provider config 或 API Key。
- route revision 或任一目的地改变时，联网前阻断。
- 本地 artifact 必须在 allowed root 内并匹配 consent 的 SHA-256。
- 每次 submit 和 poll 都有审计；每个视频/音频任务独立计数。
- 供应商结果只能先进入 candidate evidence；Timeline 和 Smart Summary 写回仍走现有验证入口。
- 自动测试不调用真实外部 API。
- 真实 smoke 仍需操作者单独明确授权。

## 10. 当前状态

- 登记完成：9 个基础模块/模式，5 个高层媒体能力。
- P0/P0.5 实现完成：能力 registry、异步协议、有界 fake-loopback client、内容寻址媒体 route、consent v2/目的地锁、CLI/UI/Broker 只读发现与 preflight，以及 21 项媒体专门测试。
- 在线调用：0；没有上传视频、音频、图片或文档。
- 配置变化：0；没有修改 Broker allowlist、consent、LiteLLM、MCP、Docker、代理或计划任务。
- 生产状态：`native_video_segment` 仍为 `deferred_use_frame_groups`；P0 client 不接受非 loopback endpoint，也没有真实 provider artifact materializer。
- 下一步：实现 Broker 内部的上传地址申请/host 二次校验/流式上传/submit/poll 审计，但继续不暴露 execute 工具；只有真实上传 host 审计完成且操作者单独授权后，才评估 `segment-scenes` 单样本 smoke。

## 2026-07-23 Execution Correction

- 2026-07-23 20:53:37 +08:00 | Codex (GPT-5)
- This historical registry is superseded for production execution. VKP now invokes the installed official MediaKit CLI only after consent v2 has bound exact local artifact hashes, fixed MediaKit control-plane destination, route revision, call/cost ceiling and expiry. The CLI owns provider-managed local upload and task polling; arbitrary upload URLs remain disallowed. Missing CLI is an honest runtime dependency error (mediakit_cli_unavailable), not a policy block. MediaKit output remains evidence subject to existing downstream validation; it does not silently overwrite source facts.