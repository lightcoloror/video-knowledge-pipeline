# Review, Supplement, and Export Stage Plan

> Updated: 2026-06-11 12:44:50 | Codex (GPT-5)

## Goal

把当前真实视频 bundle 从“已经能定位缺口”推进到“人能审核、模型能补充、最终 Markdown 可读”。

本阶段不继续扩大工具清单，不重写 ASR/OCR/多模态主流程。重点是把现有能力闭环：

- OCR 空结果进入人工审核或多模态补充，而不是反复重跑同一个失败工具。
- semantic / temporal 缺口能按安全批次继续补齐。
- 人工审核结果能回填 coverage、readiness、export。
- `knowledge-note.md` 输出成为层级清晰的人类可读知识文档。

## Current Baseline

Reference bundle:

- `%WORKSPACE_ROOT%\video-knowledge-pipeline\real-tests\feishu-video-retry-live-asr\webui-bundle`

Current verified state:

| Channel | State |
|---|---:|
| speech | 68 / 68 |
| visual_frames | 68 / 68 |
| visual_route | 68 / 68 |
| screen_text | 0 / 68, 9 OCR-empty review targets |
| structured_visual | 0 / 9, 9 OCR-empty review targets |
| semantic_frame_understanding | 10 / 61, 51 gaps |
| temporal_visual_understanding | 3 / 12, 9 gaps |

Current next action:

- `bundle-status-report`: `human_review_required`
- next key: `ocr_text_empty_review`
- recommended tool: `prepare_review_session`
- fallback tool: `run_multimodal_frame_analysis`

Important finding:

- MCP bridge already maps `prepare_review_session`.
- CLI currently lacks a direct `prepare-review-session` command, so the human-review entry is not ergonomic enough.

## Implementation Status

### 2026-06-11 12:52:21 | Codex (GPT-5)

Phase 1 progress:

- Added `prepare-review-session` CLI entrypoint.
- Kept MCP bridge compatibility through `prepare_review_session`.
- Promoted `ocr_text_empty` ebook results into explicit review-session targets.
- Added an `OCR Empty Targets` section to `review-session.md`.
- Filtered wrapper-only ebook Markdown out of review evidence excerpts.
- Changed `review-session.json` top-level `coverage` to use the current knowledge coverage audit instead of stale manifest coverage.

Verification:

- `python -m pytest -q` -> `79 passed`.
- Real bundle generated:
  - `real-tests\feishu-video-retry-live-asr\webui-bundle\review-session.md`
  - `real-tests\feishu-video-retry-live-asr\webui-bundle\review-session.json`
- Real bundle check:
  - `screen_text.covered_count = 0`
  - `structured_visual.covered_count = 0`
  - `review_targets.by_reason.ocr_text_empty = 9`

### 2026-06-11 13:05:07 | Codex (GPT-5)

Phase 2 progress:

- `review-notes.json` can now close OCR-empty / structure-gap cases through explicit human review:
  - `status=keep_image` normalizes to accepted review;
  - `keep_image=true` is preserved as `human_keep_image`;
  - `corrected_temporal_visual_understanding` is preserved as `human_corrected_temporal_visual_understanding`.
- Review import remains non-destructive:
  - machine transcript remains untouched;
  - machine visual/model outputs remain untouched;
  - human corrections are stored in parallel human fields.
- Coverage now distinguishes machine output from human fallback:
  - human keep-image or human corrected text removes OCR blockers;
  - human keep-image or corrected visual understanding can satisfy structured visual fallback;
  - human accepted review can satisfy semantic/temporal review coverage without pretending it was model output.
- Export now renders human decisions:
  - artificial OCR-wrapper text is still filtered out;
  - human keep-image decisions are shown as retained image evidence;
  - human temporal corrections are shown in the transcript/demonstration record.

Verification:

- `python -m pytest -q` -> `80 passed`.
- Real-bundle preview was run on:
  - `real-tests\feishu-video-retry-live-asr\phase2-review-preview-bundle`
- Preview results after importing 9 keep-image review notes:
  - `screen_text.blocker_count = 0`;
  - `structured_visual.covered_count = 9`;
  - `structured_visual.blocker_count = 0`;
  - `items_with_visual_understanding = 19`;
  - `items_with_temporal_understanding = 10`;
  - exported `knowledge-note.md` shows `人工保留图片` and `修正连续片段理解`;
  - export summary has `document_visual_missing_structure = []`.

## Non-Goals

- 不把 Peepshow 升级成主知识生成器。
- 不把 `ebook_markdown_pipeline` 当成“看视频”的核心，只保留为图文截图解析分支。
- 不把 OCR 空壳 Markdown 当成有效内容。
- 不在 manifest、docs、reports、tests 中写入 API key。
- 不绕过人工审核直接写回 Obsidian / Logseq。

