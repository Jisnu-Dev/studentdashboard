"""
Exam PDF service — two documents matching the official BIT format:

1. generate_pt_marks_pdf   — PERIODICAL TEST PT I / PT II MARKS
   Table: S.NO | REGISTER NUMBER | NAME OF THE STUDENT
          | [SubjCode PT I | PT II] * N subjects

2. generate_semester_pdf   — SEMESTER END EXAMINATION GRADE
   Table: S.NO | REGISTER NUMBER | NAME OF THE STUDENT
          | [Subject Code Grade] * N subjects

Both end with:  Signature of Mentor   Signature of HoD
"""

import io
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4, landscape
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

PAGE_W, PAGE_H = landscape(A4)   # Landscape – wider for many subjects
MARGIN = 1.5 * cm

# ── Styles ─────────────────────────────────────────────────────────────────────

S_TITLE  = ParagraphStyle("ex_title",  fontName="Helvetica-Bold", fontSize=12, leading=16, alignment=TA_CENTER)
S_TH     = ParagraphStyle("ex_th",     fontName="Helvetica-Bold", fontSize=8,  leading=11, alignment=TA_CENTER)
S_TD     = ParagraphStyle("ex_td",     fontName="Helvetica",      fontSize=8,  leading=11, alignment=TA_CENTER)
S_TD_L   = ParagraphStyle("ex_td_l",   fontName="Helvetica",      fontSize=8,  leading=11, alignment=TA_LEFT)

# ── Helpers ────────────────────────────────────────────────────────────────────

def _letterhead(usable_w: float):
    img_h = usable_w * (LOGO_PIXEL_H / LOGO_PIXEL_W)
    return (Image(str(LOGO_PATH), width=usable_w, height=img_h)
            if LOGO_PATH.exists() else Spacer(usable_w, img_h))


def _sig_callback(total_pages: int):
    def on_page(canvas, doc):
        if doc.page == total_pages:
            canvas.saveState()
            canvas.setFont("Helvetica", 10)
            y = MARGIN * 1.0
            canvas.drawString(MARGIN, y, "Signature of Mentor")
            canvas.drawRightString(PAGE_W - MARGIN, y, "Signature of HoD")
            canvas.restoreState()
    return on_page


def _two_pass(story_fn, doc_kwargs: dict) -> bytes:
    total_pages = [0]

    class _Counter(SimpleDocTemplate):
        def handle_pageEnd(self):
            total_pages[0] = self.page
            super().handle_pageEnd()

    _Counter(io.BytesIO(), **doc_kwargs).build(story_fn())

    buffer = io.BytesIO()
    cb = _sig_callback(total_pages[0])
    doc = SimpleDocTemplate(buffer, **doc_kwargs)
    doc.build(story_fn(), onFirstPage=cb, onLaterPages=cb)
    return buffer.getvalue()


def _base_kwargs(title: str) -> dict:
    return dict(
        pagesize=landscape(A4),
        leftMargin=MARGIN,
        rightMargin=MARGIN,
        topMargin=MARGIN,
        bottomMargin=MARGIN + 1.0 * cm,
        title=title,
    )


def _header_block(department: str, academic_year: str, title_line: str, mentor_name: str, usable_w: float) -> list:
    return [
        _letterhead(usable_w),
        Spacer(1, 5 * mm),
        Paragraph(f"DEPARTMENT OF {department.upper()}", S_TITLE),
        Paragraph(f"ACADEMIC YEAR ({academic_year})", S_TITLE),
        Paragraph(title_line, S_TITLE),
        Paragraph(f"MENTOR NAME :  {mentor_name}", S_TITLE),
        Spacer(1, 4 * mm),
    ]


# ── Column width calculator ────────────────────────────────────────────────────

FIXED_W   = 1.0 * cm   # S.NO
REG_W     = 3.0 * cm   # REGISTER NUMBER
NAME_W    = 5.0 * cm   # NAME OF STUDENT


def _subject_col_width(n_subjects: int, n_sub_cols: int, usable_w: float) -> float:
    """Remaining width divided equally across subject sub-columns."""
    remaining = usable_w - FIXED_W - REG_W - NAME_W
    total_sub_cols = n_subjects * n_sub_cols
    return max(remaining / total_sub_cols, 1.4 * cm)


# ══════════════════════════════════════════════════════════════════════════════
# 1. PT1 / PT2 MARKS PDF
# ══════════════════════════════════════════════════════════════════════════════

