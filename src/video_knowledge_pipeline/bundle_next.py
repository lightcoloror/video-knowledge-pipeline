from __future__ import annotations

from pathlib import Path
from typing import Any

from .bundle_assets import repair_bundle_assets
from .config import public_vision_provider_profile, resolve_vision_execution_profile
from .frame_recapture import run_frame_recapture_plan
from .knowledge_coverage import audit_knowledge_coverage
from .lecture_workflow import refresh_lecture_review_outputs
from .models import now_iso
from .ocr_backfill import run_ocr_backfill
from .multimodal_frame_analyzer import run_multimodal_frame_analysis
from .repair_status import refresh_bundle_repair_status
from .storage import append_jsonl, read_json, read_jsonl, write_json
from .temporal_frame_groups import run_temporal_frame_groups
from .temporal_visual_analyzer import run_temporal_visual_analysis
from .video_frame_router import run_video_frame_router
from .vision_preflight import vision_execution_preflight
from .visual_structure import run_visual_structure_plan


def bundle_next_action(bundle_dir: str | Path, *, refresh: bool = True) -> dict[str, Any]:
    """Recommend the next safe action for an existing WebUI lecture bundle."""
    root = Path(bundle_dir).expanduser().resolve()
    manifest_path = root / "manifest.json"
    if not manifest_path.exists():
        raise FileNotFoundError(f"manifest not found: {manifest_path}")
    if refresh:
        refresh_bundle_repair_status(root)
        audit_knowledge_coverage(root, write=True)
    manifest = read_json(manifest_path)
    if not isinstance(manifest, dict):
        raise ValueError("manifest.json must be a JSON object")

    action = (
        _next_knowledge_coverage_action(root, manifest)
        or _next_repair_action(root, manifest)
        or _next_readiness_action(root, manifest)
        or _export_action(root, manifest)
    )
    action = _provider_health_override(root, manifest, action)
    result = {
        "bundle_dir": str(root),
        "manifest_path": str(manifest_path),
        "refreshed": bool(refresh),
        "status": action["status"],
        "next_action": action,
        "safe_smoke_action": _safe_smoke_action(root, manifest, action),
    }
    args_path = root / "mcp-bundle-next-action.args.json"
    write_json(args_path, {"bundle_dir": str(root), "refresh": True})
    result["mcp_args_path"] = str(args_path)
    return result


def bundle_advance(
    bundle_dir: str | Path,
    *,
    execute: bool = False,
    refresh_outputs: bool = False,
    vault: str | Path | None = None,
    folder: str = "00_Inbox/AI/课程视频知识包",
    timeout_seconds: int = 30,
    ocr_input_json: str | Path | None = None,
    ocr_language: str = "chi_sim",
    captiocr_root: str | Path | None = None,
    visual_structure_input_json: str | Path | None = None,
    provider_config: dict[str, Any] | None = None,
    multimodal_limit: int | None = None,
    temporal_limit: int | None = None,
    frame_count: int | None = None,
    confirm_vision_calls: int | None = None,
    confirm_vision_indexes: str = "",
) -> dict[str, Any]:
    """Advance one safe bundle step based on bundle_next_action."""
    root = Path(bundle_dir).expanduser().resolve()
    profile = resolve_vision_execution_profile(
        provider_config=provider_config,
        multimodal_limit=multimodal_limit,
        temporal_limit=temporal_limit,
        frame_count=frame_count,
    )
    before = bundle_next_action(root, refresh=True)
    action = before.get("next_action") if isinstance(before.get("next_action"), dict) else {}
    key = str(action.get("key") or "")
    status = str(action.get("status") or "")
    result: dict[str, Any] | None = None
    advanced = False
    blocked_reason = ""

    if status in {"repair_pending", "coverage_blocked"}:
        result, advanced, blocked_reason = _advance_machine_action(
            root,
            action,
            execute=execute,
            timeout_seconds=timeout_seconds,
            ocr_input_json=ocr_input_json,
            ocr_language=ocr_language,
            captiocr_root=captiocr_root,
            visual_structure_input_json=visual_structure_input_json,
            provider_config=profile["provider_config"],
            multimodal_limit=profile["multimodal_limit"],
            temporal_limit=profile["temporal_limit"],
            frame_count=profile["frame_count"],
            confirm_vision_calls=confirm_vision_calls,
            confirm_vision_indexes=confirm_vision_indexes,
        )
    elif status == "ready":
        if refresh_outputs:
            result = _refresh_ready_outputs(root, vault=vault, folder=folder)
            advanced = True
        else:
            blocked_reason = "bundle is ready; pass refresh_outputs=true to refresh downstream outputs"
    else:
        blocked_reason = "human review or manual repair is required before machine advance"

    after = bundle_next_action(root, refresh=True)
    args_path = root / "mcp-bundle-advance.args.json"
    write_json(
        args_path,
        {
            "bundle_dir": str(root),
            "execute": False,
            "refresh_outputs": False,
            "folder": folder,
            "timeout_seconds": timeout_seconds,
            "ocr_language": ocr_language,
            "provider_config": public_vision_provider_profile(profile["provider_config"]),
            "multimodal_limit": profile["multimodal_limit"],
            "temporal_limit": profile["temporal_limit"],
            "frame_count": profile["frame_count"],
            "confirm_vision_calls": 0,
            "confirm_vision_indexes": "",
        },
    )
    output = {
        "bundle_dir": str(root),
        "status": "advanced" if advanced else "blocked",
        "advanced": advanced,
        "execute": bool(execute),
        "refresh_outputs": bool(refresh_outputs),
        "execution_profile": {
            "provider": public_vision_provider_profile(profile["provider_config"]),
            "multimodal_limit": profile["multimodal_limit"],
            "temporal_limit": profile["temporal_limit"],
            "frame_count": profile["frame_count"],
        },
        "blocked_reason": blocked_reason,
        "before": _compact_next_result(before),
        "action_result": _compact_action_result(result),
        "after": _compact_next_result(after),
        "mcp_args_path": str(args_path),
    }
    return _write_advance_log(root, output)


