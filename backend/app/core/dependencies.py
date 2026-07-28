from typing import AsyncGenerator

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import decode_access_token
from app.database import AsyncSessionLocal
from app.models.mentor import Mentor

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


# ── DB session ─────────────────────────────────────────────────────────────────

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session


# ── Current mentor ─────────────────────────────────────────────────────────────

async def get_current_mentor(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> Mentor:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    payload = decode_access_token(token)
    if payload is None:
        raise credentials_exception

    mentor_id: int | None = payload.get("sub")
    if mentor_id is None:
        raise credentials_exception

    result = await db.execute(select(Mentor).where(Mentor.id == int(mentor_id)))
    mentor = result.scalar_one_or_none()

    if mentor is None:
        raise credentials_exception

    return mentor
