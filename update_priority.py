import pandas as pd
import re
import streamlit as st

from gsheet_utils import read_sheet, clear_and_write


def run_priority():
    print("Update prioritas dimulai...")

    SHEET_KEY = st.secrets["1usVNpV9PWDQzh9p_ix0hHY4lvlG02mKcEZAyiimooMs"]

    # ==============================
    # BACA DATA DARI GOOGLE SHEET (FILTERED)
    # ==============================
    df = read_sheet(SHEET_KEY, "FILTERED")

    if df.empty:
        print("Sheet FILTERED kosong.")
        return

    # ==============================
    # KEYWORD SCORE MAP (regex lebih fleksibel)
    # ==============================
    score_map = [
        # PRIORITAS TINGGI
        (r"phk.*massal|massal.*phk", 5),
        (r"gelombang phk|phk gelombang", 5),
        (r"ribuan (buruh|pekerja)", 5),
        (r"pabrik tutup|tutup permanen|bangkrut", 5),
        (r"kerusuhan|bentrok|ricuh", 4),
        (r"blokade|aksi besar|ancam tutup", 4),
        (r"dirumahkan|layoff", 4),

        # PRIORITAS SEDANG
        (r"mogok kerja|mogok", 3),
        (r"aksi buruh|unjuk rasa|demo", 3),
        (r"tuntutan upah", 3),
        (r"perselisihan|konflik buruh", 2),
        (r"upah tidak dibayar", 2),
        (r"serikat pekerja", 2),
        (r"penutupan sementara", 2),

        # PRIORITAS RENDAH
        (r"\bphk\b", 1),
        (r"upah|tenaga kerja|ketenagakerjaan", 1),
    ]

    def calculate_score(text):
        text = str(text).lower()
        score = 0
        for pattern, nilai in score_map:
            if re.search(pattern, text):
                score += nilai
        return score

    # ==============================
    # GABUNGKAN JUDUL + RINGKASAN
    # ==============================
    text_series = df.get("Judul", "").astype(str).fillna("")
    if "Ringkasan" in df.columns:
        text_series = text_series + " " + df["Ringkasan"].astype(str).fillna("")

    # ==============================
    # APPLY ANALISIS
    # ==============================
    df["Score"] = text_series.apply(calculate_score)

    def classify_priority(score):
        if score >= 6:
            return "PRIORITAS TINGGI"
        elif score >= 3:
            return "PRIORITAS SEDANG"
        else:
            return "PRIORITAS RENDAH"

    df["Prioritas"] = df["Score"].apply(classify_priority)

    # ==============================
    # STATUS NASIONAL (EWS)
    # ==============================
    tinggi = (df["Prioritas"] == "PRIORITAS TINGGI").sum()

    if tinggi >= 5:
        status = "MERAH"
    elif tinggi >= 1:
        status = "KUNING"
    else:
        status = "HIJAU"

    df["Status_EWS"] = status

    # ==============================
    # SIMPAN KEMBALI KE SHEET FILTERED
    # ==============================
    clear_and_write(SHEET_KEY, "FILTERED", df)

    print("Prioritas berhasil diperbarui.")
    print("Status nasional:", status)


if __name__ == "__main__":
    run_priority()