"""
Mentor File PDF service — the remaining checklist documents in the official BIT format:

1. generate_cover_pdf             — "Mentor File" cover page
2. generate_mentor_note_pdf       — communication records with students / parents
3. generate_result_analysis_pdf   — RESULT ANALYSIS table + pass % chart (+ remedial actions)
4. generate_parent_meeting_pdf    — PARENT - TEACHERS MEETING form (2 pages)
5. generate_achievements_pdf      — STUDENT ACHIEVEMENTS SUMMARY sheet
6. generate_condonation_pdf       — APPLICATION FOR CONDONATION
7. generate_semester_results_pdf  — SEMESTERWISE STUDENTS GPA, CGPA + ARREAR DETAILS
"""

import io
from datetime import date
from xml.sax.saxutils import escape

from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.graphics.shapes import Drawing, String
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm, mm
from reportlab.pdfgen import canvas as pdf_canvas
from reportlab.platypus import (
    KeepTogether,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from app.services.exam_pdf_service import S_TD, S_TD_L, S_TH, S_TITLE, _letterhead

L_PAGE_W, L_PAGE_H = landscape(A4)
P_PAGE_W, P_PAGE_H = A4
L_MARGIN = 1.5 * cm
P_MARGIN = 1.8 * cm
BOX = 9   # checkbox square size in points

# ── Styles ─────────────────────────────────────────────────────────────────────

S_BODY    = ParagraphStyle("mf_body",    fontName="Times-Roman", fontSize=11, leading=15)
S_BOLD    = ParagraphStyle("mf_bold",    fontName="Times-Bold",  fontSize=11, leading=15)
S_RIGHT   = ParagraphStyle("mf_right",   fontName="Times-Roman", fontSize=11, leading=15, alignment=TA_RIGHT)
S_FORM_T  = ParagraphStyle("mf_form_t",  fontName="Times-Bold",  fontSize=12, leading=18, alignment=TA_CENTER)
S_LABEL   = ParagraphStyle("mf_label",   fontName="Helvetica-Bold", fontSize=10, leading=14, alignment=TA_LEFT)
S_LABEL_R = ParagraphStyle("mf_label_r", fontName="Helvetica-Bold", fontSize=10, leading=14, alignment=TA_RIGHT)
S_SIG     = ParagraphStyle("mf_sig",     fontName="Helvetica", fontSize=10, leading=14)
S_SIG_R   = ParagraphStyle("mf_sig_r",   fontName="Helvetica", fontSize=10, leading=14, alignment=TA_RIGHT)

GRID_STYLE = TableStyle([
    ("BOX",           (0, 0), (-1, -1), 0.75, colors.black),
    ("INNERGRID",     (0, 0), (-1, -1), 0.5,  colors.black),
    ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
    ("LEFTPADDING",   (0, 0), (-1, -1), 3),
    ("RIGHTPADDING",  (0, 0), (-1, -1), 3),
    ("TOPPADDING",    (0, 0), (-1, -1), 4),
    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
])


# ── Helpers ────────────────────────────────────────────────────────────────────

def _p(text, style) -> Paragraph:
    """Paragraph from user-entered text (escaped, newlines kept)."""
    return Paragraph(escape(str(text if text is not None else "")).replace("\n", "<br/>"), style)


def _fmt_date(d: date | None) -> str:
    return d.strftime("%d.%m.%Y") if d else ""


def _landscape_doc(buffer: io.BytesIO, title: str) -> SimpleDocTemplate:
    return SimpleDocTemplate(
        buffer, pagesize=landscape(A4), title=title,
        leftMargin=L_MARGIN, rightMargin=L_MARGIN, topMargin=L_MARGIN, bottomMargin=L_MARGIN,
    )


def _portrait_doc(buffer: io.BytesIO, title: str) -> SimpleDocTemplate:
    return SimpleDocTemplate(
        buffer, pagesize=A4, title=title,
        leftMargin=P_MARGIN, rightMargin=P_MARGIN, topMargin=1.2 * cm, bottomMargin=1.5 * cm,
    )


def _signature_row(left: str, right: str, usable_w: float, middle: str | None = None) -> Table:
    if middle is None:
        cells, widths = [[Paragraph(left, S_SIG), Paragraph(right, S_SIG_R)]], [usable_w / 2] * 2
    else:
        s_mid = ParagraphStyle("mf_sig_c", parent=S_SIG, alignment=TA_CENTER)
        cells = [[Paragraph(left, S_SIG), Paragraph(middle, s_mid), Paragraph(right, S_SIG_R)]]
        widths = [usable_w / 3] * 3
    t = Table(cells, colWidths=widths)
    t.setStyle(TableStyle([
        ("LEFTPADDING",  (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
    ]))
    return t


def _box_cell(checked: bool) -> Table:
    """A small bordered square — 'X' inside if checked."""
    t = Table([["X" if checked else " "]], colWidths=[BOX + 2], rowHeights=[BOX + 2])
    t.setStyle(TableStyle([
        ("BOX",           (0, 0), (-1, -1), 1, colors.black),
        ("FONTNAME",      (0, 0), (-1, -1), "Helvetica-Bold"),
        ("FONTSIZE",      (0, 0), (-1, -1), 7),
        ("ALIGN",         (0, 0), (-1, -1), "CENTER"),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING",   (0, 0), (-1, -1), 1),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 1),
        ("TOPPADDING",    (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
    ]))
    return t


def _checkbox_group(options: list[tuple[str, bool]], label_w: float) -> Table:
    """[box] label [box] label ... on one line."""
    cells, widths = [], []
    for label, checked in options:
        cells += [_box_cell(checked), Paragraph(f"&nbsp;{escape(label)}", S_BODY)]
        widths += [BOX + 6, label_w]
    t = Table([cells], colWidths=widths)
    t.setStyle(TableStyle([
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING",   (0, 0), (-1, -1), 0),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 0),
        ("TOPPADDING",    (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
    ]))
    return t


def _landscape_header(department: str, academic_year: str, title_line: str, mentor_name: str | None) -> list:
    usable_w = L_PAGE_W - 2 * L_MARGIN
    s = [
        _letterhead(usable_w),
        Spacer(1, 5 * mm),
        _p(f"DEPARTMENT OF {department.upper()}", S_TITLE),
        _p(f"ACADEMIC YEAR ({academic_year})", S_TITLE),
        _p(title_line, S_TITLE),
    ]
    if mentor_name is not None:
        s.append(_p(f"MENTOR NAME :  {mentor_name}", S_TITLE))
    s.append(Spacer(1, 3 * mm))
    return s


# ══════════════════════════════════════════════════════════════════════════════
# 1. COVER PAGE
# ══════════════════════════════════════════════════════════════════════════════

def generate_cover_pdf(batch_year: str, department: str, mentor_name: str) -> bytes:
    buffer = io.BytesIO()
    c = pdf_canvas.Canvas(buffer, pagesize=A4)
    c.setTitle("Mentor File")

    c.setFont("Helvetica-BoldOblique", 54)
    c.drawCentredString(P_PAGE_W / 2, P_PAGE_H * 0.62, "Mentor File")

    label_x, value_x, line_end = 3.0 * cm, 8.4 * cm, P_PAGE_W - 3.0 * cm
    y = P_PAGE_H * 0.47
    for label, value in (("Batch:", batch_year), ("Department:", department), ("Mentor Name:", mentor_name)):
        c.setFont("Helvetica-Bold", 22)
        c.drawString(label_x, y, label)
        size = 18
        while size > 9 and c.stringWidth(value, "Helvetica", size) > line_end - value_x - 8:
            size -= 1
        c.setFont("Helvetica", size)
        c.drawString(value_x + 4, y + 3, value)
        c.setLineWidth(1.5)
        c.line(value_x, y - 3, line_end, y - 3)
        y -= 1.7 * cm

    c.showPage()
    c.save()
    return buffer.getvalue()


# ══════════════════════════════════════════════════════════════════════════════
# 2. MENTOR NOTE — COMMUNICATION RECORDS
# ══════════════════════════════════════════════════════════════════════════════

def generate_mentor_note_pdf(
    department: str,
    batch_year: str,
    mentor_name: str,
    records: list[dict],   # [{communication_date, register_number, name, contact_person, mode, details, feedback, action_taken}]
) -> bytes:
    usable_w = L_PAGE_W - 2 * L_MARGIN
    s = [
        _letterhead(usable_w),
        Spacer(1, 5 * mm),
        _p(f"DEPARTMENT OF {department.upper()}", S_TITLE),
        _p(f"BATCH ({batch_year})", S_TITLE),
        _p("MENTOR NOTE - COMMUNICATION RECORDS", S_TITLE),
        _p(f"MENTOR NAME :  {mentor_name}", S_TITLE),
        Spacer(1, 3 * mm),
    ]

    col_widths = [1.0 * cm, 2.1 * cm, 4.2 * cm, 2.6 * cm, 6.8 * cm, 5.0 * cm]
    col_widths.append(usable_w - sum(col_widths))
    data = [[
        Paragraph("S.<br/>NO", S_TH),
        Paragraph("DATE", S_TH),
        Paragraph("REG. NO. &amp;<br/>STUDENT NAME", S_TH),
        Paragraph("COMMUNICATED<br/>WITH", S_TH),
        Paragraph("DETAILS OF THE INFORMATION<br/>COMMUNICATED", S_TH),
        Paragraph("FEEDBACK RECEIVED", S_TH),
        Paragraph("ACTION TAKEN", S_TH),
    ]]
    for idx, r in enumerate(records):
        who = r.get("contact_person", "")
        if r.get("mode"):
            who = f"{who}\n({r['mode']})"
        data.append([
            _p(idx + 1, S_TD),
            _p(_fmt_date(r.get("communication_date")), S_TD),
            _p(f"{r.get('register_number', '')}\n{r.get('name', '')}", S_TD_L),
            _p(who, S_TD),
            _p(r.get("details"), S_TD_L),
            _p(r.get("feedback"), S_TD_L),
            _p(r.get("action_taken"), S_TD_L),
        ])

    tbl = Table(data, colWidths=col_widths, repeatRows=1)
    tbl.setStyle(GRID_STYLE)
    s += [tbl, Spacer(1, 1.6 * cm), _signature_row("Signature of Mentor", "Signature of HoD", usable_w)]

    buffer = io.BytesIO()
    _landscape_doc(buffer, "Mentor Note").build(s)
    return buffer.getvalue()


# ══════════════════════════════════════════════════════════════════════════════
# 3. RESULT ANALYSIS
# ══════════════════════════════════════════════════════════════════════════════

def _pass_chart(subjects: list[dict], usable_w: float, semester: str) -> Drawing:
    height = 4.0 * cm
    d = Drawing(usable_w, height)
    chart = VerticalBarChart()
    chart.x, chart.y = 2.0 * cm, 1.3 * cm
    chart.width, chart.height = usable_w - 3.0 * cm, height - 2.3 * cm
    chart.data = [[s["pass_percentage"] for s in subjects]]
    chart.categoryAxis.categoryNames = [s["subject_code"] for s in subjects]
    chart.categoryAxis.labels.fontSize = 8
    chart.valueAxis.valueMin, chart.valueAxis.valueMax, chart.valueAxis.valueStep = 0, 100, 25
    chart.valueAxis.labelTextFormat = "%.2f"
    chart.valueAxis.labels.fontSize = 8
    chart.valueAxis.visibleGrid = 1
    chart.valueAxis.gridStrokeColor = colors.HexColor("#cccccc")
    chart.bars[0].fillColor = colors.HexColor("#008080")
    chart.bars[0].strokeColor = None
    chart.barWidth = 10
    chart.groupSpacing = 6
    d.add(chart)
    d.add(String(usable_w / 2, height - 0.5 * cm, semester, fontName="Helvetica-Bold", fontSize=9, textAnchor="middle"))
    d.add(String(usable_w / 2, 0.2 * cm, "Subjects", fontName="Helvetica-Bold", fontSize=8, textAnchor="middle"))
    d.add(String(0.6 * cm, height / 2, "Pass %", fontName="Helvetica-Bold", fontSize=8, textAnchor="middle"))
    return d


def generate_result_analysis_pdf(
    department: str,
    academic_year: str,
    semester: str,
    exam_title: str,          # "PERIODICAL TEST I RESULTS" | "PERIODICAL TEST II RESULTS" | "END SEMESTER RESULTS"
    mentor_name: str,
    subjects: list[dict],     # [{subject_code, subject_name, faculty, attended, passed, failed, pass_percentage, absent}]
    remedial_actions: list[dict],   # [{register_number, name, subjects, action_taken, impact}]
) -> bytes:
    usable_w = L_PAGE_W - 2 * L_MARGIN
    s = [
        _letterhead(usable_w),
        Spacer(1, 4 * mm),
        _p(f"DEPARTMENT OF {department.upper()}", S_TITLE),
        _p(f"Academic year {academic_year}", S_TITLE),
        _p(f"RESULT ANALYSIS - {semester.upper()} - {department.upper()}", S_TITLE),
        _p(exam_title, S_TITLE),
        Spacer(1, 3 * mm),
    ]

    s_num = ParagraphStyle("mf_num", parent=S_TD, fontName="Helvetica-Bold")
    col_widths = [2.6 * cm, 8.2 * cm, 6.9 * cm, 2.0 * cm, 1.7 * cm, 1.7 * cm, 2.0 * cm]
    col_widths.append(usable_w - sum(col_widths))
    data = [[
        Paragraph("Subject Code", S_TH), Paragraph("Subject Name", S_TH), Paragraph("Name of Faculty", S_TH),
        Paragraph("Attended", S_TH), Paragraph("Pass", S_TH), Paragraph("Fail", S_TH),
        Paragraph("% PASS", S_TH), Paragraph("Absent", S_TH),
    ]]
    for sub in subjects:
        data.append([
            _p(sub["subject_code"], S_TD),
            _p(sub.get("subject_name", ""), S_TD_L),
            _p(sub.get("faculty", ""), S_TD_L),
            _p(sub["attended"], s_num),
            _p(sub["passed"], s_num),
            _p(sub["failed"], s_num),
            _p(f"{sub['pass_percentage']:.2f}", s_num),
            _p(sub["absent"], S_TD),
        ])
    tbl = Table(data, colWidths=col_widths, repeatRows=1)
    tbl.setStyle(GRID_STYLE)
    s.append(tbl)

    footer = [Spacer(1, 5 * mm)]
    if subjects:
        footer.append(_pass_chart(subjects, usable_w, f"{semester} - {department}"))
    footer += [
        Spacer(1, 0.6 * cm),
        _signature_row(f"<b>Faculty Mentor</b><br/>{escape(mentor_name)}", "<b>HoD</b>", usable_w),
    ]
    s.append(KeepTogether(footer))

    if remedial_actions:
        s += [
            PageBreak(),
            _p(f"REMEDIAL ACTIONS - {exam_title}", S_TITLE),
            Spacer(1, 3 * mm),
        ]
        r_widths = [1.0 * cm, 4.6 * cm, 4.0 * cm, 9.0 * cm]
        r_widths.append(usable_w - sum(r_widths))
        r_data = [[
            Paragraph("S.<br/>NO", S_TH), Paragraph("REG. NO. &amp;<br/>STUDENT NAME", S_TH),
            Paragraph("SUBJECTS", S_TH), Paragraph("REMEDIAL ACTION TAKEN", S_TH),
            Paragraph("IMPACT ON ACADEMIC PERFORMANCE", S_TH),
        ]]
        for idx, r in enumerate(remedial_actions):
            r_data.append([
                _p(idx + 1, S_TD),
                _p(f"{r.get('register_number', '')}\n{r.get('name', '')}", S_TD_L),
                _p(r.get("subjects"), S_TD_L),
                _p(r.get("action_taken"), S_TD_L),
                _p(r.get("impact"), S_TD_L),
            ])
        r_tbl = Table(r_data, colWidths=r_widths, repeatRows=1)
        r_tbl.setStyle(GRID_STYLE)
        s += [r_tbl, Spacer(1, 1.4 * cm), _signature_row("<b>Faculty Mentor</b>", "<b>HoD</b>", usable_w)]

    buffer = io.BytesIO()
    _landscape_doc(buffer, "Result Analysis").build(s)
    return buffer.getvalue()


# ══════════════════════════════════════════════════════════════════════════════
# 4. PARENT - TEACHERS MEETING
# ══════════════════════════════════════════════════════════════════════════════

ACTION_PLAN_OPTIONS = ["Remedial Classes", "Mentorship", "Counseling", "Extra Assignments"]


def _numbered_field(no: int, label: str, value, usable_w: float) -> Table:
    label_w = 7.4 * cm
    t = Table(
        [[Paragraph(f"{no}.", S_BODY), Paragraph(label, S_BODY), Paragraph(":", S_BODY), value]],
        colWidths=[1.0 * cm, label_w, 0.4 * cm, usable_w - 1.4 * cm - label_w],
    )
    t.setStyle(TableStyle([
        ("VALIGN",        (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING",   (0, 0), (-1, -1), 0),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 0),
        ("TOPPADDING",    (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))
    return t


def _discussion_point(no: int, label: str, answer: str | None, usable_w: float) -> KeepTogether:
    indent = 1.0 * cm
    head = Table([[Paragraph(f"{no}.", S_BODY), Paragraph(label, S_BODY)]], colWidths=[indent, usable_w - indent])
    body = Table([["", _p(answer or " ", S_BODY)]], colWidths=[indent, usable_w - indent])
    for t in (head, body):
        t.setStyle(TableStyle([
            ("VALIGN",        (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING",   (0, 0), (-1, -1), 0),
            ("RIGHTPADDING",  (0, 0), (-1, -1), 0),
            ("TOPPADDING",    (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ]))
    body.setStyle(TableStyle([("LINEBELOW", (1, 0), (1, 0), 0.75, colors.grey)]))
    return KeepTogether([head, body])


def generate_parent_meeting_pdf(mentor_name: str, student_name: str, register_number: str, m: dict) -> bytes:
    """`m` holds the ParentMeeting columns."""
    usable_w = P_PAGE_W - 2 * P_MARGIN
    title = Paragraph("<u>PARENT - TEACHERS MEETING</u>", S_FORM_T)
    relationship = m.get("relationship_with_student") or ""

    s = [
        _letterhead(usable_w),
        Spacer(1, 3 * mm),
        title,
        _p(f"Academic Year: {m.get('academic_year', '')}", ParagraphStyle("mf_ay", parent=S_FORM_T, fontSize=11)),
        _p(f"Date: {_fmt_date(m.get('meeting_date'))}", S_RIGHT),
        Spacer(1, 3 * mm),
        _numbered_field(1, "Name of the Student", _p(student_name, S_BODY), usable_w),
        _numbered_field(2, "Register Number", _p(register_number, S_BODY), usable_w),
        _numbered_field(3, "Student Contact Number", _p(m.get("student_contact"), S_BODY), usable_w),
        _numbered_field(4, "Semester / Year / Branch", _p(m.get("semester_year_branch"), S_BODY), usable_w),
        _numbered_field(5, "Parent / Guardian Name", _p(m.get("parent_name"), S_BODY), usable_w),
        _numbered_field(
            6, "Relationship with Student",
            _checkbox_group([(r, relationship == r) for r in ("Father", "Mother", "Guardian")], 2.1 * cm),
            usable_w,
        ),
        _numbered_field(7, "Contact Number", _p(m.get("parent_contact"), S_BODY), usable_w),
        _numbered_field(8, "Parent Contact Address", _p(m.get("parent_address"), S_BODY), usable_w),
    ]

    questions = [
        (9, "Do you get Periodic reports from the college with respect to your ward?", "periodic_reports"),
        (10, "Do you interact with the college authorities regularly?", "interacts_regularly"),
        (11, "Are you satisfied with the progress of your ward (son/daughter)?", "satisfied_with_progress"),
    ]
    for no, question, key in questions:
        row = Table(
            [[Paragraph(f"{no}.", S_BODY),
              Paragraph(f"{question} - <b>{escape(m.get(key) or '')}</b>", S_BODY)]],
            colWidths=[1.0 * cm, usable_w - 1.0 * cm],
        )
        row.setStyle(TableStyle([
            ("VALIGN",        (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING",   (0, 0), (-1, -1), 0),
            ("RIGHTPADDING",  (0, 0), (-1, -1), 0),
            ("TOPPADDING",    (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ]))
        s.append(row)

    s.append(Paragraph("DISCUSSION POINTS", S_BOLD))
    points = [
        (12, "Academic Performance (Marks in recent exams, strengths, areas of improvement)", "academic_performance"),
        (13, "Co-curricular &amp; Extra-curricular Activities (Sports, clubs, projects, etc.)", "co_curricular"),
        (14, "Attendance", "attendance"),
        (15, "Discipline", "discipline"),
        (16, "Placements/Career Guidance", "placements"),
        (17, "Any Specific Concerns/Feedback/Suggestions for the Department/ College from Parent", "concerns"),
    ]
    for no, label, key in points:
        s.append(_discussion_point(no, label, m.get(key), usable_w))

    s += [
        _numbered_field(18, "Any other remarks", _p(m.get("other_remarks"), S_BODY), usable_w),
        Spacer(1, 1.2 * cm),
        _signature_row("Student Signature", "Mentor Signature", usable_w, middle="Parent Signature"),
    ]

    # ── Page 2: action taken / follow-up ──
    plan = m.get("action_plan") or []
    other_checked = "Others" in plan or bool(m.get("action_other"))
    plan_row = Table(
        [[Paragraph("&bull;&nbsp;&nbsp;<b>Action Plan:</b>", S_BODY),
          _checkbox_group([(o, o in plan) for o in ACTION_PLAN_OPTIONS], 3.05 * cm)]],
        colWidths=[2.9 * cm, usable_w - 2.9 * cm],
    )
    plan_row.setStyle(TableStyle([
        ("VALIGN",       (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING",  (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
    ]))
    others_row = Table(
        [[_box_cell(other_checked), Paragraph(f"&nbsp;Others: <u>{escape(m.get('action_other') or '')}</u>", S_BODY)]],
        colWidths=[BOX + 6, usable_w - BOX - 6],
    )
    others_row.setStyle(TableStyle([
        ("VALIGN",       (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING",  (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
    ]))
    details_box = Table([[_p(m.get("action_details"), S_BODY)]], colWidths=[usable_w], rowHeights=[11.5 * cm])
    details_box.setStyle(TableStyle([
        ("BOX",         (0, 0), (-1, -1), 1.25, colors.black),
        ("VALIGN",      (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING",  (0, 0), (-1, -1), 8),
    ]))
    s += [
        PageBreak(),
        _letterhead(usable_w),
        Spacer(1, 6 * mm),
        title,
        Spacer(1, 3 * mm),
        Paragraph("<u>Action Taken / Follow-up of the Meeting</u>", S_FORM_T),
        Spacer(1, 6 * mm),
        plan_row,
        Spacer(1, 3 * mm),
        others_row,
        Spacer(1, 8 * mm),
        details_box,
        Spacer(1, 1.6 * cm),
        _p(mentor_name, S_RIGHT),
        Paragraph("Mentor Name with Signature", S_RIGHT),
    ]

    buffer = io.BytesIO()
    _portrait_doc(buffer, "Parent - Teachers Meeting").build(s)
    return buffer.getvalue()


# ══════════════════════════════════════════════════════════════════════════════
# 5. STUDENT ACHIEVEMENTS SUMMARY
# ══════════════════════════════════════════════════════════════════════════════

MIN_ACHIEVEMENT_ROWS = 10


def generate_achievements_pdf(
    department: str,
    academic_year: str,
    student_name: str,
    register_number: str,
    achievements: list[dict],   # [{event_name, level, result}]
) -> bytes:
    usable_w = L_PAGE_W - 2 * L_MARGIN
    s = _landscape_header(department, academic_year, "STUDENT ACHIEVEMENTS SUMMARY", None)
    s.pop()   # name / register number line sits directly under the title

    ident = Table(
        [[_p(f"STUDENT NAME : {student_name}", S_LABEL), _p(f"REGISTER NUMBER : {register_number}", S_LABEL_R)]],
        colWidths=[usable_w * 0.55, usable_w * 0.45],
    )
    ident.setStyle(TableStyle([
        ("LEFTPADDING",   (0, 0), (-1, -1), 0),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    s.append(ident)

    s_th_l = ParagraphStyle("mf_th_l", parent=S_TH, alignment=TA_LEFT, fontSize=9, leading=13)
    s_th = ParagraphStyle("mf_th", parent=S_TH, fontSize=9, leading=13)
    col_widths = [1.7 * cm, 7.4 * cm, 5.7 * cm]
    col_widths.append(usable_w - sum(col_widths))
    data = [[
        Paragraph("S. NO", s_th),
        Paragraph("EVENT NAME", s_th),
        Paragraph("INTERNATIONAL /<br/>NATIONAL / STATE", s_th),
        Paragraph(
            "Participation / Winner / Runner-Up / Special Award /<br/>"
            "Recognition / Team Achievement / Event Organizer /<br/>"
            "Volunteer / Certificate of Appreciation. etc", s_th_l),
    ]]
    s_cell = ParagraphStyle("mf_ach", parent=S_TD, fontSize=9, leading=12)
    s_cell_l = ParagraphStyle("mf_ach_l", parent=S_TD_L, fontSize=9, leading=12)
    for idx in range(max(len(achievements), MIN_ACHIEVEMENT_ROWS)):
        a = achievements[idx] if idx < len(achievements) else {}
        data.append([
            _p(idx + 1, s_cell),
            _p(a.get("event_name", ""), s_cell_l),
            _p(a.get("level", ""), s_cell),
            _p(a.get("result", ""), s_cell_l),
        ])

    tbl = Table(data, colWidths=col_widths, repeatRows=1)
    tbl.setStyle(GRID_STYLE)
    s += [tbl, Spacer(1, 1.0 * cm), _signature_row("Signature of Mentor", "Signature of HoD", usable_w)]

    buffer = io.BytesIO()
    _landscape_doc(buffer, "Student Achievements Summary").build(s)
    return buffer.getvalue()


# ══════════════════════════════════════════════════════════════════════════════
# 6. APPLICATION FOR CONDONATION
# ══════════════════════════════════════════════════════════════════════════════

def generate_condonation_pdf(
    student_name: str,
    register_number: str,
    exam_month_year: str,
    degree_branch: str,
    semester: str,
    attendance_percentage: float,
    reason: str,
    recommended: bool,
) -> bytes:
    usable_w = P_PAGE_W - 2 * P_MARGIN
    s_cell = ParagraphStyle("mf_cd", fontName="Helvetica", fontSize=12, leading=16)
    s_cell_b = ParagraphStyle("mf_cd_b", parent=s_cell, fontName="Helvetica-Bold")
    s_small_b = ParagraphStyle("mf_cd_s", parent=s_cell, fontName="Helvetica-Bold", fontSize=8, leading=10)
    s_title = ParagraphStyle("mf_cd_t", fontName="Helvetica-Bold", fontSize=12, leading=18, alignment=TA_CENTER)

    exam_tbl = Table(
        [[Paragraph("Month &amp; Year of Exam", s_cell_b), _p(exam_month_year, s_cell)]],
        colWidths=[5.0 * cm, 5.0 * cm], hAlign="CENTER",
    )
    exam_tbl.setStyle(GRID_STYLE)

    # The chosen option is bold on a shaded cell
    yes_no = Table(
        [[Paragraph("<b>Yes</b>" if recommended else "Yes", s_cell),
          Paragraph("No" if recommended else "<b>No</b>", s_cell)]],
        colWidths=[1.3 * cm, 1.3 * cm], hAlign="LEFT",
    )
    yes_no.setStyle(TableStyle([
        ("BOX",        (0, 0), (-1, -1), 0.75, colors.black),
        ("INNERGRID",  (0, 0), (-1, -1), 0.5, colors.black),
        ("BACKGROUND", (0 if recommended else 1, 0), (0 if recommended else 1, 0), colors.HexColor("#d9d9d9")),
    ]))

    left_w = usable_w * 0.49
    rows = [
        [Paragraph("Name", s_cell), _p(student_name, s_cell)],
        [Paragraph("Reg. No.", s_cell), _p(register_number, s_cell)],
        [Paragraph("Degree &amp; Branch", s_cell), _p(degree_branch, s_cell)],
        [Paragraph("Semester", s_cell), _p(semester, s_cell)],
        [Paragraph("Attendance %", s_cell), _p(f"{attendance_percentage:g}", s_cell)],
        [Paragraph("Reason for Absence", s_cell), _p(reason, s_cell)],
        [Paragraph("Signature of the Student", s_cell), ""],
        [[Paragraph("Recommended", s_cell), Paragraph("(Attach Proof)", s_small_b)], yes_no],
    ]
    main = Table(rows, colWidths=[left_w, usable_w - left_w])
    main.setStyle(GRID_STYLE)
    main.setStyle(TableStyle([
        ("VALIGN",        (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING",   (0, 0), (-1, -1), 6),
        ("TOPPADDING",    (1, -1), (1, -1), 14),
        ("BOTTOMPADDING", (0, -1), (-1, -1), 40),
    ]))

    s = [
        _letterhead(usable_w),
        Spacer(1, 8 * mm),
        Paragraph("<u>APPLICATION FOR CONDONATION</u>", s_title),
        Spacer(1, 3 * mm),
        exam_tbl,
        Spacer(1, 1.2 * cm),
        main,
        Spacer(1, 2.4 * cm),
        _signature_row("&nbsp;&nbsp;&nbsp;&nbsp;Mentor", "HoD&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;", usable_w),
    ]

    buffer = io.BytesIO()
    _portrait_doc(buffer, "Application for Condonation").build(s)
    return buffer.getvalue()


# ══════════════════════════════════════════════════════════════════════════════
# 7. SEMESTERWISE GPA, CGPA AND ARREAR DETAILS
# ══════════════════════════════════════════════════════════════════════════════

SEMESTER_KEYS = [str(n) for n in range(1, 9)]


def _semester_table(rows: list[dict], value_key: str, usable_w: float) -> Table:
    fixed = [1.2 * cm, 3.2 * cm, 5.3 * cm]
    sem_w = (usable_w - sum(fixed)) / 9
    col_widths = fixed + [sem_w] * 9

    data = [[
        Paragraph("S.<br/>NO", S_TH),
        Paragraph("REGISTER<br/>NUMBER", S_TH),
        Paragraph("NAME OF THE<br/>STUDENT", S_TH),
    ] + [Paragraph(f"S{k}", S_TH) for k in SEMESTER_KEYS] + [Paragraph("CGPA", S_TH)]]

    for idx, r in enumerate(rows):
        values = r.get(value_key) or {}
        data.append(
            [_p(idx + 1, S_TD), _p(r.get("register_number", ""), S_TD), _p(r.get("name", ""), S_TD_L)]
            + [_p(values.get(k, ""), S_TD) for k in SEMESTER_KEYS]
            + [_p(r.get("cgpa", ""), S_TD)]
        )

    tbl = Table(data, colWidths=col_widths, repeatRows=1)
    tbl.setStyle(GRID_STYLE)
    return tbl


def generate_semester_results_pdf(
    department: str,
    academic_year: str,
    mentor_name: str,
    rows: list[dict],   # [{register_number, name, gpa{}, arrears{}, cgpa}]
) -> bytes:
    usable_w = L_PAGE_W - 2 * L_MARGIN
    s = []
    sections = (("SEMESTERWISE STUDENTS GPA, CGPA", "gpa"), ("SEMESTERWISE STUDENTS ARREAR DETAILS", "arrears"))
    for i, (title, key) in enumerate(sections):
        if i:
            s.append(PageBreak())
        s += _landscape_header(department, academic_year, title, mentor_name)
        s += [
            _semester_table(rows, key, usable_w),
            Spacer(1, 1.6 * cm),
            _signature_row("Signature of Mentor", "Signature of HoD", usable_w),
        ]

    buffer = io.BytesIO()
    _landscape_doc(buffer, "Semesterwise GPA, CGPA and Arrear Details").build(s)
    return buffer.getvalue()
