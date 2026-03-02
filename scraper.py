import feedparser
import pandas as pd
from datetime import datetime
import pytz
import os

def run_scraper():

    rss_sources = {
        "CNN": "https://www.cnnindonesia.com/nasional/rss",
        "Tribunnews": "https://www.tribunnews.com//rss",
        "CNBCIndonesia": "https://www.cnbcindonesia.com/rss",
        "SindoNews": "https://nasional.sindonews.com/rss",
        "Hariankepri": "https://www.hariankepri.com/feed/"
    }

    all_news = []

    wib = pytz.timezone("Asia/Jakarta")
    today = datetime.now(wib).date()

    for media, url in rss_sources.items():
        feed = feedparser.parse(url)

        for entry in feed.entries:

    # 👇 AMBIL TANGGAL DARI RSS
    tanggal_rss = entry.get("published_parsed")

    if tanggal_rss:
        tanggal_rss = datetime(*tanggal_rss[:6]).date()
    else:
        tanggal_rss = today

    all_news.append({
        "Media": media,
        "Judul": entry.title,
        "Tanggal": entry.get("published", ""),
        "Link": entry.link,
        "Ringkasan": entry.get("summary", ""),
        "Tanggal_Ambil": tanggal_rss
    })

    df = pd.DataFrame(all_news)

    file_name = "raw_news.csv"

# ===============================
# APPEND MODE (TIDAK HAPUS DATA LAMA)
# ===============================
    if os.path.exists(file_name):
        old_data = pd.read_csv(file_name)

    # Gabungkan lama + baru
        combined = pd.concat([old_data, df], ignore_index=True)

    # Optional: hapus duplikat berdasarkan Link
        combined = combined.drop_duplicates(subset=["Link"])

    else:
        combined = df

    combined.to_csv(file_name, index=False)

    print("Scraping selesai. Data ditambahkan ke raw_news.csv")

if __name__ == "__main__":
        run_scraper()