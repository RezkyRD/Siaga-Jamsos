import re
from html import unescape
from typing import List, Dict, Optional

import pandas as pd
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


# =========================================================
# KONFIGURASI
# =========================================================
YOUTUBE_API_KEY = ISI_API_KEY_ANDA
TIMEZONE = AsiaJakarta

# Keyword awal SIAGA JAMSOS
YOUTUBE_KEYWORDS = [
    PHK buruh,
    PHK massal,
    buruh demo,
    pesangon tidak dibayar,
    gaji terlambat buruh,
    BPJS Ketenagakerjaan,
    JHT pekerja,
    JKK pekerja,
    JKP pekerja,
    kecelakaan kerja,
]

# Batas default agar kuota aman
MAX_VIDEOS_PER_KEYWORD = 5
MAX_COMMENTS_PER_VIDEO = 20
INCLUDE_REPLIES = False


# =========================================================
# HELPER
# =========================================================
def _get_youtube_client()
    Buat client YouTube API.
    return build(youtube, v3, developerKey=YOUTUBE_API_KEY)


def _now_wib_str() - str
    return pd.Timestamp.now(tz=UTC).tz_convert(TIMEZONE).strftime(%Y-%m-%d %H%M%S)


def _to_wib_string(value Optional[str]) - str
    if value is None or str(value).strip() == 
        return _now_wib_str()

    try
        ts = pd.to_datetime(value, errors=coerce, utc=True)
        if pd.isna(ts)
            return _now_wib_str()
        return ts.tz_convert(TIMEZONE).strftime(%Y-%m-%d %H%M%S)
    except Exception
        return _now_wib_str()


def clean_text(text str) - str
    Bersihkan teks komentarvideo.
    if text is None
        return 

    text = unescape(str(text))
    text = re.sub(rhttpS+www.S+,  , text)
    text = re.sub(r[rnt]+,  , text)
    text = re.sub(rs+,  , text)
    return text.strip()


def safe_int(value, default=0) - int
    try
        return int(value)
    except Exception
        return default


def make_row_id(prefix str, raw str) - str
    return f{prefix}_{str(abs(hash(raw)))[16]}


# =========================================================
# 1) CARI VIDEO BERDASARKAN KEYWORD
# =========================================================
def search_videos_by_keyword(
    youtube,
    keyword str,
    max_results int = MAX_VIDEOS_PER_KEYWORD,
) - List[Dict]
    
    Cari video terbaru berdasarkan keyword.
    Memakai search.list.
    
    rows List[Dict] = []

    try
        request = youtube.search().list(
            q=keyword,
            part=snippet,
            type=video,
            order=date,
            maxResults=max_results,
        )
        response = request.execute()

        for item in response.get(items, [])
            video_id = item[id].get(videoId, )
            snippet = item.get(snippet, {})

            rows.append(
                {
                    Video_ID video_id,
                    Video_Judul clean_text(snippet.get(title, )),
                    Video_Deskripsi clean_text(snippet.get(description, )),
                    Video_Link fhttpswww.youtube.comwatchv={video_id},
                    Channel clean_text(snippet.get(channelTitle, )),
                    Tanggal_Video _to_wib_string(snippet.get(publishedAt)),
                    Keyword_Pencarian keyword,
                }
            )
    except HttpError as e
        print(f[youtube_scraper] Gagal search video untuk keyword '{keyword}' {e})
    except Exception as e
        print(f[youtube_scraper] Error umum search video '{keyword}' {e})

    return rows


# =========================================================
# 2) AMBIL DETAIL VIDEO (OPSIONAL TAPI BAGUS)
# =========================================================
def fetch_video_statistics(youtube, video_ids List[str]) - pd.DataFrame
    
    Ambil statistik video dengan videos.list.
    
    if not video_ids
        return pd.DataFrame(columns=[Video_ID, Video_View, Video_Like, Video_Comment_Count])

    rows = []
    try
        # API menerima comma-separated ids
        request = youtube.videos().list(
            part=statistics,
            id=,.join(video_ids),
        )
        response = request.execute()

        for item in response.get(items, [])
            stats = item.get(statistics, {})
            rows.append(
                {
                    Video_ID item.get(id, ),
                    Video_View safe_int(stats.get(viewCount, 0)),
                    Video_Like safe_int(stats.get(likeCount, 0)),
                    Video_Comment_Count safe_int(stats.get(commentCount, 0)),
                }
            )
    except HttpError as e
        print(f[youtube_scraper] Gagal ambil statistik video {e})
    except Exception as e
        print(f[youtube_scraper] Error umum statistik video {e})

    return pd.DataFrame(rows)


