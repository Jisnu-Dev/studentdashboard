"""AI routes — student performance reports, schedules, and chat."""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_mentor, get_db
from app.models.exam import ExamSetup, StudentExamMarks
from app.models.meeting import MentorMeeting
from app.models.meeting_attendance import MeetingAttendance
from app.models.counseling import CounselingSession
from app.models.mentor import Mentor
from app.models.student import Batch, Student
from app.services.ai_service import (
    build_student_context,
    generate_report,
    generate_schedule,
    chat,
)

router = APIRouter()


# ── Schemas ────────────────────────────────────────────────────────────────────

class ChatMessage(BaseModel):
    role: str   # "user" | "model"
    content: str


class ChatPayload(BaseModel):
    message: str
    history: list[ChatMessage] = []


class AIResponse(BaseModel):
    text: str


# ── Helpers ───────────────────────────────────────────────────────────────────

async def _guard_batch(batch_id: int, mentor_id: int, db: AsyncSession) -> Batch:
    res = await db.execute(select(Batch).where(Batch.id == batch_id, Batch.mentor_id == mentor_id))
    b = res.scalar_one_or_none()
    if not b:
        raise HTTPException(status_code=404, detail="Batch not found")
    return b


async def _guard_student(student_id: int, batch_id: int, db: AsyncSession) -> Student:
    res = await db.execute(
        select(Student).where(Student.id == student_id, Student.batch_id == batch_id)
    )
    s = res.scalar_one_or_none()
    if not s:
        raise HTTPException(status_code=404, detail="Student not found")
    return s


async def _build_context(
    student: Student, batch: Batch, student_id: int, db: AsyncSession
) -> str:
    """Collect all available data for this student and build AI context."""

    # All exam setups for this batch, with this student's marks
    setups_res = await db.execute(
        select(ExamSetup).where(ExamSetup.batch_id == batch.id).order_by(ExamSetup.created_at)
    )
    setups = setups_res.scalars().all()

    exam_records = []
    for setup in setups:
        marks_res = await db.execute(
            select(StudentExamMarks).where(
                StudentExamMarks.exam_setup_id == setup.id,
                StudentExamMarks.student_id == student_id,
            )
        )
        m = marks_res.scalar_one_or_none()
        exam_records.append({
            "semester": setup.semester,
            "academic_year": setup.academic_year,
            "subject_codes": setup.subject_codes,
            "pt1_marks": m.pt1_marks if m else {},
            "pt2_marks": m.pt2_marks if m else {},
            "semester_grades": m.semester_grades if m else {},
        })

    # Meeting attendance
    att_res = await db.execute(
        select(MeetingAttendance, MentorMeeting)
        .join(MentorMeeting, MeetingAttendance.meeting_id == MentorMeeting.id)
        .where(
            MeetingAttendance.student_id == student_id,
            MentorMeeting.batch_id == batch.id,
        )
        .order_by(MentorMeeting.meeting_date)
    )
    attendance_records = [
        {
            "meeting_date": str(meeting.meeting_date),
            "is_present": att.is_present,
            "points_discussed": att.points_discussed or [],
            "action_planned": att.action_planned or [],
        }
        for att, meeting in att_res.all()
    ]

    # Counseling sessions
    cs_res = await db.execute(
        select(CounselingSession)
        .where(CounselingSession.student_id == student_id)
        .order_by(CounselingSession.counseling_date)
    )
    counseling_records = [
        {
            "date": str(cs.counseling_date),
            "responses": {
                "Reason": cs.reason_details or cs.reason_initiated_by,
                "Attendance": f"{cs.attendance_status}" + (f" — {cs.attendance_other}" if cs.attendance_other else ""),
                "Discipline": f"{cs.discipline_status}" + (f" — {cs.discipline_other}" if cs.discipline_other else ""),
                "Attitude": f"{cs.attitude_status}" + (f" — {cs.attitude_other}" if cs.attitude_other else ""),
                "Difficulty meeting demands": f"{'Yes' if cs.difficulty_meeting_demands else 'No'}" + (f" — {cs.difficulty_explanation}" if cs.difficulty_explanation else ""),
                "Corrective action needed": f"{'Yes' if cs.corrective_action_needed else 'No'}" + (f" — {cs.corrective_action_explanation}" if cs.corrective_action_explanation else ""),
                "Next session needed": f"{'Yes' if cs.next_session_needed else 'No'}" + (f" — {cs.next_session_explanation}" if cs.next_session_explanation else ""),
            },
        }
        for cs in cs_res.scalars().all()
    ]

    return build_student_context(
        student={"name": student.name, "register_number": student.register_number},
        batch={"department": batch.department, "batch_year": batch.batch_year},
        exam_records=exam_records,
        attendance_records=attendance_records,
        counseling_records=counseling_records,
    )


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post(
    "/batches/{batch_id}/students/{student_id}/ai/report",
    response_model=AIResponse,
    tags=["AI"],
)
async def get_student_report(
    batch_id: int,
    student_id: int,
    db: AsyncSession = Depends(get_db),
    mentor: Mentor = Depends(get_current_mentor),
):
    """Generate a comprehensive AI performance report for a student."""
    batch = await _guard_batch(batch_id, mentor.id, db)
    student = await _guard_student(student_id, batch_id, db)
    context = await _build_context(student, batch, student_id, db)
    try:
        text = await generate_report(context)
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))
    return AIResponse(text=text)


@router.post(
    "/batches/{batch_id}/students/{student_id}/ai/schedule",
    response_model=AIResponse,
    tags=["AI"],
)
async def get_study_schedule(
    batch_id: int,
    student_id: int,
    db: AsyncSession = Depends(get_db),
    mentor: Mentor = Depends(get_current_mentor),
):
    """Generate a personalised AI study schedule for a student."""
    batch = await _guard_batch(batch_id, mentor.id, db)
    student = await _guard_student(student_id, batch_id, db)
    context = await _build_context(student, batch, student_id, db)
    try:
        text = await generate_schedule(context)
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))
    return AIResponse(text=text)


@router.post(
    "/batches/{batch_id}/students/{student_id}/ai/chat",
    response_model=AIResponse,
    tags=["AI"],
)
async def student_chat(
    batch_id: int,
    student_id: int,
    payload: ChatPayload,
    db: AsyncSession = Depends(get_db),
    mentor: Mentor = Depends(get_current_mentor),
):
    """Chat with the AI about a specific student."""
    batch = await _guard_batch(batch_id, mentor.id, db)
    student = await _guard_student(student_id, batch_id, db)
    context = await _build_context(student, batch, student_id, db)
    try:
        text = await chat(
            context=context,
            history=[{"role": m.role, "content": m.content} for m in payload.history],
            user_message=payload.message,
        )
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))
    return AIResponse(text=text)
