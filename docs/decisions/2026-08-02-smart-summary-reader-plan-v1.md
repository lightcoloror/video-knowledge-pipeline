# VKP 成熟智能总结：结构化全局归纳与读者质量门

- 状态：implemented / offline-verified
- 执行者：Codex（GPT-5.6）
- 更新时间：2026-08-02 10:50:49
- 生效版本：`smart_summary_reader_plan.v1`
- 在线调用：本轮 0 次

## 结论

成熟智能总结不能继续依赖“让在线模型直接拼最终 Markdown”。VKP 改为：

```text
章节事实包（Map）
→ 有界分层归并（Reduce input）
→ 在线模型生成 reader plan JSON
→ JSON Schema + evidence + 时间 + 语义质量门
→ VKP 确定性渲染 Markdown
→ 既有 Smart Summary 完整质量门
```

模型负责理解、聚合、抽象和重组；VKP 负责系统已知事实、字段合同、证据校验、版式、可追溯性和是否允许安装。这样可以同时提升内容成熟度、输出稳定性和跨供应商一致性。

## 现状证据

两条最新真实 Bundle 的旧摘要虽然格式完整，但新的离线读者质量门均判定不成熟：

- `每天都有客户主动咨询的秘诀`：存在生成过程元话术、弱主题标题、章节时间重叠和伪动作项。
- `2026年7月24日全国大早会`：同类问题更明显，且有一段覆盖大范围时长的章节与后续章节重叠。

改造后的无网络 Reduce 预检：

| Bundle | 章节 | 改造前输入 | 改造后输入 | 章节保留 | 当前状态 |
|---|---:|---:|---:|---:|---|
| 每天都有客户主动咨询的秘诀 | 6 | 52,402 字符 | 36,225 字符 | 6/6 | ready for scoped execute |
| 2026年7月24日全国大早会 | 11 | 74,482 字符且超预算 | 57,789 字符 | 11/11 | ready for scoped execute |

本轮没有覆盖既有 `smart-summary.codex.md`，也没有调用在线模型。

## 固定源码与运行证据

### LlamaIndex TreeSummarize

- 本地源码：`%WORKSPACE_ROOT%\reference-repos\bookwiki-mainline\llama_index`
- 固定 commit：`d8d7ffbb119a481147856392bba5bca549283030`
- 研究入口：`llama-index-core/llama_index/core/response_synthesizers/tree_summarize.py`
- 复用：按上下文预算重打包、每章公平保留、递归归并思想。
- 运行证据：本地 `TreeSummarize + MockLLM` smoke 成功；上游精确 pytest 因本机缺 `pytest-asyncio` 未启动，不误报为通过。
- 决定：复用架构，不引入 LlamaIndex 运行时依赖。

### BiliNote

- 本地源码：`%WORKSPACE_ROOT%\tool-source-review\BiliNote`
- 固定 commit：`095d772c7d0f2f4ba1e65c36b7ceb1e2db34723d`
- 研究入口：`backend/app/gpt/prompt_builder.py`
- 复用：把“内容格式”和“写作风格”分开；VKP 进一步把格式完全交给确定性 renderer。
- 运行证据：`test_universal_gpt_content_format.py` 6/6 通过。checkpoint 关联测试出现 1 个上游断言失败及 Windows 临时目录 ACL 问题，该部分没有吸收。
- 决定：只吸收职责分离，不复制提示词或状态机。

### Haystack JsonSchemaValidator

- 本地源码：`%WORKSPACE_ROOT%\reference-repos\bookwiki-mainline\haystack`
- 固定 commit：`acbf725a387dffc849b2f9bd2972d0db92e251fe`
- 研究入口：`haystack/components/validators/json_schema.py`
- 复用：`validated` 与 `validation_error` 分支的“先校验、后消费”模式。
- 运行证据：源码级路径已核对；完整 Haystack import 因本机缺 `lazy_imports` 未启动。
- 决定：不为一个校验器引入整套 Haystack，直接使用其底层成熟库 `jsonschema`。

### python-jsonschema

