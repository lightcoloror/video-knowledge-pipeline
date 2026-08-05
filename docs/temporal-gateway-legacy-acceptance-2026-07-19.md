# Temporal Gateway Legacy Acceptance — 2026-07-19

- Updated: `2026-07-19 11:47:12`
- Acting tool/model: `Codex / GPT-5.6`
- Status: `completed_6_of_6`

## Authorized scope

- Manifest: `openclaw-runs/getbrain-acquisition-20260708/1-首次沟通环节的高频问题/full-vkp-quality-20260713/webui-bundle/exports/temporal-gateway-acceptance-manifest.json`
- Manifest bytes: `21045`
- Manifest SHA-256: `00bda8d85bc6c3237087b6a56ce5702e59eff4e117fd9c955a2b4b7d5e8f11d5`
- Groups: `6, 80, 112, 135, 199, 201`
- Frames: `48`, exactly `8/8` per group
- Destination: `generativelanguage.googleapis.com`
- Model: `gemini-3.5-flash`
- Runtime: VKP built-in `legacy` adapter
- Limits: six calls, one per group, zero retry, no fallback, reserved ceiling `$0.60`

The production model settings file was not changed. The run used an isolated `.local` settings copy whose only behavioral differences were `adapter_backend=legacy` for the Gemini profile and `max_retries=0` for its vision pool.

## Result

- Calls attempted: `6`
- Calls completed: `6`
- Failed calls: `0`
- Connector status: `completed`
- Runtime status: `completed`
- Output contract: `pass`
- Automated quality gate: `pass`
- Production-qualified transport/contract result: `true`
- Human content review: `pending`
- Provider-reported cost: unavailable; VKP conservatively committed the full `$0.60` reservation.

The six responses contain structured temporal slide text, visible facts, speaker/scene state, changes, and uncertainty. They remain candidate evidence until human review.

## Security boundary repair

The first execution was blocked before networking with `calls_attempted=0`. A saved legacy route had correctly decrypted its DPAPI credential internally, but the trusted front door passed the internal `api_key` and `api_key_source` fields into the secretless policy validator. The validator correctly rejected them.

VKP now removes only those two internally resolved runtime fields before policy/consent validation. The actual adapter reacquires the credential from the local DPAPI store at execution time. Inline credentials supplied by an Agent, MCP request, provider configuration, or URL remain rejected. Focused connector/consent tests passed after the repair.

## Acceptance artifacts

- Preflight: `.local/temporal-legacy-acceptance-20260719/preflight.json`
- Consent v2: `.local/temporal-legacy-acceptance-20260719/gemini-3-5-flash-legacy-temporal-consent.v2.json`
- Full CLI result: `.local/temporal-legacy-acceptance-20260719/execution-cli-output.json`
- Connector audit: `.local/temporal-legacy-acceptance-20260719/model-connector-runs/model_connector_835d4e4117ed/connector-execution.json`
- Captured Lane A: `openclaw-runs/getbrain-acquisition-20260708/1-首次沟通环节的高频问题/full-vkp-quality-20260713/webui-bundle/exports/model-gateway-acceptance/lane-a-legacy.json`
- A/B/C JSON: `openclaw-runs/getbrain-acquisition-20260708/1-首次沟通环节的高频问题/full-vkp-quality-20260713/webui-bundle/exports/model-gateway-acceptance/model-gateway-abc-comparison.json`
- A/B/C Markdown: `openclaw-runs/getbrain-acquisition-20260708/1-首次沟通环节的高频问题/full-vkp-quality-20260713/webui-bundle/exports/model-gateway-acceptance/model-gateway-abc-comparison.md`

## A/B/C current evidence

All three lanes load the unified runtime schema and completed the same six temporal groups:

| Lane | Runtime | Calls | Recorded latency | Recovery |
|---|---|---:|---:|---|
| A | Gemini legacy remote | 6 | unavailable (`0` placeholder) | not needed |
| B | Gemini LiteLLM Proxy remote | 6 | 58,056 ms | not needed |
| C | LM Studio OpenAI-compatible local | 26 | 93,368 ms | split near-duplicate two-image windows into single-frame calls |

The comparison proves route/schema execution compatibility. It does not yet select a quality winner: automated outputs are still marked `pending_human_review`, and Lane A's direct adapter does not currently record useful latency or provider cost.

## Verification

- `python -m compileall -q src`: passed
- Focused local-media suite: `21 passed`
- Focused trusted connector/consent suite: `36 passed`
- Expanded local-media regression: `101 passed, 1 warning`
- Full suite: `865 passed, 1 warning`
- Ruff on changed Python files: passed
- `git diff --check`: passed

The warning is the pre-existing `jieba` use of deprecated `pkg_resources`; it is unrelated to this change.
