# 多模态理解与 ASR 工具选型

Updated: 2026-06-04 11:16:00
Updated by: Codex (GPT-5)

## 背景

这次选型服务于“知识类视频全量转知识库”工具，不是普通视频摘要。

目标是尽量完整地抽取讲课、知识讲解、软件演示、板书、PPT、图表、公式、代码和屏幕状态中的信息。能可靠降维成文字的内容转成 Markdown/JSON；不能安全降维的视觉信息保留截图、时间戳和证据路径。

当前本地实现已经具备：

- 视频帧抽取、画面路由、图文截图解析、WebUI bundle、MCP/CLI 基础接口。
- `ebook_markdown_pipeline` 可作为图文型截图解析分支，处理 OCR、版面、表格、公式、文档页。
- 非图文视觉理解和高质量中文 ASR 仍需要接入更合适的工具。

## 分类结论

### 当前落地决策

- OCR / 图文截图解析统一走 `run_visual_structure_plan`，由它复用 `ebook_markdown_pipeline` 的 MCP 流程：`process_material -> get_job_status -> read_artifact`。
- `run_ocr_backfill` 只保留为备用导入/CaptiOCR/Tesseract fallback，不再作为屏幕文字缺口的默认下一步。
- ASR 仍按本页既有搜索结果优先接本地 SenseVoice / FunASR，`faster-whisper` 和 WhisperX 作为保底或精细时间戳补充。
- 多模态仍按本页既有搜索结果优先用 Gemini 2.5 Flash / OpenAI-compatible Vision API 试跑；Agnes AI 只在确认支持图像理解、多图输入和稳定 JSON 后接入。

### 多模态视觉理解工具

| 工具 | 类型 | 费用状态 | 开源 | 适合能力 | 在本项目中的角色 |
|---|---|---|---|---|---|
| OpenAI GPT-5.x / GPT-4.1 / GPT-4o Vision API | API | 收费 | 否 | 单帧、多帧视觉理解，复杂画面描述，软件界面状态、对象、动作、空间关系 | 高质量 `semantic_frame` 与 `temporal_sequence` 分支 |
| Gemini 2.5 Flash / Pro | API | 有免费额度，超额收费 | 否 | 图像和视频理解，长上下文，试错成本低 | 第一批试用的云端多模态模型 |
| Agnes AI Flash 系列 | OpenAI-compatible API | 公开报道称 2026-06-01 起文本、图像、视频 API 无限期免费；具体限速/稳定性需实测 | 否 | 文本模型、图像生成/编辑、视频生成；是否适合视频帧理解需实测 | 免费 API 候选，可优先放入 OpenAI-compatible provider 试跑 |
| Twelve Labs | 视频理解 API | 有免费计划，超额收费 | 否 | 整视频索引、视频搜索、视频问答、章节理解 | 可作为整视频理解/检索基线，不替代本地证据链 |
| Google Cloud Video Intelligence | API | 有免费额度或试用额度，超额收费 | 否 | 视频 OCR、标签、shot、object tracking、语音转写 | 视频元数据补充，不适合直接生成课程知识库 |
| Azure AI Video Indexer | API/商业服务 | 有试用额度，正式收费 | 否 | 视频索引、字幕、关键词、OCR、人物/主题识别 | 商业视频索引参考方案 |
| Qwen2.5-VL / Qwen-VL | 本地/开源模型 | 模型免费，自行承担硬件成本 | 是 | 中文视觉理解、OCR 辅助、图表/界面理解 | 后续本地化多模态候选 |
| InternVL | 本地/开源模型 | 模型免费，自行承担硬件成本 | 是 | 多模态图像理解，较强视觉问答 | 后续本地化多模态候选 |
| LLaVA-OneVision | 本地/开源模型 | 模型免费，自行承担硬件成本 | 是 | 图像/视频帧组理解，研究和实验生态较多 | 后续本地化多模态候选 |

### ASR 工具

