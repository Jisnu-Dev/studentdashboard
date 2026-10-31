"""
Student insights — everything the system knows about one student, analysed without AI.

  - build_snapshot()   — collect all records and compute metrics + a rule-based risk level
  - render_context()   — turn a snapshot into the text the AI model is given
"""

import asyncio

from sqlalchemy import select

from app.database import ReadOnlySession
from app.models.counseling import CounselingSession
from app.models.exam import ExamSetup, StudentExamMarks
from app.models.meeting import MentorMeeting
from app.models.meeting_attendance import MeetingAttendance
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

ABSENT_VALUES = {"AB", "A", "ABS", "ABSENT"}
FAIL_GRADES = {"U", "RA", "F", "FAIL"}

# Risk scoring thresholds
HIGH_RISK_SCORE = 5
MEDIUM_RISK_SCORE = 2
LOW_PT_AVERAGE = 50.0
MODERATE_PT_AVERAGE = 60.0
LOW_MEETING_ATTENDANCE = 75.0


async def fetch(statement, scalars: bool = True) -> list:
    """Run one read-only query on its own connection, so independent queries can run in parallel."""
    async with ReadOnlySession() as session:
        result = await session.execute(statement)
        return list(result.scalars().all()) if scalars else list(result.all())


def _num(value) -> float | None:
    try:
        return float(str(value).strip())
    except (TypeError, ValueError):
        return None


def _is_absent(value) -> bool:
    return str(value or "").strip().upper() in ABSENT_VALUES


def _avg(values: list[float]) -> float | None:
    return round(sum(values) / len(values), 1) if values else None


def _subject_rows(setup: ExamSetup, own: StudentExamMarks | None, all_marks: list[StudentExamMarks]) -> list[dict]:
    """One row per subject: this student's marks next to the class average."""
    details = setup.subject_details or {}
    rows = []
    for code in setup.subject_codes:
        pt1 = (own.pt1_marks or {}).get(code, "") if own else ""
        pt2 = (own.pt2_marks or {}).get(code, "") if own else ""
        grade = (own.semester_grades or {}).get(code, "") if own else ""

        latest = pt2 if str(pt2).strip() else pt1
        latest_num = _num(latest)
        if str(grade).strip().upper() in FAIL_GRADES:
            status = "fail"
        elif _is_absent(latest):
            status = "absent"
        elif latest_num is None:
            status = "pass" if str(grade).strip() else "none"
        else:
            status = "fail" if latest_num < setup.pt_pass_mark else "pass"

        rows.append({
            "code": code,
            "name": details.get(code, {}).get("name", ""),
            "pt1": str(pt1),
            "pt2": str(pt2),
            "grade": str(grade),
            "class_avg_pt1": _avg([n for m in all_marks if (n := _num((m.pt1_marks or {}).get(code))) is not None]),
            "class_avg_pt2": _avg([n for m in all_marks if (n := _num((m.pt2_marks or {}).get(code))) is not None]),
            "status": status,
        })
    return rows


def _pt_metrics(exams: list[dict]) -> dict:
    """Average of the most recent periodical test, and the PT I -> PT II change."""
    out = {"pt_average_pct": None, "pt_average_label": "", "pt_trend_pct": None, "pt_trend_label": "",
           "failed_subjects": [], "absent_subjects": []}

    for exam in reversed(exams):
        for key, label in (("pt2", "PT II"), ("pt1", "PT I")):
            marks = [n for s in exam["subjects"] if (n := _num(s[key])) is not None]
            if marks:
                out["pt_average_pct"] = round(sum(marks) * 100 / (len(marks) * exam["pt_max_marks"]), 1)
                out["pt_average_label"] = f"{label}, {exam['semester']}"
                out["failed_subjects"] = [
                    s["code"] for s in exam["subjects"]
                    if (n := _num(s[key])) is not None and n < exam["pt_pass_mark"]
                ]
                out["absent_subjects"] = [s["code"] for s in exam["subjects"] if _is_absent(s[key])]
                break
        if out["pt_average_pct"] is not None:
            break

    for exam in reversed(exams):
        pairs = [(a, b) for s in exam["subjects"]
                 if (a := _num(s["pt1"])) is not None and (b := _num(s["pt2"])) is not None]
        if pairs:
            change = sum(b - a for a, b in pairs) * 100 / (len(pairs) * exam["pt_max_marks"])
            out["pt_trend_pct"] = round(change, 1)
            out["pt_trend_label"] = exam["semester"]
            break
    return out


