# Architecture

```text
Next.js Web
  -> FastAPI API
    -> Conversation Service
    -> LLM Gateway
      -> MockProvider / OpenAIProvider / GeminiProvider
    -> Observability Logger
    -> IngestionService.enqueue()
      -> Redis Streams
        -> Worker
          -> PII Redaction
          -> PostgreSQL
```

Internal app code never makes HTTP calls to the app's own ingestion route. The ingestion HTTP route is reserved for external SDK and demo events.

