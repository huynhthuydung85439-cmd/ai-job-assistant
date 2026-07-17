from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import JSON, CheckConstraint, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.resume import Resume


class AnalysisRecord(Base):
    __tablename__ = "analysis_records"
    __table_args__ = (
        CheckConstraint("score >= 0 AND score <= 100", name="ck_analysis_score_range"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    resume_id: Mapped[int] = mapped_column(
        ForeignKey("resumes.id", ondelete="CASCADE"), index=True
    )
    score: Mapped[int]
    result_json: Mapped[dict[str, Any]] = mapped_column(JSON)
    create_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    resume: Mapped[Resume] = relationship(back_populates="analysis_records")
