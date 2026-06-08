# Streaming

The streaming route is:

```text
POST /api/conversations/{conversation_id}/messages/stream
```

The frontend uses `fetch()` with `ReadableStream` because the request requires POST body data. The backend emits newline-delimited JSON events: `start`, `token`, `done`, `error`, and `cancelled`.

