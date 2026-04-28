from fastapi import FastAPI, Request, UploadFile, File
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates

import os
import json
import gspread
from google.oauth2.service_account import Credentials

# -----------------------
# APP INIT (MUST BE FIRST)
# -----------------------
app = FastAPI()
templates = Jinja2Templates(directory="templates")

# -----------------------
# GOOGLE SHEETS SETUP
# -----------------------
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

def get_google_client():
    """
    Reads credentials from environment variable (Render-safe approach)
    """
    creds_json = os.getenv("GOOGLE_CREDS_JSON")

    if not creds_json:
        raise Exception("Missing GOOGLE_CREDS_JSON environment variable")

    creds_dict = json.loads(creds_json)

    creds = Credentials.from_service_account_info(
        creds_dict,
        scopes=SCOPES
    )

    return gspread.authorize(creds)

def get_menu_data():
    client = get_google_client()

    # CHANGE THIS to your sheet name
    sheet = client.open("Table Tents").worksheet("Menu")

    return sheet.get_all_records()

# -----------------------
# ROUTES
# -----------------------

@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse(
        "index.html",
        {"request": request}
    )

@app.get("/menu")
def menu():
    try:
        data = get_menu_data()
        return JSONResponse(content=data)
    except Exception as e:
        return JSONResponse(content={"error": str(e)})

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    """
    Placeholder for future PDF parsing + AI generation
    """
    content = await file.read()

    return {
        "filename": file.filename,
        "size": len(content),
        "status": "received"
    }
