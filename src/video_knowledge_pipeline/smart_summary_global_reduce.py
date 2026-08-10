from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from .canonical_json import canonical_json_sha256
from .file_hash import sha256_file
from .model_api_settings import resolve_model_api_provider_config
from .model_business_authorization import (
    create_business_child_consent,
    validate_model_business_authorization,
)
from .model_task_gateway import model_task_api_call
from .models import now_iso
from .smart_summary_codex import generate_smart_summary_with_codex
from .smart_summary_reader_plan import (
    SCHEMA as READER_PLAN_SCHEMA,
    evaluate_reader_markdown_semantics,
    normalize_reader_plan_candidate,
    parse_reader_plan,
    reader_plan_prompt_contract,
    render_reader_summary,
    validate_reader_plan,
)
from .storage import read_json, write_json
from .text_llm_gateway import resolve_text_provider_config
from .trusted_model_connector import execute_consented_model_task


SCHEMA = "video_knowledge_pipeline.smart_summary_global_reduce.v1"
CHAPTER_FACT_PACK_SCHEMA = "video_knowledge_pipeline.smart_summary_chapter_fact_pack.v1"
DEFAULT_REDUCE_SECTION_MARKDOWN_CHARS = 1200
DEFAULT_REDUCE_FACTS_PER_TYPE = 2
DEFAULT_REDUCE_FACTS_PER_SECTION = 8
DEFAULT_REDUCE_QUOTE_REFS_PER_SECTION = 2
DEFAULT_REDUCE_REVIEW_REFS_PER_SECTION = 2


