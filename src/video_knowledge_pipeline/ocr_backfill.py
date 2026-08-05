from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from typing import Any

from .captiocr_resolver import (
    captiocr_candidate_roots,
    resolve_captiocr_root,
    resolve_tesseract_runtime,
)
from .frame_recapture import _coverage_audit, _quality_audit
from .markdown_text import markdown_table_cell as _md_cell
from .models import now_iso
from .repair_status import build_repair_status
from .storage import read_json, write_json

OCR_GAP_ISSUES = {
    "missing_visual_text",
    "structured_visual_without_ocr",
    "missing_ocr",
    "low_ocr_confidence",
    "ocr_text_empty",
    "screen_text_low_confidence",
}


def run_ocr_backfill(
    bundle_dir: str | Path,
    *,
    input_json: str | Path | None = None,
    execute: bool = False,
    language: str = "eng",
    captiocr_root: str | Path | None = None,
    limit: int = 0,
) -> dict[str, Any]:
    """Preview, import, or execute OCR backfill for a WebUI lecture bundle."""
    root = Path(bundle_dir).expanduser().resolve()
    manifest_path = root / "manifest.json"
    if not manifest_path.exists():
        raise FileNotFoundError(f"bundle missing manifest.json: {root}")
    manifest = read_json(manifest_path)
    if not isinstance(manifest, dict):
        raise ValueError("manifest.json must contain a JSON object")

    timeline = _read_timeline(root)
    candidates = _ocr_candidates(root, timeline)
    if limit and int(limit) > 0:
        candidates = candidates[: int(limit)]
    template_path = _write_ocr_input_template(root, candidates)
    screen_text_recovery = _screen_text_recovery_plan(root, candidates)
    imported_entries = _read_ocr_input(input_json) if input_json else []
    results: list[dict[str, Any]]
    runner = {"available": False, "name": "captiocr", "error": ""}
    captiocr = resolve_captiocr_root(captiocr_root)

    if imported_entries:
        results = _results_from_imported_entries(imported_entries, candidates)
    elif execute:
        runner, results = _run_captiocr_candidates(candidates, language=language, captiocr_root=captiocr_root)
    else:
        results = [_candidate_result(candidate, executed=False, ok=False) for candidate in candidates]

    backfill = _backfill_ocr_results(root, manifest, timeline, results) if imported_entries or execute else {
        "updated": 0,
        "updated_indexes": [],
        "source_package_updated": False,
    }
    timeline = _read_timeline(root)
    summary = {
        "total": len(results),
        "execute": execute,
        "input_json": str(Path(input_json).expanduser().resolve()) if input_json else "",
        "language": language,
        "limit": int(limit or 0),
        "succeeded": sum(1 for item in results if item.get("ok") and str(item.get("text") or "").strip()),
        "failed": sum(1 for item in results if item.get("executed") and not item.get("ok")),
        "planned": sum(1 for item in results if not item.get("executed")),
        "updated_at": now_iso(),
        "input_template_json": str(template_path),
    }
    manifest["coverage"] = _coverage_audit(timeline)
    manifest["ocr_backfill"] = {
        "schema": "lecture_ocr_backfill.v1",
        "count": len(candidates),
        "language": language,
        "captiocr": captiocr,
        "runner": runner,
        "items": candidates,
        "last_run": summary,
        "last_backfill": {**backfill, "updated_at": now_iso()},
        "input_template_json": str(template_path),
        "screen_text_recovery": screen_text_recovery,
    }
    manifest["repair_status"] = build_repair_status(manifest, timeline)
    write_json(manifest_path, manifest)

    report_path = root / "ocr-backfill-report.md"
    report_path.write_text(_render_ocr_backfill_report(root, results, summary, runner, template_path, screen_text_recovery), encoding="utf-8")
    handoff_path = root / "ocr-backfill-handoff.md"
    handoff_json_path = root / "ocr-backfill-handoff.json"
    handoff = _build_ocr_backfill_handoff(
        root,
        manifest,
        results,
        summary,
        runner,
        captiocr,
        screen_text_recovery,
        template_path,
        report_path,
        handoff_path,
        handoff_json_path,
    )
    write_json(handoff_json_path, handoff)
    handoff_path.write_text(_render_ocr_backfill_handoff_markdown(handoff), encoding="utf-8")
    manifest["ocr_backfill"]["handoff_markdown"] = str(handoff_path)
    manifest["ocr_backfill"]["handoff_json"] = str(handoff_json_path)
    write_json(manifest_path, manifest)
    return {
        "bundle_dir": str(root),
        "manifest_path": str(manifest_path),
        "report_path": str(report_path),
        "handoff_path": str(handoff_path),
        "handoff_json_path": str(handoff_json_path),
        "input_template_json": str(template_path),
        "summary": summary,
        "runner": runner,
        "captiocr": captiocr,
        "backfill": backfill,
        "items": results,
        "screen_text_recovery": screen_text_recovery,
    }


