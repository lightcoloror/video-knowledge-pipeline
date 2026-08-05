from __future__ import annotations

import difflib
import hashlib
import re
from pathlib import Path
from typing import Any

from .models import now_iso
from .storage import bundle_write_lock, read_json, write_json
from .transcript import format_timestamp, parse_transcript


PACK_SCHEMA = "video_knowledge_pipeline.asr_diff_adjudication_pack.v1"
RESULT_SCHEMA = "video_knowledge_pipeline.asr_diff_adjudication_result.v1"
TRANSCRIPT_SCHEMA = "video_knowledge_pipeline.asr_consensus_patched_transcript.v1"
_TOKEN_RE = re.compile(r"[一-鿿]|[A-Za-z]+(?:[-_.][A-Za-z0-9]+)*|\d+(?:\.\d+)?|[^\s]", re.UNICODE)


def build_asr_diff_adjudication(
    bundle_dir: str | Path,
    *,
    consensus_json: str | Path | None = None,
    cluster_token_gap: int = 6,
    write: bool = True,
) -> dict[str, Any]:
    """Build positioned, clustered and source-anonymous ASR disagreements."""

    root = Path(bundle_dir).expanduser().resolve()
    consensus_path = _bundle_path(root, consensus_json or "asr-consensus.json")
    consensus = read_json(consensus_path)
    if not isinstance(consensus, dict):
        raise ValueError("asr-consensus.json must be a JSON object")

    differences: list[dict[str, Any]] = []
    clusters: list[dict[str, Any]] = []
    for window in consensus.get("windows") or []:
        if not isinstance(window, dict) or window.get("status") != "conflict":
            continue
        primary_text = str(window.get("primary_text") or "")
        secondary_text = str(window.get("secondary_text") or "")
        window_diffs = _positioned_differences(window, primary_text, secondary_text)
        differences.extend(window_diffs)
        clusters.extend(_cluster_differences(window, window_diffs, max_gap=max(0, int(cluster_token_gap))))

    pack = {
        "schema": PACK_SCHEMA,
        "bundle_dir": str(root),
        "consensus_json": str(consensus_path),
        "primary_transcript": str(consensus.get("primary_transcript") or ""),
        "secondary_transcript": str(consensus.get("secondary_transcript") or ""),
        "status": "ready_for_adjudication" if clusters else "no_positioned_conflicts",
        "ok": True,
        "difference_count": len(differences),
        "cluster_count": len(clusters),
        "differences": differences,
        "clusters": clusters,
        "decision_schema": {
            "rows": [
                {
                    "diff_id": "<diff-id>",
                    "choice": "A | B | keep_primary",
                    "confidence": "0..1",
                    "evidence_refs": ["audio clip or other evidence path"],
                    "reason": "short evidence-based reason",
                }
            ]
        },
        "operator_boundary": {
            "candidate_sources_anonymous": True,
            "raw_hypotheses_preserved": True,
            "does_not_apply_patches": True,
            "no_llm_or_cloud_call": True,
            "changing_patch_requires_evidence": True,
        },
        "artifacts": {
            "json": "asr-consensus-adjudication-pack.json",
            "markdown": "asr-consensus-adjudication-pack.md",
            "todo_json": "asr-consensus-adjudication.todo.json",
        },
        "updated_at": now_iso(),
    }
    if write:
        root.mkdir(parents=True, exist_ok=True)
        with bundle_write_lock(root, operation="asr_diff_adjudication_pack", timeout_seconds=1.0):
            write_json(root / "asr-consensus-adjudication-pack.json", pack)
            (root / "asr-consensus-adjudication-pack.md").write_text(_render_pack_markdown(pack), encoding="utf-8")
            write_json(
                root / "asr-consensus-adjudication.todo.json",
                {
                    "schema": "video_knowledge_pipeline.asr_diff_adjudication_decisions.v1",
                    "consensus_json": str(consensus_path),
                    "rows": [
                        {
                            "diff_id": row["diff_id"],
                            "choice": "",
                            "confidence": None,
                            "evidence_refs": [],
                            "reason": "",
                        }
                        for row in differences
                    ],
                },
            )
            manifest_path = root / "manifest.json"
            manifest = read_json(manifest_path) if manifest_path.exists() else {}
            if isinstance(manifest, dict):
                manifest["asr_consensus_adjudication_pack_json"] = "asr-consensus-adjudication-pack.json"
                manifest["asr_consensus_adjudication_pack_markdown"] = "asr-consensus-adjudication-pack.md"
                manifest["asr_consensus_adjudication_todo_json"] = "asr-consensus-adjudication.todo.json"
                write_json(manifest_path, manifest)
    return pack


