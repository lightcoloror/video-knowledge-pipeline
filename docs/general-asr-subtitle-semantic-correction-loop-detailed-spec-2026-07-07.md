# ASR/字幕疑似错词通用语义纠错闭环详细规格

更新时间：2026-07-07 07:03:51
执行者：Codex / GPT-5
项目：`video-knowledge-pipeline`
关联目标文档：`docs/general-asr-subtitle-semantic-correction-loop-2026-07-06.md`
总设计入口：`docs/asr-subtitle-semantic-correction-loop-design-2026-07-07.md`

## 1. 核心目标

VKP 需要建立一条面向所有 ASR/字幕疑似错词的通用语义纠错闭环。

这个目标不是“做一个术语词典”，也不是“让 LLM 润色逐字稿”，而是：

> 凡是 ASR、平台字幕、自带字幕里可能识别错的词语，只要能被 OCR/ebook、画面、多模态、网页标题简介、打标器、时间线、上下文或人工标注证明“可能错了”，就进入候选；只要能被多证据高置信证明“应该改成什么”，就进入纠正版 transcript；纠正版 transcript 必须真实影响最终人类可读文件。

完成标准不是中间文件存在，而是最终输出不再继承已确认的转写错误：

```text
ASR/字幕疑似错词
  -> 多源证据候选
  -> Codex/LLM/人工语义判断
  -> 本地校验
  -> source-arbitrated-transcript
  -> full-transcript.md / smart-summary.md / content-candidate-pack
  -> impact report 确认已接受错词无残留
```

## 2. 为什么不能只做术语仲裁

术语仲裁是这个闭环的一个高优先级子模块，但不是全部。

| 类型 | 例子 | 为什么重要 |
| --- | --- | --- |
| 工具名 / 产品名 | `play right m c p`、`browser base`、`open client` | 影响工具横评、搜索、复用和后续内容素材。 |
| 品牌 / 人名 / 平台名 | 讲师名、公司名、项目名、课程名 | 影响事实核查和检索。 |
| 行业术语 / 课程概念 | 保险、外贸、跨境、量化、浏览器自动化 | 影响课程主线和智能总结结构。 |
| 数字 / 金额 / 时间 | `16k`、`1w刀`、`1500万`、比例、年份 | 错了会造成事实性误导，默认必须更保守。 |
| 动作 / 步骤 | 点击、导入、登录、注册、成交动作 | 知识类教程里直接影响行动清单。 |
| 普通 ASR 错词 | 同音错、语义不通、上下文冲突 | 不一定是专名，但会改变意思。 |
| 标点 / 断句 / 段落边界 | 因果、转折、列表、问答边界 | 影响逐字稿可读性和智能总结质量。 |
| 字幕源自身错误 | B站字幕、平台字幕、自带字幕也可能是 ASR | 不能把“有字幕”默认当作真相。 |

所以应该统一叫 **转写语义纠错闭环**。`term arbitration` 继续存在，但只是其中的实体纠错分支。

## 3. 基本原则

### 3.1 第一轮证据必须相互独立

多个角度分析时，第一轮不能互相污染。

| 分析角度 | 第一轮要求 | 融合阶段 |
| --- | --- | --- |
| 本地 ASR | 独立产出原始转写、时间戳、置信信息。 | source arbitration / semantic correction。 |
| 平台字幕 / 自带字幕 | 独立保存来源、文本、时间戳和来源类型。 | 与 ASR/OCR/上下文对比。 |
| OCR/ebook | 独立解析屏幕文字、课件、表格、代码、公式。 | 作为强证据触发候选。 |
| 多模态视觉 | 独立理解对象、界面状态、动作、空间关系。 | 对 OCR 失败、操作演示、非文字画面补证。 |
| 打标器/时间线 | 独立输出时间段、标签、重点、疑难、工具名、步骤。 | 给候选排序和抽帧/复核加权。 |
| 网页标题/简介 | 独立作为外部元数据保存。 | 支撑人名、课程名、平台名、主题词。 |
| 人工标注 | 独立记录用户确认、保留原文、需复核。 | 作为最高优先级确认来源。 |

融合只能在 evidence pack、arbitration、correction closure 阶段发生，不能在第一轮就把某一路结果覆盖掉。

### 3.2 原始证据不可覆盖

闭环只能写入纠正版 transcript 和派生产物：

- 可以写：`source-arbitrated-transcript.json/md/srt`；
- 可以写：`exports/full-transcript.md`、`exports/smart-summary.md`；
- 可以写：纠错日志、影响报告、review rows；
- 不可以改：原始 ASR 输出、平台字幕原文件、自带字幕原文件、原始 OCR/视觉证据。

### 3.3 低置信不阻塞，但必须显性暴露

用户已明确：人工复核应是可选项，不作为必选、不造成整体阻塞。

因此策略是：

- 高置信、低风险纠正：可进入纠正版 transcript；
- 低置信或高风险纠正：进入 review pack 或 known gaps；
- 输出可以是 `accepted_with_known_gaps`；
- 最终文件必须列出剩余风险，不能伪装为全量无误；
- 内容素材只允许作为 `needs_review_inspiration`，不能自动发布或当事实。

## 4. 输入证据层

| 证据源 | 代表产物 | 能证明什么 |
| --- | --- | --- |
| 本地 ASR | `normalized-transcript.json`、`normalized-transcript.srt` | 原始听写文本和时间戳。 |
| 平台字幕 | platform subtitle sidecar | 与 ASR 对比，发现不一致。 |
| 自带字幕 | 视频内字幕、外挂字幕 | 可能更准，也可能同样来自 ASR。 |
| OCR/ebook | `visual_text`、`structured_visual`、ebook pipeline 输出 | 课件文字、表格、代码、工具名、数字。 |
| 多模态视觉 | `visual_understanding`、`temporal_visual_understanding` | 画面对象、动作、界面状态、操作流程。 |
| 视频标题/简介/网页元数据 | VDO handoff、平台页面抓取结果 | 课程名、人名、品牌名、主题词。 |
| 打标器/时间线 | timeline route/tag、青龙打标器结果 | 重点、疑难、工具名、步骤、案例、结论。 |
| 全片上下文 | smart-summary input pack、chapter pack、long-video memory | 判断局部词是否符合全片主线。 |
| 人工标注 | review notes、sample eval | 用户确认、保留原文、人工纠正。 |

## 5. 候选发现策略

### 5.1 多源不一致触发

当 ASR、平台字幕、自带字幕、OCR/ebook、网页标题之间出现不同写法时，生成候选。

例：

```text
ASR: play right m c p
OCR: Playwright MCP
网页标题: 浏览器自动化工具横评
=> 候选：play right m c p -> Playwright MCP
```

### 5.2 画面强证据触发

当屏幕上明确出现文字，ASR 却识别成相近音或无意义词时，生成候选。

例：

```text
ASR: browser base
OCR/ebook: Browserbase
=> 候选：browser base -> Browserbase
```

### 5.3 语义不通触发

当句子在上下文里不通顺、与前后主题冲突、或出现孤立无意义词时，生成普通错词候选。

触发信号：

- 句子结构断裂；
- 同一概念前后写法频繁变化；
- 章节标题附近出现无法解释的词；
- 语义与课程主线冲突；
- 一句话概览或 smart summary 出现关键词拼接式病句。

### 5.4 数字/金额/时间高风险触发

数字类即使只有一次出现，也要优先进入候选池或高风险监控。

触发信号：

- ASR 出现金额、比例、年份、步骤编号；
- OCR/ebook 中出现表格或数字；
- 标题/简介中出现数字；
- 同一数字在后文重复但不一致。

数字类默认不自动改，除非有强证据，例如 OCR、标题和上下文三方一致，或人工确认。

### 5.5 动作/步骤触发

教程、课程、软件演示中的动作词会直接影响行动清单。

触发信号：

- ASR 说“点击这个”“打开这里”，但画面有具体按钮；
- 连续帧显示实际操作和 ASR 不一致；
- 打标器标出“步骤 / 操作演示 / 流程 / 案例”。

### 5.6 重复实体变体触发

同一实体在全片中出现多个变体时，应合并为 candidate group。

例：

```text
Browserbase / browser base / browser bus / Browse base
```

候选不应逐条孤立判断，而应作为一个实体簇做统一仲裁。

## 6. 候选风险分级

| 风险级别 | 条件 | 默认处理 |
| --- | --- | --- |
| `safe_auto_apply` | 多证据一致，置信度高，低事实风险 | 可写入纠正版 transcript。 |
| `auto_apply_with_audit` | 证据强，但涉及专名、数字或事实 | 可写入，但 audit/impact 必须标出。 |
| `needs_human_review` | 证据冲突、置信不足、可能影响事实结论 | 不写入，进入 review pack。 |
| `keep_original` | 原文可能正确，建议证据不足 | 保留原文。 |
| `reject` | 模型建议无证据、schema 错误或越权改写 | 拒绝。 |

## 7. Evidence Pack 结构

通用 evidence pack 建议产物：

```text
transcript-semantic-correction-pack.json
transcript-semantic-correction-prompt.md
transcript-semantic-correction-llm-prompt.md
transcript-semantic-correction-result.template.json
transcript-semantic-correction-result.codex.md
```

每个候选项至少包含：

```json
{
  "candidate_id": "semcorr-0001",
  "correction_type": "term | proper_noun | number | action | concept | ordinary_word | punctuation | segment_boundary",
  "risk_level": "safe_auto_apply | auto_apply_with_audit | needs_human_review | keep_original",
  "time_range": {"start": 123.4, "end": 130.2},
  "timeline_indexes": [12],
  "original_text": "play right m c p",
  "suggested_text": "Playwright MCP",
  "context_before": "...",
  "context_after": "...",
  "evidence": [
    {
      "evidence_id": "ev-001",
      "source_type": "asr | platform_subtitle | embedded_subtitle | ocr_ebook | visual | temporal_visual | page_metadata | tagger | human_note",
      "text": "Playwright MCP",
      "path": "...",
      "timeline_index": 12,
      "confidence": 0.92
    }
  ],
  "conflicts": [
    {"source_type": "asr", "text": "play right m c p"},
    {"source_type": "ocr_ebook", "text": "Playwright MCP"}
  ],
  "why_this_is_suspicious": "ASR text is phonetically similar to a tool name shown on screen.",
  "final_output_impact": ["full_transcript", "smart_summary", "content_candidate_pack"]
}
```

## 8. Codex / LLM 判读结果 Schema

Codex 或在线 LLM 只能判断 pack 中已有候选，不能自由重写整篇 transcript。

```json
{
  "schema": "video_knowledge_pipeline.transcript_semantic_correction_result.v1",
  "source": "codex_substitute_for_online_llm",
  "decisions": [
    {
      "candidate_id": "semcorr-0001",
      "action": "replace | keep_original | needs_human_review | reject",
      "correction_type": "term",
      "original_text": "play right m c p",
      "corrected_text": "Playwright MCP",
      "canonical": "Playwright MCP",
      "aliases": ["play right m c p", "playright m c p"],
      "confidence": 0.96,
      "safe_to_apply": true,
      "needs_human_review": false,
      "semantic_rationale": "The screen OCR and nearby discussion both refer to the browser automation tool Playwright MCP.",
      "evidence_ids": ["ev-001", "ev-002"],
      "timeline_indexes": [12],
      "final_output_policy": "apply_to_corrected_transcript_and_summary"
    }
  ]
}
```

## 9. 校验规则

`validate-transcript-semantic-correction` 必须拒绝：

| 拒绝原因 | 说明 |
| --- | --- |
| `missing_candidate_id` | 不能没有 candidate id。 |
| `unknown_candidate_id` | candidate id 不在 pack 中。 |
| `missing_evidence` | 没有引用证据。 |
| `missing_rationale` | 没有语义理由。 |
| `low_confidence` | 置信度低于阈值。 |
| `unsafe_number_change` | 数字/金额/比例/年份缺强证据。 |
| `overbroad_rewrite` | 把纠错变成整段改写。 |
| `changes_unrelated_text` | 修改了候选以外的内容。 |
| `needs_human_review` | 模型自己标记需要人工。 |
| `schema_error` | JSON/Markdown 解析失败或字段不合格。 |

## 10. 闭环写入规则

`transcript-semantic-correction-closure` 只能写入通过校验的决策。

写入时必须保留：

- 原始文本；
- 纠正文本；
- 时间戳；
- candidate id；
- evidence ids；
- 置信度；
- 是否自动应用；
- 是否人工确认；
- 写入时间。

目标产物：

```text
source-arbitrated-transcript.json
source-arbitrated-transcript.md
source-arbitrated-transcript.srt
transcript-semantic-correction-closure.json
transcript-semantic-correction-closure.md
```

## 11. 最终输出影响路径

纠错结果必须沿着下面路径进入最终人类可读文件：

```text
source-arbitrated-transcript.json
  -> exports/full-transcript.md
  -> exports/smart-summary-input-pack.*
  -> exports/smart-summary-chapters.*
  -> exports/smart-summary.codex.md
  -> exports/smart-summary.md
  -> exports/content-candidate-pack.*
  -> exports/content-material-card.*
```

如果 correction 只停留在 `transcript-semantic-correction-result.codex.md`、`transcript-semantic-correction-result.llm.md` 或 `term-arbitration-glossary.json`，没有影响最终 exports，就不能算闭环完成。

## 12. 标准命令链路

```powershell
# 1. 生成候选和证据包
.\scripts\video-knowledge.ps1 transcript-semantic-correction-pack <webui-bundle>

# 2A. Codex 暂时代替在线 LLM，生成保守判读草稿
.\scripts\video-knowledge.ps1 transcript-semantic-correction-codex-draft <webui-bundle>

# 2B. 或生成 LLM 判读计划，默认不调用云
.\scripts\video-knowledge.ps1 transcript-semantic-correction-llm-draft <webui-bundle> --limit 80

# 2C. 明确允许后才真实调用 LLM provider
.\scripts\video-knowledge.ps1 transcript-semantic-correction-llm-draft <webui-bundle> --provider-config PATH_TO_PROVIDER_CONFIG_JSON --execute --limit 80

# 3. 校验 Codex/LLM/人工结果
.\scripts\video-knowledge.ps1 validate-transcript-semantic-correction <webui-bundle> --input-json <result-md-or-json>

# 4. 写入纠正版 transcript
.\scripts\video-knowledge.ps1 transcript-semantic-correction-closure <webui-bundle> --input-json <result-md-or-json>

# 5. 重新导出人类可读文件
.\scripts\video-knowledge.ps1 export-knowledge-note <webui-bundle>

# 6. 检查纠错影响和残留
.\scripts\video-knowledge.ps1 transcript-semantic-correction-impact-report <webui-bundle>
.\scripts\video-knowledge.ps1 transcript-semantic-readable-impact-report <webui-bundle>

# 7. 查看状态
.\scripts\video-knowledge.ps1 transcript-semantic-correction-status <webui-bundle>
```

批量只读验收：

```powershell
.\scripts\video-knowledge.ps1 transcript-semantic-batch-acceptance <batch-input> --target-bundle-count 3 --limit 3
.\scripts\video-knowledge.ps1 transcript-semantic-repair-queue <batch-input> --target-bundle-count 3 --limit 3
```

## 13. UI 和 agent 调用要求

### 13.1 任务控制台

`task-console.html` 应显示：

- 通用语义纠错候选数；
- Codex/LLM 草稿状态；
- validate / closure / impact / readable impact 状态；
- 可复制命令；
- 批量重试队列入口；
- 哪些步骤是机器可执行，哪些需要人工复核。

### 13.2 视频工作台

`video-workbench.html` 应把语义纠错和视频证据连接起来：

- 能看到候选对应时间段；
- 能打开 transcript editor；
- 能看到 OCR/视觉/时间线证据；
- 能进入人工 review；
- 不直接绕过 validate/closure 写回。

### 13.3 MCP / OpenClaw

MCP 工具名需要和 CLI 保持镜像：

```text
transcript_semantic_correction_pack
transcript_semantic_correction_codex_draft
transcript_semantic_correction_llm_draft
validate_transcript_semantic_correction
transcript_semantic_correction_closure
transcript_semantic_correction_impact_report
transcript_semantic_readable_impact_report
transcript_semantic_correction_status
transcript_semantic_batch_acceptance
transcript_semantic_repair_queue
```

OpenClaw/live-smoke 只读调用时，应能返回：

- 单 bundle 语义纠错状态；
- 批量 acceptance 状态；
- repair queue 下一步；
- 是否需要人工；
- 是否允许机器动作；
- 不得自动调用云 LLM 或写回。

## 14. 完成标准

### 14.1 单个 bundle 完成

满足以下条件才算这个 bundle 的语义纠错闭环完成：

- `transcript-semantic-correction-pack.json` 已生成；
- 候选已经被 Codex、LLM 或人工处理；
- `validate-transcript-semantic-correction` 通过；
- `transcript-semantic-correction-closure` 写入纠正版 transcript；
- `export-knowledge-note` 已重新导出；
- `transcript-semantic-correction-impact-report` 通过；
- `transcript-semantic-readable-impact-report` 通过；
- `full-transcript.md` 和 `smart-summary.md` 不再残留已接受错词；
- 低置信项被列为 review 或 known gaps。

### 14.2 批量完成

满足以下条件才算进入生产可用：

- 3-5 个真实 bundle 的 `transcript-semantic-batch-acceptance` 返回 accepted 或 accepted_with_known_gaps；
- `transcript-semantic-repair-queue` 没有未解释的机器动作；
- 人工复核项集中输出，不阻塞其余 bundle；
- OpenClaw/live-smoke 能读到同一状态；
- MCP args audit 不缺关键入口。

### 14.3 输出质量完成

满足以下条件才算对用户有真实价值：

- `full-transcript.md` 更接近真实说话内容；
- `smart-summary.md` 不再继承已接受错词；
- 智能总结覆盖完整视频，不受抽帧/timeline 截断影响；
- 关键观点、行动清单、章节总结被纠正版 transcript 改善；
- 内容素材明确标记 `allowed_as_fact=false`、`publication_allowed=false`、`review_required=true`。

## 15. 当前完成度

截至 2026-07-07，当前项目状态是：

| 能力 | 状态 |
| --- | --- |
| 通用纠错目标文档 | 已有，本文件为详细规格版。 |
| 候选 pack | 已有 `transcript-semantic-correction-pack`。 |
| Codex 判读替身 | 已有 `transcript-semantic-correction-codex-draft`。 |
| LLM provider 判读入口 | 已有 `transcript-semantic-correction-llm-draft`，默认 preview，显式 `--execute` 才调用。 |
| 本地校验 | 已有 `validate-transcript-semantic-correction`。 |
| 闭环写入 | 已有 `transcript-semantic-correction-closure`。 |
| 可读文件影响检查 | 已有 `transcript-semantic-readable-impact-report`。 |
| 批量验收 | 已有 `transcript-semantic-batch-acceptance`。 |
| 批量重试队列 | 已有 `transcript-semantic-repair-queue` preview-only。 |
| UI 入口 | 已接入 task console / video workbench 的部分入口。 |

仍未完成：

1. 真实 LLM provider 对非安全词、数字、动作、普通错词、复杂断句的批量判读；
2. UI 中真正的批量执行、失败重试按钮和进度交互；
3. 智能总结质量提升的系统抽样报告；
4. 当前托管 shell 下 pytest temp/cache 权限问题导致完整测试套件还不能稳定作为门禁。

## 16. 下一阶段建议

下一阶段应该优先做四件事：

1. **扩大候选发现**：把数字、动作、普通 ASR 错词、断句候选做得比工具名更通用。
2. **真实 LLM 判读小批量验收**：用 1-2 个 bundle、20-50 个候选测试 provider 结果质量，不直接全量跑。
3. **UI 队列固化**：在 task console/video workbench 显示 repair queue、失败原因、重试命令、人工复核入口。
4. **智能总结影响评估**：抽样比较纠错前后 `smart-summary.md` 的事实准确性、关键词准确性、章节覆盖和行动清单质量。
## 17. 模块边界与职责

通用语义纠错闭环应拆成若干低耦合模块。每个模块只做一类事，避免把“发现候选、判断、写回、导出、审核”混在一起。

| 模块 | 建议入口 | 输入 | 输出 | 是否可自动执行 |
| --- | --- | --- | --- | --- |
| 证据收集 | `transcript-semantic-correction-pack` | ASR、字幕、OCR/ebook、视觉、网页元数据、timeline、tagger | `transcript-semantic-correction-pack.json/md` | 是，只读。 |
| 候选发现 | pack 内部阶段 | 多源文本和证据 | candidate groups、risk tags、evidence ids | 是，只读。 |
| Codex/LLM 判读 | `transcript-semantic-correction-codex-draft`、`transcript-semantic-correction-llm-draft` | evidence pack | correction result draft | Codex 可人工/半自动；云 LLM 必须显式执行。 |
| 结果校验 | `validate-transcript-semantic-correction` | result + pack | validation report | 是，只读。 |
| 闭环写入 | `transcript-semantic-correction-closure` | validated result | corrected transcript、closure report | 仅写派生产物，不改原始证据。 |
| 导出刷新 | `export-knowledge-note`、smart summary pipeline | corrected transcript + evidence | human-readable exports | 是。 |
| 影响检查 | `transcript-semantic-readable-impact-report` | corrected transcript + exports | residual report | 是，只读。 |
| 批量队列 | `transcript-semantic-repair-queue`、`transcript-semantic-repair-run` | bundle 或 batch summary | repair plan、run report | 默认 preview，显式允许后只执行安全动作。 |
| UI 工作台 | task console / video workbench | status、queue、reports | 可视化进度、按钮、失败重试 | 只调用稳定 CLI/MCP/bridge，不绕过校验。 |

