from datetime import datetime

from pydantic import BaseModel, EmailStr


# ── Request schemas ────────────────────────────────────────────────────────────

class MentorRegister(BaseModel):
    name: str
    email: EmailStr
    password: str


class MentorLogin(BaseModel):
    email: EmailStr
    password: str


# ── Response schemas ───────────────────────────────────────────────────────────

class MentorResponse(BaseModel):
    id: int
    name: str
    email: EmailStr
    created_at: datetime

    model_config = {"from_attributes": True}


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    mentor_id: int | None = None
