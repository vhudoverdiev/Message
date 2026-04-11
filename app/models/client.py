from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class Client(Base):
    __tablename__ = 'clients'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    full_name: Mapped[str] = mapped_column(String(120), nullable=False)
    vk_link: Mapped[str] = mapped_column(String(255), nullable=False)
    vk_user_id: Mapped[str] = mapped_column(String(50), default='')
    tags: Mapped[str] = mapped_column(String(255), default='')
    status: Mapped[str] = mapped_column(String(30), default='new')
    notes: Mapped[str] = mapped_column(Text, default='')
    manager_id: Mapped[int | None] = mapped_column(ForeignKey('users.id'), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    manager = relationship('User')
    messages = relationship('Message', back_populates='client', cascade='all, delete-orphan')
