from __future__ import annotations

from pathlib import Path
from typing import Any, Iterable

from .artifact_freshness import build_dependency_snapshot, canonical_json_sha256
from .artifact_validation import artifact_evidence, normalise_allowed_roots, validated_local_file
from .models import now_iso
from .run_artifact_registry import register_bundle_run
from .storage import read_json, write_json


GENERATION_TASK_SCHEMA = "video_creation_pipeline.generation_task.v1"
GENERATION_RECEIPT_SCHEMA = "video_creation_pipeline.generation_receipt.v1"
GENERATION_VALIDATION_SCHEMA = "video_creation_pipeline.generation_validation.v1"
CAPABILITY_PREFLIGHT_SCHEMA = "video_creation_pipeline.capability_preflight.v1"
PREVIS_SCENE_SCHEMA = "video_creation_pipeline.previs_scene.v1"
PREVIS_CAPTURE_MANIFEST_SCHEMA = "video_creation_pipeline.previs_capture_manifest.v1"
PREVIS_CAPTURE_VALIDATION_SCHEMA = "video_creation_pipeline.previs_capture_validation.v1"

GENERATION_IMPORT_SCHEMA = "video_knowledge_pipeline.generation_contract_import.v1"
PREVIS_EVIDENCE_SCHEMA = "video_knowledge_pipeline.previs_candidate_evidence.v1"