# =========================================================
# 3) AMBIL KOMENTAR LEVEL ATAS
# =========================================================
def fetch_top_comments(
    youtube,
    video_row Dict,
    max_results int = MAX_COMMENTS_PER_VIDEO,
    include_replies bool = INCLUDE_REPLIES,
) - List[Dict]
    
    Ambil komentar level atas dari sebuah video memakai commentThreads.list.
    Jika include_replies=True, balasan yang muncul di payload awal juga ikut diambil.
    
    rows List[Dict] = []
    video_id = video_row[Video_ID]

    try
        request = youtube.commentThreads().list(
            part=snippet,replies,
            videoId=video_id,
            maxResults=max_results,
            order=relevance,  # bisa diganti time bila ingin terbaru
            textFormat=plainText,
        )
        response = request.execute()

        for item in response.get(items, [])
            snippet = item.get(snippet, {})
            top_comment = snippet.get(topLevelComment, {})
            top_snippet = top_comment.get(snippet, {})

            comment_text = clean_text(top_snippet.get(textDisplay, ))

            rows.append(
                {
                    ID make_row_id(ytc, f{video_id}-{top_comment.get('id','')}-{comment_text}),
                    Sumber_Data MEDIA SOSIAL,
                    Platform YouTube,
                    Jenis_Konten KOMENTAR,
                    Akun clean_text(top_snippet.get(authorDisplayName, )),
                    Konten comment_text,
                    Konten_Bersih comment_text,
                    Link video_row[Video_Link],
                    Tanggal _to_wib_string(top_snippet.get(publishedAt)),
                    Tanggal_Ambil _now_wib_str(),
                    Like safe_int(top_snippet.get(likeCount, 0)),
                    Comment 0,
                    Share 0,
                    View 0,
                    Engagement safe_int(top_snippet.get(likeCount, 0)),
                    Keyword_Terdeteksi ,
                    Status_Validasi BELUM DIVERIFIKASI,
                    Video_ID video_id,
                    Video_Judul video_row[Video_Judul],
                    Video_Deskripsi video_row[Video_Deskripsi],
                    Channel video_row[Channel],
                    Tanggal_Video video_row[Tanggal_Video],
                    Keyword_Pencarian video_row[Keyword_Pencarian],
                    Parent_Comment_ID ,
                    Is_Reply False,
                }
            )

            # Ambil reply yang ikut terbawa dalam payload commentThreads
            if include_replies
                replies = item.get(replies, {}).get(comments, [])
                parent_id = top_comment.get(id, )

                for rep in replies
                    rep_snippet = rep.get(snippet, {})
                    rep_text = clean_text(rep_snippet.get(textDisplay, ))

                    rows.append(
                        {
                            ID make_row_id(ytr, f{video_id}-{rep.get('id','')}-{rep_text}),
                            Sumber_Data MEDIA SOSIAL,
                            Platform YouTube,
                            Jenis_Konten KOMENTAR_BALASAN,
                            Akun clean_text(rep_snippet.get(authorDisplayName, )),
                            Konten rep_text,
                            Konten_Bersih rep_text,
                            Link video_row[Video_Link],
                            Tanggal _to_wib_string(rep_snippet.get(publishedAt)),
                            Tanggal_Ambil _now_wib_str(),
                            Like safe_int(rep_snippet.get(likeCount, 0)),
                            Comment 0,
                            Share 0,
                            View 0,
                            Engagement safe_int(rep_snippet.get(likeCount, 0)),
                            Keyword_Terdeteksi ,
                            Status_Validasi BELUM DIVERIFIKASI,
                            Video_ID video_id,
                            Video_Judul video_row[Video_Judul],
                            Video_Deskripsi video_row[Video_Deskripsi],
                            Channel video_row[Channel],
                            Tanggal_Video video_row[Tanggal_Video],
                            Keyword_Pencarian video_row[Keyword_Pencarian],
                            Parent_Comment_ID parent_id,
                            Is_Reply True,
                        }
                    )

    except HttpError as e
        print(f[youtube_scraper] Gagal ambil komentar video {video_id} {e})
    except Exception as e
        print(f[youtube_scraper] Error umum komentar video {video_id} {e})

    return rows


