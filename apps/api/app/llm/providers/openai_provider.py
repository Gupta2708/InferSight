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


class OpenAIProvider:
    provider = "openai"

    async def generate(self, request: LLMRequest) -> LLMResponse:
        settings = get_settings()
        if not settings.openai_api_key:
            raise ProviderAuthError("OPENAI_API_KEY is not configured")
        payload = {
            "model": request.model,
            "input": [
                {
                    "role": message.role,
                    "content": [{"type": "input_text", "text": message.content}],
                }
                for message in request.messages
            ],
            "temperature": request.temperature,
            "max_output_tokens": request.max_tokens,
        }
        try:
            async with httpx.AsyncClient(timeout=60) as client:
                response = await client.post(
                    "https://api.openai.com/v1/responses",
                    headers={"Authorization": f"Bearer {settings.openai_api_key}"},
                    json=payload,
                )
        except httpx.HTTPError as exc:
            raise ProviderServerError("OpenAI request failed. Check network or provider status.") from exc
        self._raise_for_status(response)
        data = response.json()
        content = data.get("output_text") or self._extract_output_text(data)
        usage = data.get("usage", {})
        return LLMResponse(
            content=content,
            provider="openai",
            model=request.model,
            input_tokens=usage.get("input_tokens", 0),
            output_tokens=usage.get("output_tokens", 0),
            total_tokens=usage.get("total_tokens", 0),
            safe_metadata={"response_id": data.get("id"), "status": data.get("status")},
        )

    async def stream(self, request: LLMRequest) -> AsyncIterator[LLMChunk]:
        response = await self.generate(request)
        for index, token in enumerate(response.content.split()):
            yield LLMChunk(delta=token + " ", sequence_number=index + 1)

    def _raise_for_status(self, response: httpx.Response) -> None:
        if response.status_code in {401, 403}:
            raise ProviderAuthError("OpenAI authentication failed")
        if response.status_code == 429:
            raise ProviderRateLimitError("OpenAI rate limit exceeded")
        if response.status_code == 404:
            raise ProviderModelNotFoundError(
                "OpenAI model not found or not available to this API key/project."
            )
        if response.status_code == 400:
            raise InvalidRequestError("OpenAI request rejected. Check model and request settings.")
        if response.status_code >= 500:
            raise ProviderServerError(f"OpenAI server error: {response.status_code}")
        if response.status_code >= 400:
            raise ProviderServerError("OpenAI request failed.")

    def _extract_output_text(self, data: dict) -> str:
        parts: list[str] = []
        for item in data.get("output", []):
            for content in item.get("content", []):
                text = content.get("text")
                if isinstance(text, str):
                    parts.append(text)
        return "".join(parts)
