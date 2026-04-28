from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse
from google_sheets import load_menu_from_sheet

app = FastAPI()


@app.get("/")
def home():
    return {"status": "running"}


@app.get("/menu")
def menu():
    try:
        data = load_menu_from_sheet()
        return JSONResponse(content={"menu": data})

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )
