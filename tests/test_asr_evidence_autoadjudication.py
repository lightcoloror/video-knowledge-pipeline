from __future__ import annotations

from pathlib import Path

from video_knowledge_pipeline.asr_evidence_autoadjudication import (
    _secondary_for_primary,
    adjudicate_asr_with_independent_evidence,
)
from video_knowledge_pipeline.storage import read_json, write_json


def _write_bundle(tmp_path: Path) -> tuple[Path, Path, Path]:
    bundle = tmp_path / "bundle"
    bundle.mkdir()
    write_json(bundle / "manifest.json", {"title": "ASR evidence"})
    write_json(
        bundle / "source-arbitrated-transcript.json",
        {
            "schema": "video_knowledge_pipeline.source_arbitrated_transcript.v1",
            "segments": [
                {"index": 0, "start": 0.0, "end": 10.0, "text": "属于市场的第一批兑的产品"},
                {"index": 1, "start": 10.0, "end": 20.0, "text": "保额大约是五十万"},
                {"index": 2, "start": 20.0, "end": 30.0, "text": "原始正确正文"},
            ],
        },
    )
    secondary = tmp_path / "secondary.json"
    write_json(
        secondary,
        {
            "segments": [
                {"primary_segment_id": "segment-000001", "start": 0.0, "end": 10.0, "text": "属于市场的第一梯队的产品"},
                {"primary_segment_id": "segment-000002", "start": 10.0, "end": 20.0, "text": "保额大约是六十万"},
                {"primary_segment_id": "segment-000003", "start": 20.0, "end": 30.0, "text": "原始正确正文"},
            ]
        },
    )
    corroborator = tmp_path / "corroborator.json"
    write_json(
        corroborator,
        {
            "segments": [
                {"start": 0.0, "end": 10.0, "text": "属于市场的第一梯队的产品"},
                {"start": 10.0, "end": 20.0, "text": "保额大约是六十万"},
                {"start": 20.0, "end": 30.0, "text": "原始正确正文"},
            ]
        },
    )
    return bundle, secondary, corroborator


def test_three_source_adjudication_applies_only_exact_non_fact_support(tmp_path: Path) -> None:
    bundle, secondary, corroborator = _write_bundle(tmp_path)

    result = adjudicate_asr_with_independent_evidence(
        bundle,
        secondary_transcript=secondary,
        corroborating_transcripts=[corroborator],
        write=True,
    )
    canonical = read_json(bundle / "source-arbitrated-transcript.json")
    manifest = read_json(bundle / "manifest.json")

    assert result["status"] == "degraded"
    assert result["applied_segment_count"] == 1
    assert canonical["segments"][0]["text"] == "属于市场的第一梯队的产品"
    assert canonical["segments"][0]["start"] == 0.0
    assert canonical["segments"][0]["end"] == 10.0
    assert canonical["segments"][1]["text"] == "保额大约是五十万"
    assert canonical["segments"][2]["text"] == "原始正确正文"
    assert result["operator_boundary"]["evaluation_reference_used"] is False
    assert result["operator_boundary"]['secondary_never_wholesale_promoted'] is True
    assert result["operator_boundary"]['semantic_closure_base_preserved'] is True
    assert manifest["transcript_semantic_correction_base_json"] == "asr-evidence-adjudicated-base.json"
    assert read_json(bundle / "asr-evidence-adjudicated-base.json")["segments"] == canonical["segments"]
    assert any(row["reason"] == "fact_or_number_change_requires_review" for row in result["unresolved"])


def test_three_source_adjudication_does_not_apply_when_primary_is_also_supported(
    tmp_path: Path,
) -> None:
    bundle, secondary, corroborator = _write_bundle(tmp_path)
    payload = read_json(corroborator)
    payload["segments"][0]["text"] = "属于市场的第一批兑的产品，也可能是属于市场的第一梯队的产品"
    write_json(corroborator, payload)

    result = adjudicate_asr_with_independent_evidence(
        bundle,
        secondary_transcript=secondary,
        corroborating_transcripts=[corroborator],
        write=False,
    )

    assert result["applied_segment_count"] == 0
    assert any(
        row["reason"] == "independent_evidence_also_supports_primary"
        for row in result["unresolved"]
    )


def test_three_source_adjudication_requires_a_corroborator(tmp_path: Path) -> None:
    bundle, secondary, _ = _write_bundle(tmp_path)

    try:
        adjudicate_asr_with_independent_evidence(
            bundle,
            secondary_transcript=secondary,
            corroborating_transcripts=[],
        )
    except ValueError as exc:
        assert "independent corroborating transcript" in str(exc)
    else:
        raise AssertionError("missing corroborator must be rejected")


