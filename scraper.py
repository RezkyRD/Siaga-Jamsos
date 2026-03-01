import feedparser
import pandas as pd
from datetime import datetime
import os

rss_sources = {
    "CNN": "https://www.cnnindonesia.com/nasional/rss",
    "Tribunnews": "https://www.tribunnews.com//rss",
    "CNBCIndonesia": "https://www.cnbcindonesia.com/rss",
    "SindoNews": "https://nasional.sindonews.com/rss",
    "Hariankepri": "https://www.hariankepri.com/feed/"
}

all_news = []

today = datetime.today().date()

for media, url in rss_sources.items():
    feed = feedparser.parse(url)

    for entry in feed.entries:
        all_news.append({
            "Media": media,
            "Judul": entry.title,
            "Tanggal": entry.get("published", ""),
            "Link": entry.link,
            "Ringkasan": entry.get("summary", ""),
            "Tanggal_Ambil": today
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