# ASR and Multimodal Integration Audit

Checked at: 2026-06-05 16:15:00

Actor: Codex (GPT-5)

## Scope

This audit verifies the ASR and multimodal integration plan for `video-knowledge-pipeline`.

The goal is not to fully process every frame of the current sample video. The goal is to prove that the tool has a working ASR execution loop, provider-safe multimodal adapters, temporal frame groups, import paths, coverage accounting, CLI/MCP entrypoints, and reviewed open-source adapter plans.

## ASR

- Primary path: local FunASR/SenseVoice through `funasr.AutoModel`.
- Runner: `video_knowledge_pipeline.funasr_python_runner`.
- Plan command: `python -m video_knowledge_pipeline.cli plan-asr <workspace> <media> --preset sensevoice`.
- Execution command: `python -m video_knowledge_pipeline.cli run-asr-plan <asr-run-plan.json> --execute`.
- Model gate: `asr_model_not_ready` is returned when the model cache is missing and download is not explicitly allowed.
- Model cache evidence: `%USERPROFILE%\.cache\modelscope\hub\models\iic\SenseVoiceSmall`.
- Environment status exposes Python version, CPU/CUDA, torch, ffmpeg, tool availability, and model cache paths.

Real sample output:

- Raw ASR: `real-tests/asr-smoke/transcripts/asr_run_ef39ebbf7d0f/raw-asr-output.json`
- Run report: `real-tests/asr-smoke/transcripts/asr_run_ef39ebbf7d0f/asr-run-report.md`
- Normalized JSON: `real-tests/asr-smoke/transcripts/transcript_400d0a84830e/normalized-transcript.json`
- Normalized SRT: `real-tests/asr-smoke/transcripts/transcript_400d0a84830e/normalized-transcript.srt`

Known limitation:

- The current SenseVoice sample produced a coarse first cue. `resegment-transcript` exists for estimated timed re-segmentation, and WhisperX remains a later precision timestamp path.

## Multimodal Provider Layer

- Provider profiles: `openai`, `gemini`, `agnes`, `custom_openai_compatible`, and `openai_compatible`.
- Provider configuration reads from explicit arguments or environment variables.
- Sanitized reports expose only `api_key_configured`, not the key.
- `test-vision-provider` covers text ping, single-image JSON, and multi-image JSON when image paths are provided.
- Missing keys return `missing_api_key` and do not mutate timeline data.
- JSON repair strips code fences and preserves raw output on parse failure.

Real no-key check:

- Agnes profile returned `missing_api_key` with no key leakage.

## Single-Frame Visual Understanding

- Tool: `run-multimodal-frame-analysis`.
- First quality trial preview supports `--limit 19` semantic frames.
- Import path writes `visual_understanding` without overwriting OCR or structured visual data.
- Real sample timeline now contains imported `visual_understanding` for one frame.
- Evidence frame path is preserved in the imported result.

Sample import:

- `real-tests/feishu-video-retry-optimized/webui-bundle/codex-visual-understanding-import.json`

## Temporal Visual Understanding

- Tool: `run-temporal-frame-groups`.
- Real frame grouping supports 5-12 ordered frames; the current smoke run used 8 frames per group.
- Tool: `run-temporal-visual-analysis`.
- Import path writes `temporal_visual_understanding` without overwriting OCR or single-frame understanding.
- Real sample timeline now contains imported `temporal_visual_understanding` for one 8-frame temporal group.
- Evidence frame paths are preserved.

Sample import:

- `real-tests/feishu-video-retry-optimized/webui-bundle/codex-temporal-visual-understanding-import.json`

## Coverage and Audit Fields

`knowledge-coverage.json` now includes:

- `items_with_visual_route`
- `items_with_visual_understanding`
- `items_with_temporal_understanding`
- `semantic_frame_without_analysis`
- `temporal_sequence_without_analysis`
- `missing_visual_understanding`

The current sample remains blocked for full extraction because most semantic and temporal frames have not been sent to a real multimodal API. This is expected for the first integration audit.

## OCR Boundary

OCR and document-like screenshots remain outside this ASR/multimodal implementation plan.

The primary document screenshot path is still:

`run_visual_structure_tool -> ebook_markdown_pipeline`

`run_ocr_backfill_tool` is only a fallback import or direct OCR repair path.

## Open-Source Code Review

Source-review directories exist under `%WORKSPACE_ROOT%\tool-source-review`:

- `FunASR`
- `SenseVoice`
- `Qwen2.5-VL`
- `InternVL`
- `LLaVA-NeXT`
- `AI-Video-Transcriber`
- `BiliNote`

The local VLM path is intentionally only an adapter plan for now. The main pipeline should call OpenAI-compatible HTTP or a subprocess worker, not import model repositories directly.

## Verification Commands

Last verified commands:

```powershell
$env:PYTHONPATH='%WORKSPACE_ROOT%\video-knowledge-pipeline\src'
python -m pytest -q
python -m video_knowledge_pipeline.cli asr-env-status
python -m video_knowledge_pipeline.cli plan-asr %WORKSPACE_ROOT%\video-knowledge-pipeline\real-tests\asr-smoke %WORKSPACE_ROOT%\video-download-orchestrator\downloads\feishu-video-retry\download.mp4 --preset sensevoice
python -m video_knowledge_pipeline.cli run-temporal-frame-groups %WORKSPACE_ROOT%\video-knowledge-pipeline\real-tests\feishu-video-retry-optimized\webui-bundle --frame-count 8 --limit 5
python -m video_knowledge_pipeline.cli run-multimodal-frame-analysis %WORKSPACE_ROOT%\video-knowledge-pipeline\real-tests\feishu-video-retry-optimized\webui-bundle --limit 19
python -m video_knowledge_pipeline.cli run-temporal-visual-analysis %WORKSPACE_ROOT%\video-knowledge-pipeline\real-tests\feishu-video-retry-optimized\webui-bundle --frame-count 8
python -m video_knowledge_pipeline.cli audit-knowledge-coverage %WORKSPACE_ROOT%\video-knowledge-pipeline\real-tests\feishu-video-retry-optimized\webui-bundle
python -m video_knowledge_pipeline.cli bundle-status-report %WORKSPACE_ROOT%\video-knowledge-pipeline\real-tests\feishu-video-retry-optimized\webui-bundle
```

Latest test result:

```text
15 passed
```
