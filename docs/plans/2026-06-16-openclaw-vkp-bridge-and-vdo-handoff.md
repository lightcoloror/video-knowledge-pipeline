# OpenClaw VKP Bridge And VDO Handoff Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Make `video-knowledge-pipeline` reliably callable from OpenClaw through the existing host HTTP bridge on port 8931, while keeping video download ownership in `video-download-orchestrator` and defining a clean VDO -> VKP handoff manifest. The downstream product shape is "downloaded/local video -> analysis -> reviewable knowledge and content asset candidates", not a new Web Cut or video download backend.

**Architecture:** OpenClaw Docker calls a host-side VKP HTTP bridge through `host.docker.internal:8931`; VKP ingests only local or already-downloaded media paths. Video links are routed through VDO first. VDO produces a download artifact manifest and review checklist; VKP consumes that artifact only after the download boundary is satisfied.

**Tech Stack:** Python stdlib HTTP bridge, VKP CLI/MCP tools, PowerShell launch scripts, OpenClaw Docker bind mounts, VDO HTTP/CLI artifacts.

---

## Background From Light-Flow AI Development Note

Related context:

- Obsidian note: `%OBSIDIAN_VAULT%\00_Inbox\AI\网络分享：轻流程 AI 开发方法论对本机 Codex 系统的启发.md`
- Workspace draft: `%WORKSPACE_ROOT%\docs\codex-session-index\light-flow-ai-development-methodology-note.md`

The useful lesson for VKP is not to rebuild a full Web Cut product. The correct local shape is a controlled back-half pipeline:

```text
video link -> VDO route/download plan -> explicit download boundary -> local media path -> VKP analysis -> reviewable content assets
```

VKP should therefore focus on:

- accepting VDO manifests and already-downloaded/local media paths;
- running or planning ASR, frame extraction, OCR/document screenshot parsing, multimodal frame understanding, temporal understanding, and review bundle generation;
- exporting human-reviewable assets such as summaries, timelines, key segments, short-video script drafts, and highlight-post source material;
- keeping cloud vision/API execution behind preflight and explicit confirmation.

VKP should not:

- duplicate VDO download routing or download execution;
- bypass platform login, CAPTCHA, paywall, or rate-limit boundaries;
- auto-publish content assets;
- turn external methodology claims into trusted system facts without local verification.

---

## Read-Only Diagnostics On 2026-06-16

Commands inspected in `%WORKSPACE_ROOT%\video-knowledge-pipeline`:

```powershell
.\scripts\video-knowledge.ps1 config-status
netstat -ano | Select-String -Pattern ':8931'
```

Observed facts:

- VKP config resolves OpenClaw bridge URLs to:
  - Host: `http://127.0.0.1:8931/call`
  - Docker: `http://host.docker.internal:8931/call`
- `netstat` does not show a listener on `8931`, so OpenClaw cannot currently call VKP through the configured bridge.
- Bridge startup command already exists:

```powershell
%WORKSPACE_ROOT%\video-knowledge-pipeline\scripts\start-openclaw-http.cmd
```

- Equivalent module/console entrypoints exist:

```powershell
python -m video_knowledge_pipeline.openclaw_http
video-knowledge-openclaw-http
```

- The bridge exposes:
  - `GET /health`
  - `GET /tools`
  - `GET /contract`
  - `POST /call`
- The bridge tool surface is intentionally narrow:
  - `openclaw_video_plan`
  - `openclaw_video_ingest`
  - `openclaw_video_link`
- The bridge is currently designed as a foreground host service. There is no evidence of a built-in daemon, scheduled task, Windows service, or OpenClaw-side auto-registration that keeps it listening permanently.
- OpenClaw Docker compose does not currently mount `%WORKSPACE_ROOT%` to `/mnt/used-by-codex`, so the documented Docker helper path translation contract cannot work end to end yet.

No real video was processed. No cloud vision or ASR call was made. OpenClaw production code/config was not modified.

---

## Bridge 8931 Repair Plan

### 1. Treat The Bridge As Host-Side Service

