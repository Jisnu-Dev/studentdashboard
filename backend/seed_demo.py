"""
Seed a demo mentor account with sample data for every Mentor File item.

Talks to the running backend over its HTTP API, so start the backend first:

    venv\\Scripts\\python seed_demo.py            # create the demo account and data
    venv\\Scripts\\python seed_demo.py --reset    # delete the demo batches and seed again

All names, numbers and records below are fictitious sample data.
"""

import io
import os
import sys

import httpx
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

API = os.environ.get("SEED_API_URL", "http://127.0.0.1:8000/api/v1")

# ── Demo login ─────────────────────────────────────────────────────────────────
DEMO_NAME = "Demo Mentor"
DEMO_EMAIL = "demo.mentor@example.com"
DEMO_PASSWORD = "MentorDemo@2026"

DEPARTMENT = "Computer Science and Engineering"
BATCH_YEAR = "2023-2027"

STUDENTS = [
    ("7376231CS101", "Aravind K"),
    ("7376231CS102", "Bhavya S"),
    ("7376231CS103", "Dinesh R"),
    ("7376231CS104", "Gayathri M"),
    ("7376231CS105", "Harish V"),
    ("7376231CS106", "Keerthana P"),
    ("7376231CS107", "Naveen T"),
    ("7376231CS108", "Priya D"),
]
ARAVIND, BHAVYA, DINESH, GAYATHRI, HARISH, KEERTHANA, NAVEEN, PRIYA = range(8)

# ── Exams ──────────────────────────────────────────────────────────────────────
SEM6 = {
    "semester": "III Year - Semester VI",
    "academic_year": "2025-2026",
    "pt_max_marks": 50,
    "subjects": [
        ("22CS601", "COMPILER DESIGN", "Dr. Meenakshi R"),
        ("22CS602", "CLOUD COMPUTING", "Prof. Senthil Kumar V"),
        ("22CS603", "MACHINE LEARNING", "Dr. Lavanya S, Prof. Arun Prakash M"),
        ("22CS604", "CRYPTOGRAPHY AND NETWORK SECURITY", "Dr. Rajesh Kannan P"),
        ("22CS607", "MACHINE LEARNING LABORATORY", "Dr. Lavanya S"),
    ],
    "pt1": [
        ["42", "38", "45", "40", "47"],
        ["46", "44", "48", "43", "49"],
        ["21", "30", "19", "28", "35"],
        ["39", "41", "37", "44", "45"],
        ["28", "24", "31", "22", "38"],
        ["47", "45", "49", "46", "50"],
        ["AB", "27", "23", "30", "36"],
        ["35", "33", "40", "36", "42"],
    ],
    "pt2": [
        ["44", "40", "46", "42", "48"],
        ["47", "45", "49", "46", "50"],
        ["29", "34", "27", "31", "38"],
        ["40", "43", "39", "45", "46"],
        ["31", "29", "34", "27", "40"],
        ["48", "46", "50", "47", "50"],
        ["33", "31", "29", "34", "39"],
        ["37", "36", "41", "38", "44"],
    ],
    "grades": [
        ["A+", "A", "A+", "A", "O"],
        ["O", "A+", "O", "A+", "O"],
        ["B", "B+", "U", "B", "A"],
        ["A", "A+", "A", "A+", "O"],
        ["B+", "B", "B+", "U", "A"],
        ["O", "O", "O", "O", "O"],
        ["B", "B+", "B", "B+", "A"],
        ["A", "A", "A+", "A", "A+"],
    ],
    "remedial": [
        (DINESH, "pt1", "22CS601, 22CS603",
         "Attended remedial classes twice a week and submitted two extra problem sheets.",
         "Improved to 29 and 27 in PT II; cleared both subjects."),
        (HARISH, "pt1", "22CS602, 22CS604",
         "Paired with a peer mentor and given weekly unit tests by the course faculty.",
         "Cleared both subjects in PT II (29 and 27)."),
        (NAVEEN, "pt1", "22CS601 (absent), 22CS603",
         "Retest arranged for the missed paper after medical leave; remedial classes for 22CS603.",
         "Scored 33 and 29 in PT II."),
        (DINESH, "semester", "22CS603",
         "Special coaching classes for the arrear paper and a fortnightly review with the mentor.",
         "Registered for the supplementary examination."),
        (HARISH, "semester", "22CS604",
         "Daily one-hour study schedule and practice with previous question papers.",
         "Registered for the supplementary examination."),
    ],
}

