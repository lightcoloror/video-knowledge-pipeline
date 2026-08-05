# Next Stage Video Knowledge Pipeline Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Turn the current proof-of-pipeline into a usable first version that can process one real knowledge video with ASR, document-frame parsing, multimodal frame understanding, temporal sequence understanding, coverage audit, human review, and hierarchical Markdown export.

**Architecture:** Keep the current routing-first architecture. Reuse `ebook_markdown_pipeline` for document-like screenshots, reuse configured vision providers for semantic and temporal frames, and keep this project responsible for timeline fusion, coverage audit, review UI, MCP/CLI entrypoints, and final Markdown export. Peepshow is integrated only as an optional evidence extractor, not as the main knowledge generator.

**Tech Stack:** Python package under `src/video_knowledge_pipeline`, pytest smoke/regression tests, PowerShell wrapper `scripts/video-knowledge.ps1`, local `ebook_markdown_pipeline`, OpenAI-compatible/Gemini/Agnes vision providers, ffmpeg frame extraction, static WebUI bundle.

---

## Current Baseline

Reference bundle:

- `%WORKSPACE_ROOT%\video-knowledge-pipeline\real-tests\feishu-video-retry-live-asr\webui-bundle`

Current coverage from `knowledge-coverage.json`:

| Channel | Current |
|---|---:|
| speech | 68 / 68 |
| visual_frames | 68 / 68 |
| visual_route | 68 / 68 |
| screen_text | 0 / 68, with 9 blocking samples |
| structured_visual | 0 / 9 |
| semantic_frame_understanding | 1 / 61 |
| temporal_visual_understanding | 1 / 12 |

The next stage is not about adding more candidate tools. It is about closing these four active blockers:

1. `screen_text`
2. `structured_visual`
3. `semantic_frame_understanding`
4. `temporal_visual_understanding`

## Implementation Status

### 2026-06-11 18:40 | Codex (GPT-5)

Progress against real-bundle hardening and visual closure:

- Repaired the real bundle `manifest.json` after concurrent write corruption:
  - corrupt backup: `real-tests/feishu-video-retry-live-asr/phase2-review-preview-bundle/manifest.corrupt-20260611-182653.json`;
  - cause observed: overlapping bundle-writing commands appended a 55-character trailing fragment after the first valid JSON object;
  - verification: manifest parsed successfully after sequential `acceptance-check`, `mcp-audit-bundle`, and `export-knowledge-note`.
- Added bundle write hardening:
  - `storage.write_json` now writes JSON atomically through a same-directory temp file plus `os.replace`;
  - added `bundle_write_lock` with `.bundle-write.lock`;
  - protected the critical write sections in `acceptance_check`, `bundle_status_report`, `controlled_execution_check`, and `export_knowledge_note`;
  - focused regression tests pass:
    - `test_bundle_json_write_is_atomic`;
    - `test_bundle_write_lock_rejects_overlapping_writer`;
    - export / acceptance / bundle-status smoke tests.
- Real Agnes vision execution continued on the reference bundle:
  - semantic run `semantic_frame-20260611-183354`: indexes `9,15,19`, `3/3` ok, `3` timeline updates;
  - semantic run `semantic_frame-20260611-183553`: indexes `20,22,23`, `3/3` ok, `3` timeline updates;
  - temporal run `temporal_sequence-20260611-183647`: indexes `21,26`, `2/2` ok, `2` timeline updates;
  - temporal run `temporal_sequence-20260611-183716`: indexes `31,32`, `2/2` ok, `2` timeline updates;
  - semantic run `semantic_frame-20260611-183907`: indexes `27,28,29,30,33`, `1/5` ok, failed indexes were retry-exhausted Agnes SSL EOF failures.
- Current verified acceptance state after export at `2026-06-11T18:39:58`:
  - `speech`: `ok`;
  - `visual_frames`: `ok`;
  - `visual_route`: `ok`;
  - `structured_visual`: `ok`;
  - `screen_text`: `weak`;
  - `temporal_visual_understanding`: `ok`, `12 / 12`, missing `0`;
  - `semantic_frame_understanding`: `blocked`, `26 / 61`, missing `35`;
  - top-level acceptance status: `machine_action_available`;
  - next machine action: continue `run_multimodal_frame_analysis` for semantic indexes beginning `28,29,30,33,34,35,36,37,38,39`.
- Full-output real provider run logs were saved in the bundle:
  - `semantic-run-20260611-1836-indexes-20-22-23.json`;
  - `temporal-run-20260611-1836-indexes-21-26.json`;
  - `temporal-run-20260611-1837-indexes-31-32.json`;
  - `semantic-run-20260611-1838-indexes-27-28-29-30-33.json`.

Interpretation:

The temporal branch is now closed for the current real bundle. The remaining blocker is not architecture but provider reliability and remaining semantic single-frame coverage. Continue in smaller semantic batches or switch failed items to human review if Agnes SSL EOF repeats.

### 2026-06-11 12:32 | Codex (GPT-5)

Progress against this plan:

- Task 1 ebook bridge is operational enough to call the real `ebook_markdown_pipeline` image path and receive artifacts.
- The previous false-positive OCR coverage has been fixed:
  - wrapper-only Markdown such as `# 016_0000240000ms` plus `<!-- source: ... -->` is no longer imported as real `visual_text` / `structured_visual`;
  - existing wrapper-only timeline values are ignored by `knowledge_coverage` and `knowledge_note_export`;
  - `visual-structure-report.md` now records these real bundle results as `ocr_text_empty`.
- Real bundle verification after the fix:
  - `screen_text`: `0 / 68`, blocker `9`;
  - `structured_visual`: `0 / 9`, blocker `9`;
  - `semantic_frame_understanding`: `10 / 61`;
  - `temporal_visual_understanding`: `3 / 12`;
  - `exports/knowledge-note.md` no longer exposes wrapper-only OCR text as content.
- Test verification:
  - `python -m pytest -q` -> `76 passed`.

Interpretation:

This does not mean the document-visual branch is complete. It means the pipeline is now honest: `ebook_markdown_pipeline` ran on the 9 document/mixed candidates and produced no meaningful OCR text, so those frames remain explicit review/model gaps rather than fake structured coverage.

### 2026-06-11 12:38 | Codex (GPT-5)

Progress against operator-loop completion:

- `bundle-next-action` no longer recommends blindly rerunning `run_visual_structure_plan` when the latest visual-structure run exhausted all document/mixed candidates with `ocr_text_empty`.
- In that state, the next action becomes:
  - `status`: `human_review_required`;
  - `key`: `ocr_text_empty_review`;
  - `mcp_tool`: `prepare_review_session`;
  - fallback tool: `run_multimodal_frame_analysis`.
- Real bundle verification:
  - `bundle-next-action` reports `human_review_required / ocr_text_empty_review`;
  - `bundle-status.md` shows the same next action and MCP args path;
  - `visual-structure-report.md` still preserves the 9 `ocr_text_empty` blockers and evidence frame paths.
- Test verification:
  - `python -m pytest -q` -> `77 passed`.

Interpretation:

This closes the OCR empty-output loop for Phase 1/2: after the external OCR branch has honestly failed to extract useful text, the pipeline now directs the operator to human review or multimodal supplementation instead of cycling through the same OCR command.

### 2026-06-11 12:50 | Codex (GPT-5)

Progress against the human-review loop:

- Added the direct CLI entrypoint:
  - `python -m video_knowledge_pipeline.cli prepare-review-session <webui-bundle>`;
  - MCP bridge compatibility remains available through `mcp-call prepare_review_session`.
- `prepare_review_session` now promotes `ocr_text_empty` from visual-structure ebook results into explicit review targets:
  - reason: `ocr_text_empty`;
  - suggested filter: `ocr_empty`;
  - fallback suggestion: human mark accepted / keep image / multimodal supplementation;
  - evidence frame paths are preserved.
