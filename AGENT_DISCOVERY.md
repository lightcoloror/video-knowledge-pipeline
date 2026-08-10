# AGENT_DISCOVERY

## Update Record
### 2026-07-30 15:19:34 +08:00 | Codex (GPT-5.6)
- Hardened long-media ASR overlap merge by reusing FunASR character timestamps to crop boundary-spanning sentences to their unique core window while preserving raw chunks and review evidence. Added explicit `--rebuild-from-checkpoint` for merge-only recovery; it reuses the exact v2 checkpoint/manifest, never runs a child model, and records source freshness as not revalidated when removable media is unavailable.
- The stratified 8-sample benchmark completed 108/108 chunks with zero long-form-loss flags; 6/7 valid reference bindings passed the 5% content-distance gate. Generated an 11-window anonymous A/B review pack through the existing quality arbitration module. Offline verification: 119 associated tests, Ruff and compileall passed; no model, network, upload or provider call occurred.

### 2026-07-29 18:20:00 +08:00 | Codex (GPT-5.6)
- Corrected the final Logseq reader projection to omit `collapsed::` by default. Speaker/timestamp parents and two-space child indentation remain unchanged, so imported transcripts open expanded and readers control collapse state themselves. The change affects only final `knowledge-note.md` rendering; canonical transcript, Timeline, evidence and audit artifacts are unchanged.

### 2026-07-29 17:40:00 +08:00 | Codex (GPT-5.6)
- Final reader artifacts now use the local `getnote-logseq-sync` Logseq block contract: `摘要 → 📑 智能总结 → sections` and `逐字稿 → speaker/time → text`, two-space child indentation, and no raw Markdown headings. Reader-only program fields are filtered while canonical Smart Summary, transcript JSON, evidence, quality and audit artifacts remain unchanged. Associated offline tests: 38/38; local Matryca validation on two production reader documents: 2/2, zero issues. No model call, upload, Logseq writeback or canonical content mutation.

### 2026-07-28 22:17:56 +08:00 | Codex (GPT-5.6)
- Integrated the pinned MOSS CLI self-test into the stable `asr-env-status` JSON/Markdown surface. The status now distinguishes command presence, runtime readiness, normalized blocker, model cache and GPU readiness; the real isolated launcher is listed as runtime-blocked rather than command-ready. Focused status/MOSS regression: 8/8 passed. No installer, dependency, model, inference, network, upload or fallback was added.
### 2026-07-28 22:04:05 +08:00 | Codex (GPT-5.6)
- Reused and verified the existing FunASR chunk runner's exact-repair semantics instead of adding another state machine: timestamp-only/empty child results remain unverified, stale per-chunk JSON is removed before an attempt, targeted repair success is separated from canonical media completeness, unresolved indexes stay explicit, and progress reports targeted success without hiding remaining gaps. Offline chunk semantics/runner verification: 8/8 passed; no ASR model, media execution, network, upload, or fallback occurred.
- Hardened the explicit MOSS diarization preset by reusing the pinned upstream `mtd-subtitle --help` entrypoint as a runtime self-test. VKP now distinguishes launcher presence from runnable dependencies, reports normalized blockers such as `missing_python_dependency:transformers`, and blocks before inference instead of misreporting `available=true`. Real planning evidence shows entrypoint present/runtime not ready/model not ready; the blocked execution performed no inference, network, upload, or fallback. Verification: MOSS-focused 5/5 and full ASR pipeline 52/52 passed.
### 2026-07-28 18:57:39 +08:00 | Codex (GPT-5.6)
- Aligned the single final reader document with the requested GetBrain-style layout by projecting the existing canonical Smart Summary into `章节概要 / 金句精选 / 待办事项`, renaming the corrected final transcript section to `逐字稿`, preserving `待复核点` and anonymous speaker labels, and hiding standalone operational metadata only in the reader projection. The implementation reuses the pinned BiliNote selectable-format architecture at commit `095d772c7d0f2f4ba1e65c36b7ceb1e2db34723d`; canonical summary/evidence/quality artifacts remain the sole truth. Offline verification: 4 reader/E2E and 2 knowledge-export tests passed; Ruff, compileall and diff check passed. No model, network, upload, or production Bundle write occurred.
### 2026-07-28 18:32:17 +08:00 | Codex (GPT-5.6)
- Re-ran the pinned MOSS-Transcribe-Diarize source at commit `eda4b9f13f1574765a80438c9797780a9bd48112` in an isolated Python 3.12 environment. Its actual parser/subtitle/export/postprocess tests passed 18/18. Source review confirms the official `mtd-subtitle` CLI writes `segments.json` with `postprocess=False`, so VKP may preserve source order, IDs, boundaries, text, and speaker instead of silently sorting or merging. VKP now has a dedicated boundary-preservation regression; MOSS-focused tests pass 3/3 and the full ASR pipeline 50/50. The CLI entry point is registered but dependencies/model remain incomplete; a planning-only execution stopped at `asr_model_not_ready` before inference. No model download, audio processing, network, upload, or fallback occurred.
### 2026-07-27 11:44:39 +08:00 | Codex (GPT-5)
- Reviewed and accepted the fixed upstream OpenMOSS MOSS-Transcribe-Diarize adapter contract at commit `eda4b9f13f1574765a80438c9797780a9bd48112`. The explicit `moss-transcribe-diarize` preset delegates to upstream `mtd-subtitle`, normalizes `segments.json` while preserving start/end/text/speaker, keeps SenseVoice as the default, and fails closed when the CLI or local model cache is unavailable; it never auto-downloads or silently falls back. Offline verification: 2 focused MOSS tests and the full ASR pipeline file 49/49 passed; compileall passed. Runtime/model installation and a real short-audio A/B remain pending.
### 2026-07-23 20:53:37 +08:00 | Codex (GPT-5)
- Corrected four VKP policy errors that contradicted the operator's configured-and-tested providers. Coding Plan is now eligible for consented VKP tasks on the exact configured route; provider capability and provider responses, not an internal task-scope label, determine the result. Doubao model names are no longer filtered; the default route and onboarding pool include configured Doubao candidates. Native whole-video tasks are unified through Gemini Files API after consent and delete the provider file after use. MediaKit is executable through the official CLI after a consent-v2 reservation; the CLI performs provider-managed local upload and an unavailable CLI reports mediakit_cli_unavailable, not a policy denial. Exact artifact hashes, destinations, consent confirmation, call/cost ceilings, expiry, no arbitrary URL/key, and no silent provider/location fallback remain enforced. Offline verification: 40 core and 125 related tests passed, plus Ruff on the new adapters; no actual model, MediaKit CLI, upload, or provider request was executed.
### 2026-07-23 10:04:30 +08:00 | Codex (GPT-5.6)
- Directly adapted the fixed OpenAI Whisper and faster-whisper word_anomaly_score / is_segment_anomaly quality heuristic. Evaluation requires complete normalized word timing plus probability/score/confidence; missing API confidence is not_evaluated, never zero. Matches become human-review and exact targeted-retry candidates only. Verification: 25 focused and 198 expanded offline tests passed; a saved 54-segment Groq response produced 0 anomaly / 54 not_evaluated and retained its prior degraded result. No model, network, upload, retry, fallback, or production artifact write was executed.
### 2026-07-23 09:40:41 +08:00 | Codex (GPT-5.6)
- Audited every SOURCE_INVENTORY entry linked to VKP instead of reopening old reuse backlogs. Reused `source-ledger.ps1` to link the existing fixed-commit `recognize-anything` evidence and content-address the installed LiteLLM 1.81.7 distribution with its RECORD SHA-256. The VKP-scoped audit now reports zero missing repo/version/path/evidence fields and the global ledger remains `error_count=0`. Source-ledger mutations were verified sequentially because concurrent writers can overwrite each other; no source download, dependency, model, network, upload, runtime, or production artifact was executed.

### 2026-07-23 09:24:00 +08:00 | Codex (GPT-5.6)
- Reused the workspace `source-ledger.ps1` validator/update front door to repair the LiteLLM source-evidence record introduced by the Groq word-timestamp adaptation. The entry now uses canonical `integration_status=local_trial` and `evidence_link_status=linked`; all three evidence documents resolve and `source-ledger validate` reports `error_count=0`. No new verifier, source clone, dependency, model call, gateway start, upload, or provider action was added.

### 2026-07-23 09:11:26 +08:00 | Codex (GPT-5.6)
- Corrected the Groq ASR timestamp route by reusing Groq's official OpenAI-compatible transcription contract and LiteLLM's existing OpenAI transport, matching the already-proven Mistral ASR pattern. Installed LiteLLM 1.81.7 and upstream stable 1.86.2 native Groq STT both omit `timestamp_granularities`; the `groq_asr` profile now hashes `asr_timestamp_granularity=word` into its route and normalizes legacy `litellm_provider=groq` to `openai`. Word-only responses reuse the existing Qwen3 aligned-word grouping. Verification: 93 focused offline tests, Ruff, AST and current-settings migration preview pass; no gateway, provider, upload or production artifact was executed.
### 2026-07-23 08:50:17 +08:00 | Codex (GPT-5.6)
- Strengthened long-ASR coverage audit by reusing the existing provider word-timestamp normalizer. Complete word evidence is preferred over coarse segment bounds only when normalized word text exactly reconstructs the segment; missing, invalid, or incomplete word timestamps explicitly fall back to segment-level coverage. This exposes internal VAD-covered gaps without creating sparse-timestamp false positives. Offline verification: 113 related tests plus Ruff, AST parsing and diff check pass; no model, provider, upload, retry, or production artifact mutation was executed.
### 2026-07-23 08:25:04 +08:00 | Codex (GPT-5.6)
- Adapted fixed MIT `ufal/whisper_streaming` `HypothesisBuffer.insert/flush` into timestamp-aware candidate evidence for ASR chunk boundary conflicts. Absolute word timestamps are cropped to the actual overlap before exact hypothesis-prefix agreement; missing word timestamps remain explicitly unavailable. No text is confirmed or changed automatically. Offline verification: 63 related tests plus Ruff and py_compile pass; no runtime, model, provider, upload, retry, or fallback was executed.

### 2026-07-23 08:15:09 +08:00 | Codex (GPT-5.6)
- Adapted the fixed MIT `ufal/SimulStreaming` LocalAgreement contract into candidate-only ASR boundary evidence. Overlapping non-identical chunk segments now report character/word common-prefix agreement and fixed upstream provenance; the score never confirms, deletes, merges, or rewrites transcript text. Offline verification: 61 related tests plus Ruff pass; no model, provider, upload, retry, or fallback was executed.

### 2026-07-23 08:03:13 +08:00 | Codex (GPT-5.6)
- Adapted fixed TransNetV2/AutoShot predictions_to_scenes saved outputs into the existing scene candidate evidence front door as candidate_shot_boundary.v1. PySceneDetect remains default; no model runtime, weight download, raw-probability thresholding, silent fallback or Timeline mutation was added. Verification: 9 focused and 32 related tests plus Ruff, py_compile and diff check pass; real filmed-footage blind comparison remains pending.

### 2026-07-23 07:52:11 +08:00 | Codex (GPT-5.6)
- Extracted two exact ASCII/CJK compaction contracts into dependency-neutral text_normalization: strict source-character filtering and lower-before-filter Unicode normalization. Five ASR/term private entrypoints remain aliases; offset-preserving, underscore-preserving and whitespace-only variants remain separate. Offline verification: 52 tests plus Ruff, py_compile, owner scan and scoped diff check pass.

### 2026-07-23 07:42:35 +08:00 | Codex (GPT-5.6)
- Completed the long-ASR overlap reuse audit. Temporal intersection duration, IoU and intersection-over-shorter now live in the existing interval_coverage owner; ASR consensus and chunk-boundary dedup retain their distinct denominators through direct reuse. Directional transcript arbitration remains separate. Offline verification: 49 tests plus Ruff, py_compile and scoped diff check pass.

### 2026-07-23 07:35:13 +08:00 | Codex (GPT-5.6)
- Reused the existing interval_coverage.merge_intervals owner for lecture evidence after adding the contract-preserving merge_nonnegative_intervals adapter: bounds are clamped to zero before shared normalization and overlap/adjacency merging. lecture_package._merge_intervals remains a compatibility alias; the offline quality router stays separate because its coverage semantics differ. Offline verification: 15 tests plus Ruff, py_compile, alias/owner scan and scoped diff check pass.

### 2026-07-23 07:30:56 +08:00 | Codex (GPT-5.6)
- Extracted the byte-identical closed-interval overlap rule from Smart Summary chapters and transcript semantic summary impact into the existing `interval_coverage.closed_intervals_overlap` owner. Their private `_overlaps` names remain aliases; half-open and special-start overlap contracts remain separate. Offline verification: 100 tests plus Ruff, py_compile, unique-owner guard and scoped diff check pass.
### 2026-07-23 07:26:42 +08:00 | Codex (GPT-5.6)
- Completed the shared UTC consent timestamp parser: business authorization, model consent v2 and vision export consent now alias `time_utils.parse_utc_datetime_or_none`, preserving Z/offset parsing, naive-as-UTC behavior, invalid-value failure and UTC normalization. Offline verification: 38 tests plus Ruff, py_compile, single-owner guard and scoped diff check pass.
### 2026-07-23 07:21:21 +08:00 | Codex (GPT-5.6)
- Added a candidate-only independent VAD route by directly adapting the installed MIT `faster-whisper` 1.1.1 `decode_audio`, `VadOptions` and `get_speech_timestamps` APIs. Its bundled Silero v5 ONNX assets are content-addressed, no model download is allowed, and cross-check results can only create targeted-ASR/human-review candidates; they never modify FunASR VAD, chunk manifests or canonical transcripts. Offline regression: 47 passed; a real local 3.59-second smoke completed without network or writes.
### 2026-07-23 07:03:55 +08:00 | Codex (GPT-5.6)
- Extracted the existing UTC whole-second ISO timestamp contract into `time_utils.utc_now_iso_seconds` and migrated six batch/route/authorization/consent sites. Local naive timestamps and aware datetime arithmetic remain distinct. Offline verification: 50 tests plus Ruff/import and unique-owner guards pass.

### 2026-07-23 07:00:26 +08:00 | Codex (GPT-5.6)
- Completed atomic replacement reuse: LiteLLM YAML now uses `storage.write_text_atomic`; legacy settings rollback and stage-cache binary copy share `storage.replace_file_with_retry` while retaining distinct byte preparation. `os.replace` now has one source owner. Offline verification: 45 tests plus Ruff/import guards pass.

### 2026-07-23 06:55:20 +08:00 | Codex (GPT-5.6)
- Completed the deferred PowerShell argument audit: ASR and lecture private quoting entrypoints now alias the existing `powershell.quote_powershell_argument` owner, whose metacharacter set combines both established contracts. Command snapshots and 56 offline tests pass; the AST guard now permits one escaping owner.

### 2026-07-23 06:46:51 +08:00 | Codex (GPT-5.6)
- Extracted 17 byte-identical Markdown table-cell renderers into `markdown_text.markdown_table_cell` while preserving every private entrypoint as an alias. Different truncation, `<br>`, arbitrary-object and slash-replacement contracts remain separate. Offline verification: 98 related tests, shared-owner Ruff, import ordering, compileall, unique-owner scan and diff check pass.

### 2026-07-23 06:39:35 +08:00 | Codex (GPT-5.6)
- Extracted the identical lecture/review local-file URI wrappers into `path_utils.file_uri_or_empty`, preserving their private aliases and stdlib `Path.as_uri` behavior. Bundle-path resolvers remain separate because their allowed-root, resolve and failure contracts differ; timestamp display already shares `transcript.format_timestamp`.

### 2026-07-23 06:34:12 +08:00 | Codex (GPT-5.6)
- Promoted the existing fail-closed optional JSON-object reader from `batch_repair` into `storage.read_json_object_or_empty`. Ten private entrypoints remain compatibility aliases and VideoRAG reuses the same owner; strict, BOM, list and nullable readers remain separate. Offline verification: 79 related tests, focused Ruff, compileall, alias/AST guard and diff check pass.

### 2026-07-23 06:26:14 +08:00 | Codex (GPT-5.6)
- Reused the existing `powershell.py` owner for the byte-identical lecture/extractor subprocess contract. Both front doors keep `_run_command` compatibility aliases while sharing one runner; 11 offline tests, focused Ruff, compileall, owner guard and diff check pass without executing PowerShell.

### 2026-07-23 06:20:13 +08:00 | Codex (GPT-5.6)
- Extracted the established `artifact_freshness.canonical_json_sha256` compact sorted JSON contract into dependency-neutral `canonical_json.py`. Fourteen modules now share the owner for consent, route revision, provider contracts, ASR workflow identity, page metadata and scene evidence; 124 related tests, focused Ruff, compileall, direct-implementation guard and diff check pass.

### 2026-07-23 06:03:52 +08:00 | Codex (GPT-5.6)
- Extracted the existing repository PowerShell single-quoted literal and conditional argument renderers into dependency-neutral `powershell.py`; 31 modules now share the owner through 32 compatibility aliases. Two intentionally different minimal argument renderers remain deferred for contract review. Offline verification: 134 related tests passed; focused Ruff, compileall, AST reuse guard and scoped diff check passed.

### 2026-07-23 05:52:23 +08:00 | Codex (GPT-5.6)
- Extracted the existing stdlib `hashlib` streaming file digest from `video.sha256_file` into dependency-neutral `file_hash.sha256_file`, kept the video compatibility re-export, and routed 33 source modules through the single owner. Full-file `read_bytes` hashing was removed from production source; 206 related tests, Ruff, compileall, source reuse guard and diff check pass.

### 2026-07-23 05:37:40 +08:00 | Codex (GPT-5.6)
- Reused the shared vsummary-based balanced JSON parser for subprocess stdout and extracted the existing Coding Plan terminal-object selection into `model_json.extract_last_json_document`. Coding Plan, OpenClaw integration and video-source wrappers now share one owner while preserving their return contracts; 48 related tests, Ruff, compileall, unique-owner scan and diff check pass.

### 2026-07-23 05:26:18 +08:00 | Codex (GPT-5.6)
- Extracted the existing `alpha03123/vsummary` JSON-mode adaptation into dependency-neutral `model_json.py` and reused it from text, vision and Coding Plan result parsing. The old text-gateway import remains compatible; 76 related tests, Ruff, compileall, unique-owner scan and diff check pass.

### 2026-07-23 05:16:36 +08:00 | Codex (GPT-5.6)
- Routed the remaining Dolphin, FunASR VAD, punctuation, local-VLM, route-config and VideoRAG JSON/text artifact writes through the existing atomic `storage.write_json` / `write_text_atomic` owner. Source scanning now finds no `Path.write_text(json.dumps(...))`; focused regression: 23 passed, with Ruff, compileall and diff check passing.

### 2026-07-23 05:07:24 +08:00 | Codex (GPT-5.6)
- Expanded the Ruff `TID251` reuse guard from one `urlopen` call to the full direct-client surface used or likely to be introduced: `urllib.request`, `http.client`, `requests`, `httpx` and `urllib3`. Existing compatibility and loopback-test exceptions remain explicit per file; five negative probes were rejected and the current tree passes.

### 2026-07-23 05:00:11 +08:00 | Codex (GPT-5.6)
- Added a Ruff `TID251` banned-API guard so new modules cannot add direct `urllib.request.urlopen` provider calls. Existing reviewed compatibility and loopback-test exceptions are explicit per file; the full current tree passes and an unlisted negative probe is rejected.

### 2026-07-23 04:55:20 +08:00 | Codex (GPT-5.6)
- Routed FunASR, faster-whisper and Qwen3 ForcedAligner raw JSON artifacts through the existing atomic `storage.write_json` owner while retaining their upstream SDKs and module CLI contracts. Offline regression: 60 passed; Ruff and compileall passed.

### 2026-07-23 04:48:47 +08:00 | Codex (GPT-5.6)
- Routed `stage_cache.atomic_write_text` through the existing `storage.write_text_atomic` owner, removing the duplicate text replacement implementation while retaining the stage-cache API. Offline focused regression: 4 passed; Ruff and compileall passed.

### 2026-07-23 04:44:21 +08:00 | Codex (GPT-5.6)
- Consolidated seven ASR/authorization file-hash copies onto the existing `video.sha256_file` owner. Contracts and artifact identities are unchanged; focused offline regression: 52 passed; Ruff and compileall passed.

### 2026-07-23 04:34:42 +08:00 | Codex (GPT-5.6)
- Removed the implicit embedded-LiteLLM-to-urllib fallback when no legacy backend is specified. V2 profiles still default to LiteLLM Proxy, migrated V1 profiles remain explicit legacy, and only explicit `adapter_backend=auto` retains auditable same-route fallback. Offline focused regression: 55 passed; Ruff and compileall passed.

