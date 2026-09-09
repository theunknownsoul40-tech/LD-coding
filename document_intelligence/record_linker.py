from __future__ import annotations

from dataclasses import asdict, dataclass, field
from difflib import SequenceMatcher
import re
import unicodedata
from typing import Any, Iterable


@dataclass(frozen=True)
class LinkerWeights:
    name: float = 0.30
    survey: float = 0.25
    village: float = 0.15
    district: float = 0.10
    area: float = 0.10
    parcel_relationship: float = 0.10

    def normalized(self) -> "LinkerWeights":
        values = asdict(self)
        total = sum(values.values())
        if total <= 0:
            raise ValueError("At least one linker weight must be positive")
        return LinkerWeights(**{key: value / total for key, value in values.items()})


@dataclass(frozen=True)
class LinkerThresholds:
    """Starting points only; calibrate these on labeled records."""
    likely_match: float = 0.90
    human_review: float = 0.60

    def __post_init__(self) -> None:
        if not 0 <= self.human_review < self.likely_match <= 1:
            raise ValueError("Thresholds must satisfy 0 <= human_review < likely_match <= 1")


@dataclass
class RecordCandidate:
    record_id: str
    source: str | None = None
    owner: str | None = None
    survey_no: str | None = None
    village: str | None = None
    district: str | None = None
    area: float | None = None
    area_unit: str | None = None
    parcel_relationship: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class LinkScore:
    candidate_id: str
    score: float
    decision: str
    components: dict[str, float]
    explanation: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _normalize_text(value: str | None) -> str:
    if not value:
        return ""
    text = unicodedata.normalize("NFKC", str(value)).casefold()
    # Transliteration is intentionally injectable; normalization must not
    # invent a language mapping. Unicode digits are converted to ASCII.
    text = "".join(str(unicodedata.digit(ch)) if ch.isdigit() else ch for ch in text)
    text = re.sub(r"[^\w\s]", " ", text, flags=re.UNICODE)
    return re.sub(r"\s+", " ", text).strip()


def _survey_key(value: str | None) -> str:
    text = _normalize_text(value)
    # Treat common separators as formatting, not identity: 125/2 == 125-2.
    return re.sub(r"[\s/\\_.:-]+", "-", text).strip("-")


def _similarity(left: str | None, right: str | None) -> float:
    a, b = _normalize_text(left), _normalize_text(right)
    if not a or not b:
        return 0.0
    if a == b:
        return 1.0
    return SequenceMatcher(None, a, b).ratio()


def _survey_similarity(left: str | None, right: str | None) -> float:
    a, b = _survey_key(left), _survey_key(right)
    if not a or not b:
        return 0.0
    if a == b:
        return 1.0
    return SequenceMatcher(None, a, b).ratio()


def _area_similarity(left: RecordCandidate, right: RecordCandidate) -> float:
    if left.area is None or right.area is None:
        return 0.0
    if left.area_unit and right.area_unit and _normalize_text(left.area_unit) != _normalize_text(right.area_unit):
        return 0.0
    if left.area == right.area:
        return 1.0
    denominator = max(abs(left.area), abs(right.area), 1e-12)
    return max(0.0, 1.0 - abs(left.area - right.area) / denominator)


def _relationship_similarity(left: str | None, right: str | None) -> float:
    if not left or not right:
        return 0.0
    return _similarity(left, right)


class SmartRecordLinker:
    """Rank probable links across heterogeneous land-record sources.

    This deliberately avoids exact-record matching. Each score remains
    explainable so an officer can see why a candidate was ranked highly.
    """

    def __init__(self, weights: LinkerWeights | None = None, thresholds: LinkerThresholds | None = None):
        self.weights = (weights or LinkerWeights()).normalized()
        self.thresholds = thresholds or LinkerThresholds()

    def score(self, source: RecordCandidate, candidate: RecordCandidate) -> LinkScore:
        components = {
            "name_similarity": _similarity(source.owner, candidate.owner),
            "survey_similarity": _survey_similarity(source.survey_no, candidate.survey_no),
            "village_match": _similarity(source.village, candidate.village),
            "district_match": _similarity(source.district, candidate.district),
            "area_similarity": _area_similarity(source, candidate),
            "parcel_relationship": _relationship_similarity(source.parcel_relationship, candidate.parcel_relationship),
        }
        weighted = (
            components["name_similarity"] * self.weights.name
            + components["survey_similarity"] * self.weights.survey
            + components["village_match"] * self.weights.village
            + components["district_match"] * self.weights.district
            + components["area_similarity"] * self.weights.area
            + components["parcel_relationship"] * self.weights.parcel_relationship
        )
        score = round(weighted, 4)
        if score >= self.thresholds.likely_match:
            decision = "likely_match"
        elif score >= self.thresholds.human_review:
            decision = "human_review"
        else:
            decision = "likely_different"

        explanation = [
            f"name similarity={components['name_similarity']:.0%}",
            f"survey similarity={components['survey_similarity']:.0%}",
            f"village match={components['village_match']:.0%}",
            f"district match={components['district_match']:.0%}",
            f"area similarity={components['area_similarity']:.0%}",
            f"parcel relationship={components['parcel_relationship']:.0%}",
        ]
        return LinkScore(candidate.record_id, score, decision, components, explanation)

    def rank(self, source: RecordCandidate, candidates: Iterable[RecordCandidate], limit: int | None = None) -> list[LinkScore]:
        ranked = sorted((self.score(source, candidate) for candidate in candidates), key=lambda item: item.score, reverse=True)
        return ranked if limit is None else ranked[:limit]
