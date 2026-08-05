# 所有 ASR/字幕疑似错词的通用语义纠错闭环目标详述

更新时间：2026-07-07 00:00:00
执行者：Codex / GPT-5
项目：`video-knowledge-pipeline`

## 1. 目标定义

这个目标不是做一个“术语词典”，也不是简单润色字幕，而是给 VKP 增加一条 **所有 ASR/字幕疑似错词的通用语义纠错闭环**。

核心目标：

> 只要 ASR、平台字幕、自带字幕、导入字幕中的某个词、数字、动作、专名、断句或表达，能被 OCR/ebook、画面、多模态、网页简介、打标器、上下文或人工标注证明“可能错了”，就进入候选；只要多源证据能高置信证明“应该改成什么”，就写入纠正版 transcript；纠正版 transcript 必须真实影响最终人类可读文件。

完成标准不是生成一个候选文件，也不是输出一份 LLM 建议，而是：

```text
已确认的 ASR/字幕错词，不再残留在 full-transcript.md、smart-summary.md、knowledge-note.md、content-material-card 和下游 handoff 中。
```

## 2. 为什么这是独立目标

VKP 当前已经有 ASR、OCR/ebook、多模态、timeline、人工审核、智能总结等模块。但如果 ASR 或字幕里的错词没有被统一纠正，后续所有模块都会被污染。

典型污染链路：

```text
ASR 错词
  -> timeline transcript 错
  -> full-transcript.md 错
  -> smart-summary.md 主题抽取错
  -> 行动清单/内容素材卡错
  -> 搜索/RAG/复习时找不到真实概念
```

因此这条闭环是“最终人类可读输出质量”的上游质量门。

术语仲裁只是其中一个子集。真正目标要覆盖：

- 工具名、产品名、平台名；
- 人名、公司名、品牌名、课程名；
- 行业术语、课程概念；
- 数字、金额、比例、年份、步骤编号；
- 动作词、操作步骤、流程词；
- 普通同音错词、近音错词、语义不通词；
- 标点、断句、段落边界；
- 平台字幕或自带字幕本身的错误。

## 3. 原则

### 3.1 第一轮证据相互独立

ASR、字幕、OCR/ebook、多模态、网页元数据、打标器、人工标注都要先独立产出证据。不能在第一轮就让其中一路覆盖另一路。

正确方式：

```text
独立证据生成
  -> 统一 evidence pack
  -> 候选发现
  -> Codex/LLM/人工语义判断
  -> validate
  -> closure 写入纠正版 transcript
  -> export 刷新
  -> impact report 证明最终文件受影响
```

### 3.2 原始证据不可覆盖

不能直接改：

- 原始 ASR 输出；
- 平台字幕原文件；
- 自带字幕原文件；
- OCR/ebook 原始结果；
- 多模态原始结果；
- 原始视频和抽帧证据。

只能写派生产物：

- `source-arbitrated-transcript.json`
- `source-arbitrated-transcript.srt`
- `transcript-semantic-correction-*.json/md`
- `exports/full-transcript.md`
- `exports/smart-summary.md`
- `exports/knowledge-note.md`
- impact report、audit、review pack。

### 3.3 高置信自动写入，低置信不阻塞

人工复核是可选项，不应阻塞整个视频处理。

策略：

- 高置信、低风险：可自动写入纠正版 transcript。
- 高置信但高风险：可写入，但必须留下 audit 和 impact 记录。
- 低置信或证据冲突：进入 review pack / known gaps，不写入最终结论。
- 已 accepted_with_known_gaps 的视频仍可交付，但必须列出剩余风险。

### 3.4 Codex/LLM 只能仲裁，不能自由改稿

Codex 或在线 LLM 的职责是判断 evidence pack 里的候选，不是自由重写整篇 transcript。

任何自动纠正必须满足：

- 有 candidate id；
- 有原文；
- 有建议改法；
- 有证据 id；
- 有置信度；
- 有风险类型；
- 有 final output policy；
- 能通过本地 validate。