### 2026-07-23 04:10:02 +08:00 | Codex (GPT-5.6)
- Added a reusable no-write business-child batch preflight before ASR chunk consent creation. It composes the existing exact child preview and capacity checker on an in-memory parent shadow, so aggregate call/cost/file/byte failures occur before the first consent is written. Offline combined regression: 43 passed.
### 2026-07-23 03:57:04 +08:00 | Codex (GPT-5.6)
- Added one-command ASR chunk consent preparation from an existing confirmed business authorization. It reuses exact child consent v2, the existing Broker workflow compiler, and the existing Bundle run registry; repeated identical preparation is idempotent even after the parent allowance is fully allocated. Offline focused regression: 42 passed.

### 2026-07-21 22:28:57 | Codex (GPT-5.6)
- Completed the phase-1 reuse audit: provider throttling is delegated to LiteLLM Router, DAG/workers/gates use Python standard-library primitives, and persistence/operations reuse VKP storage, Bundle run registry, and Task Console. No custom AIMD, token bucket, adaptive limiter, second state machine, API call, upload, or push remains in this checkpoint. Full offline regression excluding two pre-existing dirty visual-triage failures: `1032 passed, 2 deselected, 1 warning`.

### 2026-07-21 22:03:35 | Codex (GPT-5.6)
- Added named consent workflow submission on top of the existing graphlib batch engine, Bundle/run-registry binding, and a redacted Task Console batch/allowance panel. Provider throttling remains LiteLLM-owned; no new state machine, retry, fallback, API call, upload, or push was added. Focused offline regression: `61 passed`.


### 2026-07-21 09:35:00 | Codex (GPT-5.6)
- Added local-only `shot-breakdown` CLI/MCP and Workbench artifacts for field-provenanced shot facts, style fingerprints, imitation-script candidates, and human-review readiness. Fixed-commit source review is registered for nine projects; offline verification: `984 passed, 1 warning`. No model, network, upload, Timeline mutation, generation, publication, or push occurred.

### 2026-07-20 23:09:40 +08:00 | Codex (GPT-5)
- Transcript semantic acceptance now fails closed unless the canonical transcript hash matches `full-transcript.md`, `knowledge-note.md`, and the Smart Summary input pack. Semantic closure refreshes this proof automatically, and the repair queue exposes only a local export-refresh action while hashes are stale. Focused regression: 78 passed; full offline regression: 966 passed, 8 dependency warnings. The existing production bundle now reports 2 accepted human decisions, 0 review-required items, and canonical integrity passed.

### 2026-07-20 22:39:23 +08:00 | Codex (GPT-5)
- Added a local-only degraded recovery path for saved secondary ASR responses that contain complete text but no provider timestamps. It keeps the ASR quality gate failed, projects text monotonically onto primary segment boundaries only as `timing_inferred` candidate evidence, creates isolated consensus/adjudication artifacts, and never patches or promotes the canonical transcript. The authorized Mistral result produced 54 inferred candidates, 8 differences in 5 clusters, and zero applied patches; canonical SHA-256 remained unchanged. Focused regression: 49 passed; full offline regression: 965 passed, 1 warning; no additional provider call or upload was made.

### 2026-07-20 22:02:41 +08:00 | Codex (GPT-5)
- Executed the single operator-authorized Mistral `voxtral-mini-2602` secondary-ASR call through the Trusted Broker and Secure MCP Tunnel: one call, zero retries, no fallback. Transport returned a complete Chinese transcript, but Mistral returned no segments because the request omitted segment timestamp granularity, so the quality gate correctly rejected it and the canonical transcript SHA-256 remained unchanged. The runtime now requests `timestamp_granularities[]=segment`; an explicit Broker `ModelSettingsPath` now drives both allowlisting and route resolution. Default Broker and LiteLLM services were restored. No verification rerun was authorized.

### 2026-07-20 21:02:35 | Codex (GPT-5)
- Added `asr-secondary-evidence` as the stable local-only closure for one saved secondary ASR connector execution. It verifies the prepared route, provider, model, destination, runtime identity, and exact upload manifest before reusing the ASR quality gate, transcript normalization, consensus, anonymous adjudication, and run registry. It never calls a provider, applies a patch, or promotes the secondary transcript; canonical SHA-256 must remain unchanged.

### 2026-07-20 08:27:41 | Codex (GPT-5)
- Hardened online transcript semantic correction end to end. Consent creation now recognizes `transcript_semantic_correction_pack.v1` artifacts and locks one canonical strict instruction plus per-decision array schema; every decision must explicitly provide action, exact original text, confidence, rationale, evidence IDs, and review flags. The Trusted Connector now runs the same task-specific deep validator before setting `production_qualified`, including candidate ID, exact original-text binding, evidence subset, duplicate ID, confidence, and risk checks. Existing consent files remain immutable and are not upgraded in place; create a new consent to use the stricter contract. Offline verification: `901 passed, 1 warning`; no provider call or upload was made.

### 2026-07-18 22:48:45 | Codex (GPT-5)
- Restored the production online-only model path with preset `online-production-existing-apis-v1`. Eight online task routes are ready on six single-deployment pools; Coding Plan is excluded from VKP content routes. LiteLLM now uses registered loopback port 18776 outside the host dynamic client range 1024-15000; Broker 8766 and gateway 18776 passed local health checks without any provider call or upload. Use the repository wrappers `.\scripts\video-knowledge-model-gateway.ps1` and `.\scripts\video-knowledge-model-smoke-readiness.ps1`. The fixed six-group readiness report is at the bundle's `exports/model-gateway-acceptance/model-gateway-smoke-readiness.json` and stops at `operator_consent_required` (routes 8/8, consents 0/4, temporal 6/6). Full offline regression: `869 passed, 1 warning`.
### 2026-07-18 16:55:00 | Codex (GPT-5)
- Completed the `capability_ceiling_v1` Ark/SiliconFlow ten-candidate run with one request per candidate, no retry and no fallback: 8 content successes and 2 terminal failures. Trusted Broker now dispatches this explicitly authorized benchmark asynchronously through one serial queue per remote destination, allowing different destinations to run concurrently without making same-provider reservations concurrent. The native SSE reader enforces a true total wall-clock timeout, and the stable parity wrapper exposes conservative interrupted-attempt reconciliation. Final machine evidence is `.local/coding-plan-siliconflow-capability-ceiling-20260718/parity-comparison.json`; human findings are recorded in `docs/coding-plan-siliconflow-native-parity-2026-07-18.md`.

### 2026-07-18 14:05:45 | Codex (GPT-5)
- Superseded the unexecuted 16,384-token content-quality plan with `capability_ceiling_v1` for natural provider completion. The request omits `max_tokens` and all vendor thinking-budget/toggle fields, streams until provider stop, and uses 900 seconds only as an unresponsive-connection guard. Call count, no-retry/no-fallback, exact artifact, destinations and a consent-only cost ceiling remain safety boundaries. The offline authoritative plan is `.local/coding-plan-siliconflow-capability-ceiling-20260718/parity-plan.json`.

### 2026-07-18 13:50:41 | Codex (GPT-5)
- Added the independent `content_quality_v1` request profile for the Ark Coding Plan/SiliconFlow five-pair suite. It locks `max_tokens=16384`, streaming, a 300-second timeout, and the common request fields into a new route revision; old consent cannot match. It deliberately omits unverified vendor-specific thinking fields and requires a new exact operator authorization before any remote call. The offline plan is `.local/coding-plan-siliconflow-content-quality-20260718/parity-plan.json`.

### 2026-07-18 13:24:00 | Codex (GPT-5)
- Added a narrow Secure MCP Broker entrypoint for the fixed native Ark Coding Plan/SiliconFlow parity suite. It recovers the exact plan, candidate and consent index from the consent path and accepts no provider/model/URL/key overrides. The ten authorized calls completed with no retries or fallback; the final offline report is `.local/coding-plan-siliconflow-native-parity-20260718/parity-comparison.json` and the committed interpretation is `docs/coding-plan-siliconflow-native-parity-2026-07-18.md`.

### 2026-07-18 11:55:00 | Codex (GPT-5)
- Switched the five-pair Ark Coding Plan/SiliconFlow parity front door to VKP's native OpenAI-compatible client. OpenClaw is no longer a runtime dependency; the native client sends one exact-model request with no redirect/retry/fallback/tool surface and derives comparison hashes without copying model content into the aggregate report.

### 2026-07-17 17:20:00 | Codex (GPT-5)
- Added the offline candidate benchmark CLI for strict same-artifact and same-instruction comparison of saved connector evidence.


### 2026-07-16 17:45:40 | Codex (GPT-5)
- Added `model-api-onboarding-prepare` as the stable offline front door for preparing all exact online-model profile bundles without reading/writing API keys, networking, changing routes, or granting consent.

### 2026-07-16 16:50:49 | Codex (GPT-5)
- Added exact Groq Qwen 3.6 / Whisper Turbo presets and a six-profile Ark no-Doubao text bundle (DeepSeek, MiniMax, GLM, Kimi). Active defaults no longer silently select a Doubao model.

### 2026-07-16 15:47:26 | Codex (GPT-5)
- Updated the ModelScope key-once bundle to the reviewed API-Inference Model-Id `ZhipuAI/GLM-5.2`; the DeepSeek preset remains `deepseek-ai/DeepSeek-V4-Pro`.


### 2026-07-16 15:33:43 | Codex (GPT-5)
- Unified Gemini runtime defaults, provider presets, onboarding, and operator examples on the stable `gemini-3.5-flash` model while retaining explicit older model compatibility.


## Tool

- Name: `video-knowledge-pipeline`
- Path: `%WORKSPACE_ROOT%\video-knowledge-pipeline`
- Purpose: 视频视觉理解优先的知识类视频全量转知识库流程。

## Preferred Interfaces

1. MCP

```powershell
python -m video_knowledge_pipeline.mcp_server
```

2. CLI

```powershell
python -m video_knowledge_pipeline.cli --help
python -m video_knowledge_pipeline.cli config-status
```

3. OpenClaw HTTP bridge

```powershell
.\scripts\start-openclaw-http.cmd
```

4. Static WebUI artifacts

## Offline Candidate Suite Preparation CLI

Prepare one isolated settings bundle per fixed-sample candidate without reading credentials, calling a model, uploading artifacts, registering the requested port, or changing default routes:

    video-knowledge-model-candidate-suite <plan.json> --settings-path <model-api-settings.json> --output-dir <prepared-dir>

The generated suite remains ready_for_operator_consent. Each real remote execution still requires its own existing connector consent and gateway checks.

After the prepared port is already registered to VKP LiteLLM Proxy, the operator-only sequential runner creates one consent per candidate, starts only the candidate gateway, executes one call, and stops only the PID it created:

    .\scripts\run-model-candidate-fixed-suite.ps1 -PreparedSuite <prepared-suite.json> -Execute

The runner is preview-only without -Execute. It refuses unregistered ports and refuses to stop an unknown listener.

## Offline Candidate Comparison CLI

Compare saved real-execution reports without calling a model or copying model content into the aggregate report:

    video-knowledge-model-candidate-benchmark <manifest.json> --output-dir <report-dir>

The comparator requires exact matching artifact-manifest and instruction hashes before a case is marked comparable. Exit code `0` means every case is ready for human review; exit code `2` means at least one case still needs a fixed-sample rerun. It never changes the default task route.

## Ark Coding Plan / SiliconFlow Same-Model Parity

Prepare the five-pair, ten-candidate native OpenAI-compatible comparison offline:

    .\scripts\run-coding-provider-parity.ps1 -Action prepare -OutputDir <output-dir>

For complete final-answer content pairing after the small-budget parity pass, prepare a distinct route and authorization request:

    .\scripts\run-coding-provider-parity.ps1 -Action prepare -RequestProfile content_quality_v1 -OutputDir <output-dir>

For natural provider capability pairing without a VKP output-token or thinking budget, use the newer authoritative profile:

    .\scripts\run-coding-provider-parity.ps1 -Action prepare -RequestProfile capability_ceiling_v1 -OutputDir <output-dir>

Preparation validates the exact saved model IDs and credential references without decrypting credentials, calling providers, creating consent, or uploading the fixed artifact. After the operator accepts the exact generated upload manifest, create candidate-specific consent files:

    .\scripts\run-coding-provider-parity.ps1 -Action create-consents -PlanPath <parity-plan.json> -ConfirmDataExport

Execute all exact candidates sequentially with crash-safe progress, or execute one candidate for diagnosis, then compare saved results offline:

    .\scripts\run-coding-provider-parity.ps1 -Action execute-all -PlanPath <parity-plan.json> -ConsentIndexPath <consent-index.json> -OperatorConfirmNetwork
    .\scripts\run-coding-provider-parity.ps1 -Action execute -PlanPath <parity-plan.json> -ConsentIndexPath <consent-index.json> -CandidateId <candidate-id> -OperatorConfirmNetwork
    .\scripts\run-coding-provider-parity.ps1 -Action compare -PlanPath <parity-plan.json>

`execute-all` writes `batch-execution.json` after every candidate, reuses exact existing results without a second call, and continues independent candidates after provider failures. This front door is limited to the fixed AI-coding benchmark. It reuses `text_llm_gateway` request construction and sends one direct HTTPS request per candidate; there is no Agent/tool runtime, redirect retry, SDK retry, or fallback. Ark remains locked to the official Coding Plan `/api/coding/v3/chat/completions` path and is never silently substituted with standard `/api/v3`; SiliconFlow remains locked to `/v1/chat/completions`. Provider-specific thinking fields are omitted on both sides. No provider/model/URL/fallback override is accepted at execution time. The official Coding Plan article demonstrates coding clients such as OpenClaw; VKP follows its OpenAI-compatible URL/field contract but does not claim the native client is a separately listed product integration. Details: `docs/coding-plan-siliconflow-native-parity-2026-07-18.md`.

## Stable Consent Execution CLI

Cross-repository callers must use the stable wrapper instead of private Python imports:

```powershell
.\scripts\video-knowledge.ps1 execute-consented-model-task `
  D:\path\to\model-connector-consent.json `
  --route-revision <exact-route-revision> `
  --write
