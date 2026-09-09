from __future__ import annotations

from typing import Any

from .verification import ActiveLearningStore, EvidenceRegion, VerificationDesk, VerificationField


def create_verification_desk(document_id: str, fields: list[dict[str, Any]], gis: dict[str, Any] | None = None) -> dict[str, Any]:
    parsed: list[VerificationField] = []
    for field in fields:
        data = dict(field)
        evidence = [EvidenceRegion(**item) for item in data.pop("evidence", [])]
        parsed.append(VerificationField(**data, evidence=evidence))
    return VerificationDesk(document_id=document_id, fields=parsed, gis=gis or {}).to_dict()


def record_officer_decision(desk: VerificationDesk, decision: str, officer_id: str, comment: str = "") -> dict[str, Any]:
    return desk.decide(decision, officer_id, comment).__dict__


def record_correction(store: ActiveLearningStore, **kwargs: Any) -> dict[str, Any]:
    return store.record_correction(**kwargs).to_dict()


def export_training_dataset(store: ActiveLearningStore) -> list[dict[str, Any]]:
    return store.export_dataset()
