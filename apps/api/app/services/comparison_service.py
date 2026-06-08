from datetime import datetime, timezone
from time import perf_counter

from sqlalchemy.orm import Session

from app.db import models
from app.llm.base import ChatMessage
from app.llm.cost import estimate_cost
from app.services.chat_service import ChatService, SYSTEM_PROMPT


class ComparisonService:
    def __init__(self, db: Session):
        self.db = db

    async def create(self, payload) -> dict:
        run = models.ComparisonRun(
            conversation_id=payload.conversation_id,
            source_message_id=payload.source_message_id,
            prompt=payload.prompt,
            context_mode=payload.context_mode,
            status="running",
        )
        self.db.add(run)
        self.db.commit()
        self.db.refresh(run)
        messages = [ChatMessage("system", SYSTEM_PROMPT), ChatMessage("user", payload.prompt)]
        for target in payload.targets:
            started = perf_counter()
            trace_id, response, error_type = await ChatService(self.db).generate_once(
                messages,
                target.provider,
                target.model,
                payload.temperature,
                payload.max_tokens,
                comparison_run_id=run.id,
            )
            latency_ms = max(0, int((perf_counter() - started) * 1000))
            input_tokens = response.input_tokens if response else max(1, len(payload.prompt.split()))
            output_tokens = response.output_tokens if response else 0
            total_tokens = response.total_tokens if response else input_tokens
            _, _, total_cost = estimate_cost(target.provider, target.model, input_tokens, output_tokens)
            self.db.add(
                models.ComparisonResult(
                    comparison_run_id=run.id,
                    trace_id=trace_id,
                    provider=target.provider,
                    model=target.model,
                    status="error" if error_type else "completed",
                    latency_ms=latency_ms,
                    time_to_first_token_ms=None,
                    total_tokens=total_tokens,
                    estimated_total_cost=total_cost,
                    output_preview=response.content[:500] if response else "",
                    error_type=error_type,
                )
            )
        run.status = "completed"
        run.completed_at = datetime.now(timezone.utc)
        self.db.commit()
        return self.get(run.id)

    def get(self, run_id) -> dict:
        run = self.db.query(models.ComparisonRun).filter_by(id=run_id).first()
        if not run:
            raise KeyError("comparison_not_found")
        results = (
            self.db.query(models.ComparisonResult)
            .filter_by(comparison_run_id=run_id)
            .order_by(models.ComparisonResult.created_at)
            .all()
        )
        return {
            "id": run.id,
            "prompt": run.prompt,
            "context_mode": run.context_mode,
            "status": run.status,
            "created_at": run.created_at,
            "completed_at": run.completed_at,
            "results": results,
        }