```

The command accepts no provider URL, model, API key, or fallback override. VKP revalidates consent v2, exact upload hashes, current route revision, destination allowlist, atomic call/cost reservation, catalog/secret resolution, and execution audit. JSON is always written to stdout for handled results. Exit codes: `0` completed, `1` provider/execution failure, `2` consent/route/policy blocked, `3` invalid input. Use exactly one of `--write` or `--no-write`; production handoffs should use `--write` so `connector-execution.json` is persisted. No local/remote or cross-remote fallback is implied.

## Stable Consent Workflow Batch

For already-created consent v2 files whose exact artifacts are ready, submit named production nodes through the Trusted Broker MCP:

```json
{
  "bundle_dir": "D:\\path\\to\\webui-bundle",
  "nodes": [
    {"id": "ocr-0001", "consent_path": "D:\\path\\ocr-consent.json", "depends_on": []},
    {"id": "semantic-frame-0001", "consent_path": "D:\\path\\vision-consent.json", "depends_on": []},
    {"id": "summary-section-01", "consent_path": "D:\\path\\summary-consent.json", "depends_on": ["ocr-0001", "semantic-frame-0001"]}
  ],
  "write": true,
  "max_parallel_global": 4,
  "max_parallel_per_destination": 2
}
```

Use MCP `submit_consented_model_workflow_tool`, then poll `consented_model_batch_status_tool`. The named-node front door only maps IDs onto the existing `TopologicalSorter` DAG and `ThreadPoolExecutor`; it does not create another scheduler or state store. The Bundle must already contain `manifest.json` and `timeline.json`. A downstream consent whose input pack is created from upstream outputs must still be created and explicitly confirmed after that pack exists; the workflow tool cannot bypass that consent boundary.


Open the generated `webui-bundle\task-console.html` as the lightweight operation console. It includes a vsummary/BiliNote-style “处理队列” plus the run/artifact registry “任务历史” panel for batch status, failures, reports, next actions, and retry commands. Use `subqueue-action-plan` / MCP `subqueue_action_plan` when an agent needs the same queue as JSON: each row includes `action_status`, `action_kind`, `priority`, `primary_command`, `blocked_reason`, `machine_action_available`, and `operator_review_required`; `primary_command` prefers failed-item action commands such as tile recovery, ebook retry, review import, or section apply before falling back to run-level retry, while remaining read-only. Keep `webui-bundle\review.html` as the detailed timeline/review workspace.
For a unified static operator surface, run `export-video-workbench <webui-bundle>` / MCP `export_video_workbench` and open `webui-bundle\video-workbench.html`; it links task console, review, transcript editor, smart-summary section editor, timeline rows, content-candidate-pack, candidate Citation Digest filters, human-sample-eval quality filters, external reuse capability status, and local video seeking without executing cloud/model work. The external reuse panel groups VTimeLLM-style time localization, MovieChat-style long-video memory, VideoRAG local retrieval, local VLM adapter smoke, and content capability pack runs into ready/action_required/missing status with artifact links and retry commands. The workbench also embeds the same `subqueue_action_plan` semantics as task console, so agents can read next-step `action_kind`, `primary_command`, `blocked_reason`, `machine_action_available`, and `operator_review_required` from `video-workbench.json` without parsing HTML.

## Key MCP Tools

- `acceptance_run_tool`
- `acceptance_bundle_run_tool`
- `batch_video_knowledge_run_tool`
- `bundle_next_action_tool`
- `bundle_advance_tool`
- `bundle_advance_queue_tool`
- `bundle_advance_log_tool`
- `controlled_execution_check_tool`
- `prepare_local_video_run_tool`
- `run_video_frame_router_tool`
- `run_multimodal_frame_analysis_tool`
- `run_temporal_frame_groups_tool`
- `run_temporal_visual_analysis_tool`
- `vision_execution_preflight_tool`
- `vision_analysis_run_log_tool`
- `vision_analysis_restore_plan_tool`
- `vision_analysis_apply_restore_tool`
- `acceptance_check`
- `openclaw_bridge_status`
- `openclaw_bridge_doctor`
- `openclaw_live_smoke`
- `openclaw_docker_contract_check`
- `openclaw_video_plan`
- `openclaw_video_ingest`
- `openclaw_video_link`
- `openclaw_video_from_vdo_handoff`
- `openclaw_video_ingest_vdo_handoff`
- `content_asset_status`
- `batch_content_asset_status`
- `content_handoff_pack`
- `vision_provider_smoke`
- `vision_provider_matrix`
- `prepare_review_session`
- `validate_review_notes`
- `apply_review_notes`
- `run_visual_structure_tool`
- `run_ocr_backfill_tool` (fallback OCR import/CaptiOCR/Tesseract; primary screenshot OCR/layout path is `run_visual_structure_tool` -> `ebook_markdown_pipeline`)
- `run_screen_text_recovery_tool`
- `config_status`
- `asr_env_status`
- `plan_asr`
- `plan_cloud_asr` / `plan_cloud_asr_tool`
- `run_cloud_asr_plan` / `run_cloud_asr_plan_tool`
- `plan_whisperx_alignment_tool`
- `run_whisperx_alignment`
- `asr_ab_sample_plan` / `asr_ab_sample_run`
- `run_asr_plan_tool`
- `asr_smoke_tool`
- `test_vision_provider_tool`
- `local_vlm_adapter_plan_tool`
- `export_knowledge_note_tool`
- `export_task_console` / `export_task_console_tool`
- `video_moment_index` / `video_moment_index_tool`
- `long_video_memory_pack` / `long_video_memory_pack_tool`
- `video_rag_pack` / `video_rag_pack_tool`
- `external_capability_pack` / `external_capability_pack_tool`
- `run_artifact_registry` / `run_artifact_registry_tool`
- `transcript_source_arbitration` / `transcript_source_arbitration_tool`
- `term_arbitration_codex` / `term_arbitration_codex_tool`
- `validate_term_arbitration_codex_result` / `validate_term_arbitration_codex_result_tool`
- `term_correction_status` / `term_correction_status_tool`
- `term_correction_impact_report` / `term_correction_impact_report_tool`
- `term_correction_closure` / `term_correction_closure_tool`
- `online_model_api` / `online_model_api_tool`
- `online_model_api_matrix` / `online_model_api_matrix_tool`
- `submit_consented_model_batch_tool`
- `submit_consented_model_workflow_tool`
- `consented_model_batch_status_tool`

## Environment

- Unified config source: `%WORKSPACE_ROOT%\video-knowledge-pipeline\config\video-knowledge-pipeline.json`.
- CLI, MCP, generated manifests, reports, and tests read service ports through `video_knowledge_pipeline.config`.
- OpenClaw HTTP bridge defaults are `services.openclaw_http`, currently exposed for host agents as `http://127.0.0.1:8931/call` and Docker agents as `http://host.docker.internal:8931/call`.
- State contract: openclaw-bridge-status reports configured, listening, healthy, and pipeline_offline_ready separately. Configured does not mean online. A stopped bridge blocks HTTP calls but local CLI offline-quality-route remains available. The status command never starts the bridge.
- `config-status` returns `config_path`, parsed `service_urls`, `vision_execution`, and `validation`; use it instead of guessing URLs, copying ports, or hard-coding vision batch defaults.
- For temporary experiments, set `VIDEO_KNOWLEDGE_PIPELINE_CONFIG` to another JSON file. Do not copy service ports into desktop shortcuts or wrapper scripts.
- Vision execution defaults live in `vision_execution` and are non-secret only: provider, model, `multimodal_limit`, `temporal_limit`, and `frame_count`. Explicit CLI/MCP args override the config.
- `acceptance-run`, `acceptance-bundle-run`, `vision-acceptance-plan`, `bundle-advance`, and `bundle-advance-queue` all read this same profile when limits/provider are not explicitly passed.
- Direct vision tools (`run-multimodal-frame-analysis`, `run-temporal-frame-groups`, `run-temporal-visual-analysis`, `test-vision-provider`) also use `vision_execution` as their provider/model/limit/frame-count default when no explicit provider config, limit, frame count, or vision env override is supplied. Pass `limit=0` only when you intentionally want all candidates.
- Local ASR: use `scripts\install-local-asr-env.ps1`.
- Local ASR readiness: run `asr-env-status --output-dir <dir> --write`; it reports Python/package/command/ffmpeg/model-cache/CPU/CUDA readiness and writes a reusable `asr-env.ps1`.
- Local ASR smoke: run `asr-smoke <media>` for a short local SenseVoice/FunASR smoke. Use `--no-execute` only when you want a preview report. Audio stays local.
- Local ASR execution: SenseVoice/FunASR returns `asr_model_not_ready` when the model cache is not ready. Set `LECTURE_ASR_ALLOW_MODEL_DOWNLOAD=1` only when you intentionally want first-run model download.
- Cloud ASR optional branch: use `prepare-cloud-asr-audio` to create a local 16 kHz mono speech MP3 candidate (preview by default; `--execute` runs only FFmpeg and never uploads), then use `plan-cloud-asr` / MCP `plan_cloud_asr` to create a no-upload plan; only `run-cloud-asr-plan --execute` / MCP `run_cloud_asr_plan(execute=true)` uploads audio through `online-model-api asr`. A lower-bitrate candidate must pass same-media provider A/B before becoming the default. Use cloud ASR as a quality branch, not as an implicit fallback.
- WhisperX alignment: use `plan-whisperx-alignment` / `plan_whisperx_alignment_tool` to preview, then `run-whisperx-alignment` / `run_whisperx_alignment(execute=true)` only when the primary ASR transcript needs word-level timestamps or diarization enhancement. WhisperX output is alignment evidence and must not replace SenseVoice/FunASR or corrected-transcript.json automatically. Use `asr-ab-sample-plan` / `asr-ab-sample-run` for bounded 5-minute ASR comparisons; the A/B matrix now includes SenseVoice basic/full-punc, Dolphin, WhisperX alignment, and optional cloud ASR. Use `asr-ab-compare --reference-transcript <path> --start-seconds <s> --end-seconds <e>` only for evaluation-only scoring; reference transcripts are never imported as correction evidence. `asr-ab-compare` also writes per-variant blocker details, so Dolphin/WhisperX must stay optional until their blockers are closed on the same fixed sample. Cloud ASR uploads only when explicitly enabled for the sample.
- Transcript quality benchmarking: use `transcript-candidate-recall-benchmark <webui-bundle>` / MCP `transcript_candidate_recall_benchmark` to compare a fixed sample against an evaluation-only reference transcript and report ASR variant similarity plus semantic-correction candidate recall. The reference transcript must remain `evaluation_only_not_correction_evidence`; this tool does not import it into source arbitration, does not apply corrections, and does not call cloud models. It writes `transcript-candidate-recall-benchmark.json/md` and is intended to answer whether the current pipeline missed ASR error candidates before changing ASR/model defaults.
- Local ASR device policy: GPU-first by default. If `LECTURE_ASR_DEVICE` is unset, VKP probes the local ASR Python environment and uses `cuda` when available, otherwise `cpu`; set `LECTURE_ASR_DEVICE=cpu` only when intentionally forcing CPU fallback.
- Gemini vision: set `LECTURE_VISION_PROVIDER=gemini` and `GEMINI_API_KEY`.
- OpenAI-compatible vision: set `LECTURE_VISION_PROVIDER=openai_compatible` and `OPENAI_API_KEY` or `LECTURE_VISION_API_KEY`.
- Agnes profile: set `LECTURE_VISION_PROVIDER=agnes` and `AGNES_API_KEY` for experimental OpenAI-compatible testing.
- Volcengine route: Coding Plan `/api/coding/v3` is eligible for explicitly consented VKP tasks. Use the selected configured route without silent substitution; Coding Plan and standard Ark `/api/v3` remain separate credentials/endpoints. The exact provider/model/capability response determines whether a request succeeds, while route revision, allowlist, consent v2, artifact hashes and call/cost limits remain mandatory.
- Unified online model API: new production profiles use LiteLLM Proxy (`pip install -e .[online]`); built-in OpenAI-compatible/Gemini adapters remain explicit legacy compatibility routes and are never automatic fallback. Use CLI `online-model-api-matrix` / MCP `online_model_api_matrix` to inspect all online model interfaces. Real remote execution must use the Trusted Broker consent-v2 surface; preview remains the default. Supported `model_type`: `asr`, `ocr`, `document_visual`, `semantic_frame`, `temporal_sequence`, `video_segment`, `text_llm`, `summary_rewrite`, `transcript_correction`.
- MediaKit capability API: use `media-capability-status` / `media-route-status` or Trusted Broker `model_connector_capabilities` to inspect the fixed `mediakit_async_v1` catalog and content-addressed routes. `media_connector_preflight_tool` validates saved consent v2, exact route revision, fixed control-plane destination, artifact manifest, call/cost limits, and credential readiness without network calls. After a successful reservation, `execute_consented_model_task` invokes the installed official MediaKit CLI, which performs provider-managed upload only for the explicitly consented local artifacts. Missing CLI is reported as `mediakit_cli_unavailable`; arbitrary URLs, unlisted uploads, silent fallback and automatic egress remain prohibited.
- Hybrid model gateway control plane: use `.\scripts\video-knowledge-model-gateway.ps1 render-config|doctor|status|start|import-legacy`; `start` and `import-legacy` are preview-only unless `--execute` is explicitly supplied. `import-legacy --bundle-dir <webui-bundle>` only accepts sources under the project root, imports into an empty or exactly matching v2 target, stores selected credentials with Windows DPAPI, and never imports old consent as authorization. The gateway is accepted only when the exact configured port is registered to `VKP LiteLLM Proxy`, the loopback bind/listener check passes, and any live listener answers the LiteLLM health probe.
- Model Provider Catalog: settings status and Secure Broker `model_connector_capabilities` expose `video_knowledge_pipeline.model_provider_catalog.v1`, its revision, capability-indexed profile ids, and the explicit `litellm_native` extension. Preconfigured profiles lock their LiteLLM prefix; prefix, Base URL, model and capability changes alter route revision and invalidate old consent. See `docs/online-model-provider-catalog-2026-07-15.md`.
- Hybrid smoke readiness: use `.\scripts\video-knowledge-model-smoke-readiness.ps1 <webui-bundle> --indexes 6,80,112,135,199,201`. Add `--online-only` to audit the eight production online task routes without requiring local VLM/Speaches. The default hybrid mode audits the six required local/remote routes, allowlists, DPAPI credential presence, gateway health, four route-revision consents, the fixed temporal manifest, and A/B/C lane files. It never starts a service, calls a model, uploads artifacts, creates consent, or writes the port registry.
- Remote model egress policy: deny by default. Online calls/uploads are allowed only through an explicit `remote-approved` provider route plus consent v2, visible operator confirmation bound to the exact per-file SHA-256 `upload_manifest`, call and cost ceilings, and Broker destination allowlist. Consent v1 is status-only. Automatic publishing, unlisted file uploads, arbitrary provider URLs/keys, and silent `local-only`/`remote-approved` fallback remain prohibited. See `docs/decisions/2026-07-15-explicit-online-model-egress-policy.md`.
- Fixed temporal remote acceptance uses one consent containing exactly all frames in the selected groups and `max_calls` equal to the group count; Broker execution sends and counts each parent frame group independently. After an authorized execution, use `video-knowledge-model-acceptance capture-lane --lane A|B|C --input <connector-execution.json> --output-dir <acceptance-dir>` before the offline `compare` command.

Do not store API keys in this file, `vision_execution`, manifests, or generated reports.

## Typical Commands

