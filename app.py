import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import re

from scraper import run_scraper
from filter_keyword import run_filter
from update_priority import run_priority
from gsheet_utils import read_sheet


SHEET_KEY = st.secrets["SHEET_KEY"]

st.set_page_config(page_title="EWS Ketenagakerjaan", page_icon="📊", layout="wide")

st.markdown("""
<style>
.block-container {padding-top: 3.4rem; padding-bottom: 2rem;}
[data-testid="stSidebar"] {background: #0B2C5F;}
[data-testid="stSidebar"] .stMarkdown,
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] p,
[data-testid="stSidebar"] span { color: #ffffff !important; }
[data-testid="stSidebar"] input,
[data-testid="stSidebar"] textarea { color: #101828 !important; background: #ffffff !important; }
[data-testid="stSidebar"] .stSelectbox div[role="combobox"],
[data-testid="stSidebar"] .stDateInput div[role="combobox"]{ background: #ffffff !important; color: #101828 !important; }
[data-testid="stSidebar"] .stSelectbox div[role="combobox"] *,
[data-testid="stSidebar"] .stDateInput div[role="combobox"] * { color: #101828 !important; }
[data-testid="stSidebar"] .stButton>button { width: 100%; border-radius: 10px; border: 1px solid rgba(255,255,255,.25); }
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
  <div style="font-size:28px; font-weight:800; color:#101828; line-height:1.2;">Early Warning System</div>
  <div style="color:#475467; margin-top:4px;">Monitoring Isu Ketenagakerjaan</div>
</div>
""", unsafe_allow_html=True)
st.divider()

# ===============================
# SIDEBAR: UPDATE DATA
# ===============================
with st.sidebar:
    st.markdown("### Kontrol Data")
    if st.button("🔄 Update Semua (RAW → FILTERED → PRIORITAS)"):
        with st.spinner("Memproses update semua..."):
            run_scraper(SHEET_KEY)
            run_filter(SHEET_KEY)
            run_priority(SHEET_KEY)

        # clear cache supaya langsung baca yang baru
        st.cache_data.clear()
        try:
            read_sheet.clear()
        except Exception:
            pass

        st.success("Update semua selesai!")
        st.rerun()

# ===============================
# LOAD DATA
# ===============================
raw = read_sheet(SHEET_KEY, "RAW")
filtered = read_sheet(SHEET_KEY, "FILTERED")