原则：任何模块都不能既“生成模型判断”又“静默写入最终 transcript”。写入必须经过校验器和 closure。

## 18. Candidate Group 设计

很多错词不是单个片段的问题，而是同一个实体在全片中出现多个变体。闭环应优先按 candidate group 处理。

### 18.1 分组键

建议分组键由以下信息共同决定：

- 标准候选文本的规范化形式，例如 `playwright mcp`；
- 时间上相近且语义上属于同一段讨论；
- OCR/网页标题/课程主题中出现的强实体；
- ASR 中音近或形近的变体；
- 人工已确认词典中的 canonical。

### 18.2 分组字段

```json
{
  "candidate_group_id": "semgroup-0001",
  "canonical_hint": "Playwright MCP",
  "candidate_type": "term",
  "mentions": [
    {
      "candidate_id": "semcorr-0001",
      "time_range": {"start": 13.2, "end": 18.5},
      "original_text": "play right m c p",
      "suggested_text": "Playwright MCP",
      "segment_id": "asr-0012",
      "timeline_index": 4
    }
  ],
  "variant_texts": ["play right m c p", "playright mcp", "playwright m c p"],
  "supporting_evidence_ids": ["ev-ocr-001", "ev-title-001"],
  "risk_level": "safe_auto_apply"
}
```

### 18.3 分组带来的收益

- 避免同一个工具名重复询问模型；
- 避免一处改、一处不改；
- 方便做 residual scan；
- 方便人工一次确认一个实体，而不是几十条片段。

## 19. 证据权重建议

纠错不能简单投票。不同证据可靠性不同，需要按来源、时间对齐和冲突类型赋权。

| 证据 | 默认权重 | 说明 |
| --- | --- | --- |
| 人工确认 | 最高 | 只要不是过期或冲突，应优先采用。 |
| 屏幕 OCR/ebook 中清晰文字 | 高 | 对工具名、标题、表格、数字尤其强。空 OCR 或 wrapper-only 不能当反证。 |
| 平台标题/简介 | 高 | 对课程名、人名、工具名有帮助，但可能标题党或不完整。 |
| 多模态视觉 | 中高 | 适合补 OCR 不可读、操作动作、界面状态。对精确文字不应替代 OCR。 |
| 本地 ASR | 中 | 是完整覆盖主来源，但错词候选通常从这里产生。 |
| 平台字幕/自带字幕 | 中 | 可能是人工字幕，也可能是平台 ASR，需记录来源。 |
| 全片上下文 | 中 | 能判断语义是否合理，但不能单独证明数字或专名。 |
| 打标器标签 | 中低 | 更适合排序和提示风险，不直接证明文本。 |
| LLM 自己的常识 | 低 | 只能辅助判断，不能作为唯一证据写回。 |

## 20. 自动写入阈值

建议把自动写入拆成三档。

| 档位 | 条件 | 可写入内容 |
| --- | --- | --- |
| `A_safe` | 至少两个独立证据一致；不是数字/金额/法律金融医疗等高风险事实；上下文一致 | 工具名、品牌名、明显同音错、常见专有名词。 |
| `B_audited` | 证据强但影响事实，或只有一个强证据加上下文支持 | 可写入 corrected transcript，但必须进入 audit 和 impact report。 |
| `C_review_only` | 证据冲突、数字不稳、动作依赖画面但视觉未跑、模型理由弱 | 只进入 review pack，不自动写入。 |

数字、金额、比例、年份、合同条款、医学/法律/金融建议默认从 `B_audited` 起步，不允许直接进入 `A_safe`，除非有人工确认。

## 21. 纠正版 Transcript 的最小字段

`source-arbitrated-transcript.json` 不应只是文本列表。它需要保留足够信息，让最终导出和审计都能解释“为什么这样改”。

```json
{
  "schema": "video_knowledge_pipeline.source_arbitrated_transcript.v1",
  "segments": [
    {
      "segment_id": "asr-0012",
      "start": 13.2,
      "end": 18.5,
      "raw_text": "首先入场的是我们的开山鼻祖 play right m c p",
      "corrected_text": "首先入场的是我们的开山鼻祖 Playwright MCP",
      "corrections": [
        {
          "candidate_id": "semcorr-0001",
          "original_text": "play right m c p",
          "corrected_text": "Playwright MCP",
          "correction_type": "term",
          "confidence": 0.96,
          "decision_source": "codex_substitute_for_online_llm",
          "evidence_ids": ["ev-ocr-001", "ev-context-001"],
          "apply_policy": "safe_auto_apply"
        }
      ],
      "status": "corrected",
      "review_required": false
    }
  ]
}
```

## 22. 对最终人类可读文件的影响规则

### 22.1 `full-transcript.md`

逐字稿应默认展示纠正版文本，但保留必要标记：

```text
[00:13 - 00:18] 首先入场的是我们的开山鼻祖 Playwright MCP。

纠正：play right m c p -> Playwright MCP；证据：OCR/上下文；置信度：0.96。
```

显示策略可以分级：

- 普通高置信专名纠正：正文用纠正版，脚注/审计里记录；
- 高风险事实纠正：正文用纠正版，但在段末标注“已纠正，需审计”；
- 低置信候选：正文保留原文或用括号提示，不应静默替换。

### 22.2 `smart-summary.md`

智能总结必须优先吃 corrected transcript。要求：

- 关键术语、工具名、课程概念使用 canonical；
- 数字/金额只在 evidence 足够时进入总结；
- 低置信项集中放到“待复核点”；
- 不得把未确认纠错当成事实写进行动建议。

### 22.3 内容素材候选

内容素材层更容易被下游误用，因此策略更保守：

- 所有素材保持 `publication_allowed=false`；
- 已纠正内容可以作为灵感，但 `allowed_as_fact=false`；
- 涉及数字、金额、收益、法律/医疗/金融建议的片段必须标注 fact-check required；
- 低置信错词不得进入标题、金句、行动清单的核心表达。

## 23. 与 OCR/ebook、多模态、打标器的关系

这条闭环不是替代 OCR、ebook 或多模态，而是把它们变成 ASR/字幕纠错证据。

```text
OCR/ebook：证明屏幕上到底写了什么。
多模态：证明画面上发生了什么、讲师在指什么、界面状态是什么。
打标器：证明哪里值得优先检查，哪里是工具名/步骤/重点/疑难。
ASR/字幕纠错：把这些证据用于修正“视频说了什么”的文本主线。
```

默认策略：

- 图文型画面优先走 ebook；
- ebook 空结果、低信息量或 wrapper-only 时，标记为 OCR 证据不足；
- 只有疑难片段或高风险片段才进入在线多模态；
- 多模态可辅助动作/界面状态，不应独自做精确文字替换；
- 打标器结果用于优先级和时间段定位，不直接覆盖 transcript。

## 24. 批量修复队列语义

`transcript-semantic-repair-queue` 应把问题分成可机器处理和需人工处理两类。

| 队列类型 | 示例 | 默认动作 |
| --- | --- | --- |
| `missing_pack` | 没有 correction pack | 生成 pack。 |
| `missing_codex_or_llm_decision` | 有候选但未判读 | 生成 Codex prompt 或 LLM preview。 |
| `validation_failed` | JSON/schema/证据不足 | 保留失败原因，等待修正结果。 |
| `closure_pending` | 结果已通过校验但未写入 | 可安全执行 closure。 |
| `export_stale` | corrected transcript 已更新但 exports 未刷新 | 可安全重新导出。 |
| `impact_residual_found` | 已接受错词仍在最终文件残留 | 重新生成导出或进入人工检查。 |
| `human_review_required` | 低置信、高风险、冲突证据 | 只生成 review item，不自动写回。 |

`transcript-semantic-repair-run` 默认必须是 preview；只有显式 `execute_safe_actions=true` 才能执行 pack、validate、closure、export、impact 这类本地安全动作。云 LLM 调用必须另有 `allow_llm=true` 和 provider config。

## 25. UI 目标

任务控制台和视频工作台最终应支持以下操作：

1. 查看当前 bundle 的语义纠错状态：候选数、已判读、已写入、残留、人工复核数。
2. 一键生成/刷新 correction pack。
3. 一键生成 Codex prompt 或 LLM preview。
4. 一键校验结果。
5. 一键执行本地安全闭环：closure -> export -> impact。
6. 对失败项显示失败原因、候选文本、证据路径、推荐下一步。
7. 对人工复核项跳转到视频时间点、transcript editor、OCR/视觉证据。
8. 显示“哪些错词已经真实影响 `full-transcript.md` / `smart-summary.md`”。

UI 不能直接改 transcript。所有写入必须调用 CLI/MCP/HTTP bridge 的稳定入口。

## 26. 质量评估指标

建议每个 bundle 输出语义纠错质量指标：

| 指标 | 含义 |
| --- | --- |
| `candidate_count` | 发现多少疑似错词候选。 |
| `candidate_groups` | 合并后的实体/问题组数量。 |
| `validated_decisions` | 通过校验的纠正决策数量。 |
| `auto_applied_count` | 自动写入 corrected transcript 的数量。 |
| `human_review_count` | 需要人工复核的数量。 |
| `residual_count` | 已接受错词在最终文件中的残留数量。 |
| `summary_absorption_count` | 纠正结果被 smart-summary 直接或上下文吸收的数量。 |
| `high_risk_fact_count` | 涉及数字/金额/事实的纠正数量。 |
| `blocked_reason` | 阻塞原因，例如缺证据、缺模型判断、导出过期。 |

批量验收时，不能只看 `accepted`，还要看 residual 是否为 0、低置信项是否清楚列出。

## 27. 测试计划

### 27.1 单元测试

- 候选发现能识别工具名、数字、动作词、普通错词、断句错误。
- 多源证据能合并成 candidate group。
- 低置信或证据不足的 LLM 结果被 validator 拒绝。
- 数字类纠正没有强证据时不能自动写入。
- closure 不修改原始 ASR/字幕，只写 corrected transcript。
- readable impact 能发现 `full-transcript.md` 和 `smart-summary.md` 残留错词。
- context absorption 能识别 smart-summary 不是逐字出现纠正词、但正确吸收了纠正后的上下文。

### 27.2 集成测试

- 用 fake bundle 跑 `pack -> codex draft -> validate -> closure -> export -> impact`。
- 用含有 OCR/ebook 强证据的 frame 验证 ASR 错词可被纠正。
- 用含数字冲突的片段验证默认进入 review，不自动写入。
- 用平台字幕和本地 ASR 冲突的片段验证 source arbitration。
- 用 task console 验证 repair queue 能展示并触发本地安全动作。

### 27.3 真实验收

- 至少 3 个真实长视频 bundle；
- 每个 bundle 抽样 20-50 个候选；
- 人工抽样检查 precision：自动写入的纠正大部分应正确；
- 对比纠错前后 `smart-summary.md`：工具名、课程概念、数字风险、行动清单是否改善；
- 保留失败样本，反向补候选发现和 validator。

## 28. 阶段路线图

| 阶段 | 目标 | 完成标志 |
| --- | --- | --- |
| Phase A | 文档和 schema 固化 | 本文档、pack schema、result schema、risk policy 稳定。 |
| Phase B | 工具名/术语闭环稳定 | 已接受 alias 不再残留在 transcript/summary。 |
| Phase C | 扩展到数字、动作、普通错词、断句 | 候选发现和 validator 覆盖非术语错误。 |
| Phase D | Codex/LLM 判读批量验收 | 小批量真实 provider 或 Codex 判读通过质量抽样。 |
| Phase E | UI 队列和重试闭环 | task console 可显示进度、失败、重试和人工复核。 |
| Phase F | 批量生产可用 | 3-5 个真实 bundle accepted_with_known_gaps 或更好。 |

## 29. 人工确认边界

以下动作必须人工确认或显式开启：

- 云 LLM / 在线多模态调用；
- 数字、金额、收益、法律/医疗/金融事实的自动采用；
- 对外发布、写入正式知识库、进入朋友圈素材发布链路；
- 关闭高风险 review item；
- 删除或覆盖任何原始证据文件。

以下动作可以默认安全执行：

- 生成候选 pack；
- 生成 Codex prompt/template；
- 本地 schema validate；
- 写入派生 corrected transcript；
- 重新导出人类可读文件；
- 生成 impact/readable impact/status 报告。

## 30. 判定这个目标“真正完成”的一句话标准

当一个真实视频中出现 ASR/字幕错词时，VKP 不只是把它列在某个报告里，而是能够：

1. 说明为什么它可能错；
2. 指出哪些独立证据支持正确写法；
3. 区分可自动纠正、需审计纠正和需人工复核；
4. 把高置信结果写入纠正版 transcript；
5. 让 `full-transcript.md`、`smart-summary.md`、内容素材候选实际使用纠正后的文本；
6. 用 impact report 证明已接受错词没有继续残留；
7. 把不确定项清楚地留给人工，而不是假装解决。

只有这七件事同时成立，才算“所有 ASR/字幕疑似错词的通用语义纠错闭环”进入可生产使用状态。

## 31. Task Console Bridge 执行路径

为避免通用语义纠错停留在“复制命令”阶段，任务控制台需要提供本机 bridge 调用能力。

### 31.1 入口

静态 `task-console.html` 中的“通用语义纠错重试队列”面板应提供：

- Bridge `/call` URL 输入框，默认读取统一配置中的 `services.openclaw_http`；
- “预览”按钮：调用 `transcript_semantic_repair_run`，但 `execute_safe_actions=false`；
- “执行下一步安全动作”按钮：调用 `transcript_semantic_repair_run`，但只允许本地安全动作；
- 调用结果输出框：显示 JSON response，方便判断成功、失败、下一步。

### 31.2 安全边界

页面按钮必须强制以下参数：

```json
{
  "allow_llm": false,
  "allow_closure": false,
  "provider_config": {},
  "max_actions": 1
}
```

含义：

- 不调用云 LLM；
- 不自动关闭高风险纠错；
- 一次只执行一个本地安全动作；
- 执行后需要刷新 task console 再看新状态；
- 用户若要跑云 LLM，必须走 provider config、preflight 和显式命令，不通过这个默认按钮偷跑。

### 31.3 Bridge 契约

`openclaw_http` 需要暴露：

```text
transcript_semantic_repair_run
```

并支持浏览器从 `file://` 打开的静态页面调用本机 HTTP bridge，所以 `/call` 需要返回 CORS header，`OPTIONS` 需要返回 `204`。

### 31.4 验收

本能力的验收标准：

- `task-console.json` 包含 `bridge.schema=video_knowledge_pipeline.task_console.bridge.v1`；
- `task-console.html` 包含 `semanticRepairBridgeUrl` 和 `runSemanticRepairViaBridge`；
- `openclaw_http /health` 工具列表包含 `transcript_semantic_repair_run`；
- `/call transcript_semantic_repair_run` preview 返回 repair-run schema；
- `OPTIONS /call` 返回 `Access-Control-Allow-Origin: *`；
- 测试证明页面 payload 不带 provider key、不允许 LLM、不允许 closure。

## 32. Candidate Group 与跨片一致性

通用语义纠错不能只处理“单句里的一个错词”。真实长视频里，更常见的问题是同一个实体、概念、动作或数字在不同时间段被识别成多个变体。系统必须把这些变体归并成 candidate group，再做统一判断。

### 32.1 为什么要分组

如果逐条判断，会出现这些问题：

- `Browserbase` 在第 1 次被改对，第 2 次仍然保留 `browser base`；
- 同一个工具名在 `full-transcript.md`、`smart-summary.md`、内容素材卡中写法不一致；
- 一个数字在不同段落中被分别纠成不同结果；
- 智能总结只能吸收前几处纠错，后文仍继承 raw ASR；
- 人工审核时看到大量重复项，无法快速关闭。

因此 candidate group 的目标是：

```text
多个疑似错词变体
  -> 归并到同一 canonical hint
  -> 一次语义判断
  -> 多处 transcript segment 同步修正
  -> impact report 检查所有残留
```

### 32.2 分组对象

| 分组类型 | 示例 | canonical hint 来源 |
| --- | --- | --- |
| 工具名 / 产品名 | `browser base`、`browse base`、`Browserbase` | OCR/ebook、标题、网页元数据、上下文。 |
| 英文缩写 / 协议名 | `m c p`、`MCP`、`M C P` | OCR、已知词典、同片重复。 |
| 人名 / 品牌名 | 讲师名、公司名、课程名 | 标题、简介、PPT 首屏、人工确认。 |
| 行业术语 | 课程概念、方法论名称 | 章节标题、课件、全片重复。 |
| 数字 / 金额 / 时间 | `16k`、`一万刀`、`1500万` | OCR 表格、标题、重复上下文。 |
| 操作动作 | 登录、导入、注册、打开、点击 | 多帧视觉、软件界面状态、步骤标签。 |
| 普通错词簇 | 同音错、近音错、上下文病句 | ASR 上下文、语义判断、人工样本。 |

### 32.3 Candidate Group Schema

建议每个 group 至少包含：

```json
{
  "candidate_group_id": "semgroup-0001",
  "canonical_hint": "Browserbase",
  "correction_type": "term",
  "risk_level": "auto_apply_with_audit",
  "candidate_ids": ["semcorr-0001", "semcorr-0007"],
  "variant_texts": ["browser base", "browse base"],
  "suggested_texts": ["Browserbase"],
  "timeline_indexes": [12, 38],
  "evidence_ids": ["ev-ocr-001", "ev-context-003"],
  "evidence_source_types": ["ocr_ebook", "asr_context"],
  "time_ranges": [
    {"start": 13.2, "end": 18.5},
    {"start": 221.4, "end": 225.7}
  ],
  "candidate_count": 2,
  "evidence_count": 2,
  "needs_human_review": false,
  "reasons": [
    "same canonical hint appears in OCR",
    "multiple ASR variants are phonetically close"
  ]
}
```

### 32.4 Group 判读规则

Codex/LLM 判断时，应优先按 group 判断，而不是孤立候选：

- 如果 group 内多个候选共享强证据，可以一次性给出 canonical；
- 如果 group 内有证据冲突，整个 group 降级为 `needs_human_review`；
- 如果 group 内只有部分候选证据强，只允许修正证据足够的 candidate；
- 数字类 group 不能因为“看起来一致”就自动覆盖，必须有强证据；
- group 判断必须输出每个 candidate 的 action，不能只给 group 总结。

## 33. 通用错词类型的具体处理策略

### 33.1 专名和术语

专名和术语是最适合自动纠错的类型，因为 OCR/标题/上下文通常能提供强证据。

自动写入条件：

- 至少两个独立证据一致，或一个强证据加多次上下文重复；
- 纠正文本只替换局部错词，不改写整句意思；
- corrected text 在全片语义中稳定出现；
- 不涉及高风险事实结论。

默认产物影响：

- 写入 `source-arbitrated-transcript.json`；
- `full-transcript.md` 用 canonical；
- `smart-summary.md` 用 canonical；
- 内容素材卡列入 evidence，但仍 `publication_allowed=false`。

### 33.2 数字、金额、比例和年份

数字类必须更保守。即使 ASR 看起来明显错，也不能只靠语言模型猜。

自动写入条件：

- OCR/ebook、标题/简介、平台字幕、重复上下文中至少两个来源一致；
- 或人工明确确认；
- 或视频画面中数字非常清楚，并且 OCR confidence 高。

否则处理为：

- 保留原文；
- 在 `full-transcript.md` 或 audit 中标记 `number_needs_review`；
- 在 smart summary 的“待复核点”中列出；
- 内容素材不得把该数字作为事实卖点。

### 33.3 动作、步骤和流程词

动作词常常需要视觉证据参与。例如 ASR 说“点这个”，但真正有价值的是屏幕上的按钮名和界面状态。

处理策略：

- 先用 ASR 时间戳定位动作发生的片段；
- 查找同一时间段 OCR/ebook、视觉理解、多帧 temporal 理解；
- 如果视觉证据明确，可把 transcript 中含糊表达补成更清楚的纠正版；
- 如果视觉证据不足，不自动补写，只在 review pack 中提示。

示例：

```text
raw: 然后点这个进去
visual: 页面按钮为 “Create Session”
corrected: 然后点击 “Create Session” 进入下一步
```

这类纠正属于“语义补全”，风险高于普通专名替换，默认应进入 `auto_apply_with_audit` 或 `needs_human_review`。

### 33.4 普通 ASR 错词

普通错词没有固定词典，必须依赖上下文和语言模型判断。

进入候选的信号：

- 一句话语义明显不通；
- 同一段上下文前后矛盾；
- ASR 出现孤立口水词、无意义词、错别字串；
- smart summary 生成时出现关键词拼接或病句；
- 人工抽样标注指出该类错误。

默认策略：

- Codex/LLM 可以建议；
- validator 必须要求语义理由；
- 不允许大段润色式替换；
- 只允许改动最小必要 span；
- 低置信进入人工复核。

### 33.5 标点、断句和段落边界

标点和断句不是“错词”，但会影响智能总结质量。它们应作为 transcript 后处理分支进入同一闭环。

可自动处理：

- 句号、逗号、问号、列表分隔；
- 明显的章节边界；
- 多个短 ASR segment 合并成可读段落；
- 口语重复的轻量清理。

不可自动处理：

