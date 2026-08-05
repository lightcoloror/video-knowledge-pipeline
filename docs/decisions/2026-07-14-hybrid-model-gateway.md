# ADR：复用成熟 AI Gateway 统一在线与本地模型

- 状态：Accepted
- 决策时间：2026-07-14 23:33:59 +08:00
- 执行者：Codex / GPT-5
- 适用范围：VKP 的文本模型、视觉模型、ASR、在线 OCR 及其本地兼容运行时
- 不包含：本记录不修改运行配置，不启动模型服务，不执行真实模型调用，也不改变现有 consent

## 背景

VKP 需要同时支持在线模型 API、本地模型服务和按任务选择最适合的模型，同时保证在线调用继续受目的地白名单、精确 artifact hash、任务与 provider 锁定、调用次数和有效期控制。在线、本地与混合部署还必须共享同一套业务管线和产物协议，而不依赖当前 Agent 是否具备视觉或音频能力。

VKP 已有 `model_task_gateway`、LiteLLM/OpenAI-compatible 适配、Trusted Broker、OCR 路由、ASR 路由和本地 API 设置。继续自研通用 provider router、健康检查、重试、fallback、成本统计和多供应商协议转换，会重复成熟开源网关已经解决的问题。

## 决策

采用以下分层，而不是维护两套产品或继续扩展自研通用模型网关：

```text
Codex / Web UI / CLI
        |
Secure MCP Tunnel（Agent 接入时）
        |
VKP Trusted Capability Broker
  - 授权、consent、artifact hash、目的地白名单
        |
VKP Model Task Gateway
  - 任务语义、输入准备、结果规范、产物写回
        |
LiteLLM Proxy
  - Provider 协议、路由、重试、限流、健康检查、费用
        |
        +-- 在线 Provider
        +-- 本地 OpenAI-compatible Provider
```

### 1. LiteLLM Proxy 是默认模型流量网关

LiteLLM 负责：

- 多 Provider 协议转换和统一 OpenAI-compatible 接口；
- 文本、视觉、音频转录和其正式 `/v1/ocr` 端点支持范围；
- 同一授权范围内的重试、fallback、负载均衡、timeout 和 cooldown；
- Provider 健康检查、成本、预算、限流和调用观测；
- 本地及在线 OpenAI-compatible 服务的统一接入。

VKP 不再新建另一套通用 provider adapter framework。现有 `online_model_gateway` 在迁移后收缩为 LiteLLM/OpenAI 客户端和兼容层；迁移期间保留内嵌 LiteLLM SDK 与当前 built-in adapter 作为兼容路径。

### 2. 本地模型通过成熟的 OpenAI-compatible Runtime 接入

支持但不强制绑定单一运行时：

| 本地能力 | 推荐运行时 | 定位 |
|---|---|---|
| 多能力一体化 | LocalAI | 文本、视觉、ASR、TTS、图像等按需后端 |
| GPU 高吞吐文本/VLM/ASR | vLLM | OpenAI-compatible 服务和可扩展推理 |
| 桌面轻量文本/VLM | Ollama | 简单本地安装和部分 OpenAI-compatible API |
| 专项本地 ASR | Speaches | OpenAI-compatible 转录、翻译和流式语音 |
| 本地 OCR | 现有 ebook Markdown pipeline | 保持 VKP 当前默认 OCR 路径 |

本地服务只需暴露明确的 loopback Base URL、模型名和能力声明。VKP 不管理模型权重、GPU 调度或推理引擎内部实现。

### 3. VKP 保留领域编排，不把业务语义交给网关

以下职责继续属于 VKP：

- 视频拆帧、抽取音频、Timeline 和 WebUI bundle；
- ASR、OCR、单帧语义、多帧时序、摘要和转录纠错等任务定义；
- Prompt、精确输入文件选择和 artifact hash；
- 统一结果 Schema、证据状态、来源追踪和产物写回；
- OCR 产物到实体词库、ASR 热词和上下文提示的只读消费；
- Smart Summary、知识整理、质量门和人工审核。

