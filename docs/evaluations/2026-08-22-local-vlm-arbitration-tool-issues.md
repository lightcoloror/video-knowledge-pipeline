# 本地 VLM 仲裁与 VKP 交付流程问题记录（2026-08-22）

- acting_tool_model: `Codex (GPT-5.6 Sol)`
- updated_at: `2026-08-22 13:28:01 +08:00`
- scope: 本地 VKP 视频处理、本地 VLM 视觉仲裁、智能总结导出、质量门禁与最终验收
- network/provider calls: `0` remote requests；视觉调用仅使用 `http://127.0.0.1:1234/v1`
- input: `<private-local-video>`（公开仓库记录已去标识化）
- bundle: `<bundle>`（公开仓库记录已去标识化）
- handoff_status: `待交接原 VKP 线程；本文件已写入，尚未发送线程消息`

## 结论

本次流程能够完成本地 ASR、OCR、时间线、局部 VLM、知识导出、复核页刷新和验收报告生成，但在“视觉结果计数一致性、失败状态表达、质量检查路径解析、结构化序号误报、长响应截断”方面存在明显的工具使用坑和可改进点。

VKP 的 fail-closed 行为总体有效：不完整的 VLM 输出没有被写成确定性证据，正式智能总结也没有绕过逐字稿质量门。但当前多个命令同时返回 `status=ok/exported` 与内部失败或 `coverage_status=blocked`，消费方必须继续读取嵌套计数和门禁文件，不能只看顶层状态。

## 运行证据摘要

本次本地 VLM 运行记录位于 `vision-analysis-runs.jsonl`，关键批次如下：

| run_id | 选中 | 完整 | 截断/失败 | 备注 |
|---|---:|---:|---:|---|
| `semantic_frame-20260821-174904` | 19 | 19 | 0 | 首批局部视觉分析 |
| `semantic_frame-20260822-130229` | 47 | 1 | 46 | `max_tokens=700`，大多数响应被正确判定为截断 |
| `semantic_frame-20260822-131534` | 46 | 42 | 4 | `max_tokens=1800`，疑难帧 306、313、363、370 未完成 |
| `semantic_frame-20260822-131957` | 4 | 0 | 4 | `max_tokens=2400`，4 帧仍截断 |
| `semantic_frame-20260822-132422` | 4 | 0 | 4 | `max_tokens=5000`，4 帧仍截断，未写回证据 |

最终时间线对齐审计为 674 项、0 个对齐问题；最终导出统计为 `items_with_visual_understanding=61`、`visual_understanding_missing_count=613`。运行日志按批次累加得到 62 个完整运行结果，与导出/验收统计存在 1 项差异，见问题 `VKP-007`。

## 问题记录

### VKP-001：从仓库根目录直接运行 Python 模块会找不到包

- 现象：在 `<project-root>` 根目录执行 `python -m video_knowledge_pipeline.cli ...`，得到 `ModuleNotFoundError: No module named 'video_knowledge_pipeline'`。
- 影响：容易误判为 VKP 未安装或环境损坏；实际仓库的稳定入口是 `scripts\video-knowledge.ps1`。
- 当前规避：统一使用 `& ".\scripts\video-knowledge.ps1" <command> ...`；不要在未设置 `PYTHONPATH`/可编辑安装的情况下直接调用模块。
- 建议修复：在 README 和 CLI 错误提示中明确“仓库开发态必须通过 PowerShell wrapper 或安装 package”；必要时让 wrapper 注入 `src`，使直接模块调用和 wrapper 行为一致。
- 证据：本次 `vision-execution-preflight` 的第一次直接模块调用失败，随后 wrapper 调用成功。

### VKP-002：`--indexes` 的逗号列表必须显式引用

- 现象：不引用逗号列表时，PowerShell/参数解析可能把逗号后的索引拆成独立参数，出现 `unrecognized arguments`。
- 影响：预检确认的 index 集合与实际执行参数不一致，可能触发确认门禁或误执行错误批次。
- 当前规避：始终使用 `--indexes "306,313,363,370"`，并同时复制 `confirm_vision_indexes`。
- 建议修复：CLI 接受重复的 `--index 306 --index 313` 形式，或在错误信息中给出正确的 PowerShell 示例。

### VKP-003：本地 provider 配置可绕过不可用的远程 gateway，但报告仍显示远程网关噪声

- 现象：预检报告显示 `127.0.0.1:18776` gateway `unreachable`，同时显式本地配置 `http://127.0.0.1:1234/v1` 的 `ready_to_execute=true`。
- 影响：操作者容易误以为本地执行被远程依赖阻断；报告中 route-based gateway profile 与 explicit provider config 的关系不够醒目。
- 当前规避：显式传入 `vision-local-config.json`，确认 provider 为 `local_vlm`、model 为 `qwen/qwen3-vl-8b`，并核对 `remote_requests_made=false`。
- 建议修复：预检报告将“未使用的远程路由不可用”和“当前显式 provider 可执行”分成两个状态层级；顶层增加 `effective_provider` 与 `remote_fallback_disabled`。