def test_three_source_adjudication_rejects_insertions_even_when_corroborated(
    tmp_path: Path,
) -> None:
    bundle, secondary, corroborator = _write_bundle(tmp_path)
    secondary_payload = read_json(secondary)
    secondary_payload["segments"][2]["text"] = "原始很正确正文"
    write_json(secondary, secondary_payload)
    corroborator_payload = read_json(corroborator)
    corroborator_payload["segments"][2]["text"] = "原始很正确正文"
    write_json(corroborator, corroborator_payload)

    result = adjudicate_asr_with_independent_evidence(
        bundle,
        secondary_transcript=secondary,
        corroborating_transcripts=[corroborator],
        write=False,
    )

    assert result["applied_segment_count"] == 1
    assert any(
        row["reason"] == "structural_delta_outside_targeted_recovery_bounds"
        for row in result["unresolved"]
    )

def test_three_source_adjudication_recovers_exact_short_gap(tmp_path: Path) -> None:
    bundle, secondary, corroborator = _write_bundle(tmp_path)
    secondary_payload = read_json(secondary)
    secondary_payload["segments"][2]["text"] = "原始非常正确正文"
    write_json(secondary, secondary_payload)
    corroborator_payload = read_json(corroborator)
    corroborator_payload["segments"][2]["text"] = "原始非常正确正文"
    write_json(corroborator, corroborator_payload)

    result = adjudicate_asr_with_independent_evidence(
        bundle,
        secondary_transcript=secondary,
        corroborating_transcripts=[corroborator],
        write=False,
    )

    recovered = next(
        row for row in result["applied"]
        if row["canonical_segment_position"] == 2
    )
    assert recovered["replacement_text"] == "原始非常正确正文"
    assert recovered["patches"][0]["support_rule"] == (
        "short_gap_exact_in_independent_aligned_asr"
    )

def test_three_source_adjudication_rejects_short_boundary_repetition(tmp_path: Path) -> None:
    bundle, secondary, corroborator = _write_bundle(tmp_path)
    secondary_payload = read_json(secondary)
    secondary_payload["segments"][2]["text"] = "原始正确正确正文"
    write_json(secondary, secondary_payload)
    corroborator_payload = read_json(corroborator)
    corroborator_payload["segments"][2]["text"] = "原始正确正确正文"
    write_json(corroborator, corroborator_payload)

    result = adjudicate_asr_with_independent_evidence(
        bundle,
        secondary_transcript=secondary,
        corroborating_transcripts=[corroborator],
        write=False,
    )

    assert not any(
        row["canonical_segment_position"] == 2 for row in result["applied"]
    )
    assert any(
        row["reason"] == "low_information_boundary_repetition_requires_review"
        for row in result["unresolved"]
    )


def test_three_source_adjudication_recovers_bounded_long_gap(tmp_path: Path) -> None:
    bundle, secondary, corroborator = _write_bundle(tmp_path)
    secondary_payload = read_json(secondary)
    secondary_payload["segments"][2]["text"] = "原始需要补回的重要内容正确正文"
    write_json(secondary, secondary_payload)
    corroborator_payload = read_json(corroborator)
    corroborator_payload["segments"][2]["text"] = "原始需要补回的确实重要内容正确正文"
    write_json(corroborator, corroborator_payload)

    result = adjudicate_asr_with_independent_evidence(
        bundle,
        secondary_transcript=secondary,
        corroborating_transcripts=[corroborator],
        write=False,
    )

    recovered = next(
        row for row in result["applied"]
        if row["canonical_segment_position"] == 2
    )
    assert recovered["replacement_text"] == "原始需要补回的重要内容正确正文"
    assert recovered["patches"][0]["support_rule"] == (
        "long_gap_near_subsequence_in_independent_aligned_asr"
    )

def test_three_source_adjudication_recovers_expanded_boundary_gap(tmp_path: Path) -> None:
    bundle, secondary, corroborator = _write_bundle(tmp_path)
    canonical = read_json(bundle / "source-arbitrated-transcript.json")
    canonical["segments"][2]["text"] = "前文余地方后文"
    write_json(bundle / "source-arbitrated-transcript.json", canonical)
    secondary_payload = read_json(secondary)
    secondary_payload["segments"][2]["text"] = "前文余地可以做调整后文"
    write_json(secondary, secondary_payload)
    corroborator_payload = read_json(corroborator)
    corroborator_payload["segments"][2]["text"] = "余地可以做二次调整"
    write_json(corroborator, corroborator_payload)

    result = adjudicate_asr_with_independent_evidence(
        bundle,
        secondary_transcript=secondary,
        corroborating_transcripts=[corroborator],
        write=False,
    )

    recovered = next(
        row for row in result["applied"]
        if row["canonical_segment_position"] == 2
    )
    assert recovered["replacement_text"] == "前文余地可以做调整后文"
    assert recovered["patches"][0]["support_rule"] == (
        "expanded_gap_near_subsequence_in_independent_aligned_asr"
    )

def test_partial_secondary_does_not_match_missing_empty_identity() -> None:
    primary = {"start": 0.0, "end": 5.0, "text": "第一段"}
    partial_secondary = [
        {"start": 25.0, "end": 40.0, "text": "远处片段"},
    ]

    assert _secondary_for_primary(primary, 0, partial_secondary) is None
