# Balanced Multimodal Escalation Gate Implementation Plan

> **Implementation owner:** Codex. Execute test-first and preserve existing queue, preflight, consent, and Bundle contracts.

**Goal:** Select only the artifacts that gain material value from multimodal analysis after local OCR, while suppressing simple high-confidence documents, static presenter-only frame groups, and duplicate pages.

**Architecture:** Extend the existing `vision_review_triage` scorer with additive, auditable signals instead of creating another router. Run the same triage a second time after local ebook/OCR/crop/tile stages so successful OCR can suppress unnecessary model work and complex layouts or conflicts can still escalate. All output remains a plan; existing preflight, consent, destination, and execution gates remain authoritative.

**Tech Stack:** Python 3.11+, Pillow for optional local perceptual frame checks, pytest, existing VKP Timeline/Bundle JSON contracts.

**Decision record:** Approved by the user on 2026-07-19. Recorded by Codex (GPT-5) at 2026-07-19 12:46:16 +08:00.

---

### Task 1: Lock the balanced selection behavior with tests

**Files:**
- Create: `tests/test_vision_escalation_gate.py`
- Modify: `tests/test_targeted_visual_evidence.py`

**Step 1: Write failing triage tests**

Cover these fixed cases:

- simple, high-confidence OCR with a resolved structure produces no multimodal candidate;
- a chat/diagram/arrow/highlight layout escalates to single-frame semantic review even when OCR is complete;
- an explicit ASR/OCR or named-entity conflict escalates to semantic review;
- a frame group whose main content changes becomes temporal review;
- an explicitly located presenter/PIP region may appear at any position and size; unknown localized motion is not automatically labelled as presenter;
- an adjacent near-duplicate page is linked to the first representative and is not charged as another model call.

Every candidate assertion must cover `selected_action`, `benefit_reasons`, `suppression_reasons`, `frame_change`, `estimated_images`, `estimated_calls`, and `recommended_execution_location`.

**Step 2: Run tests and confirm failure**

Run:

```powershell
python -m pytest -q tests/test_vision_pipeline.py -k "vision_review_triage"
```

Expected: new assertions fail because the v2 audit fields and perceptual gate do not exist.

### Task 2: Implement additive balanced triage policy

**Files:**
- Create: `src/video_knowledge_pipeline/vision_escalation_gate.py`
- Modify: `src/video_knowledge_pipeline/vision_review_triage.py`

**Step 1: Add local evidence extractors**

Implement helpers for:

- numeric OCR confidence from top-level or nested OCR/structured fields;
- explicit source conflicts and existing mismatch issues;
- relational-layout signals such as chat bubbles, arrows, highlights, diagrams, flows, multi-column layouts, and UI role relationships;
- optional local frame dynamics using an adaptive grid plus explicit normalized presenter/PIP/overlay regions without a fixed-position assumption;
- adjacent page fingerprints used only for candidate de-duplication.

Unreadable images must return `not_available`; they must never crash triage or cause an online fallback.

**Step 2: Apply the balanced decision rules**

- resolved high-confidence simple OCR suppresses model work;
- missing/low-confidence OCR stays on the local document route first;
- complex relational layouts and explicit source conflicts select single-frame multimodal;
- verified broad main-content change or a scene boundary selects temporal multimodal;
- localized motion requires operation/process language; missing temporal frames route to local recapture instead of a model call;
- static or explicit presenter/PIP-only groups cannot select temporal merely because the transcript contains operation words;
- duplicate adjacent pages retain the evidence-strongest representative, inherit `duplicate_of`, and contribute zero estimated calls.

Keep legacy queue fields and add the v2 audit fields without accepting provider or execution overrides.

**Step 3: Run focused triage tests**

Run:

```powershell
python -m pytest -q tests/test_vision_pipeline.py -k "vision_review_triage"
```

Expected: pass.

### Task 3: Re-evaluate after local OCR

**Files:**
- Modify: `src/video_knowledge_pipeline/targeted_visual_evidence.py`
- Modify: `tests/test_targeted_visual_evidence.py`

**Step 1: Write the failing post-local test**

Simulate local OCR resolving a document. Assert that triage runs again, the resolved simple page is removed from the model queue, and a resolved complex layout may remain as a one-image semantic candidate.

**Step 2: Implement post-local triage**

Preserve the initial document queue for local processing, then re-run triage against the updated Timeline. Build final semantic/temporal queues from the post-local result plus unresolved documents. Report pre-local and post-local selection counts separately.

**Step 3: Verify**

Run:

```powershell
python -m pytest -q tests/test_targeted_visual_evidence.py
```

Expected: pass; no online execution occurs.

### Task 4: Document and regress

**Files:**
- Modify: `docs/frame-sampling-strategy.md`
- Modify: `AGENT_DISCOVERY.md`

**Step 1: Document the production gate**

Record the OCR-first, semantic-escalation, verified-temporal, duplicate-suppression, and audit-field behavior. State that routing creates candidates only and does not grant upload authorization.

**Step 2: Run verification**

Run:

```powershell
python -m pytest -q tests/test_vision_pipeline.py -k "vision_review_triage"
python -m pytest -q tests/test_targeted_visual_evidence.py tests/test_vision_review_queue.py
python -m compileall -q src
python -m pytest -q
git diff --check
```

Expected: all focused tests and the full suite pass; compileall and diff checks are clean.

**Step 3: Commit the scoped checkpoint**

Stage only the plan, triage implementation, targeted-evidence implementation, focused tests, and documentation. Do not stage unrelated user changes and do not push.

## Implementation outcome

Completed by Codex (GPT-5) on 2026-07-19:

- Added the isolated local gate module and integrated it into the existing triage scorer.
- Added static/presenter-only suppression, scene-boundary evidence, OCR confidence, complex-layout escalation, duplicate-page suppression, and call/image estimates.
- Added post-local re-triage after executed ebook/OCR/crop/tile stages.
- Added the open-source implementation research document.
- Focused regression: `23 passed, 30 deselected`.
- Full offline regression: `874 passed, 1 warning`.
- No provider call, upload, download, service start, or external-account change occurred.
