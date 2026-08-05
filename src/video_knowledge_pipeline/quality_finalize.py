from __future__ import annotations

from pathlib import Path
from typing import Any

from .models import now_iso
from .semantic_chapter_plan import build_semantic_chapter_plan
from .smart_summary_chapters import build_smart_summary_chapter_pack
from .smart_summary_codex import smart_summary_quality_check
from .smart_summary_section_llm import run_smart_summary_section_llm_rewrite
from .smart_summary_global_reduce import run_smart_summary_global_reduce
from .summary_consistency import run_summary_consistency_check
from .storage import read_json, write_json
from .transcript_quality_gate import run_transcript_quality_gate


SCHEMA = "video_knowledge_pipeline.quality_finalize.v1"


def finalize_quality_outputs(
    bundle_dir: str | Path,
    *,
    provider_config: dict[str, Any] | None = None,
    execute_llm: bool = False,
    auto_from_profile: bool = False,
    quality_profile: str = "quality",
    target_chapters: int = 8,
    write: bool = True,
) -> dict[str, Any]:
    root = Path(bundle_dir).expanduser().resolve()
    if not write and (execute_llm or auto_from_profile):
        raise ValueError("LLM execution requires write=true for section calls, revisions, and quality evidence")
    corrected = _corrected_transcript_path(root)
    result: dict[str, Any] = {
        "schema": SCHEMA,
        "bundle_dir": str(root),
        "corrected_transcript": str(corrected) if corrected else "",
        "execute_llm": bool(execute_llm),
        "auto_from_profile": bool(auto_from_profile),
        "quality_profile": quality_profile,
        "status": "blocked_missing_corrected_transcript",
        "ok": False,
        "steps": [],
        "artifacts": {
            "transcript_quality": str(root / "transcript-quality-gate.json"),
            "semantic_chapters": str(root / "exports" / "semantic-chapter-plan.json"),
            "chapter_pack": str(root / "exports" / "smart-summary-chapters.json"),
            "section_llm": str(root / "exports" / "smart-summary-section-llm-rewrite.json"),
            "global_reduce": str(root / "exports" / "smart-summary-global-reduce.json"),
            "summary_consistency": str(root / "exports" / "summary-consistency.json"),
            "smart_summary": str(root / "exports" / "smart-summary.md"),
            "summary_quality": str(root / "exports" / "smart-summary-quality.json"),
            "report_json": str(root / "quality-finalize.json"),
            "report_markdown": str(root / "quality-finalize.md"),
        },
        "operator_boundary": {
            "corrected_transcript_required": True,
            "raw_asr_is_not_summary_input": True,
            "semantic_chapters_required": True,
            "preview_by_default": True,
            "network_requires_execute_or_profile_authorization": True,
            "provider_config_runtime_only": True,
        },
        "updated_at": now_iso(),
    }
    if not corrected:
        result["next_actions"] = ["Run transcript-evidence-correction-pipeline and produce corrected-transcript.json first."]
        return _write_result(root, result, write=write)

    transcript_quality = run_transcript_quality_gate(root, input_path=corrected, write=write)
    result["steps"].append(_step("transcript_quality_gate", transcript_quality))
    result["transcript_quality"] = _summary(transcript_quality)
    if int(transcript_quality.get("fail_count") or 0) > 0:
        result["status"] = "blocked_transcript_quality"
        result["next_actions"] = list(transcript_quality.get("next_actions") or [])
        return _write_result(root, result, write=write)

    semantic = build_semantic_chapter_plan(root, chapter_mode="semantic", write=write)
    chapters = build_smart_summary_chapter_pack(
        root,
        target_chapters=target_chapters,
        chapter_mode="semantic",
        write=write,
    )
    result["steps"].append(_step("semantic_chapter_plan", semantic))
    result["steps"].append(_step("smart_summary_chapter_pack", chapters))
    result["semantic_chapters"] = _summary(semantic)
    result["chapter_pack"] = _summary(chapters)
    if not semantic.get("chapters") or not chapters.get("chapters"):
        result["status"] = "blocked_semantic_chapters"
        result["next_actions"] = ["Inspect corrected transcript coverage and semantic-chapter-plan.md."]
        return _write_result(root, result, write=write)

    section_llm = run_smart_summary_section_llm_rewrite(
        root,
        provider_config=provider_config,
        execute=execute_llm,
        auto_from_profile=auto_from_profile,
        quality_profile=quality_profile,
        target_chapters=target_chapters,
        install=True,
        require_all_sections=True,
        write=write,
    )
    result["steps"].append(_step("section_llm_rewrite", section_llm))
    result["section_llm"] = _summary(section_llm)
    if str(section_llm.get("status") or "") == "planned":
        result["status"] = "planned_section_llm"
        result["next_actions"] = list(section_llm.get("next_actions") or [])
        return _write_result(root, result, write=write)
    if not section_llm.get("ok"):
        result["status"] = "section_llm_failed"
        result["next_actions"] = list(section_llm.get("next_actions") or [])
        return _write_result(root, result, write=write)

    reduce_execute = bool(execute_llm or ((section_llm.get("profile_execution") or {}).get("auto_execute")))
    global_reduce = run_smart_summary_global_reduce(
        root,
        provider_config=provider_config,
        execute=reduce_execute,
        install=True,
        write=write,
    )
    result["steps"].append(_step("smart_summary_global_reduce", global_reduce))
    result["global_reduce"] = _summary(global_reduce)
    if str(global_reduce.get("status") or "") == "planned":
        result["status"] = "planned_global_reduce"
        result["next_actions"] = list(global_reduce.get("next_actions") or [])
        return _write_result(root, result, write=write)
    if not global_reduce.get("ok"):
        result["status"] = "global_reduce_failed"
        result["next_actions"] = list(global_reduce.get("next_actions") or [])
        return _write_result(root, result, write=write)

    consistency = run_summary_consistency_check(root, write=write)
    result["steps"].append(_step("summary_consistency", consistency))
    result["summary_consistency"] = _summary(consistency)
    if int((consistency.get("quality") or {}).get("high_risk_conflicts") or 0) > 0:
        result["status"] = "summary_consistency_failed"
        result["next_actions"] = ["Resolve explicit entity/number conflicts; unknown evidence may remain review-only."]
        return _write_result(root, result, write=write)

    summary_quality = smart_summary_quality_check(root, require_codex=True, write=write)
    result["steps"].append(_step("smart_summary_quality_check", summary_quality))
    result["summary_quality"] = _summary(summary_quality)
    result["status"] = "completed" if summary_quality.get("passed") else "summary_quality_failed"
    result["ok"] = bool(summary_quality.get("passed"))
    result["next_actions"] = [] if result["ok"] else ["Inspect exports/smart-summary-quality.md and retry failed chapter revisions."]
    return _write_result(root, result, write=write)