## 4. 输入证据

| 证据源 | 代表产物 | 用途 |
| --- | --- | --- |
| 本地 ASR | `normalized-transcript.json`、`normalized-transcript.srt` | 原始听写文本、时间戳、置信信息。 |
| 平台字幕 | platform subtitle sidecar | 与本地 ASR 对比，发现不一致。 |
| 自带字幕 | embedded/external subtitle sidecar | 可能更准，也可能同样来自 ASR。 |
| OCR/ebook | `visual_text`、`structured_visual`、ebook pipeline 输出 | 屏幕文字、PPT、代码、表格、数字、工具名。 |
| 多模态单帧 | `visual_understanding` | 非文字画面、界面状态、物体、空间关系。 |
| 多帧/短片段 | `temporal_visual_understanding` | 操作链、状态变化、演示过程。 |
| 网页标题/简介 | VDO handoff、page metadata | 视频标题、课程名、人名、品牌名、主题词。 |
| 打标器/timeline | tags、chapter、route、quality issues | 重点、疑难、工具名、步骤、案例、结论。 |
| 全片上下文 | chapter pack、long-video memory、smart-summary input | 判断局部词是否符合全片主线。 |
| 人工标注 | review notes、sample review | 最高优先级确认来源。 |

## 5. 候选发现

### 5.1 多源文本冲突

不同来源对同一时间段、同一实体、同一数字给出不同写法时，生成候选。

例：

```text
ASR: play right m c p
OCR/ebook: Playwright MCP
上下文: 浏览器自动化工具横评
候选: play right m c p -> Playwright MCP
```

### 5.2 画面强证据

屏幕、课件、代码、表格或软件界面出现明确文字，而 ASR 识别成音近词、碎片词或无意义词。

例：

```text
ASR: browser base
OCR/ebook: Browserbase
候选: browser base -> Browserbase
```

### 5.3 全片语义不通

某个词单看不一定错，但放到全片主题里明显不通顺，也要进入候选。

触发信号：

- 句子结构断裂；
- 同一概念多次出现不同写法；
- 关键词与视频主题不匹配；
- 章节标题附近出现孤立无意义词；
- 智能总结出现关键词拼接式病句；
- 行动清单出现不可执行动作词。

### 5.4 数字/金额/时间高风险

数字类错误对知识视频伤害很大，默认高风险。

候选类型包括：

- 工资、价格、收益、金额；
- 年份、日期、时长；
- 比例、倍数、排名；
- 步骤编号、章节编号；
- 客户数、播放量、转化率。

数字类不能只靠“模型觉得更合理”自动改。自动写入至少需要：

- OCR/ebook 清楚识别；
- 或标题/简介和上下文一致；
- 或两个以上独立来源一致；
- 或人工确认。

### 5.5 动作和步骤

教程/课程里，动作词会直接影响行动清单。

例：

```text
ASR: 然后点这个进去
视觉: 页面按钮是 Create Session
候选: 补全为 点击 “Create Session” 进入下一步
```

这类属于语义纠正/补全，风险高于简单替换。默认需要强视觉证据或人工确认。

### 5.6 重复实体变体

同一实体在全片里可能出现多个变体：

```text
Browserbase / browser base / browse base / browser bus
```

应该合并成 candidate group，统一判断 canonical，再分别写回多个 segment。否则会出现前面改对、后面仍错的问题。

## 6. Candidate Group

候选不能只按单条 segment 孤立处理。系统应生成 `candidate_groups`：

```json
{
  "group_id": "semgroup-0001",
  "canonical_hint": "Browserbase",
  "variant_texts": ["browser base", "browse base", "browser bus"],
  "candidate_ids": ["semcorr-0001", "semcorr-0007"],
  "correction_types": ["proper_noun", "term", "action"],
  "evidence_summary": {
    "ocr_ebook": 3,
    "asr": 6,
    "page_metadata": 1,
    "human_note": 0
  }
}
```

