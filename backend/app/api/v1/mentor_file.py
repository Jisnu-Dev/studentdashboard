"""Mentor file routes — communication records, parent meetings, achievements,
condonation, semester results (GPA / CGPA / arrears), cover page and checklist summary."""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import Response
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_mentor, get_db
from app.models.counseling import CounselingSession
from app.models.exam import ExamSetup
from app.models.meeting import MentorMeeting
from app.models.mentor import Mentor
from app.models.mentor_file import (
    Achievement,
    CommunicationRecord,
    Condonation,
    ParentMeeting,
    RemedialAction,
    SemesterResult,
    StudentDocument,
)
from app.models.student import Batch, Student
from app.schemas.mentor_file import (
    ACHIEVEMENT_CATEGORIES,
    AchievementCreate,
    AchievementResponse,
    BulkSemesterResultPayload,
    CommunicationCreate,
    CommunicationResponse,
    CondonationCreate,
    CondonationResponse,
    MentorFileSummary,
    ParentMeetingCreate,
    ParentMeetingResponse,
    SemesterResultResponse,
)
from app.services.mentor_file_pdf_service import (
    generate_achievements_pdf,
    generate_condonation_pdf,
    generate_cover_pdf,
    generate_mentor_note_pdf,
    generate_parent_meeting_pdf,
    generate_semester_results_pdf,
)

router = APIRouter()

MAX_CONDONATIONS_PER_STUDENT = 2


# ── Guards / helpers ───────────────────────────────────────────────────────────

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


async def _get_record(model, record_id: int, batch_id: int, db: AsyncSession, name: str):
    result = await db.execute(
        select(model).where(model.id == record_id, model.batch_id == batch_id)
    )
    record = result.scalar_one_or_none()
    if not record:
        raise HTTPException(status_code=404, detail=f"{name} not found")
    return record


async def _check_document(document_id: int | None, student_id: int, batch_id: int, db: AsyncSession) -> None:
    if document_id is None:
        return
    result = await db.execute(
        select(StudentDocument.id).where(
            StudentDocument.id == document_id,
            StudentDocument.student_id == student_id,
            StudentDocument.batch_id == batch_id,
        )
    )
    if result.scalar_one_or_none() is None:
        raise HTTPException(status_code=404, detail="Attached document not found")


async def _delete_document(document_id: int | None, db: AsyncSession) -> None:
    if document_id is None:
        return
    doc = await db.get(StudentDocument, document_id)
    if doc:
        await db.delete(doc)


async def _list_with_students(model, batch_id: int, student_id: int | None, order_by, db: AsyncSession) -> list[tuple]:
    query = (
        select(model, Student)
        .join(Student, model.student_id == Student.id)
        .where(model.batch_id == batch_id)
        .order_by(*order_by)
    )
    if student_id:
        query = query.where(model.student_id == student_id)
    result = await db.execute(query)
    return result.all()


def _with_student(schema, record, student: Student):
    return schema.model_validate(record).model_copy(
        update={"student_name": student.name, "register_number": student.register_number}
    )


def _pdf(content: bytes, filename: str) -> Response:
    safe = "".join(ch if ch.isalnum() or ch in "-_." else "_" for ch in filename)
    return Response(
        content=content,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{safe}"'},
    )


# ══════════════════════════════════════════════════════════════════════════════
# Communication records (mentor note)
# ══════════════════════════════════════════════════════════════════════════════

@router.post(
    "/batches/{batch_id}/communications",
    response_model=CommunicationResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Mentor File"],
)
async def create_communication(
    batch_id: int,
    payload: CommunicationCreate,
    db: AsyncSession = Depends(get_db),
    mentor: Mentor = Depends(get_current_mentor),
):
    """Record a communication with a student or parent in the mentor note."""
    await _get_batch(batch_id, mentor.id, db)
    student = await _get_student(payload.student_id, batch_id, db)

    record = CommunicationRecord(batch_id=batch_id, mentor_id=mentor.id, **payload.model_dump())
    db.add(record)
    await db.commit()
    await db.refresh(record)
    return _with_student(CommunicationResponse, record, student)


@router.get(
    "/batches/{batch_id}/communications",
    response_model=list[CommunicationResponse],
    tags=["Mentor File"],
)
async def list_communications(
    batch_id: int,
    student_id: int | None = None,
    db: AsyncSession = Depends(get_db),
    mentor: Mentor = Depends(get_current_mentor),
):
    await _get_batch(batch_id, mentor.id, db)
    rows = await _list_with_students(
        CommunicationRecord, batch_id, student_id,
        (CommunicationRecord.communication_date.desc(), CommunicationRecord.id.desc()), db,
    )
    return [_with_student(CommunicationResponse, r, s) for r, s in rows]


