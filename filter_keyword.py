import pandas as pd
import streamlit as st

from gsheet_utils import read_sheet, clear_and_write


def run_filter():

    SHEET_KEY = "1usVNpV9PWDQzh9p_ix0hHY4lvlG02mKcEZAyiimooMs"

    keywords = [
        "PHK",
        "demo buruh",
        "BPJS",
        "JKP",
        "mogok",
        "konflik buruh",
        "JHT",
        "JKK",
        "JKM",
        "JP",
        "buruh",
        "UMR",
        "Ketenagakerjaan",
    ]

    # ===============================
    # BACA DATA DARI GOOGLE SHEET (RAW)
    # ===============================
    df = read_sheet(SHEET_KEY, "RAW")

    if df.empty:
        print("Sheet RAW kosong.")
        return

    # ===============================
    # FILTER KEYWORD
    # ===============================
    def contains_keyword(text):
        if pd.isna(text):
            return False
        return any(k.lower() in str(text).lower() for k in keywords)

    df_filtered = df[df["Judul"].apply(contains_keyword)].copy()

    # ===============================
    # SIMPAN KE SHEET FILTERED
    # ===============================
    clear_and_write(SHEET_KEY, "FILTERED", df_filtered)

    print("Total RAW:", len(df))
    print("Total Lolos Keyword:", len(df_filtered))


if __name__ == "__main__":
    run_filter()