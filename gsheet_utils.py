import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials


# =====================================
# GOOGLE SHEETS CLIENT
# =====================================

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


def get_or_create_worksheet(sheet_key: str, worksheet_name: str, rows: int = 2000, cols: int = 40):
    """
    Ambil worksheet. Jika belum ada, buat otomatis.
    """
    sh = open_by_key(sheet_key)
    try:
        ws = sh.worksheet(worksheet_name)
    except gspread.WorksheetNotFound:
        ws = sh.add_worksheet(title=worksheet_name, rows=rows, cols=cols)
    return ws


# =====================================
# READ SHEET
# =====================================

@st.cache_data(ttl=60, show_spinner=False)
def read_sheet(sheet_key: str, worksheet_name: str) -> pd.DataFrame:
    """
    Membaca worksheet menjadi DataFrame.
    """
    ws = get_or_create_worksheet(sheet_key, worksheet_name)

    values = ws.get_all_values()
    if not values:
        return pd.DataFrame()

    headers = values[0]
    rows = values[1:]

    # rapikan header
    headers = [str(h).strip() for h in headers]

    if not rows:
        return pd.DataFrame(columns=[h for h in headers if h != ""])

    df = pd.DataFrame(rows, columns=headers)

    # buang kolom header kosong
    df = df.loc[:, [c for c in df.columns if str(c).strip() != ""]]

    # rapikan nama kolom
    df.columns = [str(c).strip() for c in df.columns]

    # ubah nilai object jadi string strip
    for col in df.columns:
        df[col] = df[col].astype(str).fillna("").str.strip()

    # buang baris kosong total
    df = df[(df.astype(str).apply(lambda r: "".join(r).strip(), axis=1) != "")]

    return df.reset_index(drop=True)


# =====================================
# WRITE SHEET (OVERWRITE)
# =====================================

def clear_and_write(sheet_key: str, worksheet_name: str, df: pd.DataFrame):
    """
    Menghapus isi worksheet lalu menulis ulang seluruh DataFrame.
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

    df = df.copy()
    df.columns = [str(c).strip() for c in df.columns]
    df = df.fillna("").astype(str)

    ws.update([df.columns.tolist()] + df.values.tolist())
    read_sheet.clear()


# =====================================
# APPEND SHEET
# =====================================

def append_rows(sheet_key: str, worksheet_name: str, df: pd.DataFrame):
    """
    Menambahkan baris ke bawah worksheet tanpa menghapus data lama.
    """
    if df is None or df.empty:
        return

    ws = get_or_create_worksheet(sheet_key, worksheet_name)

    existing_values = ws.get_all_values()

    df = df.copy()
    df.columns = [str(c).strip() for c in df.columns]
    df = df.fillna("").astype(str)

    rows = df.values.tolist()

    if not existing_values:
        ws.update([df.columns.tolist()] + rows)
    else:
        ws.append_rows(rows, value_input_option="RAW")

    read_sheet.clear()


# =====================================
# HELPER KHUSUS SIAGA JAMSOS
# =====================================

def read_filtered(sheet_key: str) -> pd.DataFrame:
    return read_sheet(sheet_key, "FILTERED")


def read_raw_news(sheet_key: str) -> pd.DataFrame:
    return read_sheet(sheet_key, "RAW_NEWS")


def read_master_kategori(sheet_key: str) -> pd.DataFrame:
    return read_sheet(sheet_key, "MASTER_KATEGORI_ISU")


def read_master_regulasi(sheet_key: str) -> pd.DataFrame:
    return read_sheet(sheet_key, "MASTER_REGULASI")


def read_hasil_analisis(sheet_key: str) -> pd.DataFrame:
    return read_sheet(sheet_key, "HASIL_ANALISIS")


def write_filtered(sheet_key: str, df: pd.DataFrame):
    clear_and_write(sheet_key, "FILTERED", df)


def write_raw_news(sheet_key: str, df: pd.DataFrame):
    clear_and_write(sheet_key, "RAW_NEWS", df)


def write_hasil_analisis(sheet_key: str, df: pd.DataFrame):
    clear_and_write(sheet_key, "HASIL_ANALISIS", df)