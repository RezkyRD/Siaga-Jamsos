import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime

URL = "https://news.google.com/search?q=ketenagakerjaan&hl=id&gl=ID&ceid=ID:id"

headers = {
    "User-Agent": "Mozilla/5.0"
}

response = requests.get(URL, headers=headers)

soup = BeautifulSoup(response.text, "lxml")

articles = soup.find_all("article")

data = []

for article in articles:
    try:
        title = article.get_text()
        data.append({
            "judul": title,
            "isi": title,
            "tanggal": datetime.now(),
            "media": "Google News"
        })
    except:
        continue

df = pd.DataFrame(data)
df.to_csv("raw_news.csv", index=False)

print("Scraping selesai.")