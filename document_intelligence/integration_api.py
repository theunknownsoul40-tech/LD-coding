from __future__ import annotations

from typing import Any

from .integration import GovernmentApiGateway, build_oauth2_keycloak_config


def synchronize_verified_record(record: dict[str, Any], targets: list[str] | None = None) -> list[dict[str, Any]]:
    """Prototype-only sync. Default adapters are mocks and never touch government databases."""
    return [item.to_dict() for item in GovernmentApiGateway().queue_sync(record, targets)]


def auth_config(*, issuer_url: str, client_id: str, audience: str | None = None) -> dict[str, Any]:
    return build_oauth2_keycloak_config(issuer_url=issuer_url, client_id=client_id, audience=audience)