def import_generation_contracts(
    bundle_dir: str | Path,
    *,
    task_path: str | Path,
    receipt_path: str | Path,
    validation_path: str | Path,
    preflight_path: str | Path | None = None,
    allowed_roots: Iterable[str | Path] | None = None,
    write: bool = True,
) -> dict[str, Any]:
    """Import already-validated video-creation generation contracts.

    VKP intentionally does not reproduce the upstream executor or verifier.
    The fixed video-creation CLI remains responsible for creating and fully
    verifying the contracts; this bridge checks their bindings and authority
    boundary before copying them into the Bundle as candidate evidence.
    """

    root = _bundle_root(bundle_dir)
    roots = _source_roots(root, allowed_roots)
    task_source, task = _read_contract(task_path, "generation task", GENERATION_TASK_SCHEMA, roots)
    receipt_source, receipt = _read_contract(receipt_path, "generation receipt", GENERATION_RECEIPT_SCHEMA, roots)
    validation_source, validation = _read_contract(
        validation_path, "generation validation", GENERATION_VALIDATION_SCHEMA, roots
    )
    _validate_generation_binding(task, receipt, validation)
    _validate_generation_artifacts(receipt, roots)

    preflight_reference = task.get("capability_preflight")
    if not isinstance(preflight_reference, dict):
        raise ValueError("generation task lacks capability_preflight evidence")
    resolved_preflight = preflight_path or str(preflight_reference.get("path") or "")
    preflight_source, preflight = _read_contract(
        resolved_preflight, "capability preflight", CAPABILITY_PREFLIGHT_SCHEMA, roots
    )
    _validate_reference(preflight_source, preflight_reference, "capability preflight")
    capability = str(task.get("required_capability") or "")
    capability_result = _capability_result(preflight, capability)

    imported = _import_contract_set(
        root,
        {
            "generation-task": (task_source, task),
            "generation-receipt": (receipt_source, receipt),
            "generation-validation": (validation_source, validation),
            "capability-preflight": (preflight_source, preflight),
        },
    )
    snapshot = build_dependency_snapshot(
        root,
        subject="generation-contract-import",
        inputs=[{"role": role, "path": path} for role, path in imported.items()],
        source_run_id=str(task.get("task_id") or ""),
        producer_schema=GENERATION_VALIDATION_SCHEMA,
    )
    representative_frames = _representative_frames(receipt)
    status = str(receipt.get("status") or "")
    result: dict[str, Any] = {
        "schema": GENERATION_IMPORT_SCHEMA,
        "generated_at": now_iso(),
        "bundle_dir": str(root),
        "status": "completed" if status == "completed" else "degraded",
        "upstream_status": status,
        "task_id": str(task.get("task_id") or ""),
        "task_sha256": str(task.get("task_sha256") or ""),
        "generator": str(task.get("generator") or ""),
        "required_capability": capability,
        "capability_preflight": capability_result,
        "technical_verification": dict(receipt.get("technical_verification") or {}),
        "visual_verification": {
            "inspected": bool((receipt.get("visual_verification") or {}).get("inspected")),
            "blank": bool((receipt.get("visual_verification") or {}).get("blank")),
            "black": bool((receipt.get("visual_verification") or {}).get("black")),
            "wrong_composition": bool((receipt.get("visual_verification") or {}).get("wrong_composition")),
            "representative_frames": representative_frames,
        },
        "validation": dict(validation),
        "imported_contracts": {role: str(path.relative_to(root)) for role, path in imported.items()},
        "dependency_snapshot": snapshot,
        "authority_boundary": {
            "candidate_only": True,
            "mutates_vkp_timeline": False,
            "publishing_allowed": False,
            "silent_fallback_allowed": False,
            "upstream_verifier": "video-creative-contracts verify-generation-receipt",
        },
    }
    if write:
        output_json = root / "exports" / "generation-contract-import.json"
        output_md = root / "exports" / "generation-contract-import.md"
        snapshot_path = root / "exports" / "generation-contract-dependency-snapshot.json"
        write_json(output_json, result)
        output_md.write_text(_generation_markdown(result), encoding="utf-8")
        write_json(snapshot_path, snapshot)
        _update_manifest(
            root,
            {
                "generation_contract_import_json": "exports/generation-contract-import.json",
                "generation_contract_import_markdown": "exports/generation-contract-import.md",
                "generation_contract_dependency_snapshot": "exports/generation-contract-dependency-snapshot.json",
            },
        )
        run_status = "completed" if status == "completed" else "needs_review"
        register_bundle_run(
            root,
            run_type="generation_contract_import",
            run_id=f"generation-{str(task.get('task_id') or 'candidate')}",
            status=run_status,
            title="生成能力预检与代表帧证据",
            summary=(
                f"Imported {task.get('generator')} candidate; capability {capability} is ready; "
                f"representative frames: {len(representative_frames)}."
            ),
            inputs={"task_id": task.get("task_id"), "task_sha256": task.get("task_sha256")},
            parameters={
                "generator": task.get("generator"),
                "required_capability": capability,
                "probe_method": capability_result.get("probe_method"),
                "candidate_only": True,
            },
            artifacts=[output_json, output_md, snapshot_path, *imported.values()],
            failed_items=(
                []
                if status == "completed"
                else [{"id": task.get("task_id"), "reason": status, "detail": receipt.get("error", "")}]
            ),
            retry_command="video-creative-contracts verify-generation-receipt --task <task.json> --receipt <receipt.json>",
            next_actions=["在 Workbench 检查代表帧与构图；候选结果不得直接发布或覆盖 Timeline。"],
            operator_boundary=result["authority_boundary"],
            dependency_snapshot=snapshot,
            write=True,
        )
        result["paths"] = {"json": str(output_json), "markdown": str(output_md), "snapshot": str(snapshot_path)}
    return result