def _assess_risk(metrics: dict, counseling: list[dict], condonations: list[dict]) -> dict:
    """Rule-based risk level. Every point added comes with the reason shown to the mentor."""
    score, reasons = 0, []

    failed = metrics["failed_subjects"]
    if failed:
        score += min(len(failed) * 2, 4)
        reasons.append(f"Below the pass mark in {len(failed)} subject(s) in the latest test: {', '.join(failed)}")

    if metrics["absent_subjects"]:
        score += 1
        reasons.append(f"Absent for the latest test in: {', '.join(metrics['absent_subjects'])}")

    if metrics["arrears_total"] > 0:
        score += 2
        reasons.append(f"{metrics['arrears_total']} arrear(s) in semester examinations")

    average = metrics["pt_average_pct"]
    if average is not None and average < LOW_PT_AVERAGE:
        score += 2
        reasons.append(f"Latest test average is {average}%, below {LOW_PT_AVERAGE:g}%")
    elif average is not None and average < MODERATE_PT_AVERAGE:
        score += 1
        reasons.append(f"Latest test average is {average}%, below {MODERATE_PT_AVERAGE:g}%")

    total = metrics["meetings_total"]
    if total and metrics["meetings_attended"] * 100 / total < LOW_MEETING_ATTENDANCE:
        score += 1
        reasons.append(f"Attended only {metrics['meetings_attended']} of {total} mentor meetings")

    if condonations:
        score += 1
        reasons.append(f"{len(condonations)} condonation application(s) for attendance shortage")

    if counseling and counseling[-1]["corrective_action"]:
        score += 1
        reasons.append("Latest counseling session recorded that corrective action is needed")

    level = "High" if score >= HIGH_RISK_SCORE else "Medium" if score >= MEDIUM_RISK_SCORE else "Low"
    if not reasons:
        reasons.append("No concerns found in the recorded data")
    return {"level": level, "score": score, "reasons": reasons}