def apply_asr_diff_adjudication(
    bundle_dir: str | Path,
    *,
    decisions_json: str | Path,
    pack_json: str | Path | None = None,
    min_confidence: float = 0.75,
    require_evidence: bool = True,
    promote: bool = False,
    write: bool = True,
) -> dict[str, Any]:
    """Validate and apply local ASR patches without modifying raw transcripts."""

    root = Path(bundle_dir).expanduser().resolve()
    pack_path = _bundle_path(root, pack_json or "asr-consensus-adjudication-pack.json")
    decisions_path = _bundle_path(root, decisions_json)
    pack = read_json(pack_path)
    decisions = read_json(decisions_path)
    if not isinstance(pack, dict) or not isinstance(decisions, dict):
        raise ValueError("pack and decisions must be JSON objects")

    diff_by_id = {
        str(row.get("diff_id") or ""): row
        for row in pack.get("differences") or []
        if isinstance(row, dict) and row.get("diff_id")
    }
    decision_rows = _decision_rows(decisions)
    accepted: list[dict[str, Any]] = []
    no_change: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []
    occupied: dict[int, list[tuple[int, int]]] = {}
    for decision in decision_rows:
        diff_id = str(decision.get("diff_id") or "")
        diff = diff_by_id.get(diff_id)
        if not diff:
            rejected.append({"diff_id": diff_id, "reason": "unknown_diff_id"})
            continue
        resolved = _resolve_choice(diff, str(decision.get("choice") or ""))
        if resolved is None:
            rejected.append({"diff_id": diff_id, "reason": "invalid_choice"})
            continue
        confidence = _float(decision.get("confidence"))
        evidence_refs = [str(value) for value in decision.get("evidence_refs") or [] if str(value).strip()]
        primary_text = str(diff.get("primary_text") or "")
        chosen_text = str(resolved)
        if chosen_text == primary_text:
            no_change.append({"diff_id": diff_id, "status": "adjudicated_no_change", "choice": decision.get("choice"), "confidence": confidence})
            continue
        if confidence < float(min_confidence):
            rejected.append({"diff_id": diff_id, "reason": "confidence_below_threshold", "confidence": confidence})
            continue
        if require_evidence and not evidence_refs:
            rejected.append({"diff_id": diff_id, "reason": "evidence_required"})
            continue
        segment_index = int(diff.get("primary_segment_index") or 0)
        start = int(diff.get("primary_char_start") or 0)
        end = int(diff.get("primary_char_end") or start)
        if any(not (end <= left or start >= right) for left, right in occupied.setdefault(segment_index, [])):
            rejected.append({"diff_id": diff_id, "reason": "overlapping_patch"})
            continue
        occupied[segment_index].append((start, end))
        accepted.append(
            {
                "diff_id": diff_id,
                "segment_index": segment_index,
                "start": start,
                "end": end,
                "expected_text": primary_text,
                "replacement_text": chosen_text,
                "confidence": confidence,
                "evidence_refs": evidence_refs,
                "reason": str(decision.get("reason") or ""),
            }
        )

    primary_path = Path(str(pack.get("primary_transcript") or "")).expanduser()
    if not primary_path.exists():
        raise FileNotFoundError(f"primary transcript not found: {primary_path}")
    cues = parse_transcript(primary_path)
    by_segment: dict[int, list[dict[str, Any]]] = {}
    for patch in accepted:
        by_segment.setdefault(int(patch["segment_index"]), []).append(patch)
    segments: list[dict[str, Any]] = []
    applied: list[dict[str, Any]] = []
    for index, cue in enumerate(cues):
        original = str(cue.text or "")
        text = original
        for patch in sorted(by_segment.get(index, []), key=lambda row: int(row["start"]), reverse=True):
            start = int(patch["start"])
            end = int(patch["end"])
            expected = str(patch["expected_text"])
            if text[start:end] != expected:
                rejected.append({"diff_id": patch["diff_id"], "reason": "base_span_mismatch", "found_text": text[start:end]})
                continue
            text = text[:start] + str(patch["replacement_text"]) + text[end:]
            applied.append(patch)
        segments.append(
            {
                "index": index + 1,
                "start": float(cue.start),
                "end": float(cue.end),
                "text": text,
                "original_text": original,
                "changed": text != original,
                "source": "asr_diff_adjudication",
            }
        )

    transcript_payload = {
        "schema": TRANSCRIPT_SCHEMA,
        "source": "asr_diff_adjudication",
        "base_transcript": str(primary_path.resolve()),
        "updated_at": now_iso(),
        "summary": {
            "segments": len(segments),
            "applied_patches": len(applied),
            "adjudicated_no_change": len(no_change),
            "rejected": len(rejected),
            "promoted": bool(promote),
        },
        "patches": applied,
        "segments": segments,
    }
    result = {
        "schema": RESULT_SCHEMA,
        "bundle_dir": str(root),
        "status": "completed" if not rejected else "completed_with_rejections",
        "ok": bool(applied or no_change) and not rejected,
        "pack_json": str(pack_path),
        "decisions_json": str(decisions_path),
        "accepted_patches": applied,
        "adjudicated_no_change": no_change,
        "rejected": rejected,
        "summary": transcript_payload["summary"],
        "operator_boundary": {
            "raw_hypotheses_preserved": True,
            "only_positioned_patches_applied": True,
            "evidence_required_for_changes": bool(require_evidence),
            "promotion_explicit": True,
        },
        "artifacts": {
            "json": "asr-consensus-adjudication-result.json",
            "markdown": "asr-consensus-adjudication-result.md",
            "patched_transcript": "asr-consensus-patched-transcript.json",
            "promoted_transcript": "source-arbitrated-transcript.json" if promote else "",
        },
        "updated_at": now_iso(),
    }
    if write:
        with bundle_write_lock(root, operation="apply_asr_diff_adjudication", timeout_seconds=1.0):
            write_json(root / "asr-consensus-patched-transcript.json", transcript_payload)
            write_json(root / "asr-consensus-adjudication-result.json", result)
            (root / "asr-consensus-adjudication-result.md").write_text(_render_result_markdown(result), encoding="utf-8")
            manifest_path = root / "manifest.json"
            manifest = read_json(manifest_path) if manifest_path.exists() else {}
            if isinstance(manifest, dict):
                manifest["asr_consensus_patched_transcript_json"] = "asr-consensus-patched-transcript.json"
                manifest["asr_consensus_adjudication_result_json"] = "asr-consensus-adjudication-result.json"
                if promote:
                    promoted_payload = {**transcript_payload, "schema": "video_knowledge_pipeline.source_arbitrated_transcript.v1"}
                    write_json(root / "source-arbitrated-transcript.json", promoted_payload)
                    manifest["source_arbitrated_transcript_json"] = "source-arbitrated-transcript.json"
                    manifest["corrected_transcript_json"] = "source-arbitrated-transcript.json"
                    manifest["corrected_transcript_source"] = "asr_diff_adjudication"
                write_json(manifest_path, manifest)
    return result


