from datetime import datetime

from pydantic import BaseModel, Field

SEMESTERS = [
    "I Year - Semester I",
    "I Year - Semester II",
    "II Year - Semester III",
    "II Year - Semester IV",
    "III Year - Semester V",
    "III Year - Semester VI",
    "IV Year - Semester VII",
    "IV Year - Semester VIII",
]


# ── ExamSetup ──────────────────────────────────────────────────────────────────

class ExamSetupCreate(BaseModel):
    semester: str = Field(..., example="I Year - Semester I")
    academic_year: str = Field(..., example="2024-2025")
    subject_codes: list[str] = Field(..., min_length=1, example=["CS1001", "MA1001"])


class ExamSetupUpdate(BaseModel):
    semester: str | None = None
    academic_year: str | None = None
    subject_codes: list[str] | None = None


class ExamSetupResponse(BaseModel):
    id: int
    batch_id: int
    mentor_id: int
    semester: str
    academic_year: str
    subject_codes: list[str]
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Marks ──────────────────────────────────────────────────────────────────────

class StudentMarksUpsert(BaseModel):
    student_id: int
    pt1_marks:       dict[str, str] = Field(default_factory=dict)  # {subject_code: mark_string}
    pt2_marks:       dict[str, str] = Field(default_factory=dict)
    semester_grades: dict[str, str] = Field(default_factory=dict)  # {subject_code: grade}


class BulkMarksPayload(BaseModel):
    records: list[StudentMarksUpsert]


class StudentMarksResponse(BaseModel):
    id: int
    exam_setup_id: int
    student_id: int
    pt1_marks:       dict[str, str]
    pt2_marks:       dict[str, str]
    semester_grades: dict[str, str]

    # Flattened from join
    student_name:    str | None = None
    register_number: str | None = None

    model_config = {"from_attributes": True}
