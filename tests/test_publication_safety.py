from __future__ import annotations

import subprocess
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
LOCAL_WINDOWS_USERNAME = "light" + "color"
PERSONAL_PATH_MARKERS = (
    f"c:\\users\\{LOCAL_WINDOWS_USERNAME}",
    f"d:\\users\\{LOCAL_WINDOWS_USERNAME}",
    "d:\\used-by-codex",
    "d:/used-by-codex",
    "d:\\mediagodownloads",
    "d:/mediagodownloads",
    "d:\\localllm",
    "d:/localllm",
    "e:\\vkp-datasets",
    "e:/vkp-datasets",
)
LOCAL_ONLY_UNTRACKED_FILES = {
    "cell",
    "docs/plans/2026-07-23-parallel-validation-and-batch-closure.md",
    "docs/plans/2026-07-24-current-parallel-validation-matrix.md",
    "docs/plans/2026-07-30-vkp-production-closure.md",
}


def _tracked_files() -> list[str]:
    result = subprocess.run(
        ["git", "-c", "core.quotepath=false", "ls-files", "-z"],
        cwd=REPOSITORY_ROOT,
        check=True,
        capture_output=True,
    )
    return [item.decode("utf-8") for item in result.stdout.split(b"\0") if item]


def test_tracked_snapshot_does_not_expose_personal_absolute_paths() -> None:
    findings: list[str] = []
    for relative_path in _tracked_files():
        if relative_path == "tests/test_publication_safety.py":
            continue
        path = REPOSITORY_ROOT / relative_path
        if not path.is_file():
            continue
        try:
            text = path.read_text(encoding="utf-8").casefold()
        except UnicodeDecodeError:
            continue
        for marker in PERSONAL_PATH_MARKERS:
            if marker in text:
                findings.append(f"{relative_path}: {marker}")

    assert findings == []


def test_known_local_only_files_are_not_tracked() -> None:
    tracked = set(_tracked_files())
    assert tracked.isdisjoint(LOCAL_ONLY_UNTRACKED_FILES)


def test_secrets_credentials_and_runtime_outputs_are_not_tracked() -> None:
    blocked_paths: list[str] = []
    for relative_path in _tracked_files():
        normalized = relative_path.replace("\\", "/").casefold()
        name = Path(normalized).name
        if (
            normalized.startswith((".local/", "openclaw-runs/", "outputs/"))
            or "/secrets/" in f"/{normalized}"
            or "/credentials/" in f"/{normalized}"
            or name == ".env"
            or (name.startswith(".env.") and name != ".env.example")
            or name.endswith((".pem", ".key", ".pfx", ".p12", ".credential.xml"))
        ):
            blocked_paths.append(relative_path)

    assert blocked_paths == []
