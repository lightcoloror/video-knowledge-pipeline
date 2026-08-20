from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any, Callable

from .models import now_iso
from .path_defaults import local_model_root, source_reviews_root, tool_source_review_root
from .storage import bundle_write_lock, read_json, write_json
from .tagger_import import import_tagger_annotations
from .file_hash import sha256_file


SCHEMA = "video_knowledge_pipeline.general_tagger.v1"
STATUS_SCHEMA = "video_knowledge_pipeline.general_tagger_status.v1"
MODEL = "ram_plus_swin_large_14m"
IMPLEMENTATION = "recognize_anything_ram_plus"
DEFAULT_SOURCE_ROOT = tool_source_review_root() / "recognize-anything"
DEFAULT_CHECKPOINT = local_model_root() / "recognize-anything" / "ram_plus_swin_large_14m.pth"
DEFAULT_TOKENIZER_ROOT = local_model_root() / "bert-base-uncased-tokenizer"
DEFAULT_THRESHOLD_FLOOR = 0.75
COMPATIBILITY_BASELINES = ["cl_tagger", "wd_eva02_large_tagger_v3"]


def general_tagger_status(
    *,
    source_root: str | Path | None = None,
    checkpoint_path: str | Path | None = None,
    source_inventory_path: str | Path | None = None,
) -> dict[str, Any]:
    discovery = _inventory_model_discovery(source_inventory_path)
    source = _source_root(source_root, discovery=discovery)
    checkpoint = _checkpoint(checkpoint_path, discovery=discovery)
    tokenizer = _tokenizer_root(discovery=discovery)
    blockers: list[str] = []
    if source is None:
        blockers.append("recognize_anything_source_missing")
    if checkpoint is None:
        blockers.append("ram_plus_checkpoint_missing")
    if tokenizer is None:
        blockers.append("bert_tokenizer_missing")
    return {
        "schema": STATUS_SCHEMA,
        "status": "ready" if not blockers else "needs_setup",
        "selected_model": MODEL,
        "implementation": IMPLEMENTATION,
        "domain": "general_real_world_images",
        "languages": ["zh", "en"],
        "source_root": str(source or ""),
        "checkpoint_path": str(checkpoint or ""),
        "tokenizer_root": str(tokenizer or ""),
        "model_discovery": discovery,
        "threshold_floor": DEFAULT_THRESHOLD_FLOOR,
        "blockers": blockers,
        "compatibility_baselines": list(COMPATIBILITY_BASELINES),
        "automatic_remote_fallback": False,
        "automatic_model_download": False,
        "device_policy": {
            "gpu_required": True,
            "default_device": "cuda",
            "cpu_fallback_allowed": False,
        },
        "updated_at": now_iso(),
    }


