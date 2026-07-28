from datetime import date as date_type

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import Response
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_mentor, get_db
from app.models.meeting import MentorMeeting
from app.models.meeting_attendance import MeetingAttendance
from app.models.mentor import Mentor
from app.models.student import Batch, Student
from app.schemas.meeting import (
    BulkAttendancePayload,
    AttendanceResponse,
    MeetingCreate,
    MeetingResponse,
    MeetingUpdate,
)
from app.services.meeting_pdf_service import generate_circular_pdf, generate_minutes_pdf

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


async def _get_meeting(meeting_id: int, batch_id: int, db: AsyncSession) -> MentorMeeting:
    result = await db.execute(
        select(MentorMeeting).where(
            MentorMeeting.id == meeting_id,
            MentorMeeting.batch_id == batch_id,
        )
    )
    m = result.scalar_one_or_none()
    if not m:
        raise HTTPException(status_code=404, detail="Meeting not found")
    return m


# ══════════════════════════════════════════════════════════════════════════════
# CRUD
# ══════════════════════════════════════════════════════════════════════════════

@router.post(
    "/batches/{batch_id}/meetings",
    response_model=MeetingResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Meetings"],
)
async def create_meeting(
    batch_id: int,
    payload: MeetingCreate,
    db: AsyncSession = Depends(get_db),
    mentor: Mentor = Depends(get_current_mentor),
):
    """Create a new meeting for a batch. Meeting number auto-increments."""
    await _get_batch(batch_id, mentor.id, db)

    # Auto-assign meeting number
    count_result = await db.execute(
        select(func.count()).where(
            MentorMeeting.batch_id == batch_id,
            MentorMeeting.mentor_id == mentor.id,
        )
    )
    meeting_number = (count_result.scalar() or 0) + 1

    meeting = MentorMeeting(
        batch_id=batch_id,
        mentor_id=mentor.id,
        meeting_number=meeting_number,
        **payload.model_dump(),
    )
    db.add(meeting)
    await db.commit()
    await db.refresh(meeting)
    return meeting


@router.get(
    "/batches/{batch_id}/meetings",
    response_model=list[MeetingResponse],
    tags=["Meetings"],
)
async def list_meetings(
    batch_id: int,
    db: AsyncSession = Depends(get_db),
    mentor: Mentor = Depends(get_current_mentor),
):
    await _get_batch(batch_id, mentor.id, db)
    result = await db.execute(
        select(MentorMeeting)
        .where(MentorMeeting.batch_id == batch_id, MentorMeeting.mentor_id == mentor.id)
        .order_by(MentorMeeting.meeting_number)
    )
    return result.scalars().all()


@router.get(
    "/batches/{batch_id}/meetings/{meeting_id}",
    response_model=MeetingResponse,
    tags=["Meetings"],
)
async def get_meeting(
    batch_id: int,
    meeting_id: int,
    db: AsyncSession = Depends(get_db),
    mentor: Mentor = Depends(get_current_mentor),
):
    await _get_batch(batch_id, mentor.id, db)
    return await _get_meeting(meeting_id, batch_id, db)


@router.patch(
    "/batches/{batch_id}/meetings/{meeting_id}",
    response_model=MeetingResponse,
    tags=["Meetings"],
)
async def update_meeting(
    batch_id: int,
    meeting_id: int,
    payload: MeetingUpdate,
    db: AsyncSession = Depends(get_db),
    mentor: Mentor = Depends(get_current_mentor),
):
    """Update meeting details or add/edit minutes of meeting."""
    await _get_batch(batch_id, mentor.id, db)
    meeting = await _get_meeting(meeting_id, batch_id, db)

    for k, v in payload.model_dump(exclude_none=True).items():
        setattr(meeting, k, v)

    await db.commit()
    await db.refresh(meeting)
    return meeting


@router.delete(
    "/batches/{batch_id}/meetings/{meeting_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["Meetings"],
)
async def delete_meeting(
    batch_id: int,
    meeting_id: int,
    db: AsyncSession = Depends(get_db),
    mentor: Mentor = Depends(get_current_mentor),
):
    await _get_batch(batch_id, mentor.id, db)
    meeting = await _get_meeting(meeting_id, batch_id, db)
    await db.delete(meeting)
    await db.commit()


# ══════════════════════════════════════════════════════════════════════════════
# PDF exports
# ══════════════════════════════════════════════════════════════════════════════

