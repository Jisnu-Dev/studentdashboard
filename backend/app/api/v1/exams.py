from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_mentor, get_db
from app.models.exam import ExamSetup, StudentExamMarks
from app.models.mentor import Mentor
from app.models.mentor_file import RemedialAction
from app.models.student import Batch, Student
from app.schemas.exam import (
    BulkMarksPayload,
    ExamSetupCreate,
    ExamSetupResponse,
    ExamSetupUpdate,
    RemedialActionCreate,
    RemedialActionResponse,
    ResultAnalysisResponse,
    StudentMarksResponse,
    SubjectAnalysis,
)
from app.services.exam_pdf_service import generate_pt_marks_pdf, generate_semester_pdf
from app.services.mentor_file_pdf_service import generate_result_analysis_pdf

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


def _check_pass_mark(setup: ExamSetup) -> None:
    if setup.pt_pass_mark > setup.pt_max_marks:
        raise HTTPException(
            status_code=422,
            detail=f"Pass mark ({setup.pt_pass_mark}) cannot be more than the maximum marks ({setup.pt_max_marks})",
        )


def _check_marks_within_max(rows: list[tuple[str, dict, dict]], max_marks: int) -> None:
    """rows: (label, pt1_marks, pt2_marks). Non-numeric entries such as AB are allowed."""
    for label, pt1, pt2 in rows:
        for test, marks in (("PT1", pt1), ("PT2", pt2)):
            for code, value in (marks or {}).items():
                try:
                    number = float(str(value).strip())
                except ValueError:
                    continue
                if number < 0 or number > max_marks:
                    raise HTTPException(
                        status_code=422,
                        detail=f"{test} mark {value} for {code} ({label}) is outside 0 to {max_marks}",
                    )


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
    data = payload.model_dump()
    if data["pt_pass_mark"] is None:
        data["pt_pass_mark"] = (data["pt_max_marks"] + 1) // 2
    setup = ExamSetup(batch_id=batch_id, mentor_id=mentor.id, **data)
    _check_pass_mark(setup)
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
    changes = payload.model_dump(exclude_none=True)
    # Changing the maximum without giving a pass mark keeps the same pass percentage
    if "pt_max_marks" in changes and "pt_pass_mark" not in changes:
        changes["pt_pass_mark"] = round(setup.pt_pass_mark * changes["pt_max_marks"] / setup.pt_max_marks)
    for k, v in changes.items():
        setattr(setup, k, v)
    _check_pass_mark(setup)
    if "pt_max_marks" in changes:
        records = await _build_student_records(exam_id, db)
        _check_marks_within_max(
            [(r["register_number"], r["pt1_marks"], r["pt2_marks"]) for r in records], setup.pt_max_marks
        )
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
    setup = await _get_setup(exam_id, batch_id, db)
    _check_marks_within_max(
        [(f"student #{rec.student_id}", rec.pt1_marks, rec.pt2_marks) for rec in payload.records],
        setup.pt_max_marks,
    )

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


# ══════════════════════════════════════════════════════════════════════════════
# Result analysis
# ══════════════════════════════════════════════════════════════════════════════

EXAM_TYPES = {
    "pt1": ("pt1_marks", "PERIODICAL TEST I RESULTS"),
    "pt2": ("pt2_marks", "PERIODICAL TEST II RESULTS"),
    "semester": ("semester_grades", "END SEMESTER RESULTS"),
}
ABSENT_VALUES = {"AB", "A", "ABS", "ABSENT"}
FAIL_GRADES = {"U", "RA", "F", "FAIL"}
NOT_APPEARED_GRADES = ABSENT_VALUES | {"W", "WD", "SA"}


def _classify(value: str, exam_type: str, pt_pass_mark: int) -> str | None:
    """'pass' | 'fail' | 'absent', or None when nothing was entered."""
    v = (value or "").strip().upper()
    if not v:
        return None
    if exam_type == "semester":
        if v in NOT_APPEARED_GRADES:
            return "absent"
        return "fail" if v in FAIL_GRADES else "pass"
    if v in ABSENT_VALUES:
        return "absent"
    try:
        return "pass" if float(v) >= pt_pass_mark else "fail"
    except ValueError:
        return None


async def _analyse(setup: ExamSetup, exam_type: str, db: AsyncSession) -> list[SubjectAnalysis]:
    if exam_type not in EXAM_TYPES:
        raise HTTPException(status_code=422, detail="exam must be one of: pt1, pt2, semester")
    marks_key = EXAM_TYPES[exam_type][0]
    records = await _build_student_records(setup.id, db)
    details = setup.subject_details or {}

    out = []
    for code in setup.subject_codes:
        passed = failed = absent = 0
        failed_students = []
        for rec in records:
            outcome = _classify(rec[marks_key].get(code, ""), exam_type, setup.pt_pass_mark)
            if outcome == "pass":
                passed += 1
            elif outcome == "fail":
                failed += 1
                failed_students.append(f"{rec['register_number']} - {rec['name']}")
            elif outcome == "absent":
                absent += 1
        attended = passed + failed
        out.append(SubjectAnalysis(
            subject_code=code,
            subject_name=details.get(code, {}).get("name", ""),
            faculty=details.get(code, {}).get("faculty", ""),
            attended=attended,
            passed=passed,
            failed=failed,
            absent=absent,
            pass_percentage=round(passed * 100 / attended, 2) if attended else 0.0,
            failed_students=failed_students,
        ))
    return out


