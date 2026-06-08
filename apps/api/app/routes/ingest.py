from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.ingest import InferenceEventIn, IngestAccepted
from app.services.ingestion_service import IngestionService

router = APIRouter(prefix="/api/ingest", tags=["ingest"])


@router.post("/inference", response_model=IngestAccepted)
def ingest_inference(payload: InferenceEventIn, db: Session = Depends(get_db)):
    event = payload.model_dump()
    event_id = IngestionService(db).enqueue(event)
    return IngestAccepted(event_id=event_id)

