from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.dependencies import get_current_mentor, get_db
from app.models.mentor import Mentor
from app.models.student import Batch, Student
from app.schemas.student import (
    BatchCreate,
    BatchResponse,
    BatchUpdate,
    BatchWithStudents,
    StudentCreate,
    StudentResponse,
    StudentUpdate,
)
from app.services.pdf_service import generate_student_list_pdf

router = APIRouter()


# ══════════════════════════════════════════════════════════════════════════════
# Batch CRUD
# ══════════════════════════════════════════════════════════════════════════════

@router.post("/", response_model=BatchResponse, status_code=status.HTTP_201_CREATED)
async def create_batch(
    payload: BatchCreate,
    db: AsyncSession = Depends(get_db),
    mentor: Mentor = Depends(get_current_mentor),
):
    """Create a new student batch for the authenticated mentor."""
    batch = Batch(
        department=payload.department,
        batch_year=payload.batch_year,
        mentor_id=mentor.id,
    )
    db.add(batch)
    await db.commit()
    await db.refresh(batch)
    return batch


@router.get("/", response_model=list[BatchResponse])
async def list_batches(
    db: AsyncSession = Depends(get_db),
    mentor: Mentor = Depends(get_current_mentor),
):
    """List all batches belonging to the authenticated mentor."""
    result = await db.execute(
        select(Batch).where(Batch.mentor_id == mentor.id).order_by(Batch.created_at.desc())
    )
    return result.scalars().all()


@router.get("/{batch_id}", response_model=BatchWithStudents)
async def get_batch(
    batch_id: int,
    db: AsyncSession = Depends(get_db),
    mentor: Mentor = Depends(get_current_mentor),
):
    """Get a batch (with its students) by ID."""
    result = await db.execute(
        select(Batch)
        .where(Batch.id == batch_id, Batch.mentor_id == mentor.id)
        .options(selectinload(Batch.students))
    )
    batch = result.scalar_one_or_none()
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")
    return batch


@router.put("/{batch_id}", response_model=BatchResponse)
async def update_batch(
    batch_id: int,
    payload: BatchUpdate,
    db: AsyncSession = Depends(get_db),
    mentor: Mentor = Depends(get_current_mentor),
):
    """Update batch department or year."""
    result = await db.execute(
        select(Batch).where(Batch.id == batch_id, Batch.mentor_id == mentor.id)
    )
    batch = result.scalar_one_or_none()
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")

    if payload.department is not None:
        batch.department = payload.department
    if payload.batch_year is not None:
        batch.batch_year = payload.batch_year

    await db.commit()
    await db.refresh(batch)
    return batch


@router.delete("/{batch_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_batch(
    batch_id: int,
    db: AsyncSession = Depends(get_db),
    mentor: Mentor = Depends(get_current_mentor),
):
    """Delete a batch and all its students."""
    result = await db.execute(
        select(Batch).where(Batch.id == batch_id, Batch.mentor_id == mentor.id)
    )
    batch = result.scalar_one_or_none()
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")
    await db.delete(batch)
    await db.commit()


# ══════════════════════════════════════════════════════════════════════════════
# Student CRUD (nested under a batch)
# ══════════════════════════════════════════════════════════════════════════════

async def _get_batch_or_404(batch_id: int, mentor_id: int, db: AsyncSession) -> Batch:
    result = await db.execute(
        select(Batch).where(Batch.id == batch_id, Batch.mentor_id == mentor_id)
    )
    batch = result.scalar_one_or_none()
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")
    return batch


@router.post("/{batch_id}/students", response_model=StudentResponse, status_code=status.HTTP_201_CREATED)
async def add_student(
    batch_id: int,
    payload: StudentCreate,
    db: AsyncSession = Depends(get_db),
    mentor: Mentor = Depends(get_current_mentor),
):
    """Add a student to a batch."""
    await _get_batch_or_404(batch_id, mentor.id, db)
    student = Student(
        register_number=payload.register_number,
        name=payload.name,
        batch_id=batch_id,
    )
    db.add(student)
    await db.commit()
    await db.refresh(student)
    return student


@router.get("/{batch_id}/students", response_model=list[StudentResponse])
async def list_students(
    batch_id: int,
    db: AsyncSession = Depends(get_db),
    mentor: Mentor = Depends(get_current_mentor),
):
    """List all students in a batch."""
    await _get_batch_or_404(batch_id, mentor.id, db)
    result = await db.execute(
        select(Student).where(Student.batch_id == batch_id).order_by(Student.name)
    )
    return result.scalars().all()


@router.get("/{batch_id}/students/{student_id}", response_model=StudentResponse)
async def get_student(
    batch_id: int,
    student_id: int,
    db: AsyncSession = Depends(get_db),
    mentor: Mentor = Depends(get_current_mentor),
):
    """Get a single student by ID."""
    await _get_batch_or_404(batch_id, mentor.id, db)
    result = await db.execute(
        select(Student).where(Student.id == student_id, Student.batch_id == batch_id)
    )
    student = result.scalar_one_or_none()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    return student


@router.put("/{batch_id}/students/{student_id}", response_model=StudentResponse)
async def update_student(
    batch_id: int,
    student_id: int,
    payload: StudentUpdate,
    db: AsyncSession = Depends(get_db),
    mentor: Mentor = Depends(get_current_mentor),
):
    """Update a student's name or register number."""
    await _get_batch_or_404(batch_id, mentor.id, db)
    result = await db.execute(
        select(Student).where(Student.id == student_id, Student.batch_id == batch_id)
    )
    student = result.scalar_one_or_none()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    if payload.name is not None:
        student.name = payload.name
    if payload.register_number is not None:
        student.register_number = payload.register_number

    await db.commit()
    await db.refresh(student)
    return student


@router.delete("/{batch_id}/students/{student_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_student(
    batch_id: int,
    student_id: int,
    db: AsyncSession = Depends(get_db),
    mentor: Mentor = Depends(get_current_mentor),
):
    """Remove a student from a batch."""
    await _get_batch_or_404(batch_id, mentor.id, db)
    result = await db.execute(
        select(Student).where(Student.id == student_id, Student.batch_id == batch_id)
    )
    student = result.scalar_one_or_none()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    await db.delete(student)
    await db.commit()


# ══════════════════════════════════════════════════════════════════════════════
# PDF export
# ══════════════════════════════════════════════════════════════════════════════

@router.get("/{batch_id}/export/pdf", response_class=Response)
async def export_pdf(
    batch_id: int,
    db: AsyncSession = Depends(get_db),
    mentor: Mentor = Depends(get_current_mentor),
):
    """Download a PDF of the student name list for this batch."""
    result = await db.execute(
        select(Batch)
        .where(Batch.id == batch_id, Batch.mentor_id == mentor.id)
        .options(selectinload(Batch.students))
    )
    batch = result.scalar_one_or_none()
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")

    students = [
        {"register_number": s.register_number, "name": s.name}
        for s in sorted(batch.students, key=lambda s: s.name)
    ]

    pdf_bytes = generate_student_list_pdf(
        department=batch.department,
        batch_year=batch.batch_year,
        mentor_name=mentor.name,
        students=students,
    )

    filename = f"student_list_{batch.department.replace(' ', '_')}_{batch.batch_year}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
