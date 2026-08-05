from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Callable

from .local_media_progress import LocalMediaProgress, stderr_progress_callback
from .media_tools import resolve_media_tool
from .storage import read_json, write_json


SCHEMA = "video_knowledge_pipeline.qwen3_asr_raw_output.v1"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="qwen3-asr-python-runner")
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--model", default="Qwen/Qwen3-ASR-1.7B")
    parser.add_argument("--forced-aligner", default="Qwen/Qwen3-ForcedAligner-0.6B")
    parser.add_argument("--language", default="Chinese")
    parser.add_argument("--context", default="")
    parser.add_argument("--device", choices=["auto", "cuda", "cpu"], default=os.environ.get("LECTURE_ASR_DEVICE", "auto"))
    parser.add_argument("--max-new-tokens", type=int, default=1024)
    parser.add_argument("--dtype", choices=["auto", "float32", "float16", "bfloat16"], default=os.environ.get("VKP_QWEN_ASR_DTYPE", "auto"))
    parser.add_argument("--chunk-seconds", type=int, default=300)
    parser.add_argument("--chunk-indexes", default="", help="Comma-separated zero-based chunks to retry; all chunks are processed by default")
    parser.add_argument("--max-chunk-attempts", type=int, default=2, help="Bounded attempts per chunk across checkpoint resumes")
    parser.add_argument("--no-timestamps", action="store_true")
    parser.add_argument("--no-resume", action="store_true", help="Ignore a matching per-chunk checkpoint and start all requested chunks again")
    args = parser.parse_args(argv)
    result = run_qwen3_asr(
        input_path=args.input,
        output_path=args.output,
        model=args.model,
        forced_aligner="" if args.no_timestamps else args.forced_aligner,
        language=args.language,
        context=args.context,
        device=args.device,
        max_new_tokens=args.max_new_tokens,
        chunk_seconds=args.chunk_seconds,
        dtype_name=args.dtype,
        chunk_indexes=_chunk_indexes(args.chunk_indexes),
        max_chunk_attempts=args.max_chunk_attempts,
        resume=not args.no_resume,
        progress_callback=stderr_progress_callback,
    )
    print(json.dumps(result, ensure_ascii=False))
    if result.get("status") == "degraded":
        return 2
    return 0 if result.get("ok") else 1


