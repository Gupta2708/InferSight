# API

## Conversations

- `POST /api/conversations`
- `GET /api/conversations`
- `GET /api/conversations/{conversation_id}`
- `POST /api/conversations/{conversation_id}/messages`
- `POST /api/conversations/{conversation_id}/messages/stream`
- `POST /api/conversations/{conversation_id}/cancel`

## Ingestion

- `POST /api/ingest/inference`

## Observability

- `GET /api/logs`
- `GET /api/logs/{trace_id}`
- `GET /api/traces/{trace_id}`
- `POST /api/traces/{trace_id}/replay`
- `POST /api/comparisons`
- `GET /api/comparisons/{comparison_run_id}`

