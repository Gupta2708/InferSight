import pytest

from app.llm.base import ChatMessage, LLMRequest
from app.llm.gateway import LLMGateway


@pytest.mark.asyncio
async def test_gateway_uses_mock_mode_for_real_provider_request():
    response = await LLMGateway().generate(
        LLMRequest("openai", "gpt-4.1-mini", [ChatMessage("user", "hello")], stream=False)
    )
    assert response.provider == "mock"
    assert response.model == "mock-fast"

