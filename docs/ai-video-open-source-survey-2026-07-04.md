# AI 视频总结/分析开源项目扩展调研

Update: 2026-07-04 20:00:00 | Codex / GPT-5

## 目的

本页回答两个问题：

1. 除了 `vsummary`、`PrideWood/bilinote`，VKP 之前还参考过哪些项目。
2. 扩大范围后，AI 视频总结、视频分析、长视频理解、视频问答方向有哪些开源项目值得继续拉源码分析。

结论先行：VKP 不应该变成某一个外部项目的壳。更稳的路线是继续保持现有 `ASR + 字幕/sidecar + 抽帧 + ebook/OCR + 多模态复核 + 时间线融合 + 人工审核 + 导出` 主架构，然后从外部项目里拆用局部能力。

## 已经本地拉过或参考过的项目

本地源码目录主要在：

```text
%WORKSPACE_ROOT%\tool-source-review
```

| 项目 | 本地状态 | 主要参考价值 | VKP 当前定位 |
|---|---:|---|---|
| `AI-Video-Transcriber` | 已拉源码 | faster-whisper 参数、转写工作流、简单 UI 参数面板 | ASR fallback 和 UI 控制台参考 |
| `BiliNote` | 已拉源码 | 视频笔记工作流、字幕/转写配置、总结配置、模型就绪门禁 | 已部分复用到 transcript/summary 工具层 |
| `PrideWood-bilinote` | 已拉源码 | 前后端分层、视频笔记 UI、whisper.cpp fallback、LLM 总结配置 | 已新增源码审查文档和局部工具复用 |
| `vsummary` | 已拉源码 | Windows CUDA/faster-whisper 经验、LLM provider 组织方式、任务状态 | 已复用为 `text_llm_gateway` 参考 |
| `peepshow` / `peepshow-npm` | 已拉源码/包 | 抽帧、去重、OCR、帧报告、tag/annotate、HTML report | 只作为可选 evidence extractor，不替代主流程 |
| `metanote` | 已拉源码 | FunASR/SenseVoice、Streamlit UI、多模态帧处理、note generation | 架构参考，不整体嵌入 |
| `lecture2notes` | 已拉源码 | 讲课视频到笔记的 pipeline 思路 | 架构参考 |
| `DeLive` | 已拉源码 | 直播/视频内容处理链路 | 架构参考 |
| `FunASR` | 已拉源码 | 中文 ASR、时间戳、VAD、标点、热词、speaker | 本地 ASR 主线 |
| `SenseVoice` | 已拉源码 | 中文/多语种 ASR，情绪、音频事件、`sentence_info` | 本地 ASR 主线 |
| `Qwen2.5-VL` | 已拉源码 | 本地 VLM、图像/视频帧组理解、中文视觉能力 | 通过 OpenAI-compatible adapter 接，不嵌主流程 |
| `InternVL` | 已拉源码 | 本地多模态、decord 读视频、多帧输入 | 本地 temporal frame group 候选 |
| `LLaVA-NeXT` | 已拉源码 | LLaVA-Video / OneVision / SGLang 部署线索 | 较重的本地 VLM 候选 |
| `marker` / `docling` / `captiocr` | 已拉源码 | 文档/OCR/版面解析 | 低层 OCR/文档解析候选，主 OCR 仍优先 ebook pipeline |

## 新一轮开源项目候选

| 项目 | 类型 | 关键能力 | 对 VKP 的价值 | 复用优先级 |
|---|---|---|---|---:|
| Video-LLaVA | 视频/图像统一 VLM | 图像和视频统一视觉表征；支持 CLI、Gradio、Transformers 示例；示例里均匀采样 8 帧 | 可参考视频帧组输入格式、本地 VLM adapter、短片段理解 | 中 |
| Video-ChatGPT | 视频对话模型 | 视频 conversation，结合 LLM 和时空视觉编码 | 适合参考 prompt、视频问答评估，不适合直接做生产主线 | 中低 |
| Ask-Anything / VideoChat | 视频聊天系统 | 视频理解 + 多 LM 支持 | 适合参考视频问答 demo 和交互方式 | 中低 |
| MovieChat | 长视频理解 | dense token 到 sparse memory，用 memory 处理长视频 | 对 5 小时课程最有启发：长视频记忆压缩、分段 summary、跨段回溯 | 高 |
| VTimeLLM | 视频时间定位/片段理解 | boundary-aware video LLM，面向 video moments、时间边界推理 | 很适合补 VKP 的“疑难点定位”“人工审核时间戳准确化”“问某个概念在哪讲” | 高 |
| LongVA | 长上下文视频助手 | 从语言长上下文迁移到视觉，面向长视频 | 可参考长视频多帧输入和长上下文压缩策略 | 中高 |
| LLaMA-VID | 长视频 token 压缩 | 用极少 token 表达图像/视频信息 | 可参考长视频视觉压缩，但接入成本偏高 | 中 |
| InternVideo / InternVideo2/3 | 视频 foundation model | 视频检索、分类、QA、长时序理解、agent 实现 | 更像底座/研究平台，直接复用重，但思路对长视频检索层有价值 | 中 |
| VideoRAG | 视频 RAG | “chat with your videos”，视频索引、检索、问答 | 适合 VKP 后续做“视频知识库检索/问答”层 | 高 |
| UniVTG / QD-DETR / CG-DETR | temporal grounding / highlight detection | moment retrieval、highlight detection | 可借鉴“根据查询找关键片段”，但不是完整总结工具 | 中 |
| Shot2Story | 视频故事/shot-level caption benchmark | 多镜头 caption 和 story summary | 可参考分镜级摘要评价，不一定直接复用 | 中低 |
| video-recap-skills | agent 视频解说/剪辑 | ASR/VLM/FFmpeg/解说脚本/剪辑 | 对内容资产候选、短视频脚本有参考价值 | 中 |
| WordPilot / ai-video-summarizer / SubtitleAI | 应用型视频总结 | 转写、摘要、博客/字幕/剪辑 | 多数偏“字幕摘要”，低于 VKP 目标；可参考 UI/导出 | 低 |

