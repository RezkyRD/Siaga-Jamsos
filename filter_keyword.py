import re
from typing import List

import pandas as pd
import streamlit as st

from gsheet_utils import read_sheet, clear_and_write
from config import (
    RAW_SHEET_NAME,
    FILTERED_SHEET_NAME,
    KEYWORDS_KETENAGAKERJAAN,
    KEYWORDS_JAMSOS,
    TOPIC_RULES,
    TOPIC_FALLBACK_BPJS,
    TOPIC_FALLBACK_KETENAGAKERJAAN,
    TOPIC_DEFAULT,
)

SHEET_KEY = st.secrets["SHEET_KEY"]


def normalize_text(text) -> str:
    if pd.isna(text):
        return ""

    text = str(text).lower().strip()
    text = re.sub(r"http\S+|www\.\S+", " ", text)
    text = re.sub(r"[^a-zA-Z0-9\s/%()-]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def combine_text_columns(df: pd.DataFrame) -> pd.Series:
    judul = df["Judul"].astype(str) if "Judul" in df.columns else ""
    ringkasan = df["Ringkasan"].astype(str) if "Ringkasan" in df.columns else ""

    if isinstance(judul, str) and isinstance(ringkasan, str):
        return pd.Series(dtype="object")

    return (judul.fillna("") + " " + ringkasan.fillna("")).astype(str)


def contains_any_keyword(text: str, keywords: List[str]) -> bool:
    if not text:
        return False

    t = normalize_text(text)
    for kw in keywords:
        kw_norm = normalize_text(kw)
        if kw_norm and kw_norm in t:
            return True
    return False


def extract_detected_keywords(text: str, keywords: List[str]) -> str:
    if not text:
        return ""

    t = normalize_text(text)
    found = []

    for kw in keywords:
        kw_norm = normalize_text(kw)
        if kw_norm and kw_norm in t:
            found.append(kw)

    unique_found = list(dict.fromkeys(found))
    return ", ".join(unique_found)


def detect_topic(text: str) -> str:
    t = normalize_text(text)

    for topic, patterns in TOPIC_RULES.items():
        for pattern in patterns:
            if re.search(pattern, t):
                return topic

    if re.search(TOPIC_FALLBACK_BPJS, t):
        return "Kepesertaan BPJS"

    if re.search(TOPIC_FALLBACK_KETENAGAKERJAAN, t):
        return "Konflik Hubungan Industrial"

    return TOPIC_DEFAULT


def detect_program_impact(topic: str, text: str) -> str:
    t = normalize_text(text)

    if topic == "PHK":
        return "PU"
    if topic == "THR / Kesejahteraan Pekerja":
        return "PU"
    if topic == "Upah / Gaji":
        return "PU"
    if topic == "Aksi / Demo Buruh":
        return "PU"
    if topic == "Konflik Hubungan Industrial":
        return "PU"
    if topic == "Pabrik Tutup / Pailit":
        return "PU"
    if topic == "Kepesertaan BPJS":
        return "PU, BPU, PMI, Jasa Konstruksi"
    if topic == "Klaim JHT":
        return "JHT"
    if topic == "Manfaat JKP":
        return "JKP"
    if topic == "Jaminan Pensiun (JP)":
        return "JP"
    if topic == "Kecelakaan Kerja (JKK)":
        return "JKK"
    if topic == "Santunan Kematian (JKM)":
        return "JKM"
    if topic == "Pekerja Migran Indonesia (PMI)":
        return "PMI"
    if topic == "Jasa Konstruksi":
        return "Jasa Konstruksi"

    if "bpjs" in t or "bpjamsostek" in t or "jamsostek" in t:
        return "PU, BPU"

    return "Umum"


def detect_kepesertaan_impact(topic: str, text: str) -> str:
    t = normalize_text(text)

    if topic == "PHK":
        return "Penurunan kepesertaan PU"
    if topic == "Pabrik Tutup / Pailit":
        return "Risiko penurunan kepesertaan PU"
    if topic == "Kepesertaan BPJS":
        return "Perluasan / kepatuhan kepesertaan"
    if topic == "Pengawasan Kepatuhan":
        return "Kepatuhan perusahaan"
    if topic == "Tunggakan Iuran":
        return "Risiko ketidakpatuhan iuran"
    if topic == "Pekerja Migran Indonesia (PMI)":
        return "Kepesertaan PMI"

    if "tidak terdaftar" in t or "belum terdaftar" in t:
        return "Gap kepesertaan"

    return "Tidak langsung"


def detect_claim_impact(topic: str, text: str) -> str:
    t = normalize_text(text)

    if topic == "PHK":
        return "JKP, JHT"
    if topic == "Klaim JHT":
        return "JHT"
    if topic == "Manfaat JKP":
        return "JKP"
    if topic == "Jaminan Pensiun (JP)":
        return "JP"
    if topic == "Kecelakaan Kerja (JKK)":
        return "JKK"
    if topic == "Santunan Kematian (JKM)":
        return "JKM"
    if topic == "Kendala Klaim BPJS":
        return "JHT/JKP/JKK/JKM"

    if "kecelakaan kerja" in t:
        return "JKK"
    if "meninggal dunia" in t or "buruh tewas" in t or "pekerja tewas" in t:
        return "JKM"

    return "-"


def run_filter() -> pd.DataFrame:
    df = read_sheet(SHEET_KEY, RAW_SHEET_NAME)

    if df is None or df.empty:
        print("[filter_keyword] Sheet RAW kosong.")
        empty_df = pd.DataFrame()
        clear_and_write(SHEET_KEY, FILTERED_SHEET_NAME, empty_df)
        return empty_df

    df = df.copy()
    df.columns = df.columns.astype(str).str.strip()

    combined_text = combine_text_columns(df)
    if combined_text.empty:
        print("[filter_keyword] Kolom Judul/Ringkasan tidak tersedia.")
        empty_df = pd.DataFrame()
        clear_and_write(SHEET_KEY, FILTERED_SHEET_NAME, empty_df)
        return empty_df

    df["Teks_Gabungan"] = combined_text
    df["Teks_Bersih"] = df["Teks_Gabungan"].apply(normalize_text)

    df["Lolos_Keyword"] = df["Teks_Bersih"].apply(
        lambda x: contains_any_keyword(x, KEYWORDS_KETENAGAKERJAAN)
    )

    df["Relevan_Jamsos"] = df["Teks_Bersih"].apply(
        lambda x: contains_any_keyword(x, KEYWORDS_JAMSOS)
    )

    df["Keyword_Ketenagakerjaan"] = df["Teks_Bersih"].apply(
        lambda x: extract_detected_keywords(x, KEYWORDS_KETENAGAKERJAAN)
    )
    df["Keyword_Jamsos"] = df["Teks_Bersih"].apply(
        lambda x: extract_detected_keywords(x, KEYWORDS_JAMSOS)
    )

    filtered = df[df["Lolos_Keyword"]].copy()

    if filtered.empty:
        print("[filter_keyword] Tidak ada berita yang lolos keyword.")
        clear_and_write(SHEET_KEY, FILTERED_SHEET_NAME, filtered)
        return filtered

    filtered["Topik"] = filtered["Teks_Gabungan"].apply(detect_topic)

    filtered["Dampak_Program"] = filtered.apply(
        lambda row: detect_program_impact(row["Topik"], row["Teks_Gabungan"]),
        axis=1
    )
    filtered["Dampak_Kepesertaan"] = filtered.apply(
        lambda row: detect_kepesertaan_impact(row["Topik"], row["Teks_Gabungan"]),
        axis=1
    )
    filtered["Potensi_Klaim"] = filtered.apply(
        lambda row: detect_claim_impact(row["Topik"], row["Teks_Gabungan"]),
        axis=1
    )

    preferred_cols = [
        "Judul",
        "Ringkasan",
        "Link",
        "Media",
        "Tanggal",
        "Tanggal_Publish",
        "Waktu_Publish_WIB",
        "Tanggal_Ambil",
        "Lolos_Keyword",
        "Relevan_Jamsos",
        "Keyword_Ketenagakerjaan",
        "Keyword_Jamsos",
        "Topik",
        "Dampak_Program",
        "Dampak_Kepesertaan",
        "Potensi_Klaim",
        "Teks_Gabungan",
        "Teks_Bersih",
    ]

    existing_cols = [c for c in preferred_cols if c in filtered.columns]
    other_cols = [c for c in filtered.columns if c not in existing_cols]
    filtered = filtered[existing_cols + other_cols]

    clear_and_write(SHEET_KEY, FILTERED_SHEET_NAME, filtered)

    print(f"[filter_keyword] Total RAW       : {len(df)}")
    print(f"[filter_keyword] Lolos keyword   : {len(filtered)}")
    print(f"[filter_keyword] Disimpan ke     : {FILTERED_SHEET_NAME}")

    return filtered


if __name__ == "__main__":
    result = run_filter()
    print(result.head())