def _positioned_differences(window: dict[str, Any], primary_text: str, secondary_text: str) -> list[dict[str, Any]]:
    primary_tokens = _tokens(primary_text)
    secondary_tokens = _tokens(secondary_text)
    matcher = difflib.SequenceMatcher(
        a=[row["normalised"] for row in primary_tokens],
        b=[row["normalised"] for row in secondary_tokens],
        autojunk=False,
    )
    rows: list[dict[str, Any]] = []
    primary_index = int(window.get("primary_index") or 0)
    for ordinal, (operation, a0, a1, b0, b1) in enumerate(matcher.get_opcodes(), start=1):
        if operation == "equal":
            continue
        start_char, end_char = _char_span(primary_tokens, a0, a1, len(primary_text))
        secondary_start, secondary_end = _char_span(secondary_tokens, b0, b1, len(secondary_text))
        diff_id = f"{window.get('window_id')}-diff-{ordinal:03d}"
        primary_piece = primary_text[start_char:end_char]
        secondary_piece = secondary_text[secondary_start:secondary_end]
        if not primary_piece and not secondary_piece:
            continue
        if _fact_normalise(primary_piece) == _fact_normalise(secondary_piece):
            continue
        rows.append(
            {
                "diff_id": diff_id,
                "window_id": str(window.get("window_id") or ""),
                "operation": operation,
                "primary_segment_index": primary_index,
                "secondary_segment_index": window.get("secondary_index"),
                "primary_token_start": a0,
                "primary_token_end": a1,
                "secondary_token_start": b0,
                "secondary_token_end": b1,
                "primary_char_start": start_char,
                "primary_char_end": end_char,
                "secondary_char_start": secondary_start,
                "secondary_char_end": secondary_end,
                "primary_text": primary_piece,
                "secondary_text": secondary_piece,
                "left_context": primary_text[max(0, start_char - 40):start_char],
                "right_context": primary_text[end_char:end_char + 40],
                "estimated_time": _estimated_diff_time(window, a0, a1, len(primary_tokens)),
            }
        )
    return rows


