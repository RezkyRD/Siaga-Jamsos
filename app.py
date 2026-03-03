import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import os
import re

from scraper import run_scraper
from filter_keyword import run_filter
from update_priority import run_priority
from gsheet_utils import read_sheet

SHEET_KEY = st.secrets["SHEET_KEY"]

# ===============================
# PAGE CONFIG + THEME
# ===============================
st.set_page_config(page_title="EWS Ketenagakerjaan", page_icon="📊", layout="wide")

st.markdown("""
<style>

/* padding supaya header tidak kepotong */
.block-container {padding-top: 3.4rem; padding-bottom: 2rem;}

/* Sidebar background */
[data-testid="stSidebar"] {background: #0B2C5F;}

/* Sidebar text umum putih */
[data-testid="stSidebar"] .stMarkdown,
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] p,
[data-testid="stSidebar"] span {
    color: #ffffff !important;
}

/* Input tetap hitam supaya terbaca */
[data-testid="stSidebar"] input,
[data-testid="stSidebar"] textarea {
    color: #101828 !important;
    background: #ffffff !important;
}

/* Selectbox & date input */
[data-testid="stSidebar"] .stSelectbox div[role="combobox"],
[data-testid="stSidebar"] .stDateInput div[role="combobox"]{
    background: #ffffff !important;
    color: #101828 !important;
}

[data-testid="stSidebar"] .stSelectbox div[role="combobox"] *,
[data-testid="stSidebar"] .stDateInput div[role="combobox"] * {
    color: #101828 !important;
}

/* tombol sidebar */
[data-testid="stSidebar"] .stButton>button {
    width: 100%;
    border-radius: 10px;
    border: 1px solid rgba(255,255,255,.25);
}

/* Cards */
.kpi-card{background:#fff; border:1px solid #E6EAF2; border-radius:14px; padding:14px 16px; box-shadow:0 4px 14px rgba(0,0,0,.04);}
.kpi-title{font-size:12px; color:#667085; margin-bottom:6px;}
.kpi-value{font-size:22px; font-weight:700; color:#101828; line-height:1.2;}
.kpi-sub{font-size:12px; color:#475467; margin-top:6px;}
.badge{display:inline-block; padding:4px 10px; border-radius:999px; font-size:12px; font-weight:600; border:1px solid;}
.badge-high{color:#B42318; background:#FEF3F2; border-color:#FECDCA;}
.badge-mid{color:#B54708; background:#FFFAEB; border-color:#FEDF89;}
.badge-low{color:#027A48; background:#ECFDF3; border-color:#ABEFC6;}

thead tr th {background:#F2F4F7 !important; color:#344054 !important; font-size: 12px;}
tbody tr:hover {background:#F9FAFB;}

</style>
""", unsafe_allow_html=True)

st.markdown("""
<div style="margin-top:6px; margin-bottom:10px;">
  <div style="font-size:28px; font-weight:800; color:#101828; line-height:1.2;">
    Early Warning System
  </div>
  <div style="color:#475467; margin-top:4px;">
    Monitoring Isu Ketenagakerjaan
  </div>
</div>
""", unsafe_allow_html=True)
st.divider()

# ===============================
# SIDEBAR: UPDATE DATA
# ===============================
with st.sidebar:
    st.markdown("### Kontrol Data")
    if st.button("🔄 Update Data"):
        with st.spinner("Memproses update..."):
            run_scraper()
            run_filter()
            run_priority()

        st.success("Update selesai!")
        st.rerun()

# ===============================
# LOAD DATA
# ===============================
@st.cache_data(ttl=300, show_spinner=False)  # cache 5 menit
def load_sheet(key: str, tab: str) -> pd.DataFrame:
    return read_sheet(key, tab)

