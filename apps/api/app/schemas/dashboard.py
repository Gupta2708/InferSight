from pydantic import BaseModel


class SummaryOut(BaseModel):
    total_requests: int
    average_latency_ms: float
    p50_latency_ms: float
    p95_latency_ms: float
    error_rate: float
    cancellation_rate: float
    total_tokens: int
    estimated_cost: float

