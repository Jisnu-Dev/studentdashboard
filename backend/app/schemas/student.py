from datetime import datetime

from pydantic import BaseModel


# ── Student schemas ────────────────────────────────────────────────────────────

class StudentCreate(BaseModel):
    register_number: str
    name: str


class StudentUpdate(BaseModel):
    register_number: str | None = None
    name: str | None = None


class StudentResponse(BaseModel):
    id: int
    register_number: str
    name: str
    batch_id: int

    model_config = {"from_attributes": True}


# ── Batch schemas ──────────────────────────────────────────────────────────────

class BatchCreate(BaseModel):
    department: str
    batch_year: str  # e.g. "2023-2027"


class BatchUpdate(BaseModel):
    department: str | None = None
    batch_year: str | None = None


class BatchResponse(BaseModel):
    id: int
    department: str
    batch_year: str
    mentor_id: int
    created_at: datetime

    model_config = {"from_attributes": True}


class BatchWithStudents(BatchResponse):
    students: list[StudentResponse] = []
