import re
import hashlib
import pandas as pd
import streamlit as st

from gsheet_utils import read_sheet, clear_and_write


OUTPUT_COLUMNS = [
    "Cluster_ID",
    "Nama_Isu",
    "Topik_Utama",
    "Kategori_Berita",
    "Provinsi",
    "Kabupaten_Kota",
    "Lokasi_Utama",
    "Tanggal_Isu",
    "Jumlah_Berita",
    "Jumlah_Media",
    "Daftar_Media",
    "Judul_Representatif",
    "Link_Representatif",
    "Score_Maks",
    "Score_Rata_Rata",
    "Prioritas_Cluster",
    "Skala_Cluster",
    "Ringkasan_Cluster",
    "Status_Cluster",
]


STOPWORDS = {
    "dan", "di", "ke", "dari", "untuk", "pada", "dengan", "karena", "akibat",
    "yang", "ini", "itu", "atau", "oleh", "dalam", "soal", "terkait", "usai",
    "saat", "bikin", "jadi", "hingga", "kian", "bakal", "masih", "sudah",
    "para", "sejumlah", "seorang", "orang", "tahun", "hari", "bulan", "jakarta",
    "indonesia", "nasional", "media", "berita", "update", "terbaru"
}


TOPIC_HINT_WORDS = {
    "PHK": {"phk", "dirumahkan", "pesangon", "kontrak", "karyawan", "buruh", "pekerja"},
    "Kecelakaan Kerja (JKK)": {"kecelakaan", "ledakan", "kebakaran", "tewas", "korban", "proyek"},
    "THR / Kesejahteraan Pekerja": {"thr", "tunjangan", "hari", "raya"},
    "Upah / Gaji": {"upah", "gaji", "ump", "umk"},
    "Aksi / Demo Buruh": {"demo", "mogok", "unjuk", "rasa", "buruh"},
    "Konflik Hubungan Industrial": {"perselisihan", "sengketa", "konflik", "tripartit", "mediasi"},
    "Kepesertaan BPJS": {"bpjs", "bpjamsostek", "jamsostek", "kepesertaan", "iuran"},
    "Klaim JHT": {"jht", "hari", "tua", "klaim", "saldo"},
    "Manfaat JKP": {"jkp", "kehilangan", "pekerjaan", "klaim"},
    "Jaminan Pensiun (JP)": {"jp", "pensiun", "iuran"},
    "Santunan Kematian (JKM)": {"jkm", "kematian", "ahli", "waris"},
    "Tunggakan Iuran": {"tunggakan", "iuran", "denda"},
    "Pekerja Migran Indonesia (PMI)": {"pmi", "migran", "tki"},
    "Jasa Konstruksi": {"konstruksi", "proyek", "pembangunan"},
}


