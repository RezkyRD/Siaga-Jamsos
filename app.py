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
/* Hilangkan highlight putih saat tap di HP */
table {
    -webkit-tap-highlight-color: transparent;
}

tbody tr:active {
    background-color: transparent !important;
}

tbody tr:focus {
    background-color: transparent !important;
}

tbody tr {
    transition: none !important;
}

/* ===== AKHIR TAMBAHAN ===== */
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div style="margin-bottom:20px;">
  <h1 style="color: var(--text-color); margin-bottom:0;">
    Early Warning System
  </h1>
  <p style="color: var(--text-color); opacity:0.75; font-size:18px; margin-top:4px;">
    Monitoring Isu Ketenagakerjaan
  </p>
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
# TOPIC DETECTION (TARUH DI SINI)
# =====================================
TOPIC_RULES = {
    # ===== ISU KETENAGAKERJAAN =====
    "PHK / Layoff": [r"\bphk\b", r"\blayoff\b", r"\bdirumahkan\b", r"pemutusan hubungan kerja"],
    "Upah / Gaji": [r"\bupah\b", r"\bgaji\b", r"tunggakan upah", r"tidak dibayar"],
    "Aksi / Demo": [r"\bdemo\b", r"unjuk rasa", r"aksi buruh", r"mogok"],
    "Pabrik Tutup / Pailit": [r"pabrik tutup", r"tutup permanen", r"\bpailit\b", r"\bbangkrut\b", r"likuidasi"],
    "Konflik Hubungan Industrial": [r"perselisihan", r"konflik buruh", r"sengketa", r"tripartit", r"mediasi"],

    # ===== ISU BPJS KETENAGAKERJAAN =====
    "Klaim JHT": [r"\bjht\b", r"jaminan hari tua", r"klaim jht", r"pencairan jht", r"saldo jht"],
    "Jaminan Pensiun (JP)": [r"\bjp\b", r"jaminan pensiun", r"manfaat pensiun", r"iuran pensiun", r"usia pensiun", r"pensiun pekerja"],
    "Manfaat JKP": [r"\bjkp\b", r"jaminan kehilangan pekerjaan", r"manfaat jkp", r"klaim jkp"],
    "Kecelakaan Kerja (JKK)": [r"\bjkk\b", r"jaminan kecelakaan kerja", r"kecelakaan kerja", r"santunan jkk"],
    "Santunan Kematian (JKM)": [r"\bjkm\b", r"jaminan kematian", r"santunan kematian", r"ahli waris"],
    "Kepesertaan BPJS": [r"bpjs ketenagakerjaan", r"bpjamsostek", r"jamsostek", r"kepesertaan bpjs", r"terdaftar bpjs"],
    "Tunggakan Iuran": [r"tunggakan iuran", r"menunggak iuran", r"telat bayar", r"denda", r"iuran bpjs"],
    "Kendala Klaim BPJS": [r"klaim ditolak", r"kendala klaim", r"klaim lama", r"antrian klaim", r"verifikasi klaim"],
    "Pengawasan Kepatuhan": [r"pengawasan", r"pemeriksaan", r"sanksi", r"kepatuhan perusahaan", r"tidak patuh"],
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
        # ===============================
        # 📰 TOP 5 PRIORITAS TINGGI (CLICKABLE)
        # ===============================
        st.markdown("### 📰 Top 5 Berita Prioritas Tinggi (Terbaru)")

        df_high = filtered_display[
            filtered_display["Prioritas"] == "PRIORITAS TINGGI"
        ].copy()

        if not df_high.empty:
            if "Waktu_Publish_WIB" in df_high.columns:
                df_high = df_high.sort_values(
                    "Waktu_Publish_WIB",
                    ascending=False
                )

            top5 = df_high.head(5)

            for _, row in top5.iterrows():
                media = row.get("Media", "-")
                judul = row.get("Judul", "-")
                link = row.get("Link", "")
                waktu = row.get("Waktu_Publish_WIB", "")

                if link:
                    st.markdown(
                        f"- **[{judul}]({link})**  \n  _{media} • {waktu}_"
                    )
                else:
                    st.markdown(
                        f"- **{judul}**  \n  _{media} • {waktu}_"
                    )
        else:
            st.info("Belum ada berita prioritas tinggi.")

    else:
        st.warning("Belum ada data.")

with right:
    st.subheader("🧠 Analisis Situasi")
    total = len(filtered_display)

    if tinggi > 3:
        status_txt = "🔴 RISIKO TINGGI"
        kondisi = "menunjukkan eskalasi signifikan"
        rekomendasi = "Perlu mitigasi cepat dan koordinasi lintas unit."
    elif tinggi > 0:
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

# ===============================
# TAB: DATA BERITA
# ===============================
with tab_data:
    st.subheader("📰 Monitoring Berita Ketenagakerjaan")
    st.caption("Gunakan filter di sidebar untuk mengatur rentang tanggal dan prioritas.")

    # ambil data untuk tabel dari hasil filter sidebar (sama seperti dulu)
    df_display = filtered_for_table.copy()

    # kalau kosong, tampilkan info (biar tidak blank)
    if df_display.empty:
        st.info("Tidak ada berita untuk filter yang dipilih.")
        st.stop()

    # Urutkan prioritas: tinggi dulu
    priority_order = {"PRIORITAS TINGGI": 1, "PRIORITAS SEDANG": 2, "PRIORITAS RENDAH": 3}
    df_display["Urutan"] = df_display["Prioritas"].map(priority_order).fillna(99)

    # tentukan kolom waktu untuk sort (cocok untuk app baru)
    sort_col = None
    for c in ["Waktu_Publish_WIB", "Tanggal_Publish", "Tanggal_Ambil", "Tanggal_Hari"]:
        if c in df_display.columns:
            sort_col = c
            break
    if sort_col is None:
        sort_col = "Urutan"  # fallback

    df_display = df_display.sort_values(["Urutan", sort_col], ascending=[True, False]).drop(columns=["Urutan"])

    # badge html (sama seperti dulu)
    def badge(prioritas):
        if prioritas == "PRIORITAS TINGGI":
            return "<span class='badge badge-high'>PRIORITAS TINGGI</span>"
        elif prioritas == "PRIORITAS SEDANG":
            return "<span class='badge badge-mid'>PRIORITAS SEDANG</span>"
        else:
            return "<span class='badge badge-low'>PRIORITAS RENDAH</span>"

    if "Prioritas" in df_display.columns:
        df_display["Prioritas"] = df_display["Prioritas"].astype(str).apply(badge)

    # Link klik (sama seperti dulu)
    if "Link" in df_display.columns:
        df_display["Link"] = df_display["Link"].apply(lambda x: f'<a href="{x}" target="_blank">Buka Link</a>')

    # Reset index mulai 1 (sama seperti dulu)
    df_display = df_display.reset_index(drop=True)
    df_display.index = df_display.index + 1

    # Pagination (sama seperti dulu)
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

    # Tampilkan tabel (versi baru: fleksibel kolom tanggal)
    preferred_cols = ["Judul", "Tanggal", "Waktu_Publish_WIB", "Tanggal_Hari", "Prioritas", "Dampak_Program", "Dampak_Kepesertaan", "Potensi_Klaim", "Alasan_Prioritas", "Link"]
    show_cols = [c for c in preferred_cols if c in df_page.columns]
    if not show_cols:
        show_cols = df_page.columns.tolist()

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
# ===============================
# 🔥 INDEKS ESKALASI ISU (berdasarkan Topik)
# ===============================
    st.markdown("## 🔥 Indeks Eskalasi Isu")

    df_ews = filtered_display.copy()

# pastikan kolom Topik sudah ada
    if "Topik" not in df_ews.columns:
        df_ews["Topik"] = df_ews.get("Judul","").astype(str).apply(detect_topic)

# tentukan kolom waktu publish
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
            return pd.DataFrame(columns=["Topik","Berita 24 Jam","Media 24 Jam","Headline"])
        out = df_recent.groupby("Topik", dropna=False).agg(
        **{"Berita 24 Jam": ("Judul","count"), "Media 24 Jam": ("Media", pd.Series.nunique)}
        ).reset_index()
        head = (df_recent.sort_values("publish_dt", ascending=False)
                .groupby("Topik", dropna=False).head(1)[["Topik","Judul"]]
                .rename(columns={"Judul":"Headline"}))
        return out.merge(head, on="Topik", how="left")

    s1 = agg(w1)
    s0 = agg(w0).rename(columns={"Berita 24 Jam":"Berita 24-48 Jam", "Media 24 Jam":"Media 24-48 Jam"})

    esk = s1.merge(s0[["Topik","Berita 24-48 Jam","Media 24-48 Jam"]], on="Topik", how="left")
    esk[["Berita 24-48 Jam","Media 24-48 Jam"]] = esk[["Berita 24-48 Jam","Media 24-48 Jam"]].fillna(0).astype(int)

    esk["Skor"] = esk["Media 24 Jam"]*3 + esk["Berita 24 Jam"]

    def trend(r):
        if r["Media 24 Jam"] > r["Media 24-48 Jam"]:
            return "📈 Naik"
        if r["Media 24 Jam"] < r["Media 24-48 Jam"]:
            return "📉 Turun"
        return "➖ Stabil"

    esk["Trend"] = esk.apply(trend, axis=1)
    esk = esk.sort_values(["Skor","Media 24 Jam","Berita 24 Jam"], ascending=False)

    st.dataframe(
        esk[["Topik","Trend","Media 24 Jam","Berita 24 Jam","Media 24-48 Jam","Berita 24-48 Jam","Skor","Headline"]].head(10),
        use_container_width=True,
        hide_index=True
    )