def import_previs_candidate(
    bundle_dir: str | Path,
    *,
    scene_path: str | Path,
    manifest_path: str | Path,
    validation_path: str | Path,
    allowed_roots: Iterable[str | Path] | None = None,
    write: bool = True,
) -> dict[str, Any]:
    """Import fixed-upstream 3D previs captures as synthetic candidate evidence."""

    root = _bundle_root(bundle_dir)
    roots = _source_roots(root, allowed_roots)
    scene_source, scene = _read_contract(scene_path, "previs scene", PREVIS_SCENE_SCHEMA, roots)
    capture_source, capture_manifest = _read_contract(
        manifest_path, "previs capture manifest", PREVIS_CAPTURE_MANIFEST_SCHEMA, roots
    )
    validation_source, validation = _read_contract(
        validation_path, "previs capture validation", PREVIS_CAPTURE_VALIDATION_SCHEMA, roots
    )
    cameras, captures = _validate_previs_binding(scene, capture_manifest, validation, roots)
    imported = _import_contract_set(
        root,
        {
            "previs-scene": (scene_source, scene),
            "previs-capture-manifest": (capture_source, capture_manifest),
            "previs-capture-validation": (validation_source, validation),
        },
    )
    snapshot = build_dependency_snapshot(
        root,
        subject="previs-candidate-evidence",
        inputs=[{"role": role, "path": path} for role, path in imported.items()],
        source_run_id=str((scene.get("scene") or {}).get("scene_id") or ""),
        producer_schema=PREVIS_CAPTURE_VALIDATION_SCHEMA,
    )
    result: dict[str, Any] = {
        "schema": PREVIS_EVIDENCE_SCHEMA,
        "generated_at": now_iso(),
        "bundle_dir": str(root),
        "status": "needs_review",
        "scene": dict(scene.get("scene") or {}),
        "active_camera_id": str(scene.get("active_camera_id") or ""),
        "cameras": cameras,
        "captures": captures,
        "validation": dict(validation),
        "imported_contracts": {role: str(path.relative_to(root)) for role, path in imported.items()},
        "dependency_snapshot": snapshot,
        "authority_boundary": {
            "synthetic": True,
            "candidate_only": True,
            "observed_video_fact": False,
            "mutates_vkp_timeline": False,
            "final_render_claimed": False,
            "human_confirmation_required": True,
            "upstream_verifier": "video-creative-contracts verify-previs-captures",
        },
    }
    if write:
        output_json = root / "exports" / "previs-candidate-evidence.json"
        output_md = root / "exports" / "previs-candidate-evidence.md"
        snapshot_path = root / "exports" / "previs-candidate-dependency-snapshot.json"
        write_json(output_json, result)
        output_md.write_text(_previs_markdown(result), encoding="utf-8")
        write_json(snapshot_path, snapshot)
        _update_manifest(
            root,
            {
                "previs_candidate_evidence_json": "exports/previs-candidate-evidence.json",
                "previs_candidate_evidence_markdown": "exports/previs-candidate-evidence.md",
                "previs_candidate_dependency_snapshot": "exports/previs-candidate-dependency-snapshot.json",
            },
        )
        scene_id = str((scene.get("scene") or {}).get("scene_id") or "candidate")
        register_bundle_run(
            root,
            run_type="previs_candidate_import",
            run_id=f"previs-{scene_id}",
            status="needs_review",
            title="3D 预演候选证据",
            summary=f"Imported {len(captures)} synthetic capture(s) from {len(cameras)} camera(s); human review required.",
            inputs={"scene_id": scene_id, "previs_scene_sha256": scene.get("previs_scene_sha256")},
            parameters={"synthetic": True, "candidate_only": True, "observed_video_fact": False},
            artifacts=[output_json, output_md, snapshot_path, *imported.values()],
            retry_command="video-creative-contracts verify-previs-captures --scene <scene.json> --manifest <captures.json>",
            next_actions=["人工确认相机意图与构图后，方可作为 temporal visual candidate；禁止写回观察事实。"],
            operator_boundary=result["authority_boundary"],
            dependency_snapshot=snapshot,
            write=True,
        )
        result["paths"] = {"json": str(output_json), "markdown": str(output_md), "snapshot": str(snapshot_path)}
    return result


