from __future__ import annotations

import math
import re
from pathlib import Path
from typing import Any

from .models import now_iso
from .storage import read_json, write_json
from .external_reuse_run_artifacts import ps_quote, register_external_reuse_run
from .transcript import format_timestamp
from .visual_integration import integrated_visual

SCHEMA = "video_knowledge_pipeline.video_moment_index.v1"


def build_video_moment_index(
    bundle_dir: str | Path,
    *,
    query: str = "",
    target_window_seconds: float = 300.0,
    max_chunk_chars: int = 3600,
    top_k: int = 8,
    write: bool = True,
) -> dict[str, Any]:
    """Build a lightweight VideoRAG/VTime-style local moment index.

    This does not import heavy model code. It turns VKP's unified timeline into
    queryable, evidence-preserving video moments that can feed smart summary,
    human review, or a future vector/graph index.
    """

    root = Path(bundle_dir).expanduser().resolve()
    manifest_path = root / "manifest.json"
    timeline_path = root / "timeline.json"
    if not manifest_path.exists():
        raise FileNotFoundError(f"manifest not found: {manifest_path}")
    if not timeline_path.exists():
        raise FileNotFoundError(f"timeline not found: {timeline_path}")

    manifest = read_json(manifest_path)
    timeline = read_json(timeline_path)
    if not isinstance(manifest, dict):
        raise ValueError("manifest.json must be a JSON object")
    if not isinstance(timeline, list):
        raise ValueError("timeline.json must be a JSON array")

    rows = [item for item in timeline if isinstance(item, dict)]
    chunks = _build_chunks(rows, target_window_seconds=target_window_seconds, max_chunk_chars=max_chunk_chars)
    query_hits = _rank_query(chunks, query, top_k=top_k) if query.strip() else []

    result = {
        "schema": SCHEMA,
        "bundle_dir": str(root),
        "title": str(manifest.get("title") or root.name),
        "created_at": now_iso(),
        "inspired_by": [
            "VideoRAG: segment caption + transcript + retrieval index",
            "VTimeLLM: query-to-moment temporal grounding",
        ],
        "parameters": {
            "query": query,
            "target_window_seconds": target_window_seconds,
            "max_chunk_chars": max_chunk_chars,
            "top_k": top_k,
        },
        "summary": {
            "timeline_items": len(rows),
            "chunks": len(chunks),
            "duration_seconds": _duration(rows),
            "chunks_with_visual_evidence": sum(1 for chunk in chunks if chunk["has_visual_evidence"]),
            "chunks_with_temporal_evidence": sum(1 for chunk in chunks if chunk["has_temporal_evidence"]),
            "query_hits": len(query_hits),
        },
        "chunks": chunks,
        "query_hits": query_hits,
        "artifacts": {
            "json": str(root / "exports" / "video-moment-index.json"),
            "markdown": str(root / "exports" / "video-moment-index.md"),
        },
        "write": bool(write),
    }
    if write:
        exports = root / "exports"
        exports.mkdir(parents=True, exist_ok=True)
        write_json(exports / "video-moment-index.json", result)
        (exports / "video-moment-index.md").write_text(_render_markdown(result), encoding="utf-8")
        manifest["video_moment_index"] = "exports/video-moment-index.json"
        manifest["video_moment_index_markdown"] = "exports/video-moment-index.md"
        manifest["mcp_video_moment_index_args"] = "mcp-video-moment-index.args.json"
        write_json(
            root / "mcp-video-moment-index.args.json",
            {
                "bundle_dir": str(root),
                "query": query,
                "target_window_seconds": target_window_seconds,
                "max_chunk_chars": max_chunk_chars,
                "top_k": top_k,
                "write": True,
            },
        )
        write_json(manifest_path, manifest)
        failed_items = [] if chunks else [{"id": "timeline", "reason": "no_moment_chunks", "detail": "Timeline produced no moment chunks for VideoRAG/VTime-style indexing."}]
        register_external_reuse_run(
            root,
            run_type="video_moment_index",
            title="Video moment index",
            result=result,
            status="needs_input" if failed_items else "completed",
            failed_items=failed_items,
            retry_command=f".\\scripts\\video-knowledge.ps1 video-moment-index {ps_quote(root)}",
            next_actions=[] if not failed_items else ["Check timeline.json and transcript coverage, then rerun video-moment-index."],
            write=True,
        )
    return result


