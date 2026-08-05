# 在线模型目录与正确调用契约核验

更新时间：2026-07-16 19:29:29
执行者：Codex / GPT-5

## 结论

六组已保存凭据均能访问对应供应商的模型目录，最终结果为 6/6 verified。核验只读取模型元数据：0 次模型推理、0 个本地 artifact 读取、0 个文件上传。

| 供应商 | 最终 HTTP | 目录模型数 | 启用模板可见 | 结论 |
| --- | ---: | ---: | ---: | --- |
| SiliconFlow | 200 | 91 | 3/3 | verified |
| ModelScope | 200 | 55 | 2/2 | verified |
| Groq | 200 | 17 | 2/2 | verified；Python 默认 User-Agent 曾被 403，固定非密钥 User-Agent 后通过 |
| Ark Coding Plan 无豆包 | 200 | 126 | 4/4 | verified；另有 2 条 MiniMax 模板因目录不可见而禁用 |
| Google Gemini | 200 | 54 | 1/1 | verified |
| Mistral | 200 | 62 | 2/2 | verified |

本阶段共发出 14 次元数据 GET：6 次最终批量目录检查、2 次 Groq 诊断/复核、1 次 Ark 目录详情、5 次 Ark 模型详情端点诊断。模型推理调用仍为 0。

## 当前精确模型

### Ark Coding Plan（无豆包）

- `deepseek-v4-pro-260425`：高置信纠错、证据仲裁。
- `deepseek-v4-flash-260425`：低成本初筛。
- `glm-5-2-260617`：独立文本判断。
- `kimi-k2-thinking-251104`：长文本结构化与第二意见。
- `minimax-m3`、`minimax-m2.7`：官网计划页提及，但当前账户 `/models` 未返回精确 ID；profile 保留凭据但 `enabled=false`，不得调用。

### 其他供应商

- Google：`gemini-3.5-flash`。
- ModelScope：`ZhipuAI/GLM-5.2`、`deepseek-ai/DeepSeek-V4-Pro`。
- Groq：`qwen/qwen3.6-27b`、`whisper-large-v3-turbo`。
- Mistral：`voxtral-mini-2602`、`mistral-ocr-4-0`。
- SiliconFlow：`Qwen/Qwen3.5-4B`、`zai-org/GLM-4.5V`、`PaddlePaddle/PaddleOCR-VL-1.5`。

## 正确调用契约

业务模块和 Agent 不直接提交供应商 URL 或 Key。正式任务统一调用本机 LiteLLM Proxy，Broker 用 route revision 与 consent v2 锁定实际 deployment。

| 能力 | VKP 调用 LiteLLM | 供应商侧协议 | 关键格式 |
| --- | --- | --- | --- |
| 文本 / 视觉 | `POST /v1/chat/completions` | OpenAI-compatible，或由 LiteLLM 转 Gemini `generateContent` | 图片只从受控本地路径读取，并临时变为完整 MIME data URL |
| ASR | `POST /v1/audio/transcriptions` | Groq/Mistral multipart transcription | `file`、`model`、可选且限长的 `prompt` |
| OCR | `POST /v1/ocr` | Mistral native OCR | 每次一个 `document`；图片使用 `image_url`，文档使用 `document_url` |

供应商细节：

- Gemini：`POST /v1beta/models/{model}:generateContent`；Key 使用 `X-goog-api-key` header，不进入 URL。
- SiliconFlow、ModelScope、Groq、Ark：Bearer + OpenAI-compatible `/chat/completions`。
- Groq ASR：Bearer + `/audio/transcriptions`。
- Mistral ASR：Bearer + `/audio/transcriptions`。
- Mistral OCR：Bearer + `/ocr`，请求体包含 `model` 与单一 `document`。

LiteLLM 1.81.7 已能解析当前使用的 provider/model 前缀：`gemini/`、`groq/`、`mistral/`、`openai/`。

## 已应用的无豆包全流程路由

本地设置已应用 `online-screening-no-doubao-v1`，形成 8 个单 deployment remote pool，覆盖 9 个任务。保存路由没有触发网络请求，也不构成外发授权。

| VKP 任务 | 当前 deployment |
| --- | --- |
| `text_llm` | `ark-deepseek-v4-pro` / `deepseek-v4-pro-260425` |
| `summary_rewrite` | `ark-kimi-k2-6` / `kimi-k2-thinking-251104` |
| `transcript_correction` | `ark-glm-latest` / `glm-5-2-260617` |
| `document_visual` | `siliconflow-paddleocr-vl-1-5` |
| `semantic_frame` | `siliconflow-glm-4-1v-9b-thinking` / `zai-org/GLM-4.5V` |
| `temporal_sequence`、`video_segment` | `google-gemini-3-5-flash` |
| `asr` | `groq-whisper-large-v3-turbo` |
| `ocr` | `mistral-ocr-4-0` |

