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
    data_rows = values[1:]

    # jika sheet hanya header atau kosong
    if not data_rows:
        return pd.DataFrame(columns=[h for h in headers if str(h).strip() != ""])

    df = pd.DataFrame(data_rows, columns=headers)

    # buang kolom header kosong
    df = df.loc[:, [c for c in df.columns if str(c).strip() != ""]]

    # buang baris yang seluruhnya kosong
    df = df.dropna(how="all")
    df = df[(df.astype(str).apply(lambda r: "".join(r).strip(), axis=1) != "")]

    return df


def clear_and_write(sheet_key: str, worksheet_name: str, df: pd.DataFrame):
    sh = open_by_key(sheet_key)
    ws = sh.worksheet(worksheet_name)

    ws.clear()

    if df is None:
        read_sheet.clear()
        return

    # kalau df kosong, tetap tulis header (jangan bikin schema kacau)
    if df.empty:
        if len(df.columns) > 0:
            ws.update([df.columns.tolist()])
        else:
            ws.update([[""]])
        read_sheet.clear()
        return

    values = [df.columns.tolist()] + df.astype(str).values.tolist()
    ws.update(values)

    # cache read dibersihkan agar pembacaan berikutnya fresh
    read_sheet.clear()