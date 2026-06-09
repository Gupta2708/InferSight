from pydantic import BaseModel


class ProviderModelOut(BaseModel):
    provider: str
    model: str
    enabled: bool = True
    key_configured: bool = True
    available: bool = True
    status_label: str = "enabled"
    supports_streaming: bool = True
    input_cost_per_1k_tokens: float | None = None
    output_cost_per_1k_tokens: float | None = None


class ProviderListOut(BaseModel):
    providers: list[str]
    models: list[ProviderModelOut]
    mock_mode: bool
