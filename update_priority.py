import pandas as pd
import re

from gsheet_utils import read_sheet, clear_and_write


SCORE_RULES = [
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
    (re.compile(r"\bketenagakerjaan\b|\btenaga kerja\b|\bburuh\b|\bpekerja\b|\bkaryawan\b"), 1),
]

TRIGGER_BERAT = re.compile(
    r"phk.*massal|massal.*phk|gelombang phk|pailit|bangkrut|likuidasi|tutup permanen|pabrik tutup"
)

RE_BIG_SCALE = re.compile(
    r"\b(ratusan|ribuan|puluhan ribu|belasan ribu)\b|"
    r"\b\d{1,3}(\.\d{3})+\b|"
    r"\b\d{4,}\b"
)

RE_CONTEXT_PEGAWAI = re.compile(r"\b(phk|pekerja|buruh|karyawan)\b")


def _normalize_text(df: pd.DataFrame) -> pd.Series:
    judul = df.get("Judul", "").astype(str).fillna("")
    ringkasan = df["Ringkasan"].astype(str).fillna("") if "Ringkasan" in df.columns else ""
    return (judul + " " + ringkasan).str.lower()


def _calculate_score(text: str) -> int:
    if not text:
        return 0

    matched = [nilai for pattern, nilai in SCORE_RULES if pattern.search(text)]
    base = max(matched) if matched else 0

    if len(matched) >= 2:
        base += 1
    if len(matched) >= 4:
        base += 1

    if RE_BIG_SCALE.search(text) and RE_CONTEXT_PEGAWAI.search(text):
        base += 3

    return min(base, 10)


def _classify(text: str, score: int) -> str:
    if score >= 7 or TRIGGER_BERAT.search(text or ""):
        return "PRIORITAS TINGGI"
    if score >= 4:
        return "PRIORITAS SEDANG"
    return "PRIORITAS RENDAH"


def run_priority(sheet_key: str | None = None):
    if not sheet_key:
        import streamlit as st
        sheet_key = st.secrets["SHEET_KEY"]

    df = read_sheet(sheet_key, "FILTERED")
    if df.empty:
        return df

    text_series = _normalize_text(df)

    df["Score"] = text_series.apply(_calculate_score)
    df["Prioritas"] = [_classify(t, s) for t, s in zip(text_series.tolist(), df["Score"].tolist())]

    tinggi = int((df["Prioritas"] == "PRIORITAS TINGGI").sum())
    sedang = int((df["Prioritas"] == "PRIORITAS SEDANG").sum())

    if tinggi >= 3:
        status = "SIAGA"
    elif tinggi >= 1 or sedang >= 5:
        status = "WASPADA"
    else:
        status = "STABIL"

    df["Status_EWS"] = status

    clear_and_write(sheet_key, "FILTERED", df)
    return df


if __name__ == "__main__":
    run_priority()