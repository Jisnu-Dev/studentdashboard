from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Boolean, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.meeting import MentorMeeting
    from app.models.student import Student


class MeetingAttendance(Base):
    """Records a single student's attendance + discussion notes for one meeting."""
    __tablename__ = "meeting_attendances"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    meeting_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("mentor_meetings.id", ondelete="CASCADE"), nullable=False, index=True
    )
    student_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True
    )

    is_present: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    # Numbered lists stored as JSON arrays of strings
    points_discussed: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    action_planned: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)

    # Relationships
    meeting: Mapped[MentorMeeting] = relationship("MentorMeeting")
    student: Mapped[Student] = relationship("Student")
