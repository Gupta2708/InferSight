from app.db import models
from app.db.session import SessionLocal


PROVIDER_CONFIGS = [
    ("mock", "mock-fast", True, True, 0.0, 0.0),
    ("mock", "mock-slow", True, True, 0.0, 0.0),
    ("mock", "mock-error", True, True, 0.0, 0.0),
    ("openai", "gpt-4.1-mini", False, True, 0.0004, 0.0016),
    ("gemini", "gemini-flash", False, True, 0.000075, 0.0003),
]


def seed_provider_configs() -> None:
    db = SessionLocal()
    try:
        for provider, model, enabled, streaming, input_cost, output_cost in PROVIDER_CONFIGS:
            exists = (
                db.query(models.ProviderConfig)
                .filter(models.ProviderConfig.provider == provider, models.ProviderConfig.model == model)
                .first()
            )
            if not exists:
                db.add(
                    models.ProviderConfig(
                        provider=provider,
                        model=model,
                        enabled=enabled,
                        supports_streaming=streaming,
                        input_cost_per_1k_tokens=input_cost,
                        output_cost_per_1k_tokens=output_cost,
                    )
                )
        db.commit()
    finally:
        db.close()
