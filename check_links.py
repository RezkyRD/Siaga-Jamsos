import pandas as pd
import requests
import streamlit as st

from gsheet_utils import read_sheet, clear_and_write


OUTPUT_COLUMNS = [
    "UID",
    "Judul",
    "Media",
    "Link",
    "Tanggal_Publish",
    "Status_Link",
    "HTTP_Status",
    "Final_URL",
    "Terakhir_Dicek",
    "Catatan_Link",
]


def ensure_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    for col in OUTPUT_COLUMNS:
        if col not in df.columns:
            df[col] = ""
    return df[OUTPUT_COLUMNS]


def normalize_date_col(df: pd.DataFrame) -> pd.Series:
    if "Tanggal_Publish" in df.columns:
        s = pd.to_datetime(df["Tanggal_Publish"], errors="coerce")
    elif "Waktu_Publish_WIB" in df.columns:
        s = pd.to_datetime(df["Waktu_Publish_WIB"], errors="coerce")
    else:
        s = pd.Series([pd.NaT] * len(df), index=df.index)
    return s


def classify_link_status(status_code: int, final_url: str, original_url: str) -> tuple[str, str]:
    if status_code == 200:
        if final_url and original_url and final_url.rstrip("/") != original_url.rstrip("/"):
            return "REDIRECT", "Link dialihkan ke URL lain."
        return "AKTIF", "Link dapat diakses normal."

    if status_code in (301, 302, 303, 307, 308):
        return "REDIRECT", "Link dialihkan."

    if status_code in (404, 410):
        return "KEMUNGKINAN TAKEDOWN", "Halaman tidak ditemukan / sudah dihapus."

    if status_code == 403:
        return "TERBATAS", "Akses ditolak (403). Bisa anti-bot atau pembatasan situs."

    if status_code == 451:
        return "TERBATAS", "Konten tidak tersedia karena pembatasan hukum/kebijakan."

    if status_code >= 500:
        return "ERROR SITUS", "Server situs sedang bermasalah."

    return "TIDAK DAPAT DIAKSES", f"HTTP status {status_code}."


def check_one_link(url: str, timeout: int = 8) -> dict:
    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; SIAGA-JAMSOS-LinkMonitor/1.0)"
    }

    try:
        r = requests.get(url, headers=headers, timeout=timeout, allow_redirects=True)
        status_code = int(r.status_code)
        final_url = str(r.url or "").strip()
        status_link, note = classify_link_status(status_code, final_url, url)
        return {
            "Status_Link": status_link,
            "HTTP_Status": str(status_code),
            "Final_URL": final_url,
            "Catatan_Link": note,
        }
    except requests.exceptions.Timeout:
        return {
            "Status_Link": "ERROR CEK",
            "HTTP_Status": "",
            "Final_URL": "",
            "Catatan_Link": "Timeout saat cek link.",
        }
    except requests.exceptions.RequestException as e:
        return {
            "Status_Link": "ERROR CEK",
            "HTTP_Status": "",
            "Final_URL": "",
            "Catatan_Link": f"Gagal cek link: {str(e)}",
        }