def _build_chunks(timeline: list[dict[str, Any]], *, target_window_seconds: float, max_chunk_chars: int) -> list[dict[str, Any]]:
    if not timeline:
        return []
    rows = sorted(timeline, key=lambda item: (_seconds(item.get("start")), _item_index(item, 0)))
    chunks: list[dict[str, Any]] = []
    current: list[dict[str, Any]] = []
    current_start = _seconds(rows[0].get("start"))
    current_chars = 0
    for item in rows:
        text = _item_text_for_index(item)
        item_start = _seconds(item.get("start"))
        should_flush = bool(current) and (
            item_start - current_start >= max(30.0, target_window_seconds)
            or current_chars + len(text) > max(800, max_chunk_chars)
        )
        if should_flush:
            chunks.append(_chunk_from_items(current, len(chunks) + 1))
            current = []
            current_start = item_start
            current_chars = 0
        current.append(item)
        current_chars += len(text)
    if current:
        chunks.append(_chunk_from_items(current, len(chunks) + 1))
    return chunks


def _chunk_from_items(items: list[dict[str, Any]], chunk_index: int) -> dict[str, Any]:
    start = min(_seconds(item.get("start")) for item in items)
    end = max(_seconds(item.get("end")) for item in items)
    transcript_parts = []
    corrected_parts = []
    visual_parts = []
    temporal_parts = []
    evidence_paths: list[str] = []
    routes: dict[str, int] = {}
    tags: list[str] = []
    indexes: list[int] = []
    for pos, item in enumerate(items, start=1):
        idx = _item_index(item, pos)
        indexes.append(idx)
        transcript = _clean_text(item.get("transcript") or item.get("text") or "")
        corrected = _clean_text(item.get("corrected_transcript") or transcript)
        if transcript:
            transcript_parts.append(transcript)
        if corrected:
            corrected_parts.append(corrected)
        route = str(item.get("visual_route") or "unknown")
        routes[route] = routes.get(route, 0) + 1
        tags.extend(_item_tags(item))
        integrated = _safe_integrated_visual(item)
        visual_text = _clean_text(
            item.get("human_corrected_visual_text")
            or item.get("visual_text")
            or item.get("ocr_text")
            or integrated.get("text")
            or ""
        )
        structured = _mapping_text(item.get("structured_visual"))
        frame_understanding = _mapping_text(item.get("human_corrected_visual_understanding") or item.get("visual_understanding"))
        temporal = _mapping_text(item.get("human_corrected_temporal_visual_understanding") or item.get("temporal_visual_understanding"))
        for value in (visual_text, structured, frame_understanding):
            if value:
                visual_parts.append(value)
        if temporal:
            temporal_parts.append(temporal)
        evidence_paths.extend(_evidence_paths(item))
    text = _clip(" ".join(corrected_parts or transcript_parts), 12000)
    visual_text = _clip(" ".join(visual_parts), 8000)
    temporal_text = _clip(" ".join(temporal_parts), 6000)
    keywords = _keywords(" ".join([text, visual_text, temporal_text, " ".join(tags)]))
    return {
        "chunk_index": chunk_index,
        "start": start,
        "end": end,
        "start_time": format_timestamp(start),
        "end_time": format_timestamp(end),
        "duration_seconds": max(0.0, end - start),
        "timeline_indexes": indexes,
        "visual_routes": routes,
        "tags": sorted(set(tags))[:40],
        "transcript_text": text,
        "visual_text": visual_text,
        "temporal_text": temporal_text,
        "keywords": keywords[:60],
        "has_visual_evidence": bool(visual_text),
        "has_temporal_evidence": bool(temporal_text),
        "evidence_paths": sorted(set(evidence_paths))[:80],
    }


