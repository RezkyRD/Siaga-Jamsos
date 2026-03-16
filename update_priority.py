import re
import pandas as pd
import streamlit as st

from gsheet_utils import read_sheet, clear_and_write

from config import (
    FILTERED_SHEET_NAME,
    HIGH_PRIORITY_PATTERNS,
    MEDIUM_PRIORITY_PATTERNS,
    LOW_PRIORITY_PATTERNS,
    PRIORITY_THRESHOLD_HIGH,
    PRIORITY_THRESHOLD_MEDIUM,
)

# =====================================
# KONTEKS INDONESIA
# =====================================

INDONESIA_CONTEXT = [
    "jakarta","jawa","sumatera","kalimantan","sulawesi","papua","bali",
    "kemnaker","bpjs ketenagakerjaan","bpjamsostek","disnaker",
    "pekerja migran","pmi","tki","buruh indonesia",
    "pekerja indonesia","perusahaan indonesia","pabrik di indonesia",
    "jabar","jateng","jatim","bandung","surabaya","medan","makassar",
    "karawang","bekasi","tangerang","semarang","batam"
]

GLOBAL_COMPANY = [
    "amazon","google","morgan stanley","meta","facebook",
    "apple","tesla","microsoft","intel","nvidia","tiktok","netflix"
]

# =====================================
# CEK KONTEKS INDONESIA
# =====================================

def is_indonesia_related(text):

    text = (text or "").lower()

    pmi_keywords = [
        "pekerja migran indonesia",
        "pmi",
        "tki",
        "buruh indonesia",
        "pekerja indonesia"
    ]

    if any(k in text for k in pmi_keywords):
        return True

    if any(g in text for g in GLOBAL_COMPANY):

        indonesia_strong_context = [
            "di indonesia",
            "indonesia",
            "pekerja indonesia",
            "buruh indonesia",
            "pabrik di indonesia",
            "anak usaha indonesia",
            "operasi di indonesia",
            "karyawan di indonesia",
            "phk di indonesia",
            "kemnaker",
            "disnaker",
            "bpjs ketenagakerjaan",
            "bpjamsostek"
        ]

        media_only_context = [
            "cnbc indonesia","cnn indonesia","kompas.com",
            "detik","tempo.co","bisnis.com","tribun",
            "kontan","beritasatu"
        ]

        has_strong_id_context = any(k in text for k in indonesia_strong_context)
        has_only_media_context = any(m in text for m in media_only_context)

        if not has_strong_id_context or has_only_media_context:
            return False

    if any(k in text for k in INDONESIA_CONTEXT):
        return True

    return False

# =====================================
# HITUNG SKOR BERITA
# =====================================

def calculate_score(text):

    score = 0
    alasan = []

    # PRIORITAS TINGGI
    for pattern in HIGH_PRIORITY_PATTERNS:

        if re.search(pattern, text):

            score += 3
            alasan.append("Isu berdampak signifikan terhadap kondisi ketenagakerjaan.")

    # PRIORITAS SEDANG
    for pattern in MEDIUM_PRIORITY_PATTERNS:

        if re.search(pattern, text):

            score += 2
            alasan.append("Isu memiliki potensi berkembang dan perlu pemantauan.")

    # PRIORITAS RENDAH
    for pattern in LOW_PRIORITY_PATTERNS:

        if re.search(pattern, text):

            score += 1
            alasan.append("Isu bersifat informatif terkait ketenagakerjaan.")

    if not alasan:

        alasan.append(
            "Berita berkaitan dengan isu ketenagakerjaan yang berpotensi mempengaruhi kepesertaan BPJS Ketenagakerjaan."
        )

    return score, " ".join(alasan)

# =====================================
# ANALISIS PROGRAM JAMINAN SOSIAL
# =====================================

def analyze_program(text):

    program = []
    kepesertaan = []
    klaim = []

    if re.search(r"\bphk\b|\bdirumahkan\b", text):

        program.extend(["JKP","JHT","JP"])
        kepesertaan.append("PU")
        klaim.extend(["JKP","JHT"])

    if re.search(r"kecelakaan kerja|ledakan|kebakaran pabrik", text):

        program.append("JKK")
        klaim.append("JKK")

    if re.search(r"meninggal dunia|buruh tewas|pekerja tewas", text):

        program.append("JKM")
        klaim.append("JKM")

    if re.search(r"pmi|pekerja migran", text):

        kepesertaan.append("PMI")

    if re.search(r"konstruksi|proyek|pembangunan", text):

        kepesertaan.append("Jasa Konstruksi")
        program.append("JKK")

    program = list(set(program))
    kepesertaan = list(set(kepesertaan))
    klaim = list(set(klaim))

    return (
        ", ".join(program),
        ", ".join(kepesertaan),
        ", ".join(klaim)
    )

# =====================================
# KLASIFIKASI PRIORITAS
# =====================================

def classify(score):

    if score >= PRIORITY_THRESHOLD_HIGH:
        return "PRIORITAS TINGGI"

    if score >= PRIORITY_THRESHOLD_MEDIUM:
        return "PRIORITAS SEDANG"

    return "PRIORITAS RENDAH"

# =====================================
# RUN PRIORITY
# =====================================

def run_priority(sheet_key=None):

    if sheet_key is None:
        sheet_key = st.secrets["SHEET_KEY"]

    df = read_sheet(sheet_key, FILTERED_SHEET_NAME)

    if df is None or df.empty:
        return

    judul = df.get("Judul","").astype(str).fillna("")
    ringkasan = df.get("Ringkasan","").astype(str).fillna("")

    text_series = (judul + " " + ringkasan).str.lower()

    scores = []
    programs = []
    kepesertaan = []
    klaim = []
    alasan = []

    for text in text_series:

        if not is_indonesia_related(text):

            scores.append(0)
            programs.append("")
            kepesertaan.append("")
            klaim.append("")
            alasan.append(
                "Berita ketenagakerjaan global yang tidak berkaitan langsung dengan kondisi ketenagakerjaan di Indonesia."
            )
            continue

        score, reason = calculate_score(text)
        p, k, c = analyze_program(text)

        scores.append(score)
        programs.append(p)
        kepesertaan.append(k)
        klaim.append(c)
        alasan.append(reason)

    df["Score"] = scores
    df["Dampak_Program"] = programs
    df["Dampak_Kepesertaan"] = kepesertaan
    df["Potensi_Klaim"] = klaim
    df["Alasan_Prioritas"] = alasan

    df["Prioritas"] = df["Score"].apply(classify)

    clear_and_write(sheet_key, FILTERED_SHEET_NAME, df)

    return df


if __name__ == "__main__":
    run_priority()