| 工具 | 类型 | 费用状态 | 开源 | 适合能力 | 在本项目中的角色 |
|---|---|---|---|---|---|
| FunASR / Paraformer | 本地模型 | 免费，自行承担算力 | 是 | 中文 ASR、长音频、标点、热词、时间戳 | 中文讲课视频优先候选 |
| SenseVoice | 本地模型 | 免费，自行承担算力 | 是 | 中文/多语种 ASR，音频事件、情绪等辅助标签 | 中文 ASR 优先候选，尤其适合本地试装 |
| faster-whisper | 本地模型 | 免费，自行承担算力 | 是 | 稳定、轻量、部署成熟，支持多种 Whisper 模型 | 当前项目已有模块可用，适合作为保底 ASR |
| WhisperX | 本地工具 | 免费，自行承担算力 | 是 | Whisper 转写、word-level alignment、说话人分离 | 需要细粒度时间戳时接入 |
| OpenAI Whisper / Audio API | API | 收费 | 否 | 高可用 ASR，免本地依赖 | 快速试用或本地模型不可用时 |
| Deepgram | API | 有免费额度或试用额度，正式收费 | 否 | 实时/批量 ASR、diarization、关键词、摘要等 | 云端 ASR 备选 |
| AssemblyAI | API | 有免费额度或试用额度，正式收费 | 否 | 转写、章节、摘要、实体、说话人分离 | 云端 ASR 备选 |
| Google Cloud Speech-to-Text | API | 有免费额度，正式收费 | 否 | 多语种、企业级稳定性 | 云端 ASR 备选 |
| Azure AI Speech | API | 有免费月额度，正式收费 | 否 | 多语种、企业集成、实时和批量 | 云端 ASR 备选 |
| Amazon Transcribe | API | 12 个月免费层，正式收费 | 否 | 云端转写、说话人、批处理 | 云端 ASR 备选 |

## 推荐接入顺序

### 1. ASR 优先补本地中文能力

优先级：

1. SenseVoice
2. FunASR / Paraformer
3. faster-whisper
4. WhisperX

原因：

- 讲课视频的信息密度首先来自语音，ASR 错误会直接污染时间轴融合。
- 中文知识类视频优先考虑 SenseVoice/FunASR，比只靠 Whisper tiny/base 更稳。
- WhisperX 适合在需要字词级时间戳、语义关键点对齐关键帧时再接入。

本机当前状态：

- `faster_whisper` Python module 可用，但 CLI runner 不完整。
- `funasr`、`sensevoice`、`whisperx` 当前未安装或不可运行。
- 下一步应先把 SenseVoice 或 FunASR 接成 `asr_runner`，输出统一 transcript JSON。

### 2. 多模态先用 API 跑通真实效果

优先级：

1. Gemini 2.5 Flash
2. Agnes AI Flash 系列
3. OpenAI-compatible Vision API
4. Twelve Labs
5. 本地 Qwen2.5-VL / InternVL / LLaVA-OneVision

原因：

- 本项目第一版不需要立刻安装本地视觉大模型。
- API 能更快验证 `semantic_frame` 和 `temporal_sequence` 的提示词、字段结构、人工复核体验。
- Agnes AI 如果 OpenAI-compatible 接口稳定，理论上只需要修改 `base_url`、`api_key`、`model` 就能接入现有多模态分析器；但它公开案例更偏生成能力，必须用真实讲课截图和连续帧组验证“理解能力”。
- 真实需求是“看懂视频中的非文字信息”，不是只 OCR 截图。
- 本地模型适合等流程稳定后再替换，避免一开始卡在显存、驱动和推理服务部署上。

### Agnes AI 的当前判断

公开报道称 Agnes AI 于 2026-06-01 起将三类核心模型 API 无限期免费开放：

- 文本模型：`Agnes-2.0-Flash`
- 图像模型：`Agnes-Image-2.0-Flash`
- 视频模型：`Agnes-Video-2.0`

报道中提到的接入信息：

- API 平台：`platform.agnes-ai.com`
- OpenAI-compatible base URL：`https://apihub.agnes-ai.com/v1`
- 文本模型示例名称：`agnes-2.0-flash`

对本项目的意义：

- 它是低成本试跑 `multimodal_frame_analyzer` 的新候选。
- 如果支持图像输入到 chat/completions，可直接用于单帧画面理解。
- 如果支持多图输入，可用于 5-12 帧连续变化分析。
- 如果只支持图像/视频生成而不支持视觉理解，则不适合作为本项目的视频理解模型。

接入前必须验证：

- 是否无需绑卡、是否真的无试用期。
- QPS、TPM、RPM、单日上限、并发限制。
- 是否支持上传本地图片或 base64 image input。
- 是否支持多图输入和稳定 JSON 输出。
- 中文讲课截图、软件界面、图表、板书的理解质量。
- 免费服务在批量视频处理时是否稳定。

### Agnes AI 接入方式

本项目当前的 `vision_api.py` 已经按 OpenAI Chat Completions 兼容格式发送视觉请求：

- endpoint：`POST <base_url>`
- body：`model`、`messages`
- 图像输入：`messages[].content[]` 中的 `{"type": "image_url", "image_url": {"url": "data:image/..."}}`
- 鉴权：`Authorization: Bearer <api_key>`

