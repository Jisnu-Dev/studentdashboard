from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.api.v1.api import api_router
from app.database import engine
from app.models import Base


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Auto-create all DB tables on startup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        # Idempotent migrations for new columns on existing tables
        migrations = [
            "ALTER TABLE IF EXISTS mentor_meetings ADD COLUMN IF NOT EXISTS academic_year VARCHAR(20)",
            "ALTER TABLE IF EXISTS mentor_meetings ADD COLUMN IF NOT EXISTS year_of_study VARCHAR(20)",
        ]
        for sql in migrations:
            await conn.execute(text(sql))
    yield
    await engine.dispose()



app = FastAPI(
    title="Student Dashboard API",
    description="Backend API for the Student Dashboard application",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS — allow all origins for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount the v1 API router
app.include_router(api_router, prefix="/api/v1")


@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "healthy"}
