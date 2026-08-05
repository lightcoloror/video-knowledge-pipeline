# Ark 与 SiliconFlow 同模型对比基线

更新时间：2026-07-18 09:12:00
执行工具：Codex / GPT-5

## 结论

VKP 的摘要、转录纠错和其他视频知识任务属于通用模型推理。火山方舟侧必须使用标准模型 API `https://ark.cn-beijing.volces.com/api/v3`，不得使用只面向受支持 AI 编程工具的 Coding Plan `/api/coding/v3`。

凭据引用只允许在完全相同的 `(provider, normalized base_url)` 内复用。Coding Plan 与标准 Ark API 即使主机名相同，也必须分别保存凭据；VKP 不读取、复制或解密旧凭据来跨边界迁移。

## 可公平比较的精确模型

| 模型组 | Ark 标准 API 模型 | SiliconFlow 模型 |
|---|---|---|
| DeepSeek V4 Pro | `deepseek-v4-pro-260425` | `deepseek-ai/DeepSeek-V4-Pro` |
| DeepSeek V4 Flash | `deepseek-v4-flash-260425` | `deepseek-ai/DeepSeek-V4-Flash` |
| GLM-5.2 | `glm-5-2-260617` | `zai-org/GLM-5.2` |

Kimi K2.7 Code、Kimi K2.6、Kimi K3 目前只核实到 Coding Plan 别名，没有得到同版本标准 Ark API 的精确模型 ID，因此不进入本轮通用 API 公平对比。

## 固定套件

- 计划：`.local/provider-parity-20260717/fixed-parity-plan-v5.json`
- 计划 SHA-256：`64daad9ce95c763bffea4ae75dd662c46d2f3047d7da852bb2f600b884125b76`
- Prepared suite：`.local/provider-parity-20260717/prepared-8776-v5/prepared-suite.json`
- Prepared suite SHA-256：`7d82ec80b6d84329d72e03eb9b28f7300ad4c29388181abd9aedd954a68a53b4`
- 固定输入：`.local/model-candidate-benchmark-20260717/fixed-text-evidence.txt`
- 输入大小：442 字节
- 输入 SHA-256：`ff23e510b7c797a89377de52976f3135532f422a3e89245b88ddd8b78b00888e`
- 任务：摘要、转录纠错
- 候选数：12（3 个模型组 × 2 个供应商 × 2 类任务）
- 限制：每个候选最多 1 次、零重试、无 fallback、总预留上限 0.12 美元

旧 V3 套件使用 Coding Plan，已标记为 `superseded_coding_plan_not_general_api`；V4 同时向两家发送 `response_format`，但该字段未出现在方舟通用 ChatCompletions 官方参数页，因此 V5 改为两家共同的最小官方字段并由相同提示词与本地契约校验 JSON。旧套件均不得执行。

## 当前状态

- SiliconFlow 三条精确比较 profile 的 DPAPI 凭据项已保存。
- Ark 标准模型 API 三条 profile 已由 `ark_model_api` bundle 安全导入，但当前只是悬空的 `secret_ref`：对应 DPAPI 密文项不存在，因此凭据尚未保存。其引用与 Coding Plan 引用完全不同，禁止跨边界复制或复用。
- 凭据状态修复现在只读取加密凭据文档的 ID 元数据，不解密、不返回密钥值；悬空引用不会再被误报为可复用凭据。
- 导入与状态核验没有改变任务路由、没有联网、没有解密 secret，也不构成外发授权。
- V5 已完成离线准备和 12/12 preview；12 个 route revision 均重新生成，真实调用数仍为 0。
- 操作者已于 2026-07-18 明确授权该精确 artifact、两项目的地、六个模型、12 次调用与 0.12 美元上限；V5 只删除未获方舟通用文档支持的可选请求字段，未改变任何已授权的外发范围。
- 真实执行当前只剩一个阻断项：在本机设置页为 `ark_model_api` 保存一次标准 Ark `/api/v3` API Key；不得使用 Coding Plan Key 代替。

## 官方依据

- [方舟 ChatCompletions API 参数](https://api.volcengine.com/api-docs/view?action=ChatCompletions&serviceCode=ark&version=2024-01-01)：官方端点为 `POST https://ark.cn-beijing.volces.com/api/v3/chat/completions`，使用 Bearer API Key；通用字段包含 `model`、`messages`、`max_tokens`，响应回传实际 `model` 与 `usage`。
- [方舟标准模型 API 快速开始](https://www.volcengine.com/docs/82379/1795150)
- [火山方舟 Coding Plan](https://www.volcengine.com/activity/codingplan)
- [SiliconFlow Chat Completions](https://docs.siliconflow.cn/cn/api-reference/chat-completions/chat-completions)：官方端点为 `POST https://api.siliconflow.cn/v1/chat/completions`，使用 Bearer API Key，并回传 `model`、`reasoning_content` 与 `usage`。
- [SiliconFlow 模型列表](https://docs.siliconflow.cn/cn/api-reference/models/get-model-list)：官方目录端点为 `GET https://api.siliconflow.cn/v1/models`。

SiliconFlow 文档显式列出 `response_format`；方舟通用 ChatCompletions 参数页未把它列为公共字段。为避免协议差异污染模型质量对比，V5 不向任一上游发送该字段，仍以相同中文 JSON 指令和本地输出契约检查结构。SiliconFlow 的 `reasoning_effort` 仅明确适用于 DeepSeek V4 Flash 且只接受 `high`/`max`；本轮不发送该供应商特有参数。

## 安全边界

- 保存配置不等于授权外发。
- Secure MCP Tunnel 只能访问 Broker，不能扩大供应商目的地。
- 所有联网执行仍由 allowlist、consent v2、精确 artifact hash、route revision、原子调用/费用预留共同约束。
- 禁止静默 local/cloud fallback、跨供应商 fallback、未列明文件上传和自动发布。
## 2026-07-23 Policy Correction

- 2026-07-23 20:53:37 +08:00 | Codex (GPT-5)
- The 2026-07-18 Coding Plan task-scope denial is superseded. VKP must not reject a configured Coding Plan route merely because the request is a video-knowledge task. Each request stays bound to its exact route, provider/model, artifact manifest, destination allowlist, user consent, call/expense limits, and expiry; provider-side unsupported-capability or quota responses are reported as such. Standard Ark /api/v3 and Coding Plan /api/coding/v3 remain distinct endpoints and credentials, with no silent substitution.