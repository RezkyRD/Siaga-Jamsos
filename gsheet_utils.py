import time
import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials


# ===============================
# AUTH / CLIENT
# ===============================
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


# ===============================
# READ SHEET
# ===============================
@st.cache_data(ttl=60, show_spinner=False)
def read_sheet(sheet_key: str, worksheet_name: str) -> pd.DataFrame:
    sh = open_by_key(sheet_key)
    ws = sh.worksheet(worksheet_name)

    values = ws.get_all_values()
    if not values:
        return pd.DataFrame()

    headers = values[0]
    rows = values[1:]

    # buang header kosong
    headers = [h for h in headers if str(h).strip() != ""]

    if not rows:
        return pd.DataFrame(columns=headers)

    df = pd.DataFrame(rows, columns=values[0])

    # buang kolom header kosong
    df = df.loc[:, [c for c in df.columns if str(c).strip() != ""]]

    # buang baris kosong total
    df = df.dropna(how="all")
    if not df.empty:
        df = df[(df.astype(str).apply(lambda r: "".join(r).strip(), axis=1) != "")]

    return df


# ===============================
# WRITE SHEET (CHUNK SAFE)
# ===============================
def clear_and_write(
    sheet_key: str,
    worksheet_name: str,
    df: pd.DataFrame,
    chunk_size: int = 300,
    pause_sec: float = 0.35,
):
    sh = open_by_key(sheet_key)
    ws = sh.worksheet(worksheet_name)

    # kosongkan sheet dulu
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

    # pastikan tidak ada NaN / None
    df = df.copy()
    df = df.fillna("").astype(str)

    headers = df.columns.tolist()
    rows = df.values.tolist()

    # tulis header dulu
    ws.update("A1", [headers])

    total_rows = len(rows)
    total_cols = len(headers)

    # contoh: col 5 => E
    end_col_letter = gspread.utils.rowcol_to_a1(1, total_cols).rstrip("1")

    start_row = 2

    for i in range(0, total_rows, chunk_size):
        chunk = rows[i:i + chunk_size]
        if not chunk:
            continue

        end_row = start_row + len(chunk) - 1
        cell_range = f"A{start_row}:{end_col_letter}{end_row}"

        try:
            ws.update(cell_range, chunk)
        except Exception as e:
            print(f"ERROR WRITE CHUNK {worksheet_name} rows {start_row}-{end_row}: {e}")

            # retry sekali dengan chunk lebih kecil
            if len(chunk) > 1:
                sub_chunk_size = max(1, len(chunk) // 2)
                print(f"RETRY with smaller chunk size: {sub_chunk_size}")

                for j in range(0, len(chunk), sub_chunk_size):
                    sub_chunk = chunk[j:j + sub_chunk_size]
                    sub_start = start_row + j
                    sub_end = sub_start + len(sub_chunk) - 1
                    sub_range = f"A{sub_start}:{end_col_letter}{sub_end}"

                    try:
                        ws.update(sub_range, sub_chunk)
                        time.sleep(pause_sec)
                    except Exception as e2:
                        print(f"ERROR SUB-CHUNK {worksheet_name} rows {sub_start}-{sub_end}: {e2}")
                        continue
            else:
                continue

        time.sleep(pause_sec)
        start_row = end_row + 1

    read_sheet.clear()