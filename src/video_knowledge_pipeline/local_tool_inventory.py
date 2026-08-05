from __future__ import annotations

import importlib.util
import os
import shutil
from pathlib import Path
from typing import Any

from .asr_runner import detect_asr_runners
from .captiocr_resolver import resolve_captiocr_root
from .markdown_text import markdown_table_cell as _md_cell
from .media_tools import resolve_media_tool, resolve_tesseract
from .models import now_iso
from .path_defaults import tool_source_review_root, workspace_root
from .storage import write_json
from .tool_research import recommended_trial_order

LOCAL_TOOL_INVENTORY_SCHEMA = "lecture_local_tool_inventory.v1"


def local_tool_inventory(output_dir: str | Path | None = None, *, write: bool = False) -> dict[str, Any]:
    """Inspect local reusable tools for the lecture extraction stack.

    The inventory is deliberately local-only. It reuses the existing tool matrix,
    ASR detector, media-tool resolver, and known project mirror paths so agents
    can decide what to run before installing or developing anything new.
    """
    tool_rows = recommended_trial_order()
    by_name = {str(row.get("name") or "").lower(): row for row in tool_rows}
    asr = detect_asr_runners()
    media = _media_tools()
    tools = [
        _local_project_tool(
            "BiliNote",
            "product_ui",
            "产品壳 / UI",
            ["LECTURE_BILINOTE_ROOT"],
            [
                tool_source_review_root() / "BiliNote",
                workspace_root() / "BiliNote",
            ],
            evidence_files=["BillNote_frontend/package.json", "backend/app"],
            reuse_role="直接作为 Web/Tauri UI、任务系统和人工复核入口。",
        ),
        _matrix_tool(by_name, "vidclaude", "visual_timeline", "视觉/时间线提取"),
        _matrix_tool(by_name, "peepshow", "fast_frame_ocr", "快速帧/OCR/报告"),
        _matrix_tool(by_name, "vidwise", "fallback_extractor", "轻量素材抽取 fallback"),
        _local_project_tool(
            "content-core",
            "architecture_reference",
            "CLI/MCP 架构参考",
            ["LECTURE_CONTENT_CORE_ROOT"],
            [
                tool_source_review_root() / "content-core",
                workspace_root() / "content-core",
                Path.home() / "GitHub" / "content-core",
            ],
            evidence_files=["pyproject.toml", "package.json", "src"],
            reuse_role="只借 CLI/MCP 架构经验；不把音频摘要逻辑当视频全量抽取能力。",
        ),
        _matrix_tool(by_name, "FunClip", "asr_timestamp_reference", "ASR/时间戳参考"),
        _captiocr_tool(),
    ]
    runnable_asr = [item for item in asr.get("tools") or [] if isinstance(item, dict) and item.get("runnable")]
    summary = {
        "schema": LOCAL_TOOL_INVENTORY_SCHEMA,
        "checked_at": now_iso(),
        "ready_for_ui": _available(tools, "BiliNote"),
        "ready_for_visual_extraction": any(_available(tools, name) for name in ("vidclaude", "peepshow", "vidwise")),
        "ready_for_asr": bool(runnable_asr),
        "ready_for_media": bool(media.get("ffmpeg") and media.get("ffprobe")),
        "ready_for_ocr": bool(media.get("tesseract") or _available(tools, "CaptiOCR")),
        "available_tools": [tool["name"] for tool in tools if tool.get("available")],
        "missing_tools": [tool["name"] for tool in tools if not tool.get("available")],
        "recommended_route": _recommended_route(tools, asr, media),
    }
    result = {
        "schema": LOCAL_TOOL_INVENTORY_SCHEMA,
        "checked_at": summary["checked_at"],
        "summary": summary,
        "tools": tools,
        "asr": asr,
        "media": media,
        "next_action": _next_action(summary, tools, asr, media),
    }
    if output_dir:
        out_dir = Path(output_dir).expanduser().resolve()
        out_dir.mkdir(parents=True, exist_ok=True)
        json_path = out_dir / "local-tool-inventory.json"
        markdown_path = out_dir / "local-tool-inventory.md"
        args_path = out_dir / "mcp-local-tool-inventory.args.json"
        result["output_json"] = str(json_path)
        result["output_markdown"] = str(markdown_path)
        result["mcp_args_path"] = str(args_path)
        if write:
            write_json(json_path, result)
            markdown_path.write_text(render_local_tool_inventory_markdown(result), encoding="utf-8")
            write_json(args_path, {"output_dir": str(out_dir), "write": True})
    return result