def _read_timeline(root: Path) -> list[dict[str, Any]]:
    timeline_path = root / "timeline.json"
    if not timeline_path.exists():
        return []
    timeline = read_json(timeline_path)
    return [item for item in timeline if isinstance(item, dict)] if isinstance(timeline, list) else []


def _ocr_candidates(root: Path, timeline: list[dict[str, Any]]) -> list[dict[str, Any]]:
    candidates = []
    for index, item in enumerate(timeline, start=1):
        issues = _quality_issues(item)
        inferred = _inferred_screen_text_issues(item)
        issues = _dedupe([*issues, *inferred])
        has_visual_text = bool(str(item.get("visual_text") or "").strip())
        image_path = _first_existing_image(root, item)
        if not image_path and not (set(issues) & OCR_GAP_ISSUES):
            continue
        if has_visual_text and not (set(issues) & OCR_GAP_ISSUES):
            continue
        candidates.append(
            {
                "index": int(item.get("index") or index),
                "start": item.get("start", 0),
                "end": item.get("end", 0),
                "material_types": item.get("material_types", []),
                "quality_issues": issues,
                "image_path": str(image_path) if image_path else "",
                "image_exists": bool(image_path and image_path.exists()),
                "visual_text": item.get("visual_text", ""),
                "visual_route": item.get("visual_route", ""),
                "signals": item.get("signals", []),
                "recovery": _screen_text_recovery_for_item(root, item, issues, image_path),
            }
        )
    return candidates


def _first_existing_image(root: Path, item: dict[str, Any]) -> Path | None:
    paths = []
    for asset in item.get("assets") or []:
        if not isinstance(asset, dict):
            continue
        candidate = str(asset.get("source") or asset.get("resolved_path") or asset.get("path") or "")
        if candidate:
            paths.append(candidate)
    paths.extend(str(path) for path in item.get("frame_paths") or [] if path)
    for raw_path in paths:
        path = Path(raw_path).expanduser()
        if not path.is_absolute():
            path = root / path
        if path.exists() and path.is_file() and path.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tif", ".tiff"}:
            return path.resolve()
    return None


def _screen_text_recovery_plan(root: Path, candidates: list[dict[str, Any]]) -> dict[str, Any]:
    items = []
    counts: dict[str, int] = {}
    for candidate in candidates:
        recovery = candidate.get("recovery") if isinstance(candidate.get("recovery"), dict) else {}
        strategy = str(recovery.get("strategy") or "unknown")
        counts[strategy] = counts.get(strategy, 0) + 1
        items.append(
            {
                "index": candidate.get("index"),
                "strategy": strategy,
                "recommended_tool": recovery.get("recommended_tool", ""),
                "reason": recovery.get("reason", ""),
                "image_path": candidate.get("image_path", ""),
                "crop_candidates": recovery.get("crop_candidates", []),
            }
        )
    return {
        "schema": "lecture_screen_text_recovery_plan.v1",
        "bundle_dir": str(root),
        "created_at": now_iso(),
        "strategy_counts": counts,
        "items": items,
        "notes": [
            "This is a planning layer only; run_ocr_backfill preview does not crop images or execute OCR.",
            "document_visual and mixed screenshots should first use ebook_markdown_pipeline through run_visual_structure_plan.",
            "small UI text and software/browser/editor screenshots should use crop-and-OCR only as a targeted recovery step, then keep the original frame evidence.",
            "When OCR cannot be trusted, use multimodal visual description or human review/keep-image instead of pretending screen text is covered.",
        ],
    }


