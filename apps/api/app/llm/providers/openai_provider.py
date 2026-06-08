from collections.abc import AsyncIterator

import httpx

from app.config import get_settings
from app.llm.base import LLMChunk, LLMRequest, LLMResponse
from app.llm.errors import ProviderAuthError, ProviderRateLimitError, ProviderServerError


class OpenAIProvider:
    provider = "openai"

    async def generate(self, request: LLMRequest) -> LLMResponse:
        settings = get_settings()
        if not settings.openai_api_key:
            raise ProviderAuthError("OPENAI_API_KEY is not configured")
        payload = {
            "model": request.model,
            "messages": [{"role": m.role, "content": m.content} for m in request.messages],
            "temperature": request.temperature,
            "max_tokens": request.max_tokens,
        }
        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {settings.openai_api_key}"},
                json=payload,
            )
        self._raise_for_status(response)
        data = response.json()
        content = data["choices"][0]["message"]["content"]
        usage = data.get("usage", {})
        return LLMResponse(
            content=content,
            provider="openai",
            model=request.model,
            input_tokens=usage.get("prompt_tokens", 0),
            output_tokens=usage.get("completion_tokens", 0),
            total_tokens=usage.get("total_tokens", 0),
            safe_metadata={"finish_reason": data["choices"][0].get("finish_reason")},
        )

    async def stream(self, request: LLMRequest) -> AsyncIterator[LLMChunk]:
        response = await self.generate(request)
        for index, token in enumerate(response.content.split()):
            yield LLMChunk(delta=token + " ", sequence_number=index + 1)

    def _raise_for_status(self, response: httpx.Response) -> None:
        if response.status_code == 401:
            raise ProviderAuthError("OpenAI authentication failed")
        if response.status_code == 429:
            raise ProviderRateLimitError("OpenAI rate limit exceeded")
        if response.status_code >= 500:
            raise ProviderServerError(f"OpenAI server error: {response.status_code}")
        response.raise_for_status()

