# Phase 9 Productization And Output Quality Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Turn the current accepted-with-known-gaps real-video pipeline into a repeatable personal tool that produces cleaner hierarchical Markdown, supports efficient human review, and can batch process more videos without losing the evidence chain.

**Architecture:** Keep the existing routing-first pipeline and controlled execution gates. This phase should not replace the current ASR/OCR/vision modules; it should add a higher-quality export layer, review ergonomics, batch orchestration, and provider/tool adapters around the working core. All outputs must keep timeline indexes and evidence frame paths so humans and agents can audit every claim.

**Tech Stack:** Python package under `src/video_knowledge_pipeline`, static `review.html` bundle, PowerShell wrapper `scripts/video-knowledge.ps1`, pytest regression tests, local `ebook_markdown_pipeline`, local SenseVoice/FunASR, OpenAI-compatible/Gemini/Agnes vision providers, ffmpeg frame extraction.

---

## Current Baseline

Reference bundle:

- `%WORKSPACE_ROOT%\video-knowledge-pipeline\real-tests\feishu-video-retry-live-asr\phase2-review-preview-bundle`

Verified at `2026-06-11 19:06:42`:

| Item | Current State |
| --- | --- |
| Acceptance | `accepted_with_known_gaps` |
| Speech transcript | `68 / 68` |
| Visual routes | `68 / 68` |
| Single-frame visual understanding | `63` items, semantic gap `0` |
| Temporal visual understanding | `14` items, temporal gap `0` |
| Structured document visual | `9 / 9` through accepted human/keep-image fallback |
| Screen text | weak, `9 / 68`, blocker `0` |
| Main human output | `exports/knowledge-note.md`, `exports/full-transcript.md`, `exports/extraction-audit.md` |

Interpretation:

- The original “can this tool actually look at a video and produce a knowledge package?” question is mostly answered for one real video.
- The next bottleneck is not another raw extractor. It is quality and usability:
  - the knowledge note is too verbose and visually noisy;
  - model output is copied too literally into Markdown;
  - evidence paths are present but not organized enough for reading;
  - review is still JSON/template driven, not comfortable enough for repeated use;
  - batch processing lacks a durable run index, resume policy, and cross-video quality dashboard;
  - OCR/text extraction remains weak for screenshots with small UI text.

## Non-Goals

- Do not redesign the whole pipeline.
- Do not make Peepshow, MinerU, Marker, or any OCR tool the main video-understanding engine.
- Do not upload audio by default.
- Do not store provider API keys in config, docs, manifests, reports, or test fixtures.
- Do not overwrite ASR, OCR, model output, or human corrections destructively.

## Task 1: Add A Polished Knowledge Note Renderer

**Files:**

- Modify: `src/video_knowledge_pipeline/knowledge_note_export.py`
- Modify: `src/video_knowledge_pipeline/lecture_outline.py`
- Create: `src/video_knowledge_pipeline/knowledge_note_renderer.py`
- Test: `tests/test_video_pipeline_smoke.py`
- Verify: `real-tests/feishu-video-retry-live-asr/phase2-review-preview-bundle/exports/knowledge-note.md`

**Step 1: Write tests for the target Markdown contract**

Add tests asserting that the exported note contains these top-level sections in this order:

```markdown
# <title>
## 视频概要
## 核心知识结构
## 分段讲解
## 关键演示与屏幕证据
## 表格、代码、公式、图片保留清单
## 逐字稿
## 质量审计与待复核
```

Expected behavior:

- `## 视频概要` is concise, not a pasted transcript excerpt.
- `## 分段讲解` groups adjacent timeline items into readable chapters.
- Each chapter has:
  - `### <time range> <chapter title>`
  - `#### 讲了什么`
  - `#### 演示了什么`
  - `#### 必须保留的证据`
  - `#### 待复核`
- `## 逐字稿` links to `full-transcript.md` and includes a compact chronological transcript index.

Run:

```powershell
python -m pytest tests/test_video_pipeline_smoke.py -q
```

Expected: new tests fail before implementation.

**Step 2: Create `knowledge_note_renderer.py`**

Move presentation-only Markdown logic out of `knowledge_note_export.py`.

The renderer should accept an already fused timeline and export summary:

```python
def render_polished_knowledge_note(
    *,
    title: str,
    timeline: list[dict],
    coverage: dict,
    source_summary: dict,
    full_transcript_relpath: str,
) -> str:
    ...
```

Rules:

- Prefer short synthesized bullets over raw nested JSON dumps.
- Convert visual understanding objects into human phrasing.
- Deduplicate repeated frame paths in each chapter.
- Keep timeline indexes in every claim row.
- If a field is uncertain or human-reviewed, label it explicitly.
- Never invent a chapter title without evidence; use transcript keywords and route changes.

