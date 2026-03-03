import pandas as pd

from gsheet_utils import read_sheet, clear_and_write


def run_filter(sheet_key: str | None = None):
    if not sheet_key:
        import streamlit as st
        sheet_key = st.secrets["SHEET_KEY"]

    keywords = [
        "phk",
        "demo buruh",
        "bpjs",
        "jkp",
        "mogok",
        "konflik buruh",
        "jht",
        "jkk",
        "jkm",
        "jp",
        "buruh",
        "umr",
        "ketenagakerjaan",
    ]

    df = read_sheet(sheet_key, "RAW")

    if df.empty:
        clear_and_write(sheet_key, "FILTERED", df)  # tulis kosong tapi schema aman
        return df

    if "Judul" not in df.columns:
        # kalau tidak ada judul, tidak bisa filter: tulis kosong
        clear_and_write(sheet_key, "FILTERED", df.iloc[0:0].copy())
        return df.iloc[0:0].copy()

    def contains_keyword(text) -> bool:
        t = str(text or "").lower()
        return any(k in t for k in keywords)

    df_filtered = df[df["Judul"].apply(contains_keyword)].copy()

    clear_and_write(sheet_key, "FILTERED", df_filtered)
    return df_filtered


if __name__ == "__main__":
    run_filter()