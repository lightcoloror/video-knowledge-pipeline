# MOSS-Transcribe-Diarize VKP Adapter

Updated by Codex (GPT-5) at 2026-07-27 00:00:00 Asia/Shanghai.

## Role

`moss-transcribe-diarize` is an optional local challenger for long recordings with
multiple speakers. It reuses the upstream `mtd-subtitle` CLI and its `segments.json`
output. VKP owns planning, execution gates, normalization, and run logs; it does not
duplicate the model inference implementation.

SenseVoice remains the default Chinese ASR route. MOSS is selected only when a caller
explicitly passes `--preset moss-transcribe-diarize`.

## Local Contract

- Command: `mtd-subtitle`
- Optional command override: `LECTURE_MOSS_TRANSCRIBE_COMMAND`
- Default model id: `OpenMOSS-Team/MOSS-Transcribe-Diarize`
- Output consumed by VKP: `segments.json`
- Preserved metadata: segment start, end, text, and speaker id

Example planning command:

```powershell
video-knowledge plan-asr D:\workspace D:\media\interview.wav --preset moss-transcribe-diarize
```

The plan is preview-only until the normal VKP execution command is called.

## Safety And Readiness

- No model is downloaded by registration or planning.
- Execution fails closed when the CLI is missing.
- Execution fails closed when the selected model is not present in a known local cache
  or at an explicit local path.
- No server, account, API key, or remote audio upload is required by this HF CLI route.
- Promotion requires a short de-identified A/B run against SenseVoice or WhisperX.

## 2026-07-28 Source Fidelity And Speaker Preservation

Updated by Codex / GPT-5.6 at 2026-07-28 17:49:09 Asia/Shanghai.

- **Intent:** keep diarization identities through ASR normalization, transcript
  cleanup, semantic correction, arbitration, Smart Summary input, and final
  reader export.
- **Decision:** reuse the pinned upstream
  `start/end/text/speaker` contract and adapt it to optional `TranscriptCue`
  fields. Raw cluster identity stays machine-readable; reader output gets stable
  anonymous `说话人N` labels. Optional roles remain separate.
- **Reason:** merging or deduplicating by text alone can assign one person's
  statement to another speaker. Role/name inference is not equivalent to
  diarization and must not overwrite the upstream cluster.
- **Evidence:** the pinned upstream parser was executed locally against two
  compact `[S01]`/`[S02]` segments; VKP's focused/related suites passed 213
  tests. Full upstream model tests remain blocked by the global
  `tokenizers==0.21.1` versus `transformers` `>=0.22,<=0.23` mismatch.
- **Effective scope:** local contract preservation and quality gates only.
  No MOSS model/runtime was installed, no audio was uploaded, and no fallback
  route was enabled.

The corresponding source-fidelity policy, per-file decisions, CLI, tests, and
remaining GPU A/B requirement are recorded in
`docs/audio-source-fidelity-and-speaker-diarization-2026-07-28.md`.

## 2026-07-28 Isolated Upstream Executable Verification

Updated by Codex / GPT-5.6 at 2026-07-28 18:32:17 +08:00.

- **Intent:** prove which fixed upstream modules are actually reusable before
  downloading a model or changing the production ASR route.
- **Decision:** use an isolated Python 3.12.11 environment and execute the
  upstream test modules themselves. Keep the VKP adapter on the official
  `mtd-subtitle` CLI and raw `segments.json`; do not import or copy the model
  runner.
- **Reason:** the upstream package root imports the heavyweight inference stack,
  while parser/subtitle contracts are independently testable. The canonical VKP
  transcript must not silently sort, merge, split, or retime source segments.
- **Evidence:**
  - Fixed source: `%WORKSPACE_ROOT%\source-reviews\radar-intake-2026-07-18\MOSS-Transcribe-Diarize`,
    commit `eda4b9f13f1574765a80438c9797780a9bd48112`.
  - Isolated environment:
    `%WORKSPACE_ROOT%\video-knowledge-pipeline\.local\moss-runtime-py312`;
    Python `3.12.11`; upstream editable metadata and the `mtd-subtitle` entry
    point are installed.
  - Actual upstream tests for transcript parsing, SRT/ASS/JSON export, and
    subtitle postprocessing passed `18/18`.
  - Upstream `moss_transcribe_diarize/app/cli.py` calls
    `subtitle_segments_from_transcript(..., postprocess=False)` before writing
    `segments.json`. This is the contract VKP consumes.
  - VKP adds a regression proving MOSS source order, IDs, start/end boundaries,
    text, and speaker survive normalization unchanged. MOSS-focused tests pass
    `3/3`; the full `tests/test_asr_pipeline.py` passes `50/50`.
  - A planning-only run resolved the isolated CLI, selected CUDA, and reported
    `model_ready=false`. Execution then returned `asr_model_not_ready` before
    invoking inference.
  - `mtd-subtitle --help` still fails with
    `ModuleNotFoundError: transformers`; an offline full dependency install is
    currently blocked because upstream requires `transformers>=5,<6` and that
    wheel is not present in the local cache.