LiteLLM 只决定“怎样调用已获准的模型”，不能决定“哪些本地文件可以发送”或“模型输出是否可提升为事实”。

### 4. OCR 与 ASR 采用标准端点

- 在线 OCR 优先对接 LiteLLM `/v1/ocr`，并规范化为 VKP 的 `visual_text`、`structured_visual` 和 evidence 产物。
- 本地 OCR 继续使用 ebook Markdown pipeline，不为了统一 HTTP 外观而改写成熟本地流程。
- 在线 ASR 采用 `/v1/audio/transcriptions`。
- 本地 Speaches、vLLM ASR 或其他 OpenAI-compatible ASR 使用同一转录客户端契约。
- 原始 ASR 文本保持不可变；OCR 热词和模型纠错仍是候选证据。

### 5. 本地池与远程池严格分离

禁止建立会在本地失败后隐式上传数据的混合 fallback 池：

```text
local-only pool
remote-approved pool
```

规则如下：

- loopback 本地调用不构成数据外发，不需要远程数据导出 consent；
- 远程池必须在调用前经过 VKP Trusted Broker；
- consent 必须锁定任务、模型、协议、Base URL、artifact hash、调用次数和有效期；
- LiteLLM 只能在 consent 明确覆盖的远程 Provider/目的地集合内 fallback；
- 新 fallback 目的地不在原 consent 内时必须重新授权；
- Secure MCP Tunnel 只使 Agent 能访问受信任 Broker，不代表任意外部域名自动获准；
- VKP consent 不能覆盖或绕过 Agent 平台自己的外发策略。

2026-07-15 的外发策略补充将“远程池必须授权”进一步固定为默认拒绝：只有显式 route、consent v2、绑定精确上传清单的操作者确认、调用与费用上限、以及 Broker allowlist 全部通过时才允许在线调用。自动发布、未列明文件上传和静默 local/cloud fallback 永久禁止。详见 [在线模型外发策略补充](./2026-07-15-explicit-online-model-egress-policy.md)。

### 6. 一个代码库，多种安装配置

不创建长期分叉的“在线源码版”和“本地源码版”。提供同一代码库的依赖/运行配置：

- `core`：任务协议、产物、路由配置、UI、FFmpeg 编排；
- `online`：core + LiteLLM Proxy/在线 Provider 支持，不包含本地模型权重；
- `local`：core + 用户选定的本地 Runtime/模型；
- `hybrid`：online + local，通过每任务路由选择。

安装配置控制依赖与服务，不改变 Timeline、Bundle 和最终知识产物格式。

## 与当前代码的映射

| 当前组件 | 决策后的职责 |
|---|---|
| `model_task_gateway.py` | 保留为权威任务入口 |
| `online_model_gateway.py` | 收缩为 LiteLLM/OpenAI 客户端和迁移兼容层；后续可更名为 `model_runtime_client.py` |
| `trusted_model_connector.py` | 保留为 Agent/远程执行的 consent gate |
| `trusted_model_connector_policy.py` | 保留本地 loopback 与远程 allowlist 边界 |
| `model_api_settings.py` | 保存 Provider profile 和每任务路由；可生成 LiteLLM 配置视图 |
| `ocr_route.py` | 保留本地 ebook 路径；在线路径改接标准 OCR 端点并继续规范化产物 |
| `adaptive_asr_route.py` | 保留热词、上下文和质量路由；实际 Provider 调用交给统一转录端点 |

## 未选择的方案

### 自研完整模型网关

不采用。协议适配、fallback、健康检查、成本和限流均已有成熟实现；自研会扩大维护面和安全审计面。

### Portkey AI Gateway

作为成熟备选保留。其条件路由、fallback、负载均衡、缓存和 Guardrail 能力完整，但当前引入会与已经使用的 LiteLLM 重复。只有当 LiteLLM 无法满足明确需求时再做替换评估，不同时运行两套通用 AI Gateway。

### Kong AI Gateway / Envoy AI Gateway

