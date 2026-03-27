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
header[data-testid="stHeader"] {
    display: none;
}

div[data-testid="stToolbar"] {
    display: none;
}

#MainMenu {
    visibility: hidden;
}

footer {
    visibility: hidden;
}

:root {
    --bg-light: #f5f7fb;
    --card-light: rgba(255,255,255,0.78);
    --text-light: #101828;
    --line-light: rgba(16,24,40,0.08);

    --bg-dark: #0b1120;
    --card-dark: rgba(17,25,40,0.78);
    --text-dark: #e5e7eb;
    --line-dark: rgba(255,255,255,0.08);
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
    .ews-sub {
        color: #94a3b8;
    }
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

.kpi-card {
    padding: 16px 18px;
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
    .kpi-title, .kpi-sub {
        color: #94a3b8;
    }
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
.badge-high {
    background: linear-gradient(135deg, #ef4444, #dc2626);
}
.badge-mid {
    background: linear-gradient(135deg, #f59e0b, #d97706);
}
.badge-low {
    background: linear-gradient(135deg, #22c55e, #16a34a);
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
.news-link a:hover {
    text-decoration: underline;
}
@media (prefers-color-scheme: dark) {
    .news-meta {
        color: #94a3b8;
    }
    .news-chip {
        background: rgba(129,140,248,.18);
        color: #c7d2fe;
    }
    .news-link a {
        color: #a5b4fc;
    }
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
    .kpi-value {
        font-size: 22px;
    }
    .news-card {
        padding: 14px;
    }
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
        return pd.DataFrame()

    s = pd.to_datetime(s, errors="coerce")
    df = df.copy()
    df["Tanggal_Hari"] = s.dt.date
    df = df.dropna(subset=["Tanggal_Hari"]).copy()
    return df

def fallback_detect_topic(text: str) -> str:
    t = str(text or "").lower()

    rules = [
        ("PHK", [r"\bphk\b", r"pemutusan hubungan kerja", r"\bdirumahkan\b"]),
        ("THR / Kesejahteraan Pekerja", [r"\bthr\b", r"tunjangan hari raya"]),
        ("Upah / Gaji", [r"\bupah\b", r"\bgaji\b", r"\bump\b", r"\bumk\b"]),
        ("Aksi / Demo Buruh", [r"\bdemo\b", r"unjuk rasa", r"mogok"]),
        ("Konflik Hubungan Industrial", [r"perselisihan", r"sengketa", r"konflik buruh"]),
        ("Kecelakaan Kerja (JKK)", [r"kecelakaan kerja", r"buruh tewas", r"pekerja tewas"]),
        ("Kepesertaan BPJS", [r"bpjs ketenagakerjaan", r"bpjamsostek"]),
        ("Klaim JHT", [r"\bjht\b", r"jaminan hari tua"]),
        ("Manfaat JKP", [r"\bjkp\b", r"jaminan kehilangan pekerjaan"]),
        ("Jaminan Pensiun (JP)", [r"\bjp\b", r"jaminan pensiun"]),
        ("Pekerja Migran Indonesia (PMI)", [r"\bpmi\b", r"pekerja migran", r"\btki\b"]),
        ("Jasa Konstruksi", [r"konstruksi", r"proyek", r"jasa konstruksi"]),
    ]

    for topic, patterns in rules:
        for p in patterns:
            if re.search(p, t):
                return topic

    return "Lainnya"

# ===============================
# LOAD DATA
# ===============================
raw = load_sheet(SHEET_KEY, "RAW")
filtered = load_sheet(SHEET_KEY, "HASIL_ANALISIS")

if raw is None:
    raw = pd.DataFrame()
if filtered is None:
    filtered = pd.DataFrame()

if not raw.empty:
    raw.columns = raw.columns.astype(str).str.strip()
if not filtered.empty:
    filtered.columns = filtered.columns.astype(str).str.strip()

raw = ensure_publish_date(raw)
filtered = ensure_publish_date(filtered)

if raw.empty:
    st.warning("Data RAW belum tersedia.")
    st.stop()

min_date = raw["Tanggal_Hari"].min()
max_date = raw["Tanggal_Hari"].max()

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

filtered_display = filtered[
    (filtered["Tanggal_Hari"] >= start_date) &
    (filtered["Tanggal_Hari"] <= end_date)
].copy()

if not filtered_display.empty:
    if "Topik_Utama" in filtered_display.columns:
        filtered_display["Topik"] = (
            filtered_display["Topik_Utama"]
            .astype(str)
            .fillna("")
            .replace("", "Lainnya")
        )
    else:
        combo = (
            filtered_display.get("Judul", "").astype(str) + " " +
            filtered_display.get("Ringkasan", "").astype(str)
        )
        filtered_display["Topik"] = combo.apply(fallback_detect_topic)

filtered_for_table = filtered_display.copy()
if filter_option != "SEMUA" and "Prioritas" in filtered_for_table.columns:
    filtered_for_table = filtered_for_table[
        filtered_for_table["Prioritas"] == filter_option
    ].copy()

# ===============================
# TABS
# ===============================
tab_dash, tab_data, tab_info = st.tabs(["📊 Dashboard", "📰 Data Berita", "📘 Panduan"])

# ===============================
# TAB DASHBOARD
# ===============================
with tab_dash:
    if filtered_display.empty or "Prioritas" not in filtered_display.columns:
        st.info("Belum ada data HASIL_ANALISIS. Klik Update Data dulu.")
    else:
        tinggi = int((filtered_display["Prioritas"] == "PRIORITAS TINGGI").sum())
        sedang = int((filtered_display["Prioritas"] == "PRIORITAS SEDANG").sum())
        rendah = int((filtered_display["Prioritas"] == "PRIORITAS RENDAH").sum())

        c1, c2, c3, c4, c5 = st.columns([1.2, 1.2, 1, 1, 1], gap="large")

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
                f"""
                <div class="kpi-card">
                  <div class="kpi-title">Valid untuk Analisis</div>
                  <div class="kpi-value">{len(filtered_display):,}</div>
                  <div class="kpi-sub">Berita valid Indonesia / PMI</div>
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
            else:
                st.info("Belum ada data distribusi prioritas.")

            st.markdown("<div style='height:12px;'></div>", unsafe_allow_html=True)
            st.markdown('<div class="section-title">Top 5 Berita Prioritas Tinggi</div>', unsafe_allow_html=True)

            df_high = filtered_display[
                filtered_display["Prioritas"] == "PRIORITAS TINGGI"
            ].copy()

            if not df_high.empty:
                if "Waktu_Publish_WIB" in df_high.columns:
                    df_high["sort_time"] = pd.to_datetime(df_high["Waktu_Publish_WIB"], errors="coerce")
                    df_high = df_high.sort_values("sort_time", ascending=False)

                top5 = df_high.head(5)

                for _, row in top5.iterrows():
                    media = escape(str(row.get("Media", "-")))
                    judul = escape(str(row.get("Judul", "-")))
                    link = str(row.get("Link", "")).strip()
                    waktu = escape(str(row.get("Waktu_Publish_WIB", "")))

                    if link:
                        st.markdown(
                            f"""
                            <div class="news-card">
                                <div class="news-link">
                                    <a href="{escape(link, quote=True)}" target="_blank">{judul}</a>
                                </div>
                                <div class="news-meta">{media} • {waktu}</div>
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

            topik_counts = filtered_display["Topik"].value_counts()
            top3 = topik_counts.head(3)

            if not top3.empty:
                topik_text = "\n".join(
                    [f"- **{clean_label(topic)}** ({count} berita)" for topic, count in top3.items()]
                )
                topik_utama = top3.index.tolist()
            else:
                topik_text = "- **Belum ada topik dominan**"
                topik_utama = []

            ringkasan_utama = []
            dampak_utama = []

            if "PHK" in topik_utama:
                ringkasan_utama.append(
                    "Pemberitaan mengenai **PHK** menjadi sinyal penting karena menunjukkan potensi tekanan pada hubungan kerja dan keberlanjutan kepesertaan pekerja formal."
                )
                dampak_utama.append(
                    "Dari sisi jaminan sosial ketenagakerjaan, isu ini berpotensi meningkatkan klaim **JKP** dan pencairan **JHT**, serta dalam jangka lebih panjang dapat mempengaruhi kepesertaan **JP**."
                )

            if "THR / Kesejahteraan Pekerja" in topik_utama:
                ringkasan_utama.append(
                    "Isu **THR dan kesejahteraan pekerja** menunjukkan adanya potensi persoalan kepatuhan perusahaan terhadap hak normatif pekerja."
                )

            if "Kepesertaan BPJS" in topik_utama:
                ringkasan_utama.append(
                    "Pemberitaan mengenai **kepesertaan BPJS Ketenagakerjaan** menunjukkan perhatian terhadap cakupan perlindungan sosial tenaga kerja."
                )

            if "Kecelakaan Kerja (JKK)" in topik_utama:
                ringkasan_utama.append(
                    "Isu **kecelakaan kerja** menunjukkan perlunya perhatian pada keselamatan kerja, terutama di sektor berisiko tinggi."
                )
                dampak_utama.append(
                    "Dari sisi manfaat, kondisi ini berpotensi meningkatkan klaim **JKK** dan pada kasus fatal dapat berkembang menjadi klaim **JKM**."
                )

            if "Konflik Hubungan Industrial" in topik_utama or "Aksi / Demo Buruh" in topik_utama:
                ringkasan_utama.append(
                    "Isu **konflik hubungan industrial dan aksi buruh** menunjukkan adanya ketegangan antara pekerja dan perusahaan yang perlu dicermati lebih dini."
                )

            if "Layanan / Edukasi Klaim" in topik_utama:
                ringkasan_utama.append(
                    "Sebagian pemberitaan bersifat **edukasi layanan**, sehingga lebih merefleksikan kebutuhan informasi peserta dibanding eskalasi risiko langsung."
                )

            if not ringkasan_utama:
                ringkasan_utama.append(
                    "Isu yang berkembang masih bersifat campuran, namun tetap perlu dipantau karena dapat mempengaruhi stabilitas ketenagakerjaan dan perlindungan jaminan sosial."
                )

            if not dampak_utama:
                dampak_utama.append(
                    "Secara umum, perkembangan isu media dapat berdampak pada kepesertaan, kepatuhan perusahaan, dan potensi tekanan terhadap klaim manfaat BPJS Ketenagakerjaan."
                )

            st.markdown(
                f"""
<div class="news-card" style="line-height:1.75;">

**Status:** {status_txt}

Total isu valid terpantau: **{total:,} berita**

Prioritas tinggi: **{tinggi:,}**  
Prioritas sedang: **{sedang:,}**  
Prioritas rendah: **{rendah:,}**

Isu yang paling banyak muncul pada periode ini adalah:

{topik_text}

Secara umum, kondisi saat ini **{kondisi}**.

{" ".join(ringkasan_utama[:2])}

{" ".join(dampak_utama[:2])}

**Rekomendasi:** {rekomendasi}
</div>
""",
                unsafe_allow_html=True
            )

# ===============================
# TAB DATA BERITA
# ===============================
with tab_data:
    st.markdown('<div class="section-title">Berita Terkini</div>', unsafe_allow_html=True)
    st.caption("Daftar berita valid hasil analisis berdasarkan prioritas dan waktu publikasi.")

    df_display = filtered_for_table.copy()

    if df_display.empty:
        st.info("Tidak ada berita untuk filter yang dipilih.")
    else:
        priority_order = {
            "PRIORITAS TINGGI": 1,
            "PRIORITAS SEDANG": 2,
            "PRIORITAS RENDAH": 3
        }
        df_display["Urutan"] = df_display["Prioritas"].map(priority_order).fillna(99)

        sort_col = None
        for c in ["Waktu_Publish_WIB", "Tanggal_Publish", "Tanggal_Ambil", "Tanggal_Hari"]:
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

        def badge_html(prioritas):
            if prioritas == "PRIORITAS TINGGI":
                return "<span class='badge badge-high'>Prioritas Tinggi</span>"
            elif prioritas == "PRIORITAS SEDANG":
                return "<span class='badge badge-mid'>Prioritas Sedang</span>"
            return "<span class='badge badge-low'>Prioritas Rendah</span>"

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

            chips = []
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

        if "Waktu_Publish_WIB" in df_ews.columns:
            df_ews["publish_dt"] = pd.to_datetime(df_ews["Waktu_Publish_WIB"], errors="coerce")
        elif "Tanggal_Publish" in df_ews.columns:
            df_ews["publish_dt"] = pd.to_datetime(df_ews["Tanggal_Publish"], errors="coerce")
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
                return pd.DataFrame(columns=["Topik", "Berita 24 Jam", "Media 24 Jam", "Headline"])

            out = df_recent.groupby("Topik", dropna=False).agg(
                **{
                    "Berita 24 Jam": ("Judul", "count"),
                    "Media 24 Jam": ("Media", pd.Series.nunique)
                }
            ).reset_index()

            head = (
                df_recent.sort_values("publish_dt", ascending=False)
                .groupby("Topik", dropna=False)
                .head(1)[["Topik", "Judul"]]
                .rename(columns={"Judul": "Headline"})
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

            st.dataframe(
                esk[
                    ["Topik", "Trend", "Media 24 Jam", "Berita 24 Jam",
                     "Media 24-48 Jam", "Berita 24-48 Jam", "Skor", "Headline"]
                ].head(10),
                use_container_width=True,
                hide_index=True
            )
        else:
            st.info("Belum ada data eskalasi isu.")

# ===============================
# TAB PANDUAN
# ===============================
with tab_info:
    st.markdown('<div class="section-title">Panduan Sistem Early Warning System</div>', unsafe_allow_html=True)

    st.markdown(
"""
<div class="info-card">
<div class="info-text">

Sistem <b>Early Warning System (EWS) Isu Ketenagakerjaan</b> digunakan untuk memantau perkembangan isu ketenagakerjaan dari media online serta menganalisis potensi dampaknya terhadap program jaminan sosial ketenagakerjaan.

Tahapan sistem saat ini adalah sebagai berikut:

<br>

<b>1. Pengumpulan Data Berita</b><br>
Sistem mengambil berita dari berbagai sumber media online melalui proses scraping/RSS dan menyimpannya ke tab <b>RAW</b>.

<br><br>

<b>2. Penyaringan Awal Isu</b><br>
Berita pada tab RAW kemudian disaring menggunakan keyword ketenagakerjaan dan jaminan sosial tenaga kerja. Hasil tahap ini disimpan ke tab <b>FILTERED_AWAL</b>.

<br><br>

<b>3. Validasi Konteks Berita</b><br>
Berita pada FILTERED_AWAL divalidasi untuk memastikan keterkaitannya dengan kondisi ketenagakerjaan di Indonesia atau PMI. Berita global yang tidak relevan tidak dilanjutkan ke tahap analisis.

<br><br>

<b>4. Analisis Prioritas</b><br>
Berita yang lolos validasi dianalisis untuk menentukan:
<ul>
<li>Topik utama</li>
<li>Dampak program</li>
<li>Dampak kepesertaan</li>
<li>Potensi klaim</li>
<li>Tingkat prioritas</li>
</ul>

Hasil akhir disimpan ke tab <b>HASIL_ANALISIS</b>.

<br>

<b>5. Dashboard Monitoring</b><br>
Dashboard membaca data dari:
<ul>
<li><b>RAW</b> untuk total berita sumber</li>
<li><b>HASIL_ANALISIS</b> untuk berita valid yang sudah dianalisis</li>
</ul>

Dengan model ini, dashboard menjadi lebih bersih karena berita luar negeri yang tidak relevan tidak ikut ditampilkan.

</div>
</div>
""",
        unsafe_allow_html=True
    )