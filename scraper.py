import feedparser
import pandas as pd
from datetime import datetime
import re
import streamlit as st

from gsheet_utils import read_sheet, clear_and_write


def clean_html(text: str) -> str:
    if not text:
        return ""
    text = re.sub("<.*?>", "", str(text))
    return text.replace("\n", " ").strip()


# ====== Tambahan: Normalisasi judul + UID untuk dedup lintas sumber ======
def norm_title(s: str) -> str:
    s = (s or "").lower()
    s = re.sub(r"\s+", " ", s).strip()
    # buang embel-embel sumber di akhir judul (optional tapi membantu)
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

    # pakai waktu publish kalau ada, kalau tidak pakai tanggal publish, kalau tidak pakai tanggal ambil
    key_time = waktu or tgl or (row.get("Tanggal_Ambil", "") or "").strip()

    return f"{media}|{judul}|{key_time}"


def run_scraper(sheet_key=None, *args, **kwargs):
    # kebal: bisa dipanggil run_scraper() atau run_scraper(SHEET_KEY)
    if sheet_key is None:
        sheet_key = st.secrets["SHEET_KEY"]

    rss_sources = {
        "CNN": "https://www.cnnindonesia.com/nasional/rss",
        "Tribunnews": "https://www.tribunnews.com/rss",
        "CNBCIndonesia": "https://www.cnbcindonesia.com/rss",
        "SindoNews": "https://nasional.sindonews.com/rss",
        "Hariankepri": "https://www.hariankepri.com/feed/",
        "GoogleNews-Ketenagakerjaan": "https://news.google.com/rss/search?q=PHK+OR+buruh+OR+ketenagakerjaan+OR+upah+OR+UMK+OR+UMP+OR+JKP+OR+%22BPJS+Ketenagakerjaan%22+OR+%22demo+buruh%22+OR+%22mogok+kerja%22+OR+outsourcing+OR+pesangon+OR+%22tutup+pabrik%22&hl=id&gl=ID&ceid=ID:id",
    }

    now_utc = pd.Timestamp.now(tz="UTC")
    now_wib = now_utc.tz_convert("Asia/Jakarta")

    all_news = []

    for media, url in rss_sources.items():
        feed = feedparser.parse(url)

        for entry in feed.entries:
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

    # ===== UID untuk dedup lintas sumber (Google News vs RSS asli) =====
    if not df_new.empty:
        df_new["UID"] = df_new.apply(make_uid, axis=1)

    # ===== baca RAW lama =====
    try:
        df_old = read_sheet(sheet_key, "RAW")
    except Exception:
        df_old = pd.DataFrame()

    # ===== gabung lama + baru =====
    combined = pd.concat([df_old, df_new], ignore_index=True) if not df_old.empty else df_new

    # ===== pastikan UID ada juga untuk data lama, lalu dedup utama pakai UID =====
    if not combined.empty:
        if "UID" not in combined.columns:
            combined["UID"] = combined.apply(make_uid, axis=1)
        combined = combined.drop_duplicates(subset=["UID"], keep="last")

    # ===== dedup cadangan pakai Link (kalau ada) =====
    if "Link" in combined.columns:
        combined["Link"] = combined["Link"].astype(str).str.strip()
        combined = combined[combined["Link"] != ""]
        combined = combined.drop_duplicates(subset=["Link"], keep="last")

    # ===== tulis balik ke RAW =====
    clear_and_write(sheet_key, "RAW", combined)
    return combined


if __name__ == "__main__":
    run_scraper()