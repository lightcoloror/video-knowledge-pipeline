# 方舟 Coding Plan / Cline 接入说明

更新时间：2026-07-16 19:02:00
执行工具：Codex / GPT-5

> [!IMPORTANT]
> 当前强制边界（2026-07-18 00:13:09，Codex / GPT-5）：Coding Plan `/api/coding/v3` 只可用于火山官方支持的 AI 编程工具。VKP 的摘要、转录纠错、视觉和媒体知识任务不得通过该端点执行；这些任务必须改用标准 Ark 模型 API `/api/v3`、独立凭据引用、精确 route revision 与 consent v2。本文后续内容仅作为编程工具接入历史和配置参考，不能作为 VKP 通用模型执行授权。
## 目标

把火山引擎方舟 Coding Plan 作为 VKP 的无豆包在线文本模型池：

- 任务分工：DeepSeek V4 Pro/Flash、GLM 5.2、Kimi K2 Thinking 各自保存为独立 profile；当前账户目录未返回 MiniMax M3/M2.7，因此两条模板保留但禁用。
- 视觉能力：改走单独获批的 Gemini 或 Groq Qwen profile；本火山无豆包 bundle 全部是 text-only，也不自动 fallback。

VKP 内部统一使用 OpenAI-compatible 路线：

```text
https://ark.cn-beijing.volces.com/api/coding/v3
```

Anthropic-compatible 路线：

```text
https://ark.cn-beijing.volces.com/api/coding
```

当前 VKP 主接入 OpenAI-compatible，因为它能同时覆盖 OpenClaw、Codex CLI、Cline、OpenCode、Hermes Agent 等工具生态，也和本项目已有 `vision_api`、`text_llm_gateway`、`online_model_gateway` 更一致。

## VKP 环境变量

旧版兼容入口可继续使用 `ark-code-latest`，但它不证明控制台背后的具体模型，不用于固定模型 consent：

```powershell
$env:LECTURE_VISION_PROVIDER = "volcengine_coding_plan"
$env:ARK_API_KEY = "<paste-your-coding-plan-api-key>"
$env:LECTURE_VISION_BASE_URL = "https://ark.cn-beijing.volces.com/api/coding/v3"
$env:LECTURE_VISION_MODEL = "ark-code-latest"
```

无豆包文本任务应固定使用下面的通用 LLM 环境变量；API key 不写入项目文件：

```powershell
$env:LECTURE_VISION_PROVIDER = "volcengine_coding_plan"
$env:LLM_API_KEY = "<paste-your-coding-plan-api-key>"
$env:LLM_BASE_URL = "https://ark.cn-beijing.volces.com/api/coding/v3"
$env:LLM_MODEL = "deepseek-v4-pro-260425"
```

如果账户 `GET /models` 不再返回 `deepseek-v4-pro-260425`，先更新 profile 与 route revision，再重新创建 consent；不得静默切到豆包、Auto 或其他模型。

## 支持模型与 VKP 推荐用途

2026-07-16 使用当前账户 API Key 读取 `/models` 后，VKP 采用以下精确 ID：

| Model Name | VKP 推荐用途 |
| --- | --- |
| `deepseek-v4-pro-260425` | 当前无豆包默认文本模型；用于语义纠错、多证据冲突与工具名/代码名复核。 |
| `deepseek-v4-flash-260425` | 低成本快速复核或批量分类。 |
| `glm-5-2-260617` | 通用文本理解和独立仲裁。 |
| `kimi-k2-thinking-251104` | 长文本总结、课程结构化与第二意见。 |
| `minimax-m3` / `minimax-m2.7` | 官网计划页提及 MiniMax，但当前账户目录未返回精确 ID；VKP 禁用，不猜测调用。 |
| `kimi-k2.7-code` | 当前账户目录未返回；VKP 禁用，不猜测调用。 |

VKP 当前分工为：`deepseek-v4-pro-260425` 负责高置信纠错与证据仲裁，`deepseek-v4-flash-260425` 负责低成本初筛，`glm-5-2-260617` 与 `kimi-k2-thinking-251104` 提供独立二次意见和长文本结构化。每个模型都是独立 profile；切换任务模型会生成新 route revision 并要求重新授权。不得静默切到豆包、Auto 或另一个模型。视觉任务使用 Gemini、Groq Qwen 或 SiliconFlow GLM-4.5V 的独立远程池。

