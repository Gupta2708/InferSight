from __future__ import annotations

from sqlalchemy.orm import Session

from app.config import get_settings
from app.db import models


DEFAULT_PROVIDER_CONFIGS = [
    {
        "provider": "mock",
        "model": "mock-fast",
        "enabled": True,
        "supports_streaming": True,
        "input_cost_per_1k_tokens": 0.0,
        "output_cost_per_1k_tokens": 0.0,
    },
    {
        "provider": "mock",
        "model": "mock-slow",
        "enabled": True,
        "supports_streaming": True,
        "input_cost_per_1k_tokens": 0.0,
        "output_cost_per_1k_tokens": 0.0,
    },
    {
        "provider": "mock",
        "model": "mock-error",
        "enabled": True,
        "supports_streaming": True,
        "input_cost_per_1k_tokens": 0.0,
        "output_cost_per_1k_tokens": 0.0,
    },
    {
        "provider": "openai",
        "model": "gpt-4.1-mini",
        "enabled": True,
        "supports_streaming": True,
        "input_cost_per_1k_tokens": 0.0004,
        "output_cost_per_1k_tokens": 0.0016,
    },
    {
        "provider": "gemini",
        "model": "gemini-2.5-flash",
        "enabled": True,
        "supports_streaming": True,
        "input_cost_per_1k_tokens": 0.0003,
        "output_cost_per_1k_tokens": 0.0025,
    },
]

LEGACY_MODEL_ALIASES = {
    ("gemini", "gemini-flash"): "gemini-2.5-flash",
    ("gemini", "gemini-flash-latest"): "gemini-2.5-flash",
    ("gemini", "gemini-1.5-flash"): "gemini-2.5-flash",
    ("gemini", "gemini-2.0-flash"): "gemini-2.5-flash",
    ("gemini", "gemini-2.0-flash-001"): "gemini-2.5-flash",
}


def provider_configs_by_key() -> dict[tuple[str, str], dict]:
    return {
        (item["provider"], item["model"]): item.copy()
        for item in DEFAULT_PROVIDER_CONFIGS
    }


def normalize_model_alias(provider: str, model: str) -> str:
    return LEGACY_MODEL_ALIASES.get((provider, model), model)


def default_model_for_provider(provider: str) -> str:
    for item in DEFAULT_PROVIDER_CONFIGS:
        if item["provider"] == provider and item["enabled"]:
            return item["model"]
    return ""


def provider_model_exists(db: Session | None, provider: str, model: str) -> bool:
    normalized_model = normalize_model_alias(provider, model)
    if db is not None:
        row = (
            db.query(models.ProviderConfig.id)
            .filter(
                models.ProviderConfig.provider == provider,
                models.ProviderConfig.model == normalized_model,
                models.ProviderConfig.enabled.is_(True),
            )
            .first()
        )
        return bool(row)
    return (provider, normalized_model) in provider_configs_by_key()


def load_provider_rows(db: Session | None) -> list[dict]:
    if db is None:
        return [row.copy() for row in DEFAULT_PROVIDER_CONFIGS]

    rows = (
        db.query(models.ProviderConfig)
        .order_by(models.ProviderConfig.provider, models.ProviderConfig.model)
        .all()
    )
    if not rows:
        return [row.copy() for row in DEFAULT_PROVIDER_CONFIGS]

    settings = get_settings()
    return [with_runtime_status(row, settings) for row in rows]


def with_runtime_status(row: models.ProviderConfig | dict, settings=None) -> dict:
    settings = settings or get_settings()
    if isinstance(row, dict):
        item = row.copy()
    else:
        item = {
            "provider": row.provider,
            "model": row.model,
            "enabled": row.enabled,
            "supports_streaming": row.supports_streaming,
            "input_cost_per_1k_tokens": row.input_cost_per_1k_tokens,
            "output_cost_per_1k_tokens": row.output_cost_per_1k_tokens,
        }

    provider = item["provider"]
    key_configured = True
    if provider == "openai":
        key_configured = bool(settings.openai_api_key)
    elif provider == "gemini":
        key_configured = bool(settings.gemini_api_key)

    available = bool(item["enabled"]) and key_configured and not (
        settings.llm_mock_mode and provider != "mock"
    )
    item["key_configured"] = key_configured
    item["available"] = available
    item["status_label"] = provider_status_label(
        provider=provider,
        key_configured=key_configured,
        llm_mock_mode=settings.llm_mock_mode,
        available=available,
    )
    return item


def provider_status_label(
    *, provider: str, key_configured: bool, llm_mock_mode: bool, available: bool
) -> str:
    if provider == "mock":
        return "mock mode" if llm_mock_mode else "enabled"
    if not key_configured:
        return "needs key"
    if llm_mock_mode:
        return "mock mode"
    return "configured" if available else "configured"
