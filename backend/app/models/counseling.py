from __future__ import annotations

from datetime import date, datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.student import Batch, Student
    from app.models.mentor import Mentor


class CounselingSession(Base):
    """One counseling session for one student, filled by a mentor."""
    __tablename__ = "counseling_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    student_id: Mapped[int] = mapped_column(Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    batch_id: Mapped[int] = mapped_column(Integer, ForeignKey("batches.id", ondelete="CASCADE"), nullable=False, index=True)
    mentor_id: Mapped[int] = mapped_column(Integer, ForeignKey("mentors.id", ondelete="CASCADE"), nullable=False, index=True)

    counseling_date: Mapped[date] = mapped_column(Date, nullable=False)
    academic_year: Mapped[str] = mapped_column(String(20), nullable=False)  # e.g. "2024-2025"

    # Q1 – Reason for counseling
    reason_initiated_by: Mapped[str] = mapped_column(String(50), nullable=False)  # "Student Initiated" | "Institute Initiated"
    reason_details: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Q2a – Attendance
    attendance_status: Mapped[str] = mapped_column(String(50), nullable=False)  # "Punctual" | "Occasionally Tardy" | "Habitually late" | "Other"
    attendance_other: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Q2b – Discipline
    discipline_status: Mapped[str] = mapped_column(String(30), nullable=False)  # "Good" | "Unkept" | "Other"
    discipline_other: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Q2c – Attitude
    attitude_status: Mapped[str] = mapped_column(String(50), nullable=False)  # "Willing, Eager, Pleasant" | "Other"
    attitude_other: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Q3 – Difficulty meeting demands
    difficulty_meeting_demands: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    difficulty_explanation: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Q4 – Corrective action
    corrective_action_needed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    corrective_action_explanation: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Q5 – Next counseling session
    next_session_needed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    next_session_explanation: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    student: Mapped[Student] = relationship("Student")
    batch: Mapped[Batch] = relationship("Batch")
    mentor: Mapped[Mentor] = relationship("Mentor")
