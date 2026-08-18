# ASR Plan Checkpoint Resume Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Make `run-asr-plan` resume interrupted Qwen ASR work and make completed reruns idempotent without invoking the model again.

**Architecture:** Keep chunk state in the existing Qwen runner. Add a thin top-level checkpoint validator/restorer, expose resume control through the CLI, and strengthen new checkpoint identity while retaining legacy compatibility.

**Tech Stack:** Python 3.11+, argparse, pathlib, pytest, VKP atomic JSON storage.

---

### Task 1: Add failing orchestration tests

**Files:**
- Create: `tests/test_asr_plan_checkpoint_resume.py`
- Read: `src/video_knowledge_pipeline/asr_execution.py`

**Step 1: Write the failing tests**

Add synthetic plan/checkpoint fixtures and tests asserting that a complete checkpoint reconstructs `raw-asr-output.json` without calling `_run_command_with_cuda_oom_recovery`, a second run leaves that raw output byte-identical, a partial checkpoint is surfaced as resumable before the child command runs, and `resume=False` adds `--no-resume` to the Qwen command.

**Step 2: Run tests to verify failure**

Run: `python -m pytest tests/test_asr_plan_checkpoint_resume.py -q`

Expected: FAIL because `run_asr_plan` does not yet accept `resume` or restore/skip completed checkpoints.

### Task 2: Implement top-level resume orchestration

**Files:**
- Modify: `src/video_knowledge_pipeline/asr_execution.py`

**Step 1: Add checkpoint inspection helpers**

Parse only the known Qwen module command, validate its checkpoint schema/input/model/chunk settings and semantic contract, and return bounded metadata without copying transcript text into logs.

**Step 2: Add complete-checkpoint restoration**

Project checkpoint results into `video_knowledge_pipeline.qwen3_asr_raw_output.v1`, write through `storage.write_json`, and mark the result as recovered. Do not execute a child process.

**Step 3: Add idempotent completed-output reuse**

When the completed raw JSON matches the complete checkpoint, reuse it without rewriting. Keep normalization and existing run-log behavior unchanged.

**Step 4: Add explicit no-resume command control**

Accept `resume: bool = True`; append `--no-resume` only for the Qwen runner when false.

**Step 5: Run focused tests**

Run: `python -m pytest tests/test_asr_plan_checkpoint_resume.py -q`

Expected: PASS.

### Task 3: Strengthen child checkpoint identity

**Files:**
- Modify: `src/video_knowledge_pipeline/qwen3_asr_python_runner.py`
- Test: `tests/test_asr_plan_checkpoint_resume.py`

**Step 1: Add semantic execution contract fields**

Persist input path/size/mtime, model, forced aligner, language, context SHA-256, chunk seconds, token limit, dtype, and selected chunk indexes.

**Step 2: Reject semantic drift and accept legacy checkpoints**

Use exact contract equality for new checkpoints. For legacy checkpoints, retain path/size/model/chunk validation and also validate stored forced-aligner/language fields when present.

**Step 3: Run focused child/orchestration tests**

Run: `python -m pytest tests/test_asr_plan_checkpoint_resume.py tests/test_local_media_resilience.py -q`

Expected: PASS.

### Task 4: Expose CLI control and document evidence

**Files:**
- Modify: `src/video_knowledge_pipeline/cli.py`
- Modify: `docs/asr-silence-snapped-chunk-manifest-2026-07-28.md`

**Step 1: Add `--no-resume`**

Default to resume and pass the boolean to `run_asr_plan`.

**Step 2: Record intent, decision, reason, evidence, scope, and rollback**

Append a dated implementation record. Do not include real media names, paths, meeting content, or personal information.

### Task 5: Verify the change

**Files:**
- Verify: all files changed above

**Step 1: Run focused and associated tests**

Run: `python -m pytest tests/test_asr_plan_checkpoint_resume.py tests/test_local_media_resilience.py tests/test_asr_pipeline.py -q`

Expected: PASS, subject only to previously recorded unrelated dirty-worktree failures.

**Step 2: Run static checks**

Run Ruff on the changed Python files, compile them, run `git diff --check`, and scan the task diff for secrets and personal paths.

**Step 3: Review repository state**

Confirm that only task files plus pre-existing dirty files are changed. Do not reset, stash, checkout, push, invoke a model, or process real media.
