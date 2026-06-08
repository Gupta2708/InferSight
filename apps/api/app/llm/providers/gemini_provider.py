from collections.abc import AsyncIterator

import httpx

from app.config import get_settings
from app.llm.base import LLMChunk, LLMRequest, LLMResponse
from app.llm.errors import ProviderAuthError, ProviderRateLimitError, ProviderServerError


class GeminiProvider:
    provider = "gemini"

    async def generate(self, request: LLMRequest) -> LLMResponse:
        settings = get_settings()
        if not settings.gemini_api_key:
            raise ProviderAuthError("GEMINI_API_KEY is not configured")
        contents = [
            {"role": "user" if m.role != "assistant" else "model", "parts": [{"text": m.content}]}
            for m in request.messages
            if m.role != "system"
        ]
        url = (
            "https://generativelanguage.googleapis.com/v1beta/models/"
            f"{request.model}:generateContent?key={settings.gemini_api_key}"
        )
        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(
                url,
                json={
                    "contents": contents,
                    "generationConfig": {
                        "temperature": request.temperature,
                        "maxOutputTokens": request.max_tokens,
                    },
                },
            )
        self._raise_for_status(response)
        data = response.json()
        candidates = data.get("candidates", [])
        content = candidates[0]["content"]["parts"][0]["text"] if candidates else ""
        usage = data.get("usageMetadata", {})
        input_tokens = usage.get("promptTokenCount", 0)
        output_tokens = usage.get("candidatesTokenCount", 0)
        return LLMResponse(
            content=content,
            provider="gemini",
            model=request.model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=usage.get("totalTokenCount", input_tokens + output_tokens),
            safe_metadata={"finish_reason": candidates[0].get("finishReason") if candidates else None},
        )

    async def stream(self, request: LLMRequest) -> AsyncIterator[LLMChunk]:
        response = await self.generate(request)
        for index, token in enumerate(response.content.split()):
            yield LLMChunk(delta=token + " ", sequence_number=index + 1)

    def _raise_for_status(self, response: httpx.Response) -> None:
        if response.status_code in {401, 403}:
            raise ProviderAuthError("Gemini authentication failed")
        if response.status_code == 429:
            raise ProviderRateLimitError("Gemini rate limit exceeded")
        if response.status_code >= 500:
            raise ProviderServerError(f"Gemini server error: {response.status_code}")
        response.raise_for_status()

