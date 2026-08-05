# Phase 5 Real Provider and Note Quality Implementation Plan

**Goal:** Move the project from "pipeline pieces can run" to "one real video can be truthfully accepted, exported as readable Markdown, and blocked only by explicit provider or human-review decisions."

**Architecture:** Keep `video-knowledge-pipeline` as the orchestration and evidence-fusion layer. ASR, OCR/document parsing, and vision models remain external providers; this phase adds provider health gates, real-bundle acceptance checks, better Markdown synthesis, and a human-review fallback that counts only when it preserves evidence.

**Tech Stack:** Python package under `src/video_knowledge_pipeline`, pytest, PowerShell wrapper `scripts/video-knowledge.ps1`, local WebUI bundle artifacts, `ebook_markdown_pipeline` for document-like frames, OpenAI-compatible/Gemini/Agnes vision provider adapters, ffmpeg temporal frame groups.

---

## Update Record

- 2026-06-11 13:18:56 | Codex (GPT-5) | Created Phase 5 plan after the preview bundle reached truthful OCR/keep-image handling and temporal frame-group generation, while Agnes live provider calls remained unavailable.

## Current Baseline

Reference preview bundle:

```text
%WORKSPACE_ROOT%\video-knowledge-pipeline\real-tests\feishu-video-retry-live-asr\phase2-review-preview-bundle
```

Current coverage snapshot:

| Channel | Current | Status |
|---|---:|---|
| speech | 68 / 68 | ok |
| visual_frames | 68 / 68 | ok |
| visual_route | 68 / 68 | ok |
| screen_text | 9 / 68 | weak, but no blocker after human keep-image review |
| structured_visual | 9 / 9 | ok through evidence-preserving human fallback |
| semantic_frame_understanding | 17 / 61 | blocked, 44 missing |
| temporal_visual_understanding | 8 / 12 | blocked, 4 missing |
| source_artifacts | 1 / 1 | ok |
| time_axis | 100 / 100 | ok |

Temporal frame-group status:

- `run-temporal-frame-groups --execute --frame-count 8 --limit 10` generated 10 frame groups.
- Generated indexes: `12,16,17,18,21,25,26,31,32,66`.
- Each generated group has `8/8` ordered frames.

Provider status:

- `.local\vision.env` currently configures an Agnes/OpenAI-compatible provider without storing secrets in repo docs.
- Live provider probes failed with timeout or TLS EOF symptoms.
- Therefore the project must not treat Agnes as a usable production provider until a provider smoke test passes.

## Phase 5 Acceptance Target

This phase is complete when:

1. Provider health is explicit: usable, missing key, network/TLS failure, JSON failure, or unsupported image/multi-image input.
2. `bundle-next-action` can choose between machine action, provider repair, temporal frame-group generation, human review, and export.
3. The real preview bundle can reach either:
   - `complete`, or
   - `accepted_with_known_gaps`, with every remaining gap tied to human review or provider blocker.
4. `exports/knowledge-note.md` is a layered Markdown lecture note, not a raw timeline dump.
5. `exports/full-transcript.md` preserves the complete chronological transcript and demonstration record.
6. `acceptance-check` gives a single truthful result for CLI, MCP, and WebUI.
7. `python -m pytest -q` passes.

## Non-Goals

- Do not build a local VLM in this phase.
- Do not replace `ebook_markdown_pipeline`.
- Do not upload full video files to a model.
- Do not hide provider failures by importing fake fixture outputs into real bundles.
- Do not store API keys, bearer tokens, or provider secrets in manifest, docs, tests, reports, or generated discovery files.

## Task 1: Make Vision Provider Health a First-Class Gate

**Files:**

- Modify: `src/video_knowledge_pipeline/vision_api.py`
- Modify: `src/video_knowledge_pipeline/vision_preflight.py`
- Modify: `src/video_knowledge_pipeline/multimodal_frame_analyzer.py`
- Modify: `src/video_knowledge_pipeline/temporal_visual_analyzer.py`
- Modify: `tests/test_video_pipeline_smoke.py`

