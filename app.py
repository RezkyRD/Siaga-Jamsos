import re
import requests
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
    --card-solid-light: #ffffff;
    --text-light: #101828;
    --muted-light: #667085;
    --line-light: rgba(16,24,40,0.08);

    --bg-dark: #0b1120;
    --card-dark: rgba(17,25,40,0.78);
    --card-solid-dark: #111827;
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
    .ews-sub { color: #94a3b8; }
}

/* Cards */
.kpi-card,
.glass-card,
.news-card {
    background: var(--card-light);
    backdrop-filter: blur(14px);
    -webkit-backdrop-filter: blur(14px);
    border: 1px solid var(--line-light);
    border-radius: 20px;
    box-shadow: 0 10px 30px rgba(2, 6, 23, 0.08);
}

.info-card {
    background: var(--card-light);
    backdrop-filter: blur(14px);
    -webkit-backdrop-filter: blur(14px);
    border: 1px solid var(--line-light);
    border-radius: 20px;
    box-shadow: 0 10px 30px rgba(2, 6, 23, 0.08);
    padding: 18px 20px;
    margin-bottom: 14px;
}

@media (prefers-color-scheme: dark) {
    .kpi-card,
    .glass-card,
    .news-card,
    .info-card {
        background: var(--card-dark);
        border: 1px solid var(--line-dark);
        box-shadow: 0 12px 36px rgba(0, 0, 0, 0.35);
    }
}

.kpi-card { padding: 16px 18px; }

.kpi-desktop {
    display: block;
}

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

.chart-caption {
    font-size: 12px;
    color: #667085;
    margin-top: -2px;
    margin-bottom: 8px;
}