def _validate_generation_binding(
    task: dict[str, Any], receipt: dict[str, Any], validation: dict[str, Any]
) -> None:
    if task.get("task_sha256") != _payload_sha256(task, "task_sha256"):
        raise ValueError("generation task integrity check failed")
    policy = task.get("execution_policy") if isinstance(task.get("execution_policy"), dict) else {}
    if (
        policy.get("claim_after_preflight") is not True
        or policy.get("implicit_install_allowed") is not False
        or policy.get("silent_generator_fallback") is not False
    ):
        raise ValueError("generation task execution policy is unsafe")
    completion = task.get("completion_requirements") if isinstance(task.get("completion_requirements"), dict) else {}
    if (
        completion.get("technical_probe_required") is not True
        or completion.get("representative_frame_review_required") is not True
        or completion.get("acceptance_status") != "candidate_only"
    ):
        raise ValueError("generation task completion requirements are incomplete")
    if receipt.get("task_id") != task.get("task_id") or receipt.get("task_sha256") != task.get("task_sha256"):
        raise ValueError("generation receipt does not bind the exact task")
    if receipt.get("generator") != task.get("generator"):
        raise ValueError("generation receipt generator differs from the task")
    if receipt.get("published") is not False or receipt.get("fallback_used") is not False:
        raise ValueError("generation receipt reports publishing or fallback")
    status = str(receipt.get("status") or "")
    if status not in {"completed", "failed", "cancelled"}:
        raise ValueError("generation receipt status is invalid")
    if validation.get("valid") is not True:
        raise ValueError("upstream generation validation did not pass")
    for field in ("task_id", "task_sha256", "status"):
        if validation.get(field) != (task.get(field) if field != "status" else receipt.get("status")):
            raise ValueError(f"generation validation {field} binding differs")
    if validation.get("acceptance_status") != "candidate_only":
        raise ValueError("generation validation is not candidate-only")
    if status == "completed":
        technical = receipt.get("technical_verification") if isinstance(receipt.get("technical_verification"), dict) else {}
        visual = receipt.get("visual_verification") if isinstance(receipt.get("visual_verification"), dict) else {}
        if not str(technical.get("probe_method") or "").strip():
            raise ValueError("completed generation lacks a technical probe")
        if visual.get("inspected") is not True:
            raise ValueError("completed generation lacks visual inspection")
        if any(visual.get(field) is not False for field in ("blank", "black", "wrong_composition")):
            raise ValueError("completed generation failed visual inspection")
        frames = visual.get("representative_frames") if isinstance(visual.get("representative_frames"), list) else []
        if not frames or validation.get("representative_frame_count") != len(frames):
            raise ValueError("representative frame evidence is incomplete")
    elif not str(receipt.get("error") or "").strip():
        raise ValueError("failed or cancelled generation lacks a visible reason")


def _capability_result(preflight: dict[str, Any], capability: str) -> dict[str, Any]:
    rows = preflight.get("capabilities") if isinstance(preflight.get("capabilities"), list) else []
    matches = [row for row in rows if isinstance(row, dict) and row.get("id") == capability]
    if len(matches) != 1:
        raise ValueError(f"capability preflight must contain exactly one {capability} result")
    row = dict(matches[0])
    if row.get("ready") is not True or row.get("installation_performed") is not False:
        raise ValueError(f"required capability is not preflight-ready: {capability}")
    if str(row.get("probe_method") or "") not in {
        "existing_runtime",
        "registered_tool_health_check",
        "provider_capability_receipt",
        "manual_operator_verification",
    }:
        raise ValueError("capability preflight probe method is not auditable")
    return row


def _validate_generation_artifacts(
    receipt: dict[str, Any], roots: tuple[Path, ...]
) -> None:
    if str(receipt.get("status") or "") != "completed":
        return
    output = receipt.get("output") if isinstance(receipt.get("output"), dict) else {}
    output_path = validated_local_file(
        str(output.get("path") or ""), label="generated output", allowed_roots=roots
    )
    _validate_reference(output_path, output, "generated output")
    for index, frame in enumerate(_representative_frames(receipt), start=1):
        path = validated_local_file(
            str(frame.get("path") or ""),
            label=f"representative frame {index}",
            allowed_roots=roots,
        )
        _validate_reference(path, frame, f"representative frame {index}")