当前不采用。它们更适合组织级 API 基础设施、Kubernetes 或平台团队；对当前单机/个人 VKP 的部署和运维成本过高。

### 单一 Local Runtime 强绑定

不采用。LocalAI、vLLM、Ollama 和 Speaches 面向不同设备与任务。VKP 绑定 OpenAI-compatible 契约，而不是绑定某个本地推理引擎。

## 后果

正向：

- 在线、本地和混合部署共享同一业务代码和产物；
- 大幅减少 Provider 适配、fallback、健康检查和观测代码；
- 新供应商通常只需添加 LiteLLM model 配置或 OpenAI-compatible profile；
- Agent 模型本身不需要具备视觉/ASR 能力；
- 可独立升级本地推理端、模型网关和 VKP 领域管线。

代价与风险：

- LiteLLM Proxy 成为需要管理的额外本地服务；
- LiteLLM 升级必须通过 VKP 的文本、视觉、ASR、OCR 契约测试；
- LiteLLM `/ocr` 的 Provider 支持范围有限，未覆盖的供应商仍需薄适配器；
- 自动 fallback 必须与 VKP consent 范围联动，不能直接采用宽松默认配置；
- 本地 Runtime 的模型下载、显存和许可证仍由操作者管理。

## 实施顺序

1. 在不改变当前行为的情况下定义 LiteLLM virtual model 命名和本地/远程池规则。
2. 先迁移文本和视觉任务，保留 built-in adapter 回退开关。
3. 将在线 ASR 迁移到统一 `/v1/audio/transcriptions`。
4. 将在线 OCR 迁移到 `/v1/ocr`；本地 ebook 路径不动。
5. 接入一个本地通用 Runtime 和 Speaches 健康检查，验证同一任务契约。
6. 在 UI 中展示任务路由、执行位置、健康状态、预计成本和是否需要 consent。
7. 增加 `core/online/local/hybrid` 安装测试矩阵和 A/B 质量基准。
8. 全部契约测试通过后，再删除重复的 provider 路由实现。

## 验收条件

- 同一个 VKP 任务可在本地和在线 Provider 间切换，业务调用方无需修改；
- 本地与在线结果写入相同版本的 VKP 结果 Schema；
- `local-only` 配置在任何失败情况下都不会访问远程目的地；
- 远程 fallback 的每个目的地均包含在执行时 consent 和 Broker allowlist 中；
- API Key、Bearer Token 和 DPAPI 密文不会进入 Bundle、日志、文档或 MCP 参数；
- Agent 平台拒绝外发时，VKP 不尝试代理绕过；
- 文本、视觉、ASR、OCR 四类契约测试及完整回归测试通过。

## 依据与相关文档

外部官方资料：