```powershell
.\scripts\video-knowledge.ps1 prepare-local-video-run D:\path\to\lesson.mp4 D:\video-knowledge-runs\lesson-001 --title "课程名"
.\scripts\video-knowledge.ps1 openclaw-bridge-status
.\scripts\video-knowledge.ps1 openclaw-bridge-doctor
.\scripts\video-knowledge.ps1 openclaw-live-smoke --bundle-dir D:\video-knowledge-runs\lesson-001\webui-bundle --write-report
.\scripts\video-knowledge.ps1 export-task-console D:\video-knowledge-runs\lesson-001\webui-bundle
.\scripts\open-task-console.cmd
.\scripts\open-task-console.ps1 -BundleDir D:\video-knowledge-runs\lesson-001\webui-bundle
.\scripts\start-openclaw-http-background.ps1
.\scripts\openclaw-http-task.ps1 status
.\scripts\openclaw-http-task.ps1 register
.\scripts\openclaw-http-task.ps1 start
.\scripts\openclaw-http-startup-folder.ps1 status
.\scripts\openclaw-http-startup-folder.ps1 install
.\scripts\video-knowledge.ps1 openclaw-docker-contract-check
.\scripts\video-knowledge.ps1 openclaw-video-plan "https://example.com/video"
.\scripts\video-knowledge.ps1 openclaw-video-ingest D:\path\to\downloaded-or-local.mp4 --workspace D:\video-knowledge-runs\openclaw-lesson-001 --title "课程名"
.\scripts\video-knowledge.ps1 openclaw-video-link "https://example.com/video"
.\scripts\video-knowledge.ps1 openclaw-video-from-vdo-handoff --summary-path D:\path\to\vdo\summary.json --review-checklist-path D:\path\to\vdo\review-checklist.json
.\scripts\video-knowledge.ps1 openclaw-video-ingest-vdo-handoff --summary-path D:\path\to\vdo\summary.json --review-checklist-path D:\path\to\vdo\review-checklist.json
.\scripts\video-knowledge.ps1 content-asset-status D:\video-knowledge-runs\lesson-001\webui-bundle
.\scripts\video-knowledge.ps1 batch-content-asset-status D:\video-knowledge-runs
.\scripts\video-knowledge.ps1 content-handoff-pack D:\video-knowledge-runs
.\scripts\video-knowledge.ps1 video-moment-index D:\video-knowledge-runs\lesson-001\webui-bundle --query "<关键词或疑难点>"
.\scripts\video-knowledge.ps1 long-video-memory-pack D:\video-knowledge-runs\lesson-001\webui-bundle
.\scripts\video-knowledge.ps1 video-rag-pack D:\video-knowledge-runs\lesson-001\webui-bundle --query "<问题或术语>"
.\scripts\video-knowledge.ps1 resolve-terms D:\video-knowledge-runs\lesson-001\webui-bundle
.\scripts\video-knowledge.ps1 term-arbitration-codex D:\video-knowledge-runs\lesson-001\webui-bundle
# Fast local Codex-substitute path: accept only high-confidence draft replacements.
.\scripts\video-knowledge.ps1 term-arbitration-codex D:\video-knowledge-runs\lesson-001\webui-bundle --accept-draft
# Manual review path: review term-arbitration-codex-prompt.md with Codex as the first LLM substitute, edit the auto-generated term-arbitration-codex-result.codex.md, validate it, then run the closure.
# Validation is the gate: invalid/no accepted decisions must not write a glossary or corrected transcript.
.\scripts\video-knowledge.ps1 validate-term-arbitration-codex-result D:\video-knowledge-runs\lesson-001\webui-bundle --input-json D:\video-knowledge-runs\lesson-001\webui-bundle\term-arbitration-codex-result.codex.md
.\scripts\video-knowledge.ps1 term-correction-status D:\video-knowledge-runs\lesson-001\webui-bundle
.\scripts\video-knowledge.ps1 term-correction-closure D:\video-knowledge-runs\lesson-001\webui-bundle --input-json D:\video-knowledge-runs\lesson-001\webui-bundle\term-arbitration-codex-result.codex.md
.\scripts\video-knowledge.ps1 term-correction-impact-report D:\video-knowledge-runs\lesson-001\webui-bundle
.\scripts\video-knowledge.ps1 generate-smart-summary-with-codex D:\video-knowledge-runs\lesson-001\webui-bundle --input-md D:\video-knowledge-runs\lesson-001\webui-bundle\exports\smart-summary.codex.md
.\scripts\video-knowledge.ps1 external-capability-pack D:\video-knowledge-runs\lesson-001\webui-bundle --query "<关键词或问题>"
.\scripts\video-knowledge.ps1 online-model-api-matrix --output-dir D:\video-knowledge-runs\lesson-001\webui-bundle\exports
.\scripts\video-knowledge.ps1 media-capability-status
.\scripts\video-knowledge.ps1 media-route-status --task scene_segmentation
.\scripts\video-knowledge.ps1 media-connector-preflight <consent.json> --route-revision <exact-revision>
.\scripts\media-connector-consent.ps1 route-status --task scene_segmentation
.\scripts\video-knowledge.ps1 online-model-api summary_rewrite --input-text "<要改写的证据包>"
.\scripts\start-openclaw-http.cmd
sh scripts/openclaw-video-knowledge-call.sh plan "https://example.com/video"
sh scripts/openclaw-video-knowledge-call.sh live-smoke /mnt/used-by-codex/video-knowledge-pipeline/openclaw-runs/lesson-001/webui-bundle
sh scripts/openclaw-video-knowledge-call.sh content-status /mnt/used-by-codex/video-knowledge-pipeline/openclaw-runs/lesson-001/webui-bundle
sh scripts/openclaw-video-knowledge-call.sh batch-content-status /mnt/used-by-codex/video-knowledge-pipeline/openclaw-runs
sh scripts/openclaw-video-knowledge-call.sh content-handoff-pack /mnt/used-by-codex/video-knowledge-pipeline/openclaw-runs
# Agent-neutral local LLM substitute path for WorkBuddy/OpenCode/Hermes/OpenClaw/Codex; no cloud call by default.
.\scripts\video-knowledge.ps1 transcript-evidence-correction-pipeline D:\video-knowledge-runs\lesson-001\webui-bundle --agent-name openclaw
First-pass evidence branches must stay independent: ASR/subtitles, frame extraction, ebook/OCR structure, tagger annotations, and multimodal review should each complete and preserve their own raw evidence before triage/fusion resolves conflicts.

Frame sampling strategy and code-level contracts are documented in `docs/frame-sampling-strategy.md`.
`export_knowledge_note` now writes `exports/smart-summary.md` plus `exports/smart-summary-codex-prompt.md`; use `build-smart-summary-chapters` to create `exports/smart-summary-chapters.md` and `exports/course-map.md`. Chapter packs include a VideoRAG/VTimeLLM-style `citation_digest` that compresses transcript, moment, OCR/ebook, visual, temporal, and review-gap evidence into citation rows for Codex/LLM rewriting. Use `smart-summary-section-workflow` to create section-level rewrite state and TODO artifacts, use `smart-summary-section-editor` to open a static same-screen section editor, and use `smart-summary-section-apply` to install revised section Markdown into `exports/smart-summary.codex.md`. `generate-smart-summary-with-codex` without `--input-md` only prepares corrected-transcript/chapter/evidence inputs and marks `needs_llm_rewrite`; it does not create rule-composed summary prose. Final `smart-summary.md` only adopts Markdown that carries `codex_final` or `codex_llm_rewrite_final`. `knowledge-note.md` remains evidence/audit-oriented and `full-transcript.md` remains the transcript layer.
`postprocess-asr-transcript` / `postprocess_asr_transcript` is the local ASR readability postprocess: it merges tiny ASR fragments, writes `postprocessed-transcript.*` plus `readable-transcript.*`; default `punctuation_mode=readable` adds local cue-boundary punctuation, while `conservative` keeps terminal-only punctuation, and it promotes the readable result to `corrected-transcript.*` so `full-transcript.md` and smart-summary inputs use the readable transcript. It is deterministic and local-only. `readable-transcript-llm-polish` / `readable_transcript_llm_polish` is the optional text-LLM readable transcript layer: preview writes `exports/readable-transcript-llm-requests.json`; `execute=true` calls a runtime-only provider for punctuation/segmentation polish; `promote=true` is required before `llm-readable-transcript.*` can replace `corrected-transcript.*`. It must not do fact correction; facts still go through evidence conflict/source arbitration. For long-video smart summaries, prefer `run-smart-summary-section-llm-rewrite` / `run_smart_summary_section_llm_rewrite`: without `execute` it writes a safe per-section request plan; with runtime `provider_config` and `execute=true` it calls the OpenAI-compatible text provider once per chapter, writes `exports/smart-summary-section-llm-revisions.json`, then reuses `smart-summary-section-apply` to install the aggregate `smart-summary.codex.md`. `prepare-smart-summary-llm-rewrite` / `run-smart-summary-llm-rewrite` remain available for manual Codex handoff or short-video whole-summary rewriting, but long videos should not be sent as one giant prompt. Provider config/API key is runtime-only and must not be persisted.
Smart summary architecture, quality gates, and evidence-fusion rules are documented in `docs/smart-summary-best-practices.md`. The broader transcript semantic correction goal is documented in `docs/transcript-semantic-correction-to-smart-summary-goal-2026-07-06.md`; the canonical all-ASR/subtitle suspicious-word loop goal is `docs/all-asr-subtitle-suspect-word-semantic-correction-loop-2026-07-07.md`; the concrete spec entry is `docs/general-asr-subtitle-semantic-correction-loop-2026-07-06.md` (detailed spec: `docs/general-asr-subtitle-semantic-correction-loop-detailed-spec-2026-07-07.md`): terminology/tool-name arbitration is only the high-priority entity subset; any ASR/subtitle word likely disproven by OCR, visual evidence, page metadata, full-context semantics, or human annotation should enter semantic correction before final `full-transcript.md` / `smart-summary.md` export.
vsummary source review and selective reuse notes live in `docs/vsummary-source-review.md`; `text-llm-provider-smoke` is the no-secret text LLM provider plan/smoke entry adapted from vsummary gateway patterns.
PrideWood/bilinote source review and deep reuse notes live in docs/bilinote-pridewood-source-review.md; VKP uses its subtitle cleanup/merge, transcript correction prompt, and full-transcript chunking ideas while keeping VDO as the download boundary. Use transcript-correction-pack / transcript_correction_pack for the reusable correction workflow. `transcript-source-arbitration` now exposes `quality_summary.summary_input_policy`, `trusted_segment_indexes`, and `review_segment_refs`; `build-smart-summary-input-pack` promotes these into `transcript_quality_policy` for summary generation and run-queue review routing; `export-video-workbench` surfaces the same policy, review refs, and transcript editor/review/arbitration commands in the transcript arbitration panel.
External AI video project reuse is packaged as small local capabilities, not whole-project imports. Use `video-moment-index` / `video_moment_index` for VTimeLLM-style time localization, `long-video-memory-pack` / `long_video_memory_pack` for MovieChat-style short/long memory, `video-rag-pack` / `video_rag_pack` for VideoRAG-style JSONL retrieval units including per-item `content_candidate` chunks from `content-candidate-pack`, `video-rag-search` / `video_rag_search` for direct local retrieval with `retrieval_backend=keyword|sqlite|vector` (`keyword` default, `sqlite` local persistent index, `vector` future placeholder only), `video-rag-service-plan` / `video_rag_service_plan` plus explicit `video-rag-serve` for a local HTTP search service, `local-vlm-adapter-plan` / `local_vlm_adapter_plan` and `local-vlm-serving-smoke` / `local_vlm_serving_smoke` for Qwen/InternVL/LLaVA adapter checks, `vlm_preprocess.py` for shared Qwen/InternVL-style local image resize/compress/payload metadata used by semantic, temporal, and provider smoke paths, and `external-capability-pack` / `external_capability_pack` to generate the full five-capability bundle including content material generation. These commands are local-only by default: no download, no cloud call, no model server start, no publication.
External code reuse navigation starts from docs/external-code-reuse-latest-action-map-2026-07-06.md: it is the newest one-page action map for absorbed modules, recently landed reuse work, remaining modules worth extracting, rejected whole-project migrations, and the current development order. Use docs/external-code-reuse-readable-index-2026-07-06.md when a fuller narrative index is needed.
For BiliNote-style transcript editing, use `prepare-transcript-edit-session` / `prepare_transcript_edit_session` to generate `transcript-editor.html`; it registers `prepare_transcript_edit_session` as `runs/prepare-transcript-edit-session/run.json` with `needs_input` while waiting for reviewed edits. Import reviewed `transcript-edits.json` with `apply-transcript-edits` / `apply_transcript_edits`; it registers `apply_transcript_edits` as `runs/apply-transcript-edits/run.json`, with completed imports promoted to `human-corrected-transcript.*` and zero-change imports marked `needs_review`. Use `bilinote-mind-map-prompt-pack --bundle-dir <webui-bundle>` / `bilinote_mind_map_prompt_pack` when an agent needs the BiliNote-style mind-map JSON prompt structure from a bundle transcript. It writes `exports/bilinote-mind-map-prompt-pack.*`, registers `bilinote_mind_map_prompt_pack`, and does not call an LLM.
Use `term-correction-status` / `term_correction_status` as the read-only agent polling entry for terminology correction. It returns `status`, `term_validation_status`, accepted/rejected validation counts, artifact paths, `next_action_key`, and `codex_substitute`. The `codex_substitute` object is the current Codex-first replacement for an online text LLM API: it points to `term-arbitration-codex-prompt.md`, `term-arbitration-codex-pack.json`, the auto-generated editable `term-arbitration-codex-result.codex.md` response path, validation/import commands, and the rule that accepted decisions must include semantic rationale, candidate_id, and evidence_indexes. If Codex semantic arbitration output fails validation, it reports `needs_codex_term_validation` and points back to `validate_term_arbitration_codex_result` instead of silently importing weak terms. `term-correction-closure --input-json` also runs this validation first and stops without writing `term-arbitration-glossary.json` or `source-arbitrated-transcript.json` when the Codex/LLM response is invalid or has no accepted replacements.
Use `transcript-source-arbitration` / `transcript_source_arbitration` before smart-summary export when ASR, platform subtitles, self subtitles, or terminology evidence disagree. It is local-only, writes `source-arbitrated-transcript.*`, updates `manifest.corrected_transcript_*` by default, and sends low-confidence conflicts to review instead of silently overwriting text.
Use `transcript-evidence-correction-pipeline` / MCP `transcript_evidence_correction_pipeline` as the preferred one-shot transcript evidence chain: SenseVoice/FunASR ASR + platform/local subtitles + webpage context + tagger timeline/topic/visual-state evidence + OCR/ebook/vision evidence + local agent-substitute or optional online LLM semantic arbitration -> `source-arbitrated-transcript.*` -> stable `corrected-transcript.*` -> refreshed readable exports. Default mode uses the local `agent_substitute` path and does not call a cloud LLM; agents should pass `agent_name` such as `codex`, `workbuddy`, `opencode`, `hermes_agent`, or `openclaw` so reports show who performed the substitute step. After semantic closure the pipeline now runs `agent-readable-transcript-rewrite` and `transcript-quality-gate`; the standalone MCP tools are `agent_readable_transcript_rewrite` and `transcript_quality_gate`. `export-knowledge-note` also runs the transcript quality gate, records it in full-transcript/export-summary/manifest, and `smart-summary-input-pack` prefers human/LLM/corrected transcript over source-arbitrated or raw ASR, so promoted agent-readable output becomes the smart-summary source. `use_agent_substitute=false` / CLI `--no-agent-substitute` returns to preview/cloud-gated behavior. `--execute-readable-llm` and `--execute-llm` are still required for real online provider calls. Legacy `codex_substitute` / `--no-codex-substitute` remains a compatibility alias, not a Codex-only requirement. Provider config is runtime-only and must not be persisted. See `docs/transcript-evidence-correction-pipeline.md`.
Use `transcript-main-route-status` / MCP `transcript_main_route_status` after the pipeline to verify the optimized route: ASR full-mode plan, postprocessed transcript, evidence conflict index, corrected/source-arbitrated transcript, full transcript export, smart-summary quality, WhisperX alignment advisory, and ASR A/B advisory.

Use `transcript-semantic-correction-pack` / `transcript_semantic_correction_pack` when ASR/subtitle suspicious words are broader than tool names: numbers, proper nouns, actions, concepts, ordinary ASR mistakes, punctuation, or segment-boundary issues. The safe sequence is `transcript-semantic-correction-pack -> transcript-semantic-candidate-discovery-pack -> transcript-semantic-candidate-discovery-codex-draft or transcript-semantic-candidate-discovery-llm-draft -> import-transcript-semantic-candidate-suggestions -> transcript-semantic-correction-codex-draft or transcript-semantic-correction-llm-draft -> validate-transcript-semantic-correction -> transcript-semantic-correction-closure --refresh-exports -> transcript-semantic-correction-status（不带 --refresh-exports 时仍可按旧链路手动运行 export-knowledge-note -> transcript-semantic-correction-impact-report -> transcript-semantic-readable-impact-report -> transcript-semantic-summary-impact-report）`. Codex or an online LLM only judges the generated evidence pack; VKP validates the JSON locally, writes high-confidence decisions to `source-arbitrated-transcript.*`, keeps raw ASR untouched, and sends low-confidence or high-risk conflicts to review. MCP tool names mirror the CLI with underscores: `transcript_semantic_correction_pack`, `transcript_semantic_candidate_discovery_pack`, `transcript_semantic_candidate_discovery_codex_draft`, `transcript_semantic_candidate_discovery_llm_draft`, `import_transcript_semantic_candidate_suggestions`, `transcript_semantic_correction_codex_draft`, `transcript_semantic_correction_llm_draft`, `validate_transcript_semantic_correction`, `transcript_semantic_correction_closure`, `transcript_semantic_correction_impact_report`, `transcript_semantic_readable_impact_report`, `transcript_semantic_summary_impact_report`, and `transcript_semantic_correction_status`. Use `transcript-semantic-acceptance <bundle_dir>` / MCP `transcript_semantic_acceptance` for a read-only single-bundle proof; it writes `transcript-semantic-acceptance.json/md`, reuses the batch per-bundle gate, and never runs ASR, vision, closure, export, download, or cloud calls. Use `transcript-semantic-batch-acceptance <batch_input>` / `transcript_semantic_batch_acceptance` for the read-only 3-5 bundle acceptance gate; pass `--limit` / `limit` to cap sampled bundles. It reports `needs_pack`, `needs_review`, `needs_closure`, `needs_impact_report`, `needs_export_refresh_or_review`, or accepted states without running ASR, vision, download, closure, export, or cloud calls. Use `transcript-semantic-summary-impact-report <bundle_dir>` / `transcript_semantic_summary_impact_report` to prove whether accepted corrections are visible in final `smart-summary.md`; pass `baseline_summary_path` when a before-summary exists. Use `transcript-semantic-repair-queue <batch_input>` / `transcript_semantic_repair_queue` for the preview-only retry queue; it emits `transcript-semantic-repair-queue.json/md` with `action_key`, progress, retry command, machine-action flag, human-review flag, and LLM confirmation boundary; when semantic/readable impact passed but smart-summary absorption is unproven, it emits `run_summary_impact`, but does not execute actions. Use `transcript-semantic-repair-run <batch_input>` / `transcript_semantic_repair_run` to preview or explicitly execute queued actions. `--execute-safe-actions` can run local safe steps and never calls ASR/vision/download; closure writes require `--allow-closure`. Text LLM provider review has a separate gate: pass `--allow-llm --provider-config <json-or-profile>` / MCP `allow_llm=true, provider_config={...}` and optionally `llm_limit`; provider config is runtime-only and must not be persisted in reports. When repair-run has exhausted local safe actions and remaining candidates need Codex/LLM/human semantic judgment, use `transcript-semantic-batch-review-pack <batch_input>` / MCP `transcript_semantic_batch_review_pack` to generate `transcript-semantic-batch-review-pack.json/md`, `transcript-semantic-batch-review-notes.todo.json`, and `transcript-semantic-batch-codex-review-prompt.md`; after the todo JSON is filled, call `transcript-semantic-batch-import-review-notes <review_json>；也可以先用 `transcript-semantic-batch-codex-review-draft <review_pack_json>` / MCP `transcript_semantic_batch_codex_review_draft` 生成保守本地 Codex 草稿，它只自动接受明确已知错词和安全保留项，其余标记为 `needs_more_evidence`，不会调用云模型。` / MCP `transcript_semantic_batch_import_review_notes` to split rows back into bundles and reuse the single-bundle import/validate gate. Closure remains a separate explicit action; use `--refresh-exports` when the accepted corrections should immediately refresh full-transcript/smart-summary and semantic impact reports. `openclaw-live-smoke` / `openclaw_live_smoke` now embeds this same gate as `transcript_semantic_batch_acceptance`; pass `semantic_batch_input`, `semantic_target_bundle_count`, and optional `semantic_limit` for a batch, or only `bundle_dir` for a single bundle check.
Local frame sampling and online multimodal calls are separate budgets. Local ingest defaults to `--sample-mode balanced-long-video --sample-interval 5 --max-frames 720`: videos up to about 1 hour use roughly 5-second sampling, while longer videos dynamically increase the effective interval to cover the whole duration. Use `dense-local` for full 5-second local sampling on long videos, or `triage-first` to reserve budget for scene/transcript-semantic points. Do not treat local frames as permission to upload all frames; cloud/API vision still requires preflight, explicit confirmation, and small triage-first limits.
.\scripts\video-knowledge.ps1 acceptance-run D:\path\to\lesson.mp4 D:\video-knowledge-runs\lesson-001 --title "课程名" --sample-interval 5 --max-frames 720
.\scripts\video-knowledge.ps1 acceptance-bundle-run D:\video-knowledge-runs\lesson-001\webui-bundle --title "课程名"
.\scripts\video-knowledge.ps1 acceptance-bundle-run D:\video-knowledge-runs\lesson-001\webui-bundle --execute-vision --confirm-vision-calls <preflight_calls> --confirm-vision-indexes "<preflight_indexes>"
.\scripts\video-knowledge.ps1 batch-run D:\path\to\batch-manifest.json --resume
.\scripts\video-knowledge.ps1 batch-repair-run D:\path\to\batch-acceptance-summary.json
.\scripts\video-knowledge.ps1 batch-repair-run D:\path\to\batch-acceptance-summary.json --allow-ocr --execute --limit 1
.\scripts\video-knowledge.ps1 run-screen-text-recovery D:\video-knowledge-runs\lesson-001\webui-bundle --execute-crops
.\scripts\video-knowledge.ps1 bundle-next-action D:\video-knowledge-runs\lesson-001\webui-bundle
.\scripts\video-knowledge.ps1 bundle-advance D:\video-knowledge-runs\lesson-001\webui-bundle
.\scripts\video-knowledge.ps1 prepare-review-session D:\video-knowledge-runs\lesson-001\webui-bundle
.\scripts\video-knowledge.ps1 review-closure-status D:\video-knowledge-runs\lesson-001\webui-bundle
.\scripts\video-knowledge.ps1 validate-review-notes D:\video-knowledge-runs\lesson-001\webui-bundle
.\scripts\video-knowledge.ps1 apply-review-notes D:\video-knowledge-runs\lesson-001\webui-bundle
.\scripts\video-knowledge.ps1 acceptance-check D:\video-knowledge-runs\lesson-001\webui-bundle
.\scripts\video-knowledge.ps1 vision-provider-smoke --provider agnes --bundle-dir D:\video-knowledge-runs\lesson-001\webui-bundle
.\scripts\video-knowledge.ps1 vision-provider-matrix --providers "local_qwen_vl,volcengine_coding_plan,gemini,openai,agnes" --bundle-dir D:\video-knowledge-runs\lesson-001\webui-bundle
.\scripts\video-knowledge.ps1 vision-execution-preflight D:\video-knowledge-runs\lesson-001\webui-bundle
.\scripts\video-knowledge.ps1 vision-execution-preflight D:\video-knowledge-runs\lesson-001\webui-bundle --semantic-indexes "2,5" --semantic-limit 0 --no-temporal
.\scripts\video-knowledge.ps1 controlled-execution-check D:\video-knowledge-runs\lesson-001\webui-bundle
.\scripts\video-knowledge.ps1 vision-analysis-run-log D:\video-knowledge-runs\lesson-001\webui-bundle
.\scripts\video-knowledge.ps1 vision-analysis-restore-plan D:\video-knowledge-runs\lesson-001\webui-bundle --run-id "semantic_frame-..."
.\scripts\video-knowledge.ps1 vision-analysis-apply-restore D:\video-knowledge-runs\lesson-001\webui-bundle --plan-json D:\video-knowledge-runs\lesson-001\webui-bundle\vision-restore-plan.json
.\scripts\video-knowledge.ps1 config-status
.\scripts\video-knowledge.ps1 prepare-local-video-run D:\path\to\lesson.mp4 D:\video-knowledge-runs\lesson-001 --title "课程名" --build-initial-bundle --sample-interval 5 --max-frames 720
.\scripts\video-knowledge.ps1 asr-env-status --output-dir D:\video-knowledge-runs\asr-env-check --write
.\scripts\video-knowledge.ps1 asr-smoke D:\path\to\lesson.mp4 --duration-seconds 30
.\scripts\video-knowledge.ps1 plan-asr D:\path\to\workspace D:\path\to\lesson.mp4 --preset sensevoice --model iic/SenseVoiceSmall
.\scripts\video-knowledge.ps1 prepare-cloud-asr-audio D:\path\to\audio-16k-mono-64k.mp3 --output-path D:\path\to\audio-16k-mono-32k.mp3 --execute
.\scripts\video-knowledge.ps1 plan-cloud-asr D:\path\to\workspace D:\path\to\lesson.mp4 --model gpt-4o-transcribe
.\scripts\video-knowledge.ps1 run-cloud-asr-plan D:\path\to\workspace\transcripts\<cloud_asr_run_id>\cloud-asr-plan.json --execute
.\scripts\video-knowledge.ps1 plan-whisperx-alignment D:\path\to\workspace D:\path\to\lesson.mp4 --model large-v3
.\scripts\video-knowledge.ps1 plan-whisperx-alignment D:\path\to\workspace D:\path\to\lesson.mp4 --language zh
.\scripts\video-knowledge.ps1 run-multimodal-frame-analysis D:\path\to\webui-bundle --limit 19 --provider-config '{"provider":"gemini","model":"gemini-3.5-flash"}'
.\scripts\video-knowledge.ps1 run-multimodal-frame-analysis D:\path\to\webui-bundle --execute --limit 19 --indexes "2,5" --confirm-vision-calls <preflight_calls> --confirm-vision-indexes "<preflight_indexes>"
.\scripts\video-knowledge.ps1 run-temporal-visual-analysis D:\path\to\webui-bundle --execute --frame-count 8 --indexes "58,59" --confirm-vision-calls <preflight_calls> --confirm-vision-indexes "<preflight_indexes>"
.\scripts\run-volcengine-vision-batch.ps1 D:\path\to\webui-bundle -Limit 10
.\scripts\run-volcengine-vision-batch.ps1 D:\path\to\webui-bundle -Limit 10 -Execute
.\scripts\run-volcengine-vision-batch.ps1 D:\path\to\webui-bundle -Temporal -Limit 5 -FrameCount 8 -Execute
.\scripts\video-knowledge.ps1 export-knowledge-note D:\path\to\webui-bundle --title "课程名"
.\scripts\video-knowledge.ps1 test-vision-provider --provider-config '{"provider":"gemini","model":"gemini-3.5-flash"}'
.\scripts\video-knowledge.ps1 local-vlm-adapter-plan
```

