from document_intelligence.dashboard import build_dashboard_metrics
from document_intelligence.integration import GovernmentApiGateway


def test_mock_government_sync_never_requires_real_database():
    gateway = GovernmentApiGateway()
    results = gateway.queue_sync({"record_id": "LR-1", "status": "VERIFIED"})
    assert {item.target for item in results} == {"LRMS", "DILRMP", "GIS"}
    assert all(item.status == "MOCK_ACCEPTED" for item in results)
    assert all(item.response["remote_id"].startswith("MOCK-") for item in results)


def test_dashboard_metrics_match_requested_structure():
    metrics = build_dashboard_metrics(documents=128420, verified=104231, review_pending=24189, extraction_accuracy=0.942, validation_passed=82, validation_review=14, validation_failed=4, geographic_progress=[{"state": "Maharashtra", "progress_pct": 78}])
    payload = metrics.to_dict()
    assert payload["documents"] == 128420
    assert payload["verified"] == 104231
    assert payload["review_pending"] == 24189
    assert payload["extraction_accuracy"] == 94.2
    assert payload["validation_passed_pct"] == 82.0
    assert payload["validation_review_pct"] == 14.0
    assert payload["validation_failed_pct"] == 4.0