- 改变因果关系；
- 删除关键信息；
- 把讲师原意重写成总结；
- 将不确定内容写成确定结论。

## 34. Codex 代替在线 LLM 的执行标准

当前阶段允许 Codex 暂时代替在线文本 LLM，但不是“聊天里随便判断”。必须固定成可复现流程。

### 34.1 输入

Codex 输入应来自 bundle 内的结构化文件：

```text
transcript-semantic-correction-pack.json
transcript-semantic-correction-prompt.md
normalized-transcript.json
source-arbitrated-transcript.json（如已有）
timeline.json
OCR/ebook 证据
visual/temporal 证据
网页标题/简介/元数据
人工 review notes
```

### 34.2 输出

Codex 输出不得直接改文件，必须生成结构化结果：

```text
transcript-semantic-correction-result.codex.md
transcript-semantic-correction-result.json
```

### 34.3 禁止行为

Codex/LLM 不允许：

- 自由重写完整 transcript；
- 添加 evidence pack 中没有的事实；
- 把低置信猜测标成高置信；
- 静默修改数字、金额、年份；
- 删除原始语气中有信息量的内容；
- 把“听起来更通顺”当成唯一理由。

### 34.4 允许行为

Codex/LLM 可以：

- 结合上下文判断专名真实写法；
- 给出 minimal replacement；
- 判断候选是否应保持原文；
- 对需要视觉证据的片段标记 `needs_human_review`；
- 对重复变体给 canonical；
- 对智能总结会受影响的候选标记 `final_output_impact`。

## 35. UI 与批处理固化目标

用户不应靠复制几十条命令来跑完整纠错。最终需要在任务控制台固化为可配置队列。

### 35.1 UI 应展示

- 总候选数；
- candidate group 数；
- 按类型统计：term、number、action、ordinary_word、punctuation；
- 按风险统计：safe、audit、review、reject；
- 已生成 pack / 已判读 / 已校验 / 已写入 / 已导出 / 已检查残留；
- 失败项和失败原因；
- 下一个推荐动作；
- 可重试按钮；
- 打开 evidence / review page / transcript editor 的链接。

### 35.2 批次参数

批处理应可配置：

| 参数 | 含义 | 默认建议 |
| --- | --- | --- |
| `batch_size` | 每批处理多少个 candidate 或 group | 20-50 |
| `max_groups` | 每轮最多处理多少个 group | 10-20 |
| `include_types` | 本轮包含哪些类型 | 默认全部，数字可单独关闭 |
| `min_risk` | 最低风险等级过滤 | 默认包含 safe/audit/review |
| `allow_llm` | 是否允许在线 LLM | 默认 false |
| `allow_closure` | 是否允许写入 corrected transcript | 默认 false，需显式开启 |
| `dry_run` | 是否只预览 | 默认 true |

### 35.3 重试策略

失败项不能丢失，应形成 retry queue：

- schema 失败：要求修复 JSON；
- evidence 不足：要求补 OCR/ebook、多模态或人工；
- provider 失败：保留原批次，允许重跑；
- closure 失败：不更新导出，标记阻塞；
- impact residual：重新导出或人工检查替换规则。

## 36. 与智能总结质量的关系

这条闭环最终服务于 `smart-summary.md` 质量，而不是只服务逐字稿。

### 36.1 smart-summary 输入优先级

智能总结输入必须优先使用：

```text
source-arbitrated-transcript.json
  > corrected transcript sidecar
  > normalized-transcript.json
  > timeline transcript fallback
```

如果存在已通过 closure 的纠错，`smart-summary-input-pack` 应记录：

- 使用的是 corrected transcript；
- 应采用哪些 canonical terms；
- 哪些数字/事实仍待复核；
- 哪些视觉证据未执行；
- 哪些错词还有 residual。

### 36.2 质量检查

`smart-summary.md` 通过纠错闭环后，应满足：

- 工具名、品牌名、课程概念写法一致；
- 高置信错词不再残留；
- 数字和事实风险单独列出；
- 不把低置信候选写成确定结论；
- 行动清单不继承错误动作词；
- 章节总结覆盖全片，而非只覆盖前段；
- 待复核点集中放到末尾。

## 37. 当前完成状态与后续缺口

截至本文档更新时，目标状态应按以下方式判断：

| 项目 | 状态含义 |
| --- | --- |
| 目标和 schema 文档 | 已形成，可作为开发 checklist。 |
| 术语/工具名子链路 | 已部分落地，仍需真实批量验收。 |
| 通用候选发现 | 需要继续覆盖数字、动作、普通错词和断句。 |
| candidate group | 需要在 pack/status/UI 中稳定展示和测试。 |
| Codex 代替 LLM | 已有方向，需要固定输入输出和校验流程。 |
| corrected transcript 写入 | 必须确保高置信纠正真实进入 `source-arbitrated-transcript`。 |
| final exports 影响 | 必须用 impact report 证明 `full-transcript.md`、`smart-summary.md` 不再残留已接受错词。 |
| UI 批处理 | 需要显示进度、失败、重试和一键安全动作。 |
| 真实验收 | 需要至少 3-5 个真实 bundle 抽样验证。 |

换句话说，本目标不是“文档已写完就完成”。文档只是把目标钉住。真正完成要看：真实视频里 ASR/字幕错词能否被发现、被证据证明、被纠正、被写入、被最终输出吸收，并且不确定项能被诚实暴露。
## 38. Candidate Group 当前落地记录

更新时间：2026-07-07 07:03:51
执行者：Codex / GPT-5

本轮已把 candidate group 从“规格要求”推进到代码可见状态：

- `transcript-semantic-correction-pack.json` 写入 `candidate_group_count` 和 `candidate_groups`；
- 每个 candidate 写入 `candidate_group_id` 和 `canonical_hint`；
- `transcript-semantic-correction-status` 返回 `candidate_group_count` 和 `candidate_group_preview`；
- `transcript-semantic-correction-status.md` 显示“候选分组预览”表格；
- `task-console.html` 的通用语义纠错面板显示候选分组计数和候选分组预览表；
- 分组规则改为 canonical 优先：`browser base`、`browse base`、动作候选中的 `Browserbase` 可以归入同一组；
- group 保留 `correction_types`，允许同一 canonical 同时来自 `proper_noun`、`action` 等不同触发器；
- group 的 `variant_texts` 优先展示疑似错词片段，而不是整句动作文本。

轻量验收：

```text
python -m compileall -q src\video_knowledge_pipeline\transcript_semantic_correction.py tests\test_transcript_semantic_correction.py
直接调用 tests/test_transcript_semantic_correction.py::test_semantic_correction_pack_groups_repeated_variants_by_canonical_hint 通过
直接调用 tests/test_task_console.py::test_task_console_shows_transcript_semantic_correction_details 通过
最小 smoke bundle 通过：browser base / browse base / action Browserbase -> semgroup-0001
```

限制说明：

- `python -m pytest ...` 当前仍被 Windows pytest basetemp 清理权限问题拦截，错误为 `PermissionError: [WinError 5]`，不是该测试函数的断言失败；
- candidate group 落地只完成了候选归并和状态可见，不等于整个通用语义纠错闭环完成；
- 后续仍需补数字、动作、普通错词、断句的真实批量验收，以及 closure -> export -> impact 对最终文件的完整验证。
## 39. Closure 到最终可读文件的安全刷新落地记录

更新时间：2026-07-07 07:03:51
执行者：Codex / GPT-5

本轮把 `transcript-semantic-repair-run` 的 `run_closure` 动作从“只写 source-arbitrated transcript”推进为“写入后刷新最终可读输出并复查影响”。

执行条件保持保守：

- 仍然必须显式传入 `execute_safe_actions=true`；
- 仍然必须显式传入 `allow_closure=true`；
- 不调用云 LLM；
- 不调用 ASR、vision、下载；
- 不覆盖原始 ASR/字幕/OCR/视觉证据。

新的 `run_closure` 行为：

```text
validate result
  -> transcript_semantic_correction_closure
  -> export_knowledge_note
  -> transcript_semantic_correction_impact_report
  -> transcript_semantic_readable_impact_report
  -> transcript_semantic_summary_impact_report
```

这意味着高置信纠错不再停留在 `source-arbitrated-transcript.json`，而会在同一次允许 closure 的安全动作里刷新：

- `exports/full-transcript.md`
- `exports/smart-summary.md`
- `transcript-semantic-correction-impact-report.*`
- `transcript-semantic-readable-impact-report.*`
- `transcript-semantic-summary-impact-report.*`

轻量验收：

```text
python -m compileall -q src\video_knowledge_pipeline\transcript_semantic_batch.py tests\test_transcript_semantic_batch.py
直接调用 tests/test_transcript_semantic_batch.py::test_transcript_semantic_repair_run_closure_refreshes_readable_exports 通过
```

验收样例证明：

```text
raw transcript: 今天讲 browser base
OCR evidence: Browserbase
validated correction: browser base -> Browserbase
repair-run action: run_closure with allow_closure=true
full-transcript.md: Browserbase，无 browser base 残留
impact/readable impact: passed
summary impact report: generated
```

该能力推进了本文档第 11、22、24、30 节要求：纠错结果必须真实影响最终人类可读文件，而不是只生成中间报告。

## 40. Batch Review 视频定位与证据查看落地记录

更新时间：2026-07-07 00:00:00
执行者：Codex / GPT-5

本轮把通用语义纠错批量复核包从“可编辑 JSON 行”推进到“可以结合视频时间和证据进行审核”。

新增能力：

- `task-console.html` 的批量复核编辑器会从 `time_range` 解析候选开始时间；
- 每条 `.semantic-batch-review-row` 写入 `data-start-seconds`、`data-time-range`、`data-original-text`、`data-context-text`；
- 有可解析时间的候选显示“播放此处”按钮；
- 点击后调用 `seekToSemanticBatchReview(reviewId, seconds)`：
  - 高亮当前 review row；
  - 滚动到对应候选；
  - 更新右侧/下方 citation panel；
  - 如果用户已在控制台加载本地视频，则直接跳转到候选开始时间；
  - 如果未加载视频，则只选中候选并提示先加载视频；
- evidence 展示不再只显示 evidence id，会显示：
  - `source_type`；
  - `evidence_id`；
  - `timeline_index`；
  - `confidence`；
  - evidence text；
  - `path` 或 `frame_path`。

这个改动服务于本文档第 13、24、25 节：低置信候选不阻塞整体交付，但必须能被人工或 Codex 辅助流程有效关闭。以前 review item 虽然能导出 JSON，但人工要回到视频里核对很麻烦；现在每条候选都能带着时间戳和证据进入浏览器内审核流程。

轻量验收：

```text
python -c "import ast, pathlib; [ast.parse(pathlib.Path(p).read_text(encoding='utf-8')) for p in ['src/video_knowledge_pipeline/task_console.py','tests/test_task_console.py']] ; print('ast ok')"
=> ast ok

直接调用 tests/test_task_console.py::test_task_console_shows_semantic_batch_review_pack_panel 通过

git diff --check -- src/video_knowledge_pipeline/task_console.py tests/test_task_console.py
=> 通过
```

真实 bundle 验收：

```text
bundle: outputs/compare-5/workspace/cold-client-marketing-flow/webui-bundle
export_task_console(..., refresh=True)
task-console.html contains:
- seekToSemanticBatchReview: True
- data-start-seconds: True
- 播放此处: True
- evidence-path: True
- semantic-batch-review-row count: 49
```

限制说明：

- 浏览器静态页不能直接读取本地视频文件路径，仍需要用户在页面中选择本地视频文件后才能播放；
- 点击候选时使用的是 ASR/候选 `time_range` 的 start，不会统一减秒；
- 该能力不会自动接受纠错，也不会绕过 validate / closure；
- evidence 只展示已有 pack 信息，不伪造新的 OCR、多模态或人工证据。

## 41. 中文事实值与平台字幕冲突候选发现落地记录

更新时间：2026-07-07 00:00:00
执行者：Codex / GPT-5

本轮继续补齐第 5、7、9、15 节要求，把候选发现从“阿拉伯数字和明显工具名”扩展到两类更常见的视频转写错误：

1. 中文口播事实值。
   - 例如“一万六千块”“两个月”“第三步”“十家公司”；
   - 这类内容没有阿拉伯数字，也可能没有英文单位，但仍然属于高风险数字/金额/时间/步骤信息；
   - 现在候选发现统一走 `_fact_value_markers()`，同时覆盖 `NUMBER_RE` 和 `CHINESE_FACT_VALUE_RE`；
   - 生成的候选仍是 `correction_type=number`、`risk_level=high`、`needs_human_review=true`。

2. 平台字幕/自带字幕与 ASR 的具体冲突。
   - 平台字幕可能更准，也可能同样是 ASR 错误；
   - 现在冲突提取会优先识别支持证据里的事实值和专名 token；
   - 如果本地 ASR 说 `open client`，平台字幕写 `OpenClaw`，pack 会生成 `subtitle_text_differs_from_transcript` 候选；
   - 这只是候选，不代表平台字幕自动胜出，仍要经过 Codex/LLM/人工判断和 validate。

代码变化：

- `src/video_knowledge_pipeline/transcript_semantic_correction.py`
  - `_candidate_rows_for_text()` 的数字候选由 `NUMBER_RE.findall()` 改为 `_fact_value_markers()`；
  - `_visual_conflict_text()` 优先抽取 support evidence 中的 fact value marker；
  - `_suspicious_span()` 在支持证据是数字/事实值时，优先回到 ASR 文本中定位原始事实值片段。

新增测试：

- `test_semantic_correction_pack_flags_chinese_fact_values_and_visual_numeric_conflict`
  - 验证“一万六千块”会进入 number 候选；
  - 验证 OCR/视觉证据 `16k` 会作为 `visual_text_differs_from_transcript` 的候选建议；
  - 验证该候选仍然需要人工/强证据，不会自动闭环。

- `test_semantic_correction_pack_flags_platform_subtitle_as_conflict_evidence`
  - 验证 `open client` vs `OpenClaw` 会生成 `subtitle_text_differs_from_transcript` 候选；
  - 验证候选类型为 `proper_noun`；
  - 验证 evidence source 包含 `platform_subtitle`。

轻量验收：

```text
python -c "import ast, pathlib; [ast.parse(pathlib.Path(p).read_text(encoding='utf-8')) for p in ['src/video_knowledge_pipeline/transcript_semantic_correction.py','tests/test_transcript_semantic_correction.py']] ; print('ast ok')"
=> ast ok

直接调用新增两个测试函数
=> new semantic fact tests ok

直接调用已有数字风险回归测试：
- test_semantic_correction_validation_rejects_risky_number_without_strong_evidence
- test_semantic_correction_validation_rejects_mislabeled_fact_value_change_without_strong_evidence
=> number regression tests ok

git diff --check -- src/video_knowledge_pipeline/transcript_semantic_correction.py tests/test_transcript_semantic_correction.py
=> 通过
```

真实 bundle 只读 smoke：

```text
bundle: outputs/compare-5/workspace/cold-client-marketing-flow/webui-bundle
build_transcript_semantic_correction_pack(write=False)
status: pack_ready
candidate_count: 57
by_type: {'number': 21, 'segment_boundary': 12, 'action': 8, 'proper_noun': 8, 'ordinary_word': 8}
```

限制说明：

- 中文事实值候选只负责进入 pack，不自动改数字；
- OCR/字幕中的 `16k` 等支持证据只作为候选建议，不直接覆盖 ASR；
- 低置信冲突仍要通过 validate / closure / impact report；
- 当前只补候选发现和校验覆盖，尚未声称整个通用语义纠错闭环完成。

## 42. 普通语义错词的保守字幕冲突候选落地记录

更新时间：2026-07-07 00:00:00
执行者：Codex / GPT-5

本轮补齐第 5.3、5.6、8、15 节里“普通 ASR 错词 / 字幕源也可能错 / Codex 或 LLM 只能仲裁候选”的一部分代码路径。

设计依据：

- 参考已吸收的 PrideWood/BiliNote transcript correction 思路：只校正 transcript，不总结、不扩写、不改变片段 index；
- VKP 不直接采用“整段自由改写”，而是把这个约束收窄成候选发现规则：同一时间段 ASR 与平台/自带字幕高度相似，但局部字词不同，才生成普通错词候选；
- 该候选仍然不自动闭环，必须经过 Codex/LLM/人工判断、validate、closure 和 impact report。

新增能力：

- 新增 `_ordinary_subtitle_diff_candidate(text, sidecar_text)`；
- 使用 `difflib.SequenceMatcher` 比较同时间段 ASR 和字幕文本；
- 只在以下条件同时满足时生成候选：
  - 两段文本都有足够长度；
  - 整体相似度较高；
  - 长度比例接近，说明是同一句而不是不同内容；
  - 局部差异为 1-8 个汉字；
  - 不包含英文专名冲突；
  - 不包含数字/金额/时间事实值冲突；
- 生成候选类型为 `ordinary_word`，reason 为 `ordinary_word_conflict_between_asr_and_subtitle`。

这使得如下情况能进入统一语义纠错闭环：

```text
ASR: 今天我们讲客户新任建立方法
平台字幕: 今天我们讲客户信任建立方法
=> candidate: 新 -> 信
=> correction_type=ordinary_word
=> evidence_source_types includes platform_subtitle
```

同时，数字冲突不会被误标成 ordinary word：

```text
ASR: 他说底薪是一万六千块
平台字幕: 他说底薪是 16k
=> candidate type remains number
=> needs_human_review=true
```

代码变化：

- `src/video_knowledge_pipeline/transcript_semantic_correction.py`
  - 引入 `difflib`；
  - `_candidate_rows_for_text()` 增加普通字幕冲突候选；
  - 新增 `_ordinary_subtitle_diff_candidate()`；
  - 新增 `_semantic_diff_compact()` 用于保守相似度比较。

新增测试：

- `test_semantic_correction_pack_flags_ordinary_word_conflict_between_asr_and_subtitle`
  - 验证 `新 -> 信` 这类普通错词进入 pack；
  - 验证 evidence source 包含 `platform_subtitle`。

- `test_semantic_correction_pack_keeps_numeric_subtitle_conflict_as_number`
  - 验证事实值冲突仍走 `number`，不会被普通错词规则抢走。

轻量验收：

```text
python -c "import ast, pathlib; [ast.parse(pathlib.Path(p).read_text(encoding='utf-8')) for p in ['src/video_knowledge_pipeline/transcript_semantic_correction.py','tests/test_transcript_semantic_correction.py']] ; print('ast ok')"
=> ast ok

直接调用新增与相关回归测试：
- test_semantic_correction_pack_flags_ordinary_word_conflict_between_asr_and_subtitle
- test_semantic_correction_pack_keeps_numeric_subtitle_conflict_as_number
- test_semantic_correction_pack_flags_chinese_fact_values_and_visual_numeric_conflict
- test_semantic_correction_pack_flags_platform_subtitle_as_conflict_evidence
=> ordinary and conflict tests ok

git diff --check -- src/video_knowledge_pipeline/transcript_semantic_correction.py tests/test_transcript_semantic_correction.py
=> 通过
```

真实 bundle 只读 smoke：

```text
bundle: outputs/compare-5/workspace/cold-client-marketing-flow/webui-bundle
build_transcript_semantic_correction_pack(write=False)
status: pack_ready
candidate_count: 57
by_type: {'number': 21, 'segment_boundary': 12, 'action': 8, 'proper_noun': 8, 'ordinary_word': 8}
ordinary_reasons: {'fragmented_or_semantically_weak_phrase': 8}
```

说明：该真实 bundle 没有触发新的同时间段字幕冲突普通错词规则；新增能力由专门 fixture 验证。这个结果是合理的，因为普通错词规则故意保守，避免把平台字幕差异大、OCR 页面文字或章节标题误当成逐字稿纠正。

限制说明：

- 新规则只生成候选，不自动改 transcript；
- 平台字幕不是默认真相；它只是候选证据；
- 英文专名和数字事实值仍走各自更严格的类型；
- 还需要继续补“无字幕时由全片语义和上下文发现普通错词”的 LLM/Codex 判读路径。

## 43. 无字幕场景下 OCR/视觉文字支持的普通错词候选落地记录

更新时间：2026-07-07 00:00:00
执行者：Codex / GPT-5

本轮继续补齐“没有平台字幕时，仍能利用 OCR/ebook、视觉文字、打标器证据发现普通 ASR 错词”的路径。

上一轮普通错词主要依赖同时间段平台/自带字幕对照；这轮将同一套保守差异检测复用到 OCR/ebook 和视觉文字，但仍然不使用网页标题/简介做普通错词替换，避免标题污染局部 transcript。

新增能力：

- `_ordinary_subtitle_diff_candidate()` 改为复用通用 `_ordinary_support_diff_candidate()`；
- `_candidate_rows_for_text()` 现在会分别检查：
  - `ordinary_word_conflict_between_asr_and_subtitle`；
  - `ordinary_word_conflict_between_asr_and_visual_text`；
  - `ordinary_word_conflict_between_asr_and_tagger`；
- 当 OCR/视觉文字只是 ASR 句子中的短片段时，新增 `_best_semantic_diff_window()` 做局部滑动窗口比较；
- 只有局部窗口和支持文本高度相似，且差异为短中文片段时才生成候选。

示例：

```text
ASR: 今天我们讲客户新任建立方法
OCR/视觉文字: 客户信任建立方法
=> candidate: 新 -> 信
=> reason=ordinary_word_conflict_between_asr_and_visual_text
=> correction_type=ordinary_word
=> 只进入 pack，不自动 closure
```

