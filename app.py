import re
from html import escape

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from scraper import run_scraper
from filter_keyword import run_filter
from update_priority import run_priority
from gsheet_utils import read_sheet

SHEET_KEY = st.secrets["SHEET_KEY"]

# ===============================
# PAGE CONFIG
# ===============================
st.set_page_config(
    page_title="SIAGA JAMSOS",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ===============================
# STYLE — ULTRA POLISHED
# ===============================
st.markdown(
    """
<style>
header[data-testid="stHeader"] { display: none; }
div[data-testid="stToolbar"] { display: none; }
#MainMenu { visibility: hidden; }
footer { visibility: hidden; }

:root{
    --bg:#f3f6fb;
    --bg-soft:#eef3f9;
    --surface:#ffffff;
    --surface-2:#f8fbff;
    --line:#dbe5f0;
    --line-2:#e7eef6;

    --text:#0f172a;
    --muted:#64748b;
    --muted-2:#94a3b8;

    --navy:#0b1f3a;
    --navy-2:#12345b;
    --blue:#1d4ed8;
    --cyan:#0891b2;

    --red:#dc2626;
    --amber:#d97706;
    --green:#16a34a;

    --shadow-sm:0 8px 24px rgba(15, 23, 42, 0.05);
    --shadow-md:0 16px 36px rgba(15, 23, 42, 0.08);
    --radius-lg:22px;
    --radius-md:18px;
    --radius-sm:14px;
}

html, body, [class*="css"] {
    font-family: "Inter", "Segoe UI", Arial, sans-serif;
    color: var(--text);
}

.stApp {
    background:
        radial-gradient(circle at top left, rgba(29,78,216,0.08), transparent 28%),
        radial-gradient(circle at top right, rgba(8,145,178,0.08), transparent 24%),
        linear-gradient(180deg, var(--bg) 0%, var(--bg-soft) 100%);
}

.block-container {
    max-width: 1460px;
    padding-top: 1.1rem;
    padding-bottom: 2rem;
}

/* Sidebar */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0b1f3a 0%, #102b4b 100%);
    border-right: 1px solid rgba(255,255,255,0.06);
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
    background: #ffffff !important;
    color: #0f172a !important;
    border-radius: 12px !important;
}
[data-testid="stSidebar"] .stButton > button {
    width: 100%;
    border-radius: 14px;
    border: 1px solid rgba(255,255,255,0.14);
    background: linear-gradient(135deg, rgba(255,255,255,0.16), rgba(255,255,255,0.08));
    color: #ffffff;
    font-weight: 700;
}

/* Hero */
.hero-shell {
    background: linear-gradient(135deg, #0b1f3a 0%, #14385f 62%, #195b88 100%);
    border-radius: 28px;
    padding: 26px 26px 22px 26px;
    color: #ffffff;
    box-shadow: 0 18px 44px rgba(11, 31, 58, 0.18);
    margin-bottom: 18px;
    position: relative;
    overflow: hidden;
}
.hero-shell::after {
    content: "";
    position: absolute;
    right: -40px;
    top: -40px;
    width: 180px;
    height: 180px;
    border-radius: 50%;
    background: radial-gradient(circle, rgba(255,255,255,0.14), transparent 65%);
}
.hero-badge {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    padding: 7px 12px;
    border-radius: 999px;
    background: rgba(255,255,255,0.12);
    border: 1px solid rgba(255,255,255,0.14);
    font-size: 12px;
    font-weight: 700;
    margin-bottom: 14px;
}
.hero-title {
    font-size: clamp(1.9rem, 3.6vw, 2.8rem);
    font-weight: 800;
    line-height: 1.12;
    letter-spacing: -0.03em;
    margin: 0;
}
.hero-sub {
    margin-top: 10px;
    font-size: 14px;
    line-height: 1.75;
    color: rgba(255,255,255,0.92);
    max-width: 880px;
}
.hero-meta {
    margin-top: 14px;
    font-size: 12px;
    color: rgba(255,255,255,0.82);
}

/* Section titles */
.section-title {
    font-size: 1.22rem;
    font-weight: 800;
    color: var(--text);
    margin-bottom: 10px;
}
.section-sub {
    font-size: 13px;
    color: var(--muted);
    margin-top: -2px;
    margin-bottom: 12px;
}

/* Universal cards */
.glass-card,
.kpi-card,
.panel-card,
.news-card,
.info-card {
    background: rgba(255,255,255,0.92);
    border: 1px solid var(--line-2);
    border-radius: var(--radius-md);
    box-shadow: var(--shadow-sm);
}

.panel-card,
.info-card,
.news-card {
    padding: 18px 18px 16px 18px;
}

.glass-card {
    padding: 16px 18px;
}

.kpi-card {
    padding: 16px 18px 14px 18px;
    min-height: 118px;
    position: relative;
    overflow: hidden;
}
.kpi-card::before {
    content: "";
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 4px;
    background: linear-gradient(90deg, #1d4ed8, #0891b2);
}
.kpi-card.high::before { background: linear-gradient(90deg, #ef4444, #dc2626); }
.kpi-card.mid::before { background: linear-gradient(90deg, #f59e0b, #d97706); }
.kpi-card.low::before { background: linear-gradient(90deg, #22c55e, #16a34a); }

.kpi-label {
    font-size: 12px;
    color: var(--muted);
    text-transform: uppercase;
    letter-spacing: 0.05em;
    margin-bottom: 10px;
    font-weight: 700;
}
.kpi-value {
    font-size: 30px;
    line-height: 1.05;
    font-weight: 800;
    color: var(--text);
}
.kpi-sub {
    margin-top: 8px;
    font-size: 12px;
    color: var(--muted);
}

/* Tabs */
.stTabs [data-baseweb="tab-list"] {
    gap: 10px;
    margin-bottom: 12px;
}
button[data-baseweb="tab"] {
    border-radius: 999px !important;
    padding: 10px 16px !important;
    background: rgba(255,255,255,0.82) !important;
    border: 1px solid var(--line-2) !important;
    color: #334155 !important;
    font-weight: 700 !important;
}
button[data-baseweb="tab"][aria-selected="true"] {
    background: linear-gradient(135deg, #0b1f3a, #14385f) !important;
    color: #ffffff !important;
    border: 1px solid rgba(11,31,58,0.15) !important;
    box-shadow: var(--shadow-sm);
}

/* Inputs */
div[data-testid="stTextInput"] > div > div,
div[data-testid="stSelectbox"] > div > div,
div[data-testid="stDateInput"] > div > div {
    border-radius: 14px !important;
}

/* Buttons */
.stButton > button {
    border-radius: 12px !important;
    font-weight: 700 !important;
}

/* Badges */
.badge {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 6px 12px;
    border-radius: 999px;
    font-size: 12px;
    font-weight: 800;
    color: #ffffff;
}
.badge-high { background: linear-gradient(135deg, #ef4444, #dc2626); }
.badge-mid  { background: linear-gradient(135deg, #f59e0b, #d97706); }
.badge-low  { background: linear-gradient(135deg, #22c55e, #16a34a); }

.pill {
    display: inline-block;
    padding: 5px 10px;
    border-radius: 999px;
    font-size: 11px;
    font-weight: 700;
    border: 1px solid transparent;
    margin-right: 6px;
    margin-bottom: 6px;
}
.pill-blue {
    background: #eff6ff;
    color: #1d4ed8;
    border-color: #bfdbfe;
}
.pill-soft {
    background: #f8fafc;
    color: #475569;
    border-color: #e2e8f0;
}

/* News cards */
.news-title {
    font-size: 1rem;
    font-weight: 800;
    line-height: 1.55;
    color: var(--text);
    margin-bottom: 6px;
}
.news-title a {
    color: var(--text);
    text-decoration: none;
}
.news-title a:hover {
    color: var(--blue);
    text-decoration: none;
}
.news-meta {
    font-size: 12px;
    color: var(--muted);
    margin-bottom: 10px;
}
.news-body {
    font-size: 14px;
    line-height: 1.72;
    color: #334155;
}
.news-link a {
    color: var(--blue);
    text-decoration: none;
    font-weight: 700;
}
.news-link a:hover {
    text-decoration: underline;
}

/* Table/editor polish */
thead tr th {
    text-align: center !important;
    font-size: 12px !important;
}
table { -webkit-tap-highlight-color: transparent; }

/* Mobile */
@media (max-width: 768px) {
    .block-container {
        padding-top: 0.9rem;
        padding-left: 0.9rem;
        padding-right: 0.9rem;
    }
    .hero-shell {
        padding: 18px 16px 16px 16px;
        border-radius: 22px;
    }
    .hero-title {
        font-size: 1.7rem;
    }
    .hero-sub {
        font-size: 13px;
        line-height: 1.65;
    }
    .kpi-value {
        font-size: 24px;
    }
    .panel-card,
    .info-card,
    .news-card,
    .glass-card,
    .kpi-card {
        border-radius: 16px;
    }
}
</style>
""",
    unsafe_allow_html=True
)

# ===============================
# HERO
# ===============================
st.markdown(
    """
    <div class="hero-shell">
        <div class="hero-badge">🛡️ SIAGA JAMSOS • Early Warning System</div>
        <div class="hero-title">Monitoring Isu Ketenagakerjaan & Jaminan Sosial</div>
        <div class="hero-sub">
            Dashboard pemantauan isu berbasis media online untuk mendukung deteksi dini,
            analisis situasi, dan pengambilan keputusan yang lebih cepat, terukur, dan fokus pada prioritas.
        </div>
        <div class="hero-meta">
            Tampilan ini hanya mengubah layer visual aplikasi. Pipeline backend tetap sama.
        </div>
    </div>
    """,
    unsafe_allow_html=True
)

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

def kpi_card(title: str, value, sub: str = "", tone: str = ""):
    tone_class = tone if tone in ["high", "mid", "low"] else ""
    st.markdown(
        f"""
        <div class="kpi-card {tone_class}">
            <div class="kpi-label">{escape(str(title))}</div>
            <div class="kpi-value">{escape(str(value))}</div>
            <div class="kpi-sub">{escape(str(sub))}</div>
        </div>
        """,
        unsafe_allow_html=True
    )

def section_header(title: str, subtitle: str = ""):
    st.markdown(f'<div class="section-title">{escape(title)}</div>', unsafe_allow_html=True)
    if subtitle:
        st.markdown(f'<div class="section-sub">{escape(subtitle)}</div>', unsafe_allow_html=True)

def guide_card(title: str, content: str):
    st.markdown(
        f"""
        <div class="info-card">
            <div style="font-size:1rem; font-weight:800; margin-bottom:8px; color:#0f172a;">
                {escape(title)}
            </div>
            <div style="font-size:14px; line-height:1.75; color:#334155;">
                {content}
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

# ===============================
# LOAD DATA
# ===============================
@st.cache_data(ttl=300, show_spinner=False)
def load_sheet(key: str, tab: str) -> pd.DataFrame:
    return read_sheet(key, tab)

raw = load_sheet(SHEET_KEY, "RAW")
analyzed = load_sheet(SHEET_KEY, "ANALYZED")

if raw is None or raw.empty:
    st.warning("Data RAW belum tersedia.")
    st.stop()

if analyzed is None:
    analyzed = pd.DataFrame()

raw.columns = raw.columns.astype(str).str.strip()
if not analyzed.empty:
    analyzed.columns = analyzed.columns.astype(str).str.strip()

# ===============================
# FIX TANGGAL
# ===============================
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

raw = ensure_publish_date(raw)
analyzed = ensure_publish_date(analyzed)

if raw.empty:
    st.warning("Data RAW belum tersedia.")
    st.stop()

min_date = raw["Tanggal_Hari"].min()
max_date = raw["Tanggal_Hari"].max()

# ===============================
# KONTROL DATA — ULTRA POLISHED
# ===============================
section_header(
    "Kontrol Data",
    "Atur pembaruan data, rentang waktu analisis, tingkat prioritas, dan kategori berita."
)

st.markdown('<div class="glass-card">', unsafe_allow_html=True)

c_ctrl1, c_ctrl2, c_ctrl3, c_ctrl4 = st.columns([1.1, 2.2, 1.3, 1.3], gap="medium")

with c_ctrl1:
    st.markdown("<div style='font-size:12px; color:#64748b; font-weight:700; margin-bottom:8px;'>Aksi Sistem</div>", unsafe_allow_html=True)
    if st.button("🔄 Update Data", key="update_data_main", use_container_width=True):
        with st.spinner("Memproses update..."):
            run_scraper()
            run_filter()
            run_priority()
            safe_clear_caches()
        st.success("Update selesai.")
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

st.markdown(
    f"""
    <div style="margin-top:10px; font-size:12px; color:#64748b;">
        Periode data tersedia: <b>{escape(str(min_date))}</b> s.d. <b>{escape(str(max_date))}</b>
    </div>
    """,
    unsafe_allow_html=True
)

st.markdown('</div>', unsafe_allow_html=True)

# ===============================
# TOPIC FALLBACK
# ===============================
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
# APPLY DATE FILTER
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
    ["📊 Dashboard Utama", "📰 Data Berita", "📍 Analisis Wilayah", "📘 Panduan"]
)

# ===============================
# TAB: DASHBOARD
# ===============================
with tab_dash:
    if raw_filtered.empty:
        st.warning("Belum ada data RAW pada rentang tanggal ini.")
        st.stop()

    if filtered_display.empty or "Prioritas" not in filtered_display.columns:
        section_header(
            "Ringkasan Utama",
            "Gambaran cepat kondisi isu pada periode yang dipilih."
        )
        c1, c2 = st.columns([1.2, 1.2], gap="medium")
        with c1:
            kpi_card("Total Berita Raw", f"{len(raw_filtered):,}", "Sesuai rentang tanggal")
        with c2:
            kpi_card("Berita Teranalisis", "0", "Belum ada yang lolos analisis")

        st.info("Tidak ada berita yang lolos analisis pada rentang tanggal ini.")
        st.stop()

    tinggi = int((filtered_display["Prioritas"] == "PRIORITAS TINGGI").sum())
    sedang = int((filtered_display["Prioritas"] == "PRIORITAS SEDANG").sum())
    rendah = int((filtered_display["Prioritas"] == "PRIORITAS RENDAH").sum())

    kategori_nasional = int((safe_series(filtered_display, "Kategori_Berita").str.upper() == "NASIONAL").sum())
    kategori_global = int((safe_series(filtered_display, "Kategori_Berita").str.upper() == "GLOBAL").sum())
    kategori_edukasi = int((safe_series(filtered_display, "Kategori_Berita").str.upper() == "EDUKASI").sum())

    section_header(
        "Ringkasan Utama",
        "Gambaran cepat kondisi isu pada periode yang dipilih."
    )

    c1, c2, c3, c4, c5 = st.columns([1.25, 1.25, 1, 1, 1], gap="medium")

    with c1:
        kpi_card("Total Berita Raw", f"{len(raw_filtered):,}", "Sesuai rentang tanggal")
    with c2:
        kpi_card("Berita Teranalisis", f"{len(filtered_display):,}", "Basis analisis SIAGA JAMSOS")
    with c3:
        kpi_card("Prioritas Tinggi", f"{tinggi:,}", "Perlu perhatian segera", "high")
    with c4:
        kpi_card("Prioritas Sedang", f"{sedang:,}", "Perlu pemantauan", "mid")
    with c5:
        kpi_card("Prioritas Rendah", f"{rendah:,}", "Informasi umum", "low")

    st.markdown("<div style='height:14px;'></div>", unsafe_allow_html=True)

    section_header(
        "Isu Paling Kritis Hari Ini",
        "Berita dengan urgensi tertinggi berdasarkan skor, waktu publikasi, dan konteks analisis."
    )

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
            str(top_issue.get("Kabupaten_Kota", "") or "").strip() or
            str(top_issue.get("Provinsi", "") or "").strip() or "-"
        ))
        dampak = escape(clean_label(top_issue.get("Dampak_Program", "-")))
        alasan = escape(clean_label(top_issue.get("Alasan_Prioritas", "-")))
        prioritas = str(top_issue.get("Prioritas", "PRIORITAS RENDAH")).strip()
        media = escape(str(top_issue.get("Media", "-")))
        link = str(top_issue.get("Link", "")).strip()
        waktu = escape(str(top_issue.get("Waktu_Publish_WIB", "")))

        if prioritas == "PRIORITAS TINGGI":
            badge = "<span class='badge badge-high'>Prioritas Tinggi</span>"
        elif prioritas == "PRIORITAS SEDANG":
            badge = "<span class='badge badge-mid'>Prioritas Sedang</span>"
        else:
            badge = "<span class='badge badge-low'>Prioritas Rendah</span>"

        title_html = judul
        if link:
            title_html = f"<a href='{escape(link, quote=True)}' target='_blank'>{judul}</a>"

        st.markdown(
            f"""
            <div class="panel-card">
                <div style="display:flex; justify-content:space-between; gap:14px; flex-wrap:wrap; align-items:flex-start;">
                    <div style="flex:1; min-width:280px;">
                        <div class="news-title">{title_html}</div>
                        <div class="news-meta">{media} • {waktu}</div>
                    </div>
                    <div>{badge}</div>
                </div>

                <div style="margin:4px 0 10px 0;">
                    <span class="pill pill-blue">{kategori}</span>
                    <span class="pill pill-soft">{lokasi}</span>
                    <span class="pill pill-soft">Topik: {topik}</span>
                    <span class="pill pill-soft">Dampak: {dampak}</span>
                </div>

                <div class="news-body">
                    {alasan}
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

    st.markdown("<div style='height:6px;'></div>", unsafe_allow_html=True)
    left, right = st.columns([1.08, 0.92], gap="medium")

    with left:
        section_header("Distribusi Prioritas", "Perbandingan jumlah berita berdasarkan level prioritas.")
        st.markdown('<div class="panel-card">', unsafe_allow_html=True)

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
        else:
            st.info("Belum ada data distribusi prioritas.")

        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown("<div style='height:10px;'></div>", unsafe_allow_html=True)
        section_header("Topik Dominan", "Lima topik yang paling sering muncul pada periode terpilih.")
        st.markdown('<div class="panel-card">', unsafe_allow_html=True)

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
                    marker=dict(color="#1d4ed8")
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
        else:
            st.info("Belum ada topik dominan.")

        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown("<div style='height:10px;'></div>", unsafe_allow_html=True)
        section_header("Top 5 Berita Prioritas Tinggi", "Berita prioritas tinggi terbaru untuk perhatian cepat.")

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
                            <div class="news-title">
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
        else:
            st.info("Belum ada berita prioritas tinggi.")

    with right:
        section_header("Analisis Situasi", "Ringkasan kondisi isu dan implikasi umum terhadap program.")

        total = len(filtered_display)

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

        if "Topik" in filtered_display.columns and not filtered_display.empty:
            topik_counts = filtered_display["Topik"].value_counts()
            top3 = topik_counts.head(3)
            topik_list = [f"- **{clean_label(topic)}** ({count} berita)" for topic, count in top3.items()]
            topik_text = "\n".join(topik_list)
            topik_utama = top3.index.tolist()
        else:
            topik_text = "- **Belum ada topik dominan**"
            topik_utama = []

        ringkasan_utama = []
        dampak_utama = []

        if "PHK" in topik_utama:
            ringkasan_utama.append("PHK menjadi isu utama dan berpotensi meningkatkan klaim **JKP** serta pencairan **JHT**.")
            dampak_utama.append("Kondisi ini juga dapat mempengaruhi kepesertaan aktif pekerja penerima upah (**PU**).")

        if "THR / Kesejahteraan Pekerja" in topik_utama:
            ringkasan_utama.append("Permasalahan **THR** menunjukkan potensi persoalan kepatuhan perusahaan terhadap hak normatif pekerja.")
            dampak_utama.append("Isu ini dapat memicu pengaduan dan perselisihan hubungan industrial.")

        if "Kepesertaan BPJS" in topik_utama:
            ringkasan_utama.append("Isu **kepesertaan BPJS Ketenagakerjaan** berkaitan langsung dengan cakupan perlindungan tenaga kerja.")
            dampak_utama.append("Hal ini perlu dicermati dari sisi perluasan kepesertaan dan kepatuhan pemberi kerja.")

        if "Kecelakaan Kerja (JKK)" in topik_utama:
            ringkasan_utama.append("Isu **kecelakaan kerja** berpotensi meningkatkan klaim **JKK**.")
            dampak_utama.append("Pada kasus fatal, isu ini juga dapat berkembang menjadi klaim **JKM**.")

        if "Konflik Hubungan Industrial" in topik_utama or "Aksi / Demo Buruh" in topik_utama:
            ringkasan_utama.append("Konflik hubungan industrial dan aksi buruh perlu dipantau karena dapat berkembang menjadi gangguan yang lebih besar.")
            dampak_utama.append("Jika berlanjut, kondisi ini dapat mempengaruhi stabilitas hubungan kerja dan kepatuhan perlindungan sosial.")

        if not ringkasan_utama:
            ringkasan_utama.append("Perkembangan isu masih bersifat campuran dan tetap perlu dipantau.")
        if not dampak_utama:
            dampak_utama.append("Secara umum, isu media dapat mempengaruhi kepesertaan, kepatuhan, dan potensi klaim manfaat.")

        st.markdown(
            f"""
<div class="panel-card analysis-body">

**Status:** {status_txt}

Total isu teranalisis: **{total:,} berita**

Prioritas tinggi: **{tinggi:,}**  
Prioritas sedang: **{sedang:,}**  
Prioritas rendah: **{rendah:,}**

Komposisi kategori:
- **Nasional:** {kategori_nasional:,}
- **Global:** {kategori_global:,}
- **Edukasi:** {kategori_edukasi:,}

Topik dominan pada periode ini:

{topik_text}

**Kesimpulan:** {kondisi}

{" ".join(ringkasan_utama[:2])}

{" ".join(dampak_utama[:2])}

**Rekomendasi:** {rekomendasi}
</div>
""",
            unsafe_allow_html=True
        )

        st.markdown("<div style='height:10px;'></div>", unsafe_allow_html=True)
        section_header("Alert Eskalasi", "Sinyal awal yang perlu dipantau lebih dekat.")

        alerts = build_alerts(filtered_display)
        for msg in alerts:
            st.markdown(
                f"""
                <div class="news-card">
                    <div class="news-title">{escape(msg)}</div>
                </div>
                """,
                unsafe_allow_html=True
            )

# ===============================
# TAB: DATA BERITA
# ===============================
with tab_data:
    section_header(
        "Data Berita",
        "Daftar berita hasil analisis yang dapat ditelusuri berdasarkan kata kunci, prioritas, dan waktu publikasi."
    )

    st.markdown('<div class="glass-card">', unsafe_allow_html=True)

    st.markdown(
        """
        <div style="font-size:12px; color:#64748b; font-weight:700; margin-bottom:8px;">
            Pencarian Berita
        </div>
        """,
        unsafe_allow_html=True
    )

    search_keyword = st.text_input(
        "",
        placeholder="Cari berita dengan satu atau beberapa kata kunci, misalnya: PHK Bekasi, JKP, BPJS, JKK",
        key="search_berita"
    )

    st.markdown(
        """
        <div style="font-size:12px; color:#64748b; margin-top:2px;">
            Hasil ditampilkan berdasarkan prioritas tertinggi terlebih dahulu, lalu diurutkan menurut waktu publikasi terbaru.
        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("<div style='height:10px;'></div>", unsafe_allow_html=True)

    df_display = filtered_for_table.copy()

    if search_keyword:
        keywords = [k.strip().lower() for k in str(search_keyword).split() if k.strip()]

        search_parts = []
        for col in ["Judul", "Ringkasan", "Media", "Topik_Utama", "Provinsi", "Kabupaten_Kota"]:
            if col in df_display.columns:
                search_parts.append(df_display[col].astype(str).fillna("").str.lower())

        if search_parts:
            combined_text = search_parts[0]
            for s in search_parts[1:]:
                combined_text = combined_text + " " + s

            mask = pd.Series(True, index=df_display.index)
            for kw in keywords:
                mask = mask & combined_text.str.contains(kw, na=False, regex=False)

            df_display = df_display[mask].copy()

        if st.session_state.get("search_berita_prev", "") != search_keyword:
            st.session_state.page = 1
        st.session_state.search_berita_prev = search_keyword

        st.markdown(
            f"""
            <div style="font-size:12px; color:#475569; margin-top:6px; margin-bottom:10px;">
                Menampilkan hasil untuk kata kunci: <b>{escape(search_keyword)}</b>
            </div>
            """,
            unsafe_allow_html=True
        )

    if df_display.empty:
        st.info("Tidak ada berita yang sesuai dengan filter atau kata kunci yang dipilih.")
        st.stop()

    priority_order = {
        "PRIORITAS TINGGI": 1,
        "PRIORITAS SEDANG": 2,
        "PRIORITAS RENDAH": 3
    }
    df_display["Urutan"] = df_display["Prioritas"].map(priority_order).fillna(99)

    if "Waktu_Publish_WIB" in df_display.columns:
        df_display["Waktu_Publish_WIB_dt"] = normalize_datetime_col(df_display, "Waktu_Publish_WIB")
        sort_col = "Waktu_Publish_WIB_dt"
    elif "Tanggal_Publish" in df_display.columns:
        df_display["Tanggal_Publish_dt"] = pd.to_datetime(df_display["Tanggal_Publish"], errors="coerce")
        sort_col = "Tanggal_Publish_dt"
    elif "Tanggal_Ambil" in df_display.columns:
        df_display["Tanggal_Ambil_dt"] = pd.to_datetime(df_display["Tanggal_Ambil"], errors="coerce")
        sort_col = "Tanggal_Ambil_dt"
    else:
        sort_col = "Urutan"

    df_display = df_display.sort_values(["Urutan", sort_col], ascending=[True, False]).drop(columns=["Urutan"])
    df_display = df_display.reset_index(drop=True)

    items_per_page = 10
    total_rows = len(df_display)
    total_pages = max(1, (total_rows - 1) // items_per_page + 1)

    if "page" not in st.session_state:
        st.session_state.page = 1
    if st.session_state.page > total_pages:
        st.session_state.page = 1

    start_idx = (st.session_state.page - 1) * items_per_page
    end_idx = start_idx + items_per_page
    df_page = df_display.iloc[start_idx:end_idx].copy()

    section_header(
        "Berita Terkini",
        "Ringkasan berita terpilih untuk penelusuran cepat oleh pengguna dan pimpinan."
    )

    for i, row in df_page.iterrows():
        judul = escape(clean_label(row.get("Judul", "-")))
        media = escape(clean_label(row.get("Media", "-")))
        link = str(row.get("Link", "")).strip()
        waktu = escape(clean_label(row.get("Waktu_Publish_WIB", row.get("Tanggal", "-"))))
        prioritas = str(row.get("Prioritas", "PRIORITAS RENDAH")).strip()

        topik = escape(clean_label(row.get("Topik_Utama", row.get("Topik", ""))))
        dampak_program = escape(clean_label(row.get("Dampak_Program", "")))
        dampak_kepesertaan = escape(clean_label(row.get("Dampak_Kepesertaan", "")))
        potensi_klaim = escape(clean_label(row.get("Potensi_Klaim", "")))
        alasan = escape(clean_label(row.get("Alasan_Prioritas", "")))
        kategori = escape(clean_label(row.get("Kategori_Berita", "")))
        provinsi = escape(clean_label(row.get("Provinsi", "")))
        kabkota = escape(clean_label(row.get("Kabupaten_Kota", "")))

        lokasi = kabkota if kabkota else (provinsi if provinsi else "-")

        if prioritas == "PRIORITAS TINGGI":
            badge = "<span class='badge badge-high'>Prioritas Tinggi</span>"
        elif prioritas == "PRIORITAS SEDANG":
            badge = "<span class='badge badge-mid'>Prioritas Sedang</span>"
        else:
            badge = "<span class='badge badge-low'>Prioritas Rendah</span>"

        chips = []
        if kategori:
            chips.append(f"<span class='pill pill-blue'>{kategori}</span>")
        if lokasi and lokasi != "-":
            chips.append(f"<span class='pill pill-soft'>{lokasi}</span>")
        if topik:
            chips.append(f"<span class='pill pill-soft'>Topik: {topik}</span>")
        if dampak_program:
            chips.append(f"<span class='pill pill-soft'>Program: {dampak_program}</span>")
        if dampak_kepesertaan:
            chips.append(f"<span class='pill pill-soft'>Kepesertaan: {dampak_kepesertaan}</span>")
        if potensi_klaim:
            chips.append(f"<span class='pill pill-soft'>Klaim: {potensi_klaim}</span>")

        title_html = judul
        if link:
            title_html = f"<a href='{escape(link, quote=True)}' target='_blank'>{judul}</a>"

        body_text = alasan if alasan else "Belum ada analisis prioritas."

        st.markdown(
            f"""
            <div class="news-card">
                <div style="display:flex; justify-content:space-between; gap:14px; flex-wrap:wrap; align-items:flex-start;">
                    <div style="flex:1; min-width:260px;">
                        <div class="news-title">{i + 1}. {title_html}</div>
                        <div class="news-meta">{media} • {waktu}</div>
                    </div>
                    <div>{badge}</div>
                </div>

                <div style="margin:8px 0 10px 0;">
                    {''.join(chips)}
                </div>

                <div class="news-body" style="margin-bottom:10px;">
                    {body_text}
                </div>

                {f"<div class='news-link'><a href='{escape(link, quote=True)}' target='_blank'>Buka berita sumber</a></div>" if link else ""}
            </div>
            """,
            unsafe_allow_html=True
        )

    st.markdown(
        f"""
        <div style='text-align:center; margin-top:10px; color:#64748b; font-size:12px;'>
            Menampilkan <b>{min(start_idx + 1, total_rows)}</b>–<b>{min(end_idx, total_rows)}</b> dari <b>{total_rows}</b> berita
        </div>
        """,
        unsafe_allow_html=True
    )

    nav1, nav2, nav3 = st.columns([1, 2, 1])

    with nav1:
        if st.button("⬅ Sebelumnya", disabled=(st.session_state.page <= 1), use_container_width=True):
            st.session_state.page -= 1
            st.rerun()

    with nav3:
        if st.button("Berikutnya ➡", disabled=(st.session_state.page >= total_pages), use_container_width=True):
            st.session_state.page += 1
            st.rerun()

    with nav2:
        st.markdown(
            f"""
            <div style='text-align:center; color:#64748b; font-size:12px; padding-top:10px;'>
                Halaman <b>{st.session_state.page}</b> dari <b>{total_pages}</b>
            </div>
            """,
            unsafe_allow_html=True
        )

    st.markdown("<div style='height:12px;'></div>", unsafe_allow_html=True)
    section_header(
        "Indeks Eskalasi Isu",
        "Perbandingan intensitas pemberitaan 24 jam terakhir terhadap periode 24–48 jam sebelumnya."
    )

    df_ews = filtered_display.copy()

    if "Topik" not in df_ews.columns:
        combo = safe_series(df_ews, "Judul") + " " + safe_series(df_ews, "Ringkasan")
        df_ews["Topik"] = combo.apply(detect_topic)

    if "Waktu_Publish_WIB" in df_ews.columns:
        df_ews["publish_dt"] = normalize_datetime_col(df_ews, "Waktu_Publish_WIB")
    elif "Tanggal_Publish" in df_ews.columns:
        df_ews["publish_dt"] = pd.to_datetime(df_ews["Tanggal_Publish"], errors="coerce")
    else:
        df_ews["publish_dt"] = pd.to_datetime(df_ews["Tanggal_Hari"], errors="coerce")

    df_ews = df_ews.dropna(subset=["publish_dt"]).copy()

    now = pd.Timestamp.now()
    w1_start = now - pd.Timedelta(hours=24)
    w0_start = now - pd.Timedelta(hours=48)

    w1 = df_ews[df_ews["publish_dt"] >= w1_start].copy()
    w0 = df_ews[(df_ews["publish_dt"] >= w0_start) & (df_ews["publish_dt"] < w1_start)].copy()

    def agg(df_recent):
        if df_recent.empty:
            return pd.DataFrame(columns=["Topik", "Berita 24 Jam", "Media 24 Jam", "Headline", "Headline_URL"])

        out = df_recent.groupby("Topik", dropna=False).agg(
            **{
                "Berita 24 Jam": ("Judul", "count"),
                "Media 24 Jam": ("Media", pd.Series.nunique)
            }
        ).reset_index()

        head = (
            df_recent.sort_values("publish_dt", ascending=False)
            .groupby("Topik", dropna=False)
            .head(1)[["Topik", "Judul", "Link"]]
            .rename(columns={
                "Judul": "Headline",
                "Link": "Headline_URL"
            })
        )

        return out.merge(head, on="Topik", how="left")

    s1 = agg(w1)
    s0 = agg(w0).rename(columns={
        "Berita 24 Jam": "Berita 24-48 Jam",
        "Media 24 Jam": "Media 24-48 Jam"
    })

    esk = s1.merge(
        s0[["Topik", "Berita 24-48 Jam", "Media 24-48 Jam"]],
        on="Topik",
        how="left"
    )

    if not esk.empty:
        esk[["Berita 24-48 Jam", "Media 24-48 Jam"]] = esk[
            ["Berita 24-48 Jam", "Media 24-48 Jam"]
        ].fillna(0).astype(int)

        esk["Skor"] = esk["Media 24 Jam"] * 3 + esk["Berita 24 Jam"]

        def trend(r):
            if r["Media 24 Jam"] > r["Media 24-48 Jam"]:
                return "📈 Naik"
            if r["Media 24 Jam"] < r["Media 24-48 Jam"]:
                return "📉 Turun"
            return "➖ Stabil"

        esk["Trend"] = esk.apply(trend, axis=1)
        esk["Topik"] = esk["Topik"].astype(str).apply(clean_label)
        esk = esk.sort_values(["Skor", "Media 24 Jam", "Berita 24 Jam"], ascending=False)

        esk_show = esk[
            ["Topik", "Trend", "Media 24 Jam", "Berita 24 Jam",
             "Media 24-48 Jam", "Berita 24-48 Jam", "Skor", "Headline", "Headline_URL"]
        ].head(10).copy()

        esk_show["Headline"] = esk_show["Headline"].astype(str).fillna("")
        esk_show["Buka Berita"] = esk_show["Headline_URL"].astype(str).fillna("")

        st.markdown('<div class="panel-card">', unsafe_allow_html=True)

        st.data_editor(
            esk_show[
                ["Topik", "Trend", "Media 24 Jam", "Berita 24 Jam",
                 "Media 24-48 Jam", "Berita 24-48 Jam", "Skor", "Headline", "Buka Berita"]
            ],
            use_container_width=True,
            hide_index=True,
            disabled=True,
            column_config={
                "Topik": st.column_config.TextColumn("Topik", width="medium"),
                "Trend": st.column_config.TextColumn("Trend", width="small"),
                "Media 24 Jam": st.column_config.NumberColumn("Media 24 Jam", width="small"),
                "Berita 24 Jam": st.column_config.NumberColumn("Berita 24 Jam", width="small"),
                "Media 24-48 Jam": st.column_config.NumberColumn("Media 24-48 Jam", width="small"),
                "Berita 24-48 Jam": st.column_config.NumberColumn("Berita 24-48 Jam", width="small"),
                "Skor": st.column_config.NumberColumn("Skor", width="small"),
                "Headline": st.column_config.TextColumn("Headline", width="large"),
                "Buka Berita": st.column_config.LinkColumn("Buka Berita", width="small", display_text="Buka link"),
            },
        )

        st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.info("Belum ada data eskalasi isu.")

# ===============================
# TAB: ANALISIS WILAYAH
# ===============================
with tab_region:
    section_header(
        "Analisis Daerah",
        "Pemantauan isu berdasarkan wilayah untuk melihat konsentrasi topik dan tingkat prioritas secara lebih spesifik."
    )

    if filtered_display.empty:
        st.info("Belum ada data analisis daerah pada periode dan filter yang dipilih.")
    else:
        df_region_all = filtered_display.copy()

        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.markdown(
            """
            <div style="font-size:12px; color:#64748b; font-weight:700; margin-bottom:8px;">
                Filter Wilayah
            </div>
            """,
            unsafe_allow_html=True
        )

        provinsi_options = ["SEMUA"]
        if "Provinsi" in df_region_all.columns:
            provinsi_values = sorted([
                x for x in df_region_all["Provinsi"].astype(str).fillna("").unique()
                if x.strip() != ""
            ])
            provinsi_options += provinsi_values

        r1, r2 = st.columns([1.2, 1.2])

        with r1:
            selected_prov = st.selectbox("Provinsi", provinsi_options, key="prov_filter")

        df_region = df_region_all.copy()
        if selected_prov != "SEMUA" and "Provinsi" in df_region.columns:
            df_region = df_region[df_region["Provinsi"].astype(str) == selected_prov].copy()

        kab_options = ["SEMUA"]
        if "Kabupaten_Kota" in df_region.columns:
            kab_values = sorted([
                x for x in df_region["Kabupaten_Kota"].astype(str).fillna("").unique()
                if x.strip() != ""
            ])
            kab_options += kab_values

        with r2:
            selected_kab = st.selectbox("Kabupaten/Kota", kab_options, key="kab_filter")

        if selected_kab != "SEMUA" and "Kabupaten_Kota" in df_region.columns:
            df_region = df_region[df_region["Kabupaten_Kota"].astype(str) == selected_kab].copy()

        st.markdown('</div>', unsafe_allow_html=True)
        st.markdown("<div style='height:12px;'></div>", unsafe_allow_html=True)

        total_region = len(df_region)
        tinggi_region = int((df_region["Prioritas"] == "PRIORITAS TINGGI").sum()) if "Prioritas" in df_region.columns else 0
        sedang_region = int((df_region["Prioritas"] == "PRIORITAS SEDANG").sum()) if "Prioritas" in df_region.columns else 0
        rendah_region = int((df_region["Prioritas"] == "PRIORITAS RENDAH").sum()) if "Prioritas" in df_region.columns else 0

        section_header(
            "Ringkasan Wilayah",
            "Gambaran cepat jumlah isu dan komposisi prioritas pada wilayah terpilih."
        )

        c1, c2, c3, c4 = st.columns(4, gap="medium")

        with c1:
            kpi_card("Total Berita", f"{total_region:,}", "Pada wilayah terpilih")
        with c2:
            kpi_card("Prioritas Tinggi", f"{tinggi_region:,}", "Perlu perhatian segera", "high")
        with c3:
            kpi_card("Prioritas Sedang", f"{sedang_region:,}", "Perlu pemantauan", "mid")
        with c4:
            kpi_card("Prioritas Rendah", f"{rendah_region:,}", "Informasi umum", "low")

        st.markdown("<div style='height:12px;'></div>", unsafe_allow_html=True)

        lcol, rcol = st.columns([1, 1], gap="medium")

        with lcol:
            section_header(
                "Topik Dominan Wilayah",
                "Topik yang paling sering muncul pada wilayah yang dipilih."
            )
            st.markdown('<div class="panel-card">', unsafe_allow_html=True)

            if not df_region.empty:
                topik_region = df_region["Topik"].value_counts().head(5)
                if not topik_region.empty:
                    fig_reg = go.Figure()
                    fig_reg.add_trace(
                        go.Bar(
                            x=topik_region.values.tolist(),
                            y=[clean_label(x) for x in topik_region.index.tolist()],
                            orientation="h",
                            text=[f"{v:,}" for v in topik_region.values.tolist()],
                            textposition="outside",
                            marker=dict(color="#1d4ed8")
                        )
                    )
                    fig_reg.update_layout(
                        height=320,
                        margin=dict(l=10, r=45, t=6, b=20),
                        paper_bgcolor="rgba(0,0,0,0)",
                        plot_bgcolor="rgba(0,0,0,0)",
                        showlegend=False,
                        yaxis=dict(autorange="reversed", title=""),
                        xaxis=dict(title="Jumlah Berita", showgrid=True, gridcolor="rgba(148,163,184,0.20)")
                    )
                    st.plotly_chart(fig_reg, use_container_width=True, config={"displayModeBar": False})
                else:
                    st.info("Belum ada topik wilayah.")
            else:
                st.info("Tidak ada data pada wilayah terpilih.")

            st.markdown('</div>', unsafe_allow_html=True)

        with rcol:
            section_header(
                "Prioritas Wilayah",
                "Distribusi level prioritas isu pada wilayah terpilih."
            )
            st.markdown('<div class="panel-card">', unsafe_allow_html=True)

            if not df_region.empty:
                prio_region = df_region["Prioritas"].value_counts().reindex(
                    ["PRIORITAS TINGGI", "PRIORITAS SEDANG", "PRIORITAS RENDAH"]
                ).fillna(0).astype(int)

                fig_pr = go.Figure()
                fig_pr.add_trace(
                    go.Bar(
                        x=["Tinggi", "Sedang", "Rendah"],
                        y=prio_region.values.tolist(),
                        marker=dict(color=["#ef4444", "#f59e0b", "#22c55e"]),
                        text=[f"{v:,}" for v in prio_region.values.tolist()],
                        textposition="outside"
                    )
                )
                fig_pr.update_layout(
                    height=320,
                    margin=dict(l=10, r=20, t=6, b=20),
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    showlegend=False,
                    xaxis=dict(title=""),
                    yaxis=dict(title="Jumlah Berita", showgrid=True, gridcolor="rgba(148,163,184,0.20)")
                )
                st.plotly_chart(fig_pr, use_container_width=True, config={"displayModeBar": False})
            else:
                st.info("Tidak ada data prioritas wilayah.")

            st.markdown('</div>', unsafe_allow_html=True)

        st.markdown("<div style='height:12px;'></div>", unsafe_allow_html=True)

        section_header(
            "Ringkasan Wilayah",
            "Interpretasi singkat kondisi isu pada wilayah yang sedang ditinjau."
        )

        if total_region == 0:
            st.info("Belum ada data isu pada wilayah yang dipilih.")
        else:
            if tinggi_region >= 3:
                status_region = "🔴 Wilayah perlu perhatian tinggi."
                rekom_region = "Perlu pemantauan lebih intensif dan penelusuran isu utama di wilayah ini."
            elif tinggi_region > 0:
                status_region = "🟡 Wilayah dalam status waspada."
                rekom_region = "Perlu pemantauan berkala terhadap isu prioritas yang berkembang."
            else:
                status_region = "🟢 Wilayah relatif stabil."
                rekom_region = "Pemantauan rutin tetap diperlukan sebagai langkah antisipatif."

            topik_narasi = "Belum ada topik dominan."
            if not df_region.empty and "Topik" in df_region.columns:
                vc = df_region["Topik"].value_counts()
                if not vc.empty:
                    topik_narasi = ", ".join([f"{clean_label(k)} ({v})" for k, v in vc.head(3).items()])

            selected_label = selected_kab if selected_kab != "SEMUA" else selected_prov
            if selected_label == "SEMUA":
                selected_label = "seluruh wilayah"

            st.markdown(
                f"""
                <div class="panel-card">
                    <div class="news-body">
                        <p><b>Wilayah terpilih:</b> {escape(str(selected_label))}</p>
                        <p><b>Status:</b> {status_region}</p>
                        <p><b>Topik dominan:</b> {escape(topik_narasi)}</p>
                        <p><b>Rekomendasi:</b> {escape(rekom_region)}</p>
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )

        st.markdown("<div style='height:12px;'></div>", unsafe_allow_html=True)
        section_header(
            "Berita Wilayah Terbaru",
            "Daftar berita teratas pada wilayah yang dipilih."
        )

        if not df_region.empty:
            df_region_show = df_region.copy()

            if "Waktu_Publish_WIB" in df_region_show.columns:
                df_region_show["Waktu_Publish_WIB_dt"] = normalize_datetime_col(df_region_show, "Waktu_Publish_WIB")
                df_region_show = df_region_show.sort_values("Waktu_Publish_WIB_dt", ascending=False)

            for _, row in df_region_show.head(20).iterrows():
                judul = escape(clean_label(row.get("Judul", "-")))
                media = escape(clean_label(row.get("Media", "-")))
                waktu = escape(clean_label(row.get("Waktu_Publish_WIB", row.get("Tanggal", "-"))))
                prioritas = str(row.get("Prioritas", "PRIORITAS RENDAH")).strip()
                topik = escape(clean_label(row.get("Topik_Utama", row.get("Topik", ""))))
                alasan = escape(clean_label(row.get("Alasan_Prioritas", "")))
                lokasi = escape(clean_label(
                    str(row.get("Kabupaten_Kota", "") or "").strip() or str(row.get("Provinsi", "") or "").strip() or "-"
                ))
                link = str(row.get("Link", "")).strip()

                title_html = judul
                if link:
                    title_html = f"<a href='{escape(link, quote=True)}' target='_blank'>{judul}</a>"

                st.markdown(
                    f"""
                    <div class="news-card">
                        <div style="display:flex; justify-content:space-between; gap:12px; flex-wrap:wrap; align-items:flex-start;">
                            <div style="flex:1; min-width:250px;">
                                <div class="news-title">{title_html}</div>
                                <div class="news-meta">{media} • {waktu} • {lokasi}</div>
                            </div>
                            <div>{badge_html(prioritas)}</div>
                        </div>
                        <div style='margin:8px 0 10px 0;'>
                            <span class='pill pill-soft'>Topik: {topik}</span>
                        </div>
                        <div class="news-body">{alasan if alasan else "Belum ada analisis prioritas."}</div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
        else:
            st.info("Tidak ada berita pada wilayah terpilih.")

# ===============================
# TAB: PANDUAN
# ===============================
with tab_info:
    section_header(
        "Panduan Penggunaan",
        "Penjelasan ringkas mengenai fungsi dashboard, data berita, analisis wilayah, dan cara membaca prioritas isu."
    )

    guide_card(
        "1. Gambaran Umum Dashboard",
        """
        SIAGA JAMSOS merupakan dashboard pemantauan isu ketenagakerjaan dan jaminan sosial yang bersumber dari media online.
        Sistem ini digunakan untuk mendukung deteksi dini, pemantauan perkembangan isu, dan penyediaan informasi awal bagi pengambilan keputusan.
        """
    )

    guide_card(
        "2. Sumber dan Alur Data",
        """
        Data berasal dari proses pengambilan berita (scraping), kemudian disaring berdasarkan keterkaitan dengan isu ketenagakerjaan
        dan jaminan sosial. Setelah itu, berita dianalisis untuk menentukan topik, kategori, dampak, serta tingkat prioritasnya
        sebelum ditampilkan ke dalam dashboard.
        """
    )

    guide_card(
        "3. Kontrol Data",
        """
        Bagian Kontrol Data digunakan untuk memperbarui data, mengatur rentang tanggal, memilih level prioritas,
        dan membatasi kategori berita. Pengguna dapat menyesuaikan filter agar tampilan dashboard lebih fokus pada isu tertentu.
        """
    )

    guide_card(
        "4. Ringkasan Utama",
        """
        Ringkasan Utama menampilkan jumlah total berita raw, jumlah berita teranalisis, serta komposisi prioritas tinggi,
        sedang, dan rendah. Bagian ini berguna untuk membaca gambaran cepat kondisi isu pada periode yang dipilih.
        """
    )

    guide_card(
        "5. Isu Paling Kritis Hari Ini",
        """
        Bagian ini menampilkan satu isu yang dinilai paling kritis pada periode berjalan. Penentuan dilakukan dengan melihat
        skor analisis, waktu publikasi, dan konteks pemberitaan. Tujuannya adalah membantu pengguna segera mengenali isu utama
        yang paling perlu diperhatikan.
        """
    )

    guide_card(
        "6. Distribusi Prioritas dan Topik Dominan",
        """
        Distribusi Prioritas menunjukkan sebaran berita berdasarkan tingkat urgensi. Sementara itu, Topik Dominan menampilkan
        jenis isu yang paling sering muncul. Kombinasi keduanya membantu pengguna memahami apakah kondisi relatif stabil,
        waspada, atau memerlukan perhatian tinggi.
        """
    )

    guide_card(
        "7. Data Berita",
        """
        Tab Data Berita berisi daftar berita hasil analisis yang dapat ditelusuri menggunakan kata kunci. Setiap berita menampilkan
        informasi penting seperti media, waktu publikasi, topik, lokasi, dampak program, dampak kepesertaan, potensi klaim,
        dan alasan prioritas. Fitur ini berguna untuk penelusuran lebih rinci atas isu tertentu.
        """
    )

    guide_card(
        "8. Indeks Eskalasi Isu",
        """
        Indeks Eskalasi Isu membandingkan intensitas pemberitaan 24 jam terakhir dengan periode 24–48 jam sebelumnya.
        Jika jumlah media dan berita meningkat, maka isu dapat dipandang sedang mengalami eskalasi. Bagian ini membantu
        mendeteksi kenaikan perhatian publik atau media terhadap topik tertentu.
        """
    )

    guide_card(
        "9. Analisis Daerah",
        """
        Tab Analisis Daerah digunakan untuk melihat kondisi isu berdasarkan wilayah, baik provinsi maupun kabupaten/kota.
        Melalui tab ini, pengguna dapat mengetahui wilayah yang memiliki konsentrasi isu lebih tinggi, topik dominan wilayah,
        serta komposisi prioritas pada area tertentu.
        """
    )

    guide_card(
        "10. Cara Membaca Prioritas",
        """
        Prioritas Tinggi menunjukkan isu yang memerlukan perhatian cepat karena potensi dampaknya besar atau eskalasinya tinggi.
        Prioritas Sedang menunjukkan isu yang perlu dipantau lebih dekat. Prioritas Rendah menunjukkan isu informatif yang
        tetap relevan, namun belum memerlukan perhatian segera. Prioritas digunakan sebagai alat bantu pemantauan, bukan
        sebagai keputusan akhir.
        """
    )

    guide_card(
        "11. Catatan Penggunaan",
        """
        Dashboard ini berfungsi sebagai alat pemantauan awal (early warning system). Informasi yang ditampilkan membantu
        mengidentifikasi sinyal awal, namun tetap perlu dilengkapi dengan verifikasi, klarifikasi lapangan, dan analisis lanjutan
        apabila isu berkembang menjadi perhatian yang lebih serius.
        """
    )