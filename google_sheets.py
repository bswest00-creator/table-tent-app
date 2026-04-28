import os
import json
import gspread
from google.oauth2.service_account import Credentials

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets.readonly",
    "https://www.googleapis.com/auth/drive.readonly",
]


def get_client():
    raw = os.environ.get("GOOGLE_CREDS_JSON")
    if not raw:
        raise Exception("Missing GOOGLE_CREDS_JSON environment variable")
    info = json.loads(raw)
    creds = Credentials.from_service_account_info(info, scopes=SCOPES)
    return gspread.authorize(creds)


def load_menu_from_sheet() -> list[dict]:
    """
    Returns all rows from the menu Google Sheet as a list of dicts.
    Each dict has keys matching your sheet column headers,
    e.g. {"Item Name": "Chicken", "Description": "...", "Allergens": "...", "Contains": "..."}
    """
    client = get_client()
    sheet_id = os.environ.get("SHEET_ID")
    if not sheet_id:
        raise Exception("Missing SHEET_ID environment variable")
    sheet = client.open_by_key(sheet_id).sheet1
    return sheet.get_all_records()


def lookup_items(item_names: list[str]) -> list[dict]:
    """
    Given a list of item names extracted from a PDF order form,
    returns matching rows from the sheet (case-insensitive match on 'Item Name' column).
    Unmatched items are returned with a 'not_found' flag so you can handle them gracefully.
    """
    all_items = load_menu_from_sheet()

    # Build a lookup dict keyed by normalized item name
    lookup = {row["Item Name"].strip().lower(): row for row in all_items}

    results = []
    for name in item_names:
        normalized = name.strip().lower()
        if normalized in lookup:
            results.append({**lookup[normalized], "found": True})
        else:
            results.append({
                "Item Name": name,
                "Description": "",
                "Allergens": "",
                "Contains": "",
                "found": False,
            })
    return results