async def build_snapshot(student: Student, batch: Batch) -> dict:
    """Collect every record of the student and compute the metrics shown to the mentor and the AI."""
    sid = student.id
    setup_ids = select(ExamSetup.id).where(ExamSetup.batch_id == batch.id)

    (setups, all_marks, results, attendance_rows, sessions, achievement_rows, parent_rows,
     communication_rows, leave_rows, condonation_rows, remedial_rows) = await asyncio.gather(
        fetch(select(ExamSetup).where(ExamSetup.batch_id == batch.id).order_by(ExamSetup.created_at, ExamSetup.id)),
        fetch(select(StudentExamMarks).where(StudentExamMarks.exam_setup_id.in_(setup_ids))),
        fetch(select(SemesterResult).where(SemesterResult.student_id == sid)),
        fetch(
            select(MeetingAttendance, MentorMeeting)
            .join(MentorMeeting, MeetingAttendance.meeting_id == MentorMeeting.id)
            .where(MeetingAttendance.student_id == sid, MentorMeeting.batch_id == batch.id)
            .order_by(MentorMeeting.meeting_date),
            scalars=False,
        ),
        fetch(select(CounselingSession).where(CounselingSession.student_id == sid)
               .order_by(CounselingSession.counseling_date)),
        fetch(select(Achievement).where(Achievement.student_id == sid).order_by(Achievement.event_date, Achievement.id)),
        fetch(select(ParentMeeting).where(ParentMeeting.student_id == sid).order_by(ParentMeeting.meeting_date)),
        fetch(select(CommunicationRecord).where(CommunicationRecord.student_id == sid)
               .order_by(CommunicationRecord.communication_date)),
        fetch(select(StudentDocument).where(
            StudentDocument.student_id == sid, StudentDocument.category == "medical_leave"
        ).order_by(StudentDocument.from_date)),
        fetch(select(Condonation).where(Condonation.student_id == sid).order_by(Condonation.id)),
        fetch(
            select(RemedialAction, ExamSetup)
            .join(ExamSetup, RemedialAction.exam_setup_id == ExamSetup.id)
            .where(RemedialAction.student_id == sid)
            .order_by(ExamSetup.created_at, RemedialAction.id),
            scalars=False,
        ),
    )

    # Exams: this student's marks with the class average per subject
    marks_by_setup: dict[int, list[StudentExamMarks]] = {}
    for m in all_marks:
        marks_by_setup.setdefault(m.exam_setup_id, []).append(m)

    exams = []
    for setup in setups:
        rows = marks_by_setup.get(setup.id, [])
        own = next((m for m in rows if m.student_id == sid), None)
        exams.append({
            "semester": setup.semester,
            "academic_year": setup.academic_year,
            "pt_max_marks": setup.pt_max_marks,
            "pt_pass_mark": setup.pt_pass_mark,
            "subjects": _subject_rows(setup, own, rows),
        })

    # Semester results
    result = results[0] if results else None
    gpa = (result.gpa or {}) if result else {}
    arrears = (result.arrears or {}) if result else {}
    arrears_total = int(sum(n for v in arrears.values() if (n := _num(v)) is not None))

    meetings = [
        {
            "date": str(meeting.meeting_date),
            "is_present": att.is_present,
            "points": att.points_discussed or [],
            "actions": att.action_planned or [],
        }
        for att, meeting in attendance_rows
    ]

    counseling = [
        {
            "date": str(c.counseling_date),
            "reason": c.reason_details or c.reason_initiated_by,
            "attendance": c.attendance_other or c.attendance_status,
            "discipline": c.discipline_other or c.discipline_status,
            "attitude": c.attitude_other or c.attitude_status,
            "difficulty": c.difficulty_explanation if c.difficulty_meeting_demands else None,
            "corrective_action": (c.corrective_action_explanation or "Yes") if c.corrective_action_needed else None,
            "next_session": (c.next_session_explanation or "Yes") if c.next_session_needed else None,
        }
        for c in sessions
    ]

    # Mentor file records
    achievements = [
        {"event": a.event_name, "category": a.category, "level": a.level, "result": a.result,
         "academic_year": a.academic_year}
        for a in achievement_rows
    ]
    parent_meetings = [
        {"date": str(p.meeting_date), "parent": f"{p.parent_name} ({p.relationship_with_student})",
         "academic_performance": p.academic_performance, "attendance": p.attendance, "concerns": p.concerns,
         "action_plan": p.action_plan or [], "action_details": p.action_details}
        for p in parent_rows
    ]
    communications = [
        {"date": str(c.communication_date), "with": c.contact_person, "details": c.details,
         "feedback": c.feedback, "action": c.action_taken}
        for c in communication_rows
    ]
    medical_leaves = [
        {"from": str(d.from_date) if d.from_date else "", "to": str(d.to_date) if d.to_date else "",
         "reason": d.notes or d.title}
        for d in leave_rows
    ]
    condonations = [
        {"exam": c.exam_month_year, "semester": c.semester, "attendance": c.attendance_percentage, "reason": c.reason}
        for c in condonation_rows
    ]
    remedial_actions = [
        {"semester": setup.semester, "exam_type": r.exam_type, "subjects": r.subjects,
         "action": r.action_taken, "impact": r.impact}
        for r, setup in remedial_rows
    ]

    metrics = {
        "cgpa": result.cgpa if result else "",
        "arrears_total": arrears_total,
        "meetings_attended": sum(1 for m in meetings if m["is_present"]),
        "meetings_total": len(meetings),
        "counseling_sessions": len(counseling),
        "achievements": len(achievements),
        **_pt_metrics(exams),
    }

    return {
        "student": {"name": student.name, "register_number": student.register_number},
        "batch": {"department": batch.department, "batch_year": batch.batch_year},
        "metrics": metrics,
        "risk": _assess_risk(metrics, counseling, condonations),
        "exams": exams,
        "gpa": gpa,
        "arrears": arrears,
        "meetings": meetings,
        "counseling": counseling,
        "achievements": achievements,
        "parent_meetings": parent_meetings,
        "communications": communications,
        "medical_leaves": medical_leaves,
        "condonations": condonations,
        "remedial_actions": remedial_actions,
    }


# ── Text context for the AI model ──────────────────────────────────────────────