def _validate_previs_binding(
    scene: dict[str, Any],
    manifest: dict[str, Any],
    validation: dict[str, Any],
    roots: tuple[Path, ...],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    if scene.get("previs_scene_sha256") != _payload_sha256(scene, "previs_scene_sha256"):
        raise ValueError("previs scene integrity check failed")
    boundary = scene.get("authority_boundary") if isinstance(scene.get("authority_boundary"), dict) else {}
    if (
        boundary.get("derived_artifact") is not True
        or boundary.get("browser_local_storage_authoritative") is not False
        or boundary.get("vkp_timeline_mutated") is not False
        or boundary.get("final_render_claimed") is not False
        or boundary.get("acceptance_status") != "candidate_only"
    ):
        raise ValueError("previs authority boundary is invalid")
    if manifest.get("previs_scene_sha256") != scene.get("previs_scene_sha256"):
        raise ValueError("capture manifest does not bind the exact previs scene")
    if manifest.get("acceptance_status") != "candidate_only" or manifest.get("final_render_claimed") is not False:
        raise ValueError("previs capture manifest exceeds candidate authority")
    if validation.get("valid") is not True or validation.get("previs_scene_sha256") != scene.get("previs_scene_sha256"):
        raise ValueError("previs validation does not bind the exact scene")
    if validation.get("acceptance_status") != "candidate_only":
        raise ValueError("previs validation is not candidate-only")
    cameras = [dict(row) for row in scene.get("cameras") or [] if isinstance(row, dict)]
    if not cameras:
        raise ValueError("previs scene requires cameras")
    camera_by_id = {str(row.get("camera_id") or ""): row for row in cameras}
    if len(camera_by_id) != len(cameras) or not all(camera_by_id):
        raise ValueError("previs camera ids must be unique and non-empty")
    captures = [dict(row) for row in manifest.get("captures") or [] if isinstance(row, dict)]
    if not captures or validation.get("capture_count") != len(captures):
        raise ValueError("previs capture evidence is incomplete")
    normalized: list[dict[str, Any]] = []
    seen: set[str] = set()
    for capture in captures:
        capture_id = str(capture.get("capture_id") or "")
        if not capture_id or capture_id in seen:
            raise ValueError("previs capture ids must be unique and non-empty")
        seen.add(capture_id)
        camera = camera_by_id.get(str(capture.get("camera_id") or ""))
        if camera is None:
            raise ValueError(f"previs capture references unknown camera: {capture_id}")
        for key, expected in (
            ("fov", camera.get("fov")),
            ("position", camera.get("position")),
            ("target", camera.get("target")),
            ("width", (camera.get("frame") or {}).get("width")),
            ("height", (camera.get("frame") or {}).get("height")),
        ):
            if capture.get(key) != expected:
                raise ValueError(f"previs capture camera metadata drifted: {capture_id}/{key}")
        artifact = capture.get("artifact") if isinstance(capture.get("artifact"), dict) else {}
        artifact_path = validated_local_file(
            str(artifact.get("path") or ""), label=f"previs capture {capture_id}", allowed_roots=roots
        )
        _validate_reference(artifact_path, artifact, f"previs capture {capture_id}")
        normalized.append({**capture, "artifact": dict(artifact), "synthetic": True, "observed_video_fact": False})
    return cameras, normalized


def _representative_frames(receipt: dict[str, Any]) -> list[dict[str, Any]]:
    visual = receipt.get("visual_verification") if isinstance(receipt.get("visual_verification"), dict) else {}
    return [dict(row) for row in visual.get("representative_frames") or [] if isinstance(row, dict)]


def _read_contract(
    source: str | Path,
    label: str,
    schema: str,
    roots: tuple[Path, ...],
) -> tuple[Path, dict[str, Any]]:
    path = validated_local_file(source, label=label, allowed_roots=roots)
    payload = read_json(path)
    if not isinstance(payload, dict):
        raise ValueError(f"{label} must be a JSON object")
    if payload.get("schema") != schema:
        raise ValueError(f"unsupported {label} schema: {payload.get('schema')}")
    return path, payload


def _validate_reference(path: Path, reference: dict[str, Any], label: str) -> None:
    evidence = artifact_evidence(path)
    expected = {
        "bytes": int(evidence["bytes"]),
        "sha256": str(evidence["sha256"]),
    }
    if reference.get("bytes") != expected["bytes"] or reference.get("sha256") != expected["sha256"]:
        raise ValueError(f"{label} changed after the upstream contract was created")
    if reference.get("content_kind") == "json":
        value = read_json(path)
        if reference.get("canonical_sha256") != canonical_json_sha256(value):
            raise ValueError(f"{label} canonical JSON changed after contract creation")


def _import_contract_set(
    root: Path, contracts: dict[str, tuple[Path, dict[str, Any]]]
) -> dict[str, Path]:
    destination = root / "imports" / "video-creation-contracts"
    imported: dict[str, Path] = {}
    for role, (_source, payload) in contracts.items():
        digest = canonical_json_sha256(payload)
        output = destination / f"{role}-{digest[:12]}.json"
        write_json(output, payload)
        imported[role] = output
    return imported


def _payload_sha256(payload: dict[str, Any], hash_field: str) -> str:
    value = dict(payload)
    value.pop(hash_field, None)
    return canonical_json_sha256(value)


def _source_roots(root: Path, values: Iterable[str | Path] | None) -> tuple[Path, ...]:
    if values is None:
        return (root,)
    return normalise_allowed_roots(list(values), default_root=root)


def _bundle_root(value: str | Path) -> Path:
    root = Path(value).expanduser().resolve()
    if not (root / "manifest.json").is_file() or not (root / "timeline.json").is_file():
        raise FileNotFoundError(f"VKP Bundle requires manifest.json and timeline.json: {root}")
    return root


def _update_manifest(root: Path, values: dict[str, Any]) -> None:
    manifest_path = root / "manifest.json"
    manifest = read_json(manifest_path)
    if not isinstance(manifest, dict):
        raise ValueError("manifest.json must be a JSON object")
    manifest.update(values)
    write_json(manifest_path, manifest)


def _generation_markdown(result: dict[str, Any]) -> str:
    capability = result.get("capability_preflight") or {}
    visual = result.get("visual_verification") or {}
    technical = result.get("technical_verification") or {}
    lines = [
        "# Generation Contract Import",
        "",
        f"- Status: `{result.get('status', '')}`",
        f"- Task: `{result.get('task_id', '')}`",
        f"- Generator: `{result.get('generator', '')}`",
        f"- Capability: `{result.get('required_capability', '')}`",
        f"- Preflight ready: `{capability.get('ready', False)}` via `{capability.get('probe_method', '')}`",
        f"- Technical probe: `{technical.get('probe_method', '')}`",
        f"- Representative frames: `{len(visual.get('representative_frames') or [])}`",
        "",
        "> Candidate evidence only. No Timeline mutation, publication, implicit install, or silent fallback is authorized.",
    ]
    return "\n".join(lines).rstrip() + "\n"


def _previs_markdown(result: dict[str, Any]) -> str:
    scene = result.get("scene") or {}
    lines = [
        "# 3D Previs Candidate Evidence",
        "",
        f"- Status: `{result.get('status', '')}`",
        f"- Scene: `{scene.get('scene_id', '')}`",
        f"- Cameras: `{len(result.get('cameras') or [])}`",
        f"- Captures: `{len(result.get('captures') or [])}`",
        "",
        "> Synthetic candidate only. It is not an observed fact from the source video and cannot mutate Timeline without human confirmation.",
    ]
    return "\n".join(lines).rstrip() + "\n"
