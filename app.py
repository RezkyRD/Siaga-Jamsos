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
    --bg-light: #f4f7fb;
    --bg-dark: #0b1120;

    --card-light: rgba(255,255,255,0.82);
    --card-dark: rgba(17,25,40,0.82);

    --solid-light: #ffffff;
    --solid-dark: #111827;

    --text-light: #101828;
    --text-dark: #e5e7eb;

    --muted-light: #667085;
    --muted-dark: #94a3b8;

    --line-light: rgba(16,24,40,0.08);
    --line-dark: rgba(255,255,255,0.08);

    --primary: #4f46e5;
    --primary-2: #06b6d4;
    --danger: #ef4444;
    --warn: #f59e0b;
    --success: #22c55e;

    --danger-soft: rgba(239, 68, 68, 0.10);
    --warn-soft: rgba(245, 158, 11, 0.12);
    --success-soft: rgba(34, 197, 94, 0.12);
    --primary-soft: rgba(79, 70, 229, 0.10);
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
    padding-top: 1.35rem;
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

/* Main theme */
[data-testid="stHorizontalBlock"] { gap: 1rem; }

.glass-card,
.kpi-card,
.news-card,
.control-card,
.hero-card,
.info-card,
.alert-card,
.mini-card {
    background: var(--card-light);
    backdrop-filter: blur(14px);
    -webkit-backdrop-filter: blur(14px);
    border: 1px solid var(--line-light);
    border-radius: 22px;
    box-shadow: 0 10px 30px rgba(2, 6, 23, 0.08);
}

@media (prefers-color-scheme: dark) {
    .glass-card,
    .kpi-card,
    .news-card,
    .control-card,
    .hero-card,
    .info-card,
    .alert-card,
    .mini-card {
        background: var(--card-dark);
        border: 1px solid var(--line-dark);
        box-shadow: 0 12px 36px rgba(0,0,0,.35);
    }
}

/* Header hero */
.hero-wrap {
    padding: 22px 24px;
    margin-bottom: 18px;
}

.hero-grid {
    display: flex;
    justify-content: space-between;
    gap: 18px;
    flex-wrap: wrap;
    align-items: flex-start;
}

.brand-eyebrow {
    display: inline-block;
    font-size: 12px;
    font-weight: 800;
    letter-spacing: .12em;
    text-transform: uppercase;
    color: #4338ca;
    background: rgba(79,70,229,.08);
    border: 1px solid rgba(79,70,229,.12);
    padding: 7px 12px;
    border-radius: 999px;
    margin-bottom: 10px;
}

.hero-title {
    font-family: "Space Grotesk", Inter, "Segoe UI", sans-serif;
    font-size: clamp(2rem, 3.8vw, 3.15rem);
    font-weight: 800;
    line-height: 1.03;
    letter-spacing: -0.04em;
    margin: 0;
    color: inherit;
}

.hero-sub {
    font-size: 1rem;
    color: #667085;
    margin-top: .6rem;
    line-height: 1.7;
    max-width: 780px;
}

.hero-side {
    display: grid;
    gap: 12px;
    min-width: 280px;
    flex: 0 0 320px;
}

.hero-pill {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 12px;
    padding: 14px 16px;
    border-radius: 18px;
    background: rgba(255,255,255,.65);
    border: 1px solid rgba(16,24,40,.08);
}

.hero-pill-label {
    font-size: 12px;
    text-transform: uppercase;
    letter-spacing: .05em;
    color: #667085;
    font-weight: 700;
}

.hero-pill-value {
    font-size: 13px;
    font-weight: 800;
    color: inherit;
    text-align: right;
}

