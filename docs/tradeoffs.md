# Tradeoffs

- PostgreSQL is used instead of ClickHouse to keep the local project simple and demoable.
- Redis Streams are used instead of Kafka for one-command setup.
- Regex PII redaction is simple, explainable, and fast.
- Short context keeps latency and token usage bounded.
- Cost tracking is estimated, not a billing system.
- Prompt management and evaluation features are intentionally excluded.