def _rank_query(chunks: list[dict[str, Any]], query: str, *, top_k: int) -> list[dict[str, Any]]:
    query_tokens = _token_set(query)
    if not query_tokens:
        return []
    hits = []
    for chunk in chunks:
        fields = [
            chunk.get("transcript_text", ""),
            chunk.get("visual_text", ""),
            chunk.get("temporal_text", ""),
            " ".join(chunk.get("keywords") or []),
            " ".join(chunk.get("tags") or []),
        ]
        field_tokens = _token_set(" ".join(str(value) for value in fields))
        overlap = query_tokens.intersection(field_tokens)
        if not overlap:
            continue
        visual_bonus = 0.2 if chunk.get("has_visual_evidence") else 0.0
        temporal_bonus = 0.2 if chunk.get("has_temporal_evidence") else 0.0
        score = len(overlap) / max(1, len(query_tokens)) + visual_bonus + temporal_bonus
        hits.append(
            {
                "chunk_index": chunk["chunk_index"],
                "score": round(score, 4),
                "matched_terms": sorted(overlap)[:30],
                "start": chunk["start"],
                "end": chunk["end"],
                "start_time": chunk["start_time"],
                "end_time": chunk["end_time"],
                "timeline_indexes": chunk["timeline_indexes"],
                "snippet": _clip(_best_snippet(chunk, query_tokens), 500),
                "evidence_paths": chunk["evidence_paths"][:12],
            }
        )
    hits.sort(key=lambda row: (-row["score"], row["start"]))
    return hits[: max(0, top_k)]


def _best_snippet(chunk: dict[str, Any], query_tokens: set[str]) -> str:
    text = " ".join(str(chunk.get(key) or "") for key in ("transcript_text", "visual_text", "temporal_text"))
    if not text:
        return ""
    sentences = re.split(r"(?<=[。！？!?；;])\s*", text)
    ranked = []
    for sentence in sentences:
        tokens = _token_set(sentence)
        ranked.append((len(tokens.intersection(query_tokens)), len(sentence), sentence))
    ranked.sort(key=lambda row: (-row[0], row[1]))
    return ranked[0][2] if ranked else text


def _safe_integrated_visual(item: dict[str, Any]) -> dict[str, Any]:
    try:
        value = integrated_visual(item)
        return value if isinstance(value, dict) else {}
    except Exception:
        return {}


def _item_text_for_index(item: dict[str, Any]) -> str:
    return _clean_text(
        " ".join(
            str(item.get(key) or "")
            for key in (
                "corrected_transcript",
                "transcript",
                "text",
                "human_corrected_visual_text",
                "visual_text",
                "ocr_text",
            )
        )
    )


def _mapping_text(value: Any) -> str:
    if isinstance(value, str):
        return _clean_text(value)
    if isinstance(value, dict):
        parts = []
        for key, raw in value.items():
            if isinstance(raw, (str, int, float)):
                parts.append(f"{key}: {raw}")
            elif isinstance(raw, list):
                parts.append(f"{key}: {'; '.join(str(item) for item in raw[:8])}")
        return _clean_text(" ".join(parts))
    if isinstance(value, list):
        return _clean_text(" ".join(str(item) for item in value[:12]))
    return ""


def _item_tags(item: dict[str, Any]) -> list[str]:
    tags = []
    for key in ("tags", "tagger_tags", "material_types", "labels"):
        value = item.get(key)
        if isinstance(value, list):
            tags.extend(str(tag).strip() for tag in value if str(tag).strip())
        elif isinstance(value, str) and value.strip():
            tags.extend(part.strip() for part in re.split(r"[,，/|;；\s]+", value) if part.strip())
    for key in ("tagger_primary_label", "tagger_event_type", "visual_route"):
        value = str(item.get(key) or "").strip()
        if value:
            tags.append(value)
    return tags


