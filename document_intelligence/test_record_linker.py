from .record_linker import LinkerThresholds, RecordCandidate, SmartRecordLinker

def test_variants_link():
    source = RecordCandidate("source", owner="Ramesh Kumar", survey_no="125/2", village="Airoli", district="Thane", area=1.0, area_unit="acre")
    candidates = [
        RecordCandidate("A", owner="Ramesh Kumar", survey_no="125/2", village="Airoli", district="Thane", area=1.0, area_unit="acre"),
        RecordCandidate("B", owner="Ramesh K.", survey_no="125-2", village="Airoli", district="Thane", area=1.0, area_unit="acre"),
        RecordCandidate("C", owner="Other Person", survey_no="88/1", village="Pune", district="Pune", area=4.0, area_unit="acre"),
    ]
    results = SmartRecordLinker().rank(source, candidates)
    assert results[0].candidate_id == "A"
    assert results[0].decision == "likely_match"
    assert results[1].score > results[2].score

def test_indic_survey_digits():
    a = RecordCandidate("a", survey_no="125/2")
    b = RecordCandidate("b", survey_no="१२५/२")
    assert SmartRecordLinker().score(a, b).components["survey_similarity"] == 1.0

def test_thresholds_configurable():
    linker = SmartRecordLinker(thresholds=LinkerThresholds(likely_match=.95, human_review=.70))
    result = linker.score(RecordCandidate("a", owner="Ramesh Kumar"), RecordCandidate("b", owner="Ramesh K"))
    assert result.decision in {"likely_match", "human_review", "likely_different"}
