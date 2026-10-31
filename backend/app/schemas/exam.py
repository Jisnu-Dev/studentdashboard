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
    pt_max_marks: int = Field(default=100, gt=0, le=1000)      # each PT is out of this
    pt_pass_mark: int | None = Field(default=None, ge=0)       # defaults to half of the maximum


class ExamSetupUpdate(BaseModel):
    semester: str | None = None
    academic_year: str | None = None
    subject_codes: list[str] | None = None
    subject_details: dict[str, dict[str, str]] | None = None  # {code: {"name": ..., "faculty": ...}}
    pt_max_marks: int | None = Field(default=None, gt=0, le=1000)
    pt_pass_mark: int | None = Field(default=None, ge=0)


class ExamSetupResponse(BaseModel):
    id: int
    batch_id: int
    mentor_id: int
    semester: str
    academic_year: str
    subject_codes: list[str]
    subject_details: dict[str, dict[str, str]] = Field(default_factory=dict)
    pt_max_marks: int = 100
    pt_pass_mark: int = 50
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


# ── Result analysis ────────────────────────────────────────────────────────────

class SubjectAnalysis(BaseModel):
    subject_code: str
    subject_name: str = ""
    faculty: str = ""
    attended: int
    passed: int
    failed: int
    absent: int
    pass_percentage: float
    failed_students: list[str] = Field(default_factory=list)  # "REGNO - Name"


class ResultAnalysisResponse(BaseModel):
    exam_type: str   # "pt1" | "pt2" | "semester"
    pt_max_marks: int
    pt_pass_mark: int
    subjects: list[SubjectAnalysis]


class RemedialActionCreate(BaseModel):
    student_id: int
    exam_type: str = Field(..., pattern="^(pt1|pt2|semester)$")
    subjects: str | None = None
    action_taken: str
    impact: str | None = None


class RemedialActionResponse(BaseModel):
    id: int
    exam_setup_id: int
    student_id: int
    exam_type: str
    subjects: str | None
    action_taken: str
    impact: str | None

    student_name:    str | None = None
    register_number: str | None = None

    model_config = {"from_attributes": True}
