from __future__ import annotations

import difflib
import subprocess
from pathlib import Path
from typing import Any

from .interval_coverage import interval_intersection_over_union as _overlap_ratio
from .media_tools import resolve_media_tool
from .models import now_iso
from .storage import bundle_write_lock, read_json, write_json
from .text_normalization import compact_ascii_cjk_after_lowering as _compact
from .transcript import format_timestamp, parse_transcript


SCHEMA = "video_knowledge_pipeline.asr_consensus.v1"


def build_asr_consensus(
    bundle_dir: str | Path,
    *,
    primary_transcript: str | Path,
    secondary_transcript: str | Path,
    media_path: str | Path | None = None,
    agreement_threshold: float = 0.86,
    review_padding_seconds: float = 4.0,
    min_review_seconds: float = 8.0,
    max_review_seconds: float = 30.0,
    execute_clips: bool = False,
    write: bool = True,
) -> dict[str, Any]:
    """Align two independent ASR transcripts and retain disagreements as evidence.

    The secondary transcript never overwrites the primary transcript.  Consensus
    is an evidence layer used by semantic correction and quality benchmarking.
    """

    root = Path(bundle_dir).expanduser().resolve()
    manifest_path = root / "manifest.json"
    manifest = read_json(manifest_path) if manifest_path.exists() else {}
    manifest = manifest if isinstance(manifest, dict) else {}
    primary_path = _resolve_path(root, primary_transcript)
    secondary_path = _resolve_path(root, secondary_transcript)
    primary = parse_transcript(primary_path)
    secondary = parse_transcript(secondary_path)
    media = _resolve_media(root, manifest, media_path)

    matches, unmatched_secondary = _align(primary, secondary)
    windows: list[dict[str, Any]] = []
    for index, (primary_index, secondary_index, overlap) in enumerate(matches):
        p = primary[primary_index]
        s = secondary[secondary_index] if secondary_index is not None else None
        similarity = _similarity(p.text, s.text if s else "")
        status = "agreement" if s and similarity >= agreement_threshold else ("conflict" if s else "primary_only")
        window = _window(
            index=index,
            status=status,
            primary_index=primary_index,
            secondary_index=secondary_index,
            primary=p,
            secondary=s,
            overlap=overlap,
            similarity=similarity,
            media=media,
            clip_dir=root / "asr-consensus-clips",
            padding=review_padding_seconds,
            min_seconds=min_review_seconds,
            max_seconds=max_review_seconds,
        )
        windows.append(window)
    for secondary_index in unmatched_secondary:
        s = secondary[secondary_index]
        windows.append(
            _window(
                index=len(windows),
                status="secondary_only",
                primary_index=None,
                secondary_index=secondary_index,
                primary=None,
                secondary=s,
                overlap=0.0,
                similarity=0.0,
                media=media,
                clip_dir=root / "asr-consensus-clips",
                padding=review_padding_seconds,
                min_seconds=min_review_seconds,
                max_seconds=max_review_seconds,
            )
        )
    windows.sort(key=lambda row: (float(row["start"]), int(row["index"])))
    for index, row in enumerate(windows):
        row["index"] = index
        row["window_id"] = f"asr-consensus-{index:04d}"

    clip_results = _materialise_clips(windows, media, execute=execute_clips) if execute_clips else []
    counts = {key: sum(1 for row in windows if row["status"] == key) for key in ("agreement", "conflict", "primary_only", "secondary_only")}
    conflict_rows = [row for row in windows if row["status"] != "agreement"]
    result: dict[str, Any] = {
        "schema": SCHEMA,
        "bundle_dir": str(root),
        "primary_transcript": str(primary_path),
        "secondary_transcript": str(secondary_path),
        "media_path": str(media) if media else "",
        "status": "completed_with_conflicts" if conflict_rows else "completed_consensus",
        "ok": bool(primary and secondary),
        "agreement_threshold": float(agreement_threshold),
        "primary_segment_count": len(primary),
        "secondary_segment_count": len(secondary),
        "window_count": len(windows),
        "counts": counts,
        "conflict_count": len(conflict_rows),
        "conflict_indexes": [int(row["index"]) for row in conflict_rows],
        "windows": windows,
        "clip_execution": {
            "requested": bool(execute_clips),
            "executed": len([row for row in clip_results if row.get("ok")]),
            "failed": len([row for row in clip_results if not row.get("ok")]),
            "results": clip_results,
        },
        "operator_boundary": {
            "independent_hypotheses_preserved": True,
            "does_not_promote_secondary": True,
            "clip_generation_requires_execute": True,
            "no_cloud_call": True,
        },
        "artifacts": {
            "json": "asr-consensus.json",
            "markdown": "asr-consensus.md",
            "clips_dir": "asr-consensus-clips",
        },
        "updated_at": now_iso(),
    }
    if write:
        root.mkdir(parents=True, exist_ok=True)
        with bundle_write_lock(root, operation="asr_consensus", timeout_seconds=1.0):
            write_json(root / "asr-consensus.json", result)
            (root / "asr-consensus.md").write_text(_render_markdown(result), encoding="utf-8")
            write_json(
                root / "mcp-asr-consensus.args.json",
                {
                    "bundle_dir": str(root),
                    "primary_transcript": str(primary_path),
                    "secondary_transcript": str(secondary_path),
                    "media_path": str(media) if media else "",
                    "agreement_threshold": agreement_threshold,
                    "execute_clips": False,
                    "write": True,
                },
            )
            manifest["asr_primary_transcript"] = str(primary_path)
            manifest["asr_secondary_transcript"] = str(secondary_path)
            manifest["asr_consensus_json"] = "asr-consensus.json"
            manifest["asr_consensus_markdown"] = "asr-consensus.md"
            manifest["mcp_asr_consensus_args"] = "mcp-asr-consensus.args.json"
            manifest["asr_consensus_summary"] = {"status": result["status"], "conflict_count": len(conflict_rows), "updated_at": result["updated_at"]}
            write_json(manifest_path, manifest)
    return result


