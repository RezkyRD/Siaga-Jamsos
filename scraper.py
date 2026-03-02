import feedparser
import pandas as pd
from datetime import datetime
import os
import re


def clean_html(text):
    if not text:
        return ""
    text = re.sub('<.*?>', '', text)
    text = text.replace("\n", " ").strip()
    return text


def run_scraper():

    rss_sources = {
        "CNN": "https://www.cnnindonesia.com/nasional/rss",
        "Tribunnews": "https://www.tribunnews.com/rss",
        "CNBCIndonesia": "https://www.cnbcindonesia.com/rss",
        "SindoNews": "https://nasional.sindonews.com/rss",
        "Hariankepri": "https://www.hariankepri.com/feed/"
    }

    all_news = []
    today = datetime.utcnow().date()

    for media, url in rss_sources.items():
        feed = feedparser.parse(url)

        for entry in feed.entries:

            published = entry.get("published_parsed")

            if published:
                tanggal_rss = datetime(*published[:6]).date()
            else:
                tanggal_rss = today

            judul = clean_html(entry.get("title", ""))
            ringkasan = clean_html(entry.get("summary", ""))

            all_news.append({
                "Media": media,
                "Judul": judul,
                "Tanggal": entry.get("published", ""),
                "Link": entry.get("link", ""),
                "Ringkasan": ringkasan,
                "Tanggal_Ambil": tanggal_rss
            })

    df = pd.DataFrame(all_news)
    file_name = "raw_news.csv"

    if os.path.exists(file_name):
        old_data = pd.read_csv(file_name)
        combined = pd.concat([old_data, df], ignore_index=True)
        combined = combined.drop_duplicates(subset=["Link"])
    else:
        combined = df

    combined.to_csv(file_name, index=False)
    print("Scraping selesai. Data ditambahkan ke raw_news.csv")


if __name__ == "__main__":
    run_scraper()