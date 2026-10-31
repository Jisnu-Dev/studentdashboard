from fastapi import APIRouter

from app.api.v1 import auth, students, counseling, mentor_meetings, exams, ai, documents, mentor_file

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["Auth"])
api_router.include_router(students.router, prefix="/batches", tags=["Batches & Students"])
api_router.include_router(counseling.router, tags=["Counseling"])
api_router.include_router(mentor_meetings.router, tags=["Meetings"])
api_router.include_router(exams.router, tags=["Exams"])
api_router.include_router(ai.router, tags=["AI"])
api_router.include_router(documents.router, tags=["Documents"])
api_router.include_router(mentor_file.router, tags=["Mentor File"])
