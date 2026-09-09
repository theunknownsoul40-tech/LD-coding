from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import date, datetime
import re
from typing import Any


@dataclass
class ValidationIssue:
    rule: str
    severity: str
    message: str
    field: str | None = None
    evidence: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ValidationResult:
    passed: bool
    issues: list[ValidationIssue] = field(default_factory=list)
    checks: dict[str, bool] = field(default_factory=dict)

    @property
    def status(self) -> str:
        return "PASS" if self.passed else "POTENTIAL_DISCREPANCY_REQUIRING_VERIFICATION"

    def to_dict(self) -> dict[str, Any]:
        return {
            "passed": self.passed,
            "status": self.status,
            "checks": self.checks,
            "issues": [issue.to_dict() for issue in self.issues],
        }


@dataclass
class SpatialRecord:
    survey_no: str | None = None
    area_hectare: float | None = None
    geometry: Any = None


@dataclass
class TemporalEvent:
    event_date: str | date | datetime
    event_type: str
    owner: str | None = None
    survey_no: str | None = None
    area_hectare: float | None = None
    mutation_id: str | None = None
    parent_surveys: list[str] = field(default_factory=list)
    child_surveys: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


def _parse_date(value: str | date | datetime) -> datetime:
    if isinstance(value, datetime):
        return value
    if isinstance(value, date):
        return datetime.combine(value, datetime.min.time())
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _field(record: dict[str, Any], name: str) -> Any:
    value = record.get(name)
    if isinstance(value, dict):
        return value.get("value")
    return value


def _valid_survey(value: Any) -> bool:
    if value is None:
        return False
    text = str(value).strip()
    return bool(re.fullmatch(r"[\d\u0966-\u096F]+(?:\s*[/\\-]\s*[A-Za-z\d\u0966-\u096F]+)+|[A-Za-z]?\d+[A-Za-z]?(?:[/\\-][A-Za-z\d]+)*", text))


def _valid_mutation(value: Any) -> bool:
    if value in (None, ""):
        return False
    return bool(re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9./_-]{1,63}", str(value).strip()))


def validate_business_record(
    record: dict[str, Any],
    *,
    district_exists: bool = True,
    village_to_tehsil: dict[str, str] | None = None,
    duplicate_survey_numbers: set[str] | None = None,
    duplicate_mutation_ids: set[str] | None = None,
    max_area_change_fraction: float = 0.20,
    previous_area_hectare: float | None = None,
) -> ValidationResult:
    issues: list[ValidationIssue] = []
    checks: dict[str, bool] = {}

    area = _field(record, "area")
    try:
        area_ok = float(area) > 0
    except (TypeError, ValueError):
        area_ok = False
    checks["area_positive"] = area_ok
    if not area_ok:
        issues.append(ValidationIssue("area_positive", "error", "Area must be greater than zero.", "area"))

    survey = _field(record, "survey_no")
    survey_ok = _valid_survey(survey)
    checks["survey_number_valid"] = survey_ok
    if not survey_ok:
        issues.append(ValidationIssue("survey_number_valid", "error", "Survey number format is invalid.", "survey_no"))

    checks["district_exists"] = district_exists
    if not district_exists:
        issues.append(ValidationIssue("district_exists", "error", "District could not be resolved.", "district"))

    village = _field(record, "village")
    tehsil = _field(record, "tehsil")
    relationship_ok = True
    if village_to_tehsil is not None and village is not None:
        relationship_ok = village_to_tehsil.get(str(village).casefold()) == str(tehsil).casefold()
    checks["village_belongs_to_tehsil"] = relationship_ok
    if not relationship_ok:
        issues.append(ValidationIssue("village_belongs_to_tehsil", "error", "Village does not belong to the supplied tehsil.", "village"))

    mutation = _field(record, "mutation_id")
    mutation_ok = _valid_mutation(mutation)
    checks["mutation_id_format_valid"] = mutation_ok
    if mutation not in (None, "") and not mutation_ok:
        issues.append(ValidationIssue("mutation_id_format_valid", "error", "Mutation ID format is invalid.", "mutation_id"))

    owner_ok = bool(str(_field(record, "owner") or "").strip())
    checks["owner_present"] = owner_ok
    if not owner_ok:
        issues.append(ValidationIssue("owner_present", "error", "Owner field is missing.", "owner"))

    survey_key = str(survey).strip().casefold() if survey is not None else ""
    if duplicate_survey_numbers and survey_key in {str(x).casefold() for x in duplicate_survey_numbers}:
        checks["duplicate_survey_number"] = False
        issues.append(ValidationIssue("duplicate_survey_number", "warning", "Duplicate survey number detected; verify parcel identity.", "survey_no"))
    else:
        checks["duplicate_survey_number"] = True

    mutation_key = str(mutation).strip().casefold() if mutation not in (None, "") else ""
    if mutation_key and duplicate_mutation_ids and mutation_key in {str(x).casefold() for x in duplicate_mutation_ids}:
        checks["duplicate_mutation"] = False
        issues.append(ValidationIssue("duplicate_mutation", "warning", "Duplicate mutation ID detected; verify transaction history.", "mutation_id"))
    else:
        checks["duplicate_mutation"] = True

    share = _field(record, "ownership_share")
    share_ok = True
    if share is not None:
        try:
            share_ok = 0 < float(share) <= 1
        except (TypeError, ValueError):
            share_ok = False
    checks["ownership_share_valid"] = share_ok
    if not share_ok:
        issues.append(ValidationIssue("ownership_share_valid", "warning", "Ownership share must be between 0 and 1.", "ownership_share"))

    change_ok = True
    if previous_area_hectare is not None and previous_area_hectare > 0 and area_ok:
        change_fraction = abs(float(area) - previous_area_hectare) / previous_area_hectare
        change_ok = change_fraction <= max_area_change_fraction
        if not change_ok:
            issues.append(ValidationIssue("area_change_threshold", "warning", "Area change exceeds the configured verification threshold.", "area", {"change_fraction": change_fraction, "threshold": max_area_change_fraction}))
    checks["area_change_within_threshold"] = change_ok

    return ValidationResult(not any(i.severity == "error" for i in issues), issues, checks)


