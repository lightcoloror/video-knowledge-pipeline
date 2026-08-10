from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

from video_knowledge_pipeline import funasr_python_runner
from video_knowledge_pipeline.speaker_global_alignment import (
    PRIVATE_ALIGNMENT_SCHEMA,
    align_chunk_speaker_records,
    bind_local_voiceprint_role,
    delete_local_voiceprint,
    enroll_local_voiceprints,
    match_local_voiceprints,
    write_alignment_artifacts,
)
from video_knowledge_pipeline.transcript_speakers import cue_speaker


def _records() -> list[dict[str, object]]:
    return [
        {
            "chunk_index": 0,
            "record_index": 0,
            "_speaker_embedding_centers": [
                {"local_speaker_id": "0", "center": [1.0, 0.0]},
                {"local_speaker_id": "1", "center": [0.0, 1.0]},
            ],
            "sentence_info": [
                {"start": 0, "end": 1000, "text": "甲", "spk": 0},
                {"start": 2000, "end": 3000, "text": "乙", "spk": 1},
            ],
        },
        {
            "chunk_index": 1,
            "record_index": 0,
            "_speaker_embedding_centers": [
                {"local_speaker_id": "0", "center": [0.01, 0.99]},
                {"local_speaker_id": "1", "center": [0.99, 0.01]},
            ],
            "sentence_info": [
                {"start": 4000, "end": 5000, "text": "乙", "spk": 0},
                {"start": 6000, "end": 7000, "text": "甲", "spk": 1},
            ],
        },
    ]


def test_chunk_local_labels_are_mapped_to_stable_anonymous_ids() -> None:
    mapped, public, private = align_chunk_speaker_records(_records())

    assert public["status"] == "candidate"
    assert public["chunk_local_speaker_count"] == 4
    assert public["global_speaker_count"] == 2
    assert public["mapped_sentence_count"] == 4
    assert mapped[0]["sentence_info"][0]["speaker_global_id"] == "speaker-global-001"
    assert mapped[1]["sentence_info"][1]["speaker_global_id"] == "speaker-global-001"
    assert mapped[0]["sentence_info"][1]["speaker_global_id"] == "speaker-global-002"
    assert mapped[1]["sentence_info"][0]["speaker_global_id"] == "speaker-global-002"
    assert mapped[0]["sentence_info"][0]["spk"] == 0
    assert private["biometric_data"] is True
    assert len(private["global_centers"]) == 2
    assert "global_centers" not in public


def test_two_active_clusters_cannot_collapse_to_one_global_id() -> None:
    records = _records()[:1]
    records.append(
        {
            "chunk_index": 1,
            "record_index": 0,
            "_speaker_embedding_centers": [
                {"local_speaker_id": "0", "center": [1.0, 0.01]},
                {"local_speaker_id": "1", "center": [0.99, 0.02]},
            ],
            "sentence_info": [
                {"start": 4000, "end": 5000, "text": "甲", "spk": 0},
                {"start": 6000, "end": 7000, "text": "丙", "spk": 1},
            ],
        }
    )

    mapped, public, _private = align_chunk_speaker_records(records)
    global_ids = {
        row["speaker_global_id"] for row in mapped[1]["sentence_info"]
    }

    assert len(global_ids) == 2
    assert public["global_speaker_count"] >= 2


def test_missing_centers_fail_closed_without_relabeling() -> None:
    records = [
        {
            "chunk_index": 0,
            "record_index": 0,
            "sentence_info": [
                {"start": 0, "end": 1000, "text": "甲", "spk": 0}
            ],
        }
    ]

    mapped, public, private = align_chunk_speaker_records(records)

    assert public["status"] == "unavailable"
    assert public["missing_center_chunk_indexes"] == [0]
    assert "speaker_global_id" not in mapped[0]["sentence_info"][0]
    assert private["global_centers"] == []


def test_public_artifact_excludes_embeddings_and_double_run_is_stable(
    tmp_path: Path,
) -> None:
    mapped_a, public_a, private_a = align_chunk_speaker_records(_records())
    mapped_b, public_b, private_b = align_chunk_speaker_records(_records())
    public_a.pop("updated_at")
    public_b.pop("updated_at")
    private_a.pop("updated_at")
    private_b.pop("updated_at")

    assert mapped_a == mapped_b
    assert public_a == public_b
    assert private_a == private_b

    result = write_alignment_artifacts(
        tmp_path / "raw-asr-output.json", public_a, private_a, write=True
    )
    public_path = Path(result["artifacts"]["public_path"])
    private_path = Path(result["artifacts"]["private_path"])
    public_text = public_path.read_text(encoding="utf-8")
    private_payload = json.loads(private_path.read_text(encoding="utf-8"))

    assert '"center"' not in public_text
    assert private_payload["schema"] == PRIVATE_ALIGNMENT_SCHEMA
    assert private_payload["must_remain_local"] is True


