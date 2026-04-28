import os
import json
import gspread
from google.oauth2.service_account import Credentials
from functools import lru_cache

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets.readonly",
    "https://www.googleapis.com/auth/drive.readonly"
]


def get_creds():
    raw = os.environ.get("GOOGLE_CREDS_JSON")

    if not raw:
        raise Exception("Missing GOOGLE_CREDS_JSON")

    info = json.loads(raw)
    return Credentials.from_service_account_info(info, scopes=SCOPES)


def get_client():
    creds = get_creds()
    return gspread.authorize(creds)


@lru_cache(maxsize=1)
def load_menu_from_sheet():
    client = get_client()

    SHEET_ID = os.environ.get("SHEET_ID")

    if not SHEET_ID:
        raise Exception("Missing SHEET_ID")

    sheet = client.open_by_key(SHEET_ID).sheet1

    data = sheet.get_all_records()

    return data
