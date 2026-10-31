"""AI routes — student overview (computed), saved reports, study plans, and chat."""

import asyncio
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_mentor, get_db
from app.models.ai_report import AIReport
from app.models.mentor import Mentor
from app.models.student import Batch, Student
from app.services.ai_service import AIError, chat, generate_report, generate_schedule
from app.services.student_insights import build_snapshot, fetch, render_context

router = APIRouter()


# ── Schemas ────────────────────────────────────────────────────────────────────

class ChatMessage(BaseModel):
    role: str   # "user" | "model"
    content: str


class ChatPayload(BaseModel):
    message: str = Field(..., min_length=1, max_length=4000)
    history: list[ChatMessage] = []


class AIResponse(BaseModel):
    text: str


class SavedReport(BaseModel):
    content: dict
    model: str
    created_at: datetime

    model_config = {"from_attributes": True}


class OverviewResponse(BaseModel):
    snapshot: dict                      # see student_insights.build_snapshot
    report: SavedReport | None = None   # last generated performance report
    schedule: SavedReport | None = None


# ── Helpers ───────────────────────────────────────────────────────────────────

async def _guard(batch_id: int, student_id: int, mentor_id: int, db: AsyncSession) -> tuple[Student, Batch]:
    """The student and their batch, only if the batch belongs to this mentor (one query)."""
    res = await db.execute(
        select(Student, Batch)
        .join(Batch, Student.batch_id == Batch.id)
        .where(Student.id == student_id, Batch.id == batch_id, Batch.mentor_id == mentor_id)
    )
    row = res.one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="Student not found")
    return row[0], row[1]


async def _load(batch_id: int, student_id: int, mentor: Mentor, db: AsyncSession) -> dict:
    student, batch = await _guard(batch_id, student_id, mentor.id, db)
    return await build_snapshot(student, batch)


async def _saved(student_id: int, db: AsyncSession) -> dict[str, AIReport]:
    res = await db.execute(select(AIReport).where(AIReport.student_id == student_id))
    return {r.kind: r for r in res.scalars().all()}


async def _generate_and_save(kind: str, generator, batch_id: int, student_id: int,
                             mentor: Mentor, db: AsyncSession) -> AIReport:
    """Run the generator on the student's records and keep the result as the latest of its kind."""
    snapshot = await _load(batch_id, student_id, mentor, db)
    try:
        content, model = await generator(render_context(snapshot))
    except AIError as e:
        raise HTTPException(status_code=502, detail=str(e))

    saved = (await _saved(student_id, db)).get(kind)
    if saved:
        saved.content = content
        saved.model = model
        saved.created_at = datetime.now(timezone.utc)
    else:
        saved = AIReport(student_id=student_id, batch_id=batch_id, kind=kind, content=content, model=model)
        db.add(saved)
    await db.commit()
    await db.refresh(saved)
    return saved


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.get(
    "/batches/{batch_id}/students/{student_id}/ai/overview",
    response_model=OverviewResponse,
    tags=["AI"],
)
async def get_student_overview(
    batch_id: int,
    student_id: int,
    db: AsyncSession = Depends(get_db),
    mentor: Mentor = Depends(get_current_mentor),
):
    """Computed metrics and risk level for a student, plus the last saved AI report and study plan."""
    student, batch = await _guard(batch_id, student_id, mentor.id, db)
    snapshot, reports = await asyncio.gather(
        build_snapshot(student, batch),
        fetch(select(AIReport).where(AIReport.student_id == student_id)),
    )
    saved = {r.kind: r for r in reports}
    return OverviewResponse(snapshot=snapshot, report=saved.get("report"), schedule=saved.get("schedule"))


@router.post(
    "/batches/{batch_id}/students/{student_id}/ai/report",
    response_model=SavedReport,
    tags=["AI"],
)
async def get_student_report(
    batch_id: int,
    student_id: int,
    db: AsyncSession = Depends(get_db),
    mentor: Mentor = Depends(get_current_mentor),
):
    """Generate (and save) a structured AI performance report for a student."""
    return await _generate_and_save("report", generate_report, batch_id, student_id, mentor, db)


@router.post(
    "/batches/{batch_id}/students/{student_id}/ai/schedule",
    response_model=SavedReport,
    tags=["AI"],
)
async def get_study_schedule(
    batch_id: int,
    student_id: int,
    db: AsyncSession = Depends(get_db),
    mentor: Mentor = Depends(get_current_mentor),
):
    """Generate (and save) a structured one-week study plan for a student."""
    return await _generate_and_save("schedule", generate_schedule, batch_id, student_id, mentor, db)


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
    snapshot = await _load(batch_id, student_id, mentor, db)
    try:
        text = await chat(
            context=render_context(snapshot),
            history=[{"role": m.role, "content": m.content} for m in payload.history],
            user_message=payload.message,
        )
    except AIError as e:
        raise HTTPException(status_code=502, detail=str(e))
    return AIResponse(text=text)