@media (prefers-color-scheme: dark) {
    .chart-caption { color: #94a3b8; }
}

.analysis-body {
    font-size: .97rem;
    line-height: 1.75;
}

.analysis-body p,
.analysis-body li {
    color: inherit;
}

.top5-link a {
    color: #4338ca;
    text-decoration: none;
    font-weight: 700;
    line-height: 1.5;
}

.top5-link a:hover { text-decoration: underline; }

.top5-meta {
    font-size: .86rem;
    color: #667085;
    margin-top: 4px;
}

@media (prefers-color-scheme: dark) {
    .top5-link a { color: #a5b4fc; }
    .top5-meta { color: #94a3b8; }
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
.badge-mid  { background: linear-gradient(135deg, #f59e0b, #d97706); }
.badge-low  { background: linear-gradient(135deg, #22c55e, #16a34a); }

.badge-cat {
    background: rgba(79,70,229,.12);
    color: #4338ca;
    border: 1px solid rgba(79,70,229,.14);
    padding: 5px 10px;
    border-radius: 999px;
    font-size: .75rem;
    font-weight: 700;
    display: inline-block;
    margin-right: 6px;
    margin-bottom: 6px;
}

@media (prefers-color-scheme: dark) {
    .badge-cat {
        background: rgba(129,140,248,.18);
        color: #c7d2fe;
    }
}

/* Tabs */
button[data-baseweb="tab"] {
    border-radius: 999px !important;
    padding: 10px 16px !important;
}

table { -webkit-tap-highlight-color: transparent; }

tbody tr:hover,
tbody tr:active,
tbody tr:focus {
    background-color: transparent !important;
}

tbody tr {
    transition: none !important;
}

thead tr th {
    text-align: center !important;
    font-size: 12px !important;
}

/* News cards */
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

.info-text li {
    margin-bottom: 6px;
}

/* ===============================
   MOBILE
=============================== */
@media (max-width: 768px) {
    .block-container {
        padding-top: 1.2rem;
        padding-left: 1rem;
        padding-right: 1rem;
    }

    .hero-wrap {
        padding: 20px 20px !important;
        border-radius: 20px !important;
        margin-bottom: 14px !important;
    }

    .hero-title {
        font-size: 2rem !important;
        line-height: 1.15 !important;
        margin-bottom: 8px !important;
    }

    .hero-subtitle {
        font-size: 0.95rem !important;
        line-height: 1.5 !important;
        color: rgba(255,255,255,0.82) !important;
    }

    .stButton > button {
        width: 100% !important;
        min-height: 48px !important;
        border-radius: 14px !important;
        font-size: 1rem !important;
        font-weight: 700 !important;
    }

    button[data-baseweb="tab"] {
        flex: 1 1 auto !important;
        min-width: 120px !important;
        padding: 12px 14px !important;
        font-size: 0.95rem !important;
        border-radius: 14px !important;
        white-space: nowrap !important;
    }

    .section-title {
        margin-bottom: 8px !important;
    }

    .news-card {
        padding: 14px !important;
    }

    .badge {
        padding: 4px 10px !important;
        font-size: 11px !important;
    }

    .kpi-card {
        padding: 12px 14px !important;
        border-radius: 16px !important;
    }

    .kpi-title {
        font-size: 11px !important;
        margin-bottom: 6px !important;
    }

    .kpi-value {
        font-size: 22px !important;
    }

    .kpi-sub {
        font-size: 12px !important;
        margin-top: 6px !important;
    }

    /* FIX FULL WIDTH */
    .kpi-mobile-grid > div:last-child {
        grid-column: 1 / -1;
    }

}
</style>
""",
    unsafe_allow_html=True
)

st.markdown(
    """
<div class="hero-wrap" style="background: linear-gradient(135deg, #0b2c5f 0%, #1e3a5f 100%); padding: 32px 36px; border-radius: 24px; margin-bottom: 20px; box-shadow: 0 10px 30px rgba(0,0,0,0.15);">
    <div class="hero-title" style="font-size: 2.4rem; font-weight: 800; color: white; margin-bottom: 6px; letter-spacing: -0.02em;">
        Early Warning System
    </div>
    <div class="hero-subtitle" style="font-size: 1rem; color: rgba(255,255,255,0.8);">
        Monitoring Isu Jaminan Sosial Ketenagakerjaan
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

def kpi_card_html(title: str, value, subtitle: str = "") -> str:
    return f"""
    <div class="kpi-card">
        <div class="kpi-title">{escape(str(title))}</div>
        <div class="kpi-value">{value}</div>
        <div class="kpi-sub">{subtitle}</div>
    </div>
    """


def normalize_datetime_col(df: pd.DataFrame, col: str) -> pd.Series:
    s = pd.to_datetime(df[col], errors="coerce")
    try:
        if getattr(s.dt, "tz", None) is not None:
            s = s.dt.tz_localize(None)
    except Exception:
        pass
    return s

# ===============================
# CHOROPLETH HELPERS
# ===============================
@st.cache_data(ttl=86400, show_spinner=False)
def load_indonesia_geojson():
    """Try multiple CDN sources. Returns (geojson, featureidkey) or (None, None)."""
    CANDIDATE_KEYS = ["Propinsi", "PROPINSI", "name", "NAME_1", "provinsi", "PROVINSI"]
    sources = [
        "https://cdn.jsdelivr.net/gh/ans-4175/peta-indonesia-geojson@master/indonesia-province.geojson",
        "https://cdn.jsdelivr.net/gh/superpikar/indonesia-geojson@master/indonesia-en.geojson",
        "https://raw.githubusercontent.com/ans-4175/peta-indonesia-geojson/master/indonesia-province.geojson",
        "https://raw.githubusercontent.com/superpikar/indonesia-geojson/master/indonesia-en.geojson",
    ]
    for url in sources:
        try:
            r = requests.get(url, timeout=12)
            r.raise_for_status()
            gj = r.json()
            if not gj.get("features"):
                continue
            props = gj["features"][0].get("properties", {})
            for key in CANDIDATE_KEYS:
                if key in props:
                    return gj, f"properties.{key}"
            first_key = next(iter(props), None)
            if first_key:
                return gj, f"properties.{first_key}"
        except Exception:
            continue
    return None, None


PROV_TO_MAP = {
    "Aceh":                       "ACEH",
    "Sumatera Utara":             "SUMATERA UTARA",
    "Sumatera Barat":             "SUMATERA BARAT",
    "Riau":                       "RIAU",
    "Kepulauan Riau":             "KEPULAUAN RIAU",
    "Jambi":                      "JAMBI",
    "Sumatera Selatan":           "SUMATERA SELATAN",
    "Kepulauan Bangka Belitung":  "BANGKA BELITUNG",
    "Bengkulu":                   "BENGKULU",
    "Lampung":                    "LAMPUNG",
    "Banten":                     "BANTEN",
    "DKI Jakarta":                "DKI JAKARTA",
    "Jawa Barat":                 "JAWA BARAT",
    "Jawa Tengah":                "JAWA TENGAH",
    "DI Yogyakarta":              "DI YOGYAKARTA",
    "Jawa Timur":                 "JAWA TIMUR",
    "Bali":                       "BALI",
    "Nusa Tenggara Barat":        "NUSA TENGGARA BARAT",
    "Nusa Tenggara Timur":        "NUSA TENGGARA TIMUR",
    "Kalimantan Barat":           "KALIMANTAN BARAT",
    "Kalimantan Tengah":          "KALIMANTAN TENGAH",
    "Kalimantan Selatan":         "KALIMANTAN SELATAN",
    "Kalimantan Timur":           "KALIMANTAN TIMUR",
    "Kalimantan Utara":           "KALIMANTAN UTARA",
    "Sulawesi Utara":             "SULAWESI UTARA",
    "Gorontalo":                  "GORONTALO",
    "Sulawesi Tengah":            "SULAWESI TENGAH",
    "Sulawesi Barat":             "SULAWESI BARAT",
    "Sulawesi Selatan":           "SULAWESI SELATAN",
    "Sulawesi Tenggara":          "SULAWESI TENGGARA",
    "Maluku":                     "MALUKU",
    "Maluku Utara":               "MALUKU UTARA",
    "Papua Barat":                "PAPUA BARAT",
    "Papua":                      "PAPUA",
}

# Title-case mapping untuk GeoJSON yang pakai property "name" (superpikar repo)
PROV_TO_MAP_TITLE = {k: v.title() for k, v in PROV_TO_MAP.items()}
# Override beberapa yang title()-nya salah
PROV_TO_MAP_TITLE.update({
    "DKI Jakarta": "Dki Jakarta",
    "DI Yogyakarta": "Di Yogyakarta",
    "Kepulauan Bangka Belitung": "Bangka Belitung",
    "Kepulauan Riau": "Kepulauan Riau",
})


def build_prov_stats(df: pd.DataFrame, featureidkey: str = "properties.Propinsi") -> pd.DataFrame:
    """Agregasi berita per provinsi untuk choropleth."""
    if "Provinsi" not in df.columns or "Prioritas" not in df.columns:
        return pd.DataFrame()

    df_prov = df[
        ~df["Provinsi"].astype(str).isin(["", "Nasional", "Tidak Diketahui"])
    ].copy()

    if df_prov.empty:
        return pd.DataFrame()

    # Pilih mapping sesuai format nilai GeoJSON
    use_title = featureidkey.endswith("name") or featureidkey.endswith("NAME_1")
    prov_map = PROV_TO_MAP_TITLE if use_title else PROV_TO_MAP
    fallback = lambda x: x.title() if use_title else x.upper()
    df_prov["Prov_Map"] = df_prov["Provinsi"].map(prov_map).fillna(
        df_prov["Provinsi"].apply(fallback)
    )

    agg = df_prov.groupby("Prov_Map").agg(
        Total=("Judul", "count"),
        Tinggi=("Prioritas", lambda x: (x == "PRIORITAS TINGGI").sum()),
        Sedang=("Prioritas", lambda x: (x == "PRIORITAS SEDANG").sum()),
        Rendah=("Prioritas", lambda x: (x == "PRIORITAS RENDAH").sum()),
    ).reset_index()

    # Topik dominan per provinsi
    if "Topik" in df_prov.columns:
        topik_dom = (
            df_prov.groupby("Prov_Map")["Topik"]
            .agg(lambda x: x.value_counts().index[0] if len(x) else "-")
            .reset_index()
            .rename(columns={"Topik": "Topik_Dominan"})
        )
        agg = agg.merge(topik_dom, on="Prov_Map", how="left")
        agg["Topik_Dominan"] = agg["Topik_Dominan"].fillna("-")
    else:
        agg["Topik_Dominan"] = "-"

    # Risk score: Tinggi×3 + Sedang×2 + Rendah×1
    agg["Risk_Score"] = agg["Tinggi"] * 3 + agg["Sedang"] * 2 + agg["Rendah"] * 1

    agg["Hover"] = agg.apply(
        lambda r: (
            f"<b>{r['Prov_Map']}</b><br>"
            f"Total berita: {r['Total']}<br>"
            f"🔴 Prioritas Tinggi: {r['Tinggi']}<br>"
            f"🟡 Prioritas Sedang: {r['Sedang']}<br>"
            f"🟢 Prioritas Rendah: {r['Rendah']}<br>"
            f"Topik dominan: {r['Topik_Dominan']}"
        ),
        axis=1,
    )
    return agg


def build_alerts(df: pd.DataFrame) -> list[str]:
    alerts = []
    if df.empty:
        return ["Belum ada isu signifikan pada periode terpilih."]

    df_alert = df.copy()

    # Prioritas tinggi
    if "Prioritas" in df_alert.columns:
        tinggi_count = int((df_alert["Prioritas"] == "PRIORITAS TINGGI").sum())
        if tinggi_count >= 3:
            alerts.append("🚨 Terjadi peningkatan isu prioritas tinggi yang memerlukan perhatian segera.")
        elif tinggi_count > 0:
            alerts.append("🟡 Terdapat isu prioritas tinggi yang perlu dipantau lebih dekat.")

    # Topik dominan
    if "Topik" in df_alert.columns and not df_alert["Topik"].empty:
        topik_counts = df_alert["Topik"].value_counts()
        if not topik_counts.empty and int(topik_counts.iloc[0]) >= 5:
            alerts.append(f"📈 Isu didominasi oleh topik {clean_label(topik_counts.index[0])}.")

    # Wilayah dominan
    if "Provinsi" in df_alert.columns:
        prov_counts = df_alert["Provinsi"].astype(str).str.strip()
        prov_counts = prov_counts[prov_counts != ""].value_counts()
        if not prov_counts.empty and int(prov_counts.iloc[0]) >= 3:
            alerts.append(f"🌍 Konsentrasi isu terpantau di wilayah {prov_counts.index[0]}.")

    # Lonjakan 6 jam terakhir
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
# KONTROL UTAMA
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
    today = pd.Timestamp.now().date()

    if "main_date_range" not in st.session_state:
        default_start = today
        default_end = today

        if today < min_date:
            default_start = min_date
            default_end = min_date
        elif today > max_date:
            default_start = max_date
            default_end = max_date

        st.session_state["main_date_range"] = (default_start, default_end)

    date_range = st.date_input(
        "Rentang tanggal",
        min_value=min_date,
        max_value=max_date,
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
        c1, c2 = st.columns([1.2, 1.2], gap="large")

        with c1:
            st.markdown(
                f"""
                <div class="kpi-card">
                  <div class="kpi-title">Total Berita Raw</div>
                  <div class="kpi-value">{len(raw_filtered):,}</div>
                  <div class="kpi-sub">Sesuai rentang tanggal</div>
                </div>
                """,
                unsafe_allow_html=True
            )

        with c2:
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

    kategori_nasional = int((safe_series(filtered_display, "Kategori_Berita").str.upper() == "NASIONAL").sum())
    kategori_global = int((safe_series(filtered_display, "Kategori_Berita").str.upper() == "GLOBAL").sum())
    kategori_edukasi = int((safe_series(filtered_display, "Kategori_Berita").str.upper() == "EDUKASI").sum())

    # ===============================
# KPI DESKTOP
# ===============================
    st.markdown('<div class="kpi-desktop">', unsafe_allow_html=True)

    c1, c2, c3, c4, c5 = st.columns([1.2, 1.2, 1, 1, 1], gap="large")

    with c1:
        st.markdown(
            kpi_card_html("Total Berita Raw", f"{len(raw_filtered):,}", "Sesuai rentang tanggal"),
            unsafe_allow_html=True
        )

    with c2:
        st.markdown(
            kpi_card_html("Berita Teranalisis", f"{len(filtered_display):,}", "Basis analisis EWS"),
            unsafe_allow_html=True
        )

    with c3:
        st.markdown(
            kpi_card_html("Prioritas Tinggi", f"{tinggi:,}", "<span class='badge badge-high'>HIGH</span>"),
            unsafe_allow_html=True
        )

    with c4:
        st.markdown(
           kpi_card_html("Prioritas Sedang", f"{sedang:,}", "<span class='badge badge-mid'>MED</span>"),
           unsafe_allow_html=True
        )

    with c5:
        st.markdown(
            kpi_card_html("Prioritas Rendah", f"{rendah:,}", "<span class='badge badge-low'>LOW</span>"),
            unsafe_allow_html=True
        )

    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("<div style='height:14px;'></div>", unsafe_allow_html=True)

    # Isu paling kritis
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

            st.caption("Perbandingan jumlah berita berdasarkan level prioritas pada periode terpilih")

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
        else:
            st.info("Belum ada topik dominan.")

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
                            <div class="top5-link">
                                <a href="{escape(link, quote=True)}" target="_blank">{judul}</a>
                            </div>
                            <div class="top5-meta">{media} • {waktu} • {lokasi} • {kategori}</div>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
                else:
                    st.markdown(
                        f"""
                        <div class="news-card">
                            <div class="top5-link">{judul}</div>
                            <div class="top5-meta">{media} • {waktu} • {lokasi} • {kategori}</div>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
        else:
            st.info("Belum ada berita prioritas tinggi.")

    with right:
        st.markdown('<div class="section-title">🧠 Analisis Situasi</div>', unsafe_allow_html=True)

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
<div class="news-card analysis-body">

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

        st.markdown("<div style='height:12px;'></div>", unsafe_allow_html=True)
        st.markdown('<div class="section-title">🔥 Alert Eskalasi</div>', unsafe_allow_html=True)

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
    st.markdown('<div class="section-title">Berita Terkini</div>', unsafe_allow_html=True)

    search_keyword = st.text_input(
        "",
        placeholder="🔍 Cari berita (bisa lebih dari satu kata, misalnya: PHK Bekasi)",
        key="search_berita"
    )

    st.caption("Daftar 10 berita terbaru berdasarkan prioritas dan waktu publikasi.")

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
        st.caption(f"Hasil pencarian: '{search_keyword}'")

    if df_display.empty:
        st.info("Tidak ada berita untuk filter atau kata kunci yang dipilih.")
        st.stop()

    priority_order = {
        "PRIORITAS TINGGI": 1,
        "PRIORITAS SEDANG": 2,
        "PRIORITAS RENDAH": 3
    }
    df_display["Urutan"] = df_display["Prioritas"].map(priority_order).fillna(99)

    sort_col = None
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

        chips = []
        if kategori:
            chips.append(f"<span class='badge-cat'>{kategori}</span>")
        if lokasi and lokasi != "-":
            chips.append(f"<span class='badge-cat'>{lokasi}</span>")
        if topik:
            chips.append(f"<span class='news-chip'>Topik: {topik}</span>")
        if dampak_program:
            chips.append(f"<span class='news-chip'>Program: {dampak_program}</span>")
        if dampak_kepesertaan:
            chips.append(f"<span class='news-chip'>Kepesertaan: {dampak_kepesertaan}</span>")
        if potensi_klaim:
            chips.append(f"<span class='news-chip'>Klaim: {potensi_klaim}</span>")

        link_html = ""
        if link:
            safe_link = escape(link, quote=True)
            link_html = f"<div class='news-link'><a href='{safe_link}' target='_blank'>Baca berita</a></div>"

        card_html = (
            f"<div class='news-card'>"
            f"<div style='display:flex; justify-content:space-between; gap:12px; flex-wrap:wrap; align-items:flex-start;'>"
            f"<div style='flex:1; min-width:250px;'>"
            f"<div class='news-title'>{i + 1}. {judul}</div>"
            f"<div class='news-meta'>{media} • {waktu}</div>"
            f"</div>"
            f"<div>{badge_html(prioritas)}</div>"
            f"</div>"
            f"<div style='margin:8px 0 10px 0;'>{''.join(chips)}</div>"
            f"<div style='font-size:.95rem; line-height:1.65; margin-bottom:10px;'>{alasan if alasan else 'Belum ada analisis prioritas.'}</div>"
            f"{link_html}"
            f"</div>"
        )

        st.markdown(card_html, unsafe_allow_html=True)

    st.markdown(
        f"""
        <div style='text-align:center; margin-top:10px; color:#667085;'>
        Menampilkan {min(start_idx+1, total_rows)} - {min(end_idx, total_rows)} dari {total_rows} berita
        </div>
        """,
        unsafe_allow_html=True
    )

    col1, col2, col3 = st.columns([1, 2, 1])
    with col1:
        if st.button("⬅ Sebelumnya", disabled=(st.session_state.page <= 1)):
            st.session_state.page -= 1
            st.rerun()
    with col3:
        if st.button("Berikutnya ➡", disabled=(st.session_state.page >= total_pages)):
            st.session_state.page += 1
            st.rerun()
    with col2:
        st.markdown(
            f"<div style='text-align:center; color:#667085;'>Halaman {st.session_state.page} dari {total_pages}</div>",
            unsafe_allow_html=True
        )

    st.markdown("<div style='height:10px;'></div>", unsafe_allow_html=True)
    st.markdown('<div class="section-title">Indeks Eskalasi Isu</div>', unsafe_allow_html=True)

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

    if filtered_display.empty:
        st.info("Belum ada data analisis daerah.")
    else:
        df_region_all = filtered_display.copy()

        # ── PETA CHOROPLETH ─────────────────────────────────────────────
        geojson, featureidkey = load_indonesia_geojson()
        prov_stats = build_prov_stats(df_region_all, featureidkey or "properties.Propinsi")

        if geojson and featureidkey and not prov_stats.empty:
            st.markdown(
                '<div class="section-title">🗺️ Peta Hotspot Isu Ketenagakerjaan</div>',
                unsafe_allow_html=True,
            )
            st.markdown(
                '<div class="chart-caption">'
                'Warna semakin merah = semakin banyak isu prioritas tinggi. '
                'Arahkan kursor ke provinsi untuk melihat detail. '
                'Gunakan filter di bawah untuk drill-down per wilayah.'
                '</div>',
                unsafe_allow_html=True,
            )

            z_max = max(int(prov_stats["Risk_Score"].max()), 1)

            fig_map = go.Figure(
                go.Choropleth(
                    geojson=geojson,
                    locations=prov_stats["Prov_Map"],
                    z=prov_stats["Risk_Score"],
                    featureidkey=featureidkey,
                    colorscale=[
                        [0.00, "#e8f5e9"],
                        [0.25, "#fff9c4"],
                        [0.55, "#ffe0b2"],
                        [0.80, "#ef9a9a"],
                        [1.00, "#b71c1c"],
                    ],
                    zmin=0,
                    zmax=z_max,
                    text=prov_stats["Hover"],
                    hovertemplate="%{text}<extra></extra>",
                    marker_line_color="white",
                    marker_line_width=0.8,
                    showscale=True,
                    colorbar=dict(
                        title=dict(text="Risk<br>Score", font=dict(size=11)),
                        thickness=14,
                        len=0.65,
                        tickfont=dict(size=10),
                        x=1.01,
                    ),
                )
            )
            fig_map.update_geos(
                fitbounds="locations",
                visible=False,
                bgcolor="rgba(0,0,0,0)",
            )
            fig_map.update_layout(
                height=460,
                margin=dict(l=0, r=60, t=10, b=0),
                paper_bgcolor="rgba(0,0,0,0)",
                geo=dict(showframe=False, showcoastlines=False),
            )
            st.plotly_chart(
                fig_map,
                use_container_width=True,
                config={"displayModeBar": False},
            )

            # ── RANKING PROVINSI ────────────────────────────────────────
            st.markdown(
                '<div class="section-title">🔥 Ranking Provinsi Rawan</div>',
                unsafe_allow_html=True,
            )
            st.markdown(
                '<div class="chart-caption">'
                'Top 10 provinsi berdasarkan risk score (Tinggi×3 + Sedang×2 + Rendah×1).'
                '</div>',
                unsafe_allow_html=True,
            )
            df_rank = (
                prov_stats
                .sort_values("Risk_Score", ascending=False)
                .head(10)
                .reset_index(drop=True)
            )
            df_rank.index = df_rank.index + 1
            df_rank = df_rank.rename(columns={
                "Prov_Map":      "Provinsi",
                "Total":         "Total",
                "Tinggi":        "🔴 Tinggi",
                "Sedang":        "🟡 Sedang",
                "Rendah":        "🟢 Rendah",
                "Topik_Dominan": "Topik Dominan",
                "Risk_Score":    "Risk Score",
            })[["Provinsi", "Total", "🔴 Tinggi", "🟡 Sedang", "🟢 Rendah",
                "Topik Dominan", "Risk Score"]]

            st.dataframe(
                df_rank,
                use_container_width=True,
                hide_index=False,
                column_config={
                    "Risk Score": st.column_config.ProgressColumn(
                        "Risk Score",
                        min_value=0,
                        max_value=int(df_rank["Risk Score"].max()),
                        format="%d",
                    ),
                },
            )
            st.markdown("<div style='height:20px;'></div>", unsafe_allow_html=True)

        elif not prov_stats.empty:
            # Fallback: GeoJSON gagal load atau tidak tersedia → bar chart horizontal
            st.warning("Peta tidak dapat dimuat. Menampilkan chart alternatif.")
            top_prov = prov_stats.sort_values("Risk_Score", ascending=False).head(15)
            fig_fallback = go.Figure(go.Bar(
                x=top_prov["Risk_Score"].tolist(),
                y=top_prov["Prov_Map"].tolist(),
                orientation="h",
                marker=dict(
                    color=top_prov["Risk_Score"].tolist(),
                    colorscale=[[0, "#22c55e"], [0.5, "#f59e0b"], [1, "#ef4444"]],
                    showscale=False,
                ),
                text=[str(v) for v in top_prov["Risk_Score"].tolist()],
                textposition="outside",
            ))
            fig_fallback.update_layout(
                height=420,
                margin=dict(l=10, r=40, t=6, b=20),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                yaxis=dict(autorange="reversed", title=""),
                xaxis=dict(title="Risk Score", showgrid=True,
                           gridcolor="rgba(148,163,184,0.20)"),
            )
            st.plotly_chart(fig_fallback, use_container_width=True,
                            config={"displayModeBar": False})
            st.markdown("<div style='height:20px;'></div>", unsafe_allow_html=True)

        # ── FILTER DRILL-DOWN ───────────────────────────────────────────
        provinsi_options = ["SEMUA"]
        if "Provinsi" in df_region_all.columns:
            provinsi_values = sorted([
                x for x in df_region_all["Provinsi"].astype(str).fillna("").unique()
                if x.strip() != ""
            ])
            provinsi_options += provinsi_values

        r1, r2 = st.columns([1.2, 1.2])

        with r1:
            selected_prov = st.selectbox("Filter Provinsi", provinsi_options, key="prov_filter")

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

        total_region  = len(df_region)
        tinggi_region = int((df_region["Prioritas"] == "PRIORITAS TINGGI").sum()) if "Prioritas" in df_region.columns else 0
        sedang_region = int((df_region["Prioritas"] == "PRIORITAS SEDANG").sum()) if "Prioritas" in df_region.columns else 0
        rendah_region = int((df_region["Prioritas"] == "PRIORITAS RENDAH").sum()) if "Prioritas" in df_region.columns else 0

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total Berita",     total_region)
        c2.metric("Prioritas Tinggi", tinggi_region)
        c3.metric("Prioritas Sedang", sedang_region)
        c4.metric("Prioritas Rendah", rendah_region)

        st.markdown("<div style='height:12px;'></div>", unsafe_allow_html=True)

        lcol, rcol = st.columns([1, 1], gap="large")

        with lcol:
            st.markdown('<div class="section-title">Topik Dominan Wilayah</div>', unsafe_allow_html=True)
            if not df_region.empty and "Topik" in df_region.columns:
                topik_region = df_region["Topik"].value_counts().head(5)
                if not topik_region.empty:
                    fig_reg = go.Figure()
                    fig_reg.add_trace(go.Bar(
                        x=topik_region.values.tolist(),
                        y=[clean_label(x) for x in topik_region.index.tolist()],
                        orientation="h",
                        text=[f"{v:,}" for v in topik_region.values.tolist()],
                        textposition="outside",
                        marker=dict(color="#06b6d4"),
                    ))
                    fig_reg.update_layout(
                        height=320,
                        margin=dict(l=10, r=45, t=6, b=20),
                        paper_bgcolor="rgba(0,0,0,0)",
                        plot_bgcolor="rgba(0,0,0,0)",
                        showlegend=False,
                        yaxis=dict(autorange="reversed", title=""),
                        xaxis=dict(title="Jumlah Berita", showgrid=True,
                                   gridcolor="rgba(148,163,184,0.20)"),
                    )
                    st.plotly_chart(fig_reg, use_container_width=True,
                                    config={"displayModeBar": False})
                else:
                    st.info("Belum ada topik wilayah.")
            else:
                st.info("Tidak ada data pada wilayah terpilih.")

        with rcol:
            st.markdown('<div class="section-title">Prioritas Wilayah</div>', unsafe_allow_html=True)
            if not df_region.empty and "Prioritas" in df_region.columns:
                prio_region = df_region["Prioritas"].value_counts().reindex(
                    ["PRIORITAS TINGGI", "PRIORITAS SEDANG", "PRIORITAS RENDAH"]
                ).fillna(0).astype(int)

                fig_pr = go.Figure()
                fig_pr.add_trace(go.Bar(
                    x=["Tinggi", "Sedang", "Rendah"],
                    y=prio_region.values.tolist(),
                    marker=dict(color=["#ef4444", "#f59e0b", "#22c55e"]),
                    text=[f"{v:,}" for v in prio_region.values.tolist()],
                    textposition="outside",
                ))
                fig_pr.update_layout(
                    height=320,
                    margin=dict(l=10, r=20, t=6, b=20),
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    showlegend=False,
                    yaxis=dict(title="Jumlah Berita", showgrid=True,
                               gridcolor="rgba(148,163,184,0.20)"),
                )
                st.plotly_chart(fig_pr, use_container_width=True,
                                config={"displayModeBar": False})
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
                    df_region = df_region.sort_values(
                        ["Score_num", "Waktu_Publish_WIB_dt"], ascending=[False, False])
                else:
                    df_region = df_region.sort_values(["Score_num"], ascending=[False])
            elif "Waktu_Publish_WIB" in df_region.columns:
                df_region["Waktu_Publish_WIB_dt"] = normalize_datetime_col(df_region, "Waktu_Publish_WIB")
                df_region = df_region.sort_values("Waktu_Publish_WIB_dt", ascending=False)

            for _, row in df_region.head(20).iterrows():
                judul    = escape(clean_label(row.get("Judul", "-")))
                media    = escape(clean_label(row.get("Media", "-")))
                waktu    = escape(clean_label(row.get("Waktu_Publish_WIB", row.get("Tanggal", "-"))))
                prioritas = str(row.get("Prioritas", "PRIORITAS RENDAH")).strip()
                topik    = escape(clean_label(row.get("Topik_Utama", row.get("Topik", ""))))
                alasan   = escape(clean_label(row.get("Alasan_Prioritas", "")))
                link     = str(row.get("Link", "")).strip()
                lokasi   = escape(clean_label(
                    str(row.get("Kabupaten_Kota", "") or "").strip()
                    or str(row.get("Provinsi", "") or "").strip()
                    or "-"
                ))
                link_html = (
                    f"<div class='news-link'><a href='{escape(link, quote=True)}' "
                    f"target='_blank'>Baca berita</a></div>"
                    if link else ""
                )
                st.markdown(
                    f"""
                    <div class="news-card">
                        <div style="display:flex; justify-content:space-between;
                                    gap:12px; flex-wrap:wrap; align-items:flex-start;">
                            <div style="flex:1; min-width:250px;">
                                <div class="news-title">{judul}</div>
                                <div class="news-meta">{media} • {waktu} • {lokasi}</div>
                            </div>
                            <div>{badge_html(prioritas)}</div>
                        </div>
                        <div style='margin:8px 0 10px 0;'>
                            <span class='news-chip'>Topik: {topik}</span>
                        </div>
                        <div style="font-size:.95rem; line-height:1.65; margin-bottom:8px;">{alasan}</div>
                        {link_html}
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
        else:
            st.info("Tidak ada berita pada wilayah terpilih.")

# ===============================
# TAB: PANDUAN
# ===============================
with tab_info:
    st.markdown('<div class="section-title">Panduan Sistem Early Warning System</div>', unsafe_allow_html=True)

    st.markdown(
        """
Sistem **Early Warning System (EWS) Isu Ketenagakerjaan** digunakan untuk memantau perkembangan isu ketenagakerjaan di media online serta menganalisis potensi dampaknya terhadap program jaminan sosial ketenagakerjaan.
"""
    )

    st.markdown("<br>", unsafe_allow_html=True)

    # ===============================
    # DASHBOARD
    # ===============================
    with st.expander("📊 Tab Dashboard", expanded=True):
        st.markdown(
            """
Dashboard menampilkan gambaran umum kondisi isu ketenagakerjaan.

**Komponen utama:**
- Total Berita RAW  
- Berita Teranalisis  
- Prioritas Tinggi / Sedang / Rendah  
- Isu Paling Kritis Hari Ini  
- Distribusi Prioritas  
- Topik Dominan  
- Top 5 Berita Prioritas Tinggi  
- Analisis Situasi  
"""
        )

    # ===============================
    # DATA BERITA
    # ===============================
    with st.expander("📰 Tab Data Berita"):
        st.markdown(
            """
Menampilkan seluruh berita hasil analisis dalam bentuk tabel.

**Fungsi utama:**
- Melihat detail berita  
- Filter berdasarkan prioritas  
- Filter kategori berita  
- Menelusuri sumber dan waktu berita  
"""
        )

    # ===============================
    # ANALISIS DAERAH
    # ===============================
    with st.expander("📍 Tab Analisis Daerah"):
        st.markdown(
            """
Menampilkan distribusi isu berdasarkan wilayah.

**Manfaat:**
- Mengidentifikasi wilayah dengan isu tertinggi  
- Melihat persebaran isu secara geografis  
- Menentukan fokus pengawasan wilayah  
"""
        )

    # ===============================
    # CARA KERJA SISTEM
    # ===============================
    with st.expander("⚙️ Cara Kerja Sistem"):
        st.markdown(
            """
**1. Scraping (RAW)**  
Mengambil berita dari berbagai media online.

**2. Filtering (FILTERED)**  
Menyaring berita berdasarkan kata kunci ketenagakerjaan.

**3. Analisis (ANALYZED)**  
Menentukan:
- Topik utama  
- Lokasi  
- Dampak program  
- Skor  
- Prioritas  

**4. Visualisasi Dashboard**  
Menampilkan hasil analisis dalam bentuk grafik dan ringkasan.
"""
        )

    # ===============================
    # PRIORITAS
    # ===============================
    with st.expander("🚨 Penentuan Prioritas"):
        st.markdown(
            """
**Prioritas Tinggi**
- PHK massal  
- Kecelakaan kerja fatal  
- Konflik besar  

**Prioritas Sedang**
- Isu berkembang  
- Dampak terbatas  

**Prioritas Rendah**
- Edukasi layanan  
- Informasi umum  
- Berita global  
"""
        )

    # ===============================
    # ESKALASI
    # ===============================
    with st.expander("📈 Indeks Eskalasi Isu"):
        st.markdown(
            """
Membandingkan kondisi 24 jam terakhir dengan periode sebelumnya:

- 📈 Naik → isu meningkat  
- 📉 Turun → isu menurun  
- ➖ Stabil → tidak ada perubahan signifikan  

Semakin tinggi eskalasi, semakin perlu perhatian lebih lanjut.
"""
        )

    # ===============================
    # CATATAN
    # ===============================
    with st.expander("📌 Catatan Penting"):
        st.markdown(
            """
- Jika **RAW ada tetapi ANALYZED kosong**, berarti tidak ada berita yang lolos analisis  
- Gunakan tombol **Update Data** untuk memperbarui data  
- Sistem ini bersifat **early warning**, bukan keputusan final  
"""
        )