from collections.abc import AsyncIterator

from typing import Optional

from app.config import get_settings
from app.llm.base import LLMChunk, LLMRequest, LLMResponse, Provider
from app.llm.providers.gemini_provider import GeminiProvider
from app.llm.providers.mock_provider import MockProvider
from app.llm.providers.openai_provider import OpenAIProvider
from app.llm.errors import ProviderModelInvalidError, ProviderNotFoundError
from sqlalchemy.orm import Session
from app.services.provider_catalog import (
    DEFAULT_PROVIDER_CONFIGS,
    default_model_for_provider,
    normalize_model_alias,
    provider_model_exists,
)


class LLMGateway:
    def __init__(self, db: Optional[Session] = None) -> None:
        self.settings = get_settings()
        self.db = db
        self.providers: dict[str, Provider] = {
            "mock": MockProvider(),
            "openai": OpenAIProvider(),
            "gemini": GeminiProvider(),
        }

    def resolve_provider(self, provider: str | None) -> str:
        if self.settings.llm_mock_mode:
            resolved = "mock" if provider in {None, "mock", "openai", "gemini"} else provider
        else:
            resolved = provider or self.settings.default_provider
        if resolved not in self.providers:
            raise ProviderNotFoundError(f"Provider {resolved} is not configured")
        return resolved

    def resolve_model(self, provider: str, model: str | None) -> str:
        if provider == "mock":
            return model if model and model.startswith("mock") else "mock-fast"
        if model:
            return normalize_model_alias(provider, model)
        return default_model_for_provider(provider) or self.settings.default_model

    def _is_valid_provider_model(self, provider: str, model: str) -> bool:
        return provider_model_exists(self.db, provider, model)

    async def generate(self, request: LLMRequest) -> LLMResponse:
        provider = self.resolve_provider(request.provider)
        request.provider = provider
        request.model = self.resolve_model(provider, request.model)
        # validate provider/model combo
        if not self._is_valid_provider_model(request.provider, request.model):
            raise ProviderModelInvalidError(f"Model {request.model} is not valid for provider {request.provider}")
        return await self.providers[provider].generate(request)

    async def stream(self, request: LLMRequest) -> AsyncIterator[LLMChunk]:
        provider = self.resolve_provider(request.provider)
        request.provider = provider
        request.model = self.resolve_model(provider, request.model)
        # validate provider/model combo
        if not self._is_valid_provider_model(request.provider, request.model):
            raise ProviderModelInvalidError(f"Model {request.model} is not valid for provider {request.provider}")
        async for chunk in self.providers[provider].stream(request):
            yield chunk

    def available_models(self) -> list[dict]:
        return [
            {
                "provider": config["provider"],
                "model": config["model"],
                "enabled": config["enabled"],
                "supports_streaming": config["supports_streaming"],
            }
            for config in DEFAULT_PROVIDER_CONFIGS
        ]