- **Effective scope:** executable source evidence, adapter contract, and
  fail-closed readiness only. No model was downloaded, no real audio was
  processed, no service was started, and no network, upload, or fallback was
  used.

The next real trial requires a separate operator approval to install the pinned
runtime dependencies and model, followed by one short de-identified two-speaker
GPU A/B. Acceptance metrics are speaker count, speaker confusion/DER when a
manual reference exists, segment/time preservation, source-fidelity errors,
latency, peak VRAM, and a proof that failed MOSS execution does not switch ASR
providers.

## 2026-07-28 CLI Runtime Readiness Hardening

Updated by Codex / GPT-5.6 at 2026-07-28 22:04:05 +08:00.

- **Intent:** prevent an installed console-script stub from being reported as a
  runnable diarization service when its Python runtime dependencies are broken.
- **Decision:** reuse the pinned upstream `mtd-subtitle --help` entrypoint as a
  lightweight self-test. VKP now distinguishes `entrypoint_available` from
  `runtime_probe.ready`, normalizes dependency failures, and blocks execution
  before model inspection or inference when the self-test fails.
- **Reason:** executable presence only proves packaging created a launcher. It
  does not prove imports, dependency versions, or the CLI itself are usable.
  Reporting such a launcher as `available=true` moves a deterministic setup
  error into a long-running media job.
- **Evidence:** the real isolated launcher exists but its self-test exits 1 with
  `missing_python_dependency:transformers`. A new planning-only run reports
  `entrypoint_available=true`, `runtime_probe.ready=false`, and
  `available=false`; executing that plan ends `blocked` before inference and
  records the normalized blocker. MOSS-focused regression passes `5/5`; the
  complete `tests/test_asr_pipeline.py` passes `52/52`.
- **Effective scope:** ASR capability detection, plan readiness, execution
  diagnostics, and offline tests. Existing non-MOSS presets preserve their
  prior command/module behavior. No dependency or model was installed, no
  audio was processed or uploaded, and no fallback was enabled.

Local evidence:

- Plan: `.local/moss-diarization-trial-20260728-runtime-check/transcripts/asr_run_cf9d1525898a/asr-run-plan.json`
- Execution report: `.local/moss-diarization-trial-20260728-runtime-check/transcripts/asr_run_cf9d1525898a/asr-run-report.md`

The next stage remains explicitly gated: install the fixed runtime dependencies
inside `.local/moss-runtime-py312`, obtain the model from a verified mainland-
reachable mirror without changing its identity/hash, then run one bounded GPU
A/B. The current blocker is runtime/model provisioning, not the VKP adapter
contract.

## 2026-07-29 Exact-Window A/B Front Door

Updated by Codex / GPT-5.6 at 2026-07-29 09:32:03 +08:00.

- **Intent:** compare MOSS and SenseVoice + CAM++ on the exact same bounded
  two-speaker sample, with the same normalization and production quality gates.
- **Decision:** add `moss_transcribe_diarize` to the existing
  `asr-ab-sample-plan/run/compare` matrix. The adapter does not build a MOSS
  command itself; it calls the established `plan_asr_run` and `run_asr_plan`
  front doors, then reuses normalized transcript metrics, pyannote DER and
  MeetEval cpCER/tcpCER. If more than one candidate has complete anonymous
  labels, no candidate is selected until those three metrics are compared.
- **Reason:** the upstream CLI already owns inference, parser and raw segment
  export. Reimplementing them would create a second ASR path, while selecting
  solely by `speaker_count` or labeled-segment coverage would repeat the CAM++
  false-positive quality mistake.
- **Evidence:** fixed upstream source commit
  `eda4b9f13f1574765a80438c9797780a9bd48112`; parser/export/postprocess tests
  re-executed `18/18`. All MOSS-focused VKP regression passed `12/12`; associated ASR,
  source-fidelity, DER and MeetEval suite passed `88` with `3` optional skips.
  Stable CLI preview now discovers
  `.local/moss-runtime-py312/Scripts/mtd-subtitle.exe` and accurately reports
  `missing_python_dependency:transformers`, model
  `unknown_or_not_downloaded`, and no fallback. The updated local A/B artifact
  is `.local/campp-two-speaker-trial-20260729/transcripts/asr-ab-sample/asr-ab-sample-run.json`.
- **Effective scope:** local bounded A/B planning, readiness and candidate
  comparison metadata. No dependencies or model weights were installed, no
  audio inference or upload ran, no speaker roles were inferred, and no
  transcript was promoted.

## 2026-07-28 Stable ASR Status Integration

Updated by Codex / GPT-5.6 at 2026-07-28 22:17:56 +08:00.

