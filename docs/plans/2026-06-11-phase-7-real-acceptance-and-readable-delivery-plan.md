# Phase 7 Real Acceptance and Readable Delivery Plan

> Created: 2026-06-11 16:40:00 | Codex (GPT-5)

## Goal

把当前真实视频 bundle 从“工具链基本闭环，但 provider 仍阻塞、最终文档还不够好读”推进到“能被人稳定使用、能被 agent 稳定调用、能给出可信验收结论”的状态。

本阶段不再扩大工具清单，不重写 ASR/OCR/多模态主流程。重点是四件事：

- 让验收状态准确反映真实进度：机器输出、人工审核模板、已导入审核结果、provider 健康状态要分开统计。
- 让最终 Markdown 变成人能直接阅读和复习的知识文档，而不是调试报告。
- 让 WebUI 成为实际审核入口：能看缺口、填审核、导入结果、复制 MCP/CLI 命令。
- 修复或切换多模态 provider 后，用最小真实样本验证单帧和连续帧理解，再决定是否批量执行。

## Current Baseline

Reference bundle:

```text
%WORKSPACE_ROOT%\video-knowledge-pipeline\real-tests\feishu-video-retry-live-asr\phase2-review-preview-bundle
```

Current verified artifacts:

| Artifact | State |
|---|---|
| `review-notes.template.json` | exists, 30 review rows |
| Review template statuses | 9 `keep_image`, 17 `corrected_visual_understanding`, 4 `corrected_temporal_visual_understanding` |
| `acceptance-check` | `provider_blocked` |
| `knowledge-coverage` | `blocked` |
| ASR | 68 / 68 covered |
| Frames | 68 / 68 covered |
| Visual route | 68 / 68 covered |
| Document visual | 9 / 9 resolved through evidence-preserving review path |
| Semantic visual | still blocked unless provider is fixed or human notes are imported |
| Temporal visual | still blocked unless provider is fixed or human notes are imported |
| Provider health | `provider_unreachable`, unsafe to execute |
| Export freshness | stale after review/coverage changes |

Important interpretation:

- The project should not claim completion yet.
- The current system has a usable fallback mechanism: review templates can close visual gaps without inventing fake machine output.
- The next useful product milestone is not “more tools”; it is a truthful acceptance loop plus a readable knowledge-note export.

## Non-Goals

- Do not vendor or merge external OCR/ASR/VLM repositories.
- Do not store API keys in docs, manifests, reports, args, tests, or WebUI bundles.
- Do not bypass `ebook_markdown_pipeline` for图文截图解析.
- Do not treat provider-blocked machine vision as successful coverage.
- Do not make Peepshow, BiliNote, or any single external project the main knowledge generator.
- Do not write back to Logseq/Obsidian automatically; keep writeback behind explicit human review.

## Phase 7.1: Make Acceptance State Precise

### Problem

Current reports can show useful but confusing states:

- `review-notes.template.json` exists, but template preparation is not the same as imported review acceptance.
- `knowledge-coverage.md` still reports machine semantic/temporal gaps, which is correct, but it does not clearly separate human-resolvable gaps from provider-blocked gaps.
- `acceptance-check.md` can become stale after review template or export regeneration.

### Tasks

1. Add explicit review lifecycle fields:

```json
{
  "review_template_prepared": true,
  "review_notes_imported": false,
  "review_targets_open": 30,
  "review_targets_total": 48,
  "review_resolution_mode": "provider_or_human_review"
}
```

2. Update `acceptance-check` to distinguish:

| State | Meaning |
|---|---|
| `provider_blocked` | machine vision cannot safely execute |
| `human_review_ready` | a fillable template exists and can resolve known gaps |
| `human_review_imported` | review notes have been imported and counted |
| `export_stale` | knowledge note needs regeneration |
| `accepted_with_known_gaps` | human explicitly accepted retained-image or known-gap decisions |

3. Add a refresh command sequence that is safe to run repeatedly:

```powershell
.\scripts\video-knowledge.ps1 audit-knowledge-coverage <bundle>
.\scripts\video-knowledge.ps1 acceptance-check <bundle>
.\scripts\video-knowledge.ps1 bundle-status-report <bundle>
```

4. Ensure generated reports include:

- report timestamp;
- source file freshness;
- whether review notes are only a template or already imported;
- provider profile name without secret values;
- exact next command.