安全边界：

- 英文专名冲突仍走 proper noun / term 路径；
- 数字、金额、时间、步骤编号仍走 number 高风险路径；
- OCR/视觉支持短语必须与 ASR 局部高度相似，否则不生成普通错词候选；
- 不用 metadata/page title 做普通错词候选，避免标题和简介泛化污染；
- 该规则只生成候选，不自动修改 transcript。

新增测试：

- `test_semantic_correction_pack_flags_ordinary_word_conflict_from_visual_text_without_subtitle`
  - 验证没有平台字幕时，OCR/视觉文字 `客户信任建立方法` 能支持 ASR `客户新任建立方法` 生成 `新 -> 信` 候选；
  - 验证 evidence source 包含 `ocr`。

回归测试：

- `test_semantic_correction_pack_flags_ordinary_word_conflict_between_asr_and_subtitle`
- `test_semantic_correction_pack_keeps_numeric_subtitle_conflict_as_number`

轻量验收：

```text
python -c "import ast, pathlib; [ast.parse(pathlib.Path(p).read_text(encoding='utf-8')) for p in ['src/video_knowledge_pipeline/transcript_semantic_correction.py','tests/test_transcript_semantic_correction.py']] ; print('ast ok')"
=> ast ok

直接调用新增和相关回归测试
=> visual ordinary tests ok

git diff --check -- src/video_knowledge_pipeline/transcript_semantic_correction.py tests/test_transcript_semantic_correction.py
=> 通过
```

真实 bundle 只读 smoke：

```text
bundle: outputs/compare-5/workspace/cold-client-marketing-flow/webui-bundle
status: pack_ready
candidate_count: 57
by_type: {'number': 21, 'segment_boundary': 12, 'action': 8, 'proper_noun': 8, 'ordinary_word': 8}
ordinary_reasons: {'fragmented_or_semantically_weak_phrase': 8}
visual_ordinary_examples: []
```

说明：真实 bundle 没有触发新增视觉普通错词规则，也没有候选异常膨胀。这符合设计预期：该规则只在 OCR/视觉文字与 ASR 局部高度相似时触发。

该能力推进了“无字幕时也能利用画面证据发现普通错词”的目标，但还没有完成所有普通语义错词发现。下一步仍需让 Codex/LLM 基于完整上下文生成候选草稿，并通过 validate/closure/impact 接入最终输出。

## 44. Codex/LLM 候选发现层落地记录

更新时间：2026-07-07 00:00:00
执行者：Codex / GPT-5

本轮补上“规则没有抓到时，让 Codex/LLM 发现疑似错词候选”的前置层。它解决的是普通语义错词、上下文错词、漏词、打标器/OCR/字幕无法用简单规则直接对齐时的候选召回问题。

关键原则：

- Codex/LLM 在这一层只负责发现候选，不负责最终纠错；
- 导入结果只会追加到 `transcript-semantic-correction-pack.json` 的 candidates；
- 不写 `source-arbitrated-transcript.json`，不改 ASR 原文，不改最终可读文件；
- 后续仍必须走：`validate-transcript-semantic-correction -> transcript-semantic-correction-closure -> impact/readable impact`；
- 数字、金额、日期、事实值、专名仍保留高风险人工复核边界。

新增入口：

```powershell
python -m video_knowledge_pipeline.cli transcript-semantic-candidate-discovery-pack <bundle_dir> --limit 40
python -m video_knowledge_pipeline.cli import-transcript-semantic-candidate-suggestions <bundle_dir> --input-json <suggestions-json-or-md>
```

新增 MCP 工具：

```text
transcript_semantic_candidate_discovery_pack
import_transcript_semantic_candidate_suggestions
```

新增产物：

```text
transcript-semantic-candidate-discovery-pack.json
transcript-semantic-candidate-discovery-prompt.md
transcript-semantic-candidate-discovery-template.json
transcript-semantic-candidate-suggestions-import.json
mcp-transcript-semantic-candidate-discovery-pack.args.json
mcp-import-transcript-semantic-candidate-suggestions.args.json
```

候选发现 prompt 的输入材料：

- ASR / 字幕 segment 文本；
- 同时间段平台字幕、自带字幕；
- OCR / ebook 图文识别结果；
- structured visual / visual understanding / temporal visual；
- 青龙打标器和 timeline 标签；
- 页面标题、简介等 metadata 只作为辅助背景，不直接作为局部错词替换证据。

候选发现 scoring 目前使用：

- 已有规则候选；
- “这里/这个/看屏幕”等指代性表达；
- 断裂、低信息量、长无标点 ASR；
- 编码噪声；
- 数字/金额/日期等事实值；
- OCR/视觉/字幕/打标器与 ASR 存在局部语义差异；
- 是否具备跨模态或 sidecar 证据。

导入 schema：

```json
{
  "schema": "video_knowledge_pipeline.transcript_semantic_candidate_suggestions.v1",
  "source": "codex_or_llm_candidate_discovery",
  "suggestions": [
    {
      "source_segment_index": 0,
      "start": 0,
      "end": 4,
      "correction_type": "ordinary_word",
      "original_text": "疑似错词原文片段，必须来自 segment 文本",
      "candidate_text": "可能正确写法；不确定则留空",
      "reason": "为什么它疑似错，不要写成最终结论",
      "confidence": 0.0,
      "evidence_summary": "引用 ASR/字幕/OCR/视觉/打标器/上下文证据",
      "needs_human_review": true
    }
  ]
}
```

安全校验：

- `original_text` 必须出现在对应 ASR segment 中；
- 找不到 segment 或原文片段不匹配时跳过；
- 和已有 candidate 重复时跳过；
- 非法 `correction_type` 降级为 `ordinary_word`；
- 导入后重新分组、刷新 pack、模板和 MCP args；
- 仍不允许跳过 validate/closure。

轻量验收：

```text
AST parse:
- transcript_semantic_correction.py
- cli.py
- mcp_server.py
- tests/test_transcript_semantic_correction.py
=> ast ok

Repo-local smoke:
pack=6
candidate-discovery selected segments=2
imported discovered candidates=1
merged pack candidates=7
source-arbitrated-transcript.json exists=false
```

已知边界：

- 这一层目前只生成 prompt 和导入 suggestions，不自动调用在线 LLM；
- pytest 在当前 Windows Temp 权限下仍会被 `pytest-of-%USERNAME%` 权限阻断，本轮用 AST 和 repo-local smoke 验证；
- 真实长视频 bundle 还需要下一轮跑 discovery pack，看候选召回是否提高，尤其是普通语义错词和工具名上下文错词。

## 45. 候选发现 LLM Provider 层落地记录

更新时间：2026-07-07 00:00:00
执行者：Codex / GPT-5

第 44 节已经补上 Codex/LLM 候选发现 prompt 和 suggestions 导入。本轮继续把它接到 VKP 现有 text LLM provider 层，形成和 `transcript-semantic-correction-llm-draft` 类似的 preview-first 执行入口。

新增入口：

```powershell
python -m video_knowledge_pipeline.cli transcript-semantic-candidate-discovery-llm-draft <bundle_dir> --limit 40
python -m video_knowledge_pipeline.cli transcript-semantic-candidate-discovery-llm-draft <bundle_dir> --provider-config <provider-config.json> --execute --limit 40
```

新增 MCP 工具：

```text
transcript_semantic_candidate_discovery_llm_draft
```

新增产物：

```text
transcript-semantic-candidate-discovery-llm-prompt.md
transcript-semantic-candidate-suggestions.llm.json
transcript-semantic-candidate-suggestions.llm.md
transcript-semantic-candidate-suggestions.llm.raw.txt
mcp-transcript-semantic-candidate-discovery-llm-draft.args.json
```

执行边界：

- 默认 `execute=false`，只写 prompt 和 MCP args，不调用云端；
- 显式 `--execute` 才会调用 text LLM provider；
- API key 仍只从环境变量或显式 provider config 读取，不写入 manifest/report/docs；
- 即使 `execute=true` 成功，也只保存 `suggestions`；
- 不自动导入 suggestions，不自动 validate，不自动 closure，不改最终可读文件；
- 下一步仍必须手动或 agent 显式调用 `import-transcript-semantic-candidate-suggestions`，再进入 validate/closure/impact。

Provider 层复用：

- 复用 `text_llm_gateway.resolve_text_provider_config`；
- 复用 OpenAI-compatible chat completions 请求；
- 复用 JSON extraction/repair 逻辑；
- parse 失败时保存 raw output，避免污染 pack；
- provider public config 不包含 API key。

新增测试覆盖：

```text
test_semantic_candidate_discovery_llm_draft_preview_writes_prompt_only
```

验证内容：

- preview 状态为 `planned`；
- 不调用模型；
- 写出 `transcript-semantic-candidate-discovery-llm-prompt.md`；
- 写出 `mcp-transcript-semantic-candidate-discovery-llm-draft.args.json`；
- 不写 `transcript-semantic-candidate-suggestions.llm.json`；
- 不写 `source-arbitrated-transcript.json`。

轻量验收：

```text
AST parse:
- transcript_semantic_correction.py
- cli.py
- mcp_server.py
- tests/test_transcript_semantic_correction.py
=> ast ok

repo-local preview smoke:
status=planned
execute=false
segments=2
suggestions=0
prompt_exists=true
args_exists=true
llm_json_exists=false
manifest_has_prompt=true

真实 bundle 只读 preview:
bundle=outputs/compare-5/workspace/cold-client-marketing-flow/webui-bundle
status=planned
segments=5
suggestions=0
execute=false
```

当前目标状态变化：

- 之前只能生成候选发现 prompt，再由 Codex/人工手动填 suggestions；
- 现在已经具备可接在线或本地 text LLM 的稳定 provider 层；
- 但 provider 输出仍只是候选建议，不会越过本地安全门禁；
- 这为后续“用真实在线/本地 LLM 处理更多非安全普通语义错词”补上了基础接口。

剩余重点：

1. 在 Task Console 中显示 candidate discovery / LLM discovery 的状态和下一步命令。
2. 用真实 provider 在小批量样本上执行一次，不自动导入，人工检查 suggestions 质量。
3. 把高质量 suggestions 导入 pack 后，继续验证 validate/closure/impact。
4. 扩大真实视频类型覆盖，尤其是普通同音错词、机构名、人名、数字、动作步骤。

## 46. Candidate Discovery 接入任务控制台记录

更新时间：2026-07-07 12:14:41
执行者：Codex / GPT-5

第 45 节补好了候选发现的 LLM provider 入口。本轮继续把这条链路接入 VKP 的静态 Task Console，让人和 agent 都能在同一个控制台里看到“发现疑似错词候选 -> 可选 LLM 发现 -> 导入 suggestions”的完整下一步，而不是只靠记命令。

### 46.1 新增控制台命令

`task-console.json` / `task-console.html` 现在会暴露三条命令：

```text
transcript_semantic_candidate_discovery
transcript_semantic_candidate_discovery_llm
import_transcript_semantic_candidate_suggestions
```

对应 CLI：

```powershell
.\scripts\video-knowledge.ps1 transcript-semantic-candidate-discovery-pack <bundle_dir> --limit 40
.\scripts\video-knowledge.ps1 transcript-semantic-candidate-discovery-llm-draft <bundle_dir> --limit 40
.\scripts\video-knowledge.ps1 import-transcript-semantic-candidate-suggestions <bundle_dir> --input-json <bundle_dir>\transcript-semantic-candidate-suggestions.codex.md
```

三条命令的边界分别是：

| 命令 | 类型 | 默认是否调用云端 | 是否修改最终转写 | 用途 |
|---|---:|---:|---:|---|
| `transcript_semantic_candidate_discovery` | preview | 否 | 否 | 从已有 pack 中挑出更值得让 Codex/LLM 检查的片段，生成 prompt/template。 |
| `transcript_semantic_candidate_discovery_llm` | preview | 否 | 否 | 生成 LLM 候选发现计划；只有显式 `--execute` 才调用 provider。 |
| `import_transcript_semantic_candidate_suggestions` | review/import | 否 | 否 | 把人工/Codex/LLM 返回的 suggestions 追加为普通 semantic candidates。 |

注意：导入 suggestions 也只是增加候选，不会直接覆盖 transcript。后续仍必须经过 `validate-transcript-semantic-correction`、`transcript-semantic-correction-closure`、impact report 和导出刷新。

### 46.2 新增 Manifest 与 MCP Args

`export-task-console` 现在会稳定写入这些 manifest 字段：

```text
transcript_semantic_candidate_discovery_pack_json
transcript_semantic_candidate_discovery_prompt_markdown
transcript_semantic_candidate_discovery_template_json
transcript_semantic_candidate_discovery_llm_prompt_markdown
transcript_semantic_candidate_suggestions_llm_markdown
transcript_semantic_candidate_suggestions_import_json
mcp_transcript_semantic_candidate_discovery_pack_args
mcp_transcript_semantic_candidate_discovery_llm_draft_args
mcp_import_transcript_semantic_candidate_suggestions_args
```

同时写出对应 MCP args 文件：

```text
mcp-transcript-semantic-candidate-discovery-pack.args.json
mcp-transcript-semantic-candidate-discovery-llm-draft.args.json
mcp-import-transcript-semantic-candidate-suggestions.args.json
```

默认 MCP args 保持安全边界：

```json
{
  "execute": false,
  "provider_config": {}
}
```

这意味着 OpenClaw / Codex / 其他 agent 可以稳定读取这些 args，但不会因为打开控制台或导出控制台就触发云模型调用。

### 46.3 UI 可见性

`task-console.html` 现在能显示：

```text
语义错词候选发现 Prompt
LLM 候选发现计划
导入候选发现 suggestions
```

对应 artifact 链接包括：

```text
transcript-semantic-candidate-discovery-prompt.md
transcript-semantic-candidate-discovery-pack.json
transcript-semantic-candidate-discovery-llm-prompt.md
transcript-semantic-candidate-suggestions.llm.md
transcript-semantic-candidate-suggestions-import.json
mcp-transcript-semantic-candidate-discovery-pack.args.json
mcp-transcript-semantic-candidate-discovery-llm-draft.args.json
mcp-import-transcript-semantic-candidate-suggestions.args.json
```

如果 prompt 或 suggestions 尚未生成，控制台仍会给出可复制命令；如果产物已存在，artifact 区会显示可点击路径。

### 46.4 验证记录

语法检查：

```text
python -c "import ast ..."
=> ast ok
```

函数级真实 bundle smoke：

```text
bundle=outputs/compare-5/workspace/cold-client-marketing-flow/webui-bundle
has_discovery_cmd=true
has_llm_cmd=true
has_import_cmd=true
has_discovery_artifact=true
has_llm_artifact=true
artifact_count=80
```

最小 bundle 合同 smoke：

```text
ok=true
commands=[
  transcript_semantic_candidate_discovery,
  transcript_semantic_candidate_discovery_llm,
  import_transcript_semantic_candidate_suggestions
]
llm_execute_default=false
```

Whitespace 检查：

```text
git diff --check -- src/video_knowledge_pipeline/task_console.py tests/test_task_console.py ...
=> no whitespace error
```

已知测试限制：

- 直接跑 `pytest tests/test_task_console.py::test_export_task_console_writes_human_ui_and_agent_json` 仍被当前 Windows pytest 临时目录权限阻断；
- 指定 `--basetemp` 到 `C:\tmp` 和仓库内临时目录也被同类权限问题影响；
- 因此本轮用 AST、函数级 smoke、最小 bundle 合同 smoke 和 `git diff --check` 做验证。

### 46.5 当前目标状态

现在通用 ASR/字幕语义纠错闭环已经形成四层：

1. **候选生成**：规则和证据源生成初始 semantic candidates。
2. **候选发现**：Codex/LLM 反向扫 ASR/OCR/字幕/上下文，补漏“规则没发现的疑似错词”。
3. **候选判读**：Codex/LLM/人工判断候选是否应纠正，给出证据和置信度。
4. **安全闭环**：validate -> closure -> impact -> export，只有高置信或已审核结果进入最终可读文件。

这解决了一个关键问题：纠错对象不再局限于工具名/术语表，也可以覆盖所有“有其他证据证明可能出错”的 ASR/字幕词语。

### 46.6 剩余缺口

还没有完全结束的部分：

1. `candidate_discovery` 还没有进入批量 repair queue 的自动下一步编排。
2. 真实 provider 小批量执行还没验收 suggestions 质量。
3. 高质量 suggestions 导入后，需要继续跑 validate/closure/impact，确认能稳定影响 `source-arbitrated-transcript.json`、`full-transcript.md`、`smart-summary.md`。
4. 需要进一步把“候选发现数量、导入数量、已关闭数量、仍需人工复核数量”显示成 Task Console 的状态摘要，而不只是命令和 artifact。
## 47. Candidate Discovery 进入批量修复队列记录

更新时间：2026-07-07 12:26:26
执行者：Codex / GPT-5

本轮把第 46 节的 Task Console 入口继续接入批量修复队列：`no_candidates` 不再自动意味着“没有疑似错词”。如果 candidate discovery 尚未运行，`transcript_semantic_repair_queue` 会输出 `needs_candidate_discovery` 和 `run_candidate_discovery`。

新增状态字段：

```text
candidate_discovery_status
candidate_discovery_next_action
candidate_discovery_segment_count
candidate_discovery_suggestion_count
candidate_discovery_imported_candidate_count
candidate_discovery_skipped_count
```

新增安全队列动作：

```text
run_candidate_discovery
run_candidate_discovery_llm_preview
import_candidate_suggestions
```

边界：这些动作不调用云、不改最终 transcript。导入 suggestions 只是增加 candidates；后续仍必须 validate、closure、impact。

验证：

```text
initial_action=run_candidate_discovery
run_status=executed
result_status=discovery_prompt_ready
after_action=run_candidate_discovery_llm_preview
after_discovery_status=prompt_ready
git diff --check clean
```

## 48. Candidate Suggestions 预览和 Codex Suggestions 状态识别

更新时间：2026-07-07 12:52:00
执行者：Codex / GPT-5

本轮把 candidate discovery 的 Codex 替代路径补进状态机和 Task Console。

### 48.1 新增状态识别要求

`transcript-semantic-candidate-suggestions.codex.md` 是用户/Codex 手动填写候选召回结果的默认文件。只要这个文件存在且能解析出 suggestions，状态机必须返回：

```text
candidate_discovery_status=suggestions_ready
candidate_discovery_next_action=import_candidate_suggestions
candidate_discovery_suggestion_count>0
candidate_discovery_artifacts.codex_suggestions_markdown=<path>
```

如果 suggestions 已经导入，则状态变为：

```text
candidate_discovery_status=imported
candidate_discovery_next_action=validate_result
candidate_discovery_imported_candidate_count>0
```

### 48.2 Task Console 要求

Task Console 必须显示一个 `候选发现 suggestions 预览` 子面板，至少包含：

- suggestions 来源路径；
- suggestions 总数；
- 前若干条候选的 segment、类型、原文、建议、置信度和理由；
- 导入后的 candidate ids；
- 导入跳过项和跳过原因；
- `import-transcript-semantic-candidate-suggestions` 命令。

该面板只读，不直接执行云 LLM，不直接写 transcript。

### 48.3 安全边界

- Codex/LLM suggestions 只是候选召回，不是纠正决定。
- `import-transcript-semantic-candidate-suggestions` 只把 suggestions 变成 standard candidates。
- 真正进入最终 transcript 前仍必须走 semantic decision、validate、closure、readable impact、summary impact。
- 低置信 suggestions 可以保留为 review / known gaps，不阻塞整体视频交付。
## 49. Suggestions 导入后的状态机顺序

更新时间：2026-07-07 13:15:00
执行者：Codex / GPT-5

导入 candidate suggestions 后，系统不能直接进入 validate。原因是 suggestions 只是候选召回，不是 correction decisions。

正确状态机：

```text
suggestions_ready
  -> import_candidate_suggestions
  -> needs_llm_or_codex_review / run_llm_draft_preview
  -> codex_draft_ready 或 llm executed
  -> validate_result / validate_llm_result
  -> needs_closure
  -> impact / readable impact / summary impact
```

实现要求：

- `candidate_discovery_next_action` 在 imported candidates 后返回 `run_llm_draft_preview`。
- 全局 `next_action_key` 在 `candidate_count>0` 且 validation 缺失时返回 `run_llm_draft_preview`。
- repair queue 必须把该状态映射为机器可执行的 local preview 动作。
- batch markdown 不得提示用户直接 validate 不存在的 result。

安全边界：

- `run_llm_draft_preview` 默认只生成 prompt，不调用云。
- 若用户选择 Codex 替代在线 LLM，可生成本地 `transcript-semantic-correction-result.codex.*`。
- validate 只在 result 已存在后执行。
## 50. 低风险高置信普通语义错词自动闭环落地记录

更新时间：2026-07-07 13:48:07
执行者：Codex / GPT-5

### 50.1 本次补强目标

此前 	ranscript-semantic-candidate-discovery-codex-draft 能从 ASR、OCR/ebook、视觉、打标器、平台字幕和元数据中发现普通语义疑难点，但生成的 suggestions 默认全部
eeds_human_review=true。这会导致导入后的候选只能进入 review 或人工确认，不能形成真正的纠正版 transcript，也就不能稳定影响 ull-transcript.md 和 smart-summary.md。

本次补强把其中一类安全范围明确的候选打通：

