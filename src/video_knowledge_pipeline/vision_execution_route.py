from __future__ import annotations

from typing import Any

from .vision_gateway_profile import resolve_route_based_vision_gateway_profile


def resolve_vision_task_execution_route(
    task: str,
    *,
    provider_config: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Resolve one execution task to its explicit config or its configured gateway route.

    The result never substitutes a legacy provider for an absent route.  Callers
    may support legacy operation only when the caller supplied an explicit
    provider configuration.
    """
    if provider_config is not None:
        return {
            "task": task,
            "status": "explicit_provider_config",
            "provider_config": dict(provider_config),
            "provider_config_source": "explicit",
            "route_profile": {},
            "legacy_fallback_blocked": False,
        }

    profile = resolve_route_based_vision_gateway_profile(task)
    route_config = profile.get("provider_config") if isinstance(profile.get("provider_config"), dict) else {}
    if profile.get("route_configured") and route_config:
        return {
            "task": task,
            "status": str(profile.get("status") or "gateway_unavailable"),
            "provider_config": dict(route_config),
            "provider_config_source": "route_based_gateway",
            "route_profile": profile,
            "legacy_fallback_blocked": False,
        }

    return {
        "task": task,
        "status": str(profile.get("status") or "route_missing"),
        "provider_config": {},
        "provider_config_source": "route_missing",
        "route_profile": profile,
        "legacy_fallback_blocked": True,
    }
