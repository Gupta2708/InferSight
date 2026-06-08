from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import desc
from sqlalchemy.orm import Session, selectinload

from app.db import models


class ConversationService:
    def __init__(self, db: Session):
        self.db = db

    def create(self, title: str = "New Conversation") -> models.Conversation:
        try:
            safe_title = (title or "").strip() or "New Conversation"
            conversation = models.Conversation(title=safe_title)
            self.db.add(conversation)
            self.db.commit()
            self.db.refresh(conversation)
            return conversation
        except Exception:
            self.db.rollback()
            raise

    def list(self) -> list[models.Conversation]:
        return (
            self.db.query(models.Conversation)
            .order_by(
                desc(models.Conversation.last_message_at.isnot(None)),
                desc(models.Conversation.last_message_at),
                desc(models.Conversation.created_at),
            )
            .all()
        )

    def list_summaries(self) -> list[dict]:
        conversations = (
            self.db.query(models.Conversation)
            .options(selectinload(models.Conversation.messages))
            .order_by(
                desc(models.Conversation.last_message_at.isnot(None)),
                desc(models.Conversation.last_message_at),
                desc(models.Conversation.created_at),
            )
            .all()
        )
        summaries = []
        for conversation in conversations:
            user_messages = [message for message in conversation.messages if message.role == "user"]
            preview_source = user_messages[-1].content if user_messages else None
            preview = _preview(preview_source) if preview_source else None
            summaries.append(
                {
                    "id": conversation.id,
                    "title": conversation.title if conversation.messages else "Empty conversation",
                    "status": conversation.status,
                    "preview": preview,
                    "message_count": len(conversation.messages),
                    "created_at": conversation.created_at,
                    "updated_at": conversation.updated_at,
                    "last_message_at": conversation.last_message_at,
                }
            )
        return summaries

    def get(self, conversation_id: UUID) -> models.Conversation:
        conversation = (
            self.db.query(models.Conversation)
            .options(selectinload(models.Conversation.messages))
            .filter(models.Conversation.id == conversation_id)
            .first()
        )
        if not conversation:
            raise KeyError("conversation_not_found")
        return conversation

    def add_message(
        self,
        conversation_id: UUID,
        role: str,
        content: str,
        status: str = "completed",
        provider: str | None = None,
        model: str | None = None,
        trace_id: str | None = None,
    ) -> models.Message:
        conversation = self.get(conversation_id)
        now = datetime.now(timezone.utc)
        message = models.Message(
            conversation_id=conversation_id,
            role=role,
            content=content,
            status=status,
            provider=provider,
            model=model,
            trace_id=trace_id,
        )
        conversation.updated_at = now
        conversation.last_message_at = now
        self.db.add(message)
        try:
            self.db.commit()
            self.db.refresh(message)
            return message
        except Exception:
            self.db.rollback()
            raise

    def update_message(self, message_id: UUID, **updates) -> models.Message:
        message = self.db.query(models.Message).filter(models.Message.id == message_id).one()
        for key, value in updates.items():
            setattr(message, key, value)
        message.updated_at = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(message)
        return message

    def recent_context(self, conversation_id: UUID, limit: int = 8) -> list[models.Message]:
        rows = (
            self.db.query(models.Message)
            .filter(models.Message.conversation_id == conversation_id)
            .filter(models.Message.status == "completed")
            .order_by(desc(models.Message.created_at))
            .limit(limit)
            .all()
        )
        return list(reversed(rows))

    def cancel(self, conversation_id: UUID) -> None:
        conversation = self.get(conversation_id)
        conversation.status = "cancelled"
        conversation.updated_at = datetime.now(timezone.utc)
        active = (
            self.db.query(models.Message)
            .filter(models.Message.conversation_id == conversation_id)
            .filter(models.Message.status.in_(["pending", "streaming"]))
            .all()
        )
        for message in active:
            message.status = "cancelled"
            message.updated_at = datetime.now(timezone.utc)
        self.db.commit()

    def cleanup_empty(self) -> int:
        empty_conversations = (
            self.db.query(models.Conversation)
            .filter(~models.Conversation.messages.any())
            .all()
        )
        deleted = len(empty_conversations)
        for conversation in empty_conversations:
            self.db.delete(conversation)
        self.db.commit()
        return deleted

    def delete(self, conversation_id: UUID) -> None:
        conversation = self.get(conversation_id)
        self.db.delete(conversation)
        self.db.commit()


def _preview(content: str, limit: int = 96) -> str:
    compact = " ".join(content.split())
    return compact if len(compact) <= limit else f"{compact[: limit - 1]}..."
