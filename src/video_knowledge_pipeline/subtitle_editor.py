"""Evidence-preserving adapter for the vendored moys-asr-workflow editor.

Intent: reuse MAWE's mature subtitle editor without creating a second ASR,
provider, media, or evidence truth. Decision: project the selected VKP
transcript into an editor-only contract and import only explicit human-reviewed
notes. Reason: MAWE treats its project as subtitle truth, while VKP must retain
raw ASR, Timeline, translations, and evidence unchanged. Evidence: upstream
Moyf/moys-asr-workflow v1.3.1 commit
949bc84058cdae1d9c021c50203e6d2742f9392c. Effective scope: local Bundle
subtitle review and derived subtitle/transcript sidecars only.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from .models import TranscriptCue, now_iso
from .run_artifact_registry import register_bundle_run
from .storage import bundle_write_lock, read_json, write_json
from .transcript_correction_pack import _load_best_transcript
from .transcript_speakers import cue_speaker, cue_speaker_role

PROJECTION_SCHEMA = "video_knowledge_pipeline.subtitle_editor_projection.v1"
REVIEW_SCHEMA = "video_knowledge_pipeline.subtitle_review_notes.v1"
TRACK_SCHEMA = "video_knowledge_pipeline.human_reviewed_subtitle_track.v1"
RECEIPT_SCHEMA = "video_knowledge_pipeline.subtitle_review_apply_receipt.v1"
CORRECTED_SCHEMA = "video_knowledge_pipeline.human_corrected_transcript.v1"


def build_subtitle_editor_projection(
    bundle_dir: str | Path,
    *,
    write: bool = True,
) -> dict[str, Any]:
    root = _require_bundle(bundle_dir)
    manifest = _read_object(root / "manifest.json")
    cues = _load_best_transcript(root, manifest)
    if not cues:
        raise ValueError("subtitle editor requires a non-empty transcript")
    supplemental = _load_supplemental_segment_metadata(root, manifest)
    translations, translation_status = _load_translations(root, manifest)
    segments = [
        _projection_segment(
            cue,
            index=index,
            translation=translations.get(_cue_key(cue, index), ""),
            supplemental=supplemental.get(_cue_key(cue, index), {}),
        )
        for index, cue in enumerate(cues)
    ]
    _validate_projection_segments(segments)
    media_duration_ms = _media_duration_ms(manifest, segments)
    source_payload = {
        "title": str(manifest.get("title") or root.name),
        "segments": segments,
        "translation_status": translation_status,
        "media_duration_ms": media_duration_ms,
    }
    source_sha256 = _sha256_json(source_payload)
    payload: dict[str, Any] = {
        "schema": PROJECTION_SCHEMA,
        "title": str(manifest.get("title") or root.name),
        "bundle_revision": source_sha256,
        "source_sha256": source_sha256,
        "media_url": "/media",
        "media_duration_ms": media_duration_ms,
        "tracks": {
            "source": {"language": _source_language(manifest), "editable": True, "status": "ready"},
            "mandarin": {"language": "zh-CN", "editable": True, "status": translation_status},
        },
        "segments": segments,
        "operator_boundary": {
            "local_only": True,
            "no_provider_execution": True,
            "raw_asr_immutable": True,
            "timeline_immutable": True,
            "formal_apply_required": True,
        },
    }
    payload["projection_sha256"] = _sha256_json(payload)
    if write:
        write_json(root / "subtitle-editor-project.json", payload)
        manifest["subtitle_editor_project_json"] = "subtitle-editor-project.json"
        manifest["subtitle_editor_html"] = "subtitle-editor.html"
        write_json(root / "manifest.json", manifest)
    return payload


def validate_subtitle_review(
    bundle_dir: str | Path,
    review: dict[str, Any] | str | Path,
) -> dict[str, Any]:
    root = _require_bundle(bundle_dir)
    payload = _load_review(review)
    if str(payload.get("schema") or "") != REVIEW_SCHEMA:
        raise ValueError(f"review schema must be {REVIEW_SCHEMA}")
    if payload.get("human_confirmed") is not True:
        raise ValueError("subtitle review must be human_confirmed before formal apply")
    current = build_subtitle_editor_projection(root, write=False)
    if str(payload.get("projection_sha256") or "") != str(current["projection_sha256"]):
        raise ValueError("projection_sha256 mismatch: Bundle inputs changed; reload the editor")
    if str(payload.get("source_sha256") or "") != str(current["source_sha256"]):
        raise ValueError("source_sha256 mismatch: selected transcript or translation changed")
    rows = payload.get("segments")
    if not isinstance(rows, list) or not rows:
        raise ValueError("subtitle review segments must be a non-empty array")
    normalized = _validate_review_segments(
        rows,
        current["segments"],
        media_duration_ms=int(current["media_duration_ms"]),
    )
    gap_remove = payload.get("gap_remove")
    if gap_remove is not None and not isinstance(gap_remove, dict):
        raise ValueError("gap_remove must be an object when present")
    return {
        "ok": True,
        "schema": REVIEW_SCHEMA,
        "projection_sha256": current["projection_sha256"],
        "source_sha256": current["source_sha256"],
        "segments": normalized,
        "source_segments": current["segments"],
        "gap_remove": gap_remove if isinstance(gap_remove, dict) else None,
        "summary": _review_summary(current["segments"], normalized),
    }


def apply_subtitle_review(
    bundle_dir: str | Path,
    *,
    review_json: dict[str, Any] | str | Path,
    write: bool = True,
) -> dict[str, Any]:
    root = _require_bundle(bundle_dir)
    review_path = None if isinstance(review_json, dict) else Path(review_json).expanduser().resolve()
    review_payload = review_json if isinstance(review_json, dict) else review_path
    validated = validate_subtitle_review(root, review_payload)
    rows = validated["segments"]
    translation_complete = all(bool(str(row.get("mandarin_text") or "").strip()) for row in rows if not row.get("disabled"))
    track_payload = {
        "schema": TRACK_SCHEMA,
        "created_at": now_iso(),
        "source_projection_sha256": validated["projection_sha256"],
        "source_sha256": validated["source_sha256"],
        "translation_status": "complete" if translation_complete else "incomplete",
        "segments": rows,
        "gap_remove": validated.get("gap_remove"),
        "operator_boundary": {
            "human_confirmed": True,
            "raw_asr_immutable": True,
            "timeline_immutable": True,
            "subtitle_boundaries_are_derived": True,
        },
    }
    original_by_source = {
        source_id: segment
        for segment in validated["source_segments"]
        for source_id in segment["source_segment_ids"]
    }
    corrected_segments = [
        _corrected_segment(row, index, original_by_source=original_by_source)
        for index, row in enumerate(rows)
    ]
    corrected_payload = {
        "schema": CORRECTED_SCHEMA,
        "source": "human_subtitle_editor",
        "created_at": now_iso(),
        "source_projection_sha256": validated["projection_sha256"],
        "summary": {
            **validated["summary"],
            "segments": len(rows),
            "corrected_segments": validated["summary"]["source_text_changes"],
            "indexes_preserved": True,
        },
        "segments": corrected_segments,
    }
    source_srt = _render_srt(rows, field="source_text")
    mandarin_srt = _render_srt(rows, field="mandarin_text") if translation_complete else ""
    source_vtt = _render_vtt(rows, field="source_text")
    mandarin_vtt = _render_vtt(rows, field="mandarin_text") if translation_complete else ""
    source_ass = _render_ass(rows, field="source_text")
    mandarin_ass = _render_ass(rows, field="mandarin_text") if translation_complete else ""
    kept_ranges = _kept_ranges(rows, validated.get("gap_remove"))
    otio_payload = _render_otio_plan(rows, translation_complete=translation_complete)
    ffconcat_text = _render_ffconcat_plan(kept_ranges)
    receipt: dict[str, Any] = {
        "schema": RECEIPT_SCHEMA,
        "created_at": now_iso(),
        "status": "completed",
        "review_json": str(review_path) if review_path is not None else "loopback-request",
        "review_sha256": (
            _sha256_bytes(review_path.read_bytes())
            if review_path is not None
            else _sha256_json(review_json)
        ),
        "projection_sha256": validated["projection_sha256"],
        "source_sha256": validated["source_sha256"],
        "summary": validated["summary"],
        "translation_status": track_payload["translation_status"],
        "invalidated_downstream": ["smart_summary", "final_combined_document", "subtitle_exports"],
        "preserved_sources": ["raw_asr", "timeline", "translation_source"],
    }
    result = {
        "ok": True,
        "status": "completed",
        "schema": "video_knowledge_pipeline.apply_subtitle_review.v1",
        "bundle_dir": str(root),
        "summary": validated["summary"],
        "translation_status": track_payload["translation_status"],
        "write": bool(write),
    }
    if not write:
        return result
    with bundle_write_lock(root, operation="apply_subtitle_review"):
        manifest = _read_object(root / "manifest.json")
        write_json(root / "human-reviewed-subtitle-track.json", track_payload)
        write_json(root / "human-corrected-transcript.json", corrected_payload)
        (root / "human-corrected-transcript.md").write_text(
            _render_corrected_markdown(corrected_payload), encoding="utf-8"
        )
        (root / "human-reviewed-source.srt").write_text(source_srt, encoding="utf-8")
        (root / "human-reviewed-source.vtt").write_text(source_vtt, encoding="utf-8")
        (root / "human-reviewed-source.ass").write_text(source_ass, encoding="utf-8")
        write_json(root / "human-reviewed-subtitle.otio.json", otio_payload)
        write_json(
            root / "human-reviewed-kept-ranges.json",
            {
                "schema": "video_knowledge_pipeline.human_reviewed_kept_ranges.v1",
                "created_at": now_iso(),
                "ranges": kept_ranges,
                "execution_authorized": False,
            },
        )
        (root / "human-reviewed.ffconcat").write_text(ffconcat_text, encoding="utf-8")
        if translation_complete:
            (root / "human-reviewed-mandarin.srt").write_text(mandarin_srt, encoding="utf-8")
            (root / "human-reviewed-mandarin.vtt").write_text(mandarin_vtt, encoding="utf-8")
            (root / "human-reviewed-mandarin.ass").write_text(mandarin_ass, encoding="utf-8")
        write_json(root / "subtitle-review-apply-receipt.json", receipt)
        write_json(
            root / "subtitle-review-downstream-stale.json",
            {
                "schema": "video_knowledge_pipeline.subtitle_review_downstream_stale.v1",
                "created_at": now_iso(),
                "projection_sha256": validated["projection_sha256"],
                "stale": receipt["invalidated_downstream"],
                "requires_online_model": False,
                "next_action": "rebuild local transcript exports; regenerate Smart Summary only through an explicitly selected route",
            },
        )
        manifest.update(
            {
                "human_reviewed_subtitle_track_json": "human-reviewed-subtitle-track.json",
                "human_reviewed_source_srt": "human-reviewed-source.srt",
                "human_reviewed_source_vtt": "human-reviewed-source.vtt",
                "human_reviewed_source_ass": "human-reviewed-source.ass",
                "human_reviewed_subtitle_otio_json": "human-reviewed-subtitle.otio.json",
                "human_reviewed_kept_ranges_json": "human-reviewed-kept-ranges.json",
                "human_reviewed_ffconcat": "human-reviewed.ffconcat",
                "human_corrected_transcript_json": "human-corrected-transcript.json",
                "human_corrected_transcript_markdown": "human-corrected-transcript.md",
                "corrected_transcript_json": "human-corrected-transcript.json",
                "subtitle_review_apply_receipt_json": "subtitle-review-apply-receipt.json",
                "subtitle_review_downstream_stale_json": "subtitle-review-downstream-stale.json",
                "smart_summary_status": "stale_after_subtitle_review",
                "final_combined_document_status": "stale_after_subtitle_review",
            }
        )
        if translation_complete:
            manifest["human_reviewed_mandarin_srt"] = "human-reviewed-mandarin.srt"
            manifest["human_reviewed_mandarin_vtt"] = "human-reviewed-mandarin.vtt"
            manifest["human_reviewed_mandarin_ass"] = "human-reviewed-mandarin.ass"
        else:
            manifest.pop("human_reviewed_mandarin_srt", None)
            manifest.pop("human_reviewed_mandarin_vtt", None)
            manifest.pop("human_reviewed_mandarin_ass", None)
        write_json(root / "manifest.json", manifest)
    artifacts = [
        {"key": "track", "path": root / "human-reviewed-subtitle-track.json"},
        {"key": "transcript", "path": root / "human-corrected-transcript.json"},
        {"key": "source_srt", "path": root / "human-reviewed-source.srt"},
        {"key": "source_vtt", "path": root / "human-reviewed-source.vtt"},
        {"key": "source_ass", "path": root / "human-reviewed-source.ass"},
        {"key": "otio_plan", "path": root / "human-reviewed-subtitle.otio.json"},
        {"key": "kept_ranges", "path": root / "human-reviewed-kept-ranges.json"},
        {"key": "ffconcat_plan", "path": root / "human-reviewed.ffconcat"},
        {"key": "receipt", "path": root / "subtitle-review-apply-receipt.json"},
    ]
    if translation_complete:
        artifacts.extend(
            [
                {"key": "mandarin_srt", "path": root / "human-reviewed-mandarin.srt"},
                {"key": "mandarin_vtt", "path": root / "human-reviewed-mandarin.vtt"},
                {"key": "mandarin_ass", "path": root / "human-reviewed-mandarin.ass"},
            ]
        )
    register_bundle_run(
        root,
        run_type="subtitle_review",
        run_id="apply-subtitle-review",
        status="completed",
        title="人工确认双轨字幕",
        summary=f"Applied {len(rows)} source-linked subtitle segments; downstream summaries are stale.",
        artifacts=artifacts,
        retry_command=(
            f".\\scripts\\video-knowledge.ps1 apply-subtitle-review '{root}' --review-json '{review_path}'"
            if review_path is not None
            else f".\\scripts\\video-knowledge.ps1 prepare-subtitle-editor '{root}'"
        ),
        operator_boundary=track_payload["operator_boundary"],
        write=True,
    )
    return result


def _projection_segment(
    cue: TranscriptCue,
    *,
    index: int,
    translation: str,
    supplemental: dict[str, Any],
) -> dict[str, Any]:
    metadata = {**dict(supplemental.get("metadata") or {}), **dict(getattr(cue, "metadata", {}) or {})}
    words = metadata.get("words") or supplemental.get("words")
    segment_id = str(getattr(cue, "segment_id", "") or f"segment-{index + 1:06d}")
    source_ids = [str(value) for value in (getattr(cue, "source_segment_ids", None) or [segment_id])]
    speaker_global = str(
        metadata.get("speaker_global_id")
        or supplemental.get("speaker_global_id")
        or cue_speaker(cue)
        or ""
    )
    start_ms = _ms(getattr(cue, "start", 0.0))
    end_ms = _ms(getattr(cue, "end", 0.0))
    return {
        "segment_id": segment_id,
        "source_segment_ids": source_ids,
        "start_ms": start_ms,
        "end_ms": end_ms,
        "speaker_global_id": speaker_global,
        "speaker_role": str(cue_speaker_role(cue) or ""),
        "source_text": str(getattr(cue, "text", "") or "").strip(),
        "mandarin_text": str(translation or "").strip(),
        "words": _projection_words(words, start_ms=start_ms, end_ms=end_ms),
        "evidence_ids": [
            str(value)
            for value in (metadata.get("evidence_ids") or supplemental.get("evidence_ids") or [])
        ],
        "disabled": False,
    }


def _projection_words(value: Any, *, start_ms: int, end_ms: int) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    result: list[dict[str, Any]] = []
    for word in value:
        if not isinstance(word, dict):
            continue
        text = str(word.get("word") or word.get("text") or "").strip()
        if not text:
            continue
        word_start = max(start_ms, min(_word_ms(word, "start"), end_ms))
        word_end = max(word_start, min(_word_ms(word, "end", fallback="start"), end_ms))
        if word_end <= word_start:
            continue
        row = {
            "text": text,
            "start_ms": word_start,
            "end_ms": word_end,
        }
        speaker = str(word.get("speaker") or "").strip()
        if speaker:
            row["speaker_global_id"] = speaker
        result.append(row)
    return result


def _load_translations(root: Path, manifest: dict[str, Any]) -> tuple[dict[str, str], str]:
    raw = str(manifest.get("mandarin_translated_transcript_json") or "mandarin-translated-transcript.json").strip()
    path = Path(raw).expanduser()
    path = path if path.is_absolute() else root / path
    if not path.is_file():
        return {}, "missing"
    payload = _read_object(path)
    rows = payload.get("segments")
    if not isinstance(rows, list):
        return {}, "invalid"
    result: dict[str, str] = {}
    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            continue
        key = str(row.get("segment_id") or f"index:{index}")
        text = str(row.get("text") or "").strip()
        if text:
            result[key] = text
    return result, "ready" if result else "missing"


def _load_supplemental_segment_metadata(root: Path, manifest: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """Preserve direct provider fields that the generic transcript parser does not copy.

    Reuse boundary: this is a thin projection adapter, not a second transcript
    parser. The selected VKP transcript remains authoritative for ordering,
    text, and timing; direct ``words``/global speaker/evidence fields only enrich
    the matching stable segment ID.
    """

    candidates: list[Path] = []
    for key in ("corrected_transcript_json", "normalized_transcript_json", "transcript_json"):
        raw = str(manifest.get(key) or "").strip()
        if raw:
            path = Path(raw).expanduser()
            candidates.append(path if path.is_absolute() else root / path)
    candidates.extend(
        [root / "human-corrected-transcript.json", root / "corrected-transcript.json", root / "normalized-transcript.json", root / "transcript.json"]
    )
    for path in candidates:
        if not path.is_file():
            continue
        try:
            payload = read_json(path)
        except Exception:  # noqa: BLE001 - optional projection enrichment fails closed.
            continue
        rows = payload.get("segments") if isinstance(payload, dict) else payload
        if not isinstance(rows, list):
            continue
        result: dict[str, dict[str, Any]] = {}
        for index, row in enumerate(rows):
            if not isinstance(row, dict):
                continue
            key = str(row.get("segment_id") or row.get("id") or f"segment-{index + 1:06d}")
            result[key] = row
        if result:
            return result
    return {}


def _cue_key(cue: TranscriptCue, index: int) -> str:
    return str(getattr(cue, "segment_id", "") or f"index:{index}")


def _validate_projection_segments(rows: list[dict[str, Any]]) -> None:
    previous_end = 0
    for index, row in enumerate(rows):
        start = row["start_ms"]
        end = row["end_ms"]
        if start < previous_end or end <= start:
            raise ValueError(f"invalid transcript timing at segment {index}")
        if not str(row.get("source_text") or "").strip():
            raise ValueError(f"empty transcript text at segment {index}")
        previous_end = end


def _validate_review_segments(
    rows: list[Any],
    originals: list[dict[str, Any]],
    *,
    media_duration_ms: int,
) -> list[dict[str, Any]]:
    source_order: dict[str, int] = {}
    source_speaker: dict[str, str] = {}
    source_translation: dict[str, bool] = {}
    for index, row in enumerate(originals):
        for source_id in row["source_segment_ids"]:
            source_order[source_id] = index
            source_speaker[source_id] = str(row.get("speaker_global_id") or "")
            source_translation[source_id] = bool(str(row.get("mandarin_text") or "").strip())
    normalized: list[dict[str, Any]] = []
    covered: set[str] = set()
    previous_end = 0
    previous_source_index = -1
    split_counts: dict[str, int] = {}
    seen_segment_ids: set[str] = set()
    max_end = max(int(media_duration_ms), max(int(row["end_ms"]) for row in originals))
    for index, raw in enumerate(rows):
        if not isinstance(raw, dict):
            raise ValueError(f"segments[{index}] must be an object")
        segment_id = str(raw.get("segment_id") or "").strip()
        if not segment_id or segment_id in seen_segment_ids:
            raise ValueError(f"segments[{index}].segment_id is missing or duplicate")
        seen_segment_ids.add(segment_id)
        source_ids = [str(value).strip() for value in (raw.get("source_segment_ids") or []) if str(value).strip()]
        if not source_ids:
            raise ValueError(f"segments[{index}].source_segment_ids must not be empty")
        for source_id in source_ids:
            if source_id not in source_order:
                raise ValueError(f"unknown source_segment_id: {source_id}")
        indexes = [source_order[source_id] for source_id in source_ids]
        if indexes != list(range(min(indexes), max(indexes) + 1)):
            raise ValueError("merged source segments must be contiguous")
        speakers = {source_speaker[source_id] for source_id in source_ids if source_speaker[source_id]}
        if len(speakers) > 1:
            raise ValueError("cannot merge source segments from different speakers")
        current_source_index = min(indexes)
        if current_source_index < previous_source_index:
            raise ValueError("review source order differs from transcript source order")
        previous_source_index = current_source_index
        start = _strict_int(raw.get("start_ms"), f"segments[{index}].start_ms")
        end = _strict_int(raw.get("end_ms"), f"segments[{index}].end_ms")
        if start < previous_end or end <= start or end > max_end:
            raise ValueError(f"segments[{index}] has invalid or out-of-order timing")
        source_text = str(raw.get("source_text") or "").strip()
        if not source_text:
            raise ValueError(f"segments[{index}].source_text must not be empty")
        mandarin_text = str(raw.get("mandarin_text") or "").strip()
        for source_id in source_ids:
            split_counts[source_id] = split_counts.get(source_id, 0) + 1
            covered.add(source_id)
        normalized.append(
            {
                "segment_id": segment_id,
                "source_segment_ids": source_ids,
                "start_ms": start,
                "end_ms": end,
                "speaker_global_id": next(iter(speakers), str(raw.get("speaker_global_id") or "")),
                "speaker_role": str(raw.get("speaker_role") or ""),
                "source_text": source_text,
                "mandarin_text": mandarin_text,
                "words": raw.get("words") if isinstance(raw.get("words"), list) else [],
                "evidence_ids": [str(value) for value in (raw.get("evidence_ids") or [])],
                "disabled": bool(raw.get("disabled")),
            }
        )
        previous_end = end
    if covered != set(source_order):
        missing = sorted(set(source_order) - covered)
        raise ValueError(f"review omits source segments: {missing}")
    for source_id, count in split_counts.items():
        if count > 1 and source_translation[source_id]:
            related = [row for row in normalized if source_id in row["source_segment_ids"]]
            if any(not row["mandarin_text"] for row in related):
                raise ValueError(f"split source {source_id} requires reviewed mandarin_text for every part")
    return normalized


def _review_summary(originals: list[dict[str, Any]], rows: list[dict[str, Any]]) -> dict[str, Any]:
    original_by_source = {
        source_id: row
        for row in originals
        for source_id in row["source_segment_ids"]
    }
    changed_text = 0
    changed_translation = 0
    changed_timing = 0
    for row in rows:
        if len(row["source_segment_ids"]) != 1:
            changed_text += 1
            changed_timing += 1
            continue
        original = original_by_source[row["source_segment_ids"][0]]
        changed_text += int(row["source_text"] != original["source_text"])
        changed_translation += int(row["mandarin_text"] != original["mandarin_text"])
        changed_timing += int(row["start_ms"] != original["start_ms"] or row["end_ms"] != original["end_ms"])
    return {
        "source_segments": len(originals),
        "reviewed_segments": len(rows),
        "source_text_changes": changed_text,
        "mandarin_text_changes": changed_translation,
        "timing_changes": changed_timing,
        "disabled_segments": sum(1 for row in rows if row.get("disabled")),
    }


def _corrected_segment(
    row: dict[str, Any],
    index: int,
    *,
    original_by_source: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    raw_text = " ".join(
        str(original_by_source[source_id].get("source_text") or "").strip()
        for source_id in row["source_segment_ids"]
        if source_id in original_by_source
    ).strip()
    return {
        "index": index,
        "segment_id": row["segment_id"],
        "source_segment_ids": list(row["source_segment_ids"]),
        "start": row["start_ms"] / 1000.0,
        "end": row["end_ms"] / 1000.0,
        "timestamp": _clock(row["start_ms"] / 1000.0),
        "end_timestamp": _clock(row["end_ms"] / 1000.0),
        "text": row["source_text"],
        "corrected_text": row["source_text"],
        "raw_text": raw_text,
        "changed": row["source_text"] != raw_text,
        "speaker": row["speaker_global_id"],
        "speaker_role": row["speaker_role"],
        "subtitle_boundary_derived": True,
    }


def _render_srt(rows: list[dict[str, Any]], *, field: str) -> str:
    blocks: list[str] = []
    output_index = 1
    for row in rows:
        text = str(row.get(field) or "").strip()
        if row.get("disabled") or not text:
            continue
        blocks.extend(
            [
                str(output_index),
                f"{_srt_time(row['start_ms'])} --> {_srt_time(row['end_ms'])}",
                text,
                "",
            ]
        )
        output_index += 1
    return "\n".join(blocks).rstrip() + "\n"


def _render_vtt(rows: list[dict[str, Any]], *, field: str) -> str:
    blocks = ["WEBVTT", ""]
    for row in rows:
        text = str(row.get(field) or "").strip()
        if row.get("disabled") or not text:
            continue
        blocks.extend(
            [
                str(row["segment_id"]),
                f"{_vtt_time(row['start_ms'])} --> {_vtt_time(row['end_ms'])}",
                text,
                "",
            ]
        )
    return "\n".join(blocks).rstrip() + "\n"


def _render_ass(rows: list[dict[str, Any]], *, field: str) -> str:
    lines = [
        "[Script Info]",
        "ScriptType: v4.00+",
        "PlayResX: 1920",
        "PlayResY: 1080",
        "",
        "[V4+ Styles]",
        "Format: Name,Fontname,Fontsize,PrimaryColour,SecondaryColour,OutlineColour,BackColour,Bold,Italic,Underline,StrikeOut,ScaleX,ScaleY,Spacing,Angle,BorderStyle,Outline,Shadow,Alignment,MarginL,MarginR,MarginV,Encoding",
        "Style: Default,Arial,54,&H00FFFFFF,&H000000FF,&H00111111,&H80000000,0,0,0,0,100,100,0,0,1,3,1,2,80,80,60,1",
        "",
        "[Events]",
        "Format: Layer,Start,End,Style,Name,MarginL,MarginR,MarginV,Effect,Text",
    ]
    for row in rows:
        text = str(row.get(field) or "").strip()
        if row.get("disabled") or not text:
            continue
        escaped = text.replace("\\", "\\\\").replace("\r", "").replace("\n", r"\N")
        speaker = str(row.get("speaker_role") or row.get("speaker_global_id") or "")
        lines.append(
            f"Dialogue: 0,{_ass_time(row['start_ms'])},{_ass_time(row['end_ms'])},Default,{speaker},0,0,0,,{escaped}"
        )
    return "\n".join(lines).rstrip() + "\n"


def _kept_ranges(rows: list[dict[str, Any]], gap_remove: Any) -> list[dict[str, int]]:
    duration = max(int(row["end_ms"]) for row in rows)
    gaps = gap_remove.get("gaps") if isinstance(gap_remove, dict) else []
    removed: list[tuple[int, int]] = []
    for gap in gaps if isinstance(gaps, list) else []:
        if not isinstance(gap, dict) or gap.get("removed") is not True:
            continue
        start = int(gap.get("start_ms", gap.get("start", 0)) or 0)
        end = int(gap.get("end_ms", gap.get("end", start)) or start)
        start = max(0, min(start, duration))
        end = max(start, min(end, duration))
        if end > start:
            removed.append((start, end))
    removed.sort()
    kept: list[dict[str, int]] = []
    cursor = 0
    for start, end in removed:
        if start > cursor:
            kept.append({"start_ms": cursor, "end_ms": start})
        cursor = max(cursor, end)
    if cursor < duration:
        kept.append({"start_ms": cursor, "end_ms": duration})
    return kept or [{"start_ms": 0, "end_ms": duration}]


def _render_otio_plan(rows: list[dict[str, Any]], *, translation_complete: bool) -> dict[str, Any]:
    def clips(field: str) -> list[dict[str, Any]]:
        return [
            {
                "OTIO_SCHEMA": "Clip.2",
                "name": str(row["segment_id"]),
                "metadata": {
                    "text": str(row.get(field) or ""),
                    "speaker_global_id": str(row.get("speaker_global_id") or ""),
                    "source_segment_ids": list(row.get("source_segment_ids") or []),
                },
                "source_range": {
                    "OTIO_SCHEMA": "TimeRange.1",
                    "start_time": {"OTIO_SCHEMA": "RationalTime.1", "value": row["start_ms"], "rate": 1000.0},
                    "duration": {"OTIO_SCHEMA": "RationalTime.1", "value": row["end_ms"] - row["start_ms"], "rate": 1000.0},
                },
            }
            for row in rows
            if not row.get("disabled") and str(row.get(field) or "").strip()
        ]

    tracks = [
        {"OTIO_SCHEMA": "Track.1", "name": "source", "kind": "Video", "children": clips("source_text")}
    ]
    if translation_complete:
        tracks.append(
            {"OTIO_SCHEMA": "Track.1", "name": "mandarin", "kind": "Video", "children": clips("mandarin_text")}
        )
    return {
        "OTIO_SCHEMA": "Timeline.1",
        "name": "VKP human-reviewed subtitle plan",
        "tracks": {"OTIO_SCHEMA": "Stack.1", "children": tracks},
        "metadata": {"execution_authorized": False, "source": "subtitle_review_notes.v1"},
    }


def _render_ffconcat_plan(ranges: list[dict[str, int]]) -> str:
    lines = ["ffconcat version 1.0", "# Derived plan only; SOURCE_MEDIA is not executed by VKP."]
    for row in ranges:
        lines.extend(
            [
                "file 'SOURCE_MEDIA'",
                f"inpoint {row['start_ms'] / 1000:.3f}",
                f"outpoint {row['end_ms'] / 1000:.3f}",
            ]
        )
    return "\n".join(lines).rstrip() + "\n"


def _render_corrected_markdown(payload: dict[str, Any]) -> str:
    lines = ["# 人工确认逐字稿", ""]
    for row in payload["segments"]:
        lines.append(f"- {_clock(row['start'])} {row['corrected_text']}")
    return "\n".join(lines).rstrip() + "\n"


def _source_language(manifest: dict[str, Any]) -> str:
    value = str(manifest.get("transcript_language") or manifest.get("language") or "yue").strip()
    return value or "yue"


def _media_duration_ms(manifest: dict[str, Any], segments: list[dict[str, Any]]) -> int:
    """Return a stable media bound without invoking a second probe pipeline.

    The Bundle manifest or its media metadata is the authoritative duration
    source when available. Falling back to the selected transcript end keeps
    legacy Bundles usable while remaining fail-closed beyond known evidence.
    """

    transcript_end = max(int(row["end_ms"]) for row in segments)
    candidates: list[tuple[Any, bool]] = [
        (manifest.get("media_duration_ms"), True),
        (manifest.get("duration_ms"), True),
        (manifest.get("media_duration_seconds"), False),
        (manifest.get("duration_seconds"), False),
        (manifest.get("video_duration_seconds"), False),
    ]
    media_metadata = manifest.get("media")
    if isinstance(media_metadata, dict):
        candidates.extend(
            [
                (media_metadata.get("duration_ms"), True),
                (media_metadata.get("duration_seconds"), False),
                (media_metadata.get("duration"), False),
            ]
        )
    for value, already_ms in candidates:
        if value is None or isinstance(value, bool):
            continue
        try:
            numeric = float(value)
        except (TypeError, ValueError):
            continue
        if numeric <= 0:
            continue
        duration_ms = int(round(numeric if already_ms else numeric * 1000.0))
        if duration_ms > 0:
            return max(transcript_end, duration_ms)
    return transcript_end


def _load_review(review: dict[str, Any] | str | Path) -> dict[str, Any]:
    if isinstance(review, dict):
        return review
    path = Path(review).expanduser().resolve()
    payload = read_json(path)
    if not isinstance(payload, dict):
        raise ValueError("subtitle review must be a JSON object")
    return payload


def _require_bundle(value: str | Path) -> Path:
    root = Path(value).expanduser().resolve()
    if not (root / "manifest.json").is_file() or not (root / "timeline.json").is_file():
        raise ValueError(f"not a VKP webui bundle: {root}")
    return root


def _read_object(path: Path) -> dict[str, Any]:
    payload = read_json(path)
    if not isinstance(payload, dict):
        raise ValueError(f"JSON must be an object: {path}")
    return payload


def _strict_int(value: Any, name: str) -> int:
    if type(value) is not int:
        raise ValueError(f"{name} must be integer milliseconds")
    return value


def _ms(value: Any) -> int:
    return max(0, int(round(float(value or 0.0) * 1000)))


def _word_ms(row: dict[str, Any], key: str, *, fallback: str | None = None) -> int:
    millisecond_key = f"{key}_ms"
    if millisecond_key in row:
        return max(0, int(round(float(row.get(millisecond_key) or 0))))
    value = row.get(key, row.get(fallback, 0.0) if fallback else 0.0)
    return _ms(value)


def _sha256_json(value: object) -> str:
    return _sha256_bytes(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8"))


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _srt_time(value_ms: int) -> str:
    total = max(0, int(value_ms))
    hours, remainder = divmod(total, 3_600_000)
    minutes, remainder = divmod(remainder, 60_000)
    seconds, milliseconds = divmod(remainder, 1000)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d},{milliseconds:03d}"


def _vtt_time(value_ms: int) -> str:
    return _srt_time(value_ms).replace(",", ".")


def _ass_time(value_ms: int) -> str:
    total_centiseconds = max(0, int(round(value_ms / 10)))
    hours, remainder = divmod(total_centiseconds, 360_000)
    minutes, remainder = divmod(remainder, 6_000)
    seconds, centiseconds = divmod(remainder, 100)
    return f"{hours}:{minutes:02d}:{seconds:02d}.{centiseconds:02d}"


def _clock(value_seconds: float) -> str:
    total = max(0, int(value_seconds))
    hours, remainder = divmod(total, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