def _align(primary: list[Any], secondary: list[Any]) -> tuple[list[tuple[int, int | None, float]], list[int]]:
    used: set[int] = set()
    rows: list[tuple[int, int | None, float]] = []
    for p_index, p in enumerate(primary):
        best_index: int | None = None
        best_score = -1.0
        for s_index, s in enumerate(secondary):
            if s_index in used:
                continue
            overlap = _overlap_ratio(float(p.start), float(p.end), float(s.start), float(s.end))
            distance = abs(((float(p.start) + float(p.end)) / 2) - ((float(s.start) + float(s.end)) / 2))
            score = overlap * 2.0 - min(distance / 30.0, 1.0)
            if overlap > 0 and score > best_score:
                best_index = s_index
                best_score = score
        if best_index is None:
            rows.append((p_index, None, 0.0))
        else:
            used.add(best_index)
            s = secondary[best_index]
            rows.append((p_index, best_index, _overlap_ratio(float(p.start), float(p.end), float(s.start), float(s.end))))
    return rows, [index for index in range(len(secondary)) if index not in used]


def _window(
    *,
    index: int,
    status: str,
    primary_index: int | None,
    secondary_index: int | None,
    primary: Any | None,
    secondary: Any | None,
    overlap: float,
    similarity: float,
    media: Path | None,
    clip_dir: Path,
    padding: float,
    min_seconds: float,
    max_seconds: float,
) -> dict[str, Any]:
    starts = [float(row.start) for row in (primary, secondary) if row is not None]
    ends = [float(row.end) for row in (primary, secondary) if row is not None]
    start = max(0.0, min(starts or [0.0]) - max(0.0, padding))
    end = max(ends or [start]) + max(0.0, padding)
    if end - start < min_seconds:
        end = start + min_seconds
    if end - start > max_seconds:
        center = (start + end) / 2
        start = max(0.0, center - max_seconds / 2)
        end = start + max_seconds
    clip_path = clip_dir / f"asr-consensus-{index:04d}.wav"
    return {
        "index": index,
        "window_id": f"asr-consensus-{index:04d}",
        "status": status,
        "start": round(start, 3),
        "end": round(end, 3),
        "time_range": f"{format_timestamp(start)} - {format_timestamp(end)}",
        "primary_index": primary_index,
        "secondary_index": secondary_index,
        "primary_start": round(float(primary.start), 3) if primary is not None else None,
        "primary_end": round(float(primary.end), 3) if primary is not None else None,
        "secondary_start": round(float(secondary.start), 3) if secondary is not None else None,
        "secondary_end": round(float(secondary.end), 3) if secondary is not None else None,
        "primary_text": str(primary.text or "") if primary is not None else "",
        "secondary_text": str(secondary.text or "") if secondary is not None else "",
        "text_similarity": round(float(similarity), 4),
        "time_overlap_ratio": round(float(overlap), 4),
        "audio_review_window": {
            "media_path": str(media) if media else "",
            "clip_path": str(clip_path),
            "duration_seconds": round(end - start, 3),
            "execute_required": True,
        },
    }


