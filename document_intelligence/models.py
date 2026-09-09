from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Literal


@dataclass
class QualityAssessment:
    blur_score: float
    skew_angle: float
    noise_level: float
    width: int
    height: int
    dpi: int | None
    has_handwriting: bool = False
    quality: Literal["good", "fair", "poor"] = "fair"
    super_resolution_required: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class Provenance:
    page: int
    bbox: list[int] | None
    model: str
    confidence: float
    source_image: str
    value: str | None = None
    language: str | None = None
    script: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class LayoutRegion:
    region_type: str
    bbox: list[int]
    page: int
    confidence: float
    model: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ExtractedField:
    name: str
    value: str | float | int | None
    confidence: float
    provenance: Provenance

    def to_dict(self) -> dict[str, Any]:
        result = asdict(self)
        result["provenance"] = self.provenance.to_dict()
        return result


@dataclass
class NormalizedArea:
    original_value: float
    original_unit: str
    original_text: str
    standard_area: float | None
    standard_area_unit: str = "hectare"
    conversion_rule: str | None = None
    conversion_confidence: float = 1.0
    requires_review: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class DocumentResult:
    quality: QualityAssessment
    regions: list[LayoutRegion] = field(default_factory=list)
    fields: list[ExtractedField] = field(default_factory=list)
    normalized_area: NormalizedArea | None = None
    artifacts: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "quality": self.quality.to_dict(),
            "regions": [r.to_dict() for r in self.regions],
            "fields": [f.to_dict() for f in self.fields],
            "normalized_area": self.normalized_area.to_dict() if self.normalized_area else None,
            "artifacts": self.artifacts,
        }
