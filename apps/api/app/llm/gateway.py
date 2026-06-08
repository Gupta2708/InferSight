from collections.abc import AsyncIterator

from app.config import get_settings
from app.llm.base import LLMChunk, LLMRequest, LLMResponse, Provider
from app.llm.providers.gemini_provider import GeminiProvider
from app.llm.providers.mock_provider import MockProvider
from app.llm.providers.openai_provider import OpenAIProvider


class LLMGateway:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.providers: dict[str, Provider] = {
            "mock": MockProvider(),
            "openai": OpenAIProvider(),
            "gemini": GeminiProvider(),
        }

    def resolve_provider(self, provider: str | None) -> str:
        if self.settings.llm_mock_mode:
            return "mock" if provider in {None, "mock", "openai", "gemini"} else provider
        return provider or self.settings.default_provider

    def resolve_model(self, provider: str, model: str | None) -> str:
        if provider == "mock":
            return model if model and model.startswith("mock") else "mock-fast"
        return model or self.settings.default_model

    async def generate(self, request: LLMRequest) -> LLMResponse:
        provider = self.resolve_provider(request.provider)
        request.provider = provider
        request.model = self.resolve_model(provider, request.model)
        return await self.providers[provider].generate(request)

    async def stream(self, request: LLMRequest) -> AsyncIterator[LLMChunk]:
        provider = self.resolve_provider(request.provider)
        request.provider = provider
        request.model = self.resolve_model(provider, request.model)
        async for chunk in self.providers[provider].stream(request):
            yield chunk

    def available_models(self) -> list[dict]:
        return [
            {"provider": "mock", "model": "mock-fast", "enabled": True, "supports_streaming": True},
            {"provider": "mock", "model": "mock-slow", "enabled": True, "supports_streaming": True},
            {
                "provider": "openai",
                "model": "gpt-4.1-mini",
                "enabled": bool(get_settings().openai_api_key) and not get_settings().llm_mock_mode,
                "supports_streaming": True,
            },
            {
                "provider": "gemini",
                "model": "gemini-flash",
                "enabled": bool(get_settings().gemini_api_key) and not get_settings().llm_mock_mode,
                "supports_streaming": True,
            },
        ]
