from datetime import date

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from fastapi.responses import Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import undefer

from app.core.dependencies import get_current_mentor, get_db
from app.models.mentor import Mentor
from app.models.mentor_file import StudentDocument
from app.models.student import Batch, Student
from app.schemas.mentor_file import DOCUMENT_CATEGORIES, DocumentResponse

router = APIRouter()

MAX_FILE_SIZE = 10 * 1024 * 1024   # 10 MB
ALLOWED_TYPES = {
    "application/pdf",
    "image/jpeg",
    "image/png",
    "image/webp",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}


# ── Guards ─────────────────────────────────────────────────────────────────────

async def _get_batch(batch_id: int, mentor_id: int, db: AsyncSession) -> Batch:
    result = await db.execute(
        select(Batch).where(Batch.id == batch_id, Batch.mentor_id == mentor_id)
    )
    batch = result.scalar_one_or_none()
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")
    return batch


async def _get_student(student_id: int, batch_id: int, db: AsyncSession) -> Student:
    result = await db.execute(
        select(Student).where(Student.id == student_id, Student.batch_id == batch_id)
    )
    student = result.scalar_one_or_none()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    return student


# ══════════════════════════════════════════════════════════════════════════════
# Upload / list / download / delete
# ══════════════════════════════════════════════════════════════════════════════

@router.post(
    "/batches/{batch_id}/students/{student_id}/documents",
    response_model=DocumentResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Documents"],
)
async def upload_document(
    batch_id: int,
    student_id: int,
    category: str = Form(...),
    title: str = Form(...),
    notes: str | None = Form(None),
    from_date: date | None = Form(None),
    to_date: date | None = Form(None),
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    mentor: Mentor = Depends(get_current_mentor),
):
    """Upload a file (PDF / image / Word, max 10 MB) into a student's mentor file."""
    await _get_batch(batch_id, mentor.id, db)
    student = await _get_student(student_id, batch_id, db)

    if category not in DOCUMENT_CATEGORIES:
        raise HTTPException(status_code=422, detail="Unknown document category")
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(status_code=415, detail="Only PDF, image or Word files are allowed")
    if from_date and to_date and to_date < from_date:
        raise HTTPException(status_code=422, detail="'To' date cannot be before 'From' date")

    data = await file.read(MAX_FILE_SIZE + 1)
    if not data:
        raise HTTPException(status_code=422, detail="The uploaded file is empty")
    if len(data) > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail="File is larger than 10 MB")

    doc = StudentDocument(
        student_id=student_id,
        batch_id=batch_id,
        category=category,
        title=title,
        notes=notes or None,
        from_date=from_date,
        to_date=to_date,
        file_name=file.filename or "document",
        content_type=file.content_type,
        file_size=len(data),
        file_data=data,
    )
    db.add(doc)
    await db.commit()
    await db.refresh(doc)
    return DocumentResponse.model_validate(doc).model_copy(
        update={"student_name": student.name, "register_number": student.register_number}
    )


@router.get(
    "/batches/{batch_id}/documents",
    response_model=list[DocumentResponse],
    tags=["Documents"],
)
async def list_documents(
    batch_id: int,
    category: str | None = None,
    student_id: int | None = None,
    db: AsyncSession = Depends(get_db),
    mentor: Mentor = Depends(get_current_mentor),
):
    """List uploaded documents for a batch, optionally filtered by category / student."""
    await _get_batch(batch_id, mentor.id, db)

    query = (
        select(StudentDocument, Student)
        .join(Student, StudentDocument.student_id == Student.id)
        .where(StudentDocument.batch_id == batch_id)
        .order_by(Student.name, StudentDocument.uploaded_at.desc())
    )
    if category:
        query = query.where(StudentDocument.category == category)
    if student_id:
        query = query.where(StudentDocument.student_id == student_id)

    result = await db.execute(query)
    return [
        DocumentResponse.model_validate(d).model_copy(
            update={"student_name": s.name, "register_number": s.register_number}
        )
        for d, s in result.all()
    ]


@router.get(
    "/batches/{batch_id}/documents/{document_id}/download",
    response_class=Response,
    tags=["Documents"],
)
async def download_document(
    batch_id: int,
    document_id: int,
    db: AsyncSession = Depends(get_db),
    mentor: Mentor = Depends(get_current_mentor),
):
    """Download the original uploaded file."""
    await _get_batch(batch_id, mentor.id, db)
    result = await db.execute(
        select(StudentDocument)
        .where(StudentDocument.id == document_id, StudentDocument.batch_id == batch_id)
        .options(undefer(StudentDocument.file_data))
    )
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    filename = "".join(ch for ch in doc.file_name if ch.isascii() and ch not in '"\\\r\n') or "document"
    return Response(
        content=doc.file_data,
        media_type=doc.content_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.delete(
    "/batches/{batch_id}/documents/{document_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["Documents"],
)
async def delete_document(
    batch_id: int,
    document_id: int,
    db: AsyncSession = Depends(get_db),
    mentor: Mentor = Depends(get_current_mentor),
):
    await _get_batch(batch_id, mentor.id, db)
    result = await db.execute(
        select(StudentDocument).where(
            StudentDocument.id == document_id, StudentDocument.batch_id == batch_id
        )
    )
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    await db.delete(doc)
    await db.commit()
