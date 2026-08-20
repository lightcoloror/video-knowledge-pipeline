# WorkBuddy Production Feedback Hardening Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Make VKP's OCR recovery and local-runtime diagnosis fail visibly and preserve trustworthy OCR evidence through the final synthetic knowledge-note export.

**Architecture:** Extend the existing OCR backfill, Tesseract resolver, RAM++ adapter status, local runtime preflight, and knowledge-note exporter. Keep every path configurable or inventory-derived, make replacement destructive only for authoritative full-snapshot observations, and emit a standalone overwrite receipt. No dependency installation, service startup, real-media access, model execution, or provider request is part of this change.

**Tech Stack:** Python 3.11+, pytest, Ruff, existing VKP JSON/Markdown artifacts and adapters.

---

## Task 1: Freeze the shared-tree boundary

**Files:**
- Create: `docs/plans/2026-08-20-workbuddy-production-feedback-hardening.md`
- Inspect only: pre-existing dirty files recorded in the owner thread

1. Record HEAD, branch, staged paths, dirty paths, and hashes of pre-existing owner files.
2. Confirm staging is empty and use a strict implementation whitelist.
3. Do not create a worktree because this owner repository contains intentional shared in-progress boundaries that must remain visible.

## Task 2: Route multilingual OCR directly to Tesseract

**Files:**
- Modify: `src/video_knowledge_pipeline/ocr_backfill.py`
- Modify: `tests/test_ocr_backend_capability.py`

1. Add a failing test proving `chi_sim+eng` never loads CaptiOCR when Tesseract has both language packs.
2. Add a failing test proving missing multilingual packs fail before CaptiOCR and before OCR subprocess execution.
3. Run the focused tests and preserve the red evidence.
4. Add a small language-list helper and route multi-language requests directly through the existing Tesseract CLI runner.
5. Add an explicit route reason to the runner receipt and rerun focused tests green.

## Task 3: Add authoritative OCR replace-snapshot mode

**Files:**
- Modify: `src/video_knowledge_pipeline/ocr_backfill.py`
- Modify: CLI module containing `run-ocr-backfill` arguments
- Create: `tests/test_ocr_replace_snapshot.py`

1. Add failing tests for full candidate selection, authoritative empty clearing, failure preservation, coverage rejection, and overwrite receipt contents.
2. Add `apply_mode=merge|replace_snapshot` with merge as the backwards-compatible default.
3. In snapshot mode, include all image-backed timeline items and require one authoritative observation for every candidate.
4. Clear stale OCR only for an authoritative empty observation; preserve it on execution/import errors.
5. Write `ocr-backfill-overwrite-receipt.json` with mode, coverage, updated/cleared/preserved indexes, hashes, scope, and rollback guidance.
6. Expose the mode and receipt in result, manifest, and report; rerun focused tests green.

## Task 4: Expand doctor for RAM++ and heavy-model compatibility

**Files:**
- Modify: `src/video_knowledge_pipeline/general_tagger_adapter.py`
- Modify: `src/video_knowledge_pipeline/local_tool_inventory.py`
- Create or modify: `tests/test_local_runtime_preflight.py`

1. Add failing synthetic tests for SOURCE_INVENTORY discovery of recognize-anything deployment/source paths.
2. Add failing tests for a configured heavy-model interpreter and a mocked transformers compatibility probe.
3. Reuse `source_reviews_root()` and the existing `general_tagger_status`; do not hard-code this machine's paths.
4. Resolve the interpreter from `VKP_HEAVY_MODEL_PYTHON`, project venv candidates, or current Python and report provenance.
5. Run a bounded read-only subprocess probe that checks module availability and the transformers symbol locations required by RAM++; do not import models or initialize GPU.
6. Add explicit checks, blockers, and recovery commands to local runtime preflight; rerun focused tests green.

## Task 5: Prove OCR evidence reaches the final knowledge note

**Files:**
- Create: `tests/test_knowledge_note_ocr_e2e.py`
- Modify only if the red test proves necessary: `src/video_knowledge_pipeline/knowledge_note_export.py`

1. Build a fully synthetic bundle with fake image bytes, transcript, manifest, and imported OCR observation.
2. Run OCR backfill and the existing knowledge-note export without services or provider calls.
3. Assert the accepted OCR phrase exists in `timeline.json`, the final note, and the relevant export evidence artifact.
4. Preserve red evidence if the exporter drops OCR, make the smallest integration fix, and rerun green.