### VKP-004：`provider_health=not_checked` 与 `ready_to_execute=true` 可以同时出现

- 现象：本次预检在未执行 provider smoke test 时，`provider_health.status=not_checked`，但 `ready_to_execute=true`。
- 影响：执行门禁只证明配置、候选数量和确认值匹配，不代表本地模型端点已通过健康检查；首次调用可能要等很久才暴露端点问题。
- 当前规避：执行后必须读取实际 run 的 `complete_count/truncated_count/failed_count`，不能把预检 ready 当作模型健康证明。
- 建议修复：将 `ready_to_execute` 改名为 `ready_for_confirmed_execution`，或增加 `provider_health_required` 配置；对本地 provider 提供可选的低成本 smoke test。

### VKP-005：本地 VLM 长响应容易被判定为截断，且耗时明显

- 现象：47 帧批次在 `max_tokens=700` 下仅 1 帧完整；随后 46 帧在 `max_tokens=1800` 下完成 42 帧；剩余 4 帧在 2400 和 5000 上限下仍全部截断。4 帧高上限重试耗时约数分钟。
- 影响：大批量执行容易产生大量失败记录；重试会显著占用本地模型和 CPU/内存，操作者可能误把“进程仍在运行”当成卡死。
- 当前规避：分批执行；先用中等上限，失败帧单独重试；对截断结果保持 fail-closed，不导入确定性视觉证据。
- 建议修复：
  - 增加结构化 JSON 输出约束和更短的视觉 prompt；
  - 将“响应截断”和“模型请求失败”分开计数；
  - 支持按帧设置超时、指数退避和单帧断点续跑；
  - 在终端实时输出批次进度和当前 index；
  - 在结果中保存 `finish_reason`、响应长度和截断原因。

### VKP-006：顶层 `status=ok` 不代表批次没有失败

- 现象：多次执行结果顶层为 `status: ok`，但同时包含 `complete_count=0`、`truncated_count=4`、`failed_count=4`。
- 影响：脚本或人工只检查顶层状态时，会把失败批次误认为成功。
- 当前规避：必须同时检查 `complete_count`、`truncated_count`、`failed_count` 和 `updated`；以 `complete_count` 作为实际写回成功数。
- 建议修复：增加 `status=partial_failure`/`status=failed` 语义；只有 `failed_count=0 && truncated_count=0` 时才允许顶层 `ok`。

### VKP-007：VLM 运行日志、导出统计与验收统计存在 1 项数量差异

- 现象：运行日志批次完整结果累加为 62；`export-knowledge-note` 报告 `items_with_visual_understanding=61`；`acceptance-check` 报告 `semantic_missing=613`，即按 674 项总数只承认 61 项。
- 影响：无法仅凭一个报告判断到底有多少视觉证据进入导出；交接时容易造成“运行完成数”和“可消费证据数”混淆。
- 当前规避：把“运行成功数”和“导出纳入数”分开记录；最终交付以导出统计和验收统计为准，并保留运行日志供追溯。
- 建议修复：导出与验收统一复用同一 `is_complete_visual_evidence()` 判定函数；在报告中同时列出 `run_complete_count`、`timeline_complete_count`、`export_consumable_count` 及差异 index。

### VKP-008：导出命令返回 `exported`，但 coverage 仍为 blocked

- 现象：`export-knowledge-note` 返回 `status=exported`，但 summary 中 `coverage_status=blocked`；智能总结文件实际是带 `review-required` 水印的机器草稿。
- 影响：调用方容易把“文件已写出”误解为“内容已通过生产质量门”。
- 当前规避：导出后立即读取 `export-summary.json` 和 `production-artifact-gate.json`；以 production gate 的 `formal_generation_allowed`/`artifact_state` 为准。
- 建议修复：把写盘状态和质量状态拆成明确字段，例如 `write_status=exported`、`quality_status=blocked`；顶层不再使用容易被误读的单一 `status=exported`。

### VKP-009：质量检查的相对 `--summary-path` 会解析到错误目录

- 现象：传入 `--summary-path "exports\\smart-summary.codex.md"` 时，检查器把路径解析为 `<project-root>\exports\smart-summary.codex.md`，而不是 `<bundle>\exports` 目录，结果显示文件不存在、时间覆盖为 0。
- 影响：会产生大量假性失败：`exists=false`、`summary_chars=0`、`time_coverage=false`、章节检查失败。
- 当前规避：始终传入 bundle 内智能总结的绝对路径。
- 建议修复：相对路径统一以 `bundle_dir` 为基准解析；报告中输出 `resolved_summary_path`；若文件不存在，提示候选路径而非静默检查错误位置。

