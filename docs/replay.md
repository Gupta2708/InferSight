# Replay

Replay loads `request_snapshot_json`, applies debug options, runs the request through the same LLM gateway, and links the new trace with `replayed_from_trace_id`.

Supported debug options include same request, different provider, different model, lower temperature, without conversation history, edited user message, and mock timeout simulation.

