import re
import pandas as pd
import streamlit as st

from gsheet_utils import read_sheet, clear_and_write


# =====================================
# KONTEKS INDONESIA
# =====================================

INDONESIA_CONTEXT = [
    "indonesia","jakarta","jawa","sumatera","kalimantan","sulawesi","papua","bali",
    "aceh","sumut","sumbar","riau","kepri","jambi","sumsel","babel","bengkulu",
    "lampung","banten","dki","jabar","jateng","jatim","diy",
    "ntb","ntt","kalbar","kalteng","kalsel","kaltim","kaltara",
    "sulut","gorontalo","sulteng","sulbar","sulsel","sultra",
    "maluku","malut","papua barat",
    "kemnaker","disnaker","bpjs ketenagakerjaan","bpjamsostek"
]

GLOBAL_COMPANY = [
    "amazon","google","meta","facebook","instagram","apple",
    "tesla","microsoft","intel","nvidia","tiktok","netflix"
]


# =====================================
# CLEAN TEXT
# =====================================

def clean_text(text):
    text = str(text or "").lower()
    text = re.sub(r"\s+", " ", text).strip()
    return text


def contains(text, patterns):
    return any(re.search(p, text) for p in patterns)


# =====================================
# DETEKSI KATEGORI
# =====================================

def is_education(text):
    return contains(text, [
        r"cara klaim", r"panduan", r"tutorial",
        r"begini cara", r"syarat klaim", r"cek saldo",
        r"aplikasi jmo", r"\bjmo\b"
    ])


def is_indonesia(text):
    if any(g in text for g in GLOBAL_COMPANY):
        return any(k in text for k in INDONESIA_CONTEXT)
    return any(k in text for k in INDONESIA_CONTEXT)


def get_category(text):
    if is_education(text):
        return "EDUKASI"
    if is_indonesia(text):
        return "NASIONAL"
    return "GLOBAL"


# =====================================
# TIME BOOST
# =====================================

def time_boost(row):
    try:
        t = pd.to_datetime(row.get("Waktu_Publish_WIB", ""), errors="coerce")
        if pd.isna(t):
            return 0
        now = pd.Timestamp.now()
        diff = (now - t).total_seconds()/3600

        if diff <= 6:
            return 3
        if diff <= 24:
            return 2
        if diff <= 48:
            return 1
        return 0
    except:
        return 0


# =====================================
# SCORING (FINAL)
# =====================================

def scoring(text, row):

    # ==== HARD FILTER GLOBAL ====
    if any(g in text for g in GLOBAL_COMPANY) and not is_indonesia(text):
        return 0

    score = 0

    # ======================
    # PHK
    # ======================
    if contains(text, [r"\bphk\b", r"pemutusan hubungan kerja", r"dirumahkan"]):
        score += 4

    if contains(text, [r"massal", r"gelombang phk", r"ribuan", r"ratusan"]):
        score += 4

    # ======================
    # JKK
    # ======================
    if contains(text, [r"kecelakaan kerja", r"ledakan", r"kebakaran"]):
        score += 4

    if contains(text, [r"tewas", r"meninggal", r"korban jiwa"]):
        score += 4

    # ======================
    # DEMO
    # ======================
    if contains(text, [r"demo", r"unjuk rasa", r"mogok"]):
        score += 3

    # ======================
    # THR
    # ======================
    if contains(text, [r"\bthr\b"]):
        score += 2

    if contains(text, [r"tidak dibayar", r"terlambat"]):
        score += 2

    # ======================
    # UPAH
    # ======================
    if contains(text, [r"upah", r"gaji", r"ump", r"umk"]):
        score += 2

    # ======================
    # BPJS
    # ======================
    if contains(text, [r"bpjs ketenagakerjaan", r"bpjamsostek"]):
        score += 2

    # ======================
    # TIME BOOST
    # ======================
    score += time_boost(row)

    # ======================
    # CATEGORY FILTER
    # ======================
    kategori = get_category(text)

    if kategori == "GLOBAL":
        score = max(score - 4, 0)

    if kategori == "EDUKASI":
        score = 0

    return score


# =====================================
# PRIORITAS FINAL
# =====================================

def classify(score, kategori):
    if kategori in ["GLOBAL", "EDUKASI"]:
        return "PRIORITAS RENDAH"

    if score >= 9:
        return "PRIORITAS TINGGI"
    elif score >= 5:
        return "PRIORITAS SEDANG"
    else:
        return "PRIORITAS RENDAH"


# =====================================
# RUN
# =====================================

def run_priority(sheet_key=None):

    if sheet_key is None:
        sheet_key = st.secrets["SHEET_KEY"]

    df = read_sheet(sheet_key, "FILTERED")

    if df is None or df.empty:
        clear_and_write(sheet_key, "ANALYZED", pd.DataFrame())
        return

    df = df.copy()

    results = []

    for _, row in df.iterrows():

        text = clean_text(
            str(row.get("Judul","")) + " " + str(row.get("Ringkasan",""))
        )

        kategori = get_category(text)
        score = scoring(text, row)
        prioritas = classify(score, kategori)

        results.append({
            "Kategori_Berita": kategori,
            "Score": score,
            "Prioritas": prioritas
        })

    res_df = pd.DataFrame(results)

    df["Kategori_Berita"] = res_df["Kategori_Berita"]
    df["Score"] = res_df["Score"]
    df["Prioritas"] = res_df["Prioritas"]

    # 🔥 FILTER NOISE
    df = df[df["Score"] > 1]

    clear_and_write(sheet_key, "ANALYZED", df)

    return df


if __name__ == "__main__":
    run_priority()