from document_intelligence.verification import ActiveLearningStore, EvidenceRegion, VerificationDesk, VerificationField


def test_officer_verification_records_decision_and_evidence():
    desk = VerificationDesk("LR-1842", fields=[VerificationField("Owner", "Ramesh", 0.83, evidence=[EvidenceRegion("LR-1842.pdf", 3, [100, 200, 420, 260], "B4")])], gis={"area_difference_hectare": 0.02})
    decision = desk.decide("INVESTIGATE", "officer-1", "Verify source and cadastral survey")
    assert decision.decision == "INVESTIGATE"
    assert desk.to_dict()["fields"][0]["evidence"][0]["bbox"] == [100, 200, 420, 260]


def test_officer_correction_becomes_training_data():
    desk = VerificationDesk("LR-1", fields=[VerificationField("Owner", "Ramesh", 0.71)])
    correction = desk.correct_field("Owner", "Ramesh Kumar", "officer-1")
    store = ActiveLearningStore()
    example = store.record_correction(task="owner_extraction", input_data={"document_id": "LR-1"}, predicted_value=correction["original_value"], verified_value=correction["corrected_value"], officer_id="officer-1")
    assert example.label == "corrected"
    assert store.stats()["corrected"] == 1


def test_training_adapter_requires_injected_runtime():
    from document_intelligence.verification import ModelTrainingAdapter
    adapter = ModelTrainingAdapter()
    try:
        adapter.train([])
    except RuntimeError as exc:
        assert "trainer configured" in str(exc)
    else:
        raise AssertionError("Expected missing trainer error")
