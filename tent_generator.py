from reportlab.lib.pagesizes import landscape, letter
from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor, black, white
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.utils import simpleSplit
from io import BytesIO
import os

# ── Colors matching Baker's Best style ──────────────────────────────────────
COLOR_BORDER = HexColor("#AAAAAA")
COLOR_FOOTER_LINE = HexColor("#CCCCCC")
COLOR_TEXT_DARK = HexColor("#1A1A1A")
COLOR_TEXT_GRAY = HexColor("#555555")
COLOR_FOOTER_TEXT = HexColor("#888888")
BRAND_NAME = "baker's best catering"

# ── Page layout (landscape Letter = 11" × 8.5") ─────────────────────────────
PAGE_W, PAGE_H = landscape(letter)  # 792 × 612 pts
MARGIN = 0.35 * inch
TENT_W = (PAGE_W - 3 * MARGIN) / 2   # two tents side-by-side
TENT_H = PAGE_H - 2 * MARGIN         # full height minus top/bottom margins


def _register_fonts():
    """Try to load EB Garamond from a local fonts/ folder; fall back to Helvetica."""
    font_dir = os.path.join(os.path.dirname(__file__), "fonts")
    try:
        pdfmetrics.registerFont(TTFont("EBGaramond", os.path.join(font_dir, "EBGaramond-regular.ttf")))
        pdfmetrics.registerFont(TTFont("EBGaramond-Bold", os.path.join(font_dir, "EBGaramond-bold.ttf")))
        return "EBGaramond", "EBGaramond-Bold"
    except Exception:
        return "Helvetica", "Helvetica-Bold"


def _wrap_text(c, text, font, size, max_width):
    """Split text into lines that fit within max_width."""
    c.setFont(font, size)
    return simpleSplit(text, font, size, max_width)


def _draw_tent(c, x, y, item: dict, font_regular: str, font_bold: str):
    """
    Draw a single table tent card at position (x, y) — bottom-left corner.

    item dict keys (matching your Google Sheet columns):
        Item Name   : str
        Description : str
        Allergens   : str  (shown in parentheses)
        Contains    : str  (shown as CONTAINS: X in bold, optional)
    """
    pad = 0.3 * inch
    inner_w = TENT_W - 2 * pad
    cx = x + TENT_W / 2  # horizontal center

    # ── Border ───────────────────────────────────────────────────────────────
    c.setStrokeColor(COLOR_BORDER)
    c.setLineWidth(1)
    c.roundRect(x, y, TENT_W, TENT_H, radius=6, stroke=1, fill=0)

    # ── Footer branding ───────────────────────────────────────────────────────
    footer_y = y + 0.25 * inch
    c.setStrokeColor(COLOR_FOOTER_LINE)
    c.setLineWidth(0.5)
    c.line(x + pad, footer_y + 10, x + TENT_W - pad, footer_y + 10)
    c.setFont(font_regular, 7)
    c.setFillColor(COLOR_FOOTER_TEXT)
    c.drawCentredString(cx, footer_y, BRAND_NAME)

    # ── Content area: stack from vertical center ──────────────────────────────
    # We'll calculate total content height first, then center it vertically
    name = item.get("Item Name", "")
    description = item.get("Description", "")
    allergens = item.get("Allergens", "")
    contains = item.get("Contains", "")

    # Pre-calculate line counts
    name_size = _choose_name_size(name)
    name_lines = _wrap_text(c, name, font_bold, name_size, inner_w)

    desc_lines = _wrap_text(c, description, font_regular, 9.5, inner_w) if description else []
    allergen_text = f"({allergens})" if allergens else ""
    allergen_lines = _wrap_text(c, allergen_text, font_regular, 9, inner_w) if allergen_text else []
    contains_text = f"CONTAINS: {contains.upper()}" if contains else ""

    line_h_name = name_size * 1.25
    line_h_desc = 9.5 * 1.4
    line_h_allergen = 9 * 1.4
    gap = 0.12 * inch

    total_h = (
        len(name_lines) * line_h_name
        + (gap + len(desc_lines) * line_h_desc if desc_lines else 0)
        + (gap + len(allergen_lines) * line_h_allergen if allergen_lines else 0)
        + (gap + 12 if contains_text else 0)
    )

    # Start drawing from vertical center of tent (excluding footer)
    usable_top = y + TENT_H - 0.2 * inch
    usable_bottom = footer_y + 20
    usable_h = usable_top - usable_bottom
    start_y = usable_bottom + (usable_h + total_h) / 2

    cursor = start_y

    # Item Name (large, bold, centered)
    c.setFillColor(COLOR_TEXT_DARK)
    for line in name_lines:
        c.setFont(font_bold, name_size)
        cursor -= line_h_name
        c.drawCentredString(cx, cursor, line)

    # Description
    if desc_lines:
        cursor -= gap
        for line in desc_lines:
            c.setFont(font_regular, 9.5)
            c.setFillColor(COLOR_TEXT_GRAY)
            cursor -= line_h_desc
            c.drawCentredString(cx, cursor, line)

    # Allergens in parentheses
    if allergen_lines:
        cursor -= gap
        for line in allergen_lines:
            c.setFont(font_regular, 9)
            c.setFillColor(COLOR_TEXT_GRAY)
            cursor -= line_h_allergen
            c.drawCentredString(cx, cursor, line)

    # Contains line (bold, dark)
    if contains_text:
        cursor -= gap
        c.setFont(font_bold, 9.5)
        c.setFillColor(COLOR_TEXT_DARK)
        cursor -= 12
        c.drawCentredString(cx, cursor, contains_text)


def _choose_name_size(name: str) -> float:
    """Scale font size based on name length to prevent overflow."""
    length = len(name)
    if length <= 12:
        return 26
    elif length <= 22:
        return 21
    elif length <= 35:
        return 17
    else:
        return 14


def generate_tent_pdf(items: list[dict]) -> bytes:
    """
    Given a list of item dicts (from google_sheets.lookup_items),
    generates a print-ready landscape PDF with 2-up table tent cards.

    Returns the PDF as bytes.
    """
    font_regular, font_bold = _register_fonts()

    buf = BytesIO()
    c = canvas.Canvas(buf, pagesize=landscape(letter))
    c.setTitle("Table Tents")

    left_x = MARGIN
    right_x = MARGIN + TENT_W + MARGIN
    tent_y = MARGIN

    for i, item in enumerate(items):
        col = i % 2
        if col == 0 and i > 0:
            # Both columns filled — new page
            c.showPage()

        x = left_x if col == 0 else right_x
        _draw_tent(c, x, tent_y, item, font_regular, font_bold)

    c.save()
    return buf.getvalue()
