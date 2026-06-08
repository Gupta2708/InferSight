from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class MessageCreate(BaseModel):
    content: str = Field(min_length=1)
    provider: str | None = None
    model: str | None = None


class StreamMessageCreate(MessageCreate):
    temperature: float = 0.7
    max_tokens: int = 800
    mock_scenario: str | None = None


class MessageOut(BaseModel):
    id: UUID
    conversation_id: UUID
    role: str
    content: str
    status: str
    provider: str | None = None
    model: str | None = None
    trace_id: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ConversationCreate(BaseModel):
    title: str = "New Conversation"


class ConversationOut(BaseModel):
    id: UUID
    title: str
    status: str
    created_at: datetime
    updated_at: datetime
    last_message_at: datetime | None
    messages: list[MessageOut] = []

    model_config = {"from_attributes": True}


class ConversationSummary(BaseModel):
    id: UUID
    title: str
    status: str
    preview: str | None = None
    message_count: int = 0
    created_at: datetime
    updated_at: datetime
    last_message_at: datetime | None

    model_config = {"from_attributes": True}