**Step 3: Keep the current detailed audit separate**

Do not remove `exports/extraction-audit.md`.

Move verbose per-item evidence, raw model fields, quality issues, and path-heavy tables there. `knowledge-note.md` should be the human reading document; `extraction-audit.md` should be the inspection document.

**Step 4: Real bundle check**

Run:

```powershell
.\scripts\video-knowledge.ps1 export-knowledge-note `
  %WORKSPACE_ROOT%\video-knowledge-pipeline\real-tests\feishu-video-retry-live-asr\phase2-review-preview-bundle `
  --title "feishu-video-retry downloaded video ASR"
```

Inspect:

- `exports/knowledge-note.md`
- `exports/full-transcript.md`
- `exports/extraction-audit.md`

Expected:

- The first 120 lines are readable as a lecture note.
- Raw dictionaries like `{'id': ...}` no longer dominate the main note.
- Evidence frame paths remain available in the evidence/audit sections.

**Step 5: Commit**

```powershell
git add src/video_knowledge_pipeline/knowledge_note_export.py src/video_knowledge_pipeline/lecture_outline.py src/video_knowledge_pipeline/knowledge_note_renderer.py tests/test_video_pipeline_smoke.py
git commit -m "feat: render polished video knowledge notes"
```

## Task 2: Add A Review UI Editing Loop

**Files:**

- Modify: `src/video_knowledge_pipeline/webui_bridge.py`
- Modify: `src/video_knowledge_pipeline/lecture_package.py`
- Modify: `src/video_knowledge_pipeline/review_session.py`
- Test: `tests/test_video_pipeline_smoke.py`

**Step 1: Add tests for review UI metadata**

Assert generated `review.html` includes:

- paths to `review-notes.template.json`, `review-notes.json`, `review-fill-guide.md`, and `mcp-apply-review-notes.args.json`;
- per-timeline review status;
- visual route and quality issues;
- evidence frame thumbnails;
- suggested correction fields for visual text, single-frame understanding, and temporal understanding.

**Step 2: Add a lightweight editable review panel**

For this phase, avoid a full backend server. Keep the UI static but make it useful:

- Add a filter bar:
  - all;
  - needs human review;
  - missing visual text;
  - low confidence;
  - keep image;
  - corrected.
- Add per-item copy buttons for JSON snippets.
- Add a textarea showing a valid `review-notes.json` draft for selected items.
- Add clear instructions for applying via MCP/CLI, but keep commands sourced from existing manifest paths.

**Step 3: Preserve static-file compatibility**

The UI must still work as:

```text
file:///%WORKSPACE_ROOT%/video-knowledge-pipeline/.../review.html
```

No local web server should be required.

**Step 4: Verify on the real bundle**

Run:

```powershell
.\scripts\video-knowledge.ps1 refresh-review-html `
  %WORKSPACE_ROOT%\video-knowledge-pipeline\real-tests\feishu-video-retry-live-asr\phase2-review-preview-bundle
```

Then open:

```text
%WORKSPACE_ROOT%\video-knowledge-pipeline\real-tests\feishu-video-retry-live-asr\phase2-review-preview-bundle\review.html
```

Expected:

- A human can identify remaining weak screen-text items without opening JSON.
- The UI makes it obvious which screenshots should be kept as images.
- The UI does not imply that human review has already happened when only model output exists.

**Step 5: Commit**

```powershell
git add src/video_knowledge_pipeline/webui_bridge.py src/video_knowledge_pipeline/lecture_package.py src/video_knowledge_pipeline/review_session.py tests/test_video_pipeline_smoke.py
git commit -m "feat: improve static review editing loop"
```

## Task 3: Improve Screen Text And UI Text Recovery

**Files:**

- Modify: `src/video_knowledge_pipeline/visual_structure.py`
- Modify: `src/video_knowledge_pipeline/ocr_backfill.py`
- Modify: `src/video_knowledge_pipeline/knowledge_coverage.py`
- Test: `tests/test_video_pipeline_smoke.py`

**Step 1: Add tests for OCR routing decisions**

Cover these cases:

- `document_visual` still prefers `ebook_markdown_pipeline`.
- `mixed` frames can use both `ebook_markdown_pipeline` and multimodal visual understanding.
- Small UI text frames are marked as `screen_text_low_confidence`, not silently accepted.
- Wrapper-only OCR output is still rejected.

**Step 2: Add a screen-text enhancement plan**

Create a report section that recommends one of:

- `ebook_markdown_pipeline` for page-like frames;
- crop-and-OCR for small UI regions;
- multimodal text description when OCR is unreadable but semantic context is useful;
- human review / keep image when text is too small or visually important.

Do not execute new OCR by default.

**Step 3: Add optional crop candidates**

For UI-heavy screenshots, generate crop candidate metadata:

- full frame;
- central content area;
- browser/editor body;
- subtitle band excluded;
- instructor picture-in-picture excluded.

The first version can write crop plans only. Actual crop OCR can be a later execution flag.

**Step 4: Verify on the real bundle**

Run:

```powershell
.\scripts\video-knowledge.ps1 run-ocr-backfill `
  %WORKSPACE_ROOT%\video-knowledge-pipeline\real-tests\feishu-video-retry-live-asr\phase2-review-preview-bundle
```