def _screen_text_recovery_for_item(root: Path, item: dict[str, Any], issues: list[str], image_path: Path | None) -> dict[str, Any]:
    route = str(item.get("visual_route") or "")
    material_types = {str(value) for value in item.get("material_types") or []}
    signals = {str(value) for value in item.get("signals") or []}
    low_confidence = "screen_text_low_confidence" in issues
    has_image = bool(image_path and image_path.exists())
    if route == "document_visual":
        strategy = "ebook_pipeline"
        tool = "ebook_markdown_pipeline"
        reason = "图文型截图应优先用 ebook_markdown_pipeline 做版面、表格、公式、代码和文字结构化。"
    elif route == "mixed":
        strategy = "ebook_pipeline_plus_multimodal"
        tool = "ebook_markdown_pipeline + multimodal_frame_analyzer"
        reason = "混合画面既可能有文档/表格/代码，也可能有界面状态或动作；图文解析和多模态理解都应保留。"
    elif low_confidence or _is_ui_like_item(route, material_types, signals):
        strategy = "crop_and_ocr"
        tool = "crop plan + CaptiOCR/Tesseract or ebook_markdown_pipeline on crops"
        reason = "软件界面、浏览器、编辑器或小 UI 文本容易被全帧 OCR 漏掉，应先裁剪主体区域再识别。"
    elif route in {"semantic_frame", "temporal_sequence"}:
        strategy = "multimodal_text_description"
        tool = "multimodal_frame_analyzer"
        reason = "非图文主导画面更需要多模态描述屏幕状态；只在存在可读文字区域时补 OCR。"
    else:
        strategy = "human_review_keep_image"
        tool = "human review"
        reason = "无法稳定判断文字区域；保留原图证据并人工决定是否转写。"
    return {
        "strategy": strategy,
        "recommended_tool": tool,
        "reason": reason,
        "has_image": has_image,
        "crop_candidates": _crop_candidates_for_item(root, item, image_path) if has_image else [],
        "issues": issues,
    }


def _inferred_screen_text_issues(item: dict[str, Any]) -> list[str]:
    issues: list[str] = []
    if _is_wrapper_only_visual_text(item):
        issues.append("ocr_text_empty")
    route = str(item.get("visual_route") or "")
    material_types = {str(value) for value in item.get("material_types") or []}
    signals = {str(value) for value in item.get("signals") or []}
    if _is_ui_like_item(route, material_types, signals) and not _has_human_screen_text_acceptance(item):
        issues.append("screen_text_low_confidence")
    return issues


def _is_ui_like_item(route: str, material_types: set[str], signals: set[str]) -> bool:
    ui_tokens = {
        "ui",
        "software",
        "browser",
        "editor",
        "code_editor",
        "terminal",
        "screen",
        "interface",
        "app",
        "operation",
        "mouse",
        "workflow",
    }
    return route in {"semantic_frame", "temporal_sequence", "mixed"} and bool((material_types | signals) & ui_tokens)


def _is_wrapper_only_visual_text(item: dict[str, Any]) -> bool:
    visual_text = str(item.get("visual_text") or "").strip()
    if not visual_text:
        return False
    meaningful = []
    stems = _frame_stems(item)
    for line in visual_text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("<!--") and stripped.endswith("-->") and "source:" in stripped.lower():
            continue
        if stripped.startswith("# ") and stripped[2:].strip() in stems:
            continue
        meaningful.append(stripped)
    return not meaningful


def _has_human_screen_text_acceptance(item: dict[str, Any]) -> bool:
    review = item.get("human_review") if isinstance(item.get("human_review"), dict) else {}
    status = str(item.get("review_status") or review.get("status") or "").lower()
    return status in {"accepted", "reviewed", "keep_image", "corrected_visual_text"} or bool(item.get("human_corrected_visual_text") or review.get("corrected_visual_text"))


def _crop_candidates_for_item(root: Path, item: dict[str, Any], image_path: Path | None) -> list[dict[str, Any]]:
    source = str(image_path or "")
    index = int(item.get("index") or 0)
    crop_dir = root / "ocr-crops" / f"timeline-{index:04d}"
    base = [
        ("full_frame", [0.0, 0.0, 1.0, 1.0], "保留全帧，作为裁剪和人工复核的基准。"),
        ("central_content", [0.08, 0.08, 0.92, 0.86], "优先覆盖课件、浏览器主体、编辑器主体，避开边缘 UI。"),
        ("without_subtitle_band", [0.0, 0.0, 1.0, 0.82], "排除底部字幕/播放器控制栏，减少字幕污染。"),
        ("browser_or_editor_body", [0.05, 0.12, 0.95, 0.88], "针对浏览器、IDE、文档编辑器主体区域的小字。"),
        ("exclude_instructor_pip", [0.0, 0.0, 0.78, 0.88], "避开右下/侧边讲师画中画，保留屏幕主体。"),
    ]
    return [
        {
            "name": name,
            "source_image": source,
            "box": box,
            "coordinate_system": "relative_xyxy",
            "planned_output": str(crop_dir / f"{name}.jpg"),
            "purpose": purpose,
        }
        for name, box, purpose in base
    ]