- Review evidence excerpts now ignore wrapper-only ebook Markdown such as generated frame headings and `<!-- source: ... -->` comments.
- Real bundle verification:
  - `review-session.md` and `review-session.json` were generated for `real-tests\feishu-video-retry-live-asr\webui-bundle`;
  - the Markdown report contains an `OCR Empty Targets` section with 9 targets;
  - the JSON target summary reports `ocr_text_empty: 9`.
- Test verification:
  - `python -m pytest -q` -> `79 passed`.

Interpretation:

This makes the current `human_review_required / ocr_text_empty_review` next action actually usable from CLI, MCP bridge, and human-readable handoff files. The overall plan remains incomplete: semantic coverage is still 10 / 61 and temporal coverage is still 3 / 12.

### 2026-06-11 13:05 | Codex (GPT-5)

Progress against review-note round trip:

- `apply_review_notes_to_bundle` now handles `status=keep_image` as an accepted human review state.
- Review imports now preserve additional human fields:
  - `human_keep_image`;
  - `human_corrected_temporal_visual_understanding`;
  - existing machine ASR/OCR/model outputs are still not overwritten.
- Accepted review notes now clear the relevant machine-gap quality issues:
  - `missing_visual_text`;
  - `missing_ocr`;
  - `low_ocr_confidence`;
  - `ocr_text_empty`;
  - `structured_visual_without_structure`;
  - semantic/temporal missing visual understanding issues.
- `knowledge_coverage` now treats explicit human `keep_image` / human corrected text / human corrected visual understanding as an evidence-preserving fallback for OCR-empty and structured visual gaps.
- `knowledge_note_export` now renders human keep-image decisions and human temporal corrections instead of hiding them or counting them as unresolved gaps.
- Test verification:
  - `python -m pytest -q` -> `80 passed`.
- Real-bundle preview verification was done on a copied bundle:
  - `real-tests\feishu-video-retry-live-asr\phase2-review-preview-bundle`;
  - imported 9 preview review notes for indexes `16,17,18,24,25,48,66,67,68`;
  - `screen_text.blocker_count = 0`;
  - `structured_visual = 9 / 9`;
  - `items_with_visual_understanding = 19`;
  - `items_with_temporal_understanding = 10`;
  - export summary has `document_visual_missing_structure = []`.

Interpretation:

This completes the core Phase 5 review-note round trip behavior for OCR-empty / keep-image cases. It does not complete the full plan because semantic coverage still has 44 missing items and temporal coverage still has 4 missing items in the preview bundle.

### 2026-06-11 13:30 | Codex (GPT-5)

Progress against hierarchical Markdown export:

- `knowledge-note.md` now has additional lecture-note sections:
  - `关键概念与论点`;
  - `表格、公式、代码与必须保留的图片`;
  - `证据索引`.
- The new sections are generated from existing timeline evidence instead of invented summaries:
  - concept/argument rows use transcript, visual understanding, temporal understanding, and quality issues;
  - retained-media rows show material types, structured visual snippets, human keep-image decisions, and evidence paths;
  - evidence index rows list timeline index, time range, route, and frame paths.
- Regression test coverage was extended in `tests/test_video_pipeline_smoke.py`.
- Test verification:
  - `python -m pytest -q` -> `80 passed`.
- Real-bundle preview verification:
  - exported `real-tests\feishu-video-retry-live-asr\phase2-review-preview-bundle\exports\knowledge-note.md`;
  - confirmed the real output contains the new sections and keep-image evidence rows;
  - refreshed `knowledge-coverage.json` at `2026-06-11T13:26:48`.

Interpretation:

This improves Task 4's human-readable output requirement. The export is now closer to a layered lecture note, while still exposing unresolved visual gaps. The overall plan remains incomplete because the preview bundle still has `semantic_frame_understanding = 17 / 61` and `temporal_visual_understanding = 8 / 12`.

### 2026-06-11 14:01 | Codex (GPT-5)

Progress against acceptance and provider-blocked truthfulness:

- Added a first-class `acceptance_check` module with CLI and MCP entrypoints:
  - CLI: `.\scripts\video-knowledge.ps1 acceptance-check <webui-bundle>`;
  - MCP: `acceptance_check(bundle_dir, refresh=true, write=true)`.
- The acceptance layer reads existing evidence instead of duplicating provider/model logic:
  - `knowledge-coverage.json`;
  - `bundle-status.json`;
  - `vision-execution-preflight.json`;
  - export freshness for `knowledge-note.md` and `full-transcript.md`.
- It writes durable artifacts:
  - `acceptance-check.json`;
  - `acceptance-check.md`;
  - `mcp-acceptance-check.args.json`.
- `bundle-status` MCP args audit now recognizes `mcp_acceptance_check_args`.
- Regression tests now cover:
  - provider health failure plus visual gaps -> `provider_blocked`;
  - missing visual understanding without provider health failure -> `machine_action_available`.
- Real-bundle verification on `phase2-review-preview-bundle`:
  - `acceptance-check.status = provider_blocked`;
  - `semantic_missing = 44`;
  - `temporal_missing = 4`;
  - `provider_health = provider_unreachable`;
  - `provider_safe_to_execute = false`;
  - `export_freshness = stale`;
  - next action is provider repair/preflight, not unsafe direct multimodal execution.

Interpretation:

This does not close the remaining semantic/temporal visual coverage gaps. It makes the pipeline's acceptance state truthful and machine-readable, so the next implementation step can safely prioritize provider recovery or human review instead of pretending the bundle is complete.

### 2026-06-11 14:05 | Codex (GPT-5)

Progress against unsafe next-action prevention:

- `bundle_next_action` now checks the latest `vision-execution-preflight.json` before recommending direct model execution.
- If the coverage next action is `run_multimodal_frame_analysis` or `run_temporal_visual_analysis`, and provider health is unsafe, the top-level next action is rewritten to:
  - `status = provider_blocked`;
  - `key = provider_repair`;
  - `mcp_tool = vision_execution_preflight`;
  - original blocked action preserved in `for_blocked_action`.
- `bundle_status_report` now surfaces the same `provider_blocked` state as `acceptance_check`.
- Regression coverage added:
  - unsafe provider health blocks direct `run_multimodal_frame_analysis`;
  - normal visual gaps without unsafe provider still expose machine action;
  - acceptance provider-blocked and machine-action states remain covered.
- Test verification:
  - `python -m pytest -q` -> `86 passed`.
- Real-bundle verification:
  - `bundle-status-report.status = provider_blocked`;
  - `bundle-status-report.next_action.key = provider_repair`;
  - `acceptance-check.status = provider_blocked`;
  - MCP args audit remains `26 / 26 ok`.

Interpretation:

This closes a safety gap in the operator loop. The project no longer tells an agent or human to run real multimodal analysis when the latest provider preflight says the provider is unreachable. The remaining work is still real provider recovery, human-review template completion, and closing the 44 semantic plus 4 temporal visual gaps.

### 2026-06-11 14:10 | Codex (GPT-5)

Progress against provider recovery:

- Added persistent `vision_provider_smoke` as a provider repair entrypoint.
- New interfaces:
  - CLI: `.\scripts\video-knowledge.ps1 vision-provider-smoke --provider <provider> --bundle-dir <bundle>`;
  - MCP: `vision_provider_smoke(...)`.
- The smoke command reuses the existing provider adapter and writes no-secret reports:
  - `vision-provider-smoke.json`;
  - `vision-provider-smoke.md`;
  - `mcp-vision-provider-smoke.args.json`.
- When run with a bundle, it can automatically pick:
  - one normal evidence frame for single-image JSON smoke;
  - one ordered temporal frame group for multi-image JSON smoke.