Expected:

- No fake OCR coverage.
- Report explains why `screen_text` remains weak and which frames are worth human/OCR recovery.

**Step 5: Commit**

```powershell
git add src/video_knowledge_pipeline/visual_structure.py src/video_knowledge_pipeline/ocr_backfill.py src/video_knowledge_pipeline/knowledge_coverage.py tests/test_video_pipeline_smoke.py
git commit -m "feat: plan screen text recovery without fake coverage"
```

## Task 4: Add Batch Run Index And Resume Policy

**Files:**

- Create: `src/video_knowledge_pipeline/batch_run.py`
- Modify: `src/video_knowledge_pipeline/cli.py`
- Modify: `src/video_knowledge_pipeline/mcp_server.py`
- Modify: `scripts/video-knowledge.ps1`
- Test: `tests/test_video_pipeline_smoke.py`

**Step 1: Add tests for a batch manifest**

Use a manifest like:

```json
{
  "schema": "video_knowledge_batch.v1",
  "workspace": "D:/video-knowledge-runs/batch-001",
  "items": [
    {
      "id": "lesson-001",
      "media_path": "D:/videos/lesson-001.mp4",
      "title": "Lesson 001"
    }
  ]
}
```

Tests should assert:

- existing completed bundles are skipped by default;
- `--resume` continues from the current `bundle-next-action`;
- `--force-reexport` only refreshes exports and reports;
- per-item status is written to `batch-run.json` and `batch-run.md`.

**Step 2: Implement preview-safe batch orchestration**

Add CLI:

```powershell
.\scripts\video-knowledge.ps1 batch-run D:\path\to\batch-manifest.json --resume
```

Default behavior:

- create or reuse each item workspace;
- call `acceptance-run` or `acceptance-bundle-run` preview-safe;
- never call cloud vision or ebook HTTP unless explicit execution flags are passed;
- write a stable batch index.

**Step 3: Add MCP tool**

Add:

```text
batch_video_knowledge_run_tool
```

It should return:

- batch id;
- item statuses;
- next safe action per item;
- paths to reports and bundles.

**Step 4: Real dry-run**

Create a small local manifest for:

- `%WORKSPACE_ROOT%\video-download-orchestrator\downloads\feishu-video-retry\download.mp4`

Run:

```powershell
.\scripts\video-knowledge.ps1 batch-run %WORKSPACE_ROOT%\video-knowledge-pipeline\real-tests\batch-manifest.example.json --resume
```

Expected:

- no duplicate heavy work if the current bundle already exists;
- batch report points to the existing accepted-with-known-gaps bundle.

**Step 5: Commit**

```powershell
git add src/video_knowledge_pipeline/batch_run.py src/video_knowledge_pipeline/cli.py src/video_knowledge_pipeline/mcp_server.py scripts/video-knowledge.ps1 tests/test_video_pipeline_smoke.py
git commit -m "feat: add video knowledge batch runs"
```

## Task 5: Make Provider Selection More Automatic But Still Safe

**Files:**

- Modify: `src/video_knowledge_pipeline/vision_provider_smoke.py`
- Modify: `src/video_knowledge_pipeline/vision_preflight.py`
- Modify: `src/video_knowledge_pipeline/vision_environment.py`
- Test: `tests/test_video_pipeline_smoke.py`

**Step 1: Add tests for provider ranking**

Given provider matrix output, rank providers by:

1. key configured;
2. text ping OK;
3. single-image JSON OK;
4. multi-image JSON OK;
5. lower timeout/failure rate;
6. explicit user preference.

Expected:

- missing-key providers are not selected;
- text-only providers are not selected for vision;
- Agnes can be selected only when image probe checks pass;
- selected provider is never written with its API key.

**Step 2: Add `recommended_provider_config`**

In matrix/smoke reports, add a sanitized config:

```json
{
  "provider": "agnes",
  "model": "agnes-1.5-flash",
  "image_probe_max_edge": 512,
  "image_probe_jpeg_quality": 55
}
```

No secrets.

**Step 3: Wire into preflight**

If no provider config is passed and a fresh provider matrix recommends a provider, preflight may use the sanitized provider/model/probe settings, but still requires:

- key in environment;
- exact confirmation values before execution.

**Step 4: Verify**

Run:

```powershell
.\scripts\video-knowledge.ps1 vision-provider-matrix `
  --providers "agnes,gemini,openai" `
  --bundle-dir %WORKSPACE_ROOT%\video-knowledge-pipeline\real-tests\feishu-video-retry-live-asr\phase2-review-preview-bundle `
  --image-probe-max-edge 512 `
  --image-probe-jpeg-quality 55
```

Expected:

- report recommends only a provider that passes image tests;
- reports and MCP args contain no API keys.

**Step 5: Commit**

```powershell
git add src/video_knowledge_pipeline/vision_provider_smoke.py src/video_knowledge_pipeline/vision_preflight.py src/video_knowledge_pipeline/vision_environment.py tests/test_video_pipeline_smoke.py
git commit -m "feat: recommend safe vision provider profiles"
```

## Task 6: Add Local ASR Install/Readiness UX

**Files:**

- Modify: `src/video_knowledge_pipeline/asr_environment.py`
- Modify: `src/video_knowledge_pipeline/asr_execution.py`
- Modify: `scripts/install-local-asr-env.ps1`
- Modify: `README.md`
- Test: `tests/test_video_pipeline_smoke.py`

**Step 1: Add readiness tests**

Assert `asr-env-status` distinguishes:

- Python package missing;
- model cache missing;
- ffmpeg missing;
- CPU-only ready;
- CUDA ready;
- model download disabled.

**Step 2: Add actionable install report**

`asr-env-status` should return a human-readable next step:

- install command;
- model download command;
- cache path;
- expected disk usage if known;
- local-only privacy statement.

**Step 3: Add a local ASR smoke command**

Add CLI:

```powershell
.\scripts\video-knowledge.ps1 asr-smoke D:\path\to\short-audio-or-video.mp4
```

It should run a short segment only, write a report, and never upload audio.

**Step 4: Commit**

```powershell
git add src/video_knowledge_pipeline/asr_environment.py src/video_knowledge_pipeline/asr_execution.py scripts/install-local-asr-env.ps1 README.md tests/test_video_pipeline_smoke.py
git commit -m "feat: improve local ASR readiness UX"
```

## Task 7: Final Product Acceptance

**Files:**

- Modify only if failures reveal gaps:
  - `src/video_knowledge_pipeline/acceptance_check.py`
  - `src/video_knowledge_pipeline/bundle_status.py`
  - `src/video_knowledge_pipeline/knowledge_note_export.py`
  - `src/video_knowledge_pipeline/webui_bridge.py`
  - `AGENT_DISCOVERY.md`
  - `README.md`

**Step 1: Run full tests**

```powershell
python -m pytest -q
```

Expected: all tests pass.

**Step 2: Run acceptance on the real bundle**

```powershell
.\scripts\video-knowledge.ps1 acceptance-check `
  %WORKSPACE_ROOT%\video-knowledge-pipeline\real-tests\feishu-video-retry-live-asr\phase2-review-preview-bundle
```

Expected:

- `accepted_with_known_gaps` or better;
- semantic gap `0`;
- temporal gap `0`;
- screen-text weak channel is explicitly explained, not hidden.

**Step 3: Run MCP audit**

```powershell
.\scripts\video-knowledge.ps1 mcp-audit-bundle `
  %WORKSPACE_ROOT%\video-knowledge-pipeline\real-tests\feishu-video-retry-live-asr\phase2-review-preview-bundle
```

Expected:

- all generated MCP args parse;
- unsupported fields are explicitly reported;
- no API key appears.

**Step 4: Run secret scan**

```powershell
rg -n -e "sk-" -e "Authorization: Bearer" -e "AGNES_API_KEY=" -e "GEMINI_API_KEY=" -e "OPENAI_API_KEY=" %WORKSPACE_ROOT%\video-knowledge-pipeline
```

Expected:

- only placeholders, docs, or tests with fake values;
- no real key.

**Step 5: Human acceptance checklist**

Open the real exported note and review UI:

- `real-tests\feishu-video-retry-live-asr\phase2-review-preview-bundle\exports\knowledge-note.md`
- `real-tests\feishu-video-retry-live-asr\phase2-review-preview-bundle\review.html`

Accept only if:

- a human can understand the video content without reading raw JSON;
- all visual claims point to evidence;
- unresolved screen-text weakness is visible;
- review actions are obvious;
- agent-callable CLI/MCP paths are present.