用途：

- 全片统一专名写法；
- 避免同一实体重复仲裁；
- 支持批量 apply；
- 支持 UI 按 group 审核；
- 支持跨视频 glossary 积累。

## 7. Evidence Pack Schema

建议核心产物：

```text
transcript-semantic-correction-pack.json
transcript-semantic-correction-pack.md
transcript-semantic-correction-prompt.md
transcript-semantic-correction-result.template.json
transcript-semantic-correction-result.codex.md
```

候选最小结构：

```json
{
  "candidate_id": "semcorr-0001",
  "candidate_group_id": "semgroup-0001",
  "correction_type": "term",
  "risk_level": "safe_auto_apply",
  "time_range": {"start": 123.4, "end": 130.2},
  "timeline_indexes": [12],
  "original_text": "play right m c p",
  "suggested_text": "Playwright MCP",
  "canonical_hint": "Playwright MCP",
  "context_before": "...",
  "context_after": "...",
  "why_this_is_suspicious": "ASR text is phonetically similar to a tool name shown on screen.",
  "evidence": [
    {
      "evidence_id": "ev-001",
      "source_type": "ocr_ebook",
      "text": "Playwright MCP",
      "path": "visual-structure/...",
      "timeline_index": 12,
      "confidence": 0.92
    }
  ],
  "conflicts": [
    {"source_type": "asr", "text": "play right m c p"},
    {"source_type": "ocr_ebook", "text": "Playwright MCP"}
  ],
  "final_output_impact": ["full_transcript", "smart_summary", "content_candidate_pack"]
}
```

## 8. Codex/LLM 判读结果 Schema

Codex 暂时代替在线 LLM 时，输出也必须结构化。

```json
{
  "schema": "video_knowledge_pipeline.transcript_semantic_correction_result.v1",
  "source": "codex_substitute_for_online_llm",
  "decisions": [
    {
      "candidate_id": "semcorr-0001",
      "action": "replace",
      "correction_type": "term",
      "original_text": "play right m c p",
      "corrected_text": "Playwright MCP",
      "canonical": "Playwright MCP",
      "aliases": ["play right m c p", "playright m c p"],
      "confidence": 0.96,
      "safe_to_apply": true,
      "needs_human_review": false,
      "semantic_rationale": "OCR and nearby discussion both refer to the browser automation tool Playwright MCP.",
      "evidence_ids": ["ev-001"],
      "timeline_indexes": [12],
      "final_output_policy": "apply_to_corrected_transcript_and_summary"
    }
  ]
}
```

允许动作：

| action | 含义 |
| --- | --- |
| `replace` | 用 corrected_text 替换原文。 |
| `keep_original` | 保留原文，候选不成立。 |
| `needs_human_review` | 证据不足或风险高，交给人工。 |
| `reject` | 建议无证据、schema 错或越权。 |

## 9. 校验规则

`validate-transcript-semantic-correction` 必须拒绝以下结果：

| 拒绝原因 | 说明 |
| --- | --- |
| `unknown_candidate_id` | decision 引用了 pack 中不存在的候选。 |
| `missing_evidence` | replace 没有 evidence id。 |
| `unsafe_number_change` | 数字类修改没有强证据或人工确认。 |
| `low_confidence_auto_apply` | 低置信却要求自动写入。 |
| `free_rewrite_detected` | LLM 自由重写了候选之外的内容。 |
| `original_text_mismatch` | 原文与 source transcript 不匹配。 |
| `empty_corrected_text` | 替换结果为空。 |
| `same_text_noop` | 替换前后无变化却声称 correction。 |
| `evidence_conflict_unresolved` | 证据冲突但没有解释。 |

## 10. 闭环写入

`transcript-semantic-correction-closure` 只能写入通过校验的 decisions。

写入规则：

