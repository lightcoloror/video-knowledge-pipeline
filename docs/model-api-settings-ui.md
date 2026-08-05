# 在线模型 API 本地设置界面

更新时间：2026-07-16 19:05:00
执行者：Codex / GPT-5

## 启动

在 VKP 项目目录运行：

```powershell
.\scripts\start-model-api-settings.ps1
```

然后打开：

```text
http://127.0.0.1:8767/
```

重新导出的 `webui-bundle/model-settings.html` 也包含此入口。

## 可以配置的任务

- 在线 ASR
- 在线 OCR
- PPT / 文档视觉
- 单帧语义
- 多帧时序
- 视频片段视觉
- 通用文本模型
- 智能摘要改写
- 转录纠错

同一个供应商 profile 可以服务多个任务；每个任务只能路由到一个启用的 profile。显式 CLI/MCP runtime `provider_config` 的优先级高于本地 profile。

## 本地文件

- 普通配置：`.local/model-api-settings.json`
- DPAPI 密文：`.local/model-api-secrets.json`
- UI 地址单一配置源：`config/model-api-settings-ui.json`

`.local/` 已被 Git 忽略。HTTP 状态、WebUI、manifest 和报告只显示 `api_key_configured`，不会返回 API Key 或 DPAPI 密文。

## 安全边界

- 设置服务只允许绑定 loopback；默认 `127.0.0.1:8767`。
- 设置服务与 `127.0.0.1:8766/mcp` 分离，不进入 Secure MCP Tunnel。
- 远程 Base URL 必须使用 HTTPS；本地 loopback 才允许 HTTP。
- Base URL 不允许用户名、密码、query 或 fragment，避免把 Key 放进 URL。
- “仅验证”只检查结构和 URL 策略，不联网。
- 保存供应商不代表该域名已获 Trusted Broker 授权。真正发送帧、音频或文本时，仍需满足 consent、artifact hash、有效期、调用次数和目的地白名单。
- 页面不会自动执行模型调用。

## 凭据行为

- API Key 输入框永远不回填。
- 输入新 Key 会覆盖该 profile 的旧凭据。
- 留空会保留旧凭据。
- 选择“保存时删除已有 API Key”会删除凭据。
- 删除 profile 会同时删除其任务路由与本地密文。
- DPAPI 密文只能由创建它的 Windows 用户在本机解密。

## 路由设置 v2（2026-07-15）

设置页现已升级为混合模型控制台：

- profile 明确选择 `local` / `remote` 与 `text` / `vision` / `asr` / `ocr` 能力；
- 分别编辑 local-only 与 remote-approved pool 的有序 deployment；
- 每个任务分别选择默认位置、本地池和远程池；
- 展示 route revision、健康状态、最后检查时间、预计费用或“未知”、consent 与 allowlist 状态；
- `PUT /api/routes` 与 profile 保存均受 loopback、Origin 和 CSRF 检查；
- 保存配置不会创建 consent，也不会触发模型调用。

新 profile 默认 `proxy`；从 v1 迁移的旧 profile 默认保持 `legacy`，直到用户显式切换。`route_bindings` 是 v2 权威路由，旧 `task_routes` 仅作为只读兼容视图。

## Provider Catalog（2026-07-15）

- 设置 API 返回版本化 `provider_catalog`、catalog revision 和 41 个预置 profile。
- profile 显式显示 `litellm_provider`；预置 profile 的 prefix 锁定，`litellm_native` 才允许用户填写。
- 当前目录覆盖 29 个 text、27 个 vision、10 个 ASR、5 个 OCR profile；同一 profile 可声明多个兼容能力。

## һ��Ӧ���޶���ȫ���̲���·��

������Ԥ�� profile �ѵ���󣬿����ȶ� CLI Ӧ�þ������˵ĵ� deployment ·�ɣ�

```powershell
.\scripts\video-knowledge.ps1 model-api-route-preset `
  --preset online-screening-no-doubao-v1