**Step 6: Commit**

```powershell
git add AGENT_DISCOVERY.md README.md src/video_knowledge_pipeline tests docs/plans/2026-06-11-phase-9-productization-and-output-quality-plan.md
git commit -m "test: verify productized video knowledge workflow"
```

## Recommended Execution Order

1. Task 1: polished note renderer.
2. Task 2: static review UI editing loop.
3. Task 3: screen-text recovery planning.
4. Task 5: safer automatic provider recommendation.
5. Task 4: batch run index and resume policy.
6. Task 6: local ASR readiness UX.
7. Task 7: full acceptance.

Reasoning:

- The user-facing pain is currently output readability, so fix Markdown first.
- Review UI should follow because human correction is part of the real workflow.
- OCR/screen-text should be made honest and actionable before batch scaling.
- Provider selection and batch orchestration are easier to trust once the single-video output is clean.

## Acceptance Criteria

This phase is complete when:

- `knowledge-note.md` reads like a structured lecture note, not a raw model dump.
- `extraction-audit.md` still contains enough raw detail for verification.
- `review.html` supports practical human review without editing raw JSON from scratch.
- Batch preview/resume can process at least one existing local video bundle without duplicating heavy work.
- Provider selection reports a safe recommended profile without leaking secrets.
- Local ASR readiness tells the user exactly what is missing and how to fix it.
- `python -m pytest -q` passes.
- Real bundle acceptance remains `accepted_with_known_gaps` or better.

## Execution Log

### 2026-06-13 09:36 | Codex (GPT-5)

Completed Task 1 polished knowledge-note renderer:

- Added `src/video_knowledge_pipeline/knowledge_note_renderer.py`.
- `export_knowledge_note` now uses the polished renderer for `exports/knowledge-note.md`.
- Kept detailed raw fields, per-item audit tables, and extraction checks in `exports/extraction-audit.md`.
- The main note now uses these reading sections:
  - `视频概要`;
  - `核心知识结构`;
  - `分段讲解`;
  - `关键演示与屏幕证据`;
  - `表格、代码、公式、图片保留清单`;
  - `逐字稿`;
  - `质量审计与待复核`.
- Preserved human-review signals in the main note:
  - `人工审核`;
  - `人工保留图片`;
  - `修正转写`;
  - `修正视觉理解`;
  - `修正连续片段理解`.
- Added literal parsing for model fields that were stored as Python/JSON-like strings, so raw `{'key': ...}` dict dumps no longer dominate the main note.
- Refreshed the real bundle export:
  - `real-tests/feishu-video-retry-live-asr/phase2-review-preview-bundle/exports/knowledge-note.md`;
  - `full-transcript.md`;
  - `extraction-audit.md`;
  - `export-summary.json`.
- Real note size changed from roughly `560018` characters to `209160` characters while preserving evidence links and audit detail in separate files.
- Verified raw dict-pattern scan on the refreshed main note:
  - `rg -n -e "\{'" -e "\[\{'" -e "schema':" -e "evidence_frame_paths':" ...\exports\knowledge-note.md`;
  - no matches.
- Test verification:
  - targeted export/review tests: `3 passed`;
  - `python -m pytest tests\test_video_pipeline_smoke.py -q`: `104 passed`;
  - `python -m pytest -q`: `104 passed in 8.46s`.

### 2026-06-13 09:56 | Codex (GPT-5)

Completed Task 2 static review UI editing loop:

- Enhanced `review.html` with a static review editing workbench:
  - artifact path cards for `review-notes.template.json`, `review-notes.json`, `review-fill-guide.md`, and `mcp-apply-review-notes.args.json`;
  - filter buttons for all items, human review, missing visual text, low confidence, keep image, and corrected items;
  - per-item quality issue display, review status, visual route data attributes, evidence-frame paths, and copied frame thumbnails;
  - per-item correction fields for `corrected_visual_text`, `corrected_visual_understanding`, and `corrected_temporal_visual_understanding`;
  - per-item JSON snippet copy and a selected-items `lecture_review_notes.v1` draft textarea;
  - `downloadReview()` now writes `review-notes.json` shape instead of the older `lecture-review-notes.json` export shape.
- Updated bundle generation so new WebUI bundles create:
  - `review-notes.template.json`;
  - empty `review-notes.json` only when it does not already exist;
  - `review-fill-guide.md`;
  - `mcp-apply-review-notes.args.json`.
