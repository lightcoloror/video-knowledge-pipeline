from __future__ import annotations

import os
import shutil
from pathlib import Path
from typing import Any

from .path_defaults import tool_source_review_root, workspace_root


CAPTIOCR_ENV_VAR = "LECTURE_CAPTIOCR_ROOT"
TESSERACT_ENV_VAR = "LECTURE_TESSERACT_CMD"
TESSDATA_ENV_VAR = "LECTURE_TESSDATA_PREFIX"
CAPTIOCR_MARKERS = ("CaptiOCR.py", "captiocr/core/ocr.py", "requirements.txt", "README.md")


def captiocr_candidate_roots(explicit_root: str | Path | None = None) -> list[Path]:
    """Return candidate CaptiOCR checkout roots in preference order."""
    candidates: list[Path] = []
    if explicit_root:
        candidates.append(Path(explicit_root).expanduser())
    env_root = os.environ.get(CAPTIOCR_ENV_VAR, "").strip()
    if env_root:
        candidates.append(Path(env_root).expanduser())
    candidates.extend(
        [
            tool_source_review_root() / "captiocr",
            tool_source_review_root() / "CaptiOCR",
            workspace_root() / "CaptiOCR",
            Path.home() / "GitHub" / "CaptiOCR",
        ]
    )
    seen: set[str] = set()
    unique: list[Path] = []
    for candidate in candidates:
        key = str(candidate).lower()
        if key in seen:
            continue
        seen.add(key)
        unique.append(candidate)
    return unique


def resolve_captiocr_root(explicit_root: str | Path | None = None) -> dict[str, Any]:
    """Find a usable local CaptiOCR checkout and return evidence for UI/agents."""
    checked = captiocr_candidate_roots(explicit_root)
    for root in checked:
        if not root.exists() or not root.is_dir():
            continue
        markers = [root / marker for marker in CAPTIOCR_MARKERS]
        evidence = [path.resolve() for path in markers if path.exists()]
        if evidence:
            return {
                "available": True,
                "root": str(root.resolve()),
                "evidence": [str(path) for path in evidence],
                "checked": [str(path) for path in checked],
                "configure_hint": f"Set {CAPTIOCR_ENV_VAR} to the local CaptiOCR root.",
                "command_hint": f"python {root.resolve() / 'CaptiOCR.py'}" if (root / "CaptiOCR.py").exists() else "",
            }
    return {
        "available": False,
        "root": "",
        "evidence": [],
        "checked": [str(path) for path in checked],
        "configure_hint": f"Set {CAPTIOCR_ENV_VAR} to the local CaptiOCR root.",
        "command_hint": f"python {tool_source_review_root() / 'captiocr' / 'CaptiOCR.py'}",
    }


def resolve_tesseract_runtime(
    *,
    explicit_cmd: str | Path | None = None,
    explicit_tessdata: str | Path | None = None,
    required_languages: str | list[str] | tuple[str, ...] | None = None,
) -> dict[str, Any]:
    """Find a usable Tesseract executable/tessdata pair for CaptiOCR reuse."""
    cmd_candidates = _tesseract_cmd_candidates(explicit_cmd)
    selected_cmd = next((path for path in cmd_candidates if path.exists()), None)
    tessdata_candidates = _tessdata_candidates(explicit_tessdata, selected_cmd)
    selected_tessdata = next(
        (path for path in tessdata_candidates if path.is_dir() and any(path.glob("*.traineddata"))),
        None,
    )
    installed_languages = (
        sorted(path.stem for path in selected_tessdata.glob("*.traineddata") if path.is_file())
        if selected_tessdata
        else []
    )
    requested_languages = _normalise_languages(required_languages)
    missing_languages = [language for language in requested_languages if language not in installed_languages]
    runtime_available = bool(selected_cmd and selected_tessdata)
    language_ready = runtime_available and not missing_languages
    if not runtime_available:
        status = "runtime_unavailable"
    elif not language_ready:
        status = "missing_language_packs"
    else:
        status = "ready"
    return {
        "available": bool(runtime_available and language_ready),
        "runtime_available": runtime_available,
        "status": status,
        "cmd": str(selected_cmd.resolve()) if selected_cmd else "",
        "tessdata_prefix": str(selected_tessdata.resolve()) if selected_tessdata else "",
        "installed_languages": installed_languages,
        "requested_languages": requested_languages,
        "missing_languages": missing_languages,
        "language_ready": language_ready,
        "checked_cmds": [str(path) for path in cmd_candidates],
        "checked_tessdata": [str(path) for path in tessdata_candidates],
        "configure_hint": f"Set {TESSERACT_ENV_VAR} and {TESSDATA_ENV_VAR} when Tesseract is not in PATH.",
    }


def _tesseract_cmd_candidates(explicit_cmd: str | Path | None = None) -> list[Path]:
    candidates: list[Path] = []
    if explicit_cmd:
        candidates.append(Path(explicit_cmd).expanduser())
    env_cmd = os.environ.get(TESSERACT_ENV_VAR, "").strip()
    if env_cmd:
        candidates.append(Path(env_cmd).expanduser())
    for command in ("tesseract", "tesseract.cmd", "tesseract.exe"):
        found = shutil.which(command)
        if found:
            candidates.append(Path(found))
    candidates.extend(
        [
            Path("C:/Program Files/Tesseract-OCR/tesseract.exe"),
            Path("C:/Program Files (x86)/Tesseract-OCR/tesseract.exe"),
        ]
    )
    return _unique_paths(candidates)


def _tessdata_candidates(
    explicit_tessdata: str | Path | None,
    selected_cmd: Path | None,
) -> list[Path]:
    candidates: list[Path] = []
    if explicit_tessdata:
        candidates.append(Path(explicit_tessdata).expanduser())
    env_tessdata = os.environ.get(TESSDATA_ENV_VAR, "").strip()
    if env_tessdata:
        candidates.append(Path(env_tessdata).expanduser())
    if selected_cmd:
        cmd = selected_cmd.expanduser()
        candidates.extend(
            [
                cmd.parent / "tessdata",
                cmd.parent.parent / "tessdata",
                cmd.parent.parent / "app" / "tesseract" / "tessdata",
            ]
        )
    candidates.extend(
        [
            Path("C:/Program Files/Tesseract-OCR/tessdata"),
            Path("C:/Program Files (x86)/Tesseract-OCR/tessdata"),
            workspace_root() / "tools",
        ]
    )
    return _unique_paths(candidates)


def _unique_paths(paths: list[Path]) -> list[Path]:
    seen: set[str] = set()
    unique: list[Path] = []
    for path in paths:
        key = str(path).lower()
        if key in seen:
            continue
        seen.add(key)
        unique.append(path)
    return unique


def _normalise_languages(value: str | list[str] | tuple[str, ...] | None) -> list[str]:
    raw: list[str] = []
    if isinstance(value, str):
        raw.extend(value.replace(",", "+").split("+"))
    elif isinstance(value, (list, tuple)):
        for item in value:
            raw.extend(str(item).replace(",", "+").split("+"))
    seen: set[str] = set()
    result: list[str] = []
    for item in raw:
        language = item.strip()
        if not language or language in seen:
            continue
        seen.add(language)
        result.append(language)
    return result