def render_context(snap: dict) -> str:
    """Structured plain-text summary of a snapshot. Sections with no data are left out."""
    m, risk = snap["metrics"], snap["risk"]
    lines = [
        "=== STUDENT PROFILE ===",
        f"Name: {snap['student']['name']}",
        f"Register Number: {snap['student']['register_number']}",
        f"Department: {snap['batch']['department']}",
        f"Batch: {snap['batch']['batch_year']}",
        "",
        "=== SYSTEM ANALYSIS (computed from the records, treat as fact) ===",
        f"Risk level: {risk['level']}",
    ]
    lines += [f"  - {reason}" for reason in risk["reasons"]]
    if m["pt_average_pct"] is not None:
        lines.append(f"Latest test average: {m['pt_average_pct']}% ({m['pt_average_label']})")
    if m["pt_trend_pct"] is not None:
        lines.append(f"Change from PT I to PT II ({m['pt_trend_label']}): {m['pt_trend_pct']:+} percentage points")
    if m["cgpa"]:
        lines.append(f"CGPA: {m['cgpa']}")
    lines.append(f"Total arrears: {m['arrears_total']}")
    if m["meetings_total"]:
        lines.append(f"Mentor meetings attended: {m['meetings_attended']} of {m['meetings_total']}")
    lines.append("")

    if snap["exams"]:
        lines.append("=== EXAM MARKS (student's mark, with the class average in brackets) ===")
        for exam in snap["exams"]:
            lines.append(f"\n[{exam['semester']} - {exam['academic_year']}] "
                         f"PT marks are out of {exam['pt_max_marks']}, pass mark {exam['pt_pass_mark']}")
            for s in exam["subjects"]:
                name = f" {s['name']}" if s["name"] else ""

                def cell(mark, average):
                    if not str(mark).strip():
                        return "not entered"
                    return f"{mark} (class avg {average})" if average is not None else str(mark)

                lines.append(
                    f"  {s['code']}{name}: PT1={cell(s['pt1'], s['class_avg_pt1'])}  "
                    f"PT2={cell(s['pt2'], s['class_avg_pt2'])}  Semester grade={s['grade'] or 'not entered'}"
                )
        lines.append("")

    if snap["gpa"]:
        lines.append("=== SEMESTER GPA AND ARREARS ===")
        for sem in sorted(snap["gpa"], key=lambda k: int(k) if str(k).isdigit() else 99):
            if str(snap["gpa"][sem]).strip():
                lines.append(f"  Semester {sem}: GPA {snap['gpa'][sem]}, arrears {snap['arrears'].get(sem) or 0}")
        lines.append("")

    if snap["meetings"]:
        lines.append("=== MENTOR MEETINGS ===")
        for meeting in snap["meetings"]:
            lines.append(f"  {meeting['date']} - {'Present' if meeting['is_present'] else 'Absent'}")
            lines += [f"    Point discussed: {p}" for p in meeting["points"]]
            lines += [f"    Action planned: {a}" for a in meeting["actions"]]
        lines.append("")

    if snap["counseling"]:
        lines.append("=== COUNSELING SESSIONS ===")
        for c in snap["counseling"]:
            lines.append(f"  [{c['date']}] Reason: {c['reason']}")
            lines.append(f"    Attendance: {c['attendance']}; Discipline: {c['discipline']}; Attitude: {c['attitude']}")
            for label, key in (("Difficulty", "difficulty"), ("Corrective action", "corrective_action"),
                               ("Next session", "next_session")):
                if c[key]:
                    lines.append(f"    {label}: {c[key]}")
        lines.append("")

    if snap["remedial_actions"]:
        lines.append("=== REMEDIAL ACTIONS TAKEN ===")
        for r in snap["remedial_actions"]:
            lines.append(f"  [{r['semester']} {r['exam_type']}] {r['subjects'] or ''}: {r['action']}"
                         + (f" -> Impact: {r['impact']}" if r["impact"] else ""))
        lines.append("")

    if snap["parent_meetings"]:
        lines.append("=== PARENT - TEACHERS MEETINGS ===")
        for p in snap["parent_meetings"]:
            lines.append(f"  [{p['date']}] with {p['parent']}")
            for label, key in (("Academic performance", "academic_performance"), ("Attendance", "attendance"),
                               ("Parent concerns", "concerns"), ("Follow-up", "action_details")):
                if p[key]:
                    lines.append(f"    {label}: {p[key]}")
            if p["action_plan"]:
                lines.append(f"    Action plan: {', '.join(p['action_plan'])}")
        lines.append("")

    if snap["communications"]:
        lines.append("=== COMMUNICATION RECORDS ===")
        for c in snap["communications"]:
            lines.append(f"  [{c['date']}] with {c['with']}: {c['details']}")
            if c["feedback"]:
                lines.append(f"    Feedback: {c['feedback']}")
            if c["action"]:
                lines.append(f"    Action taken: {c['action']}")
        lines.append("")

    if snap["medical_leaves"] or snap["condonations"]:
        lines.append("=== MEDICAL LEAVE AND CONDONATION ===")
        lines += [f"  Medical leave {l['from']} to {l['to']}: {l['reason']}" for l in snap["medical_leaves"]]
        lines += [f"  Condonation for {c['exam']} ({c['semester']}): attendance {c['attendance']}%, {c['reason']}"
                  for c in snap["condonations"]]
        lines.append("")

    if snap["achievements"]:
        lines.append("=== ACHIEVEMENTS ===")
        lines += [f"  {a['event']} ({a['category']}, {a['level']}): {a['result']}" for a in snap["achievements"]]
        lines.append("")

    return "\n".join(lines)