- Updated `refresh-review-html` so existing bundles also get missing review entrypoint files without rebuilding heavy artifacts or overwriting an existing `review-notes.json`.
- Avoided a circular import by keeping the lightweight review-template and fill-guide generation local to `webui_bridge.py`; `review_session.py` still owns full prepare/validate/apply behavior.
- Refreshed the real bundle:
  - `real-tests/feishu-video-retry-live-asr/phase2-review-preview-bundle/review.html`;
  - `review-notes.template.json`;
  - `review-notes.json`;
  - `review-fill-guide.md`;
  - `mcp-apply-review-notes.args.json`.
- Real bundle validation:
  - `refresh-review-html` reported `timeline_items: 68`;
  - `validate-review-notes` on the empty `review-notes.json` returned `status: ok`;
  - static HTML scan confirmed `review-json-draft`, `missing-visual-text`, `corrected_visual_understanding`, and `copyReviewSnippet`.
- Browser verification note:
  - The Codex in-app Browser plugin refused direct `file://` navigation by policy, so no browser screenshot was captured;
  - verification used static file inspection plus CLI validation instead.
- Test verification:
  - `python -m pytest tests\test_video_pipeline_smoke.py -q`: `104 passed`;
  - `python -m pytest -q`: `104 passed in 14.81s`.

### 2026-06-13 10:11 | Codex (GPT-5)

Completed Task 3 screen-text and UI-text recovery planning:

- Kept the primary OCR/text route aligned with the tool-first plan:
  - `document_visual` screenshots prefer `ebook_markdown_pipeline`;
  - `mixed` screenshots keep both `ebook_markdown_pipeline` and multimodal understanding in the route decision;
  - OCR backfill remains a fallback/repair path, not the main document screenshot parser.
- Added explicit visual-structure routing metadata:
  - `routing_decision.primary_branch`;
  - `routing_decision.primary_tool`;
  - `routing_decision.also_requires_multimodal`;
  - routing reason in `visual-structure-report.md`.
- Added `screen_text_recovery` planning to `run_ocr_backfill`:
  - strategies: `ebook_pipeline`, `ebook_pipeline_plus_multimodal`, `crop_and_ocr`, `multimodal_text_description`, `human_review_keep_image`;
  - per-item `recommended_tool`, reason, and crop candidates;
  - crop candidates are plan-only relative boxes: full frame, central content, subtitle band excluded, browser/editor body, instructor picture-in-picture excluded.
- Made OCR preview semantics more honest:
  - preview rows now keep `ok: false` and `image_exists: true`;
  - `Succeeded: 0` and `Planned: N` stay explicit until OCR/import actually happens.
- Updated coverage audit:
  - wrapper-only OCR output is counted as `ocr_text_empty`;
  - UI/screen-like frames can be counted as `screen_text_low_confidence`;
  - screen-text channel text now explains that crop OCR is fallback and low-confidence text must be reviewed.
- Refreshed the real bundle:
  - `ocr-backfill-report.md`;
  - `ocr-backfill-handoff.md`;
  - `ocr-backfill-handoff.json`;
  - `ocr-backfill-input-template.json`;
  - `knowledge-coverage.md`;
  - `knowledge-coverage.json`.
- Real bundle result:
  - OCR preview total: `68`;
  - execute: `false`;
  - succeeded: `0`;
  - planned: `68`;
  - screen-text recovery strategy counts:
    - `ebook_pipeline`: `2`;
    - `ebook_pipeline_plus_multimodal`: `7`;
    - `multimodal_text_description`: `59`;
  - coverage status remains `weak`;
  - `screen_text` coverage remains `9 / 68`;
  - `ocr_text_empty`: `9`;
  - `screen_text_low_confidence`: `0` on the current reviewed real bundle;
  - screen-text blocker remains `0` because the empty OCR cases are already handled through accepted human/keep-image review fallback.
- Test verification:
  - targeted tests: `2 passed`;
  - `python -m pytest tests\test_video_pipeline_smoke.py -q`: `106 passed`;
  - `python -m pytest -q`: `106 passed in 10.47s`.

### 2026-06-13 10:27 | Codex (GPT-5)

Completed Task 5 safer automatic provider recommendation:

- Added provider ranking to `vision-provider-matrix`:
  - providers are ranked by configured key, text ping, single-image JSON, multi-image JSON, failure count, timeout, and explicit preference;
  - non-ready providers are never written as `recommended_provider`;
  - text-only or image-failing providers keep an empty `recommended_provider_config`;
  - missing-key providers remain visible in the matrix but cannot be selected.
- Added secret-safe `recommended_provider_config`:
  - includes provider, model, image probe max edge, image probe JPEG quality, optional safe base URL, and timeout;
  - does not include API keys, bearer tokens, or environment variable assignments.