@media (prefers-color-scheme: dark) {
    .hero-sub,
    .hero-pill-label { color: #94a3b8; }
    .brand-eyebrow {
        color: #c7d2fe;
        background: rgba(129,140,248,.18);
        border: 1px solid rgba(129,140,248,.18);
    }
    .hero-pill {
        background: rgba(17,25,40,.55);
        border: 1px solid rgba(255,255,255,.08);
    }
}

/* Titles */
.section-title {
    font-family: "Space Grotesk", Inter, sans-serif;
    font-size: 1.3rem;
    font-weight: 700;
    margin-bottom: .8rem;
    margin-top: .2rem;
}

.section-subtitle {
    font-size: .9rem;
    color: #667085;
    margin-top: -.35rem;
    margin-bottom: .8rem;
}

@media (prefers-color-scheme: dark) {
    .section-subtitle { color: #94a3b8; }
}

/* Control */
.control-card {
    padding: 18px 18px 6px 18px;
    margin-bottom: 18px;
}

.control-top {
    display: flex;
    justify-content: space-between;
    gap: 12px;
    align-items: flex-start;
    flex-wrap: wrap;
    margin-bottom: 6px;
}

.control-title {
    font-size: 1rem;
    font-weight: 800;
}

.control-desc {
    font-size: .9rem;
    color: #667085;
    margin-top: 4px;
}

.period-chip {
    display: inline-flex;
    align-items: center;
    gap: 7px;
    background: rgba(79,70,229,.08);
    color: #4338ca;
    padding: 7px 12px;
    border-radius: 999px;
    font-size: .82rem;
    font-weight: 700;
    border: 1px solid rgba(79,70,229,.10);
}

@media (prefers-color-scheme: dark) {
    .control-desc { color: #94a3b8; }
    .period-chip {
        background: rgba(129,140,248,.18);
        color: #c7d2fe;
        border: 1px solid rgba(129,140,248,.18);
    }
}

/* KPI */
.kpi-card {
    padding: 16px 18px;
    min-height: 116px;
}

.kpi-topline {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    gap: 10px;
    margin-bottom: 10px;
}

.kpi-title {
    font-size: 12px;
    color: #667085;
    text-transform: uppercase;
    letter-spacing: .05em;
    font-weight: 700;
}

.kpi-icon {
    width: 34px;
    height: 34px;
    border-radius: 12px;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    font-size: 15px;
    font-weight: 700;
}

.kpi-value {
    font-size: 30px;
    font-weight: 800;
    line-height: 1.05;
    color: inherit;
}

.kpi-sub {
    margin-top: 8px;
    font-size: 12px;
    color: #667085;
}

.kpi-neutral .kpi-icon { background: rgba(79,70,229,.10); color: #4338ca; }
.kpi-high .kpi-icon { background: rgba(239,68,68,.12); color: #dc2626; }
.kpi-mid .kpi-icon { background: rgba(245,158,11,.14); color: #d97706; }
.kpi-low .kpi-icon { background: rgba(34,197,94,.14); color: #16a34a; }

@media (prefers-color-scheme: dark) {
    .kpi-title, .kpi-sub { color: #94a3b8; }
}

/* Badges */
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

.soft-badge {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 6px 12px;
    border-radius: 999px;
    font-size: 12px;
    font-weight: 800;
}
.soft-high { background: var(--danger-soft); color: #dc2626; }
.soft-mid { background: var(--warn-soft); color: #b45309; }
.soft-low { background: var(--success-soft); color: #15803d; }
.soft-primary { background: var(--primary-soft); color: #4338ca; }

/* Hero issue */
.hero-card {
    padding: 20px 20px 18px 20px;
    margin-bottom: 18px;
    border-left: 6px solid #ef4444;
}

.hero-issue-title {
    font-size: 1.1rem;
    font-weight: 800;
    line-height: 1.6;
    margin-bottom: 8px;
}

.hero-issue-meta {
    font-size: .88rem;
    color: #667085;
    margin-bottom: 10px;
}

.hero-issue-body {
    font-size: .97rem;
    line-height: 1.8;
    margin-top: 8px;
}

@media (prefers-color-scheme: dark) {
    .hero-issue-meta { color: #94a3b8; }
}

/* General cards */
.news-card {
    padding: 16px 18px 14px 18px;
    margin-bottom: 12px;
}
.mini-card {
    padding: 16px 18px;
}
.info-card {
    padding: 18px 20px;
    margin-bottom: 14px;
}
.alert-card {
    padding: 14px 16px;
    margin-bottom: 10px;
    border-left: 4px solid #f59e0b;
}

.news-title {
    font-size: 1rem;
    font-weight: 800;
    line-height: 1.52;
    margin-bottom: 8px;
}
.news-title a {
    color: inherit;
    text-decoration: none;
}
.news-title a:hover {
    text-decoration: underline;
}

.news-meta,
.top5-meta {
    font-size: .84rem;
    color: #667085;
    margin-bottom: 8px;
    line-height: 1.6;
}
.news-summary {
    font-size: .93rem;
    line-height: 1.68;
    margin-top: 8px;
}
.news-link a,
.top5-link a {
    color: #4338ca;
    text-decoration: none;
    font-weight: 700;
}
.news-link a:hover,
.top5-link a:hover {
    text-decoration: underline;
}

.news-chip, .badge-cat {
    display: inline-block;
    font-size: .74rem;
    font-weight: 700;
    padding: 5px 10px;
    border-radius: 999px;
    margin-right: 6px;
    margin-bottom: 6px;
}
.news-chip {
    background: rgba(79,70,229,.10);
    color: #4338ca;
}
.badge-cat {
    background: rgba(6,182,212,.10);
    color: #0f766e;
}

@media (prefers-color-scheme: dark) {
    .news-meta, .top5-meta { color: #94a3b8; }
    .news-link a, .top5-link a { color: #a5b4fc; }
    .news-chip {
        background: rgba(129,140,248,.18);
        color: #c7d2fe;
    }
    .badge-cat {
        background: rgba(34,211,238,.14);
        color: #99f6e4;
    }
}

/* Analysis */
.analysis-body {
    font-size: .95rem;
    line-height: 1.78;
}
.analysis-list {
    margin-top: 10px;
    margin-bottom: 10px;
}
.analysis-list li {
    margin-bottom: 7px;
}
.status-line {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
    flex-wrap: wrap;
    margin-bottom: 10px;
}
.status-title {
    font-size: 1rem;
    font-weight: 800;
}

/* Tabs */
button[data-baseweb="tab"] {
    border-radius: 999px !important;
    padding: 10px 16px !important;
    font-weight: 700 !important;
}

/* Table tweaks */
table { -webkit-tap-highlight-color: transparent; }
tbody tr:hover,
tbody tr:active,
tbody tr:focus { background-color: transparent !important; }
tbody tr { transition: none !important; }
thead tr th {
    text-align: center !important;
    font-size: 12px !important;
}

/* Expander */
[data-testid="stExpander"] {
    border-radius: 16px !important;
    border: 1px solid rgba(16,24,40,0.08) !important;
    background: rgba(255,255,255,.64) !important;
}
@media (prefers-color-scheme: dark) {
    [data-testid="stExpander"] {
        background: rgba(17,25,40,.55) !important;
        border: 1px solid rgba(255,255,255,.08) !important;
    }
}

/* Mobile */
@media (max-width: 900px) {
    .block-container {
        padding-top: 1rem;
        padding-left: 1rem;
        padding-right: 1rem;
    }
    .hero-wrap { padding: 18px 16px; }
    .hero-side { flex: 1 1 100%; min-width: 100%; }
    .kpi-value { font-size: 24px; }
    .news-card, .control-card, .info-card, .alert-card, .mini-card { padding: 14px; }
}
</style>
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


def soft_badge_html(status: str) -> str:
    if "TINGGI" in status or "RISIKO TINGGI" in status:
        return "<span class='soft-badge soft-high'>🔴 Risiko Tinggi</span>"
    if "WASPADA" in status or "SEDANG" in status:
        return "<span class='soft-badge soft-mid'>🟡 Waspada</span>"
    return "<span class='soft-badge soft-low'>🟢 Stabil</span>"


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
            alerts.append("Terjadi peningkatan isu prioritas tinggi yang memerlukan perhatian segera.")
        elif tinggi_count > 0:
            alerts.append("Terdapat isu prioritas tinggi yang perlu dipantau lebih dekat.")

    if "Topik" in df_alert.columns and not df_alert["Topik"].empty:
        topik_counts = df_alert["Topik"].value_counts()
        if not topik_counts.empty and int(topik_counts.iloc[0]) >= 5:
            alerts.append(f"Isu didominasi oleh topik {clean_label(topik_counts.index[0])}.")

    if "Provinsi" in df_alert.columns:
        prov_counts = df_alert["Provinsi"].astype(str).str.strip()
        prov_counts = prov_counts[prov_counts != ""].value_counts()
        if not prov_counts.empty and int(prov_counts.iloc[0]) >= 3:
            alerts.append(f"Konsentrasi isu terpantau di wilayah {prov_counts.index[0]}.")

    if "Waktu_Publish_WIB" in df_alert.columns:
        try:
            publish_dt = normalize_datetime_col(df_alert, "Waktu_Publish_WIB")
            now = pd.Timestamp.now()
            recent = df_alert[publish_dt >= (now - pd.Timedelta(hours=6))]
            if len(recent) >= 3:
                alerts.append("Terjadi lonjakan isu dalam 6 jam terakhir.")
        except Exception:
            pass

    if not alerts:
        alerts.append("Belum ada eskalasi signifikan pada periode terpilih.")

    return alerts[:4]


def status_summary(tinggi: int):
    if tinggi > 3:
        return (
            "🔴 RISIKO TINGGI",
            "Isu ketenagakerjaan meningkat dan memerlukan perhatian segera.",
            "Perlu pemantauan intensif dan koordinasi lintas unit terhadap isu prioritas."
        )
    elif tinggi > 0:
        return (
            "🟡 WASPADA",
            "Terdapat isu prioritas yang perlu dipantau lebih dekat.",
            "Perlu klarifikasi lapangan dan pemantauan berkala terhadap isu yang berkembang."
        )
    return (
        "🟢 STABIL",
        "Belum terlihat eskalasi signifikan pada periode ini.",
        "Pemantauan rutin tetap diperlukan sebagai langkah preventif."
    )


def render_kpi_card(title: str, value, sub: str, emoji: str, mode: str = "neutral"):
    st.markdown(
        f"""
        <div class="kpi-card kpi-{mode}">
            <div class="kpi-topline">
                <div class="kpi-title">{escape(title)}</div>
                <div class="kpi-icon">{emoji}</div>
            </div>
            <div class="kpi-value">{value}</div>
            <div class="kpi-sub">{escape(sub)}</div>
        </div>
        """,
        unsafe_allow_html=True
    )


def render_news_card(
    title: str,
    media: str = "-",
    waktu: str = "-",
    prioritas: str = "PRIORITAS RENDAH",
    topik: str = "",
    kategori: str = "",
    lokasi: str = "",
    alasan: str = "",
    link: str = "",
    dampak_program: str = "",
    dampak_kepesertaan: str = "",
    potensi_klaim: str = "",
    nomor: str = "",
    compact: bool = False,
):
    title = escape(clean_label(title))
    media = escape(clean_label(media))
    waktu = escape(clean_label(waktu))
    topik = escape(clean_label(topik))
    kategori = escape(clean_label(kategori))
    lokasi = escape(clean_label(lokasi))
    alasan = escape(clean_label(alasan))
    dampak_program = escape(clean_label(dampak_program))
    dampak_kepesertaan = escape(clean_label(dampak_kepesertaan))
    potensi_klaim = escape(clean_label(potensi_klaim))

    chips = []
    if kategori:
        chips.append(f"<span class='badge-cat'>{kategori}</span>")
    if lokasi and lokasi != "-":
        chips.append(f"<span class='badge-cat'>{lokasi}</span>")
    if topik:
        chips.append(f"<span class='news-chip'>Topik: {topik}</span>")
    if dampak_program:
        chips.append(f"<span class='news-chip'>Program: {dampak_program}</span>")
    if not compact and dampak_kepesertaan:
        chips.append(f"<span class='news-chip'>Kepesertaan: {dampak_kepesertaan}</span>")
    if not compact and potensi_klaim:
        chips.append(f"<span class='news-chip'>Klaim: {potensi_klaim}</span>")

    title_show = f"{nomor}. {title}" if nomor else title
    if link:
        title_html = f"<a href='{escape(link, quote=True)}' target='_blank'>{title_show}</a>"
        link_html = f"<div class='news-link'><a href='{escape(link, quote=True)}' target='_blank'>Baca berita</a></div>"
    else:
        title_html = title_show
        link_html = ""

    summary_text = alasan if alasan else "Belum ada analisis prioritas."

    st.markdown(
        f"""
        <div class="news-card">
            <div style="display:flex; justify-content:space-between; gap:12px; flex-wrap:wrap; align-items:flex-start;">
                <div style="flex:1; min-width:250px;">
                    <div class="news-title">{title_html}</div>
                    <div class="news-meta">{media} • {waktu}</div>
                </div>
                <div>{badge_html(prioritas)}</div>
            </div>
            <div style="margin:6px 0 6px 0;">{''.join(chips)}</div>
            <div class="news-summary">{summary_text}</div>
            <div style="margin-top:8px;">{link_html}</div>
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
# HEADER HERO
# ===============================
now_stamp = pd.Timestamp.now().strftime("%d %b %Y %H:%M")
st.markdown(
    f"""
    <div class="glass-card hero-wrap">
        <div class="hero-grid">
            <div style="flex:1; min-width:320px;">
                <div class="brand-eyebrow">SIAGA JAMSOS</div>
                <h1 class="hero-title">Early Warning System</h1>
                <div class="hero-sub">
                    Monitoring isu jaminan sosial ketenagakerjaan berbasis media online
                    untuk mendukung deteksi dini, analisis risiko, dan pemantauan perkembangan isu.
                </div>
            </div>
            <div class="hero-side">
                <div class="hero-pill">
                    <div class="hero-pill-label">Update Tampilan</div>
                    <div class="hero-pill-value">{escape(now_stamp)}</div>
                </div>
                <div class="hero-pill">
                    <div class="hero-pill-label">Sumber Data</div>
                    <div class="hero-pill-value">Google Sheets + Streamlit</div>
                </div>
                <div class="hero-pill">
                    <div class="hero-pill-label">Mode Sistem</div>
                    <div class="hero-pill-value">Monitoring Harian</div>
                </div>
            </div>
        </div>
    </div>
    """,
    unsafe_allow_html=True
)

# ===============================
# CONTROL CARD
# ===============================
st.markdown(
    """
    <div class="control-card">
        <div class="control-top">
            <div>
                <div class="control-title">Kontrol Data</div>
                <div class="control-desc">Gunakan panel ini untuk memperbarui data dan menyaring periode analisis.</div>
            </div>
        </div>
    """,
    unsafe_allow_html=True
)

c_ctrl1, c_ctrl2, c_ctrl3, c_ctrl4 = st.columns([1.05, 2.35, 1.35, 1.35])

with c_ctrl1:
    if st.button("🔄 Update Data", key="update_data_main", use_container_width=True):
        with st.spinner("Memproses update data..."):
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

if isinstance(date_range, (list, tuple)) and len(date_range) == 2:
    start_date, end_date = date_range
else:
    start_date, end_date = min_date, max_date

st.markdown(
    f"""
    <div style="margin-top:6px; margin-bottom:8px;">
        <span class="period-chip">📅 Periode aktif: {start_date} s.d. {end_date}</span>
    </div>
    </div>
    """,
    unsafe_allow_html=True
)

# ===============================
# APPLY DATE FILTER
# ===============================
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
# TAB: DASHBOARD
# ===============================
with tab_dash:
    if raw_filtered.empty:
        st.warning("Belum ada data RAW pada rentang tanggal ini.")
        st.stop()

    if filtered_display.empty or "Prioritas" not in filtered_display.columns:
        s1, s2 = st.columns([1, 1])
        with s1:
            render_kpi_card("Total Berita RAW", f"{len(raw_filtered):,}", "Sesuai rentang tanggal", "📰", "neutral")
        with s2:
            render_kpi_card("Berita Teranalisis", "0", "Belum ada yang lolos analisis", "📌", "neutral")
        st.info("Tidak ada berita yang lolos analisis pada rentang tanggal ini.")
        st.stop()

    tinggi = int((filtered_display["Prioritas"] == "PRIORITAS TINGGI").sum())
    sedang = int((filtered_display["Prioritas"] == "PRIORITAS SEDANG").sum())
    rendah = int((filtered_display["Prioritas"] == "PRIORITAS RENDAH").sum())

    kategori_nasional = int((safe_series(filtered_display, "Kategori_Berita").str.upper() == "NASIONAL").sum())
    kategori_global = int((safe_series(filtered_display, "Kategori_Berita").str.upper() == "GLOBAL").sum())
    kategori_edukasi = int((safe_series(filtered_display, "Kategori_Berita").str.upper() == "EDUKASI").sum())

    status_txt, kondisi, rekomendasi = status_summary(tinggi)

    st.markdown(
        f"""
        <div style="margin-bottom:12px;">
            {soft_badge_html(status_txt)}
        </div>
        """,
        unsafe_allow_html=True
    )

    k1, k2, k3, k4, k5 = st.columns([1.2, 1.2, 1, 1, 1], gap="large")
    with k1:
        render_kpi_card("Total Berita RAW", f"{len(raw_filtered):,}", "Sesuai rentang tanggal", "📰", "neutral")
    with k2:
        render_kpi_card("Berita Teranalisis", f"{len(filtered_display):,}", "Basis analisis EWS", "📌", "neutral")
    with k3:
        render_kpi_card("Prioritas Tinggi", f"{tinggi:,}", "Isu kritis yang perlu atensi", "🚨", "high")
    with k4:
        render_kpi_card("Prioritas Sedang", f"{sedang:,}", "Perlu pemantauan berkala", "⚠️", "mid")
    with k5:
        render_kpi_card("Prioritas Rendah", f"{rendah:,}", "Tetap dimonitor", "✅", "low")

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
        topik = escape(clean_label(top_issue.get("Topik_Utama", top_issue.get("Topik", "-"))))
        kategori = escape(clean_label(top_issue.get("Kategori_Berita", "-")))
        lokasi = escape(clean_label(
            str(top_issue.get("Kabupaten_Kota", "") or "").strip() or str(top_issue.get("Provinsi", "") or "").strip() or "-"
        ))
        dampak = escape(clean_label(top_issue.get("Dampak_Program", "-")))
        alasan = escape(clean_label(top_issue.get("Alasan_Prioritas", "-")))
        prioritas = str(top_issue.get("Prioritas", "PRIORITAS RENDAH")).strip()
        media = escape(clean_label(top_issue.get("Media", "-")))
        waktu = escape(clean_label(top_issue.get("Waktu_Publish_WIB", top_issue.get("Tanggal_Publish", "-"))))
        link = str(top_issue.get("Link", "")).strip()

        judul_html = judul
        if link:
            judul_html = f"<a href='{escape(link, quote=True)}' target='_blank'>{judul}</a>"

        st.markdown(
            f"""
            <div class="hero-card">
                <div style="display:flex; justify-content:space-between; gap:12px; flex-wrap:wrap; align-items:flex-start;">
                    <div style="flex:1; min-width:280px;">
                        <div class="hero-issue-title">{judul_html}</div>
                        <div class="hero-issue-meta">{media} • {waktu} • {lokasi} • {kategori} • {topik}</div>
                    </div>
                    <div>{badge_html(prioritas)}</div>
                </div>
                <div style="margin-top:4px;">
                    <span class='news-chip'>Dampak Program: {dampak}</span>
                </div>
                <div class="hero-issue-body">{alasan}</div>
                {"<div style='margin-top:10px;' class='news-link'><a href='" + escape(link, quote=True) + "' target='_blank'>Buka berita sumber</a></div>" if link else ""}
            </div>
            """,
            unsafe_allow_html=True
        )

    left, right = st.columns([1.02, 0.98], gap="large")

    with left:
        st.markdown('<div class="section-title">Distribusi Prioritas</div>', unsafe_allow_html=True)
        st.markdown('<div class="section-subtitle">Perbandingan jumlah berita berdasarkan level prioritas pada periode terpilih.</div>', unsafe_allow_html=True)

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
                yaxis=dict(title="", autorange="reversed", showgrid=False),
                font=dict(size=13)
            )
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False, "responsive": True})
        else:
            st.info("Belum ada data distribusi prioritas.")

        st.markdown("<div style='height:10px;'></div>", unsafe_allow_html=True)
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
        else:
            st.info("Belum ada topik dominan.")

        st.markdown("<div style='height:10px;'></div>", unsafe_allow_html=True)
        st.markdown('<div class="section-title">Top 5 Berita Prioritas Tinggi</div>', unsafe_allow_html=True)

        df_high = filtered_display[filtered_display["Prioritas"] == "PRIORITAS TINGGI"].copy()
        if not df_high.empty:
            if "Waktu_Publish_WIB" in df_high.columns:
                df_high["Waktu_Publish_WIB_dt"] = normalize_datetime_col(df_high, "Waktu_Publish_WIB")
                df_high = df_high.sort_values("Waktu_Publish_WIB_dt", ascending=False)

            top5 = df_high.head(5)
            for _, row in top5.iterrows():
                media = str(row.get("Media", "-"))
                judul = str(row.get("Judul", "-"))
                link = str(row.get("Link", "")).strip()
                waktu = str(row.get("Waktu_Publish_WIB", ""))
                lokasi = str(row.get("Kabupaten_Kota", "") or row.get("Provinsi", "") or "-")
                kategori = str(row.get("Kategori_Berita", "-"))
                alasan = str(row.get("Alasan_Prioritas", ""))

                render_news_card(
                    title=judul,
                    media=media,
                    waktu=waktu,
                    prioritas="PRIORITAS TINGGI",
                    kategori=kategori,
                    lokasi=lokasi,
                    alasan=alasan,
                    link=link,
                    compact=True
                )
        else:
            st.info("Belum ada berita prioritas tinggi.")

    with right:
        st.markdown('<div class="section-title">🧠 Analisis Situasi</div>', unsafe_allow_html=True)

        total = len(filtered_display)

        if "Topik" in filtered_display.columns and not filtered_display.empty:
            topik_counts = filtered_display["Topik"].value_counts()
            top3 = topik_counts.head(3)
            topik_utama = top3.index.tolist()
        else:
            top3 = pd.Series(dtype="int64")
            topik_utama = []

        ringkasan_utama = []
        dampak_utama = []

        if "PHK" in topik_utama:
            ringkasan_utama.append("PHK menjadi isu utama dan berpotensi meningkatkan klaim JKP serta pencairan JHT.")
            dampak_utama.append("Kondisi ini juga dapat mempengaruhi kepesertaan aktif pekerja penerima upah (PU).")

        if "THR / Kesejahteraan Pekerja" in topik_utama:
            ringkasan_utama.append("Permasalahan THR menunjukkan potensi persoalan kepatuhan perusahaan terhadap hak normatif pekerja.")
            dampak_utama.append("Isu ini dapat memicu pengaduan dan perselisihan hubungan industrial.")

        if "Kepesertaan BPJS" in topik_utama:
            ringkasan_utama.append("Isu kepesertaan BPJS Ketenagakerjaan berkaitan langsung dengan cakupan perlindungan tenaga kerja.")
            dampak_utama.append("Hal ini perlu dicermati dari sisi perluasan kepesertaan dan kepatuhan pemberi kerja.")

        if "Kecelakaan Kerja (JKK)" in topik_utama:
            ringkasan_utama.append("Isu kecelakaan kerja berpotensi meningkatkan klaim JKK.")
            dampak_utama.append("Pada kasus fatal, isu ini juga dapat berkembang menjadi klaim JKM.")

        if "Konflik Hubungan Industrial" in topik_utama or "Aksi / Demo Buruh" in topik_utama:
            ringkasan_utama.append("Konflik hubungan industrial dan aksi buruh perlu dipantau karena dapat berkembang menjadi gangguan yang lebih besar.")
            dampak_utama.append("Jika berlanjut, kondisi ini dapat mempengaruhi stabilitas hubungan kerja dan kepatuhan perlindungan sosial.")

        if not ringkasan_utama:
            ringkasan_utama.append("Perkembangan isu masih bersifat campuran dan tetap perlu dipantau.")
        if not dampak_utama:
            dampak_utama.append("Secara umum, isu media dapat mempengaruhi kepesertaan, kepatuhan, dan potensi klaim manfaat.")

        topik_items = "".join([f"<li><b>{escape(clean_label(topic))}</b> ({count} berita)</li>" for topic, count in top3.items()]) if not top3.empty else "<li>Belum ada topik dominan.</li>"

        st.markdown(
            f"""
            <div class="info-card analysis-body">
                <div class="status-line">
                    <div class="status-title">Status Kondisi</div>
                    <div>{soft_badge_html(status_txt)}</div>
                </div>

                <div style="margin-bottom:10px;">
                    <b>Total isu teranalisis:</b> {total:,} berita
                </div>

                <div style="display:grid; grid-template-columns: repeat(2, minmax(0,1fr)); gap:10px; margin-bottom:14px;">
                    <div class="mini-card">
                        <div class="kpi-title">Prioritas</div>
                        <div style="font-size:.95rem; line-height:1.8;">
                            Tinggi: <b>{tinggi:,}</b><br>
                            Sedang: <b>{sedang:,}</b><br>
                            Rendah: <b>{rendah:,}</b>
                        </div>
                    </div>
                    <div class="mini-card">
                        <div class="kpi-title">Komposisi Kategori</div>
                        <div style="font-size:.95rem; line-height:1.8;">
                            Nasional: <b>{kategori_nasional:,}</b><br>
                            Global: <b>{kategori_global:,}</b><br>
                            Edukasi: <b>{kategori_edukasi:,}</b>
                        </div>
                    </div>
                </div>

                <b>Topik dominan pada periode ini:</b>
                <ul class="analysis-list">{topik_items}</ul>

                <b>Kesimpulan:</b> {escape(kondisi)}<br><br>
                <b>Dampak utama:</b> {escape(ringkasan_utama[0])}<br>
                <b>Catatan lanjutan:</b> {escape(dampak_utama[0])}<br><br>
                <b>Rekomendasi:</b> {escape(rekomendasi)}
            </div>
            """,
            unsafe_allow_html=True
        )

        st.markdown('<div class="section-title">🔥 Alert Eskalasi</div>', unsafe_allow_html=True)
        alerts = build_alerts(filtered_display)
        for msg in alerts:
            st.markdown(
                f"""
                <div class="alert-card">
                    <div style="font-size:.95rem; font-weight:700;">⚡ {escape(msg)}</div>
                </div>
                """,
                unsafe_allow_html=True
            )

# ===============================
# TAB: DATA BERITA
# ===============================
with tab_data:
    st.markdown('<div class="section-title">Berita Terkini</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-subtitle">Daftar berita terbaru berdasarkan prioritas dan waktu publikasi.</div>', unsafe_allow_html=True)

    df_display = filtered_for_table.copy()

    if df_display.empty:
        st.info("Tidak ada berita untuk filter yang dipilih.")
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

    for i, row in df_page.iterrows():
        judul = row.get("Judul", "-")
        media = row.get("Media", "-")
        link = str(row.get("Link", "")).strip()
        waktu = row.get("Waktu_Publish_WIB", row.get("Tanggal", "-"))
        prioritas = str(row.get("Prioritas", "PRIORITAS RENDAH")).strip()

        topik = row.get("Topik_Utama", row.get("Topik", ""))
        dampak_program = row.get("Dampak_Program", "")
        dampak_kepesertaan = row.get("Dampak_Kepesertaan", "")
        potensi_klaim = row.get("Potensi_Klaim", "")
        alasan = row.get("Alasan_Prioritas", "")
        kategori = row.get("Kategori_Berita", "")
        provinsi = row.get("Provinsi", "")
        kabkota = row.get("Kabupaten_Kota", "")
        lokasi = kabkota if str(kabkota).strip() else (provinsi if str(provinsi).strip() else "-")

        render_news_card(
            title=judul,
            media=media,
            waktu=waktu,
            prioritas=prioritas,
            topik=topik,
            kategori=kategori,
            lokasi=lokasi,
            alasan=alasan,
            link=link,
            dampak_program=dampak_program,
            dampak_kepesertaan=dampak_kepesertaan,
            potensi_klaim=potensi_klaim,
            nomor=str(i + 1)
        )

    st.markdown(
        f"""
        <div style='text-align:center; margin-top:8px; color:#667085;'>
            Menampilkan {min(start_idx+1, total_rows)} - {min(end_idx, total_rows)} dari {total_rows} berita
        </div>
        """,
        unsafe_allow_html=True
    )

    p1, p2, p3 = st.columns([1, 2, 1])
    with p1:
        if st.button("⬅ Sebelumnya", disabled=(st.session_state.page <= 1), use_container_width=True):
            st.session_state.page -= 1
            st.rerun()
    with p3:
        if st.button("Berikutnya ➡", disabled=(st.session_state.page >= total_pages), use_container_width=True):
            st.session_state.page += 1
            st.rerun()
    with p2:
        st.markdown(
            f"<div style='text-align:center; color:#667085; margin-top:8px;'>Halaman {st.session_state.page} dari {total_pages}</div>",
            unsafe_allow_html=True
        )

    st.markdown("<div style='height:12px;'></div>", unsafe_allow_html=True)
    st.markdown('<div class="section-title">Indeks Eskalasi Isu</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-subtitle">Perbandingan perkembangan topik 24 jam terakhir terhadap 24–48 jam sebelumnya.</div>', unsafe_allow_html=True)

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
            .rename(columns={"Judul": "Headline", "Link": "Headline_URL"})
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
    else:
        st.info("Belum ada data eskalasi isu.")

# ===============================
# TAB: ANALISIS DAERAH
# ===============================
with tab_region:
    st.markdown('<div class="section-title">Analisis Daerah</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-subtitle">Pemantauan isu berdasarkan provinsi dan kabupaten/kota.</div>', unsafe_allow_html=True)

    if filtered_display.empty:
        st.info("Belum ada data analisis daerah.")
    else:
        df_region_all = filtered_display.copy()

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

        total_region = len(df_region)
        tinggi_region = int((df_region["Prioritas"] == "PRIORITAS TINGGI").sum()) if "Prioritas" in df_region.columns else 0
        sedang_region = int((df_region["Prioritas"] == "PRIORITAS SEDANG").sum()) if "Prioritas" in df_region.columns else 0
        rendah_region = int((df_region["Prioritas"] == "PRIORITAS RENDAH").sum()) if "Prioritas" in df_region.columns else 0

        st.markdown(
            f"""
            <div class="mini-card" style="margin-bottom:14px;">
                <div style="font-size:.95rem; line-height:1.8;">
                    <b>Wilayah aktif:</b> {escape(selected_prov)} {'' if selected_kab == 'SEMUA' else '• ' + escape(selected_kab)}<br>
                    <b>Total isu wilayah:</b> {total_region:,} berita
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total Berita", total_region)
        c2.metric("Prioritas Tinggi", tinggi_region)
        c3.metric("Prioritas Sedang", sedang_region)
        c4.metric("Prioritas Rendah", rendah_region)

        st.markdown("<div style='height:12px;'></div>", unsafe_allow_html=True)

        lcol, rcol = st.columns([1, 1], gap="large")

        with lcol:
            st.markdown('<div class="section-title">Topik Dominan Wilayah</div>', unsafe_allow_html=True)
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
                            marker=dict(color="#06b6d4")
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

        with rcol:
            st.markdown('<div class="section-title">Prioritas Wilayah</div>', unsafe_allow_html=True)
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
                    yaxis=dict(title="Jumlah Berita", showgrid=True, gridcolor="rgba(148,163,184,0.20)")
                )
                st.plotly_chart(fig_pr, use_container_width=True, config={"displayModeBar": False})
            else:
                st.info("Tidak ada data prioritas wilayah.")

        st.markdown("<div style='height:12px;'></div>", unsafe_allow_html=True)
        st.markdown('<div class="section-title">Daftar Berita Wilayah</div>', unsafe_allow_html=True)

        if not df_region.empty:
            df_region = df_region.copy()
            if "Score" in df_region.columns:
                df_region["Score_num"] = pd.to_numeric(df_region["Score"], errors="coerce").fillna(0)
                if "Waktu_Publish_WIB" in df_region.columns:
                    df_region["Waktu_Publish_WIB_dt"] = normalize_datetime_col(df_region, "Waktu_Publish_WIB")
                    df_region = df_region.sort_values(["Score_num", "Waktu_Publish_WIB_dt"], ascending=[False, False])
                else:
                    df_region = df_region.sort_values(["Score_num"], ascending=[False])
            elif "Waktu_Publish_WIB" in df_region.columns:
                df_region["Waktu_Publish_WIB_dt"] = normalize_datetime_col(df_region, "Waktu_Publish_WIB")
                df_region = df_region.sort_values("Waktu_Publish_WIB_dt", ascending=False)

            for _, row in df_region.head(20).iterrows():
                judul = row.get("Judul", "-")
                media = row.get("Media", "-")
                waktu = row.get("Waktu_Publish_WIB", row.get("Tanggal", "-"))
                prioritas = str(row.get("Prioritas", "PRIORITAS RENDAH")).strip()
                topik = row.get("Topik_Utama", row.get("Topik", ""))
                alasan = row.get("Alasan_Prioritas", "")
                lokasi = str(row.get("Kabupaten_Kota", "") or row.get("Provinsi", "") or "-")
                link = str(row.get("Link", "")).strip()

                render_news_card(
                    title=judul,
                    media=media,
                    waktu=waktu,
                    prioritas=prioritas,
                    topik=topik,
                    lokasi=lokasi,
                    alasan=alasan,
                    link=link,
                    compact=True
                )
        else:
            st.info("Tidak ada berita pada wilayah terpilih.")

# ===============================
# TAB: PANDUAN
# ===============================
with tab_info:
    st.markdown('<div class="section-title">Panduan Sistem SIAGA JAMSOS</div>', unsafe_allow_html=True)
    st.markdown(
        """
        <div class="section-subtitle">
            SIAGA JAMSOS digunakan untuk memantau perkembangan isu ketenagakerjaan di media online
            serta menilai potensi dampaknya terhadap program jaminan sosial ketenagakerjaan.
        </div>
        """,
        unsafe_allow_html=True
    )

    p1, p2, p3, p4 = st.columns(4)
    with p1:
        st.markdown(
            """
            <div class="mini-card">
                <div class="kpi-title">FUNGSI</div>
                <div style="font-size:.95rem; line-height:1.7;">
                    Monitoring isu media dan deteksi dini.
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
    with p2:
        st.markdown(
            """
            <div class="mini-card">
                <div class="kpi-title">OUTPUT</div>
                <div style="font-size:.95rem; line-height:1.7;">
                    Prioritas isu, topik dominan, dan analisis situasi.
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
    with p3:
        st.markdown(
            """
            <div class="mini-card">
                <div class="kpi-title">PENGGUNA</div>
                <div style="font-size:.95rem; line-height:1.7;">
                    Analis, Direktorat terkait, dan pimpinan.
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
    with p4:
        st.markdown(
            """
            <div class="mini-card">
                <div class="kpi-title">TUJUAN</div>
                <div style="font-size:.95rem; line-height:1.7;">
                    Mendukung pemantauan risiko jamsos ketenagakerjaan.
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

    st.markdown("<div style='height:12px;'></div>", unsafe_allow_html=True)

    with st.expander("📊 Tab Dashboard", expanded=True):
        st.markdown(
            """
            **Tab Dashboard** menampilkan gambaran umum kondisi isu ketenagakerjaan.

            Komponen utama:
            - Total Berita RAW
            - Berita Teranalisis
            - Prioritas Tinggi / Sedang / Rendah
            - Isu Paling Kritis Hari Ini
            - Distribusi Prioritas
            - Topik Dominan
            - Top 5 Berita Prioritas Tinggi
            - Analisis Situasi
            - Alert Eskalasi

            Tab ini paling tepat digunakan untuk membaca **kondisi umum dan perhatian utama hari ini**.
            """
        )

    with st.expander("📰 Tab Data Berita"):
        st.markdown(
            """
            **Tab Data Berita** menampilkan daftar berita hasil analisis.

            Yang ditampilkan antara lain:
            - Judul berita
            - Media dan waktu publikasi
            - Prioritas
            - Topik utama
            - Dampak program
            - Dampak kepesertaan
            - Potensi klaim
            - Alasan prioritas
            - Link menuju berita sumber

            Tab ini digunakan untuk **membaca detail berita satu per satu**.
            """
        )

    with st.expander("📍 Tab Analisis Daerah"):
        st.markdown(
            """
            **Tab Analisis Daerah** digunakan untuk melihat isu berdasarkan wilayah.

            Fitur utama:
            - Filter Provinsi
            - Filter Kabupaten/Kota
            - Total berita wilayah
            - Distribusi prioritas wilayah
            - Topik dominan wilayah
            - Daftar berita wilayah

            Tab ini berguna untuk **membaca konsentrasi isu secara regional**.
            """
        )

    with st.expander("⚙️ Cara Kerja Sistem"):
        st.markdown(
            """
            Alur sistem SIAGA JAMSOS:
            1. **Scraping berita** dari media online
            2. **Penyaringan kata kunci** isu ketenagakerjaan
            3. **Analisis prioritas** terhadap berita yang relevan
            4. **Penyimpanan hasil** ke Google Sheets
            5. **Visualisasi** dalam dashboard Streamlit

            Dengan alur ini, sistem tidak hanya menampilkan berita,
            tetapi juga membantu memilah mana isu yang lebih perlu perhatian.
            """
        )

    with st.expander("🎯 Penentuan Prioritas"):
        st.markdown(
            """
            Prioritas berita dibagi menjadi:
            - **Prioritas Tinggi**
            - **Prioritas Sedang**
            - **Prioritas Rendah**

            Penentuan prioritas mempertimbangkan:
            - tingkat urgensi isu
            - potensi dampak terhadap program jaminan sosial ketenagakerjaan
            - kemungkinan mempengaruhi kepesertaan
            - kemungkinan memicu klaim atau eskalasi

            Regulasi digunakan sebagai **bahan analisis**, bukan satu-satunya dasar penentuan prioritas.
            """
        )

    with st.expander("📈 Indeks Eskalasi Isu"):
        st.markdown(
            """
            Indeks Eskalasi Isu membandingkan:
            - **24 jam terakhir**
            - dengan **24–48 jam sebelumnya**

            Tujuannya untuk melihat apakah sebuah topik:
            - naik
            - turun
            - atau stabil

            Semakin banyak media dan berita dalam 24 jam terakhir,
            semakin tinggi skor eskalasinya.
            """
        )

    with st.expander("📝 Catatan Penting"):
        st.markdown(
            """
            Beberapa hal yang perlu diperhatikan:
            - Tidak semua berita media online langsung berarti dampak nyata.
            - Dashboard ini adalah alat **deteksi dini**, bukan kesimpulan final.
            - Hasil analisis perlu dibaca bersama konteks lapangan dan kebijakan yang berlaku.
            - Pemutakhiran data perlu dilakukan secara berkala agar dashboard tetap relevan.
            """
        )