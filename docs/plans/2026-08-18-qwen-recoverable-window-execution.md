# Qwen Recoverable Window Execution Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Make ultra-long Qwen ASR extract and process one deterministic audio window at a time so one failed window never discards completed windows.

**Architecture:** Reuse `audio_chunk_manifest` for deterministic fixed boundaries and the single resolved FFmpeg outlet. Keep `qwen3_asr_python_runner` checkpoint as the only state owner; extraction, transcription, failure, and retry evidence are written atomically after each window.

**Tech Stack:** Python 3.11+, pathlib, subprocess/FFmpeg/ffprobe, VKP atomic JSON storage, pytest, managed Windows test runtime.

---

## Executor Rules

- Start from commit `31b7e437aaf86fce17e265dbcd16a4ff38f9de00`; first report any drift.
- Preserve the existing dirty worktree. Do not reset, stash, checkout, or edit Provider files, `tests/test_asr_pipeline.py`, guided-tour files, or `scripts/run-tests-managed.ps1` unless the owner explicitly revises scope.
- Do not run real media, a local model, a Provider, network access, upload, publication, configuration changes, or push.
- Use synthetic fixtures and the stable managed Windows test entry `D:\used-by-codex\scripts\windows-test-runtime.ps1`. The existing untracked project wrapper is outside task scope. A missing dependency is an environment blocker, not permission to install packages.
- Update the handoff `context.md` status and write one independent completion receipt in `outputs/`.

### Task 1: Write failing window-isolation tests

**Files:**
- Create: `tests/test_qwen_recoverable_windows.py`
- Read: `tests/test_asr_plan_checkpoint_resume.py`
- Read: `tests/test_local_media_resilience.py`

**Step 1: Add a deterministic three-window fixture**

Patch duration discovery to return `90.0`, window extraction to return one synthetic WAV per requested index, and the Qwen runtime to return text/timestamps without loading a model.

**Step 2: Add the extraction-failure test**

Configure index 1 extraction to fail. Assert indexes 0 and 2 succeed, index 1 is a `chunk_extraction_failed` gap, the checkpoint contains results for 0 and 2, and the final status is `degraded` and `usable`.

**Step 3: Add the resume test**

On the second run, make index 1 succeed and fail the test if extraction is called for indexes 0 or 2. Assert all three indexes complete and `resumed_from_checkpoint=true`.

**Step 4: Add the absolute-window-offset test**

Return a local timestamp `[1.0, 2.0]` for window `[30.0, 60.0]`; assert the public timestamps are `[31.0, 32.0]` exactly once.

**Step 5: Verify the tests fail before implementation**

Run through `D:\used-by-codex\scripts\windows-test-runtime.ps1 adapter` with pytest arguments `tests/test_qwen_recoverable_windows.py -q -p no:cacheprovider`. Expected: failures because the runner still calls batch `_audio_chunks`.

### Task 2: Extract reusable fixed-window primitives

**Files:**
- Modify: `src/video_knowledge_pipeline/audio_chunk_manifest.py`
- Test: `tests/test_audio_chunk_manifest.py`

**Step 1: Add deterministic boundary planning**

Add a public `fixed_chunk_boundaries(total_seconds: float, target_chunk_seconds: float) -> list[tuple[float, float]]`. Validate positive inputs and return contiguous `[index * target, min(total, (index + 1) * target)]` windows.

**Step 2: Add one-window extraction**

Add `extract_audio_chunk_window(media, output_dir, *, index, start_seconds, end_seconds, ffmpeg_path=None, timeout_seconds=900) -> dict`. It must use `resolve_media_tool`, `local_tool_subprocess_env`, `-ss`, `-t`, mono 16 kHz WAV, and return index/path/bytes/start/end/duration/command. It must not delete sibling chunks or retry silently.

**Step 3: Reuse the primitives internally**

Make existing fixed-window helpers call `fixed_chunk_boundaries` and make `_extract_chunk_windows` delegate each extraction to `extract_audio_chunk_window` while preserving existing schemas and tests.

**Step 4: Test boundary and sibling-preservation behavior**

