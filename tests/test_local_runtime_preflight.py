from __future__ import annotations

import json
from pathlib import Path

import video_knowledge_pipeline.local_tool_inventory as inventory


def test_local_runtime_preflight_reports_windows_venv_media_and_dependencies(tmp_path: Path, monkeypatch) -> None:
    project = tmp_path / "project"
    project.mkdir()
    (project / "pyproject.toml").write_text(
        """
[project]
name = "video-knowledge-pipeline"
requires-python = ">=3.11"
dependencies = ["jieba>=0.42", "jsonschema>=4", "markdown-it-py>=3", "rapidfuzz>=3"]
""".strip(),
        encoding="utf-8",
    )
    venv = project / ".venv"
    python = venv / "Scripts" / "python.exe"
    python.parent.mkdir(parents=True)
    python.write_bytes(b"")
    (venv / "pyvenv.cfg").write_text("home = C:\\Python311\n", encoding="utf-8")

    monkeypatch.setattr(inventory.sys, "executable", str(python))
    monkeypatch.setattr(inventory.sys, "prefix", str(venv))
    monkeypatch.setattr(inventory.sys, "base_prefix", str(project / "Python311"))
    monkeypatch.setattr(inventory, "resolve_media_tool", lambda name: "" if name == "ffmpeg" else str(project / "ffprobe.exe"))
    monkeypatch.setattr(inventory, "resolve_tesseract", lambda: "")
    monkeypatch.setattr(inventory.shutil, "which", lambda name: str(project / "uv.exe") if name == "uv" else None)
    monkeypatch.setattr(
        inventory.importlib.util,
        "find_spec",
        lambda name: object() if name in {"jsonschema", "markdown_it", "rapidfuzz"} else None,
    )

    result = inventory.local_runtime_preflight(project)

    assert result["schema"] == "video_knowledge_pipeline.local_runtime_preflight.v1"
    assert result["ok"] is False
    assert result["runtime"]["python"]["executable"] == str(python.resolve())
    assert result["runtime"]["python"]["absolute"] is True
    assert result["runtime"]["venv"]["active"] is True
    assert result["runtime"]["venv"]["pyvenv_cfg_exists"] is True
    assert result["runtime"]["uv"]["available"] is True
    assert result["capabilities"]["media"]["ffmpeg"]["available"] is False
    assert result["capabilities"]["media"]["ffprobe"]["available"] is True
    assert "jieba" in result["capabilities"]["dependencies"]["missing"]
    rendered = json.dumps(result["recovery_commands"], ensure_ascii=False)
    assert "lightcolor" not in rendered.lower()
    assert "used-by-codex" not in rendered.lower()
    assert result["boundaries"]["installs_dependencies"] is False
    assert result["boundaries"]["starts_service"] is False


def test_cli_registers_local_runtime_preflight() -> None:
    cli_path = Path(inventory.__file__).with_name("cli.py")
    source = cli_path.read_text(encoding="utf-8")

    assert 'args.command == "local-runtime-preflight"' in source
    assert 'sub.add_parser("local-runtime-preflight"' in source
