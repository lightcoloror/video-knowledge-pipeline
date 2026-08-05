# Phase 16: OpenClaw Docker Live Contract Closure Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Make the VKP OpenClaw bridge and content material card flow verifiable from the OpenClaw Docker side without downloading or processing new video.

**Architecture:** VKP remains a host-side local service on port 8931. OpenClaw Docker calls the host bridge through `host.docker.internal`, while VDO remains responsible for download planning/execution and VKP only exposes review-only evidence/material-card artifacts.

**Tech Stack:** Python CLI/MCP/HTTP bridge, PowerShell host bridge scripts, Docker helper script, Markdown/JSON reports, pytest.

---

## Task 1: Baseline And Sync Guardrails

1. Confirm `git status --short --branch`.
2. Run `python -m pytest -q`.
3. Run the secret scan for API keys, bearer headers, and cookie references.
4. Confirm Git does not track video/audio/subtitle media.
5. Try the stable GitHub safe-push status path; if auth is unavailable, keep the local checkpoint and continue.

## Task 2: Live Smoke Report Output

1. Extend `openclaw-live-smoke` with optional `--write-report` and `--output-dir`.
2. Write `openclaw-live-smoke-report.json` and `openclaw-live-smoke-report.md` only when explicitly requested.
3. Keep the command read-only: no download, no ASR, no vision, no publishing, no knowledge-base writeback.
4. Expose the new report arguments through CLI and MCP.

## Task 3: Bridge Doctor Recovery Guidance

1. Keep `openclaw-bridge-doctor` read-only.
2. Return specific next actions for scheduled task missing, Startup fallback missing, and started-then-exited states.
3. Include visible PowerShell commands for task registration/start, Startup fallback installation, health, contract, and doctor verification.
4. Do not register tasks or start services automatically from doctor.

## Task 4: Docker Helper And HTTP Tool Coverage

1. Expose `batch_content_asset_status` and `content_handoff_pack` through the OpenClaw HTTP bridge.
2. Add Docker helper commands:
   - `batch-content-status <container-path>`
   - `content-handoff-pack <container-path>`
3. Translate `/mnt/used-by-codex/...` paths back to `%WORKSPACE_ROOT%\...` before posting to the host bridge.
4. Preserve existing `status`, `contract`, `live-smoke`, and `content-status` commands.

## Task 5: Documentation And Verification

1. Update README, `AGENT_DISCOVERY.md`, and `docs/openclaw-integration.md` with the Phase 16 host and Docker smoke commands.
2. Add tests for report writing, Docker helper payloads, and HTTP bridge tool exposure.
3. Run focused tests for OpenClaw/client/content paths.
4. Run full regression, `git diff --check`, secret scan, and media scan.
5. Commit with `feat: close openclaw docker live contract`.
