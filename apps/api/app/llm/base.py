from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from typing import Any, Protocol


@dataclass
class ChatMessage:
    role: str
    content: str


@dataclass
class LLMRequest:
    provider: str
    model: str
    messages: list[ChatMessage]
    temperature: float = 0.7
    max_tokens: int = 800
    stream: bool = True
    mock_scenario: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class LLMChunk:
    delta: str
    sequence_number: int
    event_type: str = "token"


@dataclass
class LLMResponse:
    content: str
    provider: str
    model: str
    input_tokens: int
    output_tokens: int
    total_tokens: int
    safe_metadata: dict[str, Any] = field(default_factory=dict)


class Provider(Protocol):
    provider: str

    async def generate(self, request: LLMRequest) -> LLMResponse:
        ...

    async def stream(self, request: LLMRequest) -> AsyncIterator[LLMChunk]:
        ...