def run_link_monitor(sheet_key=None, max_links: int = 100, days_back: int = 3):
    if sheet_key is None:
        sheet_key = st.secrets["SHEET_KEY"]

    # Ambil dari ANALYZED karena itu basis tampilan sistem saat ini
    try:
        df = read_sheet(sheet_key, "ANALYZED")
    except Exception:
        df = pd.DataFrame()

    if df is None or df.empty:
        empty_df = pd.DataFrame(columns=OUTPUT_COLUMNS)
        clear_and_write(sheet_key, "LINK_MONITOR", empty_df)
        return empty_df

    df = df.copy()
    df.columns = df.columns.astype(str).str.strip()

    if "Link" not in df.columns:
        empty_df = pd.DataFrame(columns=OUTPUT_COLUMNS)
        clear_and_write(sheet_key, "LINK_MONITOR", empty_df)
        return empty_df

    # Saring link valid
    df["Link"] = df["Link"].astype(str).str.strip()
    df = df[df["Link"] != ""].copy()

    if df.empty:
        empty_df = pd.DataFrame(columns=OUTPUT_COLUMNS)
        clear_and_write(sheet_key, "LINK_MONITOR", empty_df)
        return empty_df

    # Fokus berita beberapa hari terakhir
    publish_dt = normalize_date_col(df)
    today = pd.Timestamp.now(tz="Asia/Jakarta").tz_localize(None).normalize()
    min_dt = today - pd.Timedelta(days=days_back)

    df["__publish_dt"] = publish_dt
    df = df[df["__publish_dt"] >= min_dt].copy()

    if df.empty:
        empty_df = pd.DataFrame(columns=OUTPUT_COLUMNS)
        clear_and_write(sheet_key, "LINK_MONITOR", empty_df)
        return empty_df

    # Urutkan berita terbaru dulu
    df = df.sort_values("__publish_dt", ascending=False)

    # Ambil monitor lama supaya tidak cek ulang link yang sudah dicek hari ini
    try:
        old_monitor = read_sheet(sheet_key, "LINK_MONITOR")
    except Exception:
        old_monitor = pd.DataFrame()

    checked_today_uids = set()
    if old_monitor is not None and not old_monitor.empty:
        old_monitor = old_monitor.copy()
        old_monitor.columns = old_monitor.columns.astype(str).str.strip()

        if "Terakhir_Dicek" in old_monitor.columns and "UID" in old_monitor.columns:
            old_monitor["__checked_dt"] = pd.to_datetime(old_monitor["Terakhir_Dicek"], errors="coerce")
            old_monitor_today = old_monitor[
                old_monitor["__checked_dt"].dt.date == today.date()
            ]
            checked_today_uids = set(old_monitor_today["UID"].astype(str).tolist())

    if "UID" in df.columns:
        df = df[~df["UID"].astype(str).isin(checked_today_uids)].copy()

    if df.empty:
        # tidak ada yang perlu dicek ulang hari ini
        return ensure_columns(old_monitor) if old_monitor is not None and not old_monitor.empty else pd.DataFrame(columns=OUTPUT_COLUMNS)

    df = df.head(max_links).copy()

    results = []
    check_time = pd.Timestamp.now(tz="Asia/Jakarta").tz_localize(None).strftime("%Y-%m-%d %H:%M:%S")

    for _, row in df.iterrows():
        uid = str(row.get("UID", "")).strip()
        judul = str(row.get("Judul", "")).strip()
        media = str(row.get("Media", "")).strip()
        link = str(row.get("Link", "")).strip()
        tanggal_publish = str(row.get("Tanggal_Publish", "")).strip()

        status_info = check_one_link(link)

        results.append({
            "UID": uid,
            "Judul": judul,
            "Media": media,
            "Link": link,
            "Tanggal_Publish": tanggal_publish,
            "Status_Link": status_info["Status_Link"],
            "HTTP_Status": status_info["HTTP_Status"],
            "Final_URL": status_info["Final_URL"],
            "Terakhir_Dicek": check_time,
            "Catatan_Link": status_info["Catatan_Link"],
        })

    new_monitor = pd.DataFrame(results)
    new_monitor = ensure_columns(new_monitor)

    # Gabung dengan hasil lama, pakai UID sebagai kunci
    if old_monitor is not None and not old_monitor.empty:
        old_monitor = ensure_columns(old_monitor)
        combined = pd.concat([old_monitor, new_monitor], ignore_index=True)

        if "UID" in combined.columns and combined["UID"].astype(str).str.strip().ne("").any():
            combined = combined.drop_duplicates(subset=["UID"], keep="last")
        else:
            combined = combined.drop_duplicates(subset=["Link"], keep="last")
    else:
        combined = new_monitor

    # Rapikan urutan: terbaru dicek di atas
    combined["__sort_dt"] = pd.to_datetime(combined["Terakhir_Dicek"], errors="coerce")
    combined = combined.sort_values("__sort_dt", ascending=False).drop(columns="__sort_dt", errors="ignore")
    combined = ensure_columns(combined)

    clear_and_write(sheet_key, "LINK_MONITOR", combined)
    return combined


if __name__ == "__main__":
    run_link_monitor()