from collections.abc import AsyncIterator

import httpx

from app.config import get_settings
from app.llm.base import LLMChunk, LLMRequest, LLMResponse
from app.llm.errors import (
    InvalidRequestError,
    ProviderAuthError,
    ProviderModelNotFoundError,
    ProviderRateLimitError,
    ProviderServerError,
)


class GeminiProvider:
    provider = "gemini"

    async def generate(self, request: LLMRequest) -> LLMResponse:
        settings = get_settings()
        if not settings.gemini_api_key:
            raise ProviderAuthError("GEMINI_API_KEY is not configured")
        system_text = "\n".join(m.content for m in request.messages if m.role == "system").strip()
        contents = [
            {"role": "user" if m.role != "assistant" else "model", "parts": [{"text": m.content}]}
            for m in request.messages
            if m.role != "system" and m.content.strip()
        ]
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{request.model}:generateContent"
        payload = {
            "contents": contents,
            "generationConfig": {
                "temperature": request.temperature,
                "maxOutputTokens": request.max_tokens,
            },
        }
        if system_text:
            payload["systemInstruction"] = {"parts": [{"text": system_text}]}
        try:
            async with httpx.AsyncClient(timeout=60) as client:
                response = await client.post(
                    url,
                    params={"key": settings.gemini_api_key},
                    json=payload,
                )
        except httpx.HTTPError as exc:
            raise ProviderServerError("Gemini request failed. Check network or provider status.") from exc
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
            safe_metadata={
                "finish_reason": candidates[0].get("finishReason") if candidates else None,
                "model_version": data.get("modelVersion"),
            },
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
        if response.status_code == 404:
            raise ProviderModelNotFoundError(
                "Gemini model not found or not available to this API key/project."
            )
        if response.status_code == 400:
            raise InvalidRequestError("Gemini request rejected. Check model and request settings.")
        if response.status_code >= 500:
            raise ProviderServerError(f"Gemini server error: {response.status_code}")
        if response.status_code >= 400:
            raise ProviderServerError("Gemini request failed.")