def validate_spatial(
    document_area_hectare: float | None,
    cadastral: SpatialRecord,
    *,
    area_tolerance_hectare: float = 0.02,
    geometry_validator: Any = None,
    document_survey_no: str | None = None,
) -> ValidationResult:
    """Validate document-vs-cadastral geometry.

    `geometry_validator` is an optional PostGIS adapter. It should return a dict
    containing overlap, gap, sliver, split, merge, geometry_valid and optionally
    matched_survey_no. No PostGIS dependency is required for unit testing.
    """
    issues: list[ValidationIssue] = []
    checks: dict[str, bool] = {}

    if document_area_hectare is not None and cadastral.area_hectare is not None:
        difference = abs(document_area_hectare - cadastral.area_hectare)
        checks["area_within_tolerance"] = difference <= area_tolerance_hectare
        if difference > area_tolerance_hectare:
            issues.append(ValidationIssue("area_difference", "warning", "Potential discrepancy requiring verification: document and cadastral areas differ.", "area", {"document_area_hectare": document_area_hectare, "cadastral_area_hectare": cadastral.area_hectare, "difference_hectare": difference, "tolerance_hectare": area_tolerance_hectare}))
    else:
        checks["area_within_tolerance"] = True

    if document_survey_no and cadastral.survey_no:
        checks["survey_number_matched"] = str(document_survey_no).casefold() == str(cadastral.survey_no).casefold()
        if not checks["survey_number_matched"]:
            issues.append(ValidationIssue("survey_number_mismatch", "warning", "Survey number differs between document and cadastral data.", "survey_no"))
    else:
        checks["survey_number_matched"] = True

    if geometry_validator is not None:
        result = geometry_validator(cadastral.geometry)
        for key in ("overlap", "gap", "sliver", "split", "merge", "geometry_valid"):
            if key in result:
                checks[key] = bool(result[key])
        if result.get("geometry_valid") is False:
            issues.append(ValidationIssue("geometry_valid", "warning", "Cadastral geometry is invalid and requires verification."))
        if result.get("gap"):
            issues.append(ValidationIssue("polygon_gap", "warning", "Potential polygon gap detected; manual verification required."))
        if result.get("sliver"):
            issues.append(ValidationIssue("boundary_sliver", "warning", "Potential boundary sliver detected; manual verification required."))
        if result.get("split"):
            issues.append(ValidationIssue("parcel_split", "info", "Potential parcel split detected."))
        if result.get("merge"):
            issues.append(ValidationIssue("parcel_merge", "info", "Potential parcel merge detected."))
        if result.get("overlap"):
            issues.append(ValidationIssue("polygon_overlap", "warning", "Potential polygon overlap detected; manual verification required."))

    return ValidationResult(True, issues, checks)


def validate_temporal(events: list[TemporalEvent]) -> ValidationResult:
    """Check whether land-record events form a plausible historical chain."""
    issues: list[ValidationIssue] = []
    checks = {"chronological": True, "subdivision_consistent": True, "ownership_transition_explained": True}
    ordered = sorted(events, key=lambda e: _parse_date(e.event_date))

    for previous, current in zip(ordered, ordered[1:]):
        if _parse_date(current.event_date) < _parse_date(previous.event_date):
            checks["chronological"] = False

        if current.event_type.casefold() == "subdivision":
            if previous.survey_no and current.parent_surveys and previous.survey_no not in current.parent_surveys:
                checks["subdivision_consistent"] = False
                issues.append(ValidationIssue("impossible_subdivision", "warning", "Subdivision does not reference the preceding parent parcel; verification required.", "survey_no", {"previous_survey": previous.survey_no, "parent_surveys": current.parent_surveys}))
            if current.parent_surveys and current.child_surveys:
                parent_area = previous.area_hectare
                child_total = current.metadata.get("child_area_total_hectare")
                if parent_area is not None and child_total is not None and abs(parent_area - float(child_total)) > max(0.01, parent_area * 0.02):
                    checks["subdivision_consistent"] = False
                    issues.append(ValidationIssue("subdivision_area_balance", "warning", "Subdivision child areas do not reconcile with the parent area."))

        if current.owner and previous.owner and current.owner.casefold() != previous.owner.casefold() and current.event_type.casefold() not in {"mutation", "sale", "inheritance", "transfer", "gift", "court_order"}:
            checks["ownership_transition_explained"] = False
            issues.append(ValidationIssue("ownership_transition", "warning", "Owner changed without a recognized transfer event; verification required.", "owner"))

    passed = all(checks.values())
    return ValidationResult(passed, issues, checks)