def run_qwen3_asr(
    *,
    input_path: str,
    output_path: str,
    model: str,
    forced_aligner: str = "Qwen/Qwen3-ForcedAligner-0.6B",
    language: str = "Chinese",
    context: str = "",
    device: str = "auto",
    max_new_tokens: int = 1024,
    chunk_seconds: int = 300,
    dtype_name: str = "auto",
    chunk_indexes: list[int] | None = None,
    max_chunk_attempts: int = 2,
    resume: bool = True,
    progress_callback: Callable[[dict[str, Any]], None] | None = None,
) -> dict[str, Any]:
    media = Path(input_path).expanduser().resolve()
    output = Path(output_path).expanduser().resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    progress = LocalMediaProgress(
        pipeline="local_qwen3_asr",
        snapshot_path=output.with_name(f"{output.stem}-progress.json"),
        events_path=output.with_name(f"{output.stem}-progress.jsonl"),
        callback=progress_callback,
    )
    report_path = output.with_name(f"{output.stem}-chunk-report.json")
    checkpoint_path = output.with_name(f"{output.stem}-checkpoint.json")
    progress.emit(
        stage="preflight",
        percent=0,
        message="Validating local ASR input and runtime",
        output_paths=[output],
        report_paths=[report_path, checkpoint_path],
    )
    if not media.exists():
        payload = _failure(output, "input_not_found", f"input not found: {media}", model=model)
        return _finalize_payload(payload, output, report_path, progress)
    try:
        import torch
        from qwen_asr import Qwen3ASRModel
    except Exception as exc:
        payload = _failure(output, "qwen_asr_module_not_ready", str(exc), model=model)
        return _finalize_payload(payload, output, report_path, progress)
    selected_device = _device(device, torch)
    dtype = _torch_dtype(dtype_name, selected_device, torch)
    kwargs: dict[str, Any] = {
        "dtype": dtype,
        "device_map": "cuda:0" if selected_device.startswith("cuda") else "cpu",
        "low_cpu_mem_usage": True,
        "max_inference_batch_size": 1,
        "max_new_tokens": max(128, int(max_new_tokens or 1024)),
    }
    if forced_aligner:
        kwargs["forced_aligner"] = forced_aligner
        kwargs["forced_aligner_kwargs"] = {"dtype": dtype, "device_map": kwargs["device_map"]}
    try:
        progress.emit(stage="model_load", percent=5, message=f"Loading {model} on {selected_device}")
        runtime = Qwen3ASRModel.from_pretrained(model, **kwargs)
    except RuntimeError as exc:
        code = "qwen3_asr_cuda_oom" if "out of memory" in str(exc).lower() else "qwen3_asr_runtime_failed"
        payload = _failure(output, code, str(exc), model=model)
        payload["fallback"] = {"recommended_model": "Qwen/Qwen3-ASR-0.6B", "automatic": False}
        return _finalize_payload(payload, output, report_path, progress)
    except Exception as exc:
        payload = _failure(output, "qwen3_asr_runtime_failed", str(exc), model=model)
        return _finalize_payload(payload, output, report_path, progress)

    rows: list[dict[str, Any]] = []
    failed_chunks: list[dict[str, Any]] = []
    chunk_duration = max(30, int(chunk_seconds or 300))
    attempt_limit = max(1, int(max_chunk_attempts or 1))
    checkpoint = _load_checkpoint(
        checkpoint_path,
        media=media,
        model=model,
        chunk_seconds=chunk_duration,
        resume=resume,
    )
    rows = checkpoint["results"]
    failed_chunks = checkpoint["failed_chunks"]
    resumed_from_checkpoint = bool(checkpoint["resumed"])
    selected_indexes = sorted(set(chunk_indexes or []))
    try:
        progress.emit(stage="chunking", percent=10, message=f"Splitting media into {chunk_duration}-second chunks")
        with tempfile.TemporaryDirectory(prefix="vkp-qwen3-asr-") as temp_dir:
            chunks = _audio_chunks(media, Path(temp_dir), chunk_seconds=chunk_duration)
            indexed_chunks = [(_chunk_index(path), path) for path in chunks]
            if selected_indexes:
                indexed_chunks = [row for row in indexed_chunks if row[0] in selected_indexes]
                missing = sorted(set(selected_indexes) - {row[0] for row in indexed_chunks})
                if missing:
                    raise ValueError(f"requested chunk indexes not found: {missing}")
            requested_chunk_count = len(indexed_chunks)
            completed_indexes = {int(row.get("chunk_index") or 0) for row in rows}
            if completed_indexes:
                indexed_chunks = [row for row in indexed_chunks if row[0] not in completed_indexes]
                progress.emit(stage="resume", percent=10, message=f"Resuming after {len(completed_indexes)} checkpointed chunks")
            total = len(indexed_chunks)
            failed_dir = output.with_name(f"{output.stem}-failed-chunks")
            for current, (chunk_index, chunk) in enumerate(indexed_chunks, start=1):
                previous_failure = next(
                    (row for row in failed_chunks if int(row.get("chunk_index") or -1) == chunk_index),
                    None,
                )
                previous_attempt_count = int((previous_failure or {}).get("attempt_count") or 0)
                offset = float(chunk_index * chunk_duration)
                if previous_failure and (bool(previous_failure.get("retry_exhausted")) or previous_attempt_count >= attempt_limit):
                    progress.emit(
                        stage="retry_exhausted",
                        percent=10 + (80 * current / max(1, total)),
                        current_item=current,
                        total_items=total,
                        message=f"Skipping chunk {chunk_index}: retry limit reached",
                        details={"chunk_index": chunk_index, "attempt_count": previous_attempt_count, "max_chunk_attempts": attempt_limit},
                    )
                    continue
                failed_chunks = [row for row in failed_chunks if int(row.get("chunk_index") or -1) != chunk_index]
                attempt_count = previous_attempt_count + 1
                progress.emit(
                    stage="transcription",
                    percent=10 + (80 * (current - 1) / max(1, total)),
                    current_item=current,
                    total_items=total,
                    message=f"Transcribing chunk {chunk_index}",
                )
                try:
                    values = list(
                        runtime.transcribe(
                            audio=str(chunk),
                            context=context or None,
                            language=_language(language),
                            return_time_stamps=bool(forced_aligner),
                        )
                    )
                    if not values:
                        raise RuntimeError("empty_asr_result")
                    for value_index, value in enumerate(values, start=1):
                        text = str(getattr(value, "text", "") or "").strip()
                        timestamps = _offset_timestamps(_timestamps(getattr(value, "time_stamps", None)), offset)
                        rows.append(
                            {
                                "chunk_index": chunk_index,
                                "chunk_offset_seconds": offset,
                                "text": text,
                                "language": str(getattr(value, "language", "") or language),
                                "timestamps": timestamps,
                                "segments": _segments(
                                    timestamps,
                                    text,
                                    fallback_start=offset,
                                    segment_prefix=f"chunk-{chunk_index:04d}-result-{value_index:04d}",
                                ),
                            }
                        )
                except Exception as exc:
                    code = "qwen3_asr_cuda_oom" if "out of memory" in str(exc).lower() else "chunk_transcription_failed"
                    durable_path = ""
                    copy_error = ""
                    try:
                        failed_dir.mkdir(parents=True, exist_ok=True)
                        durable = failed_dir / chunk.name
                        shutil.copy2(chunk, durable)
                        durable_path = str(durable)
                    except Exception as copy_exc:  # pragma: no cover - defensive filesystem evidence.
                        copy_error = str(copy_exc)
                    retry = _retry_command(
                        media=media,
                        output=output.with_name(f"{output.stem}-retry-chunk-{chunk_index:04d}.json"),
                        model=model,
                        forced_aligner=forced_aligner,
                        language=language,
                        device=device,
                        max_new_tokens=max_new_tokens,
                        dtype_name=dtype_name,
                        chunk_seconds=chunk_duration,
                        chunk_index=chunk_index,
                    )
                    failed_chunks.append(
                        {
                            "chunk_index": chunk_index,
                            "start": offset,
                            "end": offset + chunk_duration,
                            "reason": code,
                            "detail": str(exc),
                            "artifact_path": durable_path,
                            "artifact_copy_error": copy_error,
                            "retry_command": retry,
                            "attempt_count": attempt_count,
                            "retry_exhausted": attempt_count >= attempt_limit,
                        }
                    )
                _write_checkpoint(
                    checkpoint_path,
                    media=media,
                    model=model,
                    chunk_seconds=chunk_duration,
                    forced_aligner=forced_aligner,
                    language=language,
                    results=rows,
                    failed_chunks=failed_chunks,
                    requested_chunk_count=requested_chunk_count,
                )
                progress.emit(
                    stage="transcription",
                    percent=10 + (80 * current / max(1, total)),
                    current_item=current,
                    total_items=total,
                    message=f"Finished chunk {chunk_index}",
                    details={"failed_chunks": len(failed_chunks), "successful_results": len(rows)},
                )
    except Exception as exc:
        payload = _failure(output, "qwen3_asr_chunking_failed", str(exc), model=model)
        return _finalize_payload(payload, output, report_path, progress)

    successful_chunks = sorted({int(row.get("chunk_index") or 0) for row in rows})
    status = "degraded" if failed_chunks and rows else ("failed" if failed_chunks else "completed")
    payload = {
        "schema": SCHEMA,
        "provider": "qwen3-asr",
        "model": model,
        "forced_aligner": forced_aligner,
        "chunk_seconds": chunk_duration,
        "chunk_count": requested_chunk_count,
        "max_chunk_attempts": attempt_limit,
        "retry_exhausted_chunk_count": sum(1 for row in failed_chunks if bool(row.get("retry_exhausted"))),
        "checkpoint_path": str(checkpoint_path),
        "resumed_from_checkpoint": resumed_from_checkpoint,
        "checkpointed_successful_chunk_count": len(checkpoint.get("successful_chunk_indexes") or []),
        "successful_chunk_count": len(successful_chunks),
        "failed_chunk_count": len(failed_chunks),
        "successful_chunk_indexes": successful_chunks,
        "device": selected_device,
        "dtype": str(dtype).replace("torch.", ""),
        "input_path": str(media),
        "ok": status == "completed",
        "usable": bool(rows),
        "status": status,
        "results": rows,
        "segments": [segment for row in rows for segment in row.get("segments") or []],
        "text": "\n".join(str(row.get("text") or "") for row in rows).strip(),
        "failed_chunks": failed_chunks,
        "gaps": [
            {
                "chunk_index": row["chunk_index"],
                "start": row["start"],
                "end": row["end"],
                "reason": row["reason"],
            }
            for row in failed_chunks
        ],
        "retry_commands": [row["retry_command"] for row in failed_chunks],
        "fallback": {"recommended_model": "Qwen/Qwen3-ASR-0.6B", "automatic": False},
    }
    _write_checkpoint(
        checkpoint_path,
        media=media,
        model=model,
        chunk_seconds=chunk_duration,
        forced_aligner=forced_aligner,
        language=language,
        results=rows,
        failed_chunks=failed_chunks,
        requested_chunk_count=requested_chunk_count,
        status=status,
    )
    return _finalize_payload(payload, output, report_path, progress)


