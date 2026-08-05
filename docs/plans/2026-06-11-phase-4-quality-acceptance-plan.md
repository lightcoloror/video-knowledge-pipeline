# Phase 4 Quality Acceptance Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Turn the current video knowledge pipeline from "workflow can run" into "coverage counts are truthful, generated Markdown is useful, and one real video can be accepted or blocked with concrete next actions."

**Architecture:** Keep this project as the orchestration layer. Specialist tools stay outside: `ebook_markdown_pipeline` handles document-like screenshots, ASR tools handle transcript generation, and vision providers handle semantic/temporal understanding. Phase 4 adds stricter quality gates around imported evidence, stronger acceptance reports, and better human-readable export structure.

**Tech Stack:** Python package `video_knowledge_pipeline`, pytest, static WebUI bundle artifacts, MCP-compatible CLI bridge, external `ebook_markdown_pipeline`, local bundle fixture `real-tests/feishu-video-retry-live-asr/webui-bundle`.

---

## Update Record

- 2026-06-11 23:55:00 | Codex (GPT-5) | Created Phase 4 plan after Phase 3 revealed that OCR import can count synthetic wrapper Markdown as real visual coverage.

## Current Baseline

Reference bundle:

```text
%WORKSPACE_ROOT%\video-knowledge-pipeline\real-tests\feishu-video-retry-live-asr\webui-bundle
```

Current coverage snapshot:

| Channel | Covered | Blocker | Assessment |
|---|---:|---:|---|
| speech | 68 / 68 | 0 | usable |
| visual_frames | 68 / 68 | 0 | usable |
| visual_route | 68 / 68 | 0 | usable |
| screen_text | 9 / 68 | 0 | weak and likely over-counted |
| structured_visual | 9 / 9 | 0 | likely false-positive coverage |
| semantic_frame_understanding | 10 / 61 | 51 | real remaining blocker |
| temporal_visual_understanding | 3 / 12 | 9 | real remaining blocker |
| source_artifacts | 1 / 1 | 0 | usable |
| time_axis | 100 / 100 | 0 | usable |

Important finding:

The 9 OCR/imported `document_visual` items currently have `visual_text` like:

```markdown
# 016_0000240000ms

<!-- source: D:\...\016_0000240000ms.jpg -->
```

That is not real screen-text extraction. Phase 4 must fix this before treating OCR coverage as done. A clean-looking coverage report is worse than an honest blocked report here.

## Phase 4 Goal

Make acceptance meaningful:

1. OCR/document visual coverage only counts if the imported Markdown contains real extracted content, not wrapper headings or source comments.
2. The bundle status can distinguish:
   - machine action still available,
   - external tool produced empty evidence,
   - model/API action needed,
   - human review needed,
   - accepted with known gaps.
3. `knowledge-note.md` reads as a layered Markdown lecture note, not a timeline dump.
4. `bundle-next-action`, CLI, MCP args, and WebUI point to the same next step.
5. Tests and one real-bundle smoke run verify the new acceptance rules.

## Non-Goals

- Do not build a new OCR engine.
- Do not vendor `ebook_markdown_pipeline`.
- Do not hide empty OCR behind `structured_visual`.
- Do not require full video upload to a model.
- Do not make human review overwrite machine evidence.
- Do not store API keys in manifests, docs, reports, or tests.

## Task 1: Reject Synthetic OCR Wrapper Output

**Files:**

- Modify: `src/video_knowledge_pipeline/visual_structure.py`
- Modify: `src/video_knowledge_pipeline/knowledge_coverage.py`
- Modify: `tests/test_video_pipeline_smoke.py`

**Step 1: Write failing tests**

Add a test where `ebook_markdown_pipeline` returns only:

```markdown
# 016_0000240000ms

<!-- source: D:\path\016_0000240000ms.jpg -->
```

Expected behavior:

- no `visual_text` import,
- no `structured_visual` import,
- result marked with blocker `ocr_text_empty`,
- coverage does not count that item as `screen_text` or `structured_visual`.

Run:

```powershell
python -m pytest tests/test_video_pipeline_smoke.py -q
```

Expected: fail before implementation.

**Step 2: Add meaningful Markdown filter**

Implement a helper in `visual_structure.py`:

```python
def _meaningful_ebook_markdown(markdown: str, image_path: str | None = None) -> str:
    ...
```

Rules:

- Strip blank lines.
- Strip exact synthetic source comments: `<!-- source: ... -->`.
- Strip the exact synthetic heading matching the image stem, for example `# 016_0000240000ms`.
- Preserve real headings such as `# 商业模式`, `## 现金流`, or table/code/formula Markdown.
- Return empty string if nothing meaningful remains.

