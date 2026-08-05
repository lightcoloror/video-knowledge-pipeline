# Offline Quality Routing

## Purpose

offline-quality-route inspects existing local artifacts only. It does not run ASR, OCR, vision, downloads, network calls, or cloud fallbacks.

## Stable interface

    .\scripts\video-knowledge.ps1 offline-quality-route <webui-bundle> --benchmark-manifest <quality-benchmark-manifest.json> --output-dir <report-dir>

MCP tool: offline_quality_route(bundle_dir, benchmark_manifest="", output_dir="", write=true).

## Vocabulary

Stage quality: unknown, missing, stopped_by_design, low, weak, usable, good.

Failure classes include artifact_missing, empty_output, punctuation_sparse, segmentation_coarse, coverage_incomplete, text_mutation, execution_not_requested, provider_unavailable, and parse_failure.

Fallbacks are proposals, never automatic execution. They include local postprocess/retry, use of an existing local transcript, retaining image evidence, and optional review packs. Every route records auto_execute=false and cloud_allowed=false.

Human review state: not_required, optional, recommended.

A review HTML file existing is not evidence that content was reviewed. content_reviewed=true requires every scoped sample to contain non-empty reference_text and human_review_status=completed. ASR-prefilled text is not a human reference.

## Transcript metrics

The router compares normalized-transcript.json, postprocessed-transcript.json, and corrected-transcript.json:

- segment count
- punctuation per 100 characters
- average and P95 segment length
- timeline coverage
- content fingerprint
- punctuation-stripped character preservation

only_punctuation_or_segmentation_changed=true requires exact equality after whitespace and punctuation are removed. A preservation ratio below 0.995 is classified as text_mutation.

## Visual stages

OCR evidence counts only visual_text or structured_visual on document_visual/mixed items. Vision evidence counts only visual_understanding or temporal_visual_understanding on semantic/temporal/mixed items.

No expected items, or vision intentionally not executed, is stopped_by_design, not success and not an instruction to call a cloud model.

## Artifacts

- offline-quality-route.json/md
- routing-proposal.json/md
- review-page-machine-summary.json/md

The proposal never modifies production configuration.