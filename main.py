from fastapi import FastAPI
from fastapi.responses import FileResponse
import uuid
import os

import gspread
from google.oauth2.service_account import Credentials
from docx import Document

app = FastAPI()

# ----------------------------
# GOOGLE SHEETS CONNECTION
# ----------------------------
SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly"]

def get_sheet():
    creds = Credentials.from_service_account_file(
        "service_account.json",
        scopes=SCOPES
    )
    client = gspread.authorize(creds)

    sheet = client.open("Table Tent Menu DB").sheet1
    return sheet


def load_menu():
    sheet = get_sheet()
    records = sheet.get_all_records()

    menu = {}
    for r in records:
        menu[r["item_name"].lower()] = r

    return menu


menu_db = load_menu()


# ----------------------------
# CORE GENERATOR
# ----------------------------
def generate_table_tents(items):
    output_file = f"output_{uuid.uuid4().hex}.docx"
    doc = Document()

    for item in items:
        record = menu_db.get(item.lower())

        if not record:
            continue

        doc.add_paragraph(record["display_name"])
        doc.add_paragraph(record["description"])
        doc.add_paragraph(f"Contains: {record['allergens']}")
        doc.add_paragraph(record["tags"])
        doc.add_page_break()

    doc.save(output_file)
    return output_file


# ----------------------------
# TEMP INPUT (replace later with PDF + AI)
# ----------------------------
def parse_order():
    return ["grilled chicken", "caesar salad"]


# ----------------------------
# API
# ----------------------------
@app.get("/")
def home():
    return {"status": "running"}


@app.get("/generate")
def generate():
    items = parse_order()
    file_path = generate_table_tents(items)

    return FileResponse(file_path, filename="table_tents.docx")
