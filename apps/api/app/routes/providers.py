from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.config import get_settings
from app.db import models
from app.db.session import get_db
from app.llm.gateway import LLMGateway
from app.schemas.providers import ProviderListOut, ProviderModelOut

router = APIRouter(prefix="/api/providers", tags=["providers"])


def _models_from_db(db: Session) -> list[ProviderModelOut]:
    rows = (
        db.query(models.ProviderConfig)
        .order_by(models.ProviderConfig.provider, models.ProviderConfig.model)
        .all()
    )
    return [
        ProviderModelOut(
            provider=row.provider,
            model=row.model,
            enabled=row.enabled,
            supports_streaming=row.supports_streaming,
            input_cost_per_1k_tokens=row.input_cost_per_1k_tokens,
            output_cost_per_1k_tokens=row.output_cost_per_1k_tokens,
        )
        for row in rows
    ]


@router.get("", response_model=ProviderListOut)
def list_providers(db: Session = Depends(get_db)):
    models = _models_from_db(db) or [ProviderModelOut(**item) for item in LLMGateway().available_models()]
    return ProviderListOut(
        providers=sorted({item.provider for item in models}),
        models=models,
        mock_mode=get_settings().llm_mock_mode,
    )


@router.get("/models", response_model=list[ProviderModelOut])
def list_models(db: Session = Depends(get_db)):
    return _models_from_db(db) or [ProviderModelOut(**item) for item in LLMGateway().available_models()]
