from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class LineageNode:
    node_id: str
    node_type: str
    label: str
    properties: dict[str, Any] = field(default_factory=dict)


@dataclass
class LineageEdge:
    source: str
    relationship: str
    target: str
    properties: dict[str, Any] = field(default_factory=dict)


class OwnershipLineage:
    """Version-aware ownership graph for people, parcels and transactions."""

    def __init__(self) -> None:
        self.nodes: dict[str, LineageNode] = {}
        self.edges: list[LineageEdge] = []

    def add_node(self, node_id: str, node_type: str, label: str, **properties: Any) -> LineageNode:
        node = LineageNode(node_id, node_type, label, properties)
        self.nodes[node_id] = node
        return node

    def relate(self, source: str, relationship: str, target: str, **properties: Any) -> LineageEdge:
        if source not in self.nodes or target not in self.nodes:
            raise KeyError("Both source and target nodes must exist")
        edge = LineageEdge(source, relationship, target, properties)
        self.edges.append(edge)
        return edge

    def ownership_chain(self, parcel_id: str) -> list[dict[str, Any]]:
        """Return a deterministic graph walk relevant to a parcel."""
        if parcel_id not in self.nodes:
            return []
        visited: set[str] = set()
        result: list[dict[str, Any]] = []
        frontier = [parcel_id]
        while frontier:
            node_id = frontier.pop(0)
            if node_id in visited:
                continue
            visited.add(node_id)
            node = self.nodes[node_id]
            result.append({"node": asdict(node)})
            for edge in self.edges:
                if edge.source == node_id and edge.target not in visited:
                    result.append({"edge": asdict(edge)})
                    frontier.append(edge.target)
                elif edge.target == node_id and edge.source not in visited:
                    result.append({"edge": asdict(edge)})
                    frontier.append(edge.source)
        return result

    def to_dict(self) -> dict[str, Any]:
        return {"nodes": [asdict(n) for n in self.nodes.values()], "edges": [asdict(e) for e in self.edges]}


@dataclass
class RiskFinding:
    rule: str
    score: float
    reason: str
    evidence: dict[str, Any] = field(default_factory=dict)


@dataclass
class RiskAssessment:
    risk_score: float
    level: str
    findings: list[RiskFinding]
    model: str
    disclaimer: str = "Risk score indicates verification priority; it is not a finding of fraud."

    def to_dict(self) -> dict[str, Any]:
        return {
            "risk_score": self.risk_score,
            "level": self.level,
            "findings": [asdict(f) for f in self.findings],
            "model": self.model,
            "disclaimer": self.disclaimer,
        }


class AnomalyRiskEngine:
    """Explainable rule engine with optional Isolation Forest adapter."""

    def __init__(self, *, isolation_forest: Any = None, weights: dict[str, float] | None = None) -> None:
        self.isolation_forest = isolation_forest
        self.weights = weights or {
            "unresolved_previous_mutation": 0.22,
            "area_change": 0.18,
            "duplicate_ownership": 0.20,
            "record_conflict": 0.22,
            "incomplete_lineage": 0.18,
        }

    def assess(self, *, unresolved_previous_mutation: bool = False, area_change_fraction: float = 0.0,
               duplicate_ownership: bool = False, record_conflict: bool = False,
               incomplete_lineage: bool = False, feature_vector: Any = None) -> RiskAssessment:
        findings: list[RiskFinding] = []
        score = 0.0

        if unresolved_previous_mutation:
            score += self.weights["unresolved_previous_mutation"]
            findings.append(RiskFinding("unresolved_previous_mutation", self.weights["unresolved_previous_mutation"], "Previous owner mutation remains unresolved."))
        if area_change_fraction > 0:
            contribution = min(1.0, area_change_fraction / 0.20) * self.weights["area_change"]
            score += contribution
            findings.append(RiskFinding("area_change", contribution, f"Area changed by {area_change_fraction:.1%}.", {"change_fraction": area_change_fraction}))
        if duplicate_ownership:
            score += self.weights["duplicate_ownership"]
            findings.append(RiskFinding("duplicate_ownership", self.weights["duplicate_ownership"], "Duplicate ownership reference detected."))
        if record_conflict:
            score += self.weights["record_conflict"]
            findings.append(RiskFinding("record_conflict", self.weights["record_conflict"], "Registration/RoR or source-record conflict detected."))
        if incomplete_lineage:
            score += self.weights["incomplete_lineage"]
            findings.append(RiskFinding("incomplete_lineage", self.weights["incomplete_lineage"], "Historical ownership chain is incomplete."))

        model = "deterministic_rules"
        if self.isolation_forest is not None and feature_vector is not None:
            try:
                prediction = float(-self.isolation_forest.decision_function([feature_vector])[0])
                anomaly_component = max(0.0, min(1.0, (prediction + 0.5)))
                score = min(1.0, 0.75 * score + 0.25 * anomaly_component)
                model = "rules+isolation_forest"
            except Exception:
                model = "deterministic_rules"

        score = round(min(1.0, max(0.0, score)), 4)
        level = "high" if score >= 0.70 else "medium" if score >= 0.40 else "low"
        return RiskAssessment(score, level, findings, model)


@dataclass
class ExplainableField:
    field: str
    confidence: float
    status: str
    factors: list[str] = field(default_factory=list)
    evidence: list[dict[str, Any]] = field(default_factory=list)
    recommended_action: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def build_explainable_review(fields: list[ExplainableField], *, default_action: str = "Verify original document and latest cadastral survey.") -> dict[str, Any]:
    """Build the officer-facing explanation without hiding evidence behind one score."""
    review_required = any(f.status.casefold() in {"review", "warning", "discrepancy"} for f in fields)
    for item in fields:
        if item.recommended_action is None and item.status.casefold() in {"review", "warning", "discrepancy"}:
            item.recommended_action = default_action
    return {
        "title": "Review Required" if review_required else "Validation Passed",
        "review_required": review_required,
        "fields": [f.to_dict() for f in fields],
        "recommended_action": default_action if review_required else "No additional action required.",
    }
