from app.database import Base  # noqa: F401 - import Base so models can use it

# Import all models here so SQLAlchemy registers them with Base.metadata
from app.models.mentor import Mentor  # noqa: F401
from app.models.student import Batch, Student  # noqa: F401
from app.models.counseling import CounselingSession  # noqa: F401
from app.models.meeting import MentorMeeting  # noqa: F401
from app.models.meeting_attendance import MeetingAttendance  # noqa: F401
from app.models.exam import ExamSetup, StudentExamMarks  # noqa: F401
from app.models.ai_report import AIReport  # noqa: F401
from app.models.mentor_file import (  # noqa: F401
    Achievement,
    CommunicationRecord,
    Condonation,
    ParentMeeting,
    RemedialAction,
    SemesterResult,
    StudentDocument,
)
