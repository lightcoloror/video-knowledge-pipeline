# OpenClaw Integration

Update: 2026-06-15 00:00:00 | Codex (GPT-5)

## Boundary

`video-knowledge-pipeline` is the video knowledge extraction tool. It owns:

- local media ingest
- ASR planning/execution gates
- frame extraction and timeline bundle creation
- OCR/document screenshot branch
- multimodal single-frame and temporal-frame analysis
- knowledge note, transcript, audit, and review artifacts

It does **not** own video downloading. Video link recognition, route planning, download manifests, and real download execution are delegated to:

```text
%WORKSPACE_ROOT%\video-download-orchestrator
```

OpenClaw should treat downloads as a separate operator boundary. Link planning is safe by default. Real download execution must be an explicit action in `video-download-orchestrator`, with actor allowlist/confirmation and platform restrictions respected.

## OpenClaw-Facing Entrypoints

All commands return machine-readable JSON with:

```text
ok
input_type
will_download
download_plan
media_path
workspace
artifacts
review_url_or_file
next_actions
operator_boundary
```

### 1. Plan A Video Link

```powershell
.\scripts\video-knowledge.ps1 openclaw-video-plan "https://example.com/video"
```

This calls:

```powershell
python -m video_orchestrator.cli openclaw-plan <url-or-telegram-text> --format json
```

Expected behavior:

- `will_download=false`
- no media is downloaded
- `download_plan` contains the original `video-download-orchestrator` plan
- `next_actions` tells OpenClaw to execute download only through the downloader project after confirmation

### 2. Ingest A Local Or Already Downloaded Video

```powershell
.\scripts\video-knowledge.ps1 openclaw-video-ingest `
  D:\path\to\lesson.mp4 `
  --workspace %WORKSPACE_ROOT%\video-knowledge-pipeline\openclaw-runs\lesson-001 `
  --title "课程名"
```

Expected behavior:

- no download happens
- prepares a local video knowledge workspace
- by default builds an initial `webui-bundle`
- returns `review_url_or_file` pointing to `webui-bundle\review.html` when bundle creation succeeds

Use `--no-build-initial-bundle` only when OpenClaw wants a very fast dry ingest that only writes the run plan.

### 3. Link Flow With Download Boundary

Default:

```powershell
.\scripts\video-knowledge.ps1 openclaw-video-link "https://example.com/video"
```

This is plan-only and returns `will_download=false`.

Explicit download boundary:

```powershell
.\scripts\video-knowledge.ps1 openclaw-video-link "https://example.com/video" `
  --allow-download `
  --actor-id "<telegram-user-id>" `
  --confirm-download
```

This delegates real execution to `video-download-orchestrator openclaw-execute`. If `--actor-id` or `--confirm-download` is missing, the command returns `download_confirmation_required` and does not execute.

If OpenClaw already knows the downloaded file path, pass it to ingest:

```powershell
.\scripts\video-knowledge.ps1 openclaw-video-ingest D:\path\to\downloaded.mp4
```

## MCP Tools

The MCP server exposes the same thin adapter:

```text
openclaw_video_plan
openclaw_video_ingest
openclaw_video_link
openclaw_bridge_status
openclaw_docker_contract_check
openclaw_video_from_vdo_handoff
openclaw_video_ingest_vdo_handoff
```

For agents that use generated JSON args files through the CLI bridge:

```powershell
.\scripts\video-knowledge.ps1 mcp-call openclaw_video_plan D:\path\to\args.json
```

Before Docker/OpenClaw calls the bridge, check the host bridge without starting services:

```powershell
.\scripts\video-knowledge.ps1 openclaw-bridge-status
```

To start the bridge directly in the background with logs and a health wait loop:

```powershell
.\scripts\start-openclaw-http-background.ps1
```

Logs are written under:

```text
.local\logs\openclaw-http.stdout.log
.local\logs\openclaw-http.stderr.log
```

To manage the host bridge as a Windows scheduled task:

