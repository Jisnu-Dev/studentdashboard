from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Batch(Base):
    """A group of students under one mentor for a specific department and year."""
    __tablename__ = "batches"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    department: Mapped[str] = mapped_column(String(150), nullable=False)
    # e.g. "2023-2027"
    batch_year: Mapped[str] = mapped_column(String(20), nullable=False)
    mentor_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("mentors.id", ondelete="CASCADE"), nullable=False, index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )

    # relationships
    mentor: Mapped["Mentor"] = relationship("Mentor", back_populates="batches")  # noqa: F821
    students: Mapped[list["Student"]] = relationship(
        "Student", back_populates="batch", cascade="all, delete-orphan", order_by="Student.name"
    )


class Student(Base):
    """A student belonging to a batch."""
    __tablename__ = "students"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    register_number: Mapped[str] = mapped_column(String(30), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    batch_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("batches.id", ondelete="CASCADE"), nullable=False, index=True
    )

    batch: Mapped["Batch"] = relationship("Batch", back_populates="students")
