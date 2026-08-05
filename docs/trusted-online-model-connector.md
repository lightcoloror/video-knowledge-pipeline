# VKP Trusted Online Model Connector

Updated: 2026-07-15 12:50:25 | Codex / GPT-5

## Purpose

`vkp-model-connector` is the narrow, user-installed connector for all VKP online-model work. It covers text LLM, single-frame and temporal multimodal, cloud ASR, and online OCR while reusing `model_task_gateway -> model_runtime_client -> loopback LiteLLM Proxy`.

It is not a Volcengine-only relay. Proxy mode is the production provider surface; old OpenAI-compatible, Gemini, and ASR adapters remain only as explicitly selected legacy compatibility routes and are never automatic fallback.

## Supported task families

| Family | VKP tasks | Input locked by consent | Existing adapter reused |
|---|---|---|---|
| Text LLM | summary rewrite, chapter rewrite, global reduce, transcript polish/correction, term arbitration, mind map | exact text files and hashes | LiteLLM Proxy profile; legacy only by explicit route |
| Multimodal | semantic frame, document visual, temporal frame group | exact images and hashes, or existing bundle vision consent | LiteLLM Proxy; explicit local OpenAI-compatible/Qwen-VL pool |
| ASR | cloud ASR and OpenAI-compatible local ASR services | exactly one audio file and hash | LiteLLM transcription; explicit local Speaches pool |
| OCR | online image/document OCR | exact image/document hashes; one reserved call per artifact | LiteLLM `/v1/ocr`; local ebook Markdown OCR remains separate |

Native whole-video upload remains deferred. VKP continues to use selected frame groups for temporal understanding.

## Security and approval contract

The consent locks all of the following:

- one VKP model task;
- provider, model, Base URL, and protocol;
- exact artifact paths, byte sizes, and SHA-256 hashes;
- instructions used for the request;
- maximum call count and expiry time;
- total estimated-cost authorization and per-call cost ceiling;
- an exact per-file upload manifest plus operator confirmation bound to its manifest SHA-256.

The MCP server can validate and execute an existing consent. It cannot create, confirm, or widen consent. API keys are rejected in MCP arguments and provider JSON; they are read only from process environment variables.

Execution atomically reserves both call allowance and cost allowance under a consent-specific file lock before any provider call. This prevents two local agents or processes from both consuming the same remaining slots or budget. Completion counters and cost reconciliation use the same lock. Abandoned locks are recovered only after the stale interval and only when the recorded process is no longer alive.

When the provider reports `estimated_cost`, VKP reconciles the reservation to that value. When cost is absent, VKP conservatively keeps the full per-call ceiling committed. A response that exceeds the authorization is marked `cost_limit_exceeded_after_response` and cannot be promoted as a successful result. Provider-account or LiteLLM-side budgets remain necessary when an absolute billing cap is required.

Read-only status is advisory; the execution-time reservation is the authoritative call-limit check. Revoking consent blocks future reservations but does not cancel a provider call that already reserved its slot.

This is a formal local plugin and project execution gate. It cannot override Codex or another agent host's external-data policy. A host may still reject a request even when VKP consent is valid. Do not route a rejected call through a local proxy, another agent, or an HTTP bridge to bypass that decision.

## Runtime configuration

New profiles are configured in the loopback settings UI and persist one secret per profile as Windows DPAPI ciphertext. The Broker does not accept profile URLs or keys from MCP callers.

The following ignored environment files are legacy/operator-only inputs, not the route-based Broker contract:

```text
.local/model-connector.env
.local/video-knowledge.env
.local/vision.env
```

Example names only; do not commit values:

```text
OPENAI_API_KEY=<runtime-secret>
GEMINI_API_KEY=<runtime-secret>
ARK_API_KEY=<runtime-secret>
LECTURE_ASR_API_KEY=<runtime-secret>
```

Provider profiles passed to tools contain routing only:

```json
{
  "provider": "custom_openai_compatible",
  "base_url": "https://provider.example/v1",
  "model": "provider-model-name",
  "timeout_seconds": 120
}
```

In Proxy mode the equivalent stored profile also includes `litellm_provider`, `adapter_backend=proxy`, `location`, and capabilities. Do not pass it through MCP execution tools. Do not add `api_key`, bearer headers, cookies, tokens, or passwords to profile JSON.

The full curated and generic provider mapping is documented in `docs/online-model-provider-catalog-2026-07-15.md`.

## Operator consent workflow

Create consent in a visible PowerShell after reviewing the exact artifacts:

```powershell
cd %WORKSPACE_ROOT%\video-knowledge-pipeline

.\scripts\model-connector-consent.ps1 create %WORKSPACE_ROOT%\tmp\vkp-approved-run `
  --task smart_summary_section_rewrite `
  --artifact D:\path\to\approved-chapter.md `
  --provider-config %WORKSPACE_ROOT%\video-knowledge-pipeline\.local\provider-profile.json `
  --instructions "Generate a structured Chinese chapter summary." `
  --max-calls 1 `
  --expires-hours 24 `
  --max-estimated-cost-usd 0.50 `
  --max-cost-per-call-usd 0.50 `
  --confirm-data-export
```

Inspect or revoke it without a model call:

```powershell
.\scripts\model-connector-consent.ps1 status %WORKSPACE_ROOT%\tmp\vkp-approved-run\model-connector-consent.json `
  --provider-config %WORKSPACE_ROOT%\video-knowledge-pipeline\.local\provider-profile.json

.\scripts\model-connector-consent.ps1 revoke %WORKSPACE_ROOT%\tmp\vkp-approved-run\model-connector-consent.json
```

