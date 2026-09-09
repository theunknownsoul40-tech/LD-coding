from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass
class DashboardMetrics:
    documents: int
    verified: int
    review_pending: int
    extraction_accuracy: float
    validation_passed_pct: float
    validation_review_pct: float
    validation_failed_pct: float
    geographic_progress: list[dict[str, Any]]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def build_dashboard_metrics(*, documents: int, verified: int, review_pending: int,
                             extraction_accuracy: float,
                             validation_passed: int, validation_review: int,
                             validation_failed: int,
                             geographic_progress: list[dict[str, Any]] | None = None) -> DashboardMetrics:
    total_validation = validation_passed + validation_review + validation_failed
    if total_validation <= 0:
        percentages = (0.0, 0.0, 0.0)
    else:
        percentages = tuple(round(value / total_validation * 100, 2) for value in (validation_passed, validation_review, validation_failed))
    return DashboardMetrics(
        documents=documents,
        verified=verified,
        review_pending=review_pending,
        extraction_accuracy=round(extraction_accuracy * 100 if extraction_accuracy <= 1 else extraction_accuracy, 2),
        validation_passed_pct=percentages[0],
        validation_review_pct=percentages[1],
        validation_failed_pct=percentages[2],
        geographic_progress=geographic_progress or [],
    )


def dashboard_payload(**kwargs: Any) -> dict[str, Any]:
    return build_dashboard_metrics(**kwargs).to_dict()
