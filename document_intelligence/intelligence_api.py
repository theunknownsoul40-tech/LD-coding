from __future__ import annotations

from typing import Any

from .intelligence import AnomalyRiskEngine, ExplainableField, OwnershipLineage, build_explainable_review


def create_lineage(nodes: list[dict[str, Any]], relationships: list[dict[str, Any]]) -> dict[str, Any]:
    graph = OwnershipLineage()
    for node in nodes:
        node = dict(node)
        node_id = node.pop("node_id")
        node_type = node.pop("node_type")
        label = node.pop("label", node_id)
        graph.add_node(node_id, node_type, label, **node)
    for edge in relationships:
        edge = dict(edge)
        source = edge.pop("source")
        relationship = edge.pop("relationship")
        target = edge.pop("target")
        graph.relate(source, relationship, target, **edge)
    return graph.to_dict()


def get_ownership_chain(graph: OwnershipLineage, parcel_id: str) -> list[dict[str, Any]]:
    return graph.ownership_chain(parcel_id)


def assess_risk(**signals: Any) -> dict[str, Any]:
    return AnomalyRiskEngine().assess(**signals).to_dict()


def explain_review(fields: list[dict[str, Any]], *, default_action: str = "Verify original document and latest cadastral survey.") -> dict[str, Any]:
    return build_explainable_review([ExplainableField(**field) for field in fields], default_action=default_action)
