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
  <p class="ews-sub">Monitoring Isu Jaminan Sosial Ketenagakerjaan Berbasis Analisis Regulasi</p>
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

def safe_text(val, default=""):
    if pd.isna(val):
        return default
    return str(val).strip()

def pick_first_existing_sheet(key: str, names: list[str]) -> pd.DataFrame:
    for name in names:
        try:
            df = read_sheet(key, name)
            if df is not None:
                return df
        except Exception:
            continue
    return pd.DataFrame()

def normalize_priority(val: str) -> str:
    v = safe_text(val).upper()
    if "TINGGI" in v:
        return "PRIORITAS TINGGI"
    if "SEDANG" in v:
        return "PRIORITAS SEDANG"
    if "RENDAH" in v:
        return "PRIORITAS RENDAH"
    return v or "PRIORITAS RENDAH"

def badge_html(prioritas):
    if prioritas == "PRIORITAS TINGGI":
        return "<span class='badge badge-high'>Prioritas Tinggi</span>"
    elif prioritas == "PRIORITAS SEDANG":
        return "<span class='badge badge-mid'>Prioritas Sedang</span>"
    return "<span class='badge badge-low'>Prioritas Rendah</span>"

# ===============================
# LOAD DATA
# ===============================
@st.cache_data(ttl=300, show_spinner=False)
def load_sheet_cached(key: str, tab: str) -> pd.DataFrame:
    return read_sheet(key, tab)

raw = pick_first_existing_sheet(SHEET_KEY, ["RAW", "RAW_NEWS"])
hasil = pick_first_existing_sheet(SHEET_KEY, ["HASIL_ANALISIS", "FILTERED"])

raw.columns = raw.columns.astype(str).str.strip() if not raw.empty else pd.Index([])
hasil.columns = hasil.columns.astype(str).str.strip() if not hasil.empty else pd.Index([])

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
    elif "Tanggal_Berita" in df.columns:
        s = pd.to_datetime(df["Tanggal_Berita"], errors="coerce")
    elif "Tanggal" in df.columns:
        s = pd.to_datetime(df["Tanggal"], errors="coerce", utc=True)
        try:
            s = s.dt.tz_convert("Asia/Jakarta")
        except Exception:
            pass
    elif "Tanggal_Ambil" in df.columns:
        s = pd.to_datetime(df["Tanggal_Ambil"], errors="coerce")
    else:
        s = pd.Series([pd.NaT] * len(df))

    s = pd.to_datetime(s, errors="coerce")
    df = df.copy()
    df["Tanggal_Hari"] = s.dt.date
    df = df.dropna(subset=["Tanggal_Hari"]).copy()
    return df

raw = ensure_publish_date(raw)
hasil = ensure_publish_date(hasil)

if raw.empty:
    st.warning("Data RAW belum tersedia.")
    st.stop()

min_date = raw["Tanggal_Hari"].min()
max_date = raw["Tanggal_Hari"].max()

date_range = (min_date, max_date)
filter_option = "SEMUA"

# ===============================
# KONTROL UTAMA
# ===============================
st.markdown('<div class="section-title">Kontrol Data</div>', unsafe_allow_html=True)

c_ctrl1, c_ctrl2, c_ctrl3 = st.columns([1.2, 2.2, 1.5])

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

