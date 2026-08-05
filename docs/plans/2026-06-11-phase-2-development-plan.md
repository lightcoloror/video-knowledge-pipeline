# Phase 2 Development Plan: From Pipeline Pieces to Repeatable Video Knowledge Runs

## Update Record

- 2026-06-11 10:35:00 | Codex (GPT-5) | Created the next-stage development plan from the current real bundle coverage and implementation state.

## Current Position

The project has passed the proof-of-pipeline stage. The current real bundle already has:

| Capability | State |
|---|---|
| ASR / speech timeline | usable |
| key frames | usable |
| visual route | usable |
| source artifact tracking | usable |
| MCP / CLI entrypoints | partially usable |
| WebUI review bundle | usable for inspection |
| ebook screenshot parsing | integrated but not fully proven on real candidates |
| semantic frame vision | provider path exists, only small imported/preview coverage |
| temporal sequence vision | frame group path exists, only small imported/preview coverage |
| hierarchical Markdown export | exists, but not yet good enough as the main human deliverable |
| human review/tag round trip | not yet complete |

Reference bundle:

```text
%WORKSPACE_ROOT%\video-knowledge-pipeline\real-tests\feishu-video-retry-live-asr\webui-bundle
```

Latest known coverage snapshot:

| Channel | Current blocker |
|---|---:|
| screen_text | 9 |
| structured_visual | 9 |
| semantic_frame_understanding | 60 |
| temporal_visual_understanding | 11 |

Phase 2 should not add another extractor first. It should make the current architecture run repeatably on one real video and produce a human-readable knowledge note.

## Phase 2 Goal

Turn the current project into a repeatable local tool that can process a knowledge video into:

1. full transcript,
2. structured screen text / tables / formulas / code when present,
3. multimodal visual understanding for non-text frames,
4. temporal event understanding for changing scenes,
5. coverage and gap audit,
6. human review package,
7. hierarchical Markdown knowledge note.

The final output should be understandable without opening raw `timeline.json`.

## Non-Goals

- Do not merge `ebook_markdown_pipeline`, `video-download-orchestrator`, Peepshow, or model repos into this repository.
- Do not build a new OCR engine.
- Do not build a new ASR engine.
- Do not rely on a single commercial API as the only execution path.
- Do not hide missing data behind polished summaries.
- Do not write API keys into docs, manifests, reports, tests, or generated bundles.

## Development Priority

### Priority 0: Keep Current Worktree Stable

Before further feature work:

```powershell
python -m pytest -q
```

Then refresh current real bundle status:

```powershell
.\scripts\video-knowledge.ps1 audit-knowledge-coverage %WORKSPACE_ROOT%\video-knowledge-pipeline\real-tests\feishu-video-retry-live-asr\webui-bundle
.\scripts\video-knowledge.ps1 bundle-status-report %WORKSPACE_ROOT%\video-knowledge-pipeline\real-tests\feishu-video-retry-live-asr\webui-bundle
```

Acceptance:

- tests pass,
- coverage report is regenerated,
- no API key appears in any generated report.

### Priority 1: Prove Document-Visual Screenshot Parsing on Real Frames

Purpose:

Close `screen_text` and `structured_visual` for the 9 document-like candidates.

Implementation tasks:

- Add small-batch selection to `run_visual_structure_plan`:
  - `indexes`
  - `limit`
  - report selected candidates explicitly
- Harden ebook result import:
  - accept `markdown`, `output`, `report`, `artifact`, `text`, `content`
  - read file references only under the requested output directory
  - never mark a missing artifact as success
- Execute a 1-2 frame smoke run first, then expand to all 9 document candidates.
- Preserve evidence paths:
  - original frame path
  - ebook output directory
  - imported artifact path

Commands:

```powershell
.\scripts\video-knowledge.ps1 run-visual-structure %WORKSPACE_ROOT%\video-knowledge-pipeline\real-tests\feishu-video-retry-live-asr\webui-bundle --indexes "16,17"
.\scripts\video-knowledge.ps1 run-visual-structure %WORKSPACE_ROOT%\video-knowledge-pipeline\real-tests\feishu-video-retry-live-asr\webui-bundle --execute-ebook-pipeline --indexes "16,17" --timeout-seconds 120
```

Acceptance:

- at least 2 real document-like frames get `visual_text` or `structured_visual`,
- failed frames record concrete blocker reasons,
- coverage report no longer reports those frames as silently missing.