- Wired the preference option through:
  - CLI `vision-provider-matrix --preferred-provider`;
  - both MCP `vision_provider_matrix` tool aliases.
- Updated `vision-execution-preflight`:
  - when no explicit provider config is passed, it reads the latest bundle `vision-provider-matrix.json`;
  - `execution_profile.provider_config_source` records `vision_provider_matrix`, `explicit`, or `default_profile`;
  - preflight keeps probe settings in the human-readable recommendation but only passes runtime-safe provider/model/base_url/timeout fields to the adapter.
- Updated `vision-env-status`:
  - exposes a sanitized provider config summary;
  - recommends running provider matrix before real vision execution when a key is configured.
- Real bundle verification:
  - ran `.\scripts\video-knowledge.ps1 vision-provider-matrix --providers "agnes,gemini,openai" --bundle-dir %WORKSPACE_ROOT%\video-knowledge-pipeline\real-tests\feishu-video-retry-live-asr\phase2-review-preview-bundle --image-probe-max-edge 512 --image-probe-jpeg-quality 55`;
  - status: `ok`;
  - recommended provider: `agnes`;
  - Agnes passed text ping, single-image JSON, and multi-image JSON checks;
  - Gemini and OpenAI were not selected because the current environment did not have their keys configured;
  - report files checked: no `sk-` prefix, no user key prefix, no `API_KEY=` assignment, no `Bearer` token.
- Real preflight verification:
  - `vision-execution-preflight --semantic-limit 1 --temporal-limit 1 --frame-count 8 --no-write`;
  - `provider_config_source`: `vision_provider_matrix`;
  - selected semantic index: `16`;
  - selected temporal index: `18`;
  - `ready_to_execute`: `true`;
  - blockers: none.
- Test verification:
  - targeted provider/preflight/env/CLI dispatch tests: `10 passed`;
  - `python -m pytest`: `110 passed in 13.19s`.

### 2026-06-13 10:34 | Codex (GPT-5)

Completed Task 4 preview-safe batch orchestration:

- Added `batch_run.py` as a thin orchestration layer over existing tools:
  - reads `video_knowledge_batch.v1` manifests;
  - creates or reuses item workspaces;
  - skips already accepted bundles by default;
  - resumes existing bundles through preview-safe `acceptance-bundle-run`;
  - creates new item runs through preview-safe `acceptance-run`;
  - supports `force_reexport` without running acceptance or cloud/model branches.
- Added CLI:
  - `.\scripts\video-knowledge.ps1 batch-run <batch-manifest.json> --resume`;
  - explicit opt-in flags are required for ASR execution, temporal frame generation, vision execution, or ebook pipeline execution.
- Added MCP/tool surface:
  - `batch_video_knowledge_run_tool`;
  - `batch_video_knowledge_run` / `batch_run` in local MCP-callable mapping.
- Added batch reports:
  - `batch-run.json`;
  - `batch-run.md`;
  - per-item status, action, bundle path, next safe action, and report pointers.
- Real dry-run:
  - created `real-tests/batch-manifest.example.json`;
  - ran `.\scripts\video-knowledge.ps1 batch-run %WORKSPACE_ROOT%\video-knowledge-pipeline\real-tests\batch-manifest.example.json --resume`;
  - workspace: `real-tests/batch-run-feishu`;
  - result: total `1`, completed/skipped `1`, needs action `0`, errors `0`;
  - item `feishu-video-retry` was skipped as `accepted_with_known_gaps`;
  - report points to the existing `phase2-review-preview-bundle` artifacts.
- Test verification:
  - targeted batch tests: `4 passed`;
  - `python -m pytest`: `114 passed in 13.36s`.

### 2026-06-13 10:56 | Codex (GPT-5)

Completed Task 6 local ASR readiness UX:

- Enhanced `asr-env-status`:
  - distinguishes Python environment readiness, ASR package availability, ASR command availability, ffmpeg availability, SenseVoice model cache readiness, model download gate, CPU readiness, and CUDA readiness;
  - writes `asr-environment.json`, `asr-environment.md`, `asr-env.ps1`, and `mcp-asr-environment-status.args.json` when `--output-dir --write` is used;
  - includes install command, model download command, cache path, expected disk usage, and local-only privacy statement;
  - next action now points to model cache preparation, ffmpeg install, package install, or `asr-smoke` as appropriate.
- Added local ASR smoke:
  - CLI: `.\scripts\video-knowledge.ps1 asr-smoke <media> --duration-seconds 30`;
  - MCP: `asr_smoke_tool`;
  - default behavior runs a short local clip and local ASR;
  - `--no-execute` previews the clip command/report only;
  - writes `asr-smoke.json` and `asr-smoke.md`;
  - keeps audio local and does not upload audio.
