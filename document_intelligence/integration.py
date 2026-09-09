from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Protocol
import uuid


@dataclass
class SyncEnvelope:
    sync_id: str
    target: str
    record: dict[str, Any]
    status: str = "QUEUED"
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    response: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class GovernmentAdapter(Protocol):
    name: str
    def push(self, record: dict[str, Any]) -> dict[str, Any]: ...


class MockGovernmentAdapter:
    """Safe prototype adapter: simulates synchronization and never writes external systems."""

    def __init__(self, name: str) -> None:
        self.name = name
        self.synced: list[dict[str, Any]] = []

    def push(self, record: dict[str, Any]) -> dict[str, Any]:
        response = {"target": self.name, "status": "MOCK_ACCEPTED", "remote_id": f"MOCK-{uuid.uuid4().hex[:12]}", "record": record}
        self.synced.append(response)
        return response


class GovernmentApiGateway:
    """Routes verified records to mock LRMS/DILRMP/GIS adapters."""

    def __init__(self, adapters: dict[str, GovernmentAdapter] | None = None) -> None:
        self.adapters = adapters or {name: MockGovernmentAdapter(name) for name in ("LRMS", "DILRMP", "GIS")}
        self.audit_log: list[SyncEnvelope] = []

    def queue_sync(self, record: dict[str, Any], targets: list[str] | None = None) -> list[SyncEnvelope]:
        selected = targets or list(self.adapters)
        envelopes: list[SyncEnvelope] = []
        for target in selected:
            if target not in self.adapters:
                raise KeyError(f"Unknown integration target: {target}")
            envelope = SyncEnvelope(str(uuid.uuid4()), target, record)
            try:
                envelope.response = self.adapters[target].push(record)
                envelope.status = "MOCK_ACCEPTED"
            except Exception as exc:
                envelope.status = "FAILED"
                envelope.response = {"error": str(exc)}
            envelopes.append(envelope)
            self.audit_log.append(envelope)
        return envelopes

    def audit(self) -> list[dict[str, Any]]:
        return [item.to_dict() for item in self.audit_log]


def build_oauth2_keycloak_config(*, issuer_url: str, client_id: str, audience: str | None = None) -> dict[str, Any]:
    """Return integration configuration metadata; secrets/tokens are never stored here."""
    return {"issuer_url": issuer_url, "client_id": client_id, "audience": audience, "auth": "OAuth2", "provider": "Keycloak"}