# ===============================
# TOPIC DETECTION FALLBACK
# ===============================
TOPIC_RULES = {
    "PHK": [r"\bphk\b", r"pemutusan hubungan kerja", r"\bdirumahkan\b", r"phk massal"],
    "THR / Kesejahteraan Pekerja": [r"\bthr\b", r"tunjangan hari raya", r"pengaduan thr"],
    "Upah / Gaji": [r"\bupah\b", r"\bgaji\b", r"ump", r"umk", r"upah minimum"],
    "Aksi / Demo Buruh": [r"\bdemo\b", r"unjuk rasa", r"aksi buruh", r"mogok"],
    "Konflik Hubungan Industrial": [r"perselisihan", r"konflik buruh", r"sengketa"],
    "Pabrik Tutup / Pailit": [r"pabrik tutup", r"\bpailit\b", r"\bbangkrut\b"],
    "Kepesertaan BPJS": [r"bpjs ketenagakerjaan", r"bpjamsostek", r"jamsostek"],
    "Klaim JHT": [r"\bjht\b", r"jaminan hari tua", r"klaim jht", r"pencairan jht"],
    "Manfaat JKP": [r"\bjkp\b", r"jaminan kehilangan pekerjaan", r"manfaat jkp"],
    "Jaminan Pensiun (JP)": [r"\bjp\b", r"jaminan pensiun", r"manfaat pensiun"],
    "Kecelakaan Kerja (JKK)": [r"\bjkk\b", r"jaminan kecelakaan kerja", r"kecelakaan kerja", r"ledakan pabrik"],
    "Santunan Kematian (JKM)": [r"\bjkm\b", r"jaminan kematian", r"santunan kematian", r"meninggal dunia"],
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

hasil_display = hasil[
    (hasil["Tanggal_Hari"] >= start_date) &
    (hasil["Tanggal_Hari"] <= end_date)
].copy() if not hasil.empty else pd.DataFrame()

if not hasil_display.empty:
    if "Prioritas" in hasil_display.columns:
        hasil_display["Prioritas"] = hasil_display["Prioritas"].apply(normalize_priority)

    if "Kategori_Isu" not in hasil_display.columns or hasil_display["Kategori_Isu"].astype(str).str.strip().eq("").all():
        combo = (
            hasil_display.get("Judul", "").astype(str) + " " +
            hasil_display.get("Ringkasan", "").astype(str)
        )
        hasil_display["Kategori_Isu"] = combo.apply(detect_topic)

filtered_for_table = hasil_display.copy()
if filter_option != "SEMUA" and "Prioritas" in filtered_for_table.columns:
    filtered_for_table = filtered_for_table[
        filtered_for_table["Prioritas"] == filter_option
    ].copy()

# ===============================
# TABS
# ===============================
tab_dash, tab_data, tab_info = st.tabs(["📊 Dashboard", "📰 Data Berita", "📘 Panduan"])

# ===============================
# TAB: DASHBOARD
# ===============================
with tab_dash:
    if hasil_display.empty or "Prioritas" not in hasil_display.columns:
        st.error("Data HASIL_ANALISIS belum tersedia. Klik 🔄 Update Data dulu.")
        st.stop()

    tinggi = int((hasil_display["Prioritas"] == "PRIORITAS TINGGI").sum())
    sedang = int((hasil_display["Prioritas"] == "PRIORITAS SEDANG").sum())
    rendah = int((hasil_display["Prioritas"] == "PRIORITAS RENDAH").sum())

    total_berita = len(raw_filtered)
    total_isu = len(hasil_display)
    total_regulasi = int(
        hasil_display.get("Rujukan_Tampilan", pd.Series(dtype=str))
        .astype(str).str.strip().ne("").sum()
    )
    total_tidak_terpetakan = int(
        hasil_display.get("Kategori_Isu", pd.Series(dtype=str))
        .astype(str).str.contains("Tidak Terpetakan", case=False, na=False).sum()
    )

    c1, c2, c3, c4, c5, c6, c7 = st.columns([1.25, 1.25, 1, 1, 1, 1, 1], gap="medium")

    with c1:
        st.markdown(
            f"""
            <div class="kpi-card">
              <div class="kpi-title">Total Berita Raw</div>
              <div class="kpi-value">{total_berita:,}</div>
              <div class="kpi-sub">Sesuai rentang tanggal</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with c2:
        st.markdown(
            f"""
            <div class="kpi-card">
              <div class="kpi-title">Isu Teranalisis</div>
              <div class="kpi-value">{total_isu:,}</div>
              <div class="kpi-sub">Data hasil analisis EWS</div>
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

    with c6:
        st.markdown(
            f"""
            <div class="kpi-card">
              <div class="kpi-title">Dasar Aturan Aktif</div>
              <div class="kpi-value">{total_regulasi:,}</div>
              <div class="kpi-sub">Berita dengan rujukan regulasi</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with c7:
        st.markdown(
            f"""
            <div class="kpi-card">
              <div class="kpi-title">Belum Terpetakan</div>
              <div class="kpi-value">{total_tidak_terpetakan:,}</div>
              <div class="kpi-sub">Perlu penyempurnaan mapping</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    st.markdown("<div style='height:14px;'></div>", unsafe_allow_html=True)

    left, right = st.columns([1.05, 0.95], gap="large")

    with left:
        st.markdown('<div class="section-title">Distribusi Prioritas</div>', unsafe_allow_html=True)

        priority_counts = hasil_display["Prioritas"].value_counts()
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
        st.markdown('<div class="section-title">Top 5 Berita Prioritas Tinggi</div>', unsafe_allow_html=True)

        df_high = hasil_display[
            hasil_display["Prioritas"] == "PRIORITAS TINGGI"
        ].copy()

        if not df_high.empty:
            for c in ["Skor_Akhir", "Waktu_Publish_WIB", "Tanggal_Publish", "Tanggal_Ambil"]:
                if c in df_high.columns:
                    try:
                        df_high = df_high.sort_values(c, ascending=False)
                        break
                    except Exception:
                        pass

            top5 = df_high.head(5)

            for _, row in top5.iterrows():
                media = escape(safe_text(row.get("Media", "-")))
                judul = escape(safe_text(row.get("Judul", "-")))
                link = safe_text(row.get("Link", row.get("URL", "")))
                waktu = escape(safe_text(row.get("Waktu_Publish_WIB", row.get("Tanggal_Berita", row.get("Tanggal_Ambil", "")))))
                regulasi = escape(safe_text(row.get("Rujukan_Tampilan", "")))

                regulasi_html = f"<div class='top5-meta'><b>Dasar aturan:</b> {regulasi}</div>" if regulasi else ""

                if link:
                    st.markdown(
                        f"""
                        <div class="news-card">
                            <div class="news-title">
                                <a href="{escape(link, quote=True)}" target="_blank" style="text-decoration:none; color:inherit;">{judul}</a>
                            </div>
                            <div class="news-meta">{media} • {waktu}</div>
                            {regulasi_html}
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
                else:
                    st.markdown(
                        f"""
                        <div class="news-card">
                            <div class="news-title">{judul}</div>
                            <div class="news-meta">{media} • {waktu}</div>
                            {regulasi_html}
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
        else:
            st.info("Belum ada berita prioritas tinggi.")

        st.markdown("<div style='height:12px;'></div>", unsafe_allow_html=True)
        st.markdown('<div class="section-title">Regulasi Paling Sering Muncul</div>', unsafe_allow_html=True)

        reg_series = hasil_display.get("Rujukan_Tampilan", pd.Series(dtype=str)).astype(str).str.strip()
        reg_series = reg_series[reg_series != ""]
        if not reg_series.empty:
            reg_counts = reg_series.value_counts().head(5)
            reg_df = pd.DataFrame({
                "Rujukan Regulasi": reg_counts.index,
                "Jumlah Berita": reg_counts.values
            })
            st.dataframe(reg_df, use_container_width=True, hide_index=True)
        else:
            st.info("Belum ada data regulasi yang terpetakan.")

    with right:
        st.markdown('<div class="section-title">🧠 Analisis Situasi</div>', unsafe_allow_html=True)

        total = len(hasil_display)

        if tinggi > 3:
            status_txt = "🔴 RISIKO TINGGI"
            kondisi = "menunjukkan eskalasi signifikan isu ketenagakerjaan"
            rekomendasi = "Perlu mitigasi cepat, koordinasi lintas unit, dan pemantauan harian terhadap isu prioritas."
        elif tinggi > 0:
            status_txt = "🟡 WASPADA"
            kondisi = "menunjukkan potensi peningkatan risiko ketenagakerjaan"
            rekomendasi = "Perlu pemantauan intensif, klarifikasi lapangan, dan identifikasi dini terhadap isu prioritas."
        else:
            status_txt = "🟢 STABIL"
            kondisi = "relatif stabil tanpa indikasi eskalasi besar"
            rekomendasi = "Pemantauan rutin tetap diperlukan sebagai langkah preventif."

        if "Kategori_Isu" in hasil_display.columns and not hasil_display.empty:
            topik_counts = hasil_display["Kategori_Isu"].astype(str).str.strip().replace("", "Tidak Terpetakan").value_counts()
            top3 = topik_counts.head(3)
            topik_list = [f"- **{clean_label(topic)}** ({count} berita)" for topic, count in top3.items()]
            topik_text = "\n".join(topik_list)
            topik_utama = [str(x) for x in top3.index.tolist()]
        else:
            topik_text = "- **Belum ada topik dominan**"
            topik_utama = []

        regulasi_dominan = ""
        reg_counts = hasil_display.get("Rujukan_Tampilan", pd.Series(dtype=str)).astype(str).str.strip()
        reg_counts = reg_counts[reg_counts != ""]
        if not reg_counts.empty:
            regulasi_dominan = reg_counts.value_counts().index[0]

        ringkasan = []
        if any("PHK" in x.upper() for x in topik_utama):
            ringkasan.append(
                "Dominasi isu **PHK** menunjukkan potensi tekanan pada keberlanjutan hubungan kerja, kesinambungan kepesertaan, dan peningkatan klaim manfaat pasca pemutusan hubungan kerja."
            )
        if any("KECELAKAAN" in x.upper() or "JKK" in x.upper() for x in topik_utama):
            ringkasan.append(
                "Munculnya isu **kecelakaan kerja** menunjukkan perlunya perhatian pada sektor berisiko tinggi karena berpotensi menambah klaim JKK dan pada kasus fatal juga dapat memicu JKM."
            )
        if any("KEPESERTAAN" in x.upper() or "BPJS" in x.upper() for x in topik_utama):
            ringkasan.append(
                "Isu **kepesertaan BPJS Ketenagakerjaan** menunjukkan pentingnya pengawasan terhadap perluasan cakupan perlindungan dan kepatuhan perusahaan mendaftarkan pekerja."
            )
        if not ringkasan:
            ringkasan.append(
                "Isu yang berkembang masih bersifat campuran, namun tetap perlu dipantau karena dapat mempengaruhi stabilitas ketenagakerjaan dan perlindungan jaminan sosial."
            )

        if regulasi_dominan:
            regulasi_text = f"Rujukan regulasi yang paling sering muncul pada periode ini adalah **{clean_label(regulasi_dominan)}**."
        else:
            regulasi_text = "Belum seluruh isu memiliki pemetaan dasar aturan, sehingga penyempurnaan register regulasi masih diperlukan."

        st.markdown(
            f"""
<div class="news-card" style="line-height:1.75;">
<b>Status:</b> {status_txt}<br><br>

Total isu teranalisis: <b>{total:,} berita</b><br>
Prioritas tinggi: <b>{tinggi:,}</b><br>
Prioritas sedang: <b>{sedang:,}</b><br>
Prioritas rendah: <b>{rendah:,}</b><br><br>

Isu dominan pada periode ini:<br>
{topik_text}<br><br>

Secara umum, kondisi saat ini <b>{kondisi}</b>.<br><br>

{" ".join(ringkasan[:2])}<br><br>

{regulasi_text}<br><br>

<b>Rekomendasi:</b> {rekomendasi}
</div>
""",
            unsafe_allow_html=True
        )

# ===============================
# TAB: DATA BERITA
# ===============================
with tab_data:
    st.markdown('<div class="section-title">Berita Terkini</div>', unsafe_allow_html=True)
    st.caption("Daftar 10 berita terbaru berdasarkan prioritas, kategori isu, dan dasar aturan.")

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

    sort_col = None
    for c in ["Skor_Akhir", "Waktu_Publish_WIB", "Tanggal_Publish", "Tanggal_Berita", "Tanggal_Ambil", "Tanggal_Hari"]:
        if c in df_display.columns:
            sort_col = c
            break
    if sort_col is None:
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
        link = safe_text(row.get("Link", row.get("URL", "")))
        waktu = escape(clean_label(row.get("Waktu_Publish_WIB", row.get("Tanggal_Berita", row.get("Tanggal_Ambil", "-")))))
        prioritas = normalize_priority(row.get("Prioritas", "PRIORITAS RENDAH"))

        kategori_isu = escape(clean_label(row.get("Kategori_Isu", "")))
        dampak_program = escape(clean_label(row.get("Dampak_Program", row.get("Program_Terdampak", ""))))
        dampak_kepesertaan = escape(clean_label(row.get("Dampak_Kepesertaan", "")))
        potensi_klaim = escape(clean_label(row.get("Potensi_Klaim", "")))
        alasan = escape(clean_label(row.get("Alasan_Prioritas", row.get("Analisis_Regulatif", ""))))
        regulasi = escape(clean_label(row.get("Rujukan_Tampilan", "")))
        analisis_reg = escape(clean_label(row.get("Analisis_Regulatif", "")))

        chips = []
        if kategori_isu:
            chips.append(f"<span class='news-chip'>{kategori_isu}</span>")
        if dampak_program:
            chips.append(f"<span class='news-chip'>{dampak_program}</span>")
        if dampak_kepesertaan:
            chips.append(f"<span class='news-chip'>{dampak_kepesertaan}</span>")
        if potensi_klaim:
            chips.append(f"<span class='news-chip'>Klaim: {potensi_klaim}</span>")

        link_html = ""
        if link:
            safe_link = escape(link, quote=True)
            link_html = f"<div class='news-link'><a href='{safe_link}' target='_blank'>Baca berita</a></div>"

        regulasi_html = ""
        if regulasi:
            regulasi_html = f"<div style='font-size:.9rem; line-height:1.65; margin-bottom:8px;'><b>Dasar aturan:</b> {regulasi}</div>"

        analisis_html = ""
        if analisis_reg:
            analisis_html = f"<div style='font-size:.92rem; line-height:1.65; margin-bottom:10px;'><b>Analisis regulatif:</b> {analisis_reg}</div>"

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
            f"{regulasi_html}"
            f"{analisis_html}"
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

    df_ews = hasil_display.copy()

    if "Kategori_Isu" not in df_ews.columns:
        combo = (
            df_ews.get("Judul", "").astype(str) + " " +
            df_ews.get("Ringkasan", "").astype(str)
        )
        df_ews["Kategori_Isu"] = combo.apply(detect_topic)

    if "Waktu_Publish_WIB" in df_ews.columns:
        df_ews["publish_dt"] = pd.to_datetime(df_ews["Waktu_Publish_WIB"], errors="coerce")
    elif "Tanggal_Publish" in df_ews.columns:
        df_ews["publish_dt"] = pd.to_datetime(df_ews["Tanggal_Publish"], errors="coerce")
    elif "Tanggal_Berita" in df_ews.columns:
        df_ews["publish_dt"] = pd.to_datetime(df_ews["Tanggal_Berita"], errors="coerce")
    else:
        df_ews["publish_dt"] = pd.to_datetime(df_ews["Tanggal_Hari"], errors="coerce")

    df_ews = df_ews.dropna(subset=["publish_dt"]).copy()

    now = pd.Timestamp.now(tz="Asia/Jakarta").tz_localize(None)
    w1_start = now - pd.Timedelta(hours=24)
    w0_start = now - pd.Timedelta(hours=48)

    w1 = df_ews[df_ews["publish_dt"] >= w1_start].copy()
    w0 = df_ews[(df_ews["publish_dt"] >= w0_start) & (df_ews["publish_dt"] < w1_start)].copy()

    def agg(df_recent):
        if df_recent.empty:
            return pd.DataFrame(columns=["Kategori_Isu", "Berita 24 Jam", "Media 24 Jam", "Headline"])

        out = df_recent.groupby("Kategori_Isu", dropna=False).agg(
            **{
                "Berita 24 Jam": ("Judul", "count"),
                "Media 24 Jam": ("Media", pd.Series.nunique)
            }
        ).reset_index()

        head = (
            df_recent.sort_values("publish_dt", ascending=False)
            .groupby("Kategori_Isu", dropna=False)
            .head(1)[["Kategori_Isu", "Judul"]]
            .rename(columns={"Judul": "Headline"})
        )

        return out.merge(head, on="Kategori_Isu", how="left")

    s1 = agg(w1)
    s0 = agg(w0).rename(columns={
        "Berita 24 Jam": "Berita 24-48 Jam",
        "Media 24 Jam": "Media 24-48 Jam"
    })

    esk = s1.merge(
        s0[["Kategori_Isu", "Berita 24-48 Jam", "Media 24-48 Jam"]],
        on="Kategori_Isu",
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
        esk["Kategori_Isu"] = esk["Kategori_Isu"].astype(str).apply(clean_label)
        esk = esk.sort_values(["Skor", "Media 24 Jam", "Berita 24 Jam"], ascending=False)

        st.dataframe(
            esk[
                ["Kategori_Isu", "Trend", "Media 24 Jam", "Berita 24 Jam",
                 "Media 24-48 Jam", "Berita 24-48 Jam", "Skor", "Headline"]
            ].head(10),
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("Belum ada data yang cukup untuk menghitung indeks eskalasi isu.")

# ===============================
# TAB: PANDUAN
# ===============================
with tab_info:
    st.markdown('<div class="section-title">Panduan Sistem Early Warning System</div>', unsafe_allow_html=True)

    st.markdown(
"""
<div class="info-card">
<div class="info-text">

Sistem <b>Early Warning System (EWS) Isu Ketenagakerjaan</b> digunakan untuk memantau perkembangan isu ketenagakerjaan di media online serta menganalisis potensi dampaknya terhadap program jaminan sosial ketenagakerjaan <b>berdasarkan kategori isu dan dasar aturan yang relevan</b>.

<br><br>

<b>1. Pengumpulan Data Berita (Scraping Media Online)</b><br>
Sistem secara otomatis mengambil berita dari berbagai media online yang memuat isu ketenagakerjaan. Data yang dikumpulkan meliputi judul berita, media sumber, waktu publikasi, ringkasan, dan tautan berita asli.

<br><br>

<b>2. Penyaringan Isu Ketenagakerjaan (Keyword Filtering)</b><br>
Seluruh berita yang terkumpul kemudian disaring menggunakan kata kunci yang berkaitan dengan isu ketenagakerjaan dan jaminan sosial tenaga kerja. Hanya berita yang relevan yang diproses lebih lanjut.

<br><br>

<b>3. Identifikasi Kategori Isu</b><br>
Setelah berita lolos tahap penyaringan, sistem melakukan analisis untuk mengidentifikasi kategori isu utama, misalnya PHK, kecelakaan kerja, kepesertaan BPJS Ketenagakerjaan, jaminan hari tua, jaminan kehilangan pekerjaan, pekerja migran, dan isu hubungan industrial.

<br><br>

<b>4. Analisis Dampak terhadap Program Jaminan Sosial</b><br>
Setiap berita dianalisis untuk melihat potensi dampaknya terhadap program BPJS Ketenagakerjaan, antara lain JHT, JKK, JKM, JKP, dan JP. Analisis ini membantu mengidentifikasi dampak terhadap kepesertaan, klaim, dan perlindungan pekerja.

<br><br>

<b>5. Pemetaan Dasar Aturan</b><br>
Sistem kemudian menghubungkan kategori isu dengan register regulasi aktif yang telah disusun dalam <b>MASTER_REGULASI</b>. Dengan cara ini, setiap isu dapat ditampilkan bersama aturan induk, aturan teknis, topik norma, dan rujukan regulasi yang relevan. Aturan yang sudah tidak aktif tidak digunakan sebagai dasar analisis.

<br><br>

<b>6. Penentuan Prioritas Berita</b><br>
Setiap berita diklasifikasikan berdasarkan skor isu, bobot hukum, dan indikator eskalasi menjadi tiga kategori: <b>Prioritas Tinggi</b>, <b>Prioritas Sedang</b>, dan <b>Prioritas Rendah</b>.

<br><br>

<b>7. Dashboard Monitoring Isu</b><br>
Hasil analisis ditampilkan dalam dashboard yang memuat total berita raw, jumlah isu teranalisis, distribusi prioritas, daftar berita prioritas tinggi, regulasi yang paling sering muncul, serta analisis situasi.

<br><br>

<b>8. Indeks Eskalasi Isu</b><br>
Indeks eskalasi digunakan untuk memantau perkembangan intensitas isu berdasarkan jumlah berita dalam 24 jam terakhir, jumlah media yang memberitakan, serta tren peningkatan atau penurunan isu.

<br><br>

<b>Catatan Penting</b><br>
Analisis regulatif dalam dashboard bersifat <b>indikatif</b> dan digunakan untuk kebutuhan pemantauan dini. Sistem tidak menyimpulkan pelanggaran hukum secara final, tetapi menunjukkan keterkaitan isu dengan norma hukum dan program jaminan sosial ketenagakerjaan yang relevan.

</div>
</div>
""",
        unsafe_allow_html=True
    )