```powershell
.\scripts\openclaw-http-task.ps1 status
.\scripts\openclaw-http-task.ps1 register
.\scripts\openclaw-http-task.ps1 start
.\scripts\openclaw-http-task.ps1 stop
.\scripts\openclaw-http-task.ps1 unregister
```

The task name is `VideoKnowledgeOpenClawHttp`. The task command calls `scripts\start-openclaw-http.cmd`; it does not store a separate port.
If Windows denies task registration in the managed shell, use `scripts\start-openclaw-http-background.ps1` as the operator fallback.

If Task Scheduler is unavailable or denied, install a per-user Startup folder fallback from a visible PowerShell:

```powershell
.\scripts\openclaw-http-startup-folder.ps1 status
.\scripts\openclaw-http-startup-folder.ps1 install
.\scripts\openclaw-http-startup-folder.ps1 remove
```

This writes only `VideoKnowledgeOpenClawHttp.cmd` under the current user's Startup folder. It does not change OpenClaw or system-wide services.

To check whether OpenClaw Docker has the required mount/env contract:

```powershell
.\scripts\video-knowledge.ps1 openclaw-docker-contract-check `
  --compose-path %OPENCLAW_ROOT%\openclaw\docker-compose.yml
```

After `video-download-orchestrator` writes manifest/report/review artifacts, preview whether VKP can ingest:

```powershell
.\scripts\video-knowledge.ps1 openclaw-video-from-vdo-handoff `
  --manifest-path D:\path\to\.vdo\manifests\task.json `
  --summary-path D:\path\to\.vdo\reports\1\summary.json `
  --review-checklist-path D:\path\to\.vdo\reports\1\review-checklist.json
```

This emits `video_knowledge_pipeline.vdo_handoff.v1`. It does not download, process video, run ASR, or call vision APIs.

To bridge a ready handoff into VKP ingest, preview first:

```powershell
.\scripts\video-knowledge.ps1 openclaw-video-ingest-vdo-handoff `
  --summary-path D:\path\to\.vdo\reports\1\summary.json `
  --review-checklist-path D:\path\to\.vdo\reports\1\review-checklist.json
```

Only when the handoff is `ready_for_ingest`, run with explicit execution:

```powershell
.\scripts\video-knowledge.ps1 openclaw-video-ingest-vdo-handoff `
  --summary-path D:\path\to\.vdo\reports\1\summary.json `
  --review-checklist-path D:\path\to\.vdo\reports\1\review-checklist.json `
  --execute
```

This still does not execute cloud vision. ASR execution remains off by default.

## HTTP Bridge

For Docker OpenClaw agents that cannot call host MCP directly, start the host HTTP bridge:

```powershell
.\scripts\start-openclaw-http.cmd
```

The default host/port/path come from:

```text
config\video-knowledge-pipeline.json -> services.openclaw_http
```

Current default URLs:

```text
Host:   http://127.0.0.1:8931/call
Docker: http://host.docker.internal:8931/call
```

Health and contract:

```powershell
Invoke-RestMethod http://127.0.0.1:8931/health
Invoke-RestMethod http://127.0.0.1:8931/contract
```

Call from Docker/OpenClaw:

```json
{
  "name": "openclaw_video_plan",
  "arguments": {
    "url_or_text": "https://example.com/video"
  }
}
```

The bridge exposes only:

```text
openclaw_bridge_status
openclaw_bridge_doctor
openclaw_live_smoke
openclaw_docker_contract_check
openclaw_video_plan
openclaw_video_ingest
openclaw_video_link
openclaw_video_from_vdo_handoff
openclaw_video_ingest_vdo_handoff
content_asset_status
```

If binding outside localhost, pass `--token` or set `VIDEO_KNOWLEDGE_OPENCLAW_HTTP_TOKEN`.

## Docker Client Helper

Inside a Docker/OpenClaw container with `%WORKSPACE_ROOT%` mounted to `/mnt/used-by-codex`, call:

```sh
/mnt/used-by-codex/video-knowledge-pipeline/scripts/openclaw-video-knowledge-call.sh status
```

For a read-only live smoke:

```sh
/mnt/used-by-codex/video-knowledge-pipeline/scripts/openclaw-video-knowledge-call.sh \
  live-smoke /mnt/used-by-codex/video-knowledge-pipeline/openclaw-runs/example/webui-bundle
