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

    try:
        df = read_sheet(sheet_key, "FILTERED")
    except Exception:
        df = pd.DataFrame()

    if df is None or df.empty:
        empty_df = pd.DataFrame(columns=OUTPUT_COLUMNS)
        clear_and_write(sheet_key, "ANALYZED", empty_df)
        return empty_df

    df = df.copy()
    df.columns = df.columns.astype(str).str.strip()

    judul = df.get("Judul", pd.Series([""] * len(df), index=df.index)).astype(str).fillna("")
    ringkasan = df.get("Ringkasan", pd.Series([""] * len(df), index=df.index)).astype(str).fillna("")
    text_series = (judul + " " + ringkasan).apply(clean_text)

    hasil = []
    konteks_list = []
    provinsi_list = []
    kabkota_list = []
    status_lokasi_list = []

    for idx, text in enumerate(text_series):
        row = df.iloc[idx].to_dict()

        konteks = get_context_label(text)
        konteks_list.append(konteks)

        lokasi = detect_location(text)
        provinsi_list.append(lokasi["Provinsi"])
        kabkota_list.append(lokasi["Kabupaten_Kota"])
        status_lokasi_list.append(lokasi["Status_Lokasi"])

        hasil.append(analyze_jamsos(text, row=row))

    hasil_df = pd.DataFrame(hasil)

    df["Konteks_Berita"] = konteks_list
    df["Kategori_Berita"] = hasil_df["Kategori_Berita"]
    df["Provinsi"] = provinsi_list
    df["Kabupaten_Kota"] = kabkota_list
    df["Status_Lokasi"] = status_lokasi_list
    df["Topik_Utama"] = hasil_df["Topik_Utama"]
    df["Score"] = pd.to_numeric(hasil_df["Score"], errors="coerce").fillna(0).astype(int)
    df["Dampak_Program"] = hasil_df["Dampak_Program"]
    df["Dampak_Kepesertaan"] = hasil_df["Dampak_Kepesertaan"]
    df["Potensi_Klaim"] = hasil_df["Potensi_Klaim"]
    df["Alasan_Prioritas"] = hasil_df["Alasan_Prioritas"]

    df["Prioritas"] = df.apply(
        lambda r: classify_priority(
            int(r["Score"]),
            str(r["Kategori_Berita"]),
            str(r["Topik_Utama"])
        ),
        axis=1
    )

    # =========================
    # FINAL TUNING OUTPUT
    # =========================

    # 1. Buang berita global murni
    df = df[
        ~(
            (df["Kategori_Berita"].astype(str) == "GLOBAL") &
            (df["Konteks_Berita"].astype(str) == "LUAR NEGERI / TIDAK RELEVAN")
        )
    ].copy()

    # 2. Buang berita dengan skor terlalu rendah
    df = df[df["Score"] >= 2].copy()

    # 3. Jika ingin edukasi tetap ada, biarkan.
    # Kalau ingin lebih bersih lagi, aktifkan baris di bawah:
    # df = df[df["Kategori_Berita"].astype(str) != "EDUKASI"].copy()

    # 4. Rapikan kolom akhir
    df = ensure_columns(df)

    # 5. Sorting final: prioritas -> skor -> waktu
    priority_order = {
        "PRIORITAS TINGGI": 1,
        "PRIORITAS SEDANG": 2,
        "PRIORITAS RENDAH": 3
    }
    df["__prio_order"] = df["Prioritas"].map(priority_order).fillna(99)
    if "Waktu_Publish_WIB" in df.columns:
        df["__publish_dt"] = pd.to_datetime(df["Waktu_Publish_WIB"], errors="coerce")
        df = df.sort_values(
            ["__prio_order", "Score", "__publish_dt"],
            ascending=[True, False, False]
        )
        df = df.drop(columns=["__publish_dt"], errors="ignore")
    else:
        df = df.sort_values(
            ["__prio_order", "Score"],
            ascending=[True, False]
        )

    df = df.drop(columns=["__prio_order"], errors="ignore")

    clear_and_write(sheet_key, "ANALYZED", df)
    return df


if __name__ == "__main__":
    run_priority()