async def _get_remedial_with_students(exam_id: int, exam_type: str | None, db: AsyncSession) -> list[tuple]:
    query = (
        select(RemedialAction, Student)
        .join(Student, RemedialAction.student_id == Student.id)
        .where(RemedialAction.exam_setup_id == exam_id)
        .order_by(Student.name, RemedialAction.id)
    )
    if exam_type:
        query = query.where(RemedialAction.exam_type == exam_type)
    result = await db.execute(query)
    return result.all()


@router.get(
    "/batches/{batch_id}/exams/{exam_id}/analysis",
    response_model=ResultAnalysisResponse,
    tags=["Exams"],
)
async def get_result_analysis(
    batch_id: int, exam_id: int,
    exam: str = "pt1",
    db: AsyncSession = Depends(get_db),
    mentor: Mentor = Depends(get_current_mentor),
):
    """Subject-wise attended / pass / fail / absent counts for PT I, PT II or the semester exam."""
    await _get_batch(batch_id, mentor.id, db)
    setup = await _get_setup(exam_id, batch_id, db)
    return ResultAnalysisResponse(
        exam_type=exam,
        pt_max_marks=setup.pt_max_marks,
        pt_pass_mark=setup.pt_pass_mark,
        subjects=await _analyse(setup, exam, db),
    )


@router.get(
    "/batches/{batch_id}/exams/{exam_id}/analysis/pdf",
    response_class=Response,
    tags=["Exams"],
)
async def export_result_analysis_pdf(
    batch_id: int, exam_id: int,
    exam: str = "pt1",
    db: AsyncSession = Depends(get_db),
    mentor: Mentor = Depends(get_current_mentor),
):
    """Download the result analysis (with remedial actions) as PDF."""
    batch = await _get_batch(batch_id, mentor.id, db)
    setup = await _get_setup(exam_id, batch_id, db)
    subjects = await _analyse(setup, exam, db)
    remedial = await _get_remedial_with_students(exam_id, exam, db)

    pdf = generate_result_analysis_pdf(
        department=batch.department,
        academic_year=setup.academic_year,
        semester=setup.semester,
        exam_title=EXAM_TYPES[exam][1],
        mentor_name=mentor.name,
        subjects=[s.model_dump() for s in subjects],
        remedial_actions=[
            {
                "register_number": s.register_number,
                "name": s.name,
                "subjects": r.subjects,
                "action_taken": r.action_taken,
                "impact": r.impact,
            }
            for r, s in remedial
        ],
    )
    fname = f"result_analysis_{exam}_{setup.semester}_{batch.batch_year}.pdf".replace(" ", "_")
    return Response(content=pdf, media_type="application/pdf",
                    headers={"Content-Disposition": f'attachment; filename="{fname}"'})


# ══════════════════════════════════════════════════════════════════════════════
# Remedial actions
# ══════════════════════════════════════════════════════════════════════════════

@router.get(
    "/batches/{batch_id}/exams/{exam_id}/remedial",
    response_model=list[RemedialActionResponse],
    tags=["Exams"],
)
async def list_remedial_actions(
    batch_id: int, exam_id: int,
    db: AsyncSession = Depends(get_db),
    mentor: Mentor = Depends(get_current_mentor),
):
    await _get_batch(batch_id, mentor.id, db)
    await _get_setup(exam_id, batch_id, db)
    rows = await _get_remedial_with_students(exam_id, None, db)
    return [
        RemedialActionResponse.model_validate(r).model_copy(
            update={"student_name": s.name, "register_number": s.register_number}
        )
        for r, s in rows
    ]


@router.post(
    "/batches/{batch_id}/exams/{exam_id}/remedial",
    response_model=RemedialActionResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Exams"],
)
async def create_remedial_action(
    batch_id: int, exam_id: int,
    payload: RemedialActionCreate,
    db: AsyncSession = Depends(get_db),
    mentor: Mentor = Depends(get_current_mentor),
):
    """Record the remedial action taken for a failed student / slow learner and its impact."""
    await _get_batch(batch_id, mentor.id, db)
    await _get_setup(exam_id, batch_id, db)
    result = await db.execute(
        select(Student).where(Student.id == payload.student_id, Student.batch_id == batch_id)
    )
    student = result.scalar_one_or_none()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    action = RemedialAction(exam_setup_id=exam_id, **payload.model_dump())
    db.add(action)
    await db.commit()
    await db.refresh(action)
    return RemedialActionResponse.model_validate(action).model_copy(
        update={"student_name": student.name, "register_number": student.register_number}
    )


@router.delete(
    "/batches/{batch_id}/exams/{exam_id}/remedial/{action_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["Exams"],
)
async def delete_remedial_action(
    batch_id: int, exam_id: int, action_id: int,
    db: AsyncSession = Depends(get_db),
    mentor: Mentor = Depends(get_current_mentor),
):
    await _get_batch(batch_id, mentor.id, db)
    await _get_setup(exam_id, batch_id, db)
    result = await db.execute(
        select(RemedialAction).where(
            RemedialAction.id == action_id, RemedialAction.exam_setup_id == exam_id
        )
    )
    action = result.scalar_one_or_none()
    if not action:
        raise HTTPException(status_code=404, detail="Remedial action not found")
    await db.delete(action)
    await db.commit()
