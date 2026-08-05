# Smart Summary Best Practices

Updated: 2026-07-04 12:42:00 | Codex / GPT-5

This note documents the target design for VKP's `smart-summary.md`. It is based on the local implementation work in `video-knowledge-pipeline`, previously reviewed open-source projects, and current public documentation/research on long-document and video understanding.

## Goal

`smart-summary.md` should be the readable learning note layer.

It is not:

- a raw transcript;
- an extraction audit;
- a frame/OCR dump;
- a generic one-shot "summarize this video" output.

It should be a finished Markdown note that a human can read, review, copy into a knowledge base, and use for learning or content reuse.

Current output layers:

| Artifact | Role |
| --- | --- |
| `knowledge-note.md` | Evidence and audit-oriented note. |
| `full-transcript.md` | Full transcript layer. |
| `smart-summary.md` | GetBrain-style readable smart summary. |
| `smart-summary.codex.md` | Local Codex-style final summary used by exporter when present. |
| `smart-summary-input-pack.md/json` | Corrected transcript, term, and visual evidence input layer. |

## Core Principle

The best architecture is not `ASR -> summary`.

It should be:

```text
raw ASR / subtitles
        |
        v
term arbitration + punctuation + corrected transcript
        |
        +-- OCR / ebook courseware digest
        +-- tagger timeline and topic labels
        +-- multimodal difficult-point review
        +-- metadata: title / description / chapter hints
        |
        v
chapter builder
time + semantic + slide/page changes
        |
        v
chapter summaries
what was said / what was shown / key ideas / actions / reusable expressions / review gaps
        |
        v
global synthesis
main course line / methodology / key models / action list
        |
        v
smart-summary.md
        |
        v
quality gate
coverage / readability / evidence / uncertainty boundaries / no ASR dump
```

## Model Layer Policy

VKP should not pretend that a rule-based extractor is enough for the final smart-summary layer. A good `smart-summary.md` needs a synthesis model when the material is long, concept-dense, or visually mixed.

Current priority:

1. Use Codex as the first LLM substitute: build evidence packs locally, ask Codex to synthesize, then install/validate `smart-summary.codex.md`.
2. Keep online/cloud LLM providers as valid next integrations when quality, scale, or automation requires them.
3. Do not let model output bypass evidence boundaries: every model path must consume the same transcript, chapter evidence, OCR/ebook, multimodal, tagger, and review inputs.
4. Do not mark purely local scaffold text as equivalent to a reviewed LLM synthesis unless the quality gate passes and uncertainty boundaries remain visible.
## Evidence Independence

The first pass of each evidence branch should be independent:

- ASR/subtitle extraction should complete without being constrained by frames.
- Local frame extraction should complete without being constrained by ASR confidence.
- ebook/OCR should parse document-like frames without waiting for multimodal analysis.
- Tagger annotations should keep their own time and label evidence.
- Multimodal review should only resolve selected hard visual cases unless explicitly running full visual review.

Fusion happens after each branch has preserved its own raw evidence. This prevents early errors in one branch from suppressing useful evidence in another.

## Corrected Transcript First

`smart-summary.md` should primarily consume a corrected transcript, not raw ASR.

Correction should use:

- raw ASR;
- platform subtitles if available;
- OCR/ebook text from slides, tables, code, and formulas;
- multimodal visual evidence for screen state or ambiguous terms;
- video/page title, description, chapter text, and known glossary;
- human review notes when present.

High-confidence term decisions should be applied to final human-readable outputs. Low-confidence decisions should remain in `待复核点`.
For tool names and domain terms that need semantic judgment, run `term-arbitration-codex` after `resolve-terms` and before `transcript-source-arbitration`:

```powershell
.\scripts\video-knowledge.ps1 resolve-terms <webui-bundle>
.\scripts\video-knowledge.ps1 term-arbitration-codex <webui-bundle>
# Fast local Codex-substitute path: import only high-confidence draft replacements; ambiguous terms stay review-only.
.\scripts\video-knowledge.ps1 term-arbitration-codex <webui-bundle> --accept-draft
# Manual Codex review path: review term-arbitration-codex-prompt.md, save term-arbitration-codex-result.codex.md, validate it, then run the closure:
.\scripts\video-knowledge.ps1 validate-term-arbitration-codex-result <webui-bundle> --input-json <term-arbitration-codex-result.codex.md>
.\scripts\video-knowledge.ps1 term-correction-status <webui-bundle>
.\scripts\video-knowledge.ps1 term-correction-closure <webui-bundle> --input-json <term-arbitration-codex-result.codex.md>
.\scripts\video-knowledge.ps1 term-correction-impact-report <webui-bundle>
.\scripts\video-knowledge.ps1 transcript-source-arbitration <webui-bundle> --glossary-json <webui-bundle>\term-arbitration-glossary.json
```