- **Intent:** make the stable `asr-env-status` front door report the same MOSS
  truth as planning and execution, so operators do not start a long job from a
  misleading environment screen.
- **Decision:** add the explicit MOSS challenger to the existing ASR tool
  registry, resolve its established `LECTURE_MOSS_TRANSCRIBE_COMMAND`, reuse the
  same upstream CLI self-test, and display Command / Runtime / Blocker as
  separate columns. Model cache readiness remains a separate field.
- **Reason:** launcher, import runtime, model cache, and GPU are independent
  readiness layers. Collapsing them into one command-exists flag was the source
  of the false positive.
- **Evidence:** the real stable CLI now reports `command_exists=true`,
  `runtime_ready=false`, `missing_python_dependency:transformers`, model status
  `unknown_or_not_downloaded`, excludes MOSS from `command_tools`, and includes
  it in `runtime_blocked_tools`. Focused environment/MOSS regression passes
  `8/8`.
- **Effective scope:** read-only ASR environment JSON/Markdown and tool
  readiness calculation. SenseVoice/FunASR defaults and non-MOSS command
  semantics remain unchanged. No installer, model download, inference, upload,
  network call, or fallback was added.

## 2026-07-29 Offline model-cache completeness gate

Updated by Codex / GPT-5.6 at 2026-07-29 10:06:33 +08:00.

| Field | Record |
| --- | --- |
| Intent | Stop an empty or interrupted MOSS cache from looking runnable before a long local ASR job starts. |
| Decision | Reuse installed `huggingface_hub 0.30.2` `scan_cache_dir` and add only a VKP adapter that checks the files MOSS actually loads: config, processor, tokenizer, three trusted remote-code modules, plus either one usable weight file or every shard referenced by a valid index. |
| Reason | Directory-name matching cannot distinguish a complete model from an interrupted snapshot or a Git LFS pointer. The gate must stay offline and fail closed instead of allowing a hidden download. |
| Evidence | Installed package RECORD SHA-256 `90C92D5CC14E1E9794832B140F4B5E8F33DC1055A673CEC234F5039222574F90`; implementation source inspected at `%USERPROFILE%\AppData\Local\Programs\Python\Python313\Lib\site-packages\huggingface_hub\utils\_cache_manager.py`; real scan found five cached repositories, one cache warning, no MOSS model. Four new cache-contract tests plus 12 linked MOSS tests passed; expanded speaker/source-fidelity suite passed 93 with 3 optional skips. |
| Effective scope | `_model_ready(preset="moss-transcribe-diarize", ...)` only. `huggingface_hub` remains optional; when unavailable the direct local path gate still applies and readiness stays fail-closed. No dependency/model install, download, inference, upload, fallback or transcript promotion. |

Current local status remains `unknown_or_not_downloaded`; this change does not
claim that MOSS is installed. It only makes the negative result trustworthy.

## 2026-07-31 本地 GPU A/B 实测

Acting tool/model: Codex GPT-5；timestamp: 2026-07-31 12:05:00 +08:00。

| 字段 | 记录 |
| --- | --- |
| 意图 | 在同一 300 秒、同一双人保险咨询音频、同一人工参考窗口上，实际比较 MOSS 与 SenseVoice+CAM++，而不是只验证模型能加载。 |
| 决策 | 从大陆镜像将固定 MOSS 模型下载到 VKP `.local`；GPU 离线执行。首轮命中上游 2048 token 默认上限后，不复制推理代码，改为复用 `mtd-subtitle --max-new-tokens`，VKP 默认 8192。 |
| 理由 | 2048 token 运行返回码为 0，但只覆盖到 178.44 秒，属于成功外观下的内容截断；上游已有正式参数，应优先适配而非自研生成循环。 |
| 证据 | 模型 19 文件、1,833,163,202 字节，权重 SHA-256 `9a0ceb4ab7330357db3ff583dba8d83625d5b733b00e1d55d6970e11b07026c4`。完整重跑生成 3916 token、147 段、298.84 秒、2 位匿名说话人、覆盖率 99.4378%，GPU 推理 156.51 秒。MOSS：DER 0.30926667、cpCER 0.32207207、tcpCER 0.45795796；CAM++：DER 0.24396667、cpCER 0.36036036、tcpCER 0.52852853。18 条定向回归通过。 |
| 生效范围 | MOSS command planning、固定 300 秒本地候选 A/B 和隔离评测环境。没有上传媒体，没有覆盖正式逐字稿，没有把 MOSS 或 CAM++ 提升为生产默认。 |

结论不是单一胜负：MOSS 的匿名说话人分离 DER 更差，但说话人归属文字的 cpCER/tcpCER 更好，文本相似度也略高；两条路线都未达到当前 0.05 生产质量门。剩余必需项是人工匿名听审和更多短/中/长样本稳定性验证。