@router.get(
    "/batches/{batch_id}/meetings/{meeting_id}/circular",
    response_class=Response,
    tags=["Meetings"],
)
async def export_circular_pdf(
    batch_id: int,
    meeting_id: int,
    db: AsyncSession = Depends(get_db),
    mentor: Mentor = Depends(get_current_mentor),
):
    """Download the meeting circular as a PDF."""
    batch = await _get_batch(batch_id, mentor.id, db)
    meeting = await _get_meeting(meeting_id, batch_id, db)

    pdf = generate_circular_pdf(
        department=batch.department,
        meeting_date=meeting.meeting_date,
        meeting_time=meeting.meeting_time,
        location=meeting.location,
        semester=meeting.semester,
        meeting_number=meeting.meeting_number,
        agenda_items=meeting.agenda_items,
    )
    filename = f"circular_meeting_{meeting.meeting_number}_{batch.batch_year}.pdf"
    return Response(
        content=pdf,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get(
    "/batches/{batch_id}/meetings/{meeting_id}/minutes",
    response_class=Response,
    tags=["Meetings"],
)
async def export_minutes_pdf(
    batch_id: int,
    meeting_id: int,
    db: AsyncSession = Depends(get_db),
    mentor: Mentor = Depends(get_current_mentor),
):
    """Download the minutes of meeting as a PDF (includes attendance table)."""
    batch = await _get_batch(batch_id, mentor.id, db)
    meeting = await _get_meeting(meeting_id, batch_id, db)

    # Load attendance records with student info eagerly
    att_result = await db.execute(
        select(MeetingAttendance, Student)
        .join(Student, MeetingAttendance.student_id == Student.id)
        .where(MeetingAttendance.meeting_id == meeting_id)
        .order_by(Student.name)
    )
    attendance_rows = att_result.all()

    attendees = [
        {
            "register_number": s.register_number,
            "name": s.name,
            "is_present": a.is_present,
            "points_discussed": a.points_discussed or [],
            "action_planned": a.action_planned or [],
        }
        for a, s in attendance_rows
        if a.is_present
    ]

    pdf = generate_minutes_pdf(
        department=batch.department,
        meeting_date=meeting.meeting_date,
        meeting_time=meeting.meeting_time,
        location=meeting.location,
        semester=meeting.semester,
        academic_year=meeting.academic_year or "",
        year_of_study=meeting.year_of_study or "",
        meeting_number=meeting.meeting_number,
        mentor_name=mentor.name,
        attendees=attendees,
    )
    filename = f"minutes_meeting_{meeting.meeting_number}_{batch.batch_year}.pdf"
    return Response(
        content=pdf,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


# ══════════════════════════════════════════════════════════════════════════════
# Attendance CRUD
# ══════════════════════════════════════════════════════════════════════════════

@router.get(
    "/batches/{batch_id}/meetings/{meeting_id}/attendance",
    response_model=list[AttendanceResponse],
    tags=["Meetings"],
)
async def list_attendance(
    batch_id: int,
    meeting_id: int,
    db: AsyncSession = Depends(get_db),
    mentor: Mentor = Depends(get_current_mentor),
):
    """List all attendance records for a meeting, joined with student info."""
    await _get_batch(batch_id, mentor.id, db)
    await _get_meeting(meeting_id, batch_id, db)

    result = await db.execute(
        select(MeetingAttendance, Student)
        .join(Student, MeetingAttendance.student_id == Student.id)
        .where(MeetingAttendance.meeting_id == meeting_id)
        .order_by(Student.name)
    )
    rows = result.all()
    out = []
    for att, student in rows:
        out.append(AttendanceResponse(
            id=att.id,
            meeting_id=att.meeting_id,
            student_id=att.student_id,
            is_present=att.is_present,
            points_discussed=att.points_discussed or [],
            action_planned=att.action_planned or [],
            student_name=student.name,
            register_number=student.register_number,
        ))
    return out


@router.put(
    "/batches/{batch_id}/meetings/{meeting_id}/attendance",
    response_model=list[AttendanceResponse],
    tags=["Meetings"],
)
async def bulk_upsert_attendance(
    batch_id: int,
    meeting_id: int,
    payload: BulkAttendancePayload,
    db: AsyncSession = Depends(get_db),
    mentor: Mentor = Depends(get_current_mentor),
):
    """Bulk upsert attendance records for a meeting (one record per student)."""
    await _get_batch(batch_id, mentor.id, db)
    await _get_meeting(meeting_id, batch_id, db)

    # Build lookup of existing records
    existing_result = await db.execute(
        select(MeetingAttendance).where(MeetingAttendance.meeting_id == meeting_id)
    )
    existing = {r.student_id: r for r in existing_result.scalars().all()}

    updated = []
    for rec in payload.records:
        if rec.student_id in existing:
            att = existing[rec.student_id]
            att.is_present = rec.is_present
            att.points_discussed = rec.points_discussed
            att.action_planned = rec.action_planned
        else:
            att = MeetingAttendance(
                meeting_id=meeting_id,
                student_id=rec.student_id,
                is_present=rec.is_present,
                points_discussed=rec.points_discussed,
                action_planned=rec.action_planned,
            )
            db.add(att)
        updated.append((att, rec.student_id))

    await db.commit()

    # Re-fetch with student join
    result = await db.execute(
        select(MeetingAttendance, Student)
        .join(Student, MeetingAttendance.student_id == Student.id)
        .where(MeetingAttendance.meeting_id == meeting_id)
        .order_by(Student.name)
    )
    rows = result.all()
    return [
        AttendanceResponse(
            id=a.id, meeting_id=a.meeting_id, student_id=a.student_id,
            is_present=a.is_present, points_discussed=a.points_discussed or [],
            action_planned=a.action_planned or [],
            student_name=s.name, register_number=s.register_number,
        )
        for a, s in rows
    ]