def _checkpoint_default() -> dict[str, Any]:
    return {
        "resumed": False,
        "results": [],
        "failed_chunks": [],
        "successful_chunk_indexes": [],
    }


def _load_checkpoint(
    path: Path,
    *,
    media: Path,
    model: str,
    chunk_seconds: int,
    resume: bool,
) -> dict[str, Any]:
    default = _checkpoint_default()
    if not resume or not path.is_file():
        return default
    try:
        payload = read_json(path)
    except Exception:
        return default
    if not isinstance(payload, dict):
        return default
    identity = payload.get("input_identity")
    if not isinstance(identity, dict):
        return default
    if (
        str(identity.get("path") or "") != str(media)
        or int(identity.get("bytes") or -1) != media.stat().st_size
        or str(payload.get("model") or "") != model
        or int(payload.get("chunk_seconds") or 0) != int(chunk_seconds)
    ):
        return default
    rows = [dict(row) for row in payload.get("results") or [] if isinstance(row, dict)]
    failures = [dict(row) for row in payload.get("failed_chunks") or [] if isinstance(row, dict)]
    successful = sorted({int(row.get("chunk_index") or 0) for row in rows})
    return {
        "resumed": bool(rows or failures),
        "results": rows,
        "failed_chunks": failures,
        "successful_chunk_indexes": successful,
    }