This is the Codex-first replacement for an online terminology LLM. It combines ASR, platform subtitles, OCR/ebook, visual evidence, tagger labels, and topic context into a reviewable prompt. Reviewed Codex/LLM responses must pass `validate-term-arbitration-codex-result` before import; `term-correction-closure --input-json` repeats that validation and stops without writing `term-arbitration-glossary.json` or `source-arbitrated-transcript.json` when the response is invalid or has no accepted decisions. Ambiguous terms stay review-only. `--accept-draft` is the local Codex-substitute shortcut: it writes `term-arbitration-codex-result.json` with `source=codex_substitute_local_draft` only for draft decisions that already satisfy `action=replace`, confidence threshold, and `needs_human_review=false`.


### Terminology Impact Gate

Codex term arbitration is not only a glossary-building step. It is the local LLM substitute for semantic tool-name/domain-term judgment, and its decisions must be checked against final human-readable outputs.

After Codex term arbitration changes any tool name or domain term, run the closure command or at least the impact report before treating `smart-summary.md` as final:

```powershell
.\scripts\video-knowledge.ps1 term-correction-status <webui-bundle>
.\scripts\video-knowledge.ps1 term-correction-closure <webui-bundle> --input-json <term-arbitration-codex-result.codex.md>
.\scripts\video-knowledge.ps1 term-correction-impact-report <webui-bundle>
.\scripts\video-knowledge.ps1 generate-smart-summary-with-codex <webui-bundle> --input-md <reviewed-smart-summary.md>
.\scripts\video-knowledge.ps1 export-knowledge-note <webui-bundle>
```

The smart-summary quality gate treats unfinished terminology impact as blocking. If `term-arbitration-codex-result.json`, `term-arbitration-glossary.json`, high-confidence transcript arbitration changes, or term correction artifacts exist, `term-correction-impact-report` must show `final_export_alias_total=0`; otherwise the readable summary remains failed/needs-fix instead of silently carrying wrong tool names.
## Chaptering Strategy

A good summary needs meaningful chapters before it needs prettier wording.

Recommended chapter signals:

- transcript semantic shifts;
- slide/title changes from OCR/ebook;
- tagger labels such as `步骤`, `案例`, `结论`, `工具名`, `价格`, `风险`;
- long pauses or speaker transitions if available;
- repeated topic terms;
- visual route changes, especially `document_visual` and `mixed`.

Long videos should avoid fixed "first N frames" or "first N transcript chunks" coverage. Chaptering must cover the whole duration.

## Summary Generation Pattern

Use layered generation:

1. Build local evidence packs.
2. Generate chapter summaries.
3. Generate global course map.
4. Generate final smart summary from both chapter summaries and global map.
5. Run quality checks.
6. If quality fails, re-run targeted chapter synthesis or ask for human review.

Each chapter should have:

| Field | Description |
| --- | --- |
| Time range | Start/end timestamps for navigation. |
| What was said | Compressed teaching content, not transcript copy. |
| What was shown | OCR/ebook/multimodal visual information. |
| Key ideas | Claims, principles, distinctions, frameworks. |
| Actions | Concrete steps the learner can take. |
| Reusable expressions | Useful phrases, scripts, examples, analogies. |
| Review gaps | ASR/OCR/visual uncertainties. |

## Final Markdown Structure

Recommended `smart-summary.md`:

```text
# Title - 智能总结

生成方式 / evidence boundary

## 基本信息
video title, duration, source, transcript source, visual status

## 一句话概览
one readable sentence explaining what problem this video solves

## 课程地图 / 核心主线
3-7 top-level topics and their relationship

## 分段总结
chapter summaries with timestamps and visual/courseware supplements

## 关键观点 / 方法论
timestamped principles and frameworks

## 可执行动作清单
what the learner should do after watching

## 高频话术 / 可复用表达
quotes or rewritten scripts for review

## 术语纠错
high-confidence replacements and uncertain terms

## 待复核点 / 低置信内容
ASR, OCR, visual, fact, privacy, or compliance gaps
```

## Quality Gate

The final summary should pass these checks:

| Check | Requirement |
| --- | --- |
| Full duration coverage | Summary timestamps reach at least 85% of transcript duration, ideally the true end. |
| No fake coverage | Processing timestamps like `2026-07-04T12:30:07` must not count as video timestamps. |
| Readable overview | The one-sentence overview must not be ASR keyword stitching. |
| No ASR dump | Chapter sections should not contain long copied transcript blocks. |
| Balanced coverage | Key ideas, actions, and expressions should include early, middle, and late content. |
| Visual boundary | If visual/multimodal evidence was not executed, say so clearly. |
| Evidence-aware | Important screen/PPT/table/formula evidence should appear in relevant chapters. |
| Review-safe | Low-confidence terms and unverified claims remain review items. |

## What to Reuse From Reviewed Projects

| Source | Useful pattern | Boundary |
| --- | --- | --- |
| BiliNote | Video note workflow, transcription readiness checks, familiar UX. | Not enough evidence audit or multi-source conflict handling. |
| AI-Video-Transcriber | Local ASR workflow and parameter UI patterns. | Transcription-first, not full knowledge synthesis. |
| Peepshow | Frame reports and visual inspection workflow. | Not a course knowledge summarizer. |
| Marker / MinerU / ebook pipeline | Document-like frame parsing for slides, tables, code, formulas. | Not a general video visual understanding engine. |
| LangChain-style map/reduce/refine | Chunk summary then merge pattern. | Needs VKP-specific timestamps, visual evidence, and quality gates. |
| Gemini / Twelve Labs style video APIs | True video understanding and timestamp-aware video QA. | Should be gated by privacy/cost/preflight; not default all-frame upload. |

## External Best-Practice Notes

Long document summarization research repeatedly points toward hierarchical strategies: local summaries preserve details, while higher-level summaries preserve global structure. For VKP this maps to chapter summaries plus a course-level synthesis layer.

RAG research also supports building a global semantic representation before local retrieval/generation, because isolated chunk summaries can miss the full course line.

Official model documentation supports structured prompt/context design and timestamp-aware video understanding, but VKP should still preserve local evidence and explicit review boundaries before using cloud models.

Reference links:

- Long Document Summarization with Top-down and Bottom-up Inference: https://arxiv.org/abs/2203.07586
- Mindscape-Aware RAG for long-context understanding: https://arxiv.org/abs/2512.17220
- Gemini video understanding docs: https://ai.google.dev/gemini-api/docs/video-understanding
- OpenAI prompt engineering docs: https://platform.openai.com/docs/guides/prompt-engineering

## Implementation Direction

Near-term VKP implementation should focus on:

1. Improve `corrected-transcript.json` generation.
2. Use OCR/ebook headings to improve chapter boundaries.
3. Add chapter-level evidence packs.
4. Generate chapter summaries with Codex first, then online/cloud LLM providers when needed.
5. Generate `course-map.json/md`.
6. Make `smart-summary.codex.md` synthesize from chapter summaries plus course map only when it is produced by Codex/manual LLM or `run-smart-summary-llm-rewrite --execute`; the local scaffold is only `needs_llm_rewrite` and must not be treated as final.
7. Expand `smart-summary-quality-check` with:
   - copied-ASR ratio;
   - chapter coverage;
   - visual evidence usage;
   - term uncertainty count;
   - actionability score.

8. Prefer chapter-level LLM rewriting for long videos. `run-smart-summary-section-llm-rewrite` keeps each request small, preserves chapter coverage, and aggregates through the existing section-apply gate instead of letting one long prompt time out or over-focus on the beginning.
9. Run `postprocess-asr-transcript` after local ASR when the source transcript is fragmentary or lacks punctuation; it should improve `full-transcript.md` readability before any summary model sees the transcript.

The long-term target is a reproducible pipeline:

```text
postprocess-asr-transcript
-> transcript-source-arbitration / transcript-semantic-correction when evidence conflicts exist
-> build-smart-summary-input-pack
-> build-smart-summary-chapters
-> smart-summary-section-workflow
-> run-smart-summary-section-llm-rewrite --execute --provider-config <runtime-json-or-file>
-> smart-summary-quality-check
-> export-knowledge-note
```

## Term Correction Impact Gate

After importing Codex/LLM-reviewed term decisions and regenerating the corrected transcript plus final exports, run:

```powershell
.\scripts\video-knowledge.ps1 term-correction-impact-report <webui-bundle>
```

This report is local-only and does not call a model. It compares reviewed glossary aliases against source ASR/timeline text, corrected transcript, `full-transcript.md`, and `smart-summary.md`. A `passed` status means reviewed aliases were present in source material but no longer remain in corrected/final human-readable outputs. Raw evidence fields are intentionally not treated as final residuals.
