"""
PDF generation for Student Counseling Form.

Reproduces the official Bannari Amman Institute counseling form exactly:
  - Letterhead image at top
  - STUDENT COUNSELING FORM title
  - Date / Student / Year header
  - 5 numbered sections with proper drawn checkboxes (bordered box + X)
  - "Mentor Name with Signature" | "Signature of the HoD" pinned to bottom
"""

import io
from datetime import date
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm, mm
from reportlab.platypus import (
    HRFlowable,
    Image,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

ASSETS_DIR = Path(__file__).resolve().parent.parent.parent / "assets"
LOGO_PATH = ASSETS_DIR / "bannariammanlogo.png"
LOGO_PIXEL_W, LOGO_PIXEL_H = 1081, 157

PAGE_W, PAGE_H = A4
MARGIN = 1.8 * cm
BOX = 8   # checkbox square size in points

# ── Styles ─────────────────────────────────────────────────────────────────────
_ss = getSampleStyleSheet()

S_TITLE      = ParagraphStyle("cf_title",      fontName="Helvetica-Bold", fontSize=12, alignment=1, leading=18)
S_BODY       = ParagraphStyle("cf_body",       fontName="Helvetica",      fontSize=10, leading=15)
S_BOLD       = ParagraphStyle("cf_bold",       fontName="Helvetica-Bold", fontSize=10, leading=15)
S_SMALL      = ParagraphStyle("cf_small",      fontName="Helvetica",      fontSize=10, leading=15)
S_RIGHT      = ParagraphStyle("cf_right",      fontName="Helvetica",      fontSize=10, leading=15, alignment=2)
S_RIGHT_BOLD = ParagraphStyle("cf_right_bold", fontName="Helvetica-Bold", fontSize=10, leading=15, alignment=2)
S_SIG        = ParagraphStyle("cf_sig",        fontName="Helvetica-Bold", fontSize=10, leading=15)


# ── Checkbox helpers ────────────────────────────────────────────────────────────

def _box_cell(checked: bool) -> Table:
    """Return a tiny bordered table cell — filled 'X' if checked, empty if not."""
    inner = "X" if checked else " "
    t = Table([[inner]], colWidths=[BOX + 2], rowHeights=[BOX + 2])
    t.setStyle(TableStyle([
        ("BOX",           (0, 0), (-1, -1), 0.75, colors.black),
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


def _cb_row(label: str, checked: bool, usable_w: float, indent: float = 0.8 * cm) -> Table:
    """A full-width row: [indent spacer] [checkbox] [label text]."""
    box_w = BOX + 6
    label_w = usable_w - indent - box_w
    row = Table(
        [["", _box_cell(checked), Paragraph(label, S_BODY)]],
        colWidths=[indent, box_w, label_w],
    )
    row.setStyle(TableStyle([
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING",   (0, 0), (-1, -1), 0),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 0),
        ("TOPPADDING",    (0, 0), (-1, -1), 2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
    ]))
    return row


def _cb_other_row(other_val: str | None, checked: bool, usable_w: float, indent: float = 0.8 * cm) -> Table:
    """Checkbox 'Other:' row with a fill line."""
    box_w = BOX + 6
    label_w = usable_w - indent - box_w
    display = other_val or ""
    inner_t = Table(
        [["", _box_cell(checked), Paragraph(f"Other:  {display}", S_BODY)]],
        colWidths=[indent, box_w, label_w],
    )
    inner_t.setStyle(TableStyle([
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
        ("LINEBELOW",     (2, 0), (2, 0), 0.5, colors.black),
        ("LEFTPADDING",   (0, 0), (-1, -1), 0),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 0),
        ("TOPPADDING",    (0, 0), (-1, -1), 2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
    ]))
    return inner_t


# ── Inline checkbox (for Q3-5 yes/no on same line) ─────────────────────────────

def _inline_checkbox(label: str, checked: bool) -> Table:
    """[checkbox] [label] as a compact unit (for yes/no rows)."""
    t = Table(
        [[_box_cell(checked), Paragraph(f"  {label}", S_BODY)]],
        colWidths=[BOX + 4, 3.5 * cm],
    )
    t.setStyle(TableStyle([
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING",   (0, 0), (-1, -1), 0),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 0),
        ("TOPPADDING",    (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
    ]))
    return t


def _explanation_row(value: str | None, usable_w: float) -> Table:
    display = value or ""
    t = Table(
        [[Paragraph("Explanation if any:", S_SMALL), Paragraph(display, S_SMALL)]],
        colWidths=[3.8 * cm, usable_w - 3.8 * cm],
    )
    t.setStyle(TableStyle([
        ("LINEBELOW",     (1, 0), (1, 0), 0.5, colors.black),
        ("VALIGN",        (0, 0), (-1, -1), "BOTTOM"),
        ("LEFTPADDING",   (0, 0), (-1, -1), 0),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
        ("TOPPADDING",    (0, 0), (-1, -1), 0),
    ]))
    return t


# ── Story builder ───────────────────────────────────────────────────────────────

def _build_story(
    student_name: str,
    register_number: str,
    academic_year: str,
    counseling_date: date,
    reason_initiated_by: str,
    reason_details: str | None,
    attendance_status: str,
    attendance_other: str | None,
    discipline_status: str,
    discipline_other: str | None,
    attitude_status: str,
    attitude_other: str | None,
    difficulty_meeting_demands: bool,
    difficulty_explanation: str | None,
    corrective_action_needed: bool,
    corrective_action_explanation: str | None,
    next_session_needed: bool,
    next_session_explanation: str | None,
) -> list:
    usable_w = PAGE_W - 2 * MARGIN
    s = []

    # ── Letterhead ────────────────────────────────────────────────────────────
    img_h = usable_w * (LOGO_PIXEL_H / LOGO_PIXEL_W)
    s.append(Image(str(LOGO_PATH), width=usable_w, height=img_h) if LOGO_PATH.exists()
              else Spacer(usable_w, img_h))
    s.append(Spacer(1, 5 * mm))

    # ── Title ─────────────────────────────────────────────────────────────────
    s.append(Paragraph("<u><b>STUDENT COUNSELING FORM</b></u>", S_TITLE))
    s.append(Spacer(1, 5 * mm))

    # ── Date — S_RIGHT ensures right-alignment for Paragraph objects ───────────
    date_str = counseling_date.strftime("%d / %m / %Y")
    s.append(Paragraph(f"Date:  {date_str}", S_RIGHT))
    s.append(Spacer(1, 4 * mm))

    # ── Student info ──────────────────────────────────────────────────────────
    t_info = Table(
        [[
            Paragraph(f"<b>Student Roll No. &amp; Name:</b>  {register_number} – {student_name}", S_BODY),
            Paragraph(f"<b>Year:</b>  {academic_year}", S_RIGHT_BOLD),
        ]],
        colWidths=[usable_w * 0.62, usable_w * 0.38],
    )
    t_info.setStyle(TableStyle([
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING",   (0, 0), (-1, -1), 0),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 0),
        ("TOPPADDING",    (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
    ]))
    s.append(t_info)
    s.append(Spacer(1, 7 * mm))

    # ── Q1 ────────────────────────────────────────────────────────────────────
    s.append(Paragraph("1.  REASON FOR COUNSELING:", S_BOLD))
    s.append(Spacer(1, 3 * mm))
    s.append(Paragraph("    a.", S_SMALL))
    s.append(Spacer(1, 1 * mm))
    s.append(_cb_row("Student Initiated",   reason_initiated_by == "Student Initiated",   usable_w))
    s.append(_cb_row("Institute Initiated", reason_initiated_by == "Institute Initiated", usable_w))
    s.append(Spacer(1, 4 * mm))

    reason_row = Table(
        [[Paragraph("    b.  Identify the reason (if any):", S_SMALL),
          Paragraph(reason_details or "", S_SMALL)]],
        colWidths=[5.5 * cm, usable_w - 5.5 * cm],
    )
    reason_row.setStyle(TableStyle([
        ("LINEBELOW",     (1, 0), (1, 0), 0.5, colors.black),
        ("VALIGN",        (0, 0), (-1, -1), "BOTTOM"),
        ("LEFTPADDING",   (0, 0), (-1, -1), 0),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
        ("TOPPADDING",    (0, 0), (-1, -1), 0),
    ]))
    s.append(reason_row)
    s.append(Spacer(1, 3 * mm))
    s.append(HRFlowable(width=usable_w, thickness=0.5, color=colors.black))
    s.append(Spacer(1, 6 * mm))

    # ── Q2 ─────────────────────────────────────────────────────────────────
    s.append(Paragraph("2.  GENERAL OBSERVATIONS:", S_BOLD))
    s.append(Spacer(1, 4 * mm))

    # 2a Attendance
    s.append(Paragraph("    a.  Attendance:", S_SMALL))
    s.append(Spacer(1, 2 * mm))
    for opt in ["Punctual", "Occasionally Tardy", "Habitually late"]:
        s.append(_cb_row(opt, attendance_status == opt, usable_w))
    s.append(_cb_other_row(attendance_other, attendance_status == "Other", usable_w))
    s.append(Spacer(1, 6 * mm))

    # 2b Discipline
    s.append(Paragraph("    b.  Discipline:", S_SMALL))
    s.append(Spacer(1, 2 * mm))
    for opt in ["Good", "Unkept"]:
        s.append(_cb_row(opt, discipline_status == opt, usable_w))
    s.append(_cb_other_row(discipline_other, discipline_status == "Other", usable_w))
    s.append(Spacer(1, 6 * mm))

    # 2c Attitude
    s.append(Paragraph("    c.  Attitude:", S_SMALL))
    s.append(Spacer(1, 2 * mm))
    s.append(_cb_row("Willing, Eager, Pleasant", attitude_status == "Willing, Eager, Pleasant", usable_w))
    s.append(_cb_other_row(attitude_other, attitude_status == "Other", usable_w))
    s.append(Spacer(1, 8 * mm))

    # ── Q3 ────────────────────────────────────────────────────────────────────
    q3 = Table(
        [[Paragraph("3.  Is the student experiencing difficulty meeting course demands?", S_BODY),
          _inline_checkbox("Yes", difficulty_meeting_demands),
          _inline_checkbox("No",  not difficulty_meeting_demands)]],
        colWidths=[usable_w * 0.62, usable_w * 0.19, usable_w * 0.19],
    )
    q3.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
    ]))
    s.append(q3)
    s.append(Spacer(1, 3 * mm))
    s.append(_explanation_row(difficulty_explanation, usable_w))
    s.append(Spacer(1, 7 * mm))

    # ── Q4 ────────────────────────────────────────────────────────────────────
    q4 = Table(
        [[Paragraph("4.  Is corrective action needed?", S_BODY),
          _inline_checkbox("Yes", corrective_action_needed),
          _inline_checkbox("No",  not corrective_action_needed)]],
        colWidths=[usable_w * 0.62, usable_w * 0.19, usable_w * 0.19],
    )
    q4.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
    ]))
    s.append(q4)
    s.append(Spacer(1, 3 * mm))
    s.append(_explanation_row(corrective_action_explanation, usable_w))
    s.append(Spacer(1, 7 * mm))

    # ── Q5 ────────────────────────────────────────────────────────────────────
    q5 = Table(
        [[Paragraph("5.  Next counseling session:", S_BODY),
          _inline_checkbox("Needed",     next_session_needed),
          _inline_checkbox("Not Needed", not next_session_needed)]],
        colWidths=[usable_w * 0.50, usable_w * 0.25, usable_w * 0.25],
    )
    q5.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
    ]))
    s.append(q5)
    s.append(Spacer(1, 3 * mm))
    s.append(_explanation_row(next_session_explanation, usable_w))

    return s


