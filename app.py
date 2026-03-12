import re
from html import escape
from typing import Dict, List, Tuple

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
header[data-testid="stHeader"] {display:none;}
div[data-testid="stToolbar"] {display:none;}
#MainMenu {visibility:hidden;}
footer {visibility:hidden;}

:root {
    --bg-light: #f5f7fb;
    --card-light: rgba(255,255,255,0.82);
    --text-light: #101828;
    --muted-light: #667085;
    --line-light: rgba(16,24,40,0.08);

    --bg-dark: #0b1120;
    --card-dark: rgba(17,25,40,0.82);
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

/* Header */
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

button[data-baseweb="tab"] {
    border-radius: 999px !important;
    padding: 10px 16px !important;
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
  <p class="ews-sub">Monitoring Isu Jaminan Sosial Ketenagakerjaan</p>
</div>
""",
    unsafe_allow_html=True
)
st.divider()

# ===============================
# HELPERS
# ===============================
TOPIC_RULES: Dict[str, List[str]] = {
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
    "Pabrik Tutup / Pailit": [
        r"pabrik tutup", r"tutup permanen", r"\bpailit\b", r"\bbangkrut\b", r"likuidasi", r"stop operasional"
    ],
    "Kepesertaan BPJS": [
        r"bpjs ketenagakerjaan", r"bpjamsostek", r"jamsostek", r"kepesertaan bpjs", r"terdaftar bpjs", r"peserta bpjs"
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
    "Pengawasan Kepatuhan": [
        r"pengawasan", r"pemeriksaan", r"sanksi perusahaan", r"kepatuhan perusahaan", r"tidak patuh"
    ],
    "Kendala Klaim BPJS": [
        r"klaim ditolak", r"kendala klaim", r"klaim lama", r"antrian klaim", r"verifikasi klaim"
    ],
    "Pekerja Migran Indonesia (PMI)": [
        r"\bpmi\b", r"pekerja migran", r"tki", r"buruh migran"
    ],
    "Jasa Konstruksi": [
        r"konstruksi", r"proyek", r"pembangunan", r"jasa konstruksi"
    ],
}

PRIORITY_OPTIONS = ["SEMUA", "PRIORITAS TINGGI", "PRIORITAS SEDANG", "PRIORITAS RENDAH"]


def clean_label(text) -> str:
    return str(text).replace("_", " ").strip()


def safe_clear_caches() -> None:
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

    temp = df.copy()
    temp.columns = temp.columns.astype(str).str.strip()

    if "Tanggal_Publish" in temp.columns:
        s = pd.to_datetime(temp["Tanggal_Publish"], errors="coerce")
    elif "Waktu_Publish_WIB" in temp.columns:
        s = pd.to_datetime(temp["Waktu_Publish_WIB"], errors="coerce")
    elif "Tanggal" in temp.columns:
        s = pd.to_datetime(temp["Tanggal"], errors="coerce", utc=True)
        try:
            s = s.dt.tz_convert("Asia/Jakarta")
        except Exception:
            pass
    elif "Tanggal_Ambil" in temp.columns:
        s = pd.to_datetime(temp["Tanggal_Ambil"], errors="coerce")
    else:
        raise ValueError("Data tidak punya kolom tanggal yang dikenali.")

    s = pd.to_datetime(s, errors="coerce")
    temp["Tanggal_Hari"] = s.dt.date
    temp = temp.dropna(subset=["Tanggal_Hari"]).copy()
    return temp


def detect_topic(text: str) -> str:
    t = (text or "").lower()

    for topic, patterns in TOPIC_RULES.items():
        for pattern in patterns:
            if re.search(pattern, t):
                return topic

    if re.search(r"bpjs|bpjamsostek|jamsostek|klaim|iuran", t):
        return "Kepesertaan BPJS"

    if re.search(r"buruh|pekerja|ketenagakerjaan|tenaga kerja", t):
        return "Konflik Hubungan Industrial"

    return "Kebijakan Ketenagakerjaan"


def apply_topic_detection(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df.copy()

    temp = df.copy()
    if "Topik" not in temp.columns:
        judul = temp["Judul"].astype(str) if "Judul" in temp.columns else ""
        ringkasan = temp["Ringkasan"].astype(str) if "Ringkasan" in temp.columns else ""
        combo = judul + " " + ringkasan
        temp["Topik"] = combo.apply(detect_topic)
    return temp


def get_sort_column(df: pd.DataFrame) -> str:
    for col in ["Waktu_Publish_WIB", "Tanggal_Publish", "Tanggal_Ambil", "Tanggal_Hari"]:
        if col in df.columns:
            return col
    return "Tanggal_Hari"


def build_analysis_text(df: pd.DataFrame, tinggi: int, sedang: int, rendah: int) -> str:
    total = len(df)

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

    topik_utama: List[str] = []
    topik_text = "- **Belum ada topik dominan**"

    if "Topik" in df.columns and not df.empty:
        topik_counts = df["Topik"].value_counts()
        top3 = topik_counts.head(3)
        topik_text = "\n".join(
            [f"- **{clean_label(topic)}** ({count} berita)" for topic, count in top3.items()]
        )
        topik_utama = top3.index.tolist()

    ringkasan_utama: List[str] = []
    dampak_utama: List[str] = []

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
        dampak_utama.append(
            "Walaupun THR bukan manfaat langsung BPJS Ketenagakerjaan, isu ini dapat memicu pengaduan, perselisihan hubungan industrial, dan menurunkan stabilitas pekerja penerima upah."
        )

    if "Kepesertaan BPJS" in topik_utama:
        ringkasan_utama.append(
            "Pemberitaan mengenai **kepesertaan BPJS Ketenagakerjaan** menunjukkan perhatian terhadap cakupan perlindungan sosial tenaga kerja."
        )
        dampak_utama.append(
            "Hal ini berkaitan dengan perluasan kepesertaan, kepatuhan perusahaan, dan kualitas perlindungan bagi pekerja **PU**, **BPU**, **PMI**, serta sektor **jasa konstruksi**."
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
        dampak_utama.append(
            "Jika tidak tertangani, kondisi ini dapat berkembang menjadi gangguan operasional, PHK, dan penurunan kepatuhan terhadap perlindungan sosial tenaga kerja."
        )

    if not ringkasan_utama:
        ringkasan_utama.append(
            "Isu yang berkembang masih bersifat campuran, namun tetap perlu dipantau karena dapat mempengaruhi stabilitas ketenagakerjaan dan perlindungan jaminan sosial."
        )

    if not dampak_utama:
        dampak_utama.append(
            "Secara umum, perkembangan isu media dapat berdampak pada kepesertaan, kepatuhan perusahaan, dan potensi tekanan terhadap klaim manfaat BPJS Ketenagakerjaan."
        )

    return f"""
<div class="news-card" style="line-height:1.75;">
<b>Status:</b> {status_txt}<br><br>

Total isu ketenagakerjaan terpantau: <b>{total:,} berita</b><br><br>

Prioritas tinggi: <b>{tinggi:,}</b><br>
Prioritas sedang: <b>{sedang:,}</b><br>
Prioritas rendah: <b>{rendah:,}</b><br><br>

Isu yang paling banyak muncul pada periode ini adalah:<br><br>

{topik_text}<br><br>

Secara umum, kondisi saat ini <b>{kondisi}</b>.<br><br>

{" ".join(ringkasan_utama[:2])}<br><br>
{" ".join(dampak_utama[:2])}<br><br>

<b>Rekomendasi:</b> {rekomendasi}
</div>
"""


def build_escalation_table(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame()

    temp = apply_topic_detection(df)

    if "Waktu_Publish_WIB" in temp.columns:
        temp["publish_dt"] = pd.to_datetime(temp["Waktu_Publish_WIB"], errors="coerce")
    elif "Tanggal_Publish" in temp.columns:
        temp["publish_dt"] = pd.to_datetime(temp["Tanggal_Publish"], errors="coerce")
    else:
        temp["publish_dt"] = pd.to_datetime(temp["Tanggal_Hari"], errors="coerce")

    temp = temp.dropna(subset=["publish_dt"]).copy()
    if temp.empty:
        return pd.DataFrame()

    now = pd.Timestamp.now(tz="Asia/Jakarta").tz_localize(None)
    w1_start = now - pd.Timedelta(hours=24)
    w0_start = now - pd.Timedelta(hours=48)

    w1 = temp[temp["publish_dt"] >= w1_start].copy()
    w0 = temp[(temp["publish_dt"] >= w0_start) & (temp["publish_dt"] < w1_start)].copy()

    def agg(df_recent: pd.DataFrame, berita_label: str, media_label: str) -> pd.DataFrame:
        if df_recent.empty:
            return pd.DataFrame(columns=["Topik", berita_label, media_label, "Headline"])

        out = df_recent.groupby("Topik", dropna=False).agg(
            **{
                berita_label: ("Judul", "count"),
                media_label: ("Media", pd.Series.nunique)
            }
        ).reset_index()

        head = (
            df_recent.sort_values("publish_dt", ascending=False)
            .groupby("Topik", dropna=False)
            .head(1)[["Topik", "Judul"]]
            .rename(columns={"Judul": "Headline"})
        )

        return out.merge(head, on="Topik", how="left")

    s1 = agg(w1, "Berita 24 Jam", "Media 24 Jam")
    s0 = agg(w0, "Berita 24-48 Jam", "Media 24-48 Jam")

    esk = s1.merge(
        s0[["Topik", "Berita 24-48 Jam", "Media 24-48 Jam"]],
        on="Topik",
        how="left"
    )

    esk[["Berita 24-48 Jam", "Media 24-48 Jam"]] = esk[
        ["Berita 24-48 Jam", "Media 24-48 Jam"]
    ].fillna(0).astype(int)

    esk["Skor"] = esk["Media 24 Jam"] * 3 + esk["Berita 24 Jam"]

    def trend(row) -> str:
        if row["Media 24 Jam"] > row["Media 24-48 Jam"]:
            return "📈 Naik"
        if row["Media 24 Jam"] < row["Media 24-48 Jam"]:
            return "📉 Turun"
        return "➖ Stabil"

    esk["Trend"] = esk.apply(trend, axis=1)
    esk["Topik"] = esk["Topik"].astype(str).apply(clean_label)
    esk = esk.sort_values(["Skor", "Media 24 Jam", "Berita 24 Jam"], ascending=False)

    return esk[
        ["Topik", "Trend", "Media 24 Jam", "Berita 24 Jam", "Media 24-48 Jam", "Berita 24-48 Jam", "Skor", "Headline"]
    ]


def build_priority_chart(df: pd.DataFrame):
    priority_counts = df["Prioritas"].value_counts()
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
    return fig


def badge_html(prioritas: str) -> str:
    if prioritas == "PRIORITAS TINGGI":
        return "<span class='badge badge-high'>Prioritas Tinggi</span>"
    if prioritas == "PRIORITAS SEDANG":
        return "<span class='badge badge-mid'>Prioritas Sedang</span>"
    return "<span class='badge badge-low'>Prioritas Rendah</span>"


# ===============================
# LOAD DATA
# ===============================
try:
    raw = load_sheet(SHEET_KEY, "RAW")
    filtered = load_sheet(SHEET_KEY, "FILTERED")
except Exception as e:
    st.error(f"Gagal membaca Google Sheets: {e}")
    st.stop()

raw = ensure_publish_date(raw)
filtered = ensure_publish_date(filtered)

if raw.empty:
    st.warning("Data RAW belum tersedia.")
    st.stop()

raw.columns = raw.columns.astype(str).str.strip()
filtered.columns = filtered.columns.astype(str).str.strip()

min_date = raw["Tanggal_Hari"].min()
max_date = raw["Tanggal_Hari"].max()

# ===============================
# KONTROL DATA
# ===============================
st.markdown('<div class="section-title">Kontrol Data</div>', unsafe_allow_html=True)

ctrl1, ctrl2, ctrl3 = st.columns([1.2, 2.2, 1.5])

with ctrl1:
    if st.button("🔄 Update Data", key="update_data_main"):
        with st.spinner("Memproses update..."):
            run_scraper()
            run_filter()
            run_priority()
            safe_clear_caches()
        st.success("Update selesai!")
        st.rerun()

with ctrl2:
    date_range = st.date_input(
        "Rentang tanggal",
        value=(min_date, max_date),
        key="main_date_range"
    )

with ctrl3:
    filter_option = st.selectbox(
        "Prioritas",
        PRIORITY_OPTIONS,
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

filtered_display = apply_topic_detection(filtered_display)

filtered_for_table = filtered_display.copy()
if filter_option != "SEMUA" and "Prioritas" in filtered_for_table.columns:
    filtered_for_table = filtered_for_table[
        filtered_for_table["Prioritas"] == filter_option
    ].copy()

# reset page kalau jumlah data/filter berubah
current_signature = f"{start_date}_{end_date}_{filter_option}_{len(filtered_for_table)}"
if "table_signature" not in st.session_state:
    st.session_state.table_signature = current_signature
if st.session_state.table_signature != current_signature:
    st.session_state.table_signature = current_signature
    st.session_state.page = 1

# ===============================
# TABS
# ===============================
tab_dash, tab_data, tab_info = st.tabs(["📊 Dashboard", "📰 Data Berita", "📘 Panduan"])

# ===============================
# TAB DASHBOARD
# ===============================
with tab_dash:
    if "Prioritas" not in filtered_display.columns:
        st.error("Kolom 'Prioritas' belum ada di data FILTERED. Klik 🔄 Update Data dulu.")
        st.stop()

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
              <div class="kpi-title">Lolos Keyword</div>
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

    left, right = st.columns([1.05, 0.95], gap="large")

    with left:
        st.markdown('<div class="section-title">Distribusi Prioritas</div>', unsafe_allow_html=True)

        if not filtered_display.empty:
            st.caption("Perbandingan jumlah berita berdasarkan level prioritas pada periode terpilih")
            fig = build_priority_chart(filtered_display)
            st.plotly_chart(
                fig,
                use_container_width=True,
                config={"displayModeBar": False, "responsive": True}
            )
        else:
            st.info("Belum ada data distribusi prioritas.")

        st.markdown("<div style='height:12px;'></div>", unsafe_allow_html=True)
        st.markdown('<div class="section-title">Top 5 Berita Prioritas Tinggi</div>', unsafe_allow_html=True)

        df_high = filtered_display[filtered_display["Prioritas"] == "PRIORITAS TINGGI"].copy()
        if not df_high.empty:
            sort_col = get_sort_column(df_high)
            df_high = df_high.sort_values(sort_col, ascending=False)
            top5 = df_high.head(5)

            for _, row in top5.iterrows():
                media = escape(str(row.get("Media", "-")))
                judul = escape(str(row.get("Judul", "-")))
                link = str(row.get("Link", "")).strip()
                waktu = escape(str(row.get("Waktu_Publish_WIB", row.get("Tanggal_Publish", ""))))

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
        analysis_html = build_analysis_text(filtered_display, tinggi, sedang, rendah)
        st.markdown(analysis_html, unsafe_allow_html=True)

# ===============================
# TAB DATA BERITA
# ===============================
with tab_data:
    st.markdown('<div class="section-title">Berita Terkini</div>', unsafe_allow_html=True)
    st.caption("Daftar 10 berita terbaru berdasarkan prioritas dan waktu publikasi.")

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
        sort_col = get_sort_column(df_display)

        df_display = df_display.sort_values(["Urutan", sort_col], ascending=[True, False]).drop(columns=["Urutan"])
        df_display = df_display.reset_index(drop=True)

        items_per_page = 10
        total_rows = len(df_display)
        total_pages = max(1, (total_rows - 1) // items_per_page + 1)

        if "page" not in st.session_state:
            st.session_state.page = 1
        if st.session_state.page > total_pages:
            st.session_state.page = total_pages

        start_idx = (st.session_state.page - 1) * items_per_page
        end_idx = start_idx + items_per_page
        df_page = df_display.iloc[start_idx:end_idx].copy()

        for i, row in df_page.iterrows():
            judul = escape(clean_label(row.get("Judul", "-")))
            media = escape(clean_label(row.get("Media", "-")))
            link = str(row.get("Link", "")).strip()
            waktu = escape(clean_label(row.get("Waktu_Publish_WIB", row.get("Tanggal", "-"))))
            prioritas = str(row.get("Prioritas", "PRIORITAS RENDAH")).strip()

            topik = escape(clean_label(row.get("Topik", "")))
            dampak_program = escape(clean_label(row.get("Dampak_Program", "")))
            dampak_kepesertaan = escape(clean_label(row.get("Dampak_Kepesertaan", "")))
            potensi_klaim = escape(clean_label(row.get("Potensi_Klaim", "")))
            alasan = escape(clean_label(row.get("Alasan_Prioritas", "")))

            chips = []
            if topik:
                chips.append(f"<span class='news-chip'>{topik}</span>")
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

            card_html = (
                f"<div class='news-card'>"
                f"<div style='display:flex; justify-content:space-between; gap:12px; flex-wrap:wrap; align-items:flex-start;'>"
                f"<div style='flex:1; min-width:250px;'>"
                f"<div class='news-title'>{start_idx + i + 1}. {judul}</div>"
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
            Menampilkan {min(start_idx + 1, total_rows)} - {min(end_idx, total_rows)} dari {total_rows} berita
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

        esk = build_escalation_table(filtered_display)
        if esk.empty:
            st.info("Belum ada data cukup untuk menghitung indeks eskalasi isu.")
        else:
            st.dataframe(esk.head(10), use_container_width=True, hide_index=True)

# ===============================
# TAB PANDUAN
# ===============================
with tab_info:
    st.markdown('<div class="section-title">Panduan Sistem Early Warning System</div>', unsafe_allow_html=True)

    st.markdown(
        """
<div class="info-card">
<div class="info-text">

Sistem **Early Warning System (EWS) Isu Ketenagakerjaan** digunakan untuk memantau perkembangan isu ketenagakerjaan yang muncul di media online serta menganalisis potensi dampaknya terhadap program jaminan sosial ketenagakerjaan.

Sistem bekerja melalui beberapa tahapan proses analisis data berita sebagai berikut:

<br>

<b>1. Pengumpulan Data Berita (Scraping Media Online)</b><br><br>
Sistem secara otomatis mengambil berita dari berbagai media online yang memuat isu ketenagakerjaan.<br>
Data yang dikumpulkan meliputi:
<ul>
<li>Judul berita</li>
<li>Media sumber berita</li>
<li>Waktu publikasi berita</li>
<li>Ringkasan atau isi berita</li>
<li>Tautan berita asli</li>
</ul>

<b>2. Penyaringan Isu Ketenagakerjaan (Keyword Filtering)</b><br><br>
Seluruh berita yang terkumpul kemudian disaring menggunakan kata kunci yang berkaitan dengan isu ketenagakerjaan seperti:
<ul>
<li>PHK</li>
<li>Upah dan gaji</li>
<li>Buruh dan pekerja</li>
<li>Hubungan industrial</li>
<li>BPJS Ketenagakerjaan</li>
<li>Kecelakaan kerja</li>
<li>Jaminan sosial tenaga kerja</li>
</ul>

<b>3. Identifikasi Topik Isu</b><br><br>
Setelah berita lolos tahap penyaringan, sistem melakukan analisis untuk mengidentifikasi topik utama dari setiap berita, seperti:
<ul>
<li>PHK</li>
<li>Konflik hubungan industrial</li>
<li>Kepesertaan BPJS Ketenagakerjaan</li>
<li>Upah dan kesejahteraan pekerja</li>
<li>Aksi buruh atau demonstrasi pekerja</li>
<li>Kecelakaan kerja</li>
<li>Tunggakan iuran BPJS</li>
</ul>

<b>4. Analisis Dampak terhadap Program Jaminan Sosial</b><br><br>
Setiap berita dianalisis untuk melihat potensi dampaknya terhadap program BPJS Ketenagakerjaan, antara lain:
<ul>
<li>JHT (Jaminan Hari Tua)</li>
<li>JKK (Jaminan Kecelakaan Kerja)</li>
<li>JKM (Jaminan Kematian)</li>
<li>JKP (Jaminan Kehilangan Pekerjaan)</li>
<li>JP (Jaminan Pensiun)</li>
</ul>

<b>5. Penentuan Prioritas Berita</b><br><br>
Setiap berita kemudian diklasifikasikan berdasarkan tingkat urgensi isu menjadi tiga kategori:
<ul>
<li><b>Prioritas Tinggi</b>: berpotensi berdampak besar terhadap kondisi ketenagakerjaan atau program jaminan sosial</li>
<li><b>Prioritas Sedang</b>: perlu dipantau karena memiliki potensi perkembangan isu</li>
<li><b>Prioritas Rendah</b>: bersifat informatif dan tidak menunjukkan potensi dampak signifikan</li>
</ul>

<b>6. Dashboard Monitoring Isu</b><br><br>
Hasil analisis ditampilkan dalam bentuk dashboard yang memuat:
<ul>
<li>Total berita yang berhasil dikumpulkan</li>
<li>Jumlah berita yang relevan dengan isu ketenagakerjaan</li>
<li>Distribusi berita berdasarkan tingkat prioritas</li>
<li>Daftar berita prioritas tinggi</li>
<li>Analisis situasi isu ketenagakerjaan</li>
</ul>

<b>7. Indeks Eskalasi Isu</b><br><br>
Indeks eskalasi digunakan untuk memantau perkembangan intensitas isu ketenagakerjaan dengan membandingkan:
<ul>
<li>Jumlah berita dalam 24 jam terakhir</li>
<li>Jumlah media yang memberitakan</li>
<li>Tren peningkatan atau penurunan isu</li>
</ul>

Sistem kemudian menentukan tren isu sebagai:
<ul>
<li>📈 Naik</li>
<li>📉 Turun</li>
<li>➖ Stabil</li>
</ul>

Semakin tinggi skor eskalasi, semakin besar kemungkinan isu tersebut berkembang dan memerlukan perhatian lebih lanjut.
</div>
</div>
""",
        unsafe_allow_html=True
    )