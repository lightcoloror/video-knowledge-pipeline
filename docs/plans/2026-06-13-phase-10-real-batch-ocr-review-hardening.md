# Phase 10 Real Batch OCR Review Hardening Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Move `video-knowledge-pipeline` from a single-video acceptance loop to a repeatable multi-video personal tool with a closed screen-text recovery and review workflow.

**Architecture:** Keep the existing video-first routing pipeline. Add orchestration and evidence-preserving recovery layers around the working core: batch acceptance dashboards, crop-based screen text recovery, clearer review statuses, and more stable Markdown exports. Do not replace ASR, ebook Markdown parsing, or multimodal provider layers.

**Tech Stack:** Python package under `src/video_knowledge_pipeline`, static `review.html`, PowerShell wrapper `scripts/video-knowledge.ps1`, pytest, existing `ebook_markdown_pipeline`, CaptiOCR/Tesseract fallback, local SenseVoice/FunASR, current CLI/MCP bridge.

---

## Current Baseline

- Phase 9 completed in commit `e087e28`.
- Real bundle acceptance is `accepted_with_known_gaps`.
- ASR, semantic visual analysis, temporal visual analysis, provider matrix, review UI, and batch-run preview are functional.
- Main weak channel is screen text, especially small UI/browser/editor text.
- Test coverage exists but is concentrated in a large smoke test file, which slows future iteration.

## Task 1: Batch Acceptance Dashboard

- Extend `batch-run` to write `batch-acceptance-summary.json` and `batch-acceptance-summary.md`.
- Summarize each item with acceptance status, screen text status, semantic/temporal gaps, pending review count, export freshness, and next action.
- Preserve manifest compatibility and allow optional item metadata: `expected_content_type`, `priority`, and `notes`.

## Task 2: Screen Text Recovery

- Add `run-screen-text-recovery` CLI/MCP entrypoint.
- Reuse `run_ocr_backfill` recovery planning.
- Default mode previews only.
- `--execute-crops` creates crop images under `ocr-crops/`.
- `--execute-ocr` runs available OCR fallback on generated crops and imports only non-empty text.
- OCR failures, empty text, and wrapper-only output must not clear blockers.

## Task 3: Review and Export Closure

- Extend review statuses with `accepted_known_gap` and `needs_rerun_ocr`.
- Make review template and fill guide distinguish `corrected_visual_text`, `keep_image`, `accepted_known_gap`, and `needs_rerun_ocr`.
- After applying review notes, refresh coverage, readiness, acceptance check, review HTML, and knowledge note export freshness.
- Add a screen-text review priority queue to static `review.html`.
- Include source-channel participation in `knowledge-note.md`, visual/demo notes in `full-transcript.md`, and crop evidence in `extraction-audit.md`.

## Task 4: Test Maintainability

- Add focused test files for batch, screen text recovery, review, and export behavior.
- Keep old public CLI/MCP contracts stable.
- Run the full pytest suite and a secret scan before committing.

## Acceptance

- `python -m pytest -q` passes.
- Existing `mcp-audit-bundle` stays OK on the real bundle.
- Existing accepted bundle remains `accepted_with_known_gaps` or better.
- Secret scan only finds placeholders/docs/examples, not real keys.

## Execution Log

- 2026-06-13 11:30:00 | Codex (GPT-5) | Added batch acceptance dashboard outputs, `run-screen-text-recovery` CLI/MCP, crop generation, wrapper-only OCR import rejection, review status distinctions, screen-text WebUI queue, export source-channel/demo/crop evidence improvements, and focused Phase 10 tests.
- 2026-06-13 11:30:00 | Codex (GPT-5) | Verification: `python -m pytest -q` passed with `126 passed`.
- 2026-06-13 11:35:00 | Codex (GPT-5) | Real bundle verification: `run-screen-text-recovery` preview planned 25 crop candidates without executing crops/OCR; `acceptance-check` stayed `accepted_with_known_gaps`; `mcp-audit-bundle` passed with 31/31 MCP args OK after the new screen-text entrypoint was registered.
- 2026-06-13 11:35:00 | Codex (GPT-5) | Secret scan checked `sk-`, `Authorization: Bearer`, `AGNES_API_KEY=`, `GEMINI_API_KEY=`, and `OPENAI_API_KEY=` across docs/src/tests/scripts/README/AGENT_DISCOVERY; hits were placeholders, docs, or scan commands only.
- 2026-06-13 11:40:00 | Codex (GPT-5) | Split `tests/test_video_pipeline_smoke.py` from 5371 lines down to 117 lines. Moved topic tests into focused files including batch, screen text recovery, review session, knowledge export, ASR, vision, provider, bundle workflow, acceptance, video source, CLI/config, and misc modules.
- 2026-06-13 11:40:00 | Codex (GPT-5) | Batch real-run verification: ran `batch-run --resume` over 3 existing real bundles and wrote `real-tests/phase10-batch-acceptance/batch-acceptance-summary.json` plus `.md`; dashboard separated one `accepted_with_known_gaps` bundle from two bundles needing ASR/visual follow-up.
- 2026-06-13 11:40:00 | Codex (GPT-5) | Final verification after test split: `python -m pytest -q` passed with `126 passed`; real bundle `acceptance-check` stayed `accepted_with_known_gaps`; `mcp-audit-bundle` passed with 31/31 MCP args OK; `git diff --check` passed.
- 2026-06-13 11:40:00 | Codex (GPT-5) | Secret verification: source/docs/tests scan still found placeholders/docs/tests only; full-repo `sk-...` filename scan found no matches; real-test API key hits were `<your key>` placeholders in generated vision acceptance instructions.
