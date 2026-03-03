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


def run_scraper(sheet_key=None):
    # kalau dipanggil dari app.py pakai SHEET_KEY, gunakan itu
    # kalau tidak, ambil dari secrets
    if sheet_key is None:
        SHEET_KEY = st.secrets["SHEET_KEY"]
    else:
        SHEET_KEY = sheet_key

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
    combined = pd.concat([df_old, df_new], ignore_index=True) if not df_old.empty else df_new
    if "Link" in combined.columns:
        combined = combined.drop_duplicates(subset=["Link"])

    # tulis ulang sheet RAW
    clear_and_write(SHEET_KEY, "RAW", combined)
    print("Scraping selesai. Data disimpan ke Google Sheets (RAW).")
    return combined


if __name__ == "__main__":
    run_scraper()