1. 读取原始 transcript sidecar。
2. 应用 validated decisions。
3. 生成 `source-arbitrated-transcript.json`。
4. 生成 `source-arbitrated-transcript.srt`。
5. 写入 correction provenance。
6. 刷新最终导出。
7. 生成 impact report。

纠正版 segment 最小字段：

```json
{
  "start": 123.4,
  "end": 130.2,
  "text": "这里我们看 Playwright MCP 的用法。",
  "source_text": "这里我们看 play right m c p 的用法。",
  "correction_status": "corrected",
  "corrections": [
    {
      "candidate_id": "semcorr-0001",
      "original_text": "play right m c p",
      "corrected_text": "Playwright MCP",
      "confidence": 0.96,
      "evidence_ids": ["ev-001"],
      "applied_at": "2026-07-07 00:00:00",
      "applied_by": "transcript-semantic-correction-closure"
    }
  ]
}
```

## 11. 最终文件影响路径

高置信纠错必须影响这些文件：

| 文件 | 要求 |
| --- | --- |
| `exports/full-transcript.md` | 使用纠正版 transcript，保留必要 correction note。 |
| `exports/smart-summary.md` | 使用纠正版 transcript 作为优先输入，不继承已接受错词。 |
| `exports/knowledge-note.md` | 证据审计层显示纠错来源和剩余风险。 |
| `exports/content-material-card.json/md` | 不把低置信候选当事实，不把已纠正错词继续输出。 |
| `video-rag-pack` | 检索文本应使用纠正版，同时保留 source_text。 |

如果只生成 `transcript-semantic-correction-result.codex.md`，但最终文件没有变化，不能算完成。

## 12. Impact Report

每次 closure 后必须生成影响报告。

建议产物：

```text
transcript-semantic-correction-impact-report.json
transcript-semantic-correction-impact-report.md
transcript-semantic-readable-impact-report.json
transcript-semantic-readable-impact-report.md
transcript-semantic-summary-impact-report.json
transcript-semantic-summary-impact-report.md
```

检查内容：

- accepted decisions 数量；
- applied decisions 数量；
- `full-transcript.md` 是否还有原始错词残留；
- `smart-summary.md` 是否还有原始错词残留；
- content card 是否输出了低置信候选；
- 数字类修改是否出现在 audit；
- review_required 是否只作为 known gaps，而不是 blocked。

## 13. UI 和批处理目标

### 13.1 Task Console

Task Console 应展示：

- correction pack 是否存在；
- candidate count；
- candidate group count；
- accepted decisions；
- review required decisions；
- closure 是否已执行；
- final export 是否 fresh；
- impact 是否通过；
- 下一步建议。

### 13.2 批量队列

批量能力应支持：

- 生成多个 bundle 的 correction pack；
- 分批调用 Codex/LLM 判读；
- 校验每批结果；
- 只对通过校验的高置信项 closure；
- 自动刷新导出；
- 汇总 batch acceptance；
- 对低置信项生成 review pack；
- 失败项可重试。

### 13.3 人工审核

人工审核不是必选阻塞，但必须可用。

Review item 应包含：

- 时间戳；
- 原句；
- 建议改法；
- 证据来源；
- OCR/ebook 结果；
- 画面/抽帧证据；
- 是否数字/事实高风险；
- 操作按钮或 JSON 行：`accept`、`keep_original`、`needs_more_evidence`、`reject`。

## 14. 命令链路

推荐命令链路：

```powershell
.\scripts\video-knowledge.ps1 transcript-semantic-correction-pack <webui-bundle>

.\scripts\video-knowledge.ps1 transcript-semantic-correction-codex-draft <webui-bundle>

.\scripts\video-knowledge.ps1 validate-transcript-semantic-correction `
  <webui-bundle> `
  --input-json <result-md-or-json>

.\scripts\video-knowledge.ps1 transcript-semantic-correction-closure `
  <webui-bundle> `
  --input-json <result-md-or-json>

.\scripts\video-knowledge.ps1 export-knowledge-note <webui-bundle>

.\scripts\video-knowledge.ps1 transcript-semantic-correction-impact-report <webui-bundle>

.\scripts\video-knowledge.ps1 transcript-semantic-readable-impact-report <webui-bundle>

.\scripts\video-knowledge.ps1 transcript-semantic-summary-impact-report <webui-bundle>

.\scripts\video-knowledge.ps1 transcript-semantic-correction-status <webui-bundle>
```