def test_voiceprint_registry_is_explicit_local_candidate_only_and_deletable(
    tmp_path: Path,
) -> None:
    _mapped, public, private = align_chunk_speaker_records(_records())
    artifacts = write_alignment_artifacts(
        tmp_path / "first.json", public, private, write=True
    )
    private_path = artifacts["artifacts"]["private_path"]
    registry = tmp_path / "voiceprints.private.json"

    blocked = enroll_local_voiceprints(
        private_path,
        registry,
        source_id="video-a",
        confirm_local_biometric_storage=False,
    )
    assert blocked["status"] == "blocked"
    assert not registry.exists()

    first = enroll_local_voiceprints(
        private_path,
        registry,
        source_id="video-a",
        confirm_local_biometric_storage=True,
    )
    repeated = enroll_local_voiceprints(
        private_path,
        registry,
        source_id="video-a",
        confirm_local_biometric_storage=True,
    )
    self_match = match_local_voiceprints(private_path, registry)
    second_private = dict(private)
    second_private["source_revision"] = "second-video-revision"
    second_private_path = tmp_path / "second-speaker-global-alignment.private.json"
    second_private_path.write_text(
        json.dumps(second_private, ensure_ascii=False), encoding="utf-8"
    )
    matched = match_local_voiceprints(second_private_path, registry)

    assert first["added_count"] == 2
    assert repeated["added_count"] == 0
    assert all(row["status"] == "no_match" for row in self_match["matches"])
    assert all(row["status"] == "suspected_same_speaker" for row in matched["matches"])
    assert all(row["identity_confirmed"] is False for row in matched["matches"])
    assert "center" not in json.dumps(matched)

    voiceprint_id = json.loads(registry.read_text(encoding="utf-8"))["entries"][0][
        "voiceprint_id"
    ]
    blocked_role = bind_local_voiceprint_role(
        registry,
        voiceprint_id,
        "采访者",
        confirm_role_binding=False,
    )
    bound_role = bind_local_voiceprint_role(
        registry,
        voiceprint_id,
        "采访者",
        confirm_role_binding=True,
    )
    assert blocked_role["status"] == "blocked"
    assert bound_role["status"] == "role_bound"
    assert json.loads(registry.read_text(encoding="utf-8"))["entries"][0][
        "role_status"
    ] == "human_confirmed"
    blocked_delete = delete_local_voiceprint(
        registry, voiceprint_id, confirm_delete=False
    )
    deleted = delete_local_voiceprint(registry, voiceprint_id, confirm_delete=True)
    assert blocked_delete["status"] == "blocked"
    assert deleted["status"] == "deleted"
    assert deleted["deleted_count"] == 1


def test_downstream_reader_prefers_global_anonymous_id() -> None:
    cue = {
        "spk": 4,
        "speaker_local_cluster": "4",
        "speaker_global_id": "speaker-global-002",
    }

    assert cue_speaker(cue) == "speaker-global-002"


def test_funasr_runner_requests_and_serializes_only_speaker_centers(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    media = tmp_path / "dialogue.wav"
    output = tmp_path / "raw.json"
    media.write_bytes(b"audio")
    captured: dict[str, object] = {}

    class ArrayLike:
        def tolist(self) -> list[list[float]]:
            return [[1.0, 0.0], [0.0, 1.0]]

    class FakeAutoModel:
        def __init__(self, **_kwargs: object) -> None:
            pass

        def generate(self, **kwargs: object) -> list[dict[str, object]]:
            captured.update(kwargs)
            return [
                {
                    "text": "甲乙",
                    "spk_embedding_center": ArrayLike(),
                    "sentence_info": [
                        {"start": 0, "end": 500, "text": "甲", "spk": 0},
                        {"start": 500, "end": 1000, "text": "乙", "spk": 1},
                    ],
                }
            ]

    monkeypatch.setitem(
        sys.modules,
        "funasr",
        type("FakeFunASR", (), {"AutoModel": FakeAutoModel}),
    )
    monkeypatch.setattr(funasr_python_runner, "_select_device", lambda _value: "cpu")

    result = funasr_python_runner.run_funasr(
        input_path=str(media),
        output_path=str(output),
        provider="sensevoice",
        model="iic/SenseVoiceSmall",
        spk_model="cam++",
        device="cpu",
    )
    payload = json.loads(output.read_text(encoding="utf-8"))

    assert result["ok"] is True
    assert captured["return_spk_center"] is True
    assert "spk_embedding_center" not in json.dumps(payload)
    assert payload["result"][0]["_speaker_embedding_centers"] == [
        {"local_speaker_id": "0", "center": [1.0, 0.0]},
        {"local_speaker_id": "1", "center": [0.0, 1.0]},
    ]
    assert payload["speaker_embedding_evidence"]["biometric_data"] is True
