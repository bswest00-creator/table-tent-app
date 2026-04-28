from fastapi import FastAPI, Request, UploadFile, File
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import os
import io

# Google Sheets imports
from google.oauth2.service_account import Credentials
import gspread

# =====================================================
# 1. APP (MUST BE FIRST — fixes your recurring crash)
# =====================================================
app = FastAPI()

# =====================================================
# 2. TEMPLATE SETUP (Render-safe absolute path)
# =====================================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))

# =====================================================
# 3. GOOGLE SHEETS SETUP
# =====================================================
GOOGLE_SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

GOOGLE_SHEET_NAME = "Table Tent Menu DB"  # must match EXACTLY

def get_google_client():
    """
    Loads Google credentials safely from file OR environment variable.
    Prevents Render crashes if credentials are missing.
    """
    try:
        creds_path = os.path.join(BASE_DIR, "service_account.json")

        creds = Credentials.from_service_account_file(
            creds_path,
            scopes=GOOGLE_SCOPES
        )

        client = gspread.authorize(creds)
        return client

    except Exception as e:
        print("Google auth error:", e)
        return None


def load_menu_from_sheets():
    """
    Pulls menu data from Google Sheets into a usable dict.
    Expected columns in sheet:
    A: item_key
    B: name
    C: description
    D: allergens
    """
    client = get_google_client()
    if not client:
        return {}

    try:
        sheet = client.open(GOOGLE_SHEET_NAME).sheet1
        rows = sheet.get_all_records()

        menu = {}

        for row in rows:
            key = str(row.get("item_key", "")).lower().strip()
            if not key:
                continue

            menu[key] = {
                "name": row.get("name", ""),
                "description": row.get("description", ""),
                "allergens": row.get("allergens", "")
            }

        return menu

    except Exception as e:
        print("Sheet load error:", e)
        return {}

# Load menu at startup (safe fallback if it fails)
menu_db = load_menu_from_sheets()

# =====================================================
# 4. ROUTES
# =====================================================

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

# =====================================================
# 5. UPLOAD ORDER FILE (PDF placeholder for now)
# =====================================================
@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    content = await file.read()

    return {
        "filename": file.filename,
        "size_bytes": len(content),
        "message": "File received successfully"
    }

# =====================================================
# 6. DEBUG ENDPOINT (SEE YOUR MENU DATA)
# =====================================================
@app.get("/menu")
def get_menu():
    return menu_db

# =====================================================
# 7. ORDER PROCESSING PLACEHOLDER
# =====================================================
@app.post("/process-order")
async def process_order(file: UploadFile = File(...)):
    content = await file.read()

    return {
        "status": "received",
        "filename": file.filename,
        "menu_items_loaded": len(menu_db),
        "note": "Next step: PDF parsing + matching"
    }

# =====================================================
# 8. SAMPLE GENERATOR
# =====================================================
@app.get("/generate-sample")
def generate_sample():
    return {
        "items": list(menu_db.keys()),
        "status": "ready"
    }
