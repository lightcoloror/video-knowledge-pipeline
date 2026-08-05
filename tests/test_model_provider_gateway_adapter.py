from __future__ import annotations

import pytest

pytest.importorskip("model_provider_gateway")

from video_knowledge_pipeline.model_provider_gateway_adapter import (
    reviewed_shared_preset,
    shared_vkp_adapter_contract,
    vkp_route_to_shared,
)


def _profile(profile_id: str = "remote-gemini") -> dict[str, object]:
    return {
        "id": profile_id,
        "name": "Gemini 3.6 Flash",
        "provider": "gemini",
        "litellm_provider": "gemini",
        "auth_mode": "api_key_dpapi",
        "api_key_optional": False,
        "provider_options": {},
        "required_provider_options": [],
        "environment_bindings": [],
        "adapter_backend": "proxy",
        "base_url": "https://generativelanguage.googleapis.com/v1beta",
        "model": "gemini-3.6-flash",
        "location": "remote",
        "capabilities": ["text", "vision"],
        "secret_ref": f"dpapi:{profile_id}",
        "timeout_seconds": 120,
        "enabled": True,
    }


def _settings(*profiles: dict[str, object]) -> dict[str, object]:
    return {
        "profiles": list(profiles),
        "route_pools": [
            {
                "id": "remote-vision",
                "location": "remote_approved",
                "capability": "vision",
                "deployments": [str(profile["id"]) for profile in profiles],
                "retry_policy": {
                    "max_retries": 0,
                    "timeout_seconds": 120,
                    "cooldown_seconds": 0,
                },
            }
        ],
        "route_bindings": {
            "semantic_frame": {
                "default_location": "remote",
                "local_pool_id": "",
                "remote_pool_id": "remote-vision",
            }
        },
    }


def test_exact_vkp_profile_maps_to_reviewed_shared_preset() -> None:
    profile = _profile()
    assert reviewed_shared_preset(profile) == "gemini-3-6-flash"
    first = vkp_route_to_shared(
        _settings(profile), task="semantic_frame", max_calls=2, max_cost_usd=0.25
    )
    second = vkp_route_to_shared(
        _settings(profile), task="semantic_frame", max_calls=2, max_cost_usd=0.25
    )
    assert first["schema"] == "video_knowledge_pipeline.model_provider_gateway_adapter.v1"
    assert first["shared_route"]["route_revision"] == second["shared_route"]["route_revision"]
    assert first["profiles"][0]["auth_ref"] == "dpapi:remote-gemini"
    assert first["profiles"][0]["model"] == "gemini-3.6-flash"
    assert first["profiles"][0]["provenance"]["vkp_source"]["route_revision"]
    assert first["secrets_exposed"] is False
    assert first["provider_execution_performed"] is False


def test_adapter_contract_is_shared_and_route_bound() -> None:
    contract = shared_vkp_adapter_contract()
    assert contract["schema"] == "model_provider_gateway.adapter_contract.v1"
    assert contract["consumer_id"] == "vkp"
    assert contract["tasks"] == {
        "text": ["text"],
        "visual": ["vision"],
        "asr": ["asr"],
    }


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("model", "gemini-custom", "does not exactly match"),
        ("base_url", "https://example.invalid/v1", "does not exactly match"),
        ("adapter_backend", "legacy", "must not silently migrate"),
        ("location", "local", "remote VKP profiles only"),
    ],
)
def test_unreviewed_or_legacy_profiles_fail_closed(field: str, value: str, message: str) -> None:
    profile = _profile()
    profile[field] = value
    with pytest.raises(ValueError, match=message):
        reviewed_shared_preset(profile)


def test_provider_option_drift_fails_closed() -> None:
    profile = _profile()
    profile["provider_options"] = {"thinking_mode": "disabled"}
    with pytest.raises(ValueError, match="provider options drifted"):
        reviewed_shared_preset(profile)


def test_multiple_deployments_require_explicit_fallback() -> None:
    settings = _settings(_profile("gemini-a"), _profile("gemini-b"))
    with pytest.raises(ValueError, match="explicit fallback_enabled"):
        vkp_route_to_shared(settings, task="semantic_frame")
    result = vkp_route_to_shared(
        settings,
        task="semantic_frame",
        fallback_enabled=True,
        max_calls=2,
        max_cost_usd=0.25,
    )
    assert result["shared_route"]["fallback_policy"] == {
        "enabled": True,
        "ordered": True,
        "requires_consent": True,
    }
    assert result["silent_fallback_allowed"] is False
