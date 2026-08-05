# VKP 在线模型 Provider Catalog 与统一适配

- 更新时间：2026-07-15 14:35:19 +08:00
- 执行者：Codex / GPT-5
- 状态：控制面与离线契约已实现；真实供应商调用仍受 profile、allowlist、consent v2 和操作者 smoke 门禁

## 目标

VKP 不再为每个厂商分别实现文本、视觉、ASR 和 OCR 客户端。Provider 协议转换统一交给 LiteLLM Proxy，VKP 只保留：

1. 任务语义与统一结果 schema。
2. 本地/远程池隔离和内容寻址 route revision。
3. 精确文件 SHA-256、upload manifest、调用/费用上限和 consent v2。
4. Timeline、Bundle、Smart Summary、ASR/OCR candidate evidence 写回。
5. Secure MCP Broker 目的地 allowlist 和原子 reservation。

这使模型选择不依赖当前 Agent 是否具备视觉或音频能力。Agent 选择的是 VKP task 和已保存 route；模型服务由本地或在线 Provider 执行。

## 当前目录

权威实现：

- `src/video_knowledge_pipeline/model_provider_catalog.py`
- schema：`video_knowledge_pipeline.model_provider_catalog.v1`
- 当前预置 profile：41
- 能力索引：text 29、vision 27、asr 10、ocr 5

目录按 profile 而不是按厂商宣传名称计数；同一厂商的聊天、ASR、OCR 可以是不同 profile，因为端点、模型和计费单位不同。

### 文本与视觉

已登记常用远程族：OpenAI、Anthropic、Gemini、DeepSeek、阿里云百炼/DashScope、火山方舟、OpenRouter、Groq、Mistral、Moonshot、MiniMax、智谱/Z.AI、xAI、Together AI、Fireworks AI、DeepInfra、Cerebras、SambaNova、Perplexity、NVIDIA NIM、SiliconFlow，以及 OpenAI-compatible 自定义服务。

本地 profile 包括 OpenAI-compatible 文本/视觉、Qwen-VL 和通用本地 VLM。服务进程和模型权重仍由操作者管理，VKP 不安装新的本地大模型运行时。

### ASR

标准端点为 `/v1/audio/transcriptions`。目录包含：

- OpenAI-compatible / OpenAI Transcribe
- Groq ASR
- Deepgram ASR
- Fireworks AI ASR
- Mistral Voxtral ASR
- 其他 LiteLLM 原生 ASR prefix
- 本地 Speaches OpenAI-compatible ASR

本地 ebook Markdown OCR 的 PPT 文本和热词只作为受长度限制的 ASR prompt/context；原始 ASR 结果不会被纠错模型直接覆盖。

### OCR

标准端点为 `/v1/ocr`。正式 Proxy OCR 只接受 LiteLLM 已声明的 OCR prefix：`mistral`、`azure_ai`、`vertex_ai`，或显式 Mistral-compatible thin adapter。未支持的 OCR Provider 不会被静默改写为视觉聊天。

本地 `ebook_markdown_pipeline` 仍是默认 OCR，路径和产物不变；它的 PPT 文本、版面结构和热词继续供 ASR、摘要、纠错和实体词典只读消费。

## 通用扩展点

`provider=litellm_native` 是唯一通用扩展入口。新增 LiteLLM 已支持的单 Key Provider 时，只需显式保存：

- `litellm_provider`
- `base_url`
- `model`
- `location`
- `capabilities`

不需要增加新的 VKP provider 分支。预置 profile 的 LiteLLM prefix 被锁定，不能在 UI 中改成另一厂商；通用 profile 的 prefix 也会进入 route revision、authorized deployments 和 consent 路由快照，变更后旧 consent 立即失配。

高级认证已采用显式、可审计的双轨契约：

- API Key profile：Key 仍由 DPAPI 持久化，明文只注入 LiteLLM 子进程环境。
- 外部环境 profile：VKP 只保存固定环境变量名和非密钥参数，不读取、返回或持久化环境变量值。
- Azure OpenAI：支持 API Key 与 Entra ID 两种 profile；`api_version` 是非密钥必填项。
- Vertex AI：`vertex_project`、`vertex_location` 作为非密钥配置，凭据路径只从 `GOOGLE_APPLICATION_CREDENTIALS` 注入。
- AWS Bedrock：`aws_region_name` 作为非密钥配置，凭据只从 `AWS_ACCESS_KEY_ID`、`AWS_SECRET_ACCESS_KEY` 注入。
- Azure AI OCR 与 Vertex AI OCR 继续走正式 `/v1/ocr` 契约。

`provider_options` 只能包含 Catalog 为该 profile 明确允许的标量字段；secret 形状字段、任意环境引用、换行和未知参数均拒绝。认证模式、非密钥参数、环境绑定名会进入 deployment identity、route revision、authorized deployments 与 consent 路由快照，任何变化都会使旧 consent 失配。网关渲染只生成 `os.environ/ENV_NAME` 引用；缺少必填参数、环境变量或 API Key 时 `ready_for_start=false`，不会启动 LiteLLM。

