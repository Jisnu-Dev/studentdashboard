from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_mentor, get_db
from app.models.exam import ExamSetup, StudentExamMarks
from app.models.mentor import Mentor
from app.models.student import Batch, Student
from app.schemas.exam import (
    BulkMarksPayload,
    ExamSetupCreate,
    ExamSetupResponse,
    ExamSetupUpdate,
    StudentMarksResponse,
)
from app.services.exam_pdf_service import generate_pt_marks_pdf, generate_semester_pdf

router = APIRouter()


# ── Guards ─────────────────────────────────────────────────────────────────────

async def _get_batch(batch_id: int, mentor_id: int, db: AsyncSession) -> Batch:
    result = await db.execute(
        select(Batch).where(Batch.id == batch_id, Batch.mentor_id == mentor_id)
    )
    b = result.scalar_one_or_none()
    if not b:
        raise HTTPException(status_code=404, detail="Batch not found")
    return b


async def _get_setup(exam_id: int, batch_id: int, db: AsyncSession) -> ExamSetup:
    result = await db.execute(
        select(ExamSetup).where(ExamSetup.id == exam_id, ExamSetup.batch_id == batch_id)
    )
    s = result.scalar_one_or_none()
    if not s:
        raise HTTPException(status_code=404, detail="Exam setup not found")
    return s


# ══════════════════════════════════════════════════════════════════════════════
# ExamSetup CRUD
# ══════════════════════════════════════════════════════════════════════════════

@router.post(
    "/batches/{batch_id}/exams",
    response_model=ExamSetupResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Exams"],
)
async def create_exam_setup(
    batch_id: int,
    payload: ExamSetupCreate,
    db: AsyncSession = Depends(get_db),
    mentor: Mentor = Depends(get_current_mentor),
):
    await _get_batch(batch_id, mentor.id, db)
    setup = ExamSetup(batch_id=batch_id, mentor_id=mentor.id, **payload.model_dump())
    db.add(setup)
    await db.commit()
    await db.refresh(setup)
    return setup


@router.get(
    "/batches/{batch_id}/exams",
    response_model=list[ExamSetupResponse],
    tags=["Exams"],
)
async def list_exam_setups(
    batch_id: int,
    db: AsyncSession = Depends(get_db),
    mentor: Mentor = Depends(get_current_mentor),
):
    await _get_batch(batch_id, mentor.id, db)
    result = await db.execute(
        select(ExamSetup)
        .where(ExamSetup.batch_id == batch_id, ExamSetup.mentor_id == mentor.id)
        .order_by(ExamSetup.created_at)
    )
    return result.scalars().all()


@router.get(
    "/batches/{batch_id}/exams/{exam_id}",
    response_model=ExamSetupResponse,
    tags=["Exams"],
)
async def get_exam_setup(
    batch_id: int, exam_id: int,
    db: AsyncSession = Depends(get_db),
    mentor: Mentor = Depends(get_current_mentor),
):
    await _get_batch(batch_id, mentor.id, db)
    return await _get_setup(exam_id, batch_id, db)


@router.patch(
    "/batches/{batch_id}/exams/{exam_id}",
    response_model=ExamSetupResponse,
    tags=["Exams"],
)
async def update_exam_setup(
    batch_id: int, exam_id: int,
    payload: ExamSetupUpdate,
    db: AsyncSession = Depends(get_db),
    mentor: Mentor = Depends(get_current_mentor),
):
    await _get_batch(batch_id, mentor.id, db)
    setup = await _get_setup(exam_id, batch_id, db)
    for k, v in payload.model_dump(exclude_none=True).items():
        setattr(setup, k, v)
    await db.commit()
    await db.refresh(setup)
    return setup


@router.delete(
    "/batches/{batch_id}/exams/{exam_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["Exams"],
)
async def delete_exam_setup(
    batch_id: int, exam_id: int,
    db: AsyncSession = Depends(get_db),
    mentor: Mentor = Depends(get_current_mentor),
):
    await _get_batch(batch_id, mentor.id, db)
    setup = await _get_setup(exam_id, batch_id, db)
    await db.delete(setup)
    await db.commit()


# ══════════════════════════════════════════════════════════════════════════════
# Marks CRUD
# ══════════════════════════════════════════════════════════════════════════════

async def _get_marks_with_students(exam_id: int, db: AsyncSession) -> list[tuple]:
    result = await db.execute(
        select(StudentExamMarks, Student)
        .join(Student, StudentExamMarks.student_id == Student.id)
        .where(StudentExamMarks.exam_setup_id == exam_id)
        .order_by(Student.name)
    )
    return result.all()


@router.get(
    "/batches/{batch_id}/exams/{exam_id}/marks",
    response_model=list[StudentMarksResponse],
    tags=["Exams"],
)
async def list_marks(
    batch_id: int, exam_id: int,
    db: AsyncSession = Depends(get_db),
    mentor: Mentor = Depends(get_current_mentor),
):
    await _get_batch(batch_id, mentor.id, db)
    await _get_setup(exam_id, batch_id, db)
    rows = await _get_marks_with_students(exam_id, db)
    return [
        StudentMarksResponse(
            id=m.id, exam_setup_id=m.exam_setup_id, student_id=m.student_id,
            pt1_marks=m.pt1_marks or {}, pt2_marks=m.pt2_marks or {},
            semester_grades=m.semester_grades or {},
            student_name=s.name, register_number=s.register_number,
        )
        for m, s in rows
    ]