def bundle_advance_log(bundle_dir: str | Path) -> dict[str, Any]:
    """Read and render the persisted bundle advance history."""
    root = Path(bundle_dir).expanduser().resolve()
    log_path = root / "bundle-advance-runs.jsonl"
    markdown_path = root / "bundle-advance-runs.md"
    rows = read_jsonl(log_path)
    markdown_path.write_text(_render_advance_log_markdown(root, rows), encoding="utf-8")
    return {
        "bundle_dir": str(root),
        "log_path": str(log_path),
        "markdown_path": str(markdown_path),
        "count": len(rows),
        "advances": rows,
        "last": rows[-1] if rows else {},
    }


def bundle_advance_queue(
    bundle_dir: str | Path,
    *,
    max_steps: int = 4,
    execute: bool = False,
    refresh_outputs: bool = False,
    vault: str | Path | None = None,
    folder: str = "00_Inbox/AI/课程视频知识包",
    timeout_seconds: int = 30,
    ocr_input_json: str | Path | None = None,
    ocr_language: str = "chi_sim",
    captiocr_root: str | Path | None = None,
    visual_structure_input_json: str | Path | None = None,
    provider_config: dict[str, Any] | None = None,
    multimodal_limit: int | None = None,
    temporal_limit: int | None = None,
    frame_count: int | None = None,
    confirm_vision_calls: int | None = None,
    confirm_vision_indexes: str = "",
) -> dict[str, Any]:
    """Advance a bundle until it is blocked, stalled, ready, or reaches max_steps."""
    root = Path(bundle_dir).expanduser().resolve()
    profile = resolve_vision_execution_profile(
        provider_config=provider_config,
        multimodal_limit=multimodal_limit,
        temporal_limit=temporal_limit,
        frame_count=frame_count,
    )
    steps: list[dict[str, Any]] = []
    stop_reason = "max_steps"
    max_count = max(int(max_steps or 1), 1)
    for _ in range(max_count):
        step = bundle_advance(
            root,
            execute=execute,
            refresh_outputs=refresh_outputs,
            vault=vault,
            folder=folder,
            timeout_seconds=timeout_seconds,
            ocr_input_json=ocr_input_json,
            ocr_language=ocr_language,
            captiocr_root=captiocr_root,
            visual_structure_input_json=visual_structure_input_json,
            provider_config=profile["provider_config"],
            multimodal_limit=profile["multimodal_limit"],
            temporal_limit=profile["temporal_limit"],
            frame_count=profile["frame_count"],
            confirm_vision_calls=confirm_vision_calls,
            confirm_vision_indexes=confirm_vision_indexes,
        )
        steps.append(step)
        before_action = _action(step.get("before"))
        after_action = _action(step.get("after"))
        if not step.get("advanced"):
            stop_reason = "blocked"
            break
        if before_action.get("status") == "ready":
            stop_reason = "refreshed_outputs" if refresh_outputs else "ready"
            break
        if _same_action(before_action, after_action):
            stop_reason = "stalled"
            break
    final = bundle_next_action(root, refresh=True)
    args_path = root / "mcp-bundle-advance-queue.args.json"
    write_json(
        args_path,
        {
            "bundle_dir": str(root),
            "max_steps": max_count,
            "execute": False,
            "refresh_outputs": False,
            "folder": folder,
            "timeout_seconds": timeout_seconds,
            "ocr_language": ocr_language,
            "provider_config": public_vision_provider_profile(profile["provider_config"]),
            "multimodal_limit": profile["multimodal_limit"],
            "temporal_limit": profile["temporal_limit"],
            "frame_count": profile["frame_count"],
            "confirm_vision_calls": 0,
            "confirm_vision_indexes": "",
        },
    )
    return {
        "bundle_dir": str(root),
        "status": "advanced" if any(step.get("advanced") for step in steps) else "blocked",
        "stop_reason": stop_reason,
        "max_steps": max_count,
        "step_count": len(steps),
        "execution_profile": {
            "provider": public_vision_provider_profile(profile["provider_config"]),
            "multimodal_limit": profile["multimodal_limit"],
            "temporal_limit": profile["temporal_limit"],
            "frame_count": profile["frame_count"],
        },
        "steps": steps,
        "final": final,
        "mcp_args_path": str(args_path),
        "advance_log": bundle_advance_log(root),
    }


def _next_repair_action(root: Path, manifest: dict[str, Any]) -> dict[str, Any] | None:
    repair_status = manifest.get("repair_status") if isinstance(manifest.get("repair_status"), dict) else {}
    items = [item for item in repair_status.get("items") or [] if isinstance(item, dict)]
    next_item = next((item for item in items if str(item.get("status") or "") in {"pending", "ran_no_update", "failed"}), {})
    if not next_item and not items:
        next_item = repair_status.get("next") if isinstance(repair_status.get("next"), dict) else {}
    if str(next_item.get("status") or "") not in {"pending", "ran_no_update", "failed"}:
        return None
    if not next_item:
        return None
    tool = str(next_item.get("mcp_tool") or "")
    args_path = _resolve_bundle_path(root, next_item.get("mcp_args_path"))
    return {
        "status": "repair_pending",
        "kind": "repair",
        "key": str(next_item.get("key") or "repair"),
        "label": str(next_item.get("label") or "修复任务"),
        "reason": str(next_item.get("action_hint") or "先处理机器可执行的修复任务。"),
        "count": next_item.get("count", 0),
        "mcp_tool": tool,
        "mcp_args_path": str(args_path) if args_path else "",
        "command": _mcp_command(tool, args_path),
        "human_required": False,
    }