## Phase 1: Close OCR-Empty Human Review Loop

### Tasks

1. Add direct CLI command:

```powershell
python -m video_knowledge_pipeline.cli prepare-review-session <webui-bundle>
```

2. Keep MCP parity:

```powershell
.\scripts\video-knowledge.ps1 mcp-call prepare_review_session <mcp-prepare-review-session.args.json>
```

3. Improve `prepare_review_session` output for OCR-empty cases:

- add reason: `ocr_text_empty`
- list affected indexes: `16, 17, 18, 24, 25, 48, 66, 67, 68`
- show evidence frame path
- show transcript excerpt
- show route and material types
- explicitly say: “ebook pipeline returned no meaningful text”
- suggest next choices: human mark as accepted / keep image / needs multimodal supplementation

4. Make review excerpts ignore wrapper-only OCR text such as:

```markdown
# 016_0000240000ms
<!-- source: ... -->
```

### Files

- `src/video_knowledge_pipeline/cli.py`
- `src/video_knowledge_pipeline/review_session.py`
- `tests/test_video_pipeline_smoke.py`
- `AGENT_DISCOVERY.md`

### Verification

```powershell
$env:PYTHONPATH='src'
python -m video_knowledge_pipeline.cli prepare-review-session %WORKSPACE_ROOT%\video-knowledge-pipeline\real-tests\feishu-video-retry-live-asr\webui-bundle
python -m pytest -q
```

Expected artifacts:

- `review-session.json`
- `review-session.md`
- `mcp-prepare-review-session.args.json`

Acceptance:

- command exits successfully
- review session includes OCR-empty targets
- report does not contain wrapper-only OCR text as evidence content
- tests pass

## Phase 2: Make Review Notes a Real Coverage Mechanism

### Tasks

1. Finalize `review-notes.json` schema:

```json
{
  "timeline_index": 16,
  "status": "accepted | needs_fix | irrelevant | keep_image | needs_human_review",
  "tags": [],
  "comment": "",
  "corrected_transcript": "",
  "corrected_visual_text": "",
  "corrected_visual_understanding": "",
  "corrected_temporal_visual_understanding": "",
  "reviewed_at": ""
}
```

2. Apply review notes without destructive overwrite:

- preserve machine ASR/OCR/model fields
- store human corrections under review/human fields
- coverage may count a missing machine result as resolved only when the human status is explicit

3. Add review status into export:

- show human-confirmed visual gaps
- show kept screenshots
- show items still needing review

### Files

- `src/video_knowledge_pipeline/review_session.py`
- `src/video_knowledge_pipeline/knowledge_coverage.py`
- `src/video_knowledge_pipeline/bundle_readiness.py`
- `src/video_knowledge_pipeline/knowledge_note_export.py`
- `tests/test_video_pipeline_smoke.py`

### Verification

```powershell
$env:PYTHONPATH='src'
python -m video_knowledge_pipeline.cli apply-review-notes %WORKSPACE_ROOT%\video-knowledge-pipeline\real-tests\feishu-video-retry-live-asr\webui-bundle --review-json <review-notes.json>
python -m video_knowledge_pipeline.cli audit-knowledge-coverage %WORKSPACE_ROOT%\video-knowledge-pipeline\real-tests\feishu-video-retry-live-asr\webui-bundle
python -m pytest -q
```

Acceptance:

- human-reviewed OCR-empty items no longer cause blind OCR rerun
- coverage distinguishes machine-covered, human-reviewed, and still-missing
- review import can be dry-run or written explicitly

## Phase 3: Continue Semantic and Temporal Supplementation

### Tasks

1. Use current vision provider profile from:

- `config/video-knowledge-pipeline.json`

Current default:

```json
{
  "provider": "gemini",
  "model": "gemini-2.5-flash",
  "multimodal_limit": 19,
  "temporal_limit": 3,
  "frame_count": 8
}
```

2. Semantic branch:

- preflight exact next batch
- execute only with confirmation
- preserve evidence frame path
- do not overwrite existing 10 completed semantic items

3. Temporal branch:

- ensure 5-12 ordered frame groups exist
- preflight exact next batch
- execute only with confirmation
- preserve all ordered frame paths

### Commands