The VKP HTTP bridge should run on the Windows host, not inside OpenClaw Docker.

Reason:

- VKP receives Windows media paths such as `%WORKSPACE_ROOT%\...`.
- The bridge already protects local bind behavior and maps Docker callers through `host.docker.internal`.
- Running inside Docker would require duplicating media processing dependencies and path handling.

Recommended lifecycle:

- Default local bind: `127.0.0.1:8931`.
- Start command: `%WORKSPACE_ROOT%\video-knowledge-pipeline\scripts\start-openclaw-http.cmd`.
- Long-running mode: user-level scheduled task or equivalent local supervisor.
- On-demand mode: OpenClaw/operator starts the host bridge before Telegram/OpenClaw video tasks.

Do not call this bridge "registered" unless a durable supervisor or explicit startup routine exists.

### 2. Add A Health Gate Before OpenClaw Calls VKP

OpenClaw-side helpers should check this before calling `/call`:

```text
GET http://host.docker.internal:8931/health
```

Host-side checks should use:

```text
GET http://127.0.0.1:8931/health
```

Success criteria:

- HTTP 200.
- JSON `ok=true`.
- `server=video-knowledge-openclaw-http`.
- `tools` includes `openclaw_video_plan`, `openclaw_video_ingest`, `openclaw_video_link`.
- `service_urls.openclaw_http_docker` matches `http://host.docker.internal:8931/call`.

Failure behavior:

- If port is not listening, return a clear `vkp_bridge_not_running` operator error.
- Do not fall back to guessing ports.
- Do not silently run video processing.
- Do not upload media to cloud ASR/vision as a fallback.

### 3. Add A Small Status/Registration Surface

Future VKP patch:

- Add CLI/MCP command: `openclaw-bridge-status`.
- It should read the single config source, run `/health`, and emit JSON:

```json
{
  "ok": false,
  "configured": true,
  "running": false,
  "host_call_url": "http://127.0.0.1:8931/call",
  "docker_call_url": "http://host.docker.internal:8931/call",
  "start_command": "%WORKSPACE_ROOT%\\video-knowledge-pipeline\\scripts\\start-openclaw-http.cmd",
  "operator_boundary": "Start the host bridge before OpenClaw Docker calls VKP."
}
```

Optional future helper:

- `scripts/register-openclaw-http-task.ps1`
- Creates or updates a user-level scheduled task that runs the bridge hidden.
- Must verify the command line belongs to VKP before stopping/restarting anything.
- Must not duplicate host/port values; it should read VKP config.

### 4. Security Boundary

Current local bind is acceptable for Docker through `host.docker.internal`.

Rules:

- Keep default bind to `127.0.0.1`.
- If binding to `0.0.0.0`, require `VIDEO_KNOWLEDGE_OPENCLAW_HTTP_TOKEN` or `--token`.
- Never write API keys, cookies, bearer tokens, or OpenClaw secrets into VKP docs, manifests, reports, registry files, or handoff payloads.
- The bridge should not expose arbitrary command execution; keep the narrow three-tool surface.

---

## OpenClaw Docker Path Contract

Required host/container path mapping:

```text
Host root:      %WORKSPACE_ROOT%
Container root: /mnt/used-by-codex
```

Required OpenClaw environment variables:

```text
VKP_API_BASE=http://host.docker.internal:8931
VDO_API_BASE=http://host.docker.internal:8921
VKP_HOST_ROOT=%WORKSPACE_ROOT%
VKP_CONTAINER_ROOT=/mnt/used-by-codex
```

Required Docker volume, expressed as a contract rather than an applied change:

```yaml
volumes:
  - %WORKSPACE_ROOT%:/mnt/used-by-codex
```

Practical effect:

- Host path:

```text
%WORKSPACE_ROOT%\video-download-orchestrator\downloads\...
```

- Container path:

```text
/mnt/used-by-codex/video-download-orchestrator/downloads/...
```

- VKP helper translates container paths back to Windows host paths before sending them to the host bridge.

Current gap:

