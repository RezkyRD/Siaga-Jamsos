import re
import pandas as pd
import streamlit as st

from gsheet_utils import read_sheet, clear_and_write


KEYWORD_PATTERNS = [
    # PHK / hubungan kerja
    r"\bphk\b",
    r"pemutusan hubungan kerja",
    r"\bdirumahkan\b",
    r"phk massal",
    r"gelombang phk",
    r"pengurangan karyawan",
    r"efisiensi tenaga kerja",
    r"pesangon",

    # THR / kesejahteraan
    r"\bthr\b",
    r"tunjangan hari raya",
    r"pengaduan thr",
    r"posko thr",
    r"thr.*tidak dibayar",
    r"thr.*terlambat",
    r"thr.*dicicil",
    r"thr.*dipotong",

    # upah / gaji
    r"\bupah\b",
    r"\bgaji\b",
    r"\bump\b",
    r"\bumk\b",
    r"upah minimum",
    r"tunggakan upah",
    r"gaji tidak dibayar",

    # buruh / pekerja / industrial
    r"\bburuh\b",
    r"\bpekerja\b",
    r"tenaga kerja",
    r"hubungan industrial",
    r"perselisihan industrial",
    r"konflik buruh",
    r"sengketa industrial",
    r"mediasi hubungan industrial",
    r"tripartit",

    # aksi buruh
    r"demo buruh",
    r"aksi buruh",
    r"\bdemo\b",
    r"unjuk rasa",
    r"mogok",
    r"mogok kerja",

    # BPJS Ketenagakerjaan / program
    r"bpjs ketenagakerjaan",
    r"bpjamsostek",
    r"\bjht\b",
    r"jaminan hari tua",
    r"\bjkp\b",
    r"jaminan kehilangan pekerjaan",
    r"\bjkk\b",
    r"jaminan kecelakaan kerja",
    r"\bjkm\b",
    r"jaminan kematian",
    r"\bjp\b",
    r"jaminan pensiun",
    r"klaim jht",
    r"klaim jkp",
    r"pencairan jht",
    r"saldo jht",
    r"iuran bpjs",
    r"tunggakan iuran",
    r"denda bpjs",
    r"kepesertaan bpjs",
    r"peserta bpjs",
    r"terdaftar bpjs",

    # edukasi layanan / JMO
    r"cara klaim",
    r"syarat klaim",
    r"panduan",
    r"tutorial",
    r"cara mencairkan",
    r"cara cairkan",
    r"alur klaim",
    r"prosedur klaim",
    r"tips klaim",
    r"\bjmo\b",
    r"aplikasi jmo",

    # kecelakaan kerja / fatalitas
    r"kecelakaan kerja",
    r"ledakan pabrik",
    r"kebakaran pabrik",
    r"pekerja jatuh",
    r"buruh tewas",
    r"pekerja tewas",
    r"korban jiwa",

    # sektor / kepesertaan khusus
    r"\bpmi\b",
    r"pekerja migran",
    r"\btki\b",
    r"buruh migran",
    r"jasa konstruksi",
    r"konstruksi",
    r"proyek",
]


def clean_text(text: str) -> str:
    text = str(text or "").lower()
    text = re.sub(r"\s+", " ", text).strip()
    return text


def contains_keyword(row) -> bool:
    judul = clean_text(row.get("Judul", ""))
    ringkasan = clean_text(row.get("Ringkasan", ""))
    text = f"{judul} {ringkasan}"
    return any(re.search(pattern, text) for pattern in KEYWORD_PATTERNS)


def run_filter(sheet_key=None):
    if sheet_key is None:
        sheet_key = st.secrets["SHEET_KEY"]

    df = read_sheet(sheet_key, "RAW")

    if df is None or df.empty:
        print("Sheet RAW kosong.")
        return pd.DataFrame()

    df = df.copy()
    df.columns = df.columns.astype(str).str.strip()

    df_filtered = df[df.apply(contains_keyword, axis=1)].copy()

    if "UID" in df_filtered.columns:
        df_filtered = df_filtered.drop_duplicates(subset=["UID"], keep="last")

    if "Link" in df_filtered.columns:
        df_filtered["Link"] = df_filtered["Link"].astype(str).str.strip()
        df_filtered = df_filtered.drop_duplicates(subset=["Link"], keep="last")

    clear_and_write(sheet_key, "FILTERED_AWAL", df_filtered)

    print("Total RAW:", len(df))
    print("Total Lolos Keyword:", len(df_filtered))

    return df_filtered


if __name__ == "__main__":
    run_filter()