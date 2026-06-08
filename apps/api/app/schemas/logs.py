from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel


class LogOut(BaseModel):
    id: UUID
    trace_id: str
    conversation_id: UUID | None
    message_id: UUID | None
    provider: str
    model: str
    status: str
    latency_ms: int | None
    time_to_first_token_ms: int | None
    total_tokens: int
    estimated_total_cost: float
    input_preview: str
    output_preview: str
    error_type: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class LogDetailOut(LogOut):
    safe_metadata_json: dict[str, Any]
    request_snapshot_json: dict[str, Any]

