# Phase 3 Development Plan: Stabilize Review, OCR Bridge, and Repeatable Runs

## Update Record

- 2026-06-11 23:20:00 | Codex (GPT-5) | Created the next-stage plan from the current real bundle coverage, exported Markdown state, and partially implemented review round trip.

## Current Baseline

Reference bundle:

```text
%WORKSPACE_ROOT%\video-knowledge-pipeline\real-tests\feishu-video-retry-live-asr\webui-bundle
```

Current coverage snapshot:

| Channel | Covered | Blocker |
|---|---:|---:|
| speech | 68 / 68 | 0 |
| visual_frames | 68 / 68 | 0 |
| visual_route | 68 / 68 | 0 |
| screen_text | 0 / 68 | 9 |
| structured_visual | 0 / 9 | 9 |
| semantic_frame_understanding | 10 / 61 | 51 |
| temporal_visual_understanding | 3 / 12 | 9 |
| source_artifacts | 1 / 1 | 0 |
| time_axis | 100 / 100 | 0 |

The pipeline is no longer missing its main architecture. The working pieces are:

- local video bundle generation,
- ASR timeline,
- frame extraction,
- visual routing,
- single-frame multimodal API calls,
- temporal frame groups and temporal multimodal calls,
- coverage audit,
- hierarchical Markdown export,
- CLI / MCP / WebUI surfaces.

The next stage should focus on making the existing pieces dependable and reviewable. Do not start another broad tool hunt unless a listed blocker proves impossible with the current tool-first architecture.

## Phase 3 Goal

Make one real knowledge-video run repeatable end to end:

1. OCR/document-like frames either parsed through `ebook_markdown_pipeline` or explicitly marked with a concrete external blocker.
2. Human review notes round-trip into `timeline.json`, coverage, readiness, and exported Markdown without overwriting machine evidence.
3. `bundle-next-action` and WebUI/MCP commands guide the operator through the next missing step without reconstructing commands by hand.
4. `knowledge-note.md` becomes the primary human-readable artifact, with layered Markdown, transcript, visual description, temporal events, evidence paths, and unresolved gaps.
5. Tests and a real smoke run prove the loop is stable.

## Non-Goals

- Do not vendor `ebook_markdown_pipeline`, `video-download-orchestrator`, Peepshow, or model repositories into this repo.
- Do not rewrite OCR, ASR, or multimodal inference engines.
- Do not treat human review as a destructive edit of machine outputs.
- Do not hide missing OCR or model failures behind a clean-looking summary.
- Do not store API keys in docs, manifests, reports, tests, or generated bundles.

## Priority 0: Lock the Current Worktree

Purpose:

Make sure the partially implemented changes are internally consistent before adding new features.

Tasks:

- Run the full test suite.
- Inspect and finish the partially added human-review export code.
- Confirm generated reports do not contain API keys.
- Keep unrelated dirty files intact.

Commands:

```powershell
python -m pytest -q
rg -n -e "sk-" -e "api_key" %WORKSPACE_ROOT%\video-knowledge-pipeline\real-tests\feishu-video-retry-live-asr\webui-bundle
```

Acceptance:

- `python -m pytest -q` passes.
- Secret scan finds no literal key.
- The repo can be resumed from this plan without guessing which patch was half-applied.

## Priority 1: Finish Human Review Round Trip

Purpose:

Human judgment must become structured data. Quality screening, tags, corrections, and accepted gaps should affect coverage and final Markdown, while preserving original ASR/OCR/model outputs.

Implementation tasks:

- Finish `apply_review_notes_to_bundle`.
- Add CLI:
  - `apply-review-notes <bundle_dir> [--review-json <path>] [--no-write]`
- Add MCP tool:
  - `apply_review_notes(bundle_dir, review_json?, write=true)`
- Ensure `review-notes.json` schema is stable:

```json
{
  "schema": "lecture_review_notes.v1",
  "reviews": [
    {
      "timeline_index": 1,
      "status": "accepted",
      "tags": ["人工确认"],
      "comment": "人工确认该片段不需要额外视觉模型补充",
      "corrected_transcript": "...",
      "corrected_visual_text": "...",
      "corrected_visual_understanding": {}
    }
  ]
}
```

Rules:

- Do not overwrite `transcript`, `visual_text`, `structured_visual`, `visual_understanding`, or `temporal_visual_understanding`.
- Store human corrections under explicit fields:
  - `human_corrected_transcript`
  - `human_corrected_visual_text`
  - `human_corrected_visual_understanding`
  - `human_review`
- `accepted` / `reviewed` can clear machine-missing blockers only when the review note is attached to the exact timeline index.
- Re-run coverage and readiness after applying notes.

Tests:

- Review notes preserve original machine fields.
- Accepted review removes relevant `needs_human_review` style quality issues.
- Human corrections appear in `knowledge-note.md`.
- Coverage/readiness count accepted review as intentional fallback.

Acceptance:

- A fake review note applied to a fixture updates timeline, coverage, readiness, and export.
- Real bundle can run `apply-review-notes --no-write` without modifying files.

## Priority 2: Make OCR Bridge Failure Actionable

Purpose:

The current real OCR path reaches `ebook_markdown_pipeline` but is blocked by the external image OCR dependency: `Umi-OCR module not found: PPOCR_api.py`. This should become an actionable status, not a generic failed row.

Implementation tasks:

- Add explicit external blocker classification:
  - `ebook_pipeline_unavailable`
  - `umi_ocr_missing`
  - `artifact_missing`
  - `artifact_parse_failed`
- Add visual-structure report rows showing:
  - timeline index,
  - frame path,
  - chosen external tool,
  - MCP flow,
  - exact blocker,
  - next human action.
- Keep support for imported external JSON so OCR results from a repaired `ebook_markdown_pipeline` can be backfilled later.
- Add a no-network/no-external-tool test for failure normalization.

Recommended human action when `umi_ocr_missing` appears:

```text
Repair ebook_markdown_pipeline image OCR branch, then rerun:
.\scripts\video-knowledge.ps1 run-visual-structure <bundle> --execute-ebook-pipeline --indexes "16,17" --timeout-seconds 120
```

Acceptance:

- `visual-structure-report.md` tells the operator exactly whether the problem is this repo, MCP bridge, missing Umi-OCR, or missing artifact.
- Coverage remains blocked but no longer ambiguous.

## Priority 3: Turn Bundle Next Action into the Main Operator Loop

Purpose:

The user or an agent should ask "下一步" and get a concrete command that is safe to run, with the correct confirmation values and bundle paths.

Implementation tasks:

- Update `bundle-next-action` priority order:
  1. OCR/document visual blockers,
  2. temporal frame groups missing,
  3. temporal analysis missing,
  4. semantic analysis missing,
  5. human review pending,
  6. export stale,
  7. acceptance report.
- Include:
  - exact CLI command,
  - MCP tool name,
  - args JSON path,
  - preview/execute distinction,
  - whether API/model calls are required,
  - expected files after success.
- Make WebUI consume the same next-action payload instead of duplicating command text.

Tests:

- A fixture with missing temporal frame groups recommends frame group generation before temporal analysis.
- A fixture with OCR blockers recommends visual structure before more semantic calls.
- A fixture with stale export recommends export.

Acceptance:

- Running one command returns the next safe action without reading internal JSON manually.

## Priority 4: Improve Markdown Knowledge Note Quality

Purpose:

The current export has the right headings, but it is still too raw. The next version should read like a structured lecture note while preserving full transcript and evidence.

Implementation tasks:

- Add chapter titles from transcript/topic cues when possible.
- Add per-chapter tables:
  - key claims,
  - tools/platforms shown,
  - operations demonstrated,
  - evidence frames,
  - unresolved gaps.
- Separate "模型看到的画面" from "人工审核补充".
- Preserve full chronological transcript in `full-transcript.md`.
- Add a compact top-level summary:
  - video topic,
  - main sections,
  - demonstrated workflow,
  - unresolved extraction gaps.

Acceptance:

- `knowledge-note.md` can be read without opening `timeline.json`.
- Every nontrivial visual/temporal claim links to a frame path or source artifact.
- Missing OCR and missing model understanding remain visible.

## Priority 5: Formalize Optional Peepshow Import

Purpose:

Peepshow can help as an optional evidence extractor, but it must not become the main reasoning pipeline.

Implementation tasks:

- Audit current `peepshow_adapter.py` against actual source artifacts.
- Define importable fields:
  - transcript,
  - OCR text,
  - key frame paths,
  - tags,
  - HTML report path,
  - deduped frame groups.
- Add tests with fixture artifacts only.
- Register imported outputs as `source_artifacts`, then let routing/coverage decide how to use them.

Acceptance:

- Peepshow output can be attached to a bundle as evidence.
- It does not bypass `video_frame_router`, OCR bridge, multimodal frame analysis, temporal analysis, review, or export.

## Priority 6: Real Acceptance Run

Purpose:

Prove the tool is usable, not just unit-tested.

Commands:

```powershell
python -m pytest -q
.\scripts\video-knowledge.ps1 audit-knowledge-coverage %WORKSPACE_ROOT%\video-knowledge-pipeline\real-tests\feishu-video-retry-live-asr\webui-bundle
.\scripts\video-knowledge.ps1 bundle-status-report %WORKSPACE_ROOT%\video-knowledge-pipeline\real-tests\feishu-video-retry-live-asr\webui-bundle
.\scripts\video-knowledge.ps1 export-knowledge-note %WORKSPACE_ROOT%\video-knowledge-pipeline\real-tests\feishu-video-retry-live-asr\webui-bundle --title "feishu-video-retry"
```

Acceptance:

- Tests pass.
- Coverage report is current.
- Status report names the remaining blockers.
- `exports/knowledge-note.md` and `exports/full-transcript.md` are human-readable.
- No API key appears in generated artifacts.

## Suggested Commit Slices

1. `feat: add review note round trip`
2. `feat: classify ebook visual structure blockers`
3. `feat: make bundle next action operator friendly`
4. `feat: improve knowledge note chapters`
5. `feat: formalize peepshow source artifact import`
6. `test: add real bundle acceptance checks`

## Stop Conditions

Pause and reassess before deeper work if:

- `ebook_markdown_pipeline` cannot process image screenshots even after Umi-OCR repair.
- Agnes/OpenAI-compatible provider keeps timing out on small confirmed batches.
- Human review starts requiring a full editing UI instead of JSON/WebUI-assisted review.
- Markdown quality requires semantic rewriting beyond evidence-backed extraction.

In those cases, keep this repo as orchestration and choose a better external tool for the failing specialist branch rather than absorbing that branch into this codebase.