def _frame_stems(item: dict[str, Any]) -> set[str]:
    stems: set[str] = set()
    for key in ("frame_paths", "temporal_frame_paths"):
        values = item.get(key)
        if isinstance(values, list):
            for value in values:
                text = str(value or "").strip()
                if text:
                    stems.add(Path(text).stem)
    for asset in item.get("assets") or []:
        if isinstance(asset, dict):
            for key in ("path", "source"):
                text = str(asset.get(key) or "").strip()
                if text:
                    stems.add(Path(text).stem)
    return stems


def _recovery_strategy_label(strategy: str) -> str:
    labels = {
        "ebook_pipeline": "图文型截图，优先复用 ebook_markdown_pipeline。",
        "ebook_pipeline_plus_multimodal": "混合画面，同时需要图文解析和多模态画面理解。",
        "crop_and_ocr": "小 UI 文本或界面文字，先规划裁剪再 OCR。",
        "multimodal_text_description": "非纯文字画面，优先用多模态描述屏幕状态。",
        "human_review_keep_image": "不确定或不可降维内容，保留图片并人工复核。",
        "unknown": "未分类。",
    }
    return labels.get(strategy, "")


def _read_ocr_input(input_json: str | Path) -> list[dict[str, Any]]:
    path = Path(input_json).expanduser().resolve()
    data = read_json(path)
    if isinstance(data, dict):
        rows = data.get("items") or data.get("results") or data.get("ocr") or []
    else:
        rows = data
    if not isinstance(rows, list):
        raise ValueError("OCR input JSON must be a list or an object with items/results/ocr")
    return [row for row in rows if isinstance(row, dict)]


def _write_ocr_input_template(root: Path, candidates: list[dict[str, Any]]) -> Path:
    path = root / "ocr-backfill-input-template.json"
    rows = []
    for candidate in candidates:
        rows.append(
            {
                "index": candidate.get("index"),
                "start": candidate.get("start", 0),
                "end": candidate.get("end", 0),
                "text": "",
                "source": candidate.get("image_path", ""),
                "image_path": candidate.get("image_path", ""),
                "image_exists": bool(candidate.get("image_exists")),
                "material_types": candidate.get("material_types", []),
                "quality_issues": candidate.get("quality_issues", []),
                "screen_text_recovery": candidate.get("recovery", {}),
                "crop_candidates": (candidate.get("recovery") or {}).get("crop_candidates", []),
                "current_visual_text": candidate.get("visual_text", ""),
                "notes": "",
            }
        )
    write_json(
        path,
        {
            "schema": "lecture_ocr_backfill_input.v1",
            "generated_at": now_iso(),
            "bundle_dir": str(root),
            "instructions": "Fill text with corrected OCR/manual visual text, then pass this JSON to run-ocr-backfill --input-json.",
            "items": rows,
        },
    )
    return path