def _write_checkpoint(
    path: Path,
    *,
    media: Path,
    model: str,
    chunk_seconds: int,
    forced_aligner: str,
    language: str,
    results: list[dict[str, Any]],
    failed_chunks: list[dict[str, Any]],
    requested_chunk_count: int,
    status: str = "running",
) -> None:
    successful = sorted({int(row.get("chunk_index") or 0) for row in results})
    payload = {
        "schema": "video_knowledge_pipeline.qwen3_asr_checkpoint.v1",
        "status": status,
        "input_identity": {"path": str(media), "bytes": media.stat().st_size},
        "model": model,
        "forced_aligner": forced_aligner,
        "language": language,
        "chunk_seconds": int(chunk_seconds),
        "requested_chunk_count": int(requested_chunk_count),
        "successful_chunk_indexes": successful,
        "successful_chunk_count": len(successful),
        "failed_chunk_count": len(failed_chunks),
        "results": results,
        "failed_chunks": failed_chunks,
    }
    write_json(path, payload)

def _torch_dtype(value: str, device: str, torch: Any) -> Any:
    requested = str(value or "auto").strip().lower()
    if requested == "float32":
        return torch.float32
    if requested == "float16":
        return torch.float16
    if requested == "bfloat16":
        return torch.bfloat16
    return torch.bfloat16 if str(device).startswith("cuda") else torch.float32

