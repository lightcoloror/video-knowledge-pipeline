# VKP 多供应商 Key-only 接入与开源复用

更新时间：2026-07-18 10:36:32 +08:00
执行者：Codex / GPT-5

## 决策

普通接入路径固定为：选择供应商，填写一次 API Key，安装版本化精确预设。用户不需要手填 Base URL、LiteLLM provider、模型 ID、能力、协议或 Provider JSON。

手工 Provider、URL、模型和 JSON 参数属于高级入口。保存预设不联网、不改变默认路由、不创建 consent，也不授权外发。

## 复用来源

| 上游 | 复用内容 | VKP 保留的差异 |
| --- | --- | --- |
| [LiteLLM](https://github.com/BerriAI/litellm) | Provider 协议转换、统一 chat/vision/ASR/OCR 端点、模型能力/费用元数据结构 | 任务 schema、DPAPI、route revision、consent v2、目的地 allowlist、调用与费用 reservation |
| [Cline `@cline/llms`](https://docs.cline.bot/sdk/model-providers) | Provider Registry、Provider 到模型目录的组织方式 | 不让远端目录静默替换精确 deployment |
| [Open WebUI OpenAI-compatible connections](https://docs.openwebui.com/getting-started/quick-start/connect-a-provider/starting-with-openai-compatible) | Provider-aware 连接 UI、`/models` 自动发现及不支持目录时的显式模型 allowlist | 目录只用于发现与漂移证据，不自动改 route/consent/fallback |
| [Cherry Studio](https://github.com/CherryHQ/cherry-studio) | 桌面端多 Provider 预设分组与本地凭据交互模式 | 只参考设计；不复制 AGPL 前端或业务代码 |

字段权威顺序始终是：供应商官方文档 > 已获授权的账户模型目录 > 固定版本的开源注册表提示。LiteLLM 或客户端注册表不能代替供应商对当前模型、价格和数据政策的声明。

每个 Key-only bundle 现在同时携带 `provider_prefill_contract.v1`：官方文档 URL、最后核对日期、允许的 Base URL、Provider、协议、禁止字段以及内容 SHA-256。安装 bundle 前会统一执行 fail-closed 校验；设置页显示契约 ID、核对日期和短 SHA。这样常规接入不需要重复查文档，代码更新若把 SiliconFlow `enable_thinking` 与 Ark `thinking_mode` 混用，会在测试和安装阶段直接失败。

## 当前 Key-only bundles

- SiliconFlow：文本、视觉、PaddleOCR-VL 文档视觉及五组同系列对比候选。
- ModelScope：当前已登记的 API-Inference 文本候选。
- Groq：文本、最多三图视觉和 Whisper ASR。
- Ark no-Doubao Coding Plan：固定 Coding Plan alias 的文本候选。
- Ark standard model API：固定标准 `/api/v3` deployment 的文本候选。
- Google Gemini：文本及多帧/视频视觉候选。
- Mistral：Voxtral ASR 与 OCR。

OpenRouter、NVIDIA NIM、GitHub Models 等只有在精确模型、额外 headers、目的地与任务能力都审核后，才能升级为 Key-only bundle；不能以“OpenAI-compatible”为由自动开放任意 URL。

## Provider 参数

- SiliconFlow 官方思考开关使用 `enable_thinking: false|true`，可选 `thinking_budget`。
- Ark / Coding Plan 的 VKP 扩展使用 `thinking_mode: "disabled"|"enabled"|"auto"`。
- UI 会显示当前预设的允许字段。SiliconFlow 旧的 `thinking_mode=disabled|enabled` 保存请求会迁移为 `enable_thinking=false|true`；`auto` 无明确等价语义，继续拒绝。
- Provider 参数、模型 ID 或 Base URL 变化都会进入 route revision；既有 consent 不能继续匹配。

## 安全边界

- Key 只通过本机设置页进入，使用 Windows DPAPI 持久化，接口和页面不回显。
- 模型目录检查是操作者触发的元数据调用，不执行推理、不读取 artifact。
- 不允许静默 local/cloud fallback 或跨供应商 fallback。
- 动态发现不能自动修改精确 bundle；变更须经过审核、版本化和重新授权。

工作区级规则：`%WORKSPACE_ROOT%\docs\agent-rules\multi-provider-api-integration.md`。