### VKP-010：阿拉伯数字章节序号被数字一致性检查误报

- 现象：将章节标题改为常用序号 `1` 至 `8` 后，`smart-summary-quality-check` 将章节编号 `8` 报为 `unsupported_numbers`，尽管它只是结构编号，不是事实数字。
- 影响：用户要求的常用序号与质量门的数字一致性检查发生冲突；摘要结构正确，但质量检查仍为 failed。
- 当前规避：保留阿拉伯数字序号，不为了通过检查改回甲乙丙丁或其他不常用序号；在交接中注明该项是结构编号误报。
- 建议修复：数字证据检查剥离 Markdown 标题中的枚举编号，或增加 `structural_number` 分类；仅对正文中的金额、比例、日期、数量和事实性数字执行证据核对。

### VKP-011：视觉证据更新后必须显式重导出和重跑门禁

- 现象：VLM 写回 Timeline 后，已有的 `smart-summary.codex.md` 不会自动绑定最新视觉证据；必须手动修改/刷新总结，再执行 `export-knowledge-note`、质量检查、production gate 和 acceptance check。
- 影响：如果只执行 VLM 而不重导出，最终文件、运行日志和 Timeline 时间可能不一致。
- 当前规避：固定顺序：VLM 执行 → `timeline-alignment-audit` → 更新总结证据边界 → `export-knowledge-note` → `smart-summary-quality-check` → `production-artifact-gate` → `acceptance-check --no-refresh`。
- 建议修复：为视觉写回增加“证据版本/哈希”并让导出 freshness gate 自动检测；视觉更新后自动标记旧总结 stale。

### VKP-012：验收报告把全量待复核项与视觉缺失项混在一起，阅读成本高

- 现象：本次 `acceptance-check` 报告 `review_targets_open=674`，同时 `semantic_missing=613`；前者是全量 Timeline 复核状态，后者是视觉理解缺失，二者不是同一维度。
- 影响：用户容易误解为 674 帧都没有视觉分析，或者把 613 个缺失项当成 613 个模型调用失败。
- 当前规避：交付说明同时给出“总 Timeline 项、可消费视觉项、视觉缺失项、实际重试失败 index”。
- 建议修复：验收报告按 `transcript_review_targets`、`ocr_review_targets`、`semantic_visual_missing`、`temporal_visual_missing` 分组，并提供去重后的 review queue。

### VKP-013：长批次本地执行的进度反馈不足

- 现象：调用期间终端长时间只有 Python/jieba 警告，没有当前 index、完成数或预计剩余时间；本次 4 帧高上限重试期间持续数分钟无进度输出。
- 影响：操作者无法区分模型推理慢、端点无响应、子进程堆积或真实卡死。
- 当前规避：用独立终端轮询运行会话，完成后读取 run log；不在无证据时强制杀进程。
- 建议修复：增加进度文件或 stdout heartbeat；记录 `started_at`、`completed_at`、当前 index、重试次数和每帧耗时；批次超时后自动写出可恢复状态。

## 推荐的稳定操作顺序

```powershell
# 1. 使用稳定 wrapper，不直接从仓库根目录调用 Python module
& ".\\scripts\\video-knowledge.ps1" vision-execution-preflight "<bundle>" `
  --semantic-indexes "306,313,363,370" --semantic-limit 4 --no-temporal `
  --provider-config "<vision-local-config.json>"

# 2. 只复制 preflight 返回的确认值，并显式指定本地 provider
& ".\\scripts\\video-knowledge.ps1" run-multimodal-frame-analysis "<bundle>" `
  --execute --limit 4 --indexes "306,313,363,370" `
  --confirm-vision-calls 4 `
  --confirm-vision-indexes "306,313,363,370" `
  --provider-config "<vision-local-config.json>" `
  --execution-actor operator --max-tokens 1800