- 官方源码：`%WORKSPACE_ROOT%\source-reviews\vkp-summary-reader-v2-20260802\jsonschema`
- 版本：`v4.25.1`
- 固定 commit：`331c38425519b69118d22ebe467ad230fb83a010`
- 许可证：MIT
- 运行证据：官方 `jsonschema/tests/test_validators.py` 303/303 通过。
- 复用：直接调用 `Draft202012Validator`，不复制验证算法。

### RapidFuzz + jieba

- RapidFuzz commit：`edf9f3c2d016c878dae1511301f8b4a501bba871`
- jieba commit：`1e20c89b66f56c9301b0feed211733ffaa1bd72a`
- 复用：中文分词后的同义重复候选门；它只判断词面高度重叠，不证明语义事实。
- 决定：延续 VKP 已评审依赖，不新增第二套文本相似度算法。

### Chain-of-Density

- 来源：Adams 等，NewSum 2023。
- 吸收：在有限篇幅内提高信息密度、先识别遗漏信息再压缩表达的设计思想。
- 拒绝：不复制第三方非官方 prompt 实现，不让模型输出或保存思考过程，不使用固定新闻摘要长度作为课程统一阈值。

## 变更记录

### SS-RP-001：结构化 reader plan

- 意图：让在线 API 模型输出可验证的内容决策，而不是自由格式文档。
- 决策：新增 `video_knowledge_pipeline.smart_summary_reader_plan.v1`，包含概览、4–8 条核心洞察、3–8 个互斥主题、方法论、行动、原句/表达和待复核项。
- 理由：自由 Markdown 可以看起来流畅，却把元话术、截断标题和伪动作隐藏在格式合格结果中。
- 证据：两条真实摘要均命中新语义缺口；Haystack 使用 JSON Schema 将验证成功与失败分支分开。
- 生效范围：`smart-summary-global-reduce --execute` 的新模型输出；不改变章节 Map、Timeline 或逐字稿。

### SS-RP-002：证据与时间硬门

- 意图：阻止模型补造引用、提升低置信内容或生成相互重叠的章节。
- 决策：每个确定性条目必须引用 fact pack 中存在的 eligible evidence；主题时间范围必须有序、互斥；review-only evidence 只能进入待复核项。
- 理由：系统已知的 evidence ID 和时间范围不应由模型自由陈述。
- 证据：旧摘要出现多处相互重叠时间范围；既有 fact pack 已提供 eligible/review-only 分组。
- 生效范围：global Reduce candidate 的安装前校验；原始证据不被改写。

### SS-RP-003：确定性 Markdown renderer

- 意图：跨 Gemini、DeepSeek、Qwen 等在线路线保持相同读者格式。
- 决策：模型不再决定二级标题、内部标记和字段排版；VKP 从已验证 reader plan 生成得到大脑式正文。
- 理由：格式不是模型能力问题，让模型承担只会增加漂移和 token。
- 证据：BiliNote 的格式/风格分离模块测试 6/6 通过；VKP renderer focused 回归通过。
- 生效范围：`smart-summary.codex.md` 候选；内部 evidence 字段不会出现在读者正文。

### SS-RP-004：有界事实投影

- 意图：长视频全局 Reduce 不丢后半段，同时降低网络流量和输入 token。
- 决策：保留每章 evidence group，按事实类型最多取 3 条、每章最多 12 条事实，并只附 4 条可用于原句核验的 snippet；章节 Map 文本按公平预算重打包。
- 理由：99 条逐项引用和重复章节文本会挤占上下文；普通结论只需引用章节 evidence group。
- 证据：11 章真实 Bundle 从超预算 74,482 降至 57,789 字符，11/11 章节仍在输入中。
- 生效范围：只影响发给 summary Reduce 模型的派生输入；完整 fact pack 仍本地保存。

### SS-RP-005：成熟度语义门

- 意图：让“像智能总结”成为机器可检查的生产条件。
- 决策：新增元话术、读者概览、语义标题、章节顺序/重叠、可执行动作、原句逐字匹配和同义重复检查。
- 理由：原质量门偏重格式、长度、数字和时间覆盖，无法识别内容组织是否成熟。
- 证据：新门在两个真实旧摘要上均发现对应缺口；新 renderer fixture 通过。
- 生效范围：global Reduce 形状门与最终 `smart-summary-quality`；不会自动改写旧摘要。