- `bundle_next_action`, `bundle_status_report`, and `acceptance_check` now point provider repair to `vision_provider_smoke` instead of an unsafe direct multimodal command.
- MCP args audit now includes the smoke tool:
  - real bundle audit: `27 / 27 ok`.
- Real Agnes smoke on `phase2-review-preview-bundle`:
  - provider: `agnes`;
  - model: `agnes-1.5-flash`;
  - base URL: `https://apihub.agnes-ai.com/v1`;
  - key configured: `true`;
  - timeout: `8` seconds;
  - text ping: `provider_unreachable`;
  - single-image JSON: `provider_unreachable`;
  - multi-image JSON: `provider_unreachable`;
  - recovery suggestion: check base URL, local proxy/network, and timeout before real model execution.
- Test verification:
  - `python -m pytest -q` -> `88 passed`.
- Secret scan:
  - no real provider key found in smoke reports, MCP args, source changes, or plan update;
  - only test placeholders such as `AGNES_API_KEY=<your key>` remain.

Interpretation:

The provider recovery path is now explicit and reusable. This still does not solve the provider reachability problem or close semantic/temporal visual gaps, but it converts the blocker from an ambiguous API failure into a stable operator action with evidence, reports, MCP args, and no key leakage.

### 2026-06-11 14:30 | Codex (GPT-5)

Progress against review lifecycle and truthful acceptance:

- `acceptance-check` now exposes a first-class `review_lifecycle` object instead of mixing template preparation, imported human review, provider health, and export freshness into one vague blocked state.
- New acceptance summary fields:
  - `review_state`;
  - `review_template_prepared`;
  - `review_notes_imported`;
  - `review_targets_open`;
  - `review_targets_listed`.
- `acceptance-check.md` now includes a `Review Lifecycle` section with template path, review notes path, imported status, and open/listed target counts.
- `prepare-review-session` now registers generated review artifacts in `manifest.json`:
  - `review_session`;
  - `review_session_json`;
  - `review_notes_template`;
  - `mcp_prepare_review_session_args`.
- Review target generation now avoids reopening items that already have an accepted human review. This prevents old OCR-empty records or missing machine vision fields from re-entering the review queue after an explicit keep-image / accepted human decision.
- Real-bundle verification on `phase2-review-preview-bundle` after sequential refresh:
  - `acceptance-check.status = provider_blocked`;
  - `review_state = human_review_imported`;
  - `review_template_prepared = true`;
  - `review_notes_imported = true`;
  - `review_targets_open = 59`;
  - `review_targets_listed = 30`;
  - `semantic_missing = 44`;
  - `temporal_missing = 4`;
  - next action remains `provider_repair`, because the imported preview review notes only resolved the OCR/keep-image subset and did not close all semantic/temporal visual gaps.
- Test verification:
  - focused acceptance/review lifecycle tests passed;
  - `python -m pytest -q` -> `90 passed`.
- Secret scan:
  - no real provider key found in source, tests, docs, or refreshed real-bundle acceptance/review artifacts;
  - remaining hits are placeholders such as `<your key>` and documented scan commands.

Operational note:

Do not run `prepare-review-session` and `acceptance-check` in parallel against the same bundle. Both can refresh reports and write `manifest.json`; run them sequentially to avoid transient JSON read/write races.

Interpretation:

This improves the original plan's human-review and acceptance loop. The bundle can now truthfully say: OCR/document-visual blockers have an evidence-preserving human path, review artifacts are discoverable through the manifest, and remaining semantic/temporal gaps are still blocked by provider reachability or by pending human review. The full plan remains incomplete until either provider recovery succeeds and real multimodal batches fill the remaining 44 + 4 gaps, or those gaps are explicitly reviewed/imported as accepted known gaps.

### 2026-06-11 14:36 | Codex (GPT-5)

Progress against readable export and acceptance freshness:

- `export-knowledge-note` now writes three human-facing artifacts:
  - `exports/knowledge-note.md`;
  - `exports/full-transcript.md`;
  - `exports/extraction-audit.md`.
- `extraction-audit.md` is a dedicated audit file for checking whether the video extraction still has leak risks. It includes:
  - overall extraction counts;
  - route distribution;
  - document-visual and visual-understanding gap indexes;
  - human review status;
  - per-timeline audit table with speech, visual text, single-frame understanding, temporal understanding, review status, quality issues, and evidence paths;
  - links back to knowledge note, full transcript, coverage, acceptance, review session, and review template.
- `manifest.json` now records:
  - `knowledge_note_extraction_audit_markdown`;
  - `knowledge_note_export.extraction_audit_path`.
- `acceptance-check` freshness logic now ignores derived reports such as `knowledge-coverage.json`. Previously, `acceptance-check --refresh` rewrote coverage and then immediately judged the freshly exported note as stale. Freshness now watches source inputs such as `timeline.json`, `review-notes.json`, review template/session, and provider preflight.
- Real-bundle verification on `phase2-review-preview-bundle`:
  - `exports/knowledge-note.md` exists and is refreshed;
  - `exports/full-transcript.md` exists and is refreshed;
  - `exports/extraction-audit.md` exists and is refreshed;
  - `acceptance-check.summary.export_freshness = fresh`;
  - `acceptance-check.status = provider_blocked`;
  - `review_state = human_review_imported`;
  - `semantic_missing = 44`;
  - `temporal_missing = 4`;
  - next action remains `provider_repair`.
- Test verification:
  - focused export/acceptance freshness tests passed;
  - `python -m pytest -q` -> `91 passed`.
- Secret scan:
  - no real provider key found in source, tests, docs, refreshed acceptance artifacts, or refreshed export artifacts;
  - remaining hits are placeholders such as `<your key>` and documented scan commands.

Interpretation:

This closes the stale-export gap and makes Task 4's hierarchical Markdown export more usable for humans. The real bundle now has a readable knowledge note, a full transcript, and a separate extraction audit. The full plan remains incomplete because the remaining 44 semantic and 4 temporal visual gaps still require provider recovery or explicit human review import.

### 2026-06-11 14:48 | Codex (GPT-5)

Progress against WebUI review usability:

- `review.html` workflow cards now include first-class links and copyable commands for:
  - `acceptance-check.md` through `mcp-acceptance-check.args.json`;
  - `review-session.md` through `mcp-prepare-review-session.args.json`;
  - `review-notes.template.json`;
  - `exports/knowledge-note.md`;
  - `exports/full-transcript.md`;
  - `exports/extraction-audit.md`.
- New helper:
  - `refresh_bundle_review_html(bundle_dir, write=true)`;
  - CLI: `.\scripts\video-knowledge.ps1 refresh-review-html <bundle>`.
- The helper refreshes only `review.html` from the current bundle's `manifest.json` and `timeline.json`. It does not rebuild the bundle and does not overwrite current timeline, review imports, coverage, or visual understanding fields.
- Initial WebUI bundle generation now records additional stable manifest entries:
  - `acceptance_check`;
  - `acceptance_check_json`;
  - `mcp_acceptance_check_args`;
  - `review_session`;
  - `review_session_json`;
  - `review_notes_template`;
  - `knowledge_note_extraction_audit_markdown`.
- `README.md` generated inside a bundle now documents the acceptance report, review session/template, extraction audit, and acceptance MCP command.
- Real-bundle verification on `phase2-review-preview-bundle`:
  - `refresh-review-html` refreshed `review.html` from the current bundle without changing the 68-item timeline;
  - `review.html` contains links to `acceptance-check.md`, `review-session.md`, `review-notes.template.json`, `exports/full-transcript.md`, and `exports/extraction-audit.md`;
  - `manifest.review_html_refreshed_at = 2026-06-11T14:47:59`;
  - `acceptance-check.status = provider_blocked`;
  - `export_freshness = fresh`;
  - `review_state = human_review_imported`;
  - `semantic_missing = 44`;
  - `temporal_missing = 4`.