- OpenClaw Docker currently mounts its own config/workspace paths, but not `%WORKSPACE_ROOT%`.
- Without this mount, OpenClaw can call the HTTP bridge but cannot reliably pass artifact paths that VKP can inspect through the documented helper flow.

---

## VDO To VKP Handoff Contract Draft

Schema name:

```text
video_knowledge_pipeline.vdo_handoff.v1
```

The handoff should be produced by VDO after a planned or confirmed download attempt. VKP consumes this as an input plan, not as proof that media is safe to process.

### Top-Level Fields

```json
{
  "schema": "video_knowledge_pipeline.vdo_handoff.v1",
  "created_at": "2026-06-16T00:00:00+08:00",
  "source_tool": "video-download-orchestrator",
  "task_id": "string",
  "source_url": "https://example.com/video",
  "canonical_url": "https://example.com/video",
  "platform": "bilibili|youtube|feishu|generic|unknown",
  "title": "string",
  "selected_backend": "yt-dlp|browser|playwright|manual|unknown",
  "vdo_status": "planned|finished|failed|needs_review",
  "media_path": "%WORKSPACE_ROOT%\\video-download-orchestrator\\downloads\\...\\video.mp4",
  "media_path_container": "/mnt/used-by-codex/video-download-orchestrator/downloads/.../video.mp4",
  "output_dir": "%WORKSPACE_ROOT%\\video-download-orchestrator\\downloads\\...",
  "sidecars": [],
  "vdo_artifacts": {},
  "review": {},
  "content_assets": {},
  "ingestion": {},
  "safety": {}
}
```

### Required Media Fields

`media_path` is required before VKP can ingest.

Valid sources, in priority order:

1. VDO review checklist `output_files[]` entry with a media extension and successful existence/size checks.
2. VDO `backend_result.output_file`.
3. VDO report summary `sniffed_media[]` or `ffprobe.path`.

If no valid media path exists, VKP must not ingest. It should return a plan with `operator_boundary=download_or_review_required`.

### Sidecar Fields

Each sidecar item:

```json
{
  "kind": "info_json|description|subtitle|thumbnail|cookies_report|other",
  "path": "%WORKSPACE_ROOT%\\...",
  "path_container": "/mnt/used-by-codex/...",
  "language": "zh-CN",
  "source": "yt-dlp|platform|manual|unknown",
  "exists": true,
  "size_bytes": 12345
}
```

Expected sidecar sources:

- VDO review checklist `archive_files`.
- VDO report summary `archive_files`.
- Known yt-dlp outputs such as `.info.json`, `.description`, `.vtt`, `.srt`, thumbnail files.

### VDO Artifact Fields

```json
{
  "manifest_path": "%WORKSPACE_ROOT%\\...\\.vdo\\manifests\\task.json",
  "report_path": "%WORKSPACE_ROOT%\\...\\report.md",
  "summary_path": "%WORKSPACE_ROOT%\\...\\summary.json",
  "review_checklist_path": "%WORKSPACE_ROOT%\\...\\review-checklist.json",
  "log_path": "%WORKSPACE_ROOT%\\...\\attempts.jsonl"
}
```

At minimum, `manifest_path` and `review_checklist_path` should be present for an executed download. A plan-only VDO result may omit media and instead provide `download_plan`.

### Review Fields

```json
{
  "needs_human_review": true,
  "manual_review_required": true,
  "review_status": "ok|warning|failed|unknown",
  "review_checklist_path": "%WORKSPACE_ROOT%\\...\\review-checklist.json",
  "reasons": [
    "download_not_confirmed",
    "media_missing",
    "ffprobe_failed",
    "site_requires_login",
    "output_needs_manual_check"
  ],
  "accepted_by_human": false
}
```

VKP automatic ingest is allowed only when:

- `vdo_status=finished`.
- `media_path` exists and is a media file.
- VDO review does not require unresolved human action, or `accepted_by_human=true`.
- The handoff explicitly records that a real download was confirmed by the operator.

Otherwise, VKP should produce a review task or next-action plan, not process the media.

### Ingestion Fields