Agnes 文档中 `agnes-1.5-flash` 页面明确给出了同形态的 `image_url` 多模态请求示例，并标注兼容 OpenAI Chat Completions API。因此最小接入方式是只配置环境变量：

```powershell
$env:LECTURE_VISION_PROVIDER = "agnes"
$env:LECTURE_VISION_BASE_URL = "https://apihub.agnes-ai.com/v1"
$env:LECTURE_VISION_API_KEY = "<AGNES_API_KEY>"
$env:LECTURE_VISION_MODEL = "agnes-1.5-flash"
$env:LECTURE_VISION_TIMEOUT_SECONDS = "90"
```

如果平台确认 `agnes-2.0-flash` 支持图像输入，也可以把模型换成：

```powershell
$env:LECTURE_VISION_MODEL = "agnes-2.0-flash"
```

不要把 API key 写入项目文件、MCP args、manifest 或 Obsidian 文档。

对当前真实测试 bundle，可以先预览候选：

```powershell
cd %WORKSPACE_ROOT%\video-knowledge-pipeline
.\scripts\video-knowledge.ps1 run-multimodal-frame-analysis `
  %WORKSPACE_ROOT%\video-knowledge-pipeline\real-tests\feishu-video-retry-optimized\webui-bundle
```

确认候选没问题后再执行单帧视觉理解：

```powershell
.\scripts\video-knowledge.ps1 run-multimodal-frame-analysis `
  %WORKSPACE_ROOT%\video-knowledge-pipeline\real-tests\feishu-video-retry-optimized\webui-bundle `
  --execute
```

连续变化分支要先生成真实帧组：

```powershell
.\scripts\video-knowledge.ps1 run-temporal-frame-groups `
  %WORKSPACE_ROOT%\video-knowledge-pipeline\real-tests\feishu-video-retry-optimized\webui-bundle `
  --execute `
  --frame-count 8
```

再执行 5-12 帧连续理解：

```powershell
.\scripts\video-knowledge.ps1 run-temporal-visual-analysis `
  %WORKSPACE_ROOT%\video-knowledge-pipeline\real-tests\feishu-video-retry-optimized\webui-bundle `
  --execute `
  --frame-count 8