def _timestamps(values: Any) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for value in values or []:
        if isinstance(value, dict):
            text = value.get("text")
            start = value.get("start_time")
            end = value.get("end_time")
        else:
            text = getattr(value, "text", "")
            start = getattr(value, "start_time", 0.0)
            end = getattr(value, "end_time", start)
        rows.append({"text": str(text or ""), "start": float(start or 0.0), "end": float(end or start or 0.0)})
    return rows


def _segments(
    timestamps: list[dict[str, Any]],
    text: str,
    *,
    fallback_start: float = 0.0,
    segment_prefix: str = "segment",
) -> list[dict[str, Any]]:
    if not timestamps:
        return [
            {
                "segment_id": f"{segment_prefix}-0001",
                "source_segment_ids": [f"{segment_prefix}-0001"],
                "start": fallback_start,
                "end": fallback_start,
                "text": text,
            }
        ] if text else []
    segments: list[dict[str, Any]] = []
    current: list[dict[str, Any]] = []
    for row in timestamps:
        current.append(row)
        duration = float(current[-1]["end"]) - float(current[0]["start"])
        token = str(row.get("text") or "")
        if duration >= 15.0 or re.search(r"[。！？!?]$", token):
            segments.append(_merge(current))
            current = []
    if current:
        segments.append(_merge(current))
    for index, segment in enumerate(segments, start=1):
        segment_id = f"{segment_prefix}-{index:04d}"
        segment["segment_id"] = segment_id
        segment["source_segment_ids"] = [segment_id]
    return segments


def _audio_chunks(media: Path, output_dir: Path, *, chunk_seconds: int) -> list[Path]:
    ffmpeg = resolve_media_tool("ffmpeg")
    if not ffmpeg:
        raise RuntimeError("ffmpeg_not_ready_for_qwen3_asr_chunking")
    output_dir.mkdir(parents=True, exist_ok=True)
    pattern = output_dir / "chunk-%04d.wav"
    command = [
        ffmpeg, "-hide_banner", "-loglevel", "error", "-y", "-i", str(media),
        "-map", "0:a:0", "-ac", "1", "-ar", "16000", "-f", "segment",
        "-segment_time", str(chunk_seconds), "-reset_timestamps", "1", str(pattern),
    ]
    completed = subprocess.run(command, capture_output=True, text=True, encoding="utf-8", errors="replace", check=False)
    chunks = sorted(output_dir.glob("chunk-*.wav"))
    if completed.returncode != 0 or not chunks:
        raise RuntimeError(f"qwen3_asr_audio_chunking_failed: {completed.stderr[-500:]}")
    return chunks


def _offset_timestamps(rows: list[dict[str, Any]], offset: float) -> list[dict[str, Any]]:
    return [
        {
            **row,
            "start": round(float(row.get("start") or 0.0) + offset, 6),
            "end": round(float(row.get("end") or row.get("start") or 0.0) + offset, 6),
        }
        for row in rows
    ]


def _merge(rows: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "start": float(rows[0]["start"]),
        "end": float(rows[-1]["end"]),
        "text": "".join(str(row.get("text") or "") for row in rows).strip(),
        "words": rows,
    }


def _device(value: str, torch: Any) -> str:
    requested = str(value or "auto").lower()
    if requested == "cuda":
        return "cuda:0" if torch.cuda.is_available() else "cpu"
    if requested == "cpu":
        return "cpu"
    return "cuda:0" if torch.cuda.is_available() else "cpu"


