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


def get_or_create_worksheet(
    sheet_key: str,
    worksheet_name: str,
    rows: int = 5000,
    cols: int = 40
):
    sh = open_by_key(sheet_key)
    try:
        return sh.worksheet(worksheet_name)
    except gspread.WorksheetNotFound:
        return sh.add_worksheet(
            title=worksheet_name,
            rows=str(rows),
            cols=str(cols)
        )


@st.cache_data(ttl=60, show_spinner=False)
def read_sheet(sheet_key: str, worksheet_name: str) -> pd.DataFrame:
    ws = get_or_create_worksheet(sheet_key, worksheet_name)

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


def replace_sheet(sheet_key: str, worksheet_name: str, df: pd.DataFrame):
    """
    Overwrite penuh isi worksheet.
    Cocok untuk FILTERED / ANALYZED / BACKUP.
    """
    ws = get_or_create_worksheet(sheet_key, worksheet_name)
    ws.clear()

    if df is None:
        read_sheet.clear()
        return

    if df.empty:
        if len(df.columns) > 0:
            ws.update([df.columns.tolist()])
        else:
            ws.update([[""]])
        read_sheet.clear()
        return

    ws.update([df.columns.tolist()] + df.astype(str).values.tolist())
    read_sheet.clear()


def append_rows(sheet_key: str, worksheet_name: str, df: pd.DataFrame):
    """
    Tambah baris ke worksheet tanpa menghapus isi lama.
    Cocok untuk RAW_LOG_HARIAN.
    """
    if df is None or df.empty:
        return

    ws = get_or_create_worksheet(sheet_key, worksheet_name)

    existing = ws.get_all_values()
    if not existing:
        ws.update([df.columns.tolist()] + df.astype(str).values.tolist())
    else:
        ws.append_rows(
            df.astype(str).values.tolist(),
            value_input_option="RAW"
        )

    read_sheet.clear()


def backup_sheet(sheet_key: str, source_name: str, backup_name: str):
    """
    Salin isi satu worksheet ke worksheet backup.
    """
    try:
        df = read_sheet(sheet_key, source_name)
    except Exception:
        df = pd.DataFrame()

    replace_sheet(sheet_key, backup_name, df)


def clear_and_write(sheet_key: str, worksheet_name: str, df: pd.DataFrame):
    """
    Backward-compatible dengan file lama.
    Untuk sementara tetap diarahkan ke replace_sheet.
    """
    replace_sheet(sheet_key, worksheet_name, df)