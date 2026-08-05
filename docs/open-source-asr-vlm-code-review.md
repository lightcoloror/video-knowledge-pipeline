# ASR and Local VLM Source Review

Update record: 2026-06-05 23:50:00 | Codex (GPT-5)

This note records the real local source review behind the ASR and multimodal integration plan. It is not based only on repository summaries.

## Reviewed Source Trees

- `%WORKSPACE_ROOT%\tool-source-review\FunASR`
- `%WORKSPACE_ROOT%\tool-source-review\SenseVoice`
- `%WORKSPACE_ROOT%\tool-source-review\Qwen2.5-VL`
- `%WORKSPACE_ROOT%\tool-source-review\InternVL`
- `%WORKSPACE_ROOT%\tool-source-review\LLaVA-NeXT`
- `%WORKSPACE_ROOT%\tool-source-review\AI-Video-Transcriber`
- `%WORKSPACE_ROOT%\tool-source-review\BiliNote`

## ASR Findings

### FunASR / SenseVoice

Evidence checked:

- `FunASR\README.md` shows direct `from funasr import AutoModel` usage with `model="iic/SenseVoiceSmall"`, `vad_model="fsmn-vad"`, and optional `spk_model="cam++"`.
- `FunASR\README.md` describes structured output with speaker labels, timestamps, and punctuation.
- `SenseVoice\README.md` shows `AutoModel(model="iic/SenseVoiceSmall", vad_model="fsmn-vad")`.
- `SenseVoice\README.md` documents `sentence_info` and timestamp support.
- SenseVoice README describes ASR plus language, emotion, and audio event recognition.

Decision:

- Use FunASR/SenseVoice as the primary local Chinese ASR path.
- Do not embed the source repository into this project.
- Execute through `video_knowledge_pipeline.funasr_python_runner`, which imports `funasr.AutoModel` in the ASR Python environment.
- Normalize raw output through the existing ASR adapter into `normalized-transcript.json` and `normalized-transcript.srt`.
- Preserve SenseVoice tags as metadata: language, emotion, audio events, and speaker where present.

Current implementation:

- `src\video_knowledge_pipeline\funasr_python_runner.py`
- `src\video_knowledge_pipeline\asr_runner.py`
- `src\video_knowledge_pipeline\asr_execution.py`
- `src\video_knowledge_pipeline\asr_adapter.py`
- `src\video_knowledge_pipeline\asr_environment.py`

Operational gate:

- If the selected FunASR/SenseVoice model is not found in a known local cache, execution returns `asr_model_not_ready`.
- To intentionally allow first-run download, set `LECTURE_ASR_ALLOW_MODEL_DOWNLOAD=1`.

### faster-whisper fallback

Evidence checked:

- `AI-Video-Transcriber\backend\transcriber.py` uses `faster_whisper.WhisperModel`.
- The local implementation keeps faster-whisper as a fallback plan, not as the Chinese-first default.

Decision:

- Keep CPU `int8`, VAD, and conservative fallback defaults.
- Prefer SenseVoice/FunASR for Chinese lecture videos.

### BiliNote reuse

Evidence checked:

- BiliNote transcriber code separates model readiness and transcriber provider routing.
- BiliNote provider code shows an OpenAI-compatible API pattern.

Decision:

- Reuse the idea of model readiness gates and provider profiles.
- Do not import BiliNote as a runtime dependency.

## Multimodal / Local VLM Findings

### Qwen2.5-VL / Qwen3-VL

Evidence checked:

- `Qwen2.5-VL\README.md` currently documents Qwen3-VL usage.
- It supports image input, multi-image input, local video paths, video URL input, and image lists treated as video.
- It exposes sampling controls such as `fps` and `num_frames`.
- It uses `AutoProcessor`, `AutoModelForImageTextToText`, and `qwen_vl_utils.process_vision_info`.
- It recommends token budget controls for video and image processors.

Decision:

- Best local path is an HTTP/OpenAI-compatible server when available.
- For this project, Qwen should be called through the existing vision provider layer, not imported directly into the main pipeline.
- The existing `temporal_frame_groups` output can map to Qwen's image-list-as-video input.

### InternVL

Evidence checked:

- `InternVL\internvl_chat\README.md` includes video examples using `decord.VideoReader`.
- It implements `load_video(video_path, num_segments=32)` and `get_index(...)` to uniformly sample video frames.
- It uses `dynamic_preprocess` and model chat calls over sampled visual tensors.

Decision:

- InternVL is suitable as a local subprocess or HTTP worker for temporal frame groups.
- It should receive ordered frame groups or short local video segments.
- Keep it behind `local_vlm_server_adapter` planning until a stable local serving environment exists.

### LLaVA-NeXT / LLaVA-OneVision

Evidence checked:

- `LLaVA-NeXT\llava\utils.py` implements `process_video_with_decord` and `process_video_with_pyav`.
- It samples by FPS and can cap frames with `frames_upbound`.
- `LLaVA-NeXT\README.md` points to LLaVA-Video, LLaVA-OneVision, and SGLang HTTP deployment paths.

Decision:

- LLaVA is a candidate for local video understanding, but it is operationally heavier than Qwen/InternVL.
- Prefer SGLang HTTP or a subprocess worker.
- Do not couple its repository code into the pipeline package.

## Adapter Boundary

The project now exposes a local VLM adapter plan:

```powershell
python -m video_knowledge_pipeline.cli local-vlm-adapter-plan
```

MCP tools:

- `local_vlm_adapter_plan_tool`
- `local_vlm_adapter_plan`

The adapter rules are:

- Main pipeline never directly imports local VLM repositories.
- Production flow uses API provider profiles first.
- Local VLMs should expose OpenAI-compatible HTTP where possible.
- Subprocess smoke workers are allowed, but must write raw outputs and must not mutate timeline on parse failure.
- Every output must preserve frame or video segment evidence paths.

## Current Recommendation

1. Use SenseVoice/FunASR locally for ASR.
2. Use Gemini/OpenAI-compatible API for first real multimodal quality checks.
3. Use Qwen as the first local VLM candidate if a serving endpoint is installed.
4. Use InternVL for local temporal frame-group experiments.
5. Treat LLaVA-NeXT/LLaVA-OneVision as a heavier option, most useful when SGLang serving is already available.
