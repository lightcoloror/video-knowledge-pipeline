# Model Task Gateway Coverage

- Status: `complete`
- Total: `15`
- Unified: `14`
- Legacy adapter: `0`
- Deferred: `1`
- Contract drift: `0`

| Task | Model type | Modality | Gateway | Providers | Status |
|---|---|---|---|---|---|
| `cloud_asr` | `asr` | `audio` | `model_task_gateway` | litellm, openai_compatible_asr | `unified` |
| `local_asr_service` | `asr` | `audio` | `model_task_gateway` | speaches_openai_compatible, custom_openai_compatible_asr | `unified` |
| `multimodal_frame_analysis` | `semantic_frame` | `image` | `model_task_gateway` | litellm, gemini, openai_compatible, local_qwen_vl | `unified` |
| `temporal_visual_analysis` | `temporal_sequence` | `multi_image` | `model_task_gateway` | litellm, gemini, openai_compatible, local_qwen_vl | `unified` |
| `smart_summary_rewrite` | `summary_rewrite` | `text` | `model_task_gateway` | litellm, openai_compatible | `unified` |
| `smart_summary_section_rewrite` | `summary_rewrite` | `text` | `model_task_gateway` | litellm, openai_compatible | `unified` |
| `smart_summary_global_reduce` | `summary_rewrite` | `text` | `model_task_gateway` | litellm, openai_compatible | `unified` |
| `transcript_readable_polish` | `text_llm` | `text` | `model_task_gateway` | litellm, openai_compatible | `unified` |
| `transcript_correction_pack` | `transcript_correction` | `text` | `model_task_gateway` | litellm, openai_compatible | `unified` |
| `transcript_candidate_discovery` | `transcript_correction` | `text` | `model_task_gateway` | litellm, openai_compatible | `unified` |
| `transcript_semantic_correction` | `transcript_correction` | `text` | `model_task_gateway` | litellm, openai_compatible | `unified` |
| `term_arbitration` | `transcript_correction` | `text` | `model_task_gateway` | litellm, openai_compatible | `unified` |
| `bilinote_mind_map` | `text_llm` | `text` | `model_task_gateway` | litellm, openai_compatible | `unified` |
| `provider_task_benchmark` | `text_llm` | `text` | `model_task_gateway` | litellm, openai_compatible | `unified` |
| `native_video_segment` | `video_segment` | `video` | `online_model_gateway` | none | `deferred` |

> Native whole-video API is deferred; temporal frame groups remain the production path.