- Test verification:
  - focused WebUI tests passed;
  - `python -m pytest -q` -> `92 passed`.
- Secret scan:
  - no real provider key found in source, tests, docs, refreshed `review.html`, or refreshed `manifest.json`;
  - remaining hits are placeholders such as `<your key>` and documented scan commands.

Interpretation:

This completes the current WebUI handoff gap: a human can open `review.html` and find the acceptance report, review template, final readable exports, and agent commands without manually hunting through bundle files. The full plan remains incomplete because provider recovery or explicit review import is still required for the remaining semantic/temporal visual gaps.

### 2026-06-11 15:12 | Codex (GPT-5)

Progress against full review queue preparation:

- `prepare-review-session` now supports practical slicing of large review queues:
  - `--limit`;
  - `--offset`;
  - `--reason`;
  - `--limit 0` means list all filtered open targets.
- The MCP tool and generated MCP args now carry the same parameters:
  - `prepare_review_session(bundle_dir, refresh=true, limit=30, offset=0, reason="")`;
  - `mcp-prepare-review-session.args.json` includes `limit`, `offset`, and `reason`.
- Review target summaries now distinguish:
  - `total_open`;
  - `filtered_open`;
  - `listed_count`;
  - `offset`;
  - `limit`;
  - `reason_filter`.
- A shadowing bug in review filtering was fixed: the target loop no longer overwrites the requested `reason` filter with the last target reason.
- Real-bundle verification on `phase2-review-preview-bundle`:
  - `review-notes.template.json` contains 59 rows;
  - `review_targets_open = 59`;
  - `review_targets_listed = 59`;
  - suggested statuses:
    - `accepted`: 11;
    - `corrected_visual_understanding`: 44;
    - `corrected_temporal_visual_understanding`: 4.
  - `acceptance-check.status = provider_blocked`;
  - `review_state = human_review_imported`;
  - `semantic_missing = 44`;
  - `temporal_missing = 4`;
  - `export_freshness = fresh`;
  - next action remains `provider_repair`.
- Test verification:
  - `python -m pytest -q` -> `93 passed`.

Interpretation:

The remaining semantic and temporal gaps are now all represented in one complete, fillable review template. This makes the human-review fallback real instead of theoretical. The full plan is still incomplete because those 44 semantic and 4 temporal gaps have not yet been filled by a reachable provider or imported human review.

### 2026-06-11 15:24 | Codex (GPT-5)

Progress against review-note safety:

- Added a validation path for review notes:
  - CLI: `validate-review-notes <bundle> --review-json <path>`;
  - MCP: `validate_review_notes(bundle_dir, review_json?)`.
- `apply-review-notes` now runs the same validation before writing timeline changes.
- Invalid rows are skipped instead of being imported as completed review:
  - unknown `timeline_index`;
  - missing `timeline_index`;
  - duplicate `timeline_index` in one import;
  - `status=corrected_visual_understanding` without a non-empty `corrected_visual_understanding`;
  - `status=corrected_temporal_visual_understanding` without a non-empty `corrected_temporal_visual_understanding`;
  - `status=corrected_visual_text` without `corrected_visual_text`.
- Accepted rows without evidence paths now produce warnings. They are not blocked if the timeline item itself has asset paths.
- Import results now include a `validation` object with:
  - `status`;
  - `error_count`;
  - `warning_count`;
  - `invalid_row_numbers`;
  - `errors`;
  - `warnings`.
- Focused test verification:
  - `python -m pytest tests\test_video_pipeline_smoke.py::test_validate_review_notes_cli_contract tests\test_video_pipeline_smoke.py::test_review_notes_validation_skips_invalid_corrections_and_duplicates tests\test_video_pipeline_smoke.py::test_apply_review_notes_roundtrip_preserves_machine_outputs_and_exports tests\test_video_pipeline_smoke.py::test_review_notes_keep_image_resolves_ocr_structure_and_temporal_gaps -q` -> `4 passed`.

Interpretation:

This protects the main human-review fallback from a dangerous failure mode: an empty correction row can no longer clear a semantic or temporal blocker. The full plan remains incomplete until the remaining review rows are filled and imported, or a reachable provider completes the visual understanding batches.

### 2026-06-11 17:38 | Codex (GPT-5)

Progress against provider recovery diagnostics:

- `vision-provider-smoke` now writes a `diagnostics` section:
  - provider/model;
  - base URL scheme and host;
  - secret-redacted request URL;
  - endpoint kind, such as `openai_chat_completions`;
  - timeout seconds;
  - API key configured/required booleans;
  - proxy environment presence booleans for `HTTP_PROXY`, `HTTPS_PROXY`, `ALL_PROXY`, and `NO_PROXY`.
- `vision-provider-smoke` now writes an `image_selection` section:
  - total image count;
  - whether single-image check is active;
  - whether multi-image check is active;
  - max image cap.
- Provider public config and generated smoke MCP args now redact secret-like URL query values such as `key`, `api_key`, `token`, `access_token`, `authorization`.
- Provider error classification now distinguishes additional network classes:
  - `provider_dns_failed`;
  - `provider_proxy_failed`;
  - `provider_connection_refused`;
  - existing `provider_transport_error`, `provider_unreachable`, auth, quota, and JSON parse failures remain.
- `vision-execution-preflight` now includes the same secret-safe `provider_diagnostics` and renders request URL/proxy presence in Markdown.
- Real Agnes verification on `phase2-review-preview-bundle`:
  - provider: `agnes`;
  - model: `agnes-1.5-flash`;
  - request URL: `https://apihub.agnes-ai.com/v1/chat/completions`;
  - API key configured: `true`;
  - proxy env present: `HTTP_PROXY`, `HTTPS_PROXY`, `ALL_PROXY`, `NO_PROXY`;
  - smoke status: `provider_transport_error`;
  - error summary: `SSL: UNEXPECTED_EOF_WHILE_READING`;
  - preflight status: `provider_transport_error`;
  - acceptance status remains `provider_blocked`;
  - `semantic_missing = 44`;
  - `temporal_missing = 4`;
  - `export_freshness = fresh` after re-export.
- Focused test verification:
  - provider smoke diagnostics/redaction, missing-key smoke, and preflight readiness tests passed.

Interpretation:

The current blocker is now better characterized: Agnes is not blocked by missing key, but by a transport/TLS failure on the current endpoint/proxy path. The next meaningful provider-recovery action is to switch provider/profile or fix the network/proxy/TLS route, not to keep retrying the same unsafe execution command. The full plan remains incomplete because real multimodal coverage is still missing for 44 semantic and 4 temporal items.

### 2026-06-11 17:44 | Codex (GPT-5)

Progress against provider switching:

- Added a provider matrix diagnostic entrypoint:
  - CLI: `vision-provider-matrix --providers "agnes,gemini,openai" --bundle-dir <bundle>`;
  - MCP: `vision_provider_matrix(providers?, bundle_dir?, timeout_seconds?, ...)`.
- The matrix reuses the same smoke checks and evidence image selection as `vision-provider-smoke`, but writes comparison artifacts:
  - `vision-provider-matrix.json`;
  - `vision-provider-matrix.md`;
  - `mcp-vision-provider-matrix.args.json`.
- The report records for each provider:
  - provider/model;
  - safe-to-execute;
  - status/error class;
  - secret-redacted request URL;
  - proxy environment presence;
  - recovery suggestion.
- Fixed provider profile contamination:
  - when `LECTURE_VISION_PROVIDER=agnes` and `LECTURE_VISION_MODEL=agnes-1.5-flash` are set, explicit `--provider gemini` and `--provider openai` no longer inherit the Agnes model/base URL;
  - Gemini now resolves to `gemini-2.5-flash`;
  - OpenAI now resolves to `gpt-4o-mini`.
