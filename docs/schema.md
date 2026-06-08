# Schema

The database stores conversations, messages, provider configs, inference traces, spans, logs, stream events, provider errors, PII redaction events, ingestion events, dead letters, comparison runs, and comparison results.

`ingestion_events.event_id` has a unique constraint for idempotency.

`inference_logs.request_snapshot_json` stores only replay-safe request data: provider, model, messages/context snapshot, temperature, max tokens, stream flag, and mock/debug options. It must never contain API keys, headers, bearer tokens, cookies, environment variables, or secrets.