```

MCP 调用时，仍然使用同一套工具：

```text
run_multimodal_frame_analysis
run_temporal_frame_groups
run_temporal_visual_analysis
```

并在启动 MCP server 的进程环境里设置：

```powershell
$env:LECTURE_VISION_PROVIDER = "agnes"
$env:LECTURE_VISION_BASE_URL = "https://apihub.agnes-ai.com/v1"
$env:LECTURE_VISION_API_KEY = "<AGNES_API_KEY>"
$env:LECTURE_VISION_MODEL = "agnes-1.5-flash"
%WORKSPACE_ROOT%\video-knowledge-pipeline\scripts\start-mcp.cmd
```

接入测试顺序：

1. 先用一张截图测试 `run_multimodal_frame_analysis --execute`，看 Agnes 是否接受 base64 data URL。
2. 再用 5-8 张连续帧测试 `run_temporal_visual_analysis --execute`，看是否支持多图输入。
3. 如果返回不是 JSON，先调整 prompt 或增加 JSON repair，不要直接污染 timeline。
4. 如果 `agnes-2.0-flash` 不支持图像输入，降级用文档明确支持图像的 `agnes-1.5-flash`。
5. 如果 Agnes 只能做图像/视频生成而不能做图像理解，则不接入本项目的视频理解分支。

### 3. Twelve Labs 适合作为整视频对照组

Twelve Labs 的定位更像“视频搜索、视频问答、视频索引平台”。它可能很适合回答：

- 这段视频哪里讲了某个概念？
- 哪些片段出现了某个视觉动作或主题？
- 整个视频有哪些章节？

但它不应该替代本项目自己的证据链，因为本项目需要：

- 保留逐帧/逐段证据路径。
- 保留图文型截图的 OCR/版面/表格/公式解析。
- 允许人工审核和标注。
- 输出 Obsidian/Markdown 可读资料。

## 与现有模块的对应关系

| 项目模块 | 推荐工具 | 说明 |
|---|---|---|
| `document_visual_parser` | `ebook_markdown_pipeline`，必要时 Mistral OCR/API OCR | 只处理 PPT、板书、表格、公式、代码、文档页截图 |
| `multimodal_frame_analyzer` | Gemini / OpenAI-compatible Vision / Qwen2.5-VL | 处理实物、界面状态、人物动作、空间关系、讲师指向 |
| `temporal_visual_analyzer` | Gemini / OpenAI-compatible Vision / LLaVA-OneVision | 处理 5-12 帧连续变化、软件操作、流程演示、实验过程 |
| `asr_runner` | SenseVoice / FunASR / faster-whisper / WhisperX | 处理中文讲课转写、时间戳、说话人或字词级对齐 |
| `timeline_fuser` | 项目自有代码 | 合并 ASR、OCR、结构化图文、多模态视觉理解 |
| `review_webui` | 项目自有 WebUI bundle | 人工检查遗漏、低置信度、截图保留理由 |

## 当前实现建议

短期不要大改 UI，也不要先追求本地大模型部署。建议按下面顺序推进：

1. 为 ASR runner 增加 SenseVoice/FunASR 接入，并保持 faster-whisper 作为 fallback。
2. 给 `run_multimodal_frame_analysis` 增加一套可配置 OpenAI-compatible provider 示例配置。
3. 用当前真实测试视频的 19 个时间段，先执行多模态单帧理解。
4. 对 `temporal_sequence` 路由生成的 5-12 帧帧组执行多帧理解。
5. 在 `note.md` 中追加“画面理解”和“连续变化理解”区块，保留所有截图证据。
6. 如果 API 成本或隐私成为主要问题，再开始本地 Qwen2.5-VL/InternVL 的服务化接入。

## 费用与开源判断

### 免费/开源但需要本机算力

- FunASR
- SenseVoice
- faster-whisper
- WhisperX
- Qwen2.5-VL / Qwen-VL
- InternVL
- LLaVA-OneVision

优点：本地可控、长期成本低、适合 agent 持续调用。

缺点：安装、显存、驱动、推理速度和模型质量需要实测。

### 有免费额度或试用额度

- Gemini API
- Agnes AI Flash 系列
- Twelve Labs
- Deepgram
- AssemblyAI
- Google Cloud Speech-to-Text
- Azure AI Speech
- Amazon Transcribe
- Google Cloud Video Intelligence
- Azure AI Video Indexer

优点：上线快、部署轻、质量通常稳定。

缺点：额度和价格会变化；长期批量处理需要成本控制；视频/音频上传有隐私边界。

### 完全商业/按量付费为主

- OpenAI Vision / Audio API
- 大多数云端 STT 和视频索引 API 的正式生产用量

优点：工程接入简单，质量上限高。

缺点：长期成本随视频时长、帧数、token 和调用次数增长。

## 评估标准

每个候选工具都应按同一批视频实测，而不是只看仓库介绍或产品文案。

多模态评估：

- 是否能看懂非文字视觉信息。
- 是否能描述界面状态、鼠标/操作、动作、空间关系。
- 是否能区分“可转文字”和“必须保留截图”的内容。
- 是否输出置信度、遗漏风险、证据帧路径。
- 是否能稳定处理 5-12 帧连续帧组。

ASR 评估：

- 中文识别准确率。
- 标点和分段质量。
- 时间戳粒度。
- 长视频稳定性。
- 噪声、口头禅、专有名词、英文混杂的表现。
- 是否容易接入 CLI/MCP。

## 参考链接

- [OpenAI API pricing](https://openai.com/api/pricing/)
- [Gemini API pricing](https://ai.google.dev/gemini-api/docs/pricing)
- [Agnes AI API documentation](https://agnes-ai.com/doc)
- [Agnes AI 全模态 API 免费开放报道 - 新浪科技/量子位](https://finance.sina.com.cn/tech/csj/2026-06-01/doc-inhzwist5375854.shtml?froms=ggmp)
- [Twelve Labs pricing](https://www.twelvelabs.io/pricing)
- [Deepgram pricing](https://deepgram.com/pricing)
- [Google Cloud Speech-to-Text pricing](https://cloud.google.com/speech-to-text/pricing)
- [Azure AI Speech pricing](https://azure.microsoft.com/en-us/pricing/details/speech/)
- [Amazon Transcribe pricing](https://aws.amazon.com/transcribe/pricing/)

## 决策摘要

当前最稳妥的路线是：

```text
本地 SenseVoice/FunASR 做中文 ASR
+ ebook_markdown_pipeline 处理图文型截图
+ Gemini / Agnes AI / OpenAI-compatible Vision API 处理非文字画面和连续帧组
+ video-knowledge-pipeline 自己做时间轴融合、人工复核、Obsidian/Markdown 输出、MCP
```

这条路线符合“优先复用现成工具，只写调度层和粘合层”的原则，同时不会再把 OCR/文档解析误当成真正的视频理解。
