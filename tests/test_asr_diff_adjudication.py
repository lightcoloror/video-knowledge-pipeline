from __future__ import annotations

import json
from pathlib import Path

from video_knowledge_pipeline.asr_consensus import build_asr_consensus
from video_knowledge_pipeline.asr_diff_adjudication import (
    _positioned_differences,
    _tokens,
    apply_asr_diff_adjudication,
    build_asr_diff_adjudication,
)


def _bundle(tmp_path: Path) -> tuple[Path, Path, Path]:
    root = tmp_path / "bundle"
    root.mkdir()
    (root / "manifest.json").write_text(json.dumps({"title": "ASR diff fixture"}), encoding="utf-8")
    primary = root / "primary.json"
    secondary = root / "secondary.json"
    primary.write_text(
        json.dumps(
            {
                "segments": [
                    {"start": 0, "end": 10, "text": "使用 Playwright MCP 操作浏览器"},
                    {"start": 10, "end": 20, "text": "最后检查结果"},
                ]
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    secondary.write_text(
        json.dumps(
            {
                "segments": [
                    {"start": 0, "end": 10, "text": "使用 Playwright client 操作浏览器"},
                    {"start": 10, "end": 20, "text": "最后检查结果"},
                ]
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    build_asr_consensus(root, primary_transcript=primary, secondary_transcript=secondary, write=True)
    return root, primary, secondary


def test_build_asr_diff_adjudication_positions_clusters_and_anonymises(tmp_path: Path) -> None:
    root, _, _ = _bundle(tmp_path)

    result = build_asr_diff_adjudication(root, write=True)

    assert result["status"] == "ready_for_adjudication"
    assert result["difference_count"] >= 1
    assert result["cluster_count"] == 1
    diff = result["differences"][0]
    assert diff["primary_text"] == "MCP"
    assert diff["secondary_text"] == "client"
    assert diff["primary_char_start"] < diff["primary_char_end"]
    assert diff["estimated_time"]["start"] >= 0
    cluster = result["clusters"][0]
    assert {cluster["candidate_a"], cluster["candidate_b"]} == {"MCP", "client"}
    assert "primary" not in cluster
    assert (root / "asr-consensus-adjudication.todo.json").exists()


def test_apply_asr_diff_adjudication_only_applies_valid_local_patch(tmp_path: Path) -> None:
    root, _, _ = _bundle(tmp_path)
    pack = build_asr_diff_adjudication(root, write=True)
    diff = pack["differences"][0]
    choice = "A" if diff["candidate_a_text"] == "client" else "B"
    decisions = root / "decisions.json"
    decisions.write_text(
        json.dumps(
            {
                "rows": [
                    {
                        "diff_id": diff["diff_id"],
                        "choice": choice,
                        "confidence": 0.96,
                        "evidence_refs": ["asr-consensus-clips/asr-consensus-0000.wav"],
                        "reason": "local audio supports client",
                    }
                ]
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    result = apply_asr_diff_adjudication(root, decisions_json=decisions, write=True)

    assert result["summary"]["applied_patches"] == 1
    patched = json.loads((root / "asr-consensus-patched-transcript.json").read_text(encoding="utf-8"))
    assert patched["segments"][0]["text"] == "使用 Playwright client 操作浏览器"
    assert not (root / "source-arbitrated-transcript.json").exists()


def test_apply_asr_diff_adjudication_rejects_change_without_evidence(tmp_path: Path) -> None:
    root, _, _ = _bundle(tmp_path)
    pack = build_asr_diff_adjudication(root, write=True)
    diff = pack["differences"][0]
    choice = "A" if diff["candidate_a_text"] == "client" else "B"
    decisions = root / "decisions.json"
    decisions.write_text(
        json.dumps({"rows": [{"diff_id": diff["diff_id"], "choice": choice, "confidence": 0.99, "evidence_refs": []}]}),
        encoding="utf-8",
    )

    result = apply_asr_diff_adjudication(root, decisions_json=decisions, write=False)

    assert result["summary"]["applied_patches"] == 0
    assert result["rejected"][0]["reason"] == "evidence_required"

def test_diff_tokenizer_keeps_decimal_and_drops_whitespace() -> None:
    rows = _tokens("价格 100.5 元")

    assert [row["text"] for row in rows] == ["价", "格", "100.5", "元"]
    assert rows[2]["start"] == 3
    assert rows[2]["end"] == 8

def test_diff_adjudication_ignores_punctuation_only_changes() -> None:
    window = {
        "window_id": "punctuation-only",
        "primary_index": 0,
        "secondary_index": 0,
        "primary_start": 0,
        "primary_end": 1,
    }

    assert _positioned_differences(window, "你好。", "你好！") == []