```powershell
.\scripts\video-knowledge.ps1 vision-execution-preflight %WORKSPACE_ROOT%\video-knowledge-pipeline\real-tests\feishu-video-retry-live-asr\webui-bundle --semantic-limit 19 --no-temporal

.\scripts\video-knowledge.ps1 run-multimodal-frame-analysis %WORKSPACE_ROOT%\video-knowledge-pipeline\real-tests\feishu-video-retry-live-asr\webui-bundle --execute --limit 19 --confirm-vision-calls <calls> --confirm-vision-indexes "<indexes>"

.\scripts\video-knowledge.ps1 run-temporal-frame-groups %WORKSPACE_ROOT%\video-knowledge-pipeline\real-tests\feishu-video-retry-live-asr\webui-bundle --execute --frame-count 8 --limit 5

.\scripts\video-knowledge.ps1 vision-execution-preflight %WORKSPACE_ROOT%\video-knowledge-pipeline\real-tests\feishu-video-retry-live-asr\webui-bundle --no-semantic --temporal-limit 3 --frame-count 8

.\scripts\video-knowledge.ps1 run-temporal-visual-analysis %WORKSPACE_ROOT%\video-knowledge-pipeline\real-tests\feishu-video-retry-live-asr\webui-bundle --execute --limit 3 --frame-count 8 --confirm-vision-calls <calls> --confirm-vision-indexes "<indexes>"
```

Acceptance:

- semantic coverage moves beyond 10 / 61
- temporal coverage moves beyond 3 / 12
- direct executor logs are recoverable through restore plan
- reports include frame path, transcript excerpt, model status, confidence, and omission risk

## Phase 4: Upgrade Human-Readable Markdown Export

### Required Output Shape

`exports/knowledge-note.md` must contain:

- `# <title>`
- `## 视频概要`
- `## 覆盖情况`
- `## 知识结构`
- `## 图文与视觉信息`
- `## 连续演示与操作变化`
- `## 逐字稿与演示记录`
- `## 未解决缺口`

`exports/full-transcript.md` must remain complete and chronological.

### Tasks

1. Group timeline into chapters by time continuity, transcript density, and route changes.
2. For each chapter, show:

- 说了什么
- 演示了什么
- 屏幕/图表/界面信息
- 保留图片证据
- 仍缺什么

3. Render OCR-empty frames as gaps or human-reviewed evidence, not fake OCR content.
4. Include links/paths to evidence frames and source artifacts.

### Files

- `src/video_knowledge_pipeline/knowledge_note_export.py`
- `src/video_knowledge_pipeline/knowledge_coverage.py`
- `tests/test_video_pipeline_smoke.py`

### Verification

```powershell
.\scripts\video-knowledge.ps1 export-knowledge-note %WORKSPACE_ROOT%\video-knowledge-pipeline\real-tests\feishu-video-retry-live-asr\webui-bundle --title "feishu-video-retry"
```

Acceptance:

- `knowledge-note.md` can be read without opening raw `timeline.json`
- transcript is complete in `full-transcript.md`
- summary does not hide missing visual coverage
- evidence frame paths are preserved

## Phase 5: WebUI Review Surface

### Tasks

1. Add review-session links to `review.html` metadata panel:

- `review-session.md`
- `review-session.json`
- `review-notes.json`
- `mcp-prepare-review-session.args.json`
- `mcp-apply-review-notes.args.json`

2. Add visible state for:

- OCR-empty review needed
- semantic missing
- temporal missing
- human reviewed
- keep image

3. If full editing UI is too large, ship a stable “copy JSON template / import JSON” workflow first.

### Files

- `src/video_knowledge_pipeline/webui_bridge.py`
- `src/video_knowledge_pipeline/review_session.py`
- `tests/test_video_pipeline_smoke.py`

Acceptance:

- a human can open `review.html`, see what needs review, and know which JSON file to edit/import
- no direct writeback to external vault happens without explicit reviewed command

## Execution Order

1. Phase 1: expose and improve `prepare-review-session`.
2. Phase 2: make review notes affect coverage/readiness/export.
3. Phase 3: continue semantic and temporal model supplementation.
4. Phase 4: improve hierarchical Markdown export.
5. Phase 5: improve WebUI review surface.

This order is intentional: the current blocker is no longer “which OCR tool to use”; it is that the system must handle OCR-empty evidence honestly and let either humans or multimodal models close the gap.

## Final Acceptance Check

Run:

```powershell
python -m pytest -q
$env:PYTHONPATH='src'; python -m video_knowledge_pipeline.cli bundle-status-report %WORKSPACE_ROOT%\video-knowledge-pipeline\real-tests\feishu-video-retry-live-asr\webui-bundle
$env:PYTHONPATH='src'; python -m video_knowledge_pipeline.cli audit-knowledge-coverage %WORKSPACE_ROOT%\video-knowledge-pipeline\real-tests\feishu-video-retry-live-asr\webui-bundle
.\scripts\video-knowledge.ps1 export-knowledge-note %WORKSPACE_ROOT%\video-knowledge-pipeline\real-tests\feishu-video-retry-live-asr\webui-bundle --title "feishu-video-retry"
```

Stage is complete when:

- tests pass
- bundle next action is either machine-actionable or explicitly human-reviewable
- OCR-empty items are not counted as fake OCR coverage
- semantic and temporal gaps are smaller or intentionally reviewed
- exported Markdown is useful as a standalone knowledge note