- 候选必须来自 candidate discovery suggestions 导入，而不是原始 pack 里的普通候选。
- 候选必须是低风险类型：proper_noun、	erm、concept、ordinary_word。
- 候选必须有 OCR/ebook、结构化视觉、视觉理解、连续片段理解、打标器、平台字幕、内嵌字幕或人工笔记等强证据。
- 候选不得涉及数字、金额、比例、年份等事实值。
- 候选不得涉及点击、登录、保存、注册、运行等动作步骤改写。
- 候选长度必须可控，避免把长段总结误写成逐字稿。
- 候选仍必须经过现有 alidate-transcript-semantic-correction 校验，不能绕过 evidence ids、confidence、conflict 和高风险规则。

### 50.2 代码落地

新增/修改位置：

- src/video_knowledge_pipeline/transcript_semantic_correction.py
  - 新增 _candidate_draft_generic_correction：只对 candidate discovery 导入的低风险高置信候选生成
eplace decision。
  - 调整 uild_transcript_semantic_correction_codex_draft：在原有工具名/术语内置纠错之外，增加通用低风险语义候选的 decision 生成。
  - 新增 _candidate_discovery_auto_safe：在候选发现阶段判断是否可以把 suggestion 标成
eeds_human_review=false。
  - 调整 _codex_discovery_suggestion：支持显式
eeds_human_review。
  - 调整 _best_candidate_discovery_support_phrase：证据来源优先级高于短语长度，避免 tagger/metadata 的长文本压过 OCR/ebook 的直接屏幕文字。

- 	ests/test_transcript_semantic_correction.py
  - 补齐 candidate discovery 相关函数导入。
  - 新增 	est_semantic_candidate_discovery_high_confidence_visual_support_reaches_readable_outputs：验证低风险 OCR/视觉强证据候选能进入纠正版 transcript，并刷新到 ull-transcript.md 和 smart-summary.md。

### 50.3 标准链路

`powershell
.\scripts\video-knowledge.ps1 build-transcript-semantic-correction-pack <bundle>
.\scripts\video-knowledge.ps1 transcript-semantic-candidate-discovery-codex-draft <bundle>
.\scripts\video-knowledge.ps1 import-transcript-semantic-candidate-suggestions <bundle> --input-json <bundle>\transcript-semantic-candidate-suggestions.codex.md
.\scripts\video-knowledge.ps1 transcript-semantic-correction-codex-draft <bundle>
.\scripts\video-knowledge.ps1 validate-transcript-semantic-correction <bundle> --input-json <bundle>\transcript-semantic-correction-result.codex.md
.\scripts\video-knowledge.ps1 transcript-semantic-correction-closure <bundle> --input-json <bundle>\transcript-semantic-correction-result.codex.md --refresh-exports
`

### 50.4 验证记录

已通过：

`powershell
python -m py_compile src\video_knowledge_pipeline\transcript_semantic_correction.py tests\test_transcript_semantic_correction.py
`

已通过直接 smoke：

`powershell
='src'
python semantic-refresh-smoke-run\generic_visual_support_smoke2.py
`

该 smoke 覆盖：

- ASR/字幕文本存在普通语义错词或低信息表达。
- timeline 中 OCR/结构化视觉提供更具体候选。
- candidate discovery 生成
eeds_human_review=false 的低风险 suggestion。
- suggestion 导入 correction pack。
- Codex draft 生成唯一
eplace decision。
- validate 接受该 decision。
- closure 生成 source-arbitrated-transcript.json。
- --refresh-exports 刷新 ull-transcript.md 和 smart-summary.md。
- readable impact report 返回 passed。

未能稳定运行 pytest 的原因不是断言失败，而是当前 Windows/Codex 环境创建 pytest asetemp 时出现 PermissionError: [WinError 5]。因此本次以 py_compile 和直接 smoke 作为实测证据。

### 50.5 安全边界

本次补强没有放宽高风险规则：

-
umber、punctuation、segment_boundary 仍属于高风险类型。
- 动作/步骤变化仍需要强视觉/连续片段证据或人工确认。
- 候选如果
eeds_human_review=true，validate 仍会拒绝非人工确认的自动写入。
- 原始 ASR、平台字幕、OCR、视觉证据文件不被覆盖。

### 50.6 当前剩余缺口

这个目标仍未完全完成，后续至少还要补：

- 数字、金额、比例、年份的更强证据校验和真实样例验收。
- 动作/步骤词的多帧视觉证据自动确认。
- 平台字幕、自带字幕、ASR 三源冲突的分组仲裁。
- 人工 review notes 回写后的批量 closure 验证。
- 真实长视频 bundle 上的多类型候选覆盖率报告。
- Task Console 中对这类 candidate discovery suggestions、导入、Codex draft、closure 刷新的进度显示和失败重试入口。

## 51. 数字/金额/年份强证据自动闭环落地记录

更新时间：2026-07-07 13:55:31
执行者：Codex / GPT-5

### 51.1 本次补强目标

第 50 节补上了低风险普通语义错词的自动闭环，但数字、金额、比例、年份属于高风险事实值，不能套用低风险逻辑。本次补强的目标是：当 ASR/字幕里的数字疑似错误，并且 OCR/ebook、结构化视觉、平台字幕、内嵌字幕或人工笔记给出直接强证据时，允许 Codex draft 生成
umber 类型 decision；该 decision 仍必须经过现有 alidate-transcript-semantic-correction 的高风险数字校验闸门后，才能由 closure 写入纠正版 transcript。

### 51.2 代码落地

新增/修改位置：

- src/video_knowledge_pipeline/transcript_semantic_correction.py
  - 新增 _candidate_draft_number_correction：只处理
umber 类型候选，要求 corrected 数字与原数字不同、存在 evidence ids、置信度至少 0.95，并且 _has_strong_number_evidence 返回 true。
  - 调整 uild_transcript_semantic_correction_codex_draft：在低风险通用候选之外，加入数字强证据候选 decision 生成。
  - 新增 _candidate_discovery_decisive_number：候选发现阶段识别 OCR/结构化视觉/平台字幕/人工笔记中的决定性数字证据。
  - 新增 _candidate_discovery_original_for_kind 和 _candidate_discovery_candidate_for_kind：数字候选以数字 marker 为粒度，例如把 1k 修成 16k，避免把整句话替成 16k底薪 造成重复或语义损坏。

### 51.3 安全规则

数字类自动写入必须同时满足：

- correction type 为
umber。
- corrected text 中存在数字/金额/年份 marker。
- corrected marker 与 original marker 不同。
- evidence ids 不为空。
- decision confidence >= max(0.95, min_confidence)。
- _has_strong_number_evidence(candidate, evidence_ids, corrected_text=corrected) 为 true。
- corrected 数字必须能在强证据源中找到。

强证据源沿用现有校验器：

- ocr
- structured_visual
- platform_subtitle
- mbedded_subtitle
- page_metadata
- human_note

候选发现阶段更保守，决定性数字自动建议只接受：

- ocr
- structured_visual
- platform_subtitle
- mbedded_subtitle
- human_note

不单独因为 tagger 或 metadata 标题就自动确认数字。

### 51.4 验证记录

已通过：

`powershell
python -m py_compile src\video_knowledge_pipeline\transcript_semantic_correction.py tests\test_transcript_semantic_correction.py
`

已通过手动调用测试函数：

`powershell
='src'
python semantic-refresh-smoke-run\manual_two_test_functions.py
`

覆盖内容：

- 普通低风险 OCR/视觉支持候选仍能写入最终可读文件。
- 数字强证据候选能从 1k -> 16k，并且只替换数字 marker，不破坏整句。
- validate 接受数字 decision。
- closure --refresh-exports 刷新 source-arbitrated-transcript.json、xports/full-transcript.md、xports/smart-summary.md。
- readable impact 返回通过。

pytest 仍受当前环境临时目录权限影响，不能作为本轮稳定证据；这不是断言失败。

### 51.5 当前剩余缺口

数字/金额/年份闭环已有最小强证据路径，但还需要继续补：

- 中文数字金额，例如 一万刀、十六 k、十五百万 等归一化。
- 百分比、年份、日期、步骤编号的更细粒度 marker 替换。
- 平台字幕与 ASR 数字冲突的跨源分组仲裁。
- 批量报告中区分 uto_applied_number_with_strong_evidence 与
umber_needs_human_review。
- 真实长视频 bundle 的数字候选抽样验收。

## 52. 动作/步骤词强视觉证据自动闭环落地记录

更新时间：2026-07-07 14:02:14
执行者：Codex / GPT-5

### 52.1 本次补强目标

动作/步骤词会直接影响课程可执行流程，例如 打开、点击、登录、保存、导入、配置 等。如果 ASR/字幕把操作动作识别错，最终 ull-transcript.md 和 smart-summary.md 会误导用户执行错误步骤。因此本次补强目标是：当视觉理解、连续片段理解、结构化视觉、OCR 或人工笔记给出明确动作证据时，让 Codex draft 能生成 ction 类型 decision；该 decision 仍必须经过现有高风险动作校验后才写入纠正版 transcript。

### 52.2 代码落地

新增/修改位置：

- src/video_knowledge_pipeline/transcript_semantic_correction.py
  - 新增 _candidate_draft_action_correction：只处理 ction 类型候选，要求存在强证据、置信度至少 0.92，并通过 _has_strong_action_evidence。
  - 新增 _candidate_action_replacement_terms：把动作纠错限制在动作词 marker 粒度，例如 打开 -> 点击，避免把整段 ASR 替换成视觉描述。
  - 调整 uild_transcript_semantic_correction_codex_draft：在普通低风险和数字强证据路径之外，增加动作强证据候选 decision 生成。
  - 新增 _candidate_discovery_decisive_action：候选发现阶段识别视觉/连续片段/OCR/人工笔记中的决定性动作证据。
  - 扩展 _candidate_discovery_original_for_kind 和 _candidate_discovery_candidate_for_kind：支持 action marker 级别提取。

### 52.3 安全规则

动作类自动写入必须同时满足：

- correction type 为 ction。
- original 和 corrected 都能抽出动作 marker，且两者不同。
- evidence ids 不为空。
- decision confidence >= max(0.92, min_confidence)。
- _has_strong_action_evidence(candidate, evidence_ids, corrected_text=corrected_action) 为 true。
- corrected action 必须能在强视觉/连续片段/OCR/人工证据中找到。

候选发现阶段的决定性动作证据只接受：

- isual_understanding
- 	emporal_visual
- structured_visual
- ocr
- human_note

	agger 可以作为后续 validate 的证据之一，但不会单独让 candidate discovery 把动作候选标成自动安全。这样能利用打标器，又不让粗标签直接改操作流程。

### 52.4 验证记录

已通过：

`powershell
python -m py_compile src\video_knowledge_pipeline\transcript_semantic_correction.py tests\test_transcript_semantic_correction.py
`

已通过手动调用测试函数：

`powershell
='src'
python semantic-refresh-smoke-run\manual_three_test_functions.py
`

覆盖内容：

- 普通低风险 OCR/视觉支持候选仍能写入最终可读文件。
- 数字强证据候选仍能写入最终可读文件。
- 动作强视觉/连续片段证据候选能从 打开 -> 点击，且只替换动作 marker。
- validate 接受 action decision。
- closure --refresh-exports 刷新 source-arbitrated-transcript.json、xports/full-transcript.md、xports/smart-summary.md。
- readable impact 返回通过。

pytest 仍受当前环境临时目录权限影响，不能作为本轮稳定证据；手动测试函数实际调用的是测试文件中的新增测试。

### 52.5 当前剩余缺口

动作/步骤词已有最小强证据闭环，但还需要继续补：

- 多动作链条的结构化修正，例如 点击登录并保存配置 这类不只是单个动词替换的情况。
- 连续片段理解中的 steps 字段与 ASR segment 的更精确对齐。
- 复杂操作流程需要 review pack 展示视频时间点，不能完全自动改。
- 批量报告中区分 uto_applied_action_with_visual_evidence 与 ction_needs_human_review。
- 真实长视频 bundle 的动作候选抽样验收。

## 53. 平台字幕/内嵌字幕与 ASR 冲突仲裁最小闭环落地记录

更新时间：2026-07-07 14:07:56
执行者：Codex / GPT-5

### 53.1 本次补强目标

很多视频网站字幕本身也是 ASR 生成，不能被视为绝对正确；但当平台字幕、内嵌字幕、本地 ASR、OCR/视觉/元数据之间出现差异时，字幕仍然是重要证据。本次补强目标是：让 VKP 能显式接入平台字幕和内嵌字幕 sidecar，把它们作为独立证据源参与候选发现、候选分组、Codex draft、validate 和 closure；当冲突属于低风险专名/术语且字幕证据明确时，可以写入纠正版 transcript，并刷新最终人类可读文件。

### 53.2 代码落地

新增/修改位置：

- src/video_knowledge_pipeline/transcript_semantic_correction.py
  - 扩展 SIDE_SOURCE_MANIFEST_KEYS：新增 mbedded_subtitle、mbedded_subtitle_path、mbedded_subtitle_json、mbedded_subtitle_srt、mbedded_subtitle_vtt。
  - 扩展 SIDE_SOURCE_ROOT_FILES：新增 mbedded-subtitle.json、mbedded-subtitle.srt、mbedded-subtitle.vtt。
  - 调整 _candidate_draft_generic_correction：除了 candidate discovery 导入候选外，允许初始 pack 中由 subtitle_text_differs_from_transcript 产生、且 evidence source types 包含 platform_subtitle 或 mbedded_subtitle 的低风险候选进入 Codex draft。
  - 继续复用现有 validate：数字、动作、低置信冲突、缺 evidence ids 等仍会被拦截。

### 53.3 支持的 sidecar 输入

Manifest 可声明：

`json
{
  "platform_subtitle_path": "platform-subtitle.json",
  "embedded_subtitle_path": "embedded-subtitle.json"
}
`

Bundle 根目录也会自动发现：

- platform-subtitle.json/srt/vtt
- subtitle.json/srt/vtt
- source-subtitle.json/srt/vtt
- mbedded-subtitle.json/srt/vtt

这些 sidecar 统一通过 parse_transcript 读取，并按时间重叠匹配到当前 ASR cue。

### 53.4 安全边界

本次补强不意味着“平台字幕一定正确”：

- 平台字幕和内嵌字幕只是证据源。
- 只有低风险 proper_noun、	erm、concept、ordinary_word 会走自动草稿。
- 数字和动作仍走更严格的数字/动作闸门。
- 如果平台字幕与 ASR、OCR、视觉互相矛盾，仍进入 review/LLM/人工仲裁。
- 如果字幕候选需要人工确认，validate 仍会拒绝非人工确认的自动写入。

### 53.5 验证记录

已通过：

`powershell
python -m py_compile src\video_knowledge_pipeline\transcript_semantic_correction.py tests\test_transcript_semantic_correction.py
`

已通过手动调用测试函数：

`powershell
='src'
python semantic-refresh-smoke-run\manual_four_test_functions.py
`

覆盖内容：

- 普通低风险 OCR/视觉支持候选可闭环。
- 数字强证据候选可闭环。
- 动作强视觉/连续片段候选可闭环。
- ASR playright 与平台/内嵌字幕 Playwright 冲突时，可生成低风险专名 decision。
- closure --refresh-exports 刷新 source-arbitrated-transcript.json、xports/full-transcript.md、xports/smart-summary.md。
- readable impact 返回通过。

pytest 仍受当前环境临时目录权限影响，不能作为本轮稳定证据；手动测试函数实际调用的是测试文件中的新增测试。

### 53.6 当前剩余缺口

多字幕源冲突仲裁已有最小闭环，但完整目标还需要继续补：

- ASR、平台字幕、内嵌字幕三源互相不一致时的分组投票/权重报告。
- 平台字幕疑似错误时的反向纠错，即不要让错误字幕覆盖正确 ASR。
- 字幕侧普通错词候选进入 LLM/Codex 语义判断，而不是只依赖规则。
- 多语言字幕、翻译字幕、自动生成字幕的 source reliability 标记。
- UI/Task Console 中显示每个候选来自哪些字幕源、哪些源支持/反对。

## 54. UI/队列可见性落地记录（2026-07-07 由 Codex / GPT-5 更新）

本轮补强把通用 ASR/字幕语义纠错闭环从“只在状态 JSON 中散落字段”推进为可被 UI、批量队列、MCP/OpenClaw 复用的稳定摘要层。

### 54.1 新增 `ui_summary`

`transcript-semantic-correction-status.json` 新增 `ui_summary`：

- `ui_state`：当前闭环阶段，例如 `machine_review_required`、`human_review_required`、`accepted_waiting_for_closure`、`closed_and_export_checked`。
- `candidate_count`：候选总数。
- `auto_candidate_count`：规则判断为可机器优先处理的候选数。
- `human_review_candidate_count`：高风险或显式需要人工复核的候选数。
- `candidate_type_counts`：按 `proper_noun / term / number / action / concept / ordinary_word / punctuation / segment_boundary` 统计。
- `risk_level_counts`：按 low/medium/high/unknown 统计。
- `evidence_source_counts`：按 ASR、平台字幕、内嵌字幕、OCR、图文结构、多模态、打标器、人工备注等证据源统计。
- `accepted_decision_type_counts`：已通过 validation 的纠错类型统计。
- `rejected_decision_reason_counts`：validation 拒绝原因统计。
- `applied_correction_type_counts`：真正写入纠正版 transcript 的类型统计。
- `applied_correction_preview`：最多展示 8 条已应用纠错，供 UI 快速预览。
- `review_required_count`、`review_imported_count`、`review_closed_count`：人工复核进度。
- `candidate_discovery`：候选发现包、Codex/LLM 建议、导入数量、跳过数量。
- `export_chain`：纠正版 transcript、可读文件、smart-summary 影响检查状态。

### 54.2 Task Console 展示

`task-console.html` 的“通用 ASR/字幕语义纠错”面板新增“通用语义纠错闭环进度摘要”：

- 显示自动候选、需人工候选、接受/拒绝、已应用、导入/关闭/未关。
- 显示可读文件影响和智能总结影响状态。
- 显示已接受类型、已应用类型、拒绝原因。
- 显示已应用预览，便于确认哪些错词已进入纠正版 transcript。

这层展示不绕过 validation / closure。UI 只能辅助判断和生成 review notes，真正写回仍必须经过：

```text
pack / candidate discovery -> Codex/LLM/人工判断 -> validate -> closure -> refresh exports -> impact reports -> status
```

### 54.3 验证记录

已通过编译：

```powershell
python -m py_compile src\video_knowledge_pipeline\transcript_semantic_correction.py src\video_knowledge_pipeline\task_console.py tests\test_transcript_semantic_correction.py tests\test_task_console.py semantic-refresh-smoke-run\ui-summary-status-smoke.py
```

已通过手动 smoke：

```powershell
python semantic-refresh-smoke-run\ui-summary-status-smoke.py
```

覆盖内容：

- 语义纠错 closure 后 `ui_summary.ui_state=closed_and_export_checked`。
- 已接受、已应用、证据来源、可读导出影响状态能进入 status。
- Task Console HTML 出现“通用语义纠错闭环进度摘要”“自动候选”“需人工候选”。

pytest 定向测试仍被当前 Windows 临时目录权限阻塞，错误点在 `%USERPROFILE%\AppData\Local\Temp\pytest-of-%USERNAME%`，不是本轮代码逻辑失败。

## 55. 下游内容资产 / Handoff 语义纠错状态接入（2026-07-07 由 Codex / GPT-5 更新）

本轮把第 18 节“下游 agent 契约”继续向代码落地：`content-asset-status`、`batch-content-asset-status`、`content-handoff-pack` 不再只暴露基础 semantic correction 状态，也会透传和汇总 `ui_summary`。

### 55.1 单 bundle 状态

`content_asset_status(bundle_dir)` 现在返回：

- `semantic_correction_ui_summary`
- `semantic_correction_status`
- `semantic_correction_candidate_count`
- `semantic_correction_accepted_count`
- `semantic_correction_review_count`
- `semantic_correction_final_residual_error_total`
- `semantic_correction_candidate_type_counts`
- `semantic_correction_risk_level_counts`
- `semantic_correction_evidence_source_counts`
- `semantic_correction_review_closure_summary`
- `semantic_correction_next_action_key`
- `semantic_correction_artifacts`
- `semantic_correction_commands`

其中 `semantic_correction_ui_summary` 是 UI、批量队列和 OpenClaw 下游最稳定的入口。下游不需要重新推导自动候选、人审候选、已应用类型和导出影响状态。

### 55.2 批量内容素材状态

`batch_content_asset_status` 的 `semantic_correction_summary` 新增汇总：

- `auto_candidate_count`
- `human_review_candidate_count`
- `applied_correction_count`
- `rejected_decision_count`
- `by_ui_state`
- `by_accepted_type`
- `by_applied_type`

批量 Markdown 中同步显示：

- Auto candidates
- Human review candidates
- Applied corrections
- Rejected decisions
- UI state
- Accepted type
- Applied type

这样批量素材交接前可以直接判断：哪些视频的转写纠错已经进入可读导出，哪些还卡在 validation、closure、impact 或人工复核。

### 55.3 Handoff Pack

`content_handoff_pack` 继续保持安全边界：

```text
review_required=true
publication_allowed=false
allowed_as_fact=false
```

新增的 semantic correction summary 只作为下游判断素材可信度和复核优先级的证据，不允许被解释为“可以自动发布”或“已事实核查”。

### 55.4 验证记录

已通过编译：