def run_smart_summary_global_reduce(
    bundle_dir: str | Path,
    *,
    provider_config: dict[str, Any] | None = None,
    execute: bool = False,
    reuse_candidate: bool = False,
    recovery_execution_report: str | Path | None = None,
    max_input_chars: int = 60000,
    max_tokens: int = 5000,
    temperature: float = 0,
    install: bool = True,
    write: bool = True,
    business_authorization_path: str | Path | None = None,
) -> dict[str, Any]:
    """Reduce complete semantic-chapter Map outputs into one final summary."""

    root = Path(bundle_dir).expanduser().resolve()
    exports = root / "exports"
    revisions_path = exports / "smart-summary-section-llm-revisions.json"
    workflow_path = exports / "smart-summary-section-workflow.json"
    course_map_path = exports / "course-map.json"
    revisions = _mapping(revisions_path)
    workflow = _mapping(workflow_path)
    course_map = _mapping(course_map_path)
    rows = _revision_rows(revisions)
    expected_ids = {
        str(row.get("section_id") or "")
        for row in workflow.get("sections") or []
        if isinstance(row, dict) and row.get("section_id")
    }
    completed_ids = {str(row.get("section_id") or "") for row in rows if _section_text(row)}
    missing = sorted(expected_ids - completed_ids)
    cfg = resolve_text_provider_config(
        resolve_model_api_provider_config("summary_rewrite", provider_config)
    )
    fact_pack = _chapter_fact_pack(
        root,
        rows,
        workflow,
        source_paths={
            "workflow": workflow_path,
            "revisions": revisions_path,
            "course_map": course_map_path,
        },
    )
    prompt_plan = _reduce_prompt_plan(
        root,
        rows,
        course_map,
        fact_pack=fact_pack,
        max_input_chars=max_input_chars,
    )
    prompt = str(prompt_plan["prompt"])
    fact_summary = fact_pack.get("summary") if isinstance(fact_pack.get("summary"), dict) else {}
    result: dict[str, Any] = {
        "schema": SCHEMA,
        "bundle_dir": str(root),
        "status": "planned",
        "ok": True,
        "execute": bool(execute),
        "reuse_candidate": bool(reuse_candidate),
        "map_stage": {
            "workflow_json": str(workflow_path),
            "revisions_json": str(revisions_path),
            "expected_sections": len(expected_ids),
            "completed_sections": len(completed_ids),
            "missing_sections": missing,
            "chapter_fact_pack_schema": CHAPTER_FACT_PACK_SCHEMA,
            "chapter_fact_pack_revision": str(fact_pack.get("revision") or ""),
            "evidence_bound_sections": int(fact_summary.get("evidence_bound_sections") or 0),
            "review_only_sections": int(fact_summary.get("review_only_sections") or 0),
            "unbound_sections": list(fact_summary.get("unbound_section_ids") or []),
        },
        "reduce_stage": {
            "course_map_json": str(course_map_path),
            "input_chars": len(prompt),
            "full_input_chars": int(prompt_plan["full_input_chars"]),
            "max_input_chars": int(max_input_chars),
            "all_sections_included": bool(prompt_plan["all_sections_included"]),
            "prompt_within_budget": len(prompt) <= max(1000, int(max_input_chars)),
            "balanced_section_clipping": bool(prompt_plan["clipped_section_ids"]),
            "clipped_section_ids": list(prompt_plan["clipped_section_ids"]),
            "model": str(cfg.get("model") or ""),
            "evidence_reference_count": int(fact_summary.get("evidence_reference_count") or 0),
            "review_only_evidence_count": int(fact_summary.get("review_only_evidence_count") or 0),
            "source_kinds": list(fact_summary.get("source_kinds") or []),
            "evidence_lineage_complete": not bool(fact_summary.get("unbound_section_ids")),
            "input_profile": "chapter_fact_pack_compact_v2",
            "section_markdown_chars": DEFAULT_REDUCE_SECTION_MARKDOWN_CHARS,
            "facts_per_type": DEFAULT_REDUCE_FACTS_PER_TYPE,
            "facts_per_section": DEFAULT_REDUCE_FACTS_PER_SECTION,
            "quote_refs_per_section": DEFAULT_REDUCE_QUOTE_REFS_PER_SECTION,
            "review_refs_per_section": DEFAULT_REDUCE_REVIEW_REFS_PER_SECTION,
        },
        "operator_boundary": {
            "chapter_map_must_be_complete": True,
            "does_not_read_raw_asr": True,
            "provider_config_runtime_only": True,
            "preview_by_default": True,
            "network_requires_execute": True,
            "install_requires_quality_shape": True,
            "late_chapters_not_dropped": True,
            "over_budget_metadata_blocks_execution": True,
            "candidate_reuse_skips_model_call": True,
            "chapter_fact_pack_explicit": True,
            "evidence_ids_must_be_bound": True,
            "review_gap_not_promoted": True,
            "speaker_meaning_not_external_fact_check": True,
            "legacy_unbound_sections_are_review_only": True,
            "provider_returns_structured_reader_plan": True,
            "markdown_layout_is_deterministic": True,
            "json_schema_validation_before_install": True,
            "legacy_markdown_candidate_read_only_compatibility": True,
            "remote_proxy_requires_business_authorization": True,
        },
        "business_authorization": {
            "path": (
                str(Path(business_authorization_path).expanduser().resolve())
                if business_authorization_path
                else ""
            ),
            "required_for_remote_proxy": _uses_remote_proxy(cfg),
            "execution_mode": (
                "business_child_consent"
                if business_authorization_path
                else "direct_or_local"
            ),
        },
        "artifacts": {
            "json": "exports/smart-summary-global-reduce.json",
            "markdown": "exports/smart-summary-global-reduce.md",
            "prompt": "exports/smart-summary-global-reduce-prompt.md",
            "candidate": "exports/smart-summary.codex.md",
            "final_summary": "exports/smart-summary.md",
            "chapter_fact_pack": "exports/smart-summary-chapter-fact-pack.json",
            "reader_plan": "exports/smart-summary-reader-plan.json",
            "raw_response": "exports/smart-summary-global-reduce-raw-response.txt",
        },
        "updated_at": now_iso(),
    }
    if missing or not rows:
        result["status"] = "blocked_incomplete_map"
        result["ok"] = False
        result["next_actions"] = ["Complete all semantic chapter rewrites before global Reduce."]
        return _write(root, result, prompt=prompt, fact_pack=fact_pack, write=write)
    if not prompt_plan["all_sections_included"] or len(prompt) > max(1000, int(max_input_chars)):
        result["status"] = "blocked_reduce_input_budget"
        result["ok"] = False
        result["next_actions"] = ["Reduce chapter metadata or increase max_input_chars; late chapters will not be silently dropped."]
        return _write(root, result, prompt=prompt, fact_pack=fact_pack, write=write)
    manifest = _mapping(root / "manifest.json")
    title = str(manifest.get("title") or root.name)
    first_time = str(rows[0].get("time_range") or "").split(" - ", 1)[0] if rows else ""
    last_time = str(rows[-1].get("time_range") or "").split(" - ", 1)[-1] if rows else ""
    reused_candidate = False
    reader_plan: dict[str, Any] = {}
    reader_plan_validation: dict[str, Any] = {
        "passed": False,
        "errors": ["reader_plan_not_evaluated"],
        "compatibility_mode": False,
    }
    raw_candidate = ""
    if recovery_execution_report:
        call = _recover_execution_report_call(root, recovery_execution_report)
        raw_candidate = str(call.get("content") or "")
        reader_plan, reader_plan_validation, content = _validated_reader_plan_content(
            raw_candidate,
            fact_pack=fact_pack,
            expected_ids=expected_ids,
            title=title,
            first_time=first_time,
            last_time=last_time,
        )
        reused_candidate = True
        result["recovery"] = {
            "execution_report": str(call.get("execution_report") or ""),
            "execution_report_sha256": str(
                call.get("execution_report_sha256") or ""
            ),
            "network_requests_made": False,
        }
    elif reuse_candidate:
        reader_plan_path = exports / "smart-summary-reader-plan.json"
        if reader_plan_path.is_file():
            reader_plan = _mapping(reader_plan_path)
            normalization = normalize_reader_plan_candidate(
                reader_plan,
                fact_pack=fact_pack,
            )
            reader_plan = normalization["plan"]
            reader_plan_validation = validate_reader_plan(
                reader_plan,
                fact_pack=fact_pack,
                expected_section_ids=expected_ids,
            )
            reader_plan_validation = {
                **reader_plan_validation,
                "normalizations": normalization["repairs"],
            }
            content = (
                render_reader_summary(
                    reader_plan,
                    title=title,
                    first_time=first_time,
                    last_time=last_time,
                )
                if reader_plan_validation["passed"]
                else ""
            )
            call = {"ok": True, "error": "", "content": content}
            reused_candidate = True
        else:
            raw_response_path = exports / "smart-summary-global-reduce-raw-response.txt"
            if raw_response_path.is_file():
                # Intent: recover a complete provider response after a
                # deterministic contract-label or presentation-length repair.
                # Decision: parse, normalize and revalidate the immutable raw
                # response before considering the legacy Markdown candidate.
                # Reason: a valid paid/local result must not require another
                # model call merely because the first validation was stricter
                # than the deterministic normalizer.
                # Evidence: the 2026-08-10 interview Reduce was complete and
                # evidence-bound; only overview.text exceeded maxLength=240.
                # Effective scope: --reuse-candidate only; no network call,
                # evidence mutation, silent fallback or raw response rewrite.
                raw_candidate = raw_response_path.read_text(encoding="utf-8-sig")
                reader_plan, reader_plan_validation, content = _validated_reader_plan_content(
                    raw_candidate,
                    fact_pack=fact_pack,
                    expected_ids=expected_ids,
                    title=title,
                    first_time=first_time,
                    last_time=last_time,
                )
                call = {"ok": True, "error": "", "content": content}
                reused_candidate = True
            else:
                candidate_path = exports / "smart-summary-global-reduce-candidate.md"
                if not candidate_path.exists():
                    result["status"] = "blocked_missing_reduce_candidate"
                    result["ok"] = False
                    result["next_actions"] = ["Run one successful Reduce call before reusing its persisted candidate."]
                    return _write(root, result, prompt=prompt, fact_pack=fact_pack, write=write)
                content = _normalise_markdown(candidate_path.read_text(encoding="utf-8-sig"), title=title)
                call = {"ok": True, "error": "", "content": content}
                reused_candidate = True
                reader_plan_validation = {
                    "passed": True,
                    "errors": [],
                    "compatibility_mode": True,
                    "detail": "legacy Markdown candidate reused without upgrading its generation contract",
                }
    else:
        if not execute:
            result["next_actions"] = ["Rerun with --execute after reviewing the Reduce input and provider boundary."]
            return _write(root, result, prompt=prompt, fact_pack=fact_pack, write=write)
        if _uses_remote_proxy(cfg) and not business_authorization_path:
            result.update(
                {
                    "status": "business_authorization_required",
                    "ok": False,
                    "next_actions": [
                        "Create or reuse one matching business authorization for this Reduce call.",
                        "Rerun with --business-authorization <active authorization JSON>; direct remote proxy execution is forbidden.",
                    ],
                }
            )
            return _write(
                root, result, prompt=prompt, fact_pack=fact_pack, write=write
            )
        if _uses_remote_proxy(cfg) and not write:
            result.update(
                {
                    "status": "business_authorization_write_required",
                    "ok": False,
                    "next_actions": [
                        "Remote business-child execution writes an immutable request, child consent and Broker receipt; omit --no-write."
                    ],
                }
            )
            return _write(
                root, result, prompt=prompt, fact_pack=fact_pack, write=write
            )
        messages = [
            {
                "role": "system",
                "content": (
                    "你是长课程视频的总编辑。只根据章节事实包和课程地图做全局 Reduce，不得回到原始 ASR，不得编造视觉事实。"
                    "只输出符合字段合同的一个 JSON 对象，不输出 Markdown、解释或思考过程。字段合同："
                    + reader_plan_prompt_contract()
                ),
            },
            {"role": "user", "content": prompt},
        ]
        if business_authorization_path:
            business_context = _prepare_business_reduce_context(
                root,
                cfg,
                business_authorization_path,
                lineage_input_paths=[workflow_path, revisions_path, course_map_path],
            )
            request_path = _write_business_reduce_request(
                root,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
            )
            child = create_business_child_consent(
                business_context["authorization_path"],
                stage_id=business_context["stage_id"],
                artifact_paths=[request_path],
                producer=business_context["producer"],
                input_paths=business_context["lineage_input_paths"],
                max_calls=1,
                write=True,
            )
            execution = execute_consented_model_task(
                child["consent_path"],
                expected_route_revision=business_context["route_revision"],
                write=True,
            )
            model_result = (
                execution.get("model_result")
                if isinstance(execution.get("model_result"), dict)
                else {}
            )
            call = {
                "ok": bool(execution.get("ok")),
                "error": str(
                    execution.get("error") or model_result.get("error") or ""
                ),
                "content": _connector_model_content(model_result),
                "business_child_consent": _public_child_consent(child),
                "connector_status": str(execution.get("status") or ""),
            }
        else:
            call = model_task_api_call(
                "smart_summary_global_reduce",
                provider_config=cfg,
                messages=messages,
                execute=True,
                temperature=temperature,
                response_format={"type": "json_object"},
                max_tokens=max_tokens,
                write=False,
            )
        raw_candidate = str(call.get("content") or "")
        reader_plan, reader_plan_validation, content = _validated_reader_plan_content(
            raw_candidate if call.get("ok") else "",
            fact_pack=fact_pack,
            expected_ids=expected_ids,
            title=title,
            first_time=first_time,
            last_time=last_time,
        )
    result["reader_plan"] = {
        "schema": READER_PLAN_SCHEMA,
        "validation": reader_plan_validation,
        "source_section_ids": list(reader_plan.get("source_section_ids") or []),
    }
    quality = _shape_quality(content, expected_ids=expected_ids, rows=rows, fact_pack=fact_pack)
    result["model_call"] = {
        "ok": bool(call.get("ok")),
        "error": str(call.get("error") or ""),
        "content_chars": len(content),
        "reused_candidate": reused_candidate,
        "business_child_consent": call.get("business_child_consent") or {},
        "connector_status": str(call.get("connector_status") or ""),
    }
    result["quality"] = quality
    if not call.get("ok"):
        result["status"] = "reduce_call_failed"
        result["ok"] = False
        result["next_actions"] = ["Retry the global Reduce call; chapter Map artifacts remain reusable."]
        return _write(root, result, prompt=prompt, raw_candidate=raw_candidate, fact_pack=fact_pack, write=write)
    if not reader_plan_validation.get("passed"):
        result["status"] = "reduce_reader_plan_failed"
        result["ok"] = False
        result["next_actions"] = ["Inspect reader-plan schema, evidence, chronology and semantic validation errors; do not install this candidate."]
        return _write(
            root,
            result,
            prompt=prompt,
            raw_candidate=raw_candidate,
            reader_plan=reader_plan,
            fact_pack=fact_pack,
            write=write,
        )
    if not quality["passed"]:
        result["status"] = "reduce_quality_failed"
        result["ok"] = False
        result["next_actions"] = ["Inspect failed Reduce shape checks; do not install this candidate."]
        return _write(
            root,
            result,
            prompt=prompt,
            candidate=content,
            raw_candidate=raw_candidate,
            reader_plan=reader_plan,
            fact_pack=fact_pack,
            write=write,
        )

    install_result: dict[str, Any] | None = None
    if write:
        exports.mkdir(parents=True, exist_ok=True)
        (exports / "smart-summary.codex.md").write_text(content, encoding="utf-8")
    if install:
        install_result = generate_smart_summary_with_codex(root, input_md=exports / "smart-summary.codex.md", write=write)
    result["install_result"] = install_result
    installed_quality = (install_result or {}).get("quality") if isinstance((install_result or {}).get("quality"), dict) else {}
    result["status"] = "completed" if (not install or installed_quality.get("passed")) else "installed_quality_failed"
    result["ok"] = bool(not install or installed_quality.get("passed"))
    result["next_actions"] = [] if result["ok"] else ["Inspect exports/smart-summary-quality.md and revise only the failing Reduce output."]
    return _write(
        root,
        result,
        prompt=prompt,
        candidate=content,
        raw_candidate=raw_candidate,
        reader_plan=reader_plan,
        fact_pack=fact_pack,
        write=write,
    )


