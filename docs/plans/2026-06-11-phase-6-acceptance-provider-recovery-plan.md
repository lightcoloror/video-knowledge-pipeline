# Phase 6 Acceptance and Provider Recovery Implementation Plan

**Goal:** Turn the current real-bundle preview into an operator-safe acceptance loop: the project can say whether a video bundle is complete, provider-blocked, human-review-blocked, or ready for the next machine action, and it can recover provider execution without hiding gaps.

**Architecture:** Keep `video-knowledge-pipeline` as the orchestration layer. External tools still provide ASR, document-frame parsing, and multimodal vision; this phase adds a single acceptance decision layer, explicit provider recovery commands, review-note templates, WebUI surface, and final lecture-note quality checks.

**Tech Stack:** Python package under `src/video_knowledge_pipeline`, pytest, PowerShell wrapper `scripts/video-knowledge.ps1`, MCP bridge, static WebUI bundle, OpenAI-compatible/Gemini/Agnes provider profiles, `ebook_markdown_pipeline`, ffmpeg frame groups.

---

## Update Record

- 2026-06-11 14:05:00 | Codex (GPT-5) | Created Phase 6 plan after the preview bundle gained provider health gates but remained blocked by live provider reachability and unresolved semantic/temporal visual coverage.

## Current Baseline

Reference bundle:

```text
%WORKSPACE_ROOT%\video-knowledge-pipeline\real-tests\feishu-video-retry-live-asr\phase2-review-preview-bundle
```

Current known state:

| Area | Current State | Interpretation |
|---|---|---|
| ASR | `speech = 68 / 68` | Complete enough for this phase |
| Frames | `visual_frames = 68 / 68` | Evidence frames exist |
| Routing | `visual_route = 68 / 68` | Main branch routing exists |
| Document visual | `structured_visual = 9 / 9` | Covered through evidence-preserving human fallback |
| Screen text | `screen_text = 9 / 68`, weak but no blocker | Weak channel, not the active blocker |
| Semantic vision | `semantic_frame_understanding = 17 / 61` | 44 missing, main content gap |
| Temporal vision | `temporal_visual_understanding = 8 / 12` | 4 missing, secondary content gap |
| Provider health | `provider_unreachable`, safe `false` | Machine vision execution must remain blocked |
| Controlled execution | `blocked`, restore available | Correctly refuses unsafe real model writes |
| Markdown export | exists | Needs final acceptance and quality gate |

The project is not failing because the architecture is wrong. It is blocked because the real provider path is not yet healthy, and because final acceptance logic is still split across status, coverage, preflight, review, and export reports.

## Phase 6 Acceptance Target

Phase 6 is complete when the real preview bundle reaches one of these truthful states:

| State | Meaning |
|---|---|
| `complete` | No known unresolved extraction, vision, review, export, or provider blocker |
| `accepted_with_known_gaps` | Remaining gaps are explicitly human-reviewed with evidence paths |
| `provider_blocked` | Machine vision can proceed only after provider/network/key/model repair |
| `human_review_required` | Human decision is needed before acceptance |
| `machine_action_available` | A safe next machine command exists and is confirmed by preflight |
| `incomplete` | Required evidence or setup is missing |

For the current bundle, the expected first honest target is `provider_blocked`, not `complete`.

## Non-Goals

- Do not redesign the ASR path.
- Do not replace `ebook_markdown_pipeline`.
- Do not upload full videos to a model.
- Do not import fake model outputs into the real bundle to make coverage green.
- Do not store API keys in docs, reports, manifests, tests, or generated args.
- Do not make Peepshow the main knowledge generator.

## Task 1: Add a First-Class `acceptance-check`

**Files:**

- Modify: `src/video_knowledge_pipeline/cli.py`
- Modify: `src/video_knowledge_pipeline/mcp_server.py`
- Modify: `src/video_knowledge_pipeline/bundle_status.py`
- Modify: `src/video_knowledge_pipeline/knowledge_coverage.py`
- Create or modify: `src/video_knowledge_pipeline/acceptance_check.py`
- Test: `tests/test_video_pipeline_smoke.py`

**Step 1: Write failing tests for acceptance states**

Add tests that build small bundles or fixture status objects and assert:

- provider health `safe_to_execute=false` plus missing semantic/temporal items returns `provider_blocked`;
- missing semantic/temporal items with no provider health check returns `machine_action_available`;
- review notes with accepted known gaps can return `accepted_with_known_gaps`;
- missing ASR or missing frames returns `incomplete`;
- stale export returns an export freshness issue.