```powershell
python -m py_compile src\video_knowledge_pipeline\content_asset_status.py src\video_knowledge_pipeline\content_asset_batch.py tests\test_knowledge_export.py
```

pytest 仍在 Windows basetemp 清理阶段被权限阻塞：

```text
PermissionError: [WinError 5] ... semantic-refresh-smoke-run\pytest-content-assets
```

已通过函数级 smoke：

```powershell
python semantic-refresh-smoke-run\content-asset-semantic-summary-smoke.py
```

覆盖内容：

- `content_asset_status` 单项包含 `semantic_correction_ui_summary`。
- batch summary 汇总 auto/human/rejected/applied/ui_state/accepted_type。
- batch Markdown 出现 Auto candidates、UI state、Accepted type。
- `content_handoff_pack` 保留不可发布、不可当事实的边界，同时携带 semantic correction summary。

## 56. 多字幕源支持/反对摘要与错误字幕反向保护（2026-07-07 由 Codex / GPT-5 更新）

本轮继续补第 53.6 节的缺口：平台字幕、内嵌字幕、自带字幕不能被默认当成事实。候选现在会记录每个证据源到底支持候选、支持原文，还是保持中立。

### 56.1 新增 `source_support_summary`

每个 semantic correction candidate 新增：

```json
{
  "source_support_summary": {
    "supports_candidate": ["platform_subtitle", "embedded_subtitle"],
    "supports_original": ["asr_or_subtitle", "ocr"],
    "neutral": ["page_metadata"],
    "has_source_conflict": true,
    "votes": [
      {
        "source_type": "platform_subtitle",
        "evidence_id": "platform_subtitle_path_1",
        "vote": "supports_candidate",
        "text_excerpt": "..."
      }
    ]
  }
}
```

判断规则：

- ASR / 当前主 transcript 默认支持原文。
- 平台字幕、内嵌字幕、OCR、结构化视觉、多模态、人工笔记如果包含候选文本，则支持候选。
- 如果 OCR、结构化视觉、多模态或人工笔记包含原文，则视为强证据支持原文。
- 当字幕候选与强视觉/OCR/人工原文证据冲突时，候选仍会进入 pack，但不会被本地 Codex draft 自动接受。

### 56.2 错误平台字幕反向保护

新增 `_has_strong_source_opposition(candidate)`：

- 如果 `source_support_summary.supports_original` 中存在 `ocr / structured_visual / visual_understanding / temporal_visual / human_note`；
- 且候选没有同等级强证据支持；
- 则 `_candidate_draft_generic_correction` 不会自动生成 replace decision。

这解决了一个重要风险：很多视频网站字幕本身也是 ASR 生成的，可能错。平台字幕只能作为证据源，不能单独覆盖屏幕文字或人工确认。

### 56.3 状态与 UI 透传

`source_support_summary` 已进入：

- `transcript-semantic-correction-pack.json` 的 candidates；
- `transcript-semantic-correction-status.json` 的 `review_required_items`；
- `transcript-semantic-correction-status.json` 的 `semantic_attention_items`。

后续 UI 可以直接用这个字段展示“哪些源支持候选、哪些源支持原文”，不需要前端重新解析 evidence。

### 56.4 验证记录

已通过编译：

```powershell
python -m py_compile src\video_knowledge_pipeline\transcript_semantic_correction.py tests\test_transcript_semantic_correction.py
```

已通过 smoke：

```powershell
python semantic-refresh-smoke-run\subtitle-source-support-smoke.py
```

覆盖内容：

- ASR `playright`，平台字幕和内嵌字幕 `Playwright` 时，candidate 的 `supports_candidate` 包含 `platform_subtitle` 与 `embedded_subtitle`，`supports_original` 包含 `asr_or_subtitle`。
- ASR/OCR 都支持 `Playwright`，平台字幕错误为 `Playright` 时，candidate 标记 `has_source_conflict=true`，但 Codex 本地草稿不会生成 `Playright` 的自动 replace decision。
## 57. 来源可靠性投票与下游状态传播落地记录

更新时间：2026-07-07 18:55:00
执行者：Codex / GPT-5

### 57.1 本次补强目标

平台字幕、内嵌字幕、自带字幕不能被默认视为事实。它们可能比本地 ASR 更准确，也可能同样来自 ASR 或自动翻译而产生新错误。因此通用语义纠错闭环需要把“来源是否支持候选 / 是否支持原文 / 来源可靠性如何”显式进入 pack、status、UI 和内容素材下游。

本次补强目标是：

- 每个候选记录来源投票和来源可靠性权重。
- 当平台字幕候选被 OCR、视觉或人工强证据反对时，不自动写入错误字幕。
- `transcript-semantic-correction-status` 输出 bundle 级 `source_vote_summary`。
- Task Console 显示“来源投票 / 字幕可靠性摘要”。
- `content_asset_status`、`batch_content_asset_status`、`content_handoff_pack` 透传并汇总来源投票摘要，让 OpenClaw / 内容资产线程不用重新解析 evidence。

### 57.2 代码落地

新增/修改位置：

- `src/video_knowledge_pipeline/transcript_semantic_correction.py`
  - 新增 `SOURCE_RELIABILITY_WEIGHTS` 和 `SOURCE_RELIABILITY_NOTES`。
  - 扩展 `_source_support_summary`，输出 `candidate_weight`、`original_weight`、`neutral_weight`、`weight_margin`、`dominant_side`、`needs_review_by_source_vote`、`strong_candidate_sources`、`strong_original_sources`、`source_reliability` 和带 `source_weight` 的 votes。
  - 新增 `_source_vote_summary`，聚合候选数、来源冲突数、投票需复核数、候选/原文/中立权重、优势方分布、支持候选来源、支持原文来源和冲突预览。
  - `transcript_semantic_correction_status` 和 manifest summary 写入 `source_vote_summary`。
  - `_render_status_markdown` 输出来源投票摘要。

- `src/video_knowledge_pipeline/task_console.py`
  - 新增 `_semantic_correction_source_vote_html`。
  - `task-console.html` 的通用语义纠错面板显示来源冲突、投票需复核、候选/原文权重、优势方、支持候选来源、支持原文来源和冲突预览。

- `src/video_knowledge_pipeline/content_asset_status.py`
  - 新增 `semantic_correction_source_vote_summary`，作为单 bundle 下游稳定字段。

- `src/video_knowledge_pipeline/content_asset_batch.py`
  - batch row 透传 `semantic_correction_source_vote_summary`。
  - `semantic_correction_summary` 聚合 `source_vote_candidate_count`、`source_conflict_count`、`needs_review_by_source_vote_count`、候选/原文/中立权重总量、`by_source_vote_dominant_side`、`by_candidate_support_source`、`by_original_support_source`。
  - 批量 Markdown 输出 Source vote candidates、Source conflicts、Needs review by source vote、Source vote dominant side、Candidate support source、Original support source。

### 57.3 来源可靠性权重

当前权重：

| 来源 | 权重 | 说明 |
| --- | ---: | --- |
| `human_note` | 90 | 人工确认最高，但仍保留 provenance。 |
| `structured_visual` | 75 | ebook/OCR 结构化图文结果，适合课件、表格、代码、公式。 |
| `ocr` | 70 | 屏幕文字强证据，但要防低置信、空结果和 wrapper-only。 |
| `visual_understanding` | 65 | 多模态单帧理解，适合非纯文字画面。 |
| `temporal_visual` | 65 | 连续片段理解，适合操作链和状态变化。 |
| `platform_subtitle` | 50 | 中等证据，不能单独压过 OCR/视觉/人工。 |
| `embedded_subtitle` | 50 | 中等证据，需要与其他来源互证。 |
| `asr_or_subtitle` | 40 | 当前主 transcript/ASR 来源，默认支持原文。 |
| `tagger` | 30 | 用于优先级和定位，不单独改词。 |
| `page_metadata` | 20 | 标题简介可辅助，但不能单独确认高风险事实。 |
| `unknown` | 5 | 未知来源弱证据。 |

### 57.4 安全边界

- 字幕源支持候选但 OCR/结构化视觉/多模态/人工支持原文时，候选进入 pack，但本地 Codex draft 不自动生成 replace decision。
- 候选侧只有平台字幕或内嵌字幕支持时，不能单独覆盖强视觉、OCR 或人工证据。
- 数字、金额、时间、人物、事实归属仍必须走高风险 validate，不因来源投票较高而绕过。
- 下游内容素材只读取状态和证据，不因 `dominant_side=candidate` 自动变成事实结论。

### 57.5 验证记录

已通过编译：

```powershell
python -m py_compile src\video_knowledge_pipeline\transcript_semantic_correction.py src\video_knowledge_pipeline\task_console.py src\video_knowledge_pipeline\content_asset_status.py src\video_knowledge_pipeline\content_asset_batch.py tests\test_transcript_semantic_correction.py tests\test_task_console.py tests\test_knowledge_export.py
```

已通过 smoke：

```powershell
python semantic-refresh-smoke-run\subtitle-source-support-smoke.py
python semantic-refresh-smoke-run\ui-summary-status-smoke.py
python semantic-refresh-smoke-run\content-asset-semantic-summary-smoke.py
```

覆盖内容：

- ASR `playright`，平台字幕和内嵌字幕 `Playwright` 时，候选侧权重大于原文侧，并可进入纠错闭环。
- 平台字幕错误为 `Playright`，ASR/OCR 原文支持 `Playwright` 时，`dominant_side=original`，`needs_review_by_source_vote=true`，且不会自动生成错误字幕 replace decision。
- Task Console 能显示来源投票 / 字幕可靠性摘要。
- 内容素材单项、批量状态和 handoff pack 能透传/汇总来源投票字段。

定向 pytest 仍受当前 Windows 临时目录权限阻塞，错误发生在 `tmp_path` fixture 初始化前：

```text
PermissionError: [WinError 5] ... %USERPROFILE%\AppData\Local\Temp\pytest-of-%USERNAME%
```

因此本轮以 `py_compile` 和项目内 smoke 脚本作为验证证据；这不是测试断言失败。

### 57.6 当前剩余缺口

来源投票链路已经进入核心 pack/status/UI/downstream，但完整目标仍未结束：

- 需要在真实 3-5 个长视频上验证普通 ASR 错词、复杂断句、数字和动作候选的召回质量。
- 需要把 source vote summary 更细地接入人工 review 页面，直接给出 accept/keep/review 建议。
- 需要修复或绕开本机 pytest temp/cache 权限，恢复全量测试门禁。
- 需要验证 `smart-summary.md` 在真实视频中确实吸收纠正版 transcript，而不仅是逐字稿层无残留。
## 58. 长句标点/断句候选召回闭环落地记录

更新时间：2026-07-07 19:08:00
执行者：Codex / GPT-5

### 58.1 本次补强目标

普通 ASR 错词之外，长视频逐字稿常见问题还包括长句没有标点、多个知识点被粘成一个 segment、章节边界和动作链条没有断开。这类问题不一定能给出一个确定的 `corrected_text`，但它们会直接影响 `full-transcript.md` 可读性、`smart-summary.md` 分段质量和后续内容素材抽取。

本次补强目标是：让 candidate discovery 能把长句缺标点 / 长段需断句作为正式高风险候选召回，进入 review/LLM 队列，而不是因为 `candidate_text` 为空被本地 Codex suggestions 过滤掉。

### 58.2 代码落地

新增/修改位置：

- `src/video_knowledge_pipeline/transcript_semantic_correction.py`
  - `_semantic_candidate_discovery_score` 现在接收 `start/end`，调用 `_punctuation_or_boundary_kind` 判断 `punctuation` 或 `segment_boundary`。
  - 长段无可靠分段时加入 `needs_segment_boundary_review`，长句缺标点时加入 `needs_punctuation_review`。
  - `_codex_suggestions_for_segment` 对这两类 reason 生成明确候选：
    - `segment_boundary` -> `candidate_text=【待断句复核】`
    - `punctuation` -> `candidate_text=【待标点复核】`
  - 这类候选固定 `needs_human_review=true`，风险级别由 `HIGH_RISK_TYPES` 保持为 high，不会自动写入纠正版 transcript。

- `tests/test_transcript_semantic_correction.py`
  - 新增 `test_semantic_candidate_discovery_imports_segment_boundary_review_candidate`。
  - 覆盖长段 ASR 缺少可靠分段时，Codex candidate discovery 生成 `segment_boundary` 建议，并且 import 后进入 `transcript-semantic-correction-pack.json`。

- `semantic-refresh-smoke-run/segment-boundary-discovery-smoke.py`
  - 新增 smoke 入口，直接调用新增测试函数，绕过当前 pytest temp/cache 权限问题。

### 58.3 安全边界

- 断句/标点候选只进入候选池，不直接 closure。
- 本地 Codex 不自由改写整段 transcript，只输出“待复核”占位候选。
- 真正标点恢复和重分段需要 LLM/人工返回结构化 decision，并通过 validate。
- 这类候选允许不阻塞整体视频交付，但必须进入 known gaps / review pack / Task Console。

### 58.4 验证记录

已通过：

```powershell
python -m py_compile src\video_knowledge_pipeline\transcript_semantic_correction.py tests\test_transcript_semantic_correction.py
python semantic-refresh-smoke-run\segment-boundary-discovery-smoke.py
python semantic-refresh-smoke-run\subtitle-source-support-smoke.py
python semantic-refresh-smoke-run\ui-summary-status-smoke.py
python semantic-refresh-smoke-run\content-asset-semantic-summary-smoke.py
```

`segment-boundary-discovery-smoke.py` 证明：

- 长段无标点 ASR 被 candidate discovery 选中。
- Codex suggestions 生成 `correction_type=segment_boundary`。
- `candidate_text=【待断句复核】` 没有被空 candidate 过滤。
- import 后 pack 中存在 high risk、needs human review 的 `segment_boundary` 候选。

### 58.5 当前剩余缺口

- 现在只是把断句/标点问题召回并进入复核队列，还没有实现 LLM/人工返回“结构化断句结果”后的安全应用。
- 需要继续设计 `segment_boundary` / `punctuation` decision schema，例如分段列表、标点后文本、原文覆盖范围和禁止改义规则。
- 需要在真实长视频上统计：长段 ASR 候选召回数量、人工/LLM处理成本、对 smart-summary 分段质量的改善。

## 59. 实现进展记录：2026-07-07 Smart Summary 缺语义纠错 Pack 不再误判 Final

更新时间：2026-07-07 15:10:00
执行者：Codex / GPT-5

### 59.1 本次补强目标

目标文档要求：如果视频已经有 transcript，但还没有跑 `transcript-semantic-correction-pack`，`smart-summary.md` 不能伪装成最终可用总结。它可以作为草稿导出，但必须明确提示：语音识别/字幕语义纠错闭环还没有启动，不能把转写纠错状态视为 closed。

此前 `_semantic_correction_quality_gate` 在 `missing_pack` 且存在 transcript 时返回 `passed=true`，只在 detail 里提醒后续要跑 pack。这会造成一个危险状态：`smart_summary_quality_check` 可能通过，`export-knowledge-note` 可能把 `smart_summary_final_status` 判为 `final`，而实际上疑似错词候选根本还没有生成。

### 59.2 代码落地

修改位置：

- `src/video_knowledge_pipeline/smart_summary_codex.py`
  - `_semantic_correction_quality_gate` 的 `missing_pack` 分支改为 `passed=false`。
  - detail 文案改为：`smart summary may be exported as a draft, but run transcript-semantic-correction-pack before treating transcript correction as closed`。

新增测试位置：

- `tests/test_knowledge_export.py`
  - 新增 `test_export_marks_smart_summary_draft_when_semantic_pack_missing_but_transcript_exists`。
  - 构造有 `normalized-transcript.json` 但没有 `transcript-semantic-correction-pack.json` 的 bundle。
  - 期望 `export_knowledge_note` 输出：
    - `smart_summary_final_status=draft_needs_semantic_correction`
    - `transcript_semantic_correction_gate.passed=false`
    - `transcript_semantic_correction_gate.status=missing_pack`
    - `publication_allowed=false`

### 59.3 安全边界

- 不阻止导出草稿。
- 不自动生成 pack。
- 不自动调用 LLM、ASR、OCR 或视觉模型。
- 只改变 smart summary quality/final 边界，避免把未启动的纠错闭环误报成完成。

### 59.4 验证记录

已通过：

```powershell
python -m py_compile src\video_knowledge_pipeline\smart_summary_codex.py tests\test_knowledge_export.py
python semantic-refresh-smoke-run\content-asset-semantic-summary-smoke.py
python semantic-refresh-smoke-run\segment-boundary-discovery-smoke.py
python semantic-refresh-smoke-run\subtitle-source-support-smoke.py
python semantic-refresh-smoke-run\ui-summary-status-smoke.py
git diff --check -- src\video_knowledge_pipeline\smart_summary_codex.py tests\test_knowledge_export.py
```

新增门禁 smoke：

```powershell
$env:PYTHONPATH='src'
python -c "... smart_summary_quality_check(... missing transcript-semantic-correction-pack ...)"
```

结果：

```text
semantic missing-pack gate smoke passed: semantic correction pack missing; smart summary may be exported as a draft, but run transcript-semantic-correction-pack before treating transcript correction as closed
```

### 59.5 当前剩余缺口

- 需要恢复本机 pytest temp/cache 权限后，把新增测试纳入正式 pytest 门禁。
- 需要在真实 bundle 上跑 `export-knowledge-note`，确认缺 pack 时 `smart_summary_final_status` 稳定为 `draft_needs_semantic_correction`。
- 需要继续把 `transcript-semantic-correction-pack -> codex/llm decision -> validate -> closure --refresh-exports -> readable/summary impact` 跑到真实长视频批量验收。

## 60. 实现进展记录：2026-07-07 单 Bundle 状态机纳入 Smart Summary Impact

更新时间：2026-07-07 15:18:00
执行者：Codex / GPT-5

### 60.1 本次补强目标

目标文档要求：已接受的 ASR/字幕语义纠错不仅要进入 `source-arbitrated-transcript.json` 和 `full-transcript.md`，也必须真实影响 `smart-summary.md`。本轮真实 bundle 只读检查发现一个状态机缺口：

```text
status=impact_passed
next_action_key=none
summary_impact_status=missing
```

这意味着单 bundle 的 `transcript-semantic-correction-status` 只检查了基础 impact 和 readable impact，没有把 `transcript-semantic-summary-impact-report` 纳入 closed 条件。Batch 层已经能识别 summary impact 缺失，但单 bundle 状态会误报完成。

### 60.2 代码落地

修改位置：

- `src/video_knowledge_pipeline/transcript_semantic_correction.py`
  - `_status_from_artifacts` 新增 `summary_impact` 参数。
  - 当基础 impact 和 readable impact 都通过后，继续要求：
    - `transcript-semantic-summary-impact-report.json` 存在；
    - summary impact 不比 readable impact 旧；
    - summary impact 状态为 `passed`、`no_accepted_decisions` 或 `no_evaluable_replacements`。
  - 如果 summary impact 缺失或过期，状态返回：
    - `status=needs_summary_impact_report`
    - `next_action_key=run_summary_impact`
  - 如果 summary impact 存在但失败，状态返回：
    - `status=summary_impact_needs_fix`
    - `next_action_key=refresh_summary_or_review`
  - `_status_commands` 新增 `refresh_summary_or_review` 命令：先 `export-knowledge-note`，再 `transcript-semantic-summary-impact-report`。

测试修改：

- `tests/test_transcript_semantic_correction.py`
  - 在完整闭环测试里新增断言：readable impact 通过但 summary impact 未跑时，status 必须是 `needs_summary_impact_report`，quality gate 也必须显示同一状态。

### 60.3 真实 Bundle 验收记录

只读检查以下真实 bundle：

```text
openclaw-runs/knowledge/BV134Ei6KEaJ-browser-automation/webui-bundle
openclaw-runs/knowledge/tongyi-teacher-20260624-live-replay-rerun-current/webui-bundle
openclaw-runs/knowledge/tiktok-crossborder-day2/webui-bundle
```

修复后，在未跑 summary impact 的 bundle 上，状态从误报：

```text
status=impact_passed
next_action_key=none
summary_impact_status=missing
```

变为：

```text
status=needs_summary_impact_report
next_action_key=run_summary_impact
summary_impact_status=missing
```

对 `BV134Ei6KEaJ-browser-automation` 执行本地 summary impact 报告后，发现真实残留：

```text
status=needs_fix
summary_residual_original_total=4
```

残留示例：已接受纠错 `javascript -> JavaScript` 后，`smart-summary.md` 中仍残留 `javascript`。随后 status 正确变为：

```text
status=summary_impact_needs_fix
next_action_key=refresh_summary_or_review
summary_impact_status=needs_fix
summary_residual_original_total=4
```

这证明 summary impact gate 不只是形式检查，确实能发现最终智能总结仍继承已接受 ASR/字幕错词的问题。

### 60.4 验证记录

已通过：

```powershell
python -m py_compile src\video_knowledge_pipeline\transcript_semantic_correction.py tests\test_transcript_semantic_correction.py
python semantic-refresh-smoke-run\content-asset-semantic-summary-smoke.py
python semantic-refresh-smoke-run\ui-summary-status-smoke.py
git diff --check -- src\video_knowledge_pipeline\transcript_semantic_correction.py tests\test_transcript_semantic_correction.py src\video_knowledge_pipeline\smart_summary_codex.py tests\test_knowledge_export.py docs\general-asr-subtitle-semantic-correction-loop-detailed-spec-2026-07-07.md
```

定点函数 smoke：