**Step 1: Add failing tests for provider health states**

Cover these cases:

- missing API key returns `missing_api_key`;
- endpoint timeout returns `provider_unreachable`;
- TLS/transport failure returns `provider_transport_error`;
- valid text ping but image JSON failure returns `single_image_failed`;
- valid image JSON but multi-image failure returns `multi_image_failed`;
- reports never include raw key values.

Run:

```powershell
python -m pytest tests/test_video_pipeline_smoke.py -q
```

Expected before implementation: tests fail because health states are too coarse.

**Step 2: Add normalized provider smoke result**

Create a small result schema used by both CLI and MCP:

```json
{
  "provider": "agnes",
  "model": "agnes-1.5-flash",
  "status": "provider_transport_error",
  "text_ping": false,
  "single_image_json": false,
  "multi_image_json": false,
  "safe_to_execute": false,
  "error_class": "ssl_eof",
  "error_summary": "transport failed before a valid model response",
  "secrets_redacted": true
}
```

**Step 3: Block real execution when provider is not safe**

`run_multimodal_frame_analysis --execute` and `run_temporal_visual_analysis --execute` should refuse to run unless:

- provider key is present;
- provider smoke status is safe;
- preflight confirmation calls and indexes match exactly.

The refusal should write a report, not mutate `timeline.json`.

**Step 4: Verify on current bundle**

Run:

```powershell
.\scripts\video-knowledge.ps1 vision-env-status
.\scripts\video-knowledge.ps1 vision-execution-preflight %WORKSPACE_ROOT%\video-knowledge-pipeline\real-tests\feishu-video-retry-live-asr\phase2-review-preview-bundle --semantic-limit 5 --no-temporal
```

Expected:

- API key values are not printed.
- If Agnes still fails, the bundle gets an explicit provider blocker rather than a half-run.

## Task 2: Finish Temporal Branch Preconditions

**Files:**

- Modify: `src/video_knowledge_pipeline/temporal_frame_groups.py`
- Modify: `src/video_knowledge_pipeline/vision_preflight.py`
- Modify: `src/video_knowledge_pipeline/bundle_next.py`
- Test: `tests/test_video_pipeline_smoke.py`

**Step 1: Add tests for frame-group completeness**

Assert:

- temporal candidates without `temporal_frame_paths` recommend `run_temporal_frame_groups`;
- candidates with 5-12 ordered frames recommend `run_temporal_visual_analysis`;
- candidates with fewer than 5 frames remain blocked as `temporal_frame_group_incomplete`;
- generated paths are bundle-resolvable and ordered by timestamp.

**Step 2: Make preflight list missing and ready temporal groups separately**

The preflight report should include:

| Field | Meaning |
|---|---|
| `temporal_ready_indexes` | can be sent to model now |
| `temporal_missing_groups` | need frame group generation first |
| `temporal_incomplete_groups` | have too few frames |
| `temporal_already_analyzed` | skipped unless overwrite is explicit |

**Step 3: Verify current preview bundle**

Run:

```powershell
.\scripts\video-knowledge.ps1 vision-execution-preflight %WORKSPACE_ROOT%\video-knowledge-pipeline\real-tests\feishu-video-retry-live-asr\phase2-review-preview-bundle --no-semantic --temporal-limit 5 --frame-count 8
```

Expected:

- indexes `21,26,31,32` are either ready for model analysis or already analyzed;
- no temporal candidate is hidden without a reason.

## Task 3: Add `acceptance-check`

**Files:**

- Modify: `src/video_knowledge_pipeline/cli.py`
- Modify: `src/video_knowledge_pipeline/mcp_server.py`
- Modify: `src/video_knowledge_pipeline/bundle_readiness.py`
- Modify: `src/video_knowledge_pipeline/knowledge_coverage.py`
- Modify: `src/video_knowledge_pipeline/webui_bridge.py`
- Test: `tests/test_video_pipeline_smoke.py`

