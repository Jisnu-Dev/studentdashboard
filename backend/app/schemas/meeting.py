from datetime import date, datetime

from pydantic import BaseModel, Field


DEFAULT_AGENDA = [
    "Discussion about academic activities.",
    "Discussion about participating in different events.",
    "Any other matter.",
]

YEAR_OPTIONS = ["I Year", "II Year", "III Year", "IV Year"]


class MeetingCreate(BaseModel):
    meeting_date: date
    meeting_time: str = Field(..., example="3.30 PM")
    location: str = Field(..., example="Department conference hall")
    semester: str = Field(..., example="I Year - Semester I")
    academic_year: str | None = Field(None, example="2025-2026")
    year_of_study: str | None = Field(None, example="I Year")
    agenda_items: list[str] = Field(default_factory=lambda: list(DEFAULT_AGENDA))


class MeetingUpdate(BaseModel):
    meeting_date: date | None = None
    meeting_time: str | None = None
    location: str | None = None
    semester: str | None = None
    academic_year: str | None = None
    year_of_study: str | None = None
    agenda_items: list[str] | None = None
    minutes_text: str | None = None


class MeetingResponse(BaseModel):
    id: int
    batch_id: int
    mentor_id: int
    meeting_number: int
    meeting_date: date
    meeting_time: str
    location: str
    semester: str
    academic_year: str | None
    year_of_study: str | None
    agenda_items: list[str]
    minutes_text: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Attendance ─────────────────────────────────────────────────────────────────

class AttendanceUpsert(BaseModel):
    student_id: int
    is_present: bool = True
    points_discussed: list[str] = Field(default_factory=list)
    action_planned: list[str] = Field(default_factory=list)


class BulkAttendancePayload(BaseModel):
    records: list[AttendanceUpsert]


class AttendanceResponse(BaseModel):
    id: int
    meeting_id: int
    student_id: int
    is_present: bool
    points_discussed: list[str]
    action_planned: list[str]

    # Flattened student info for convenience
    student_name: str | None = None
    register_number: str | None = None

    model_config = {"from_attributes": True}