def _recover_execution_report_call(
    root: Path,
    execution_report: str | Path,
) -> dict[str, Any]:
    """Recover a paid model response without another network request.

    Intent: prevent a completed Broker call from being lost after a runner error.
    Decision: accept only an immutable execution report located inside this Bundle.
    Reason: the report already binds consent, task, route and exact request artifact.
    Evidence: the Trusted Connector persists connector-execution.json before the
    summary runner parses or installs the provider response.
    Effective scope: Smart Summary Global Reduce recovery only; it does not reserve
    consent, contact a provider, or relax reader-plan validation.
    """

    path = Path(execution_report).expanduser().resolve()
    if not path.is_file():
        return {
            "ok": False,
            "error": f"execution report not found: {path}",
            "content": "",
            "connector_status": "recovery_report_missing",
            "execution_report": str(path),
        }
    try:
        path.relative_to(root)
    except ValueError:
        return {
            "ok": False,
            "error": "execution report is outside the target Bundle",
            "content": "",
            "connector_status": "recovery_report_outside_bundle",
            "execution_report": str(path),
        }
    report = read_json(path)
    model_result = (
        report.get("model_result")
        if isinstance(report.get("model_result"), dict)
        else {}
    )
    content = _connector_model_content(model_result)
    task_matches = str(report.get("task") or "") == "smart_summary_global_reduce"
    ok = bool(report.get("ok")) and bool(model_result.get("ok")) and task_matches
    return {
        "ok": ok,
        "error": (
            ""
            if ok
            else str(
                report.get("error")
                or model_result.get("error")
                or "execution report is not a completed global Reduce call"
            )
        ),
        "content": content if ok else "",
        "connector_status": str(report.get("status") or ""),
        "execution_report": str(path),
        "execution_report_sha256": sha256_file(path),
    }


def _connector_model_content(model_result: dict[str, Any]) -> str:
    runtime = (
        model_result.get("runtime_result")
        if isinstance(model_result.get("runtime_result"), dict)
        else {}
    )
    response = (
        model_result.get("response")
        if isinstance(model_result.get("response"), dict)
        else {}
    )
    value = runtime.get("content")
    if value is None:
        value = model_result.get("content")
    if value is None:
        value = response.get("content")
    if isinstance(value, str):
        return value
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False)
    return ""