### Files

- `src/video_knowledge_pipeline/acceptance_check.py`
- `src/video_knowledge_pipeline/knowledge_coverage.py`
- `src/video_knowledge_pipeline/bundle_status.py`
- `src/video_knowledge_pipeline/review_session.py`
- `tests/test_video_pipeline_smoke.py`

### Acceptance Criteria

- Real bundle status says either `provider_blocked + human_review_ready` or `human_review_required`, not a vague blocked state.
- No report claims machine semantic/temporal coverage when only a template exists.
- Tests cover stale export, template-only review, imported review notes, and provider-blocked states.

## Phase 7.2: Upgrade Human-Readable Markdown Output

### Target Output

The project should generate at least three human-facing files:

| File | Purpose |
|---|---|
| `knowledge-note.md` | 层级化知识笔记，适合阅读、复习、导入 Obsidian |
| `full-transcript.md` | 逐字稿 + 同时间段画面/演示记录 |
| `extraction-audit.md` | 覆盖率、缺口、证据路径、人工审核状态 |

### `knowledge-note.md` Structure

```markdown
# 视频知识笔记

## 1. 视频概要

## 2. 核心主题与论证结构

## 3. 分段知识整理

### 3.1 00:00:00-00:03:20 主题标题

#### 讲了什么

#### 画面/演示了什么

#### 屏幕文字、图表、公式、代码

#### 需要保留的图片证据

#### 可复习要点

## 4. 表格、公式、代码和图示索引

## 5. 仍需人工复核的地方

## 6. 证据与来源
```

### `full-transcript.md` Structure

```markdown
# 逐字稿与演示记录

| 时间 | 说了什么 | 画面/操作/演示 | 证据帧 | 状态 |
|---|---|---|---|---|
```

### Tasks

1. Split current export logic into:

- semantic outline generation;
- transcript table generation;
- evidence index generation;
- audit appendix generation.

2. Add export quality checks:

- heading hierarchy exists;
- transcript coverage equals timeline count;
- every retained image has an evidence path;
- every unresolved visual gap appears in the review section;
- no OCR wrapper-only text is treated as content.

3. Add CLI/MCP entry:

```powershell
.\scripts\video-knowledge.ps1 export-readable-notes <bundle>
```

MCP:

```text
export_readable_notes(bundle_dir, include_audit=true)
```

4. Keep old export command compatible, but make it call the new readable export path internally.

### Files

- `src/video_knowledge_pipeline/knowledge_note_export.py`
- `src/video_knowledge_pipeline/cli.py`
- `src/video_knowledge_pipeline/mcp_server.py`
- `tests/test_video_pipeline_smoke.py`

### Acceptance Criteria

- `knowledge-note.md` is readable without opening JSON.
- `full-transcript.md` includes both speech and visual/operation records.
- `extraction-audit.md` makes unresolved gaps explicit.
- Real bundle export is fresh after running the command.

## Phase 7.3: Make WebUI a Real Review Surface

### Tasks

1. Add WebUI sections:

| Section | Function |
|---|---|
| Acceptance | show current state, blockers, next command |
| Review Template | link/copy path for `review-notes.template.json` |
| Visual Gaps | semantic, temporal, OCR-empty grouped tabs |
| Provider Health | latest smoke/preflight state |
| Exports | open `knowledge-note.md`, `full-transcript.md`, `extraction-audit.md` |

2. Add copyable commands:

- `prepare-review-session`
- `apply-review-notes`
- `vision-provider-smoke`
- `vision-execution-preflight`
- `run-multimodal-frame-analysis`
- `run-temporal-visual-analysis`
- `export-readable-notes`

3. Avoid implementing an overbuilt editor first. The first useful version can be:

- view target rows;
- open evidence frame;
- copy timeline index;
- download/fill JSON template;
- import JSON through CLI/MCP.

### Files

- `src/video_knowledge_pipeline/webui_bridge.py`
- WebUI generation assets under current bundle builder
- `tests/test_video_pipeline_smoke.py`

### Acceptance Criteria

- Opening `review.html` shows the same next action as `bundle-status.md`.
- User can find the review template path from the page.
- User can find final readable exports from the page.
- No API key or secret-bearing environment variable is rendered.

## Phase 7.4: Provider Recovery and Minimal Real Vision Test

### Tasks