```text
semantic status summary-impact gate smoke passed
```

真实 bundle 命令验证：

```powershell
python -m video_knowledge_pipeline.cli transcript-semantic-correction-status openclaw-runs\knowledge\BV134Ei6KEaJ-browser-automation\webui-bundle --no-write
python -m video_knowledge_pipeline.cli transcript-semantic-summary-impact-report openclaw-runs\knowledge\BV134Ei6KEaJ-browser-automation\webui-bundle
```

### 60.5 当前剩余缺口

- `BV134Ei6KEaJ-browser-automation` 的 `smart-summary.md` 需要重新生成或修正，直到 `transcript-semantic-summary-impact-report` 通过。
- `tongyi-teacher-20260624-live-replay-rerun-current` 和 `tiktok-crossborder-day2` 仍需要跑 summary impact 报告。
- 后续需要让 repair queue / batch acceptance 使用同一单 bundle 状态口径，避免下游看到不一致状态。
- 全量 pytest 仍受当前 Windows pytest temp/cache 权限问题影响，本轮继续用定点 smoke 和真实 bundle 命令作为验证证据。

## 61. 2026-07-07 15:24: Codex 修复 summary impact 的大小写纠错误判

### 问题

在真实 `BV134Ei6KEaJ-browser-automation` bundle 上，`transcript-semantic-summary-impact-report` 曾把 `javascript -> JavaScript` 这种只修正大小写/规范写法的 accepted correction 误判为未吸收：

- `summary_residual_original_total=4`
- `summary_impact_status=needs_fix`
- `transcript-semantic-correction-status` 被推进到 `summary_impact_needs_fix`

根因是旧的 `_count_text` 对 ASCII 词使用不区分大小写的边界匹配。于是最终总结里的 `JavaScript` 会同时被算作 corrected hit，也被算作原始 `javascript` residual。

### 修复原则

1. “纠正词命中”应检查最终规范写法是否真的出现。
2. “原错词残留”不能把规范写法反向算成残留。
3. 对 `javascript -> JavaScript`、`mcp -> MCP` 这类只改大小写/规范大小写的纠错，残留统计必须区分大小写。
4. 对 `playright -> Playwright`、`chrom -> Chrome` 这类真实错拼，原错词残留仍可以保持大小写不敏感，以免漏掉 `Playright` 这种首字母变化的错误残留。

### 代码变更

新增/调整 helper：

- `_count_corrected_text(text, corrected)`：ASCII corrected text 使用大小写敏感边界匹配。
- `_case_only_correction(original, corrected)`：判断是否只改大小写。
- `_count_original_residual(text, original, corrected)`：只改大小写时使用大小写敏感 residual 匹配；其它 ASCII 错词沿用大小写不敏感 residual 匹配。
- `_sample_corrected_lines(...)` 和 `_sample_residual_lines(...)`：样例行跟随同一套计数语义，避免报告里 residual count 为 0 但 residual sample 仍显示规范写法。

### 测试补充

新增测试：

- `test_semantic_summary_impact_does_not_treat_case_fixed_term_as_residual`

覆盖场景：

- accepted decision：`javascript -> JavaScript`
- baseline summary 包含 `javascript`
- final `smart-summary.md` 只包含 `JavaScript`
- 预期：`status=passed`、`summary_residual_original_total=0`、`summary_corrected_hit_total=1`、`baseline_residual_delta=1`

### 真实 bundle 验收

对 `openclaw-runs\knowledge\BV134Ei6KEaJ-browser-automation\webui-bundle` 重新执行：

```powershell
python -m video_knowledge_pipeline.cli transcript-semantic-summary-impact-report openclaw-runs\knowledge\BV134Ei6KEaJ-browser-automation\webui-bundle
python -m video_knowledge_pipeline.cli transcript-semantic-correction-status openclaw-runs\knowledge\BV134Ei6KEaJ-browser-automation\webui-bundle --no-write
```

修复后结果：

- `summary_impact_status=passed`
- `summary_residual_original_total=0`
- `summary_absorption_rate=1.0`
- `status=impact_passed`
- `next_action_key=none`

### 验证记录

已通过：

- `python -m py_compile src\video_knowledge_pipeline\transcript_semantic_summary_impact.py tests\test_transcript_semantic_correction.py`
- 直接函数 smoke：`case-only summary impact smoke passed`
- `python semantic-refresh-smoke-run\content-asset-semantic-summary-smoke.py`
- `python semantic-refresh-smoke-run\ui-summary-status-smoke.py`

限制：

- `pytest -k case_fixed` 仍被 Windows pytest 临时目录/项目 basetemp 权限问题阻塞，错误在 pytest setup/sessionfinish 临时目录访问阶段，不是业务断言失败。

## 62. 2026-07-07 15:36: Codex 补齐内容素材/下游 Handoff 的语义纠错门禁

### 问题

单 bundle 的 `transcript-semantic-correction-status` 已经要求 readable impact 和 smart-summary impact 都通过，才能进入 `impact_passed`。但内容素材层此前只透传了基础语义纠错状态，没有把以下字段明确暴露给下游：

- `readable_impact_status`
- `readable_required_residual_total`
- `summary_impact_status`
- `summary_absorption_rate`
- `summary_residual_original_total`

这会造成一个风险：`content_asset_status` / `batch-content-asset-status` / `content-handoff-pack` 可能只看到素材卡和候选包已存在，却看不出 accepted ASR/字幕纠错是否已经真实进入 `full-transcript.md` 和 `smart-summary.md`。

### 修复原则

内容素材卡不是发布稿，但它仍然会被内容资产/朋友圈线程作为 inspiration 输入。因此只要存在已接受的 ASR/字幕语义纠错，就必须满足：

```text
source-arbitrated transcript 已写入
full-transcript readable impact 已通过
smart-summary summary impact 已通过
final residual = 0
summary residual = 0
review_required = 0
```

否则内容资产状态不能是 `ready_for_inspiration_review`，而应显示为：

```text
semantic_correction_needs_action
```

### 代码变更

修改位置：

- `src/video_knowledge_pipeline/content_asset_status.py`
  - 新增 `_semantic_asset_gate(semantic_correction)`。
  - `content_asset_status` 新增字段：
    - `semantic_correction_readable_impact_status`
    - `semantic_correction_readable_required_residual_total`
    - `semantic_correction_summary_impact_status`
    - `semantic_correction_summary_impact_ok`
    - `semantic_correction_summary_absorption_rate`
    - `semantic_correction_summary_residual_original_total`
    - `semantic_correction_asset_gate`
  - 当素材卡和候选包都存在但 semantic gate 未通过时，顶层状态返回 `semantic_correction_needs_action`，`ok=false`。
  - `next_actions` 增加 `finish_transcript_semantic_correction_before_handoff`，并尽量带上当前 semantic next action 命令。

- `src/video_knowledge_pipeline/content_asset_batch.py`
  - batch row 透传上述 semantic summary/readable/gate 字段。
  - `semantic_correction_summary` 新增：
    - `readable_required_residual_total`
    - `summary_residual_original_total`
    - `summary_impact_missing_or_failed_count`
    - `semantic_asset_gate_blocked_count`
    - `by_summary_impact_status`
    - `by_asset_gate_status`
  - batch Markdown 表格里的 semantic correction 文本显示 summary impact 和 asset gate。

### 测试补充

扩展测试：

- `test_semantic_correction_pack_validation_closure_and_impact`

新增断言：

1. 生成安全素材卡和内容候选包。
2. 在 readable impact 已通过但 summary impact 未跑时：
   - `content_asset_status.ok == False`
   - `status == semantic_correction_needs_action`
   - `semantic_correction_asset_gate.status == needs_summary_impact_report`
   - `next_actions` 包含 `finish_transcript_semantic_correction_before_handoff`
3. 跑完 `transcript_semantic_summary_impact_report` 后：
   - `content_asset_status.ok == True`
   - `status == ready_for_inspiration_review`
   - `semantic_correction_asset_gate.status == passed`
   - `semantic_correction_summary_residual_original_total == 0`

### 真实 Bundle 验收

对 `openclaw-runs\knowledge\BV134Ei6KEaJ-browser-automation\webui-bundle` 执行：

```powershell
python -m video_knowledge_pipeline.cli content-asset-status openclaw-runs\knowledge\BV134Ei6KEaJ-browser-automation\webui-bundle --no-write
python -m video_knowledge_pipeline.cli batch-content-asset-status openclaw-runs\knowledge\BV134Ei6KEaJ-browser-automation\webui-bundle --no-write
```

结果显示：

- `content_asset_status.status=ready_for_inspiration_review`
- `semantic_correction_status=impact_passed`
- `semantic_correction_readable_impact_status=passed`
- `semantic_correction_summary_impact_status=passed`
- `semantic_correction_summary_absorption_rate=1.0`
- `semantic_correction_summary_residual_original_total=0`
- `semantic_correction_asset_gate.status=passed`
- batch summary 中：
  - `by_summary_impact_status.passed=1`
  - `by_asset_gate_status.passed=1`
  - `summary_impact_missing_or_failed_count=0`
  - `semantic_asset_gate_blocked_count=0`

### 验证记录

已通过：

```powershell
python -m py_compile src\video_knowledge_pipeline\content_asset_status.py src\video_knowledge_pipeline\content_asset_batch.py tests\test_transcript_semantic_correction.py
python -c "... mod.test_semantic_correction_pack_validation_closure_and_impact(root) ..."
python -m video_knowledge_pipeline.cli content-asset-status openclaw-runs\knowledge\BV134Ei6KEaJ-browser-automation\webui-bundle --no-write
python -m video_knowledge_pipeline.cli batch-content-asset-status openclaw-runs\knowledge\BV134Ei6KEaJ-browser-automation\webui-bundle --no-write
```

这一步把“已确认纠错必须真实影响最终人类可读输出”的要求继续向下游内容资产和 handoff 层推进了一格。

## 63. 2026-07-07 2026-07-07 15:50:15 | Codex / GPT-5：内容素材导出物内嵌通用语义纠错状态快照

本轮把“所有 ASR/字幕疑似错词的通用语义纠错闭环”继续下沉到内容素材导出层，避免下游只读取 content-material-card.json 或 content-candidate-pack.json 时绕过 content-asset-status 的 gate。

### 已落实到代码

- xport-knowledge-note 在构建导出物时读取 	ranscript_semantic_correction_status(root, write=false)。
- content-material-card.json 新增 	ranscript_semantic_correction 快照，包含：
  - status / ok
  - candidate_count / ccepted_decision_count /
eview_required_count
  - inal_residual_error_total
  -
eadable_impact_status /
eadable_required_residual_total
  - summary_impact_status / summary_absorption_rate / summary_residual_original_total
  - closure_status / corrected_transcript_exists
  -
ext_action_key
  - candidate_type_counts /
isk_level_counts / vidence_source_counts
  - sset_gate，复用内容资产状态里的语义纠错 gate 口径
  - 关键证据 artifact 路径
- content-candidate-pack.json 新增同样的 	ranscript_semantic_correction 快照。
- 每条内容候选新增：
  - semantic_correction_status
  - semantic_correction_gate_status
  - semantic_correction_review_count
  - semantic_correction_summary_impact_status
- content-material-card.md 与 content-candidate-pack.md 顶部显示语义纠错状态、gate 和下一步动作。
- manifest.json 与 knowledge_note_export 摘要写入 	ranscript_semantic_correction_status。

### 设计约束

- 素材卡和候选包仍然不是发布稿：publication_allowed=false、llowed_as_fact=false 不变。
- 语义纠错 gate 通过只表示“疑似错词已经进入纠正版转写、人类可读输出和智能总结影响检查”，不等于事实核查通过。
- 如果后续重新生成 smart summary 或重新跑语义纠错 impact，需要再次运行 xport-knowledge-note 刷新导出物快照。

### 验证

- 编译检查：
  - python -m py_compile src\\video_knowledge_pipeline\\knowledge_note_export.py tests\\test_knowledge_export.py
- 单测函数 smoke：
  - 	est_export_marks_smart_summary_draft_when_semantic_correction_missing 通过，确认素材卡、候选包、Markdown、manifest 都带语义纠错状态。
- 真实 bundle smoke：
  - BV134Ei6KEaJ-browser-automation 重新运行 xport-knowledge-note。
  - content-asset-status 返回 semantic_correction_status=impact_passed。
  - content-material-card.json、content-candidate-pack.json、候选条目均显示 semantic_correction_gate_status=passed。

### 仍需后续处理

- 该真实 bundle 的 smart_summary_final_status 当前仍为 draft_quality_failed，原因是总结质量检查中的 segment_not_asr_dump 与 alanced_sections 未通过。这属于智能总结成品质量问题，不再是 ASR/字幕疑似错词语义纠错闭环本身的问题。

## 64. 2026-07-07 2026-07-07 15:57:00 | Codex / GPT-5：语义纠错 gate 未通过时阻断素材卡直接作为 inspiration

在第 63 节之后继续收紧下游旁路：仅把语义纠错状态写入素材卡还不够，因为粗糙下游可能只读取 llowed_as_inspiration。本轮把导出物本体的安全布尔值也接到语义纠错 gate。

### 已落实到代码

- content-material-card.json：
  - 当 	ranscript_semantic_correction.asset_gate.passed=true 时，保持 llowed_as_inspiration=true 与 circle_of_friends_status=needs_review_inspiration。
  - 当 gate 未通过时，写为 llowed_as_inspiration=false、circle_of_friends_status=semantic_correction_required、locked_reason=semantic_correction_not_passed、
ext_action=finish_transcript_semantic_correction_before_handoff。
- content-candidate-pack.json 与每条 candidate：
  - gate 通过时继续允许作为待审核灵感素材。
  - gate 未通过时 llowed_as_inspiration=false，避免绕过 content-asset-status 的低质量消费。
- content-asset-status 增加两个解释字段：
  - semantic_blocked_material_card_flags
  - semantic_blocked_content_candidate_pack_flags
- content-asset-status 现在能区分：
  - 普通导出损坏：material_card_needs_reexport / content_candidate_pack_needs_reexport
  - 语义纠错未完成导致的安全阻断：semantic_correction_needs_action

### 验证

- 夹具 smoke：语义纠错未通过时，素材卡与候选包 llowed_as_inspiration=false，content-asset-status.status=semantic_correction_needs_action。
- 真实 BV134Ei6KEaJ-browser-automation bundle：语义纠错 gate 已通过，素材卡、候选包、候选条目均保持 llowed_as_inspiration=true，content-asset-status=ready_for_inspiration_review。

### 边界

- 这不是事实核查通过。即使语义纠错 gate 通过，llowed_as_fact=false 与 publication_allowed=false 仍保持不变。
- 语义纠错 gate 控制的是“可否作为待审核灵感素材进入内容资产链路”，不是自动发布许可。

## 65. 2026-07-07 2026-07-07 16:05:11 | Codex / GPT-5：内容素材 gate 对齐低置信非阻塞与 no-candidates 防漏规则

本轮修正内容素材 gate 的两个边界，使其更符合本文档第 3.3、13、24、83、88 节的目标：低置信候选不阻塞，但必须可见；没有候选不能自动等于没有错词，必须先经过候选发现防漏。

### 已落实到代码

- content_asset_status._semantic_asset_gate 不再要求
eview_required_count == 0 才能通过。
- 当以下条件同时成立时，即使仍有 open review 候选，也允许素材进入
eady_for_inspiration_review：
  - status=impact_passed
  - inal_residual_error_total=0
  -
eadable_impact_status=passed
  -
eadable_required_residual_total=0
  - summary_impact_status 为 passed /
o_accepted_decisions /
o_evaluable_replacements
  - summary_residual_original_total=0
- 如果仍有 open review 候选，gate 状态写为 passed_with_open_review，并输出：
  -
eview_required_count
  -
eview_required_nonblocking=true
-
o_candidates 不再天然通过。只有 candidate discovery 已经进入可解释终态时才允许通过：
  -
o_segments_selected
  -
o_suggestions
  -
o_candidates_imported
  - imported
- 如果 status=no_candidates 但 candidate_discovery_status=not_planned/prompt_ready/llm_prompt_ready/suggestions_ready/model_output_parse_failed 等未闭合状态，gate 返回：
  - passed=false
  - status=needs_candidate_discovery
  -
ext_action_key=run_candidate_discovery 或当前 discovery next action

### 为什么要这样改

此前内容资产 gate 要求
eview_required_count == 0，会把低置信待复核项变成硬阻塞，违背“低置信不阻塞但显性暴露”的目标。另一方面，
o_candidates 直接通过又会绕开候选发现防漏，导致系统可能因为初始规则没召回候选而误判为干净。

新的规则把两者分开：

- 已确认高置信纠错必须完整闭环并影响最终可读文件；
- 低置信项可以继续作为 review backlog 可见存在；
- 没跑候选发现的 no-candidates 不能进入内容素材交接。

### 验证

- 	est_semantic_asset_gate_keeps_low_confidence_review_nonblocking：impact/readable/summary 均通过且仍有 3 条 open review 时，gate 为 passed_with_open_review。
- 	est_semantic_asset_gate_does_not_accept_no_candidates_before_discovery：未跑 candidate discovery 的 no-candidates 返回
eeds_candidate_discovery。
- 真实 BV134Ei6KEaJ-browser-automation bundle 仍为：
  - content_asset_status=ready_for_inspiration_review
  - semantic_correction_asset_gate.status=passed
  - semantic_correction_review_count=0

### 边界

- passed_with_open_review 只允许作为待审核 inspiration，不允许发布，不允许当作事实。
- open review 候选必须继续出现在 batch/handoff/review pack 中，后续可由人工、Codex 或在线 LLM 继续关闭。

## 66. 2026-07-07 16:18:00 | Codex / GPT-5：最终 smart-summary 自动接入 Codex 替代总结，但继续受语义纠错 gate 约束

本轮把“Codex 代替在线 LLM”的智能总结层从可选命令推进到默认导出链路：`export-knowledge-note` 在生成最终 `exports/smart-summary.md` 前，会先检查是否已有人工/LLM 成品 `exports/smart-summary.codex.md`；如果没有且本次是写入导出，则自动调用现有 `generate_smart_summary_with_codex` 生成本地 Codex 替代版，然后最终 `smart-summary.md` 优先采用该成品。

### 为什么要这样改

语义纠错闭环的目标不是只生成一堆中间 JSON，而是让纠正版 transcript 和证据仲裁真正影响用户会阅读的文件。此前存在一个断点：

- `generate-smart-summary-with-codex` 已经能生成更像成品的 `smart-summary.codex.md`；
- 但普通导出仍可能只产出 `codex_assisted_draft` 规则草稿；
- 规则草稿虽然结构完整，但容易变成 ASR 摘抄或关键词拼接；
- 用户打开最终 `smart-summary.md` 时，未必能看出它还不是成品总结。

新规则把导出流程改成：能生成 Codex 替代总结时就生成，不能生成或质量门禁不过时，明确降级为 draft，不再把规则草稿伪装成最终智能总结。

### 已落实到代码

- `knowledge_note_export.export_knowledge_note` 新增默认接线：
  - 先生成 `smart-summary-codex-prompt.md`；
  - 调用 `_ensure_smart_summary_codex_summary(...)`；
  - 若已有 `smart-summary.codex.md`，不覆盖，直接复用；
  - 若没有且 `write=True`，调用 `generate_smart_summary_with_codex(root, write=True)`；
  - 再调用 `_render_smart_summary(...)`，让最终 `smart-summary.md` 优先读取 Codex 替代版。
- `export-summary.json` 与 `manifest.knowledge_note_export` 记录 `smart_summary_codex` 状态，后续 UI / OpenClaw / MCP 可以判断：
  - 是否自动生成；
  - 是否已有人工/LLM 成品；
  - 对应质量检查是否通过。
- 测试同步改为区分两种情况：
  - 已完成语义候选扫描且无候选：Codex 替代总结可以通过质量门禁；
  - 未完成语义纠错：即使 Codex 替代总结结构合格，也只能是 `draft_needs_semantic_correction`。

### 质量门禁仍然保留

自动生成 Codex 替代总结不等于语义纠错闭环完成。最终 `smart-summary.md` 仍必须通过这些 gate：

- `codex_final`：不能是 `codex_assisted_draft`；必须来自 `smart-summary.codex.md`、`codex_first_llm_substitute` 或人工/LLM final 标记。
- `term_correction_impact`：工具名、专名、品牌名等高置信纠错必须进入最终导出。
- `transcript_semantic_correction_impact`：所有 ASR/字幕疑似错词的通用语义纠错必须完成候选发现、验证、闭环、可读文件影响检查。
- `overview_readable`：一句话概览不能是关键词拼接。
- `segment_not_asr_dump`：分段总结不能是大段 ASR 原文复制。
- `time_coverage` 与 `balanced_sections`：总结必须覆盖完整视频时长，关键观点、动作清单、话术不能只集中在前几分钟。
- `visual_boundary`：没有执行或没有可靠提取的视觉证据必须保留待复核边界。

### 与低置信候选的关系

低置信候选仍然是非阻塞 review backlog，但不能被吞掉：

- 高置信、已接受的纠错必须进入 `source-arbitrated-transcript.json`、`full-transcript.md`、`smart-summary.md`、素材卡和候选包；
- 低置信候选可以不阻塞内容素材作为 `needs_review_inspiration` 流转；
- 但它们必须继续出现在 review/status/handoff 中，不能因为 Codex 总结生成成功而消失；
- 如果候选发现本身没跑，`no_candidates` 不能被当作干净，素材交接 gate 返回 `needs_candidate_discovery`。

