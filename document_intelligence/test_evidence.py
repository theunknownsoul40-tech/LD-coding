from .evidence import EvidenceGraph, evidence_from_extraction


def test_evidence_lifecycle_and_location() -> None:
    graph = EvidenceGraph()
    evidence = graph.add(
        evidence_from_extraction(
            field="owner",
            value="Ramesh Kumar",
            document_id="LR_1842",
            document_name="LR_1842.pdf",
            page=3,
            region_id="B4",
            bbox=[100, 200, 420, 260],
            ocr_confidence=0.96,
            ner_confidence=0.91,
            source_text="Ramesh Kumar",
            extraction_model="land-record-ner-v1",
        )
    )
    graph.validate(evidence.evidence_id, True)
    graph.verify(evidence.evidence_id, True)

    assert evidence.combined_confidence == 0.935
    assert evidence.location.page == 3
    assert evidence.location.region_id == "B4"
    assert evidence.validation == "PASS"
    assert evidence.human_verification == "APPROVED"
    assert graph.for_field("owner")[0].value == "Ramesh Kumar"


def test_evidence_search() -> None:
    graph = EvidenceGraph()
    graph.add(
        evidence_from_extraction(
            field="owner",
            value="Ramesh Kumar",
            document_id="LR_1842",
            document_name="LR_1842.pdf",
            page=3,
            region_id="B4",
            bbox=[0, 0, 10, 10],
        )
    )
    assert len(graph.search("Ramesh")) == 1
    assert len(graph.search("LR_1842.pdf")) == 1