@router.delete(
    "/batches/{batch_id}/communications/{record_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["Mentor File"],
)
async def delete_communication(
    batch_id: int,
    record_id: int,
    db: AsyncSession = Depends(get_db),
    mentor: Mentor = Depends(get_current_mentor),
):
    await _get_batch(batch_id, mentor.id, db)
    record = await _get_record(CommunicationRecord, record_id, batch_id, db, "Communication record")
    await db.delete(record)
    await db.commit()


@router.get(
    "/batches/{batch_id}/communications/pdf",
    response_class=Response,
    tags=["Mentor File"],
)
async def export_mentor_note_pdf(
    batch_id: int,
    student_id: int | None = None,
    db: AsyncSession = Depends(get_db),
    mentor: Mentor = Depends(get_current_mentor),
):
    """Download the mentor note (all communication records, oldest first) as PDF."""
    batch = await _get_batch(batch_id, mentor.id, db)
    rows = await _list_with_students(
        CommunicationRecord, batch_id, student_id,
        (CommunicationRecord.communication_date, CommunicationRecord.id), db,
    )
    pdf = generate_mentor_note_pdf(
        department=batch.department,
        batch_year=batch.batch_year,
        mentor_name=mentor.name,
        records=[
            {
                "communication_date": r.communication_date,
                "register_number": s.register_number,
                "name": s.name,
                "contact_person": r.contact_person,
                "mode": r.mode,
                "details": r.details,
                "feedback": r.feedback,
                "action_taken": r.action_taken,
            }
            for r, s in rows
        ],
    )
    return _pdf(pdf, f"mentor_note_{batch.batch_year}.pdf")


# ══════════════════════════════════════════════════════════════════════════════
# Parent - Teachers Meeting (parental communication report)
# ══════════════════════════════════════════════════════════════════════════════

@router.post(
    "/batches/{batch_id}/parent-meetings",
    response_model=ParentMeetingResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Mentor File"],
)
async def create_parent_meeting(
    batch_id: int,
    payload: ParentMeetingCreate,
    db: AsyncSession = Depends(get_db),
    mentor: Mentor = Depends(get_current_mentor),
):
    await _get_batch(batch_id, mentor.id, db)
    student = await _get_student(payload.student_id, batch_id, db)

    meeting = ParentMeeting(batch_id=batch_id, mentor_id=mentor.id, **payload.model_dump())
    db.add(meeting)
    await db.commit()
    await db.refresh(meeting)
    return _with_student(ParentMeetingResponse, meeting, student)


@router.get(
    "/batches/{batch_id}/parent-meetings",
    response_model=list[ParentMeetingResponse],
    tags=["Mentor File"],
)
async def list_parent_meetings(
    batch_id: int,
    student_id: int | None = None,
    db: AsyncSession = Depends(get_db),
    mentor: Mentor = Depends(get_current_mentor),
):
    await _get_batch(batch_id, mentor.id, db)
    rows = await _list_with_students(
        ParentMeeting, batch_id, student_id, (ParentMeeting.meeting_date.desc(), ParentMeeting.id.desc()), db
    )
    return [_with_student(ParentMeetingResponse, m, s) for m, s in rows]


@router.delete(
    "/batches/{batch_id}/parent-meetings/{meeting_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["Mentor File"],
)
async def delete_parent_meeting(
    batch_id: int,
    meeting_id: int,
    db: AsyncSession = Depends(get_db),
    mentor: Mentor = Depends(get_current_mentor),
):
    await _get_batch(batch_id, mentor.id, db)
    meeting = await _get_record(ParentMeeting, meeting_id, batch_id, db, "Parent meeting")
    await db.delete(meeting)
    await db.commit()


