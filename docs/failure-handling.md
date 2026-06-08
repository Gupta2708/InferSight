# Failure Handling

Errors normalize to provider timeout, rate limit, auth error, server error, invalid request, stream interrupted, user cancelled, database error, ingestion error, worker error, or unknown error.

Timeouts and rate limits are retryable. Auth and invalid request errors are not. Worker/database failures remain unacked until retry or dead-letter.

