import json
from collections.abc import AsyncIterator
from uuid import UUID

from redis import Redis
from sqlalchemy.orm import Session

from app.config import get_settings
from app.llm.base import ChatMessage, LLMRequest, LLMResponse
from app.llm.errors import UserCancelledError, normalize_exception
from app.llm.gateway import LLMGateway
from app.observability.logger import ObservabilityLogger
from app.services.conversation_service import ConversationService


SYSTEM_PROMPT = "You are a concise, helpful assistant inside InferLens demo traffic."


class ChatService:
    def __init__(self, db: Session):
        self.db = db
        self.settings = get_settings()
        self.conversations = ConversationService(db)
        self.gateway = LLMGateway(db)

    async def stream_message(
        self,
        conversation_id: UUID,
        content: str,
        provider: str | None,
        model: str | None,
        temperature: float,
        max_tokens: int,
        mock_scenario: str | None = None,
    ) -> AsyncIterator[str]:
        user_message = self.conversations.add_message(conversation_id, "user", content)
        context = self.conversations.recent_context(conversation_id, self.settings.default_context_window)
        messages = [ChatMessage("system", SYSTEM_PROMPT)] + [
            ChatMessage(row.role, row.content) for row in context
        ]
        request = LLMRequest(
            provider=provider or self.settings.default_provider,
            model=model or self.settings.default_model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=True,
            mock_scenario=mock_scenario,
        )
        assistant = self.conversations.add_message(
            conversation_id, "assistant", "", "streaming", request.provider, request.model
        )
        logger = ObservabilityLogger(self.db, request, conversation_id, assistant.id)
        logger.span("request_received", user_message_id=str(user_message.id))
        logger.span("context_loaded", message_count=len(context))
        logger.span("gateway_routing", provider=request.provider, model=request.model)
        logger.span("provider_request", provider=request.provider, model=request.model)
        content_parts: list[str] = []
        yield _line({"event": "start", "trace_id": logger.trace_id, "message_id": str(assistant.id)})
        try:
            async for chunk in self.gateway.stream(request):
                if self._is_cancelled(conversation_id):
                    raise UserCancelledError("User cancelled the running response")
                content_parts.append(chunk.delta)
                logger.record_chunk(chunk.sequence_number, chunk.delta)
                yield _line({"event": "token", "delta": chunk.delta, "sequence": chunk.sequence_number})
            full_content = "".join(content_parts)
            response = LLMResponse(
                content=full_content,
                provider=request.provider,
                model=request.model,
                input_tokens=max(1, sum(len(m.content.split()) for m in request.messages)),
                output_tokens=max(1, len(full_content.split())),
                total_tokens=max(1, sum(len(m.content.split()) for m in request.messages))
                + max(1, len(full_content.split())),
                safe_metadata={"streamed": True},
            )
            logger.span("message_saved", message_id=str(assistant.id))
            trace_id = logger.finish("completed", response=response, content=full_content)
            self.conversations.update_message(
                assistant.id,
                content=full_content,
                status="completed",
                provider=request.provider,
                model=request.model,
                trace_id=trace_id,
            )
            yield _line({"event": "done", "trace_id": trace_id})
        except Exception as exc:
            error_type, error_message, retryable = normalize_exception(exc)
            status = "cancelled" if error_type == "user_cancelled" else "error"
            trace_id = logger.finish(
                status,
                content="".join(content_parts),
                error_type=error_type,
                error_message=error_message,
                retryable=retryable,
            )
            self.conversations.update_message(
                assistant.id,
                content="".join(content_parts),
                status=status,
                provider=request.provider,
                model=request.model,
                trace_id=trace_id,
            )
            yield _line({"event": status, "trace_id": trace_id, "error_type": error_type, "message": error_message})

    async def generate_once(
        self,
        messages: list[ChatMessage],
        provider: str,
        model: str,
        temperature: float,
        max_tokens: int,
        mock_scenario: str | None = None,
        replayed_from_trace_id: str | None = None,
        comparison_run_id: UUID | None = None,
    ) -> tuple[str, LLMResponse | None, str | None]:
        request = LLMRequest(provider, model, messages, temperature, max_tokens, False, mock_scenario)
        logger = ObservabilityLogger(
            self.db,
            request,
            trace_id=None,
            replayed_from_trace_id=replayed_from_trace_id,
            comparison_run_id=comparison_run_id,
        )
        logger.span("gateway_routing", provider=provider, model=model)
        logger.span("provider_request", provider=provider, model=model)
        try:
            response = await self.gateway.generate(request)
            trace_id = logger.finish("completed", response=response, content=response.content)
            return trace_id, response, None
        except Exception as exc:
            error_type, error_message, retryable = normalize_exception(exc)
            trace_id = logger.finish(
                "error",
                error_type=error_type,
                error_message=error_message,
                retryable=retryable,
            )
            return trace_id, None, error_type

    def cancel(self, conversation_id: UUID) -> None:
        self.conversations.cancel(conversation_id)
        try:
            Redis.from_url(
                self.settings.redis_url, decode_responses=True, socket_connect_timeout=0.05, socket_timeout=0.05
            ).setex(
                f"cancel:{conversation_id}", 60, "1"
            )
        except Exception:
            pass

    def _is_cancelled(self, conversation_id: UUID) -> bool:
        try:
            return (
                Redis.from_url(
                    self.settings.redis_url,
                    decode_responses=True,
                    socket_connect_timeout=0.05,
                    socket_timeout=0.05,
                ).get(f"cancel:{conversation_id}")
                == "1"
            )
        except Exception:
            return False


def _line(payload: dict) -> str:
    return json.dumps(payload) + "\n"