```

�ֹ�Ϊ��Ark DeepSeek V4 Pro��ͨ���ı�����Ark Kimi K2 Thinking��ժҪ����Ark GLM 5.2������ת¼��������SiliconFlow PaddleOCR-VL��PPT/�ĵ��Ӿ�����SiliconFlow GLM-4.5V����֡���壩��Gemini 3.5 Flash��temporal/video segment����Groq Whisper Large V3 Turbo��ASR����Mistral OCR 4����׼ OCR����ÿ����ֻ��һ�� deployment�����ᾲĬ�繩Ӧ�� fallback��

������ֻ����·�ɲ������µ� route revision������ Broker allowlist��ƥ�䵱ǰ revision �� consent v2 �Ͳ�����ȷ�Ϻ��������ִ�С�

- 新的本地 profile 包含 OpenAI-compatible 文本/视觉与 Speaches ASR，默认端口分开。
- LiteLLM-native 是新供应商扩展点，但不会扩大 Broker allowlist，也不会绕过 consent v2。
- UI 已支持 Catalog allowlist 内的非密钥 `provider_options`；API Key profile 使用 DPAPI，Entra/Vertex/AWS profile 只显示固定环境变量名与就绪状态，不展示或持久化值。

详细目录：`docs/online-model-provider-catalog-2026-07-15.md`。

## 精确模型模板预导入

更新时间：2026-07-16 17:45:40
执行者：Codex / GPT-5

无需 API Key 即可离线准备全部已有精确模板：

```powershell
.\scripts\video-knowledge.ps1 model-api-onboarding-prepare
```

默认准备 SiliconFlow、ModelScope、Groq、Ark 无豆包、Google Gemini 和 Mistral 六组，共 16 个 profile。也可重复使用 `--provider <id>` 只准备指定供应商。

该命令不读取或写入 `.local/model-api-secrets.json`，不联网、不创建 consent、不分配任务路由，也不改变已有 route pool/binding。准备完成后，在本地设置页为每个供应商粘贴一次 API Key 并点击“Fill API Key”；同一 Key 会通过 DPAPI 分配到该供应商的精确模板，输入框不会回填明文。

## 模型目录检查与安全刷新（2026-07-16）

已保存 Key 的精确供应商卡片提供“只读检查 Key 与模型目录”。该操作必须由操作者点击，调用固定的供应商 `GET /models`：

- 只验证认证与精确模型可见性；
- 不执行模型推理；
- 不读取或上传本地 artifact；
- 不创建 consent，也不改变 route；
- Gemini 使用 `X-goog-api-key` header，Key 不进入 URL；
- 返回内容只包含状态、数量、模型 ID 与调用契约，不包含 Key。

同样的稳定 CLI：

```powershell
.\scripts\video-knowledge.ps1 model-api-catalog-probe --provider <provider-id> --execute
```

当代码登记的精确模板已被供应商目录替换时，可运行：

```powershell
.\scripts\video-knowledge.ps1 model-api-onboarding-prepare --refresh-known-models
```

它只替换 `replaces_models` 白名单内的旧 ID。用户自定义模型不会被覆盖，API Key 不会被读取或重填。当前 Ark MiniMax M3/M2.7 因账户目录未返回精确 ID而保持禁用。

核验记录：[`online-model-catalog-verification-2026-07-16.md`](online-model-catalog-verification-2026-07-16.md)。

## Update Record

### 2026-07-15 01:21:45 | Codex / GPT-5

- 更新为支持本地/远程池、任务默认位置、route revision、安全状态与 Proxy/legacy 显式切换的 v2 设置界面。

### 2026-07-15 12:50:25 | Codex / GPT-5
- 增加 Provider Catalog、LiteLLM prefix 显式字段、通用 Provider 扩展以及本地 OpenAI-compatible/Speaches profile。


### 2026-07-15 14:35:19 | Codex / GPT-5

- 增加高级认证的非密钥参数编辑、外部环境凭据就绪状态和 API Key 输入禁用逻辑；保存配置仍不等于外发授权。

### 2026-07-15 19:04:24 | Codex / GPT-5

- Added an offline free-provider onboarding area to the existing loopback settings UI.
- The interaction selectively reuses the API-settings pattern recorded in docs/bilinote-pridewood-source-review.md and the run/readiness state pattern recorded in docs/vsummary-source-review.md; it does not copy either full frontend.
- Registered SiliconFlow, ModelScope, Groq ASR, OpenRouter, NVIDIA NIM, and GitHub Models as screening candidates with official account, credential, and documentation links.
- Added local-only readiness states for profile, model, credential, route, allowlist, and consent gaps.
- One-click prefill only edits an unsaved disabled form draft. It does not select tasks, persist credentials, call a provider, create a route, or grant consent.
- GitHub Models remains adapter_required and cannot be prefilled into an executable route until its fixed-header contract is implemented and tested.

### 2026-07-16 00:13:32 | Codex / GPT-5

- Added the Offline Model Screening Lab to the existing loopback settings UI and API.
- Reused the existing A/B/C acceptance schema and unified runtime-client contracts instead of creating a second quality benchmark.
- The simulator covers completed, HTTP 429, HTTP 503, timeout, invalid-response, and local-gateway-unavailable contracts for text, vision, ASR, and OCR endpoints.
- Simulated latency, cost, reliability, and success are never eligible for model-quality ranking; quality still requires human-reviewed fixed-sample results.
- `POST /api/screening/simulate` inherits loopback Host, JSON content type, request-size, Origin, and CSRF enforcement.
- Every simulated receipt records zero provider requests, zero source-artifact reads, zero payload generation, and zero credential access.
- Real smoke tests still require a saved route revision, an approved destination, consent v2, exact artifact hashes, and operator authorization. No local/remote silent fallback is introduced.

### 2026-07-16 19:05:00 | Codex / GPT-5

- 增加六组精确 bundle 的只读模型目录检查按钮与 CLI。
- 把 Ark、SiliconFlow 过期模型别名迁移到当前账户可见的精确 ID。
- Catalog 不可见的 Ark MiniMax profile 默认禁用；不猜测调用。
- Gemini legacy 请求改用 `X-goog-api-key` header，避免凭据出现在 URL。
