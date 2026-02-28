import pandas as pd

df = pd.read_csv("filtered_news.csv")

def classify(text):
    text = str(text).lower()

    if "phk massal" in text or "ribuan pekerja" in text:
        return "PRIORITAS TINGGI"
    elif "demo" in text or "mogok" in text:
        return "PRIORITAS SEDANG"
    else:
        return "PRIORITAS RENDAH"

df["prioritas"] = df["title"].apply(classify)

df.to_csv("prioritized_news.csv", index=False)

print("Klasifikasi selesai.")