# OCR Provider Routing

- Updated: 2026-07-15 12:50:25 +08:00
- Acting agent/model: Codex (GPT-5)
- Status: implemented, preview/import path verified

## Outcome

VKP exposes one OCR route with two user-selectable backends:

| Backend | Identifier | Execution | Default |
|---|---|---|---|
| Local | ebook_markdown_pipeline | Local process_material -> job status -> Markdown artifact | Yes |
| Online | online_ocr | Trusted Model Connector only, with exact artifact hashes, consent, call limit, and trusted destination | No |

Both backends normalize into the existing timeline fields:

- visual_text
- structured_visual
- evidence_paths

Those fields are then reusable by build-entity-lexicon and adaptive-asr-route as terminology candidates, ASR hotwords, and bounded context hints. OCR evidence never directly overwrites the raw ASR transcript.

## Interfaces

MCP:

- ocr_route_tool
  - backend=local: preview or execute ebook_markdown_pipeline with execute_local=true.
  - backend=online: prepare exact image artifacts and an online-ocr-consent-request.json.
  - connector_result_json: import an audited Trusted Connector result into the existing visual-structure timeline path.
- adaptive_asr_route_tool
  - builds local Contextual Paraformer/SenseVoice plans.
  - may create a preview-only online ASR plan.
  - consumes OCR-derived terms without depending on the current Agent model's multimodal capability.

Direct module CLI:

    python -m video_knowledge_pipeline.ocr_route <bundle-dir> --backend local --execute-local

    python -m video_knowledge_pipeline.ocr_route <bundle-dir> --backend online --indexes 6,80 --limit 8

The online planning command does not send images. Use the Trusted Model Connector to create/execute a consent locked to task online_ocr and the exact artifact list, then import its connector-execution.json:

    python -m video_knowledge_pipeline.ocr_route <bundle-dir> --backend online --connector-result-json <connector-execution.json>

## Provider scope

Proxy-mode OCR uses LiteLLM `/v1/ocr`. The accepted LiteLLM prefixes are `mistral`, `azure_ai`, and `vertex_ai`, plus an explicit Mistral-compatible thin adapter. Unsupported OCR providers are rejected instead of being silently converted to a vision-chat request. Gemini/OpenAI-compatible/Qwen-VL OCR remains available only through explicit legacy/visual extraction routes, not as the standard Proxy OCR contract.

The Trusted Connector remains the only approved online execution surface for this route. Provider credentials are runtime-only and are not written into OCR route artifacts. The full catalog and advanced-auth boundary are in `docs/online-model-provider-catalog-2026-07-15.md`.

The same provider-router pattern already covers cloud ASR, semantic frame analysis, temporal visual analysis, transcript/text refinement, terminology arbitration, smart-summary rewriting, and mind-map generation.

## Safety and quality boundaries

- Local ebook_markdown_pipeline remains the default.
- The OCR router itself cannot perform an online network call.
- Online results must identify pages by timeline index or image filename and return Markdown plus confidence/uncertainties.
- Imported online OCR becomes candidate evidence, not verified fact.
- Raw ASR remains immutable; promotion of corrected text requires the existing evidence and quality gates.
- No real provider call, upload, secret read, or external write was performed while implementing this route.
