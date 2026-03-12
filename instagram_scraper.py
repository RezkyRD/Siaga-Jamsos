import os
import re
from html import unescape
from typing import List, Dict, Optional

import pandas as pd
import requests


ACCESS_TOKEN = os.getenv("IG_ACCESS_TOKEN", "")
IG_USER_ID = os.getenv("IG_USER_ID", "")  # akun profesional milik app user
GRAPH_VERSION = "v23.0"
BASE_URL = f"https://graph.facebook.com/{GRAPH_VERSION}"

TIMEZONE = "Asia/Jakarta"

INSTAGRAM_HASHTAGS = [
    "phk",
    "buruh",
    "bpjsketenagakerjaan",
    "jht",
    "jkk",
    "jkp",
    "pesangon",
    "kecelakaankerja",
]

WATCHED_ACCOUNTS = [
    # username akun profesional yang relevan
    # contoh: "kemnaker", "bpjsketenagakerjaan"
]


def _now_wib_str() -> str:
    return pd.Timestamp.now(tz="UTC").tz_convert(TIMEZONE).strftime("%Y-%m-%d %H:%M:%S")


def _to_wib_string(value: Optional[str]) -> str:
    if not value:
        return _now_wib_str()
    try:
        ts = pd.to_datetime(value, errors="coerce", utc=True)
        if pd.isna(ts):
            return _now_wib_str()
        return ts.tz_convert(TIMEZONE).strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        return _now_wib_str()


def clean_text(text: str) -> str:
    if text is None:
        return ""
    text = unescape(str(text))
    text = re.sub(r"http\S+|www\.\S+", " ", text)
    text = re.sub(r"[\r\n\t]+", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def safe_int(value, default=0) -> int:
    try:
        return int(value)
    except Exception:
        return default


def make_row_id(prefix: str, raw: str) -> str:
    return f"{prefix}_{str(abs(hash(raw)))[:16]}"


def _get(url: str, params: Dict) -> Dict:
    resp = requests.get(url, params=params, timeout=30)
    resp.raise_for_status()
    return resp.json()


def get_hashtag_id(hashtag_name: str) -> Optional[str]:
    """
    Cari hashtag ID via /ig_hashtag_search
    """
    if not ACCESS_TOKEN or not IG_USER_ID:
        return None

    url = f"{BASE_URL}/ig_hashtag_search"
    params = {
        "user_id": IG_USER_ID,
        "q": hashtag_name,
        "access_token": ACCESS_TOKEN,
    }

    try:
        data = _get(url, params)
        items = data.get("data", [])
        if items:
            return items[0].get("id")
    except Exception as e:
        print(f"[instagram_scraper] gagal cari hashtag_id #{hashtag_name}: {e}")
    return None


def fetch_hashtag_posts(hashtag_name: str, media_type: str = "recent_media") -> List[Dict]:
    """
    media_type: recent_media / top_media
    """
    hashtag_id = get_hashtag_id(hashtag_name)
    if not hashtag_id:
        return []

    url = f"{BASE_URL}/{hashtag_id}/{media_type}"
    params = {
        "user_id": IG_USER_ID,
        "fields": "id,caption,like_count,comments_count,media_type,media_url,permalink,timestamp,username",
        "access_token": ACCESS_TOKEN,
    }

    rows = []
    try:
        data = _get(url, params)
        for item in data.get("data", []):
            caption = clean_text(item.get("caption", ""))
            like_count = safe_int(item.get("like_count", 0))
            comments_count = safe_int(item.get("comments_count", 0))

            rows.append({
                "ID": make_row_id("igp", f"{item.get('id','')}-{caption}"),
                "Sumber_Data": "MEDIA SOSIAL",
                "Platform": "Instagram",
                "Jenis_Konten": "POST",
                "Akun": clean_text(item.get("username", "")),
                "Konten": caption,
                "Konten_Bersih": caption,
                "Link": item.get("permalink", ""),
                "Tanggal": _to_wib_string(item.get("timestamp")),
                "Tanggal_Ambil": _now_wib_str(),
                "Like": like_count,
                "Comment": comments_count,
                "Share": 0,
                "View": 0,
                "Engagement": like_count + comments_count,
                "Keyword_Terdeteksi": "",
                "Status_Validasi": "BELUM DIVERIFIKASI",
                "Hashtag_Pencarian": hashtag_name,
                "Media_Type": item.get("media_type", ""),
                "Parent_Post_ID": item.get("id", ""),
                "Post_Akun": clean_text(item.get("username", "")),
                "Post_Caption": caption,
            })
    except Exception as e:
        print(f"[instagram_scraper] gagal ambil post #{hashtag_name}: {e}")

    return rows


def run_instagram_scraper(
    hashtags: Optional[List[str]] = None,
    save_csv: bool = True
) -> pd.DataFrame:
    """
    Tahap awal: fokus ke post berbasis hashtag.
    """
    hashtags = hashtags or INSTAGRAM_HASHTAGS
    all_rows = []

    for tag in hashtags:
        all_rows.extend(fetch_hashtag_posts(tag, media_type="recent_media"))

    df = pd.DataFrame(all_rows)

    if df.empty:
        df = pd.DataFrame(columns=[
            "ID", "Sumber_Data", "Platform", "Jenis_Konten", "Akun", "Konten",
            "Konten_Bersih", "Link", "Tanggal", "Tanggal_Ambil", "Like",
            "Comment", "Share", "View", "Engagement", "Keyword_Terdeteksi",
            "Status_Validasi", "Hashtag_Pencarian", "Media_Type",
            "Parent_Post_ID", "Post_Akun", "Post_Caption"
        ])
    else:
        df.drop_duplicates(subset=["Platform", "Akun", "Konten_Bersih", "Tanggal"], inplace=True)
        df = df[df["Konten_Bersih"].str.len() > 0].reset_index(drop=True)

    if save_csv:
        df.to_csv("raw_instagram_posts.csv", index=False, encoding="utf-8-sig")

    print(f"[instagram_scraper] total post instagram: {len(df)}")
    return df


if __name__ == "__main__":
    df = run_instagram_scraper()
    print(df.head())