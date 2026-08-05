from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from video_knowledge_pipeline.artifact_freshness import canonical_json_sha256
from video_knowledge_pipeline.creative_contract_bridge import (
    import_generation_contracts,
    import_previs_candidate,
)
from video_knowledge_pipeline.storage import read_json, write_json


def _bundle(tmp_path: Path) -> Path:
    root = tmp_path / "bundle"
    root.mkdir()
    write_json(root / "manifest.json", {"title": "fixture"})
    write_json(root / "timeline.json", [])
    return root


def _reference(path: Path) -> dict[str, object]:
    raw = path.read_bytes()
    payload = json.loads(path.read_text(encoding="utf-8")) if path.suffix == ".json" else None
    return {
        "path": str(path.resolve()),
        "bytes": len(raw),
        "sha256": hashlib.sha256(raw).hexdigest(),
        "content_kind": "json" if payload is not None else "binary",
        "canonical_sha256": canonical_json_sha256(payload) if payload is not None else None,
    }


def _generation_contracts(root: Path) -> tuple[Path, Path, Path, Path]:
    preflight_path = root / "preflight.json"
    write_json(
        preflight_path,
        {
            "schema": "video_creation_pipeline.capability_preflight.v1",
            "checked_at": "2026-07-22T00:00:00+00:00",
            "capabilities": [
                {
                    "id": "hyperframes_render",
                    "ready": True,
                    "installation_performed": False,
                    "probe_method": "registered_tool_health_check",
                    "detail": "fixed runtime",
                }
            ],
        },
    )
    task = {
        "schema": "video_creation_pipeline.generation_task.v1",
        "task_id": "task-1",
        "generator": "hyperframes",
        "required_capability": "hyperframes_render",
        "capability_preflight": _reference(preflight_path),
        "execution_policy": {
            "claim_after_preflight": True,
            "implicit_install_allowed": False,
            "silent_generator_fallback": False,
            "network_execution_performed": False,
            "render_execution_performed": False,
        },
        "completion_requirements": {
            "technical_probe_required": True,
            "representative_frame_review_required": True,
            "acceptance_status": "candidate_only",
        },
    }
    task["task_sha256"] = canonical_json_sha256(task)
    task_path = root / "task.json"
    write_json(task_path, task)
    frame_path = root / "representative.png"
    frame_path.write_bytes(b"png-fixture")
    output_path = root / "output.mp4"
    output_path.write_bytes(b"video-fixture")
    receipt = {
        "schema": "video_creation_pipeline.generation_receipt.v1",
        "task_id": "task-1",
        "task_sha256": task["task_sha256"],
        "generator": "hyperframes",
        "status": "completed",
        "published": False,
        "fallback_used": False,
        "output": _reference(output_path),
        "technical_verification": {
            "probe_method": "ffprobe-json",
            "width": 1080,
            "height": 1920,
            "duration_s": 8.0,
            "has_video_stream": True,
        },
        "visual_verification": {
            "inspected": True,
            "blank": False,
            "black": False,
            "wrong_composition": False,
            "representative_frames": [_reference(frame_path)],
        },
    }
    receipt_path = root / "receipt.json"
    write_json(receipt_path, receipt)
    validation_path = root / "validation.json"
    write_json(
        validation_path,
        {
            "schema": "video_creation_pipeline.generation_validation.v1",
            "valid": True,
            "task_id": "task-1",
            "task_sha256": task["task_sha256"],
            "status": "completed",
            "representative_frame_count": 1,
            "acceptance_status": "candidate_only",
            "next_action": "human_review",
        },
    )
    return task_path, receipt_path, validation_path, preflight_path


def test_generation_contract_import_registers_candidate_evidence(tmp_path: Path) -> None:
    root = _bundle(tmp_path)
    task, receipt, validation, preflight = _generation_contracts(root)

    result = import_generation_contracts(
        root,
        task_path=task,
        receipt_path=receipt,
        validation_path=validation,
        preflight_path=preflight,
    )

    assert result["status"] == "completed"
    assert result["authority_boundary"]["candidate_only"] is True
    assert result["authority_boundary"]["mutates_vkp_timeline"] is False
    assert result["capability_preflight"]["probe_method"] == "registered_tool_health_check"
    assert len(result["visual_verification"]["representative_frames"]) == 1
    assert (root / "exports" / "generation-contract-import.json").is_file()
    registry = read_json(root / "run-artifact-registry.json")
    row = next(item for item in registry["runs"] if item["run_type"] == "generation_contract_import")
    assert row["freshness"]["status"] == "fresh"


