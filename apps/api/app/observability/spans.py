from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from app.observability.trace import new_span_id


@dataclass
class SpanRecord:
    name: str
    span_id: str = field(default_factory=new_span_id)
    parent_span_id: str | None = None
    status: str = "ok"
    start_time: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    end_time: datetime | None = None
    duration_ms: int | None = None
    metadata_json: dict[str, Any] = field(default_factory=dict)

    def finish(self, status: str = "ok", **metadata: Any) -> "SpanRecord":
        self.status = status
        self.end_time = datetime.now(timezone.utc)
        self.duration_ms = int((self.end_time - self.start_time).total_seconds() * 1000)
        self.metadata_json.update(metadata)
        return self