```

```sh
/mnt/used-by-codex/video-knowledge-pipeline/scripts/openclaw-video-knowledge-call.sh \
  plan "https://example.com/video"
```

For an already downloaded file in the mounted workspace:

```sh
/mnt/used-by-codex/video-knowledge-pipeline/scripts/openclaw-video-knowledge-call.sh \
  ingest /mnt/used-by-codex/video-download-orchestrator/downloads/example/download.mp4 \
  --workspace /mnt/used-by-codex/video-knowledge-pipeline/openclaw-runs/example \
  --title "课程名"
```

For a VDO handoff preview:

```sh
/mnt/used-by-codex/video-knowledge-pipeline/scripts/openclaw-video-knowledge-call.sh \
  handoff \
  --summary-path /mnt/used-by-codex/video-download-orchestrator/downloads/example/.vdo/reports/1/summary.json \
  --review-checklist-path /mnt/used-by-codex/video-download-orchestrator/downloads/example/.vdo/reports/1/review-checklist.json
```

For a ready VDO handoff ingest preview:

```sh
/mnt/used-by-codex/video-knowledge-pipeline/scripts/openclaw-video-knowledge-call.sh \
  ingest-handoff \
  --summary-path /mnt/used-by-codex/video-download-orchestrator/downloads/example/.vdo/reports/1/summary.json \
  --review-checklist-path /mnt/used-by-codex/video-download-orchestrator/downloads/example/.vdo/reports/1/review-checklist.json
```

For a read-only Docker contract check:

```sh
/mnt/used-by-codex/video-knowledge-pipeline/scripts/openclaw-video-knowledge-call.sh contract
```

For read-only content material card status after VKP export:

```sh
/mnt/used-by-codex/video-knowledge-pipeline/scripts/openclaw-video-knowledge-call.sh \
  content-status /mnt/used-by-codex/video-knowledge-pipeline/openclaw-runs/example/webui-bundle
```

Batch content material cards and review-only handoff packs can also be verified from Docker:

```sh
/mnt/used-by-codex/video-knowledge-pipeline/scripts/openclaw-video-knowledge-call.sh \
  batch-content-status /mnt/used-by-codex/video-knowledge-pipeline/openclaw-runs

/mnt/used-by-codex/video-knowledge-pipeline/scripts/openclaw-video-knowledge-call.sh \
  content-handoff-pack /mnt/used-by-codex/video-knowledge-pipeline/openclaw-runs
```

These helper commands only call the host bridge. They do not download, run ASR, run vision, publish, or write Logseq/Obsidian.

The helper reads:

```text
VKP_API_BASE=http://host.docker.internal:8931
VKP_CONTAINER_ROOT=/mnt/used-by-codex
VKP_HOST_ROOT=%WORKSPACE_ROOT%
```

It translates mounted container paths back to Windows host paths before calling the host HTTP bridge. Use `--print-payload` to inspect the JSON without making a request.

For host-side diagnostics without starting services:

```powershell
.\scripts\video-knowledge.ps1 openclaw-bridge-doctor
.\scripts\video-knowledge.ps1 openclaw-live-smoke `
  --bundle-dir D:\video-knowledge-runs\lesson-001\webui-bundle `
  --write-report