def _pt_story(
    department: str,
    academic_year: str,
    mentor_name: str,
    subject_codes: list[str],
    student_records: list[dict],
    pt_number: int,   # 1 or 2
) -> list:
    usable_w = PAGE_W - 2 * MARGIN
    pt_key = "pt1_marks" if pt_number == 1 else "pt2_marks"
    title = f"PERIODICAL TEST PT {'I' if pt_number == 1 else 'II'} MARKS"
    s = _header_block(department, academic_year, title, mentor_name, usable_w)

    n = len(subject_codes)
    sub_w = _subject_col_width(n, 1, usable_w)   # 1 col per subject
    col_widths = [FIXED_W, REG_W, NAME_W] + [sub_w] * n

    # Header: one column per subject
    hdr = [
        Paragraph("S.\nNO",              S_TH),
        Paragraph("REGISTER\nNUMBER",    S_TH),
        Paragraph("NAME OF THE\nSTUDENT", S_TH),
    ] + [Paragraph(f"Subject\nCode\n{code}", S_TH) for code in subject_codes]

    table_data = [hdr]
    for idx, rec in enumerate(student_records):
        row = [
            Paragraph(str(idx + 1), S_TD),
            Paragraph(rec.get("register_number", ""), S_TD),
            Paragraph(rec.get("name", ""), S_TD_L),
        ]
        marks_dict = rec.get(pt_key, {})
        for code in subject_codes:
            row.append(Paragraph(str(marks_dict.get(code, "")), S_TD))
        table_data.append(row)

    tbl = Table(table_data, colWidths=col_widths, repeatRows=1)
    tbl.setStyle(TableStyle([
        ("BOX",           (0, 0), (-1, -1), 0.75, colors.black),
        ("INNERGRID",     (0, 0), (-1, -1), 0.5,  colors.black),
        ("BACKGROUND",    (0, 0), (-1, 0),  colors.HexColor("#f0f0f0")),
        ("FONTNAME",      (0, 0), (-1, 0),  "Helvetica-Bold"),
        ("FONTSIZE",      (0, 0), (-1, -1), 8),
        ("ALIGN",         (0, 0), (-1, -1), "CENTER"),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN",         (2, 1), (2, -1),  "LEFT"),
        ("LEFTPADDING",   (0, 0), (-1, -1), 2),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 2),
        ("TOPPADDING",    (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("ROWBACKGROUNDS",(0, 1), (-1, -1), [colors.white, colors.HexColor("#fafafa")]),
    ]))
    s.append(tbl)
    return s


def generate_pt_marks_pdf(
    department: str,
    academic_year: str,
    mentor_name: str,
    subject_codes: list[str],
    student_records: list[dict],
    pt_number: int = 1,
) -> bytes:
    """Generate PT1 or PT2 marks sheet as a separate PDF."""
    title_str = f"PT {'I' if pt_number == 1 else 'II'} Marks"
    kwargs = _base_kwargs(title_str)
    return _two_pass(
        lambda: _pt_story(department, academic_year, mentor_name,
                          subject_codes, student_records, pt_number),
        kwargs,
    )


# ══════════════════════════════════════════════════════════════════════════════
# 2. SEMESTER END EXAMINATION GRADE PDF
# ══════════════════════════════════════════════════════════════════════════════

def _semester_story(
    department: str,
    academic_year: str,
    mentor_name: str,
    subject_codes: list[str],
    student_records: list[dict],   # [{register_number, name, semester_grades{}}]
) -> list:
    usable_w = PAGE_W - 2 * MARGIN
    s = _header_block(department, academic_year, "SEMESTER END EXAMINATION GRADE", mentor_name, usable_w)

    n = len(subject_codes)
    sub_w = _subject_col_width(n, 1, usable_w)  # 1 col per subject

    col_widths = [FIXED_W, REG_W, NAME_W] + [sub_w] * n

    # Header row
    hdr = [
        Paragraph("S.\nNO",              S_TH),
        Paragraph("REGISTER\nNUMBER",    S_TH),
        Paragraph("NAME OF THE\nSTUDENT", S_TH),
    ] + [Paragraph(f"Subject\nCode\n{code}", S_TH) for code in subject_codes]

    table_data = [hdr]

    for idx, rec in enumerate(student_records):
        row = [
            Paragraph(str(idx + 1), S_TD),
            Paragraph(rec.get("register_number", ""), S_TD),
            Paragraph(rec.get("name", ""), S_TD_L),
        ]
        for code in subject_codes:
            grade = rec.get("semester_grades", {}).get(code, "")
            row.append(Paragraph(str(grade), S_TD))
        table_data.append(row)

    tbl = Table(table_data, colWidths=col_widths, repeatRows=1)
    tbl.setStyle(TableStyle([
        ("BOX",           (0, 0), (-1, -1), 0.75, colors.black),
        ("INNERGRID",     (0, 0), (-1, -1), 0.5,  colors.black),
        ("BACKGROUND",    (0, 0), (-1, 0),  colors.HexColor("#f0f0f0")),
        ("FONTNAME",      (0, 0), (-1, 0),  "Helvetica-Bold"),
        ("FONTSIZE",      (0, 0), (-1, -1), 8),
        ("ALIGN",         (0, 0), (-1, -1), "CENTER"),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN",         (2, 1), (2, -1),  "LEFT"),
        ("LEFTPADDING",   (0, 0), (-1, -1), 2),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 2),
        ("TOPPADDING",    (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("ROWBACKGROUNDS",(0, 1), (-1, -1), [colors.white, colors.HexColor("#fafafa")]),
    ]))

    s.append(tbl)
    return s


def generate_semester_pdf(
    department: str,
    academic_year: str,
    mentor_name: str,
    subject_codes: list[str],
    student_records: list[dict],
) -> bytes:
    kwargs = _base_kwargs("Semester End Examination Grade")
    return _two_pass(
        lambda: _semester_story(department, academic_year, mentor_name, subject_codes, student_records),
        kwargs,
    )
