from datetime import date, datetime

from pydantic import BaseModel, Field

DOCUMENT_CATEGORIES = ["personal_details", "medical_leave", "certificate", "condonation"]

ACHIEVEMENT_CATEGORIES = [
    "Technical Events",
    "Non-Technical Events",
    "Cultural Events",
    "Sports Events",
    "Social Service Activities",
    "Entrepreneurship and Innovation Activities",
    "Leadership and Personality Development Programs",
    "Placement and Career Development Events",
]


class _StudentInfo(BaseModel):
    # Flattened from join
    student_name: str | None = None
    register_number: str | None = None


# ── Documents ──────────────────────────────────────────────────────────────────

class DocumentResponse(_StudentInfo):
    id: int
    student_id: int
    batch_id: int
    category: str
    title: str
    notes: str | None
    from_date: date | None
    to_date: date | None
    file_name: str
    content_type: str
    file_size: int
    uploaded_at: datetime

    model_config = {"from_attributes": True}


# ── Communication records (mentor note) ────────────────────────────────────────

class CommunicationCreate(BaseModel):
    student_id: int
    communication_date: date
    contact_person: str = Field(..., example="Father")
    mode: str | None = None
    details: str
    feedback: str | None = None
    action_taken: str | None = None


class CommunicationResponse(_StudentInfo):
    id: int
    student_id: int
    batch_id: int
    communication_date: date
    contact_person: str
    mode: str | None
    details: str
    feedback: str | None
    action_taken: str | None

    model_config = {"from_attributes": True}


# ── Parent - Teachers Meeting ──────────────────────────────────────────────────

class ParentMeetingCreate(BaseModel):
    student_id: int
    academic_year: str = Field(..., example="2025-2026")
    meeting_date: date
    student_contact: str | None = None
    semester_year_branch: str | None = None
    parent_name: str
    relationship_with_student: str = Field(..., example="Father")
    parent_contact: str | None = None
    parent_address: str | None = None
    periodic_reports: str | None = None
    interacts_regularly: str | None = None
    satisfied_with_progress: str | None = None
    academic_performance: str | None = None
    co_curricular: str | None = None
    attendance: str | None = None
    discipline: str | None = None
    placements: str | None = None
    concerns: str | None = None
    other_remarks: str | None = None
    action_plan: list[str] = Field(default_factory=list)
    action_other: str | None = None
    action_details: str | None = None


class ParentMeetingResponse(ParentMeetingCreate, _StudentInfo):
    id: int
    batch_id: int

    model_config = {"from_attributes": True}


# ── Achievements ───────────────────────────────────────────────────────────────

class AchievementCreate(BaseModel):
    student_id: int
    academic_year: str = Field(..., example="2025-2026")
    semester: str | None = None
    category: str
    event_name: str
    level: str = Field(..., example="National")
    result: str = Field(..., example="Participation")
    event_date: date | None = None
    document_id: int | None = None


class AchievementResponse(AchievementCreate, _StudentInfo):
    id: int
    batch_id: int

    model_config = {"from_attributes": True}


# ── Condonation ────────────────────────────────────────────────────────────────

class CondonationCreate(BaseModel):
    student_id: int
    exam_month_year: str = Field(..., example="Nov 2025")
    degree_branch: str
    semester: str
    attendance_percentage: float = Field(..., ge=0, le=100)
    reason: str
    recommended: bool = True
    document_id: int | None = None


class CondonationResponse(CondonationCreate, _StudentInfo):
    id: int
    batch_id: int

    model_config = {"from_attributes": True}


# ── Semester results (GPA / CGPA / arrears) ────────────────────────────────────

class SemesterResultUpsert(BaseModel):
    student_id: int
    gpa: dict[str, str] = Field(default_factory=dict)      # {"1": "8.21"}
    arrears: dict[str, str] = Field(default_factory=dict)  # {"1": "2"}
    cgpa: str = ""


class BulkSemesterResultPayload(BaseModel):
    records: list[SemesterResultUpsert]


class SemesterResultResponse(SemesterResultUpsert, _StudentInfo):
    id: int
    batch_id: int

    model_config = {"from_attributes": True}


# ── Mentor file summary ────────────────────────────────────────────────────────

class MentorFileSummary(BaseModel):
    students: int
    personal_details: int      # students with a CAMPS profile uploaded
    counseling_sessions: int
    students_counseled: int
    meetings: int
    communications: int
    exam_setups: int
    remedial_actions: int
    parent_meetings: int
    medical_leaves: int
    achievements: int
    condonations: int
    semester_results: int      # students with GPA data entered