@router.get(
    "/batches/{batch_id}/parent-meetings/{meeting_id}/pdf",
    response_class=Response,
    tags=["Mentor File"],
)
async def export_parent_meeting_pdf(
    batch_id: int,
    meeting_id: int,
    db: AsyncSession = Depends(get_db),
    mentor: Mentor = Depends(get_current_mentor),
):
    """Download the filled Parent - Teachers Meeting form as PDF."""
    await _get_batch(batch_id, mentor.id, db)
    meeting = await _get_record(ParentMeeting, meeting_id, batch_id, db, "Parent meeting")
    student = await _get_student(meeting.student_id, batch_id, db)

    pdf = generate_parent_meeting_pdf(
        mentor_name=mentor.name,
        student_name=student.name,
        register_number=student.register_number,
        m=ParentMeetingCreate.model_validate(meeting, from_attributes=True).model_dump(),
    )
    return _pdf(pdf, f"parent_meeting_{student.register_number}_{meeting.meeting_date}.pdf")


# ══════════════════════════════════════════════════════════════════════════════
# Student achievements
# ══════════════════════════════════════════════════════════════════════════════

@router.post(
    "/batches/{batch_id}/achievements",
    response_model=AchievementResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Mentor File"],
)
async def create_achievement(
    batch_id: int,
    payload: AchievementCreate,
    db: AsyncSession = Depends(get_db),
    mentor: Mentor = Depends(get_current_mentor),
):
    await _get_batch(batch_id, mentor.id, db)
    student = await _get_student(payload.student_id, batch_id, db)
    if payload.category not in ACHIEVEMENT_CATEGORIES:
        raise HTTPException(status_code=422, detail="Unknown event category")
    await _check_document(payload.document_id, payload.student_id, batch_id, db)

    achievement = Achievement(batch_id=batch_id, **payload.model_dump())
    db.add(achievement)
    await db.commit()
    await db.refresh(achievement)
    return _with_student(AchievementResponse, achievement, student)


@router.get(
    "/batches/{batch_id}/achievements",
    response_model=list[AchievementResponse],
    tags=["Mentor File"],
)
async def list_achievements(
    batch_id: int,
    student_id: int | None = None,
    db: AsyncSession = Depends(get_db),
    mentor: Mentor = Depends(get_current_mentor),
):
    await _get_batch(batch_id, mentor.id, db)
    rows = await _list_with_students(
        Achievement, batch_id, student_id, (Student.name, Achievement.academic_year, Achievement.id), db
    )
    return [_with_student(AchievementResponse, a, s) for a, s in rows]


@router.delete(
    "/batches/{batch_id}/achievements/{achievement_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["Mentor File"],
)
async def delete_achievement(
    batch_id: int,
    achievement_id: int,
    db: AsyncSession = Depends(get_db),
    mentor: Mentor = Depends(get_current_mentor),
):
    """Delete an achievement together with its certificate."""
    await _get_batch(batch_id, mentor.id, db)
    achievement = await _get_record(Achievement, achievement_id, batch_id, db, "Achievement")
    await _delete_document(achievement.document_id, db)
    await db.delete(achievement)
    await db.commit()


@router.get(
    "/batches/{batch_id}/students/{student_id}/achievements/pdf",
    response_class=Response,
    tags=["Mentor File"],
)
async def export_achievements_pdf(
    batch_id: int,
    student_id: int,
    academic_year: str,
    semester: str | None = None,
    db: AsyncSession = Depends(get_db),
    mentor: Mentor = Depends(get_current_mentor),
):
    """Download a student's achievements summary sheet for one academic year (optionally one semester)."""
    batch = await _get_batch(batch_id, mentor.id, db)
    student = await _get_student(student_id, batch_id, db)

    query = (
        select(Achievement)
        .where(
            Achievement.student_id == student_id,
            Achievement.batch_id == batch_id,
            Achievement.academic_year == academic_year,
        )
        .order_by(Achievement.event_date, Achievement.id)
    )
    if semester:
        query = query.where(Achievement.semester == semester)
    result = await db.execute(query)

    pdf = generate_achievements_pdf(
        department=batch.department,
        academic_year=academic_year,
        student_name=student.name,
        register_number=student.register_number,
        achievements=[
            {"event_name": a.event_name, "level": a.level, "result": a.result}
            for a in result.scalars().all()
        ],
    )
    return _pdf(pdf, f"achievements_{student.register_number}_{academic_year}.pdf")


# ══════════════════════════════════════════════════════════════════════════════
# Condonation
# ══════════════════════════════════════════════════════════════════════════════

