import pandas as pd
import streamlit as st
import hashlib

from gsheet_utils import read_sheet, clear_and_write


OUTPUT_COLUMNS = [
    "Strategic_ID",
    "Nama_Isu_Strategis",
    "Topik_Utama",
    "Kategori_Dominan",
    "Cakupan_Wilayah",
    "Window_Tanggal",
    "Jumlah_Cluster",
    "Jumlah_Berita",
    "Jumlah_Media",
    "Daftar_Media",
    "Score_Maks",
    "Score_Rata_Rata",
    "Prioritas_Strategis",
    "Skala_Strategis",
    "Ringkasan_Strategis",
    "Status_Strategis",
    "Contoh_Isu",
]


def ensure_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    for col in OUTPUT_COLUMNS:
        if col not in df.columns:
            df[col] = ""
    return df[OUTPUT_COLUMNS]


def make_strategic_id(topik: str, cakupan: str, window_tanggal: str) -> str:
    raw = f"{topik}|{cakupan}|{window_tanggal}"
    digest = hashlib.md5(raw.encode("utf-8")).hexdigest()[:10].upper()
    return f"STR-{digest}"


def normalize_scope(lokasi_series: pd.Series) -> str:
    values = [str(x).strip() for x in lokasi_series.astype(str).tolist() if str(x).strip()]
    if not values:
        return "Nasional"

    nasional_like = {
        "Nasional",
        "Nasional / Tidak Diketahui",
        "Nasional / Tidak Spesifik",
        "Tidak Diketahui",
    }

    unique_vals = set(values)

    if unique_vals & nasional_like:
        return "Nasional"

    if len(unique_vals) >= 3:
        return "Lintas Daerah"

    return sorted(unique_vals)[0]


def classify_strategic_priority(score: float) -> str:
    if score >= 11:
        return "PRIORITAS TINGGI"
    if score >= 6:
        return "PRIORITAS SEDANG"
    return "PRIORITAS RENDAH"


def classify_strategic_scale(jumlah_cluster: int, jumlah_berita: int, jumlah_media: int) -> str:
    if jumlah_cluster >= 5 or jumlah_berita >= 15 or jumlah_media >= 8:
        return "BESAR"
    if jumlah_cluster >= 3 or jumlah_berita >= 6 or jumlah_media >= 4:
        return "MENENGAH"
    return "KECIL"


def build_strategic_name(topik: str, cakupan: str) -> str:
    topik = str(topik).strip()

    strategic_map = {
        "PHK": "Gelombang PHK",
        "THR / Kesejahteraan Pekerja": "Permasalahan THR dan Kesejahteraan Pekerja",
        "Upah / Gaji": "Isu Upah dan Gaji",
        "Aksi / Demo Buruh": "Aksi dan Demo Buruh",
        "Konflik Hubungan Industrial": "Konflik Hubungan Industrial",
        "Kepesertaan BPJS": "Kepesertaan dan Kepatuhan BPJS Ketenagakerjaan",
        "Klaim JHT": "Klaim JHT",
        "Manfaat JKP": "Manfaat JKP",
        "Jaminan Pensiun (JP)": "Jaminan Pensiun",
        "Santunan Kematian (JKM)": "Santunan Kematian",
        "Tunggakan Iuran": "Tunggakan Iuran",
        "Pekerja Migran Indonesia (PMI)": "Isu Pekerja Migran Indonesia",
        "Jasa Konstruksi": "Isu Jasa Konstruksi",
        "Kecelakaan Kerja (JKK)": "Kecelakaan Kerja",
    }

    base = strategic_map.get(topik, topik if topik else "Isu Strategis")
    return f"{base} - {cakupan}"


