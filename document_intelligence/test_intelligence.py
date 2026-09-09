from document_intelligence.intelligence import AnomalyRiskEngine, ExplainableField, OwnershipLineage, build_explainable_review


def test_ownership_lineage_reconstructs_chain():
    graph = OwnershipLineage()
    graph.add_node("person:ramesh", "PERSON", "Ramesh Kumar")
    graph.add_node("parcel:125-2", "PARCEL", "125/2")
    graph.add_node("tx:m1", "TRANSACTION", "Sale 2007")
    graph.add_node("mutation:m1", "MUTATION", "M-1")
    graph.add_node("parcel:125-2a", "PARCEL", "125/2A")
    graph.relate("person:ramesh", "OWNS", "parcel:125-2")
    graph.relate("parcel:125-2", "HAS_TRANSACTION", "tx:m1")
    graph.relate("tx:m1", "CREATES_MUTATION", "mutation:m1")
    graph.relate("parcel:125-2", "SUBDIVIDES_TO", "parcel:125-2a")
    chain = graph.ownership_chain("parcel:125-2")
    assert chain
    assert any(item.get("edge", {}).get("relationship") == "SUBDIVIDES_TO" for item in chain)


def test_risk_engine_is_not_a_fraud_verdict():
    assessment = AnomalyRiskEngine().assess(unresolved_previous_mutation=True, area_change_fraction=0.18, duplicate_ownership=True, record_conflict=True, incomplete_lineage=True)
    assert assessment.level == "high"
    assert "not a finding of fraud" in assessment.disclaimer
    assert len(assessment.findings) == 5


def test_explainable_review_contains_evidence_and_action():
    result = build_explainable_review([
        ExplainableField("Survey Number", 0.91, "pass", ["OCR confidence", "Format valid", "Parcel found"]),
        ExplainableField("Area", 0.68, "review", ["OCR confidence: 91%", "Reference match: 74%", "GIS difference: 0.02 ha"], [{"page": 3, "region": "B4"}]),
    ])
    assert result["review_required"]
    assert result["fields"][1]["recommended_action"]