- Real matrix result on `phase2-review-preview-bundle`:
  - `agnes`: `provider_unreachable`, model `agnes-1.5-flash`;
  - `gemini`: `missing_api_key`, model `gemini-2.5-flash`;
  - `openai`: `missing_api_key`, model `gpt-4o-mini`;
  - `recommended_provider` remains empty because no provider is currently safe.
- Real acceptance after re-export:
  - `acceptance-check.status = provider_blocked`;
  - `semantic_missing = 44`;
  - `temporal_missing = 4`;
  - `export_freshness = fresh`.
- Focused test verification:
  - provider config scoping and provider matrix tests passed.

Interpretation:

Provider recovery is now a real comparison workflow instead of a single failing Agnes smoke. The current machine state says: Agnes has a network/transport reachability problem, while Gemini/OpenAI are not configured with keys in this process. The full plan remains incomplete until one provider becomes safe and fills the 44 + 4 visual gaps, or those gaps are imported through validated human review.

### 2026-06-11 17:52 | Codex (GPT-5)

Progress against provider-blocked operator routing:

- `acceptance-check` now reads `vision-provider-matrix.json` and embeds a compact `provider_matrix` summary:
  - matrix status;
  - recommended provider;
  - provider/model/status/error class for each candidate;
  - matrix report path and MCP args path.
- `acceptance-check.md` now renders a `Provider Matrix` table when matrix artifacts exist.
- When provider health blocks semantic/temporal execution, `acceptance-check.next_action` now prefers:
  - `mcp_tool = vision_provider_matrix`;
  - `key = provider_matrix_repair` when no provider is ready;
  - `key = provider_preflight_with_recommended` if a ready provider exists.
- `bundle-next-action` now also prefers `vision_provider_matrix` over single-provider smoke when a multimodal action is blocked by provider health.
- `bundle-next-action` writes a default `mcp-vision-provider-matrix.args.json` when it recommends matrix repair, so the suggested MCP command is immediately callable.
- MCP args audit mapping now recognizes `mcp_vision_provider_matrix_args`.
- Real-bundle verification on `phase2-review-preview-bundle`:
  - `bundle-next-action.status = provider_blocked`;
  - `bundle-next-action.next_action.key = provider_matrix_repair`;
  - `bundle-next-action.next_action.mcp_tool = vision_provider_matrix`;
  - blocked action remains correctly preserved as `run_multimodal_frame_analysis`;
  - `acceptance-check.status = provider_blocked`;
  - `acceptance-check.next_action.key = provider_matrix_repair`;
  - matrix summary: `agnes=provider_unreachable`, `gemini=missing_api_key`, `openai=missing_api_key`;
  - `semantic_missing = 44`;
  - `temporal_missing = 4`;
  - `export_freshness = fresh`.
- Focused test verification:
  - provider-blocked acceptance, bundle-next provider override, and review lifecycle tests passed.

Interpretation:

The operator loop is now less brittle. When real multimodal coverage is blocked, the project points to provider comparison/switching instead of repeatedly retrying the currently failing provider. The full plan remains incomplete until provider recovery or validated human review actually closes the remaining visual understanding gaps.

### 2026-06-11 17:56 | Codex (GPT-5)

Progress against MCP handoff correctness:

- Fixed the local `mcp-call` / MCP args audit mapping for the new provider recovery tools:
  - `acceptance_check`;
  - `vision_provider_smoke`;
  - `vision_provider_matrix`.
- Real-bundle verification:
  - `mcp-audit-bundle` now reports `status = ok`;
  - total args files: `29`;
  - ok: `29`;
  - blocked: `0`.

Interpretation:

The provider matrix route is now usable from the generated MCP args files, not only from direct CLI. This matters because the plan requires CLI/MCP/agent-stable invocation, and provider recovery is currently the main blocker before real multimodal execution.

## Success Criteria

Phase 1 is complete when the real bundle satisfies:

- `screen_text` blocker count is reduced from 9 to 0 or every remaining blocker has an explicit `needs_human_review` reason.
- `structured_visual` blocker count is reduced from 9 to 0 or every remaining blocker has an explicit evidence-preserving fallback.
- At least 10 `semantic_frame` items have `visual_understanding` generated by a real provider or imported from audited JSON.
- At least 3 `temporal_sequence` / `mixed` items have `temporal_visual_understanding`.
- `exports/knowledge-note.md` contains separate sections for video overview, coverage, route distribution, visual knowledge, temporal events, transcript with demonstrations, and remaining gaps.
- `python -m pytest -q` passes.

Phase 2 is complete when:

- `bundle-next-action` can advance through visual structure, semantic frame, temporal frame groups, temporal visual analysis, coverage audit, and export without manual command reconstruction.
- WebUI exposes current coverage gaps and the correct MCP/CLI commands for each next step.
- All real execution paths preserve API key secrecy and write restore/audit artifacts.

Phase 3 is complete when:

- Peepshow can be used as an optional extractor and its `manifest.json`, `report.html`, transcript, OCR, per-frame analysis, and tags are imported or preserved as source artifacts.
- Peepshow output does not bypass `video_frame_router`, `run_visual_structure_plan`, multimodal analysis, temporal analysis, or knowledge export.

## Task 1: Make ebook Pipeline Integration Operational

**Files:**

- Modify: `src/video_knowledge_pipeline/visual_structure.py`
- Modify: `src/video_knowledge_pipeline/config.py`
- Modify: `src/video_knowledge_pipeline/bundle_next.py`
- Test: `tests/test_video_pipeline_smoke.py`
- Verify real bundle: `real-tests/feishu-video-retry-live-asr/webui-bundle`

**Step 1: Add tests for successful ebook result normalization**

Write a test that feeds a fake `ebook_markdown_pipeline` result into `_ebook_results_to_import_rows` and asserts:

- `source == "ebook_markdown_pipeline"`
- `visual_text` is populated from Markdown artifact text
- `structured_visual` keeps tables/code/formula-like Markdown blocks when present
- evidence path and source artifact path are preserved

Run:

```powershell
python -m pytest tests/test_video_pipeline_smoke.py -q
```

Expected: failing test before implementation.

**Step 2: Harden `_read_best_ebook_artifact` and `_ebook_markdown`**

Implementation requirements:

- Prefer explicit `markdown`, `output`, `report`, or `artifact` payloads from `read_artifact`.
- If the MCP result points to files, read only files under the requested output directory.
- Never treat missing artifact as success.
- Preserve raw result metadata in the report, but do not store huge raw blobs in `timeline.json`.

Run the focused tests and then:

```powershell
python -m pytest -q
```

**Step 3: Add dry-run report clarity**

Update the `visual-structure-report.md` writer in `visual_structure.py` so every candidate row shows:

- timeline index
- visual route
- frame path
- planned MCP flow: `process_material -> get_job_status -> read_artifact`
- status: preview / imported / failed / needs human review

Add or update tests that assert report text includes `process_material`, candidate index, and output artifact status.

**Step 4: Real bundle smoke**

Run preview first:

```powershell
$env:PYTHONPATH='src'
python -m video_knowledge_pipeline.cli run-visual-structure %WORKSPACE_ROOT%\video-knowledge-pipeline\real-tests\feishu-video-retry-live-asr\webui-bundle
```

Then run execution only if `ebook_markdown_pipeline` is available:

```powershell
.\scripts\video-knowledge.ps1 mcp-call run_visual_structure_plan %WORKSPACE_ROOT%\video-knowledge-pipeline\real-tests\feishu-video-retry-live-asr\webui-bundle\mcp-run-visual-structure.args.json
```

If execution is blocked by external service readiness, write the blocker into the report and keep the task incomplete rather than falling back silently.

**Step 5: Commit**