def clean_text(text: str) -> str:
    text = str(text or "").lower()
    text = re.sub(r"<.*?>", " ", text)
    text = re.sub(r"[^a-z0-9\s\-]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def ensure_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    for col in OUTPUT_COLUMNS:
        if col not in df.columns:
            df[col] = ""
    return df[OUTPUT_COLUMNS]


def get_lokasi_utama(row) -> str:
    kab = str(row.get("Kabupaten_Kota", "") or "").strip()
    prov = str(row.get("Provinsi", "") or "").strip()

    if kab:
        return kab
    if prov:
        return prov
    return "Nasional / Tidak Diketahui"


def tokenize_title(title: str) -> list[str]:
    text = clean_text(title)
    tokens = text.split()

    hasil = []
    for tok in tokens:
        if tok in STOPWORDS:
            continue
        if tok.isdigit():
            continue
        if len(tok) <= 2:
            continue
        hasil.append(tok)

    return hasil


def build_signature(title: str, topic: str = "") -> str:
    tokens = tokenize_title(title)

    if not tokens:
        return "umum"

    topic_hints = TOPIC_HINT_WORDS.get(str(topic or "").strip(), set())

    preferred = []
    others = []

    for tok in tokens:
        if tok in topic_hints:
            preferred.append(tok)
        else:
            others.append(tok)

    chosen = []
    for tok in preferred:
        if tok not in chosen:
            chosen.append(tok)
        if len(chosen) >= 3:
            break

    for tok in others:
        if tok not in chosen:
            chosen.append(tok)
        if len(chosen) >= 3:
            break

    if not chosen:
        chosen = tokens[:3]

    return " ".join(chosen)


def make_cluster_id(topic: str, lokasi: str, tanggal: str, signature: str) -> str:
    raw = f"{topic}|{lokasi}|{tanggal}|{signature}"
    digest = hashlib.md5(raw.encode("utf-8")).hexdigest()[:10].upper()
    return f"ISU-{digest}"


def classify_cluster_priority(score: float) -> str:
    if score >= 9:
        return "PRIORITAS TINGGI"
    if score >= 5:
        return "PRIORITAS SEDANG"
    return "PRIORITAS RENDAH"


def get_cluster_scale(jumlah_media: int, jumlah_berita: int) -> str:
    if jumlah_media >= 6 or jumlah_berita >= 10:
        return "BESAR"
    if jumlah_media >= 3 or jumlah_berita >= 5:
        return "MENENGAH"
    return "KECIL"


def build_cluster_summary(row) -> str:
    topik = str(row.get("Topik_Utama", "") or "").strip()
    lokasi = str(row.get("Lokasi_Utama", "") or "").strip()
    jumlah_media = int(row.get("Jumlah_Media", 0) or 0)
    jumlah_berita = int(row.get("Jumlah_Berita", 0) or 0)
    prioritas = str(row.get("Prioritas_Cluster", "") or "").strip()

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
        f"Isu {topik.lower()} di {lokasi} diberitakan oleh {jumlah_media} media "
        f"dalam {jumlah_berita} berita. Isu ini {dampak}. "
        f"Prioritas cluster saat ini adalah {prioritas.lower()}."
    )


def pick_representative(group: pd.DataFrame) -> pd.Series:
    df = group.copy()

    if "Score" not in df.columns:
        df["Score"] = 0
    if "Jumlah_Media_Serupa" not in df.columns:
        df["Jumlah_Media_Serupa"] = 0

    df["Score"] = pd.to_numeric(df["Score"], errors="coerce").fillna(0)
    df["Jumlah_Media_Serupa"] = pd.to_numeric(df["Jumlah_Media_Serupa"], errors="coerce").fillna(0)

    if "Waktu_Publish_WIB" in df.columns:
        df["__publish_dt"] = pd.to_datetime(df["Waktu_Publish_WIB"], errors="coerce")
    else:
        df["__publish_dt"] = pd.NaT

    df = df.sort_values(
        ["Score", "Jumlah_Media_Serupa", "__publish_dt"],
        ascending=[False, False, False]
    )

    return df.iloc[0]


