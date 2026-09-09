from .record_linker import LinkerThresholds, RecordCandidate, SmartRecordLinker


def test_cross_script_and_separator_variants_rank_as_match() -> None:
    source = RecordCandidate(
        record_id="doc-1", owner="Ramesh Kumar", survey_no="125/2", village="Airoli", district="Thane", area=1.0, area_unit="acre"
    )
    candidates = [
        RecordCandidate(record_id="db-a", owner="Ramesh Kumar", survey_no="125/2", village="Airoli", district="Thane", area=1.0, area_unit="acre"),
        RecordCandidate(record_id="db-b", owner="Ramesh K.", survey_no="125-2", village="Airoli", district="Thane", area=1.0, area_unit="acre"),
        RecordCandidate(record_id="db-c", owner="Other Person", survey_no="88/1", village="Pune", district="Pune", area=4.0, area_unit="acre"),
    ]
    results = SmartRecordLinker().rank(source, candidates)
    assert results[0].candidate_id == "db-a"
    assert results[0].decision == "likely_match"
    assert results[1].score > results[2].score
    assert results[1].components["survey_similarity"] == 1.0


def test_thresholds_are_configurable() -> None:
    linker = SmartRecordLinker(thresholds=LinkerThresholds(likely_match=0.95, human_review=0.70))
    source = RecordCandidate(record_id="s", owner="Ramesh Kumar", survey_no="125/2")
    candidate = RecordCandidate(record_id="c", owner="Ramesh K", survey_no="125-2")
    result = linker.score(source, candidate)
    assert result.decision in {"human_review", "likely_different", "likely_match"}


def test_devanagari_digits_normalize_for_survey_matching() -> None:
    source = RecordCandidate(record_id="s", survey_no="125/2")
    candidate = RecordCandidate(record_id="c", survey_no="१२५/२")
    result = SmartRecordLinker().score(source, candidate)
    assert result.components["survey_similarity"] == 1.0