```powershell
git add src/video_knowledge_pipeline/visual_structure.py src/video_knowledge_pipeline/config.py src/video_knowledge_pipeline/bundle_next.py tests/test_video_pipeline_smoke.py
git commit -m "feat: harden ebook visual structure integration"
```

## Task 2: Batch Semantic Frame Understanding Safely

**Files:**

- Modify: `src/video_knowledge_pipeline/multimodal_frame_analyzer.py`
- Modify: `src/video_knowledge_pipeline/vision_preflight.py`
- Modify: `src/video_knowledge_pipeline/knowledge_coverage.py`
- Test: `tests/test_video_pipeline_smoke.py`

**Step 1: Add tests for selected batch execution**

Create tests for:

- `--indexes` selects exact semantic timeline indexes.
- already analyzed items are skipped unless an explicit overwrite flag exists.
- `confirm_vision_calls` and `confirm_vision_indexes` must match the selected batch.
- evidence frame paths are preserved as full bundle-resolvable paths.

Expected failing behavior should be narrow and explicit.

**Step 2: Improve report for batch quality review**

Update multimodal report output to include a compact review table:

| index | time | frame | transcript excerpt | route | model status | keep screenshot reason | confidence |

Do not include prompts or API keys.

**Step 3: Real provider small batch**

Run preflight for 10 semantic candidates:

```powershell
.\scripts\video-knowledge.ps1 vision-execution-preflight %WORKSPACE_ROOT%\video-knowledge-pipeline\real-tests\feishu-video-retry-live-asr\webui-bundle --semantic-limit 10 --no-temporal
```

Then execute only with exact confirmation values from the preflight report:

```powershell
.\scripts\video-knowledge.ps1 run-multimodal-frame-analysis %WORKSPACE_ROOT%\video-knowledge-pipeline\real-tests\feishu-video-retry-live-asr\webui-bundle --execute --limit 10 --confirm-vision-calls <calls> --confirm-vision-indexes "<indexes>"
```

**Step 4: Update coverage and export**

Run:

```powershell
.\scripts\video-knowledge.ps1 audit-knowledge-coverage %WORKSPACE_ROOT%\video-knowledge-pipeline\real-tests\feishu-video-retry-live-asr\webui-bundle
.\scripts\video-knowledge.ps1 export-knowledge-note %WORKSPACE_ROOT%\video-knowledge-pipeline\real-tests\feishu-video-retry-live-asr\webui-bundle --title "feishu-video-retry"
```

Expected:

- `semantic_frame_understanding.covered_count >= 10`
- `exports/knowledge-note.md` shows model-understood visual information with evidence frames.

**Step 5: Commit**

```powershell
git add src/video_knowledge_pipeline/multimodal_frame_analyzer.py src/video_knowledge_pipeline/vision_preflight.py src/video_knowledge_pipeline/knowledge_coverage.py tests/test_video_pipeline_smoke.py
git commit -m "feat: support safe semantic vision batches"
```

## Task 3: Batch Temporal Sequence Understanding

**Files:**

- Modify: `src/video_knowledge_pipeline/temporal_frame_groups.py`
- Modify: `src/video_knowledge_pipeline/temporal_visual_analyzer.py`
- Modify: `src/video_knowledge_pipeline/bundle_next.py`
- Test: `tests/test_video_pipeline_smoke.py`

**Step 1: Add tests for temporal preconditions**

Tests should assert:

- `bundle-next-action` recommends `run_temporal_frame_groups` before `run_temporal_visual_analysis` when `temporal_frame_paths` are missing.
- generated temporal frame groups contain 5-12 ordered frames.
- `temporal_visual_analyzer` sends frames in order and preserves frame paths.

**Step 2: Strengthen temporal frame group report**

Add report columns:

| index | start-end | route | frame_count | generated paths | source video | status |

**Step 3: Real temporal smoke**

Generate frame groups:

```powershell
.\scripts\video-knowledge.ps1 run-temporal-frame-groups %WORKSPACE_ROOT%\video-knowledge-pipeline\real-tests\feishu-video-retry-live-asr\webui-bundle --execute --frame-count 8 --limit 5
```

Run preflight:

```powershell
.\scripts\video-knowledge.ps1 vision-execution-preflight %WORKSPACE_ROOT%\video-knowledge-pipeline\real-tests\feishu-video-retry-live-asr\webui-bundle --no-semantic --temporal-limit 3 --frame-count 8
```

Execute with exact confirmation:

```powershell
.\scripts\video-knowledge.ps1 run-temporal-visual-analysis %WORKSPACE_ROOT%\video-knowledge-pipeline\real-tests\feishu-video-retry-live-asr\webui-bundle --execute --limit 3 --frame-count 8 --confirm-vision-calls <calls> --confirm-vision-indexes "<indexes>"
```

Expected:

- `temporal_visual_understanding.covered_count >= 3`
- every temporal output includes event sequence, state changes, possible omissions, and evidence frames.

**Step 4: Commit**

```powershell
git add src/video_knowledge_pipeline/temporal_frame_groups.py src/video_knowledge_pipeline/temporal_visual_analyzer.py src/video_knowledge_pipeline/bundle_next.py tests/test_video_pipeline_smoke.py
git commit -m "feat: support safe temporal vision batches"
```

## Task 4: Improve Hierarchical Markdown Export

**Files:**

- Modify: `src/video_knowledge_pipeline/knowledge_note_export.py`
- Modify: `src/video_knowledge_pipeline/knowledge_coverage.py`
- Test: `tests/test_video_pipeline_smoke.py`
- Verify: `real-tests/feishu-video-retry-live-asr/webui-bundle/exports/knowledge-note.md`

**Step 1: Add tests for required Markdown sections**

Assert exported `knowledge-note.md` contains:

- `# <title>`
- `## 视频概要`
- `## 覆盖情况`
- `## 知识结构`
- `## 图文与视觉信息`
- `## 连续演示与操作变化`
- `## 逐字稿与演示记录`
- `## 未解决缺口`

**Step 2: Add section-level synthesis**

Implementation requirements:

- Group timeline items into coarse chapters using transcript time continuity and route changes.
- Each chapter should include `说了什么`, `演示了什么`, `屏幕/图表信息`, and `证据`.
- Do not hide missing visual data. If a chapter has OCR or multimodal gaps, list them.

**Step 3: Preserve full transcript separately**

`full-transcript.md` should remain complete and chronological. `knowledge-note.md` can be structured and synthesized, but must link back to full transcript and timeline indexes.

**Step 4: Real export check**

Run:

```powershell
.\scripts\video-knowledge.ps1 export-knowledge-note %WORKSPACE_ROOT%\video-knowledge-pipeline\real-tests\feishu-video-retry-live-asr\webui-bundle --title "feishu-video-retry"
```

Open/read:

- `real-tests/feishu-video-retry-live-asr/webui-bundle/exports/knowledge-note.md`
- `real-tests/feishu-video-retry-live-asr/webui-bundle/exports/full-transcript.md`

**Step 5: Commit**

```powershell
git add src/video_knowledge_pipeline/knowledge_note_export.py src/video_knowledge_pipeline/knowledge_coverage.py tests/test_video_pipeline_smoke.py
git commit -m "feat: improve hierarchical knowledge export"
```

## Task 5: Make Human Review and Tagging Round Trip

**Files:**

- Modify: `src/video_knowledge_pipeline/review_session.py`
- Modify: `src/video_knowledge_pipeline/webui_bridge.py`
- Modify: `src/video_knowledge_pipeline/bundle_readiness.py`
- Modify: `src/video_knowledge_pipeline/knowledge_coverage.py`
- Test: `tests/test_video_pipeline_smoke.py`

**Step 1: Define review note schema**

Use `review-notes.json` with fields:

