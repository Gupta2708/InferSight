# InferSight

InferSight is a production-style LLM gateway and inference observability platform. It includes a chatbot to generate real LLM traffic, then captures inference metadata, queues events through Redis Streams, stores normalized logs in PostgreSQL, and visualizes latency, errors, tokens, cost, traces, replay, and provider comparison.

## Run

```bash
docker compose up --build
```

Then open:

- Web: http://localhost:3000
- API: http://localhost:8000/health

Mock mode is enabled by default with `LLM_MOCK_MODE=true`, so the project runs without OpenAI or Gemini keys.

## Services

- `web`: Next.js, TypeScript, Tailwind, Recharts
- `api`: FastAPI, SQLAlchemy, Alembic
- `worker`: Redis Streams ingestion worker
- `postgres`: PostgreSQL
- `redis`: Redis Streams and cancellation flags

The worker depends only on Postgres and Redis.

## Key Flows

- Chat streaming uses `POST /api/conversations/{conversation_id}/messages/stream`.
- The frontend reads the POST response with `fetch()` and `ReadableStream`.
- Internal logging calls `IngestionService.enqueue()` directly.
- `POST /api/ingest/inference` remains available for external SDK/demo ingestion.
- Replay uses `request_snapshot_json`, which stores replay-safe request data only.
- Trace/log UI shows redacted previews and safe metadata by default.

## Excluded

Prompt playground, prompt versioning, dataset evals, LLM-as-judge, Kubernetes, OpenTelemetry/Grafana, ClickHouse, semantic cache, complex auth/RBAC, billing, RAG/vector DB, and agent framework are intentionally out of scope.