def _evidence_paths(item: dict[str, Any]) -> list[str]:
    paths: list[str] = []
    for key in ("frame_paths", "temporal_frame_paths", "original_frame_paths", "ocr_crop_paths"):
        value = item.get(key)
        if isinstance(value, list):
            paths.extend(str(path) for path in value if str(path).strip())
        elif isinstance(value, str) and value.strip():
            paths.append(value)
    for key in ("frame_path", "image_path", "evidence_path"):
        value = str(item.get(key) or "").strip()
        if value:
            paths.append(value)
    return paths


def _keywords(text: str) -> list[str]:
    tokens = list(_token_set(text))
    tokens.sort(key=lambda token: (-len(token), token))
    return tokens


def _token_set(text: str) -> set[str]:
    value = str(text or "").lower()
    ascii_tokens = set(re.findall(r"[a-z0-9][a-z0-9_\-]{1,}", value))
    chinese = re.findall(r"[\u4e00-\u9fff]", value)
    chinese_tokens = set(chinese)
    chinese_tokens.update("".join(chinese[i : i + 2]) for i in range(max(0, len(chinese) - 1)))
    return {token for token in ascii_tokens.union(chinese_tokens) if len(token.strip()) >= 1}


def _duration(timeline: list[dict[str, Any]]) -> float:
    if not timeline:
        return 0.0
    return max(_seconds(item.get("end")) for item in timeline)


def _seconds(value: Any) -> float:
    try:
        number = float(value)
        if math.isfinite(number):
            return max(0.0, number)
    except Exception:
        return 0.0
    return 0.0


def _item_index(item: dict[str, Any], fallback: int) -> int:
    try:
        return int(item.get("index") or fallback)
    except Exception:
        return fallback


def _clean_text(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "").strip())


def _clip(text: str, limit: int) -> str:
    value = _clean_text(text)
    if len(value) <= limit:
        return value
    return value[: max(0, limit - 1)].rstrip() + "…"


def _render_markdown(result: dict[str, Any]) -> str:
    lines = [
        "# Video Moment Index",
        "",
        f"- Bundle: `{result['bundle_dir']}`",
        f"- Title: {result['title']}",
        f"- Created: {result['created_at']}",
        f"- Chunks: `{result['summary']['chunks']}`",
        f"- Duration: `{format_timestamp(result['summary']['duration_seconds'])}`",
        f"- Chunks with visual evidence: `{result['summary']['chunks_with_visual_evidence']}`",
        f"- Chunks with temporal evidence: `{result['summary']['chunks_with_temporal_evidence']}`",
        "",
        "## Query Hits",
        "",
    ]
    if result.get("query_hits"):
        lines.append("| Score | Time | Timeline | Matched | Snippet |")
        lines.append("|---:|---|---|---|---|")
        for hit in result["query_hits"]:
            lines.append(
                f"| {hit['score']} | {hit['start_time']} - {hit['end_time']} | "
                f"`{','.join(str(i) for i in hit['timeline_indexes'][:12])}` | "
                f"{', '.join(hit['matched_terms'][:8])} | {hit['snippet']} |"
            )
    else:
        lines.append("No query was provided, or no lexical hit was found.")
    lines.extend(["", "## Chunks", ""])
    for chunk in result["chunks"]:
        lines.extend(
            [
                f"### {chunk['chunk_index']}. {chunk['start_time']} - {chunk['end_time']}",
                "",
                f"- Timeline: `{','.join(str(i) for i in chunk['timeline_indexes'][:20])}`",
                f"- Routes: `{chunk['visual_routes']}`",
                f"- Keywords: {', '.join(chunk['keywords'][:16])}",
                "",
                _clip(chunk["transcript_text"], 800) or "_No transcript text._",
                "",
            ]
        )
        if chunk["visual_text"] or chunk["temporal_text"]:
            lines.append("Visual/temporal evidence:")
            if chunk["visual_text"]:
                lines.append(f"- Visual: {_clip(chunk['visual_text'], 500)}")
            if chunk["temporal_text"]:
                lines.append(f"- Temporal: {_clip(chunk['temporal_text'], 500)}")
            lines.append("")
    return "\n".join(lines).rstrip() + "\n"