def test_generation_contract_import_rejects_silent_fallback(tmp_path: Path) -> None:
    root = _bundle(tmp_path)
    task_path, receipt, validation, preflight = _generation_contracts(root)
    task = read_json(task_path)
    task["execution_policy"]["silent_generator_fallback"] = True
    task["task_sha256"] = canonical_json_sha256({key: value for key, value in task.items() if key != "task_sha256"})
    write_json(task_path, task)

    with pytest.raises(ValueError, match="unsafe"):
        import_generation_contracts(
            root,
            task_path=task_path,
            receipt_path=receipt,
            validation_path=validation,
            preflight_path=preflight,
            write=False,
        )


def _previs_contracts(root: Path) -> tuple[Path, Path, Path]:
    scene = {
        "schema": "video_creation_pipeline.previs_scene.v1",
        "scene": {"scene_id": "scene-1", "name": "Candidate", "timeline_indexes": [1]},
        "cameras": [
            {
                "camera_id": "camera-main",
                "fov": 50.0,
                "position": [0.0, 1.6, 5.0],
                "target": [0.0, 1.5, 0.0],
                "frame": {"width": 1080, "height": 1920},
            }
        ],
        "active_camera_id": "camera-main",
        "authority_boundary": {
            "derived_artifact": True,
            "browser_local_storage_authoritative": False,
            "vkp_timeline_mutated": False,
            "final_render_claimed": False,
            "acceptance_status": "candidate_only",
        },
    }
    scene["previs_scene_sha256"] = canonical_json_sha256(scene)
    scene_path = root / "previs-scene.json"
    write_json(scene_path, scene)
    capture_path = root / "previs.png"
    capture_path.write_bytes(b"previs-fixture")
    manifest_path = root / "previs-manifest.json"
    write_json(
        manifest_path,
        {
            "schema": "video_creation_pipeline.previs_capture_manifest.v1",
            "previs_scene_sha256": scene["previs_scene_sha256"],
            "acceptance_status": "candidate_only",
            "final_render_claimed": False,
            "captures": [
                {
                    "capture_id": "capture-1",
                    "camera_id": "camera-main",
                    "fov": 50.0,
                    "position": [0.0, 1.6, 5.0],
                    "target": [0.0, 1.5, 0.0],
                    "width": 1080,
                    "height": 1920,
                    "artifact": _reference(capture_path),
                }
            ],
        },
    )
    validation_path = root / "previs-validation.json"
    write_json(
        validation_path,
        {
            "schema": "video_creation_pipeline.previs_capture_validation.v1",
            "valid": True,
            "previs_scene_sha256": scene["previs_scene_sha256"],
            "capture_count": 1,
            "acceptance_status": "candidate_only",
            "next_action": "human_previs_review",
        },
    )
    return scene_path, manifest_path, validation_path


def test_previs_import_stays_synthetic_candidate_only(tmp_path: Path) -> None:
    root = _bundle(tmp_path)
    scene, manifest, validation = _previs_contracts(root)

    result = import_previs_candidate(
        root,
        scene_path=scene,
        manifest_path=manifest,
        validation_path=validation,
    )

    assert result["status"] == "needs_review"
    assert result["captures"][0]["synthetic"] is True
    assert result["captures"][0]["observed_video_fact"] is False
    assert result["authority_boundary"]["mutates_vkp_timeline"] is False
    assert (root / "exports" / "previs-candidate-evidence.json").is_file()


def test_previs_import_rejects_camera_metadata_drift(tmp_path: Path) -> None:
    root = _bundle(tmp_path)
    scene, manifest_path, validation = _previs_contracts(root)
    manifest = read_json(manifest_path)
    manifest["captures"][0]["fov"] = 80.0
    write_json(manifest_path, manifest)

    with pytest.raises(ValueError, match="metadata drifted"):
        import_previs_candidate(
            root,
            scene_path=scene,
            manifest_path=manifest_path,
            validation_path=validation,
            write=False,
        )
