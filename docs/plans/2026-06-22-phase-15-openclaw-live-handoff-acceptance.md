# Phase 15: OpenClaw Live Handoff Acceptance Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Make the Phase 14 content material card flow verifiable from OpenClaw/Docker with a stable host bridge and safe downstream handoff artifacts.

**Architecture:** VKP remains a host-side local video knowledge service. VDO owns download planning/execution, OpenClaw calls VKP through the host bridge, and content/朋友圈 consumers only receive review-only evidence cards.

**Tech Stack:** Python CLI/MCP/HTTP bridge, PowerShell startup helpers, static Markdown/JSON artifacts, pytest.

---

## Task 1: Baseline Guardrails

1. Confirm `git status --short --branch`.
2. Confirm no tracked video/audio/subtitle media files.
3. Run the existing secret scan patterns for API keys, bearer headers, and cookies references.
4. Do not process or download any new real video.

## Task 2: Bridge Doctor And Live Smoke

1. Add a read-only `openclaw-bridge-doctor` report that combines config, bridge status, task status, Startup fallback status, and recent bridge logs.
2. Add `openclaw-live-smoke` to check the bridge, optional Docker contract, and optional content asset status without processing video.
3. Expose both through CLI, MCP, and local `mcp-call`.
4. Keep task registration/start commands as recommendations only; do not auto-register from doctor/smoke.

## Task 3: Batch Content Asset Status

1. Add `batch-content-asset-status` to accept one bundle, a directory of bundles, or a JSON summary with bundle paths.
2. Write `batch-content-material-cards.json/md` only when `write=true`.
3. Report ready/export_required/material_card_needs_reexport counts and next actions.
4. Never run ASR, vision, download, or export automatically.

## Task 4: Content Handoff Pack

1. Add `content-handoff-pack` for ready material cards only.
2. Output `content-handoff-pack.json/md` with review-only routing fields, evidence paths, and fact-check warnings.
3. Exclude cards where `publication_allowed=true` or `allowed_as_fact=true`; these indicate unsafe or malformed input.
4. Do not write Logseq/Obsidian and do not generate publish-ready copy.

## Task 5: Docker Helper And Docs

1. Keep Docker helper path translation for `content-status`.
2. Add helper payload tests for live smoke and batch/handoff commands where useful.
3. Update README, AGENT_DISCOVERY, and OpenClaw docs with the new commands and visible PowerShell bridge verification flow.

## Task 6: Verification

1. Run focused tests for OpenClaw and content asset modules.
2. Run `python -m pytest -q`.
3. Run `git diff --check`.
4. Re-run secret/media scans.
5. Commit with `feat: add openclaw live handoff checks`.
