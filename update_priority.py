import pandas as pd
import re
import streamlit as st

from gsheet_utils import read_sheet, clear_and_write


# =====================================
# KONTEKS INDONESIA
# =====================================

INDONESIA_CONTEXT = [
"indonesia","jakarta","jawa","sumatera","kalimantan","sulawesi","papua","bali",
"kemnaker","bpjs ketenagakerjaan","bpjamsostek","disnaker",
"pekerja migran","pmi","tki","buruh indonesia"
]


def is_indonesia_related(text):

    text = text.lower()

    for k in INDONESIA_CONTEXT:
        if k in text:
            return True

    return False


# =====================================
# ANALISIS JAMINAN SOSIAL
# =====================================

def analyze_jamsos(text):

    score = 0

    program = []
    kepesertaan = []
    klaim = []
    alasan = []

    # ======================
    # PHK
    # ======================

    if re.search(r"\bphk\b|\blayoff\b|\bdirumahkan\b", text):

        score += 4

        program.extend(["JKP","JHT","JP"])
        kepesertaan.append("PU")

        klaim.append("JKP")
        klaim.append("JHT")

        alasan.append(
        "Pemberitaan mengenai PHK berpotensi meningkatkan klaim JKP serta pencairan JHT bagi pekerja terdampak."
        )

    # PHK MASSAL
    if re.search(r"phk.*massal|massal.*phk", text):

        score += 6

        alasan.append(
        "PHK massal berpotensi menurunkan jumlah kepesertaan pekerja penerima upah serta meningkatkan klaim JKP."
        )

    # ======================
    # KECELAKAAN KERJA
    # ======================

    if re.search(r"kecelakaan kerja|ledakan|kebakaran pabrik|tertimbun", text):

        score += 4

        program.append("JKK")
        klaim.append("JKK")

        alasan.append(
        "Peristiwa kecelakaan kerja berpotensi menimbulkan klaim JKK."
        )

    # ======================
    # KEMATIAN PEKERJA
    # ======================

    if re.search(r"meninggal dunia|pekerja tewas|buruh tewas", text):

        score += 3

        program.append("JKM")
        klaim.append("JKM")

        alasan.append(
        "Kematian pekerja berpotensi menimbulkan klaim JKM bagi ahli waris."
        )

    # ======================
    # DEMO BURUH
    # ======================

    if re.search(r"demo|unjuk rasa|aksi buruh|mogok", text):

        score += 3

        alasan.append(
        "Aksi buruh menunjukkan potensi konflik hubungan industrial yang dapat berdampak pada stabilitas ketenagakerjaan."
        )
    # ======================
    # THR
    # ======================

    if re.search(r"\bthr\b|tunjangan hari raya", text):

        score += 2
        kepesertaan.append("PU")

        alasan.append(
        "Isu pembayaran THR menunjukkan potensi permasalahan hubungan industrial yang dapat mempengaruhi stabilitas pekerja penerima upah."
        )

    if re.search(r"thr.*tidak dibayar|tidak dibayar.*thr|thr.*terlambat|terlambat.*thr|thr.*dicicil|thr.*dipotong|pengaduan thr|posko thr", text):

        score += 3

        alasan.append(
        "Permasalahan pembayaran THR dapat memicu pengaduan pekerja, perselisihan hubungan industrial, dan berpotensi berdampak pada kepatuhan perusahaan."
        )

    # ======================
    # PMI
    # ======================

    if re.search(r"pmi|pekerja migran", text):

        kepesertaan.append("PMI")

        alasan.append(
        "Isu pekerja migran dapat mempengaruhi kepesertaan BPJS Ketenagakerjaan bagi PMI."
        )

    # ======================
    # KONSTRUKSI
    # ======================

    if re.search(r"konstruksi|proyek|pembangunan", text):

        kepesertaan.append("Jasa Konstruksi")
        program.append("JKK")

        alasan.append(
        "Sektor konstruksi memiliki risiko kecelakaan kerja tinggi sehingga berkaitan dengan program JKK."
        )

    # ======================
    # DEFAULT
    # ======================

    if not alasan:

        alasan.append(
        "Berita berkaitan dengan isu ketenagakerjaan yang berpotensi mempengaruhi kepesertaan BPJS Ketenagakerjaan."
        )

    program = list(set(program))
    kepesertaan = list(set(kepesertaan))
    klaim = list(set(klaim))

    return (
        score,
        ", ".join(program),
        ", ".join(kepesertaan),
        ", ".join(klaim),
        " ".join(alasan)
    )


# =====================================
# RUN PRIORITY
# =====================================

def run_priority(sheet_key=None):

    if sheet_key is None:
        sheet_key = st.secrets["SHEET_KEY"]

    df = read_sheet(sheet_key, "FILTERED")

    if df is None or df.empty:
        return

    judul = df.get("Judul", "").astype(str).fillna("")
    ringkasan = df.get("Ringkasan", "").astype(str).fillna("")

    text_series = (judul + " " + ringkasan).str.lower()

    scores = []
    programs = []
    kepesertaan = []
    klaim = []
    alasan = []

    for text in text_series:

        # =========================
        # FILTER INDONESIA
        # =========================

        if not is_indonesia_related(text):

            scores.append(0)
            programs.append("")
            kepesertaan.append("")
            klaim.append("")
            alasan.append(
            "Berita ketenagakerjaan global yang tidak berkaitan langsung dengan kondisi ketenagakerjaan di Indonesia."
            )

            continue

        score, p, k, c, a = analyze_jamsos(text)

        scores.append(score)
        programs.append(p)
        kepesertaan.append(k)
        klaim.append(c)
        alasan.append(a)

    df["Score"] = scores
    df["Dampak_Program"] = programs
    df["Dampak_Kepesertaan"] = kepesertaan
    df["Potensi_Klaim"] = klaim
    df["Alasan_Prioritas"] = alasan


    # ======================
    # KLASIFIKASI PRIORITAS
    # ======================

    def classify(score):

        if score >= 7:
            return "PRIORITAS TINGGI"

        elif score >= 4:
            return "PRIORITAS SEDANG"

        else:
            return "PRIORITAS RENDAH"

    df["Prioritas"] = df["Score"].apply(classify)

    clear_and_write(sheet_key, "FILTERED", df)

    return df


if __name__ == "__main__":
    run_priority()