**New CLI:**

```powershell
.\scripts\video-knowledge.ps1 acceptance-check <webui-bundle>
```

**New MCP tool:**

```text
acceptance_check(bundle_dir)
```

**Checklist output:**

| Check | Required result |
|---|---|
| ASR | complete or human-accepted gap |
| frames | complete or recapture-needed gap |
| route | complete |
| document visual | no synthetic OCR false positives |
| semantic visual | analyzed, provider-blocked, or human-reviewed |
| temporal visual | analyzed, provider-blocked, or human-reviewed |
| review notes | imported if used for acceptance |
| export freshness | export generated after latest timeline/review update |
| provider health | safe, blocked, or not required |
| secret scan | no known key patterns in reports/docs |
| restore chain | available for any model write |

**Result states:**

| State | Meaning |
|---|---|
| `complete` | no known machine or review blockers |
| `accepted_with_known_gaps` | remaining gaps explicitly human-reviewed |
| `provider_blocked` | machine branch is ready but provider is not usable |
| `human_review_required` | missing information needs human decision |
| `machine_action_available` | safe next command exists |
| `incomplete` | setup or evidence chain is missing |

**Verify:**

```powershell
python -m pytest -q
.\scripts\video-knowledge.ps1 acceptance-check %WORKSPACE_ROOT%\video-knowledge-pipeline\real-tests\feishu-video-retry-live-asr\phase2-review-preview-bundle
```

Expected current result:

- not `complete`;
- likely `provider_blocked` or `machine_action_available`, depending on provider smoke result;
- semantic missing count remains visible.

## Task 4: Improve Human Review as a Real Acceptance Path

**Files:**

- Modify: `src/video_knowledge_pipeline/review_session.py`
- Modify: `src/video_knowledge_pipeline/knowledge_coverage.py`
- Modify: `src/video_knowledge_pipeline/knowledge_note_export.py`
- Modify: `src/video_knowledge_pipeline/webui_bridge.py`
- Test: `tests/test_video_pipeline_smoke.py`

**Step 1: Normalize review statuses**

Support these review states without deleting machine output:

- `accepted`
- `keep_image`
- `accepted_no_visual_content`
- `accepted_provider_blocked`
- `corrected_visual_text`
- `corrected_visual_understanding`
- `corrected_temporal_visual_understanding`
- `needs_recapture`
- `needs_model_retry`

**Step 2: Add tests for acceptance effects**

Assert:

- `keep_image` clears OCR-empty blockers but appears in export;
- corrected visual understanding counts toward semantic coverage;
- corrected temporal understanding counts toward temporal coverage;
- `accepted_provider_blocked` counts only when provider health is blocked and evidence frames are present;
- no review state overwrites original ASR/OCR/model fields.

**Step 3: Make review session generate fillable JSON templates**

`prepare-review-session` should generate:

- `review-session.md`
- `review-session.json`
- `review-notes.template.json`

The template should include timeline index, suggested status, evidence frame paths, and empty correction fields.

## Task 5: Rewrite Markdown Export into Layered Lecture Notes

**Files:**

- Modify: `src/video_knowledge_pipeline/knowledge_note_export.py`
- Test: `tests/test_video_pipeline_smoke.py`
- Generated: `exports/knowledge-note.md`
- Generated: `exports/full-transcript.md`

**Required `knowledge-note.md` sections:**

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

**Chapter table format:**

| Column | Content |
|---|---|
| 时间段 | start/end time |
| 讲了什么 | transcript or corrected transcript |
| 画面显示 | visual text, structured visual, or visual understanding |
| 演示变化 | temporal visual understanding |
| 必须保留的图片 | keep-image evidence |
| 缺口 | unresolved quality issues |
| 证据 | frame paths and timeline indexes |

**Implementation rule:**