- `timeline_index`
- `status`: `accepted`, `needs_fix`, `irrelevant`, `keep_image`, `needs_human_review`
- `tags`
- `comment`
- `corrected_transcript`
- `corrected_visual_text`
- `corrected_visual_understanding`
- `reviewed_at`

**Step 2: Add tests for review merge**

Assert review notes:

- do not overwrite model output destructively
- appear in export
- affect readiness counts
- can mark a missing machine result as intentionally human-reviewed

**Step 3: Update WebUI bridge**

Expose review note paths and commands in `review.html` bundle metadata. If full interactive editing is too large for this phase, ship a stable JSON import/export workflow first.

**Step 4: Commit**

```powershell
git add src/video_knowledge_pipeline/review_session.py src/video_knowledge_pipeline/webui_bridge.py src/video_knowledge_pipeline/bundle_readiness.py src/video_knowledge_pipeline/knowledge_coverage.py tests/test_video_pipeline_smoke.py
git commit -m "feat: add review note round trip"
```

## Task 6: Formalize Peepshow as Optional Extractor

**Files:**

- Modify: `src/video_knowledge_pipeline/peepshow_adapter.py`
- Modify: `src/video_knowledge_pipeline/extractor_execution.py`
- Modify: `src/video_knowledge_pipeline/visual_tool_resolver.py`
- Modify: `src/video_knowledge_pipeline/source_artifacts.py`
- Test: `tests/test_video_pipeline_smoke.py`
- Docs: `docs/architecture.md`

**Step 1: Add fixture for real Peepshow manifest shape**

Use a compact fixture with:

- `outputDir`
- `frames`
- `video`
- `audio.transcript`
- `analysis.summary`
- `analysis.perFrame`
- optional OCR-like frame text

**Step 2: Improve import**

`import_peepshow_output` should:

- preserve original `manifest.json`
- copy or reference `report.html`
- import transcript excerpts when available
- import per-frame analysis as evidence but not as final `visual_understanding` unless marked as imported model output
- preserve tags as source metadata
- route resulting timeline items through normal `video_frame_router`

**Step 3: Add guarded run command**

`run-extractor-plan peepshow --execute` should:

- use resolved Peepshow command
- write planned and actual command to report
- capture output directory
- not assume Peepshow OCR is equivalent to structured visual parsing

**Step 4: Commit**

```powershell
git add src/video_knowledge_pipeline/peepshow_adapter.py src/video_knowledge_pipeline/extractor_execution.py src/video_knowledge_pipeline/visual_tool_resolver.py src/video_knowledge_pipeline/source_artifacts.py tests/test_video_pipeline_smoke.py docs/architecture.md
git commit -m "feat: formalize peepshow evidence extractor"
```

## Task 7: End-to-End Acceptance Run

**Files:**

- Modify only if failures reveal gaps:
  - `src/video_knowledge_pipeline/acceptance_run.py`
  - `src/video_knowledge_pipeline/bundle_next.py`
  - `src/video_knowledge_pipeline/bundle_status.py`
  - `src/video_knowledge_pipeline/webui_bridge.py`

**Step 1: Run tests**

```powershell
python -m pytest -q
```

Expected: all tests pass.

**Step 2: Run status on real bundle**

```powershell
$env:PYTHONPATH='src'
python -m video_knowledge_pipeline.cli bundle-status-report %WORKSPACE_ROOT%\video-knowledge-pipeline\real-tests\feishu-video-retry-live-asr\webui-bundle
python -m video_knowledge_pipeline.cli audit-knowledge-coverage %WORKSPACE_ROOT%\video-knowledge-pipeline\real-tests\feishu-video-retry-live-asr\webui-bundle
```

Expected:

- status is not blocked by missing transcript, missing frames, or missing route.
- any remaining blockers are specifically OCR, semantic, temporal, or human review.

**Step 3: Run export**

```powershell
.\scripts\video-knowledge.ps1 export-knowledge-note %WORKSPACE_ROOT%\video-knowledge-pipeline\real-tests\feishu-video-retry-live-asr\webui-bundle --title "feishu-video-retry"
```

Expected outputs:

- `exports/knowledge-note.md`
- `exports/full-transcript.md`
- `exports/export-summary.json`

**Step 4: Commit final acceptance updates**

```powershell
git add .
git commit -m "test: verify next-stage video knowledge pipeline"
```

Only stage intentional source, docs, and test changes. Do not commit local secrets, `.local`, generated heavy video files, or ignored real-test artifacts unless explicitly required.

## Execution Order

Recommended order:

1. Task 1: ebook visual structure integration.
2. Task 2: semantic frame batch.
3. Task 3: temporal sequence batch.
4. Task 4: hierarchical Markdown export.
5. Task 5: human review round trip.
6. Task 6: Peepshow optional extractor.
7. Task 7: end-to-end acceptance.

Do not start Task 6 before Tasks 1-4 are usable. Peepshow is helpful, but the current blocker is coverage inside the existing bundle, not lack of another extractor.

## Risk Controls

- Never write API keys to config, manifest, reports, docs, or tests.
- Do not silently fallback from `ebook_markdown_pipeline` to weak OCR when the requested route is `document_visual`.
- Do not let model output overwrite ASR, OCR, or human corrections.
- Keep every visual output tied to evidence frame paths.
- Keep all real API execution behind preflight and confirmation values.
- Keep generated reports human-readable and machine-readable.

## Plan Completion Check

Plan implementation is complete when:

```powershell
python -m pytest -q
$env:PYTHONPATH='src'; python -m video_knowledge_pipeline.cli audit-knowledge-coverage %WORKSPACE_ROOT%\video-knowledge-pipeline\real-tests\feishu-video-retry-live-asr\webui-bundle
```

shows that all remaining blockers are either resolved or intentionally marked for human review, and `exports/knowledge-note.md` is good enough for a human to read without opening the raw timeline first.

## Execution Log

### 2026-06-11 17:58 | Codex (GPT-5)

- Completed the human-review fallback for the current provider-blocked state by adding `review-fill-guide.md` generation from `prepare_review_session`.
- `review-fill-guide.md` now groups fillable review rows into:
  - `连续片段待补`;
  - `单帧视觉待补`;
  - `其他人工确认`.
- Each row includes the timeline index, time range, visual route, reason, transcript excerpt, evidence frame path, Markdown image reference, and a compact JSON snippet that can be copied into `review-notes.json`.
- The real `phase2-review-preview-bundle` was refreshed with `--limit 0`:
  - `review_targets.listed_count = 59`;
  - `review-notes.template.json` rows = `59`;
  - `corrected_temporal_visual_understanding` rows = `4`;
  - `corrected_visual_understanding` rows = `44`;
  - manifest now records `review_fill_guide = review-fill-guide.md`.
- Re-ran export and acceptance on the real bundle:
  - `export_freshness = fresh`;
  - `acceptance-check.status = provider_blocked`;
  - `semantic_missing = 44`;
  - `temporal_missing = 4`;
  - provider matrix remains `no_provider_ready`.
- Re-ran MCP args audit:
  - `status = ok`;
  - `ok_count = 29`;
  - `blocked_count = 0`.
- Ran targeted and full tests:
  - focused review-session tests: `2 passed`;
  - full suite: `98 passed`.
- Sensitive scan over the new review guide/template and provider/acceptance artifacts found no API key patterns.
- Remaining blocker is unchanged but now has a usable human fallback path: either repair a multimodal provider and run the 44+4 visual analyses, or fill/import `review-notes.json` from `review-fill-guide.md`.

### 2026-06-11 18:08 | Codex (GPT-5)

- Improved provider diagnostics so `test_vision_provider`, `vision_provider_smoke`, and `vision_provider_matrix` can distinguish text-only provider health from image/multi-image failures.
- Added `failure_diagnosis` to provider test/smoke/matrix reports with:
  - `text_ping_ok`;
  - image check counts;
  - failed image check names;
  - max image payload bytes;
  - likely causes.
