"""
PDF services for Mentor-Mentee Meeting:

1. generate_circular_pdf   — Official circular announcing the meeting
2. generate_minutes_pdf    — Minutes of meeting with per-student attendance table
                              Matches the reference image exactly:
                              Header info rows → bordered 4-col table → Prepared by / Approved by
"""

import io
from datetime import date
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm, mm
from reportlab.platypus import (
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

# ── Shared Styles ───────────────────────────────────────────────────────────────

S_DEPT   = ParagraphStyle("m_dept",   fontName="Helvetica-Bold", fontSize=13, leading=18, alignment=TA_CENTER)
S_DATE   = ParagraphStyle("m_date",   fontName="Helvetica",      fontSize=11, leading=16, alignment=TA_RIGHT)
S_CIRC   = ParagraphStyle("m_circ",   fontName="Helvetica-Bold", fontSize=12, leading=16, alignment=TA_CENTER)
S_BODY   = ParagraphStyle("m_body",   fontName="Helvetica",      fontSize=11, leading=17, alignment=TA_JUSTIFY)
S_LABEL  = ParagraphStyle("m_label",  fontName="Helvetica",      fontSize=11, leading=16, alignment=TA_LEFT)
S_LABEL_B= ParagraphStyle("m_label_b",fontName="Helvetica-Bold", fontSize=11, leading=16, alignment=TA_LEFT)
S_AGENDA = ParagraphStyle("m_agenda", fontName="Helvetica",      fontSize=11, leading=16, alignment=TA_LEFT)

# Minutes-specific
S_MOM_TH  = ParagraphStyle("mom_th",   fontName="Helvetica-Bold", fontSize=10, leading=13, alignment=TA_CENTER)
S_MOM_TITLE = ParagraphStyle("mom_title", fontName="Helvetica-Bold", fontSize=11, leading=15, alignment=TA_CENTER)
S_MOM_CELL= ParagraphStyle("mom_cell", fontName="Helvetica",      fontSize=9,  leading=13, alignment=TA_LEFT)
S_MOM_NUM = ParagraphStyle("mom_num",  fontName="Helvetica-Bold", fontSize=9,  leading=13, alignment=TA_CENTER)
S_MOM_SIG = ParagraphStyle("mom_sig",  fontName="Helvetica-Bold", fontSize=11, leading=16, alignment=TA_LEFT)
S_MOM_SIGR= ParagraphStyle("mom_sigr", fontName="Helvetica-Bold", fontSize=11, leading=16, alignment=TA_RIGHT)

# ── Helpers ────────────────────────────────────────────────────────────────────

_ROMAN = [
    (1000,"M"),(900,"CM"),(500,"D"),(400,"CD"),
    (100,"C"),(90,"XC"),(50,"L"),(40,"XL"),
    (10,"X"),(9,"IX"),(5,"V"),(4,"IV"),(1,"I"),
]

def _to_roman(n: int) -> str:
    result = ""
    for val, sym in _ROMAN:
        while n >= val:
            result += sym
            n -= val
    return result


def _letterhead(usable_w: float):
    img_h = usable_w * (LOGO_PIXEL_H / LOGO_PIXEL_W)
    return (Image(str(LOGO_PATH), width=usable_w, height=img_h)
            if LOGO_PATH.exists() else Spacer(usable_w, img_h))


def _dept_date_row(department: str, date_str: str, usable_w: float) -> Table:
    """3-col table: [empty] [Dept centered] [Date right-aligned]."""
    DATE_COL = 3.8 * cm
    t = Table(
        [["", Paragraph(f"Department of {department}", S_DEPT),
          Paragraph(f"Date:  {date_str}", S_DATE)]],
        colWidths=[DATE_COL, usable_w - 2 * DATE_COL, DATE_COL],
    )
    t.setStyle(TableStyle([
        ("VALIGN",        (0, 0), (-1, -1), "BOTTOM"),
        ("LEFTPADDING",   (0, 0), (-1, -1), 0),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 0),
        ("TOPPADDING",    (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
    ]))
    return t


def _base_doc_kwargs(title: str) -> dict:
    return dict(
        pagesize=A4,
        leftMargin=MARGIN,
        rightMargin=MARGIN,
        topMargin=MARGIN,
        bottomMargin=MARGIN + 1.5 * cm,
        title=title,
    )


def _two_pass(story_fn, doc_kwargs: dict, sig_cb) -> bytes:
    """Two-pass build so signature is pinned to last page."""
    total_pages = [0]

    class _Counter(SimpleDocTemplate):
        def handle_pageEnd(self):
            total_pages[0] = self.page
            super().handle_pageEnd()

    _Counter(io.BytesIO(), **doc_kwargs).build(story_fn())

    buffer = io.BytesIO()
    cb = sig_cb(total_pages[0])
    doc = SimpleDocTemplate(buffer, **doc_kwargs)
    doc.build(story_fn(), onFirstPage=cb, onLaterPages=cb)
    return buffer.getvalue()


# ══════════════════════════════════════════════════════════════════════════════
# 1. CIRCULAR PDF
# ══════════════════════════════════════════════════════════════════════════════

def _circular_sig_cb(total_pages: int):
    def on_page(canvas, doc):
        if doc.page == total_pages:
            canvas.saveState()
            canvas.setFont("Helvetica-Bold", 11)
            y = MARGIN * 1.2
            canvas.drawString(MARGIN, y, "Mentor Signature")
            canvas.drawRightString(PAGE_W - MARGIN, y, "Signature of the HOD")
            canvas.restoreState()
    return on_page


def _circular_story(
    department: str,
    meeting_date: date,
    meeting_time: str,
    location: str,
    semester: str,
    meeting_number: int,
    agenda_items: list[str],
) -> list:
    usable_w = PAGE_W - 2 * MARGIN
    s = []

    s.append(_letterhead(usable_w))
    s.append(Spacer(1, 6 * mm))
    s.append(_dept_date_row(department, meeting_date.strftime("%d.%m.%Y"), usable_w))
    s.append(Spacer(1, 5 * mm))

    s.append(Paragraph("CIRCULAR", S_CIRC))
    s.append(Paragraph(f"Student Meeting – {_to_roman(meeting_number)}", S_CIRC))
    s.append(Spacer(1, 5 * mm))

    s.append(Paragraph(f"Year &amp; Semester:  {semester}", S_LABEL))
    s.append(Spacer(1, 5 * mm))

    date_fmt = meeting_date.strftime("%d.%m.%Y")
    body = (
        f"A meeting has been scheduled on <b>{date_fmt}</b> at <b>{meeting_time}</b> "
        f"in the <b>{location}</b>. All students are required to attend the meeting "
        f"without fail."
    )
    s.append(Paragraph(body, S_BODY))
    s.append(Spacer(1, 8 * mm))

    s.append(Paragraph("Agenda:", S_LABEL))
    s.append(Spacer(1, 3 * mm))
    NUM_W = 1.2 * cm
    for i, item in enumerate(agenda_items):
        row = Table(
            [[Paragraph(f"{i + 1}.", S_LABEL_B), Paragraph(item, S_AGENDA)]],
            colWidths=[NUM_W, usable_w - NUM_W],
        )
        row.setStyle(TableStyle([
            ("VALIGN",        (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING",   (0, 0), (-1, -1), 0),
            ("RIGHTPADDING",  (0, 0), (-1, -1), 0),
            ("TOPPADDING",    (0, 0), (-1, -1), 2),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
        ]))
        s.append(row)
    return s


def generate_circular_pdf(
    department: str,
    meeting_date: date,
    meeting_time: str,
    location: str,
    semester: str,
    meeting_number: int,
    agenda_items: list[str],
) -> bytes:
    kwargs = _base_doc_kwargs(f"Circular – Student Meeting {_to_roman(meeting_number)}")
    return _two_pass(
        lambda: _circular_story(
            department, meeting_date, meeting_time, location,
            semester, meeting_number, agenda_items,
        ),
        kwargs,
        _circular_sig_cb,
    )


# ══════════════════════════════════════════════════════════════════════════════
# 2. MINUTES OF MEETING PDF
# ══════════════════════════════════════════════════════════════════════════════

def _minutes_sig_cb(total_pages: int):
    """Prepared by / Approved by pinned to bottom of last page."""
    def on_page(canvas, doc):
        if doc.page == total_pages:
            canvas.saveState()
            canvas.setFont("Helvetica-Bold", 11)
            y = MARGIN * 1.2
            canvas.drawString(MARGIN, y, "Prepared by:")
            canvas.drawRightString(PAGE_W - MARGIN, y, "Approved by:")
            canvas.restoreState()
    return on_page


def _numbered_cell_content(items: list[str]) -> Paragraph:
    """Format a list of strings as a numbered paragraph block for a table cell."""
    if not items:
        return Paragraph("", S_MOM_CELL)
    lines = []
    for i, item in enumerate(items):
        lines.append(f"{i + 1}.&nbsp;&nbsp;{item}")
    return Paragraph("<br/>".join(lines), S_MOM_CELL)


def _minutes_story(
    department: str,
    meeting_date: date,
    semester: str,
    academic_year: str,
    year_of_study: str,
    meeting_number: int,
    mentor_name: str,
    attendees: list[dict],   # [{register_number, name, points_discussed, action_planned}]
) -> list:
    usable_w = PAGE_W - 2 * MARGIN
    s = []

    # ── Letterhead ─────────────────────────────────────────────────────────────
    s.append(_letterhead(usable_w))
    s.append(Spacer(1, 5 * mm))

    # ── Department (centered, no date on this form per the image) ─────────────
    s.append(Paragraph(f"Department of {department}", S_DEPT))
    s.append(Spacer(1, 6 * mm))

    # ── Header info rows (left/right pairs) ───────────────────────────────────
    # Row 1: AcademicYear (left)  |  Semester (right)
    # Row 2: Year of study (left)
    # Row 3: Mentor Name (left)   |  Date (right)
    # Row 4: Student Members Present (left)
    half = usable_w / 2

    def _kv(label: str, value: str = "") -> list:
        return [Paragraph(f"<b>{label}</b>  {value}", S_LABEL)]

    header_table = Table(
        [
            [_kv("Academic Year:", academic_year)[0],  _kv("Semester:", semester)[0]],
            [_kv("Year of study:", year_of_study)[0],  ""],
            [_kv("Mentor Name:", mentor_name)[0],       _kv("Date:", meeting_date.strftime("%d.%m.%Y"))[0]],
            [_kv("Student Members Present:")[0],        ""],
        ],
        colWidths=[half, half],
    )
    header_table.setStyle(TableStyle([
        ("VALIGN",        (0, 0), (-1, -1), "TOP"),
        ("ALIGN",         (1, 0), (1, -1), "RIGHT"),
        ("LEFTPADDING",   (0, 0), (-1, -1), 0),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 0),
        ("TOPPADDING",    (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("FONTNAME",      (0, 0), (-1, -1), "Helvetica"),
        ("FONTSIZE",      (0, 0), (-1, -1), 11),
    ]))
    s.append(header_table)
    s.append(Spacer(1, 8 * mm))

    # ── Minutes table ──────────────────────────────────────────────────────────
    # Column widths matching image: S No | Reg+Name | Points Discussed | Action Planned
    SN_W   = 1.0 * cm
    REG_W  = 3.5 * cm
    REST   = usable_w - SN_W - REG_W
    PD_W   = REST * 0.5
    AP_W   = REST * 0.5

    # Title spanning row
    title_row = [
        Paragraph("Minutes of the Meeting", S_MOM_TITLE), "", "", ""
    ]

    # Header row
    header_row = [
        Paragraph("S No",            S_MOM_TH),
        Paragraph("Reg. No. &\nStudent Name", S_MOM_TH),
        Paragraph("Points Discussed", S_MOM_TH),
        Paragraph("Action Planned",   S_MOM_TH),
    ]

    table_data = [title_row, header_row]

    for idx, att in enumerate(attendees):
        reg_cell = Paragraph(
            f"{att['register_number']}<br/>{att['name']}", S_MOM_CELL
        )
        pd_cell  = _numbered_cell_content(att.get("points_discussed", []))
        ap_cell  = _numbered_cell_content(att.get("action_planned", []))
        table_data.append([
            Paragraph(str(idx + 1), S_MOM_NUM),
            reg_cell,
            pd_cell,
            ap_cell,
        ])

    main_table = Table(
        table_data,
        colWidths=[SN_W, REG_W, PD_W, AP_W],
        repeatRows=2,
    )
    main_table.setStyle(TableStyle([
        # Title row — merged, shaded
        ("SPAN",          (0, 0), (3, 0)),
        ("BACKGROUND",    (0, 0), (3, 0), colors.HexColor("#e8e8e8")),
        ("ALIGN",         (0, 0), (3, 0), "CENTER"),
        ("VALIGN",        (0, 0), (-1, -1), "TOP"),

        # All borders
        ("BOX",           (0, 0), (-1, -1), 0.75, colors.black),
        ("INNERGRID",     (0, 0), (-1, -1), 0.5, colors.black),

        # Header row bold
        ("FONTNAME",      (0, 1), (-1, 1), "Helvetica-Bold"),
        ("BACKGROUND",    (0, 1), (-1, 1), colors.HexColor("#f5f5f5")),

        # Padding
        ("LEFTPADDING",   (0, 0), (-1, -1), 4),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 4),
        ("TOPPADDING",    (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),

        # S No column centered
        ("ALIGN",         (0, 0), (0, -1), "CENTER"),
        ("ALIGN",         (1, 0), (1, -1), "LEFT"),
    ]))
    s.append(main_table)
    return s


def generate_minutes_pdf(
    department: str,
    meeting_date: date,
    meeting_time: str,
    location: str,
    semester: str,
    academic_year: str,
    year_of_study: str,
    meeting_number: int,
    mentor_name: str,
    attendees: list[dict],
) -> bytes:
    """Generate the minutes of meeting PDF matching the official format."""
    kwargs = _base_doc_kwargs(f"Minutes – Student Meeting {_to_roman(meeting_number)}")
    return _two_pass(
        lambda: _minutes_story(
            department, meeting_date, semester, academic_year,
            year_of_study, meeting_number, mentor_name, attendees,
        ),
        kwargs,
        _minutes_sig_cb,
    )
