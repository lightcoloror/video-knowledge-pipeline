from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest


@pytest.mark.skipif(sys.platform != "win32", reason="PowerShell wrapper is Windows-only")
def test_video_knowledge_wrapper_propagates_cli_failure() -> None:
    powershell = shutil.which("powershell")
    if not powershell:
        pytest.skip("Windows PowerShell is unavailable")
    repo = Path(__file__).resolve().parents[1]
    env = dict(os.environ)
    env["VKP_MODEL_CONNECTOR_ALLOWED_DESTINATIONS"] = "test.invalid"

    completed = subprocess.run(
        [
            powershell,
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(repo / "scripts" / "video-knowledge.ps1"),
            "definitely-not-a-vkp-command",
        ],
        cwd=repo,
        capture_output=True,
        text=True,
        env=env,
        timeout=180,
        check=False,
    )

    assert completed.returncode != 0
