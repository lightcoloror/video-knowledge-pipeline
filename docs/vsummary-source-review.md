# vsummary Source Review

Updated: 2026-07-04 13:24:00 | Codex / GPT-5

Source reviewed: `%WORKSPACE_ROOT%\tool-source-review\vsummary`

Repository: https://github.com/alpha03123/vsummary

Reviewed commit: `1b8ac39` on `main`

## Summary

`alpha03123/vsummary` is a full local video knowledge application, not just a summarizer script. Its stack is:

- backend: FastAPI-style Python service;
- frontend: React/Vite workspace UI;
- ASR: faster-whisper with GPU/CPU configuration;
- LLM: LiteLLM gateway with OpenAI-compatible provider support;
- knowledge/RAG: LlamaIndex + LanceDB + FastEmbed;
- workflow: staging directory, stage cache, cancellation, progress reporting;
- UI: video player, chapter cards, transcript jump, chat drawer, citation previews.

VKP already has a stronger evidence pipeline for ASR/OCR/ebook/multimodal/timeline/review/export. Therefore `vsummary` should not replace VKP. The useful path is selective reuse: provider gateway patterns, UI interaction patterns, stage cache and generation ergonomics.

## Files Reviewed

| Area | vsummary files | VKP relevance |
| --- | --- | --- |
| Generation workflow | `src/backend/video_summary/generation/usecases/generate_summary.py` | Good model for long-running UI tasks: probe, extract audio, transcribe, enhance, summarize, atomic commit. |
| Stage cache | `src/backend/video_summary/generation/stage_cache.py` | Good reusable pattern for caching audio/transcript/model-stage artifacts by media fingerprint + implementation identity. |
| Artifact store | `src/backend/video_summary/infrastructure/storage/filesystem_generation_artifact_store.py` | Good pattern for paired JSON/Markdown writes and atomic text writes. |
| Media tools | `src/backend/video_summary/infrastructure/media_tools.py` | Good cancellation-aware ffmpeg wrapper; VKP already has ffmpeg use but can borrow cancellation shape. |
| ASR | `src/backend/video_summary/infrastructure/asr/faster_whisper_transcriber.py` | Useful CUDA DLL path discovery and progress callback design. VKP main ASR remains SenseVoice/FunASR; faster-whisper stays fallback. |
| LLM gateway | `src/backend/shared/llm/litellm_gateway.py`, `base_url.py`, `json_mode.py` | Very useful provider abstraction and JSON parsing fallback. Partially reused in VKP. |
| Summary prompts/schema | `src/backend/video_summary/generation/prompts/summary.py`, `schemas.py` | Useful map/reduce summary baseline, but too simple for VKP's evidence-rich `smart-summary.md`. |
| Frontend video seek | `WorkspaceVideoPlayer.jsx`, `WorkspaceOverviewView.jsx`, `WorkspaceMarkdownMessage.jsx`, `useWorkspaceController.js` | Very relevant for VKP review UI: chapter/transcript/citation click -> video seek. |
| Tool actions | `src/backend/video_summary/tools/video.py`, `overview.py` | Useful model for agent/UI actions returning `video_seek` and selected tool payloads. |

## Direct Reuse Already Implemented

VKP now has `src/video_knowledge_pipeline/text_llm_gateway.py`.

This directly adapts useful, small, low-coupling pieces from `vsummary`:

1. OpenAI-compatible base URL normalization from `src/backend/shared/llm/base_url.py`.
2. JSON extraction strategy from `src/backend/shared/llm/json_mode.py`:
   - direct JSON;
   - fenced Markdown JSON;
   - balanced brace/bracket scan.
3. Provider smoke shape inspired by `LiteLLMCompletionGateway.test_connection`.

VKP intentionally did not copy `litellm` as a dependency yet. The current gateway uses Python stdlib `urllib` and VKP's existing provider configuration so it does not add installation risk. It is a stepping stone for the next phase where online/cloud LLM provider execution can be connected to `smart-summary.md` generation.

New VKP interface:

```powershell
.\scripts\video-knowledge.ps1 text-llm-provider-smoke `
  --provider-config '{"provider":"volcengine_coding_plan","base_url":"https://ark.cn-beijing.volces.com/api/coding/v3","model":"doubao-seed-2.0-pro"}'