def _next_readiness_action(root: Path, manifest: dict[str, Any]) -> dict[str, Any] | None:
    readiness = manifest.get("review_readiness") if isinstance(manifest.get("review_readiness"), dict) else {}
    if readiness.get("ready") is True:
        return None
    next_action = readiness.get("next_action") if isinstance(readiness.get("next_action"), dict) else {}
    blockers = [item for item in readiness.get("blockers") or [] if isinstance(item, dict)]
    first = blockers[0] if blockers else {}
    key = str(next_action.get("key") or first.get("next_action") or first.get("key") or "review")
    human_required = key.startswith("review_") or key in {"manual_repair_review", "inspect_time_gap_frames", "run_frame_recapture_or_manual_review"}
    if _has_blocker(blockers, "asset_gap"):
        args_path = root / "mcp-repair-bundle-assets.args.json"
        write_json(args_path, {"bundle_dir": str(root)})
        return {
            "status": "repair_pending",
            "kind": "repair",
            "key": "bundle_assets",
            "label": "修复关键帧资产",
            "reason": "存在关键帧资产未复制或文件不可用，先尝试从记录的 source 路径重新复制。",
            "blockers": blockers,
            "mcp_tool": "repair_bundle_assets",
            "mcp_args_path": str(args_path),
            "command": _mcp_command("repair_bundle_assets", args_path),
            "human_required": False,
        }
    args_path = _resolve_bundle_path(root, manifest.get("mcp_readiness_args") or "mcp-audit-bundle-readiness.args.json")
    return {
        "status": "review_blocked",
        "kind": "human_review" if human_required else "readiness",
        "key": key,
        "label": str(next_action.get("label") or first.get("message") or "继续复核"),
        "reason": str(next_action.get("hint") or "先处理最高优先级 blocker，再重新检查 readiness。"),
        "blockers": blockers,
        "mcp_tool": "audit_bundle_readiness",
        "mcp_args_path": str(args_path) if args_path else "",
        "command": _mcp_command("audit_bundle_readiness", args_path),
        "human_required": human_required,
    }


def _next_knowledge_coverage_action(root: Path, manifest: dict[str, Any]) -> dict[str, Any] | None:
    coverage = manifest.get("knowledge_coverage") if isinstance(manifest.get("knowledge_coverage"), dict) else {}
    status = str(coverage.get("status") or "").strip().lower()
    if status != "blocked":
        return None
    next_action = coverage.get("next_action") if isinstance(coverage.get("next_action"), dict) else {}
    tool = str(next_action.get("mcp_tool") or "audit_knowledge_coverage")
    args_path = _resolve_bundle_path(root, next_action.get("mcp_args_path") or manifest.get("mcp_knowledge_coverage_args") or "mcp-audit-knowledge-coverage.args.json")
    key = str(next_action.get("key") or "knowledge_coverage")
    if key in {"screen_text", "structured_visual"} and _visual_structure_ocr_empty_exhausted(manifest):
        args_path = _resolve_bundle_path(root, manifest.get("mcp_review_session_args") or "mcp-prepare-review-session.args.json")
        return {
            "status": "human_review_required",
            "kind": "human_review",
            "key": "ocr_text_empty_review",
            "label": "OCR 空结果需要人工审核或多模态补充",
            "reason": "ebook_markdown_pipeline 已经处理图文候选，但只返回包装/source 元数据，没有提取到真实屏幕文字；继续重跑 OCR 很可能空转。请保留证据帧，进入人工审核，或对这些帧执行多模态理解补充。",
            "coverage_status": status,
            "blockers": coverage.get("blockers") if isinstance(coverage.get("blockers"), list) else [],
            "weak_channels": coverage.get("weak_channels") if isinstance(coverage.get("weak_channels"), list) else [],
            "mcp_tool": "prepare_review_session",
            "mcp_args_path": str(args_path) if args_path else "",
            "command": _mcp_command("prepare_review_session", args_path),
            "fallback_mcp_tool": "run_multimodal_frame_analysis",
            "fallback_mcp_args_path": str(_resolve_bundle_path(root, manifest.get("mcp_multimodal_frame_analysis_args") or "mcp-run-multimodal-frame-analysis.args.json")),
            "human_required": True,
        }
    if key == "temporal_visual_understanding" and _needs_temporal_frame_groups(root):
        tool = "run_temporal_frame_groups"
        args_path = _resolve_bundle_path(root, manifest.get("mcp_temporal_frame_groups_args") or "mcp-run-temporal-frame-groups.args.json")
        key = "temporal_frame_groups"
        next_action = {
            **next_action,
            "label": "生成连续片段帧组",
            "hint": "连续片段理解前需要先为 temporal_sequence/mixed 时间片生成 5-12 帧顺序证据组。",
        }
    return {
        "status": "coverage_blocked" if status == "blocked" else "coverage_weak",
        "kind": "knowledge_coverage",
        "key": key,
        "label": str(next_action.get("label") or "补齐知识覆盖"),
        "reason": str(next_action.get("hint") or "先检查知识通道覆盖缺口，避免在最终导出前漏掉语言、屏幕文字、图像或结构化视觉材料。"),
        "coverage_status": status,
        "blockers": coverage.get("blockers") if isinstance(coverage.get("blockers"), list) else [],
        "weak_channels": coverage.get("weak_channels") if isinstance(coverage.get("weak_channels"), list) else [],
        "mcp_tool": tool,
        "mcp_args_path": str(args_path) if args_path else "",
        "command": _mcp_command(tool, args_path),
        "human_required": tool == "audit_knowledge_coverage" or key in {"source_artifacts", "time_axis"},
    }