```

If `openclaw-bridge-doctor` reports that port 8931 is not listening, run the lifecycle commands from a visible PowerShell instead of the Codex managed shell:

```powershell
cd %WORKSPACE_ROOT%\video-knowledge-pipeline
.\scripts\openclaw-http-task.ps1 register
.\scripts\openclaw-http-task.ps1 start
.\scripts\video-knowledge.ps1 openclaw-bridge-doctor
Invoke-RestMethod http://127.0.0.1:8931/health
Invoke-RestMethod http://127.0.0.1:8931/contract
```

If task registration is denied, install the per-user Startup fallback and then start a host bridge:

```powershell
.\scripts\openclaw-http-startup-folder.ps1 install
.\scripts\start-openclaw-http-background.ps1
.\scripts\video-knowledge.ps1 openclaw-bridge-doctor
```

For content-asset batch handoff artifacts:

```powershell
.\scripts\video-knowledge.ps1 batch-content-asset-status D:\video-knowledge-runs
.\scripts\video-knowledge.ps1 content-handoff-pack D:\video-knowledge-runs
```

These commands do not download, run ASR, call vision models, publish, or write Logseq/Obsidian. They only inspect existing bundles and write local review artifacts when `write=true`.

## Docker OpenClaw Notes

Recommended setup:

1. Run `video-download-orchestrator` HTTP bridge on the host when OpenClaw needs link planning from inside Docker.
2. Run `video-knowledge-pipeline` OpenClaw HTTP bridge on the host when Docker OpenClaw should call video knowledge tools through `/call`.
3. Set this in the OpenClaw container:

```text
VDO_API_BASE=http://host.docker.internal:8921
VKP_API_BASE=http://host.docker.internal:8931
```

4. Mount the host workspace into Docker, for example:

```text
%WORKSPACE_ROOT% -> /mnt/used-by-codex
```

VKP provides an example override:

```text
examples\openclaw\docker-compose.used-by-codex.override.yml
```

Review and apply it manually with your OpenClaw compose workflow. VKP does not modify the production OpenClaw compose file.

The path contract is:

```text
Host root:      %WORKSPACE_ROOT%
Container root: /mnt/used-by-codex
VKP_API_BASE:   http://host.docker.internal:8931
VDO_API_BASE:   http://host.docker.internal:8921
```

5. Keep path translation explicit. This project returns Windows host paths such as:

```text
%WORKSPACE_ROOT%\video-knowledge-pipeline\openclaw-runs\lesson\webui-bundle\review.html
```

If the Docker agent calls a host-side CLI/MCP/HTTP bridge, pass host paths. If it reads artifacts directly inside the container, translate to the mounted path.

## VDO To VKP Handoff

VKP accepts VDO artifacts as a handoff preview, not as proof that a video should be processed. The handoff contract is:

```text
video_knowledge_pipeline.vdo_handoff.v1
```

Important fields:

- `source_url`, `platform`, `title`: provenance for the source video.
- `media_path`, `media_path_container`: host and mounted-container media paths.
- `sidecars`: subtitle/info/description/thumbnail files produced by VDO.
- `vdo_artifacts`: VDO manifest, summary, report, log, and review checklist paths.
- `review`: whether VDO still requires human review.
- `ingestion`: recommended VKP next action. `execute_asr=false` and `execute_vision=false` by default.
- `content_assets`: reserved namespace for reviewable summaries, timelines, key segments, short-video script drafts, and highlight-post source material.

VKP automatic ingest is allowed only when the handoff reports a verified local media file and no unresolved VDO review blockers. If VDO reports `needs_review`, `manual_review_required`, warning checks, failed checks, or no detected media file, VKP must return an operator review action instead of ingesting.

Content assets are drafts. They must be marked `review_required=true` and `publication_allowed=false`; OpenClaw must not auto-publish them.

VKP export currently writes:

```text
exports\knowledge-note.md
exports\full-transcript.md
exports\extraction-audit.md
exports\key-segments.md
exports\short-video-script-drafts.md
exports\highlight-post-drafts.md
exports\content-material-card.json
exports\content-material-card.md
```

The `content_assets` index is stored in `exports\export-summary.json` and `manifest.json`.
Use `content-asset-status` after export to verify that the material card exists and is safe only for review/inspiration routing:

```powershell
.\scripts\video-knowledge.ps1 content-asset-status D:\video-knowledge-runs\lesson-001\webui-bundle
```

## Self-Media Material Handoff

VKP participates in the cross-thread self-media material contract documented at:

```text
%WORKSPACE_ROOT%\docs\codex-session-index\self-media-topic-material-linkage-routing-2026-06-20.md
```

Scope:

- VKP handles videos from courses, live lessons, short-video benchmarks, and video-based paid/community materials after the source file is locally available or handed off by VDO.
- VKP outputs structured material, timestamps, evidence paths, extraction gaps, and review risks.
- VKP does not write final posts, publish, send Telegram messages, or write canonical Logseq/Obsidian notes.

Minimum output fields for content-asset consumers:

```text
schema: video_knowledge_pipeline.content_assets.v1
review_required: true
publication_allowed: false
summary_path
timeline_path
audit_path
key_segments_path
short_video_script_drafts_path
highlight_post_drafts_path
material_card_contract
consumer_rules
human_confirmation_required
```

The embedded `material_card_contract` maps VKP assets to the shared material card fields:

```text
material_id
source_path
source_type=video
source_fact_status
evidence_tier
privacy_level
desensitized
compliance_risk
fact_check_status
target_layer
publish_surface
content_stage
cta_type
crm_followup_needed
owner_thread=video-knowledge-pipeline
next_action
blocked_reason
```

VDO handoff stage:

- `content_stage=candidate`
- `source_fact_status=download_artifact_needs_vkp_extraction`
- `allowed_as_inspiration=false`
- Circle-of-friends consumption status: `not_allowed_until_vkp_export`

VKP export stage:

- `content_stage=evidence`
- `source_fact_status=ai_extracted_needs_review`
- `evidence_tier=timestamped_video_evidence`
- `allowed_as_inspiration=true`
- `allowed_as_fact=false`
- Circle-of-friends consumption status: `needs_review_inspiration`

What can be passed as inspiration:

- topic angle
- question prompt
- analogy or framing
- structure of an argument
- timestamped quote or visual observation for human review

What must be fact-checked before it becomes a claim:

- customer stories or service facts
- medical, claims, underwriting, or insurance compliance statements
- investment, income, pricing, or market-performance statements
- platform policy, tool ranking, benchmark, or anti-bot conclusions
- any time-sensitive regulatory, product, or market information

Actions that require explicit human confirmation:

- downloading or account-authorized access
- cloud ASR or cloud vision execution
- fact-checking before claiming truth
- privacy desensitization before customer-related use
- compliance review before insurance or medical use
- publishing or sending to any external surface
- writing back to canonical Logseq or Obsidian notes

OpenClaw and downstream content threads should treat VKP outputs as reviewable evidence, not final copy. The safe handoff wording is:

```text
发现一个视频来源素材候选：
来源：
适合用途：内容资产池 / 朋友圈灵感
风险：AI 抽取结果需复核；事实、合规、隐私边界未确认
建议下一步：交给内容资产线程归档，或交给朋友圈线程生成 draft_only 灵感稿
```

## Telegram Flow

Recommended Telegram/OpenClaw decision tree:

1. If message contains an existing host media path:
   - call `openclaw-video-ingest <media-path>`
2. If message contains a URL:
   - call `openclaw-video-plan <message-or-url>`
   - show/record the download plan
   - only on explicit user/operator confirmation, execute download through `video-download-orchestrator`
   - after download, call `openclaw-video-ingest <downloaded-media-path>`
3. If message is unclear:
   - return the plan/error JSON and ask for a local path or supported video link

## Safety Rules

- Do not bypass login, CAPTCHA, paid content, platform restrictions, or rate limits.
- Do not write cookies, tokens, API keys, bearer headers, or logged-in page content into docs, manifests, or reports.
- Browser/authorized state can be used only for low-frequency, user-authorized access.
- This adapter never replaces `video-download-orchestrator`; it only calls its documented OpenClaw contract.
