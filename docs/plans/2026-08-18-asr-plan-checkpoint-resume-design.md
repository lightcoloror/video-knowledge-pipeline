# ASR Plan Checkpoint Resume Design

## Intent

Make `run-asr-plan` recover predictably after a long local Qwen ASR process is interrupted. A rerun must preserve successful chunks, execute only unfinished chunks, reconstruct the final raw JSON when every chunk is already checkpointed, and avoid a second model invocation when the completed output already exists.

## Decision

Reuse `qwen3_asr_python_runner` as the only chunk/checkpoint state machine. `run_asr_plan` remains an orchestration layer: it validates the checkpoint against the persisted command, reports resume evidence, restores a complete raw output from the existing checkpoint when necessary, and otherwise launches the same child command whose default behavior skips successful chunk indexes. An explicit `--no-resume` option is the only way to ignore a matching checkpoint.

New checkpoints record a semantic execution contract covering the input identity, model, forced aligner/timestamp mode, language, a SHA-256 digest of context, chunk duration, token limit, and dtype. Existing checkpoints remain resumable when their legacy identity and any stored semantic fields match. Device selection and retry limit are operational controls and do not invalidate already accepted text.

## Data Flow and Failure Handling

Before execution, `run_asr_plan` locates `<expected-output-stem>-checkpoint.json`. A corrupt, unrelated, or contract-mismatched checkpoint is reported as non-resumable and left untouched. A partial matching checkpoint is passed through to the existing child runner. A complete matching checkpoint with no failed chunks is projected into the canonical Qwen raw-output schema if the final JSON is absent or invalid. A complete matching raw output is reused byte-for-byte. Timeout reports retain checkpoint counts and an explicit retry command.

No media is modified, uploaded, or re-encoded by the orchestration change. The implementation does not introduce another ASR engine, fallback, provider call, or editing state machine.

## Verification

Synthetic tests cover partial resume metadata, complete-checkpoint recovery without launching a command, byte-stable idempotent reruns, explicit no-resume execution, semantic-contract drift rejection, and legacy checkpoint compatibility. Focused ASR tests and scoped static checks run without real media or models.
