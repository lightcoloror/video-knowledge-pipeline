from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any


def main() -> int:
    parser = argparse.ArgumentParser(description="Export an auditable frame manifest from a VKP bundle")
    parser.add_argument("bundle_dir")
    args = parser.parse_args()
    root = Path(args.bundle_dir).expanduser().resolve()
    timeline = _read(root / "timeline.json", [])
    bundle_manifest = _read(root / "manifest.json", {})
    media_path = _media_path(timeline, bundle_manifest)
    rows = []
    seen: set[str] = set()
    for item in timeline if isinstance(timeline, list) else []:
        if not isinstance(item, dict):
            continue
        evidence = ((item.get("integrated_visual") or {}).get("evidence_frame_paths") or [])
        temporal = item.get("temporal_frame_paths") or []
        assets = [asset.get("source") or asset.get("path") for asset in item.get("assets") or [] if isinstance(asset, dict)]
        for role, values in (("keyframe", [*assets, *evidence]), ("temporal_frame", temporal)):
            for value in values:
                path = _resolve(root, value)
                key = str(path).lower()
                if key in seen:
                    continue
                seen.add(key)
                rows.append({
                    "timeline_index": item.get("index"),
                    "start_seconds": item.get("start"),
                    "end_seconds": item.get("end"),
                    "role": role,
                    "path": str(path),
                    "exists": path.exists(),
                    "sha256": _sha256(path) if path.exists() else "",
                    "evidence_status": "available" if path.exists() else "missing",
                })
    result = {
        "schema": "video_knowledge_pipeline.frame_manifest.v1",
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "bundle_dir": str(root),
        "source_media_path": str(media_path or ""),
        "source_media_sha256": _sha256(media_path) if media_path and media_path.exists() else "",
        "extractor": {"name": "ffmpeg", "version": _ffmpeg_version()},
        "frame_count": len(rows),
        "available_frame_count": sum(1 for row in rows if row["exists"]),
        "missing_frame_count": sum(1 for row in rows if not row["exists"]),
        "frames": rows,
        "operator_boundary": {"local_only": True, "no_external_vision": True, "no_upload": True},
    }
    path = root / "frame-manifest.json"
    path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    if isinstance(bundle_manifest, dict):
        bundle_manifest["frame_manifest"] = "frame-manifest.json"
        (root / "manifest.json").write_text(json.dumps(bundle_manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"ok": True, "path": str(path), "frame_count": len(rows), "missing": result["missing_frame_count"]}, ensure_ascii=False))
    return 0


def _read(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8-sig"))


def _resolve(root: Path, value: Any) -> Path:
    path = Path(str(value or "")).expanduser()
    return path.resolve() if path.is_absolute() else (root / path).resolve()


def _media_path(timeline: Any, manifest: Any) -> Path | None:
    if isinstance(timeline, list):
        for item in timeline:
            if isinstance(item, dict) and item.get("video_key"):
                path = Path(str(item["video_key"])).expanduser().resolve()
                if path.exists():
                    return path
    if isinstance(manifest, dict):
        for key in ("media_path", "source_media_path", "video_path"):
            if manifest.get(key):
                path = Path(str(manifest[key])).expanduser().resolve()
                if path.exists():
                    return path
    return None


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _ffmpeg_version() -> str:
    try:
        completed = subprocess.run(["ffmpeg", "-version"], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=20, check=False)
        return (completed.stdout.splitlines() or [""])[0]
    except Exception as exc:
        return f"unavailable: {exc}"


if __name__ == "__main__":
    raise SystemExit(main())