- Added image payload byte summaries per check, so payload-size and frame-count issues are visible without exposing API keys.
- Added explicit aggregate statuses:
  - `text_only_ok_image_timeout`;
  - `text_only_ok_image_not_supported`;
  - `text_only_ok_image_payload_too_large`;
  - `text_only_ok_image_parse_failed`.
- Re-ran the real provider matrix on `phase2-review-preview-bundle` with `--timeout-seconds 30`:
  - `status = no_provider_ready`;
  - `agnes = text_only_ok_image_timeout`;
  - `gemini = missing_api_key`;
  - `openai = missing_api_key`;
  - Agnes text ping works, but both single-image and multi-image checks timed out;
  - max multi-image payload was `1936949` bytes.
- Re-ran acceptance on the real bundle:
  - `acceptance-check.status = provider_blocked`;
  - next action hint now reports `agnes=text_only_ok_image_timeout` instead of a generic unreachable/provider failure.
- Re-ran verification:
  - provider-focused tests: `4 passed`;
  - full suite: `100 passed`;
  - MCP args audit: `29/29 ok`;
  - real provider/acceptance artifacts sensitive scan found no API key patterns.
- Remaining path to close the visual gaps is now clearer:
  - either reduce image payload / switch Agnes model or endpoint if Agnes supports vision;
  - or configure Gemini/OpenAI key and rerun provider matrix;
  - or use `review-fill-guide.md` to import human-reviewed visual understanding.

### 2026-06-11 18:17 | Codex (GPT-5)

- Added reusable small-image provider probes to `vision_provider_smoke` and `vision_provider_matrix`:
  - `image_probe_max_edge`;
  - `image_probe_jpeg_quality`;
  - `max_images`.
- Probe images are written under `vision-provider-smoke-probes/`; original evidence frames are not overwritten.
- Added the same image-probe controls to real semantic and temporal visual execution:
  - `run_multimodal_frame_analysis`;
  - `run_temporal_visual_analysis`;
  - CLI and MCP wrappers.
- Real bundle probe results:
  - original first smoke image: `243295` bytes;
  - probe image at max edge `512`, JPEG quality `55`: `15784` bytes.
- Re-ran provider matrix on the real bundle with one compressed image:
  - `status = ok`;
  - `recommended_provider = agnes`;
  - `agnes.safe_to_execute = true`;
  - Gemini/OpenAI remain `missing_api_key`.
- Executed one real semantic-frame API write through Agnes with compressed image input:

```powershell
.\scripts\video-knowledge.ps1 run-multimodal-frame-analysis %WORKSPACE_ROOT%\video-knowledge-pipeline\real-tests\feishu-video-retry-live-asr\phase2-review-preview-bundle --execute --provider-config '{"provider":"agnes"}' --limit 1 --indexes 4 --confirm-vision-calls 1 --confirm-vision-indexes 4 --image-probe-max-edge 512 --image-probe-jpeg-quality 55
```

- Real execution result:
  - run id: `semantic_frame-20260611-181631`;
  - selected index: `4`;
  - executed API calls: `1`;
  - updated timeline items: `1`;
  - evidence frame path remains the original asset frame;
  - sent image path points to the compressed probe under `vision-analysis-image-probes/semantic/4/`.
- Re-ran acceptance/export/MCP audit:
  - `acceptance-check.status = machine_action_available`;
  - `semantic_missing = 43` (down from `44`);
  - `temporal_missing = 4`;
  - `items_with_visual_understanding = 20`;
  - `export_freshness = fresh`;
  - MCP audit: `29/29 ok`.
- Re-ran verification:
  - full suite: `101 passed`;
  - real provider/acceptance/vision-run artifacts sensitive scan found no API key patterns.
- This proves the main multimodal route can now make real progress with Agnes when compressed image probes are used. The remaining work is to batch this carefully over the remaining `43` semantic and `4` temporal gaps, with confirmation gates and restore audits preserved.

### 2026-06-11 19:10 | Codex (GPT-5)

Final verification against this plan on the real `phase2-review-preview-bundle`:

- Re-ran acceptance:
  - command: `.\scripts\video-knowledge.ps1 acceptance-check %WORKSPACE_ROOT%\video-knowledge-pipeline\real-tests\feishu-video-retry-live-asr\phase2-review-preview-bundle`;
  - `acceptance-check.status = accepted_with_known_gaps`;
  - `blockers = []`;
  - `next_action.key = none`;
  - `export_freshness = fresh`;
  - `review_state = human_review_imported`.
- Coverage state:
  - `speech = ok`, `68 / 68`;
  - `visual_frames = ok`, `68 / 68`;
  - `visual_route = ok`, `68 / 68`;
  - `structured_visual = ok`, `9 / 9`;
  - `semantic_frame_understanding = ok`, `61 / 61`, missing `0`;
  - `temporal_visual_understanding = ok`, `12 / 12`, missing `0`;
  - `screen_text = weak`, `9 / 68`, blocker count `0`.
- Interpretation of the remaining weak channel:
  - The original blocking OCR/document-visual gap is closed through the explicit review/keep-image fallback and visual evidence chain.
  - `screen_text` remains weak because small UI text is not fully OCR-recovered, but there are no unresolved blockers and the weakness is visible in coverage, acceptance, and export audit.
- Real human-facing outputs exist and are fresh:
  - `exports/knowledge-note.md`;
  - `exports/full-transcript.md`;
  - `exports/extraction-audit.md`;
  - `review.html`;
  - `review-session.md`;
  - `review-notes.template.json`.
- `knowledge-note.md` contains the required human-readable sections:
  - `视频概要`;
  - `覆盖情况`;
  - `知识结构`;
  - `图文与视觉信息`;
  - `连续演示与操作变化`;
  - `逐字稿与演示记录`;
  - `未解决缺口`.
- Re-ran MCP args audit:
  - command: `.\scripts\video-knowledge.ps1 mcp-audit-bundle %WORKSPACE_ROOT%\video-knowledge-pipeline\real-tests\feishu-video-retry-live-asr\phase2-review-preview-bundle`;
  - `status = ok`;
  - `ok_count = 29`;
  - `blocked_count = 0`.
- Re-ran the explicit completion-check coverage command:
  - command: `.\scripts\video-knowledge.ps1 audit-knowledge-coverage %WORKSPACE_ROOT%\video-knowledge-pipeline\real-tests\feishu-video-retry-live-asr\phase2-review-preview-bundle`;
  - `status = weak`;
  - `blockers = []`;
  - `semantic_frame_without_analysis = 0`;
  - `temporal_sequence_without_analysis = 0`;
  - `missing_visual_understanding = 0`.
- Re-ran full test suite:
  - command: `python -m pytest -q`;
  - result: `104 passed in 10.10s`.
- File integrity checks:
  - `manifest.json`, `acceptance-check.json`, and `knowledge-coverage.json` parse successfully;
  - `.bundle-write.lock` is absent after the run, so no stale bundle write lock remains.
- Secret scan:
  - command: `rg -n -e "sk-" -e "Authorization: Bearer" -e "AGNES_API_KEY=" -e "GEMINI_API_KEY=" -e "OPENAI_API_KEY=" %WORKSPACE_ROOT%\video-knowledge-pipeline`;
  - no real provider key was found;
  - hits are placeholders, docs, tests, or scan commands such as `<your key>`, `...`, and `Authorization: Bearer <api_key>`.

Completion interpretation:

The plan's original goal is satisfied for the reference real video: the tool can process one real knowledge video with ASR, document-frame parsing/fallback, multimodal frame understanding, temporal sequence understanding, coverage audit, human review, and hierarchical Markdown export. The remaining `screen_text` weakness is a known quality limitation rather than an unresolved blocker, and it is explicitly surfaced in acceptance and audit outputs.
