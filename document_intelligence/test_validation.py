from document_intelligence.change_radar import compare_records
from document_intelligence.validation import TemporalEvent, validate_business_record, validate_spatial, validate_temporal, SpatialRecord


def test_business_validation_passes_simple_record():
    result = validate_business_record({"area": 2.43, "survey_no": "125/2", "district": "Thane", "village": "Airoli", "tehsil": "Thane", "mutation_id": "M-1001", "owner": "Ramesh Kumar"})
    assert result.passed
    assert result.checks["area_positive"]
    assert result.checks["survey_number_valid"]


def test_business_validation_flags_invalid_share_and_area_change():
    result = validate_business_record({"area": 3.0, "survey_no": "125/2", "owner": "Ramesh", "district": "Thane"}, previous_area_hectare=2.0, ownership_share=0.5)
    assert result.checks["area_change_within_threshold"] is False


def test_spatial_area_discrepancy_is_not_fraud():
    result = validate_spatial(2.43, SpatialRecord(survey_no="125/2", area_hectare=2.41), area_tolerance_hectare=0.01, document_survey_no="125/2")
    assert not result.passed
    assert "discrepancy" in result.issues[0].message.lower()
    assert "fraud" not in result.issues[0].message.lower()


def test_temporal_subdivision_lineage():
    events = [
        TemporalEvent("1998-01-01", "grant", owner="Ramesh", survey_no="125/2", area_hectare=2.5),
        TemporalEvent("2016-01-01", "subdivision", owner="Ramesh", parent_surveys=["125/2"], child_surveys=["125/2A", "125/2B"], metadata={"child_area_total_hectare": 2.5}),
    ]
    result = validate_temporal(events)
    assert result.passed


def test_change_radar_keeps_history_and_classifies_changes():
    result = compare_records({"owner": "Ramesh", "area": 2.43, "mutation_id": "M1"}, {"owner": "Suresh", "area": 2.51, "mutation_id": "M2"})
    assert {c.field for c in result.changes} == {"owner", "area", "mutation_id"}
    assert all(action in result.to_dict()["actions"] for action in ["ACCEPT", "REJECT", "INVESTIGATE"])