def run_cluster_isu(sheet_key=None):
    if sheet_key is None:
        sheet_key = st.secrets["SHEET_KEY"]

    try:
        df = read_sheet(sheet_key, "ANALYZED")
    except Exception:
        df = pd.DataFrame()

    if df is None or df.empty:
        empty_df = pd.DataFrame(columns=OUTPUT_COLUMNS)
        clear_and_write(sheet_key, "CLUSTERED", empty_df)
        return empty_df

    df = df.copy()
    df.columns = df.columns.astype(str).str.strip()

    for col in [
        "Judul", "Media", "Link", "Topik_Utama", "Kategori_Berita",
        "Provinsi", "Kabupaten_Kota", "Tanggal_Publish", "Prioritas", "Score"
    ]:
        if col not in df.columns:
            df[col] = ""

    df["Judul"] = df["Judul"].astype(str).fillna("")
    df["Media"] = df["Media"].astype(str).fillna("")
    df["Link"] = df["Link"].astype(str).fillna("")
    df["Topik_Utama"] = df["Topik_Utama"].astype(str).fillna("")
    df["Kategori_Berita"] = df["Kategori_Berita"].astype(str).fillna("")
    df["Provinsi"] = df["Provinsi"].astype(str).fillna("")
    df["Kabupaten_Kota"] = df["Kabupaten_Kota"].astype(str).fillna("")
    df["Tanggal_Publish"] = df["Tanggal_Publish"].astype(str).fillna("")
    df["Prioritas"] = df["Prioritas"].astype(str).fillna("")
    df["Score"] = pd.to_numeric(df["Score"], errors="coerce").fillna(0)

    df = df[df["Topik_Utama"].str.strip() != ""].copy()

    if df.empty:
        empty_df = pd.DataFrame(columns=OUTPUT_COLUMNS)
        clear_and_write(sheet_key, "CLUSTERED", empty_df)
        return empty_df

    df["Lokasi_Utama"] = df.apply(get_lokasi_utama, axis=1)
    df["Signature_Judul"] = df.apply(
        lambda r: build_signature(r.get("Judul", ""), r.get("Topik_Utama", "")),
        axis=1
    )

    cluster_rows = []

    group_cols = ["Topik_Utama", "Lokasi_Utama", "Tanggal_Publish", "Signature_Judul"]

    for keys, group in df.groupby(group_cols, dropna=False):
        topik, lokasi, tanggal, signature = keys
        rep = pick_representative(group)

        jumlah_berita = int(len(group))
        jumlah_media = int(group["Media"].astype(str).str.strip().replace("", pd.NA).dropna().nunique())
        daftar_media = ", ".join(sorted({
            m.strip() for m in group["Media"].astype(str).tolist() if m.strip()
        }))

        score_maks = float(pd.to_numeric(group["Score"], errors="coerce").fillna(0).max())
        score_rata = float(pd.to_numeric(group["Score"], errors="coerce").fillna(0).mean())

        boost = 0
        if jumlah_media >= 7:
            boost += 2
        elif jumlah_media >= 4:
            boost += 1

        if jumlah_berita >= 6:
            boost += 1

        score_cluster = score_maks + boost
        prioritas_cluster = classify_cluster_priority(score_cluster)
        skala_cluster = get_cluster_scale(jumlah_media, jumlah_berita)

        cluster_id = make_cluster_id(topik, lokasi, tanggal, signature)

        row_out = {
            "Cluster_ID": cluster_id,
            "Nama_Isu": str(rep.get("Judul", "") or "").strip(),
            "Topik_Utama": str(topik or "").strip(),
            "Kategori_Berita": str(rep.get("Kategori_Berita", "") or "").strip(),
            "Provinsi": str(rep.get("Provinsi", "") or "").strip(),
            "Kabupaten_Kota": str(rep.get("Kabupaten_Kota", "") or "").strip(),
            "Lokasi_Utama": str(lokasi or "").strip(),
            "Tanggal_Isu": str(tanggal or "").strip(),
            "Jumlah_Berita": jumlah_berita,
            "Jumlah_Media": jumlah_media,
            "Daftar_Media": daftar_media,
            "Judul_Representatif": str(rep.get("Judul", "") or "").strip(),
            "Link_Representatif": str(rep.get("Link", "") or "").strip(),
            "Score_Maks": round(score_maks, 2),
            "Score_Rata_Rata": round(score_rata, 2),
            "Prioritas_Cluster": prioritas_cluster,
            "Skala_Cluster": skala_cluster,
            "Ringkasan_Cluster": "",
            "Status_Cluster": "ISU HARI INI",
        }

        cluster_rows.append(row_out)

    cluster_df = pd.DataFrame(cluster_rows)

    if cluster_df.empty:
        cluster_df = pd.DataFrame(columns=OUTPUT_COLUMNS)
        clear_and_write(sheet_key, "CLUSTERED", cluster_df)
        return cluster_df

    cluster_df["Ringkasan_Cluster"] = cluster_df.apply(build_cluster_summary, axis=1)

    priority_order = {
        "PRIORITAS TINGGI": 1,
        "PRIORITAS SEDANG": 2,
        "PRIORITAS RENDAH": 3,
    }
    cluster_df["__prio_order"] = cluster_df["Prioritas_Cluster"].map(priority_order).fillna(99)
    cluster_df["__score"] = pd.to_numeric(cluster_df["Score_Maks"], errors="coerce").fillna(0)
    cluster_df = cluster_df.sort_values(
        ["__prio_order", "__score", "Jumlah_Media", "Jumlah_Berita"],
        ascending=[True, False, False, False]
    )

    cluster_df = cluster_df.drop(columns=["__prio_order", "__score"], errors="ignore")
    cluster_df = ensure_columns(cluster_df)

    clear_and_write(sheet_key, "CLUSTERED", cluster_df)
    return cluster_df


if __name__ == "__main__":
    run_cluster_isu()