### Priority 2: Prove Real Multimodal Single-Frame Understanding

Purpose:

Close the largest blocker: `semantic_frame_understanding`.

Implementation tasks:

- Use provider preflight before every real call.
- Prefer currently configured provider if available; otherwise use a provider profile explicitly passed through CLI/MCP.
- Execute only confirmed batches:
  - first 1 frame,
  - then 10 frames,
  - then the remaining high-value semantic frames.
- The report must show:
  - timeline index,
  - time range,
  - frame path,
  - transcript excerpt,
  - model status,
  - extracted non-text visual information,
  - keep screenshot reason,
  - confidence,
  - validation issues.

Commands:

```powershell
.\scripts\video-knowledge.ps1 vision-env-status
.\scripts\video-knowledge.ps1 vision-execution-preflight %WORKSPACE_ROOT%\video-knowledge-pipeline\real-tests\feishu-video-retry-live-asr\webui-bundle --semantic-limit 1 --no-temporal
.\scripts\video-knowledge.ps1 run-multimodal-frame-analysis %WORKSPACE_ROOT%\video-knowledge-pipeline\real-tests\feishu-video-retry-live-asr\webui-bundle --execute --limit 1 --confirm-vision-calls <calls> --confirm-vision-indexes "<indexes>"
```

Acceptance:

- at least 10 `semantic_frame` items have `visual_understanding`,
- every item has evidence frame paths,
- model output parse failures are retained as raw output plus `model_output_parse_failed`, not dropped.

### Priority 3: Prove Temporal Understanding with Real Frame Groups

Purpose:

Handle操作过程、界面状态变化、演示变化，而不是把视频当成孤立截图。

Implementation tasks:

- Ensure `run_temporal_frame_groups` can generate 5-12 ordered frames per selected timeline item.
- Ensure `run_temporal_visual_analysis` preserves ordered frame paths in the output.
- Report should compare:
  - transcript,
  - first/middle/last frame,
  - event sequence,
  - state changes,
  - operation steps,
  - possible missing points.
- Run 1 temporal group first, then 3 groups.

Commands:

```powershell
.\scripts\video-knowledge.ps1 run-temporal-frame-groups %WORKSPACE_ROOT%\video-knowledge-pipeline\real-tests\feishu-video-retry-live-asr\webui-bundle --execute --frame-count 8 --limit 1
.\scripts\video-knowledge.ps1 vision-execution-preflight %WORKSPACE_ROOT%\video-knowledge-pipeline\real-tests\feishu-video-retry-live-asr\webui-bundle --no-semantic --temporal-limit 1 --frame-count 8
.\scripts\video-knowledge.ps1 run-temporal-visual-analysis %WORKSPACE_ROOT%\video-knowledge-pipeline\real-tests\feishu-video-retry-live-asr\webui-bundle --execute --limit 1 --frame-count 8 --confirm-vision-calls <calls> --confirm-vision-indexes "<indexes>"
```

Acceptance:

- at least 3 timeline items have `temporal_visual_understanding`,
- each temporal output references 5-12 ordered frames,
- export shows operation / event changes separately from ordinary transcript.

### Priority 4: Make Markdown Export the Primary Human Artifact

Purpose:

The user should be able to read `knowledge-note.md` as the main deliverable.

Implementation tasks:

- Enforce required sections:
  - `# <title>`
  - `## 视频概要`
  - `## 覆盖情况`
  - `## 知识结构`
  - `## 图文与视觉信息`
  - `## 连续演示与操作变化`
  - `## 逐字稿与演示记录`
  - `## 未解决缺口`
- Add chapter grouping:
  - by transcript continuity,
  - by route changes,
  - by topic shifts if available.
- Each chapter must include:
  - `说了什么`
  - `演示了什么`
  - `屏幕/图表信息`
  - `证据`
  - `缺口`
- Keep `full-transcript.md` complete and chronological.

Commands:

```powershell
.\scripts\video-knowledge.ps1 export-knowledge-note %WORKSPACE_ROOT%\video-knowledge-pipeline\real-tests\feishu-video-retry-live-asr\webui-bundle --title "feishu-video-retry"
```

Acceptance:

- `exports/knowledge-note.md` can be read as a layered Markdown document,
- `exports/full-transcript.md` preserves the full transcript,
- unresolved gaps are visible instead of silently omitted.

### Priority 5: Add Human Review Round Trip

