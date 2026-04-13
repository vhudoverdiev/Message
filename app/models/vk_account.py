from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class VKAccount(Base):
    __tablename__ = 'vk_accounts'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    group_id: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default='active')
    access_token: Mapped[str] = mapped_column(Text, default='')
    long_poll_server: Mapped[str] = mapped_column(String(255), default='')
    long_poll_key: Mapped[str] = mapped_column(String(255), default='')
    long_poll_ts: Mapped[str] = mapped_column(String(100), default='')
    description: Mapped[str] = mapped_column(Text, default='')
    avatar_url: Mapped[str] = mapped_column(String(500), default='')
    owner_id: Mapped[int | None] = mapped_column(ForeignKey('users.id'), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    owner = relationship('User')
    messages = relationship('Message', back_populates='vk_account', cascade='all, delete-orphan')
