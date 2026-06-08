# Ingestion

Internal inference logging calls `IngestionService.enqueue()` directly. The service validates idempotency using `event_id`, records a pending ingestion event, and pushes the payload to Redis Stream `inference_logs`.

The worker consumes the stream, redacts PII, persists logs/traces/spans/errors/redactions, and ACKs only after database success. After three failed attempts, the event is moved to a dead-letter stream and table.

