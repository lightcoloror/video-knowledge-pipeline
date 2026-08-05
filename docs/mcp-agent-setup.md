# MCP Agent Setup

Updated: 2026-06-04

The lecture extraction POC exposes the current workflow through the
`lecture-extract` MCP server. Use this when an AI agent should call the same
local orchestration layer as the CLI and BiliNote UI.

## Generate Config

From `%WORKSPACE_ROOT%\question-research-poc`:

```powershell
.\scripts\write-mcp-config.ps1 -Client codex -Validate
```

Write the config to a file:

```powershell
.\scripts\write-mcp-config.ps1 -Client codex -Output .\mcp.lecture-extract.json -Validate
.\scripts\write-mcp-config.ps1 -Client claude -Output .\mcp.lecture-extract.json -Validate
```

`-Validate` runs:

```powershell
python -m question_research_poc.mcp_server --list-tools
```

with `PYTHONPATH` pointed at the local `src` directory. This catches broken
local imports before the config is pasted into an agent client.

## Config Shape

Codex-style and Claude Desktop-style clients can use the same core shape:

```json
{
  "mcpServers": {
    "lecture-extract": {
      "command": "python",
      "args": ["-m", "question_research_poc.mcp_server"],
      "cwd": "%WORKSPACE_ROOT%\\question-research-poc",
      "env": {
        "PYTHONPATH": "%WORKSPACE_ROOT%\\question-research-poc\\src"
      }
    }
  }
}
```

Use `-Python` if the agent client needs a specific interpreter:

```powershell
.\scripts\write-mcp-config.ps1 -Python C:\Path\To\python.exe -Output .\mcp.lecture-extract.json -Validate
```

## Useful Tools

The most useful agent-facing tools for the current recommended route are:

- `prepare_video_source`: plan or explicitly execute `video-download-orchestrator` for a URL, writing source provenance before any lecture extraction starts.
- `prepare_lecture_workspace_from_url`: URL entrypoint that first prepares/downloads the source video, then creates a normal lecture workspace when `execute: true` produced local media.
- `prepare_lecture_workspace`: create a planned extraction workspace for one video.
- `recommended_route_status`: inspect which local extractor route should run next.
- `recommended_workspace_advance`: preview or execute the normal route queue plus ready-output import.
- `lecture_project_health`: inspect package, bundle, extractor, ASR, BiliNote patch readiness, and review state.
- `lecture_next_step`: execute only safe local glue steps.
- `refresh_lecture_review_outputs`: refresh source package, WebUI bundle, and optional Obsidian export after BiliNote review.
- `bundle_source_artifacts`: inspect or explicitly rebuild the original extractor artifact index for a WebUI bundle.
- `audit_knowledge_coverage`: inspect no-loss coverage across speech, OCR/screen text, visual frames, structured visual material, time-axis gaps, and source-artifact traceability.
- `run_video_frame_router`: classify bundle timeline frames into `document_visual`, `semantic_frame`, `temporal_sequence`, `mixed`, or `unknown`.
- `run_multimodal_frame_analysis`: preview/import or explicitly execute OpenAI-compatible single-frame visual understanding for non-document screenshots.
- `run_temporal_visual_analysis`: preview/import or explicitly execute OpenAI-compatible 5-12 frame sequence understanding for operations, demos, experiments, and state changes.
- `build_lecture_study_index`: rebuild evidence-preserving study index and study cards.
- `bilinote_patch_status`: check whether the packaged BiliNote lecture patch is installed or drifted.
- `apply_bilinote_patch`: preview or explicitly install/repair the packaged
  BiliNote lecture patch; read-only unless `execute: true`.

The MCP server mirrors the CLI safety model: extractor/ASR execution is explicit,
and preview paths are available for agent planning without running long local
jobs.

## URL Source Flow

Use URL ingestion only through the local `video-download-orchestrator` front door. The default mode is dry-run:

```json
{
  "url": "https://www.bilibili.com/video/BV...",
  "output_dir": "D:\\path\\to\\downloads"
}
```

Call MCP `prepare_video_source` first. It writes:

- `video-source-provenance.json`
- `video-source-provenance.md`
- the orchestrator manifest path when available

Only pass `execute: true` after the human/operator accepts the dry-run plan. To create the lecture extraction workspace from a URL, call `prepare_lecture_workspace_from_url` with the same safety model:

```json
{
  "project": "D:\\path\\to\\research-project",
  "url": "https://www.bilibili.com/video/BV...",
  "title": "课程名",
  "download_output_dir": "D:\\path\\to\\downloads",
  "output_root": "D:\\path\\to\\planned-runs"
}
```

Without `execute: true`, it returns `status: download_planned` and does not create a workspace. With `execute: true`, it scans the download directory for the produced local video file, then calls the normal `prepare_lecture_workspace` flow and embeds `source_provenance` in `lecture-pipeline-plan.json` and `lecture-pipeline-plan.md`.

## Video Visual Understanding Order

For WebUI bundles, agents should use this order:

1. `run_video_frame_router`
2. `run_multimodal_frame_analysis` for `semantic_frame` / `mixed`
3. `run_temporal_visual_analysis` for `temporal_sequence` / `mixed`
4. `run_visual_structure_plan` only for `document_visual` screenshots where PPT, board, table, formula, code, or document-page parsing is needed.

`run_multimodal_frame_analysis` and `run_temporal_visual_analysis` default to preview/import mode. They call a vision API only when `execute: true` is passed. Configure API execution with `provider_config` or environment variables:

- `LECTURE_VISION_BASE_URL`
- `LECTURE_VISION_API_KEY`
- `LECTURE_VISION_MODEL`
- `LECTURE_VISION_TIMEOUT_SECONDS`

For document-like screenshots, prefer the existing `ebook_markdown_pipeline` MCP/HTTP/CLI path:

```text
process_material -> get_job_status -> read_artifact
```

Then import the cleaned Markdown/table/formula/code JSON through `run_visual_structure_plan`.

`lecture_project_health` accepts optional `bilinote_root` and
`bilinote_patch_root` arguments. Use them when an agent is validating a custom
BiliNote checkout; otherwise it checks the default local reviewed BiliNote tree.
The returned `recommended_tools.tools[]` BiliNote row includes `patch_status`
with the same `installed`, `missing`, and `drift` counts as
`bilinote_patch_status`.

`lecture_next_step` accepts the same BiliNote patch-check arguments. If a WebUI
bundle is ready but the target BiliNote tree is not patched, the selected action
is `setup_bilinote_patch` with `manual_required` mode, so an agent does not ask
the user to start human review in an unusable UI shell.
The returned `selected_action.command` contains the same command selected by
`lecture_project_health`, and `lecture_action_log` preserves that command in the
JSONL log plus the Markdown action table.
To resolve that state through MCP, call `apply_bilinote_patch` first in preview
mode, then call it again with `execute: true` only after the operator intends to
modify the target BiliNote checkout.
`prepare_lecture_workspace` also writes `mcp-apply-bilinote-patch.args.json`
into each planned workspace, so agents can use the same preview-first repair
path from the generated handoff and dashboard.
