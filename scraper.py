import feedparser
import pandas as pd
from datetime import datetime
import re
import streamlit as st

from gsheet_utils import read_sheet, clear_and_write


def clean_html(text):
    if not text:
        return ""
    text = re.sub("<.*?>", "", text)
    text = text.replace("\n", " ").strip()
    return text


def run_scraper():
    SHEET_KEY = st.secrets["1usVNpV9PWDQzh9p_ix0hHY4lvlG02mKcEZAyiimooMs"]

    rss_sources = {
        "CNN": "https://www.cnnindonesia.com/nasional/rss",
        "Tribunnews": "https://www.tribunnews.com/rss",
        "CNBCIndonesia": "https://www.cnbcindonesia.com/rss",
        "SindoNews": "https://nasional.sindonews.com/rss",
        "Hariankepri": "https://www.hariankepri.com/feed/",
    }

    all_news = []

    for media, url in rss_sources.items():
        feed = feedparser.parse(url)

        for entry in feed.entries:
            published_str = entry.get("published") or entry.get("updated") or ""
            ts = pd.to_datetime(published_str, errors="coerce", utc=True)

            if pd.notna(ts):
                publish_wib = ts.tz_convert("Asia/Jakarta")
                tanggal_publish = publish_wib.date()
            else:
                publish_wib = pd.NaT
                tanggal_publish = pd.NaT

            judul = clean_html(entry.get("title", ""))
            ringkasan = clean_html(entry.get("summary", ""))

            all_news.append(
                {
                    "Media": media,
                    "Judul": judul,
                    "Tanggal": published_str,
                    "Link": entry.get("link", ""),
                    "Ringkasan": ringkasan,
                    "Waktu_Publish_WIB": str(publish_wib) if pd.notna(publish_wib) else "",
                    "Tanggal_Publish": str(tanggal_publish) if pd.notna(tanggal_publish) else "",
                    "Waktu_Ambil_UTC": datetime.utcnow().isoformat(),
                }
            )

    df_new = pd.DataFrame(all_news)

    # baca data lama di sheet RAW (kalau ada)
    try:
        df_old = read_sheet(SHEET_KEY, "RAW")
    except Exception:
        df_old = pd.DataFrame()

    # gabung + dedup by Link
    if not df_old.empty:
        combined = pd.concat([df_old, df_new], ignore_index=True)
    else:
        combined = df_new

    if "Link" in combined.columns:
        combined = combined.drop_duplicates(subset=["Link"])

    # tulis ulang sheet RAW (lebih stabil daripada append banyak baris)
    clear_and_write(SHEET_KEY, "RAW", combined)

    print("Scraping selesai. Data disimpan ke Google Sheets (RAW).")


if __name__ == "__main__":
    run_scraper()