def _cluster_differences(window: dict[str, Any], differences: list[dict[str, Any]], *, max_gap: int) -> list[dict[str, Any]]:
    if not differences:
        return []
    groups: list[list[dict[str, Any]]] = []
    current: list[dict[str, Any]] = []
    last_end = -1
    for row in differences:
        start = int(row.get("primary_token_start") or 0)
        if current and start - last_end > max_gap:
            groups.append(current)
            current = []
        current.append(row)
        last_end = int(row.get("primary_token_end") or start)
    if current:
        groups.append(current)

    clusters: list[dict[str, Any]] = []
    for ordinal, group in enumerate(groups, start=1):
        cluster_id = f"{window.get('window_id')}-cluster-{ordinal:03d}"
        flip = int(hashlib.sha256(cluster_id.encode("utf-8")).hexdigest()[-1], 16) % 2 == 1
        primary = " … ".join(str(row.get("primary_text") or "∅") for row in group)
        secondary = " … ".join(str(row.get("secondary_text") or "∅") for row in group)
        candidate_a, candidate_b = (secondary, primary) if flip else (primary, secondary)
        for item in group:
            item["cluster_id"] = cluster_id
            item["candidate_a_text"] = str(item.get("secondary_text") if flip else item.get("primary_text") or "")
            item["candidate_b_text"] = str(item.get("primary_text") if flip else item.get("secondary_text") or "")
        start = min(float((row.get("estimated_time") or {}).get("start") or window.get("start") or 0) for row in group)
        end = max(float((row.get("estimated_time") or {}).get("end") or window.get("end") or start) for row in group)
        clusters.append(
            {
                "cluster_id": cluster_id,
                "window_id": str(window.get("window_id") or ""),
                "diff_ids": [str(row.get("diff_id") or "") for row in group],
                "time_range": f"{format_timestamp(start)} - {format_timestamp(end)}",
                "candidate_a": candidate_a,
                "candidate_b": candidate_b,
                "context_before": str(group[0].get("left_context") or ""),
                "context_after": str(group[-1].get("right_context") or ""),
                "audio_review_window": dict(window.get("audio_review_window") or {}),
                "instruction": "只根据音频和证据选择 A、B 或 keep_primary；不得改写争议范围外文本。",
            }
        )
    return clusters


