from sqlalchemy import case, func
from sqlalchemy.orm import Session

from app.db import models


class DashboardService:
    def __init__(self, db: Session):
        self.db = db

    def summary(self) -> dict:
        logs = self.db.query(models.InferenceLog).all()
        total = len(logs)
        latencies = sorted([log.latency_ms or 0 for log in logs])
        errors = len([log for log in logs if log.status == "error"])
        cancelled = len([log for log in logs if log.status == "cancelled"])
        return {
            "total_requests": total,
            "average_latency_ms": round(sum(latencies) / total, 2) if total else 0,
            "p50_latency_ms": percentile(latencies, 50),
            "p95_latency_ms": percentile(latencies, 95),
            "error_rate": round(errors / total, 4) if total else 0,
            "cancellation_rate": round(cancelled / total, 4) if total else 0,
            "total_tokens": sum(log.total_tokens for log in logs),
            "estimated_cost": round(sum(log.estimated_total_cost for log in logs), 8),
        }

    def time_series(self, metric: str) -> list[dict]:
        column = {
            "latency": func.avg(models.InferenceLog.latency_ms),
            "errors": func.sum(case((models.InferenceLog.status == "error", 1), else_=0)),
            "tokens": func.sum(models.InferenceLog.total_tokens),
            "cost": func.sum(models.InferenceLog.estimated_total_cost),
        }.get(metric, func.count(models.InferenceLog.id))
        rows = (
            self.db.query(func.date(models.InferenceLog.created_at).label("bucket"), column.label("value"))
            .group_by("bucket")
            .order_by("bucket")
            .all()
        )
        return [{"bucket": str(bucket), "value": float(value or 0)} for bucket, value in rows]

    def providers(self) -> list[dict]:
        rows = (
            self.db.query(
                models.InferenceLog.provider,
                models.InferenceLog.model,
                func.count(models.InferenceLog.id),
                func.avg(models.InferenceLog.latency_ms),
                func.sum(models.InferenceLog.estimated_total_cost),
            )
            .group_by(models.InferenceLog.provider, models.InferenceLog.model)
            .all()
        )
        return [
            {
                "provider": provider,
                "model": model,
                "label": f"{provider}/{model}",
                "requests": count,
                "average_latency_ms": round(float(latency or 0), 2),
                "estimated_cost": round(float(cost or 0), 8),
            }
            for provider, model, count, latency, cost in rows
        ]


def percentile(values: list[int], pct: int) -> float:
    if not values:
        return 0
    index = min(len(values) - 1, round((pct / 100) * (len(values) - 1)))
    return float(values[index])
