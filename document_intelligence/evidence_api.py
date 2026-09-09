from __future__ import annotations

from typing import Any

from .evidence import EvidenceGraph, EvidenceNode


def evidence_response(graph: EvidenceGraph, field_name: str) -> dict[str, Any]:
    items = graph.for_field(field_name)
    return {"field": field_name, "count": len(items), "evidence": [i.to_dict() for i in items]}


def highlight_payload(evidence: EvidenceNode) -> dict[str, Any]:
    return {
        "document_id": evidence.location.document_id,
        "document_name": evidence.location.document_name,
        "page": evidence.location.page,
        "region_id": evidence.location.region_id,
        "bbox": evidence.location.bbox,
        "evidence_id": evidence.evidence_id,
    }