@router.post(
    "/batches/{batch_id}/condonations",
    response_model=CondonationResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Mentor File"],
)
async def create_condonation(
    batch_id: int,
    payload: CondonationCreate,
    db: AsyncSession = Depends(get_db),
    mentor: Mentor = Depends(get_current_mentor),
):
    """Record a condonation application. A student may apply only twice in the entire course."""
    await _get_batch(batch_id, mentor.id, db)
    student = await _get_student(payload.student_id, batch_id, db)
    await _check_document(payload.document_id, payload.student_id, batch_id, db)

    count_result = await db.execute(
        select(func.count()).select_from(Condonation).where(Condonation.student_id == payload.student_id)
    )
    if (count_result.scalar() or 0) >= MAX_CONDONATIONS_PER_STUDENT:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This student has already applied for condonation twice",
        )

    condonation = Condonation(batch_id=batch_id, **payload.model_dump())
    db.add(condonation)
    await db.commit()
    await db.refresh(condonation)
    return _with_student(CondonationResponse, condonation, student)


@router.get(
    "/batches/{batch_id}/condonations",
    response_model=list[CondonationResponse],
    tags=["Mentor File"],
)
async def list_condonations(
    batch_id: int,
    student_id: int | None = None,
    db: AsyncSession = Depends(get_db),
    mentor: Mentor = Depends(get_current_mentor),
):
    await _get_batch(batch_id, mentor.id, db)
    rows = await _list_with_students(Condonation, batch_id, student_id, (Student.name, Condonation.id), db)
    return [_with_student(CondonationResponse, c, s) for c, s in rows]


@router.delete(
    "/batches/{batch_id}/condonations/{condonation_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["Mentor File"],
)
async def delete_condonation(
    batch_id: int,
    condonation_id: int,
    db: AsyncSession = Depends(get_db),
    mentor: Mentor = Depends(get_current_mentor),
):
    """Delete a condonation record together with its attached proof."""
    await _get_batch(batch_id, mentor.id, db)
    condonation = await _get_record(Condonation, condonation_id, batch_id, db, "Condonation record")
    await _delete_document(condonation.document_id, db)
    await db.delete(condonation)
    await db.commit()


@router.get(
    "/batches/{batch_id}/condonations/{condonation_id}/pdf",
    response_class=Response,
    tags=["Mentor File"],
)
async def export_condonation_pdf(
    batch_id: int,
    condonation_id: int,
    db: AsyncSession = Depends(get_db),
    mentor: Mentor = Depends(get_current_mentor),
):
    """Download the filled Application for Condonation as PDF."""
    await _get_batch(batch_id, mentor.id, db)
    c = await _get_record(Condonation, condonation_id, batch_id, db, "Condonation record")
    student = await _get_student(c.student_id, batch_id, db)

    pdf = generate_condonation_pdf(
        student_name=student.name,
        register_number=student.register_number,
        exam_month_year=c.exam_month_year,
        degree_branch=c.degree_branch,
        semester=c.semester,
        attendance_percentage=c.attendance_percentage,
        reason=c.reason,
        recommended=c.recommended,
    )
    return _pdf(pdf, f"condonation_{student.register_number}_{c.exam_month_year}.pdf")


# ══════════════════════════════════════════════════════════════════════════════
# Semester results — GPA, CGPA and arrear details
# ══════════════════════════════════════════════════════════════════════════════

async def _semester_rows(batch_id: int, db: AsyncSession) -> list[tuple]:
    """Every student of the batch with their SemesterResult (or None)."""
    result = await db.execute(
        select(Student, SemesterResult)
        .outerjoin(SemesterResult, SemesterResult.student_id == Student.id)
        .where(Student.batch_id == batch_id)
        .order_by(Student.name)
    )
    return result.all()


@router.get(
    "/batches/{batch_id}/semester-results",
    response_model=list[SemesterResultResponse],
    tags=["Mentor File"],
)
async def list_semester_results(
    batch_id: int,
    db: AsyncSession = Depends(get_db),
    mentor: Mentor = Depends(get_current_mentor),
):
    await _get_batch(batch_id, mentor.id, db)
    return [_with_student(SemesterResultResponse, r, s) for s, r in await _semester_rows(batch_id, db) if r]


