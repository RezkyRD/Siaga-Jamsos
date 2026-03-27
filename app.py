import re
import streamlit as st
import pandas as pd
from html import escape
import plotly.graph_objects as go

from scraper import run_scraper
from filter_keyword import run_filter
from update_priority import run_priority
from gsheet_utils import read_sheet

SHEET_KEY = st.secrets["SHEET_KEY"]

# ===============================
# PAGE CONFIG
# ===============================
st.set_page_config(
    page_title="EWS Ketenagakerjaan",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ===============================
# STYLE
# ===============================
st.markdown(
    """
<style>
header[data-testid="stHeader"] { display: none; }
div[data-testid="stToolbar"] { display: none; }
#MainMenu { visibility: hidden; }
footer { visibility: hidden; }

:root {
    --bg-light: #f5f7fb;
    --card-light: rgba(255,255,255,0.78);
    --text-light: #101828;
    --muted-light: #667085;
    --line-light: rgba(16,24,40,0.08);

    --bg-dark: #0b1120;
    --card-dark: rgba(17,25,40,0.78);
    --text-dark: #e5e7eb;
    --muted-dark: #94a3b8;
    --line-dark: rgba(255,255,255,0.08);

    --primary: #4f46e5;
    --primary-2: #06b6d4;
    --success: #16a34a;
    --warn: #d97706;
    --danger: #dc2626;
}

html, body, [class*="css"] {
    font-family: Inter, "Segoe UI", Roboto, Arial, sans-serif;
}

.stApp {
    background:
        radial-gradient(circle at top left, rgba(79,70,229,0.12), transparent 30%),
        radial-gradient(circle at top right, rgba(34,211,238,0.10), transparent 28%),
        var(--bg-light);
    color: var(--text-light);
}

@media (prefers-color-scheme: dark) {
    .stApp {
        background:
            radial-gradient(circle at top left, rgba(79,70,229,0.16), transparent 30%),
            radial-gradient(circle at top right, rgba(34,211,238,0.12), transparent 28%),
            var(--bg-dark);
        color: var(--text-dark);
    }
}

.block-container {
    padding-top: 2rem;
    padding-bottom: 2rem;
    max-width: 1450px;
}

/* Sidebar */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0b2c5f 0%, #0b1530 100%);
    border-right: 1px solid rgba(255,255,255,0.08);
}

[data-testid="stSidebar"] .stMarkdown,
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] p,
[data-testid="stSidebar"] span {
    color: #ffffff !important;
}

[data-testid="stSidebar"] input,
[data-testid="stSidebar"] textarea,
[data-testid="stSidebar"] .stSelectbox div[role="combobox"],
[data-testid="stSidebar"] .stDateInput div[role="combobox"] {
    color: #101828 !important;
    background: #ffffff !important;
    border-radius: 12px !important;
}

[data-testid="stSidebar"] .stButton > button {
    width: 100%;
    border-radius: 14px;
    border: 1px solid rgba(255,255,255,.18);
    background: linear-gradient(135deg, rgba(255,255,255,.18), rgba(255,255,255,.08));
    color: #fff;
    font-weight: 700;
}

/* Heading */
.ews-title {
    font-family: "Space Grotesk", Inter, "Segoe UI", sans-serif;
    font-size: clamp(2rem, 4vw, 3rem);
    font-weight: 800;
    letter-spacing: -0.03em;
    margin: 0;
    color: inherit;
}
.ews-sub {
    color: #667085;
    font-size: 1rem;
    margin-top: .35rem;
}
@media (prefers-color-scheme: dark) {
    .ews-sub {
        color: #94a3b8;
    }
}

/* Cards */
.kpi-card,
.news-card,
.info-card {
    background: var(--card-light);
    backdrop-filter: blur(14px);
    -webkit-backdrop-filter: blur(14px);
    border: 1px solid var(--line-light);
    border-radius: 20px;
    box-shadow: 0 10px 30px rgba(2, 6, 23, 0.08);
}

@media (prefers-color-scheme: dark) {
    .kpi-card,
    .news-card,
    .info-card {
        background: var(--card-dark);
        border: 1px solid var(--line-dark);
        box-shadow: 0 12px 36px rgba(0, 0, 0, 0.35);
    }
}

.kpi-card { padding: 16px 18px; }
.kpi-title {
    font-size: 12px;
    color: #667085;
    margin-bottom: 8px;
    text-transform: uppercase;
    letter-spacing: .04em;
}
.kpi-value {
    font-size: 28px;
    font-weight: 800;
    color: inherit;
    line-height: 1.1;
}
.kpi-sub {
    font-size: 12px;
    color: #667085;
    margin-top: 8px;
}
@media (prefers-color-scheme: dark) {
    .kpi-title, .kpi-sub { color: #94a3b8; }
}

.section-title {
    font-family: "Space Grotesk", Inter, sans-serif;
    font-size: 1.45rem;
    font-weight: 700;
    margin-bottom: .65rem;
}

.news-card {
    padding: 18px 18px 16px 18px;
    margin-bottom: 14px;
}
.news-title {
    font-size: 1rem;
    font-weight: 700;
    line-height: 1.5;
    margin-bottom: 8px;
}
.news-meta {
    font-size: .86rem;
    color: #667085;
    margin-bottom: 10px;
}
.news-chip {
    display: inline-block;
    font-size: .76rem;
    font-weight: 700;
    padding: 5px 10px;
    border-radius: 999px;
    background: rgba(79,70,229,.12);
    color: #4338ca;
    margin-right: 6px;
    margin-bottom: 6px;
}
.news-link a {
    color: #4338ca;
    text-decoration: none;
    font-weight: 700;
}
.news-link a:hover { text-decoration: underline; }

@media (prefers-color-scheme: dark) {
    .news-meta { color: #94a3b8; }
    .news-chip {
        background: rgba(129,140,248,.18);
        color: #c7d2fe;
    }
    .news-link a { color: #a5b4fc; }
}

/* Badge */
.badge {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 6px 12px;
    border-radius: 999px;
    font-size: 12px;
    font-weight: 700;
    color: #fff;
}
.badge-high { background: linear-gradient(135deg, #ef4444, #dc2626); }
.badge-mid { background: linear-gradient(135deg, #f59e0b, #d97706); }
.badge-low { background: linear-gradient(135deg, #22c55e, #16a34a); }

.info-card {
    padding: 18px 20px;
    margin-bottom: 14px;
}
.info-title {
    font-size: 1.05rem;
    font-weight: 800;
    margin-bottom: 10px;
}
.info-text {
    font-size: .96rem;
    line-height: 1.75;
    color: inherit;
}
.info-text ul {
    padding-left: 18px;
    margin-top: 8px;
    margin-bottom: 0;
}
.info-text li { margin-bottom: 6px; }

thead tr th {
    text-align: center !important;
    font-size: 12px !important;
}

@media (max-width: 768px) {
    .block-container {
        padding-top: 1.2rem;
        padding-left: 1rem;
        padding-right: 1rem;
    }
    .kpi-value { font-size: 22px; }
    .news-card { padding: 14px; }
}
</style>
""",
    unsafe_allow_html=True
)

st.markdown(
    """
<div style="margin-bottom:18px;">
  <h1 class="ews-title">Early Warning System</h1>
  <p class="ews-sub">Monitoring Isu Jaminan Sosial Ketenagakerjaan</p>
</div>
""",
    unsafe_allow_html=True
)
st.divider()

# ===============================
# HELPERS
# ===============================
def clean_label(text) -> str:
    return str(text).replace("_", " ").strip()


def safe_clear_caches():
    try:
        st.cache_data.clear()
    except Exception:
        pass
    try:
        read_sheet.clear()
    except Exception:
        pass


def safe_series(df: pd.DataFrame, col: str, default="") -> pd.Series:
    if col in df.columns:
        return df[col].astype(str).fillna(default)
    return pd.Series([default] * len(df), index=df.index)


def badge_html(prioritas: str) -> str:
    if prioritas == "PRIORITAS TINGGI":
        return "<span class='badge badge-high'>Prioritas Tinggi</span>"
    elif prioritas == "PRIORITAS SEDANG":
        return "<span class='badge badge-mid'>Prioritas Sedang</span>"
    return "<span class='badge badge-low'>Prioritas Rendah</span>"


def normalize_datetime_col(df: pd.DataFrame, col: str) -> pd.Series:
    s = pd.to_datetime(df[col], errors="coerce")
    try:
        if getattr(s.dt, "tz", None) is not None:
            s = s.dt.tz_localize(None)
    except Exception:
        pass
    return s


def build_alerts(df: pd.DataFrame) -> list[str]:
    alerts = []
    if df.empty:
        return ["Belum ada isu signifikan pada periode terpilih."]

    df_alert = df.copy()

    if "Prioritas" in df_alert.columns:
        tinggi_count = int((df_alert["Prioritas"] == "PRIORITAS TINGGI").sum())
        if tinggi_count >= 3:
            alerts.append("🚨 Terjadi peningkatan isu prioritas tinggi yang memerlukan perhatian segera.")
        elif tinggi_count > 0:
            alerts.append("🟡 Terdapat isu prioritas tinggi yang perlu dipantau lebih dekat.")

    if "Topik" in df_alert.columns and not df_alert["Topik"].empty:
        topik_counts = df_alert["Topik"].value_counts()
        if not topik_counts.empty and int(topik_counts.iloc[0]) >= 5:
            alerts.append(f"📈 Isu didominasi oleh topik {clean_label(topik_counts.index[0])}.")

    if "Provinsi" in df_alert.columns:
        prov_counts = df_alert["Provinsi"].astype(str).str.strip()
        prov_counts = prov_counts[prov_counts != ""].value_counts()
        if not prov_counts.empty and int(prov_counts.iloc[0]) >= 3:
            alerts.append(f"🌍 Konsentrasi isu terpantau di wilayah {prov_counts.index[0]}.")

    if "Waktu_Publish_WIB" in df_alert.columns:
        try:
            publish_dt = normalize_datetime_col(df_alert, "Waktu_Publish_WIB")
            now = pd.Timestamp.now()
            recent = df_alert[publish_dt >= (now - pd.Timedelta(hours=6))]
            if len(recent) >= 3:
                alerts.append("⏱ Terjadi lonjakan isu dalam 6 jam terakhir.")
        except Exception:
            pass

    return alerts if alerts else ["Belum ada eskalasi signifikan pada periode terpilih."]


@st.cache_data(ttl=300, show_spinner=False)
def load_sheet(key: str, tab: str) -> pd.DataFrame:
    return read_sheet(key, tab)


def ensure_publish_date(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or df.empty:
        return pd.DataFrame()

    if "Tanggal_Publish" in df.columns:
        s = pd.to_datetime(df["Tanggal_Publish"], errors="coerce")
    elif "Waktu_Publish_WIB" in df.columns:
        s = pd.to_datetime(df["Waktu_Publish_WIB"], errors="coerce")
    elif "Tanggal" in df.columns:
        s = pd.to_datetime(df["Tanggal"], errors="coerce", utc=True)
        try:
            s = s.dt.tz_convert("Asia/Jakarta")
        except Exception:
            pass
    elif "Tanggal_Ambil" in df.columns:
        s = pd.to_datetime(df["Tanggal_Ambil"], errors="coerce")
    else:
        s = pd.Series([pd.NaT] * len(df), index=df.index)

    s = pd.to_datetime(s, errors="coerce")
    df = df.copy()
    df["Tanggal_Hari"] = s.dt.date
    df = df.dropna(subset=["Tanggal_Hari"]).copy()
    return df


TOPIC_RULES = {
    "PHK": [
        r"\bphk\b", r"pemutusan hubungan kerja", r"\bdirumahkan\b",
        r"gelombang phk", r"phk massal", r"pengurangan karyawan", r"efisiensi tenaga kerja"
    ],
    "THR / Kesejahteraan Pekerja": [
        r"\bthr\b", r"tunjangan hari raya", r"pengaduan thr", r"posko thr",
        r"thr tidak dibayar", r"thr terlambat", r"thr dicicil", r"thr dipotong"
    ],
    "Upah / Gaji": [
        r"\bupah\b", r"\bgaji\b", r"tunggakan upah", r"gaji tidak dibayar",
        r"ump", r"umk", r"upah minimum"
    ],
    "Aksi / Demo Buruh": [
        r"\bdemo\b", r"unjuk rasa", r"aksi buruh", r"mogok", r"mogok kerja"
    ],
    "Konflik Hubungan Industrial": [
        r"perselisihan", r"konflik buruh", r"sengketa", r"tripartit", r"mediasi hubungan industrial"
    ],
    "Kepesertaan BPJS": [
        r"bpjs ketenagakerjaan", r"bpjamsostek", r"jamsostek",
        r"kepesertaan bpjs", r"terdaftar bpjs", r"peserta bpjs"
    ],
    "Klaim JHT": [
        r"\bjht\b", r"jaminan hari tua", r"klaim jht", r"pencairan jht", r"saldo jht"
    ],
    "Manfaat JKP": [
        r"\bjkp\b", r"jaminan kehilangan pekerjaan", r"manfaat jkp", r"klaim jkp"
    ],
    "Jaminan Pensiun (JP)": [
        r"\bjp\b", r"jaminan pensiun", r"manfaat pensiun", r"iuran pensiun", r"usia pensiun"
    ],
    "Kecelakaan Kerja (JKK)": [
        r"\bjkk\b", r"jaminan kecelakaan kerja", r"kecelakaan kerja",
        r"santunan jkk", r"ledakan pabrik", r"buruh tewas", r"pekerja tewas"
    ],
    "Santunan Kematian (JKM)": [
        r"\bjkm\b", r"jaminan kematian", r"santunan kematian", r"ahli waris", r"meninggal dunia"
    ],
    "Tunggakan Iuran": [
        r"tunggakan iuran", r"menunggak iuran", r"telat bayar iuran", r"denda bpjs"
    ],
    "Pekerja Migran Indonesia (PMI)": [
        r"\bpmi\b", r"pekerja migran", r"tki", r"buruh migran"
    ],
    "Jasa Konstruksi": [
        r"konstruksi", r"proyek", r"pembangunan", r"jasa konstruksi"
    ],
}


def detect_topic(text: str) -> str:
    t = (text or "").lower()
    for topic, patterns in TOPIC_RULES.items():
        for p in patterns:
            if re.search(p, t):
                return topic
    if re.search(r"bpjs|bpjamsostek|jamsostek|klaim|iuran", t):
        return "Kepesertaan BPJS"
    if re.search(r"buruh|pekerja|ketenagakerjaan|tenaga kerja", t):
        return "Konflik Hubungan Industrial"
    return "Kebijakan Ketenagakerjaan"


# ===============================
# LOAD DATA
# ===============================
raw = load_sheet(SHEET_KEY, "RAW")
analyzed = load_sheet(SHEET_KEY, "ANALYZED")

if raw is None:
    raw = pd.DataFrame()
if analyzed is None:
    analyzed = pd.DataFrame()

if not raw.empty:
    raw.columns = raw.columns.astype(str).str.strip()
if not analyzed.empty:
    analyzed.columns = analyzed.columns.astype(str).str.strip()

raw = ensure_publish_date(raw)
analyzed = ensure_publish_date(analyzed)

if raw.empty:
    st.warning("Data RAW belum tersedia. Klik 🔄 Update Data dulu.")
    st.stop()

min_date = raw["Tanggal_Hari"].min()
max_date = raw["Tanggal_Hari"].max()

# ===============================
# KONTROL DATA
# ===============================
st.markdown('<div class="section-title">Kontrol Data</div>', unsafe_allow_html=True)

c_ctrl1, c_ctrl2, c_ctrl3, c_ctrl4 = st.columns([1.1, 2.2, 1.4, 1.4])

with c_ctrl1:
    if st.button("🔄 Update Data", key="update_data_main"):
        with st.spinner("Memproses update..."):
            run_scraper()
            run_filter()
            run_priority()
            safe_clear_caches()
        st.success("Update selesai!")
        st.rerun()

with c_ctrl2:
    date_range = st.date_input(
        "Rentang tanggal",
        value=(min_date, max_date),
        key="main_date_range"
    )

with c_ctrl3:
    filter_option = st.selectbox(
        "Prioritas",
        ["SEMUA", "PRIORITAS TINGGI", "PRIORITAS SEDANG", "PRIORITAS RENDAH"],
        key="main_filter_option"
    )

with c_ctrl4:
    kategori_option = st.selectbox(
        "Kategori Berita",
        ["SEMUA", "NASIONAL", "GLOBAL", "EDUKASI"],
        key="main_kategori_option"
    )

# ===============================
# FILTER DATA
# ===============================
if isinstance(date_range, (list, tuple)) and len(date_range) == 2:
    start_date, end_date = date_range
else:
    start_date, end_date = min_date, max_date

raw_filtered = raw[
    (raw["Tanggal_Hari"] >= start_date) &
    (raw["Tanggal_Hari"] <= end_date)
].copy()

filtered_display = analyzed[
    (analyzed["Tanggal_Hari"] >= start_date) &
    (analyzed["Tanggal_Hari"] <= end_date)
].copy() if not analyzed.empty else pd.DataFrame()

if not filtered_display.empty and kategori_option != "SEMUA" and "Kategori_Berita" in filtered_display.columns:
    filtered_display = filtered_display[
        filtered_display["Kategori_Berita"].astype(str).str.upper().eq(kategori_option)
    ].copy()

if not filtered_display.empty:
    if "Topik_Utama" in filtered_display.columns:
        filtered_display["Topik"] = (
            filtered_display["Topik_Utama"].astype(str).fillna("").replace("", "Lainnya")
        )
    else:
        combo = safe_series(filtered_display, "Judul") + " " + safe_series(filtered_display, "Ringkasan")
        filtered_display["Topik"] = combo.apply(detect_topic)

filtered_for_table = filtered_display.copy()
if not filtered_for_table.empty and filter_option != "SEMUA" and "Prioritas" in filtered_for_table.columns:
    filtered_for_table = filtered_for_table[
        filtered_for_table["Prioritas"].astype(str).eq(filter_option)
    ].copy()

# ===============================
# TABS
# ===============================
tab_dash, tab_data, tab_region, tab_info = st.tabs(
    ["📊 Dashboard", "📰 Data Berita", "📍 Analisis Daerah", "📘 Panduan"]
)

# ===============================
# TAB DASHBOARD
# ===============================
with tab_dash:
    if raw_filtered.empty:
        st.warning("Belum ada data RAW pada rentang tanggal ini.")
        st.stop()

    if filtered_display.empty or "Prioritas" not in filtered_display.columns:
        col_a, col_b = st.columns(2)

        with col_a:
            st.markdown(
                f"""
                <div class="kpi-card">
                  <div class="kpi-title">Total Berita RAW</div>
                  <div class="kpi-value">{len(raw_filtered):,}</div>
                  <div class="kpi-sub">Ada data mentah pada periode ini</div>
                </div>
                """,
                unsafe_allow_html=True
            )

        with col_b:
            st.markdown(
                """
                <div class="kpi-card">
                  <div class="kpi-title">Berita Teranalisis</div>
                  <div class="kpi-value">0</div>
                  <div class="kpi-sub">Belum ada yang lolos analisis</div>
                </div>
                """,
                unsafe_allow_html=True
            )

        st.info("Tidak ada berita yang lolos analisis pada rentang tanggal ini.")
        st.stop()

    tinggi = int((filtered_display["Prioritas"] == "PRIORITAS TINGGI").sum())
    sedang = int((filtered_display["Prioritas"] == "PRIORITAS SEDANG").sum())
    rendah = int((filtered_display["Prioritas"] == "PRIORITAS RENDAH").sum())

    c1, c2, c3, c4, c5 = st.columns([1.2, 1.2, 1, 1, 1], gap="large")

    with c1:
        st.markdown(
            f"""
            <div class="kpi-card">
              <div class="kpi-title">Total Berita RAW</div>
              <div class="kpi-value">{len(raw_filtered):,}</div>
              <div class="kpi-sub">Sesuai rentang tanggal</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with c2:
        st.markdown(
            f"""
            <div class="kpi-card">
              <div class="kpi-title">Berita Teranalisis</div>
              <div class="kpi-value">{len(filtered_display):,}</div>
              <div class="kpi-sub">Basis analisis EWS</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with c3:
        st.markdown(
            f"""
            <div class="kpi-card">
              <div class="kpi-title">Prioritas Tinggi</div>
              <div class="kpi-value">{tinggi:,}</div>
              <div class="kpi-sub"><span class="badge badge-high">HIGH</span></div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with c4:
        st.markdown(
            f"""
            <div class="kpi-card">
              <div class="kpi-title">Prioritas Sedang</div>
              <div class="kpi-value">{sedang:,}</div>
              <div class="kpi-sub"><span class="badge badge-mid">MED</span></div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with c5:
        st.markdown(
            f"""
            <div class="kpi-card">
              <div class="kpi-title">Prioritas Rendah</div>
              <div class="kpi-value">{rendah:,}</div>
              <div class="kpi-sub"><span class="badge badge-low">LOW</span></div>
            </div>
            """,
            unsafe_allow_html=True
        )

    st.markdown("<div style='height:14px;'></div>", unsafe_allow_html=True)

    st.markdown('<div class="section-title">🚨 Isu Paling Kritis Hari Ini</div>', unsafe_allow_html=True)

    df_critical = filtered_display.copy()
    if "Score" in df_critical.columns:
        df_critical["Score_num"] = pd.to_numeric(df_critical["Score"], errors="coerce").fillna(0)
        sort_cols = ["Score_num"]
        ascending = [False]
        if "Waktu_Publish_WIB" in df_critical.columns:
            df_critical["Waktu_Publish_WIB_dt"] = normalize_datetime_col(df_critical, "Waktu_Publish_WIB")
            sort_cols.append("Waktu_Publish_WIB_dt")
            ascending.append(False)
        df_critical = df_critical.sort_values(sort_cols, ascending=ascending)
    elif "Waktu_Publish_WIB" in df_critical.columns:
        df_critical["Waktu_Publish_WIB_dt"] = normalize_datetime_col(df_critical, "Waktu_Publish_WIB")
        df_critical = df_critical.sort_values("Waktu_Publish_WIB_dt", ascending=False)

    if not df_critical.empty:
        top_issue = df_critical.iloc[0]
        judul = escape(str(top_issue.get("Judul", "-")))
        topik = escape(clean_label(top_issue.get("Topik_Utama", "-")))
        kategori = escape(clean_label(top_issue.get("Kategori_Berita", "-")))
        lokasi = escape(clean_label(
            str(top_issue.get("Kabupaten_Kota", "") or "").strip() or str(top_issue.get("Provinsi", "") or "").strip() or "-"
        ))
        dampak = escape(clean_label(top_issue.get("Dampak_Program", "-")))
        alasan = escape(clean_label(top_issue.get("Alasan_Prioritas", "-")))
        prioritas = str(top_issue.get("Prioritas", "PRIORITAS RENDAH")).strip()

        st.markdown(
            f"""
            <div class="news-card">
                <div style="display:flex; justify-content:space-between; gap:12px; flex-wrap:wrap; align-items:flex-start;">
                    <div style="flex:1; min-width:280px;">
                        <div class="news-title">{judul}</div>
                        <div class="news-meta">{lokasi} • {kategori} • {topik}</div>
                    </div>
                    <div>{badge_html(prioritas)}</div>
                </div>
                <div style="margin-top:6px;">
                    <span class='news-chip'>Dampak: {dampak}</span>
                </div>
                <div style="font-size:.96rem; line-height:1.7; margin-top:10px;">
                    {alasan}
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

    left, right = st.columns([1.05, 0.95], gap="large")

    with left:
        st.markdown('<div class="section-title">Distribusi Prioritas</div>', unsafe_allow_html=True)

        priority_counts = filtered_display["Prioritas"].value_counts()
        if not priority_counts.empty:
            order = ["PRIORITAS TINGGI", "PRIORITAS SEDANG", "PRIORITAS RENDAH"]
            label_map = {
                "PRIORITAS TINGGI": "Prioritas Tinggi",
                "PRIORITAS SEDANG": "Prioritas Sedang",
                "PRIORITAS RENDAH": "Prioritas Rendah"
            }
            color_map = {
                "PRIORITAS TINGGI": "#ef4444",
                "PRIORITAS SEDANG": "#f59e0b",
                "PRIORITAS RENDAH": "#22c55e"
            }

            priority_counts = priority_counts.reindex(order).fillna(0).astype(int)
            x_vals = priority_counts.tolist()
            y_vals = [label_map[x] for x in priority_counts.index]
            colors = [color_map[x] for x in priority_counts.index]
            max_val = max(x_vals) if max(x_vals) > 0 else 1

            fig = go.Figure()
            fig.add_trace(
                go.Bar(
                    x=x_vals,
                    y=y_vals,
                    orientation="h",
                    marker=dict(color=colors, line=dict(width=0)),
                    text=[f"{v:,}" for v in x_vals],
                    textposition="outside",
                    cliponaxis=False,
                    hovertemplate="<b>%{y}</b><br>Jumlah berita: %{x}<extra></extra>"
                )
            )

            fig.update_layout(
                height=300,
                margin=dict(l=10, r=45, t=6, b=20),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                showlegend=False,
                xaxis=dict(
                    title="Jumlah Berita",
                    showgrid=True,
                    gridcolor="rgba(148, 163, 184, 0.20)",
                    zeroline=False,
                    showline=False,
                    range=[0, max_val * 1.18]
                ),
                yaxis=dict(
                    title="",
                    autorange="reversed",
                    showgrid=False
                ),
                font=dict(size=13)
            )

            st.plotly_chart(
                fig,
                use_container_width=True,
                config={"displayModeBar": False, "responsive": True}
            )

        st.markdown("<div style='height:12px;'></div>", unsafe_allow_html=True)

        st.markdown('<div class="section-title">Topik Dominan</div>', unsafe_allow_html=True)
        topik_counts = filtered_display["Topik"].value_counts().head(5)

        if not topik_counts.empty:
            fig_topik = go.Figure()
            fig_topik.add_trace(
                go.Bar(
                    x=topik_counts.values.tolist(),
                    y=[clean_label(x) for x in topik_counts.index.tolist()],
                    orientation="h",
                    text=[f"{v:,}" for v in topik_counts.values.tolist()],
                    textposition="outside",
                    marker=dict(color="#4f46e5")
                )
            )
            fig_topik.update_layout(
                height=320,
                margin=dict(l=10, r=45, t=6, b=20),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                showlegend=False,
                yaxis=dict(autorange="reversed", title=""),
                xaxis=dict(title="Jumlah Berita", showgrid=True, gridcolor="rgba(148,163,184,0.20)")
            )
            st.plotly_chart(fig_topik, use_container_width=True, config={"displayModeBar": False})

        st.markdown("<div style='height:12px;'></div>", unsafe_allow_html=True)
        st.markdown('<div class="section-title">Top 5 Berita Prioritas Tinggi</div>', unsafe_allow_html=True)

        df_high = filtered_display[filtered_display["Prioritas"] == "PRIORITAS TINGGI"].copy()

        if not df_high.empty:
            if "Waktu_Publish_WIB" in df_high.columns:
                df_high["Waktu_Publish_WIB_dt"] = normalize_datetime_col(df_high, "Waktu_Publish_WIB")
                df_high = df_high.sort_values("Waktu_Publish_WIB_dt", ascending=False)

            top5 = df_high.head(5)

            for _, row in top5.iterrows():
                media = escape(str(row.get("Media", "-")))
                judul = escape(str(row.get("Judul", "-")))
                link = str(row.get("Link", "")).strip()
                waktu = escape(str(row.get("Waktu_Publish_WIB", "")))
                lokasi = escape(clean_label(
                    str(row.get("Kabupaten_Kota", "") or "").strip() or str(row.get("Provinsi", "") or "").strip() or "-"
                ))
                kategori = escape(clean_label(row.get("Kategori_Berita", "-")))

                if link:
                    st.markdown(
                        f"""
                        <div class="news-card">
                            <div class="news-link">
                                <a href="{escape(link, quote=True)}" target="_blank">{judul}</a>
                            </div>
                            <div class="news-meta">{media} • {waktu} • {lokasi} • {kategori}</div>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
                else:
                    st.markdown(
                        f"""
                        <div class="news-card">
                            <div class="news-title">{judul}</div>
                            <div class="news-meta">{media} • {waktu} • {lokasi} • {kategori}</div>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )

    with right:
        st.markdown('<div class="section-title">🧠 Analisis Situasi</div>', unsafe_allow_html=True)

        if tinggi > 3:
            status_txt = "🔴 RISIKO TINGGI"
            kondisi = "Isu ketenagakerjaan meningkat dan perlu perhatian segera."
            rekomendasi = "Perlu pemantauan intensif dan koordinasi lintas unit terhadap isu prioritas."
        elif tinggi > 0:
            status_txt = "🟡 WASPADA"
            kondisi = "Terdapat isu prioritas yang perlu dipantau lebih dekat."
            rekomendasi = "Perlu klarifikasi lapangan dan pemantauan berkala terhadap isu yang berkembang."
        else:
            status_txt = "🟢 STABIL"
            kondisi = "Belum terlihat eskalasi signifikan pada periode ini."
            rekomendasi = "Pemantauan rutin tetap diperlukan sebagai langkah preventif."

        topik_counts = filtered_display["Topik"].value_counts()
        top3 = topik_counts.head(3)
        topik_list = [f"- **{clean_label(topic)}** ({count} berita)" for topic, count in top3.items()]
        topik_text = "\n".join(topik_list) if topik_list else "- **Belum ada topik dominan**"

        alerts = build_alerts(filtered_display)

        st.markdown(
            f"""
            <div class="info-card">
                <div class="info-title">{status_txt}</div>
                <div class="info-text">
                    <p>{kondisi}</p>
                    <p><strong>Topik dominan:</strong></p>
                    <div>{topik_text}</div>
                    <p style="margin-top:10px;"><strong>Ringkasan kondisi:</strong></p>
                    <ul>
                        {''.join([f"<li>{escape(a)}</li>" for a in alerts])}
                    </ul>
                    <p style="margin-top:10px;"><strong>Rekomendasi:</strong> {rekomendasi}</p>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

# ===============================
# TAB DATA BERITA
# ===============================
with tab_data:
    st.markdown('<div class="section-title">Data Berita</div>', unsafe_allow_html=True)

    if filtered_for_table.empty:
        st.info("Tidak ada berita untuk filter yang dipilih.")
    else:
        show_cols = [
            c for c in [
                "Media", "Judul", "Waktu_Publish_WIB", "Kategori_Berita",
                "Topik_Utama", "Provinsi", "Prioritas", "Score", "Link"
            ] if c in filtered_for_table.columns
        ]

        st.dataframe(
            filtered_for_table[show_cols],
            use_container_width=True,
            hide_index=True
        )

# ===============================
# TAB ANALISIS DAERAH
# ===============================
with tab_region:
    st.markdown('<div class="section-title">Analisis Daerah</div>', unsafe_allow_html=True)

    if filtered_display.empty or "Provinsi" not in filtered_display.columns:
        st.info("Belum ada data analisis daerah.")
    else:
        region_df = filtered_display.copy()
        region_df["Provinsi"] = region_df["Provinsi"].astype(str).str.strip()
        region_df = region_df[region_df["Provinsi"] != ""]

        if region_df.empty:
            st.info("Belum ada wilayah yang teridentifikasi.")
        else:
            region_counts = region_df["Provinsi"].value_counts().head(10)

            fig_region = go.Figure()
            fig_region.add_trace(
                go.Bar(
                    x=region_counts.values.tolist(),
                    y=region_counts.index.tolist(),
                    orientation="h",
                    text=[f"{v:,}" for v in region_counts.values.tolist()],
                    textposition="outside",
                    marker=dict(color="#06b6d4")
                )
            )
            fig_region.update_layout(
                height=420,
                margin=dict(l=10, r=45, t=6, b=20),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                showlegend=False,
                yaxis=dict(autorange="reversed", title=""),
                xaxis=dict(title="Jumlah Berita", showgrid=True, gridcolor="rgba(148,163,184,0.20)")
            )
            st.plotly_chart(fig_region, use_container_width=True, config={"displayModeBar": False})

            st.dataframe(
                region_counts.rename_axis("Provinsi").reset_index(name="Jumlah Berita"),
                use_container_width=True,
                hide_index=True
            )

# ===============================
# TAB PANDUAN
# ===============================
with tab_info:
    st.markdown('<div class="section-title">Panduan Membaca Dashboard</div>', unsafe_allow_html=True)
    st.markdown(
        """
<div class="info-card">
    <div class="info-title">Alur Sistem</div>
    <div class="info-text">
        <ul>
            <li><strong>RAW</strong>: seluruh berita hasil scraping dari berbagai sumber RSS dan Google News.</li>
            <li><strong>FILTERED</strong>: berita yang lolos kata kunci isu ketenagakerjaan/jamsos.</li>
            <li><strong>ANALYZED</strong>: berita yang telah dianalisis topik, lokasi, dampak program, dan prioritas.</li>
        </ul>
    </div>
</div>

<div class="info-card">
    <div class="info-title">Cara Sistem Menentukan Prioritas</div>
    <div class="info-text">
        <ul>
            <li><strong>Prioritas Tinggi</strong>: isu berdampak besar seperti PHK, kecelakaan kerja fatal, konflik industrial besar, atau isu strategis yang masih baru.</li>
            <li><strong>Prioritas Sedang</strong>: isu cukup relevan dan perlu dipantau, tetapi skala/dampaknya belum setinggi prioritas tinggi.</li>
            <li><strong>Prioritas Rendah</strong>: berita edukasi layanan, isu ringan, atau referensi global.</li>
        </ul>
    </div>
</div>

<div class="info-card">
    <div class="info-title">Catatan Penting</div>
    <div class="info-text">
        Bila pada suatu tanggal <strong>RAW ada tetapi ANALYZED kosong</strong>, berarti ada berita mentah namun tidak ada yang lolos analisis akhir pada tanggal tersebut.
    </div>
</div>
""",
        unsafe_allow_html=True
    )