# 3. 失败批次必须按 counters 判断，不看顶层 status
# 4. VLM 写回后按固定顺序重导出、重跑质量门禁和 acceptance
```

## 本次交付状态

- `smart-summary.md`、`full-body.md`、`full-transcript.md` 已刷新。
- `timeline-alignment-audit.json`：674 项，0 个对齐问题。
- `production-artifact-gate.json`：`blocked_review_required`，阻断原因是 `transcript_quality:failed`。
- `acceptance-check.json`：`incomplete`，`human_review_ready`，未伪造“生产完成”。
- 4 个疑难帧仍是截断待复核：306、313、363、370。

## 交接给原线程时必须带上的文件

1. 本文档：`video-knowledge-pipeline/docs/evaluations/2026-08-22-local-vlm-arbitration-tool-issues.md`
2. 运行审计：`<bundle>\vision-analysis-runs.jsonl` 与 `vision-analysis-runs.md`
3. 预检：`<bundle>\vision-execution-preflight.json` 与 `vision-execution-preflight.md`
4. 导出统计：`<bundle>\exports\export-summary.json`
5. 质量门禁：`<bundle>\exports\smart-summary-quality.json`、`<bundle>\production-artifact-gate.json`（前者在 exports，后者在 bundle 根目录）
6. 最终验收：`<bundle>\acceptance-check.json` 与 `acceptance-check.md`

## 后续修复优先级

1. P0：修复 `status=ok`/`exported` 与内部失败或 blocked 状态的语义冲突。
2. P0：统一运行日志、Timeline、导出和验收的视觉完成数判定。
3. P1：修复质量检查相对路径解析和结构序号数字误报。
4. P1：补强长批次进度、超时、断点续跑和截断原因记录。
5. P2：优化预检报告的本地 provider 与远程 gateway 状态分层。

## 2026-08-22 14:03:00 | Codex (GPT-5.6 Sol)

- Action: changed VKP default summary numbering to Arabic hierarchical numbering and fixed the adjacent CLI syntax regression.
- Files: `src/video_knowledge_pipeline/smart_summary_codex.py`; `src/video_knowledge_pipeline/smart_summary_global_reduce.py`; `src/video_knowledge_pipeline/smart_summary_section_apply.py`; `src/video_knowledge_pipeline/cli.py`; `tests/test_smart_summary_numbering.py`
- Summary: default main sections now use `1`, `2`, `3`; child entries use structures such as `4.1.1` and `4.1.2`; quality checks recognize numbered headings and exclude structural heading numbers from factual-number evidence checks. The existing repeatable `--index` CLI change had an invalid list-unpacking expression, which was corrected to preserve its intended merge behavior.
- Verification: numbering regression `5 passed`; section normalization `2 passed`; `py_compile` and targeted Ruff checks passed. The managed section-apply suite remains blocked by the test runtime missing `rapidfuzz`; direct full section tests also encounter the repository's pre-existing protected output-directory ACL.

## 2026-08-22 | Codex 修复关闭矩阵

本节只关闭工具代码与离线契约问题，不改写本文记录的真实执行事实。独立实施回执见 `docs/evaluations/2026-08-22-local-vlm-arbitration-tool-fixes.md`。

| 问题 | 代码/契约状态 | 关键结果 |
| --- | --- | --- |
| VKP-001 | 已修复 | README 使用稳定 wrapper；开发态直接 module 的安装/PYTHONPATH 前提已写明。 |
| VKP-002 | 已修复 | 视觉执行与预检支持可重复 `--index`，并与 CSV 输入去重合并。 |
| VKP-003 | 已修复 | 预检区分 effective provider、未使用路由和已禁用远程 fallback。 |
| VKP-004 | 已修复 | 配置/确认 ready 与 provider health verified 分开报告。 |
| VKP-005 | 已修复 | 保存 finish reason、完整/截断/失败 indexes、耗时、重试和 progress。 |
| VKP-006 | 已修复 | 任一截断或失败时顶层不得返回 `ok`。 |
| VKP-007 | 已修复 | 运行事件、唯一 Timeline 证据、可导出证据分别计数并报告差集。 |
| VKP-008 | 已修复 | `write_status` 与 `quality_status/quality_ready` 分离。 |
| VKP-009 | 已修复 | 相对 summary 路径以 bundle 目录解析，并记录请求/解析路径。 |
| VKP-010 | 已修复 | 结构序号单列为 structural numbers，不参与事实数字误报。 |
| VKP-011 | 已修复 | 视觉写回将旧导出标记 stale，并提供显式恢复命令；不会冒充自动刷新成功。 |
| VKP-012 | 已修复 | 验收队列按 transcript/OCR/semantic/temporal 分组并给出去重样本。 |
| VKP-013 | 已修复 | 单帧与时序批次均写 progress JSON，并在真实执行时输出 heartbeat。 |

分级连续帧方案也已实现：连续 RAM++ 标签经漏标/抖动平滑后形成稳定、出现、消失标签，并与 OCR、镜头/画面变化和 ASR 动作词联合仲裁。静态片段只能形成粗描述；动态、复杂或歧义片段进入 `temporal_multimodal_escalation`。标签结果绝不写成 `temporal_visual_understanding`，因此不会冒充连续多帧多模态理解。

离线相关回归最终为 `153 passed, 8 warnings`。原真实 bundle 的 306、313、363、370 仍保留旧截断状态；本轮未读取真实媒体、未调用模型或 provider，也未重跑真实导出与质量门。