@router.put(
    "/batches/{batch_id}/exams/{exam_id}/marks",
    response_model=list[StudentMarksResponse],
    tags=["Exams"],
)
async def bulk_upsert_marks(
    batch_id: int, exam_id: int,
    payload: BulkMarksPayload,
    db: AsyncSession = Depends(get_db),
    mentor: Mentor = Depends(get_current_mentor),
):
    """Bulk save PT1/PT2 marks and semester grades for all students."""
    await _get_batch(batch_id, mentor.id, db)
    await _get_setup(exam_id, batch_id, db)

    existing_result = await db.execute(
        select(StudentExamMarks).where(StudentExamMarks.exam_setup_id == exam_id)
    )
    existing = {r.student_id: r for r in existing_result.scalars().all()}

    for rec in payload.records:
        if rec.student_id in existing:
            m = existing[rec.student_id]
            m.pt1_marks = rec.pt1_marks
            m.pt2_marks = rec.pt2_marks
            m.semester_grades = rec.semester_grades
        else:
            m = StudentExamMarks(
                exam_setup_id=exam_id,
                student_id=rec.student_id,
                pt1_marks=rec.pt1_marks,
                pt2_marks=rec.pt2_marks,
                semester_grades=rec.semester_grades,
            )
            db.add(m)

    await db.commit()
    rows = await _get_marks_with_students(exam_id, db)
    return [
        StudentMarksResponse(
            id=m.id, exam_setup_id=m.exam_setup_id, student_id=m.student_id,
            pt1_marks=m.pt1_marks or {}, pt2_marks=m.pt2_marks or {},
            semester_grades=m.semester_grades or {},
            student_name=s.name, register_number=s.register_number,
        )
        for m, s in rows
    ]


# ══════════════════════════════════════════════════════════════════════════════
# PDF exports
# ══════════════════════════════════════════════════════════════════════════════

async def _build_student_records(exam_id: int, db: AsyncSession) -> list[dict]:
    rows = await _get_marks_with_students(exam_id, db)
    return [
        {
            "register_number": s.register_number,
            "name": s.name,
            "pt1_marks": m.pt1_marks or {},
            "pt2_marks": m.pt2_marks or {},
            "semester_grades": m.semester_grades or {},
        }
        for m, s in rows
    ]


@router.get(
    "/batches/{batch_id}/exams/{exam_id}/pdf/pt1",
    response_class=Response,
    tags=["Exams"],
)
async def export_pt1_marks_pdf(
    batch_id: int, exam_id: int,
    db: AsyncSession = Depends(get_db),
    mentor: Mentor = Depends(get_current_mentor),
):
    """Download PT I marks sheet as PDF."""
    batch = await _get_batch(batch_id, mentor.id, db)
    setup = await _get_setup(exam_id, batch_id, db)
    records = await _build_student_records(exam_id, db)

    pdf = generate_pt_marks_pdf(
        department=batch.department,
        academic_year=setup.academic_year,
        mentor_name=mentor.name,
        subject_codes=setup.subject_codes,
        student_records=records,
        pt_number=1,
    )
    fname = f"pt1_marks_{setup.semester}_{batch.batch_year}.pdf".replace(" ", "_")
    return Response(content=pdf, media_type="application/pdf",
                    headers={"Content-Disposition": f'attachment; filename="{fname}"'})


@router.get(
    "/batches/{batch_id}/exams/{exam_id}/pdf/pt2",
    response_class=Response,
    tags=["Exams"],
)
async def export_pt2_marks_pdf(
    batch_id: int, exam_id: int,
    db: AsyncSession = Depends(get_db),
    mentor: Mentor = Depends(get_current_mentor),
):
    """Download PT II marks sheet as PDF."""
    batch = await _get_batch(batch_id, mentor.id, db)
    setup = await _get_setup(exam_id, batch_id, db)
    records = await _build_student_records(exam_id, db)

    pdf = generate_pt_marks_pdf(
        department=batch.department,
        academic_year=setup.academic_year,
        mentor_name=mentor.name,
        subject_codes=setup.subject_codes,
        student_records=records,
        pt_number=2,
    )
    fname = f"pt2_marks_{setup.semester}_{batch.batch_year}.pdf".replace(" ", "_")
    return Response(content=pdf, media_type="application/pdf",
                    headers={"Content-Disposition": f'attachment; filename="{fname}"'})



@router.get(
    "/batches/{batch_id}/exams/{exam_id}/pdf/semester",
    response_class=Response,
    tags=["Exams"],
)
async def export_semester_pdf(
    batch_id: int, exam_id: int,
    db: AsyncSession = Depends(get_db),
    mentor: Mentor = Depends(get_current_mentor),
):
    """Download semester end examination grade sheet as PDF."""
    batch = await _get_batch(batch_id, mentor.id, db)
    setup = await _get_setup(exam_id, batch_id, db)
    records = await _build_student_records(exam_id, db)

    pdf = generate_semester_pdf(
        department=batch.department,
        academic_year=setup.academic_year,
        mentor_name=mentor.name,
        subject_codes=setup.subject_codes,
        student_records=records,
    )
    fname = f"semester_grades_{setup.semester}_{batch.batch_year}.pdf".replace(" ", "_")
    return Response(content=pdf, media_type="application/pdf",
                    headers={"Content-Disposition": f'attachment; filename="{fname}"'})