```json
{
  "recommended_tool": "openclaw_video_ingest",
  "workspace": "%WORKSPACE_ROOT%\\video-knowledge-pipeline\\openclaw-runs\\...",
  "title": "string",
  "execute_asr": false,
  "execute_vision": false,
  "max_frames": 720,
  "next_action": "operator_review|run_ingest_plan|confirm_download|none"
}
```

Default execution flags must remain false. VKP can prepare a bundle/review workspace, but ASR, cloud vision, and real download actions remain behind explicit flags.

### Content Asset Candidate Fields

VKP may emit content asset candidates after ingest or analysis. These are drafts for human review, not publication-ready outputs.

```json
{
  "summary_path": "%WORKSPACE_ROOT%\\video-knowledge-pipeline\\...\\exports\\knowledge-note.md",
  "timeline_path": "%WORKSPACE_ROOT%\\video-knowledge-pipeline\\...\\exports\\full-transcript.md",
  "audit_path": "%WORKSPACE_ROOT%\\video-knowledge-pipeline\\...\\exports\\extraction-audit.md",
  "key_segments_path": "%WORKSPACE_ROOT%\\video-knowledge-pipeline\\...\\exports\\key-segments.md",
  "short_video_script_drafts_path": "%WORKSPACE_ROOT%\\video-knowledge-pipeline\\...\\exports\\short-video-script-drafts.md",
  "highlight_post_drafts_path": "%WORKSPACE_ROOT%\\video-knowledge-pipeline\\...\\exports\\highlight-post-drafts.md",
  "review_required": true,
  "publication_allowed": false
}
```

First implementation can leave optional candidate paths absent and still be valid. The contract should reserve this namespace now so OpenClaw/content-asset threads can route the outputs later without confusing them with raw extraction artifacts.

### Safety Fields

```json
{
  "download_was_explicitly_confirmed": false,
  "secrets_redacted": true,
  "no_cloud_execution_by_default": true,
  "content_assets_are_review_drafts": true,
  "operator_boundary": "VDO owns download. VKP owns ASR/OCR/frame understanding/knowledge exports."
}
```

---

## Recommended Future Implementation Tasks

1. Add `openclaw-bridge-status` CLI/MCP command in VKP.
2. Add optional host registration helper for a user-level scheduled task, reading port/host from VKP config.
3. Add `vdo_handoff.py` normalizer that accepts VDO manifest/report/review checklist paths and emits `video_knowledge_pipeline.vdo_handoff.v1`.
4. Add `openclaw-video-from-vdo-handoff` preview command that returns whether VKP can ingest or needs human/download review.
5. Add a content asset candidate namespace to VKP bundle/export metadata, initially populated only when existing exports are present.
6. Update `AGENT_DISCOVERY.md` and `docs/openclaw-integration.md` with:
   - bridge lifecycle,
   - health gate,
   - Docker mount contract,
   - VDO handoff contract,
   - content asset candidate review boundary.
7. Add tests:
   - bridge status returns `running=false` when port 8931 is configured but not listening,
   - handoff normalizer accepts successful VDO artifacts and produces valid `media_path`,
   - failed/no-output VDO result blocks VKP auto-ingest,
   - container path translation maps `/mnt/used-by-codex/...` to `%WORKSPACE_ROOT%\...`,
   - plan-only URL path keeps `will_download=false`,
   - content asset candidates are marked `review_required=true` and `publication_allowed=false`.

---

## Operational Checklist

Before OpenClaw calls VKP:

```powershell
cd %WORKSPACE_ROOT%\video-knowledge-pipeline
.\scripts\video-knowledge.ps1 config-status
.\scripts\start-openclaw-http.cmd
```

In another shell:

```powershell
Invoke-RestMethod http://127.0.0.1:8931/health
```

From OpenClaw Docker:

```bash
curl http://host.docker.internal:8931/health
```

Expected next decision:

- If the user wants OpenClaw to call VKP reliably without manual startup, implement the scheduled-task registration helper.
- If the user wants to keep manual control, document `start-openclaw-http.cmd` as an operator prerequisite and keep `openclaw-bridge-status` as the guardrail.
