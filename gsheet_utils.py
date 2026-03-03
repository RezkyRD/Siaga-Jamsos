import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials

def _client():
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive"
    ]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(
        st.secrets["gcp_service_account"],
        scope
    )
    return gspread.authorize(creds)

def open_by_key(sheet_key: str):
    return _client().open_by_key(sheet_key)

def read_sheet(sheet_key: str, worksheet_name: str) -> pd.DataFrame:
    sh = open_by_key(sheet_key)
    ws = sh.worksheet(worksheet_name)
    rows = ws.get_all_records()
    return pd.DataFrame(rows)

def append_rows(sheet_key: str, worksheet_name: str, df: pd.DataFrame):
    if df is None or df.empty:
        return
    sh = open_by_key(sheet_key)
    ws = sh.worksheet(worksheet_name)

    # kalau sheet masih kosong: tulis header dulu
    existing = ws.get_all_values()
    if len(existing) == 0:
        ws.append_row(df.columns.tolist())

    # append data
    ws.append_rows(df.astype(str).values.tolist())

def clear_and_write(sheet_key: str, worksheet_name: str, df: pd.DataFrame):
    sh = open_by_key(sheet_key)
    ws = sh.worksheet(worksheet_name)
    ws.clear()
    if df is None or df.empty:
        ws.append_row(["EMPTY"])
        return
    ws.update([df.columns.tolist()] + df.astype(str).values.tolist())