def run_general_tagger(
    bundle_dir: str | Path,
    *,
    source_root: str | Path | None = None,
    checkpoint_path: str | Path | None = None,
    device: str = "cuda",
    prefer_language: str = "zh",
    limit: int = 0,
    execute: bool = False,
    import_annotations: bool = True,
    write: bool = True,
    _inference_backend: Callable[[Path], dict[str, object]] | None = None,
) -> dict[str, Any]:
    """Run RAM++ over bundle keyframes and import candidate tag evidence."""

    if device not in {"auto", "cpu", "cuda"}:
        raise ValueError("device must be auto, cpu, or cuda")
    if prefer_language not in {"zh", "en"}:
        raise ValueError("prefer_language must be zh or en")
    root = Path(bundle_dir).expanduser().resolve()
    timeline_path = root / "timeline.json"
    if not timeline_path.exists():
        raise FileNotFoundError(f"timeline.json not found: {timeline_path}")
    timeline = read_json(timeline_path)
    if not isinstance(timeline, list):
        raise ValueError("timeline.json must be an array")

    setup = general_tagger_status(source_root=source_root, checkpoint_path=checkpoint_path)
    source = _source_root(source_root)
    checkpoint = _checkpoint(checkpoint_path)
    frames = _bundle_frames(root, timeline)
    if int(limit) > 0:
        frames = frames[: int(limit)]
    status = "planned"
    error: dict[str, Any] | None = None
    annotations: list[dict[str, Any]] = []
    backend = _inference_backend

    if execute:
        blockers = list(setup.get("blockers") or [])
        if not frames:
            blockers.append("bundle_keyframes_missing")
        if blockers and backend is None:
            status = "blocked_setup"
            error = {"code": "general_tagger_runtime_not_ready", "blockers": sorted(set(blockers))}
        else:
            try:
                if backend is None:
                    backend = _ram_plus_backend(source, checkpoint, device=device)
                revision = sha256_file(checkpoint) if checkpoint is not None else "test-backend"
                for frame in frames:
                    output = backend(frame["frame_path"])
                    labels_en = _labels(output.get("tags_en"))
                    labels_zh = _labels(output.get("tags_zh"))
                    selected = labels_zh if prefer_language == "zh" and labels_zh else labels_en
                    if prefer_language == "en" and labels_en:
                        selected = labels_en
                    annotations.append(
                        {
                            "schema": "video_knowledge_pipeline.tagger_annotation.v1",
                            "index": frame["timeline_index"],
                            "timeline_index": frame["timeline_index"],
                            "start": frame["start"],
                            "end": frame["end"],
                            "tags": selected,
                            "labels_en": labels_en,
                            "labels_zh": labels_zh,
                            "text": "、".join(selected),
                            "source": "ram_plus_general",
                            "model": MODEL,
                            "model_revision": revision,
                            "artifact_path": str(frame["frame_path"]),
                            "artifact_sha256": sha256_file(frame["frame_path"]),
                            "tag_vocabulary": "ram_plus_open_set",
                            "candidate_only": True,
                            "human_review_required": True,
                        }
                    )
                status = "completed"
            except Exception as exc:  # optional local model errors never trigger a remote route
                status = "failed"
                error = {"code": "general_tagger_execution_failed", "message": f"{type(exc).__name__}: {exc}"}

    result = {
        "schema": SCHEMA,
        "status": status,
        "ok": status == "completed",
        "bundle_dir": str(root),
        "implementation": IMPLEMENTATION,
        "model": MODEL,
        "model_revision": sha256_file(checkpoint) if checkpoint is not None else "",
        "source_root": str(source or ""),
        "checkpoint_path": str(checkpoint or ""),
        "device": device,
        "prefer_language": prefer_language,
        "planned_frame_count": len(frames),
        "annotation_count": len(annotations),
        "annotations": annotations,
        "error": error,
        "compatibility_baselines": list(COMPATIBILITY_BASELINES),
        "operator_boundary": {
            "local_only": True,
            "remote_calls_made": 0,
            "automatic_model_download": False,
            "automatic_remote_fallback": False,
            "gpu_required": True,
            "cpu_fallback_allowed": False,
            "candidate_only": True,
            "does_not_overwrite_ocr_asr_or_human_facts": True,
        },
        "artifacts": {
            "json": "exports/general-tagger.json",
            "markdown": "exports/general-tagger.md",
        },
        "updated_at": now_iso(),
    }
    if write:
        _write_result(root, result)
        if status == "completed" and import_annotations:
            imported = import_tagger_annotations(
                root,
                root / "exports" / "general-tagger.json",
                source="ram_plus_general",
                write=True,
            )
            result["timeline_import"] = {
                "status": "completed",
                "updated_count": imported["updated_count"],
                "updated_indexes": imported["updated_indexes"],
            }
            _write_result(root, result)
    return result


def _ram_plus_backend(
    source_root: Path | None,
    checkpoint: Path | None,
    *,
    device: str,
) -> Callable[[Path], dict[str, object]]:
    if source_root is None:
        raise FileNotFoundError("Recognize Anything source is required")
    if checkpoint is None:
        raise FileNotFoundError("RAM++ checkpoint is required")
    tokenizer_root = _tokenizer_root()
    if tokenizer_root is None:
        raise FileNotFoundError("bert-base-uncased tokenizer is required")
    if str(source_root) not in sys.path:
        sys.path.insert(0, str(source_root))
    import torch
    from PIL import Image
    from ram import get_transform, inference_ram
    from ram.models import ram_plus

    if device == "cpu":
        raise RuntimeError("gpu_required_for_local_model")
    if not torch.cuda.is_available():
        raise RuntimeError("cuda_unavailable_gpu_required")
    resolved_device = "cuda"
    transform = get_transform(image_size=384)
    model = ram_plus(
        pretrained=str(checkpoint),
        image_size=384,
        vit="swin_l",
        text_encoder_type=str(tokenizer_root),
    )
    model.class_threshold = torch.clamp(
        model.class_threshold,
        min=DEFAULT_THRESHOLD_FLOOR,
    )
    model.eval()
    model = model.to(torch.device(resolved_device))

    def infer(frame_path: Path) -> dict[str, object]:
        with Image.open(frame_path) as image:
            tensor = transform(image.convert("RGB")).unsqueeze(0).to(torch.device(resolved_device))
        with torch.no_grad():
            output = inference_ram(tensor, model)
        return {
            "tags_en": _split_pipe_labels(output[0] if len(output) > 0 else ""),
            "tags_zh": _split_pipe_labels(output[1] if len(output) > 1 else ""),
        }

    return infer