Run:

```powershell
python -m pytest tests\test_video_pipeline_smoke.py -q
```

Expected before implementation: the new tests fail because no unified acceptance object exists.

**Step 2: Implement `acceptance_check.py`**

Return a stable JSON shape:

```json
{
  "schema": "lecture_acceptance_check.v1",
  "checked_at": "2026-06-11T14:05:00",
  "status": "provider_blocked",
  "bundle_dir": "...",
  "summary": {
    "speech": "ok",
    "frames": "ok",
    "visual_route": "ok",
    "document_visual": "accepted",
    "semantic_visual": "blocked",
    "temporal_visual": "blocked",
    "provider_health": "provider_unreachable",
    "export_freshness": "stale_or_missing"
  },
  "blockers": [
    {
      "key": "provider_health_failed",
      "severity": "blocking",
      "next_action": "run vision-provider-smoke or switch provider"
    }
  ],
  "next_action": {
    "key": "provider_repair",
    "mcp_tool": "vision_provider_smoke"
  }
}
```

Do not duplicate all coverage logic. Read existing `knowledge-coverage.json`, `bundle-status.json`, `vision-execution-preflight.json`, review notes, and export summary.

**Step 3: Add CLI and MCP tools**

CLI:

```powershell
.\scripts\video-knowledge.ps1 acceptance-check <webui-bundle>
```

MCP:

```text
acceptance_check(bundle_dir)
```

Write:

- `acceptance-check.json`
- `acceptance-check.md`
- `mcp-acceptance-check.args.json`

**Step 4: Verify real bundle**

Run:

```powershell
.\scripts\video-knowledge.ps1 acceptance-check %WORKSPACE_ROOT%\video-knowledge-pipeline\real-tests\feishu-video-retry-live-asr\phase2-review-preview-bundle
```

Expected current result:

- status is `provider_blocked`;
- semantic missing count remains visible as `44`;
- temporal missing count remains visible as `4`;
- provider health is `provider_unreachable`;
- no API key is printed or written.

## Task 2: Add Provider Recovery Commands

**Files:**

- Modify: `src/video_knowledge_pipeline/vision_api.py`
- Modify: `src/video_knowledge_pipeline/vision_preflight.py`
- Modify: `src/video_knowledge_pipeline/cli.py`
- Modify: `src/video_knowledge_pipeline/mcp_server.py`
- Test: `tests/test_video_pipeline_smoke.py`

**Step 1: Add tests for provider profile smoke**

Cover:

- `openai`, `gemini`, `agnes`, and `custom_openai_compatible` profiles build sanitized configs;
- missing key returns `missing_api_key`;
- timeout returns `provider_unreachable`;
- JSON parse failure returns `model_output_parse_failed`;
- report redacts secrets.

**Step 2: Add CLI/MCP provider smoke**

CLI:

```powershell
.\scripts\video-knowledge.ps1 vision-provider-smoke --provider agnes --single-image <frame-path> --multi-image-dir <frame-group-dir> --timeout-seconds 8
```

MCP:

```text
vision_provider_smoke(provider?, single_image?, multi_image_dir?, timeout_seconds?)
```

The command should write:

- `vision-provider-smoke.json`
- `vision-provider-smoke.md`

**Step 3: Add provider recovery suggestions**

When smoke fails, report one of:

- `missing_api_key`: set the provider-specific env var locally;
- `provider_unreachable`: check network/proxy/base URL/timeout;
- `provider_auth_failed`: rotate or verify key;
- `provider_rate_limited`: wait or switch provider;
- `model_output_parse_failed`: use JSON repair or switch model.

Never write the raw key, request headers, or bearer token to disk.

**Step 4: Verify with Agnes short timeout**

Run:

```powershell
.\scripts\video-knowledge.ps1 vision-provider-smoke --provider agnes --timeout-seconds 8
```

Expected if the current network issue persists:

- status `provider_unreachable`;
- safe `false`;
- human-readable recovery advice.

## Task 3: Make Provider State Override Unsafe Next Actions

**Files:**

- Modify: `src/video_knowledge_pipeline/bundle_next.py`
- Modify: `src/video_knowledge_pipeline/bundle_status.py`
- Modify: `src/video_knowledge_pipeline/webui_bridge.py`
- Test: `tests/test_video_pipeline_smoke.py`

**Step 1: Add tests for next-action priority**

Assert:

