"""
PDF generation service for Student Name List.

Produces a multi-page A4 document matching the Bannari Amman Institute format:
  - Every page: bannariammanlogo.png (full letterhead image) at the top
  - Page 1: department heading, batch year, mentor name below the image
  - All pages: S.NO / REGISTER NUMBER / NAME OF THE STUDENT table
  - Last page only: Signature of Mentor | Signature of HoD pinned to the bottom
"""

import io
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
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

# Actual image pixel dimensions: 1081 × 157
LOGO_PIXEL_W = 1081
LOGO_PIXEL_H = 157

PAGE_W, PAGE_H = A4
MARGIN = 1.8 * cm
SIG_HEIGHT = 1.2 * cm   # space reserved at the bottom for signatures

# ── Styles ─────────────────────────────────────────────────────────────────────
_base = getSampleStyleSheet()

STYLE_HEADING = ParagraphStyle(
    "sdheading",
    fontName="Helvetica-Bold",
    fontSize=12,
    leading=16,
    alignment=1,
    spaceAfter=2,
)
STYLE_SUBHEADING = ParagraphStyle(
    "sdsubheading",
    fontName="Helvetica-Bold",
    fontSize=11,
    leading=14,
    alignment=1,
    spaceAfter=2,
)
STYLE_MENTOR = ParagraphStyle(
    "sdmentor",
    fontName="Helvetica-Bold",
    fontSize=11,
    leading=14,
    alignment=1,
    spaceAfter=4,
)


# ── Story builder ──────────────────────────────────────────────────────────────

def _make_story(
    department: str,
    batch_year: str,
    mentor_name: str,
    rows: list[tuple[int, str, str]],
) -> list:
    """Build and return the full list of flowables (no signatures — those go on canvas)."""
    usable_w = PAGE_W - 2 * MARGIN
    story = []

    # ── Letterhead image ──────────────────────────────────────────────────────
    img_h = usable_w * (LOGO_PIXEL_H / LOGO_PIXEL_W)
    if LOGO_PATH.exists():
        story.append(Image(str(LOGO_PATH), width=usable_w, height=img_h))
    else:
        story.append(Spacer(usable_w, img_h))

    story.append(Spacer(1, 4 * mm))

    # ── Page-1 headings ───────────────────────────────────────────────────────
    story.append(Paragraph(f"DEPARTMENT OF {department.upper()}", STYLE_HEADING))
    story.append(Paragraph(f"STUDENT NAME LIST ({batch_year})", STYLE_SUBHEADING))
    story.append(Paragraph(f"MENTOR NAME : {mentor_name.upper()}", STYLE_MENTOR))
    story.append(Spacer(1, 2 * mm))

    # ── Student table ─────────────────────────────────────────────────────────
    col_widths = [1.4 * cm, 5.5 * cm, usable_w - 1.4 * cm - 5.5 * cm]

    header_row = [
        Paragraph("<b>S. NO</b>", _base["Normal"]),
        Paragraph("<b>REGISTER NUMBER</b>", _base["Normal"]),
        Paragraph("<b>NAME OF THE STUDENT</b>", _base["Normal"]),
    ]
    data = [header_row] + [[str(sno), reg, name] for sno, reg, name in rows]

    table = Table(data, colWidths=col_widths, repeatRows=1)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 10),
        ("ALIGN", (0, 0), (-1, 0), "CENTER"),
        ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 1), (-1, -1), 10),
        ("ALIGN", (0, 0), (0, -1), "CENTER"),
        ("ALIGN", (1, 1), (1, -1), "LEFT"),
        ("ALIGN", (2, 1), (2, -1), "LEFT"),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("GRID", (0, 0), (-1, -1), 0.75, colors.black),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    story.append(table)

    return story


# ── Canvas page callback ───────────────────────────────────────────────────────

def _make_page_callback(total_pages: int):
    """Return an onPage callback that draws signatures at the bottom of the last page."""

    def on_page(canvas, doc):
        if doc.page == total_pages:
            canvas.saveState()
            canvas.setFont("Helvetica-Oblique", 11)
            y = MARGIN * 1.2          # slightly above the bottom edge
            canvas.drawString(MARGIN, y, "Signature of Mentor")
            canvas.drawRightString(PAGE_W - MARGIN, y, "Signature of HoD")
            canvas.restoreState()

    return on_page


# ── Doc kwargs factory ─────────────────────────────────────────────────────────

def _doc_kwargs(department: str, batch_year: str, mentor_name: str) -> dict:
    return dict(
        pagesize=A4,
        leftMargin=MARGIN,
        rightMargin=MARGIN,
        topMargin=MARGIN,
        # Extra bottom margin so signatures have room without overlapping content
        bottomMargin=MARGIN + SIG_HEIGHT,
        title=f"Student Name List – {department} ({batch_year})",
        author=mentor_name,
    )


# ── Public API ─────────────────────────────────────────────────────────────────

def generate_student_list_pdf(
    department: str,
    batch_year: str,
    mentor_name: str,
    students: list[dict],
) -> bytes:
    """
    Generate and return the student name list PDF as bytes.

    Uses a two-pass build:
      Pass 1 — dry-run into a dummy buffer to count the total page count.
      Pass 2 — real render; the canvas callback draws signatures pinned to
               the bottom of the last page only.

    Args:
        department:  e.g. "Computer Science and Engineering"
        batch_year:  e.g. "2023-2027"
        mentor_name: e.g. "Dr. A. Rajkumar"
        students:    list of {"register_number": ..., "name": ...} dicts
    """
    rows = [
        (i + 1, s["register_number"], s["name"])
        for i, s in enumerate(students)
    ]
    kwargs = _doc_kwargs(department, batch_year, mentor_name)

    # ── Pass 1: count pages ────────────────────────────────────────────────────
    total_pages = [0]

    class _PageCounter(SimpleDocTemplate):
        def handle_pageEnd(self):
            total_pages[0] = self.page
            super().handle_pageEnd()

    _PageCounter(io.BytesIO(), **kwargs).build(
        _make_story(department, batch_year, mentor_name, rows)
    )

    # ── Pass 2: real render with signatures on last page ───────────────────────
    buffer = io.BytesIO()
    cb = _make_page_callback(total_pages[0])
    doc = SimpleDocTemplate(buffer, **kwargs)
    doc.build(
        _make_story(department, batch_year, mentor_name, rows),
        onFirstPage=cb,
        onLaterPages=cb,
    )
    return buffer.getvalue()