def _language(value: str) -> str | None:
    text = str(value or "").strip()
    if not text or text.lower() == "auto":
        return None
    aliases = {"zh": "Chinese", "zh-cn": "Chinese", "cn": "Chinese", "en": "English"}
    return aliases.get(text.lower(), text)


def _chunk_indexes(value: str) -> list[int] | None:
    text = str(value or "").strip()
    if not text:
        return None
    indexes = sorted({int(part.strip()) for part in text.split(",") if part.strip()})
    if any(value < 0 for value in indexes):
        raise ValueError("chunk indexes must be zero or greater")
    return indexes


def _chunk_index(path: Path) -> int:
    match = re.search(r"(\d+)$", path.stem)
    if not match:
        raise ValueError(f"chunk filename has no numeric index: {path.name}")
    return int(match.group(1))


def _retry_command(
    *,
    media: Path,
    output: Path,
    model: str,
    forced_aligner: str,
    language: str,
    device: str,
    max_new_tokens: int,
    dtype_name: str,
    chunk_seconds: int,
    chunk_index: int,
) -> dict[str, Any]:
    command = [
        sys.executable,
        "-m",
        "video_knowledge_pipeline.qwen3_asr_python_runner",
        "--input",
        str(media),
        "--output",
        str(output),
        "--model",
        model,
        "--language",
        language,
        "--device",
        device,
        "--max-new-tokens",
        str(max_new_tokens),
        "--dtype",
        dtype_name,
        "--chunk-seconds",
        str(chunk_seconds),
        "--chunk-indexes",
        str(chunk_index),
    ]
    if forced_aligner:
        command.extend(["--forced-aligner", forced_aligner])
    else:
        command.append("--no-timestamps")
    return {"chunk_index": chunk_index, "command": command, "powershell": subprocess.list2cmdline(command)}


def _finalize_payload(
    payload: dict[str, Any],
    output: Path,
    report_path: Path,
    progress: LocalMediaProgress,
) -> dict[str, Any]:
    status = str(payload.get("status") or ("completed" if payload.get("ok") else "failed"))
    payload["status"] = status
    payload["output_path"] = str(output)
    payload["report_path"] = str(report_path)
    payload["progress"] = progress.artifacts()
    write_json(output, payload)
    report = {
        "schema": "video_knowledge_pipeline.local_asr_chunk_report.v1",
        "status": status,
        "input_path": payload.get("input_path", ""),
        "output_path": str(output),
        "successful_chunk_count": int(payload.get("successful_chunk_count") or 0),
        "failed_chunk_count": int(payload.get("failed_chunk_count") or 0),
        "failed_chunks": payload.get("failed_chunks") or [],
        "gaps": payload.get("gaps") or [],
        "retry_commands": payload.get("retry_commands") or [],
        "raw_successful_content_preserved": bool(payload.get("results")),
    }
    write_json(report_path, report)
    terminal = status if status in {"completed", "failed", "degraded"} else "failed"
    progress.emit(
        stage="finalize",
        percent=100,
        current_item=int(payload.get("successful_chunk_count") or 0) + int(payload.get("failed_chunk_count") or 0),
        total_items=int(payload.get("chunk_count") or 0),
        message=(
            "Local ASR completed"
            if terminal == "completed"
            else "Local ASR completed with missing chunks"
            if terminal == "degraded"
            else "Local ASR failed"
        ),
        status=terminal,
        output_paths=[output],
        report_paths=[report_path],
        details={
            "successful_chunk_count": int(payload.get("successful_chunk_count") or 0),
            "failed_chunk_count": int(payload.get("failed_chunk_count") or 0),
        },
    )
    return payload


def _failure(output: Path, code: str, error: str, *, model: str) -> dict[str, Any]:
    return {
        "schema": SCHEMA,
        "provider": "qwen3-asr",
        "model": model,
        "ok": False,
        "usable": False,
        "status": "failed",
        "error_code": code,
        "error": error,
        "output_path": str(output),
    }


if __name__ == "__main__":
    raise SystemExit(main())