Purpose:

Quality筛选和人工标注必须进入机器可读流程，而不是只存在于聊天或临时判断里。

Implementation tasks:

- Implement or finish `review-notes.json` schema:
  - `timeline_index`
  - `status`
  - `tags`
  - `comment`
  - `corrected_transcript`
  - `corrected_visual_text`
  - `corrected_visual_understanding`
  - `reviewed_at`
- Merge review notes into:
  - coverage audit,
  - bundle readiness,
  - Markdown export.
- WebUI first version can be JSON import/export plus visible command links; full interactive editing can wait.

Acceptance:

- a human can mark a missing model result as `needs_human_review` or `accepted`,
- review state appears in coverage and export,
- model output is never destructively overwritten.

### Priority 6: One-Step Orchestration

Purpose:

Codex / OpenClaw / MCP agents should not reconstruct command sequences by hand.

Implementation tasks:

- Improve `bundle-next-action`:
  - choose visual structure before semantic vision when document candidates are blocking,
  - recommend temporal frame group generation before temporal analysis,
  - expose exact MCP/CLI args.
- Improve `bundle-advance`:
  - preview by default,
  - execute only when `--execute` and confirmations are present,
  - stop with explicit blocker reasons.
- Add an acceptance runner that executes safe preview steps and writes a run report.

Acceptance:

- `bundle-advance-queue --max-steps 4` can move through safe preview steps without manual command reconstruction,
- real API calls still require confirmation,
- generated reports are enough for another agent to continue.

## Implementation Order

1. Finish small-batch `run_visual_structure_plan` and real ebook smoke.
2. Run real multimodal single-frame batch.
3. Run real temporal frame-group batch.
4. Improve Markdown export format and tests.
5. Add review note round trip.
6. Strengthen `bundle-next-action` / `bundle-advance`.
7. Re-run full acceptance on the real bundle.

## Test Plan

Always run after source changes:

```powershell
python -m pytest -q
```

Focused tests to add or strengthen:

| Area | Test |
|---|---|
| visual structure | `indexes` / `limit` select exact document candidates |
| visual structure | ebook artifact variants normalize into `visual_text` / `structured_visual` |
| multimodal | provider config never leaks API key |
| multimodal | parse failure preserves raw output and creates audit issue |
| temporal | generated frame groups are ordered and 5-12 frames |
| export | required Markdown headings exist |
| export | transcript and visual/temporal information appear in separate sections |
| review | review notes affect coverage without overwriting model output |
| orchestration | `bundle-next-action` recommends the next correct blocked channel |

## Real Acceptance Run

After implementation:

```powershell
python -m pytest -q
.\scripts\video-knowledge.ps1 audit-knowledge-coverage %WORKSPACE_ROOT%\video-knowledge-pipeline\real-tests\feishu-video-retry-live-asr\webui-bundle
.\scripts\video-knowledge.ps1 bundle-status-report %WORKSPACE_ROOT%\video-knowledge-pipeline\real-tests\feishu-video-retry-live-asr\webui-bundle
.\scripts\video-knowledge.ps1 export-knowledge-note %WORKSPACE_ROOT%\video-knowledge-pipeline\real-tests\feishu-video-retry-live-asr\webui-bundle --title "feishu-video-retry"
```

Target:

| Channel | Target |
|---|---:|
| screen_text blockers | 0, or explicit reviewed fallback |
| structured_visual blockers | 0, or explicit reviewed fallback |
| semantic_frame_understanding covered | >= 10 |
| temporal_visual_understanding covered | >= 3 |
| tests | pass |
| knowledge-note.md | human-readable layered Markdown |

## Stop Conditions

Pause and reassess if:

- `ebook_markdown_pipeline` cannot be called reliably through MCP or direct local adapter;
- configured vision providers fail connection tests repeatedly;
- real model cost or rate limit makes batch execution impractical;
- generated Markdown remains unreadable after structured export changes;
- implementation starts requiring deep vendor-code integration instead of routing/glue code.

## Immediate Next Task

Implement small-batch execution for `run_visual_structure_plan`:

1. add `indexes` and `limit` parameters,
2. expose them through CLI and MCP,
3. add tests,
4. run a 1-2 frame ebook smoke on the real bundle,
5. regenerate coverage and export.

This is the best next step because it reduces the highest-confidence deterministic blocker before spending API calls on semantic/temporal vision.
