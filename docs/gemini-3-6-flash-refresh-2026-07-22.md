# VKP Google Gemini 3.6 Flash / 3.5 Flash-Lite 路由更新

更新：2026-07-22 11:05:45 +08:00
执行：Codex / GPT-5.6

## 官方结论

- `gemini-3.6-flash` 是 GA 生产模型，适合复杂指令、多模态、时空推理和需要较高质量的长上下文任务。
- `gemini-3.5-flash-lite` 是 GA 生产模型，优先面向低成本、高吞吐解析、文档抽取和结构化 JSON。
- 两者均支持文本、图片、视频、音频和 PDF 输入，文本输出；上下文为 1M，最大输出为 64K。
- 新型号不再接受旧采样字段 `temperature`、`top_p`、`top_k`，并以 `thinking_level` 取代 `thinking_budget`。VKP 当前依赖各模型默认思考级别，不自行发明额外字段。

权威来源：

- https://ai.google.dev/gemini-api/docs/latest-model
- https://ai.google.dev/gemini-api/docs/models/gemini-3.6-flash
- https://ai.google.dev/gemini-api/docs/models/gemini-3.5-flash-lite
- https://ai.google.dev/gemini-api/docs/pricing

## VKP 路由决策

| VKP 任务 | 默认模型 | 理由 |
|---|---|---|
| `temporal_sequence` | `gemini-3.6-flash` | 复杂跨帧变化与时空推理 |
| `video_segment` | `gemini-3.6-flash` | 短视频片段的过程和状态理解 |
| `text_llm` | `gemini-3.6-flash` | 生产质量优先的证据综合 |
| `summary_rewrite` | `gemini-3.6-flash` | 章节与全局摘要质量优先 |
| `transcript_correction` | `gemini-3.6-flash` | 纠错需严格遵循证据与 Schema |
| 低成本结构化抽取候选 | `gemini-3.5-flash-lite` | 仅作为可选 profile，暂不替换复杂生产任务 |

ASR 继续使用既有 Groq 路线，OCR 继续使用既有 Mistral/SiliconFlow/本地 ebook 路线；本次不把通用 Gemini 模型静默替换为专用 ASR/OCR。

## 安全与兼容性

- Google API Key 沿用同 provider、同 Base URL 的本地 DPAPI 引用；不读取、不显示、不重写密钥明文。
- 保存新 profile 与切换 route 不等于授权外发。
- model ID 变化会产生新的内容寻址 route revision；旧 consent v2 不得用于新路线。
- 本次仅做本地配置与离线测试，不调用 Google API，不上传视频帧、音频或文档。
- `gemini-3.5-flash` 旧 profile 与既有执行证据保留，便于审计和显式回滚；不自动删除。