raw = load_sheet(SHEET_KEY, "RAW")
filtered = load_sheet(SHEET_KEY, "FILTERED")
# ===============================
# FIX TANGGAL (ANTI ERROR .dt)
# ===============================
def ensure_publish_date(df: pd.DataFrame) -> pd.DataFrame:
    # prioritas kolom tanggal (dari scraper baru)
    if "Tanggal_Publish" in df.columns:
        s = pd.to_datetime(df["Tanggal_Publish"], errors="coerce")

    elif "Waktu_Publish_WIB" in df.columns:
        s = pd.to_datetime(df["Waktu_Publish_WIB"], errors="coerce")

    elif "Tanggal" in df.columns:
        # parse UTC, lalu coba convert ke WIB (kalau tz-aware)
        s = pd.to_datetime(df["Tanggal"], errors="coerce", utc=True)
        try:
            s = s.dt.tz_convert("Asia/Jakarta")
        except Exception:
            pass

    elif "Tanggal_Ambil" in df.columns:
        s = pd.to_datetime(df["Tanggal_Ambil"], errors="coerce")

    else:
        raise ValueError("CSV tidak punya kolom tanggal yang dikenali.")

    # pastikan datetime series
    s = pd.to_datetime(s, errors="coerce")

    df["Tanggal_Hari"] = s.dt.date
    df = df.dropna(subset=["Tanggal_Hari"]).copy()
    return df

raw = ensure_publish_date(raw)
filtered = ensure_publish_date(filtered)

min_date = raw["Tanggal_Hari"].min()
max_date = raw["Tanggal_Hari"].max()

# =====================================
# SPIKE DETECTION FUNCTION (TARUH DI SINI)
# =====================================
def spike_ratio(df: pd.DataFrame, start_date, end_date) -> float:
    if df.empty:
        return 0.0

    daily = df.groupby("Tanggal_Hari").size().sort_index()

    today = end_date
    today_count = int(daily.get(today, 0))

    prev_days = pd.date_range(end=today - pd.Timedelta(days=1), periods=7).date
    prev_counts = [int(daily.get(d, 0)) for d in prev_days]
    avg_7 = sum(prev_counts) / 7 if prev_counts else 0

    if avg_7 == 0:
        return float(today_count)
    return today_count / avg_7

# =====================================
# TOPIC DETECTION (TARUH DI SINI)
# =====================================
TOPIC_RULES = {
    "PHK / Layoff": [r"\bphk\b", r"\blayoff\b", r"\bdirumahkan\b", r"pemutusan hubungan kerja"],
    "Upah / Gaji": [r"\bupah\b", r"\bgaji\b", r"tunggakan upah", r"tidak dibayar"],
    "Aksi / Demo": [r"\bdemo\b", r"unjuk rasa", r"aksi buruh", r"mogok"],
    "Pabrik Tutup / Pailit": [r"pabrik tutup", r"tutup permanen", r"\bpailit\b", r"\bbangkrut\b", r"likuidasi"],
    "Konflik Hubungan Industrial": [r"perselisihan", r"konflik buruh", r"sengketa", r"tripartit", r"mediasi"],
}

def detect_topic(text: str) -> str:
    t = (text or "").lower()
    for topic, patterns in TOPIC_RULES.items():
        for p in patterns:
            if re.search(p, t):
                return topic
    return "Lainnya"

# ===============================
# FILTER PANEL (GLOBAL, DIPAKAI 2 TAB)
# ===============================
with st.sidebar:
    st.markdown("### Filter")
    date_range = st.date_input("Rentang tanggal", value=(min_date, max_date))
    filter_option = st.selectbox(
        "Prioritas",
        ["SEMUA", "PRIORITAS TINGGI", "PRIORITAS SEDANG", "PRIORITAS RENDAH"]
    )

# ===============================
# APPLY DATE FILTER (ANTI GESER TIMEZONE)
# ===============================
# Gunakan tanggal murni agar tidak bergeser hari

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
# ===============================
# APPLY TOPIC DETECTION (pada data yang sudah terfilter tanggal)
# ===============================
if not filtered_display.empty:
    combo = filtered_display.get("Judul", "").astype(str)
    if "Ringkasan" in filtered_display.columns:
        combo = combo + " " + filtered_display["Ringkasan"].astype(str).fillna("")
    filtered_display["Topik"] = combo.apply(detect_topic)

