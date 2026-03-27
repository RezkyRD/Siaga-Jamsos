import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials


def _client():
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive",
    ]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(
        st.secrets["gcp_service_account"], scope
    )
    return gspread.authorize(creds)


def open_by_key(sheet_key: str):
    return _client().open_by_key(sheet_key)


@st.cache_data(ttl=60, show_spinner=False)
def read_sheet(sheet_key: str, worksheet_name: str) -> pd.DataFrame:
    sh = open_by_key(sheet_key)
    ws = sh.worksheet(worksheet_name)

    values = ws.get_all_values()
    if not values:
        return pd.DataFrame()

    headers = values[0]
    rows = values[1:]

    if not rows:
        return pd.DataFrame(columns=[h for h in headers if str(h).strip() != ""])

    df = pd.DataFrame(rows, columns=headers)

    # buang kolom header kosong
    df = df.loc[:, [c for c in df.columns if str(c).strip() != ""]]

    # buang baris kosong total
    df = df.dropna(how="all")
    df = df[(df.astype(str).apply(lambda r: "".join(r).strip(), axis=1) != "")]

    return df


def clear_and_write(sheet_key: str, worksheet_name: str, df: pd.DataFrame, chunk_size: int = 500):
    sh = open_by_key(sheet_key)
    ws = sh.worksheet(worksheet_name)
    ws.clear()

    if df is None:
        read_sheet.clear()
        return

    if df.empty:
        if len(df.columns) > 0:
            ws.update("A1", [df.columns.tolist()])
        else:
            ws.update("A1", [[""]])
        read_sheet.clear()
        return

    # pastikan semua string dan tidak ada NaN
    df = df.fillna("").astype(str)

    headers = df.columns.tolist()
    rows = df.values.tolist()

    # tulis header dulu
    ws.update("A1", [headers])

    # tulis isi per chunk
    start_row = 2
    for i in range(0, len(rows), chunk_size):
        chunk = rows[i:i + chunk_size]
        end_row = start_row + len(chunk) - 1

        start_col_letter = "A"
        end_col_letter = gspread.utils.rowcol_to_a1(1, len(headers)).rstrip("1")
        cell_range = f"{start_col_letter}{start_row}:{end_col_letter}{end_row}"

        ws.update(cell_range, chunk)
        start_row = end_row + 1

    read_sheet.clear()