# Phase 12: Human Review Pack and Closure

Update: 2026-06-13  |  Acting tool/model: Codex GPT-5

## Goal

Move human review from a flat list of open targets into a trackable closure workflow:

- generate grouped review packs for batch human work;
- keep a machine-readable todo JSON beside the human-readable pack;
- expose open/closed/invalid/imported review progress;
- refresh exports and status reports after review import;
- keep the static WebUI as the human workbench and CLI/MCP as the agent interface.

## Implemented Interfaces

- `prepare-review-session <bundle>`
  - adds `--group-by reason|suggested_status|route`;
  - adds `--include-closed`;
  - adds `--output-prefix`;
  - writes `review-pack.md`, `review-pack.json`, `review-notes.todo.json`, `review-closure-status.md`, `review-closure-status.json`.

- `review-closure-status <bundle>`
  - writes `review-closure-status.md/json`;
  - reports total/open/closed review targets, imported rows, invalid rows, open reasons, closed statuses, suggested statuses, and the next review batch command.

- MCP tools
  - `prepare_review_session` accepts the new review pack arguments;
  - `review_closure_status` exposes the progress report for agents.

## Workflow

1. Run `prepare-review-session --limit 0` to generate the full review pack.
2. Edit or export review notes from the static `review.html` / `review-notes.todo.json`.
3. Run `validate-review-notes`.
4. Run `apply-review-notes`.
5. Run `review-closure-status` or `acceptance-check` to confirm open count and remaining risks.

`apply-review-notes` refreshes coverage/readiness, exports, acceptance, bundle status, review HTML, and closure status after import.

## WebUI

`review.html` now surfaces:

- review pack and closure status links;
- a review progress panel;
- quick status buttons for `accepted_known_gap`, `keep_image`, `needs_rerun_ocr`, and `corrected_visual_text`;
- existing static export/import workflow, without a backend.

## Batch Integration

`batch-repair-run` now links review packs and closure reports through bundle reports. When a `review-pack.json` exists, `batch-human-review.md` expands human review rows down to timeline item level with reason, suggested action, and evidence path.

## Validation

Required gates:

- focused tests for review closure and batch repair;
- full `pytest`;
- real bundle generation of `review-pack.*` and `review-closure-status.*`;
- `acceptance-check`;
- `mcp-audit-bundle`;
- secret scan for common API key patterns.

