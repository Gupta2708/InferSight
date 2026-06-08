from uuid import UUID

import logging

from fastapi import APIRouter, Body, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.conversations import (
    ConversationCreate,
    ConversationOut,
    ConversationSummary,
    MessageCreate,
    MessageOut,
    StreamMessageCreate,
)
from app.services.chat_service import ChatService
from app.services.conversation_service import ConversationService

router = APIRouter(prefix="/api/conversations", tags=["conversations"])
logger = logging.getLogger(__name__)


@router.post("", response_model=ConversationOut)
def create_conversation(
    payload: ConversationCreate | None = Body(default=None), db: Session = Depends(get_db)
):
    try:
        return ConversationService(db).create((payload or ConversationCreate()).title)
    except Exception:
        logger.exception("Failed to create conversation")
        raise HTTPException(status_code=500, detail="Failed to create conversation")


@router.get("", response_model=list[ConversationSummary])
def list_conversations(db: Session = Depends(get_db)):
    return ConversationService(db).list_summaries()


@router.post("/cleanup-empty")
def cleanup_empty_conversations(db: Session = Depends(get_db)):
    deleted = ConversationService(db).cleanup_empty()
    return {"deleted": deleted}


@router.get("/{conversation_id}", response_model=ConversationOut)
def get_conversation(conversation_id: UUID, db: Session = Depends(get_db)):
    try:
        return ConversationService(db).get(conversation_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Conversation not found")


@router.delete("/{conversation_id}")
def delete_conversation(conversation_id: UUID, db: Session = Depends(get_db)):
    try:
        ConversationService(db).delete(conversation_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return {"status": "deleted"}


@router.post("/{conversation_id}/messages", response_model=MessageOut)
def add_message(conversation_id: UUID, payload: MessageCreate, db: Session = Depends(get_db)):
    try:
        return ConversationService(db).add_message(
            conversation_id, "user", payload.content, provider=payload.provider, model=payload.model
        )
    except KeyError:
        raise HTTPException(status_code=404, detail="Conversation not found")


@router.post("/{conversation_id}/messages/stream")
async def stream_message(conversation_id: UUID, payload: StreamMessageCreate, db: Session = Depends(get_db)):
    service = ChatService(db)
    stream = service.stream_message(
        conversation_id,
        payload.content,
        payload.provider,
        payload.model,
        payload.temperature,
        payload.max_tokens,
        payload.mock_scenario,
    )
    return StreamingResponse(stream, media_type="application/x-ndjson")


@router.post("/{conversation_id}/cancel")
def cancel_conversation(conversation_id: UUID, db: Session = Depends(get_db)):
    try:
        ChatService(db).cancel(conversation_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return {"status": "cancelled"}
