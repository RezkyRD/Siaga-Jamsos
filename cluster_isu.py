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
    "Window_Tanggal",
    "Entity_Key",
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
    "para", "sejumlah", "seorang", "orang", "tahun", "hari", "bulan",
    "indonesia", "nasional", "media", "berita", "update", "terbaru",
    "menteri", "pemerintah", "tegaskan", "ternyata", "ancaman", "isu",
    "katanya", "bakal", "resmi", "soal", "begini", "bikin", "jadi",
    "buruh", "pekerja", "karyawan", "pegawai", "perusahaan", "industri",
    "jakarta", "jawa", "barat", "timur", "tengah", "sumatera", "sulawesi",
    "bali", "papua", "kalimantan", "kepulauan", "provinsi", "kabupaten", "kota"
}


TOPIC_HINT_WORDS = {
    "PHK": {"phk", "dirumahkan", "pesangon", "kontrak", "pabrik", "efisiensi", "gelombang"},
    "Kecelakaan Kerja (JKK)": {"kecelakaan", "ledakan", "kebakaran", "tewas", "korban", "proyek"},
    "THR / Kesejahteraan Pekerja": {"thr", "tunjangan", "raya"},
    "Upah / Gaji": {"upah", "gaji", "ump", "umk"},
    "Aksi / Demo Buruh": {"demo", "mogok", "unjuk", "rasa", "aksi"},
    "Konflik Hubungan Industrial": {"perselisihan", "sengketa", "konflik", "tripartit", "mediasi"},
    "Kepesertaan BPJS": {"bpjs", "bpjamsostek", "jamsostek", "kepesertaan", "iuran"},
    "Klaim JHT": {"jht", "klaim", "saldo"},
    "Manfaat JKP": {"jkp", "klaim", "kehilangan"},
    "Jaminan Pensiun (JP)": {"jp", "pensiun", "iuran"},
    "Santunan Kematian (JKM)": {"jkm", "kematian", "waris"},
    "Tunggakan Iuran": {"tunggakan", "iuran", "denda"},
    "Pekerja Migran Indonesia (PMI)": {"pmi", "migran", "tki"},
    "Jasa Konstruksi": {"konstruksi", "proyek", "pembangunan"},
}

TOPIC_GENERIC_KEYS = {
    "PHK": "gelombang_phk",
    "THR / Kesejahteraan Pekerja": "isu_thr",
    "Upah / Gaji": "isu_upah",
    "Aksi / Demo Buruh": "aksi_buruh",
    "Konflik Hubungan Industrial": "konflik_hubungan_industrial",
    "Kepesertaan BPJS": "kepesertaan_bpjs",
    "Klaim JHT": "klaim_jht",
    "Manfaat JKP": "manfaat_jkp",
    "Jaminan Pensiun (JP)": "jaminan_pensiun",
    "Santunan Kematian (JKM)": "santunan_kematian",
    "Tunggakan Iuran": "tunggakan_iuran",
    "Pekerja Migran Indonesia (PMI)": "isu_pmi",
    "Jasa Konstruksi": "isu_konstruksi",
}

