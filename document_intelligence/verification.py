from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any
import uuid


@dataclass
class EvidenceRegion:
    document_id: str
    page: int
    bbox: list[int] | None = None
    region_id: str | None = None
    image_url: str | None = None


@dataclass
class VerificationField:
    name: str
    value: Any
    confidence: float
    status: str = "review"
    evidence: list[EvidenceRegion] = field(default_factory=list)
    validation: list[str] = field(default_factory=list)
    correction: Any = None


@dataclass
class OfficerDecision:
    decision: str
    officer_id: str
    timestamp: str
    comment: str = ""


@dataclass
class VerificationDesk:
    document_id: str
    fields: list[VerificationField] = field(default_factory=list)
    gis: dict[str, Any] = field(default_factory=dict)
    decisions: list[OfficerDecision] = field(default_factory=list)

    def decide(self, decision: str, officer_id: str, comment: str = "") -> OfficerDecision:
        normalized = decision.upper()
        if normalized not in {"APPROVE", "REJECT", "INVESTIGATE"}:
            raise ValueError("decision must be APPROVE, REJECT, or INVESTIGATE")
        item = OfficerDecision(normalized, officer_id, datetime.now(timezone.utc).isoformat(), comment)
        self.decisions.append(item)
        return item

    def correct_field(self, field_name: str, corrected_value: Any, officer_id: str) -> dict[str, Any]:
        for item in self.fields:
            if item.name == field_name:
                original = item.value
                item.correction = corrected_value
                item.status = "verified"
                return {"field": field_name, "original_value": original, "corrected_value": corrected_value, "officer_id": officer_id}
        raise KeyError(f"Unknown field: {field_name}")

    def to_dict(self) -> dict[str, Any]:
        return {
            "document_id": self.document_id,
            "fields": [asdict(f) for f in self.fields],
            "gis": self.gis,
            "decisions": [asdict(d) for d in self.decisions],
            "actions": ["APPROVE", "REJECT", "INVESTIGATE"],
        }


@dataclass
class TrainingExample:
    example_id: str
    task: str
    input_data: dict[str, Any]
    predicted_value: Any
    verified_value: Any
    label: str
    officer_id: str
    created_at: str
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class ActiveLearningStore:
    """Append-only verified corrections suitable for later model training."""

    def __init__(self) -> None:
        self.examples: list[TrainingExample] = []

    def record_correction(self, *, task: str, input_data: dict[str, Any], predicted_value: Any,
                          verified_value: Any, officer_id: str, metadata: dict[str, Any] | None = None) -> TrainingExample:
        label = "correct" if predicted_value == verified_value else "corrected"
        example = TrainingExample(
            example_id=str(uuid.uuid4()), task=task, input_data=input_data,
            predicted_value=predicted_value, verified_value=verified_value,
            label=label, officer_id=officer_id,
            created_at=datetime.now(timezone.utc).isoformat(), metadata=metadata or {},
        )
        self.examples.append(example)
        return example

    def export_dataset(self) -> list[dict[str, Any]]:
        return [example.to_dict() for example in self.examples]

    def stats(self) -> dict[str, int]:
        return {
            "total": len(self.examples),
            "correct": sum(e.label == "correct" for e in self.examples),
            "corrected": sum(e.label == "corrected" for e in self.examples),
        }


class ModelTrainingAdapter:
    """Optional PyTorch/MLflow/ONNX integration boundary.

    Dependencies stay optional so verification and data collection work without
    a heavyweight ML runtime. Concrete projects can inject a trainer/exporter.
    """

    def __init__(self, trainer: Any = None, mlflow_client: Any = None, onnx_exporter: Any = None) -> None:
        self.trainer = trainer
        self.mlflow_client = mlflow_client
        self.onnx_exporter = onnx_exporter

    def train(self, dataset: list[dict[str, Any]], **kwargs: Any) -> Any:
        if self.trainer is None:
            raise RuntimeError("No trainer configured. Inject a PyTorch-compatible trainer.")
        model = self.trainer.train(dataset, **kwargs)
        if self.mlflow_client is not None:
            self.mlflow_client.log_model(model, **kwargs)
        return model

    def export_onnx(self, model: Any, **kwargs: Any) -> Any:
        if self.onnx_exporter is None:
            raise RuntimeError("No ONNX exporter configured.")
        return self.onnx_exporter.export(model, **kwargs)
