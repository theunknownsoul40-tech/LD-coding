from __future__ import annotations

from typing import Any

from .change_radar import compare_records
from .validation import SpatialRecord, TemporalEvent, validate_business_record, validate_spatial, validate_temporal


def validate_record(record: dict[str, Any], **kwargs: Any) -> dict[str, Any]:
    return validate_business_record(record, **kwargs).to_dict()


def validate_spatial_record(document_area_hectare: float | None, cadastral: dict[str, Any], **kwargs: Any) -> dict[str, Any]:
    spatial = SpatialRecord(
        survey_no=cadastral.get("survey_no"),
        area_hectare=cadastral.get("area_hectare"),
        geometry=cadastral.get("geometry"),
    )
    return validate_spatial(document_area_hectare, spatial, **kwargs).to_dict()


def validate_record_history(events: list[dict[str, Any]]) -> dict[str, Any]:
    parsed = [TemporalEvent(**event) for event in events]
    return validate_temporal(parsed).to_dict()


def detect_changes(old_record: dict[str, Any], new_record: dict[str, Any], **kwargs: Any) -> dict[str, Any]:
    return compare_records(old_record, new_record, **kwargs).to_dict()
