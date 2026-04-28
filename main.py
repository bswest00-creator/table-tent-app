from fastapi import FastAPI, Request, UploadFile, File
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import os

# ----------------------------
# App setup (MUST be first)
# ----------------------------
app = FastAPI()

# ----------------------------
# Templates setup (Render-safe)
# ----------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))

# ----------------------------
# Home page
# ----------------------------
@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


# ----------------------------
# Upload endpoint (placeholder)
# ----------------------------
@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    contents = await file.read()

    return {
        "filename": file.filename,
        "size_bytes": len(contents),
        "status": "uploaded"
    }


# ----------------------------
# Health check (Render uses this a lot)
# ----------------------------
@app.get("/health")
def health():
    return {"status": "ok"}
