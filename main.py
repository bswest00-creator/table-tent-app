from fastapi import FastAPI, File, UploadFile, Request
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
import io

from google_sheets import load_menu_from_sheet, lookup_items
from pdf_parser import extract_items_from_pdf
from tent_generator import generate_tent_pdf

app = FastAPI(title="Table Tent Generator")
templates = Jinja2Templates(directory="templates")


# ── Health check ─────────────────────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


# ── Menu preview (for debugging your Sheet connection) ───────────────────────

@app.get("/menu")
def menu():
    try:
        data = load_menu_from_sheet()
        return JSONResponse(content={"count": len(data), "menu": data})
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})


# ── Main endpoint: upload PDF → get table tent PDF back ──────────────────────

@app.post("/generate")
def generate(file: UploadFile = File(...)):
    # 1. Read the uploaded PDF
    if not file.filename.lower().endswith(".pdf"):
        return JSONResponse(status_code=400, content={"error": "Please upload a PDF file."})

    pdf_bytes = file.file.read()

    # 2. Extract item names from the PDF
    try:
        item_names = extract_items_from_pdf(pdf_bytes)
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": f"PDF parsing failed: {str(e)}"})

    if not item_names:
        return JSONResponse(status_code=422, content={"error": "No items found in the PDF. Check the PDF format."})

    # 3. Look up each item in the Google Sheet
    try:
        items = lookup_items(item_names)
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": f"Google Sheets lookup failed: {str(e)}"})

    # 4. Generate the table tent PDF
    try:
        pdf_output = generate_tent_pdf(items)
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": f"PDF generation failed: {str(e)}"})

    # 5. Return the PDF as a download
    return StreamingResponse(
        io.BytesIO(pdf_output),
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=table_tents.pdf"},
    )


# ── Preview endpoint: returns JSON of what was parsed + looked up ─────────────

@app.post("/preview")
def preview(file: UploadFile = File(...)):
    """
    Same as /generate but returns JSON instead of a PDF.
    Useful for debugging — shows you exactly what was extracted and matched.
    """
    pdf_bytes = file.file.read()

    try:
        item_names = extract_items_from_pdf(pdf_bytes)
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": f"PDF parsing failed: {str(e)}"})

    try:
        items = lookup_items(item_names)
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": f"Sheets lookup failed: {str(e)}"})

    return JSONResponse(content={
        "extracted_names": item_names,
        "matched_items": items,
        "unmatched": [i["Item Name"] for i in items if not i.get("found")],
    })
