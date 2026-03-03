import feedparser
import pandas as pd
import re

from gsheet_utils import read_sheet, clear_and_write


def clean_html(text: str) -> str:
    if not text:
        return ""
    text = re.sub("<.*?>", "", text)
    return text.replace("\n", " ").strip()


def _parse_entry_time(entry) -> pd.Timestamp:
    if entry.get("published_parsed"):
        return pd.to_datetime(entry.published_parsed, utc=True, errors="coerce")
    if entry.get("updated_parsed"):
        return pd.to_datetime(entry.updated_parsed, utc=True, errors="coerce")

    published_str = entry.get("published") or entry.get("updated") or ""
    return pd.to_datetime(published_str, utc=True, errors="coerce")


def run_scraper(sheet_key: str | None = None) -> pd.DataFrame:
    if not sheet_key:
        import streamlit as st
        sheet_key = st.secrets["SHEET_KEY"]

    rss_sources = {
        "CNN": "https://www.cnnindonesia.com/nasional/rss",
        "Tribunnews": "https://www.tribunnews.com/rss",
        "CNBCIndonesia": "https://www.cnbcindonesia.com/rss",
        "SindoNews": "https://nasional.sindonews.com/rss",
        "Hariankepri": "https://www.hariankepri.com/feed/",
    }

    now_utc = pd.Timestamp.utcnow().tz_localize("UTC")
    now_wib = now_utc.tz_convert("Asia/Jakarta")

    all_news = []

    for media, url in rss_sources.items():
        feed = feedparser.parse(url)

        for entry in feed.entries:
            ts_utc = _parse_entry_time(entry)

            if pd.notna(ts_utc):
                publish_wib = ts_utc.tz_convert("Asia/Jakarta")
                waktu_publish_wib = publish_wib.strftime("%Y-%m-%d %H:%M:%S")
                tanggal_publish = publish_wib.strftime("%Y-%m-%d")
            else:
                waktu_publish_wib = ""
                tanggal_publish = ""

            judul = clean_html(entry.get("title", ""))
            ringkasan = clean_html(entry.get("summary", ""))

            all_news.append(
                {
                    "Media": media,
                    "Judul": judul,
                    "Tanggal": entry.get("published") or entry.get("updated") or "",
                    "Link": (entry.get("link", "") or "").strip(),
                    "Ringkasan": ringkasan,
                    "Waktu_Publish_WIB": waktu_publish_wib,
                    "Tanggal_Publish": tanggal_publish,
                    "Waktu_Ambil_UTC": now_utc.isoformat(),
                    "Waktu_Ambil_WIB": now_wib.strftime("%Y-%m-%d %H:%M:%S"),
                    "Tanggal_Ambil": now_wib.strftime("%Y-%m-%d"),
                }
            )

    df_new = pd.DataFrame(all_news)

    try:
        df_old = read_sheet(sheet_key, "RAW")
    except Exception:
        df_old = pd.DataFrame()

    combined = pd.concat([df_old, df_new], ignore_index=True) if not df_old.empty else df_new

    if "Link" in combined.columns:
        combined["Link"] = combined["Link"].astype(str).str.strip()
        combined = combined[combined["Link"] != ""]
        combined = combined.drop_duplicates(subset=["Link"], keep="last")
    else:
        for col in ["Judul", "Tanggal_Publish"]:
            if col not in combined.columns:
                combined[col] = ""
        combined = combined.drop_duplicates(subset=["Judul", "Tanggal_Publish"], keep="last")

    clear_and_write(sheet_key, "RAW", combined)
    return combined


if __name__ == "__main__":
    run_scraper()