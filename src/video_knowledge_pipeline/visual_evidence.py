from __future__ import annotations

from typing import Any, Iterable


ACCEPTED_REVIEW_STATUSES = frozenset(
    {
        "accepted",
        "reviewed",
        "keep_image",
        "accepted_known_gap",
        "accepted_no_visual_content",
        "accepted_provider_blocked",
        "corrected_visual_text",
        "corrected_visual_understanding",
        "corrected_temporal_visual_understanding",
    }
)

VISUAL_CONTENT_FIELDS = (
    "objects",
    "actions",
    "interface_state",
    "spatial_relations",
    "non_text_information",
    "instructor_focus",
)
TEMPORAL_CONTENT_FIELDS = (
    "event_sequence",
    "state_changes",
    "operation_steps",
    "causal_links",
)


def visual_evidence_state(item: dict[str, Any]) -> dict[str, Any]:
    return _evidence_state(
        item,
        machine_key="visual_understanding",
        corrected_key="human_corrected_visual_understanding",
        review_corrected_key="corrected_visual_understanding",
        content_fields=VISUAL_CONTENT_FIELDS,
    )


def temporal_evidence_state(item: dict[str, Any]) -> dict[str, Any]:
    return _evidence_state(
        item,
        machine_key="temporal_visual_understanding",
        corrected_key="human_corrected_temporal_visual_understanding",
        review_corrected_key="corrected_temporal_visual_understanding",
        content_fields=TEMPORAL_CONTENT_FIELDS,
    )


def has_visual_evidence(item: dict[str, Any], *, include_human_review: bool = True) -> bool:
    state = visual_evidence_state(item)
    return bool(state["consumable"] if include_human_review else state["model_complete"])


def has_temporal_evidence(item: dict[str, Any], *, include_human_review: bool = True) -> bool:
    state = temporal_evidence_state(item)
    return bool(state["consumable"] if include_human_review else state["model_complete"])


def visual_understanding_value(item: dict[str, Any]) -> dict[str, Any]:
    value = visual_evidence_state(item).get("understanding")
    return dict(value) if isinstance(value, dict) else {}


def temporal_understanding_value(item: dict[str, Any]) -> dict[str, Any]:
    value = temporal_evidence_state(item).get("understanding")
    return dict(value) if isinstance(value, dict) else {}


def evidence_index_sets(timeline: Iterable[dict[str, Any]]) -> dict[str, list[int]]:
    visual_model: list[int] = []
    visual_consumable: list[int] = []
    temporal_model: list[int] = []
    temporal_consumable: list[int] = []
    for position, item in enumerate(timeline, start=1):
        if not isinstance(item, dict):
            continue
        index = _positive_int(item.get("index")) or position
        visual = visual_evidence_state(item)
        temporal = temporal_evidence_state(item)
        if visual["model_complete"]:
            visual_model.append(index)
        if visual["consumable"]:
            visual_consumable.append(index)
        if temporal["model_complete"]:
            temporal_model.append(index)
        if temporal["consumable"]:
            temporal_consumable.append(index)
    return {
        "visual_model_complete": visual_model,
        "visual_export_consumable": visual_consumable,
        "temporal_model_complete": temporal_model,
        "temporal_export_consumable": temporal_consumable,
    }


def human_review_accepted(item: dict[str, Any]) -> bool:
    review = _human_review(item)
    status = str(item.get("review_status") or review.get("status") or "").strip().lower()
    return status in ACCEPTED_REVIEW_STATUSES


def _evidence_state(
    item: dict[str, Any],
    *,
    machine_key: str,
    corrected_key: str,
    review_corrected_key: str,
    content_fields: tuple[str, ...],
) -> dict[str, Any]:
    review = _human_review(item)
    candidates = (
        ("human_corrected", item.get(corrected_key)),
        ("human_review_corrected", review.get(review_corrected_key)),
        ("model", item.get(machine_key)),
    )
    selected: dict[str, Any] = {}
    source = "missing"
    for candidate_source, value in candidates:
        if _valid_understanding(value, item=item, content_fields=content_fields):
            selected = dict(value)
            source = candidate_source
            break
    model_complete = bool(selected)
    review_accepted = human_review_accepted(item)
    return {
        "model_complete": model_complete,
        "human_review_accepted": review_accepted,
        "consumable": model_complete or review_accepted,
        "source": source if model_complete else ("human_review_status" if review_accepted else "missing"),
        "understanding": selected,
    }


def _valid_understanding(
    value: Any,
    *,
    item: dict[str, Any],
    content_fields: tuple[str, ...],
) -> bool:
    if not isinstance(value, dict) or not value:
        return False
    if value.get("parse_failed") is True:
        return False
    if str(value.get("validation_status") or "").strip().lower() in {
        "blocked",
        "failed",
        "incomplete",
        "invalid",
    }:
        return False
    if not any(_non_empty(value.get(field)) for field in content_fields):
        return False
    return bool(_as_list(value.get("evidence_frame_paths"))) or _item_has_frame_evidence(item)


def _item_has_frame_evidence(item: dict[str, Any]) -> bool:
    for key in ("assets", "evidence_frame_paths", "temporal_frame_paths"):
        values = item.get(key)
        rows = values if isinstance(values, list) else [values]
        for row in rows:
            if isinstance(row, dict):
                if _non_empty(row.get("path")) or _non_empty(row.get("source_path")):
                    return True
            elif _non_empty(row):
                return True
    integrated = item.get("integrated_visual")
    if isinstance(integrated, dict):
        return bool(_as_list(integrated.get("evidence_frame_paths")))
    return False


def _human_review(item: dict[str, Any]) -> dict[str, Any]:
    value = item.get("human_review")
    return value if isinstance(value, dict) else {}


def _as_list(value: Any) -> list[Any]:
    if isinstance(value, list):
        return [item for item in value if _non_empty(item)]
    if _non_empty(value):
        return [value]
    return []


def _non_empty(value: Any) -> bool:
    return value not in (None, "", [], {})


def _positive_int(value: Any) -> int:
    try:
        number = int(value or 0)
    except (TypeError, ValueError):
        return 0
    return number if number > 0 else 0
