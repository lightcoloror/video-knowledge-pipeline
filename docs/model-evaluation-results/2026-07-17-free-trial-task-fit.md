# VKP 免费/试用候选固定样本评测

## 2026-07-18 20:16:26 | Codex (GPT-5)

- Action: 从本地真实调用证据提取脱敏、可版本化的质量复核。
- Source run time: 2026-07-17。
- Review mode: 只读复核已保存证据；本次整理没有新增模型调用或上传。
- Status: 单固定样本筛选，不能自动晋升生产路由。

## 执行完整性

| 指标 | 结果 |
|---|---:|
| 尝试调用 | 27 |
| 成功 | 24 |
| 失败 | 3 |
| 外部重试 | 0 |
| fallback | 0 |
| 每候选调用次数 | 1 |
| 内部总预留上限 | USD 0.27 |
| 供应商报告实际费用 | unknown |

## 暂定任务选择

| 任务 | 暂定优胜 | 次选 | 主要依据 |
|---|---|---|---|
| 中文短音频 ASR | Groq `whisper-large-v3-turbo` | Groq `whisper-large-v3` | 归一化识别质量并列；Turbo 更快且标点更完整。 |
| 清晰 PPT OCR | Mistral `ocr-4.0` | Google Gemini Flash | 7/7 术语命中；页面/区块结构最完整，且本组延迟最低。 |
| PPT 版式视觉 | SiliconFlow `zai-org/GLM-4.5V` | Google Gemini Flash | 版式区域、图文关系与层次描述最完整。 |
| 非文字单帧语义 | Google Gemini Flash | SiliconFlow `zai-org/GLM-4.5V` | 非文字视觉元素更干净，未用 OCR 内容替代视觉判断。 |
| 双帧 temporal | Google Gemini Flash | SiliconFlow `zai-org/GLM-4.5V` | 稳定元素与讲师手势变化均被识别；速度暂不可比较。 |
| 证据提取 | Google Gemini Flash | Groq `qwen/qwen3.6-27b` | 唯一同时满足字段、冲突保留和 JSON 合同的可用候选。 |
| Smart Summary | Google Gemini Flash | ModelScope `ZhipuAI/GLM-5.2` | 核心概念完整、三要点结构稳定、没有思考过程泄漏。 |
| 转录纠错 | Google Gemini Flash | ModelScope `ZhipuAI/GLM-5.2` | 准确完成 `王飞` 到 `王菲` 的证据约束纠错，且延迟更低。 |

这些是筛选结论，不代表当前生产配置已经切换到对应模型。

## 全部调用状态

| # | 任务 | 供应商 / 模型 | 状态 | 延迟 ms | 备注 |
|---:|---|---|---|---:|---|
| 1 | ASR | Groq Whisper Large V3 Turbo | completed | 1663 | 质量通过 |
| 2 | ASR | Groq Whisper Large V3 | completed | 1884 | 质量通过 |
| 3 | ASR | Mistral Voxtral Mini | completed | 2341 | 质量通过 |
| 4 | PPT OCR | Mistral OCR 4.0 | completed | 827 | 7/7 术语；结构最佳 |
| 5 | PPT OCR | SiliconFlow PaddleOCR-VL-1.5 | completed | 1064 | OCR 候选 |
| 6 | PPT OCR | Google Gemini Flash | completed | 9820 | OCR 次选 |
| 7 | PPT 版式视觉 | Google Gemini Flash | completed | 5305 | 次选 |
| 8 | PPT 版式视觉 | SiliconFlow GLM-4.5V | completed | 24161 | 质量优胜 |
| 9 | PPT 版式视觉 | Groq Qwen3.6 | completed | 3315 | 有思考标签泄漏 |
| 10 | 单帧语义 | Google Gemini Flash | completed | 6046 | 质量优胜 |
| 11 | 单帧语义 | SiliconFlow GLM-4.5V | completed | 5286 | 次选 |
| 12 | 单帧语义 | Groq Qwen3.6 | completed | 3228 | 有思考标签泄漏 |
| 13 | temporal | Google Gemini Flash | completed | unavailable | 聚合器没有保留延迟 |
| 14 | temporal | SiliconFlow GLM-4.5V | completed | unavailable | 聚合器没有保留延迟 |
| 15 | temporal | Groq Qwen3.6 | completed | unavailable | 有思考标签泄漏；聚合器没有保留延迟 |
| 16 | 证据提取 | ModelScope DeepSeek V4 Pro | HTTP 429 | 842 | 免费层限流/拥挤，未进入质量比较 |
| 17 | 证据提取 | ModelScope GLM-5.2 | HTTP 429 | 852 | 免费层限流/拥挤，未进入质量比较 |
| 18 | 证据提取 | Groq Qwen3.6 | completed | 3946 | 内容可用，但有思考标签泄漏 |
| 19 | 证据提取 | Google Gemini Flash | completed | 4144 | 质量优胜 |
| 20 | 摘要 | ModelScope DeepSeek V4 Pro | completed | 5925 | 可用候选 |
| 21 | 摘要 | ModelScope GLM-5.2 | completed | 26335 | 次选 |
| 22 | 摘要 | Groq Qwen3.6 | completed | 4124 | 有思考标签泄漏 |
| 23 | 摘要 | Google Gemini Flash | completed | 4296 | 质量优胜 |
| 24 | 转录纠错 | ModelScope DeepSeek V4 Pro | HTTP 429 | 807 | 免费层限流/拥挤，未进入质量比较 |
| 25 | 转录纠错 | ModelScope GLM-5.2 | completed | 63506 | 次选 |
| 26 | 转录纠错 | Groq Qwen3.6 | completed | 3702 | 有思考标签泄漏 |
| 27 | 转录纠错 | Google Gemini Flash | completed | 7458 | 质量优胜 |

## 重要限制

1. Groq Qwen3.6 在六个结构化任务中均出现 `<think>` 标签或思考过程泄漏。这是结构化输出合同的硬失败；可以保留为候选，但在完成禁用思考、响应清洗和重新测评前不得自动用于生产写回。
2. ModelScope 的三次 HTTP 429 证明当时免费层可用性不足，不足以判定底层模型质量失败。
3. temporal 汇总器丢失延迟，不能用本轮结果排列 temporal 速度。
4. Markdown JSON fence、供应商包装 token 等属于可恢复格式问题，但必须经过统一 sanitizer 和 schema 验证。
5. 本轮每项只有一个样本；最终路由至少还需要多视频、多版式、多口音和失败恢复测试。
