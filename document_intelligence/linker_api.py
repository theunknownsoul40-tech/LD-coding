from __future__ import annotations
from typing import Any, Iterable
from .record_linker import RecordCandidate, SmartRecordLinker

def link_records(source: RecordCandidate, candidates: Iterable[RecordCandidate], linker: SmartRecordLinker | None = None, limit: int = 10) -> dict[str, Any]:
    engine = linker or SmartRecordLinker()
    results = engine.rank(source, candidates, limit=limit)
    return {"source_record_id": source.record_id, "candidate_count": len(results), "calibration_note": "Thresholds and weights are starting points and must be calibrated on labeled jurisdiction-specific data.", "candidates": [r.to_dict() for r in results]}
