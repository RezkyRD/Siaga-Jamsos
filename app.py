import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import os

from scraper import run_scraper
from filter_keyword import run_filter
from update_priority import run_priority

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
# AUTO GENERATE DATA JIKA BELUM ADA
# ===============================
from scraper import run_scraper
from filter_keyword import run_filter
from update_priority import run_priority

if not os.path.exists("raw_news.csv") or not os.path.exists("filtered_news.csv"):
    with st.spinner("Memuat data awal..."):
        run_scraper()
        run_filter()
        run_priority()

# ===============================
# LOAD DATA
# ===============================
raw = pd.read_csv("raw_news.csv")
filtered = pd.read_csv("filtered_news.csv")
# gunakan tanggal publish jika ada
def ensure_publish_date(df):
    if "Tanggal_Publish" in df.columns:
        df["Tanggal_Hari"] = pd.to_datetime(df["Tanggal_Publish"], errors="coerce").dt.date
    else:
        df["Tanggal_Hari"] = pd.to_datetime(df["Tanggal"], errors="coerce").dt.date
    return df

raw = ensure_publish_date(raw)
filtered = ensure_publish_date(filtered)

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

raw["Tanggal_Hari"] = raw["Tanggal_Ambil"].dt.date
filtered["Tanggal_Hari"] = filtered["Tanggal_Ambil"].dt.date

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
    # KPI counts
    tinggi = (filtered_display["Prioritas"] == "PRIORITAS TINGGI").sum()
    sedang = (filtered_display["Prioritas"] == "PRIORITAS SEDANG").sum()
    rendah = (filtered_display["Prioritas"] == "PRIORITAS RENDAH").sum()

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

        st.markdown(f"""
        <div class="kpi-card">
          <div class="kpi-title">Ringkasan</div>
          <div style="margin:6px 0 10px 0;">{tag}</div>
          <div style="color:#344054; line-height:1.55;">
            Total berita terfilter: <b>{total:,}</b><br>
            Prioritas tinggi: <b>{tinggi:,}</b><br>
            Prioritas sedang: <b>{sedang:,}</b><br>
            Prioritas rendah: <b>{rendah:,}</b><br><br>
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

    # Urutkan prioritas: tinggi dulu
    priority_order = {"PRIORITAS TINGGI": 1, "PRIORITAS SEDANG": 2, "PRIORITAS RENDAH": 3}
    df_display = filtered_for_table.copy()
    df_display["Urutan"] = df_display["Prioritas"].map(priority_order)
    df_display = df_display.sort_values(["Urutan", "Tanggal_Ambil"], ascending=[True, False]).drop(columns=["Urutan"])

    # badge html
    def badge(prioritas):
        if prioritas == "PRIORITAS TINGGI":
            return "<span class='badge badge-high'>PRIORITAS TINGGI</span>"
        elif prioritas == "PRIORITAS SEDANG":
            return "<span class='badge badge-mid'>PRIORITAS SEDANG</span>"
        else:
            return "<span class='badge badge-low'>PRIORITAS RENDAH</span>"

    if "Prioritas" in df_display.columns:
        df_display["Prioritas"] = df_display["Prioritas"].apply(badge)

    # Link klik
    if "Link" in df_display.columns:
        df_display["Link"] = df_display["Link"].apply(lambda x: f'<a href="{x}" target="_blank">Buka Link</a>')

    # Reset index mulai 1
    df_display = df_display.reset_index(drop=True)
    df_display.index = df_display.index + 1

    # Pagination
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

    # Tampilkan tabel
    show_cols = [c for c in ["Judul", "Tanggal", "Prioritas", "Link"] if c in df_page.columns]
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