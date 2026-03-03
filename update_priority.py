import pandas as pd
import re
import streamlit as st

from gsheet_utils import read_sheet, clear_and_write


def run_priority(sheet_key=None, *args, **kwargs):
    if sheet_key is None:
        sheet_key = st.secrets["SHEET_KEY"]

    df = read_sheet(sheet_key, "FILTERED")

    if df is None or df.empty:
        return

    judul = df.get("Judul", "").astype(str).fillna("")
    ringkasan = df.get("Ringkasan", "").astype(str).fillna("")
    text_series = (judul + " " + ringkasan).str.lower()

    score_map = [
        (re.compile(r"\bphk\b.*\bmassal\b|\bmassal\b.*\bphk\b"), 6),
        (re.compile(r"\bgelombang\b.*\bphk\b|\bphk\b.*\bgelombang\b"), 6),
        (re.compile(r"\bpabrik\b.*\btutup\b|\btutup\b.*\bpabrik\b|\btutup permanen\b"), 6),
        (re.compile(r"\bbangkrut\b|\bpailit\b|\blikuidasi\b"), 6),
        (re.compile(r"\bkerusuhan\b|\bbentrok\b|\bricuh\b"), 5),
        (re.compile(r"\bblokade\b|\baksi besar\b|\bancam tutup\b"), 5),
        (re.compile(r"\bdirumahkan\b|\blayoff\b|\bpemutusan hubungan kerja\b"), 4),
        (re.compile(r"\bmogok\b|\bmogok kerja\b"), 3),
        (re.compile(r"\bunjuk rasa\b|\bdemo\b|\baksi buruh\b"), 3),
        (re.compile(r"\bupah\b.*\btidak dibayar\b|\bgaji\b.*\btidak dibayar\b|\btunggakan upah\b"), 3),
        (re.compile(r"\bpengurangan karyawan\b|\befisiensi\b|\brestrukturisasi\b"), 2),
        (re.compile(r"\bperselisihan\b|\bkonflik buruh\b|\bsengketa\b"), 2),
        (re.compile(r"\bpenutupan sementara\b|\bstop operasional\b"), 2),
        (re.compile(r"\bphk\b"), 1),
        (re.compile(r"\bketenagakerjaan\b|\btenaga kerja\b|\bburuh\b|\bpekerja\b"), 1),
    ]

    re_big_scale = re.compile(
        r"\b(ratusan|ribuan|puluhan ribu|belasan ribu)\b|"
        r"\b\d{1,3}(\.\d{3})+\b|"
        r"\b\d{4,}\b"
    )

    def calculate_score(text):
        score = 0
        for pattern, nilai in score_map:
            if pattern.search(text):
                score += nilai
        if re_big_scale.search(text) and re.search(r"\b(phk|pekerja|buruh|karyawan)\b", text):
            score += 3
        return score

    df["Score"] = text_series.apply(calculate_score)

    trigger_berat = re.compile(
        r"phk.*massal|massal.*phk|gelombang phk|pailit|bangkrut|likuidasi|tutup permanen|pabrik tutup"
    )

    def classify_priority(text, score):
        if score >= 7 or trigger_berat.search(text):
            return "PRIORITAS TINGGI"
        elif score >= 4:
            return "PRIORITAS SEDANG"
        else:
            return "PRIORITAS RENDAH"

    df["Prioritas"] = [
        classify_priority(t, s)
        for t, s in zip(text_series.tolist(), df["Score"].tolist())
    ]

    clear_and_write(sheet_key, "FILTERED", df)
    return df


if __name__ == "__main__":
    run_priority()