SEM7 = {
    "semester": "IV Year - Semester VII",
    "academic_year": "2026-2027",
    "pt_max_marks": 100,
    "subjects": [
        ("22CS701", "DEEP LEARNING", "Dr. Lavanya S"),
        ("22CS702", "BIG DATA ANALYTICS", "Prof. Karthik Raja N"),
        ("22CS703", "INTERNET OF THINGS", "Dr. Meenakshi R"),
        ("22CS704", "SOFTWARE PROJECT MANAGEMENT", "Prof. Senthil Kumar V"),
    ],
    "pt1": [
        ["78", "72", "81", "75"],
        ["88", "91", "86", "90"],
        ["46", "55", "41", "58"],
        ["74", "80", "77", "82"],
        ["52", "47", "60", "49"],
        ["93", "95", "90", "96"],
        ["61", "58", "49", "66"],
        ["70", "73", "76", "71"],
    ],
    "pt2": [[] for _ in STUDENTS],
    "grades": [[] for _ in STUDENTS],
    "remedial": [
        (DINESH, "pt1", "22CS701, 22CS703",
         "Remedial classes scheduled every Tuesday and Thursday; parent informed.", None),
        (HARISH, "pt1", "22CS702, 22CS704",
         "Extra assignments given and progress reviewed in the weekly mentor meeting.", None),
        (NAVEEN, "pt1", "22CS703",
         "Advised to attend the remedial class and complete the pending laboratory records.", None),
    ],
}

# ── Meetings ───────────────────────────────────────────────────────────────────
MEETINGS = [
    ("2026-08-07", ["Discussion about academic activities.",
                    "Review of Semester VI results and arrear status.",
                    "Any other matter."]),
    ("2026-08-21", ["Preparation for Periodical Test I.",
                    "Discussion about participating in different events.",
                    "Any other matter."]),
    ("2026-09-18", ["Review of Periodical Test I performance.",
                    "Placement training and PS level clearance.",
                    "Any other matter."]),
]

# Per-student notes used in the minutes: (points discussed, action planned)
MEETING_NOTES = {
    ARAVIND: (["Academic progress - consistent performance in all subjects",
               "PS level clearance - one level pending"],
              ["Advised to complete the pending PS level before the next meeting."]),
    BHAVYA: (["Academic progress - scoring above 85% in all subjects",
              "Participation in technical events"],
             ["Encouraged to take part in the national level hackathon."]),
    DINESH: (["Academic progress - low marks in two subjects",
              "Support for students with arrear courses - one arrear in Semester VI",
              "Attendance percentage as on date - 78%"],
             ["Attend remedial classes and complete extra practice assignments.",
              "Prepare a study plan for the arrear paper and review it weekly."]),
    GAYATHRI: (["Academic progress - good",
                "Reward points secured - on track"],
               ["Review reward points periodically."]),
    HARISH: (["Academic progress - below pass mark in two subjects",
              "Support for students with arrear courses - one arrear in Semester VI",
              "Participation in classes - needs improvement"],
             ["Follow a daily study schedule and track progress weekly.",
              "Parent to be informed about the performance."]),
    KEERTHANA: (["Academic progress - excellent",
                 "Placement preparation - attending aptitude training"],
                ["Encouraged to mentor two classmates in Machine Learning."]),
    NAVEEN: (["Attendance percentage as on date - 74%, low due to medical leave",
              "Academic progress - one subject below pass mark"],
             ["Advised to improve attendance; daily monitoring by the mentor.",
              "Attend remedial classes for the weak subject."]),
    PRIYA: (["Academic progress - satisfactory",
             "Participation in non-technical events"],
            ["Advised to complete the pending PS level."]),
}
ABSENTEES = {1: {NAVEEN}, 2: set(), 3: {HARISH}}   # meeting number -> absent students

