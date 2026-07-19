from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import JSON, DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.mysql import LONGTEXT
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.user import User


class ChatHistory(Base):
    __tablename__ = "chat_histories"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    question: Mapped[str] = mapped_column(Text().with_variant(LONGTEXT(), "mysql"))
    answer: Mapped[str] = mapped_column(Text().with_variant(LONGTEXT(), "mysql"))
    chat_type: Mapped[str] = mapped_column(
        String(16), default="chat", server_default="chat", index=True
    )
    sources_json: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    user: Mapped[User] = relationship(back_populates="chat_histories")