def build_strategic_summary(row) -> str:
    nama = str(row.get("Nama_Isu_Strategis", "")).strip()
    topik = str(row.get("Topik_Utama", "")).strip()
    cakupan = str(row.get("Cakupan_Wilayah", "")).strip()
    jumlah_cluster = int(row.get("Jumlah_Cluster", 0) or 0)
    jumlah_berita = int(row.get("Jumlah_Berita", 0) or 0)
    jumlah_media = int(row.get("Jumlah_Media", 0) or 0)
    prioritas = str(row.get("Prioritas_Strategis", "")).strip().lower()

    topic_map = {
        "PHK": "berpotensi meningkatkan klaim JKP dan pencairan JHT",
        "Kecelakaan Kerja (JKK)": "berpotensi menimbulkan klaim JKK dan pada kasus fatal dapat berkembang menjadi JKM",
        "THR / Kesejahteraan Pekerja": "berpotensi memicu pengaduan dan konflik hubungan industrial",
        "Upah / Gaji": "berpotensi memicu perselisihan hubungan industrial",
        "Aksi / Demo Buruh": "perlu dipantau karena dapat meningkatkan tensi hubungan industrial",
        "Konflik Hubungan Industrial": "perlu dipantau karena dapat berkembang menjadi gangguan yang lebih besar",
        "Kepesertaan BPJS": "berdampak pada cakupan perlindungan tenaga kerja dan kepatuhan pemberi kerja",
        "Klaim JHT": "berkaitan dengan pencairan manfaat peserta",
        "Manfaat JKP": "berkaitan langsung dengan perlindungan pekerja terdampak PHK",
        "Jaminan Pensiun (JP)": "berkaitan dengan kesinambungan manfaat jangka panjang peserta",
        "Santunan Kematian (JKM)": "berpotensi menimbulkan klaim manfaat kematian",
        "Tunggakan Iuran": "berdampak pada kepatuhan dan kesinambungan perlindungan peserta",
        "Pekerja Migran Indonesia (PMI)": "berkaitan dengan perlindungan jaminan sosial pekerja migran Indonesia",
        "Jasa Konstruksi": "perlu dicermati karena sektor konstruksi memiliki risiko kecelakaan kerja yang tinggi",
    }

    dampak = topic_map.get(topik, "perlu dipantau karena dapat mempengaruhi jaminan sosial ketenagakerjaan")

    return (
        f"{nama} pada cakupan {cakupan} terbentuk dari {jumlah_cluster} cluster, "
        f"{jumlah_berita} berita, dan {jumlah_media} media. "
        f"Isu ini {dampak}. Prioritas strategis saat ini adalah {prioritas}."
    )