## Task 6: Verify and selectively commit

**Files:** only files listed above plus evidence documentation if required.

1. Run focused OCR, doctor, and knowledge-note tests.
2. Run associated regression suites and Ruff/AST checks.
3. Re-hash pre-existing dirty boundaries and ensure no unexpected path changed.
4. Stage only the implementation whitelist and inspect staged diff plus sensitive-data scan.
5. Commit locally with one scoped commit. Do not push unless the user separately asks.

## 2026-08-20 16:21:54 | Codex（GPT-5.6 Sol）| Implementation Record

### Multilingual OCR routing

- Intent: prevent CaptiOCR's combined-language fallback from producing English-only garbage for `chi_sim+eng`.
- Decision: split the requested language list in VKP and route requests containing more than one language directly to the existing Tesseract CLI adapter.
- Reason: Tesseract natively accepts combined language codes, while CaptiOCR checks for a nonexistent combined `.traineddata` filename.
- Evidence: red receipt `codex-test-32000-6216c6a8068e44e894336ce55581b595`; green receipts `codex-test-5256-1dbbd3eb4d134e2dae6b5dbe64ebff94` and `codex-test-54880-858b898f500242d9943ce025bc75d9e8`.
- Effective scope: OCR backend selection and its structured runner/capability report only; no language pack install, real OCR run, or remote fallback.
- Rollback: revert the scoped commit to restore CaptiOCR-first routing; existing bundle artifacts are not migrated automatically.

### OCR replace snapshot

- Intent: make a reviewed full OCR rerun able to remove stale text instead of leaving invalid earlier values in the timeline.
- Decision: add opt-in `replace_snapshot`, require authoritative coverage of every image-backed candidate, preserve text on errors, and write `ocr-backfill-overwrite-receipt.json` with hashes and indexes.
- Reason: clearing on failed OCR would lose evidence, while merge-only behavior cannot remove known-bad historical text.
- Evidence: snapshot update/clear, incomplete-coverage rejection, failure preservation, CLI, manifest, report, and receipt tests in `tests/test_ocr_replace_snapshot.py`; associated 73-test receipt `codex-test-18824-484c5f64f64e4d55b466953f5d0f0289`.
- Effective scope: `visual_text` and OCR backfill fields for the full image-backed candidate snapshot; default mode remains `merge`.
- Rollback: restore the exact prior value from `receipt.changes[].before_text` (with `original_visual_text` retained as legacy context), or revert the scoped commit; no automatic rollback mutates bundles.

### RAM++ and heavy-model doctor

- Intent: stop false missing-model reports and surface the actual interpreter/dependency/transformers import-layout readiness before a heavy run.
- Decision: discover recognize-anything source and deployment from `SOURCE_INVENTORY.json`, resolve a configurable heavy interpreter, and run a bounded source-file symbol probe without importing models.
- Reason: the model and tokenizer already exist outside the project default model directory, and transformers 4.57 moved RAM++ helper symbols to `pytorch_utils`.
- Evidence: doctor red receipt `codex-test-12956-02f16a3098914ea6a22d77dc24145beb`; green `codex-test-39364-63b0e61d997a43afaf99e37fab28dc4d`; live read-only preflight reported `ready`, RAM++ paths discovered, heavy Python found, modules present, and transformers `4.57.6` compatible.
- Effective scope: local read-only preflight/status; it starts one bounded Python metadata probe but does not install, load a model, initialize CUDA, process media, or use network access.
- Rollback: unset `VKP_HEAVY_MODEL_PYTHON` to return to discovery order or revert the scoped commit; no runtime environment is modified.

### OCR evidence export regression

- Intent: guarantee accepted OCR evidence remains visible in the final reader-facing knowledge note.
- Decision: add a synthetic OCR-import-to-export E2E contract covering timeline, smart-summary input pack, full transcript, and final knowledge note.
- Reason: existing code already carries `visual_text` through the transcript projection, but no single test protected the complete chain.
- Evidence: E2E receipt `codex-test-48988-b57f13b6a54f45f8b5f3ece34c7ef56e`; focused combined receipt `codex-test-54880-858b898f500242d9943ce025bc75d9e8`; associated 73-test receipt above.
- Effective scope: synthetic regression coverage only; no real media, provider, model, service, or account is touched.
- Rollback: remove the new E2E test with the scoped commit; production export behavior is unchanged by this item.
