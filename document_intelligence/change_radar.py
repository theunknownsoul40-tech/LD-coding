from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class FieldChange:
    field: str
    change_type: str
    old_value: Any = None
    new_value: Any = None
    confidence: float = 1.0
    reason: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ChangeRadarResult:
    changes: list[FieldChange] = field(default_factory=list)
    decision: str | None = None
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "changes": [c.to_dict() for c in self.changes],
            "decision": self.decision,
            "notes": self.notes,
            "actions": ["ACCEPT", "REJECT", "INVESTIGATE"],
        }

    def set_decision(self, decision: str) -> None:
        decision = decision.upper()
        if decision not in {"ACCEPT", "REJECT", "INVESTIGATE"}:
            raise ValueError("decision must be ACCEPT, REJECT, or INVESTIGATE")
        self.decision = decision


def compare_records(
    old_record: dict[str, Any],
    new_record: dict[str, Any],
    *,
    tracked_fields: list[str] | None = None,
    area_tolerance: float = 1e-9,
) -> ChangeRadarResult:
    """Compare versions without overwriting the historical record."""
    fields = tracked_fields or [
        "owner",
        "survey_no",
        "area",
        "area_unit",
        "mutation_id",
        "village",
        "tehsil",
        "district",
        "land_class",
    ]
    changes: list[FieldChange] = []

    for name in fields:
        old = old_record.get(name)
        new = new_record.get(name)
        if isinstance(old, dict):
            old = old.get("value")
        if isinstance(new, dict):
            new = new.get("value")
        if old == new:
            continue

        change_type = "CHANGED"
        if old in (None, "") and new not in (None, ""):
            change_type = "NEW"
        elif new in (None, "") and old not in (None, ""):
            change_type = "POSSIBLY_OBSOLETE"
        elif name == "area":
            try:
                if abs(float(old) - float(new)) <= area_tolerance:
                    continue
            except (TypeError, ValueError):
                pass

        changes.append(FieldChange(name, change_type, old, new))

    notes = []
    if any(c.field == "survey_no" for c in changes):
        notes.append("Survey relationship changed; review parcel lineage.")
    if any(c.field == "mutation_id" and c.change_type == "POSSIBLY_OBSOLETE" for c in changes):
        notes.append("Previous mutation is no longer present in the new version; verify history.")
    if any(c.field == "owner" for c in changes):
        notes.append("Owner name changed; reconcile against mutation/transfer history.")

    return ChangeRadarResult(changes=changes, notes=notes)