```

Default behavior is preview/plan only. Add `--execute` only when a real provider call is intended.

MCP tools added:

- `text_llm_provider_smoke`
- `text_llm_provider_smoke_tool`

Tests added:

- `tests/test_text_llm_gateway.py`

## Additional Direct Reuse Implemented

Update: 2026-07-04 23:59:00 | Codex / GPT-5

VKP now also reuses two more low-coupling pieces from `alpha03123/vsummary`:

1. Stage cache and atomic generation commits
   - VKP file: `src/video_knowledge_pipeline/stage_cache.py`
   - Reused idea: cache expensive intermediate artifacts by source fingerprint, stage name, and implementation identity.
   - Supported artifacts: JSON, text/Markdown, and arbitrary files.
   - Intended use: ASR audio/raw transcript/normalized transcript, ebook/OCR batches, smart-summary chunk outputs, content asset drafts.

2. Windows CUDA DLL discovery for faster-whisper fallback
   - VKP file: `src/video_knowledge_pipeline/cuda_runtime.py`
   - ASR status integration: `src/video_knowledge_pipeline/asr_environment.py`
   - Reused idea: discover `nvidia.cublas`, `nvidia.cudnn`, `nvidia.cuda_nvrtc`, and `nvidia.cuda_runtime` package `bin/` directories, optionally register them via `os.add_dll_directory`, and prepend PATH only on explicit registration.
   - Current default: `asr-env-status` reports discovery status only; it does not mutate PATH.

Verification:

```text
python -m pytest -q tests/test_stage_cache_and_cuda_runtime.py tests/test_asr_pipeline.py::test_asr_env_status_reports_readiness_and_actionable_next_steps
```

Result: `4 passed, 1 warning`.
## What Is Worth Reusing Next

### 1. UI video seek interaction

Highest value for VKP.

`vsummary` solves a product problem VKP has repeatedly hit: clicking a chapter, transcript segment, citation, or chat reference seeks the embedded video to the exact timestamp. The reusable design is:

```text
chapter/transcript/citation click
-> dispatch player_seek_requested
-> state.playerSeekRequest
-> video.currentTime = seconds
-> video.play()
```

VKP's static review pages can reuse this design without adopting React:

- add one shared `playerSeekRequest` object in page JS;
- all review targets, transcript rows, and citations call `seekTo(seconds, endSeconds, label)`;
- keep the current review row highlighted after seeking;
- show matched transcript/visual evidence near the player.

### 2. LLM provider gateway

Medium-high value.

VKP should keep Codex as the first LLM substitute, but online/cloud LLM providers are valid when quality/scale requires them. `vsummary`'s best pattern is the provider gateway, especially:

- base URL normalization;
- text/stream/structured output methods;
- structured output fallback: schema -> json_object -> prompt;
- connection smoke;
- provider cache identity.

Current VKP implementation started with stdlib OpenAI-compatible text calls. A future phase can add optional `litellm` support only if it is worth the dependency.

### 3. Stage cache and atomic generation commits

Medium value.

For VKP UI batch jobs, borrow `vsummary`'s idea:

```text
staging dir
-> run stages
-> cache each stage by media fingerprint + implementation identity
-> atomic commit into bundle
-> cleanup staging on cancel/failure
```

This is especially useful for:

- ASR reruns;
- ebook/OCR batch runs;
- smart-summary LLM generation;
- content asset export.

### 4. CUDA DLL discovery for faster-whisper fallback

Medium value.

VKP uses SenseVoice/FunASR first. But for faster-whisper fallback, `vsummary` has a concrete Windows CUDA helper:

- discover `nvidia.cublas`, `nvidia.cudnn`, `nvidia.cuda_nvrtc`, `nvidia.cuda_runtime` package bin dirs;
- call `os.add_dll_directory`;
- prepend `PATH`.

This can reduce the recurring Windows GPU runtime friction.

## What Should Not Be Directly Reused

| Component | Why not direct reuse |
| --- | --- |
| Whole FastAPI backend | VKP already has CLI/MCP/OpenClaw/static bundle contracts. Full backend would duplicate orchestration and ports. |
| Whole React app | Useful product direction, but direct transplant would fight VKP's static review bundle and current task console. Selectively port interaction ideas. |
| Summary schema | vsummary schema is `one_sentence_summary/core_problem/chapters/key_takeaways`; VKP needs richer evidence: ASR, OCR/ebook, visual understanding, temporal evidence, review gaps, term arbitration. |
| Bilibili / Chaoxing download logic | VKP must not own download backend. Continue using `video-download-orchestrator` for downloads. |
| RAG stack wholesale | LanceDB/LlamaIndex can be useful later, but VKP first needs stable evidence/export. RAG should be a downstream query layer, not a replacement for extraction. |

## Recommended Next Steps

1. Connect `text_llm_gateway` to `generate-smart-summary-with-codex` as an optional provider path:
   - default: Codex-first local substitute;
   - optional: `generate-smart-summary-with-llm --provider-config ... --execute`;
   - same input pack, same quality gate, no secret persistence.
2. Port the `WorkspaceVideoPlayer` seek-request pattern into VKP static review pages.
3. Add a VKP stage-cache module for ASR/OCR/smart-summary reruns.
4. Borrow faster-whisper CUDA DLL discovery for VKP fallback ASR.
5. Keep vsummary as a reference source in `%WORKSPACE_ROOT%\tool-source-review\vsummary`; do not vendor the full repo.

## Verification

```text
python -m compileall src\video_knowledge_pipeline\text_llm_gateway.py src\video_knowledge_pipeline\cli.py src\video_knowledge_pipeline\mcp_server.py tests\test_text_llm_gateway.py
python -m pytest -q --basetemp <repo-local-temp> tests\test_text_llm_gateway.py tests\test_knowledge_export.py
```

Latest local result:

```text
16 passed, 1 pytest cache permission warning
```