def _validated_reader_plan_content(
    raw_candidate: str,
    *,
    fact_pack: dict[str, Any],
    expected_ids: set[str],
    title: str,
    first_time: str,
    last_time: str,
) -> tuple[dict[str, Any], dict[str, Any], str]:
    parsed = (
        parse_reader_plan(raw_candidate)
        if raw_candidate
        else {"ok": False, "plan": {}, "errors": ["reader_plan_parse_failed"]}
    )
    reader_plan = parsed.get("plan") if isinstance(parsed.get("plan"), dict) else {}
    if parsed.get("ok"):
        normalization = normalize_reader_plan_candidate(
            reader_plan,
            fact_pack=fact_pack,
        )
        reader_plan = normalization["plan"]
        validation = validate_reader_plan(
            reader_plan,
            fact_pack=fact_pack,
            expected_section_ids=expected_ids,
        )
        validation = {**validation, "normalizations": normalization["repairs"]}
    else:
        errors = list(parsed.get("errors") or ["reader_plan_parse_failed"])
        validation = {
            "passed": False,
            "errors": errors,
            "error_count": len(errors),
            "compatibility_mode": False,
        }
    content = (
        render_reader_summary(
            reader_plan,
            title=title,
            first_time=first_time,
            last_time=last_time,
        )
        if validation.get("passed")
        else ""
    )
    return reader_plan, validation, content



def _uses_remote_proxy(cfg: dict[str, Any]) -> bool:
    return (
        str(cfg.get("execution_location") or "").strip().lower() == "remote"
        and str(cfg.get("adapter_backend") or "").strip().lower() == "proxy"
    )


def _prepare_business_reduce_context(
    root: Path,
    cfg: dict[str, Any],
    authorization_path: str | Path,
    *,
    lineage_input_paths: list[Path],
) -> dict[str, Any]:
    path = Path(authorization_path).expanduser().resolve()
    status = validate_model_business_authorization(path)
    if not status.get("valid"):
        blockers = [
            str(row.get("key") or "blocked")
            for row in status.get("blockers") or []
            if isinstance(row, dict)
        ]
        raise ValueError(
            "business authorization is not active: "
            + (",".join(blockers) or "unknown")
        )
    bound_bundle_dirs = {
        Path(str(value or "")).expanduser().resolve()
        for value in (status.get("bundle_dirs") or [status.get("bundle_dir")])
        if str(value or "").strip()
    }
    if root not in bound_bundle_dirs:
        raise ValueError("business authorization bundle does not match bundle_dir")
    payload = read_json(path)
    route_id = str(cfg.get("route_id") or "").strip()
    route_revision = str(cfg.get("route_revision") or "").strip()
    matches: list[dict[str, Any]] = []
    for stage in payload.get("stages") or []:
        if (
            not isinstance(stage, dict)
            or str(stage.get("task") or "") != "smart_summary_global_reduce"
        ):
            continue
        route = (
            stage.get("route_snapshot")
            if isinstance(stage.get("route_snapshot"), dict)
            else {}
        )
        if route_id and str(route.get("route_id") or "") != route_id:
            continue
        if route_revision and str(route.get("route_revision") or "") != route_revision:
            continue
        matches.append(stage)
    if len(matches) != 1:
        raise ValueError(
            "business authorization must contain exactly one matching smart_summary_global_reduce route stage"
        )
    stage = matches[0]
    producer = "smart_summary_global_reduce_request"
    if producer not in [str(value) for value in stage.get("allowed_producers") or []]:
        raise ValueError(
            "business authorization Reduce stage does not allow smart_summary_global_reduce_request"
        )
    known_paths = {
        str(row.get("path") or "")
        for row in payload.get("sources") or []
        if isinstance(row, dict)
    }
    known_paths.update(
        str(row.get("path") or "")
        for admission in payload.get("admissions") or []
        if isinstance(admission, dict)
        for row in admission.get("artifacts") or []
        if isinstance(row, dict)
    )
    inputs = [value.expanduser().resolve() for value in lineage_input_paths]
    if any(not value.is_file() for value in inputs):
        raise ValueError("global Reduce lineage inputs must exist")
    if any(str(value) not in known_paths for value in inputs):
        raise ValueError(
            "business authorization does not bind the current global Reduce inputs"
        )
    route = (
        stage.get("route_snapshot")
        if isinstance(stage.get("route_snapshot"), dict)
        else {}
    )
    return {
        "authorization_path": str(path),
        "stage_id": str(stage.get("id") or ""),
        "producer": producer,
        "lineage_input_paths": [str(value) for value in inputs],
        "route_revision": str(route.get("route_revision") or ""),
    }


def _write_business_reduce_request(
    root: Path,
    *,
    messages: list[dict[str, Any]],
    max_tokens: int,
    temperature: float,
) -> Path:
    path = (
        root
        / "exports"
        / "business-authorized-summary-requests"
        / "smart-summary-global-reduce.json"
    )
    write_json(
        path,
        {
            "schema": "video_knowledge_pipeline.smart_summary_global_reduce_request.v1",
            "task": "smart_summary_global_reduce",
            "messages": messages,
            "generation_parameters": {
                "temperature": float(temperature),
                "max_tokens": int(max_tokens),
                "response_format": "json_object",
            },
            "output_contract": {
                "schema": READER_PLAN_SCHEMA,
                "rendering": "deterministic_local_markdown",
            },
        },
    )
    return path


def _public_child_consent(child: dict[str, Any]) -> dict[str, str]:
    return {
        key: str(child.get(key) or "")
        for key in (
            "status",
            "consent_path",
            "consent_id",
            "route_revision",
            "admission_id",
        )
    }