- if coverage says semantic model action is needed but provider health is unsafe, top-level next action becomes `provider_repair`;
- controlled execution remains `blocked`;
- MCP args point to provider smoke or preflight repair, not direct model execution;
- once provider health is safe, next action returns to `run_multimodal_frame_analysis` or `run_temporal_visual_analysis`.

**Step 2: Implement next-action priority**

Priority order:

1. Missing source evidence or ASR/frame setup.
2. Provider repair, if a model action is needed and latest provider health is unsafe.
3. Human review, if no safe machine action can resolve the gap.
4. Machine action, if preflight and confirmations are ready.
5. Export, if coverage is accepted and export is stale.
6. Complete / accepted.

**Step 3: Verify real bundle status**

Run:

```powershell
.\scripts\video-knowledge.ps1 bundle-status-report %WORKSPACE_ROOT%\video-knowledge-pipeline\real-tests\feishu-video-retry-live-asr\phase2-review-preview-bundle
```

Expected:

- top-level status should not suggest direct `run_multimodal_frame_analysis` while provider health is unsafe;
- it should direct the operator to provider repair/preflight.

## Task 4: Generate Fillable Human Review Templates

**Files:**

- Modify: `src/video_knowledge_pipeline/review_session.py`
- Modify: `src/video_knowledge_pipeline/knowledge_coverage.py`
- Modify: `src/video_knowledge_pipeline/knowledge_note_export.py`
- Modify: `src/video_knowledge_pipeline/webui_bridge.py`
- Test: `tests/test_video_pipeline_smoke.py`

**Step 1: Add tests for review template generation**

Assert `prepare-review-session` creates:

- `review-session.md`
- `review-session.json`
- `review-notes.template.json`

Template rows must include:

- `timeline_index`
- `time_range`
- `route`
- `reason`
- `suggested_status`
- `evidence_frame_paths`
- `transcript_excerpt`
- `visual_text_excerpt`
- `model_output_excerpt`
- empty correction fields.

**Step 2: Normalize review statuses**

Supported statuses:

- `accepted`
- `keep_image`
- `accepted_no_visual_content`
- `accepted_provider_blocked`
- `corrected_visual_text`
- `corrected_visual_understanding`
- `corrected_temporal_visual_understanding`
- `needs_recapture`
- `needs_model_retry`

Review notes must never destructively overwrite ASR, OCR, model, or source-artifact fields.

**Step 3: Verify on current bundle**

Run:

```powershell
.\scripts\video-knowledge.ps1 prepare-review-session %WORKSPACE_ROOT%\video-knowledge-pipeline\real-tests\feishu-video-retry-live-asr\phase2-review-preview-bundle
```

Expected:

- semantic missing indexes include examples such as `4, 6, 9, 15, 19`;
- temporal missing indexes include `21, 26, 31, 32`;
- template is directly fillable by a human or another agent.

## Task 5: Add Lecture Note Quality Gate

**Files:**

- Modify: `src/video_knowledge_pipeline/knowledge_note_export.py`
- Create or modify: `src/video_knowledge_pipeline/note_quality.py`
- Modify: `src/video_knowledge_pipeline/cli.py`
- Modify: `src/video_knowledge_pipeline/mcp_server.py`
- Test: `tests/test_video_pipeline_smoke.py`

**Step 1: Add tests for required sections**

`knowledge-note.md` must contain:

```markdown
# <title>
## 视频概要
## 章节化知识结构
## 关键概念与论点
## 图文与视觉证据
## 操作演示与状态变化
## 表格、公式、代码与必须保留的图片
## 逐字稿与演示记录
## 未解决缺口
## 证据索引
```

**Step 2: Add `note-quality-check`**

CLI:

```powershell
.\scripts\video-knowledge.ps1 note-quality-check <webui-bundle>
```

MCP:

```text
note_quality_check(bundle_dir)
```

Checks:

- required sections exist;
- each chapter has evidence indexes or explicit gaps;
- `full-transcript.md` exists and has chronological transcript entries;
- unresolved visual gaps are not hidden;
- generated export is newer than timeline/review notes.

**Step 3: Feed quality result into acceptance**

`acceptance-check` should treat stale or low-quality export as:

- `machine_action_available` if export can be regenerated;
- `human_review_required` if note has hidden unresolved gaps;
- not `complete`.

## Task 6: WebUI Surface for Acceptance and Recovery

**Files:**

