# Smart Summary Global Reduce Token Budget Hardening

- Acting tool/model: Codex（GPT-5 系列）
- Updated: 2026-08-02 15:33:46
- Status: implemented and offline-verified

## Change 1: DeepSeek Flash route locks thinking disabled

- Intent: prevent hidden reasoning from consuming the completion budget needed by the final structured summary.
- Decision: the reviewed `ark-deepseek-v4-flash` onboarding profile now prefills `provider_options.thinking_mode=disabled`; the existing local profile was migrated through `upsert_model_api_profile` without reading or replacing its DPAPI secret.
- Reason: the prior 10,000-token call used 7,595 reasoning tokens and returned a JSON object truncated inside `principles`.
- Evidence: immutable connector report `model_connector_227d5342b6e2`; route revision changed from `9114f187...` to `021017006...`; focused provider/onboarding regression passed.
- Effective scope: only routes that explicitly use the `ark-deepseek-v4-flash` profile. No silent provider fallback and no reuse of old consent across the new revision.

## Change 2: Chapter fact-pack compact projection v2

- Intent: reduce network traffic and prompt tokens while preserving complete chapter coverage and evidence traceability.
- Decision: reuse the existing chapter fact pack and evidence-group contract. Each chapter sends at most 8 facts, 2 quote-capable snippets, 2 review-gap references and one or more compact evidence-group IDs. Full member evidence lists remain local and are validated after the response.
- Reason: the previous prompt repeated 11 facts and 4 long snippets per chapter. The prompt was 57,948 characters even though chapter Markdown itself was already short.
- Evidence: the real 11-chapter preview fell to 40,900 characters (29.4% reduction), retained 11/11 chapters, 11/11 evidence-bound sections, and preserved review-gap IDs. Associated regression: 69 passed, 1 warning.
- Effective scope: `smart_summary_global_reduce` only. It does not alter canonical transcripts, chapter revisions, Timeline, source evidence, or existing installed summaries.

## Reuse and source-ledger result

- Reused existing VKP modules: `smart_summary_global_reduce`, `smart_summary_reader_plan`, `text_llm_gateway`, `model_runtime_client`, provider catalog validation, business authorization, child consent and Broker reservation.
- The local source ledger was checked for LlamaIndex, vsummary and VideoLingo; no registered source match was found, so no duplicate clone or new dependency was introduced.
- This change adapts the already implemented TreeSummarize-style fact-pack repacking rather than introducing a second summarization pipeline.

## Verification

- `python -m pytest -q tests/test_smart_summary_global_reduce_repack_budget.py tests/test_smart_summary_global_reduce_business_authorization.py tests/test_smart_summary_global_reduce_fact_pack.py tests/test_smart_summary_global_reduce_review_gap_gate.py tests/test_smart_summary_reader_plan.py tests/test_trusted_model_connector.py tests/test_model_provider_onboarding.py tests/test_model_api_settings_ui.py ...`
- Result: `69 passed, 1 warning`.
- Preview result: `expected_sections=11`, `completed_sections=11`, `input_chars=40900`, `network_requests_made=0`.
