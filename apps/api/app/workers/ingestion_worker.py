import json
import time

from redis import Redis
from redis.exceptions import TimeoutError as RedisTimeoutError
from sqlalchemy import inspect

from app.config import get_settings
from app.db import models
from app.db.session import SessionLocal, engine
from app.services.ingestion_service import process_ingestion_event
from app.workers.dead_letter import move_to_dead_letter


def ensure_group(redis: Redis) -> None:
    settings = get_settings()
    try:
        redis.xgroup_create(settings.ingestion_stream, settings.worker_group, id="0", mkstream=True)
    except Exception as exc:
        if "BUSYGROUP" not in str(exc):
            raise


def run_forever() -> None:
    settings = get_settings()
    wait_for_schema()
    redis = Redis.from_url(settings.redis_url, decode_responses=True, socket_timeout=10)
    ensure_group(redis)
    consumer = f"worker-{int(time.time())}"
    while True:
        try:
            messages = redis.xreadgroup(
                settings.worker_group,
                consumer,
                {settings.ingestion_stream: ">"},
                count=10,
                block=5000,
            )
        except RedisTimeoutError:
            continue
        for _, entries in messages:
            for redis_id, fields in entries:
                event_id = fields["event_id"]
                payload = json.loads(fields["payload"])
                db = SessionLocal()
                try:
                    process_ingestion_event(db, event_id, payload)
                    redis.xack(settings.ingestion_stream, settings.worker_group, redis_id)
                except Exception as exc:
                    db.rollback()
                    record = db.query(models.IngestionEvent).filter_by(event_id=event_id).first()
                    if record:
                        record.retry_count += 1
                        record.status = "failed"
                        db.commit()
                        if record.retry_count >= 3:
                            move_to_dead_letter(db, redis, event_id, payload, str(exc))
                            redis.xack(settings.ingestion_stream, settings.worker_group, redis_id)
                    else:
                        move_to_dead_letter(db, redis, event_id, payload, str(exc))
                        redis.xack(settings.ingestion_stream, settings.worker_group, redis_id)
                finally:
                    db.close()


def wait_for_schema() -> None:
    while True:
        try:
            inspector = inspect(engine)
            if inspector.has_table("ingestion_events") and inspector.has_table("inference_logs"):
                return
        except Exception:
            pass
        time.sleep(2)


if __name__ == "__main__":
    run_forever()
