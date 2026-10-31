from __future__ import annotations

from datetime import date, datetime, timezone

from sqlalchemy import Boolean, Date, DateTime, Float, ForeignKey, Integer, LargeBinary, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


def _now() -> datetime:
    return datetime.now(timezone.utc)


class StudentDocument(Base):
    """An uploaded file kept in the mentor file (CAMPS profile, medical proof, certificate, ...)."""
    __tablename__ = "student_documents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    student_id: Mapped[int] = mapped_column(Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    batch_id: Mapped[int] = mapped_column(Integer, ForeignKey("batches.id", ondelete="CASCADE"), nullable=False, index=True)

    # "personal_details" | "medical_leave" | "certificate" | "condonation"
    category: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Leave period — used by medical leave records
    from_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    to_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    content_type: Mapped[str] = mapped_column(String(100), nullable=False)
    file_size: Mapped[int] = mapped_column(Integer, nullable=False)
    # Deferred so listings never pull the file bytes
    file_data: Mapped[bytes] = mapped_column(LargeBinary, nullable=False, deferred=True)

    uploaded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)


class CommunicationRecord(Base):
    """One entry of the mentor note: a communication with a student or parent."""
    __tablename__ = "communication_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    student_id: Mapped[int] = mapped_column(Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    batch_id: Mapped[int] = mapped_column(Integer, ForeignKey("batches.id", ondelete="CASCADE"), nullable=False, index=True)
    mentor_id: Mapped[int] = mapped_column(Integer, ForeignKey("mentors.id", ondelete="CASCADE"), nullable=False, index=True)

    communication_date: Mapped[date] = mapped_column(Date, nullable=False)
    contact_person: Mapped[str] = mapped_column(String(30), nullable=False)  # "Student" | "Father" | "Mother" | "Guardian"
    mode: Mapped[str | None] = mapped_column(String(30), nullable=True)      # "Phone" | "In Person" | "Message" | "Email"
    details: Mapped[str] = mapped_column(Text, nullable=False)
    feedback: Mapped[str | None] = mapped_column(Text, nullable=True)
    action_taken: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)


class ParentMeeting(Base):
    """Parent - Teachers Meeting form (parental communication report)."""
    __tablename__ = "parent_meetings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    student_id: Mapped[int] = mapped_column(Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    batch_id: Mapped[int] = mapped_column(Integer, ForeignKey("batches.id", ondelete="CASCADE"), nullable=False, index=True)
    mentor_id: Mapped[int] = mapped_column(Integer, ForeignKey("mentors.id", ondelete="CASCADE"), nullable=False, index=True)

    academic_year: Mapped[str] = mapped_column(String(20), nullable=False)
    meeting_date: Mapped[date] = mapped_column(Date, nullable=False)

    # Q3 – Q8
    student_contact: Mapped[str | None] = mapped_column(String(30), nullable=True)
    semester_year_branch: Mapped[str | None] = mapped_column(String(200), nullable=True)
    parent_name: Mapped[str] = mapped_column(String(150), nullable=False)
    relationship_with_student: Mapped[str] = mapped_column(String(20), nullable=False)  # "Father" | "Mother" | "Guardian"
    parent_contact: Mapped[str | None] = mapped_column(String(30), nullable=True)
    parent_address: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Q9 – Q11
    periodic_reports: Mapped[str | None] = mapped_column(String(200), nullable=True)
    interacts_regularly: Mapped[str | None] = mapped_column(String(200), nullable=True)
    satisfied_with_progress: Mapped[str | None] = mapped_column(String(200), nullable=True)

    # Q12 – Q18 discussion points
    academic_performance: Mapped[str | None] = mapped_column(Text, nullable=True)
    co_curricular: Mapped[str | None] = mapped_column(Text, nullable=True)
    attendance: Mapped[str | None] = mapped_column(Text, nullable=True)
    discipline: Mapped[str | None] = mapped_column(Text, nullable=True)
    placements: Mapped[str | None] = mapped_column(Text, nullable=True)
    concerns: Mapped[str | None] = mapped_column(Text, nullable=True)
    other_remarks: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Page 2 – action taken / follow-up
    action_plan: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)  # ["Remedial Classes", "Mentorship", ...]
    action_other: Mapped[str | None] = mapped_column(String(200), nullable=True)
    action_details: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)


class Achievement(Base):
    """One row of a student's achievements summary sheet."""
    __tablename__ = "achievements"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    student_id: Mapped[int] = mapped_column(Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    batch_id: Mapped[int] = mapped_column(Integer, ForeignKey("batches.id", ondelete="CASCADE"), nullable=False, index=True)

    academic_year: Mapped[str] = mapped_column(String(20), nullable=False)
    semester: Mapped[str | None] = mapped_column(String(50), nullable=True)
    category: Mapped[str] = mapped_column(String(80), nullable=False)   # "Technical Events" | "Sports Events" | ...
    event_name: Mapped[str] = mapped_column(String(300), nullable=False)
    level: Mapped[str] = mapped_column(String(30), nullable=False)      # "International" | "National" | "State"
    result: Mapped[str] = mapped_column(String(100), nullable=False)    # "Participation" | "Winner" | ...
    event_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    # Certificate, if uploaded
    document_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("student_documents.id", ondelete="SET NULL"), nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)


class Condonation(Base):
    """Application for condonation submitted by a student."""
    __tablename__ = "condonations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    student_id: Mapped[int] = mapped_column(Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    batch_id: Mapped[int] = mapped_column(Integer, ForeignKey("batches.id", ondelete="CASCADE"), nullable=False, index=True)

    exam_month_year: Mapped[str] = mapped_column(String(30), nullable=False)   # e.g. "Nov 2025"
    degree_branch: Mapped[str] = mapped_column(String(150), nullable=False)
    semester: Mapped[str] = mapped_column(String(50), nullable=False)
    attendance_percentage: Mapped[float] = mapped_column(Float, nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    recommended: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    # Approved form / medical certificate, if uploaded
    document_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("student_documents.id", ondelete="SET NULL"), nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)


class SemesterResult(Base):
    """Semester-wise GPA and arrear counts plus CGPA for one student."""
    __tablename__ = "semester_results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    student_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False, unique=True, index=True
    )
    batch_id: Mapped[int] = mapped_column(Integer, ForeignKey("batches.id", ondelete="CASCADE"), nullable=False, index=True)

    # Dicts keyed by semester number: {"1": "8.21", "2": "7.9"}
    gpa: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    arrears: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    cgpa: Mapped[str] = mapped_column(String(10), nullable=False, default="")


class RemedialAction(Base):
    """Remedial action for a student who failed an exam or is a slow learner."""
    __tablename__ = "remedial_actions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    exam_setup_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("exam_setups.id", ondelete="CASCADE"), nullable=False, index=True
    )
    student_id: Mapped[int] = mapped_column(Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)

    exam_type: Mapped[str] = mapped_column(String(10), nullable=False)  # "pt1" | "pt2" | "semester"
    subjects: Mapped[str | None] = mapped_column(String(300), nullable=True)
    action_taken: Mapped[str] = mapped_column(Text, nullable=False)
    impact: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
