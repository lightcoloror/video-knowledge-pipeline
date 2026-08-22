from __future__ import annotations

import json
from pathlib import Path

from video_knowledge_pipeline.general_tagger_adapter import run_general_tagger
from video_knowledge_pipeline.temporal_tag_delta import (
    analyze_temporal_tag_observations,
    run_temporal_tag_delta,
)


def _observation(position: int, tags: list[str], *, ocr_text: str = "") -> dict:
    return {
        "frame_position": position,
        "frame_path": f"frame-{position}.jpg",
        "tags": tags,
        "ocr_text": ocr_text,
    }


def test_tag_delta_smooths_single_frame_gap_and_flicker() -> None:
    result = analyze_temporal_tag_observations(
        [
            _observation(1, ["讲师", "白板"]),
            _observation(2, ["讲师", "临时噪声"]),
            _observation(3, ["讲师", "白板"]),
        ]
    )

    assert result["status"] == "completed"
    assert result["decision"] == "coarse_static_summary"
    assert result["smoothed_observations"][1]["tags"] == ["白板", "讲师"]
    assert result["stable_tags"] == ["白板", "讲师"]
    assert result["transitions"] == []
    assert "不据此" not in result["coarse_summary"]
    assert result["limitations"]


def test_tag_delta_escalates_dynamic_or_cross_channel_change() -> None:
    result = analyze_temporal_tag_observations(
        [
            _observation(1, ["桌面", "窗口"], ocr_text="首页"),
            _observation(2, ["菜单", "鼠标"], ocr_text="设置"),
            _observation(3, ["对话框", "按钮"], ocr_text="确认"),
        ],
        transcript="接下来点击按钮，切换到设置页。",
        supporting_signals={
            "ocr_changed": True,
            "scene_boundary": False,
            "frame_change_status": "dynamic",
        },
    )

    assert result["decision"] == "temporal_multimodal"
    assert "high_tag_change" in result["escalation_reasons"]
    assert "ocr_changed" in result["escalation_reasons"]
    assert "asr_dynamic_term" in result["escalation_reasons"]
    assert "需升级连续帧多模态理解" in result["coarse_summary"]


def test_temporal_tag_delta_import_updates_only_supporting_fields(tmp_path: Path) -> None:
    bundle = tmp_path / "bundle"
    bundle.mkdir()
    (bundle / "manifest.json").write_text(json.dumps({"title": "synthetic"}), encoding="utf-8")
    timeline = [
        {
            "index": 1,
            "start": 0,
            "end": 3,
            "transcript": "讲师站在白板前。",
            "temporal_frame_paths": ["f1.jpg", "f2.jpg", "f3.jpg"],
        }
    ]
    (bundle / "timeline.json").write_text(json.dumps(timeline, ensure_ascii=False), encoding="utf-8")
    input_path = bundle / "tag-input.json"
    input_path.write_text(
        json.dumps(
            {
                "schema": "video_knowledge_pipeline.temporal_tag_delta_input.v1",
                "items": [
                    {
                        "index": 1,
                        "frames": [
                            _observation(1, ["讲师", "白板"]),
                            _observation(2, ["讲师", "白板"]),
                            _observation(3, ["讲师", "白板"]),
                        ],
                    }
                ],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    result = run_temporal_tag_delta(bundle, input_json=input_path)
    updated = json.loads((bundle / "timeline.json").read_text(encoding="utf-8"))[0]

    assert result["status"] == "completed"
    assert result["coarse_static_count"] == 1
    assert updated["temporal_tag_delta"]["decision"] == "coarse_static_summary"
    assert updated["temporal_multimodal_escalation"]["required"] is False
    assert "temporal_visual_understanding" not in updated
    assert (bundle / "temporal-tag-delta.json").is_file()
    assert (bundle / "temporal-tag-delta.md").is_file()


def test_general_tagger_continuous_mode_tags_every_ordered_frame(tmp_path: Path) -> None:
    bundle = tmp_path / "bundle"
    bundle.mkdir()
    frame_paths = []
    for position in range(1, 4):
        path = bundle / f"frame-{position}.jpg"
        path.write_bytes(f"synthetic-{position}".encode())
        frame_paths.append(path.name)
    (bundle / "timeline.json").write_text(
        json.dumps(
            [
                {
                    "index": 7,
                    "start": 0,
                    "end": 3,
                    "temporal_frame_paths": frame_paths,
                }
            ]
        ),
        encoding="utf-8",
    )

    result = run_general_tagger(
        bundle,
        frame_mode="continuous",
        execute=True,
        import_annotations=False,
        write=False,
        _inference_backend=lambda path: {"tags_zh": [path.stem], "tags_en": []},
    )

    assert result["status"] == "completed"
    assert result["planned_frame_count"] == 3
    assert [row["frame_position"] for row in result["annotations"]] == [1, 2, 3]
    assert [row["frame_id"] for row in result["annotations"]] == [
        "frame-001",
        "frame-002",
        "frame-003",
    ]