实测路由记录见 [`volcengine-model-routing-test-2026-07-09.md`](volcengine-model-routing-test-2026-07-09.md)。VKP 已提供 `volcengine-model-task-matrix` 命令，可用小文本样本验证每个模型是否适合对应任务。

## Base URL 边界

OpenAI-compatible 工具必须使用：

```text
https://ark.cn-beijing.volces.com/api/coding/v3
```

不要使用：

```text
https://ark.cn-beijing.volces.com/api/v3
```

后者不是 Coding Plan 专用入口，不会消耗 Coding Plan 额度，可能产生额外费用。VKP 的 `volcengine_coding_plan` profile 默认固定使用 `/api/coding/v3`。

## VKP 验证命令

只读查看配置，不调用云端：

```powershell
.\scripts\video-knowledge.ps1 model-api-settings
.\scripts\video-knowledge.ps1 online-model-api-matrix
```

普通 LLM preview，不调用云端：

```powershell
.\scripts\video-knowledge.ps1 online-model-api summary_rewrite `
  --provider-config '{"provider":"volcengine_coding_plan"}' `
  --input-text "测试证据包"
```

多模态 preview，不调用云端：

```powershell
.\scripts\video-knowledge.ps1 online-model-api semantic_frame `
  --provider-config '{"provider":"volcengine_coding_plan"}' `
  --image-paths D:\path\to\frame.png
```

真实调用必须显式加 `--execute`。大批量视觉调用仍应先跑 VKP 的 preflight / queue：

```powershell
.\scripts\video-knowledge.ps1 vision-execution-preflight D:\path\to\webui-bundle --semantic-limit 10 --no-temporal
```

## Cline 配置

在 Cline 中选择 OpenAI-compatible 或 Compatible/OpenAI API 类型，然后填写：

```text
API Provider: OpenAI Compatible
Base URL: https://ark.cn-beijing.volces.com/api/coding/v3
API Key: <paste-your-coding-plan-api-key>
Model ID: deepseek-v4-pro-260425
```

如果 Cline UI 要求完整 endpoint，优先仍填写 base URL，不要追加 `/chat/completions`；大多数 OpenAI-compatible 客户端会自己拼接。如果某个 Cline 版本明确要求 endpoint，再使用：

```text
https://ark.cn-beijing.volces.com/api/coding/v3/chat/completions
```

## 边界

- VKP 设置 UI 可把 Coding Plan API key 以当前 Windows 用户的 DPAPI 密文保存到 `.local/model-api-secrets.json`；明文不写配置、日志、Bundle 或报告。
- 生成的 bundle、manifest、报告、README、AGENT_DISCOVERY 里不得出现真实 key。
- 默认 preview 不调用外部 API。
- `--execute` 才会调用云端。
- 大批量多模态仍走 queue/preflight，避免误把大量私有视频帧一次性外发。
- 图文截图主通道仍优先复用本地 `ebook_markdown_pipeline`；方舟多模态主要用于疑难点、低置信、非图文视觉信息和最终语义复核。

## 当前项目接入点

- `vision_api.resolve_provider_config`：解析 `volcengine_coding_plan` 的 key/base URL/model。
- `text_llm_gateway.resolve_text_provider_config`：复用同一 provider config 作为普通 LLM。
- `online_model_gateway`：统一暴露 `semantic_frame`、`temporal_sequence`、`summary_rewrite`、`transcript_correction` 等在线模型类型。
- `task-console.html`：显示在线模型 API 矩阵和火山批处理命令。

## 2026-07-23 Policy Correction

- 2026-07-23 20:53:37 +08:00 | Codex (GPT-5)
- The 2026-07-18 Coding Plan task-scope denial is superseded. VKP must not reject a configured Coding Plan route merely because the request is a video-knowledge task. Each request stays bound to its exact route, provider/model, artifact manifest, destination allowlist, user consent, call/expense limits, and expiry; provider-side unsupported-capability or quota responses are reported as such. Standard Ark /api/v3 and Coding Plan /api/coding/v3 remain distinct endpoints and credentials, with no silent substitution.