For local files, start with `acceptance-run` when you want an end-to-end local acceptance package. It writes `acceptance-report.md` and `acceptance-run.json`, creates the initial review bundle by default, routes frames, previews visual branches, audits coverage, and exports a draft knowledge note. Its default mode is preview-safe for ASR, cloud vision APIs, and temporal frame extraction. The document screenshot branch reuses `ebook_markdown_pipeline`; new bundle MCP args and the task console read the unified `ebook_pipeline` profile for stable local execution defaults.
Use `openclaw-video-plan` / `openclaw_video_plan` for Telegram/OpenClaw messages that contain video links. It delegates route/download planning to `%WORKSPACE_ROOT%\video-download-orchestrator` and returns `will_download=false`; this project does not implement a downloader.
Use `openclaw-video-ingest` / `openclaw_video_ingest` for existing host video files or files already downloaded by `video-download-orchestrator`. It prepares a video knowledge workspace and returns `review_url_or_file`, usually the generated `webui-bundle\review.html`.
Use `openclaw-video-link` / `openclaw_video_link` for the combined link workflow. Default mode is plan-only. Real download execution requires explicit `allow_download`, `actor_id`, and `confirm_download`; the execution call is still delegated to `video-download-orchestrator openclaw-execute`.
Use `openclaw-bridge-status` / `openclaw_bridge_status` before Docker/OpenClaw calls VKP. It reads the unified config and checks whether the host bridge is listening, optionally healthy, and whether the Windows scheduled task is registered; it does not start services, process video, or call cloud APIs.
Use `scripts\start-openclaw-http-background.ps1` for a direct hidden host start with logs in `.local\logs` and a `/health` wait loop. Use `scripts\openclaw-http-task.ps1` for host-side lifecycle operations: `status`, `register`, `start`, `stop`, `unregister`. It registers a user-level scheduled task named `VideoKnowledgeOpenClawHttp` that calls `scripts\start-openclaw-http.cmd`; it does not keep its own port copy. If task registration is denied, use `scripts\openclaw-http-startup-folder.ps1 install` from a visible PowerShell as a per-user Startup folder fallback.
Use `openclaw-docker-contract-check` / `openclaw_docker_contract_check` to inspect whether OpenClaw Docker has the required `/mnt/used-by-codex` mount and `VKP_API_BASE` / `VDO_API_BASE` environment contract. It is read-only and does not modify OpenClaw production compose files.
Use `openclaw-video-from-vdo-handoff` / `openclaw_video_from_vdo_handoff` after VDO produces manifest/report/review artifacts. It normalizes source URL, platform, title, media path, sidecars, report paths, and review status into `video_knowledge_pipeline.vdo_handoff.v1`. It blocks auto-ingest when VDO review still needs human action or no media file is verified. Use `import-page-metadata <webui-bundle> <local-json>` / MCP `import_page_metadata` when a VDO/yt-dlp/acquisition JSON already exists locally. It normalizes title, description, author, tags, chapters, local subtitle paths, and cover provenance into `source/page-metadata.json/md`, updates `source-artifacts.json/md`, and never fetches the source URL. Page text is untrusted weak context: it may feed hotwords, bounded ASR hints, semantic-correction evidence, and Smart Summary input, but cannot override transcript/visual evidence or authorize upload/publication. See `docs/page-metadata-handoff.md`.
Use `openclaw-video-ingest-vdo-handoff` / `openclaw_video_ingest_vdo_handoff` to safely bridge VDO handoff into VKP. Default mode is preview. It calls `openclaw_video_ingest` only when the handoff is `ready_for_ingest` and `execute=true`; ASR and vision execution remain off by default.
For Docker OpenClaw, keep `video-download-orchestrator` as the download API with `VDO_API_BASE=http://host.docker.internal:8921`, start this project's bridge with `.\scripts\start-openclaw-http.cmd`, set `VKP_API_BASE=http://host.docker.internal:8931`, mount `%WORKSPACE_ROOT%` into the container, and translate container paths back to Windows host paths before calling this project. See `docs\openclaw-integration.md`.
In a mounted Docker workspace, use `scripts/openclaw-video-knowledge-call.sh` or `examples/openclaw/openclaw_video_knowledge_call.py`; it translates `/mnt/used-by-codex/...` paths back to `%WORKSPACE_ROOT%\...` before posting to the host bridge.
Use Docker helper command `content-status <webui-bundle>` after export to let OpenClaw verify content-material-card readiness without reading files directly. `content-asset-status`, `batch-content-asset-status`, and `content-handoff-pack` also surface `human-sample-eval` quality signals when present, including content-candidate usability/evidence-sufficiency rates. These are advisory review signals only; they do not permit publication or fact claims.
VKP may expose content asset candidates after ingest/export, such as summaries, timelines, key segments, short-video script drafts, or highlight-post source material. These are always review drafts: `review_required=true`, `publication_allowed=false`, and must not be auto-published by OpenClaw. The `content_assets` index also carries the shared self-media material card contract: VDO handoff assets are only `candidate` stage and cannot be used by朋友圈 automation yet; VKP exported assets are `evidence` stage, may be passed as `needs_review_inspiration`, and cannot be treated as facts until human fact-check/compliance/privacy review is complete. See `docs\openclaw-integration.md#self-media-material-handoff`.
After `export-knowledge-note`, call `content-asset-status` / `content_asset_status` to verify that `exports\content-material-card.json`, `exports\content-material-card.md`, `exports\content-candidate-pack.json`, and `exports\content-candidate-pack.md` exist and are safe only for review/inspiration routing. If `exports\smart-summary-chapters.json` exists, the candidate pack carries per-candidate `evidence_citations` / `Citation Digest` rows for evidence navigation; this does not make candidates factual or publishable.
Use `batch-run` / `batch_video_knowledge_run_tool` for repeated local videos or existing bundles. It reads `video_knowledge_batch.v1`, writes `batch-run.json/md` plus `batch-acceptance-summary.json/md`, skips already accepted bundles by default, resumes existing bundles with preview-safe acceptance, and only runs ASR/vision/ebook execution when explicit flags are passed. Batch manifest items may include `expected_content_type`, `priority`, and `notes` for the dashboard.
Use `batch-repair-run` / `batch_repair_run_tool` after `batch-run`. It reads `batch-acceptance-summary.json`, plans each bundle's next action, and writes `batch-repair-run.json/md` plus `batch-human-review.md`. Default mode is preview-only. Pass `allow_asr`, `allow_vision`, or `allow_ocr` plus `execute=true` only when the user explicitly wants those branches to run; OCR execution uses the existing screen-text recovery path, ASR only plans local SenseVoice/FunASR unless the runner is explicitly invoked elsewhere, and vision remains behind existing preflight/confirmation gates.
Use `run-visual-structure` / `run_visual_structure_tool` as the primary document screenshot/text-layout branch. It calls local `ebook_markdown_pipeline` (`process_material -> get_job_status -> read_artifact`) when `execute_ebook_pipeline=true`; the recommended args come from `config\\video-knowledge-pipeline.json -> ebook_pipeline`. Use `high-res-tile-plan` / `run_high_res_tile_plan` when ebook/OCR returns empty, wrapper-only, low-information, or when PPT/table/software UI frames need local high-resolution tile evidence. It defaults to preview and writes `high-res-tiles\\` only with `execute_tiles=true`; it does not run OCR/VLM or claim OCR success. Use `tile-result-import-build` / `build_tile_result_import` to normalise existing tile `.json` / `.txt` / `.md` result files into `tile-result-import.json`; it understands common OCR/VLM JSON shapes including RapidOCR/PaddleOCR entries, OpenAI-compatible choices, Gemini candidates, VKP `visual_understanding`, and `structured_visual`. It does not run OCR/VLM; use `default_confidence` only when the result source is trusted enough to merge without per-entry scores. Use `tile-result-merge` / `run_tile_result_merge` to import already-produced tile OCR/VLM/human results; it defaults to preview, writes timeline only with `execute=true`, and keeps empty/wrapper-only/low-confidence outputs as review targets instead of clearing blockers. Use `run-screen-text-recovery` / `run_screen_text_recovery_tool` only for small UI text recovery fallback. It reuses `run_ocr_backfill` planning, defaults to preview, writes crop images only with `execute_crops=true`, and attempts local OCR only with `execute_ocr=true`.
In acceptance reports, `Workflow` means the orchestration ran, while `Content` / `Status` reflects bundle readiness. If `Content` is `machine_action_available`, follow `Bundle Next Action` instead of treating the package as complete.
Use `timeline-alignment-audit` / `timeline_alignment_audit` when review timestamps, ASR starts, frame times, or Qinglong tagger times appear misaligned. It writes `timeline-alignment-audit.json/md` and `mcp-timeline-alignment-audit.args.json`, does not modify `timeline.json`, and should be run before manually changing review_start fields. Use `bundle-next-action` to inspect the next safe step and `bundle-advance` / `bundle-advance-queue` to run safe machine actions. These commands default to preview-safe behavior; pass explicit execution flags only when external tools/API calls are intended. Vision execution defaults come from the unified `vision_execution` profile, currently small batches: `multimodal_limit=19`, `temporal_limit=3`, `frame_count=8`. The acceptance commands use the same profile unless `--semantic-limit`, `--temporal-limit`, or `--frame-count` is passed.
Use `prepare-review-session` when `bundle-next-action` reports `human_review_required`, especially `ocr_text_empty_review`. It writes `review-session.md/json`, `review-pack.md/json`, `review-notes.todo.json`, and `review-closure-status.md/json`; review pack rows include time, reason, suggested status/action, transcript/OCR/model excerpts, evidence frames, and crop paths. Before importing edited review notes, run `validate-review-notes` / `validate_review_notes`. It catches unknown or duplicate timeline indexes and prevents empty `corrected_visual_understanding`, `corrected_temporal_visual_understanding`, or `corrected_visual_text` rows from clearing visual blockers. Then run `apply-review-notes` / `apply_review_notes`; it refreshes coverage/readiness, exports, acceptance, bundle status, review HTML, and closure status in that order. Use `review-closure-status` / `review_closure_status` to get current total/open/closed counts and the next review batch command without regenerating the whole session.
Use `acceptance-check` / `acceptance_check` after review import, provider smoke, or export. It is the current top-level truth report for provider health, semantic/temporal gaps, review lifecycle, export freshness, and next action.
Use local Qwen-VL through the existing OpenAI-compatible provider layer: set `LECTURE_VISION_PROVIDER=local_qwen_vl`, `LECTURE_VISION_BASE_URL=http://127.0.0.1:8000/v1`, and `LECTURE_VISION_MODEL=Qwen/Qwen2.5-VL-3B-Instruct`. No API key is required by default; use `LOCAL_QWEN_VL_API_KEY` only when the local server requires auth. Generic local OpenAI-compatible VLMs can use `provider=local_vlm` with `LOCAL_VLM_*` overrides. VKP does not import or launch model repository code. Use `local-vlm-serving-smoke` / `local_vlm_serving_smoke` for local service readiness: preview mode writes a capability matrix for OpenAI-compatible endpoint, text JSON, single-image JSON, multi-image JSON, and short-frame-group JSON; `execute=true` only calls an already-running local service and still never mutates timeline.
Use `export-video-workbench` / `export_video_workbench` to expose existing `vision-provider-smoke`, `vision-provider-matrix`, and `local-vlm-serving-smoke` reports in a static Provider / 本地 VLM panel. These smoke commands also register `runs/*/run.json`: provider smoke and matrix become `completed` or `needs_retry`, while plan-only local VLM smoke is `needs_execution`. The panel is read-only: it does not start a model server, call a cloud provider, or mutate timeline. Use `vision-provider-smoke` / `vision_provider_smoke` before real multimodal execution when provider health is uncertain. It writes secret-safe text/single-image/multi-image smoke reports, endpoint/proxy diagnostics, image-selection summaries, and MCP args. If it reports `provider_transport_error`, `provider_unreachable`, `provider_dns_failed`, `provider_proxy_failed`, or `provider_connection_refused`, fix or switch provider before running real multimodal execution.
Use `vision-provider-matrix` / `vision_provider_matrix` when one provider is blocked. It compares provider profiles with the same secret-safe smoke checks, writes a sanitized `recommended_provider_config`, and avoids one-provider retry loops. Quote comma-separated providers in PowerShell, for example `--providers "local_qwen_vl,volcengine_coding_plan,gemini,openai,agnes"`.
In acceptance commands, `run_temporal_frame_groups` runs before `vision_execution_preflight`, so `--execute-temporal-groups --execute-vision` can generate frame groups and then preflight the resulting exact semantic/temporal batch in one controlled run.
Before real vision execution, run `vision-execution-preflight` / `vision_execution_preflight_tool`. It checks provider/key readiness, selected candidates, expected API calls, controlled timeline write fields, and restore-chain availability. It writes `vision-execution-preflight.json/md` and `mcp-vision-execution-preflight.args.json`; it must not contain API keys. `bundle-advance --execute`, `acceptance-run --execute-vision`, `acceptance-bundle-run --execute-vision`, `run-multimodal-frame-analysis --execute`, and `run-temporal-visual-analysis --execute` automatically run this preflight before single-frame or temporal vision API actions and return `vision_preflight_blocked`, `vision_provider_not_ready`, or `vision_confirmation_required` instead of calling the model when the gate is not satisfied. If preflight is ready, these execution entrypoints still require matching `confirm_vision_calls` and `confirm_vision_indexes` copied from the preflight confirmation block.

For agent-initiated online vision, create and validate `vision-export-consent.json` with `vision-export-consent-create` / `vision_export_consent_create` and `vision-export-consent-status` / `vision_export_consent_status`. MCP vision executors default to `execution_actor=agent`; they require a consent scoped to the bundle, provider/model/endpoint, selected semantic/temporal indexes, call limit, image size, and expiry. The consent contains no API key and does not override the agent platform's external-data policy. If the platform still blocks export, use the exact visible-PowerShell command from preflight or the local VLM fallback; do not broaden, disguise, or retry around the policy. Full contract: `docs/agent-online-vision-consent.md`.
When a user or agent wants an explicit semantic batch, pass `semantic_indexes` plus `include_temporal=false` to `vision_execution_preflight_tool`, or use `--semantic-indexes ... --no-temporal` in CLI. For temporal batches, pass `temporal_indexes` plus `include_semantic=false`, or use `run-temporal-visual-analysis --execute --indexes`. Direct `run-multimodal-frame-analysis --execute --indexes` and `run-temporal-visual-analysis --execute --indexes` forward those indexes into preflight, so the confirmation indexes match the exact candidate indexes that would be called. Items that already have `visual_understanding` or `temporal_visual_understanding` are skipped to avoid accidental overwrite. Limit `0` means all candidates for an enabled branch; disable branches explicitly.
Preflight writes confirmed direct-executor MCP args such as `mcp-run-multimodal-frame-analysis-confirmed.args.json` and `mcp-run-temporal-visual-analysis-confirmed.args.json`; these contain execute/index/limit/frame_count/confirmation fields plus sanitized provider/model config, never API keys. If a base_url contains suspicious key/token query parameters, it is omitted from confirmed args. Do not treat global preflight as a confirmed `bundle-advance` source: `bundle-advance` must get confirmation from its own next-action gate because it does not accept index filters and only executes one selected next action.
For local terminal use, `.\scripts\video-knowledge.ps1 mcp-call <tool_name> <args.json>` is a CLI bridge for the generated MCP args files. It reads the JSON file, invokes the matching local project function, filters unsupported extra fields, and still respects execute/preflight/confirmation/API-key gates.
Before a real run, use `.\scripts\video-knowledge.ps1 mcp-audit-bundle <webui-bundle>` to statically verify generated MCP args files. This audit does not call models or mutate timeline data; it checks file existence, supported tool mapping, readable JSON, required arguments, and ignored extra fields.
Use `vision-analysis-run-log` / `vision_analysis_run_log_tool` after multimodal or temporal runs to inspect persisted execution audits and timeline field diffs. The audit records provider/model state, selected indexes, updated counts, report paths, and sanitized changes to controlled timeline fields; it does not store API keys, prompts, or raw model responses. Use `vision-analysis-restore-plan` / `vision_analysis_restore_plan_tool` to write a human-review restore plan for a specific run before rollback. Use `vision-analysis-apply-restore` / `vision_analysis_apply_restore_tool` only after review; it defaults to dry-run and requires both `execute=true` and matching `confirm_run_id` before it modifies `timeline.json`.
After a successful vision write through direct executors or `bundle-advance --execute`, inspect `vision_restore_hint` / `action_result.vision_restore_hint`. It includes the run id, a ready `vision-analysis-restore-plan` command for the exact run, and dry-run / execute restore commands that still require reviewed restore files and matching `confirm_run_id`. The latest `bundle-advance-runs.jsonl` entry also keeps the restore-plan command for the unified advance path.
Use `bundle-status-report` to inspect the whole controlled-execution chain in one place: preflight, confirmation gate, vision run audit, restore plan, restore apply runs, and the latest restore-plan command. It also reads `execution_control` from direct `vision-analysis-runs.jsonl` entries, so direct multimodal/temporal executor confirmation gates are visible even without a `bundle-advance` record.
Use `controlled-execution-check` / `controlled_execution_check_tool` when an agent needs a strict boolean and checklist for the controlled execution chain. The checklist distinguishes an audit log from a recoverable timeline write, so confirmed but empty runs are still blocked.
If vision execution is requested but preflight blockers remain, bundle advance returns `vision_preflight_blocked` and does not call the model.
For temporal routes, generate frame groups first: when `temporal_frame_paths` are missing, `bundle-next-action` routes to `run_temporal_frame_groups` before `run_temporal_visual_analysis`.
For an existing `webui-bundle`, use `acceptance-bundle-run` to continue the acceptance workflow without re-preparing the source video.
Use `prepare-local-video-run` when you only need the lower-level video run folder. It writes a human-readable `video-knowledge-run.md` and a machine-readable `video-knowledge-run.json`.
Use `--build-initial-bundle` when ffmpeg/ffprobe are available and you want an initial `webui-bundle\review.html` in the same run.
Use `asr-env-status` before local ASR work and `asr-smoke` to verify a real short local segment. `asr-smoke` defaults to execution; pass `--no-execute` for a preview-only report.

Phase 17 quality route: use `plan-asr --preset sensevoice` and `plan-asr --preset qwen3-asr-1.7b` for independent hypotheses, then `asr-consensus` / MCP `asr_consensus`. Qwen3-ASR reuses the official `qwen-asr` package and ForcedAligner, chunks local audio at 300 seconds, and never silently falls back from 1.7B to 0.6B. Use `quality-benchmark build/run/report` / MCP `quality_benchmark` for evaluation-only human truth; reference text must never be imported as correction evidence. Use `transcript-evidence-correction-pipeline --quality-profile quality`, `semantic-chapter-plan`, and `run-smart-summary-section-llm-rewrite --auto-from-profile` for the quality chain. Automatic text LLM execution requires `processing_profiles.quality.data_export_allowed=true`, a ready runtime provider, and a batch below 20 calls / 120,000 input characters. Use `export-quality-console` / MCP `export_quality_console` for the static progress/failure/retry-command UI. Current adapter availability does not prove the 24-sample quality targets; only a completed benchmark may switch model defaults. The Qwen3 ForcedAligner runtime is verified through `plan-asr --preset qwen3-forced-aligner` followed by `run-asr-plan --execute`; alignment plans automatically skip transcript normalization, remain sidecars, and never replace the ASR transcript. `smart-summary-global-reduce` preserves every semantic chapter under budget and blocks instead of dropping late chapters when metadata cannot fit. Mainland-China model downloads should use the official ModelScope route and local directories under `%LOCAL_MODEL_ROOT%\models`; `plan-asr` discovers those directories before remote model IDs. For a usable human pack, repeat `--media-path` once per bundle and add `--execute-clips`; never mark a model switch ready until `model_switch_allowed=true`, including all 24 human references and all 3 summary blind reviews.
Use `export-knowledge-note` after ASR/OCR/multimodal imports to create `exports\knowledge-note.md`, `exports\full-transcript.md`, `exports\extraction-audit.md`, and `exports\export-summary.json`. The main note is the human reading artifact; the audit file keeps raw/detail-heavy inspection data.

## Source Review

Open-source ASR/local VLM review notes:

- `%WORKSPACE_ROOT%\video-knowledge-pipeline\docs\open-source-asr-vlm-code-review.md`
- MediaKit CLI 的 VKP 专用模块/源码登记：`%WORKSPACE_ROOT%\video-knowledge-pipeline\docs\mediakit-cli-vkp-reuse-registry-2026-07-15.md`。它把 MediaKit 定位为候选远程媒体能力适配器而非 LiteLLM deployment；首选 PoC 是 `segment-scenes`，真实调用前仍需单独 allowlist、consent v2、计费确认和操作者授权。

Reviewed local source trees:

- `%WORKSPACE_ROOT%\tool-source-review\FunASR`
- `%WORKSPACE_ROOT%\tool-source-review\SenseVoice`
- `%WORKSPACE_ROOT%\tool-source-review\Qwen2.5-VL`
- `%WORKSPACE_ROOT%\tool-source-review\InternVL`
- `%WORKSPACE_ROOT%\tool-source-review\LLaVA-NeXT`
Use `plan-supplemental-frame-sampling` / `plan_supplemental_frame_sampling` after `vision-review-triage` to convert hard ASR/OCR/tagger/route conflicts into local frame recapture items. It writes `supplemental-frame-sampling-plan.json/md` and updates `manifest.frame_recapture.items`; execute with `run-frame-recapture-plan --execute` only when local ffmpeg recapture is desired. This planner does not call cloud vision.
Use `vision-review-queue` / `vision_review_queue` after `vision-review-triage` when many semantic-frame gaps need cloud multimodal review. It writes `vision-review-queue.html/json/md`, `vision-review-queue-run.ps1`, and MCP args. `batch_size` controls images per batch, `max_items=0` means all matching candidates, and failed/incomplete previous vision items are re-queued first. The queue artifacts only expose copyable commands; API calls happen only when an operator runs the generated `-Execute` PowerShell command.
Use `multimodal-sample-review` / `multimodal_sample_review` to create a static human sampling UI for ASR/OCR/ebook/multimodal/final-note quality and `content-candidate-pack` usefulness; content candidate samples include `evidence_citations` / Citation summary when the candidate pack provides them. After saving reviewed notes, run `validate-multimodal-sample-notes` / `validate_multimodal_sample_notes`; it writes `multimodal-sample-review-summary.md/json` plus `human-sample-eval.md/json` with term accuracy, visual fact accuracy, step completeness, timestamp accuracy, keep-image rate, multimodal added-info rate, hallucination/error rate, content-candidate usability/evidence sufficiency rates, and a net-help proxy. This is review evidence only and does not write timeline corrections or approve publication.
`transcript-correction-pack` registers `transcript_correction_pack` as `runs/transcript-correction-pack/run.json`; preview packs are `needs_execution`, missing provider config is `needs_input`, provider failures are `needs_retry`, imported/executed corrections are `completed`, and zero-change corrections become `needs_review`. `run-visual-structure` registers `visual_structure_ebook` as `runs/visual-structure-ebook/run.json`; preview runs are `needs_execution`, successful ebook runs are `completed`, and ebook blockers become `needs_retry` failed items with evidence paths, same-index ebook retry commands, high-res tile recovery, multimodal triage, and review fallback commands. `high-res-tile-plan` registers `high_res_tile_plan` as `runs/high-res-tile-plan/run.json`; preview runs are `needs_execution`, successful tile writes are `completed`, and missing images/Pillow/write failures become `needs_retry` failed items with evidence paths, same-index retry commands, and review commands. `tile-result-import-build` registers `tile_result_import_build` as `runs/tile-result-import-build/run.json`; `tile-result-merge` registers `tile_result_merge` as `runs/tile-result-merge/run.json`; preview runs are `needs_execution`, successful imports are `completed`, and pending/low-confidence/empty tile outputs become failed review items with tile import, tile merge, evidence, and review commands for UI retry/review queues. `timeline-alignment-audit` registers `timeline_alignment_audit` as `runs/timeline-alignment-audit/run.json`; aligned bundles are `completed`, timestamp conflicts are `needs_review`, and missing transcript sidecars are `needs_input`. `build-smart-summary-input-pack` registers `smart_summary_input_pack` as `runs/smart-summary-input-pack/run.json`; `build-smart-summary-chapters` registers `smart_summary_chapter_pack` as `runs/smart-summary-chapter-pack/run.json`; both are `completed` when evidence is clean, `needs_review` when review gaps remain, and `needs_input` when transcript/chapter evidence is missing. `smart-summary-section-workflow` registers `smart_summary_section_workflow` as `runs/smart-summary-section-workflow/run.json`; failed global/section quality checks become `needs_input` section action items for the summary/export queue, with section id, time range, citation count, editor command, and apply command. `smart-summary-section-editor` registers `smart_summary_section_editor` as `runs/smart-summary-section-editor/run.json` and writes `smart-summary-section-editor.html` for same-screen video/transcript/evidence/section editing. `smart-summary-section-apply` registers `smart_summary_section_apply` as `runs/smart-summary-section-apply/run.json`; missing section revisions are `needs_input`, completed staged installs pass through `smart-summary-quality`. `prepare-smart-summary-llm-rewrite` registers `smart_summary_llm_rewrite` as `runs/smart-summary-llm-rewrite/run.json`; status is `needs_input` until `exports/smart-summary.llm.md` is written and installed through `generate-smart-summary-with-codex --input-md`. `run-smart-summary-llm-rewrite` registers/updates `smart_summary_llm_rewrite` run status through `smart-summary-llm-run-status.*`; preview is `planned`, provider failures become retryable status, and successful execution installs only final-marker Markdown. `generate-smart-summary-with-codex` registers `smart_summary_codex` as `runs/smart-summary-codex/run.json`; passed quality gates are `completed`, failed quality checks are `needs_retry` failed items. `export-knowledge-note` registers `knowledge_note_export` as `runs/knowledge-note-export/run.json`; complete exports are `completed`, missing final artifacts/content candidates are `needs_input`, and content candidates without smart-summary chapter links are `needs_review` with a `build-smart-summary-chapters` next action. `video-moment-index`、`long-video-memory-pack`、`video-rag-pack`、`video-rag-search`、`video-rag-service-plan` and `external-capability-pack` also register run artifacts so timeline/RAG queues can show completed, needs_input, needs_review, or needs_execution status. Use `run-artifact-registry` / `run_artifact_registry` to refresh the vsummary-style local run and artifact index for a bundle. It writes `run-artifact-registry.json/md`, `mcp-run-artifact-registry.args.json`, and reads `runs/*/run.json`; it does not execute tasks, call cloud APIs, start services, or process media. `task-console.html` reads this registry into its “任务历史” panel and shows timeline alignment as a “时间错位” metric plus `timeline-alignment-audit.md` artifact link. `vision-review-queue` now registers itself as `runs/vision-review-queue/run.json`, including artifacts, per-index pending/failed items, batch ids/status, suggested retry commands, and retry command metadata for UI/MCP retry panels.

## Update - 2026-07-04 22:53:57 | Codex / GPT-5

