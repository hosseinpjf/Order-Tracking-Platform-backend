from sqlalchemy import Column, String, DateTime, ForeignKey, Boolean, Index
from datetime import datetime, timezone
import uuid
from app.db.base import Base

class Message(Base):
    __tablename__ = "messages"

    id = Column(String, primary_key=True, default=lambda: uuid.uuid4().hex)

    sender_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    receiver_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)

    content = Column(String(5000), nullable=False)

    reply_to_message_id = Column(String, ForeignKey("messages.id"), nullable=True, index=True)

    is_read = Column(Boolean, default=False, nullable=False)
    is_delivered = Column(Boolean, default=False, nullable=False)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    __table_args__ = (Index("ix_messages_conversation", "sender_id", "receiver_id", "created_at"),)