def _reduce_prompt_plan(
    root: Path,
    rows: list[dict[str, Any]],
    course_map: dict[str, Any],
    *,
    max_input_chars: int,
    fact_pack: dict[str, Any] | None = None,
) -> dict[str, Any]:
    limit = max(1000, int(max_input_chars))
    pack = fact_pack or _chapter_fact_pack(root, rows, {})
    full_prompt = _render_reduce_prompt(root, rows, course_map, fact_pack=pack)
    if len(full_prompt) <= limit:
        return {
            "prompt": full_prompt,
            "full_input_chars": len(full_prompt),
            "clipped_section_ids": [],
            "all_sections_included": _all_section_ids_present(full_prompt, rows),
        }

    empty_rows = [{**row, "final_markdown": ""} for row in rows]
    fixed_chars = len(_render_reduce_prompt(root, empty_rows, course_map, fact_pack=pack))
    per_section_budget = max(80, (limit - fixed_chars) // max(1, len(rows)))
    clipped_rows, clipped_ids = _balanced_rows(rows, per_section_budget=per_section_budget)
    prompt = _render_reduce_prompt(root, clipped_rows, course_map, fact_pack=pack)
    while len(prompt) > limit and per_section_budget > 80:
        overflow_per_section = (len(prompt) - limit + len(rows) - 1) // max(1, len(rows))
        per_section_budget = max(80, per_section_budget - max(20, overflow_per_section))
        clipped_rows, clipped_ids = _balanced_rows(rows, per_section_budget=per_section_budget)
        prompt = _render_reduce_prompt(root, clipped_rows, course_map, fact_pack=pack)
    return {
        "prompt": prompt,
        "full_input_chars": len(full_prompt),
        "clipped_section_ids": clipped_ids,
        "all_sections_included": _all_section_ids_present(prompt, rows),
    }


def _render_reduce_prompt(
    root: Path, rows: list[dict[str, Any]], course_map: dict[str, Any], *, fact_pack: dict[str, Any]
) -> str:
    manifest = _mapping(root / "manifest.json")
    title = str(manifest.get("title") or root.name)
    content_profile = "interview" if "采访" in title else "course_or_general"
    fact_sections = _fact_sections_by_id(fact_pack)
    payload = {
        "title": title,
        "content_profile": content_profile,
        "course_map": course_map,
        "chapters": [
            {
                "section_id": row.get("section_id"),
                "title": row.get("title"),
                "time_range": row.get("time_range"),
                "markdown": _balanced_excerpt(
                    _section_text(row),
                    max_chars=DEFAULT_REDUCE_SECTION_MARKDOWN_CHARS,
                ),
                "facts": _compact_prompt_facts(fact_sections.get(str(row.get("section_id") or ""), {})),
                "evidence_refs": _compact_prompt_refs(fact_sections.get(str(row.get("section_id") or ""), {})),
                "evidence_status": fact_sections.get(str(row.get("section_id") or ""), {}).get("evidence_status", "legacy_unbound"),
            }
            for row in rows
        ],
    }
    first_time = str(rows[0].get("time_range") or "").split(" - ", 1)[0] if rows else ""
    last_time = str(rows[-1].get("time_range") or "").split(" - ", 1)[-1] if rows else ""
    instructions = f"""
请执行全局 Reduce：
1. 统一跨章节术语、实体和数字，发现冲突时放入待复核点，不得强行选边。
2. 去除章节间重复，但保留每个章节的独有观点、步骤、案例和话术。
3. 保持全片时间覆盖，不得只总结前段。
4. 只保留导航所需时间范围，不输出证据流水账。
5. 视觉证据未执行时必须如实说明。
6. 不直接编写 Markdown；先生成互斥、有序的主题结构，再由 VKP 确定性渲染读者正文。
7. 正文默认控制在 900–1300 个中文字符；复杂长内容最多 1600 字，优先删同义重复，不得删掉任何章节的独有信息。
8. “分段总结”必须原样包含全片首尾时间戳 `{first_time}` 与 `{last_time}`。
9. “关键观点”“可执行动作清单”“高频话术”中的每一项都必须带来源时间戳，并且每个栏目整体至少覆盖前段和后段两个时间区间。
10. 基本信息只能使用输入中明确存在的标题、讲师、时长等事实；视觉证据独有或冲突的数字放入待复核，不得当作确定事实。
11. 每条确定性内容必须能回链到同章 facts 中的 time_range、evidence_ids 和 source_kinds；不得补造不存在的 evidence_id。
12. fact_status=review_gap_not_fact、review_only evidence 或 legacy_unbound 只能进入“待复核点 / 低置信内容”，不得提升为确定事实。
13. fact_status=candidate_evidence 表示来源内候选证据，不代表外部世界已核真；任务是忠实还原说话人原意，主观评价应归因给说话人，不做外部事实裁判。
14. 数字、姓名、产品名或专业术语若没有 eligible evidence_id，必须保留原说话人表述并标明来源不充分，不得自行纠正或扩写。
15. core_insights 与 principles 不得同义重复；主题标题必须是读者可理解的语义标题，禁止使用截断口语、元话术或“章节一”等占位名。
16. themes 必须按时间排序且互不重叠，并使用“问题/原因/方法/案例/行动”字段；没有证据的字段返回空字符串，不得补造。
17. actions 只保留明确可执行动作；章节标题、视觉缺口、背景介绍和一般观点不得伪装成行动项。
18. verbatim_quote 必须能在相应 evidence snippet 中逐字找到；否则使用 reusable_expression，不得加引号冒充原句。 普通结论优先引用每章 eligible-evidence-set；只有逐字原句才引用单条 snippet ID。
19. 严格控制数组规模：core_insights 3–6 项（短内容不得为凑数重复观点）、themes 3–8 项、principles 3–5 项、actions 0–8 项、reusable_expressions 0–5 项、review_items 0–6 项。
20. 直接输出最终 JSON；不要在隐藏推理或解释中重复输入材料。
21. 当 content_profile=interview 时，未经 eligible evidence 明确出现的姓名、身份、职务一律不得推断；使用“受访者”“采访者”等匿名角色。
22. 当 content_profile=interview 时，个人治疗、投保或理赔选择只能表述为“受访者的经历/选择/看法”，不得改写成面向读者的医疗或保险建议；actions 只保留访谈中明确承诺的后续动作，没有则返回空数组。
""".strip()
    return instructions + "\n\n输入 JSON：\n" + json.dumps(payload, ensure_ascii=False, separators=(",", ":"))


def _balanced_rows(rows: list[dict[str, Any]], *, per_section_budget: int) -> tuple[list[dict[str, Any]], list[str]]:
    balanced: list[dict[str, Any]] = []
    clipped_ids: list[str] = []
    for row in rows:
        section_id = str(row.get("section_id") or "")
        text = _section_text(row)
        excerpt = _balanced_excerpt(text, max_chars=per_section_budget)
        if excerpt != text:
            clipped_ids.append(section_id)
        balanced.append({**row, "final_markdown": excerpt})
    return balanced, clipped_ids


def _balanced_excerpt(text: str, *, max_chars: int) -> str:
    value = str(text or "")
    limit = max(80, int(max_chars))
    if len(value) <= limit:
        return value
    marker = "\n\n[本章中段已按上下文预算压缩；头尾均保留]\n\n"
    available = max(32, limit - len(marker))
    head = max(16, int(available * 0.6))
    tail = max(16, available - head)
    return value[:head].rstrip() + marker + value[-tail:].lstrip()


def _all_section_ids_present(prompt: str, rows: list[dict[str, Any]]) -> bool:
    return all(str(row.get("section_id") or "") in prompt for row in rows if str(row.get("section_id") or ""))

def _shape_quality(
    content: str,
    *,
    expected_ids: set[str],
    rows: list[dict[str, Any]],
    fact_pack: dict[str, Any] | None = None,
) -> dict[str, Any]:
    required = (
        "基本信息",
        "一句话概览",
        "核心主题",
        "分段总结",
        "关键观点",
        "可执行动作清单",
        "高频话术",
        "待复核点",
    )
    checks = [
        {
            "key": f"heading:{heading}",
            "passed": bool(re.search(rf"(?m)^##\s+{re.escape(heading)}(?:\s|/|$)", content)),
        }
        for heading in required
    ]
    checks.append({"key": "final_marker", "passed": "codex_llm_rewrite_final" in content or "codex_final" in content})
    first_time = str(rows[0].get("time_range") or "").split(" - ", 1)[0] if rows else ""
    last_time = str(rows[-1].get("time_range") or "").split(" - ", 1)[-1] if rows else ""
    coverage = bool(first_time and last_time and first_time in content and last_time in content)
    checks.append({"key": "time_coverage", "passed": coverage, "detail": f"first={first_time}; last={last_time}"})
    checks.append({"key": "not_raw_json", "passed": not content.lstrip().startswith("{")})
    checks.append({"key": "minimum_length", "passed": len(content) >= 600, "detail": f"chars={len(content)}"})
    promoted_review_gaps = _review_gap_promotions(content, fact_pack or {})
    checks.append(
        {
            "key": "review_gap_not_promoted",
            "passed": not promoted_review_gaps,
            "detail": f"promoted_review_gaps={promoted_review_gaps[:8]}",
        }
    )
    reader_semantics = evaluate_reader_markdown_semantics(content)
    checks.append(
        {
            "key": "reader_semantic_maturity",
            "passed": bool(reader_semantics.get("passed")),
            "detail": f"problems={list(reader_semantics.get('problems') or [])[:12]}",
        }
    )
    return {
        "passed": all(bool(row.get("passed")) for row in checks),
        "checks": checks,
        "expected_section_count": len(expected_ids),
    }


def _review_gap_promotions(content: str, fact_pack: dict[str, Any]) -> list[str]:
    boundary = re.search(r"(?m)^##\s+待复核点(?:\s|/|$)", str(content or ""))
    confirmed_content = str(content or "")[: boundary.start()] if boundary else str(content or "")
    confirmed_compact = re.sub(r"\s+", "", confirmed_content)
    candidates: set[str] = set()
    for section in fact_pack.get("sections") or []:
        if not isinstance(section, dict):
            continue
        for fact in section.get("facts") or []:
            if isinstance(fact, dict) and str(fact.get("fact_status") or "") == "review_gap_not_fact":
                candidates.add(str(fact.get("text") or "").strip())
        for ref in section.get("evidence_refs") or []:
            if isinstance(ref, dict) and str(ref.get("fact_status") or "") == "review_gap_not_fact":
                candidates.add(str(ref.get("snippet") or "").strip())
    promoted: list[str] = []
    for value in sorted(candidates):
        compact = re.sub(r"\s+", "", value)
        if len(compact) >= 6 and compact in confirmed_compact:
            promoted.append(value[:120])
    return promoted


def _normalise_markdown(value: str, *, title: str = "") -> str:
    text = str(value or "").strip()
    fence = chr(96) * 3
    if text.startswith(fence):
        text = re.sub(r"^" + re.escape(fence) + r"(?:markdown)?\s*", "", text, count=1, flags=re.IGNORECASE)
        text = re.sub(r"\s*" + re.escape(fence) + r"$", "", text, count=1)
    text = text.strip()
    if not text:
        return ""

    section_headings = (
        "基本信息",
        "一句话概览",
        "核心主题",
        "分段总结",
        "关键观点",
        "可执行动作清单",
        "高频话术",
        "待复核点",
    )
    lines = text.splitlines()
    for index, line in enumerate(lines):
        if not line.startswith("# "):
            continue
        heading = line[2:].strip()
        if any(heading.startswith(required) for required in section_headings):
            lines[index] = "## " + heading
    first_index = next((index for index, line in enumerate(lines) if line.strip()), 0)
    if lines and lines[first_index].startswith("## "):
        lines.insert(first_index, f"# {title or '智能总结'} - 智能总结")
        lines.insert(first_index + 1, "")
    text = "\n".join(lines)
    if "生成方式：`codex_llm_rewrite_final`" not in text and "生成方式：`codex_final`" not in text:
        lines = text.splitlines()
        insert_at = 1 if lines and lines[0].startswith("#") else 0
        lines.insert(insert_at, "")
        lines.insert(insert_at + 1, "生成方式：`codex_llm_rewrite_final`。")
        text = "\n".join(lines)
    return text.rstrip() + "\n"

def _revision_rows(payload: dict[str, Any]) -> list[dict[str, Any]]:
    rows = payload.get("rows") if isinstance(payload.get("rows"), list) else []
    return [row for row in rows if isinstance(row, dict)]


def _section_text(row: dict[str, Any]) -> str:
    for key in ("final_markdown", "revised_markdown", "draft_markdown", "markdown", "content"):
        value = str(row.get(key) or "").strip()
        if value:
            return value
    return ""


def _mapping(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    value = read_json(path)
    return value if isinstance(value, dict) else {}


def _chapter_fact_pack(
    root: Path,
    rows: list[dict[str, Any]],
    workflow: dict[str, Any],
    *,
    source_paths: dict[str, Path] | None = None,
) -> dict[str, Any]:
    manifest = _mapping(root / "manifest.json")
    title = str(manifest.get("title") or root.name)
    content_profile = "interview" if "采访" in title else "course_or_general"
    workflow_sections = {
        str(row.get("section_id") or ""): row
        for row in workflow.get("sections") or []
        if isinstance(row, dict) and row.get("section_id")
    }
    sections = [
        _chapter_fact_section(row, workflow_sections.get(str(row.get("section_id") or ""), {}))
        for row in rows
    ]
    evidence_refs = [ref for section in sections for ref in section.get("evidence_refs") or [] if isinstance(ref, dict)]
    eligible_sections = [section for section in sections if section.get("evidence_status") == "evidence_bound"]
    review_only_sections = [section for section in sections if section.get("evidence_status") == "review_only"]
    unbound_sections = [section for section in sections if section.get("evidence_status") == "legacy_unbound"]
    source_kinds = sorted(
        {
            str(ref.get("source_kind") or "")
            for ref in evidence_refs
            if str(ref.get("source_kind") or "") and str(ref.get("source_kind") or "") != "evidence_group"
        }
    )
    lineage = [
        _lineage_entry(root, key, path)
        for key, path in sorted((source_paths or {}).items())
    ]
    base = {
        "schema": CHAPTER_FACT_PACK_SCHEMA,
        "bundle_dir": str(root),
        "title": title,
        "content_profile": content_profile,
        "sections": sections,
        "lineage": lineage,
        "summary": {
            "section_count": len(sections),
            "evidence_bound_sections": len(eligible_sections),
            "review_only_sections": len(review_only_sections),
            "unbound_section_ids": [str(section.get("section_id") or "") for section in unbound_sections],
            "evidence_reference_count": len(evidence_refs),
            "review_only_evidence_count": sum(
                1 for ref in evidence_refs if str(ref.get("fact_status") or "") == "review_gap_not_fact"
            ),
            "evidence_group_count": sum(
                1 for ref in evidence_refs if str(ref.get("source_kind") or "") == "evidence_group"
            ),
            "source_kinds": source_kinds,
        },
    }
    base["revision"] = canonical_json_sha256(
        {
            "schema": CHAPTER_FACT_PACK_SCHEMA,
            "title": title,
            "content_profile": content_profile,
            "sections": sections,
            "lineage": lineage,
        }
    )
    return base


def _chapter_fact_section(row: dict[str, Any], workflow_section: dict[str, Any]) -> dict[str, Any]:
    evidence = workflow_section.get("evidence") if isinstance(workflow_section.get("evidence"), dict) else {}
    citations = workflow_section.get("citations") if isinstance(workflow_section.get("citations"), list) else []
    if not citations and isinstance(evidence.get("citations"), list):
        citations = evidence.get("citations")
    refs: list[dict[str, Any]] = []
    for citation in citations or []:
        if isinstance(citation, dict):
            refs.extend(_citation_evidence_refs(citation))
    semantic_items = workflow_section.get("semantic_correction_items")
    if not isinstance(semantic_items, list):
        semantic_items = evidence.get("semantic_correction_items") if isinstance(evidence.get("semantic_correction_items"), list) else []
    for item in semantic_items:
        if isinstance(item, dict):
            ref = _semantic_correction_ref(item)
            if ref:
                refs.append(ref)
    refs = _dedupe_evidence_refs(refs)
    eligible_ids = [
        str(ref.get("evidence_id") or "")
        for ref in refs
        if str(ref.get("evidence_id") or "") and str(ref.get("fact_status") or "") != "review_gap_not_fact"
    ]
    review_only_ids = [
        str(ref.get("evidence_id") or "")
        for ref in refs
        if str(ref.get("evidence_id") or "") and str(ref.get("fact_status") or "") == "review_gap_not_fact"
    ]
    source_kinds = sorted(
        {
            str(ref.get("source_kind") or "")
            for ref in refs
            if str(ref.get("fact_status") or "") != "review_gap_not_fact" and str(ref.get("source_kind") or "")
        }
    )
    section_id = str(row.get("section_id") or "section")
    time_range = str(row.get("time_range") or workflow_section.get("time_range") or "")
    eligible_group_id = f"{section_id}:eligible-evidence-set" if eligible_ids else ""
    review_group_id = f"{section_id}:review-evidence-set" if review_only_ids else ""
    if eligible_group_id:
        refs.append(
            {
                "evidence_id": eligible_group_id,
                "source_kind": "evidence_group",
                "source_kinds": source_kinds,
                "time_range": time_range,
                "fact_status": "candidate_evidence",
                "source": "smart_summary_chapter_fact_pack",
                "member_evidence_ids": eligible_ids,
                "snippet": "",
            }
        )
    if review_group_id:
        refs.append(
            {
                "evidence_id": review_group_id,
                "source_kind": "evidence_group",
                "source_kinds": sorted(
                    {
                        str(ref.get("source_kind") or "")
                        for ref in refs
                        if str(ref.get("fact_status") or "") == "review_gap_not_fact"
                    }
                ),
                "time_range": time_range,
                "fact_status": "review_gap_not_fact",
                "source": "smart_summary_chapter_fact_pack",
                "member_evidence_ids": review_only_ids,
                "snippet": "",
            }
        )
    fact_rows = _workflow_fact_rows(evidence)
    facts = [
        {
            "fact_id": f"{section_id}-{kind}-{index:02d}",
            "fact_type": kind,
            "text": text,
            "time_range": time_range,
            "evidence_ids": [eligible_group_id] if eligible_group_id else ([review_group_id] if review_group_id else []),
            "source_kinds": source_kinds if eligible_group_id else ["review_gap"],
            "fact_status": "candidate_evidence" if eligible_ids else "review_gap_not_fact",
            "evidence_scope": "section_level_group",
        }
        for index, (kind, text) in enumerate(fact_rows, start=1)
    ]
    status = "evidence_bound" if eligible_ids else ("review_only" if review_only_ids else "legacy_unbound")
    return {
        "section_id": str(row.get("section_id") or ""),
        "title": str(row.get("title") or workflow_section.get("title") or ""),
        "time_range": time_range,
        "evidence_status": status,
        "eligible_evidence_ids": eligible_ids,
        "review_only_evidence_ids": review_only_ids,
        "source_kinds": source_kinds,
        "facts": facts,
        "evidence_refs": refs,
    }


def _workflow_fact_rows(evidence: dict[str, Any]) -> list[tuple[str, str]]:
    rows: list[tuple[str, str]] = []
    for key in ("summary_sentences", "key_points", "actions", "reusable_expressions", "visual_notes"):
        values = evidence.get(key) if isinstance(evidence.get(key), list) else []
        for value in values[:8]:
            text = str(value or "").strip()
            if text:
                rows.append((key, text))
    return rows[:24]


def _citation_evidence_refs(citation: dict[str, Any]) -> list[dict[str, Any]]:
    evidence_id = str(citation.get("citation_id") or citation.get("chunk_id") or "").strip()
    if not evidence_id:
        return []
    kind = str(citation.get("chunk_kind") or "").strip()
    snippet = str(citation.get("snippet") or "").strip()
    visual_snippet = str(citation.get("visual_snippet") or "").strip()
    temporal_snippet = str(citation.get("temporal_snippet") or "").strip()
    base_kind = str(citation.get("source_kind") or "").strip()
    if not base_kind:
        if kind == "visual_evidence":
            base_kind = "visual"
        elif kind == "content_asset":
            base_kind = "metadata"
        elif kind == "review_gap":
            base_kind = "review_gap"
        elif visual_snippet and snippet == visual_snippet:
            base_kind = "visual"
        elif temporal_snippet and snippet == temporal_snippet:
            base_kind = "temporal_visual"
        else:
            base_kind = "asr"
    common = {
        "time_range": str(citation.get("time_range") or ""),
        "fact_status": str(citation.get("fact_status") or "candidate_evidence"),
        "source": str(citation.get("source") or ""),
        "timeline_indexes": list(citation.get("timeline_indexes") or [])[:12],
        "evidence_paths": list(citation.get("evidence_paths") or [])[:8],
    }
    refs = [{"evidence_id": evidence_id, "source_kind": base_kind, "snippet": snippet, **common}]
    if visual_snippet and base_kind != "visual":
        refs.append({"evidence_id": f"{evidence_id}:visual", "source_kind": "visual", "snippet": visual_snippet, **common})
    if temporal_snippet and base_kind != "temporal_visual":
        refs.append({"evidence_id": f"{evidence_id}:temporal", "source_kind": "temporal_visual", "snippet": temporal_snippet, **common})
    return refs


def _semantic_correction_ref(item: dict[str, Any]) -> dict[str, Any]:
    evidence_id = str(item.get("candidate_id") or "").strip()
    if not evidence_id:
        return {}
    status = str(item.get("correction_status") or item.get("semantic_correction_status") or "candidate")
    review_only = bool(item.get("needs_human_review")) or status not in {"applied", "human_confirmed"}
    text = str(item.get("corrected_text") or item.get("candidate_text") or "").strip()
    return {
        "evidence_id": evidence_id,
        "source_kind": "human_confirmed" if status == "human_confirmed" else "transcript_semantic_correction",
        "time_range": str(item.get("time_range") or ""),
        "fact_status": "review_gap_not_fact" if review_only else "candidate_evidence",
        "source": "transcript_semantic_correction",
        "snippet": text,
        "linked_evidence_ids": list(item.get("evidence_ids") or [])[:12],
    }


def _dedupe_evidence_refs(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[str] = set()
    result: list[dict[str, Any]] = []
    for row in rows:
        evidence_id = str(row.get("evidence_id") or "")
        if not evidence_id or evidence_id in seen:
            continue
        seen.add(evidence_id)
        result.append(row)
    return result


def _fact_sections_by_id(fact_pack: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        str(row.get("section_id") or ""): row
        for row in fact_pack.get("sections") or []
        if isinstance(row, dict) and row.get("section_id")
    }


def _compact_prompt_facts(section: dict[str, Any]) -> list[dict[str, Any]]:
    """Project a bounded per-chapter fact set using TreeSummarize-style repacking."""

    keys = ("fact_type", "text", "time_range", "evidence_ids", "source_kinds", "fact_status")
    selected: list[dict[str, Any]] = []
    type_counts: dict[str, int] = {}
    for row in section.get("facts") or []:
        if not isinstance(row, dict):
            continue
        fact_type = str(row.get("fact_type") or "fact")
        if type_counts.get(fact_type, 0) >= DEFAULT_REDUCE_FACTS_PER_TYPE:
            continue
        value = {key: row.get(key) for key in keys}
        value["text"] = str(value.get("text") or "")[:200]
        selected.append(value)
        type_counts[fact_type] = type_counts.get(fact_type, 0) + 1
        if len(selected) >= DEFAULT_REDUCE_FACTS_PER_SECTION:
            break
    return selected


def _compact_prompt_refs(section: dict[str, Any]) -> list[dict[str, Any]]:
    """Keep evidence groups plus a small quote-capable snippet sample."""

    keys = ("evidence_id", "source_kind", "time_range", "fact_status")
    rows = [row for row in section.get("evidence_refs") or [] if isinstance(row, dict)]
    groups = [row for row in rows if str(row.get("source_kind") or "") == "evidence_group"]
    review_candidates = [
        row for row in rows
        if str(row.get("fact_status") or "") == "review_gap_not_fact"
    ][:DEFAULT_REDUCE_REVIEW_REFS_PER_SECTION]
    quote_candidates = [
        row
        for row in rows
        if str(row.get("source_kind") or "") != "evidence_group"
        and str(row.get("fact_status") or "") != "review_gap_not_fact"
        and str(row.get("snippet") or "").strip()
    ][:DEFAULT_REDUCE_QUOTE_REFS_PER_SECTION]
    compact: list[dict[str, Any]] = []
    for row in [*groups, *review_candidates, *quote_candidates]:
        value = {key: row.get(key) for key in keys}
        if row.get("source_kinds"):
            value["source_kinds"] = list(row.get("source_kinds") or [])
        snippet = str(row.get("snippet") or "").strip()
        if snippet:
            value["snippet"] = snippet[:220]
        compact.append(value)
    return compact


def _lineage_entry(root: Path, key: str, path: Path) -> dict[str, Any]:
    resolved = Path(path).resolve()
    try:
        relative = resolved.relative_to(root).as_posix()
    except ValueError:
        relative = str(resolved)
    return {
        "source": key,
        "path": relative,
        "sha256": sha256_file(resolved) if resolved.is_file() else "",
    }


def _write(
    root: Path,
    result: dict[str, Any],
    *,
    prompt: str,
    candidate: str = "",
    raw_candidate: str = "",
    reader_plan: dict[str, Any] | None = None,
    fact_pack: dict[str, Any] | None = None,
    write: bool,
) -> dict[str, Any]:
    if not write:
        return result
    exports = root / "exports"
    exports.mkdir(parents=True, exist_ok=True)
    write_json(exports / "smart-summary-global-reduce.json", result)
    (exports / "smart-summary-global-reduce.md").write_text(_render_markdown(result), encoding="utf-8")
    (exports / "smart-summary-global-reduce-prompt.md").write_text(prompt, encoding="utf-8")
    if candidate:
        (exports / "smart-summary-global-reduce-candidate.md").write_text(candidate, encoding="utf-8")
    if raw_candidate:
        (exports / "smart-summary-global-reduce-raw-response.txt").write_text(raw_candidate, encoding="utf-8")
    if reader_plan:
        write_json(exports / "smart-summary-reader-plan.json", reader_plan)
    if fact_pack:
        write_json(exports / "smart-summary-chapter-fact-pack.json", fact_pack)
    manifest_path = root / "manifest.json"
    manifest = _mapping(manifest_path)
    manifest["smart_summary_global_reduce_json"] = "exports/smart-summary-global-reduce.json"
    manifest["smart_summary_global_reduce_markdown"] = "exports/smart-summary-global-reduce.md"
    manifest["smart_summary_global_reduce_summary"] = {
        "status": result.get("status"),
        "ok": result.get("ok"),
        "updated_at": result.get("updated_at"),
    }
    if reader_plan:
        manifest["smart_summary_reader_plan_json"] = "exports/smart-summary-reader-plan.json"
        manifest["smart_summary_reader_plan_schema"] = str(reader_plan.get("schema") or "")
    if fact_pack:
        manifest["smart_summary_chapter_fact_pack_json"] = "exports/smart-summary-chapter-fact-pack.json"
        manifest["smart_summary_chapter_fact_pack_summary"] = {
            "schema": fact_pack.get("schema"),
            "revision": fact_pack.get("revision"),
            "summary": fact_pack.get("summary"),
        }
    write_json(manifest_path, manifest)
    return result


def _render_markdown(result: dict[str, Any]) -> str:
    lines = [
        "# Smart Summary Global Reduce",
        "",
        f"- Status: {result.get('status')}",
        f"- OK: {result.get('ok')}",
        f"- Map sections: {(result.get('map_stage') or {}).get('completed_sections', 0)} / {(result.get('map_stage') or {}).get('expected_sections', 0)}",
        "",
        "## Quality Checks",
        "",
    ]
    for row in (result.get("quality") or {}).get("checks") or []:
        lines.append(f"- {row.get('key')}: {row.get('passed')} {row.get('detail', '')}")
    return "\n".join(lines).rstrip() + "\n"