# ── Communication records (mentor note) ────────────────────────────────────────
COMMUNICATIONS = [
    (DINESH, "2026-08-10", "Father", "Phone",
     "Informed about the arrear in 22CS603 and the low attendance of 78%.",
     "Parent was not aware of the arrear and agreed to monitor study hours at home.",
     "Remedial class schedule shared with the parent; follow-up call fixed after PT I."),
    (HARISH, "2026-08-12", "Mother", "Phone",
     "Informed about the arrear in 22CS604 and irregular submission of assignments.",
     "Parent requested weekly updates on attendance.",
     "Weekly update to be sent every Friday."),
    (NAVEEN, "2026-08-17", "Student", "In Person",
     "Discussed the attendance shortage after medical leave and the pending laboratory records.",
     "Student said he has recovered and will attend regularly.",
     "Laboratory record submission date extended by one week."),
    (DINESH, "2026-09-21", "Father", "Phone",
     "Shared PT I marks: below pass mark in 22CS701 and 22CS703.",
     "Parent asked for extra coaching support.",
     "Enrolled in remedial classes on Tuesdays and Thursdays."),
    (KEERTHANA, "2026-09-22", "Student", "In Person",
     "Appreciated for securing the first place in the national hackathon and top marks in PT I.",
     "Student wants guidance on higher studies.",
     "Shared details of GATE coaching and research internships."),
    (HARISH, "2026-09-23", "Guardian", "Message",
     "Informed about the absence for the mentor meeting on 18.09.2026 and the PT I marks.",
     "Guardian said the student was out of station for a family function.",
     "Advised to submit a leave letter; counseling session scheduled."),
]

# ── Parent - Teachers Meeting reports ──────────────────────────────────────────
PARENT_MEETINGS = [
    (DINESH, {
        "academic_year": "2026-2027", "meeting_date": "2026-09-26",
        "student_contact": "90000 10103", "semester_year_branch": "VII / IV / CSE",
        "parent_name": "Mr. Ramesh R", "relationship_with_student": "Father",
        "parent_contact": "90000 20103", "parent_address": "14, Gandhi Nagar, Erode - 638 001",
        "periodic_reports": "Yes", "interacts_regularly": "Occasionally", "satisfied_with_progress": "Needs improvement",
        "academic_performance": "Scored below the pass mark in 22CS701 and 22CS703 in PT I. Good in laboratory work. One arrear in 22CS603.",
        "co_curricular": "Member of the coding club; participated in one intra-college event.",
        "attendance": "78% as on date. Advised to maintain above 80%.",
        "discipline": "Good.",
        "placements": "Interested in software development roles; needs to improve aptitude scores.",
        "concerns": "Parent requested extra coaching for mathematics-oriented subjects.",
        "other_remarks": "Parent will monitor study hours at home.",
        "action_plan": ["Remedial Classes", "Mentorship"],
        "action_details": "Remedial classes arranged twice a week. Mentor will review progress every Friday and report to the parent after PT II.",
    }),
    (HARISH, {
        "academic_year": "2026-2027", "meeting_date": "2026-09-28",
        "student_contact": "90000 10105", "semester_year_branch": "VII / IV / CSE",
        "parent_name": "Mrs. Vasanthi V", "relationship_with_student": "Mother",
        "parent_contact": "90000 20105", "parent_address": "7/22, Nehru Street, Gobichettipalayam - 638 452",
        "periodic_reports": "Yes", "interacts_regularly": "No", "satisfied_with_progress": "No",
        "academic_performance": "Below the pass mark in 22CS702 and 22CS704 in PT I. One arrear in 22CS604.",
        "co_curricular": "Plays for the department cricket team.",
        "attendance": "81% as on date.",
        "discipline": "Good; irregular in assignment submission.",
        "placements": "Yet to register for placement training.",
        "concerns": "Parent asked for weekly updates on attendance and marks.",
        "other_remarks": "Nil.",
        "action_plan": ["Counseling", "Extra Assignments", "Others"],
        "action_other": "Weekly update to parent",
        "action_details": "Counseling session scheduled. Extra assignments given in the two weak subjects. Attendance and marks will be shared with the parent every Friday.",
    }),
]