NATIONAL_TOPICS = {
    "PHK",
    "THR / Kesejahteraan Pekerja",
    "Upah / Gaji",
    "Aksi / Demo Buruh",
    "Konflik Hubungan Industrial",
    "Kepesertaan BPJS",
    "Tunggakan Iuran",
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


def is_national_like_location(lokasi: str) -> bool:
    lokasi = str(lokasi or "").strip().lower()
    return lokasi in {"nasional", "nasional / tidak spesifik", "nasional / tidak diketahui", "tidak diketahui", ""}


def normalize_entity_word(tok: str) -> str:
    tok = str(tok or "").strip().lower()

    replacements = {
        "pppk": "pppk",
        "asn": "asn",
        "bpjs": "bpjs",
        "bpjamsostek": "bpjs",
        "jamsostek": "bpjs",
        "jkp": "jkp",
        "jht": "jht",
        "jkk": "jkk",
        "jkm": "jkm",
        "jp": "jp",
        "thr": "thr",
        "umk": "umk",
        "ump": "ump",
        "phk": "phk",
        "sritex": "sritex",
        "prabowo": "prabowo",
        "pns": "asn",
        "honorer": "honorer",
    }
    return replacements.get(tok, tok)


def tokenize_title(title: str) -> list[str]:
    text = clean_text(title)
    tokens = text.split()

    hasil = []
    for tok in tokens:
        tok = normalize_entity_word(tok)
        if tok in STOPWORDS:
            continue
        if tok.isdigit():
            continue
        if len(tok) <= 2:
            continue
        hasil.append(tok)

    return hasil


def extract_entity_candidates(title: str, topic: str = "") -> list[str]:
    tokens = tokenize_title(title)
    if not tokens:
        return []

    topic_hints = TOPIC_HINT_WORDS.get(str(topic or "").strip(), set())

    priority = []
    secondary = []

    for tok in tokens:
        if tok in topic_hints:
            priority.append(tok)
        else:
            secondary.append(tok)

    chosen = []
    for tok in priority:
        if tok not in chosen:
            chosen.append(tok)

    for tok in secondary:
        if tok not in chosen:
            chosen.append(tok)

    return chosen[:5]


def build_entity_key(title: str, topic: str = "", lokasi: str = "") -> str:
    candidates = extract_entity_candidates(title, topic)
    lokasi = str(lokasi or "").strip()

    # ambil 2 kata inti pertama kalau ada
    core = []
    for tok in candidates:
        if tok not in core:
            core.append(tok)
        if len(core) >= 2:
            break

    # fallback nasional untuk topik besar bila judul terlalu generik
    if len(core) == 0:
        return TOPIC_GENERIC_KEYS.get(str(topic or "").strip(), "isu_umum")

    # bila lokasi nasional/tidak jelas dan topik besar, longgarkan cluster
    if is_national_like_location(lokasi) and str(topic or "").strip() in NATIONAL_TOPICS:
        return TOPIC_GENERIC_KEYS.get(str(topic or "").strip(), "isu_umum")

    return "_".join(core)


def get_time_window_key(date_value) -> str:
    dt = pd.to_datetime(date_value, errors="coerce")
    if pd.isna(dt):
        return "unknown"

    # bucket 3 harian
    day = int(dt.day)
    bucket = ((day - 1) // 3) + 1
    return f"{dt.year}-{dt.month:02d}-W{bucket:02d}"


def make_cluster_id(topic: str, lokasi: str, window_tanggal: str, entity_key: str) -> str:
    raw = f"{topic}|{lokasi}|{window_tanggal}|{entity_key}"
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
    if jumlah_media >= 3 or jumlah_berita >= 4:
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
        "Provinsi", "Kabupaten_Kota", "Tanggal_Publish", "Prioritas", "Score",
        "Waktu_Publish_WIB", "Jumlah_Media_Serupa"
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
    df["Jumlah_Media_Serupa"] = pd.to_numeric(df["Jumlah_Media_Serupa"], errors="coerce").fillna(0)

    df = df[df["Topik_Utama"].str.strip() != ""].copy()

    if df.empty:
        empty_df = pd.DataFrame(columns=OUTPUT_COLUMNS)
        clear_and_write(sheet_key, "CLUSTERED", empty_df)
        return empty_df

    df["Lokasi_Utama"] = df.apply(get_lokasi_utama, axis=1)
    df["Window_Tanggal"] = df["Tanggal_Publish"].apply(get_time_window_key)
    df["Entity_Key"] = df.apply(
        lambda r: build_entity_key(
            r.get("Judul", ""),
            r.get("Topik_Utama", ""),
            r.get("Lokasi_Utama", "")
        ),
        axis=1
    )

    cluster_rows = []

    # cluster lebih longgar: topik + lokasi + window tanggal + entity key
    group_cols = ["Topik_Utama", "Lokasi_Utama", "Window_Tanggal", "Entity_Key"]

    for keys, group in df.groupby(group_cols, dropna=False):
        topik, lokasi, window_tanggal, entity_key = keys
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
        elif jumlah_berita >= 3:
            boost += 0.5

        score_cluster = score_maks + boost
        prioritas_cluster = classify_cluster_priority(score_cluster)
        skala_cluster = get_cluster_scale(jumlah_media, jumlah_berita)

        # ambil tanggal isu dari berita representatif
        tanggal_isu = str(rep.get("Tanggal_Publish", "") or "").strip()

        cluster_id = make_cluster_id(topik, lokasi, window_tanggal, entity_key)

        row_out = {
            "Cluster_ID": cluster_id,
            "Nama_Isu": str(rep.get("Judul", "") or "").strip(),
            "Topik_Utama": str(topik or "").strip(),
            "Kategori_Berita": str(rep.get("Kategori_Berita", "") or "").strip(),
            "Provinsi": str(rep.get("Provinsi", "") or "").strip(),
            "Kabupaten_Kota": str(rep.get("Kabupaten_Kota", "") or "").strip(),
            "Lokasi_Utama": str(lokasi or "").strip(),
            "Tanggal_Isu": tanggal_isu,
            "Window_Tanggal": str(window_tanggal or "").strip(),
            "Entity_Key": str(entity_key or "").strip(),
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
    cluster_df["Jumlah_Media"] = pd.to_numeric(cluster_df["Jumlah_Media"], errors="coerce").fillna(0)
    cluster_df["Jumlah_Berita"] = pd.to_numeric(cluster_df["Jumlah_Berita"], errors="coerce").fillna(0)

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