def ensure_publish_date(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or df.empty:
        return pd.DataFrame(columns=(df.columns if df is not None else []))

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
        df = df.copy()
        df["Tanggal_Hari"] = pd.NaT
        return df

    s = pd.to_datetime(s, errors="coerce")
    df = df.copy()
    df["Tanggal_Hari"] = s.dt.date
    df = df.dropna(subset=["Tanggal_Hari"]).copy()
    return df

raw = ensure_publish_date(raw)
filtered = ensure_publish_date(filtered)

if raw.empty and filtered.empty:
    st.info("Data masih kosong. Klik 🔄 Update Semua untuk mengambil berita.")
    st.stop()

min_date = None
max_date = None
if not raw.empty:
    min_date = raw["Tanggal_Hari"].min()
    max_date = raw["Tanggal_Hari"].max()
if not filtered.empty:
    min_f = filtered["Tanggal_Hari"].min()
    max_f = filtered["Tanggal_Hari"].max()
    min_date = min_date if min_date is not None else min_f
    max_date = max_date if max_date is not None else max_f
    min_date = min(min_date, min_f) if min_f is not None else min_date
    max_date = max(max_date, max_f) if max_f is not None else max_date

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

with st.sidebar:
    st.markdown("### Filter")
    date_range = st.date_input("Rentang tanggal", value=(min_date, max_date))
    filter_option = st.selectbox(
        "Prioritas",
        ["SEMUA", "PRIORITAS TINGGI", "PRIORITAS SEDANG", "PRIORITAS RENDAH"]
    )

if isinstance(date_range, (list, tuple)) and len(date_range) == 2:
    start_date, end_date = date_range
else:
    start_date, end_date = min_date, max_date

raw_filtered = raw[
    (raw["Tanggal_Hari"] >= start_date) &
    (raw["Tanggal_Hari"] <= end_date)
].copy() if not raw.empty else pd.DataFrame(columns=raw.columns)

filtered_display = filtered[
    (filtered["Tanggal_Hari"] >= start_date) &
    (filtered["Tanggal_Hari"] <= end_date)
].copy() if not filtered.empty else pd.DataFrame(columns=filtered.columns)

if not filtered_display.empty:
    filtered_display["Topik"] = filtered_display.get("Judul", "").astype(str).apply(detect_topic)

filtered_for_table = filtered_display.copy()
if filter_option != "SEMUA":
    if "Prioritas" in filtered_for_table.columns:
        filtered_for_table = filtered_for_table[filtered_for_table["Prioritas"] == filter_option].copy()
    else:
        filtered_for_table = filtered_for_table.iloc[0:0]

tab_dash, tab_data = st.tabs(["📊 Dashboard", "📰 Data Berita"])

with tab_dash:
    if filtered_display.empty:
        st.info("Belum ada data FILTERED pada rentang tanggal ini. Klik 🔄 Update Semua atau ubah filter.")
        st.stop()

    if "Prioritas" not in filtered_display.columns:
        st.error("Kolom 'Prioritas' belum ada. Klik 🔄 Update Semua.")
        st.stop()

    tinggi = int((filtered_display["Prioritas"] == "PRIORITAS TINGGI").sum())
    sedang = int((filtered_display["Prioritas"] == "PRIORITAS SEDANG").sum())
    rendah = int((filtered_display["Prioritas"] == "PRIORITAS RENDAH").sum())

    c1, c2, c3, c4, c5 = st.columns([1.2, 1.2, 1, 1, 1], gap="large")
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

    st.markdown("<div style='height:14px;'></div>", unsafe_allow_html=True)
    left, right = st.columns([1.1, 0.9], gap="large")

    with left:
        st.subheader("Distribusi Prioritas")
        priority_counts = filtered_display["Prioritas"].value_counts()
        order = ["PRIORITAS TINGGI", "PRIORITAS SEDANG", "PRIORITAS RENDAH"]
        priority_counts = priority_counts.reindex(order).fillna(0).astype(int)

        fig, ax = plt.subplots(figsize=(7.5, 2.6), dpi=120)
        priority_counts.plot(kind="barh", ax=ax)
        ax.set_xlabel("Jumlah Berita")
        ax.set_ylabel("")
        ax.set_title("")
        fig.subplots_adjust(top=0.92, left=0.35, right=0.98, bottom=0.25)
        st.pyplot(fig, use_container_width=True)

    with right:
        st.subheader("🧠 Analisis Situasi")
        total = len(filtered_display)

        if tinggi >= 3:
            status_txt = "🔴 RISIKO TINGGI"
            kondisi = "menunjukkan eskalasi signifikan"
            rekomendasi = "Perlu mitigasi cepat dan koordinasi lintas unit."
        elif tinggi >= 1:
            status_txt = "🟡 WASPADA"
            kondisi = "menunjukkan potensi peningkatan risiko"
            rekomendasi = "Perlu pemantauan intensif dan klarifikasi lapangan."
        else:
            status_txt = "🟢 STABIL"
            kondisi = "relatif stabil tanpa indikasi eskalasi besar"
            rekomendasi = "Pemantauan rutin sebagai langkah preventif."

        st.markdown(f"""
**Status:** {status_txt}

Total berita terfilter: **{total:,}**  
Prioritas tinggi: **{tinggi:,}**  
Prioritas sedang: **{sedang:,}**  
Prioritas rendah: **{rendah:,}**

Kondisi saat ini **{kondisi}**.  
{rekomendasi}
""")

with tab_data:
    st.subheader("📰 Monitoring Berita Ketenagakerjaan")
    st.caption("Gunakan filter di sidebar untuk mengatur rentang tanggal dan prioritas.")

    df_display = filtered_for_table.copy()

    if df_display.empty:
        st.info("Tidak ada berita untuk filter yang dipilih.")
        st.stop()

    priority_order = {"PRIORITAS TINGGI": 1, "PRIORITAS SEDANG": 2, "PRIORITAS RENDAH": 3}
    df_display["Urutan"] = df_display.get("Prioritas", "").map(priority_order).fillna(99)

    sort_col = None
    for c in ["Waktu_Publish_WIB", "Tanggal_Publish", "Tanggal_Ambil", "Tanggal_Hari"]:
        if c in df_display.columns:
            sort_col = c
            break
    sort_col = sort_col or "Urutan"

    df_display = df_display.sort_values(["Urutan", sort_col], ascending=[True, False]).drop(columns=["Urutan"])

    def badge(prioritas: str) -> str:
        if prioritas == "PRIORITAS TINGGI":
            return "<span class='badge badge-high'>PRIORITAS TINGGI</span>"
        if prioritas == "PRIORITAS SEDANG":
            return "<span class='badge badge-mid'>PRIORITAS SEDANG</span>"
        return "<span class='badge badge-low'>PRIORITAS RENDAH</span>"

    if "Prioritas" in df_display.columns:
        df_display["Prioritas"] = df_display["Prioritas"].astype(str).apply(badge)

    if "Link" in df_display.columns:
        df_display["Link"] = df_display["Link"].apply(lambda x: f'<a href="{x}" target="_blank">Buka Link</a>')

    df_display = df_display.reset_index(drop=True)
    df_display.index = df_display.index + 1

    items_per_page = 8
    total_rows = len(df_display)
    total_pages = max(1, (total_rows - 1) // items_per_page + 1)

    if "page" not in st.session_state:
        st.session_state.page = 1
    if st.session_state.page > total_pages:
        st.session_state.page = 1

    start_idx = (st.session_state.page - 1) * items_per_page
    end_idx = start_idx + items_per_page
    df_page = df_display.iloc[start_idx:end_idx]

    preferred_cols = ["Judul", "Tanggal", "Waktu_Publish_WIB", "Tanggal_Hari", "Prioritas", "Link"]
    show_cols = [c for c in preferred_cols if c in df_page.columns]
    show_cols = show_cols or df_page.columns.tolist()

    st.write(df_page[show_cols].to_html(escape=False), unsafe_allow_html=True)

    st.markdown(f"""
    <div style='text-align:center; margin-top:10px; color:#475467;'>
    Menampilkan {min(start_idx+1, total_rows)} - {min(end_idx, total_rows)} dari {total_rows} berita
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col1:
        if st.button("⬅ Back", disabled=(st.session_state.page <= 1)):
            st.session_state.page -= 1
            st.rerun()
    with col3:
        if st.button("Next ➡", disabled=(st.session_state.page >= total_pages)):
            st.session_state.page += 1
            st.rerun()
    with col2:
        st.markdown(
            f"<div style='text-align:center; color:#475467;'>Halaman {st.session_state.page} dari {total_pages}</div>",
            unsafe_allow_html=True
        )