from app.llm.base import ChatMessage
from app.services.chat_service import ChatService


class ReplayService:
    def __init__(self, db):
        self.db = db

    async def replay(self, trace_id: str, options) -> dict:
        from app.db import models

        log = self.db.query(models.InferenceLog).filter_by(trace_id=trace_id).first()
        if not log:
            raise KeyError("trace_not_found")
        snapshot = dict(log.request_snapshot_json or {})
        messages = snapshot.get("messages", [])
        if options.without_context and messages:
            messages = messages[-1:]
        if options.edited_user_message:
            if messages:
                messages[-1]["content"] = options.edited_user_message
            else:
                messages = [{"role": "user", "content": options.edited_user_message}]
        provider = options.provider or snapshot.get("provider") or log.provider
        model = options.model or snapshot.get("model") or log.model
        temperature = options.temperature if options.temperature is not None else snapshot.get("temperature", 0.7)
        chat_messages = [ChatMessage(m["role"], m["content"]) for m in messages]
        new_trace_id, response, error_type = await ChatService(self.db).generate_once(
            chat_messages,
            provider,
            model,
            temperature,
            snapshot.get("max_tokens", 800),
            options.mock_scenario,
            replayed_from_trace_id=trace_id,
        )
        return {
            "trace_id": new_trace_id,
            "status": "error" if error_type else "completed",
            "output_preview": response.content[:500] if response else "",
            "error_type": error_type,
        }