**Step 3: Classify empty OCR output**

When the external tool succeeds but the meaningful text is empty:

- mark candidate result as `ok=false`,
- use `blocker="ocr_text_empty"`,
- write a report row explaining that OCR ran but found no real screen text,
- do not import fake `structured_visual`.

**Step 4: Update coverage**

Ensure `knowledge_coverage.py` only counts:

- `visual_text` with meaningful content, or
- `structured_visual` with meaningful text/table/code/formula content.

Synthetic wrapper-only values must not count.

**Step 5: Verify**

Run:

```powershell
python -m pytest -q
```

Expected: all tests pass.

**Suggested commit:**

```powershell
git add src/video_knowledge_pipeline/visual_structure.py src/video_knowledge_pipeline/knowledge_coverage.py tests/test_video_pipeline_smoke.py
git commit -m "fix: reject empty visual structure imports"
```

## Task 2: Re-audit the Real Bundle Without False Coverage

**Files:**

- Modify: generated real-bundle artifacts under `real-tests/feishu-video-retry-live-asr/webui-bundle`
- No source code changes unless Task 1 reveals missing status fields.

**Step 1: Rerun visual structure for the 9 document/mixed frames**

Run:

```powershell
$env:PYTHONPATH='src'
python -m video_knowledge_pipeline.cli run-visual-structure `
  %WORKSPACE_ROOT%\video-knowledge-pipeline\real-tests\feishu-video-retry-live-asr\webui-bundle `
  --execute-ebook-pipeline `
  --indexes "16,17,18,24,25,48,66,67,68" `
  --timeout-seconds 300
```

Expected:

- Real extracted OCR text is imported if present.
- Empty wrapper-only OCR becomes `ocr_text_empty`.

**Step 2: Rebuild coverage and status**

Run:

```powershell
.\scripts\video-knowledge.ps1 audit-knowledge-coverage %WORKSPACE_ROOT%\video-knowledge-pipeline\real-tests\feishu-video-retry-live-asr\webui-bundle
.\scripts\video-knowledge.ps1 bundle-status-report %WORKSPACE_ROOT%\video-knowledge-pipeline\real-tests\feishu-video-retry-live-asr\webui-bundle
```

Expected:

- `screen_text` and `structured_visual` counts drop if OCR was empty.
- Remaining document gaps are explicit blockers, not hidden successes.
- `bundle-next-action` chooses the next real action.

**Step 3: Inspect a concise sample**

Run:

```powershell
@'
import json
from pathlib import Path
bundle=Path(r"%WORKSPACE_ROOT%\video-knowledge-pipeline\real-tests\feishu-video-retry-live-asr\webui-bundle")
timeline=json.loads((bundle/"timeline.json").read_text(encoding="utf-8"))
for idx in [16,17,18,24,25,48,66,67,68]:
    item=next(x for x in timeline if x.get("index")==idx)
    print(idx, bool(item.get("visual_text")), len(item.get("structured_visual") or []), item.get("quality_issues"))
'@ | python -
```

Expected:

- Empty OCR frames remain visible as gaps or review-needed items.

## Task 3: Strengthen Bundle Next Action and Acceptance Status

**Files:**

- Modify: `src/video_knowledge_pipeline/bundle_readiness.py`
- Modify: `src/video_knowledge_pipeline/knowledge_coverage.py`
- Modify: `src/video_knowledge_pipeline/cli.py`
- Modify: `src/video_knowledge_pipeline/mcp_server.py`
- Test: `tests/test_video_pipeline_smoke.py`

**Step 1: Add tests for next-action priority**

Fixtures should cover:

- `ocr_text_empty` exists: recommend human review or multimodal fallback, not another blind OCR loop.
- temporal frame groups missing: recommend `run_temporal_frame_groups`.
- temporal groups exist but analysis missing: recommend `run_temporal_visual_analysis`.
- semantic gaps remain: recommend `run_multimodal_frame_analysis`.
- no machine action remains but `needs_human_review` exists: recommend review session.

**Step 2: Implement status categories**

Use explicit bundle states:

| State | Meaning |
|---|---|
| `machine_action_available` | A safe automatic next command exists |
| `vision_confirmation_required` | API call needs preflight confirmation |
| `external_tool_empty_output` | OCR/tool ran but extracted no useful content |
| `human_review_required` | Machine branch cannot confidently resolve gap |
| `accepted_with_known_gaps` | Human accepted remaining gaps |
| `complete` | No known coverage blockers |

