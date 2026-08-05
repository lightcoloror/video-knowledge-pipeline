---
name: vkp-model-connector
description: Use VKP's consent-gated online model connector for text LLM, multimodal frame, temporal frame-group, and ASR tasks. Use only when a human-created consent already exists.
---

# VKP Model Connector

Use the connector in this order:

1. Call `model_connector_capabilities` to confirm the task is supported.
2. Call `model_connector_consent_status` with the consent path and secret-free provider profile.
3. Execute only when status is `active` and the requested task, model, endpoint, artifact hashes, expiry, and remaining call count match.
4. Use `execute_consented_model_task_tool` for consented text, standalone image groups, or audio ASR.
5. Use `execute_consented_semantic_vision` or `execute_consented_temporal_vision` for existing VKP bundles with `vision-export-consent.json`.

Never place API keys, tokens, cookies, passwords, or Authorization headers in tool arguments. The launcher reads credentials from `.local/model-connector.env` or existing local VKP env files. This plugin cannot create or confirm consent and cannot override the host agent's external-data policy.
