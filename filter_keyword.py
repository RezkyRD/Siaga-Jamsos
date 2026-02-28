import pandas as pd

KEYWORDS = [
    "phk",
    "bpjs",
    "demo",
    "mogok",
    "upah",
    "jaminan sosial"
]

df = pd.read_csv("raw_news.csv")

total_raw = len(df)

def contains_keyword(text):
    text = str(text).lower()
    for k in KEYWORDS:
        if k in text:
            return True
    return False

df_filtered = df[df["title"].apply(contains_keyword)]

total_filtered = len(df_filtered)

df_filtered.to_csv("filtered_news.csv", index=False)

print("Total berita raw:", total_raw)
print("Total lolos keyword:", total_filtered)