def run_cluster_level2(sheet_key=None):
    if sheet_key is None:
        sheet_key = st.secrets["SHEET_KEY"]

    try:
        df = read_sheet(sheet_key, "CLUSTERED")
    except Exception:
        df = pd.DataFrame()

    if df is None or df.empty:
        empty_df = pd.DataFrame(columns=OUTPUT_COLUMNS)
        clear_and_write(sheet_key, "CLUSTERED_L2", empty_df)
        return empty_df

    df = df.copy()
    df.columns = df.columns.astype(str).str.strip()

    required_defaults = {
        "Nama_Isu": "",
        "Topik_Utama": "",
        "Kategori_Berita": "",
        "Lokasi_Utama": "",
        "Window_Tanggal": "",
        "Jumlah_Berita": 0,
        "Jumlah_Media": 0,
        "Daftar_Media": "",
        "Score_Maks": 0,
        "Score_Rata_Rata": 0,
    }

    for col, default in required_defaults.items():
        if col not in df.columns:
            df[col] = default

    df["Topik_Utama"] = df["Topik_Utama"].astype(str).fillna("")
    df["Kategori_Berita"] = df["Kategori_Berita"].astype(str).fillna("")
    df["Lokasi_Utama"] = df["Lokasi_Utama"].astype(str).fillna("")
    df["Window_Tanggal"] = df["Window_Tanggal"].astype(str).fillna("")
    df["Nama_Isu"] = df["Nama_Isu"].astype(str).fillna("")
    df["Daftar_Media"] = df["Daftar_Media"].astype(str).fillna("")
    df["Jumlah_Berita"] = pd.to_numeric(df["Jumlah_Berita"], errors="coerce").fillna(0)
    df["Jumlah_Media"] = pd.to_numeric(df["Jumlah_Media"], errors="coerce").fillna(0)
    df["Score_Maks"] = pd.to_numeric(df["Score_Maks"], errors="coerce").fillna(0)
    df["Score_Rata_Rata"] = pd.to_numeric(df["Score_Rata_Rata"], errors="coerce").fillna(0)

    df = df[df["Topik_Utama"].str.strip() != ""].copy()

    if df.empty:
        empty_df = pd.DataFrame(columns=OUTPUT_COLUMNS)
        clear_and_write(sheet_key, "CLUSTERED_L2", empty_df)
        return empty_df

    strategic_rows = []

    group_cols = ["Topik_Utama", "Window_Tanggal"]

    for (topik, window_tanggal), group in df.groupby(group_cols, dropna=False):
        jumlah_cluster = int(len(group))
        jumlah_berita = int(group["Jumlah_Berita"].sum())

        media_set = set()
        for item in group["Daftar_Media"].tolist():
            for m in str(item).split(","):
                m = m.strip()
                if m:
                    media_set.add(m)

        jumlah_media = len(media_set)
        daftar_media = ", ".join(sorted(media_set))

        score_maks = float(group["Score_Maks"].max())
        score_rata = float(group["Score_Rata_Rata"].mean())

        cakupan = normalize_scope(group["Lokasi_Utama"])
        kategori_dominan = (
            group["Kategori_Berita"]
            .astype(str)
            .value_counts()
            .idxmax()
            if not group["Kategori_Berita"].empty
            else ""
        )

        strategic_boost = 0
        if jumlah_cluster >= 5:
            strategic_boost += 2
        elif jumlah_cluster >= 3:
            strategic_boost += 1

        if jumlah_media >= 8:
            strategic_boost += 2
        elif jumlah_media >= 4:
            strategic_boost += 1

        if jumlah_berita >= 15:
            strategic_boost += 2
        elif jumlah_berita >= 6:
            strategic_boost += 1

        strategic_score = score_maks + strategic_boost
        prioritas_strategis = classify_strategic_priority(strategic_score)
        skala_strategis = classify_strategic_scale(jumlah_cluster, jumlah_berita, jumlah_media)

        contoh_isu = (
            group.sort_values(["Score_Maks", "Jumlah_Media", "Jumlah_Berita"], ascending=[False, False, False])
            .iloc[0]["Nama_Isu"]
        )

        nama_isu_strategis = build_strategic_name(topik, cakupan)
        strategic_id = make_strategic_id(topik, cakupan, window_tanggal)

        row_out = {
            "Strategic_ID": strategic_id,
            "Nama_Isu_Strategis": nama_isu_strategis,
            "Topik_Utama": str(topik).strip(),
            "Kategori_Dominan": kategori_dominan,
            "Cakupan_Wilayah": cakupan,
            "Window_Tanggal": str(window_tanggal).strip(),
            "Jumlah_Cluster": jumlah_cluster,
            "Jumlah_Berita": jumlah_berita,
            "Jumlah_Media": jumlah_media,
            "Daftar_Media": daftar_media,
            "Score_Maks": round(score_maks, 2),
            "Score_Rata_Rata": round(score_rata, 2),
            "Prioritas_Strategis": prioritas_strategis,
            "Skala_Strategis": skala_strategis,
            "Ringkasan_Strategis": "",
            "Status_Strategis": "ISU STRATEGIS",
            "Contoh_Isu": str(contoh_isu).strip(),
        }

        strategic_rows.append(row_out)

    strategic_df = pd.DataFrame(strategic_rows)

    if strategic_df.empty:
        strategic_df = pd.DataFrame(columns=OUTPUT_COLUMNS)
        clear_and_write(sheet_key, "CLUSTERED_L2", strategic_df)
        return strategic_df

    strategic_df["Ringkasan_Strategis"] = strategic_df.apply(build_strategic_summary, axis=1)

    priority_order = {
        "PRIORITAS TINGGI": 1,
        "PRIORITAS SEDANG": 2,
        "PRIORITAS RENDAH": 3,
    }
    strategic_df["__prio"] = strategic_df["Prioritas_Strategis"].map(priority_order).fillna(99)
    strategic_df["__score"] = pd.to_numeric(strategic_df["Score_Maks"], errors="coerce").fillna(0)

    strategic_df = strategic_df.sort_values(
        ["__prio", "__score", "Jumlah_Media", "Jumlah_Berita", "Jumlah_Cluster"],
        ascending=[True, False, False, False, False]
    )

    strategic_df = strategic_df.drop(columns=["__prio", "__score"], errors="ignore")
    strategic_df = ensure_columns(strategic_df)

    clear_and_write(sheet_key, "CLUSTERED_L2", strategic_df)
    return strategic_df


if __name__ == "__main__":
    run_cluster_level2()