def _provider_health_override(root: Path, manifest: dict[str, Any], action: dict[str, Any]) -> dict[str, Any]:
    blocked_tool = str(action.get("mcp_tool") or "")
    if blocked_tool not in {"run_multimodal_frame_analysis", "run_temporal_visual_analysis"}:
        return action
    preflight = _latest_preflight_json(root, manifest)
    provider_health = preflight.get("provider_health") if isinstance(preflight.get("provider_health"), dict) else {}
    blockers = preflight.get("blockers") if isinstance(preflight.get("blockers"), list) else []
    blocker_keys = [str(item.get("key") or "") for item in blockers if isinstance(item, dict)]
    if provider_health.get("safe_to_execute") is not False and "provider_health_failed" not in blocker_keys:
        return action
    matrix_args_path = _resolve_bundle_path(root, manifest.get("mcp_vision_provider_matrix_args") or "mcp-vision-provider-matrix.args.json")
    smoke_args_path = _resolve_bundle_path(root, manifest.get("mcp_vision_provider_smoke_args") or "mcp-vision-provider-smoke.args.json")
    tool = "vision_provider_matrix" if matrix_args_path else "vision_provider_smoke"
    args_path = matrix_args_path or smoke_args_path
    if tool == "vision_provider_matrix" and args_path:
        write_json(
            args_path,
            {
                "providers": ["volcengine_coding_plan", "gemini", "openai", "agnes"],
                "bundle_dir": str(root),
                "output_dir": str(root),
                "timeout_seconds": 8,
                "write": True,
            },
        )
    return {
        "status": "provider_blocked",
        "kind": "provider_repair",
        "key": "provider_matrix_repair" if tool == "vision_provider_matrix" else "provider_repair",
        "label": "比较并修复多模态 Provider" if tool == "vision_provider_matrix" else "修复或切换多模态 Provider",
        "reason": "知识覆盖需要多模态视觉分析，但最新 provider health 显示当前 provider 不安全；先比较 provider matrix 或运行 provider smoke，确认文本/单图/多图 JSON 能通过后再执行真实模型写回。",
        "for_blocked_action": {
            "key": action.get("key", ""),
            "mcp_tool": blocked_tool,
            "mcp_args_path": action.get("mcp_args_path", ""),
        },
        "provider_health": {
            "status": provider_health.get("status", "not_checked"),
            "safe_to_execute": provider_health.get("safe_to_execute"),
            "error_class": provider_health.get("error_class", ""),
        },
        "blocker_keys": blocker_keys,
        "mcp_tool": tool,
        "mcp_args_path": str(args_path) if args_path else "",
        "command": _mcp_command(tool, args_path),
        "human_required": False,
    }


def _latest_preflight_json(root: Path, manifest: dict[str, Any]) -> dict[str, Any]:
    path = _resolve_bundle_path(root, manifest.get("vision_execution_preflight_json") or "vision-execution-preflight.json")
    if not path or not path.exists():
        return {}
    data = read_json(path)
    return data if isinstance(data, dict) else {}


def _visual_structure_ocr_empty_exhausted(manifest: dict[str, Any]) -> bool:
    visual_structure = manifest.get("visual_structure") if isinstance(manifest.get("visual_structure"), dict) else {}
    last_run = visual_structure.get("last_run") if isinstance(visual_structure.get("last_run"), dict) else {}
    blockers = last_run.get("ebook_pipeline_blockers") if isinstance(last_run.get("ebook_pipeline_blockers"), dict) else {}
    total = int(last_run.get("ebook_pipeline_total") or 0)
    succeeded = int(last_run.get("ebook_pipeline_succeeded") or 0)
    empty_count = int(blockers.get("ocr_text_empty") or 0)
    if total > 0 and succeeded == 0 and empty_count == total:
        return True
    results = [item for item in visual_structure.get("ebook_pipeline_results") or [] if isinstance(item, dict)]
    if not results:
        return False
    return all(str(item.get("blocker") or "") == "ocr_text_empty" for item in results)


def _export_action(root: Path, manifest: dict[str, Any]) -> dict[str, Any]:
    post_review = manifest.get("post_review") if isinstance(manifest.get("post_review"), dict) else {}
    tool = str(post_review.get("mcp_tool") or "refresh_lecture_review_outputs")
    args_path = _resolve_bundle_path(root, post_review.get("mcp_args_path") or manifest.get("mcp_refresh_args"))
    return {
        "status": "ready",
        "kind": "export",
        "key": "refresh_review_outputs",
        "label": "可以刷新导出",
        "reason": "repair_status 和 review_readiness 已收口，可以刷新 WebUI/Obsidian 输出。",
        "mcp_tool": tool,
        "mcp_args_path": str(args_path) if args_path else "",
        "command": _mcp_command(tool, args_path),
        "human_required": False,
    }


def _safe_smoke_action(root: Path, manifest: dict[str, Any], action: dict[str, Any]) -> dict[str, Any]:
    tool = str(action.get("mcp_tool") or "")
    key = str(action.get("key") or "")
    if tool not in {"run_multimodal_frame_analysis", "run_temporal_visual_analysis", "run_temporal_frame_groups"}:
        return {}
    args_path = _resolve_bundle_path(root, manifest.get("mcp_controlled_execution_smoke_args") or "mcp-controlled-execution-smoke.args.json")
    return {
        "status": "available",
        "kind": "controlled_execution_smoke",
        "key": "controlled_execution_smoke",
        "label": "本地执行演练",
        "reason": "在真实 provider/key 或确认参数就绪前，可先用本地 fixture 演练 preflight、确认写入、审计和可选回滚。",
        "for_next_action_key": key,
        "mcp_tool": "controlled_execution_smoke",
        "mcp_args_path": str(args_path) if args_path else "",
        "command": _mcp_command("controlled_execution_smoke", args_path),
        "human_required": False,
    }


