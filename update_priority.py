import pandas as pd
import re
import streamlit as st
from gsheet_utils import read_sheet, clear_and_write


def run_priority():
    print("Update prioritas dimulai...")

    SHEET_KEY = st.secrets["SHEET_KEY"]

    # ==============================
    # BACA DATA DARI GOOGLE SHEET (FILTERED)
    # ==============================
    df = read_sheet(SHEET_KEY, "FILTERED")

    if df.empty:
        print("Sheet FILTERED kosong.")
        return

    # ==============================
    # GABUNGKAN JUDUL + RINGKASAN
    # ==============================
    judul = df.get("Judul", "").astype(str).fillna("")
    ringkasan = df["Ringkasan"].astype(str).fillna("") if "Ringkasan" in df.columns else ""
    text_series = (judul + " " + ringkasan).str.lower()

    # ==============================
    # REGEX / KEYWORD (COMPILED)
    # ==============================
    score_map = [
        # --- TRIGGER BERAT (biasanya langsung TINGGI) ---
        (re.compile(r"\bphk\b.*\bmassal\b|\bmassal\b.*\bphk\b"), 6),
        (re.compile(r"\bgelombang\b.*\bphk\b|\bphk\b.*\bgelombang\b"), 6),
        (re.compile(r"\bpabrik\b.*\btutup\b|\btutup\b.*\bpabrik\b|\btutup permanen\b"), 6),
        (re.compile(r"\bbangkrut\b|\bpailit\b|\blikuidasi\b"), 6),
        (re.compile(r"\bkerusuhan\b|\bbentrok\b|\bricuh\b"), 5),
        (re.compile(r"\bblokade\b|\baksi besar\b|\bancam tutup\b"), 5),

        # --- ESKALASI MENENGAH ---
        (re.compile(r"\bdirumahkan\b|\blayoff\b|\bpemutusan hubungan kerja\b"), 4),
        (re.compile(r"\bmogok\b|\bmogok kerja\b"), 3),
        (re.compile(r"\bunjuk rasa\b|\bdemo\b|\baksi buruh\b"), 3),
        (re.compile(r"\bupah\b.*\btidak dibayar\b|\bgaji\b.*\btidak dibayar\b|\btunggakan upah\b"), 3),
        (re.compile(r"\bpengurangan karyawan\b|\befisiensi\b|\brestrukturisasi\b"), 2),
        (re.compile(r"\bperselisihan\b|\bkonflik buruh\b|\bsengketa\b"), 2),
        (re.compile(r"\bpenutupan sementara\b|\bstop operasional\b"), 2),

        # --- UMUM (LOW SIGNAL) ---
        (re.compile(r"\bphk\b"), 1),
        (re.compile(r"\bketenagakerjaan\b|\btenaga kerja\b|\bburuh\b|\bpekerja\b"), 1),
    ]

    # Deteksi skala jumlah (ratusan/ribuan/angka)
    # Skor tambahan jika ada indikasi dampak besar
    re_big_scale = re.compile(
        r"\b(ratusan|ribuan|puluhan ribu|belasan ribu)\b|"
        r"\b\d{1,3}(\.\d{3})+\b|"         # 1.000 / 10.000
        r"\b\d{4,}\b"                     # 1200 / 10000
    )

    def calculate_score(text: str) -> int:
        if not text:
            return 0
        score = 0
        for pattern, nilai in score_map:
            if pattern.search(text):
                score += nilai

        # Bonus dampak bila ada skala besar + konteks pekerja/PHK
        if re_big_scale.search(text) and re.search(r"\b(phk|pekerja|buruh|karyawan)\b", text):
            score += 3

        return score

    df["Score"] = text_series.apply(calculate_score)

    # ==============================
    # PRIORITAS LEBIH REALISTIS
    # - TINGGI: score >= 7 ATAU ada trigger berat
    # - SEDANG: score >= 4
    # - RENDAH: sisanya
    # ==============================
    trigger_berat = re.compile(r"phk.*massal|massal.*phk|gelombang phk|pailit|bangkrut|likuidasi|tutup permanen|pabrik tutup")

    def classify_priority(text: str, score: int) -> str:
        if score >= 7 or trigger_berat.search(text or ""):
            return "PRIORITAS TINGGI"
        elif score >= 4:
            return "PRIORITAS SEDANG"
        else:
            return "PRIORITAS RENDAH"

    df["Prioritas"] = [
        classify_priority(t, s) for t, s in zip(text_series.tolist(), df["Score"].tolist())
    ]

    # ==============================
    # STATUS EWS (GLOBAL) - ringan untuk internal monitoring
    # ==============================
    tinggi = int((df["Prioritas"] == "PRIORITAS TINGGI").sum())
    sedang = int((df["Prioritas"] == "PRIORITAS SEDANG").sum())

    # Rule sederhana tapi lebih masuk akal
    if tinggi >= 3:
        status = "SIAGA"
    elif tinggi >= 1 or sedang >= 5:
        status = "WASPADA"
    else:
        status = "STABIL"

    df["Status_EWS"] = status

    # ==============================
    # SIMPAN KEMBALI KE SHEET FILTERED
    # ==============================
    clear_and_write(SHEET_KEY, "FILTERED", df)

    print("Prioritas berhasil diperbarui.")
    print("Status:", status, "| Tinggi:", tinggi, "| Sedang:", sedang)


if __name__ == "__main__":
    run_priority()