- Modify: `src/video_knowledge_pipeline/webui_bridge.py`
- Modify: generated `review.html` template logic if applicable
- Test: `tests/test_video_pipeline_smoke.py`

**Step 1: Add WebUI contract tests**

Assert generated review bundle exposes:

- acceptance status path;
- provider health status;
- provider recovery command;
- semantic missing count;
- temporal missing count;
- review template path;
- export quality status.

**Step 2: Add visible sections**

`review.html` should show:

- `当前验收状态`
- `Provider 健康`
- `剩余视觉缺口`
- `下一步命令`
- `人工审核模板`
- `导出质量`

This can be static HTML populated from generated JSON. It does not need a full editing app in this phase.

**Step 3: Verify by opening the bundle**

Use the current review page:

```text
%WORKSPACE_ROOT%\video-knowledge-pipeline\real-tests\feishu-video-retry-live-asr\phase2-review-preview-bundle\review.html
```

Expected:

- a human can see why the bundle is not complete;
- a human can copy the exact next command;
- no API key or sensitive env value is visible.

## Task 7: Real Bundle Phase 6 Acceptance Run

**Files:**

- Generated:
  - `acceptance-check.json`
  - `acceptance-check.md`
  - `vision-provider-smoke.json`
  - `vision-provider-smoke.md`
  - `review-notes.template.json`
  - `note-quality-check.json`
  - `note-quality-check.md`
- Docs:
  - `docs/plans/2026-06-11-phase-6-acceptance-provider-recovery-plan.md`
  - `docs/architecture.md`

**Run sequence:**

```powershell
python -m pytest -q
.\scripts\video-knowledge.ps1 vision-provider-smoke --provider agnes --timeout-seconds 8
.\scripts\video-knowledge.ps1 acceptance-check %WORKSPACE_ROOT%\video-knowledge-pipeline\real-tests\feishu-video-retry-live-asr\phase2-review-preview-bundle
.\scripts\video-knowledge.ps1 bundle-status-report %WORKSPACE_ROOT%\video-knowledge-pipeline\real-tests\feishu-video-retry-live-asr\phase2-review-preview-bundle
.\scripts\video-knowledge.ps1 prepare-review-session %WORKSPACE_ROOT%\video-knowledge-pipeline\real-tests\feishu-video-retry-live-asr\phase2-review-preview-bundle
.\scripts\video-knowledge.ps1 export-knowledge-note %WORKSPACE_ROOT%\video-knowledge-pipeline\real-tests\feishu-video-retry-live-asr\phase2-review-preview-bundle --title "feishu-video-retry"
.\scripts\video-knowledge.ps1 note-quality-check %WORKSPACE_ROOT%\video-knowledge-pipeline\real-tests\feishu-video-retry-live-asr\phase2-review-preview-bundle
```

Expected final result for the current environment:

- tests pass;
- provider smoke either passes or records a precise provider blocker;
- acceptance status is truthful, likely `provider_blocked`;
- top-level next action does not invite unsafe direct model execution;
- review template lists the remaining semantic and temporal visual gaps;
- exported Markdown stays readable and evidence-linked;
- secret scan finds no real provider key.

## Suggested Commit Slices

1. `feat: add bundle acceptance check`
2. `feat: add vision provider smoke command`
3. `feat: prioritize provider repair in next action`
4. `feat: generate fillable review templates`
5. `feat: add lecture note quality gate`
6. `feat: surface acceptance status in webui`
7. `test: verify phase six real bundle acceptance`

## Stop Conditions

Pause and reassess if:

- all configured cloud vision providers fail even text ping after proxy/base URL checks;
- the provider returns unstable non-JSON for two consecutive image smoke attempts;
- manual review becomes faster than provider repair for the remaining 48 visual gaps;
- WebUI needs real editing before review templates are usable;
- `knowledge-note.md` starts hiding unresolved visual gaps in prose.

## Completion Check

Phase 6 is complete when:

```powershell
python -m pytest -q
.\scripts\video-knowledge.ps1 acceptance-check %WORKSPACE_ROOT%\video-knowledge-pipeline\real-tests\feishu-video-retry-live-asr\phase2-review-preview-bundle
.\scripts\video-knowledge.ps1 note-quality-check %WORKSPACE_ROOT%\video-knowledge-pipeline\real-tests\feishu-video-retry-live-asr\phase2-review-preview-bundle
```

returns a state that a human can trust:

- `complete`, or
- `accepted_with_known_gaps`, or
- `provider_blocked` with exact repair commands and no hidden visual gaps.
