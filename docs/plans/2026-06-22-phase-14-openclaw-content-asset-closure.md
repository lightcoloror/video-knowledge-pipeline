# Phase 14: OpenClaw Runtime And Content Material Card Closure Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Make VKP reliably callable from OpenClaw and make exported video evidence safe for content-asset and circle-of-friends inspiration workflows.

**Architecture:** VKP keeps the existing VDO/OpenClaw boundary: VDO owns link planning and download execution, VKP owns local-video understanding and export artifacts. This phase adds a first-class content material card export and a read-only status interface without changing download or model execution behavior.

**Tech Stack:** Python CLI/MCP/HTTP bridge, static Markdown/JSON exports, PowerShell bridge lifecycle scripts, pytest.

---

## Task 1: Baseline And Guardrail Check

**Files:** no tracked edits.

1. Run `git status --short --branch` and confirm the repo has no uncommitted changes before implementation.
2. Run tracked-media scan with `git ls-files` for video/audio/subtitle extensions.
3. Run secret scan for API keys, bearer headers, and cookies references.
4. Record that real videos, cookies, ASR outputs, and review bundles remain ignored.

## Task 2: Content Material Card Export

**Files:**
- Modify: `src/video_knowledge_pipeline/knowledge_note_export.py`
- Test: `tests/test_knowledge_export.py`

1. Add `exports/content-material-card.json` and `exports/content-material-card.md` to `export_knowledge_note`.
2. Build the JSON card from the shared self-media fields: `material_id`, `source_path`, `source_type`, `source_fact_status`, `evidence_tier`, `privacy_level`, `desensitized`, `compliance_risk`, `fact_check_status`, `target_layer`, `publish_surface`, `content_stage`, `cta_type`, `crm_followup_needed`, `owner_thread`, `next_action`, and `blocked_reason`.
3. Keep exported cards conservative: `review_required=true`, `publication_allowed=false`, `allowed_as_inspiration=true`, `allowed_as_fact=false`, `circle_of_friends_status=needs_review_inspiration`.
4. Add both card paths to `content_assets`, `export-summary.json`, and `manifest.json`.
5. Test that both files exist and that the card cannot be treated as a fact or publishable artifact.

## Task 3: Content Asset Status Interface

**Files:**
- Create: `src/video_knowledge_pipeline/content_asset_status.py`
- Modify: `src/video_knowledge_pipeline/cli.py`
- Modify: `src/video_knowledge_pipeline/mcp_server.py`
- Modify: `src/video_knowledge_pipeline/openclaw_http.py`
- Test: `tests/test_knowledge_export.py`
- Test: `tests/test_openclaw_integration.py`

1. Implement `content_asset_status(bundle_dir, write=false)` as a read-only status report.
2. Return `export_required` when no material card exists, and `ready_for_inspiration_review` when the material card exists with safe draft-only flags.
3. Include material card paths, missing fields, `publication_allowed`, `review_required`, `allowed_as_inspiration`, `allowed_as_fact`, `human_confirmation_required`, and `next_actions`.
4. Expose the tool through CLI, MCP, local `mcp-call`, and OpenClaw HTTP `/call`.
5. Add bridge health/tool tests confirming `content_asset_status` is listed and callable.

## Task 4: Docs And Discovery

**Files:**
- Modify: `README.md`
- Modify: `AGENT_DISCOVERY.md`
- Modify: `docs/openclaw-integration.md`

1. Document the two new artifacts and the `content-asset-status` command.
2. Clarify that VDO handoff remains `candidate`, while VKP export becomes `evidence`.
3. Keep `publication_allowed=false` and review boundary visible in the quick-start/discovery path.

## Task 5: Real Bundle Verification

**Files:** no tracked edits expected; outputs stay under ignored `openclaw-runs`.

1. Run `export-knowledge-note` on `openclaw-runs\knowledge\BV134Ei6KEaJ-browser-automation\webui-bundle`.
2. Run `content-asset-status` on the same bundle.
3. Confirm these paths exist: `knowledge-note.md`, `full-transcript.md`, `extraction-audit.md`, `content-material-card.json`, and `content-material-card.md`.

## Task 6: Final Regression

**Files:** commit only tracked source/docs/tests/plan changes.

1. Run focused tests for knowledge export and OpenClaw integration.
2. Run `python -m pytest -q`.
3. Run `git diff --check`.
4. Re-run secret/media scans.
5. Commit with `feat: add content material card status`.