External open-source reuse ledger: `docs/external-code-reuse-ledger-2026-07-04.md` is the detailed high-level map for which external project modules have been absorbed into VKP, which CLI/MCP/WebUI entries expose them, and which reuse directions remain worthwhile. Use `docs/external-code-reuse-decision-map-2026-07-04.md` as the shorter decision entry before adding another video AI dependency or copying a larger external subsystem. Use `docs/external-code-reuse-remaining-modules-2026-07-05.md` when deciding the next concrete reuse module: unified video workbench, batch retry UI, transcript arbitration post-processing, long-video summary input pack, video RAG/time grounding, local VLM adapter, or human sampling score UI. Use `docs/external-code-reuse-exhaustion-status-2026-07-05.md` to check which reviewed projects have already been sufficiently absorbed, which modules still deserve another implementation pass, and which whole-project migrations should be avoided. Use `docs/external-open-source-reuse-module-inventory-2026-07-06.md` as the newest module-level inventory before choosing the next external-code reuse task. Use `docs/external-code-reuse-current-module-map-2026-07-06.md` as the shortest current navigation page for absorbed modules, remaining reusable modules, rejected whole-project migrations, and the next implementation order. Use `docs/external-code-reuse-next-module-decisions-2026-07-06.md` when you need the execution-level decision table: module priority, VKP landing point, acceptance standard, and stop condition. Use `docs/external-code-reuse-closure-and-next-actions-2026-07-06.md` as the current compact closure map before deciding whether to keep extracting code from another external project. Use `docs/external-code-reuse-practical-playbook-2026-07-06.md` as the operational playbook for deciding what to copy, what to adapt, what to reject, and how to validate each external-code reuse module. Use `docs/external-code-reuse-next-code-modules-2026-07-06.md` as the execution queue for the next code modules worth reusing, including landing files, acceptance standards, and stop conditions.

- Offline quality route: use CLI offline-quality-route <bundle> --benchmark-manifest <manifest> or MCP offline_quality_route. It only reads existing normalized/postprocessed/corrected transcripts, timeline OCR/vision evidence, and benchmark review state. It never executes models or cloud fallback; every route is proposal-only with auto_execute=false and cloud_allowed=false. review_page_exists=true must not be interpreted as content_reviewed=true.

## Quality execution front doors (2026-07-11)

Use these interfaces instead of manually chaining private modules:

```powershell
.\scripts\video-knowledge.ps1 punctuation-model-stage <bundle>
.\scripts\video-knowledge.ps1 quality-benchmark execute-variants <manifest>
.\scripts\video-knowledge.ps1 quality-benchmark build-summary-review <manifest>
.\scripts\video-knowledge.ps1 quality-benchmark apply-summary-review <private-json> --scores-json <scores-json>
.\scripts\video-knowledge.ps1 transcript-evidence-correction-pipeline <bundle> --asr-json <primary> --secondary-asr-json <secondary>
.\scripts\video-knowledge.ps1 quality-finalize <bundle>
.\scripts\video-knowledge.ps1 targeted-visual-evidence <bundle>
```

MCP equivalents are `punctuation_model_stage`, `quality_benchmark(action="execute-variants")`, `quality_benchmark(action="build-summary-review")`, `quality_benchmark(action="apply-summary-review", scores_json=...)`, `transcript_evidence_correction_pipeline(secondary_asr_json=...)`, `quality_finalize`, and `targeted_visual_evidence`. Summary blind review randomizes old VKP, current VKP, and Get笔记 as A/B/C; the Get笔记 role is evaluation-only and never correction evidence.

Boundaries: preview first; no silent Qwen 1.7B -> 0.6B fallback; second ASR never directly replaces the primary; empty/wrapper-only OCR remains a blocker; online text/vision calls retain explicit execution/preflight gates. See `docs/quality-improvement-execution-chain-2026-07-11.md`.
## Unified Model Task Gateway

- Coverage audit: `model-task-coverage-audit` / MCP `model_task_coverage_audit`.
- Terminology model execution: `run-term-arbitration-model` / MCP `run_term_arbitration_model`.
- BiliNote mind-map model execution: `run-bilinote-mind-map-model` / MCP `run_bilinote_mind_map_model`.
- All three are preview-first. Provider config is runtime-only; `execute=true` is required for provider calls.
- Native whole-video provider upload is available through a consented Gemini Files API route; semantic frames and temporal frame groups remain complementary local evidence.
- Contract and artifacts: `docs/model-task-gateway.md`, `docs/model-task-coverage.json`, `docs/model-task-coverage.md`.

## Video editing handoff

- Use `video-edit-review-pack <webui-bundle>` / MCP `video_edit_review_pack_tool` to build the local-only editing handoff.
- It writes Storyboard candidates, refined edit decisions, artifact validation, preference evidence, and a run-registry entry; existing Workbench exposes the artifacts.
- Active edit decisions must be user-sourced or `confirmed=true`; Storyboard remains review-only and the command never edits media, calls cloud models, publishes, or starts a second FFmpeg/review pipeline.
- Source-level reuse contract: `docs/videocut-kit-vkp-edit-review-pack-2026-07-15.md`.

## Video structure and general tagging update

2026-07-18 19:42:38 +08:00 | Codex / GPT-5

For filmed footage and knowledge-video structure, use the specialized local evidence chain as complementary evidence alongside consented native whole-video execution:

```powershell
.\scripts\video-knowledge.ps1 media-capability-status
.\scripts\video-knowledge.ps1 video-structure <webui-bundle> --media-path <video>
.\scripts\video-knowledge.ps1 highlight-detection <webui-bundle> --query "人物完成关键动作" --media-path <scene-clip>
.\scripts\video-knowledge.ps1 general-tagger-status
.\scripts\video-knowledge.ps1 run-general-tagger <webui-bundle>
```

MCP equivalents are `video_structure`, `highlight_detection`, `general_tagger_status`, and `run_general_tagger`.

`video-structure` combines existing local shot detection and semantic chapter evidence into semantic scenes and storyline roles. `highlight-detection` is a preview-first thin adapter for local Lighthouse CG-DETR or saved-prediction import. Videos longer than 150 seconds must be split into local scene clips before CG-DETR execution. `run-general-tagger` selects RAM++ for general real-world image tagging and preserves Qinglong CL/WD tags as compatibility evidence only.

Native whole-video understanding is available only through the explicitly consented Gemini Files API route; these local commands do not download models, call cloud services, or automatically fall back between local and remote routes. Model outputs remain candidate evidence and cannot overwrite OCR, ASR, human-confirmed facts, Timeline, Bundle, or publication gates. Full contract: `docs/video-structure-and-general-tagger-2026-07-18.md`.

Local RAM++ and CG-DETR execution requires CUDA GPU. Their `auto` device mode may select CUDA but never falls back to CPU; a missing CUDA runtime is an explicit blocker. This GPU-required policy does not apply to local shot detection or semantic evidence fusion.

## Balanced hard-frame escalation gate (2026-07-19)

2026-07-19 16:25:14 +08:00 | Codex / GPT-5

Use `vision-review-triage` / `vision_review_triage` for the production hard-frame gate. Its v2 result remains compatible with v1 queue fields and adds local OCR-confidence, complex-layout, ASR/OCR-conflict, PySceneDetect-boundary, adaptive localized-motion plus explicit-position presenter/PIP frame-change, duplicate-page, and estimated-call evidence. Use `targeted-visual-evidence` when local ebook/OCR/crop/tile stages should run first; it re-triages only after an executed local stage and records pre/post candidate counts.

Static or explicit presenter/PIP-only frame groups must not become temporal model calls solely because a transcript contains operation words. Presenter/PIP regions may be any normalized position and size; unknown localized motion is not automatically labelled presenter. Missing temporal frames enter `temporal_recapture_indexes`; localized motion needs operation/process evidence, while broad change or scene boundaries may become temporal candidates. High-confidence simple OCR stops locally; OCR gaps stay on local document recovery first; complex relational layouts and source conflicts may become one-image semantic candidates. Routing is candidate-only and does not authorize online execution. Existing vision preflight, consent, destination allowlist, call/cost limits, and operator confirmation remain mandatory.

Implementation and research: `docs/open-source-hard-frame-routing-research-2026-07-19.md`.

## Local OCR batch recovery and online production transition (2026-07-19)

2026-07-19 19:12:53 | Codex / GPT-5

- Use `run-visual-structure-ebook-batches <bundle> --execute --batch-size 3` for resumable ebook OCR in short-lived child processes. Successful items are skipped by default; later batches continue after a child failure and the terminal result is `degraded` rather than a false success.
- Use `repair-ebook-artifact-text <bundle>` to replace mojibake Timeline OCR text from verified UTF-8 ebook artifacts without rerunning OCR. It only reads artifact paths inside the bundle, updates the manifest-selected source package, and writes `exports/ebook-artifact-text-repair.json`.
- The default batch production route is `online-production-existing-apis-v1`: Groq ASR, Mistral OCR, SiliconFlow document/single-frame vision, and Gemini temporal/text/summary/correction. It reuses DPAPI secret references, uses six single-deployment remote pools, and has no automatic fallback.
- `scripts/video-knowledge-model-gateway.ps1 status` is the stable local readiness front door for the loopback LiteLLM Proxy at `127.0.0.1:18776`. A ready gateway does not authorize egress. Before every online video run, generate an exact artifact SHA-256 manifest and consent v2 with route revision, call count, cost cap, and destinations.
- Machine progress and intermediate schema fields may be English. Final transcript, Smart Summary, reports, and user-visible error guidance should be Chinese.
- Acceptance and route handoff: `docs/local-production-v1-acceptance-and-online-transition-2026-07-19.md`.

## Shot breakdown, style fingerprint, and imitation-script handoff

2026-07-21 09:25:00 | Codex / GPT-5.6

Use the local-only evidence fusion front door:

```powershell
.\scripts\video-knowledge.ps1 shot-breakdown <webui-bundle> `
  --reference-analysis-json <optional-saved-local-analysis.json>
