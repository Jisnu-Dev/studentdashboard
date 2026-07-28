from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_mentor, get_db
from app.core.security import create_access_token, hash_password, verify_password
from app.models.mentor import Mentor
from app.schemas.auth import MentorRegister, MentorResponse, Token

router = APIRouter()


@router.post("/register", response_model=MentorResponse, status_code=status.HTTP_201_CREATED)
async def register(payload: MentorRegister, db: AsyncSession = Depends(get_db)):
    """Register a new mentor account."""
    # Check email not already taken
    result = await db.execute(select(Mentor).where(Mentor.email == payload.email))
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A mentor with this email already exists",
        )

    mentor = Mentor(
        name=payload.name,
        email=payload.email,
        hashed_password=hash_password(payload.password),
    )
    db.add(mentor)
    await db.commit()
    await db.refresh(mentor)
    return mentor


@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
):
    """Login with email + password, returns a JWT access token.
    
    Uses OAuth2 form fields: `username` = email, `password` = password.
    """
    result = await db.execute(select(Mentor).where(Mentor.email == form_data.username))
    mentor = result.scalar_one_or_none()

    if not mentor or not verify_password(form_data.password, mentor.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = create_access_token(data={"sub": str(mentor.id)})
    return Token(access_token=token)


@router.get("/me", response_model=MentorResponse)
async def get_me(current_mentor: Mentor = Depends(get_current_mentor)):
    """Return the currently authenticated mentor's profile."""
    return current_mentor
