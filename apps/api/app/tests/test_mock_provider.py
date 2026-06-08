import pytest

from app.llm.base import ChatMessage, LLMRequest
from app.llm.errors import ProviderRateLimitError, ProviderServerError, ProviderTimeoutError
from app.llm.providers.mock_provider import MockProvider


@pytest.mark.asyncio
async def test_mock_generate_normal():
    response = await MockProvider().generate(
        LLMRequest("mock", "mock-fast", [ChatMessage("user", "hello")], stream=False)
    )
    assert response.provider == "mock"
    assert "hello" in response.content
    assert response.total_tokens > 0


@pytest.mark.asyncio
async def test_mock_stream_chunks():
    chunks = [
        chunk
        async for chunk in MockProvider().stream(
            LLMRequest("mock", "mock-fast", [ChatMessage("user", "hello")])
        )
    ]
    assert chunks
    assert chunks[0].event_type == "token"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("scenario", "error"),
    [
        ("timeout", ProviderTimeoutError),
        ("rate_limit", ProviderRateLimitError),
        ("provider_error", ProviderServerError),
    ],
)
async def test_mock_failures(scenario, error):
    with pytest.raises(error):
        await MockProvider().generate(
            LLMRequest("mock", "mock-fast", [ChatMessage("user", "hello")], mock_scenario=scenario)
        )

