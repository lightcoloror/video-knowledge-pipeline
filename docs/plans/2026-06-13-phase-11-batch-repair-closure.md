# Phase 11 Batch Repair Closure Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Turn the Phase 10 batch dashboard into a repeatable batch repair loop that plans or safely advances each bundle until it is accepted or clearly queued for human review.

**Architecture:** Keep the existing single-bundle tools as the source of truth. Add a thin batch repair orchestrator that reads a batch manifest or acceptance summary, dispatches only explicitly allowed branches, refreshes derived reports after each action, and writes human-readable repair/review dashboards.

**Tech Stack:** Python package under `src/video_knowledge_pipeline`, existing CLI/MCP bridge, `bundle_next_action`, `bundle_advance_queue`, `run_screen_text_recovery`, `export_knowledge_note`, static `review.html`, pytest.

---

## Current Baseline

- Phase 10 baseline is committed as `67c4ccb`.
- `batch-run` writes `batch-acceptance-summary.json/md`.
- `run-screen-text-recovery` exists and defaults to preview.
- Main real-test weak points are screen text, missing ASR on one bundle, and visual gaps on older bundles.

## Task 1: Batch Repair Runner

- Add `batch-repair-run` CLI/MCP.
- Input can be `video_knowledge_batch.v1`, `video_knowledge_batch_acceptance_summary.v1`, or `video_knowledge_batch_run.v1`.
- Default is preview: no ASR, OCR, or vision execution.
- Explicit flags `--allow-asr`, `--allow-vision`, `--allow-ocr`, and `--execute` decide which machine actions may run.
- Write `batch-repair-run.json`, `batch-repair-run.md`, and `batch-human-review.md`.

## Task 2: Screen Text Closure

- Route `screen_text` and `ocr_text_empty_review` through `run_screen_text_recovery`.
- In preview, only plan crops and commands.
- With `execute=true` and `allow_ocr=true`, generate crops and optionally OCR.
- Refresh coverage, acceptance, status, and exports after action.
- If OCR remains empty or human review is required, add rows to `batch-human-review.md`.

## Task 3: Output Quality

- Add a "本视频剩余风险" section to exported `knowledge-note.md`.
- Make full transcript visual notes say "画面未可靠提取" when the visual branch is expected but missing.
- Add final acceptance/status fields to extraction audit.
- Surface batch summary links and next-action command in static review HTML when the manifest contains batch repair metadata.

## Task 4: Tests and Real Verification

- Unit test preview planning, allow flags, skipped accepted bundles, OCR review routing, and human review aggregation.
- Integration test 3 real bundle preview.
- Execute one real screen-text crop run with `--allow-ocr --execute --limit 1` and verify crop evidence reaches audit/export.
- Run full regression, MCP audit, acceptance check, diff check, and secret scans.

## Execution Log

- 2026-06-13 11:47:00 | Codex (GPT-5) | Phase 10 baseline verified and committed as `67c4ccb`.
- 2026-06-13 11:55:00 | Codex (GPT-5) | Added `batch_repair_run` orchestration module, CLI command, and MCP tools. Default mode is preview-only; ASR, vision, and OCR remain behind explicit allow/execute flags.
- 2026-06-13 11:56:00 | Codex (GPT-5) | Updated human-readable exports with `本视频剩余风险`, explicit `画面未可靠提取` transcript fallbacks, and final acceptance/next-action rows in `extraction-audit.md`.
- 2026-06-13 11:57:00 | Codex (GPT-5) | Added static WebUI links for bundle next action, batch acceptance, batch repair, and batch human review without introducing a backend.
- 2026-06-13 11:58:00 | Codex (GPT-5) | Real batch preview over 3 real bundles produced `batch-repair-run.json/md` and `batch-human-review.md`; actions were blocked by default allow flags.
- 2026-06-13 11:58:15 | Codex (GPT-5) | Real OCR repair sample ran with `--allow-ocr --execute --limit 1`, wrote 5 crop images for timeline item 1, imported one fallback OCR result, and surfaced remaining human review.
- 2026-06-13 11:59:03 | Codex (GPT-5) | Fixed repair refresh ordering to export before acceptance. Main real bundle returned to `accepted_with_known_gaps` with fresh exports; `mcp-audit-bundle` stayed 31/31 OK.
- 2026-06-13 11:59:20 | Codex (GPT-5) | Regression: `python -m pytest -q` passed with 130 tests. `git diff --check` passed with CRLF warnings only. Secret scans found placeholders only and no `sk-...` real key pattern.