For existing VKP bundle vision work, continue to use `vision-export-consent.json`; the connector's semantic and temporal tools call the existing analyzers and their preflight/confirmation checks.

## MCP tools

The narrow server is started with:

```powershell
.\scripts\start-trusted-model-connector-with-env.ps1
```

It exposes only:

- `model_connector_capabilities`
- `model_connector_consent_status`
- `execute_consented_model_task_tool`
- `execute_local_model_task_tool`
- `execute_consented_semantic_vision`
- `execute_consented_temporal_vision`

There is deliberately no consent-create or consent-confirm MCP tool.

## Codex plugin

The versioned plugin source is:

```text
agent-integration-pack/codex-plugin/vkp-model-connector
```

The user installation is:

```text
%USERPROFILE%\plugins\vkp-model-connector
```

After install or update, start a new Codex task so the MCP tools are loaded. The plugin is local and user-installed; it is not an OpenAI-certified remote connector and does not change host policy.

## Model expansion rule

Adding another single-Key online model should normally require only a curated profile or `litellm_native` prefix plus a LiteLLM-supported model name. Add VKP code only for a genuinely different protocol or an explicitly modeled advanced-auth contract. Every model must map to a declared task and pass the same route-revision/artifact-hash consent gate.

## Consent v2 and configured routes (2026-07-15)

The default remote MCP execution surface no longer accepts caller-supplied provider URLs or API keys. Route-based consent locks every deployment in the selected remote pool, plus `route_id`, `route_revision`, virtual model, and a canonical route snapshot hash. Any route change blocks before network access.

Remote execution is deny-by-default. The Broker accepts uploads only when a configured remote route, consent v2, visible operator confirmation, call/cost limits, exact file hashes, and every deployment allowlist check all pass. Consent v1 remains readable for compatibility but cannot reserve a new remote execution.
Automatic publishing, files absent from `upload_manifest`, and silent fallback between `local-only` and `remote-approved` pools remain prohibited.
```text
execute_consented_model_task_tool(consent_path, route_revision)
execute_local_model_task_tool(task, artifact_paths, route_id)
```

The two compatibility bundle-vision tools also no longer accept `provider_config`; they resolve only a configured singleton `legacy` route and require its current revision. Proxy or multi-deployment visual work uses the main consent-v2 tool.

Online OCR is now included. Each approved image/document consumes an independent reserved call. Partial success is retained as candidate evidence with the source artifact hash. Local ebook Markdown OCR remains unchanged.

Temporal consent groups authorized frames by their immediate parent directory. One fixed-sample consent must contain exactly every frame in all selected groups and reserve one call per group; the Broker executes each group independently, then returns one unified runtime result with per-group status, evidence, usage, cost, and recovery metadata. `model_connector_consent_status` accepts `expected_calls` for a no-network allowance check.

Create a route-based consent in a visible operator shell with `--route-id` and `--route-revision`. Consent creation validates every deployment against `VKP_MODEL_CONNECTOR_ALLOWED_DESTINATIONS` before writing the consent. Secure MCP Tunnel exposes the Broker only; it does not widen this allowlist.

## Update Record

### 2026-07-15 01:21:45 | Codex / GPT-5

- Added consent v2 multi-deployment locking, configured-route execution, the local-only tool, OCR call accounting, and removal of arbitrary provider arguments from execution MCP tools.

### 2026-07-15 03:52:28 | Codex / GPT-5

- Added temporal frame-group call reservation/execution, unified grouped runtime results, and `expected_calls` consent-status validation. No real provider call or data export was performed.

### 2026-07-15 12:07:19 | Codex / GPT-5

- Added deny-by-default remote execution, exact upload manifests, operator confirmation binding, atomic call/cost reservation, conservative unknown-cost accounting, and explicit no-publish/no-unlisted-upload/no-cross-pool-fallback boundaries.

### 2026-07-15 12:50:25 | Codex / GPT-5

- Added the versioned Provider Catalog to Broker capabilities, including per-task capability/profile discovery.
- Added curated remote text/vision/ASR/OCR profiles, a generic LiteLLM-native extension, and explicit local OpenAI-compatible/Speaches profiles.
- Removed outdated documentation implying automatic Proxy-to-legacy fallback. No real Provider call or upload was performed.

### 2026-07-15 14:35:19 | Codex / GPT-5

- Added a stable cross-repository CLI front door:

  `scripts/video-knowledge.ps1 execute-consented-model-task <consent_path> --route-revision <exact-revision> --write`

- The CLI applies the same allowed-root, consent-v2 execution contract, exact manifest, destination allowlist, route revision, atomic reservation, Catalog/secret resolution, and audit path as the Broker.
- Callers cannot pass provider URLs, models, API keys, or fallback overrides. Exit codes distinguish completed (`0`), execution failure (`1`), blocked (`2`), and invalid input (`3`); handled results are JSON on stdout.
- No real Provider call or data export was performed while adding the interface.

## 2026-07-23 Native video capability correction

- 2026-07-23 20:53:37 +08:00 | Codex (GPT-5)
- native_video_segment is no longer deferred. A consented Gemini route uses the Gemini Files API to upload the exact approved local video, request analysis, and delete the temporary provider file. Other providers are not silently substituted: unsupported native-video capability returns an explicit provider-capability result. Local temporal evidence remains available as an independent complementary route.