import pandas as pd
import streamlit as st
import re

from gsheet_utils import read_sheet, clear_and_write


def run_filter():

    SHEET_KEY = st.secrets["SHEET_KEY"]

    # ===============================
    # KEYWORD BERBASIS REGEX (LEBIH KUAT)
    # ===============================
    KEYWORD_PATTERNS = [
        r"\bphk\b",
        r"pemutusan hubungan kerja",
        r"\bdirumahkan\b",
        r"phk massal",
        r"gelombang phk",

        r"\bthr\b",
        r"tunjangan hari raya",
        r"thr.*tidak dibayar",
        r"thr.*terlambat",

        r"\bupah\b",
        r"\bgaji\b",
        r"ump|umk",
        r"upah minimum",

        r"\bburuh\b",
        r"\bpekerja\b",
        r"tenaga kerja",

        r"demo buruh",
        r"aksi buruh",
        r"mogok",
        r"mogok kerja",

        r"bpjs ketenagakerjaan",
        r"bpjamsostek",
        r"\bjht\b",
        r"\bjkp\b",
        r"\bjkk\b",
        r"\bjkm\b",
        r"\bjp\b",

        r"kecelakaan kerja",
        r"ledakan pabrik",
        r"buruh tewas",
        r"pekerja tewas",

        r"tunggakan iuran",
        r"denda bpjs",
        r"tidak patuh",
        r"sanksi perusahaan"
    ]

    # ===============================
    # BACA DATA
    # ===============================
    df = read_sheet(SHEET_KEY, "RAW")

    if df.empty:
        print("Sheet RAW kosong.")
        return

    # ===============================
    # FILTER BERBASIS JUDUL + RINGKASAN
    # ===============================
    def is_relevant(row):
        text = f"{row.get('Judul','')} {row.get('Ringkasan','')}".lower()

        return any(re.search(pattern, text) for pattern in KEYWORD_PATTERNS)

    df_filtered = df[df.apply(is_relevant, axis=1)].copy()

    # ===============================
    # OPTIONAL: HAPUS DUPLIKAT LAGI (AMAN)
    # ===============================
    if "UID" in df_filtered.columns:
        df_filtered = df_filtered.drop_duplicates(subset=["UID"], keep="last")

    # ===============================
    # SIMPAN KE SHEET FILTERED
    # ===============================
    clear_and_write(SHEET_KEY, "FILTERED", df_filtered)

    print("Total RAW:", len(df))
    print("Total Lolos Keyword:", len(df_filtered))


if __name__ == "__main__":
    run_filter()