import pdfplumber
import re
from io import BytesIO


def extract_items_from_pdf(pdf_bytes: bytes) -> list[str]:
    """
    Extracts menu item names from a structured PDF order form.

    Strategy:
    1. First tries to extract from tables (works best for grid/table PDFs)
    2. Falls back to line-by-line text parsing if no tables found

    Returns a deduplicated list of item name strings.
    """
    items = []

    with pdfplumber.open(BytesIO(pdf_bytes)) as pdf:
        for page in pdf.pages:
            # --- Strategy 1: Table extraction ---
            tables = page.extract_tables()
            if tables:
                for table in tables:
                    for row in table:
                        if not row:
                            continue
                        # The item name is typically in the first non-empty cell
                        # Adjust the column index below if your table is structured differently
                        for cell in row:
                            if cell and isinstance(cell, str):
                                cleaned = cell.strip()
                                if cleaned and not _looks_like_header(cleaned):
                                    items.append(cleaned)
                                break  # only take first meaningful cell per row
            else:
                # --- Strategy 2: Line-by-line text fallback ---
                text = page.extract_text()
                if text:
                    for line in text.splitlines():
                        cleaned = line.strip()
                        if cleaned and not _looks_like_header(cleaned):
                            items.append(cleaned)

    # Deduplicate while preserving order
    seen = set()
    unique_items = []
    for item in items:
        key = item.lower()
        if key not in seen:
            seen.add(key)
            unique_items.append(item)

    return unique_items


def _looks_like_header(text: str) -> bool:
    """
    Filters out common header/footer rows that aren't menu items.
    Customize this list based on your actual order form.
    """
    skip_patterns = [
        r"^item\s*name",
        r"^description",
        r"^qty",
        r"^quantity",
        r"^order",
        r"^menu",
        r"^date",
        r"^event",
        r"^total",
        r"^\d+$",       # pure numbers
        r"^page\s+\d+", # page numbers
    ]
    lower = text.lower().strip()
    for pattern in skip_patterns:
        if re.match(pattern, lower):
            return True
    return False