def _resolve_bundle_path(root: Path, value: Any) -> Path | None:
    text = str(value or "").strip()
    if not text:
        return None
    path = Path(text)
    return path if path.is_absolute() else root / path


def _mcp_command(tool: str, args_path: Path | None) -> str:
    if not tool or not args_path:
        return ""
    return f".\\scripts\\video-knowledge.ps1 mcp-call {tool} {args_path}"


def _has_blocker(blockers: list[dict[str, Any]], key: str) -> bool:
    return any(str(blocker.get("key") or "") == key for blocker in blockers)


def _action(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        return {}
    action = value.get("next_action")
    return action if isinstance(action, dict) else {}


def _same_action(left: dict[str, Any], right: dict[str, Any]) -> bool:
    if not left or not right:
        return False
    return (
        str(left.get("status") or "") == str(right.get("status") or "")
        and str(left.get("key") or "") == str(right.get("key") or "")
        and str(left.get("mcp_tool") or "") == str(right.get("mcp_tool") or "")
    )


def _advance_machine_action(
    root: Path,
    action: dict[str, Any],
    *,
    execute: bool,
    timeout_seconds: int,
    ocr_input_json: str | Path | None,
    ocr_language: str,
    captiocr_root: str | Path | None,
    visual_structure_input_json: str | Path | None,
    provider_config: dict[str, Any] | None,
    multimodal_limit: int,
    temporal_limit: int,
    frame_count: int,
    confirm_vision_calls: int | None,
    confirm_vision_indexes: str,
) -> tuple[dict[str, Any] | None, bool, str]:
    key = str(action.get("key") or "")
    tool = str(action.get("mcp_tool") or "")
    if key in {"frame_recapture", "visual_frames"} or tool == "run_frame_recapture_plan":
        return run_frame_recapture_plan(root, execute=execute, timeout_seconds=timeout_seconds), True, ""
    if key == "screen_text" or tool == "run_visual_structure_plan":
        return run_visual_structure_plan(root, input_json=visual_structure_input_json), True, ""
    if key == "ocr_backfill" or tool == "run_ocr_backfill":
        return (
            run_ocr_backfill(
                root,
                input_json=ocr_input_json,
                execute=execute,
                language=ocr_language,
                captiocr_root=captiocr_root,
            ),
            True,
            "",
        )
    if key in {"visual_structure", "structured_visual"}:
        return run_visual_structure_plan(root, input_json=visual_structure_input_json), True, ""
    if key in {"video_frame_router", "visual_route_gap"} or tool == "run_video_frame_router":
        return run_video_frame_router(root, write=True), True, ""
    if key in {"multimodal_frame_analysis", "visual_analysis_gap"} or tool == "run_multimodal_frame_analysis":
        if execute:
            gate = _vision_execution_preflight_gate(
                root,
                provider_config,
                semantic_limit=multimodal_limit,
                temporal_limit=0,
                frame_count=frame_count,
                confirm_vision_calls=confirm_vision_calls,
                confirm_vision_indexes=confirm_vision_indexes,
            )
            if gate:
                return gate, False, _vision_gate_blocked_reason(gate)
        return (
            run_multimodal_frame_analysis(
                root,
                execute=execute,
                provider_config=provider_config,
                limit=multimodal_limit,
                confirm_vision_calls=confirm_vision_calls,
                confirm_vision_indexes=confirm_vision_indexes,
            ),
            True,
            "",
        )
    if key in {"temporal_frame_groups"} or tool == "run_temporal_frame_groups":
        return run_temporal_frame_groups(root, execute=execute, frame_count=frame_count, limit=temporal_limit, timeout_seconds=timeout_seconds), True, ""
    if key in {"temporal_visual_analysis"} or tool == "run_temporal_visual_analysis":
        if execute:
            gate = _vision_execution_preflight_gate(
                root,
                provider_config,
                semantic_limit=0,
                temporal_limit=temporal_limit,
                frame_count=frame_count,
                confirm_vision_calls=confirm_vision_calls,
                confirm_vision_indexes=confirm_vision_indexes,
            )
            if gate:
                return gate, False, _vision_gate_blocked_reason(gate)
        return (
            run_temporal_visual_analysis(
                root,
                execute=execute,
                provider_config=provider_config,
                limit=temporal_limit,
                frame_count=frame_count,
                confirm_vision_calls=confirm_vision_calls,
                confirm_vision_indexes=confirm_vision_indexes,
            ),
            True,
            "",
        )
    if key == "bundle_assets" or tool == "repair_bundle_assets":
        return repair_bundle_assets(root), True, ""
    if key == "knowledge_coverage" or tool == "audit_knowledge_coverage":
        return audit_knowledge_coverage(root, write=True), True, ""
    return None, False, f"unsupported machine action: {key or tool}"


def _write_advance_log(root: Path, result: dict[str, Any]) -> dict[str, Any]:
    record = _advance_record(result)
    append_jsonl(root / "bundle-advance-runs.jsonl", [record])
    log = bundle_advance_log(root)
    result["advance_log"] = {
        "record": record,
        "log_path": log["log_path"],
        "markdown_path": log["markdown_path"],
        "count": log["count"],
    }
    return result


def _vision_execution_preflight_gate(
    root: Path,
    provider_config: dict[str, Any] | None,
    *,
    semantic_limit: int,
    temporal_limit: int,
    frame_count: int,
    confirm_vision_calls: int | None,
    confirm_vision_indexes: str,
) -> dict[str, Any] | None:
    preflight = vision_execution_preflight(
        root,
        provider_config=provider_config,
        semantic_limit=semantic_limit,
        temporal_limit=temporal_limit,
        frame_count=frame_count,
        include_semantic=semantic_limit > 0,
        include_temporal=temporal_limit > 0,
        write=True,
    )
    if preflight.get("ready_to_execute"):
        confirmation = _vision_execution_confirmation_gate(
            preflight,
            confirm_vision_calls=confirm_vision_calls,
            confirm_vision_indexes=confirm_vision_indexes,
        )
        if not confirmation:
            return None
        return confirmation
    return {
        "schema": "lecture_bundle_advance_vision_preflight_gate.v1",
        "status": "vision_preflight_blocked",
        "bundle_dir": str(root),
        "preflight_path": preflight.get("preflight_path", ""),
        "preflight_json_path": preflight.get("preflight_json_path", ""),
        "blockers": preflight.get("blockers") if isinstance(preflight.get("blockers"), list) else [],
        "summary": {
            "provider": preflight.get("provider") if isinstance(preflight.get("provider"), dict) else {},
            "ready_to_execute": False,
            "expected_api_calls": preflight.get("expected_api_calls", 0),
            "candidate_counts": preflight.get("candidate_counts") if isinstance(preflight.get("candidate_counts"), dict) else {},
            "blocker_keys": [str(item.get("key") or "") for item in preflight.get("blockers", []) if isinstance(item, dict)],
            "hint": "Inspect vision-execution-preflight.md, fix blockers, then retry execute=true.",
        },
    }


def _vision_execution_confirmation_gate(
    preflight: dict[str, Any],
    *,
    confirm_vision_calls: int | None,
    confirm_vision_indexes: str,
) -> dict[str, Any] | None:
    expected_calls = int(preflight.get("expected_api_calls") or 0)
    expected_indexes = _preflight_selected_index_string(preflight)
    calls_ok = confirm_vision_calls is not None and int(confirm_vision_calls) == expected_calls
    indexes_ok = str(confirm_vision_indexes or "").strip() == expected_indexes
    if calls_ok and indexes_ok:
        return None
    return {
        "schema": "lecture_bundle_advance_vision_confirmation_gate.v1",
        "status": "vision_confirmation_required",
        "bundle_dir": str(preflight.get("bundle_dir") or ""),
        "preflight_path": preflight.get("preflight_path", ""),
        "preflight_json_path": preflight.get("preflight_json_path", ""),
        "summary": {
            "ready_to_execute": True,
            "expected_api_calls": expected_calls,
            "expected_indexes": expected_indexes,
            "received_confirm_vision_calls": confirm_vision_calls,
            "received_confirm_vision_indexes": str(confirm_vision_indexes or ""),
            "hint": "Retry with confirm_vision_calls and confirm_vision_indexes exactly matching the preflight output.",
        },
    }


def _preflight_selected_index_string(preflight: dict[str, Any]) -> str:
    selected = preflight.get("selected_indexes") if isinstance(preflight.get("selected_indexes"), dict) else {}
    indexes: list[int] = []
    for key in ("semantic", "temporal"):
        for value in selected.get(key) or []:
            try:
                indexes.append(int(value))
            except (TypeError, ValueError):
                continue
    return ",".join(str(index) for index in indexes)


def _vision_gate_blocked_reason(gate: dict[str, Any]) -> str:
    if str(gate.get("status") or "") == "vision_confirmation_required":
        return "vision execution confirmation required; match confirm_vision_calls and confirm_vision_indexes from preflight"
    return "vision execution preflight blocked; inspect the preflight report before execute"


def _needs_temporal_frame_groups(root: Path) -> bool:
    timeline_path = root / "timeline.json"
    if not timeline_path.exists():
        return False
    data = read_json(timeline_path)
    timeline = data if isinstance(data, list) else []
    for item in timeline:
        if not isinstance(item, dict):
            continue
        if str(item.get("visual_route") or "") not in {"temporal_sequence", "mixed"}:
            continue
        paths = item.get("temporal_frame_paths")
        if not isinstance(paths, list) or len(paths) < 2:
            return True
    return False


def _advance_record(result: dict[str, Any]) -> dict[str, Any]:
    before = result.get("before") if isinstance(result.get("before"), dict) else {}
    after = result.get("after") if isinstance(result.get("after"), dict) else {}
    before_action = before.get("next_action") if isinstance(before.get("next_action"), dict) else {}
    after_action = after.get("next_action") if isinstance(after.get("next_action"), dict) else {}
    action_result = result.get("action_result") if isinstance(result.get("action_result"), dict) else {}
    summary = action_result.get("summary") if isinstance(action_result.get("summary"), dict) else {}
    artifacts = _advance_artifacts(action_result)
    return {
        "created_at": now_iso(),
        "status": result.get("status", ""),
        "advanced": bool(result.get("advanced")),
        "execute": bool(result.get("execute")),
        "refresh_outputs": bool(result.get("refresh_outputs")),
        "blocked_reason": result.get("blocked_reason", ""),
        "before_status": before_action.get("status", ""),
        "before_key": before_action.get("key", ""),
        "before_tool": before_action.get("mcp_tool", ""),
        "after_status": after_action.get("status", ""),
        "after_key": after_action.get("key", ""),
        "after_tool": after_action.get("mcp_tool", ""),
        "action_summary": summary,
        "action_artifacts": artifacts,
    }


def _advance_artifacts(action_result: dict[str, Any]) -> dict[str, Any]:
    if not action_result:
        return {}
    artifacts: dict[str, Any] = {}
    for key in ("report_path", "manifest_path", "timeline_path", "asset_manifest_path", "preflight_path", "preflight_json_path"):
        value = action_result.get(key)
        if value:
            artifacts[key] = str(value)
    backfill = action_result.get("backfill") if isinstance(action_result.get("backfill"), dict) else {}
    if backfill:
        artifacts["updated_indexes"] = list(backfill.get("updated_indexes") or [])[:20]
        artifacts["updated_count"] = backfill.get("updated", 0)
        artifacts["source_package_updated"] = bool(backfill.get("source_package_updated"))
    if isinstance(action_result.get("missing"), list):
        artifacts["missing_paths"] = [_artifact_path(item, prefer="source") for item in action_result.get("missing", [])[:10]]
    if isinstance(action_result.get("copied"), list):
        artifacts["copied_paths"] = [_artifact_path(item, prefer="path") for item in action_result.get("copied", [])[:10]]
    webui_bundle = action_result.get("webui_bundle") if isinstance(action_result.get("webui_bundle"), dict) else {}
    if webui_bundle:
        for key in ("bundle_dir", "manifest_path", "review_html_path", "note_path"):
            value = webui_bundle.get(key)
            if value:
                artifacts[f"webui_{key}"] = str(value)
    obsidian_export = action_result.get("obsidian_export") if isinstance(action_result.get("obsidian_export"), dict) else {}
    if obsidian_export:
        for key in (
            "path",
            "note_path",
            "output_path",
            "vault",
            "folder",
            "export_manifest_path",
            "export_status_path",
            "export_status_markdown_path",
            "asset_manifest_path",
            "source_artifact_index_path",
        ):
            value = obsidian_export.get(key)
            if value:
                artifacts[f"obsidian_{key}"] = str(value)
        if isinstance(obsidian_export.get("export_status"), dict):
            artifacts["obsidian_export_status"] = obsidian_export["export_status"]
        if obsidian_export.get("mcp_status_args_path"):
            artifacts["obsidian_mcp_status_args_path"] = str(obsidian_export.get("mcp_status_args_path"))
        if obsidian_export.get("mcp_export_args_path"):
            artifacts["obsidian_mcp_export_args_path"] = str(obsidian_export.get("mcp_export_args_path"))
        entrypoints = obsidian_export.get("agent_entrypoints") if isinstance(obsidian_export.get("agent_entrypoints"), dict) else {}
        if not entrypoints and isinstance(obsidian_export.get("pages_by_name"), dict):
            folder = str(obsidian_export.get("folder") or "")
            if folder:
                entrypoints = {
                    "full_speech_text": str(Path(folder) / "transcript.md"),
                    "full_screen_text": str(Path(folder) / "screen-text.md"),
                    "evidence_map": str(Path(folder) / "evidence-map.md"),
                    "structured_materials": str(Path(folder) / "structured-materials.md"),
                    "source_artifacts_json": str(Path(folder) / "source-artifacts.json"),
                }
        for key in (
            "full_speech_text",
            "full_screen_text",
            "timeline",
            "evidence_map",
            "structured_materials",
            "source_artifacts_json",
            "asset_manifest",
        ):
            value = entrypoints.get(key)
            if value:
                artifacts[f"obsidian_{key}"] = str(value)
    if isinstance(action_result.get("obsidian_export_blocked"), dict):
        artifacts["obsidian_export_blocked"] = action_result["obsidian_export_blocked"]
    if isinstance(action_result.get("vision_restore_hint"), dict):
        hint = action_result["vision_restore_hint"]
        for key in ("run_id", "kind", "restore_plan_command", "audit_jsonl_path", "audit_markdown_path"):
            value = hint.get(key)
            if value:
                artifacts[f"vision_{key}"] = value
    if action_result.get("review_json"):
        artifacts["review_json"] = str(action_result.get("review_json"))
    if action_result.get("default_review_notes_created"):
        artifacts["default_review_notes_created"] = True
    return artifacts


def _compact_action_result(result: dict[str, Any] | None) -> dict[str, Any] | None:
    if result is None:
        return None
    compact: dict[str, Any] = {}
    for key in (
        "schema",
        "status",
        "bundle_dir",
        "manifest_path",
        "timeline_path",
        "report_path",
        "report_markdown_path",
        "coverage_path",
        "coverage_markdown_path",
        "preflight_path",
        "preflight_json_path",
        "input_template_json",
        "note_path",
        "full_transcript_path",
        "mcp_args_path",
    ):
        if key in result:
            compact[key] = result[key]
    if isinstance(result.get("summary"), dict):
        compact["summary"] = result["summary"]
    if isinstance(result.get("run_audit"), dict):
        compact["run_audit"] = _compact_run_audit(result["run_audit"])
        hint = result.get("vision_restore_hint") if isinstance(result.get("vision_restore_hint"), dict) else _vision_restore_hint(result)
        if hint:
            compact["vision_restore_hint"] = hint
    if isinstance(result.get("coverage"), dict):
        compact["coverage"] = _compact_coverage(result["coverage"])
    if isinstance(result.get("backfill"), dict):
        compact["backfill"] = {
            "updated": result["backfill"].get("updated", 0),
            "updated_indexes": list(result["backfill"].get("updated_indexes") or [])[:20],
            "source_package_updated": bool(result["backfill"].get("source_package_updated")),
        }
    if isinstance(result.get("items"), list):
        compact["item_count"] = len(result["items"])
    return compact


def _compact_run_audit(run_audit: dict[str, Any]) -> dict[str, Any]:
    record = run_audit.get("record") if isinstance(run_audit.get("record"), dict) else {}
    return {
        "run_id": str(record.get("run_id") or ""),
        "kind": str(record.get("kind") or ""),
        "execute": bool(record.get("execute")),
        "status": str(record.get("status") or ""),
        "updated_count": int(record.get("updated_count") or 0),
        "timeline_diff_count": int(record.get("timeline_diff_count") or 0),
        "execution_control": record.get("execution_control") if isinstance(record.get("execution_control"), dict) else {},
        "jsonl_path": str(run_audit.get("jsonl_path") or ""),
        "markdown_path": str(run_audit.get("markdown_path") or ""),
    }


def _vision_restore_hint(result: dict[str, Any]) -> dict[str, Any]:
    run_audit = result.get("run_audit") if isinstance(result.get("run_audit"), dict) else {}
    record = run_audit.get("record") if isinstance(run_audit.get("record"), dict) else {}
    run_id = str(record.get("run_id") or "")
    if not run_id:
        return {}
    bundle_dir = str(result.get("bundle_dir") or record.get("bundle_dir") or "")
    command = f'python -m video_knowledge_pipeline.cli vision-analysis-restore-plan "{bundle_dir}" --run-id {run_id}' if bundle_dir else ""
    return {
        "run_id": run_id,
        "kind": str(record.get("kind") or ""),
        "updated_count": int(record.get("updated_count") or 0),
        "timeline_diff_count": int(record.get("timeline_diff_count") or 0),
        "audit_jsonl_path": str(run_audit.get("jsonl_path") or ""),
        "audit_markdown_path": str(run_audit.get("markdown_path") or ""),
        "restore_plan_command": command,
    }


def _compact_next_result(value: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(value, dict):
        return {}
    compact = {
        "bundle_dir": value.get("bundle_dir", ""),
        "manifest_path": value.get("manifest_path", ""),
        "refreshed": bool(value.get("refreshed")),
        "status": value.get("status", ""),
        "mcp_args_path": value.get("mcp_args_path", ""),
    }
    if isinstance(value.get("next_action"), dict):
        compact["next_action"] = _compact_next_action(value["next_action"])
    return compact


def _compact_next_action(value: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(value, dict):
        return {}
    keep = [
        "status",
        "kind",
        "key",
        "label",
        "reason",
        "coverage_status",
        "mcp_tool",
        "mcp_args_path",
        "command",
        "human_required",
    ]
    compact = {key: value[key] for key in keep if key in value}
    blockers = value.get("blockers") if isinstance(value.get("blockers"), list) else []
    weak = value.get("weak_channels") if isinstance(value.get("weak_channels"), list) else []
    if blockers:
        compact["blocker_count"] = len(blockers)
        compact["blocker_keys"] = [str(item.get("key") or "") for item in blockers[:5] if isinstance(item, dict)]
    if weak:
        compact["weak_count"] = len(weak)
        compact["weak_keys"] = [str(item.get("key") or "") for item in weak[:5] if isinstance(item, dict)]
    return compact


def _compact_coverage(value: dict[str, Any]) -> dict[str, Any]:
    blockers = value.get("blockers") if isinstance(value.get("blockers"), list) else []
    weak = value.get("weak_channels") if isinstance(value.get("weak_channels"), list) else []
    return {
        "status": value.get("status", ""),
        "timeline_items": value.get("timeline_items", 0),
        "items_with_visual_route": value.get("items_with_visual_route", 0),
        "items_with_visual_understanding": value.get("items_with_visual_understanding", 0),
        "items_with_temporal_understanding": value.get("items_with_temporal_understanding", 0),
        "missing_visual_understanding": value.get("missing_visual_understanding", 0),
        "blocker_count": len(blockers),
        "weak_count": len(weak),
        "blocker_keys": [str(item.get("key") or "") for item in blockers[:5] if isinstance(item, dict)],
        "weak_keys": [str(item.get("key") or "") for item in weak[:5] if isinstance(item, dict)],
    }


def _artifact_path(item: Any, *, prefer: str) -> str:
    if isinstance(item, dict):
        fallback = "source" if prefer == "path" else "path"
        return str(item.get(prefer) or item.get(fallback) or "")
    return str(item or "")


def _render_advance_log_markdown(root: Path, rows: list[dict[str, Any]]) -> str:
    lines = [
        "# Bundle Advance Runs",
        "",
        f"- Bundle: `{root}`",
        f"- Count: {len(rows)}",
        "",
        "| Time | Status | From | To | Execute | Refresh | Reason |",
        "|---|---|---|---|---|---|---|",
    ]
    for row in rows:
        execute = "yes" if row.get("execute") else "no"
        refresh = "yes" if row.get("refresh_outputs") else "no"
        before = row.get("before_key") or row.get("before_status") or "-"
        after = row.get("after_key") or row.get("after_status") or "-"
        reason = str(row.get("blocked_reason") or "")
        lines.append(
            f"| {row.get('created_at', '')} | {row.get('status', '')} | `{before}` | `{after}` | {execute} | {refresh} | {reason} |"
        )
    return "\n".join(lines).rstrip() + "\n"


def _refresh_ready_outputs(root: Path, *, vault: str | Path | None, folder: str) -> dict[str, Any]:
    args_path = root / "mcp-refresh-lecture-review.args.json"
    if not args_path.exists():
        raise FileNotFoundError(f"refresh args not found: {args_path}")
    args = read_json(args_path)
    if not isinstance(args, dict):
        raise ValueError("mcp-refresh-lecture-review.args.json must be a JSON object")
    result = refresh_lecture_review_outputs(
        args["project"],
        args["review_json"],
        webui_output_dir=args.get("webui_output_dir") or str(root),
        vault=vault,
        folder=folder,
        target=args.get("target") or "bilinote",
        allow_blocked_export=True,
    )
    return result