def _results_from_imported_entries(entries: list[dict[str, Any]], candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    candidate_indexes = {_int_value(candidate.get("index")) for candidate in candidates}
    results = []
    for entry in entries:
        index = _int_value(entry.get("index") or entry.get("timeline_index"))
        text = str(entry.get("text") or entry.get("visual_text") or entry.get("ocr_text") or "").strip()
        source = str(entry.get("source") or "imported_json")
        notes = str(entry.get("notes") or "")
        wrapper_only = _imported_text_is_wrapper_only(text, source)
        needs_review = _imported_text_requires_human_review(source, notes)
        results.append(
            {
                "index": index,
                "text": "" if wrapper_only else text,
                "source": source,
                "executed": False,
                "ok": bool(index and text and not wrapper_only and not needs_review),
                "candidate": index in candidate_indexes,
                "stderr": (
                    "wrapper-only OCR text"
                    if wrapper_only
                    else (
                        "crop OCR requires human review before clearing screen text gap"
                        if needs_review
                        else ("" if index else "missing timeline index")
                    )
                ),
            }
        )
    return results


def _imported_text_requires_human_review(source: str, notes: str) -> bool:
    source_text = str(source or "").replace("\\", "/").lower()
    notes_text = str(notes or "").lower()
    return "ocr-crops/" in source_text or "screen_text_recovery crop ocr" in notes_text


def _imported_text_is_wrapper_only(text: str, source: str) -> bool:
    lines = [line.strip() for line in str(text or "").splitlines() if line.strip()]
    if not lines:
        return False
    source_stems = {Path(part.strip()).stem for part in str(source or "").split(";") if part.strip()}
    meaningful = []
    for line in lines:
        lower = line.lower()
        if lower.startswith("<!--") and lower.endswith("-->"):
            continue
        if line.startswith("![") and "](" in line and line.endswith(")"):
            continue
        if line.startswith("# ") and (not source_stems or line[2:].strip() in source_stems):
            continue
        meaningful.append(line)
    return not meaningful


def _run_captiocr_candidates(
    candidates: list[dict[str, Any]],
    *,
    language: str,
    captiocr_root: str | Path | None,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    runner, processor, image_cls = _load_captiocr_runner(captiocr_root)
    if not runner.get("available"):
        tesseract = runner.get("tesseract") if isinstance(runner.get("tesseract"), dict) else resolve_tesseract_runtime()
        if tesseract.get("cmd"):
            return _run_tesseract_cli_candidates(candidates, language=language, tesseract=tesseract, previous_error=str(runner.get("error") or ""))
        return runner, [
            {
                **_candidate_result(candidate, executed=True, ok=False),
                "stderr": runner.get("error", "CaptiOCR runner unavailable"),
            }
            for candidate in candidates
        ]

    results = []
    for candidate in candidates:
        result = _candidate_result(candidate, executed=True, ok=False)
        image_path = Path(str(candidate.get("image_path") or ""))
        if not image_path.exists():
            result["stderr"] = "image path does not exist"
            results.append(result)
            continue
        try:
            image = image_cls.open(image_path)
            image = processor.optimize_image_for_ocr(image)
            text = processor.process_image(image, lang_code=language, caption_mode=False)
            result["text"] = str(text or "").strip()
            result["ok"] = bool(result["text"])
        except Exception as exc:  # pragma: no cover - depends on optional local OCR stack
            result["stderr"] = str(exc)
        results.append(result)
    return runner, results


def _run_tesseract_cli_candidates(
    candidates: list[dict[str, Any]],
    *,
    language: str,
    tesseract: dict[str, Any],
    previous_error: str,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    cmd = str(tesseract.get("cmd") or "")
    runner = {
        "available": bool(cmd),
        "name": "tesseract_cli",
        "tesseract": tesseract,
        "fallback_from": "captiocr",
        "fallback_error": previous_error,
        "error": "" if cmd else "Tesseract command not found",
    }
    results = []
    for candidate in candidates:
        result = _candidate_result(candidate, executed=True, ok=False)
        image_path = Path(str(candidate.get("image_path") or ""))
        if not image_path.exists():
            result["stderr"] = "image path does not exist"
            results.append(result)
            continue
        command = [cmd, str(image_path), "stdout", "-l", language]
        try:
            completed = subprocess.run(command, text=True, encoding="utf-8", errors="replace", capture_output=True, check=False)
        except Exception as exc:  # pragma: no cover - depends on optional local OCR stack
            result["stderr"] = str(exc)
            results.append(result)
            continue
        text = str(completed.stdout or "").strip()
        result["text"] = text
        result["ok"] = completed.returncode == 0 and bool(text)
        result["stderr"] = str(completed.stderr or "").strip() if completed.returncode != 0 else ""
        results.append(result)
    return runner, results


def _load_captiocr_runner(captiocr_root: str | Path | None) -> tuple[dict[str, Any], Any, Any]:
    resolved = resolve_captiocr_root(captiocr_root)
    tesseract = resolve_tesseract_runtime()
    roots = [Path(root) for root in captiocr_candidate_roots(captiocr_root)]
    for root in roots:
        if root.exists() and str(root) not in sys.path:
            sys.path.insert(0, str(root))
    try:
        import captiocr.core.ocr as ocr_module
        from captiocr.core.ocr import OCRProcessor
        from PIL import Image
    except Exception as exc:  # pragma: no cover - depends on optional local OCR stack
        return {
            "available": False,
            "name": "captiocr",
            "root": str(resolved.get("root") or ""),
            "tesseract": tesseract,
            "checked_paths": list(resolved.get("checked") or []),
            "error": str(exc),
        }, None, None
    if tesseract.get("cmd"):
        ocr_module.TESSERACT_CMD = str(tesseract.get("cmd"))
    if tesseract.get("tessdata_prefix"):
        ocr_module.TESSDATA_PREFIX = str(tesseract.get("tessdata_prefix"))
    try:
        processor = OCRProcessor()
    except Exception as exc:  # pragma: no cover - depends on optional local OCR stack
        return {
            "available": False,
            "name": "captiocr",
            "root": str(resolved.get("root") or ""),
            "tesseract": tesseract,
            "checked_paths": list(resolved.get("checked") or []),
            "error": str(exc),
        }, None, None
    available = bool(processor.is_tesseract_available())
    return {
        "available": available,
        "name": "captiocr",
        "root": str(resolved.get("root") or ""),
        "tesseract": tesseract,
        "evidence": list(resolved.get("evidence") or []),
        "checked_paths": list(resolved.get("checked") or []),
        "error": "" if available else "Tesseract is not initialized",
    }, processor, Image


def _candidate_result(candidate: dict[str, Any], *, executed: bool, ok: bool) -> dict[str, Any]:
    return {
        "index": candidate.get("index"),
        "image_path": candidate.get("image_path", ""),
        "executed": executed,
        "ok": ok,
        "image_exists": bool(candidate.get("image_exists")),
        "text": "",
        "stderr": "",
        "screen_text_recovery": candidate.get("recovery", {}),
    }


def _backfill_ocr_results(
    root: Path,
    manifest: dict[str, Any],
    timeline: list[dict[str, Any]],
    results: list[dict[str, Any]],
) -> dict[str, Any]:
    updated_indexes = _apply_ocr_results_to_timeline(timeline, results)
    write_json(root / "timeline.json", timeline)

    source_updated = False
    source_package_text = str(manifest.get("source_package") or "").strip()
    source_package = Path(source_package_text).expanduser() if source_package_text else None
    if source_package and source_package.exists() and source_package.is_file():
        package = read_json(source_package)
        if isinstance(package, dict) and isinstance(package.get("timeline"), list):
            _apply_ocr_results_to_timeline(package["timeline"], results)
            package["coverage"] = _coverage_audit(package["timeline"])
            package["quality_audit"] = _quality_audit(package["timeline"])
            package["ocr_backfilled_at"] = now_iso()
            write_json(source_package, package)
            source_updated = True
    return {
        "updated": len(updated_indexes),
        "updated_indexes": updated_indexes,
        "source_package_updated": source_updated,
    }


def _apply_ocr_results_to_timeline(timeline: list[dict[str, Any]], results: list[dict[str, Any]]) -> list[int]:
    updated = []
    for result in results:
        text = str(result.get("text") or "").strip()
        index = _int_value(result.get("index"))
        if not (result.get("ok") and text and 1 <= index <= len(timeline)):
            continue
        item = timeline[index - 1]
        current = str(item.get("visual_text") or "").strip()
        if current and current != text:
            item.setdefault("original_visual_text", current)
        item["visual_text"] = text
        item["ocr_backfilled_text"] = text
        item["ocr_backfilled_at"] = now_iso()
        item["quality_issues"] = [issue for issue in _quality_issues(item) if issue not in OCR_GAP_ISSUES]
        updated.append(index)
    return updated


def _quality_issues(item: dict[str, Any]) -> list[str]:
    audit = _quality_audit([item])
    priority_items = audit.get("priority_items") if isinstance(audit, dict) else []
    if isinstance(priority_items, list) and priority_items:
        issues = priority_items[0].get("issues", [])
        return [str(issue) for issue in issues if issue]
    return []


def _render_ocr_backfill_report(
    root: Path,
    results: list[dict[str, Any]],
    summary: dict[str, Any],
    runner: dict[str, Any],
    template_path: Path,
    screen_text_recovery: dict[str, Any],
) -> str:
    lines = [
        "# OCR Backfill Report",
        "",
        f"- Bundle: `{root}`",
        f"- Execute: `{summary.get('execute')}`",
        f"- Input JSON: `{summary.get('input_json') or ''}`",
        f"- Input template JSON: `{template_path}`",
        f"- Runner: `{runner.get('name')}` available=`{runner.get('available')}`",
        f"- Total: {summary.get('total', 0)}",
        f"- Succeeded: {summary.get('succeeded', 0)}",
        f"- Failed: {summary.get('failed', 0)}",
        f"- Planned: {summary.get('planned', 0)}",
        "",
        "## Screen Text Recovery Plan",
        "",
        "这个计划只给出恢复策略和裁剪候选，不默认执行新的 OCR。图文型画面优先走 ebook_markdown_pipeline；小 UI 字、浏览器/编辑器界面、字幕干扰和画中画遮挡会被标成低置信度并进入人工或 crop OCR 计划。",
        "",
        "| Strategy | Count | Meaning |",
        "|---|---:|---|",
    ]
    for key, count in sorted((screen_text_recovery.get("strategy_counts") or {}).items()):
        lines.append(f"| `{key}` | {count} | {_recovery_strategy_label(key)} |")
    lines.extend([""])
    if runner.get("error"):
        lines.extend(["```text", str(runner.get("error") or "").strip(), "```", ""])
    for item in results:
        lines.extend(
            [
                f"## Timeline {item.get('index')}",
                "",
                f"- Image: `{item.get('image_path', '')}`",
                f"- OK: `{item.get('ok')}`",
                f"- Image exists: `{item.get('image_exists')}`",
                "",
            ]
        )
        recovery = item.get("screen_text_recovery") if isinstance(item.get("screen_text_recovery"), dict) else {}
        if recovery:
            lines.extend(
                [
                    f"- Recovery strategy: `{recovery.get('strategy', '')}`",
                    f"- Recommended tool: `{recovery.get('recommended_tool', '')}`",
                    f"- Reason: {recovery.get('reason', '')}",
                    "",
                ]
            )
            crop_candidates = recovery.get("crop_candidates") if isinstance(recovery.get("crop_candidates"), list) else []
            if crop_candidates:
                lines.extend(["### Crop candidates", "", "| Name | Box | Purpose |", "|---|---|---|"])
                for crop in crop_candidates:
                    if not isinstance(crop, dict):
                        continue
                    lines.append(
                        "| "
                        + " | ".join(
                            [
                                _md_cell(str(crop.get("name") or "")),
                                _md_cell(str(crop.get("box") or "")),
                                _md_cell(str(crop.get("purpose") or "")),
                            ]
                        )
                        + " |"
                    )
                lines.append("")
        text = str(item.get("text") or "").strip()
        if text:
            lines.extend(["```text", text, "```", ""])
        if item.get("stderr"):
            lines.extend(["```text", str(item.get("stderr") or "").strip(), "```", ""])
    return "\n".join(lines).rstrip() + "\n"


def _build_ocr_backfill_handoff(
    root: Path,
    manifest: dict[str, Any],
    results: list[dict[str, Any]],
    summary: dict[str, Any],
    runner: dict[str, Any],
    captiocr: dict[str, Any],
    screen_text_recovery: dict[str, Any],
    template_path: Path,
    report_path: Path,
    handoff_path: Path,
    handoff_json_path: Path,
) -> dict[str, Any]:
    mcp_args_path = _resolve_manifest_path(root, manifest.get("mcp_ocr_backfill_args"))
    mcp_command = _mcp_command("run_ocr_backfill", mcp_args_path) if mcp_args_path else ""
    unresolved = [
        item
        for item in results
        if not (item.get("ok") and str(item.get("text") or "").strip())
    ]
    return {
        "schema": "lecture_ocr_backfill_handoff.v1",
        "created_at": now_iso(),
        "bundle_dir": str(root),
        "status": _ocr_handoff_status(summary),
        "objective": "Fill missing screen text, board text, formulas, code, tables, and diagram labels without summarizing or dropping visual information.",
        "paths": {
            "handoff_markdown": str(handoff_path),
            "handoff_json": str(handoff_json_path),
            "report_markdown": str(report_path),
            "input_template_json": str(template_path),
            "manifest_json": str(root / "manifest.json"),
            "timeline_json": str(root / "timeline.json"),
        },
        "captiocr": {
            **captiocr,
            "runner_available": bool(runner.get("available")),
            "runner_error": str(runner.get("error") or ""),
        },
        "mcp": {
            "tool": "run_ocr_backfill",
            "args_path": str(mcp_args_path) if mcp_args_path else "",
            "args_exists": bool(mcp_args_path and mcp_args_path.exists()),
            "command": mcp_command,
            "import_argument": "input_json",
        },
        "summary": summary,
        "screen_text_recovery": screen_text_recovery,
        "next_steps": _ocr_handoff_next_steps(summary, captiocr, mcp_command),
        "import_schema": {
            "schema": "lecture_ocr_backfill_input.v1",
            "items": [
                {
                    "index": 1,
                    "text": "Exact OCR/manual transcription for the frame.",
                    "source": "absolute/or bundle-relative image path",
                    "notes": "Optional uncertainty or human review notes.",
                }
            ],
        },
        "items": [
            {
                "index": item.get("index"),
                "image_path": item.get("image_path", ""),
                "image_exists": bool(item.get("image_exists")),
                "needs_text": not bool(str(item.get("text") or "").strip()),
                "ok": bool(item.get("ok")),
                "stderr": str(item.get("stderr") or ""),
                "text": str(item.get("text") or ""),
                "screen_text_recovery": item.get("screen_text_recovery", {}),
            }
            for item in results
        ],
        "unresolved_indexes": [item.get("index") for item in unresolved],
    }


def _ocr_handoff_status(summary: dict[str, Any]) -> str:
    total = int(summary.get("total") or 0)
    succeeded = int(summary.get("succeeded") or 0)
    if total == 0:
        return "not_needed"
    if succeeded >= total:
        return "filled"
    if succeeded:
        return "partially_filled"
    return "needs_ocr"


def _ocr_handoff_next_steps(summary: dict[str, Any], captiocr: dict[str, Any], mcp_command: str) -> list[dict[str, Any]]:
    steps: list[dict[str, Any]] = []
    if int(summary.get("total") or 0) == 0:
        return [{"actor": "human_or_agent", "action": "No OCR gap candidates were detected for this bundle."}]
    if captiocr.get("available"):
        steps.append(
            {
                "actor": "agent",
                "action": "Run CaptiOCR/Tesseract through the existing OCR backfill tool for available frames.",
                "command": mcp_command,
            }
        )
    else:
        steps.append(
            {
                "actor": "human",
                "action": "Configure LECTURE_CAPTIOCR_ROOT or open another OCR/Tk tool, then fill ocr-backfill-input-template.json.",
                "configure_hint": captiocr.get("configure_hint", ""),
                "command_hint": captiocr.get("command_hint", ""),
            }
        )
    steps.append(
        {
            "actor": "human_or_agent",
            "action": "Import corrected OCR JSON through run_ocr_backfill input_json; preserve formulas, code indentation, tables, and diagram labels verbatim where possible.",
        }
    )
    return steps


def _resolve_manifest_path(root: Path, value: Any) -> Path | None:
    text = str(value or "").strip()
    if not text:
        return None
    path = Path(text).expanduser()
    return path if path.is_absolute() else root / path


def _mcp_command(tool: str, args_path: Path) -> str:
    escaped = str(args_path).replace("'", "''")
    return f".\\scripts\\video-knowledge.ps1 mcp-call {tool} '{escaped}'"


def _render_ocr_backfill_handoff_markdown(handoff: dict[str, Any]) -> str:
    paths = handoff.get("paths") if isinstance(handoff.get("paths"), dict) else {}
    captiocr = handoff.get("captiocr") if isinstance(handoff.get("captiocr"), dict) else {}
    mcp = handoff.get("mcp") if isinstance(handoff.get("mcp"), dict) else {}
    lines = [
        "# OCR Backfill Handoff",
        "",
        f"- Status: `{handoff.get('status')}`",
        f"- Bundle: `{handoff.get('bundle_dir')}`",
        f"- Input template: `{paths.get('input_template_json', '')}`",
        f"- Report: `{paths.get('report_markdown', '')}`",
        f"- CaptiOCR root: `{captiocr.get('root', '')}`",
        f"- CaptiOCR checkout available: `{captiocr.get('available')}`",
        f"- CaptiOCR runner available: `{captiocr.get('runner_available')}`",
        f"- MCP args: `{mcp.get('args_path', '')}`",
        "",
        "## MCP",
        "",
        "```powershell",
        str(mcp.get("command") or ""),
        "```",
        "",
        "## Next Steps",
        "",
    ]
    for step in handoff.get("next_steps") or []:
        if not isinstance(step, dict):
            continue
        lines.append(f"- `{step.get('actor', '')}`: {step.get('action', '')}")
        if step.get("command_hint"):
            lines.append(f"  Command hint: `{step.get('command_hint')}`")
        if step.get("configure_hint"):
            lines.append(f"  Configure: `{step.get('configure_hint')}`")
    lines.extend(
        [
            "",
            "## Screen Text Recovery Plan",
            "",
            "| Strategy | Count | Meaning |",
            "|---|---:|---|",
        ]
    )
    recovery = handoff.get("screen_text_recovery") if isinstance(handoff.get("screen_text_recovery"), dict) else {}
    for key, count in sorted((recovery.get("strategy_counts") or {}).items()):
        lines.append(f"| `{key}` | {count} | {_recovery_strategy_label(key)} |")
    lines.extend(
        [
            "",
            "## Import Schema",
            "",
            "```json",
            '{ "items": [ { "index": 1, "text": "exact screen text/formula/code/table text", "source": "frame path", "notes": "" } ] }',
            "```",
            "",
            "## Items",
            "",
            "| Index | OK | Needs text | Image | Error |",
            "|---:|---|---|---|---|",
        ]
    )
    for item in handoff.get("items") or []:
        if not isinstance(item, dict):
            continue
        lines.append(
            "| "
            + " | ".join(
                [
                    str(item.get("index") or ""),
                    str(bool(item.get("ok"))),
                    str(bool(item.get("needs_text"))),
                    _md_cell(str(item.get("image_path") or "")),
                    _md_cell(str(item.get("stderr") or "")),
                ]
            )
            + " |"
        )
    return "\n".join(lines).rstrip() + "\n"




def _dedupe(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        result.append(value)
    return result


def _int_value(value: Any) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0