# ── Achievements ───────────────────────────────────────────────────────────────
# (student, academic year, semester, category, event, level, result, date, attach certificate)
ACHIEVEMENTS = [
    (KEERTHANA, "2026-2027", "IV Year - Semester VII", "Technical Events",
     "Smart India Hackathon 2026", "National", "Winner", "2026-08-29", True),
    (KEERTHANA, "2026-2027", "IV Year - Semester VII", "Placement and Career Development Events",
     "Industry Connect - Cloud Careers Session", "State", "Participation", "2026-09-05", False),
    (BHAVYA, "2026-2027", "IV Year - Semester VII", "Technical Events",
     "Paper Presentation - National Conference on AI", "National", "Runner-Up", "2026-09-12", True),
    (BHAVYA, "2026-2027", "IV Year - Semester VII", "Cultural Events",
     "Inter-college Classical Music Competition", "State", "Special Award", "2026-08-15", False),
    (ARAVIND, "2026-2027", "IV Year - Semester VII", "Entrepreneurship and Innovation Activities",
     "Ideathon - Campus Innovation Challenge", "State", "Team Achievement", "2026-09-02", False),
    (PRIYA, "2026-2027", "IV Year - Semester VII", "Social Service Activities",
     "NSS Blood Donation Camp", "State", "Volunteer", "2026-08-20", False),
    (HARISH, "2026-2027", "IV Year - Semester VII", "Sports Events",
     "Inter-department Cricket Tournament", "State", "Winner", "2026-09-10", False),
]

# ── Condonation ────────────────────────────────────────────────────────────────
CONDONATIONS = [
    (NAVEEN, "Apr 2026", "III Year - Semester VI", 72.5,
     "Hospitalised for viral fever from 09.02.2026 to 13.02.2026 and advised rest for one week.", True),
    (HARISH, "Nov 2025", "III Year - Semester V", 71.0,
     "Underwent a minor surgery and was on medical leave for three weeks.", False),
    (HARISH, "Apr 2026", "III Year - Semester VI", 73.0,
     "Fracture in the right hand; could not attend classes for two weeks.", False),
]

# ── Semester results: GPA for S1..S6, arrears, CGPA ────────────────────────────
RESULTS = {
    ARAVIND:   (["8.21", "8.05", "8.34", "8.40", "8.52", "8.61"], ["0", "0", "0", "0", "0", "0"], "8.36"),
    BHAVYA:    (["9.02", "9.10", "9.24", "9.18", "9.31", "9.40"], ["0", "0", "0", "0", "0", "0"], "9.21"),
    DINESH:    (["6.84", "6.52", "6.90", "7.01", "6.75", "6.48"], ["0", "1", "0", "0", "0", "1"], "6.75"),
    GAYATHRI:  (["8.45", "8.60", "8.52", "8.71", "8.80", "8.92"], ["0", "0", "0", "0", "0", "0"], "8.67"),
    HARISH:    (["7.02", "6.88", "7.10", "6.95", "6.70", "6.61"], ["0", "0", "0", "1", "0", "1"], "6.88"),
    KEERTHANA: (["9.45", "9.52", "9.60", "9.71", "9.68", "9.80"], ["0", "0", "0", "0", "0", "0"], "9.63"),
    NAVEEN:    (["7.35", "7.20", "7.42", "7.15", "7.30", "7.05"], ["0", "0", "0", "0", "0", "0"], "7.25"),
    PRIYA:     (["8.02", "7.95", "8.10", "8.22", "8.15", "8.30"], ["0", "0", "0", "0", "0", "0"], "8.12"),
}


# ── Helpers ────────────────────────────────────────────────────────────────────

