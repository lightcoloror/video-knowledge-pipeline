from __future__ import annotations

import json
from pathlib import Path

from video_knowledge_pipeline.shot_language_analysis import (
    SCHEMA,
    run_shot_language_analysis,
)


def _write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False), encoding="utf-8")


def _bundle(tmp_path: Path) -> Path:
    root = tmp_path / "bundle"
    frame_a = root / "frames" / "frame_01_0000000000ms.jpg"
    frame_b = root / "frames" / "frame_02_0000001000ms.jpg"
    frame_a.parent.mkdir(parents=True)
    frame_a.write_bytes(b"a")
    frame_b.write_bytes(b"b")
    _write_json(
        root / "manifest.json",
        {"schema": "lecture_webui_bundle.v1", "title": "fixture"},
    )
    _write_json(
        root / "timeline.json",
        [
            {
                "index": 1,
                "start": 0.0,
                "end": 2.0,
                "corrected_transcript": "spoken evidence",
                "visual_text": "screen evidence",
                "frame_paths": [str(frame_a), str(frame_b)],
                "temporal_visual_understanding": {
                    "event_sequence": ["subject raises a hand"]
                },
                "visual_understanding": {
                    "composition": {"rule_of_thirds": True},
                    "lighting": "soft",
                },
            }
        ],
    )
    _write_json(
        root / "exports" / "technical-shot-boundaries.json",
        {
            "schema": "video_knowledge_pipeline.technical_shot_boundaries.v1",
            "status": "completed",
            "ok": True,
            "backend": "autoshot",
            "boundary_kind": "technical_shot",
            "shots": [
                {
                    "shot_id": "technical-shot-0001",
                    "index": 1,
                    "start": 0.0,
                    "end": 2.0,
                }
            ],
        },
    )
    return root


def test_shot_facts_bind_each_non_unknown_field_to_evidence(
    tmp_path: Path,
) -> None:
    root = _bundle(tmp_path)

    result = run_shot_language_analysis(
        root,
        execute=True,
        write=False,
        route_id="local-qwen-vl",
        _shot_type_analyzer=lambda path: {
            "\u666f\u522b": "\u4e2d\u666f",
            "confidence": 0.91,
        },
        _movement_analyzer=lambda paths: {
            "\u955c\u5934\u8fd0\u52a8": "\u56fa\u5b9a\u955c\u5934",
            "confidence": 0.88,
        },
    )

    assert result["schema"] == SCHEMA
    assert result["status"] == "completed"
    fields = result["shots"][0]["fields"]
    assert fields["shot_type"]["value"] == "medium"
    assert fields["shot_type"]["status"] == "inferred"
    assert fields["camera_movement"]["value"] == "static"
    assert fields["dialogue_or_narration"]["status"] == "confirmed"
    assert fields["screen_text"]["status"] == "confirmed"
    for field in fields.values():
        if field["status"] != "unavailable":
            assert field["evidence_ids"]
    assert result["operator_boundary"]["no_remote_fallback"] is True
    assert result["operator_boundary"]["no_model_download"] is True


def test_low_confidence_stays_inferred_and_queues_explicit_local_vlm(
    tmp_path: Path,
) -> None:
    root = _bundle(tmp_path)

    result = run_shot_language_analysis(
        root,
        execute=True,
        write=False,
        route_id="local-qwen-vl",
        _shot_type_analyzer=lambda path: {
            "\u666f\u522b": "\u7279\u5199",
            "confidence": 0.2,
        },
        _movement_analyzer=lambda paths: {
            "\u955c\u5934\u8fd0\u52a8": "\u6447\u955c\u5934",
            "confidence": 0.3,
        },
    )

    fields = result["shots"][0]["fields"]
    assert fields["shot_type"]["status"] == "inferred"
    assert fields["shot_type"]["missing_evidence"]
    assert fields["camera_movement"]["status"] == "inferred"
    assert result["local_vlm_escalations"][0]["automatic_execution"] is False
    assert result["local_vlm_escalations"][0]["route_id"] == "local-qwen-vl"


def test_no_execute_never_claims_model_fields(tmp_path: Path) -> None:
    root = _bundle(tmp_path)

    result = run_shot_language_analysis(root, execute=False, write=False)

    fields = result["shots"][0]["fields"]
    assert fields["shot_type"]["status"] == "unavailable"
    assert fields["shot_type"]["value"] is None
    assert fields["camera_movement"]["status"] == "unavailable"
    assert result["runtime_errors"] == {}


def test_shot_facts_block_without_verified_technical_shots(
    tmp_path: Path,
) -> None:
    root = tmp_path / "bundle"
    root.mkdir()
    _write_json(root / "manifest.json", {"schema": "lecture_webui_bundle.v1"})
    _write_json(root / "timeline.json", [{"index": 1, "start": 0, "end": 5}])

    result = run_shot_language_analysis(root, execute=False, write=False)

    assert result["status"] == "blocked_missing_technical_shots"
    assert result["shot_count"] == 0
    assert result["operator_boundary"]["no_chapter_or_timeline_range_fallback"]