def _materialise_clips(windows: list[dict[str, Any]], media: Path | None, *, execute: bool) -> list[dict[str, Any]]:
    if not execute:
        return []
    if not media or not media.exists():
        return [{"ok": False, "error": "media_path_missing"}]
    ffmpeg = resolve_media_tool("ffmpeg")
    if not ffmpeg:
        return [{"ok": False, "error": "ffmpeg_not_found"}]
    results: list[dict[str, Any]] = []
    for row in windows:
        if row.get("status") == "agreement":
            continue
        clip = Path(str(row["audio_review_window"]["clip_path"]))
        clip.parent.mkdir(parents=True, exist_ok=True)
        command = [
            ffmpeg,
            "-y",
            "-ss",
            str(row["start"]),
            "-t",
            str(max(0.1, float(row["end"]) - float(row["start"]))),
            "-i",
            str(media),
            "-vn",
            "-ac",
            "1",
            "-ar",
            "16000",
            str(clip),
        ]
        completed = subprocess.run(command, capture_output=True, text=True, encoding="utf-8", errors="replace", check=False)
        ok = completed.returncode == 0 and clip.exists() and clip.stat().st_size > 0
        row["audio_review_window"]["executed"] = True
        row["audio_review_window"]["ok"] = ok
        results.append({"window_id": row["window_id"], "ok": ok, "returncode": completed.returncode, "clip_path": str(clip), "error": "" if ok else completed.stderr[-500:]})
    return results


def _resolve_path(root: Path, value: str | Path) -> Path:
    path = Path(value).expanduser()
    if not path.is_absolute():
        path = root / path
    if not path.exists():
        raise FileNotFoundError(f"transcript not found: {path}")
    return path.resolve()


def _resolve_media(root: Path, manifest: dict[str, Any], value: str | Path | None) -> Path | None:
    candidate = value or manifest.get("media_path") or manifest.get("source_path")
    if not candidate:
        return None
    path = Path(str(candidate)).expanduser()
    if not path.is_absolute():
        path = root / path
    return path.resolve() if path.exists() else None


def _similarity(left: str, right: str) -> float:
    a = _compact(left)
    b = _compact(right)
    return difflib.SequenceMatcher(a=a, b=b, autojunk=False).ratio() if a and b else 0.0


def _render_markdown(result: dict[str, Any]) -> str:
    counts = result.get("counts") if isinstance(result.get("counts"), dict) else {}
    lines = [
        "# ASR Consensus",
        "",
        f"- Status: `{result.get('status')}`",
        f"- Primary: `{result.get('primary_transcript')}`",
        f"- Secondary: `{result.get('secondary_transcript')}`",
        f"- Agreement / conflict / primary-only / secondary-only: `{counts.get('agreement', 0)}` / `{counts.get('conflict', 0)}` / `{counts.get('primary_only', 0)}` / `{counts.get('secondary_only', 0)}`",
        "",
        "## Review Windows",
        "",
        "| ID | Time | Status | Similarity | Primary | Secondary | Clip |",
        "| --- | --- | --- | ---: | --- | --- | --- |",
    ]
    for row in result.get("windows") or []:
        if row.get("status") == "agreement":
            continue
        audio = row.get("audio_review_window") if isinstance(row.get("audio_review_window"), dict) else {}
        lines.append(
            f"| `{row.get('window_id')}` | `{row.get('time_range')}` | `{row.get('status')}` | {row.get('text_similarity')} | "
            f"{_md(row.get('primary_text'))} | {_md(row.get('secondary_text'))} | `{audio.get('clip_path', '')}` |"
        )
    return "\n".join(lines).rstrip() + "\n"


def _md(value: Any) -> str:
    return str(value or "").replace("|", "\\|").replace("\n", " ")[:240]