- Do not invent missing visual details.
- If a section lacks model/human understanding, say `未完成视觉理解` and list the exact indexes.
- Keep `full-transcript.md` chronological and complete.

**Verify:**

```powershell
.\scripts\video-knowledge.ps1 export-knowledge-note %WORKSPACE_ROOT%\video-knowledge-pipeline\real-tests\feishu-video-retry-live-asr\phase2-review-preview-bundle --title "feishu-video-retry"
```

Expected:

- A human can read `knowledge-note.md` as a lecture note.
- Claims have evidence paths or explicit gap markers.

## Task 6: Provider Alternative Trial Without Reworking the Pipeline

**Files:**

- Modify only if needed:
  - `src/video_knowledge_pipeline/vision_api.py`
  - `src/video_knowledge_pipeline/vision_preflight.py`
  - `docs/architecture.md`

**Purpose:**

Agnes is configured but currently not usable from this environment. Do not redesign the pipeline around it. Add a small provider profile trial path for existing profiles:

- `gemini`
- `openai`
- `custom_openai_compatible`
- `agnes`

**Command pattern:**

```powershell
.\scripts\video-knowledge.ps1 vision-env-status --provider gemini
.\scripts\video-knowledge.ps1 vision-provider-smoke --provider gemini --single-image <frame-path> --multi-image-dir <frame-group-dir>
```

If the wrapper does not yet expose `vision-provider-smoke`, add it as a thin alias over the provider smoke function.

**Acceptance:**

- At least one provider either passes text + single-image + multi-image JSON smoke, or all providers are explicitly marked unavailable with reasons.
- No secret value is written to report output.

## Task 7: Real Bundle Final Pass

**Files:**

- Generated bundle artifacts under:
  - `real-tests/feishu-video-retry-live-asr/phase2-review-preview-bundle`
- Docs:
  - `docs/plans/2026-06-11-phase-5-real-provider-and-note-quality-plan.md`
  - `docs/architecture.md`

**Run sequence:**

```powershell
python -m pytest -q
.\scripts\video-knowledge.ps1 acceptance-check %WORKSPACE_ROOT%\video-knowledge-pipeline\real-tests\feishu-video-retry-live-asr\phase2-review-preview-bundle
.\scripts\video-knowledge.ps1 bundle-status-report %WORKSPACE_ROOT%\video-knowledge-pipeline\real-tests\feishu-video-retry-live-asr\phase2-review-preview-bundle
.\scripts\video-knowledge.ps1 audit-knowledge-coverage %WORKSPACE_ROOT%\video-knowledge-pipeline\real-tests\feishu-video-retry-live-asr\phase2-review-preview-bundle
.\scripts\video-knowledge.ps1 export-knowledge-note %WORKSPACE_ROOT%\video-knowledge-pipeline\real-tests\feishu-video-retry-live-asr\phase2-review-preview-bundle --title "feishu-video-retry"
```

**Expected result:**

- Tests pass.
- Status is truthful.
- If provider still fails, final state is `provider_blocked`, not fake completion.
- If human review resolves remaining gaps, final state can become `accepted_with_known_gaps`.
- Markdown output is readable enough to inspect without opening raw JSON.

## Suggested Commit Slices

1. `feat: add vision provider health gate`
2. `feat: tighten temporal frame group readiness`
3. `feat: add bundle acceptance check`
4. `feat: route human review into final acceptance`
5. `feat: improve lecture note markdown export`
6. `docs: document phase five acceptance workflow`

## Stop Conditions

Pause and reassess if:

- Agnes or another provider cannot complete even text ping from this machine after proxy/TLS checks.
- A provider returns non-JSON or unstable JSON for more than 2 consecutive smoke attempts.
- Manual review becomes the dominant path for semantic frames; then build a dedicated review UI before adding more JSON schema fields.
- `knowledge-note.md` starts hiding gaps in prose; acceptance must remain evidence-first.

