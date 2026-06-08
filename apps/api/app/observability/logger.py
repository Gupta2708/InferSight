import time
import uuid
from datetime import datetime
from typing import Any

from sqlalchemy.orm import Session

from app.llm.base import LLMRequest, LLMResponse
from app.llm.cost import estimate_cost
from app.observability.metadata import preview, safe_metadata
from app.observability.spans import SpanRecord
from app.observability.trace import new_trace_id
from app.services.ingestion_service import IngestionService


class ObservabilityLogger:
    def __init__(
        self,
        db: Session,
        request: LLMRequest,
        conversation_id: Any = None,
        message_id: Any = None,
        trace_id: str | None = None,
        replayed_from_trace_id: str | None = None,
        comparison_run_id: Any = None,
    ):
        self.db = db
        self.request = request
        self.conversation_id = conversation_id
        self.message_id = message_id
        self.trace_id = trace_id or new_trace_id()
        self.replayed_from_trace_id = replayed_from_trace_id
        self.comparison_run_id = comparison_run_id
        self.started = time.perf_counter()
        self.spans: list[SpanRecord] = []
        self.stream_events: list[dict] = []
        self.first_token_ms: int | None = None

    def span(self, name: str, status: str = "ok", **metadata: Any) -> None:
        span = SpanRecord(name=name)
        span.finish(status=status, **safe_metadata(metadata))
        self.spans.append(span)

    def record_chunk(self, sequence_number: int, delta_text: str) -> None:
        if self.first_token_ms is None:
            self.first_token_ms = self.elapsed_ms()
            self.span("first_token", sequence_number=sequence_number)
        self.stream_events.append(
            {"sequence_number": sequence_number, "event_type": "token", "delta_text": delta_text}
        )

    def elapsed_ms(self) -> int:
        return int((time.perf_counter() - self.started) * 1000)

    def snapshot(self) -> dict:
        return {
            "provider": self.request.provider,
            "model": self.request.model,
            "messages": [{"role": m.role, "content": m.content} for m in self.request.messages],
            "temperature": self.request.temperature,
            "max_tokens": self.request.max_tokens,
            "stream": self.request.stream,
            "mock_scenario": self.request.mock_scenario,
        }

    def finish(
        self,
        status: str,
        response: LLMResponse | None = None,
        content: str = "",
        error_type: str | None = None,
        error_message: str | None = None,
        retryable: bool = False,
    ) -> str:
        latency_ms = self.elapsed_ms()
        input_tokens = response.input_tokens if response else self._input_tokens()
        output_tokens = response.output_tokens if response else max(0, len(content.split()))
        total_tokens = response.total_tokens if response else input_tokens + output_tokens
        input_cost, output_cost, total_cost = estimate_cost(
            self.request.provider, self.request.model, input_tokens, output_tokens
        )
        if status in {"completed", "cancelled"}:
            self.span("stream_completed" if self.request.stream else "completed", status=status)
        self.span("log_emitted", status=status)
        event = {
            "event_id": f"evt_{uuid.uuid4().hex}",
            "trace_id": self.trace_id,
            "conversation_id": self.conversation_id,
            "message_id": self.message_id,
            "provider": self.request.provider,
            "model": self.request.model,
            "temperature": self.request.temperature,
            "max_tokens": self.request.max_tokens,
            "stream": self.request.stream,
            "status": status,
            "latency_ms": latency_ms,
            "time_to_first_token_ms": self.first_token_ms,
            "tokens_per_second": round(output_tokens / max(latency_ms / 1000, 0.001), 2),
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_tokens": total_tokens,
            "estimated_input_cost": input_cost,
            "estimated_output_cost": output_cost,
            "estimated_total_cost": total_cost,
            "input_preview": preview(self.snapshot()["messages"]),
            "output_preview": content[:500],
            "error_type": error_type,
            "error_message": error_message,
            "retryable": retryable,
            "request_snapshot_json": self.snapshot(),
            "safe_metadata_json": safe_metadata(response.safe_metadata if response else {}),
            "spans": [
                {
                    "span_id": s.span_id,
                    "parent_span_id": s.parent_span_id,
                    "name": s.name,
                    "status": s.status,
                    "start_time": s.start_time,
                    "end_time": s.end_time,
                    "duration_ms": s.duration_ms,
                    "metadata_json": s.metadata_json,
                }
                for s in self.spans
            ],
            "stream_events": self.stream_events,
            "replayed_from_trace_id": self.replayed_from_trace_id,
            "comparison_run_id": self.comparison_run_id,
        }
        IngestionService(self.db).enqueue(event)
        return self.trace_id

    def _input_tokens(self) -> int:
        return max(1, sum(len(message.content.split()) for message in self.request.messages))
