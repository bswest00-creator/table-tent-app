from fastapi import FastAPI, UploadFile, File
from fastapi.responses import FileResponse
import csv
from docx import Document
import uuid
import os
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi import Request

templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

app = FastAPI()

# Load menu database
def load_menu():
    menu = {}
    with open("menu.csv", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            menu[row["name"].lower()] = row
    return menu

menu_db = load_menu()

# MOCK function (replace later with Claude)
def extract_items_from_pdf(file_bytes):
    # Pretend every PDF contains these items
    return ["Grilled Chicken", "Caesar Salad"]

def create_table_tents(items):
    output_file = f"output_{uuid.uuid4().hex}.docx"
    doc = Document()

    for item_name in items:
        item = menu_db.get(item_name.lower())
        if not item:
            continue

        temp = Document("template.docx")

        for p in temp.paragraphs:
            p.text = p.text.replace("{{NAME}}", item["name"])
            p.text = p.text.replace("{{DESCRIPTION}}", item["description"])
            p.text = p.text.replace("{{ALLERGENS}}", item["allergens"])

        for element in temp.element.body:
            doc.element.body.append(element)

        doc.add_page_break()

    doc.save(output_file)
    return output_file

@app.post("/upload/")
async def upload(file: UploadFile = File(...)):
    contents = await file.read()

    items = extract_items_from_pdf(contents)
    output_path = create_table_tents(items)

    return FileResponse(output_path, filename="table_tents.docx")