@router.put(
    "/batches/{batch_id}/semester-results",
    response_model=list[SemesterResultResponse],
    tags=["Mentor File"],
)
async def bulk_upsert_semester_results(
    batch_id: int,
    payload: BulkSemesterResultPayload,
    db: AsyncSession = Depends(get_db),
    mentor: Mentor = Depends(get_current_mentor),
):
    """Bulk save semester-wise GPA, arrears and CGPA (one record per student)."""
    await _get_batch(batch_id, mentor.id, db)

    rows = await _semester_rows(batch_id, db)
    existing = {s.id: r for s, r in rows}

    for rec in payload.records:
        if rec.student_id not in existing:
            raise HTTPException(status_code=404, detail="Student not found")
        r = existing[rec.student_id]
        if r:
            r.gpa = rec.gpa
            r.arrears = rec.arrears
            r.cgpa = rec.cgpa
        else:
            db.add(SemesterResult(
                student_id=rec.student_id,
                batch_id=batch_id,
                gpa=rec.gpa,
                arrears=rec.arrears,
                cgpa=rec.cgpa,
            ))

    await db.commit()
    return [_with_student(SemesterResultResponse, r, s) for s, r in await _semester_rows(batch_id, db) if r]


@router.get(
    "/batches/{batch_id}/semester-results/pdf",
    response_class=Response,
    tags=["Mentor File"],
)
async def export_semester_results_pdf(
    batch_id: int,
    academic_year: str,
    db: AsyncSession = Depends(get_db),
    mentor: Mentor = Depends(get_current_mentor),
):
    """Download semester-wise GPA / CGPA and arrear details as PDF."""
    batch = await _get_batch(batch_id, mentor.id, db)
    pdf = generate_semester_results_pdf(
        department=batch.department,
        academic_year=academic_year,
        mentor_name=mentor.name,
        rows=[
            {
                "register_number": s.register_number,
                "name": s.name,
                "gpa": r.gpa if r else {},
                "arrears": r.arrears if r else {},
                "cgpa": r.cgpa if r else "",
            }
            for s, r in await _semester_rows(batch_id, db)
        ],
    )
    return _pdf(pdf, f"gpa_cgpa_arrears_{batch.batch_year}.pdf")


# ══════════════════════════════════════════════════════════════════════════════
# Cover page + checklist summary
# ══════════════════════════════════════════════════════════════════════════════

@router.get(
    "/batches/{batch_id}/mentor-file/cover",
    response_class=Response,
    tags=["Mentor File"],
)
async def export_cover_pdf(
    batch_id: int,
    db: AsyncSession = Depends(get_db),
    mentor: Mentor = Depends(get_current_mentor),
):
    """Download the Mentor File cover page."""
    batch = await _get_batch(batch_id, mentor.id, db)
    pdf = generate_cover_pdf(batch_year=batch.batch_year, department=batch.department, mentor_name=mentor.name)
    return _pdf(pdf, f"mentor_file_cover_{batch.batch_year}.pdf")


@router.get(
    "/batches/{batch_id}/mentor-file/summary",
    response_model=MentorFileSummary,
    tags=["Mentor File"],
)
async def mentor_file_summary(
    batch_id: int,
    db: AsyncSession = Depends(get_db),
    mentor: Mentor = Depends(get_current_mentor),
):
    """How much of each checklist item has been recorded for this batch."""
    await _get_batch(batch_id, mentor.id, db)

    async def count(column, *where) -> int:
        result = await db.execute(select(func.count(column)).where(*where))
        return result.scalar() or 0

    def docs(category: str) -> tuple:
        return (StudentDocument.batch_id == batch_id, StudentDocument.category == category)

    return MentorFileSummary(
        students=await count(Student.id, Student.batch_id == batch_id),
        personal_details=await count(StudentDocument.student_id.distinct(), *docs("personal_details")),
        counseling_sessions=await count(CounselingSession.id, CounselingSession.batch_id == batch_id),
        students_counseled=await count(
            CounselingSession.student_id.distinct(), CounselingSession.batch_id == batch_id
        ),
        meetings=await count(MentorMeeting.id, MentorMeeting.batch_id == batch_id),
        communications=await count(CommunicationRecord.id, CommunicationRecord.batch_id == batch_id),
        exam_setups=await count(ExamSetup.id, ExamSetup.batch_id == batch_id),
        remedial_actions=await count(
            RemedialAction.id,
            RemedialAction.exam_setup_id.in_(select(ExamSetup.id).where(ExamSetup.batch_id == batch_id)),
        ),
        parent_meetings=await count(ParentMeeting.id, ParentMeeting.batch_id == batch_id),
        medical_leaves=await count(StudentDocument.id, *docs("medical_leave")),
        achievements=await count(Achievement.id, Achievement.batch_id == batch_id),
        condonations=await count(Condonation.id, Condonation.batch_id == batch_id),
        semester_results=await count(SemesterResult.id, SemesterResult.batch_id == batch_id),
    )