1. Keep provider config environment-only:

| Provider | Env |
|---|---|
| Agnes | `AGNES_API_KEY`, optional base URL/model env |
| OpenAI-compatible | `OPENAI_API_KEY` or custom key env |
| Gemini | `GEMINI_API_KEY` |

2. Run smoke in this order:

```powershell
.\scripts\video-knowledge.ps1 vision-provider-smoke <bundle> --provider agnes --timeout-seconds 15
.\scripts\video-knowledge.ps1 vision-provider-smoke <bundle> --provider gemini --timeout-seconds 15
.\scripts\video-knowledge.ps1 vision-provider-smoke <bundle> --provider openai --timeout-seconds 15
```

3. Once one provider is healthy, run only minimal writes:

```powershell
.\scripts\video-knowledge.ps1 run-multimodal-frame-analysis <bundle> --execute --limit 1 --check-provider
.\scripts\video-knowledge.ps1 run-temporal-visual-analysis <bundle> --execute --limit 1 --frame-count 8 --check-provider
```

4. Compare output quality before batch execution:

- Does it describe non-text visual information?
- Does it keep evidence paths?
- Does it return parseable JSON?
- Does it avoid hallucinating content not visible in frame/transcript?
- Does it help the final Markdown become more complete?

### Acceptance Criteria

- At least one provider has a passing smoke report, or the project clearly reports provider recovery failure.
- At least one semantic frame and one temporal frame group are tested before batch mode.
- Failed provider calls never write partial fake understanding into timeline.

## Phase 7.5: Batch Closure Strategy

After Phase 7.4, choose exactly one closure path for the real bundle.

### Path A: Provider Works

Run controlled batches:

```powershell
.\scripts\video-knowledge.ps1 run-multimodal-frame-analysis <bundle> --execute --limit 10 --check-provider
.\scripts\video-knowledge.ps1 run-temporal-visual-analysis <bundle> --execute --limit 5 --frame-count 8 --check-provider
.\scripts\video-knowledge.ps1 audit-knowledge-coverage <bundle>
.\scripts\video-knowledge.ps1 export-readable-notes <bundle>
.\scripts\video-knowledge.ps1 acceptance-check <bundle>
```

Stop when:

- coverage is complete, or
- remaining gaps are low-value and explicitly reviewed, or
- provider quality is too poor for batch mode.

### Path B: Provider Still Blocked

Use the review template:

```powershell
.\scripts\video-knowledge.ps1 prepare-review-session <bundle>
.\scripts\video-knowledge.ps1 apply-review-notes <bundle> --review-json <filled-review-notes.json>
.\scripts\video-knowledge.ps1 audit-knowledge-coverage <bundle>
.\scripts\video-knowledge.ps1 export-readable-notes <bundle>
.\scripts\video-knowledge.ps1 acceptance-check <bundle>
```

Stop when:

- all high-risk visual gaps are human-reviewed;
- retained-image decisions have evidence paths;
- final export clearly marks known gaps.

## Phase 7.6: Regression and Safety

### Required Checks

```powershell
python -m pytest -q
rg -n -e "sk-" -e "AGNES_API_KEY=" -e "OPENAI_API_KEY=" -e "GEMINI_API_KEY=" src tests docs real-tests
```

### Manual Verification

Open:

```text
%WORKSPACE_ROOT%\video-knowledge-pipeline\real-tests\feishu-video-retry-live-asr\phase2-review-preview-bundle\review.html
```

Verify:

- acceptance state is visible;
- review template path is visible;
- readable exports are linked;
- visual evidence frame paths are visible;
- no secret appears.

## Final Acceptance for Phase 7

Phase 7 is done only when the real bundle reaches one of these states:

| Final State | Acceptable? | Meaning |
|---|---|---|
| `complete` | yes | machine and human coverage are complete |
| `accepted_with_known_gaps` | yes | all remaining gaps are explicitly reviewed and evidence-preserving |
| `provider_blocked + human_review_ready` | partial | usable, but still needs either human review import or provider repair |
| `provider_blocked` only | no | still too hard for a human/operator to close |
| `incomplete` | no | missing base evidence such as ASR, frames, routes, or exports |

The immediate target should be:

```text
provider_blocked + human_review_ready + fresh readable export
```

That is the first practical milestone where the tool is useful even before provider recovery is solved.
