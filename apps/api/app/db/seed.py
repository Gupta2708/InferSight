from app.db import models
from app.db.session import SessionLocal
from app.services.provider_catalog import DEFAULT_PROVIDER_CONFIGS, LEGACY_MODEL_ALIASES, normalize_model_alias


def seed_provider_configs() -> None:
    db = SessionLocal()
    try:
        for provider, legacy_model in LEGACY_MODEL_ALIASES:
            current_model = normalize_model_alias(provider, legacy_model)
            legacy_row = (
                db.query(models.ProviderConfig)
                .filter(
                    models.ProviderConfig.provider == provider,
                    models.ProviderConfig.model == legacy_model,
                )
                .first()
            )
            current_row = (
                db.query(models.ProviderConfig)
                .filter(
                    models.ProviderConfig.provider == provider,
                    models.ProviderConfig.model == current_model,
                )
                .first()
            )
            if legacy_row and not current_row:
                legacy_row.model = current_model
                legacy_row.input_cost_per_1k_tokens = next(
                    item["input_cost_per_1k_tokens"]
                    for item in DEFAULT_PROVIDER_CONFIGS
                    if item["provider"] == provider and item["model"] == current_model
                )
                legacy_row.output_cost_per_1k_tokens = next(
                    item["output_cost_per_1k_tokens"]
                    for item in DEFAULT_PROVIDER_CONFIGS
                    if item["provider"] == provider and item["model"] == current_model
                )
            elif legacy_row and current_row:
                db.delete(legacy_row)

        db.flush()

        existing_rows = {
            (row.provider, row.model): row
            for row in db.query(models.ProviderConfig).all()
        }

        for config in DEFAULT_PROVIDER_CONFIGS:
            row = existing_rows.get((config["provider"], config["model"]))
            if not row:
                row = models.ProviderConfig(
                    provider=config["provider"],
                    model=config["model"],
                )
                db.add(row)
                existing_rows[(config["provider"], config["model"])] = row

            row.enabled = config["enabled"]
            row.supports_streaming = config["supports_streaming"]
            row.input_cost_per_1k_tokens = config["input_cost_per_1k_tokens"]
            row.output_cost_per_1k_tokens = config["output_cost_per_1k_tokens"]
        db.commit()
    finally:
        db.close()
