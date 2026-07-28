from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.student import Batch
    from app.models.mentor import Mentor
    from app.models.student import Student


class ExamSetup(Base):
    """Defines subject codes for one semester's exams in a batch."""
    __tablename__ = "exam_setups"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    batch_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("batches.id", ondelete="CASCADE"), nullable=False, index=True
    )
    mentor_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("mentors.id", ondelete="CASCADE"), nullable=False, index=True
    )

    semester: Mapped[str] = mapped_column(String(50), nullable=False)       # e.g. "I Year - Semester I"
    academic_year: Mapped[str] = mapped_column(String(20), nullable=False)  # e.g. "2024-2025"
    subject_codes: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)  # ["CS1001", "MA1001", ...]

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    batch: Mapped[Batch] = relationship("Batch")
    mentor: Mapped[Mentor] = relationship("Mentor")
    marks_records: Mapped[list[StudentExamMarks]] = relationship(
        "StudentExamMarks", back_populates="exam_setup", cascade="all, delete-orphan"
    )


class StudentExamMarks(Base):
    """PT1, PT2 marks and semester grades for one student in one ExamSetup."""
    __tablename__ = "student_exam_marks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    exam_setup_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("exam_setups.id", ondelete="CASCADE"), nullable=False, index=True
    )
    student_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # Dicts keyed by subject code: {"CS1001": "25", "MA1001": "28"}
    pt1_marks:       Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    pt2_marks:       Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    semester_grades: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)

    exam_setup: Mapped[ExamSetup] = relationship("ExamSetup", back_populates="marks_records")
    student: Mapped[Student] = relationship("Student")