# =========================================================
# 4) OPSIONAL AMBIL SEMUA BALASAN DARI KOMENTAR TERTENTU
# =========================================================
def fetch_all_replies_for_parent(youtube, parent_comment_id str) - List[Dict]
    
    Jika suatu saat Anda ingin semua balasan lengkap, gunakan comments.list(parentId=...).
    Fungsi ini disiapkan untuk pengembangan lanjut.
    
    rows List[Dict] = []

    try
        request = youtube.comments().list(
            part=snippet,
            parentId=parent_comment_id,
            maxResults=100,
            textFormat=plainText,
        )
        response = request.execute()

        for item in response.get(items, [])
            snippet = item.get(snippet, {})
            rows.append(
                {
                    Reply_ID item.get(id, ),
                    Parent_Comment_ID parent_comment_id,
                    Akun clean_text(snippet.get(authorDisplayName, )),
                    Konten clean_text(snippet.get(textDisplay, )),
                    Tanggal _to_wib_string(snippet.get(publishedAt)),
                    Like safe_int(snippet.get(likeCount, 0)),
                }
            )
    except Exception as e
        print(f[youtube_scraper] Gagal ambil semua replies {e})

    return rows


# =========================================================
# 5) GABUNGKAN SEMUA
# =========================================================
def run_youtube_comment_scraper(
    keywords Optional[List[str]] = None,
    max_videos_per_keyword int = MAX_VIDEOS_PER_KEYWORD,
    max_comments_per_video int = MAX_COMMENTS_PER_VIDEO,
    include_replies bool = INCLUDE_REPLIES,
    save_comments_csv bool = True,
    save_videos_csv bool = True,
)
    
    Jalankan scraper YouTube berbasis komentar.

    Output
    - raw_youtube_videos.csv
    - raw_social.csv  (komentar YouTube sebagai sumber media sosial)
    
    if not YOUTUBE_API_KEY or YOUTUBE_API_KEY == ISI_API_KEY_ANDA
        raise ValueError(Isi dulu YOUTUBE_API_KEY di youtube_scraper.py)

    youtube = _get_youtube_client()
    keywords = keywords or YOUTUBE_KEYWORDS

    # 1. Cari video
    all_videos List[Dict] = []
    for kw in keywords
        found = search_videos_by_keyword(
            youtube=youtube,
            keyword=kw,
            max_results=max_videos_per_keyword,
        )
        all_videos.extend(found)

    if not all_videos
        df_videos = pd.DataFrame(columns=[
            Video_ID, Video_Judul, Video_Deskripsi, Video_Link,
            Channel, Tanggal_Video, Keyword_Pencarian,
            Video_View, Video_Like, Video_Comment_Count
        ])
        df_comments = pd.DataFrame()
        return df_videos, df_comments

    # Hapus video duplikat
    df_videos = pd.DataFrame(all_videos).drop_duplicates(subset=[Video_ID]).reset_index(drop=True)

    # 2. Tambah statistik video
    stats_df = fetch_video_statistics(youtube, df_videos[Video_ID].dropna().tolist())
    if not stats_df.empty
        df_videos = df_videos.merge(stats_df, on=Video_ID, how=left)
    else
        df_videos[Video_View] = 0
        df_videos[Video_Like] = 0
        df_videos[Video_Comment_Count] = 0

    # 3. Ambil komentar
    all_comments List[Dict] = []
    for _, row in df_videos.iterrows()
        comments = fetch_top_comments(
            youtube=youtube,
            video_row=row.to_dict(),
            max_results=max_comments_per_video,
            include_replies=include_replies,
        )
        all_comments.extend(comments)

    df_comments = pd.DataFrame(all_comments)

    if df_comments.empty
        df_comments = pd.DataFrame(columns=[
            ID, Sumber_Data, Platform, Jenis_Konten, Akun, Konten,
            Konten_Bersih, Link, Tanggal, Tanggal_Ambil, Like,
            Comment, Share, View, Engagement, Keyword_Terdeteksi,
            Status_Validasi, Video_ID, Video_Judul, Video_Deskripsi,
            Channel, Tanggal_Video, Keyword_Pencarian,
            Parent_Comment_ID, Is_Reply
        ])
    else
        df_comments.drop_duplicates(subset=[Video_ID, Akun, Konten_Bersih, Tanggal], inplace=True)
        df_comments = df_comments[df_comments[Konten_Bersih].str.len()  0].reset_index(drop=True)

    # 4. Simpan
    if save_videos_csv
        df_videos.to_csv(raw_youtube_videos.csv, index=False, encoding=utf-8-sig)

    if save_comments_csv
        df_comments.to_csv(raw_social.csv, index=False, encoding=utf-8-sig)

    print(f[youtube_scraper] Total video {len(df_videos)})
    print(f[youtube_scraper] Total komentar {len(df_comments)})

    return df_videos, df_comments


if __name__ == __main__
    videos_df, comments_df = run_youtube_comment_scraper(
        max_videos_per_keyword=3,
        max_comments_per_video=10,
        include_replies=False,
    )
    print(videos_df.head())
    print(comments_df.head())