def _corrected_transcript_path(root: Path) -> Path | None:
    manifest_path = root / "manifest.json"
    manifest = read_json(manifest_path) if manifest_path.exists() else {}
    manifest = manifest if isinstance(manifest, dict) else {}
    for key in ("human_corrected_transcript_json", "corrected_transcript_json", "source_arbitrated_transcript_json"):
        value = str(manifest.get(key) or "").strip()
        if not value:
            continue
        path = Path(value)
        path = path if path.is_absolute() else root / path
        if path.exists():
            return path.resolve()
    for name in ("human-corrected-transcript.json", "corrected-transcript.json", "source-arbitrated-transcript.json"):
        path = root / name
        if path.exists():
            return path.resolve()
    return None


def _step(name: str, value: dict[str, Any]) -> dict[str, Any]:
    return {"name": name, "status": str(value.get("status") or "unknown"), "ok": bool(value.get("ok", value.get("passed", True)))}


def _summary(value: dict[str, Any]) -> dict[str, Any]:
    keys = (
        "status",
        "ok",
        "passed",
        "fail_count",
        "warning_count",
        "chapter_count",
        "part_count",
        "section_count",
        "selected_section_count",
        "rewritten_section_count",
        "failed_section_count",
        "profile_execution",
    )
    return {key: value.get(key) for key in keys if key in value}


def _write_result(root: Path, result: dict[str, Any], *, write: bool) -> dict[str, Any]:
    if not write:
        return result
    write_json(root / "quality-finalize.json", result)
    (root / "quality-finalize.md").write_text(_render_markdown(result), encoding="utf-8")
    manifest_path = root / "manifest.json"
    manifest = read_json(manifest_path) if manifest_path.exists() else {}
    manifest = manifest if isinstance(manifest, dict) else {}
    manifest["quality_finalize_json"] = "quality-finalize.json"
    manifest["quality_finalize_markdown"] = "quality-finalize.md"
    manifest["quality_finalize_summary"] = {
        "status": result.get("status"),
        "ok": result.get("ok"),
        "updated_at": result.get("updated_at"),
    }
    write_json(manifest_path, manifest)
    return result


def _render_markdown(result: dict[str, Any]) -> str:
    lines = [
        "# Quality Finalize",
        "",
        f"- Status: {result.get('status')}",
        f"- Corrected transcript: {result.get('corrected_transcript')}",
        f"- Execute LLM: {result.get('execute_llm')}",
        "",
        "| Step | Status | OK |",
        "| --- | --- | --- |",
    ]
    for row in result.get("steps") or []:
        lines.append(f"| {row.get('name', '')} | {row.get('status', '')} | {row.get('ok', False)} |")
    lines.extend(["", "## Next Actions", ""])
    lines.extend(f"- {action}" for action in result.get("next_actions") or [])
    return "\n".join(lines).rstrip() + "\n"