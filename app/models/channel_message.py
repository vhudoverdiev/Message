from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class ChannelMessage(Base):
    __tablename__ = 'channel_messages'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    channel: Mapped[str] = mapped_column(String(20), index=True)  # gmail|telegram|vk
    account_id: Mapped[int] = mapped_column(Integer, index=True)
    external_message_id: Mapped[str] = mapped_column(String(120), index=True)
    conversation_id: Mapped[str] = mapped_column(String(120), default='', index=True)
    sender_name: Mapped[str] = mapped_column(String(255), default='')
    subject: Mapped[str] = mapped_column(String(255), default='')
    body_preview: Mapped[str] = mapped_column(Text, default='')
    body_full: Mapped[str] = mapped_column(Text, default='')
    status: Mapped[str] = mapped_column(String(20), default='new')
    is_read: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
