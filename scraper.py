import feedparser
import pandas as pd
from datetime import datetime
import re
import streamlit as st

from gsheet_utils import read_sheet, replace_sheet, append_rows, backup_sheet


def clean_html(text: str) -> str:
    if not text:
        return ""
    text = re.sub("<.*?>", "", str(text))
    return text.replace("\n", " ").strip()


def norm_title(s: str) -> str:
    s = (s or "").lower()
    s = re.sub(r"\s+", " ", s).strip()
    s = re.sub(
        r"\s*[-|]\s*(kompas\.com|detikcom|cnn indonesia|tribunnews\.com|cnbc indonesia|sindonews)\s*$",
        "",
        s
    )
    return s


def make_uid(row) -> str:
    media = (row.get("Media", "") or "").strip().lower()
    judul = norm_title(row.get("Judul", ""))

    waktu = (row.get("Waktu_Publish_WIB", "") or "").strip()
    tgl = (row.get("Tanggal_Publish", "") or "").strip()
    key_time = waktu or tgl or (row.get("Tanggal_Ambil", "") or "").strip()

    return f"{media}|{judul}|{key_time}"


def google_news_url(query: str) -> str:
    q = query.replace(" ", "+")
    return f"https://news.google.com/rss/search?q={q}&hl=id&gl=ID&ceid=ID:id"


def build_sources() -> dict:
    return {
        # RSS media utama
        "CNN": "https://www.cnnindonesia.com/nasional/rss",
        "Tribunnews": "https://www.tribunnews.com/rss",
        "CNBCIndonesia": "https://www.cnbcindonesia.com/rss",
        "SindoNews": "https://nasional.sindonews.com/rss",
        "Hariankepri": "https://www.hariankepri.com/feed/",

        # Google News per topik
        "GoogleNews-PHK": google_news_url('PHK OR "pemutusan hubungan kerja" OR dirumahkan OR pesangon OR "tutup pabrik"'),
        "GoogleNews-Buruh": google_news_url('buruh OR pekerja OR "tenaga kerja" OR "hubungan industrial"'),
        "GoogleNews-BPJS": google_news_url('"BPJS Ketenagakerjaan" OR BPJAMSOSTEK OR jamsostek OR kepesertaan'),
        "GoogleNews-Program": google_news_url('JHT OR JKP OR JKK OR JKM OR JP OR "jaminan hari tua" OR "jaminan kehilangan pekerjaan"'),
        "GoogleNews-Upah": google_news_url('upah OR gaji OR UMP OR UMK OR "upah minimum"'),
        "GoogleNews-THR": google_news_url('THR OR "tunjangan hari raya" OR "pengaduan THR"'),
        "GoogleNews-Kecelakaan": google_news_url('"kecelakaan kerja" OR "buruh tewas" OR "pekerja tewas" OR "ledakan pabrik"'),
        "GoogleNews-Aksi": google_news_url('"demo buruh" OR "aksi buruh" OR "mogok kerja" OR "unjuk rasa buruh"'),
        "GoogleNews-PMI": google_news_url('"pekerja migran indonesia" OR PMI OR TKI'),
        "GoogleNews-Konstruksi": google_news_url('konstruksi OR proyek OR "jasa konstruksi" OR "pekerja proyek"'),
        "GoogleNews-BPU": google_news_url('UMKM OR "pekerja informal" OR BPU OR nelayan OR petani OR driver'),
    }


def dedup_news(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or df.empty:
        return pd.DataFrame()

    df = df.copy()

    if "UID" not in df.columns:
        df["UID"] = df.apply(make_uid, axis=1)

    df = df.drop_duplicates(subset=["UID"], keep="last")

    if "Link" in df.columns:
        df["Link"] = df["Link"].astype(str).str.strip()

        df_blank = df[df["Link"] == ""].copy()
        df_link = df[df["Link"] != ""].copy()

        if not df_link.empty:
            df_link = df_link.drop_duplicates(subset=["Link"], keep="last")

        df = pd.concat([df_link, df_blank], ignore_index=True)

    return df


def run_scraper(sheet_key=None, *args, **kwargs):
    if sheet_key is None:
        sheet_key = st.secrets["SHEET_KEY"]

    rss_sources = build_sources()

    now_utc = pd.Timestamp.now(tz="UTC")
    now_wib = now_utc.tz_convert("Asia/Jakarta")

    all_news = []

    for media, url in rss_sources.items():
        try:
            feed = feedparser.parse(url)
        except Exception:
            continue

        for entry in getattr(feed, "entries", []):
            published_str = entry.get("published") or entry.get("updated") or ""
            ts = pd.to_datetime(published_str, errors="coerce", utc=True)

            if pd.notna(ts):
                publish_wib = ts.tz_convert("Asia/Jakarta")
                waktu_publish_wib = publish_wib.strftime("%Y-%m-%d %H:%M:%S")
                tanggal_publish = publish_wib.strftime("%Y-%m-%d")
            else:
                waktu_publish_wib = ""
                tanggal_publish = ""

            all_news.append(
                {
                    "Media": media,
                    "Judul": clean_html(entry.get("title", "")),
                    "Tanggal": published_str,
                    "Link": (entry.get("link", "") or "").strip(),
                    "Ringkasan": clean_html(entry.get("summary", "")),
                    "Waktu_Publish_WIB": waktu_publish_wib,
                    "Tanggal_Publish": tanggal_publish,
                    "Waktu_Ambil_UTC": datetime.utcnow().isoformat(),
                    "Waktu_Ambil_WIB": now_wib.strftime("%Y-%m-%d %H:%M:%S"),
                    "Tanggal_Ambil": now_wib.strftime("%Y-%m-%d"),
                }
            )

    df_new = pd.DataFrame(all_news)

    if not df_new.empty:
        df_new["UID"] = df_new.apply(make_uid, axis=1)
        df_new = dedup_news(df_new)

    try:
        df_old = read_sheet(sheet_key, "RAW")
    except Exception:
        df_old = pd.DataFrame()

    # backup RAW lama
    try:
        backup_sheet(sheet_key, "RAW", "RAW_BACKUP")
    except Exception:
        pass

    # simpan log harian hasil scrape baru
    try:
        if df_new is not None and not df_new.empty:
            append_rows(sheet_key, "RAW_LOG_HARIAN", df_new)
    except Exception:
        pass

    # kalau scrape baru kosong, jangan timpa RAW lama
    if (df_new is None or df_new.empty) and (df_old is not None and not df_old.empty):
        return df_old

    combined = pd.concat([df_old, df_new], ignore_index=True) if not df_old.empty else df_new
    combined = dedup_news(combined)

    # guard tambahan: kalau hasil akhir turun terlalu jauh, pakai RAW lama
    if not df_old.empty and len(combined) < max(20, int(len(df_old) * 0.30)):
        return df_old

    replace_sheet(sheet_key, "RAW", combined)
    return combined


if __name__ == "__main__":
    run_scraper()