Add synthetic tests for a 65-second source with 30-second windows and for an index-1 extraction failure that leaves an existing index-0 artifact untouched.

### Task 3: Convert Qwen to lazy recoverable windows

**Files:**
- Modify: `src/video_knowledge_pipeline/qwen3_asr_python_runner.py`
- Test: `tests/test_qwen_recoverable_windows.py`

**Step 1: Discover duration before iteration**

Reuse an existing registered ffprobe duration helper or add a bounded local helper that uses `resolve_media_tool('ffprobe')`, `local_tool_subprocess_env`, and a timeout. Do not use a guessed duration.

**Step 2: Build the deterministic plan**

Call `fixed_chunk_boundaries`; validate requested indexes against the plan; calculate a canonical plan revision from input identity, chunk seconds, and boundaries. Add only this revision to the new execution contract.

**Step 3: Skip completed indexes before extraction**

Iterate planned `(index, start, end)` rows after removing checkpointed successes. Call `extract_audio_chunk_window` only inside the per-window loop.

**Step 4: Isolate extraction failures**

Catch extraction errors inside the loop, write/update the existing failed-chunk record with exact boundaries, `reason=chunk_extraction_failed`, detail, attempt count, retry exhaustion, and existing retry-command shape; atomically write the checkpoint and continue.

**Step 5: Transcribe and checkpoint immediately**

For a successfully extracted window, call the existing runtime, add `start_seconds` once to local timestamps, preserve current segment IDs, update results/failures, and atomically write the checkpoint before moving on. Remove only the current temporary window after its result is durable.

**Step 6: Preserve compatibility**

Legacy checkpoints without plan revision remain eligible under the current bounded legacy match. New checkpoints require exact execution-contract equality. Do not change canonical transcript arbitration or Provider routing.

### Task 4: Preserve top-level idempotency and reports

**Files:**
- Modify only if necessary: `src/video_knowledge_pipeline/asr_execution.py`
- Test: `tests/test_asr_plan_checkpoint_resume.py`

**Step 1: Keep completed checkpoint recovery working**

Ensure a complete lazy-window checkpoint still rebuilds the final Qwen raw output without model execution and a second run reuses it byte-for-byte.

**Step 2: Surface extraction gaps without transcript text**

If report changes are necessary, expose only counts, indexes, boundaries, reasons, and receipt paths. Never copy ASR text or context into command logs.

### Task 5: Documentation and completion receipt

**Files:**
- Modify: `docs/asr-silence-snapped-chunk-manifest-2026-07-28.md`
- Create: `docs/receipts/VKP-QWEN-RECOVERABLE-WINDOWS-20260818-01.completion-receipt.json`
- Modify: `agents/vkp-implementation-agent/handoff/20260818191138-62ca97/context.md`
- Create: `agents/vkp-implementation-agent/handoff/20260818191138-62ca97/outputs/completion-receipt.json`

**Step 1: Record intent, decision, reason, evidence, scope, and rollback**

Do not include real media names, personal paths, meeting content, or context text.

**Step 2: Complete the handoff receipt**

Include base/HEAD commits, exact changed paths, tests and counts, warnings/blockers, proof that no real media/model/network was used, and `Status: completed` only after every required check passes.

### Task 6: Verification and selective checkpoint commit

**Files:**
- Verify all task files above

**Step 1: Run focused tests**

Run the new recoverable-window tests plus `test_asr_plan_checkpoint_resume.py`, `test_local_media_resilience.py`, `test_audio_chunk_manifest.py`, and `test_funasr_chunked_runner.py` through the stable shared managed runtime.

**Step 2: Run static checks**

Run Ruff on touched Python files, AST parse, `git diff --check`, JSON validation, and task-diff scans for personal paths, media names, secrets, and context plaintext.

**Step 3: Review dirty-worktree isolation**

Confirm the staged set contains only task files. Do not stage pre-existing Provider, guided-tour, ASR pipeline, or wrapper changes.

**Step 4: Commit without push**

Commit only after the receipt is valid, using `feat: add recoverable Qwen ASR windows`. Do not push. Return the commit hash to Codex for independent acceptance.