### 验证

- `py_compile` 覆盖：
  - `src/video_knowledge_pipeline/knowledge_note_export.py`
  - `src/video_knowledge_pipeline/content_asset_status.py`
  - `src/video_knowledge_pipeline/smart_summary_codex.py`
  - `tests/test_knowledge_export.py`
- 直接函数 smoke 覆盖：
  - `test_generate_smart_summary_with_codex_auto_generates_local_final`
  - `test_codex_smart_summary_quality_gate_and_final_export`
  - `test_semantic_asset_gate_keeps_low_confidence_review_nonblocking`
  - `test_semantic_asset_gate_does_not_accept_no_candidates_before_discovery`
- `pytest` 当前仍受 Windows 临时目录 PermissionError 影响，不能作为本轮完整门禁；本轮用直接函数 smoke 验证真实断言。

### 剩余边界

- 这仍是本地 Codex 替代 LLM 的第一版，不等于在线强 LLM 的最终质量；后续可把同一 evidence pack 接到在线文本 LLM provider。
- 自动生成不会覆盖用户已经写好的 `smart-summary.codex.md`。
- 语义纠错未完成时，`smart-summary.md` 可以存在，但状态必须是 draft，不能作为最终事实笔记或发布素材。
## 94. 实现进展记录：2026-07-07 16:29:00 单 bundle 语义纠错验收证明入口

执行者：Codex / GPT-5

本轮新增单视频/单 bundle 的只读验收证明入口，避免每次都用批量验收来判断一个视频是否完成语义纠错闭环。新入口复用批量验收内部的 per-bundle 判定逻辑，因此不会出现“单视频状态”和“批量状态”两套规则分叉。

### 94.1 新增接口

| 层 | 入口 | 说明 |
| --- | --- | --- |
| Python | `transcript_semantic_acceptance(bundle_dir, output_dir="", write=True)` | 读取当前 bundle 证据，生成单 bundle acceptance JSON/Markdown。 |
| CLI | `transcript-semantic-acceptance <bundle_dir> [--output-dir DIR]` | 输出 `transcript-semantic-acceptance.json/md`。 |
| MCP | `transcript_semantic_acceptance` / `transcript_semantic_acceptance_tool` | 给 Codex/OpenClaw/其他 agent 调用。 |
| Task Console | `单视频语义纠错验收证明` 命令 | UI 中能复制执行，只读检查。 |

### 94.2 输出字段

最小输出包括：

```json
{
  "schema": "video_knowledge_pipeline.transcript_semantic_acceptance.v1",
  "ok": true,
  "status": "accepted | needs_semantic_correction_action",
  "acceptance_state": "accepted | accepted_no_candidates | needs_pack | needs_review | needs_closure | needs_impact_report | needs_summary_impact_report | needs_candidate_discovery | ...",
  "semantic_status": "impact_passed | no_candidates | missing_pack | ...",
  "next_action_key": "none | build_pack | run_closure | run_summary_impact | ...",
  "item": "同 batch acceptance 的 per-bundle row",
  "next_actions": []
}
```

### 94.3 安全边界

该入口是纯只读证明：

- 不跑 ASR。
- 不跑 OCR/视觉/多模态。
- 不下载视频。
- 不调用云端 LLM。
- 不 validate、不 closure、不 export。
- 不修改原始 ASR、字幕或媒体文件。

### 94.4 为什么需要它

批量验收适合 3-5 个真实视频的阶段性验收，但真实调试一个长视频时，用户和 agent 更需要“一眼看懂这个 bundle 现在是否闭环”的证明文件。单 bundle acceptance 解决这个问题：

- 输出更短、更适合放进 Task Console / OpenClaw live smoke；
- 仍保留 evidence file 存在性、candidate/review/residual/summary-impact 数字；
- 可直接告诉下一步命令；
- 与 batch acceptance 使用同一个 `_row_for_bundle`，后续规则只维护一份。

### 94.5 验证记录

编译检查通过：

```text
python -m py_compile src\video_knowledge_pipeline\transcript_semantic_batch.py src\video_knowledge_pipeline\transcript_semantic_correction.py src\video_knowledge_pipeline\cli.py src\video_knowledge_pipeline\mcp_server.py src\video_knowledge_pipeline\task_console.py tests\test_transcript_semantic_batch.py
```

函数级 smoke 通过：

```text
test_transcript_semantic_acceptance_writes_single_bundle_proof
=> single acceptance direct smoke passed
```

CLI smoke 通过：

```text
python -m video_knowledge_pipeline.cli transcript-semantic-acceptance semantic-acceptance-cli-smoke\webui-bundle --output-dir semantic-acceptance-cli-smoke\report2
=> status=accepted, acceptance_state=accepted_no_candidates, ok=true
```

顺手修复：`transcript_semantic_correction_status.commands.import_candidate_suggestions` 里的 `--input-json` 路径缺少结尾引号，现在输出命令可直接复制执行。
## 95. 实现进展记录：2026-07-07 16:35:00 真实 bundle summary-impact 缺口自动推进到闭合

执行者：Codex / GPT-5

本轮用真实 bundle 验证第 94 节新增的单视频验收入口，不只检查已完成样例，也检查未闭合样例能否给出机器可执行下一步。发现并修复了一个状态映射缺口：当底层 `transcript_semantic_correction_status` 返回 `needs_summary_impact_report` 时，单 bundle acceptance 曾显示为 `needs_inspection`，导致用户和 agent 看不到明确下一步。现在该状态会正确映射到 `acceptance_state=needs_summary_impact_report`，repair queue 会给出 `run_summary_impact`。

### 95.1 修复内容

- `_acceptance_state(...)` 新增状态映射：
  - `semantic_status=needs_summary_impact_report` -> `acceptance_state=needs_summary_impact_report`
  - `semantic_status=summary_impact_needs_fix` -> `acceptance_state=needs_summary_refresh_or_review`
- 这样单 bundle acceptance、batch acceptance、repair queue 三者对 summary impact 缺口的判断一致。

### 95.2 真实 bundle 验证

样例：

```text
openclaw-runs\knowledge\tiktok-crossborder-day2\webui-bundle
```

修复前/执行前只读验收：

```text
status=needs_semantic_correction_action
acceptance_state=needs_summary_impact_report
semantic_status=needs_summary_impact_report
next_action_key=run_summary_impact
candidate_count=55
accepted_decision_count=2
final_residual_error_total=0
summary_impact_status=missing_report
```

repair queue 正确给出：

```text
action_key=run_summary_impact
machine_action_available=true
human_review_required=false
progress=87.5%
```

执行安全本地动作：

```powershell
python -m video_knowledge_pipeline.cli transcript-semantic-repair-run `
  openclaw-runs\knowledge\tiktok-crossborder-day2\webui-bundle `
  --target-bundle-count 1 `
  --execute-safe-actions `
  --max-actions 1 `
  --max-rounds 1
```

执行结果：

```text
status=completed
executed_count=1
action_key=run_summary_impact
result_status=passed
```

执行后队列：

```text
status=complete
action_key=none
semantic_status=impact_passed
acceptance_state=accepted
progress=100%
summary_impact_status=passed
summary_impact_corrected_hit_total=68
summary_impact_absorption_rate=1.0
```

最终单 bundle acceptance：

```text
status=accepted
acceptance_state=accepted
semantic_status=impact_passed
next_action_key=none
candidate_count=55
accepted_decision_count=2
review_required_count=0
final_residual_error_total=0
summary_impact_status=passed
summary_impact_residual_total=0
summary_impact_corrected_hit_total=68
summary_impact_absorption_rate=1.0
```

### 95.3 安全边界

本次真实 bundle 推进只执行了本地 summary impact 报告：

- 不跑 ASR。
- 不跑 OCR/视觉/多模态。
- 不调用在线 LLM。
- 不下载视频。
- 不修改原始 ASR / 字幕 / 视频。
- 不执行 closure，也不重新写 transcript。

### 95.4 验证命令

编译检查：

```text
python -m py_compile src\video_knowledge_pipeline\transcript_semantic_batch.py tests\test_transcript_semantic_batch.py
```

函数级 smoke：

```text
test_transcript_semantic_repair_queue_requires_summary_impact_after_readable_passed
test_transcript_semantic_repair_run_executes_summary_impact_report
=> summary impact queue smoke passed
```

### 95.5 对完整目标的意义

这一步证明闭环不仅能验收已经完成的样例，也能把真实未闭合 bundle 的“最后一公里”缺口自动转成安全本地动作并完成。后续仍需继续处理更早阶段未闭合的 bundle，例如 `missing_pack`、`needs_review`、`needs_closure`，并扩大到 3-5 个真实视频的批量验收。
## 96. 可选人工复核不阻塞本地机器闭环的状态机修正

更新时间：2026-07-07 16:52:41
执行者：Codex / GPT-5

目标文档要求“低置信冲突进入人工复核”，但用户也明确过：人工确认复核是可选项，不作为必选、不造成阻塞。本轮修正的是 batch acceptance / repair queue 中的一个状态优先级问题：当 bundle 已有 accepted correction、残留为 0、但还有少量 open review target 时，机器仍应继续执行 closure / impact / readable impact / summary impact 等本地安全动作，而不是被 `review_required_count > 0` 直接挡到 `needs_review`。

### 96.1 修复内容

`transcript_semantic_batch._acceptance_state(...)` 的优先级调整为：

```text
missing_pack / no_candidates
  -> needs_closure
  -> needs_impact_report
  -> needs_summary_impact_report
  -> summary_impact_needs_fix
  -> residual / export refresh
  -> needs_llm_or_codex_review / needs_human_review_or_new_result / review_required_count
```

也就是说：

- 如果已有可执行的本地机器动作，先返回对应机器动作状态。
- `review_required_count > 0` 继续保留在报告中，但不抢占 summary impact、closure、impact 等下一步。
- 当没有可推进机器动作，只剩低置信或冲突候选时，才返回 `needs_review`。

### 96.2 新增回归用例

新增测试：

```text
test_transcript_semantic_repair_queue_keeps_summary_impact_machine_action_with_optional_review
```

它构造一个 accepted decisions 已存在、summary impact 缺失、同时还有 `review_required_count=1` 的 bundle，期望：

```text
acceptance_state=needs_summary_impact_report
action_key=run_summary_impact
machine_action_available=true
human_review_required=false
```

因为当前 Windows pytest tmpdir 存在权限问题，pytest 命令在 session setup/finish 阶段被 `PermissionError` 阻断；已用直接函数调用 smoke 验证该测试逻辑通过：

```text
direct optional review summary-impact smoke passed
```

### 96.3 真实 bundle 验证：summary impact 不再被可选 review 阻塞

样例：

```text
openclaw-runs\knowledge\tongyi-teacher-20260624-live-replay-rerun-current\webui-bundle
```

修复前该 bundle 因 `review_required_count=1` 显示为 `acceptance_state=needs_review`，但真正机器下一步是 `run_summary_impact`。修复后只读 acceptance 显示：

```text
status=needs_semantic_correction_action
acceptance_state=needs_summary_impact_report
semantic_status=needs_summary_impact_report
next_action_key=run_summary_impact
candidate_count=80
accepted_decision_count=4
review_required_count=1
final_residual_error_total=0
summary_impact_status=missing_report
```

repair queue 显示：

```text
status=machine_actions_available
action_key=run_summary_impact
machine_action_available=true
human_review_required=false
progress=87.5%
```

执行本地安全动作：

```powershell
python -m video_knowledge_pipeline.cli transcript-semantic-repair-run `
  openclaw-runs\knowledge\tongyi-teacher-20260624-live-replay-rerun-current\webui-bundle `
  --target-bundle-count 1 `
  --execute-safe-actions `
  --max-actions 1 `
  --max-rounds 1
```

执行后：

```text
status=complete
acceptance_state=accepted
semantic_status=impact_passed
action_key=none
review_required_count=1
summary_impact_status=passed
summary_impact_residual_total=0
summary_impact_corrected_hit_total=312
summary_impact_absorption_rate=1.0
```

这证明可选 review target 会保留在报告里，但不会阻塞已接受纠正进入最终 summary impact 验收。

### 96.4 真实 bundle 验证：通用候选不只覆盖术语

样例：

```text
openclaw-runs\knowledge\tongyi-teacher-20260624-live-replay\webui-bundle
```

该 bundle 原状态：

```text
semantic_status=missing_pack
acceptance_state=needs_pack
action_key=build_pack
```

执行本地安全动作后生成 evidence pack：

```text
result_status=pack_ready
candidate_count=246
candidate_group_count=177
```

候选类型覆盖：

```text
number=84
segment_boundary=25
proper_noun=69
punctuation=43
ordinary_word=13
action=12
```

风险覆盖：

```text
high=152
medium=94
```

这说明当前通用语义纠错 pack 已经覆盖数字、断句、专名、标点、普通错词和动作词，不再只是术语/工具名纠错。

### 96.5 安全边界

本轮真实 bundle 推进只执行本地安全动作：

- 不跑 ASR。
- 不跑 OCR/视觉/多模态。
- 不调用在线 LLM。
- 不下载视频。
- 不修改原始 ASR / 字幕 / 视频。
- 不执行 closure。
- 只生成本地 pack、repair queue、summary impact report 和验收报告。

### 96.6 对完整目标的意义

这一步补齐了两个关键验收点：

1. `review_required_count` 不再把可机器完成的最后一公里挡住，符合“人工复核可选、不阻塞”的产品原则。
2. 真实长视频 pack 已证明候选发现覆盖数字、动作、普通错词、标点和断句，符合“所有 ASR/字幕疑似错词”而非“术语仲裁”的目标方向。

完整目标仍未结束：后续还要继续推进更多 bundle 的 Codex/LLM 语义判断、closure、readable impact、summary impact 和批量 3-5 视频验收。
## 97. 2026-07-07 17:21:29 | Codex / GPT-5：安全缩写白名单与最终摘要覆盖闭环

### 97.1 本次修复的问题

在真实长视频 bundle 上推进通用 ASR/字幕语义纠错时，发现两个容易把“疑似错词”误写成“已确定纠错”的风险：

1. Codex-substitute 草稿如果扫描 `context_text`，可能把上下文里的 `a i` 误绑定到另一个候选，例如数字候选 `一个`。
2. 字母间隔缩写如果只看 compact 相等，可能把不确定缩写自动写成大写，例如 `g p d -> GPD`、`h t t m l -> HTTML`。这些看起来像缩写，但很可能其实是 `GPT`、`HTML` 或其它词，必须交给 LLM/人工/视觉证据复核。

### 97.2 代码侧安全收口

本次在 `src/video_knowledge_pipeline/transcript_semantic_correction.py` 做了三类收口：

- `_candidate_draft_correction_matches` 不再扫描 `context_text`，只使用 `original_text`、`candidate_text`、`suggested_text`；并且跳过高风险、需要人审、非专名/术语/概念/普通错词类型。
- 新增 `SAFE_ACRONYM_NORMALIZATIONS`，当前只允许 `AI`、`SEO`、`SKU`、`APP`、`app` 这类已确认安全缩写自动通过。
- `_candidate_draft_acronym_normalization` 只有在“同字母、同顺序、同 compact 文本、命中安全白名单、非事实值、非动作语义、有 evidence id”时才生成可自动 validate 的决策。

这意味着：

```text
s e o -> SEO     可以由本地 Codex-substitute 自动接受
s k u -> SKU     可以由本地 Codex-substitute 自动接受
a i -> AI        可以由本地 Codex-substitute 自动接受
g p d -> GPD     不自动接受，进入 LLM/人工/更多证据
h t t m l -> HTTML 不自动接受，进入 LLM/人工/更多证据
```

### 97.3 最终人类可读摘要的二次覆盖

真实验收发现：closure 后 `source-arbitrated-transcript.json` 和 `full-transcript.md` 已经吸收纠错，但 `smart-summary.md` 可能因为旧 Codex 草稿、视觉标签、摘要缓存而重新出现已接受错词残留。

本次新增 `_apply_validated_corrections_to_readable_exports(root)`：

- 只读取已经通过 `validate-transcript-semantic-correction` 的 `accepted_decisions`。
- 只修改派生可读摘要：`exports/smart-summary.md`、`exports/smart-summary.codex.md`。
- 不修改原始 ASR、字幕、timeline、OCR、视觉证据、`knowledge-note.md` 审计层。
- 在 `_refresh_semantic_correction_outputs` 中位于 `export_knowledge_note(root)` 之后、impact/readable/summary impact 报告之前执行。

这个设计保留了证据层的原貌，同时保证用户最终阅读和复制的智能总结层不会继续暴露已高置信接受的错词。

### 97.4 新增测试与轻量验证

新增/强化测试用例：

- `test_semantic_correction_codex_draft_accepts_safe_spaced_acronym_normalization`
- `test_semantic_correction_codex_draft_does_not_attach_known_term_to_number_candidate_context`
- `test_semantic_correction_codex_draft_does_not_attach_context_term_to_different_proper_candidate`
- `test_semantic_correction_codex_draft_keeps_unknown_spaced_acronym_for_review`

轻量验证：

```text
ast syntax check passed
直接函数 smoke：SEO 自动通过，GPD 不自动通过，数字候选上下文里的 AI 不会错绑。
```

受当前 Windows pytest 临时目录权限影响，定向 pytest 未能启动 fixture；失败点是 `PermissionError: C:\tmp\vkp-pytest-semantic-correction`，不是断言失败。

### 97.5 真实长视频验收结果

验收 bundle：

```text
openclaw-runs\knowledge\tongyi-teacher-20260624-live-replay\webui-bundle
```

重新生成 Codex-substitute draft 后，自动接受决策从此前不安全的 15 条收窄为 7 条：

```text
tiktok -> TikTok
s e o -> SEO
a p p -> app
s k u -> SKU
whatsapp -> WhatsApp
a i -> AI
shopify -> Shopify
```

明确没有进入自动决策的高风险/不确定缩写：

```text
GPD / HTTML / HQB / VES / AEI
```

closure 结果：

```text
accepted_decision_count=7
applied_correction_count=49
changed_segment_count=43
```

最终 refresh 结果：

```text
impact_status=passed
readable_impact_status=passed
summary_impact_status=passed
readable_patch_status=applied
readable_patch_replacement_count=24
```

最终 acceptance：

```text
status=accepted
acceptance_state=accepted
semantic_status=impact_passed
next_action_key=none
summary_impact_status=passed
summary_impact_residual_total=0
summary_impact_corrected_hit_total=33
summary_impact_absorption_rate=0.8571
```

这证明：

1. 安全纠错已经进入 `source-arbitrated-transcript.*`。
2. `full-transcript.md` 和 `smart-summary.md` 都能吸收已接受纠错。
3. 不确定缩写不会被本地规则强行纠正。
4. 最终人类可读摘要层已经纳入通用 ASR/字幕语义纠错闭环。

### 97.6 仍未完成的完整目标

这次只证明了一个真实长视频 bundle 的完整闭环。完整目标仍需要继续推进：

- 对 3-5 个真实 bundle 跑批量 acceptance。
- 对仍需 LLM/人工判断的数字、动作、断句、普通错词做语义判断。
- UI/Task Console 中完整展示每个候选状态、重试命令和最终摘要吸收状态。
- 在线 LLM provider 批量执行仍要保持显式确认和限量调用。

## 98. 2026-07-07 17:34:57 | Codex / GPT-5：批量验收与 Task Console 验收补充

在第 97 节的单真实长视频闭环基础上，本轮补齐批量验收和 UI 可见性验收。

### 98.1 批量 acceptance

命令：

~~~powershell
$env:PYTHONDONTWRITEBYTECODE='1'
$env:PYTHONPATH='src'
python -m video_knowledge_pipeline.cli transcript-semantic-batch-acceptance openclaw-runs\knowledge --target-bundle-count 3 --limit 4
~~~

结果摘要：

~~~text
status=accepted
ok=true
bundle_count=4
accepted_count=4
not_accepted_count=0
candidate_count=411
accepted_decision_count=22
review_required_count=1
final_residual_error_total=0
~~~

4 个真实 bundle 均为 accepted，语义状态均为 impact_passed。这说明闭环不是只对单个演示 bundle 有效，而是可以在多个本地真实视频包上进行只读批量验收。

### 98.2 Task Console 状态展示

验收 bundle：

~~~text
openclaw-runs\knowledge\tongyi-teacher-20260624-live-replay\webui-bundle
~~~

已重新生成：

~~~text
task-console.json
task-console.html
~~~

HTML 中已确认出现：

- 通用语义纠错闭环进度摘要
- 自动候选与需人工候选
- 通用语义纠错修复/重试队列
- summary impact / readable impact
- 重试按钮与本机安全动作 bridge 区域

### 98.3 最新完成判断

截至本记录，通用 ASR/字幕疑似错词语义纠错闭环已经具备：

1. 候选召回。
2. Codex/LLM 决策入口。
3. 本地 validate 安全门禁。
4. closure 写入纠正版 transcript。
5. full-transcript 与 smart-summary 吸收纠错。
6. impact/readable/summary impact 证明。
7. 单 bundle acceptance。
8. 4 个真实 bundle 批量 acceptance。
9. repair queue / repair run 的 UI 和 CLI 入口。
10. 低置信项不阻塞但可见。

仍需作为后续增强而非当前阻塞项处理：更强的在线 LLM 语义判断、更细的数字/动作/断句抽样人工评估、更多垂直领域词典，以及把这些审查结果持续喂回术语库。
