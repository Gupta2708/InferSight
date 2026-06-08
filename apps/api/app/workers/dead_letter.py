import json

from redis import Redis
from sqlalchemy.orm import Session

from app.config import get_settings
from app.db import models


def move_to_dead_letter(db: Session, redis: Redis, event_id: str, payload: dict, reason: str) -> None:
    settings = get_settings()
    redis.xadd(settings.dead_letter_stream, {"event_id": event_id, "payload": json.dumps(payload)})
    db.add(
        models.DeadLetterEvent(
            event_id=event_id,
            trace_id=payload.get("trace_id", "unknown"),
            event_type="inference",
            failure_reason=reason,
            payload_json=payload,
        )
    )
    event = db.query(models.IngestionEvent).filter_by(event_id=event_id).first()
    if event:
        event.status = "dead_lettered"
    db.commit()