### SS-RP-006：兼容与失败策略

- 意图：升级新路线但不破坏旧 Bundle。
- 决策：旧 Markdown candidate 仍可显式复用，并标记 `compatibility_mode=true`；新在线响应若 JSON、Schema、证据或语义门失败，则保存原始响应并 fail-closed，不安装。
- 理由：不能为兼容性静默降低新合同，也不能因一次错误覆盖已有可读产物。
- 证据：现有 Phase 17 兼容回归继续通过。
- 生效范围：旧 Bundle 候选复用与新 global Reduce 失败恢复。

## 验证

```powershell
python -B -m pytest -q `
  tests\test_smart_summary_reader_plan.py `
  tests\test_smart_summary_global_reduce_fact_pack.py `
  tests\test_smart_summary_global_reduce_repack_budget.py `
  tests\test_smart_summary_global_reduce_review_gap_gate.py `
  tests\test_phase17_reuse_closure.py
```

- focused：24 passed。
- Smart Summary/导出扩展关联：60 passed。
- python-jsonschema 官方 validator：303 passed。
- 已知非产品告警：jieba 使用的 `pkg_resources` 发出弃用警告。

## 尚未执行

- 没有对两个真实 Bundle 发起新的在线 global Reduce 调用。
- 没有覆盖当前 `smart-summary.codex.md` 或 `exports-final`。
- 没有用人工金标准评价新摘要的洞察召回率和读者偏好。

下一次真实调用应在既有 provider gateway、business authorization、调用次数和费用上限内分别执行一次 global Reduce；安装前由本 ADR 的全部质量门自动决定是否接受。

## 2026-08-03 真实历史 Bundle 验证补记

- 执行者：Codex（GPT-5.6）
- 记录时间：2026-08-03 15:55:33
- 说明：本节是追加记录；上文“尚未执行”仅代表 2026-08-02 当时状态，现已由本节取代。

### SS-RP-007：已完成响应的本地规范化复用

- 意图：保留已经完成且已计费的在线响应，同时继续执行严格的最终质量门，避免为了可修复的标签错误再次调用模型。
- 决策：新鲜执行和 `--reuse-candidate` 统一调用 `normalize_reader_plan_candidate`；删除误放入 `actions` 的非动作陈述并记录 repair；短内容允许 3 条互不重复的核心洞察，仍拒绝少于 3 条或重复凑数。
- 理由：三次真实 Reduce 暴露了两个合同边界：首次沟通、TikTok 各有一条背景陈述误入行动列表；2 分 38 秒的 Browser 视频只有 3 条有效核心洞察，不应为了满足固定 4 条而重复观点。
- 证据：三次 provider 调用均已正常返回；本地严格校验分别命中 `non_action_item:actions[1]`、`core_insights minItems=4`、`non_action_item:actions[4]`。修复后 3/3 保存候选的 Reader Plan 均通过，且 `--reuse-candidate` 未产生网络请求。
- 生效范围：Smart Summary Global Reduce 的候选规范化和本地复用；不改变逐字稿、Timeline、原始 evidence、provider 路由或 consent 限额。

### 真实执行与验证证据

- 章节 Map：10/10 成功；首次沟通 5 章、Browser 1 章、TikTok 4 章。
- 全局 Reduce：3/3 provider 调用完成；零重试、无 fallback；仅上传精确哈希绑定的章节 Map 派生 JSON，未上传视频、音频、图片或原始 ASR。
- 本地复用：3/3 Reader Plan 通过 Schema、evidence、时间顺序和语义成熟度检查，并已刷新 `exports/smart-summary.md` 与 `exports/knowledge-note.md`。
- focused 回归：`12 passed, 1 warning`；警告仍为 jieba 的 `pkg_resources` 弃用提示。
- 当前最终质量边界：首次沟通仍受语音完整性、压缩率与数字一致性门阻断；Browser 受旧转录语义纠错影响与压缩率门阻断；TikTok 受旧转录纠错、视觉边界、压缩率与数字一致性门阻断。因此三份正文可供人工复核，但不得标记为 production-ready。