## 对 VKP 最值得吸收的模块

### 1. 长视频 memory summary

参考：MovieChat、LongVA、LLaMA-VID。

VKP 当前已经避免了长视频只覆盖前 10 分钟，但 `smart-summary` 还需要更强的全片分层压缩：

```text
完整 transcript / timeline
-> 固定时间窗 chunk
-> chunk summary
-> 跨 chunk 合并
-> 主题线索 / 方法论 / 行动清单
-> low-confidence / missing visual evidence 单独列出
```

优先做成 VKP 自己的 `smart_summary_codex` / LLM summarizer 流程，不直接嵌 MovieChat。

### 2. 时间定位和疑难点复核

参考：VTimeLLM、UniVTG、QD-DETR。

VKP 现有 `vision-review-triage` 可以继续升级：

```text
ASR / corrected transcript / OCR / ebook / tagger / route
-> 发现术语冲突、字幕疑似错词、屏幕文字缺失、操作演示缺口
-> 输出 query-like review target
-> 定位最相关时间窗
-> 只把疑难帧/短片段送多模态
```

这比“所有帧都送在线多模态”更适合用户的成本和隐私边界。

### 3. 视频 RAG / 可问答知识库

参考：VideoRAG、InternVideo。

VKP 现在主要产出 Markdown 和 review bundle。后续可加：

```text
timeline item
ASR segment
OCR/ebook text
visual_understanding
temporal_visual_understanding
evidence paths
```

统一切成可检索块，做本地索引。这样用户可以问：

- 这个视频哪里讲到某个工具？
- 某个术语到底应该是什么？
- 哪些地方出现了价格、流程、案例、结论？

### 4. 本地 VLM provider

参考：Qwen2.5-VL/Qwen3-VL、InternVL、LLaVA-NeXT、Video-LLaVA。

VKP 不应该导入这些模型仓库代码。更合适的做法：

```text
local VLM server
-> OpenAI-compatible / HTTP adapter
-> VKP provider layer
-> semantic_frame / temporal_sequence 调用
```

这样可以保持 CLI/MCP/UI 稳定，模型服务可以单独换。

## 不建议直接复用为主线的项目类型

| 类型 | 原因 |
|---|---|
| 只基于 YouTube 字幕的 summarizer | VKP 目标是全量知识提取，不只是字幕摘要 |
| 传统 video summarization / keyframe selection 学术代码 | 多数目标是选精彩片段，不是提取知识、课件、术语、公式、操作流程 |
| 重训练型视频 VLM 工程 | 对个人工具维护成本太高；除非只是部署现成 checkpoint |
| 整套 Web app | 会破坏 VKP 已成型的 timeline/evidence/review/export 数据结构；更适合吸收 UI 交互细节 |

## 下一步建议

按复用价值排序，下一批源码深挖建议是：

1. `MovieChat`：重点看长视频 sparse memory、分段压缩和最终总结生成。
2. `VTimeLLM`：重点看时间边界、moment grounding、query 到片段定位。
3. `VideoRAG`：重点看视频块索引、检索、问答的数据结构。
4. `Video-LLaVA`：重点看本地视频帧组输入和 provider 封装。
5. `video-recap-skills`：重点看内容资产/短视频脚本/剪辑候选，不进入知识提取主线。

这些项目进入 VKP 时应遵守三条线：

- 只拿局部模块或设计，不整体搬家。
- 重模型统一走 provider/adapter。
- 输出仍回到 VKP 的 timeline、evidence、review、Markdown 三层产物。

## Sources

- Video-LLaVA: https://github.com/PKU-YuanGroup/Video-LLaVA
- Video-ChatGPT: https://github.com/mbzuai-oryx/Video-ChatGPT
- Ask-Anything / VideoChat: https://github.com/OpenGVLab/Ask-Anything
- MovieChat: https://github.com/wenhaochai/MovieChat
- VTimeLLM: https://github.com/huangb23/VTimeLLM
- LongVA: https://github.com/EvolvingLMMs-Lab/LongVA
- LLaMA-VID: https://github.com/JIA-Lab-research/LLaMA-VID
- InternVideo: https://github.com/OpenGVLab/InternVideo
- InternVL: https://github.com/OpenGVLab/InternVL
- Qwen-VL: https://github.com/QwenLM/Qwen3-VL
- LLaVA-NeXT: https://github.com/LLaVA-VL/LLaVA-NeXT
- VideoRAG: https://github.com/HKUDS/VideoRAG
- GitHub video-summarization topic: https://github.com/topics/video-summarization
