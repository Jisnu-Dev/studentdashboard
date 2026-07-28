from __future__ import annotations

from datetime import date, datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import Date, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.student import Batch
    from app.models.mentor import Mentor


class MentorMeeting(Base):
    """One mentor-mentee meeting for a batch."""
    __tablename__ = "mentor_meetings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    batch_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("batches.id", ondelete="CASCADE"), nullable=False, index=True
    )
    mentor_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("mentors.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # Meeting details
    meeting_number: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    meeting_date: Mapped[date] = mapped_column(Date, nullable=False)
    meeting_time: Mapped[str] = mapped_column(String(20), nullable=False)   # e.g. "3.30 PM"
    location: Mapped[str] = mapped_column(String(200), nullable=False)
    semester: Mapped[str] = mapped_column(String(50), nullable=False)       # e.g. "I Year - Semester I"
    academic_year: Mapped[str | None] = mapped_column(String(20), nullable=True)  # e.g. "2025-2026"
    year_of_study: Mapped[str | None] = mapped_column(String(20), nullable=True)  # e.g. "I Year"

    # Agenda items stored as a JSON array of strings
    agenda_items: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)

    # Minutes of meeting (filled after the meeting, optional)
    minutes_text: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    batch: Mapped[Batch] = relationship("Batch")
    mentor: Mapped[Mentor] = relationship("Mentor")