def sample_pdf(title: str, lines: list[str]) -> bytes:
    """A one-page placeholder PDF, clearly marked as sample data."""
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    c.setFont("Helvetica-Bold", 16)
    c.drawCentredString(width / 2, height - 90, title)
    c.setFont("Helvetica", 9)
    c.drawCentredString(width / 2, height - 108, "SAMPLE DOCUMENT - generated demo data, not a real record")
    c.setFont("Helvetica", 12)
    y = height - 160
    for line in lines:
        c.drawString(80, y, line)
        y -= 24
    c.showPage()
    c.save()
    return buffer.getvalue()


class Api:
    def __init__(self) -> None:
        self.http = httpx.Client(base_url=API, timeout=60.0)

    def call(self, method: str, path: str, **kwargs):
        r = self.http.request(method, path, **kwargs)
        if r.status_code >= 400:
            sys.exit(f"FAILED {method} {path} -> {r.status_code}: {r.text[:300]}")
        return r.json() if r.content and r.headers.get("content-type", "").startswith("application/json") else None

    def login(self) -> None:
        r = self.http.post("/auth/register", json={"name": DEMO_NAME, "email": DEMO_EMAIL, "password": DEMO_PASSWORD})
        if r.status_code == 201:
            print(f"created mentor account {DEMO_EMAIL}")
        elif r.status_code == 409:
            print(f"mentor account {DEMO_EMAIL} already exists")
        else:
            sys.exit(f"FAILED register -> {r.status_code}: {r.text[:300]}")
        r = self.http.post("/auth/login", data={"username": DEMO_EMAIL, "password": DEMO_PASSWORD})
        if r.status_code != 200:
            sys.exit(f"FAILED login -> {r.status_code}: {r.text[:300]}")
        self.http.headers["Authorization"] = f"Bearer {r.json()['access_token']}"

    def upload(self, batch_id: int, student_id: int, fields: dict, filename: str, content: bytes) -> dict:
        return self.call(
            "POST", f"/batches/{batch_id}/students/{student_id}/documents",
            data=fields, files={"file": (filename, content, "application/pdf")},
        )


def seed_exam(api: Api, batch_id: int, student_ids: list[int], exam: dict) -> None:
    codes = [code for code, _, _ in exam["subjects"]]
    setup = api.call("POST", f"/batches/{batch_id}/exams", json={
        "semester": exam["semester"], "academic_year": exam["academic_year"],
        "subject_codes": codes, "pt_max_marks": exam["pt_max_marks"],
    })
    base = f"/batches/{batch_id}/exams/{setup['id']}"
    api.call("PATCH", base, json={
        "subject_details": {code: {"name": name, "faculty": faculty} for code, name, faculty in exam["subjects"]},
    })
    api.call("PUT", f"{base}/marks", json={"records": [
        {
            "student_id": sid,
            "pt1_marks": dict(zip(codes, exam["pt1"][i])),
            "pt2_marks": dict(zip(codes, exam["pt2"][i])),
            "semester_grades": dict(zip(codes, exam["grades"][i])),
        }
        for i, sid in enumerate(student_ids)
    ]})
    for student, exam_type, subjects, action, impact in exam["remedial"]:
        api.call("POST", f"{base}/remedial", json={
            "student_id": student_ids[student], "exam_type": exam_type,
            "subjects": subjects, "action_taken": action, "impact": impact,
        })
    for exam_type in ("pt1", "pt2", "semester"):
        api.call("GET", f"{base}/analysis", params={"exam": exam_type})
    print(f"  exam record: {exam['semester']} (PT out of {exam['pt_max_marks']})")


