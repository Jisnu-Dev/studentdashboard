from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel

AttendanceStatus = Literal["Punctual", "Occasionally Tardy", "Habitually late", "Other"]
DisciplineStatus = Literal["Good", "Unkept", "Other"]
AttitudeStatus = Literal["Willing, Eager, Pleasant", "Other"]
ReasonInitiated = Literal["Student Initiated", "Institute Initiated"]


class CounselingCreate(BaseModel):
    counseling_date: date
    academic_year: str                   # e.g. "2024-2025"

    # Q1
    reason_initiated_by: ReasonInitiated
    reason_details: str | None = None

    # Q2
    attendance_status: AttendanceStatus
    attendance_other: str | None = None
    discipline_status: DisciplineStatus
    discipline_other: str | None = None
    attitude_status: AttitudeStatus
    attitude_other: str | None = None

    # Q3-5
    difficulty_meeting_demands: bool = False
    difficulty_explanation: str | None = None
    corrective_action_needed: bool = False
    corrective_action_explanation: str | None = None
    next_session_needed: bool = False
    next_session_explanation: str | None = None


class CounselingResponse(BaseModel):
    id: int
    student_id: int
    batch_id: int
    mentor_id: int

    counseling_date: date
    academic_year: str

    reason_initiated_by: str
    reason_details: str | None
    attendance_status: str
    attendance_other: str | None
    discipline_status: str
    discipline_other: str | None
    attitude_status: str
    attitude_other: str | None
    difficulty_meeting_demands: bool
    difficulty_explanation: str | None
    corrective_action_needed: bool
    corrective_action_explanation: str | None
    next_session_needed: bool
    next_session_explanation: str | None
    created_at: datetime

    model_config = {"from_attributes": True}
