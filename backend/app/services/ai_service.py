"""
Gemini AI service using google-genai SDK with gemini-3.5-flash-lite.

Provides:
  - build_student_context()  — assemble all student data into a rich text summary
  - generate_report()        — AI performance analysis + improvement tips
  - generate_schedule()      — AI-generated personalised study schedule
  - chat()                   — multi-turn chat with student context pre-loaded
"""

import asyncio
from google import genai
from google.genai import types

from app.core.config import settings

MODEL = "gemini-3.5-flash-lite"

SYSTEM_PROMPT = """You are an expert academic mentor assistant for Bannari Amman Institute of Technology (BIT).
You help mentors understand their students' academic performance and provide actionable, personalised guidance.
Always be encouraging, specific, and practical. Format responses clearly with sections and bullet points.
Base all analysis strictly on the provided student data."""


def _get_client() -> genai.Client:
    if not settings.GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY not configured")
    return genai.Client(api_key=settings.GEMINI_API_KEY)


def _generate_config() -> types.GenerateContentConfig:
    return types.GenerateContentConfig(
        system_instruction=SYSTEM_PROMPT,
        temperature=0.7,
        max_output_tokens=2048,
    )


async def _call_gemini(contents: list) -> str:
    """Call Gemini and collect all streamed chunks into one string."""
    client = _get_client()
    config = _generate_config()

    # Run the synchronous streaming call in a thread pool to avoid blocking
    def _stream():
        result = []
        for chunk in client.models.generate_content_stream(
            model=MODEL,
            contents=contents,
            config=config,
        ):
            if chunk.text:
                result.append(chunk.text)
        return "".join(result)

    text = await asyncio.to_thread(_stream)
    if not text:
        raise ValueError("Empty response from Gemini")
    return text


# ── Student context builder ────────────────────────────────────────────────────

def build_student_context(
    student: dict,
    batch: dict,
    exam_records: list[dict],
    attendance_records: list[dict],
    counseling_records: list[dict],
) -> str:
    """Build a structured text summary of a student for AI context."""
    lines = [
        "=== STUDENT PROFILE ===",
        f"Name: {student.get('name', 'N/A')}",
        f"Register Number: {student.get('register_number', 'N/A')}",
        f"Department: {batch.get('department', 'N/A')}",
        f"Batch Year: {batch.get('batch_year', 'N/A')}",
        "",
    ]

    if exam_records:
        lines.append("=== EXAM MARKS ===")
        for rec in exam_records:
            lines.append(f"\n[{rec['semester']} — {rec['academic_year']}]")
            for code in rec.get("subject_codes", []):
                pt1 = rec.get("pt1_marks", {}).get(code, "—")
                pt2 = rec.get("pt2_marks", {}).get(code, "—")
                grade = rec.get("semester_grades", {}).get(code, "—")
                lines.append(f"  {code}: PT1={pt1}  PT2={pt2}  Final Grade={grade}")
        lines.append("")

    if attendance_records:
        lines.append("=== MEETING ATTENDANCE ===")
        present = sum(1 for r in attendance_records if r.get("is_present"))
        lines.append(f"Attended {present} of {len(attendance_records)} meetings")
        for rec in attendance_records:
            status = "✓ Present" if rec.get("is_present") else "✗ Absent"
            lines.append(f"  {rec.get('meeting_date', '')} — {status}")
            for pt in rec.get("points_discussed", []):
                lines.append(f"    Issue: {pt}")
            for ac in rec.get("action_planned", []):
                lines.append(f"    Action: {ac}")
        lines.append("")

    if counseling_records:
        lines.append("=== COUNSELING SESSIONS ===")
        for cs in counseling_records:
            lines.append(f"\n[Session: {cs.get('date', 'N/A')}]")
            for q, a in (cs.get("responses") or {}).items():
                if a:
                    lines.append(f"  {q}: {a}")
        lines.append("")

    return "\n".join(lines)


# ── AI generators ──────────────────────────────────────────────────────────────

async def generate_report(context: str) -> str:
    prompt = f"""{context}

Please provide a comprehensive academic performance analysis for this student including:

1. **Overall Performance Summary** — strengths and areas of concern
2. **Subject-wise Analysis** — breakdown per subject, comparing PT1 vs PT2 trends
3. **Attendance & Engagement** — meeting attendance impact
4. **Key Issues Identified** — from counseling and meeting notes
5. **Improvement Recommendations** — specific, actionable steps for each weak area
6. **Motivational Message** — personalised encouragement

Be specific with numbers and subject codes from the data provided."""

    contents = [types.Content(role="user", parts=[types.Part.from_text(text=prompt)])]
    return await _call_gemini(contents)


async def generate_schedule(context: str) -> str:
    prompt = f"""{context}

Based on this student's performance data, create a detailed personalised weekly study schedule.

Include:
1. **Priority Subjects** — which subjects need the most attention and why
2. **Daily Study Plan (Mon–Sun)** — time blocks with specific subjects/topics
3. **Suggested Study Techniques** — per subject based on their weak areas
4. **Weekly Goals** — measurable targets for each subject
5. **Revision Strategy** — how to prepare for upcoming tests
6. **Tips for Consistency** — habit-building advice specific to their situation

Make the schedule realistic for a college student with ~4–6 hours of study time per day."""

    contents = [types.Content(role="user", parts=[types.Part.from_text(text=prompt)])]
    return await _call_gemini(contents)


async def chat(context: str, history: list[dict], user_message: str) -> str:
    """Multi-turn chat with student context pre-loaded as opening exchange."""
    contents = [
        types.Content(
            role="user",
            parts=[types.Part.from_text(
                text=f"Here is the complete profile of the student I want to discuss:\n\n{context}\n\nI'm ready to ask questions about this student."
            )],
        ),
        types.Content(
            role="model",
            parts=[types.Part.from_text(
                text="I've reviewed the student's complete profile including their exam marks, meeting attendance, and counseling records. I'm ready to help you analyze their performance and provide guidance. What would you like to know?"
            )],
        ),
    ]

    for msg in history:
        contents.append(types.Content(
            role=msg["role"],
            parts=[types.Part.from_text(text=msg["content"])],
        ))

    contents.append(types.Content(
        role="user",
        parts=[types.Part.from_text(text=user_message)],
    ))

    return await _call_gemini(contents)