def main() -> None:
    api = Api()
    api.login()

    existing = api.call("GET", "/batches/")
    if existing:
        if "--reset" not in sys.argv:
            sys.exit("The demo account already has data. Run again with --reset to delete it and seed afresh.")
        for batch in existing:
            api.call("DELETE", f"/batches/{batch['id']}")
        print(f"deleted {len(existing)} existing demo batch(es)")

    batch = api.call("POST", "/batches/", json={"department": DEPARTMENT, "batch_year": BATCH_YEAR})
    bid = batch["id"]
    sids = [
        api.call("POST", f"/batches/{bid}/students", json={"register_number": reg, "name": name})["id"]
        for reg, name in STUDENTS
    ]
    print(f"batch {BATCH_YEAR} ({DEPARTMENT}) with {len(sids)} students")

    # 2. Personal details
    for sid, (reg, name) in zip(sids, STUDENTS):
        api.upload(bid, sid, {"category": "personal_details", "title": "CAMPS Student Record"},
                   f"student_record_{reg}.pdf",
                   sample_pdf("STUDENT RECORD", [f"Name: {name}", f"Register Number: {reg}",
                                                 f"Department: {DEPARTMENT}", f"Batch: {BATCH_YEAR}"]))
    print("  personal details uploaded for every student")

    # 3. Counseling: a general session for everyone, a second one for three students
    for i, sid in enumerate(sids):
        api.call("POST", f"/batches/{bid}/students/{sid}/counseling", json={
            "counseling_date": f"2026-07-{13 + i:02d}", "academic_year": "2026-2027",
            "reason_initiated_by": "Institute Initiated",
            "reason_details": "General counseling session at the beginning of the semester.",
            "attendance_status": "Occasionally Tardy" if i in (DINESH, NAVEEN) else "Punctual",
            "discipline_status": "Good", "attitude_status": "Willing, Eager, Pleasant",
            "difficulty_meeting_demands": i in (DINESH, HARISH),
            "difficulty_explanation": "Finds mathematics-oriented subjects difficult." if i in (DINESH, HARISH) else None,
            "corrective_action_needed": i in (DINESH, HARISH),
            "corrective_action_explanation": "Remedial classes and a weekly study plan." if i in (DINESH, HARISH) else None,
            "next_session_needed": i in (DINESH, HARISH, NAVEEN),
            "next_session_explanation": "Review after Periodical Test I." if i in (DINESH, HARISH, NAVEEN) else None,
        })
    follow_ups = {
        DINESH: ("2026-09-22", "Scored below the pass mark in two subjects in Periodical Test I.",
                 "Punctual", "Attend remedial classes; fortnightly review with the mentor."),
        HARISH: ("2026-09-24", "Absent for the mentor meeting and low marks in Periodical Test I.",
                 "Occasionally Tardy", "Daily study schedule; parent to be updated every week."),
        NAVEEN: ("2026-09-25", "Attendance shortage after medical leave.",
                 "Occasionally Tardy", "Attendance to be monitored daily for one month."),
    }
    for student, (day, reason, attendance, action) in follow_ups.items():
        api.call("POST", f"/batches/{bid}/students/{sids[student]}/counseling", json={
            "counseling_date": day, "academic_year": "2026-2027",
            "reason_initiated_by": "Institute Initiated", "reason_details": reason,
            "attendance_status": attendance, "discipline_status": "Good",
            "attitude_status": "Willing, Eager, Pleasant",
            "difficulty_meeting_demands": True,
            "difficulty_explanation": "Needs additional academic support.",
            "corrective_action_needed": True, "corrective_action_explanation": action,
            "next_session_needed": True, "next_session_explanation": "Review after Periodical Test II.",
        })
    print("  counseling sessions recorded")

    # 4. Mentor-mentee meetings with attendance, then the mentor note
    for number, (day, agenda) in enumerate(MEETINGS, start=1):
        meeting = api.call("POST", f"/batches/{bid}/meetings", json={
            "meeting_date": day, "meeting_time": "3.30 PM", "location": "CSE Department Conference Hall",
            "semester": "IV Year - Semester VII", "academic_year": "2026-2027",
            "year_of_study": "IV Year", "agenda_items": agenda,
        })
        api.call("PUT", f"/batches/{bid}/meetings/{meeting['id']}/attendance", json={"records": [
            {
                "student_id": sid,
                "is_present": i not in ABSENTEES[number],
                "points_discussed": [] if i in ABSENTEES[number] else MEETING_NOTES[i][0],
                "action_planned": [] if i in ABSENTEES[number] else MEETING_NOTES[i][1],
            }
            for i, sid in enumerate(sids)
        ]})
        api.call("PATCH", f"/batches/{bid}/meetings/{meeting['id']}", json={
            "minutes_text": "Individual academic progress, attendance and action plans were discussed with every student present.",
        })
    for student, day, person, mode, details, feedback, action in COMMUNICATIONS:
        api.call("POST", f"/batches/{bid}/communications", json={
            "student_id": sids[student], "communication_date": day, "contact_person": person, "mode": mode,
            "details": details, "feedback": feedback, "action_taken": action,
        })
    print(f"  {len(MEETINGS)} meetings with attendance, {len(COMMUNICATIONS)} mentor note entries")

    # 5 + 6. Exam marks, result analysis and remedial actions
    seed_exam(api, bid, sids, SEM6)
    seed_exam(api, bid, sids, SEM7)

    # 7. Parental communication reports
    for student, report in PARENT_MEETINGS:
        api.call("POST", f"/batches/{bid}/parent-meetings", json={"student_id": sids[student], **report})
    print(f"  {len(PARENT_MEETINGS)} parent meeting reports")

    # 8. Medical leave proof
    api.upload(bid, sids[NAVEEN],
               {"category": "medical_leave", "title": "Medical Certificate", "notes": "Viral fever",
                "from_date": "2026-02-09", "to_date": "2026-02-13"},
               "medical_certificate_7376231CS107.pdf",
               sample_pdf("MEDICAL CERTIFICATE", ["Patient: Naveen T", "Diagnosis: Viral fever",
                                                  "Advised rest: 09.02.2026 to 13.02.2026"]))
    print("  1 medical leave record")

    # 9. Achievements (some with a certificate)
    for student, year, semester, category, event, level, result, day, with_certificate in ACHIEVEMENTS:
        document_id = None
        if with_certificate:
            reg, name = STUDENTS[student]
            document_id = api.upload(
                bid, sids[student], {"category": "certificate", "title": event}, f"certificate_{reg}.pdf",
                sample_pdf("CERTIFICATE", [f"Awarded to: {name} ({reg})", f"Event: {event}", f"Result: {result}"]),
            )["id"]
        api.call("POST", f"/batches/{bid}/achievements", json={
            "student_id": sids[student], "academic_year": year, "semester": semester, "category": category,
            "event_name": event, "level": level, "result": result, "event_date": day, "document_id": document_id,
        })
    print(f"  {len(ACHIEVEMENTS)} achievements")

    # 10. Condonation applications (one student has used both chances)
    for student, exam_month, semester, attendance, reason, with_proof in CONDONATIONS:
        document_id = None
        if with_proof:
            reg, name = STUDENTS[student]
            document_id = api.upload(
                bid, sids[student], {"category": "condonation", "title": f"Condonation proof - {exam_month}"},
                f"condonation_proof_{reg}.pdf",
                sample_pdf("APPROVED CONDONATION FORM", [f"Student: {name} ({reg})", f"Exam: {exam_month}",
                                                         f"Attendance: {attendance}%"]),
            )["id"]
        api.call("POST", f"/batches/{bid}/condonations", json={
            "student_id": sids[student], "exam_month_year": exam_month, "degree_branch": f"B.E. - {DEPARTMENT}",
            "semester": semester, "attendance_percentage": attendance, "reason": reason,
            "recommended": True, "document_id": document_id,
        })
    print(f"  {len(CONDONATIONS)} condonation applications")

    # 11. GPA, CGPA and arrears
    api.call("PUT", f"/batches/{bid}/semester-results", json={"records": [
        {
            "student_id": sids[student],
            "gpa": {str(n): value for n, value in enumerate(gpa, start=1)},
            "arrears": {str(n): value for n, value in enumerate(arrears, start=1)},
            "cgpa": cgpa,
        }
        for student, (gpa, arrears, cgpa) in RESULTS.items()
    ]})
    print("  GPA, CGPA and arrears for every student")

    summary = api.call("GET", f"/batches/{bid}/mentor-file/summary")
    print("mentor file summary:", summary)
    print(f"\nDone. Log in as {DEMO_EMAIL} (password is DEMO_PASSWORD at the top of this file).")


if __name__ == "__main__":
    main()
