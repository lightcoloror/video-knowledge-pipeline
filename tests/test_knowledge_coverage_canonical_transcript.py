from __future__ import annotations

import json
import os
from pathlib import Path

from video_knowledge_pipeline.knowledge_coverage import build_knowledge_coverage


def test_coverage_reuses_fresh_canonical_transcript_alignment(tmp_path: Path) -> None:
    timeline = [
        {"index": 1, "start": 0.0, "end": 4.0, "transcript": ""},
        {"index": 2, "start": 4.0, "end": 8.0, "transcript": ""},
    ]
    timeline_path = tmp_path / "timeline.json"
    timeline_path.write_text(json.dumps(timeline), encoding="utf-8")
    audit_path = tmp_path / "timeline-alignment-audit.json"
    audit_path.write_text(
        json.dumps(
            {
                "summary": {
                    "items": 2,
                    "transcript_available": True,
                    "missing_asr_overlap": 0,
                },
                "items": [
                    {"index": 1, "asr_overlap_count": 1, "issues": []},
                    {"index": 2, "asr_overlap_count": 2, "issues": []},
                ],
            }
        ),
        encoding="utf-8",
    )
    newer = timeline_path.stat().st_mtime_ns + 1_000_000
    os.utime(audit_path, ns=(newer, newer))

    report = build_knowledge_coverage({}, timeline, bundle_dir=tmp_path)

    speech = next(row for row in report["channels"] if row["key"] == "speech")
    assert speech["covered_count"] == 2
    assert speech["coverage_percent"] == 100.0
    assert report["canonical_transcript_aligned_items"] == 2
    assert report["samples"]["missing_transcript"] == []


def test_coverage_rejects_stale_canonical_alignment(tmp_path: Path) -> None:
    timeline = [{"index": 1, "start": 0.0, "end": 4.0, "transcript": ""}]
    audit_path = tmp_path / "timeline-alignment-audit.json"
    audit_path.write_text(
        json.dumps(
            {
                "summary": {"items": 1, "transcript_available": True},
                "items": [{"index": 1, "asr_overlap_count": 1, "issues": []}],
            }
        ),
        encoding="utf-8",
    )
    timeline_path = tmp_path / "timeline.json"
    timeline_path.write_text(json.dumps(timeline), encoding="utf-8")
    newer = audit_path.stat().st_mtime_ns + 1_000_000
    os.utime(timeline_path, ns=(newer, newer))

    report = build_knowledge_coverage({}, timeline, bundle_dir=tmp_path)

    speech = next(row for row in report["channels"] if row["key"] == "speech")
    assert speech["covered_count"] == 0
    assert report["canonical_transcript_aligned_items"] == 0