# ── Canvas callback — signatures pinned to bottom of last page ─────────────────

def _make_page_cb(total_pages: int):
    def on_page(canvas, doc):
        if doc.page == total_pages:
            canvas.saveState()
            canvas.setFont("Helvetica-Bold", 10)
            y = MARGIN * 1.2
            canvas.drawString(MARGIN, y, "Mentor Name with Signature")
            canvas.drawRightString(PAGE_W - MARGIN, y, "Signature of the HoD")
            canvas.restoreState()
    return on_page


# ── Public API ─────────────────────────────────────────────────────────────────

def generate_counseling_pdf(
    mentor_name: str,
    student_name: str,
    register_number: str,
    academic_year: str,
    counseling_date: date,
    reason_initiated_by: str,
    reason_details: str | None,
    attendance_status: str,
    attendance_other: str | None,
    discipline_status: str,
    discipline_other: str | None,
    attitude_status: str,
    attitude_other: str | None,
    difficulty_meeting_demands: bool,
    difficulty_explanation: str | None,
    corrective_action_needed: bool,
    corrective_action_explanation: str | None,
    next_session_needed: bool,
    next_session_explanation: str | None,
) -> bytes:
    """Generate counseling form PDF. Two-pass build to pin signatures to last page."""

    kwargs = dict(
        pagesize=A4,
        leftMargin=MARGIN,
        rightMargin=MARGIN,
        topMargin=MARGIN,
        bottomMargin=MARGIN + 1.2 * cm,
    )

    def story():
        return _build_story(
            student_name, register_number, academic_year, counseling_date,
            reason_initiated_by, reason_details,
            attendance_status, attendance_other,
            discipline_status, discipline_other,
            attitude_status, attitude_other,
            difficulty_meeting_demands, difficulty_explanation,
            corrective_action_needed, corrective_action_explanation,
            next_session_needed, next_session_explanation,
        )

    # Pass 1: count pages
    total_pages = [0]

    class _Counter(SimpleDocTemplate):
        def handle_pageEnd(self):
            total_pages[0] = self.page
            super().handle_pageEnd()

    _Counter(io.BytesIO(), **kwargs).build(story())

    # Pass 2: real render
    buffer = io.BytesIO()
    cb = _make_page_cb(total_pages[0])
    doc = SimpleDocTemplate(buffer, **kwargs)
    doc.build(story(), onFirstPage=cb, onLaterPages=cb)
    return buffer.getvalue()