def render_local_tool_inventory_markdown(result: dict[str, Any]) -> str:
    summary = result.get("summary") if isinstance(result.get("summary"), dict) else {}
    next_action = result.get("next_action") if isinstance(result.get("next_action"), dict) else {}
    lines = [
        "# Local Lecture Tool Inventory",
        "",
        f"- Schema: `{result.get('schema', '')}`",
        f"- Checked: `{result.get('checked_at', '')}`",
        f"- UI ready: `{summary.get('ready_for_ui', False)}`",
        f"- Visual extraction ready: `{summary.get('ready_for_visual_extraction', False)}`",
        f"- ASR ready: `{summary.get('ready_for_asr', False)}`",
        f"- OCR ready: `{summary.get('ready_for_ocr', False)}`",
        f"- Next: `{next_action.get('key', '')}` / {next_action.get('label', '')}",
        "",
        "## Recommended Route",
        "",
    ]
    route = summary.get("recommended_route") if isinstance(summary.get("recommended_route"), list) else []
    for item in route:
        if not isinstance(item, dict):
            continue
        status = "ready" if item.get("ready") else "missing"
        lines.append(f"- `{status}` **{item.get('layer', '')}**: {item.get('tool', '')} - {item.get('use', '')}")
    lines.extend(
        [
            "",
            "## Tools",
            "",
            "| Tool | Layer | Available | Role | Evidence | Install / Configure |",
            "|---|---|---|---|---|---|",
        ]
    )
    for tool in result.get("tools") or []:
        if not isinstance(tool, dict):
            continue
        evidence = ", ".join(str(item) for item in tool.get("evidence") or []) or "-"
        install = str(tool.get("install_hint") or tool.get("configure_hint") or "")
        lines.append(
            "| {name} | {layer} | `{available}` | {role} | {evidence} | `{install}` |".format(
                name=_md_cell(str(tool.get("name") or "")),
                layer=_md_cell(str(tool.get("layer") or "")),
                available=bool(tool.get("available")),
                role=_md_cell(str(tool.get("reuse_role") or "")),
                evidence=_md_cell(evidence),
                install=_md_cell(install),
            )
        )
    lines.extend(["", "## ASR", "", "| Preset | Runnable | Command | Notes |", "|---|---|---|---|"])
    asr = result.get("asr") if isinstance(result.get("asr"), dict) else {}
    for runner in asr.get("tools") or []:
        if not isinstance(runner, dict):
            continue
        lines.append(
            "| {name} | `{runnable}` | `{command}` | {notes} |".format(
                name=_md_cell(str(runner.get("name") or "")),
                runnable=bool(runner.get("runnable")),
                command=_md_cell(str(runner.get("command_path") or runner.get("command") or "")),
                notes=_md_cell(str(runner.get("notes") or "")),
            )
        )
    return "\n".join(lines).rstrip() + "\n"


def _matrix_tool(by_name: dict[str, dict[str, Any]], name: str, kind: str, layer: str) -> dict[str, Any]:
    row = by_name.get(name.lower()) or {}
    return {
        "name": name,
        "kind": kind,
        "layer": layer,
        "available": bool(row.get("installed")),
        "evidence": list(row.get("installed_paths") or []),
        "reuse_role": str(row.get("reuse_role") or ""),
        "best_for": str(row.get("best_for") or ""),
        "install_hint": str(row.get("install_hint") or ""),
        "url": str(row.get("url") or ""),
        "source": "tool_matrix",
    }


def _local_project_tool(
    name: str,
    kind: str,
    layer: str,
    env_names: list[str],
    candidates: list[Path],
    *,
    evidence_files: list[str],
    reuse_role: str,
) -> dict[str, Any]:
    paths: list[Path] = []
    for env_name in env_names:
        env_value = os.environ.get(env_name, "").strip()
        if env_value:
            paths.append(Path(env_value).expanduser())
    paths.extend(candidates)
    evidence: list[str] = []
    for path in paths:
        if not path.exists():
            continue
        matched = [relative for relative in evidence_files if (path / relative).exists()]
        if matched:
            evidence.append(str(path.resolve()))
            evidence.extend(str((path / relative).resolve()) for relative in matched[:3])
            break
    return {
        "name": name,
        "kind": kind,
        "layer": layer,
        "available": bool(evidence),
        "evidence": evidence,
        "reuse_role": reuse_role,
        "configure_hint": f"Set {env_names[0]} to the local {name} root." if env_names else "",
        "source": "local_project_probe",
    }