旧 `remote-ark / ark-code-latest` profile 被保留用于显式回滚，但已不再绑定任何任务。所有池只有一个 deployment，`automatic_cross_destination_fallback=false`。

当前 20 个本地 profile 均保留 DPAPI 凭据引用；20/20 显示 Key ready。两个当前账户目录不可见的 MiniMax profile 和未启动的本地 Qwen-VL 保持禁用。

## 可重复检查

CLI：

```powershell
.\scripts\video-knowledge.ps1 model-api-catalog-probe --provider siliconflow --execute
.\scripts\video-knowledge.ps1 model-api-catalog-probe --provider modelscope --execute
.\scripts\video-knowledge.ps1 model-api-catalog-probe --provider groq --execute
.\scripts\video-knowledge.ps1 model-api-catalog-probe --provider ark_no_doubao --execute
.\scripts\video-knowledge.ps1 model-api-catalog-probe --provider google_gemini --execute
.\scripts\video-knowledge.ps1 model-api-catalog-probe --provider mistral --execute
```

设置 UI 在每个已保存 Key 的精确 bundle 下提供“只读检查 Key 与模型目录”。点击后只发一次目录 GET，并显示可见模板数。

刷新已知旧模板：

```powershell
.\scripts\video-knowledge.ps1 model-api-onboarding-prepare --refresh-known-models
```

这个刷新只允许把代码登记过的旧 ID 换为已复核新 ID。任意自定义模型 ID 仍会触发冲突并拒绝覆盖。它不读取凭据、不联网、不改任务路由。

## 尚未完成

- 目录检查证明 Key 和模型 ID 有效，但不是生成质量证明。
- 8 个 route revision 已生成；当前 CLI 进程的 allowlist 状态为 `unknown`。正式最小推理 smoke 仍需 Broker 明确允许五个精确目的地，并针对当前 revision 创建 consent v2；不得绕过 Broker 直接调用。
- 五个精确目的地为 `ark.cn-beijing.volces.com`、`api.siliconflow.cn`、`generativelanguage.googleapis.com`、`api.groq.com`、`api.mistral.ai`。
- 六组 temporal 视频帧仍需独立有效 consent，不能复用本次目录检查。
- MiniMax 只有在当前账户目录返回精确 ID 后才能重新启用。

## 验证

- 路由预设聚焦测试：`27 passed`；显式 provider 与 proxy 预览聚焦测试：`29 passed`。
- 完整离线回归：`779 passed, 1 warning`，高于本阶段开始前的 `772 passed` 基线。
- Groq 403 已定位为缺少稳定 User-Agent；修正后同一 Key、同一路径返回 HTTP 200。
- 本地设置迁移：5 个旧模型 ID 已安全刷新；16 个 exact onboarding profile 和 4 个既有 profile 均保留；Key 无需重填；任务路由已从旧 `ark-code-latest` 切换为上述 9 条精确路由。
- 代理模式的 `execute=false` 预览只生成计划，不读取 artifact；显式 legacy `provider_config` 不再被同名任务 route 的 model 静默覆盖。
- 未打印、记录或提交任何 API Key、DPAPI 密文或 transient data URL。
## 2026-07-18 使用范围更正

更新时间：2026-07-18 00:13:09
执行工具：Codex / GPT-5

火山方舟 Coding Plan `/api/coding/v3` 只用于其官方支持的 AI 编程工具，不再作为 VKP 摘要、纠错、视觉或其他通用推理任务的执行端点。通用 VKP 任务必须使用标准方舟模型 API `/api/v3`，并使用独立 provider/base URL 凭据引用、新 route revision 和 consent v2。既有 Coding Plan 探测与调用记录只保留为历史证据，不能证明通用 API 路线可用。

同模型 Ark/SiliconFlow 对比的当前边界和精确模型见 `docs/ark-siliconflow-same-model-parity-2026-07-17.md`。

## 2026-07-23 Policy Correction

- 2026-07-23 20:53:37 +08:00 | Codex (GPT-5)
- The 2026-07-18 Coding Plan task-scope denial is superseded. VKP must not reject a configured Coding Plan route merely because the request is a video-knowledge task. Each request stays bound to its exact route, provider/model, artifact manifest, destination allowlist, user consent, call/expense limits, and expiry; provider-side unsupported-capability or quota responses are reported as such. Standard Ark /api/v3 and Coding Plan /api/coding/v3 remain distinct endpoints and credentials, with no silent substitution.