**Step 3: Keep CLI/MCP/WebUI aligned**

All three surfaces should read the same next-action payload:

- `bundle-next-action`
- generated `mcp-*.args.json`
- WebUI review page command block

**Step 4: Verify**

Run:

```powershell
python -m pytest -q
.\scripts\video-knowledge.ps1 bundle-next-action %WORKSPACE_ROOT%\video-knowledge-pipeline\real-tests\feishu-video-retry-live-asr\webui-bundle
```

Expected:

- The next action is specific and not misleading.

## Task 4: Complete a Controlled Vision Batch

**Files:**

- Generated bundle artifacts:
  - `vision-execution-preflight.json/md`
  - `vision-analysis-runs.jsonl`
  - `timeline.json`
  - `knowledge-coverage.json`
  - `bundle-status-report.md`

**Step 1: Run preflight for a small semantic batch**

Run:

```powershell
.\scripts\video-knowledge.ps1 vision-execution-preflight `
  %WORKSPACE_ROOT%\video-knowledge-pipeline\real-tests\feishu-video-retry-live-asr\webui-bundle `
  --semantic-indexes "4,6,9,15,16" `
  --semantic-limit 0 `
  --no-temporal
```

Expected:

- Provider readiness is shown.
- Confirmation values are emitted.
- No API key appears in the report.

**Step 2: Execute only after confirmation**

Run the generated confirmed command from the preflight report, or use:

```powershell
.\scripts\video-knowledge.ps1 run-multimodal-frame-analysis `
  %WORKSPACE_ROOT%\video-knowledge-pipeline\real-tests\feishu-video-retry-live-asr\webui-bundle `
  --execute `
  --indexes "4,6,9,15,16" `
  --limit 0 `
  --confirm-vision-calls <preflight_calls> `
  --confirm-vision-indexes "<preflight_indexes>"
```

Expected:

- Only selected indexes are updated.
- `vision-analysis-runs.jsonl` records the run.
- Restore-plan command is available.

**Step 3: Run a small temporal batch**

First ensure frame groups:

```powershell
.\scripts\video-knowledge.ps1 run-temporal-frame-groups `
  %WORKSPACE_ROOT%\video-knowledge-pipeline\real-tests\feishu-video-retry-live-asr\webui-bundle `
  --execute `
  --frame-count 8 `
  --indexes "18,21,25"
```

Then preflight and execute temporal analysis for those same indexes.

**Acceptance:**

- At least 5 additional `semantic_frame` items are filled.
- At least 3 temporal candidates have real 8-frame groups and analysis.
- Coverage improves and reports remain reversible.

## Task 5: Improve `knowledge-note.md` Structure

**Files:**

- Modify: `src/video_knowledge_pipeline/knowledge_note_export.py`
- Test: `tests/test_video_pipeline_smoke.py`
- Generated: `exports/knowledge-note.md`
- Generated: `exports/full-transcript.md`

**Step 1: Add export tests**

Expected sections:

- `# <title>`
- `## 视频概要`
- `## 章节化知识结构`
- `## 图文与视觉证据`
- `## 操作演示与状态变化`
- `## 逐字稿与演示记录`
- `## 未解决缺口`
- `## 证据索引`

**Step 2: Build chapter grouping**

Group timeline items into chapters using:

- transcript topic shifts,
- route clusters,
- time gaps,
- optional human review tags.

Keep implementation conservative. If no strong chapter signal exists, use fixed time windows with meaningful titles derived from transcript phrases.

**Step 3: Add chapter tables**

Each chapter should include:

| Column | Source |
|---|---|
| 时间段 | timeline start/end |
| 讲了什么 | transcript / corrected transcript |
| 画面显示 | visual_text / structured_visual / visual_understanding |
| 演示变化 | temporal_visual_understanding |
| 证据 | frame paths / source artifacts |
| 缺口 | quality issues |

**Step 4: Preserve raw transcript**

`full-transcript.md` should stay chronological and complete. Do not collapse it into summary prose.

**Step 5: Verify**

Run:

```powershell
.\scripts\video-knowledge.ps1 export-knowledge-note `
  %WORKSPACE_ROOT%\video-knowledge-pipeline\real-tests\feishu-video-retry-live-asr\webui-bundle `
  --title "feishu-video-retry"
```

Acceptance:

- A human can read `knowledge-note.md` without opening JSON.
- Every visual/temporal claim has evidence paths or an explicit gap.

## Task 6: Make Human Review the Fallback, Not a Side Channel

**Files:**