def _captiocr_tool() -> dict[str, Any]:
    resolved = resolve_captiocr_root()
    evidence = list(resolved.get("evidence") or [])
    if resolved.get("root"):
        evidence.insert(0, str(resolved.get("root")))
    command = shutil.which("captiocr") or ""
    if command:
        evidence.append(command)
    return {
        "name": "CaptiOCR",
        "kind": "ocr_widget",
        "layer": "OCR 小组件 / 人工校对",
        "available": bool(evidence or importlib.util.find_spec("PIL")),
        "evidence": evidence,
        "reuse_role": "复用 Tk 截屏 OCR 和人工校对思路；作为 OCR backfill 的局部工具。",
        "configure_hint": str(resolved.get("configure_hint") or ""),
        "command_hint": str(resolved.get("command_hint") or command or ""),
        "checked_paths": list(resolved.get("checked") or []),
        "source": "local_project_probe",
    }


def _media_tools() -> dict[str, str]:
    return {
        "ffmpeg": resolve_media_tool("ffmpeg"),
        "ffprobe": resolve_media_tool("ffprobe"),
        "tesseract": resolve_tesseract(),
    }


def _recommended_route(tools: list[dict[str, Any]], asr: dict[str, Any], media: dict[str, str]) -> list[dict[str, Any]]:
    runnable_asr = next((item for item in asr.get("tools") or [] if isinstance(item, dict) and item.get("runnable")), {})
    visual = _first_available(tools, ["vidclaude", "peepshow", "vidwise"])
    return [
        {"layer": "产品壳 / UI", "tool": "BiliNote", "ready": _available(tools, "BiliNote"), "use": "课程任务、人工复核、WebUI。"},
        {
            "layer": "视觉/时间线提取",
            "tool": visual.get("name") or "vidclaude / peepshow / vidwise",
            "ready": bool(visual),
            "use": "把视频转成时间线、OCR、关键帧、原始证据。",
        },
        {
            "layer": "中文 ASR",
            "tool": runnable_asr.get("name") or "FunASR / SenseVoice / WhisperX",
            "ready": bool(runnable_asr),
            "use": "生成带时间戳的中文转写。",
        },
        {
            "layer": "媒体/OCR 基础设施",
            "tool": "ffmpeg + ffprobe + tesseract",
            "ready": bool(media.get("ffmpeg") and media.get("ffprobe")),
            "use": "抽帧、探测视频、OCR 回填。",
        },
        {"layer": "调度层", "tool": "lecture-extract", "ready": True, "use": "统一数据模型、CLI/MCP、Obsidian 导出。"},
    ]


def _next_action(summary: dict[str, Any], tools: list[dict[str, Any]], asr: dict[str, Any], media: dict[str, str]) -> dict[str, Any]:
    if not summary.get("ready_for_media"):
        return {
            "key": "configure_media_tools",
            "label": "配置 ffmpeg/ffprobe",
            "hint": "先让抽帧和视频探测可用；设置 FFMPEG_BINARY/FFPROBE_BINARY 或 LECTURE_FFMPEG_DIR。",
        }
    if not summary.get("ready_for_visual_extraction"):
        return {
            "key": "prepare_visual_extractor",
            "label": "准备 vidclaude/peepshow/vidwise",
            "hint": "优先复用本地已验证的 vidclaude 或 peepshow；没有就安装/拉取其中一个。",
        }
    if not summary.get("ready_for_asr"):
        return {
            "key": "prepare_asr",
            "label": "准备中文 ASR",
            "hint": "先运行 asr-env-status 写出 ASR 环境交接；优先 FunASR/SenseVoice，需要英文或对齐能力时再用 WhisperX/faster-whisper。",
        }
    if not _available(tools, "BiliNote"):
        return {
            "key": "configure_bilinote_root",
            "label": "配置 BiliNote UI",
            "hint": "设置 LECTURE_BILINOTE_ROOT 或把本地 BiliNote 镜像放到默认路径。",
        }
    return {
        "key": "ready_to_run_pipeline",
        "label": "可以运行课程抽取流水线",
        "hint": "用 detect-extractor-output / run-detected-lecture-pipeline 或 BiliNote 任务入口开始处理视频。",
    }


def _first_available(tools: list[dict[str, Any]], names: list[str]) -> dict[str, Any]:
    for name in names:
        for tool in tools:
            if str(tool.get("name") or "").lower() == name.lower() and tool.get("available"):
                return tool
    return {}


def _available(tools: list[dict[str, Any]], name: str) -> bool:
    return any(str(tool.get("name") or "").lower() == name.lower() and tool.get("available") for tool in tools)