# Apply priority filter (only for display/data table)
filtered_for_table = filtered_display.copy()
if filter_option != "SEMUA":
    filtered_for_table = filtered_for_table[filtered_for_table["Prioritas"] == filter_option].copy()

# ===============================
# TABS
# ===============================
tab_dash, tab_data = st.tabs(["📊 Dashboard", "📰 Data Berita"])

# ===============================
# TAB: DASHBOARD
# ===============================
with tab_dash:
    # pastikan kolom Prioritas ada
    if "Prioritas" not in filtered_display.columns:
        st.error("Kolom 'Prioritas' belum ada di data FILTERED. Klik 🔄 Update Data dulu.")
        st.stop()

    # KPI counts
    tinggi = (filtered_display["Prioritas"] == "PRIORITAS TINGGI").sum()
    sedang = (filtered_display["Prioritas"] == "PRIORITAS SEDANG").sum()
    rendah = (filtered_display["Prioritas"] == "PRIORITAS RENDAH").sum()

    # ======================
    # SPIKE DETECTION
    # ======================
    ratio = spike_ratio(filtered_display, start_date, end_date)

    if ratio >= 2.0:
        spike_label = "LONJAKAN TINGGI"
        spike_badge = "<span class='badge badge-high'>SPIKE</span>"
    elif ratio >= 1.2:
        spike_label = "NAIK"
        spike_badge = "<span class='badge badge-mid'>NAIK</span>"
    else:
        spike_label = "NORMAL"
        spike_badge = "<span class='badge badge-low'>NORMAL</span>"

    c1, c2, c3, c4, c5, c6 = st.columns([1.2, 1.2, 1, 1, 1, 1.1], gap="large")
    with c1:
        st.markdown(f"""
        <div class="kpi-card">
          <div class="kpi-title">Total Berita (RAW)</div>
          <div class="kpi-value">{len(raw_filtered):,}</div>
          <div class="kpi-sub">Sesuai rentang tanggal</div>
        </div>""", unsafe_allow_html=True)

    with c2:
        st.markdown(f"""
        <div class="kpi-card">
          <div class="kpi-title">Lolos Keyword</div>
          <div class="kpi-value">{len(filtered_display):,}</div>
          <div class="kpi-sub">Basis analisis EWS</div>
        </div>""", unsafe_allow_html=True)

    with c3:
        st.markdown(f"""
        <div class="kpi-card">
          <div class="kpi-title">Prioritas Tinggi</div>
          <div class="kpi-value">{tinggi:,}</div>
          <div class="kpi-sub"><span class="badge badge-high">HIGH</span></div>
        </div>""", unsafe_allow_html=True)

    with c4:
        st.markdown(f"""
        <div class="kpi-card">
          <div class="kpi-title">Prioritas Sedang</div>
          <div class="kpi-value">{sedang:,}</div>
          <div class="kpi-sub"><span class="badge badge-mid">MED</span></div>
        </div>""", unsafe_allow_html=True)

    with c5:
        st.markdown(f"""
        <div class="kpi-card">
          <div class="kpi-title">Prioritas Rendah</div>
          <div class="kpi-value">{rendah:,}</div>
          <div class="kpi-sub"><span class="badge badge-low">LOW</span></div>
        </div>""", unsafe_allow_html=True)
    with c6:
        st.markdown(f"""
    <div class="kpi-card">
      <div class="kpi-title">Lonjakan (vs 7 hari)</div>
      <div class="kpi-value">{ratio:.2f}x</div>
      <div class="kpi-sub">{spike_badge} {spike_label}</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<div style='height:14px;'></div>", unsafe_allow_html=True)

    # Chart + Narrative in 2 columns
    left, right = st.columns([1.1, 0.9], gap="large")

    with left:
        st.subheader("Distribusi Prioritas")
        priority_counts = filtered_display["Prioritas"].value_counts()
        if not priority_counts.empty:
            order = ["PRIORITAS TINGGI", "PRIORITAS SEDANG", "PRIORITAS RENDAH"]
            priority_counts = priority_counts.reindex(order).fillna(0).astype(int)

            fig, ax = plt.subplots(figsize=(7.5, 2.6), dpi=120)
            priority_counts.plot(kind="barh", ax=ax)

            ax.set_xlabel("Jumlah Berita")
            ax.set_ylabel("")
            ax.set_title("")
            fig.subplots_adjust(top=0.92, left=0.35, right=0.98, bottom=0.25)

            st.pyplot(fig, width="stretch")
        else:
            st.warning("Belum ada data.")

    with right:
        st.subheader("🧠 Analisis Situasi")
        total = len(filtered_display)

    if tinggi > 3:
        kondisi = "menunjukkan eskalasi signifikan"
        rekomendasi = "Perlu mitigasi cepat dan koordinasi lintas unit."
        tag = "<span class='badge badge-high'>RISIKO TINGGI</span>"
    elif tinggi > 0:
        kondisi = "menunjukkan potensi peningkatan risiko"
        rekomendasi = "Perlu pemantauan intensif dan klarifikasi lapangan."
        tag = "<span class='badge badge-mid'>WASPADA</span>"
    else:
        kondisi = "relatif stabil tanpa indikasi eskalasi besar"
        rekomendasi = "Pemantauan rutin sebagai langkah preventif."
        tag = "<span class='badge badge-low'>STABIL</span>"

    # Topik teratas (HARUS DI DALAM with right)
    top_topics = (
        filtered_display["Topik"].value_counts().head(5)
        if "Topik" in filtered_display.columns else pd.Series(dtype=int)
    )
    topics_html = "<br>".join([f"• {k}: <b>{v}</b>" for k, v in top_topics.items()]) if not top_topics.empty else "—"

    st.markdown(f"""
    <div class="kpi-card">
      <div class="kpi-title">Ringkasan</div>
      <div style="margin:6px 0 10px 0;">{tag}</div>
      <div style="color:#344054; line-height:1.55;">
        Total berita terfilter: <b>{total:,}</b><br>
        Prioritas tinggi: <b>{tinggi:,}</b><br>
        Prioritas sedang: <b>{sedang:,}</b><br>
        Prioritas rendah: <b>{rendah:,}</b><br><br>

        <b>Topik teratas:</b><br>
        {topics_html}<br><br>

        Kondisi saat ini <b>{kondisi}</b>.<br>
        {rekomendasi}
      </div>
    </div>
    """, unsafe_allow_html=True)

# ===============================
# TAB: DATA BERITA
# ===============================
with tab_data:
    st.subheader("📰 Monitoring Berita Ketenagakerjaan")
    st.caption("Gunakan filter di sidebar untuk mengatur rentang tanggal dan prioritas.")

    # ===============================
    # FILTER TAMBAHAN (TAB DATA)
    # ===============================
    colf1, colf2 = st.columns([1, 1.2])
    with colf1:
        q = st.text_input("Cari judul (contains)", "")
    with colf2:
        media_col = "Media" if "Media" in filtered_for_table.columns else ("Sumber" if "Sumber" in filtered_for_table.columns else None)
        if media_col:
            media_list = ["SEMUA"] + sorted([
                m for m in filtered_for_table[media_col].dropna().unique().tolist()
                if str(m).strip() != ""
            ])
            media_pick = st.selectbox("Filter Media", media_list)
        else:
            media_pick = "SEMUA"
            st.caption("Kolom Media tidak ditemukan.")

    # Urutkan prioritas: tinggi dulu
    priority_order = {"PRIORITAS TINGGI": 1, "PRIORITAS SEDANG": 2, "PRIORITAS RENDAH": 3}
    df_display = filtered_for_table.copy()

    # ===============================
    # APPLY FILTER TAMBAHAN
    # ===============================
    if q.strip():
        df_display = df_display[df_display["Judul"].astype(str).str.contains(q, case=False, na=False)].copy()

    if media_pick != "SEMUA" and media_col:
        df_display = df_display[df_display[media_col] == media_pick].copy()

    df_display["Urutan"] = df_display["Prioritas"].map(priority_order)