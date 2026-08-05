# 火山 Coding Plan 与 SiliconFlow 同模型 OpenClaw 对比

更新时间：2026-07-18 11:30:55 +08:00
执行者：Codex / GPT-5

## 目标与公平性

比较五组两边均提供的同系列模型：DeepSeek V4 Pro、DeepSeek V4 Flash、GLM-5.2、Kimi K2.7 Code、Kimi K2.6。每组分别调用 Ark Coding Plan 与 SiliconFlow，共 10 个候选。

双方统一使用 OpenClaw、`openai-completions`、同一 1356 字节合成代码样本、同一提示、temperature 0、max tokens 1024、thinking off、工具全禁用、零外部重试、无 fallback。报告区分“同系列/同版本名称”与“供应商已证明同一底层权重”；后者若响应不返回可核验模型身份，不作推断。

## 官方调用契约

- 火山 Coding Plan：按[官方 OpenClaw 接入说明](https://developer.volcengine.com/articles/7615528054736945158)使用 `https://ark.cn-beijing.volces.com/api/coding/v3` 和 `openai-completions`。不得替换为标准计费的 `/api/v3`。本对比是受支持 AI coding tool 的固定代码任务，不把 Coding Plan 当成 VKP 通用摘要/视觉 API。
- SiliconFlow：按[OpenClaw/CC Switch 说明](https://docs.siliconflow.cn/cn/usercases/use-siliconcloud-in-ccswitch)和[Chat Completions 参考](https://docs.siliconflow.cn/en/api-reference/chat-completions/chat-completions)使用 `https://api.siliconflow.cn/v1` 的 `/v1/chat/completions`。

## 精确模型映射

| 系列 | Ark Coding Plan alias | SiliconFlow model ID |
| --- | --- | --- |
| DeepSeek V4 Pro | `deepseek-v4-pro` | `deepseek-ai/DeepSeek-V4-Pro` |
| DeepSeek V4 Flash | `deepseek-v4-flash` | `deepseek-ai/DeepSeek-V4-Flash` |
| GLM-5.2 | `glm-5.2` | `zai-org/GLM-5.2` |
| Kimi K2.7 Code | `kimi-k2.7-code` | `moonshotai/Kimi-K2.7-Code` |
| Kimi K2.6 | `kimi-k2.6` | `Pro/moonshotai/Kimi-K2.6` |

## 执行防护

- 每个候选单独 route revision、单 deployment、单 consent v2、最多一次调用、最多 0.02 美元。
- OpenClaw 使用隔离的 `OPENCLAW_CONFIG_PATH`、state 和 agent 目录；配置 `models.mode=replace`、空 fallbacks、`tools.deny=["*"]`。
- loopback audit proxy 只转发第一条精确模型请求；OpenClaw/SDK 后续重试只得到本地 400，不会再次到达供应商。
- 审计记录 request/response SHA、请求模型、供应商响应模型（若返回）、状态和 request id；不记录请求正文、Authorization 或 API Key。
- Runner 超时或异常后仍保存已发生的外部请求审计，并按未知费用调用结算 reservation。
- `execute-all` 严格按计划顺序串行执行并在每个候选后原子写入 `batch-execution.json`；已有精确结果只读复用，不会二次调用。某个供应商失败只记入该候选，不触发 retry/fallback，也不阻止其他独立候选。

## 当前状态

- 隔离 OpenClaw 配置验证：`valid=true`。
- 离线回归：57 passed（parity、Provider Catalog、Key-only onboarding、设置 UI）。
- 最新计划：`.local/coding-plan-siliconflow-parity-20260718/parity-plan.json`。
- Plan SHA-256：`dcf7fca0cbb6c7916b259195d0a54cd3768938ca04dd54db30433a9b5f986c5d`。
- 上传文件 SHA-256：`4844ae6b718c893d4ca2e05976d4534f4cb94e36cbe1c18a32221995fcac7336`。
- 十个候选的凭据引用元数据均 ready；未读取明文凭据。
- 尚未创建本轮 consent、未调用供应商、未上传文件；真实结果和差异结论待操作者精确授权后生成。

## 产物

- 操作者授权请求：`.local/coding-plan-siliconflow-parity-20260718/operator-authorization-request.md`
- 最终 JSON：`.local/coding-plan-siliconflow-parity-20260718/parity-comparison.json`
- 最终报告：`.local/coding-plan-siliconflow-parity-20260718/parity-comparison.md`
- 可恢复批量进度：`.local/coding-plan-siliconflow-parity-20260718/batch-execution.json`