def _bundle_frames(root: Path, timeline: list[Any]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for position, item in enumerate(timeline, start=1):
        if not isinstance(item, dict):
            continue
        values = item.get("frame_paths") if isinstance(item.get("frame_paths"), list) else []
        if not values and isinstance(item.get("evidence_frame_paths"), list):
            values = item["evidence_frame_paths"]
        integrated = item.get("integrated_visual") if isinstance(item.get("integrated_visual"), dict) else {}
        if not values and isinstance(integrated.get("evidence_frame_paths"), list):
            values = integrated["evidence_frame_paths"]
        if not values and item.get("frame_path"):
            values = [item["frame_path"]]
        frame = _first_image(root, values)
        if frame is None:
            continue
        result.append(
            {
                "timeline_index": _int(item.get("index")) or position,
                "start": _float(item.get("start")),
                "end": _float(item.get("end")),
                "frame_path": frame,
            }
        )
    return result


def _first_image(root: Path, values: list[Any]) -> Path | None:
    for value in values:
        path = Path(str(value)).expanduser()
        if not path.is_absolute():
            path = root / path
        if path.exists() and path.is_file() and path.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp", ".bmp"}:
            return path.resolve()
    return None


def _source_root(
    value: str | Path | None,
    *,
    discovery: dict[str, Any] | None = None,
) -> Path | None:
    candidate = value or os.environ.get("VKP_RECOGNIZE_ANYTHING_SOURCE")
    if candidate:
        path = Path(candidate).expanduser()
        if path.exists() and path.is_dir():
            return path.resolve()
    inventory_path = str((discovery or {}).get("source_root") or "")
    candidate_path = Path(inventory_path).expanduser() if inventory_path else None
    if candidate_path and candidate_path.is_dir():
        return candidate_path.resolve()
    return DEFAULT_SOURCE_ROOT.resolve() if DEFAULT_SOURCE_ROOT.exists() else None


def _checkpoint(
    value: str | Path | None,
    *,
    discovery: dict[str, Any] | None = None,
) -> Path | None:
    candidate = value or os.environ.get("VKP_RAM_PLUS_CHECKPOINT")
    if candidate:
        path = Path(candidate).expanduser()
        if path.exists() and path.is_file():
            return path.resolve()
    inventory_path = str((discovery or {}).get("checkpoint_path") or "")
    candidate_path = Path(inventory_path).expanduser() if inventory_path else None
    if candidate_path and candidate_path.is_file():
        return candidate_path.resolve()
    return DEFAULT_CHECKPOINT.resolve() if DEFAULT_CHECKPOINT.exists() else None


def _tokenizer_root(*, discovery: dict[str, Any] | None = None) -> Path | None:
    candidate = os.environ.get("VKP_RAM_PLUS_TOKENIZER")
    if candidate:
        path = Path(candidate).expanduser()
        if path.exists() and path.is_dir() and (path / "vocab.txt").is_file():
            return path.resolve()
    inventory_path = str((discovery or {}).get("tokenizer_root") or "")
    candidate_path = Path(inventory_path).expanduser() if inventory_path else None
    if candidate_path and candidate_path.is_dir() and (candidate_path / "vocab.txt").is_file():
        return candidate_path.resolve()
    if DEFAULT_TOKENIZER_ROOT.exists() and (DEFAULT_TOKENIZER_ROOT / "vocab.txt").is_file():
        return DEFAULT_TOKENIZER_ROOT.resolve()
    return None


def _inventory_model_discovery(value: str | Path | None = None) -> dict[str, Any]:
    inventory_path = (
        Path(value).expanduser().resolve()
        if value is not None
        else (source_reviews_root() / "SOURCE_INVENTORY.json").resolve()
    )
    result = {
        "source": "source_inventory",
        "inventory_path": str(inventory_path),
        "inventory_available": inventory_path.is_file(),
        "entry_found": False,
        "source_root": "",
        "deployment_path": "",
        "checkpoint_path": "",
        "tokenizer_root": "",
    }
    if not inventory_path.is_file():
        return result
    try:
        payload = read_json(inventory_path)
    except (OSError, ValueError):
        return result
    entries = payload.get("entries") if isinstance(payload, dict) else []
    entry = next(
        (
            row
            for row in entries or []
            if isinstance(row, dict) and str(row.get("name") or "").casefold() == "recognize-anything"
        ),
        None,
    )
    if not isinstance(entry, dict):
        return result
    source_text = str(entry.get("local_path") or "").strip()
    deployment_text = str(entry.get("deployment_path") or "").strip()
    source = Path(source_text).expanduser() if source_text else None
    deployment = Path(deployment_text).expanduser() if deployment_text else None
    checkpoint = deployment / "ram_plus_swin_large_14m.pth" if deployment else None
    tokenizer = deployment.parent / "bert-base-uncased-tokenizer" if deployment else None
    return {
        **result,
        "entry_found": True,
        "source_root": str(source.resolve()) if source and source.is_dir() else "",
        "deployment_path": str(deployment.resolve()) if deployment and deployment.is_dir() else "",
        "checkpoint_path": str(checkpoint.resolve()) if checkpoint and checkpoint.is_file() else "",
        "tokenizer_root": str(tokenizer.resolve()) if tokenizer and tokenizer.is_dir() and (tokenizer / "vocab.txt").is_file() else "",
    }


def _write_result(root: Path, result: dict[str, Any]) -> None:
    exports = root / "exports"
    exports.mkdir(parents=True, exist_ok=True)
    manifest_path = root / "manifest.json"
    with bundle_write_lock(root, operation="general_tagger", timeout_seconds=1.0):
        write_json(exports / "general-tagger.json", result)
        (exports / "general-tagger.md").write_text(_render_markdown(result), encoding="utf-8")
        write_json(
            root / "mcp-general-tagger.args.json",
            {
                "bundle_dir": str(root),
                "source_root": result["source_root"],
                "checkpoint_path": result["checkpoint_path"],
                "device": "cuda",
                "prefer_language": result["prefer_language"],
                "limit": 0,
                "execute": False,
                "import_annotations": True,
                "write": True,
            },
        )
        manifest = read_json(manifest_path) if manifest_path.exists() else {}
        if isinstance(manifest, dict):
            manifest["general_tagger_json"] = "exports/general-tagger.json"
            manifest["general_tagger_markdown"] = "exports/general-tagger.md"
            manifest["mcp_general_tagger_args"] = "mcp-general-tagger.args.json"
            manifest["general_tagger_summary"] = {
                "status": result["status"],
                "model": MODEL,
                "model_revision": result["model_revision"],
                "annotation_count": result["annotation_count"],
                "updated_at": result["updated_at"],
            }
            write_json(manifest_path, manifest)


def _render_markdown(result: dict[str, Any]) -> str:
    lines = [
        "# General Image Tagger",
        "",
        f"- Status: `{result.get('status')}`",
        f"- Model: `{result.get('model')}`",
        f"- Planned frames: `{result.get('planned_frame_count')}`",
        f"- Annotations: `{result.get('annotation_count')}`",
        "- Domain: general real-world images; CL/WD remain compatibility baselines only.",
        "- Boundary: local candidate evidence, no automatic download or remote fallback.",
        "- Device policy: CUDA GPU required; no automatic CPU fallback.",
        "",
        "| Timeline | Tags | Frame SHA-256 |",
        "| ---: | --- | --- |",
    ]
    for row in result.get("annotations") or []:
        lines.append(
            f"| {row.get('timeline_index')} | {_md(', '.join(row.get('tags') or []))} | `{row.get('artifact_sha256')}` |"
        )
    return "\n".join(lines).rstrip() + "\n"


def _labels(value: object) -> list[str]:
    if isinstance(value, list):
        return _unique([str(item).strip() for item in value if str(item).strip()])
    return _split_pipe_labels(str(value or ""))


def _split_pipe_labels(value: str) -> list[str]:
    return _unique([part.strip() for part in str(value or "").split("|") if part.strip()])


def _unique(values: list[str]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        key = value.casefold()
        if key not in seen:
            seen.add(key)
            result.append(value)
    return result


def _int(value: Any) -> int:
    try:
        return int(value or 0)
    except Exception:
        return 0


def _float(value: Any) -> float:
    try:
        return float(value or 0.0)
    except Exception:
        return 0.0


def _md(value: Any) -> str:
    return str(value or "").replace("|", "\\|").replace("\n", " ")