- [LiteLLM Getting Started](https://docs.litellm.ai/)
- [LiteLLM Router](https://docs.litellm.ai/docs/routing)
- [LiteLLM Health Check Driven Routing](https://docs.litellm.ai/docs/proxy/health_check_routing)
- [LiteLLM Audio Transcription](https://docs.litellm.ai/docs/audio_transcription)
- [LiteLLM OCR](https://docs.litellm.ai/docs/ocr)
- [LocalAI Overview](https://localai.io/docs/overview/index.html)
- [vLLM OpenAI-Compatible Server](https://docs.vllm.ai/en/latest/serving/online_serving/openai_compatible_server/)
- [Ollama OpenAI Compatibility](https://docs.ollama.com/api/openai-compatibility)
- [Speaches](https://github.com/speaches-ai/speaches)
- [Portkey AI Gateway](https://portkey.ai/docs/product/ai-gateway)
- [Kong AI Gateway](https://developer.konghq.com/ai-gateway/)
- [Envoy AI Gateway Supported Endpoints](https://aigateway.envoyproxy.io/docs/capabilities/llm-integrations/supported-endpoints/)

项目内相关文档：

- `docs/model-task-gateway.md`
- `docs/trusted-online-model-connector.md`
- `docs/model-api-settings-ui.md`
- `docs/ocr-provider-routing-2026-07-14.md`
- `docs/architecture.md`

## Update Record

### 2026-07-14 23:33:59 | Codex / GPT-5

- Action：记录在线/本地混合模型架构决策。
- Files：`docs/decisions/2026-07-14-hybrid-model-gateway.md`；`docs/architecture.md`。
- Summary：决定采用 LiteLLM Proxy 作为模型流量网关，以 LocalAI/vLLM/Ollama/Speaches 作为可选本地运行时；VKP 保留任务、产物和安全授权职责，并强制分离本地与远程 fallback 池。

### 2026-07-15 01:21:45 | Codex / GPT-5

- Action：实施 accepted 决策的阶段 0–5 代码与离线测试。
- Files：`model_api_settings.py`、`model_route_settings.py`、`model_gateway.py`、`model_runtime_client.py`、`model_connector_consent.py`、Trusted Broker、ASR/OCR 路由、设置 UI、安装矩阵与离线 A/B/C 工具。
- Boundary：未执行真实外部 API、未上传视频帧/音频/文档、未启动 Docker/计划任务、未更新 Obsidian；阶段 6 清理等待操作者 smoke。

### 2026-07-15 02:42:54 | Codex / GPT-5

- Action：完成阶段 0–5 的最终安全审计、生产入口覆盖、UI/安装/A-B-C 工具验收和两轮完整回归。
- Verification：任务覆盖 15 unified / 1 deferred / 0 drift；`compileall` 通过；完整测试连续两次 `682 passed, 1 warning`；6 组 temporal 样本均为 8/8 且 Timeline 写回 6/6。
- Remaining：真实 local VLM、Speaches、远程四类 smoke 和模型网关 A/B/C lane 数据仍需操作者单独授权；阶段 6 未执行。

### 2026-07-15 03:10:34 | Codex / GPT-5

- Action：把真实 smoke readiness 固化为不产生外部副作用的阶段机，并补严端口归属与 LiteLLM HTTP 健康门。
- Verification：当前真实配置路线 `0/6`、consent `0/4`、固定 temporal 样本 `6/6`；不会把任意占用端口的进程当作可用网关。
- Boundary：端口登记、服务启动、consent 创建、真实模型调用和 Obsidian 更新仍需操作者分别授权。

### 2026-07-15 03:52:28 | Codex / GPT-5

- Action：明确固定 temporal 验收的一份 consent/多帧组契约：artifact 精确覆盖所有组，调用额度等于组数，Broker 逐组执行和聚合。
- Verification：A/B/C lane 捕获严格区分 remote legacy、remote proxy、local proxy；完整离线回归连续两次 `695 passed, 1 warning`。
- Remaining：实际路线、consent、lane 与真实 smoke 仍是操作者门禁；未进入阶段 6。

### 2026-07-15 04:05:16 | Codex / GPT-5

- Action：网关 live readiness 与 start 只接受 LiteLLM 健康端点的 2xx；通用 404/不健康监听 fail closed。
- Verification：最终完整离线回归连续两次 `697 passed, 1 warning`。
- Boundary：真实启动、调用、外发及阶段 6 清理仍未授权、未执行。

### 2026-07-15 12:07:19 | Codex / GPT-5

- Action：接受在线模型外发策略补充，并把 consent v2、逐文件 SHA-256 上传清单、操作者确认和调用/费用额度定为远程执行前置条件。

### 2026-07-15 13:15:34 | Codex / GPT-5

- Action：把厂商硬编码分支升级为版本化 Provider Catalog，并由 LiteLLM prefix 驱动文本、视觉、ASR 和 OCR 配置渲染。
- Result：35 个 profile；25 text、23 vision、8 ASR、3 OCR；新增 `litellm_native` 扩展、本地 OpenAI-compatible 与 Speaches profile。
- Security：LiteLLM prefix 进入 route revision、authorized deployments 与 consent 路由快照；Secure Broker capabilities 返回 capability-indexed profile ids，但执行仍只接受 consent path 与 route revision。
- Cross-project：确认视频创作侧 edit-job v3 只读引用 VKP consent v2；provider receipt 不是新授权真源，也不能覆盖 VKP Bundle/Timeline。
- Verification：扩大定向 `99 passed`；Ruff、compileall、secret pattern 与 `git diff --check` 通过；完整离线回归 `722 passed, 1 warning`。
- Boundary：未启动 LiteLLM/本地模型服务，未调用真实 Provider，未上传 artifact，未 push，未写 Obsidian。
- Boundary：默认不外发；仍禁止自动发布、未列明上传、静默跨本地/远程 fallback 和平台策略绕过。

### 2026-07-15 14:35:19 | Codex / GPT-5

- Action：补齐 Azure OpenAI/Entra、Azure AI OCR、Vertex AI/Vertex OCR、AWS Bedrock 的显式高级认证控制面，并发布稳定 consent 执行 CLI。
- Security：非密钥 provider options 和固定环境绑定名进入 route revision/consent；密钥值不进入设置、YAML、stdout、Bundle、MCP 参数或文档。
- CLI：调用方只提交 consent path、精确 route revision 与显式 write 选择；VKP 继续独占 consent v2 复核、allowlist、原子 calls/cost reservation、Catalog/secret 解析与执行审计。
- Verification：仅 fake policy/fake executor/设置文件与 secretless YAML 测试；未调用真实 Provider、未上传 artifact。
- Boundary：默认不外发；仍禁止自动发布、未列明上传、静默 local/cloud fallback 和平台策略绕过。

### 2026-07-17 21:38:11 | Codex / GPT-5

- Action：补齐 route-locked `response_format` / `max_tokens` / M3 `thinking_mode=disabled`，修复 temporal 嵌套 runtime 指标，并新增 consent 锁定输出契约与 transport/contract/quality 三层状态。
- Offline evidence：复用已保存的 Stage B 43 个响应，未重新调用模型；质量门结果为 OCR `7/7`、语义视觉 `7/7`（2 个显式别名）、temporal `6/7`、证据摘要 `6/11`、最小纠错 `1/11`。
- Runtime：LiteLLM 子进程固定 `LITELLM_LOCAL_MODEL_COST_MAP=True`，避免启动时访问远程 cost map；未知费用仍保持 unknown。
- Verification：聚焦 `87 passed`；完整 `811 passed, 1 warning`；compileall、PowerShell AST、diff check、变更密钥扫描通过。
- Boundary：未调用任何在线模型、未上传 artifact、未读取或输出 secret、未自动提升默认路由；调用参数改变会生成新 route revision 并要求新 consent。
### 2026-07-18 00:13:09 | Codex / GPT-5

- Decision：新增 Coding Plan 使用范围硬边界。`volcengine_coding_plan` 只允许火山官方支持的 AI 编程工具；VKP 通用文本、视觉、ASR、OCR 与媒体知识任务必须使用标准 Ark `/api/v3` 或其他获批通用模型 API。
- Credential：凭据引用只在精确 `(provider, normalized base_url)` 内复用。Coding Plan 与标准 Ark API 不跨边界复制、解密或自动迁移凭据。
- Enforcement：统一运行时、legacy gateway 和 Trusted Broker 都在联网和 consent 原子额度预留前返回 `provider_usage_scope_blocked`。
- Comparison：Ark/SiliconFlow 同模型固定套件改为标准 Ark API，旧 Coding Plan 套件标记 superseded，不能执行或复用 consent。

## 2026-07-23 Policy Correction

- 2026-07-23 20:53:37 +08:00 | Codex (GPT-5)
- The 2026-07-18 Coding Plan task-scope denial is superseded. VKP must not reject a configured Coding Plan route merely because the request is a video-knowledge task. Each request stays bound to its exact route, provider/model, artifact manifest, destination allowlist, user consent, call/expense limits, and expiry; provider-side unsupported-capability or quota responses are reported as such. Standard Ark /api/v3 and Coding Plan /api/coding/v3 remain distinct endpoints and credentials, with no silent substitution.