- Modify: `src/video_knowledge_pipeline/review_session.py`
- Modify: `src/video_knowledge_pipeline/webui_bridge.py`
- Modify: `src/video_knowledge_pipeline/knowledge_note_export.py`
- Test: `tests/test_video_pipeline_smoke.py`

**Step 1: Add review categories**

Support:

- `accepted_no_visual_content`
- `accepted_ocr_empty`
- `corrected_transcript`
- `corrected_visual_text`
- `corrected_visual_understanding`
- `needs_recapture`
- `needs_model_retry`

**Step 2: Update review apply rules**

Rules:

- Human accepted OCR-empty can clear `ocr_text_empty` but must keep a visible note in export.
- Human corrected visual text can count toward `screen_text`.
- Human corrected visual understanding can count toward `semantic_frame_understanding`.
- Human review never deletes original machine output.

**Step 3: WebUI copy**

Make the review page show:

- machine output,
- human correction fields,
- exact apply command,
- exact MCP args path.

Acceptance:

- Review can resolve real gaps without editing `timeline.json` manually.

## Task 7: Add a Real Acceptance Checklist Command

**Files:**

- Modify: `src/video_knowledge_pipeline/cli.py`
- Modify: `src/video_knowledge_pipeline/mcp_server.py`
- Modify: `src/video_knowledge_pipeline/bundle_readiness.py`
- Test: `tests/test_video_pipeline_smoke.py`

**New CLI:**

```powershell
.\scripts\video-knowledge.ps1 acceptance-check <webui-bundle>
```

**New MCP tool:**

```text
acceptance_check_tool(bundle_dir)
```

**Checklist output:**

- ASR complete?
- frames complete?
- routing complete?
- OCR truthful?
- semantic coverage acceptable?
- temporal coverage acceptable?
- human review applied?
- export fresh?
- secrets absent?
- restore chain available for model writes?

**Acceptance thresholds for personal use:**

| Area | Minimum |
|---|---|
| ASR | 100% or explicit accepted gaps |
| route | 100% |
| document visual | no false-positive OCR |
| semantic | either processed or review accepted |
| temporal | either processed or review accepted |
| export | generated after latest timeline update |
| secrets | no known key patterns |

Run:

```powershell
python -m pytest -q
.\scripts\video-knowledge.ps1 acceptance-check %WORKSPACE_ROOT%\video-knowledge-pipeline\real-tests\feishu-video-retry-live-asr\webui-bundle
```

Expected:

- returns `ok=false` with specific blockers until the bundle is genuinely accepted,
- returns `ok=true` only after machine or human review paths resolve all required gaps.

## Task 8: Documentation and Discovery Refresh

**Files:**

- Modify: `docs/architecture.md`
- Modify: `AGENT_DISCOVERY.md`
- Modify: `README.md`

**Step 1: Update architecture links**

Add this Phase 4 plan to `docs/architecture.md`.

**Step 2: Update discovery commands**

Document:

- `acceptance-check`,
- `ocr_text_empty`,
- review fallback categories,
- the difference between OCR success and meaningful OCR coverage.

**Step 3: Verify docs do not contain secrets**

Run:

```powershell
rg -n -e "sk-" -e "api_key" -e "AGNES_API_KEY" -e "OPENAI_API_KEY" %WORKSPACE_ROOT%\video-knowledge-pipeline
```

Expected:

- only environment variable names are present,
- no real keys appear.

## Suggested Commit Slices

1. `fix: reject empty visual structure imports`
2. `feat: clarify bundle acceptance states`
3. `feat: improve knowledge note evidence structure`
4. `feat: route human review into coverage fallback`
5. `feat: add acceptance checklist`
6. `docs: document phase four quality gates`

## Stop Conditions

Pause and reassess if:

- `ebook_markdown_pipeline` repeatedly returns empty OCR for frames that visibly contain dense text.
- The current multimodal provider cannot return stable JSON for 5 selected semantic frames.
- Temporal analysis quality is worse than single-frame analysis on the same segments.
- Human review categories expand into a full annotation product; then the right move is a small dedicated review UI, not more JSON fields.

## Final Acceptance for Phase 4

Phase 4 is complete when:

- `python -m pytest -q` passes.
- Real bundle coverage no longer counts synthetic OCR wrappers.
- `bundle-next-action` gives one truthful next step.
- `acceptance-check` distinguishes incomplete, human-accepted, and complete states.
- `exports/knowledge-note.md` is useful to read as a lecture note.
- `exports/full-transcript.md` preserves the chronological transcript.
- Generated reports contain no API keys.