在线 LLM 版本必须默认 preview，显式 `--execute` 才调用：

```powershell
.\scripts\video-knowledge.ps1 transcript-semantic-correction-llm-draft `
  <webui-bundle> `
  --provider-config <provider-config.json> `
  --limit 80
```

## 15. 与 ebook/OCR、多模态、打标器的关系

### 15.1 ebook/OCR

ebook/OCR 是图文证据来源，不是转写纠错本身。

用途：

- 识别屏幕上的工具名、标题、表格、数字；
- 作为候选证据；
- 对 ASR/字幕错词提出冲突；
- 进入 evidence pack。

如果 OCR 为空、wrapper-only 或低信息量：

- 不清除缺口；
- 标记为 `ocr_weak_or_empty`；
- 对疑难片段提高多模态或人工复核优先级。

### 15.2 多模态

多模态用于：

- OCR 无法识别的界面状态；
- 实物演示、操作步骤、动作；
- 连续帧状态变化；
- ASR 说“这个、这里、这样”的指代消解；
- 高风险疑难点复核。

默认不把所有帧送在线模型。在线多模态只用于疑难点、低置信冲突和人工/规则无法确认的片段。

### 15.3 打标器

打标器不仅是标签来源，也是时间轴和优先级来源。

用途：

- 标出工具名、步骤、重点、疑难、案例、结论；
- 提高相关片段候选优先级；
- 帮助定位真实说话时间段；
- 触发补帧、OCR、视觉复核；
- 作为 evidence pack 的 tagger evidence。

## 16. 完成标准

单个 bundle 达标：

- `transcript-semantic-correction-pack.json` 存在；
- candidate group 正常生成；
- Codex/LLM/人工 decisions 能被 validate；
- 高置信 decisions 能 closure；
- `source-arbitrated-transcript.json` 存在；
- `full-transcript.md` 使用纠正版 transcript；
- `smart-summary.md` 使用纠正版 transcript；
- impact report 证明 accepted 原错词无残留；
- 低置信项进入 review pack 或 known gaps；
- 状态报告说明剩余风险。

批量达标：

- 3-5 个真实知识视频 bundle 跑通；
- batch acceptance 返回 accepted 或 accepted_with_known_gaps；
- `final_residual_error_total = 0`，至少对 accepted decisions 成立；
- review_required 不阻塞整体交付；
- UI 能显示进度、失败、重试和人工复核入口。

## 17. 当前落地状态

截至 2026-07-07，本项目已有一部分能力：

| 能力 | 状态 |
| --- | --- |
| 术语/工具名候选 | 已有。 |
| Codex 代替 LLM 的判读草稿 | 已有。 |
| 通用 semantic correction pack | 已在推进。 |
| candidate group | 已有落地记录。 |
| validate | 已有。 |
| closure 写入纠正版 transcript | 已有。 |
| closure 后刷新最终导出 | 已有落地记录。 |
| readable/summary impact report | 已有。 |
| batch acceptance / repair queue | 已有。 |
| Task Console 展示 | 已有基础，仍需继续增强审核和重试体验。 |
| 数字、动作、普通错词、断句全覆盖 | 未完全完成，需要继续扩展候选发现和真实验收。 |

因此当前判断：

```text
术语/工具名纠错子链路：已部分落地并可验证。
所有 ASR/字幕疑似错词通用闭环：目标和主干已明确，仍需继续补齐全类型候选、批量真实验收和 UI 审核闭环。
```

## 18. 下一步开发顺序

1. 扩展候选发现。
   - 数字/金额/时间；
   - 动作/步骤；
   - 普通语义不通错词；
   - 标点/断句；
   - 平台字幕与本地 ASR 冲突。

2. 强化 candidate group。
   - 全片实体变体合并；
   - 跨视频 glossary 只作为建议，不直接覆盖；
   - group 级别 UI 审核。

3. 固化 Codex/LLM 仲裁。
   - Codex 替代在线 LLM 的人工半自动流程；
   - 在线 LLM provider 仍必须 preview-first；
   - JSON repair 和 schema validate。

4. 强化 closure 到最终输出。
   - 每次 closure 后刷新 export；
   - 每次刷新后跑 readable impact；
   - smart-summary 必须优先读取纠正版 transcript。

5. 做真实批量验收。
   - 选择 3-5 个真实 bundle；
   - 每个 bundle 至少验证 5-10 个候选；
   - accepted decisions 原错词最终无残留；
   - 低置信项不阻塞，但能在 review pack 中看到。

## 19. 关键边界

- 不改原始证据。
- 不把字幕当真相。
- 不把 OCR 当唯一真相。
- 不把 LLM 猜测当事实。
- 不自动改数字，除非证据强。
- 不自动发布内容素材。
- 不绕过 review notes 写回人工结果。
- 不让“有候选文件”冒充“闭环完成”。

## 20. 一句话验收

这条目标真正完成时，用户应该能拿一个知识视频 bundle 跑完整链路，然后看到：

```text
原始 ASR/字幕里的疑似错词被多源证据发现；
高置信错词被纠正进 source-arbitrated-transcript；
full-transcript.md 和 smart-summary.md 已使用纠正版；
impact report 证明已接受错词无残留；
低置信项被列入可选人工复核，不阻塞最终交付。
```


## 21. 实现拆解

这个目标在工程上应拆成九个可单独验收的模块。每个模块都必须有 CLI/MCP 或 Task Console 入口，避免只能靠人手改 JSON。

| 模块 | 责任 | 输入 | 输出 | 完成标准 |
| --- | --- | --- | --- | --- |
| `transcript_sidecar_collector` | 收集 ASR、平台字幕、自带字幕和纠正版 transcript。 | ASR 输出、字幕文件、manifest。 | 统一 transcript sidecar 索引。 | 每个来源都有来源类型、时间戳、文本、置信信息和证据路径。 |
| `visual_text_evidence_collector` | 收集 OCR/ebook、屏幕文字、结构化图文证据。 | timeline、frame、ebook pipeline 输出。 | visual text evidence。 | 空结果、wrapper-only、低信息量结果不能当成功，必须标记。 |
| `visual_semantic_evidence_collector` | 收集多模态单帧和连续片段证据。 | `visual_understanding`、`temporal_visual_understanding`。 | visual semantic evidence。 | 明确区分文字证据、画面语义、动作/状态变化。 |
| `metadata_and_tagger_evidence_collector` | 收集网页标题简介、VDO handoff、打标器标签和时间段。 | manifest、VDO artifact、tagger output。 | metadata/tag evidence。 | 标签既用于优先级，也用于时间轴定位。 |
| `semantic_candidate_discovery` | 发现所有疑似错词、错数字、错动作、断句问题。 | 多源证据池。 | candidate suggestions / candidate pack。 | 不只发现工具名，还覆盖普通错词、数字、动作、指代、断句。 |
| `candidate_grouping` | 合并同一真实概念的多个错写。 | candidates。 | candidate groups。 | 同一实体或概念全片统一判断，不逐条孤立纠正。 |
| `semantic_decision` | Codex/LLM/人工进行语义仲裁。 | evidence pack、prompt、上下文。 | correction result draft。 | 每条 decision 必须引用证据、置信度、风险和输出策略。 |
| `semantic_validation_and_closure` | 校验并写入纠正版 transcript。 | validated decisions。 | `source-arbitrated-transcript.json/srt`。 | 原始证据不变；只写派生产物。 |
| `readable_output_impact` | 证明纠正进入最终人类可读文件。 | corrected transcript、exports。 | impact report/status。 | accepted 原错词不再残留在 `full-transcript.md`、`smart-summary.md`、素材卡。 |

## 22. 状态机

每个 bundle 的通用语义纠错状态应能被 `transcript-semantic-correction-status` 和 Task Console 读出。

| 状态 | 含义 | 下一步 |
| --- | --- | --- |
| `not_started` | 还没有构建通用语义纠错候选。 | 运行 `transcript-semantic-correction-pack`。 |
| `no_candidates` | 当前规则没有发现候选。 | 如果 candidate discovery 未跑，先跑候选发现；否则可接受为低风险状态。 |
| `needs_candidate_discovery` | 初始 pack 没发现候选，但还没跑 Codex/LLM 候选召回。 | 运行 `transcript-semantic-candidate-discovery-pack`。 |
| `candidate_discovery_prompt_ready` | 已生成候选发现 prompt，等待 Codex/LLM/人工填充。 | 用 Codex 或在线 LLM 生成 suggestions。 |
| `candidate_suggestions_ready` | 已有候选 suggestions，但尚未导入标准候选。 | 运行 `import-transcript-semantic-candidate-suggestions`。 |
| `needs_codex_or_llm_review` | 有标准候选，等待语义仲裁。 | 运行 Codex draft、LLM draft 或人工 review。 |
| `needs_validation` | 有仲裁草稿，但未校验。 | 运行 `validate-transcript-semantic-correction`。 |
| `needs_closure` | 校验通过但未写入纠正版 transcript。 | 运行 `transcript-semantic-correction-closure`。 |
| `needs_export_refresh` | 纠正版 transcript 已更新，但最终导出未刷新。 | 运行 `export-knowledge-note` 或对应刷新入口。 |
| `needs_readable_impact` | 导出已刷新，但未证明最终文件吸收纠正。 | 运行 readable/summary impact report。 |
| `impact_failed` | accepted 错词仍残留在最终输出。 | 重新导出、修复 smart-summary 输入，或人工处理残留。 |
| `ready_for_summary_input` | 纠正版 transcript 可作为智能总结优先输入。 | 生成/刷新 smart summary。 |
| `accepted_with_known_gaps` | 高置信项已闭合，低置信项作为可选复核保留。 | 可交付，但保留风险清单。 |

## 23. 高置信自动纠正规则

高置信不是“模型说得很像”，而是证据链足够强。

可以自动进入纠正版 transcript 的情况：

1. OCR/ebook 清楚识别出屏幕文字，ASR 是明显音近错词。
2. 平台标题、简介、课件标题和全片上下文一致支持同一个专名。
3. 同一候选在多个时间段反复出现，且其他来源一致给出标准写法。
4. 人工标注已确认。
5. Codex/LLM decision 通过 validate，且 risk 不属于高风险数字、金额、事实归属。

必须保守处理的情况：

1. 数字、金额、比例、时间、排名。
2. 涉及人物、公司、收入、疗效、法律、金融结论。
3. OCR 低置信、画面模糊或只出现一次。
4. 只有 LLM 语义猜测，没有独立证据。
5. 纠正会改变原句事实含义，而不是修复识别错误。

保守处理不是阻塞视频交付，而是写入 review pack / known gaps，并在 `smart-summary.md` 的低置信内容中提示。

## 24. 与最终人类可读文件的关系

通用语义纠错必须改变最终输出，而不是停在中间报告。

| 最终文件 | 应如何使用纠正版 transcript |
| --- | --- |
| `exports/full-transcript.md` | 优先使用 `source-arbitrated-transcript.json`，展示纠正后的文本，并可保留必要的原文/纠正说明。 |
| `exports/smart-summary.md` | 优先从纠正版 transcript、smart-summary input pack 和章节包生成；未闭合候选只能写入待复核点，不能当事实写入正文。 |
| `exports/knowledge-note.md` | 展示语义纠错状态、accepted 数、review 数、known gaps、impact 状态和证据路径。 |
| `exports/extraction-audit.md` | 保留每条纠正的原文、纠正文、证据、置信度、风险和写入路径。 |
| `exports/content-material-card.*` | 透传 `semantic_correction_status`；未闭合时只允许作为 inspiration，不允许当事实或发布稿。 |
| 下游 handoff | 只传递状态和证据，不把低置信纠正包装成已确认结论。 |

## 25. Task Console / UI 要求

UI 不只是展示结果，还要让人知道下一步该做什么。

Task Console 至少应展示：

- 当前 `semantic_correction_status`；
- candidate discovery 状态、候选数、导入数、跳过数；
- 标准候选数量、attention 候选数量、group 数；
- Codex/LLM draft 是否存在；
- validate 状态、accepted/review/rejected 数；
- closure 是否写出纠正版 transcript；
- readable impact / summary impact 是否通过；
- 最新 batch repair run 的动作、失败原因和下一步命令；
- 人工 review pack 入口；
- 低置信项可以继续复核，但不阻塞整体交付。

UI 允许复制命令和查看证据，不应直接静默调用云 LLM、云视觉或写回知识库。

## 26. 批量验收标准

这条闭环不能只在一个样例上跑通，至少要覆盖 3-5 个真实知识视频。

批量验收表应包含：

| 字段 | 说明 |
| --- | --- |
| `bundle` | bundle 路径。 |
| `title` | 视频标题。 |
| `semantic_status` | 当前语义纠错状态。 |
| `candidate_count` | 标准候选数量。 |
| `candidate_discovery_status` | 候选召回是否已跑。 |
| `accepted_count` | 已接受纠正数量。 |
| `review_count` | 保留复核数量。 |
| `applied_correction_count` | 写入纠正版 transcript 的数量。 |
| `readable_impact_status` | full transcript/knowledge note 是否吸收。 |
| `summary_impact_status` | smart summary 是否吸收。 |
| `residual_error_total` | accepted 原错词残留数量。 |
| `next_action` | 下一步机器动作或人工动作。 |

批量通过条件：

```text
- 所有 ready/accepted bundle 的 accepted 原错词残留为 0；
- 低置信项进入 known gaps 或 review pack；
- 没有 bundle 因“未人工复核”被硬阻塞；
- Task Console / batch report 能指出下一步；
- smart-summary 不再使用 raw ASR 中已接受的错词。
```

## 27. 下一阶段最小可执行计划

下一阶段不要再扩大概念，而是围绕“候选召回不足”和“最终输出吸收不足”做闭环。

1. **候选发现补漏**
   - 把 `no_candidates` 状态改成先触发 candidate discovery，而不是直接接受。
   - 对普通错词、指代词、低信息句、OCR 强概念、字幕/ASR 冲突生成 suggestions。
   - 把 suggestions 导入标准 semantic correction candidates。

2. **UI 复核和批次队列**
   - Task Console 展示 candidate discovery suggestions。
   - 批量 repair queue 能自动执行本地安全动作：pack、candidate discovery、import suggestions。
   - 云 LLM 仍保持 preview-first。

3. **纠正版 transcript 到最终输出**
   - closure 后强制刷新 `full-transcript.md`、`smart-summary-input-pack`、`smart-summary.md`。
   - impact report 同时检查逐字稿和智能总结。
   - 如果 smart-summary 没吸收纠正，状态不能显示为 final。

4. **真实长视频验收**
   - 对 3-5 个真实 bundle 做抽样。
   - 每个 bundle 记录 5-10 个错词前后对比。
   - 用人工抽样判断智能总结准确率是否提升。

5. **文档与接口冻结**
   - CLI/MCP 命令、输出 schema、状态机、Task Console 字段固定下来。
   - 后续在线 LLM、本地模型或 Codex 替代，只替换 `semantic_decision` 层，不改整条闭环。