## Agent 与 UI 发现

设置 UI 的公开状态同时返回：

- `provider_presets`
- 完整 `provider_catalog`
- catalog revision
- 每个 profile 的 `litellm_provider`

Secure MCP Broker 的 `model_connector_capabilities` 也返回完整 catalog，并为每项任务给出：

- `catalog_capability`
- `provider_profile_ids`
- `runtime_policy`
- `transport.kind=streamable-http`
- `transport.loopback_only=true`
- `transport.platform_access=secure_mcp_tunnel`

执行工具仍只接受 `consent_path + route_revision`；Agent 不能提交任意 Provider URL、API Key 或未保存的 fallback。

## 安全边界

- 保存配置不等于授权外发。
- 远程 profile 必须是 HTTPS；本地 profile 必须是 loopback。
- local-only 与 remote-approved profile 不能进入同一池。
- Proxy 失败不会切换到 legacy 或另一执行位置。
- 远程池内候选全部进入 route revision、consent v2 和 Broker allowlist。
- API Key 只以 DPAPI 密文持久化，解密值只进入 LiteLLM 子进程环境。
- 本地图片在内存中临时转成完整 MIME data URL；裸 base64、无协议路径和 data URL 正文不持久化。
- 无 consent v2 的远程执行在发起 socket 请求前返回 `remote_consent_required`。

## 与视频创作侧的契约

`mvp-video-pipeline` 的 `video_creation_pipeline.vkp_edit_job.v3` 只读引用 VKP 的 `video_knowledge_pipeline.model_connector_consent.v2`。VKP 继续是 Provider、route、任务、剩余额度和 upload manifest 的唯一授权真源。

视频创作侧 `human_selection -> provider_request -> provider_receipt` 是候选交付与回执闭环，不是新的 consent；回执不能扩大 route、calls/cost、上传清单或写回权限，也不能覆盖 VKP Bundle、Timeline 或上传源文件。

## 开源复用依据

- LiteLLM 版本约束：`litellm[proxy]>=1.81.7,<2`
- 复用范围：Provider prefix、OpenAI-compatible chat/vision、audio transcription、OCR、同一池内路由和错误归一化
- VKP 自有范围：任务 schema、证据写回、路由 revision、consent、Broker allowlist、费用/调用 reservation
- 官方文档：[LiteLLM](https://docs.litellm.ai/)、[Audio Transcription](https://docs.litellm.ai/docs/audio_transcription)、[OCR](https://docs.litellm.ai/docs/ocr)

## 验证

自动测试只使用设置文件和 fake loopback Proxy，不调用真实供应商：

- 预置 prefix 锁定与通用 prefix 校验
- capability/location 查询
- provider prefix 进入 route revision
- 文本、ASR、OCR LiteLLM YAML 渲染
- UI 保存/公开状态不泄露 secret
- Broker 能力目录、consent v2、目的地与原子 reservation
- OCR 非标准 prefix 拒绝

真实模型可用性、模型名称、额度和价格仍需逐 profile 由操作者在对应账户与固定样本上 smoke。目录中的“支持”表示协议已接入，不代表账户、模型或目的地已经获准运行。

## 稳定 consent 执行入口

跨仓调用统一使用：

```powershell
.\scripts\video-knowledge.ps1 execute-consented-model-task <consent_path> --route-revision <exact-route-revision> --write
```

输入面不接受 Provider URL、model、API Key 或 fallback。退出码为 `0` 成功、`1` 执行失败、`2` consent/route/policy 阻断、`3` 输入无效；完整 JSON 写到 stdout。生产交接应使用 `--write` 持久化执行报告。

### 2026-07-15 14:35:19 | Codex / GPT-5

- 增加 Azure OpenAI/Entra、Azure AI OCR、Vertex AI/Vertex OCR 与 AWS Bedrock 高级认证 profile；新增 secretless 环境映射、启动 readiness 门和稳定 consent 执行 CLI。离线测试不调用真实 Provider。
## 2026-07-23 Groq ASR transport 更正

更新：2026-07-23 09:11:26 +08:00，Codex / GPT-5.6。

Groq ASR 仍使用 `https://api.groq.com/openai/v1`、`whisper-large-v3-turbo` 和既有 DPAPI Key。由于 LiteLLM 1.81.7 至上游稳定版 1.86.2 的原生 Groq STT transform 都未暴露官方 `timestamp_granularities` 参数，Groq ASR profile 改为复用 LiteLLM `openai` transcription transport，并预填 `asr_timestamp_granularity=word`。保存的旧 `litellm_provider=groq` 会在加载时迁移为该已审计 transport；Key 不需重填。transport 和粒度都会改变 route revision，旧 consent 不可复用。

本轮只完成离线契约验证；“已接入”仍不等于供应商当前可用。下一次真实 Groq ASR 必须重新渲染网关配置并使用匹配新 revision 的有效 consent。