def _decision_rows(decisions: dict[str, Any]) -> list[dict[str, Any]]:
    rows = decisions.get("rows") or []
    return [row for row in rows if isinstance(row, dict)]


def _resolve_choice(diff: dict[str, Any], choice: str) -> str | None:
    value = choice.strip().upper()
    if value in {"KEEP_PRIMARY", "PRIMARY", "NO_CHANGE"}:
        return str(diff.get("primary_text") or "")
    if value == "A":
        return str(diff.get("candidate_a_text") or "")
    if value == "B":
        return str(diff.get("candidate_b_text") or "")
    return None


def _fact_normalise(text: str) -> str:
    return re.sub(r"[^\w]+", "", str(text or ""), flags=re.UNICODE).casefold()


def _tokens(text: str) -> list[dict[str, Any]]:
    return [
        {"text": match.group(0), "normalised": match.group(0).casefold(), "start": match.start(), "end": match.end()}
        for match in _TOKEN_RE.finditer(text)
    ]


def _char_span(tokens: list[dict[str, Any]], start: int, end: int, text_length: int) -> tuple[int, int]:
    if start < end and start < len(tokens):
        return int(tokens[start]["start"]), int(tokens[min(end - 1, len(tokens) - 1)]["end"])
    position = int(tokens[start]["start"]) if start < len(tokens) else text_length
    return position, position


def _estimated_diff_time(window: dict[str, Any], start: int, end: int, token_count: int) -> dict[str, float]:
    segment_start = float(window.get("primary_start") if window.get("primary_start") is not None else window.get("start") or 0)
    segment_end = float(window.get("primary_end") if window.get("primary_end") is not None else window.get("end") or segment_start)
    duration = max(0.001, segment_end - segment_start)
    count = max(1, token_count)
    return {
        "start": round(segment_start + duration * start / count, 3),
        "end": round(segment_start + duration * max(start + 1, end) / count, 3),
    }


def _bundle_path(root: Path, value: str | Path) -> Path:
    path = Path(value).expanduser()
    if not path.is_absolute():
        path = root / path
    if not path.exists():
        raise FileNotFoundError(f"artifact not found: {path}")
    return path.resolve()


def _float(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _render_pack_markdown(pack: dict[str, Any]) -> str:
    lines = [
        "# ASR Difference Adjudication Pack",
        "",
        f"- Status: `{pack.get('status')}`",
        f"- Positioned differences: `{pack.get('difference_count')}`",
        f"- Clusters: `{pack.get('cluster_count')}`",
        "",
        "## Anonymous Clusters",
        "",
    ]
    for row in pack.get("clusters") or []:
        lines.extend(
            [
                f"### {row.get('cluster_id')} · {row.get('time_range')}",
                "",
                f"- A: {row.get('candidate_a')}",
                f"- B: {row.get('candidate_b')}",
                f"- Context: {row.get('context_before')} **[DIFF]** {row.get('context_after')}",
                f"- Audio: `{(row.get('audio_review_window') or {}).get('clip_path', '')}`",
                "",
            ]
        )
    return "\n".join(lines).rstrip() + "\n"


def _render_result_markdown(result: dict[str, Any]) -> str:
    lines = [
        "# ASR Difference Adjudication Result",
        "",
        f"- Status: `{result.get('status')}`",
        f"- Applied patches: `{len(result.get('accepted_patches') or [])}`",
        f"- Adjudicated without change: `{len(result.get('adjudicated_no_change') or [])}`",
        f"- Rejected: `{len(result.get('rejected') or [])}`",
        "",
    ]
    for row in result.get("rejected") or []:
        lines.append(f"- `{row.get('diff_id')}`: {row.get('reason')}")
    return "\n".join(lines).rstrip() + "\n"