- Updated `scripts/install-local-asr-env.ps1`:
  - added `-AllowModelDownload`;
  - env snippet includes `LECTURE_ASR_ALLOW_MODEL_DOWNLOAD`;
  - output includes local privacy and expected disk usage fields.
- Updated `README.md`:
  - added `asr-env-status --output-dir --write`;
  - added `asr-smoke`;
  - clarified model cache gate, local-only privacy, and `--no-execute`.
- Real machine verification:
  - `asr-env-status --output-dir real-tests/asr-env-check --write`;
  - FunASR/SenseVoice package and command are ready;
  - primary model `iic/SenseVoiceSmall` cache is ready;
  - CPU path is ready;
  - CUDA is not available but not required.
- Real smoke verification:
  - ran `.\scripts\video-knowledge.ps1 asr-smoke %WORKSPACE_ROOT%\video-download-orchestrator\downloads\feishu-video-retry\download.mp4 --output-dir %WORKSPACE_ROOT%\video-knowledge-pipeline\real-tests\asr-smoke-execute --duration-seconds 30 --timeout-seconds 600`;
  - status: `ok`;
  - runner: `funasr_python`;
  - raw output and normalized transcript were written under `real-tests/asr-smoke-execute`;
  - no audio upload path is used.
- Test verification:
  - targeted ASR tests: `6 passed`;
  - `python -m pytest`: `119 passed in 15.09s`.

### 2026-06-13 11:00 | Codex (GPT-5)

Completed Task 7 final product acceptance:

- Full test verification:
  - `python -m pytest -q`: `119 passed in 14.98s`.
- Real bundle acceptance:
  - first run found stale export and returned `machine_action_available`;
  - refreshed `exports/knowledge-note.md`, `full-transcript.md`, `extraction-audit.md`, and `export-summary.json`;
  - reran `acceptance-check`;
  - final status: `accepted_with_known_gaps`;
  - semantic gap: `0`;
  - temporal gap: `0`;
  - export freshness: `fresh`;
  - screen-text channel remains `weak` and explicitly reported, with `ocr_text_empty` sample indexes preserved.
- MCP audit:
  - ran `mcp-audit-bundle` on the real bundle;
  - status: `ok`;
  - total generated MCP arg files: `30`;
  - ok count: `30`;
  - blocked count: `0`.
- Secret scan:
  - scanned for `sk-`, `Authorization: Bearer`, `AGNES_API_KEY=`, `GEMINI_API_KEY=`, and `OPENAI_API_KEY=`;
  - hits were scan commands, placeholders, docs, or tests with fake/redacted values;
  - no real API key was found in generated reports, manifests, docs, or tests.
- Human acceptance artifact check:
  - `knowledge-note.md` contains the required top-level sections in order;
  - first 140 lines read as a structured lecture note rather than raw JSON;
  - raw dict-pattern scan on the main note had no matches;
  - `review.html` contains review filters, evidence paths, correction fields, JSON draft area, review template path, and MCP apply args path.
- Documentation updates:
  - `AGENT_DISCOVERY.md` now documents batch run, local ASR readiness/smoke, provider matrix recommendation, polished export, and review workflow;
  - `README.md` documents `batch-run`, `asr-env-status --write`, `asr-smoke`, local-only ASR privacy, and key MCP tools;
  - `docs/architecture.md` now reflects Phase 9 output/review/batch/provider/ASR layers and current real-bundle status.

## Risks And Controls

- **Risk:** making the Markdown prettier may hide missing evidence.
  - **Control:** every synthesized bullet keeps timeline indexes and evidence references.
- **Risk:** static review UI becomes too ambitious.
  - **Control:** ship copyable JSON snippets first; do not require a backend.
- **Risk:** batch mode accidentally triggers paid API calls.
  - **Control:** default batch mode is preview-safe; all external execution keeps existing preflight and confirmation gates.
- **Risk:** screen text weak channel gets masked as solved.
  - **Control:** weak OCR remains visible unless real text or reviewed keep-image/correction exists.
- **Risk:** provider recommendation stores secrets.
  - **Control:** reports store only provider names, models, endpoint type, and image compression settings.

## Documentation Updates

After implementation, update:

- `AGENT_DISCOVERY.md`: add batch command, polished export behavior, review UI workflow.
- `README.md`: revise the recommended human workflow.
- `docs/architecture.md`: add Phase 9 output/review/batch layer to the architecture diagram.
- Obsidian project documentation if this becomes the new stable local workflow, following `%OBSIDIAN_VAULT%\00 - System\AI Documentation Policy.md`.
