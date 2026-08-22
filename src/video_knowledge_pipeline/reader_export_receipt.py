from __future__ import annotations

from pathlib import Path
from typing import Any

from .file_hash import sha256_file
from .models import now_iso


READER_EXPORT_RECEIPT_SCHEMA = "video_knowledge_pipeline.reader_export_receipt.v2"


def build_reader_export_receipt(
    *,
    canonical_transcript: Path | None,
    full_transcript: Path,
    full_body: Path,
    reading_note: Path,
) -> dict[str, Any]:
    return {
        "schema": READER_EXPORT_RECEIPT_SCHEMA,
        "created_at": now_iso(),
        "canonical_transcript_path": str(canonical_transcript) if canonical_transcript else "",
        "canonical_transcript_sha256": sha256_file(canonical_transcript) if canonical_transcript and canonical_transcript.is_file() else "",
        "full_transcript_path": str(full_transcript),
        "full_transcript_sha256": sha256_file(full_transcript) if full_transcript.is_file() else "",
        "full_body_path": str(full_body),
        "full_body_sha256": sha256_file(full_body) if full_body.is_file() else "",
        "reading_note_path": str(reading_note),
        "reading_note_sha256": sha256_file(reading_note) if reading_note.is_file() else "",
    }


def receipt_matches_reader_files(
    receipt: dict[str, Any],
    *,
    canonical_transcript: Path,
    full_transcript: Path,
    full_body: Path,
    reading_note: Path,
) -> bool:
    if not isinstance(receipt, dict):
        return False
    if receipt.get("schema") != READER_EXPORT_RECEIPT_SCHEMA:
        return False
    if str(receipt.get("canonical_transcript_sha256") or "") != sha256_file(canonical_transcript):
        return False
    if str(receipt.get("full_transcript_sha256") or "") != sha256_file(full_transcript):
        return False
    if str(receipt.get("full_body_sha256") or "") != sha256_file(full_body):
        return False
    return str(receipt.get("reading_note_sha256") or "") == sha256_file(reading_note)
