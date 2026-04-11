from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class Message(Base):
    __tablename__ = 'messages'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    vk_account_id: Mapped[int] = mapped_column(ForeignKey('vk_accounts.id'))
    client_id: Mapped[int | None] = mapped_column(ForeignKey('clients.id'), nullable=True)
    dialog_id: Mapped[str] = mapped_column(String(80), nullable=False)
    direction: Mapped[str] = mapped_column(String(10), default='in')
    text: Mapped[str] = mapped_column(Text, nullable=False)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False)
    sent_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    vk_account = relationship('VKAccount', back_populates='messages')
    client = relationship('Client', back_populates='messages')
