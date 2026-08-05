# Unified Model Task Gateway

Updated: 2026-07-15 13:15:34 | Codex / GPT-5

## Purpose

`model_task_gateway` is the task-aware front door for model execution. It keeps
task identity separate from provider transport:

```text
task -> model_type -> model_task_gateway -> model_runtime_client -> LiteLLM Proxy -> provider
```

The lower layers remain reused rather than rewritten:

This audit covers tasks that require a generative/online-capable model. Local specialist engines such as SenseVoice, Qwen3-ASR, FunASR ct-punc, ebook/RapidOCR, VAD, and forced alignment remain local runtime engines and are intentionally not counted as online LLM tasks.

- Text: LiteLLM Proxy; built-in OpenAI-compatible is explicit legacy only.
- Vision: LiteLLM Proxy; Gemini/OpenAI-compatible legacy and local Qwen-VL remain explicit routes.
- ASR: LiteLLM `/v1/audio/transcriptions`; local Speaches uses the same request contract.
- OCR: LiteLLM `/v1/ocr`; local ebook Markdown OCR remains the unchanged default path.

## Coverage Audit

```powershell
.\scripts\video-knowledge.ps1 model-task-coverage-audit --output-dir docs
```

Artifacts:

- `docs/model-task-coverage.json`
- `docs/model-task-coverage.md`

The audit is complete only when every production task is `unified`. Native
whole-video upload remains explicitly `deferred`; the production temporal path
continues to use bounded frame groups.

## Automatic Prompt-Pack Execution

Terminology arbitration:

```powershell
.\scripts\video-knowledge.ps1 run-term-arbitration-model <bundle> --provider-config <runtime-json-or-file>

# Network execution is explicit.
.\scripts\video-knowledge.ps1 run-term-arbitration-model <bundle> --provider-config <runtime-json-or-file> --execute
```

The model result must pass the existing terminology validation before it is
imported into `term-arbitration-glossary.json`.

BiliNote-style mind map:

```powershell
.\scripts\video-knowledge.ps1 run-bilinote-mind-map-model <bundle> --provider-config <runtime-json-or-file>

.\scripts\video-knowledge.ps1 run-bilinote-mind-map-model <bundle> --provider-config <runtime-json-or-file> --execute --limit 2
```

Generated mind maps remain review-required. Preview is the default for both
commands. Provider configuration and API keys are runtime-only and are not
written to bundle manifests or reports.

## Compatibility

Existing task commands and their result structures remain valid. Compatibility
wrappers preserve existing test/provider injection seams while production calls
route through `model_task_gateway`.

## Proxy runtime client (2026-07-15)

Proxy-mode tasks use `model_runtime_client.py` and fixed loopback LiteLLM endpoints: chat/vision at `/v1/chat/completions`, ASR at `/v1/audio/transcriptions`, and online OCR at `/v1/ocr`. The result schema is `video_knowledge_pipeline.model_runtime_result.v1` for local and remote execution.

Proxy failure never switches to a legacy adapter or a different execution location. LiteLLM fallback is limited to deployments already contained in the selected pool and, for remote execution, in consent v2 and the Broker allowlist. Local-only failure returns `local_gateway_unavailable` without a remote socket request.

Legacy mode remains explicit for migrated profiles and rollback. Existing Timeline, Bundle, Smart Summary, ASR raw-output, ebook OCR, and candidate-evidence schemas remain the business writeback contracts.

## Update Record

### 2026-07-15 01:21:45 | Codex / GPT-5

- Added the unified Proxy runtime contract and explicit no-cross-location/no-legacy-fallback behavior.
## 2026-07-23 Native video capability correction

- 2026-07-23 20:53:37 +08:00 | Codex (GPT-5)
- native_video_segment is no longer deferred. A consented Gemini route uses the Gemini Files API to upload the exact approved local video, request analysis, and delete the temporary provider file. Other providers are not silently substituted: unsupported native-video capability returns an explicit provider-capability result. Local temporal evidence remains available as an independent complementary route.