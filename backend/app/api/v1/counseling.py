from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_mentor, get_db
from app.models.counseling import CounselingSession
from app.models.mentor import Mentor
from app.models.student import Batch, Student
from app.schemas.counseling import CounselingCreate, CounselingResponse
from app.services.counseling_pdf_service import generate_counseling_pdf

router = APIRouter()


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


async def _get_session(session_id: int, student_id: int, db: AsyncSession) -> CounselingSession:
    result = await db.execute(
        select(CounselingSession).where(
            CounselingSession.id == session_id,
            CounselingSession.student_id == student_id,
        )
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Counseling session not found")
    return session


# ══════════════════════════════════════════════════════════════════════════════
# CRUD
# ══════════════════════════════════════════════════════════════════════════════

@router.post(
    "/batches/{batch_id}/students/{student_id}/counseling",
    response_model=CounselingResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Counseling"],
)
async def create_counseling_session(
    batch_id: int,
    student_id: int,
    payload: CounselingCreate,
    db: AsyncSession = Depends(get_db),
    mentor: Mentor = Depends(get_current_mentor),
):
    """Create a new counseling session for a student."""
    await _get_batch(batch_id, mentor.id, db)
    await _get_student(student_id, batch_id, db)

    session = CounselingSession(
        student_id=student_id,
        batch_id=batch_id,
        mentor_id=mentor.id,
        **payload.model_dump(),
    )
    db.add(session)
    await db.commit()
    await db.refresh(session)
    return session


@router.get(
    "/batches/{batch_id}/students/{student_id}/counseling",
    response_model=list[CounselingResponse],
    tags=["Counseling"],
)
async def list_counseling_sessions(
    batch_id: int,
    student_id: int,
    db: AsyncSession = Depends(get_db),
    mentor: Mentor = Depends(get_current_mentor),
):
    """List all counseling sessions for a student."""
    await _get_batch(batch_id, mentor.id, db)
    await _get_student(student_id, batch_id, db)

    result = await db.execute(
        select(CounselingSession)
        .where(
            CounselingSession.student_id == student_id,
            CounselingSession.batch_id == batch_id,
        )
        .order_by(CounselingSession.counseling_date.desc())
    )
    return result.scalars().all()


@router.get(
    "/batches/{batch_id}/students/{student_id}/counseling/{session_id}",
    response_model=CounselingResponse,
    tags=["Counseling"],
)
async def get_counseling_session(
    batch_id: int,
    student_id: int,
    session_id: int,
    db: AsyncSession = Depends(get_db),
    mentor: Mentor = Depends(get_current_mentor),
):
    """Get a single counseling session."""
    await _get_batch(batch_id, mentor.id, db)
    await _get_student(student_id, batch_id, db)
    return await _get_session(session_id, student_id, db)


@router.delete(
    "/batches/{batch_id}/students/{student_id}/counseling/{session_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["Counseling"],
)
async def delete_counseling_session(
    batch_id: int,
    student_id: int,
    session_id: int,
    db: AsyncSession = Depends(get_db),
    mentor: Mentor = Depends(get_current_mentor),
):
    """Delete a counseling session."""
    await _get_batch(batch_id, mentor.id, db)
    await _get_student(student_id, batch_id, db)
    session = await _get_session(session_id, student_id, db)
    await db.delete(session)
    await db.commit()


# ══════════════════════════════════════════════════════════════════════════════
# PDF export
# ══════════════════════════════════════════════════════════════════════════════

@router.get(
    "/batches/{batch_id}/students/{student_id}/counseling/{session_id}/pdf",
    response_class=Response,
    tags=["Counseling"],
)
async def export_counseling_pdf(
    batch_id: int,
    student_id: int,
    session_id: int,
    db: AsyncSession = Depends(get_db),
    mentor: Mentor = Depends(get_current_mentor),
):
    """Download the counseling form as a filled PDF."""
    await _get_batch(batch_id, mentor.id, db)
    student = await _get_student(student_id, batch_id, db)
    s = await _get_session(session_id, student_id, db)

    pdf = generate_counseling_pdf(
        mentor_name=mentor.name,
        student_name=student.name,
        register_number=student.register_number,
        academic_year=s.academic_year,
        counseling_date=s.counseling_date,
        reason_initiated_by=s.reason_initiated_by,
        reason_details=s.reason_details,
        attendance_status=s.attendance_status,
        attendance_other=s.attendance_other,
        discipline_status=s.discipline_status,
        discipline_other=s.discipline_other,
        attitude_status=s.attitude_status,
        attitude_other=s.attitude_other,
        difficulty_meeting_demands=s.difficulty_meeting_demands,
        difficulty_explanation=s.difficulty_explanation,
        corrective_action_needed=s.corrective_action_needed,
        corrective_action_explanation=s.corrective_action_explanation,
        next_session_needed=s.next_session_needed,
        next_session_explanation=s.next_session_explanation,
    )

    filename = f"counseling_{student.register_number}_{s.counseling_date}.pdf"
    return Response(
        content=pdf,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