```

MCP equivalent: `shot_breakdown`.

The command writes `exports/shot-breakdown.*`, `style-fingerprint.json`, `imitation-script.*`, and `shot-imitation-readiness.json`, plus a run-registry entry and Workbench links. It reads existing Timeline, scene boundaries, ASR/OCR, temporal vision, tags, and an optional saved local analysis JSON. It does not decode media, execute a model, call a provider, or mutate Timeline.

All fields are candidate evidence with field-level provenance. Unknown shot language stays `unknown`; imitation fields stay `needs_human_input`. `ready` means only ready for human script review, never ready for automatic media generation or publication. Detailed fixed-commit source review and rejected modules: `docs/shot-breakdown-and-imitation-open-source-review-2026-07-21.md`.

### Filmed pullfilm v2

2026-08-01 20:56:48 +08:00 | Codex / GPT-5.6

For filmed footage, never call `shot-breakdown` before a verified technical-shot artifact exists:

```powershell
.\scripts\video-knowledge.ps1 technical-shot-detection <bundle> --backend autoshot --media-path <video>
.\scripts\video-knowledge.ps1 technical-shot-fusion <bundle> <candidate-a.json> <candidate-b.json> --frame-rate <fps>
.\scripts\video-knowledge.ps1 shot-language-analysis <bundle> --execution-location local --execute
.\scripts\video-knowledge.ps1 video-structure <bundle> --content-profile filmed-v1
.\scripts\video-knowledge.ps1 shot-breakdown <bundle>
.\scripts\video-knowledge.ps1 shot-review-status <bundle>
```

`technical-shot-detection` is strict by default. Chapters, semantic scenes, Timeline rows, and whole-video duration are never accepted as shots. AutoShot is the filmed-footage default candidate; OmniShotCut requires an explicit local checkpoint and is limited to bounded disagreement/transition clips. Multi-detector fusion never auto-selects disputed boundaries.

`shot-language-analysis` directly reuses the fixed Auto Scenes optical-flow/DINO modules. Missing weights, CUDA, low confidence, or invalid output remain `unavailable`/`inferred`; there is no CPU or remote fallback. `video-structure --content-profile filmed-v1` directly reuses ruptures PELT and never assigns story roles from position alone. Lighthouse CG-DETR remains candidate-only until its fixed local dependencies and checkpoint pass a real smoke, and only scene clips up to 150 seconds are eligible.

The existing loopback Workbench embeds fixed WaveSurfer.js Regions assets. Draft edits autosave in localStorage; formal apply requires the CSRF-protected “保存到 VKP” action and writes only a hash-bound reviewed projection. It does not change Timeline or raw evidence. `shot-breakdown` also emits `shot-breakdown.csv` and `shot-breakdown.logseq.md`; the Logseq projection uses nested bullets and does not add `collapsed:: true`.

Full five-field decision record: `docs/decisions/2026-08-01-filmed-pullfilm-v2.md`.
## Review attestation, freshness, generation receipt, and previs import

2026-07-22 11:44:11 +08:00 | Codex / GPT-5.6

Stable local front doors:

```powershell
.\scripts\video-knowledge.ps1 review-attestation-create <bundle> --target <target> --artifact role=path --approved-by <operator>
.\scripts\video-knowledge.ps1 review-attestation-status <bundle> --target <target>
.\scripts\video-knowledge.ps1 import-generation-contracts <bundle> --task <task.json> --receipt <receipt.json> --validation <validation.json> --preflight <preflight.json> --source-root <contract-root>
.\scripts\video-knowledge.ps1 import-previs-candidate <bundle> --scene <scene.json> --capture-manifest <captures.json> --validation <validation.json> --source-root <contract-root>
```

MCP tools:

- `create_review_attestation_tool`
- `review_attestation_status_tool`
- `import_generation_contracts_tool`
- `import_previs_candidate_tool`

Review attestations and dependency snapshots are content-bound. Timeline/export/edit inputs that change after confirmation become stale or invalid, and the existing handoff gate fails closed. Run registry rows expose SHA-256/canonical JSON evidence, dependency freshness, parameters, operator boundary, and artifact rows.

Generation and previs import reuse video-creation commit `27acddc` versioned contracts and its stable verifier CLIs. VKP does not import that repository's private Python modules or reproduce its queue/executor. Imported JSON is copied to `imports/video-creation-contracts` with canonical content-addressed names. Generated outputs, representative frames, and previs captures are local-path/hash checked.

All generation/previs outputs remain candidate evidence. Previs is explicitly synthetic and not an observed source-video fact. These commands do not install generators, execute rendering, call external APIs, upload files, publish, start services, or silently fallback. Full fixed-upstream decisions and verification: `docs/decisions/2026-07-22-video-workflow-second-wave-absorption-review.md`.
## One business authorization for one video workflow

2026-07-22 23:40:00 +08:00 | Codex / GPT-5.6

Use one visible operator confirmation for a predeclared video workflow instead of asking once per derived OCR, vision, correction, or summary artifact.

Stable CLI front doors:

- .\scripts\video-knowledge.ps1 model-business-authorization-create <plan.json> --output-path <authorization.json> --confirm-data-export
- .\scripts\video-knowledge.ps1 model-business-authorization-status <authorization.json>
- .\scripts\video-knowledge.ps1 model-business-child-consent <authorization.json> --stage-id <id> --producer <producer> --artifact <derived-file> --lineage-input <source-or-prior-admission> --max-calls 1
- .\scripts\video-knowledge.ps1 asr-chunk-business-workflow <chunk-manifest.json> <authorization.json> --stage-id <asr-stage> --producer asr_vad_chunking --lineage-input <exact-source-media>

Secure MCP tools are model_business_authorization_status_tool and create_business_child_consent_tool. MCP cannot confirm the parent or override provider, model, URL, credential, destination, or route revision.

The parent locks exact source hashes, Bundle, tasks, producers, route snapshots, destinations, aggregate calls/cost/files/bytes, zero retry, no fallback, no publish, and expiry. A derived file is admitted only inside the Bundle and only through a hash-linked chain from an exact source or prior admission. Every actual upload still receives an exact consent v2 and uses the existing Broker allowlist and atomic call/cost reservation. A new destination, model, route revision, task, producer, source, retry/fallback rule, or higher limit requires a new parent confirmation. Contract: docs/model-business-authorization.md.

## Offline network and token optimization A/B

- Stable module front door: `python -m video_knowledge_pipeline.input_optimization_benchmark {asr,semantic,final}` with `PYTHONPATH=src` in a source checkout.
- It reuses the existing transcript stability evaluator, reads saved connector reports, makes zero provider calls, applies no corrections, and changes no production defaults. See `docs/network-and-token-optimization-2026-07-22.md`.

## VAD-aligned cloud ASR chunk preparation

2026-07-23 00:32:18 +08:00 | Codex / GPT-5.6

Stable local front door:

    .\scripts\video-knowledge.ps1 prepare-cloud-asr-chunks <media> <funasr-vad.json> <output-dir> --max-request-seconds 180 --context-padding-seconds 1.5

- Default is preview-only and writes an ASR VAD chunk manifest.
- --execute invokes the existing local FFmpeg resolver only; it never calls an ASR provider.
- Default artifact profile is 16 kHz mono 64 kbps MP3.
- Each chunk records core/padded bounds, source VAD IDs, exact bytes and SHA-256, and an independent terminal status.
- A degraded run retains successful chunks and lists failed chunks.
- Remote execution must reuse consented_model_batch and exact consent; the chunk preparer is not a provider executor.
- asr_response_quality can consume VAD intervals to find missing speech coverage and emit exact retry windows.
- No automatic retry, provider fallback, local/cloud fallback, upload, or canonical transcript replacement is allowed.

Detailed contract and fixed-source research: docs/asr-vad-chunking-and-gap-recovery-2026-07-23.md.

Optional local-only blind-spot audit, reusing the existing quality-benchmark FFmpeg `silencedetect` implementation:

    .\scripts\video-knowledge.ps1 asr-vad-activity-audit <media> <funasr-vad.json> --execute

- Default without `--execute` is plan-only; execution uses registered local FFprobe/FFmpeg and no network.
- Non-silent audio outside FunASR VAD becomes candidate evidence only because it may be music or noise.
- The audit never changes VAD, chunks, Timeline or transcript and never authorizes upload/retry.
- A passed, content-addressed audit can be bound with `asr-chunk-batch-workflow --activity-audit <audit.json>`.
- Unresolved candidates block that audited workflow; source/VAD/audit hash changes invalidate the gate.

Compare an authoritative FSMN-VAD run with a candidate-permissive run locally:

    .\scripts\video-knowledge.ps1 asr-vad-profile-compare <authoritative-vad.json> <candidate-permissive-vad.json> <activity-audit.json>

- Reuses the existing interval coverage and exact-hash contracts; never runs a model or network call.
- Validates same input/model/revision and genuinely permissive threshold settings.
- Same-model support remains candidate-only and cannot modify authoritative VAD or transcript.
- Without labels it writes a SHA-bound asr-vad-human-labels.template.json.
- Re-run with --labels-path <filled-labels.json> to calculate candidate-screening precision/recall.
- production_default_change_allowed is always false; fixed-sample acceptance remains an explicit operator decision.

After exact consent v2 exists for every completed chunk, compile the existing Broker workflow input locally:

    .\scripts\video-knowledge.ps1 asr-chunk-batch-workflow <chunk-manifest.json> --consent-path <chunk-1-consent.json> --consent-path <chunk-2-consent.json> --bundle-dir <bundle>

- Consent paths must be repeated in chunk order.
- The command validates exact artifact hashes, consent integrity, remaining calls, route revision, destination and explicit zero retry.
- It writes asr-chunk-batch-workflow.json but never submits it.
- The generated submission.arguments are native input for submit_consented_model_workflow_tool.
- The Broker revalidates policy and owns all execution, atomic reservations, concurrency and durable status.

Stable VKP-owned submission front door, reusing the MCP Python SDK and the existing Broker tool:

    .\scripts\video-knowledge.ps1 asr-chunk-batch-submit <asr-chunk-batch-workflow.json>
    .\scripts\video-knowledge.ps1 asr-chunk-batch-submit <asr-chunk-batch-workflow.json> --execute

- Preview is the default. It rebuilds the workflow from the current manifest, artifacts, consents, activity audit and concurrency settings, then rejects any stale identity.
- --execute permits only an explicit loopback HTTP MCP URL ending in /mcp; it never accepts a provider URL or API key.
- VKP sends one control request to submit_consented_model_workflow_tool. The persistent Broker, not the CLI or Agent, owns provider execution and durable batch status.
- The CLI adds no retry or fallback and makes no direct provider request.
- Override the loopback endpoint only when needed with --broker-url http://127.0.0.1:<port>/mcp.

Read the returned job_id through VKP's read-only front door:

    .\scripts\video-knowledge.ps1 asr-chunk-batch-status <model_batch_job_id>
    .\scripts\video-knowledge.ps1 asr-chunk-batch-status <model_batch_job_id> --output-path <terminal-status.json>

- It reuses the same shared loopback MCP client and consented_model_batch_status_tool.
- The call is read-only and makes no provider request.
- An explicit output path stores the original consented_model_batch.v1 payload without wrapping or schema conversion, so it can be passed directly to asr-chunk-batch-merge --batch-status-path.
- The Broker remains the only durable batch state store.

After the existing Broker batch reaches a terminal state, merge saved execution evidence locally:

    .\scripts\video-knowledge.ps1 asr-chunk-batch-merge <workflow.json> --execution-report <chunk-1-report.json> --execution-report <chunk-2-report.json>

Alternatively pass `--batch-status-path <terminal-status.json>`. The merge front door:

- performs no provider call, retry, fallback, upload or batch submission;
- revalidates the workflow, manifest, current chunk bytes/SHA-256, consent identity, route revision and report upload manifest;
- reuses the existing ASR normalizer and TranscriptCue/SRT renderer;
- applies artifact-start offsets and midpoint-based core ownership;
- removes only exact-text strong-time-overlap duplicates;
- exposes non-identical boundary overlaps for human review and preserves successful chunks when another chunk fails;
- writes an independent candidate transcript and never changes the canonical transcript.

Optional text-preserving timestamp alignment after a fully completed merge:

    .\scripts\video-knowledge.ps1 asr-chunk-batch-merge <workflow.json> --batch-status-path <terminal-status.json> --prepare-alignment-plan

- Reuses the existing plan_asr_run preset qwen3-forced-aligner and official Qwen3 ForcedAligner adapter; no alignment model is executed by merge.
- The merged transcript is supplied as the exact alignment transcript. WhisperX remains a separate optional word/speaker evidence route because it performs its own transcription.
- Planning requires a completed merge, the workflow's content-addressed Bundle, and unchanged source media bytes/SHA-256.
- A missing local alignment runtime or plan error is recorded as plan_failed; completed merge JSON/SRT remain intact.
- Alignment output remains a sidecar and cannot replace canonical text automatically.

When the merge report is degraded by VAD coverage gaps, reuse the existing exact-snippet front door directly:

    .\scripts\video-knowledge.ps1 asr-retry-snippets <original-media> <asr-chunk-merge-report.json> <retry-output-dir>

- The adapter reads nested `asr_quality.retry_plan` and verifies source media bytes/SHA-256 first.
- Preview remains the default; `--execute` invokes only the registered local FFmpeg tool.
- Generated snippets are not remote authorization. Each exact hash still requires consent/parent business authorization and Broker execution.
- Saved retry reports continue through the existing `asr_targeted_retry_merge`; no second retry merger or transcript truth source exists.

## Targeted ASR downstream refresh (2026-07-23)

Updated by Codex / GPT-5.6 at 2026-07-23 11:59:16.

A successful `asr_targeted_retry_merge --write` now automatically:

1. invalidates and content-addresses the old Smart Summary for audit;
2. rebuilds local transcript-derived exports with existing VKP modules;
3. prepares the existing summary workflow without executing a model;
4. reruns transcript and Smart Summary quality gates;
5. refreshes review, Quality Console, Task Console, and Video Workbench.

Stable local-only backfill front door:

    .\scripts\video-knowledge.ps1 refresh-transcript-downstream <bundle>
    .\scripts\video-knowledge.ps1 refresh-transcript-downstream <bundle> --no-write

- No network, provider call, upload, API key access, retry, or fallback is performed.
- `needs_summary_regeneration` is expected until an existing consented summary route installs a new summary.
- `full_pipeline_production_qualified=true` requires both the canonical transcript gate and fresh-summary gate to pass.
- Exact behavior and artifacts are documented in `docs/asr-targeted-merge-downstream-refresh-2026-07-23.md`.

## Local media execution receipts and rough-cut candidate import

2026-07-23 12:36:26 +08:00 | Codex / GPT-5.6

Stable local front door:

```powershell
.\scripts\video-knowledge-local-media-contract.ps1 provider-status
.\scripts\video-knowledge-local-media-contract.ps1 speech-receipt --request <speech-request.json> --write
.\scripts\video-knowledge-local-media-contract.ps1 ffmpeg-receipt --request <ffmpeg-request.json> --write
.\scripts\video-knowledge-local-media-contract.ps1 rough-cut-import --request <rough-cut-request.json> --write
```

The receipt commands consume completed local execution evidence; they never start ASR, FFmpeg, llama.cpp, sqlite-vec, a network service, or a provider call. `speech_execution_receipt.v1` is VKP-owned and pins reviewed CrispASR `v0.8.18` commit `9deefe8f47273722415e4b4be5d87361b96177c9`, exact binary/model/input/transcript/word-timestamp hashes, visible GPU/CPU attempts, chunk/overlap/LCS policy and accepted VKP arbitration. `ffmpeg_execution_receipt.v1` binds the existing single outlet, actual argv, exact artifacts, hardware profile and explicit fallback reason.

`rough_cut_finalize_receipt.v1` is imported as candidate evidence only. Transcript, OCR and temporal provenance must be present or explicitly marked as a known gap. Import does not mutate Timeline, human labels, metadata, run-registry truth, publish state, or invoke videocut-kit. llama.cpp `b8644` and sqlite-vec `v0.1.7` are registered candidates only; real benchmark gates remain pending. Details: `docs/local-media-execution-contracts-2026-07-23.md`.
## 2026-07-28 Transcript / Smart Summary Completeness

- Updated: 2026-07-28 12:06:24 +08:00 by Codex / GPT-5.6.
- Intent: stop treating full timeline span or a successful process exit as proof that every speech interval was transcribed.
- Decision: `transcript-quality-gate` now composes the existing ASR response gate with source-hash-bound `silero-vad-candidate.v1`; empty FunASR chunks remain blocked unless the already-installed faster-whisper/Silero v5 route independently proves no speech in their exact intervals.
- Reason: forcing text from verified silence would fabricate content, while ignoring independent speech would hide real omissions.
- Evidence: both current production videos completed full local Silero runs. The second video's empty chunk indexes 1/2/3 overlap no Silero speech and are reported as `passed_with_verified_silence`; no canonical transcript was rewritten.
- Effective scope: local transcript and Smart Summary quality/acceptance only. Use `silero-vad-candidate <media> --output-path <bundle>\silero-vad-candidate.json --execute`, then `transcript-quality-gate <bundle>`, `smart-summary-quality-check <bundle> --summary-path <bundle>\exports\smart-summary.codex.md`, and `acceptance-check <bundle> --no-refresh`.
- `funasr_python_runner` now reuses the existing `media_tools.resolve_media_tool("ffprobe")`, so isolated ASR environments retain correct duration metadata without a global PATH installation.
- Detailed source/commit decisions and five-field change provenance: `docs/transcript-summary-completeness-hardening-2026-07-28.md`.

## 2026-07-28 Untimed Chunk Timing Repair

- Updated: 2026-07-28 12:42:15 +08:00 by Codex / GPT-5.6.
- Intent: preserve complete transcript content while making untimed local ASR chunks navigable and preventing false whole-video retry plans.
- Decision: `asr_adapter` anchors synthetic timing to persisted chunk start/end, labels it `precision=coarse`, and `asr_response_quality` evaluates source-window density only against exact-source Silero speech intervals.
- Reason: synthetic character timing is navigation evidence, not word alignment; whole-media density created 320 false positives on a real 104-minute Bundle.
- Evidence: 326/326 segment IDs/text remained identical; 18 populated chunks passed VAD-conditioned density; retry windows dropped to zero; 37 focused offline tests passed.
- Effective scope: local FunASR/SenseVoice normalization, transcript quality, Smart Summary freshness, acceptance, and export refresh. No provider call, upload, fallback, model download, or transcript-text mutation.
- Detailed record: `docs/transcript-summary-completeness-hardening-2026-07-28.md`.

### Source arbitration timing provenance

- Updated: 2026-07-28 12:48:29 +08:00 by Codex / GPT-5.6.
- Intent / Decision / Reason: preserve the already-normalized coarse chunk timing through the existing local source arbitration because text voting must not erase timing-source identity.
- Evidence: post-export production quality remains `response_quality=passed`, `review_segments=0`, `retry_windows=0`; focused test batches passed 91, 41, and 15 tests.
- Effective scope: `source-arbitrated-transcript.json` transformations and downstream local quality/freshness only. No model or network action.

## 2026-07-28 Source Fidelity And Speaker Diarization

- Updated: 2026-07-28 17:49:09 +08:00 by Codex / GPT-5.6.
- Intent: preserve what the recording actually says and retain anonymous
  speaker clusters through the complete transcript/Summary pipeline.
- Decision: reuse the pinned MOSS `mtd-subtitle` and
  `segments.json(start/end/text/speaker)` contract. Reader labels are
  `说话人N`; optional roles remain separate and names are never guessed.
- Reason: external-world truth checking is not transcript restoration, and a
  text-only merge/dedup can attribute one person's words to another.
- Evidence: MOSS parser two-speaker local smoke plus 213 VKP related tests.
- Effective scope: local normalization, postprocess, arbitration, semantic
  correction, Summary inputs, reader export, and transcript quality gate. The
  MOSS runtime/model remains uninstalled; no network, upload, or fallback.
- Stable check:

      $env:PYTHONPATH = 'src'
      python -m video_knowledge_pipeline.cli transcript-quality-gate <bundle> --require-speaker-diarization --min-speaker-count 2

- Full decision record:
  `docs/audio-source-fidelity-and-speaker-diarization-2026-07-28.md`.

### Reader metadata follow-up

- Updated: 2026-07-28 18:44:00 +08:00 by Codex / GPT-5.6.
- Intent / Decision / Reason: reuse manifest identity, the existing source-path
  resolver, stdlib `mimetypes`, and transcript quality-gate speaker evidence so
  an audio-only Bundle is not labeled as video and participant count is not
  invented by a summary model.
- Evidence: 45 export/speaker tests plus 20 Summary selector/install tests
  passed; `.ogg`, `.mp4`, explicit business type, and observed-vs-declared
  speaker counts are covered.
- Effective scope: final reader Markdown metadata only; no probe, model,
  transcript mutation, identity inference, network, or upload.

## 2026-07-28 Exact ASR chunk manifest and silence snapping

- Updated: 2026-07-28 19:33:57 +08:00 by Codex / GPT-5.6.
- Intent: make resumable local ASR safe for non-equal chunks and avoid cutting
  speech at a blind fixed-duration boundary.
- Decision: reuse pinned Subtitle Edit
  `OpenAiSttChunker` @ `1517bb5c23e1c4072ea829edbc8d08e27cf79289`;
  persist `audio_chunk_manifest.v1`; bind checkpoints to its revision; expose
  `--chunk-boundary-mode silence_snap` as opt-in while preserving
  `fixed_duration` as the default.
- Reason: `index × chunk_seconds` cannot represent silence-adjusted windows,
  and a mature tested boundary algorithm is preferable to a new VKP one.
- Evidence: mapped upstream boundary cases, 18 focused tests, 81 expanded ASR
  tests, and a real local FFmpeg smoke producing exact 43/35/42-second 16 kHz
  mono chunks.
- Effective scope: local FunASR/SenseVoice chunk planning, checkpoint identity,
  targeted retry and timing normalization only. No model, download, network,
  upload, provider fallback or canonical transcript mutation.
- Detailed record:
  `docs/asr-silence-snapped-chunk-manifest-2026-07-28.md`.

## 2026-07-28 Evidence-bound Smart Summary Global Reduce

- Updated: 2026-07-28 20:20:27 +08:00 by Codex / GPT-5.6.
- Intent: preserve explicit time and evidence lineage from semantic chapter Map outputs through the final global Reduce.
- Decision: adapt pinned LlamaIndex `TreeSummarize` repack/recursive-reduce architecture while retaining VKP Workflow, revisions, provider gateway and Bundle as the only owners. `exports/smart-summary-chapter-fact-pack.json` is a deterministic projection, not a second state machine.
- Reason: chapter Markdown alone discarded `evidence_id`, `source_kind` and `review_gap_not_fact` before Reduce; repeating every long evidence ID on every fact also exceeded the 60,000-character budget.
- Evidence: 18 focused and 42 expanded offline tests pass. Existing 6/11-chapter Bundles complete no-write preflight at 39,314/57,945 characters with all chapters included and no model call.
- Effective scope: `run-smart-summary-global-reduce` prompt/audit/quality only. Review-gap text outside the pending-review section fails `review_gap_not_promoted`; this preserves speaker meaning and does not perform external-world fact checking. No transcript, Timeline, provider, consent, upload or fallback change.
- Contract and source proof: `docs/smart-summary-chapter-fact-pack-global-reduce-2026-07-28.md`.

## 2026-07-28 Explainable human key-point recall

- Updated: 2026-07-28 20:52:50 +08:00 by Codex / GPT-5.
- Intent: replace an opaque Smart Summary bigram score with auditable,
  per-key-point recall decisions.
- Decision: directly reuse pinned Jieba `lcut(HMM=False)` commit
  `1e20c89b...` and RapidFuzz `process.extractOne`,
  `fuzz.token_set_ratio` / `fuzz.WRatio` commit `edf9f3c...`. Explicit
  human `aliases` are the only semantic-equivalence authority.
- Reason: lexical algorithms can tolerate punctuation and word-order drift but
  cannot prove two claims have the same meaning.
- Evidence: RapidFuzz upstream 10 tests; VKP 13 focused, 47 Smart Summary, and
  33 Knowledge Export tests pass. Two real Bundles remain correctly blocked
  because no independent human gold set exists.
- Effective scope: `smart-summary-quality-check` only. It reads
  `<bundle>\exports\human-key-points.json`, emits structured decisions under
  `quality_metrics.human_key_point_recall`, and never edits transcript,
  summary, Timeline, provider, consent, or upload state.
- Contract and source proof:
  `docs/smart-summary-human-keypoint-evaluation-2026-07-28.md`.

## 2026-07-28 Human key-point review writeback

- Updated: 2026-07-28 21:28:42 +08:00 by Codex / GPT-5.6.
- Intent: let an independent human gold set close the explainable Smart
  Summary recall gate without creating a second review system.
- Decision: reuse the existing `review.html` localStorage draft,
  `review_http` loopback/CSRF/revision checks, `review_writeback` bundle lock,
  Timeline bindings and the retrieval gold-set `human_confirmed + source SHA`
  pattern. Only explicitly checked, non-empty, Timeline-bound rows are merged
  into `exports/human-key-points.json`.
- Reason: a model candidate or generated summary cannot promote itself into
  the standard used to grade its own recall; optional gold-set metadata must
  also never block unrelated transcript/OCR review.
- Evidence: 23 focused offline tests cover UI fields, draft/writeback,
  malformed and unbound rows, merge preservation, SHA lineage, explicit alias
  recall, speaker preservation and the four user-confirmed corrections.
- Effective scope: local review and Smart Summary evaluation metadata only.
  It does not alter transcript, Timeline facts, summary prose, provider route,
  consent, upload or external-world fact checking.
- Stable entry: start the existing loopback review UI, select
  `人工关键点`, explicitly confirm rows, then click `保存到 VKP`.


## 2026-07-28 Local sherpa-onnx speaker diarization evidence

- Updated: 2026-07-28 22:48:04 +08:00 by Codex / GPT-5.6.
- Intent: add required multi-speaker labels to any existing timed transcript without replacing its ASR engine.
- Decision: reuse pinned sherpa-onnx official CLI commit `75e1fc31...` for segmentation/embedding/clustering and independently adapt pinned WhisperX `5f2f9d4...` maximum-overlap assignment. Both upstream provider flags default to `cuda`; no CPU fallback, nearest fill, download, or transcript overwrite is permitted.
- Reason: speaker diarization is an evidence branch, not another transcript truth source. Re-running ASR or inferring the nearest speaker across silence would weaken source fidelity.
- Evidence: 5 offline tests pass for official-output parsing, overlap/ambiguity/conflict handling, exact artifact hashes, CUDA argv, fail-closed mutation checks, and byte-identical source transcript preservation.
- Effective scope: `python -m video_knowledge_pipeline.speaker_diarization_evidence {plan,run}` writes only `transcripts/speaker-diarization/*` candidate artifacts. Runtime remains unavailable until the CLI and two ONNX models are installed and a real CUDA A/B is approved.
- Detailed record: `docs/sherpa-onnx-speaker-diarization-adapter-2026-07-28.md`.


## 2026-07-28 GetBrain speaker-timestamp transcript import

- Updated: 2026-07-28 22:56:00 +08:00 by Codex / GPT-5.6.
- Intent: consume exported consultation transcripts that already contain anonymous speakers and true start times.
- Decision: before generic TXT/Markdown fallback, detect `说话人N HH:MM:SS`; reuse existing VKP timestamp/speaker/Cue contracts and adapt the pinned MOSS source-field separation pattern.
- Reason: the old fallback created separate zero-duration pseudo rows for title, speaker header and body; rerunning diarization would duplicate already-present evidence.
- Evidence: 14 offline parser/source-fidelity tests pass. Both the user-provided raw export and combined GetBrain Markdown were read-only parsed as 433 segments, two speakers, and 0–3529 seconds; the summary preamble was excluded and raw ASR wording retained.
- Effective scope: local TXT/Markdown import only. The next source start supplies the previous end; final end remains unknown; non-monotonic times are flagged, never sorted. No correction, role inference, model, network, upload, or sensitive transcript persistence.
- Detailed record: `docs/getbrain-speaker-timeline-import-2026-07-28.md`.

## 2026-07-28 pyannote speaker-aware transcript stability evaluation

- Updated: 2026-07-28 23:35:26 +08:00 by Codex / GPT-5.6.
- Intent: detect speaker swaps, missing speaker coverage, and false speaker coverage that text-only transcript distance cannot see.
- Decision: directly reuse pinned pyannote.metrics `DiarizationErrorRate` and Hungarian optimal mapping; expose it as the optional `evaluation` extra and an explicit `--require-speaker-attribution` gate.
- Reason: anonymous speaker labels cannot be compared by their literal names, and an evaluation dependency must not become a core runtime or a second diarization service.
- Evidence: upstream official 12/12 tests, VKP focused 24/24 plus one optional skip, and isolated real-pyannote 7/7 pass. A local user-provided pair parsed as 433/433 segments, two speakers, 3529 seconds, text distance 0 and DER 0; only aggregate metrics were recorded.
- Effective scope: local evaluation reports only. The report anonymizes mappings and excludes transcript text; no ASR, semantic correction, summary, routing, model, network, or upload changes.
- Strict boundary: summary-only Markdown is rejected; production references still require the exact media SHA-256 → GetNote ID → reference SHA-256 binding. The one local sample used explicit `legacy_unbound` because its export has no GetNote ID.
- Install: `python -m pip install -e ".[evaluation]"`.
- Detailed record: `docs/pyannote-speaker-aware-transcript-evaluation-2026-07-28.md`.

## 2026-07-29 MeetEval speaker-attributed transcript text evaluation

- Updated: 2026-07-29 00:01:13 +08:00 by Codex / GPT-5.6.
- Intent: detect text assigned to the wrong anonymous speaker even when total text distance and diarization duration appear correct.
- Decision: directly call pinned MeetEval commit `184ff17eb77fd6db4aba27a9e303a6a3edb09364` `cp_word_error_rate` and `tcp_word_error_rate`; feed existing normalized Chinese character tokens, so VKP exposes the results as cpCER/tcpCER rather than misleading whitespace WER.
- Reason: permutation assignment, edit distance, time constraints and speaker-count accounting are mature upstream algorithms; VKP must not reimplement them or add another tokenizer/model.
- Evidence: official upstream source built on Windows/Python 3.12; 30 related tests passed and one unrelated external-Perl test was deselected. VKP global associated tests passed 30 with 3 optional skips; isolated real-MeetEval integration passed 21. The local user pair produced 12,090/12,090 character tokens, two speakers, cpCER=0 and tcpCER=0.
- Effective scope: explicit local transcript stability evaluation only. Reports omit transcript text, tokens, real labels and identity; no ASR, correction, Summary, model, network, upload or fallback change.
- Install: `python -m pip install -e ".[evaluation]"`.
- Detailed record: `docs/meeteval-speaker-transcription-evaluation-2026-07-29.md`.


## 2026-07-29 NarratoAI low-level audio recovery candidate

- Updated: 2026-07-29 00:23:42 +08:00 by Codex / GPT-5.6.
- Intent: recover an auditable local sidecar for low-level ASR failure chunks without amplifying verified silence into a false transcript source.
- Decision: adapt the pinned NarratoAI commit `0a5dcf5f21f7f40ca77bc38ea6d1d3fd52e32c26` two-pass FFmpeg EBU R128 `loudnorm` algorithm behind `python -m video_knowledge_pipeline.audio_loudness_recovery {plan,prepare}`. Reuse VKP `audio_silence_probe`, media-tool resolver, hashing and atomic storage; reject MoviePy/pydub/numpy, simple-gain and MP3 fallback.
- Reason: loudness and non-silence do not prove speech. Any rendered 16 kHz mono PCM sidecar therefore remains `candidate_only`, `speech_proven=false`, and `asr_retry_authorized=false` until independent speech VAD or human confirmation.
- Evidence: 24 focused tests passed with 2 optional MeetEval skips; the expanded ASR/VAD/speaker set passed 75 with 3 optional skips. Ruff and compileall passed. Real local FFmpeg smoke blocked three seconds of silence before normalization and rendered a low-level 440 Hz sine sidecar while still refusing to call it speech.
- Effective scope: local candidate WAV/JSON only. Source audio, canonical ASR, speaker labels, transcript, provider routes, network, upload and fallback remain unchanged.
- Detailed record: `docs/narratoai-low-level-audio-recovery-adapter-2026-07-29.md`.

## 2026-07-29 00:57:47 | Codex / GPT-5.6 — Low-level candidate speech validation

- Stable entry: `python -m video_knowledge_pipeline.audio_loudness_recovery_validation <recovery-report.json> [--execute-vad] [--chunk-manifest <manifest.json> --chunk-index N]`.
- Intent: confirm that a loudness-recovered candidate contains speech before any targeted ASR retry is planned.
- Decision: reuse the existing faster-whisper/Silero candidate adapter and content-addressed `audio_chunk_manifest.v1`; do not add another VAD, ASR runner or state machine.
- Reason: loudness/non-silence is not speech evidence, and a retry without exact parent/chunk lineage can merge text at the wrong time.
- Evidence: pinned faster-whisper `ed9a06cd89a93e47838f564998a6c09b655d7f43`; 22 focused tests, 54 expanded tests, Ruff/compileall, and real local JFK/sine smoke.
- Effective scope: local plan artifacts only. `targeted_retry_planned` still has `automatic_execution=false`; no network, upload, fallback, transcript write or speaker inference.
- Required consumer rule: inspect `status`, manifest recorded/computed revision, source/chunk SHA-256 and `targeted_retry_recommended`; never treat `ok=true` alone as authorization.
- Source-fidelity boundary: the current recording's four human-confirmed corrections remain scoped to that recording, final output must retain anonymous speaker labels, and Smart Summary checks source fidelity rather than external-world truth.

## 2026-07-29 FunASR CAM++ speaker-readiness gate

- Updated: 2026-07-29 01:28:27 +08:00 by Codex / GPT-5.6.
- Intent: make required anonymous speaker labels an executable local capability rather than a configuration-only claim.
- Decision: reuse the installed FunASR/SenseVoice runner and its existing local-model resolver. When `spk_model` is explicitly requested, `plan-asr` now requires a prepared CAM++ path and reports `model_readiness.speaker`; a missing model blocks before subprocess execution.
- Reason: fixed FunASR commit `516c4f770496a5cbb89c8e2e447211bbb7b0db71` can otherwise resolve/download the speaker model only at runtime, which would violate VKP fail-closed and no-silent-download boundaries.
- Evidence: current no-write cache status reports SenseVoice/FSMN-VAD/CT-Punc ready and CAM++ `missing_or_not_downloaded`; 63 linked ASR, source-fidelity, and final-reader tests pass.
- Effective scope: FunASR-family local plans with explicit diarization only. Existing non-diarization plans are unchanged; no model download, inference, network, upload, or role inference occurred.
- Stable status check: `$env:PYTHONPATH='src'; $env:LECTURE_ASR_PYTHON=(Resolve-Path '.conda-lecture-asr\python.exe').Path; python -m video_knowledge_pipeline.cli asr-model-cache-status . --include-optional --no-write`.
- Safe CAM++ preview: `python -m video_knowledge_pipeline.cli prepare-asr-model-cache . --models 'cam++' --device cuda --no-write`. The preview reports `hub=modelscope`, official model IDs, the isolated Python command, and `network_access=disabled`; it never downloads.
- Explicit download boundary: only add `--execute --allow-download` after operator approval. VKP reuses FunASR's native ModelScope alias/downloader and never accepts an arbitrary model URL here.
- CAM++ A/B trial: the existing `asr-ab-sample-plan/run/compare` matrix now includes `sensevoice_full_punc_campp`, fixed to CUDA and the same SenseVoice/VAD/ITN/punctuation settings as `sensevoice_full_punc`. Missing CAM++ blocks before the ASR runner; reports include anonymous speaker count and labeled-duration coverage.
- Dialogue A/B production gate: when the bounded evaluation reference contains two or more anonymous speakers, `asr-ab-compare` now separates `primary_recommendation` (text baseline) from `production_recommendation`. A candidate must label every spoken segment and meet the reference speaker count; otherwise status is `primary_text_ready_speaker_diarization_pending` and production remains blocked. This reuses existing transcript parsing, speaker identity and A/B metrics; it does not infer roles or import reference text as correction evidence. Real CUDA text baseline completed on the fixed 300-second sample; full ASR plus speaker-gate regression passed 60/60.
- Speaker-preserving fixed reference window: use `scripts\video-knowledge.ps1 transcript-reference-window <transcript> <output.json> --start-seconds <s> --end-seconds <s> [--human-corrections-json <exact-source-SHA-bound.json>]`. It reuses the canonical transcript parser and human-confirmed semantic-correction engine, preserves source segment IDs/order/anonymous speakers, rebases timestamps for the extracted A/B sample, and returns only a hash/count receipt on stdout; the text-bearing JSON remains local and evaluation-only. Unconfirmed, global, structural, or source-hash-mismatched corrections fail closed.
- Production gate: run the existing `video_knowledge_pipeline.transcript_stability_evaluation` with exact reference binding plus `--require-speaker-attribution --require-speaker-transcription` to obtain pinned pyannote DER and MeetEval cpCER/tcpCER. A/B output remains candidate-only and cannot infer speaker roles or replace the canonical transcript.
- Detailed record: `docs/audio-source-fidelity-and-speaker-diarization-2026-07-28.md`.

## 2026-07-29 08:32:08 FunASR 1.3.30 CAM++ real GPU checkpoint

- Intent: verify anonymous two-speaker transcription locally while preserving the user's recording-specific source-fidelity corrections.
- Decision: directly reuse reviewed FunASR release snapshot `16cd165ac3946cc8c08bf845331f91fefec8e1a9` (`1.3.30`) plus existing VKP A/B, pyannote.metrics and MeetEval adapters. No diarization, VAD or metric algorithm was copied.
- Reason: the old `1.3.9` runtime reproduced the upstream None timestamp-boundary failure; `1.3.30` completed the same CUDA sample. VKP also had to preserve numeric `spk=0` instead of treating it as missing.
- Evidence: upstream focused 13/13; real 300-second CUDA chunk 1/1; normalized 168/168 spoken segments labeled across two anonymous clusters. After three recording-scoped human source-fidelity corrections, quality remains below production: DER `0.24396667`, cpCER `0.36036036`, tcpCER `0.52852853`.
- Effective scope: `sensevoice_full_punc_campp` is `speaker_evaluation_candidate` only. `production_recommendation=blocked_until_speaker_quality_evaluation_passes`; no identity/role inference, upload, provider call, canonical transcript overwrite or external-world insurance fact checking.
- Current model cache: `%USERPROFILE%\.cache\modelscope\hub\models\iic\speech_campplus_sv_zh-cn_16k-common`.
- Reviewed source snapshot: `%WORKSPACE_ROOT%\source-reviews\FunASR-1.3.30-16cd165`.
- Fail-closed production-gate artifacts: `.local/campp-two-speaker-trial-20260729/campp-human-confirmed-pyannote-production-gate.json` and `.local/campp-two-speaker-trial-20260729/campp-human-confirmed-meeteval-production-gate.json`; both record `status=failed` at the required 0.05 thresholds.

## 2026-07-29 09:32:03 MOSS exact-window A/B integration

- Intent: compare the already-reviewed MOSS model-native speaker transcript with CAM++ on the same bounded local audio instead of introducing another diarization implementation.
- Decision: register `moss_transcribe_diarize` in the existing `asr-ab-sample-plan/run/compare` path and delegate command construction, model/runtime readiness, execution, normalization and logs to `plan_asr_run` / `run_asr_plan`. The shared command resolver now discovers the existing `.local/moss-runtime-py312/Scripts/mtd-subtitle.exe` without requiring a repeated environment variable.
- Reason: upstream `mtd-subtitle` owns inference and writes raw `segments.json` with `postprocess=False`; label coverage alone cannot choose between MOSS and CAM++, so multiple ready candidates remain blocked until the existing pyannote DER and MeetEval cpCER/tcpCER comparison passes.
- Evidence: pinned OpenMOSS commit `eda4b9f13f1574765a80438c9797780a9bd48112`; upstream parser/export/postprocess tests re-executed `18/18`; all MOSS-focused VKP tests passed `12/12` and the final associated ASR/speaker suite passed `88` with `3` optional skips. Stable preview found the launcher but correctly reported `missing_python_dependency:transformers`, model `unknown_or_not_downloaded`, and `does_not_fallback_to_another_asr=true`; no inference or upload occurred.
- Effective scope: local five-minute A/B planning, readiness display and candidate metadata only. SenseVoice remains primary; CAM++ remains candidate-only; no dependency/model install, download, ASR execution, remote call, role inference, transcript promotion or fallback is enabled.

## 2026-07-29 10:06:33 MOSS model-cache content gate

- Updated by Codex / GPT-5.6.
- Intent: prevent an empty Hugging Face repository shell, interrupted shard set, or Git LFS pointer from being reported as an installed MOSS model.
- Decision: directly reuse installed `huggingface_hub 0.30.2` `scan_cache_dir`, then validate the exact configuration, processor, tokenizer, remote-code modules and complete weight layout required by pinned MOSS commit `eda4b9f13f1574765a80438c9797780a9bd48112`.
- Reason: a matching directory name proves neither a complete snapshot nor offline loadability; the former name-only check could let a long ASR run reach model loading or implicit-download behavior before failing.
- Evidence: the real local scanner inspected `%LOCAL_MODEL_ROOT%\huggingface\hub`, found no MOSS snapshot, and reports `ready=false`, `status=unknown_or_not_downloaded`, `network_access=disabled`. Empty snapshots, incomplete indexed shards and Git LFS pointers fail closed; 16 focused tests and the 93-pass / 3-optional-skip associated speaker/source-fidelity suite passed.
- Effective scope: MOSS readiness metadata only. No package/model install, download, model load, audio inference, network request, role inference, fallback or transcript promotion is performed.
- Source-fidelity boundary: the recording-scoped human decisions are `根排期来的嘛 → 根据排期来的嘛`, `会义纪要 → 会议纪要`, `发了一分材料 → 发了一份材料`, and `星合系统 → 星河系统`. Final transcript output requires anonymous `说话人1/说话人2`; Smart Summary restores the speakers' meaning and does not adjudicate external insurance truth.

## 2026-07-29 11:07:11 CAM++ known-speaker-count diagnostic

- Updated by Codex / GPT-5.6.
- Intent: determine whether the fixed two-speaker sample is failing because CAM++ estimates the speaker count incorrectly or because clustering, segmentation, and speaker-text attribution are inaccurate.
- Decision: directly expose FunASR `1.3.30` upstream `spk_kwargs.cb_kwargs.merge_thr` and `generate(preset_spk_num=...)` through the existing local runner and chunk wrapper. The fixed-sample `sensevoice_full_punc_campp_oracle_2` variant is explicitly evaluation-only and is reported under `speaker_diagnostic_variants`; it cannot satisfy the production speaker gate.
- Reason: a known speaker count is ground-truth leakage for ordinary production audio. It is useful as a diagnostic upper bound but must not be silently promoted into a route default.
- Evidence: pinned release snapshot `16cd165ac3946cc8c08bf845331f91fefec8e1a9`; real 300-second CUDA run completed 168 segments with two anonymous clusters and 168/168 labeled spoken segments. DER remained `0.24396667`, identical to automatic CAM++, while cpCER/tcpCER were `0.36261261/0.53078078`, slightly worse than `0.36036036/0.52852853`.
- Effective scope: local A/B diagnostics only. No default-route change, role inference, transcript promotion, model download, network request, upload, or fallback. Production remains `blocked_until_speaker_quality_evaluation_passes`.

## 2026-07-29 12:11:59 ll-video-decomposer read-only producer

- Updated by Codex / GPT-5.6.
- Intent: expose existing VKP evidence as an auditable five-layer decomposition report for downstream creative planning.
- Stable CLI:
  - `scripts\video-knowledge.ps1 video-decomposition-report <bundle>`
  - `scripts\video-knowledge.ps1 video-decomposition-status <bundle> --no-write`
  - `scripts\video-knowledge.ps1 video-decomposition-compare <report...> --output-dir <dir>`
- Contract: `video_knowledge_pipeline.video_decomposition_report.v1`; consumer-required fields are `report_id/title/source_artifacts/modality_coverage/findings/structure_segments/creative_strategy/report_sha256`.
- Artifacts: `exports/video-decomposition-report.json/.md`, `exports/video-decomposition-report-status.json/.md`, and `mcp-video-decomposition-report.args.json`.
- Decision: directly reuse canonical transcript selection, artifact dependency snapshots, canonical JSON hashing, atomic Bundle writes and Workbench cards. The report is a derived projection and never registers a run.
- Evidence discipline: findings are `confirmed|inferred|unavailable`; inferred needs multiple evidence items and cannot replace confirmed; unavailable carries only `missing_evidence`; BGM identity, author identity, behind-the-scenes data and performance metrics require direct evidence.
- Multi-video route: 2–4 reports use a comparison table; 5+ use per-video cards plus a uniform matrix.
- Hard boundary: no ASR, FFmpeg/ffprobe, model execution, provider call, link download, tool scan, cookie access, second state machine/index, Timeline/transcript/evidence mutation, network, upload or publish.
- Detailed record: `docs/ll-video-decomposer-adapter-2026-07-29.md`.
## 2026-08-02 Smart Summary reader plan v1

- Updated: 2026-08-02 10:50:49 +08:00 by Codex / GPT-5.6.
- Stable entry: `scripts\video-knowledge.ps1 smart-summary-global-reduce <bundle> [--provider-config <json>] [--execute|--reuse-candidate]`.
- Intent: make an online model produce a mature, evidence-bound summary instead of free-form Markdown that merely passes layout checks.
- Decision: the provider returns `video_knowledge_pipeline.smart_summary_reader_plan.v1` JSON; VKP validates JSON Schema, evidence eligibility, mutually exclusive time ranges, actionable actions and exact transcript quotes, then renders reader Markdown locally.
- Reason: providers should decide meaning and organization; VKP should own system-known facts, evidence, formatting and installation safety.
- Evidence: official python-jsonschema validator suite 303/303; VKP focused suite 24/24; expanded Smart Summary/export suite 60/60. Two real bundles retain all 6/6 and 11/11 chapters while Reduce inputs shrink from 52,402→36,225 and 74,482→57,789 characters.
- Effective scope: new global Reduce candidates and final Smart Summary semantic quality. It does not modify Timeline, canonical transcript, chapter fact packs, provider authorization, or existing summaries unless an explicitly authorized call passes every gate.
- New artifacts: `exports/smart-summary-reader-plan.json`, raw provider response, candidate Markdown, and the existing Reduce report. Legacy Markdown candidates remain explicit compatibility mode only; malformed or unsupported model output fails closed.
- Detailed record: `docs/decisions/2026-08-02-smart-summary-reader-plan-v1.md`.
## 2026-08-05 Shared model-provider-gateway adapter

- Updated: 2026-08-05 23:10:00 +08:00 by Codex / GPT-5.6.
- Stable module: `video_knowledge_pipeline.model_provider_gateway_adapter`.
- Optional install: `pip install -e .[shared_gateway]`; pinned public AGPL execution commit `c5f3ec49644453e0cddb56350e3b243b49e0f7da`.
- Intent: share reviewed presets and canonical LiteLLM text/vision execution contracts without duplicating VKP's gateway state machine.
- Decision: exact remote proxy profiles only. `vkp_execution_request_to_shared` requires existing shared consent plus VKP Broker reservation receipt hash and only builds a request; it never resolves a secret or executes a Provider. Multi-member routes require explicit profile selection.
- Reason: OpenAI compatibility is a protocol property, while VKP business authorization, Bundle lineage and Broker reservation remain owner-only decisions.
- Evidence: shared gateway 53/53 double-run tests, text/vision loopback parity, build and redaction/path scans; VKP adapter 10/10 focused tests.
- Effective scope: optional config/request projection. VKP Timeline, Bundle, route revision, business authorization, consent v2, Broker execution and audit remain authoritative. Shared Wave 1 ASR/OCR remain blocked.
- Detailed record: `docs/model-provider-gateway-adapter-2026-08-05.md`.

## 2026-08-09 material-manifest.v1 production adapter

- Updated: 2026-08-09 11:25:00 +08:00 by Codex / GPT-5.6 Sol.
- Stable CLI: `python -m video_knowledge_pipeline.cli material-manifest <bundle>` and `material-manifest-validate <bundle>`.
- Intent: expose VKP canonical transcript, keyframes, temporal evidence and Bundle metadata through the shared `material-manifest.v1` facade.
- Decision: reuse `creative_contract_bridge`, canonical transcript selection, artifact hashes, dependency snapshots and atomic writes. The adapter emits Bundle-relative references only and declares source order as `video_temporal_only`.
- Reason: WCF owns mixed document-node ordering; VKP owns temporal video evidence. A thin reference envelope avoids copying either manifest/state machine and prevents metadata from becoming execution authority.
- Evidence: positive fixture plus version/hash drift, missing/out-of-range frame, stale Bundle, wrong source order, corrupt input and byte-identical double-run regressions. No Provider, key, upload or service is involved.
- Effective scope: derived `exports/material-manifest.v1.json` only. It never mutates Timeline/native manifest, embeds transcript text, grants consent/review approval, registers a run, or permits fallback/publishing.
- Rollback: stop invoking the two CLI commands and remove the adapter/schema; all native Bundle artifacts remain unchanged.
- Detailed record: `docs/material-manifest-v1-adapter-2026-08-09.md`.

## 2026-08-10 Recording-global anonymous speakers and local cross-video candidates

- Intent: keep one anonymous speaker ID across ASR chunks and optionally compare explicitly selected recordings locally.
- Decision: reuse pinned FunASR `1.3.30` centroid mapping (`16cd165ac3946cc8c08bf845331f91fefec8e1a9`) plus the existing VKP overlap-agreement module. Do not implement another speaker embedding model.
- Reason: chunk-local CAM++ labels are not stable across independently executed chunks; voice embeddings are biometric data and require local-only, explicit, deletable storage.
- Evidence: upstream mapping test passed; VKP regressions cover swapped local labels, same-chunk anti-collapse, missing-center fail-closed, public/private separation, self-match exclusion, explicit role binding and delete.
- Effective scope: `speaker-global-align` writes an anonymous public alignment and a local biometric `.private.json` sidecar. `speaker-voiceprint enroll|match|bind-role|delete` is opt-in; matching reports only suspected sameness and never assigns identity automatically.
- Rollback: remove the private sidecar/registry or stop consuming `speaker_global_id`; readers retain backward compatibility with `speaker/spk`.
- Commands: `python -m video_knowledge_pipeline.cli speaker-global-align <chunked-output.json>` and `python -m video_knowledge_pipeline.cli speaker-voiceprint --help`.
- Detailed record: `docs/speaker-global-alignment-and-cross-video-voiceprint-2026-08-10.md`.

## 2026-08-10 Dual-track subtitle editor

- Updated: 2026-08-10 18:14:34 +08:00 by Codex / GPT-5.6 Sol.
- Stable preparation: `scripts\video-knowledge.ps1 prepare-subtitle-editor <bundle>`.
- Review server: `scripts\start-review-webui.ps1 <bundle>` then open `/subtitle-editor`.
- Offline validation/apply: `validate-subtitle-review` and `apply-subtitle-review --review-json <path>`.
- Contracts: `video_knowledge_pipeline.subtitle_editor_projection.v1`, `subtitle_review_notes.v1`, `human_reviewed_subtitle_track.v1`, and `subtitle_review_apply_receipt.v1`.
- Upstream: Moyf/moys-asr-workflow v1.3.1 commit `949bc84058cdae1d9c021c50203e6d2742f9392c`, AGPL-3.0-only; only the eight root `web/` assets are vendored.
- Intent: reuse the complete upstream player/waveform/subtitle/workspace editor while giving VKP Cantonese-source and Mandarin-translation tracks with one shared timeline.
- Decision: browser drafts are isolated by Bundle/source hash; formal apply requires loopback CSRF plus exact projection lineage and writes derived sidecars only.
- Reason: editing convenience must not create a second transcript truth or overwrite raw ASR, Timeline, translation evidence, or media.
- Evidence: upstream JavaScript tests 92/92; VKP contract/HTTP tests 10/10; related editor/review/workbench/translation/speaker/freshness tests 33/33; local Chrome Playwright draft/apply/revision-conflict tests 2/2.
- Effective scope: local subtitle review, source/translation SRT/VTT/ASS, OTIO/FFconcat/kept-range plans, and downstream stale markers. No Provider, upload, model, FFmpeg execution, publish, or arbitrary sticker path.
- Rollback: stop invoking the new commands/routes and continue using `transcript-editor.html`.
- Detailed record: `docs/moys-asr-workflow-subtitle-editor-integration-2026-08-10.md`.
