import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

st.title("Early Warning System - Isu Ketenagakerjaan")

# ===============================
# LOAD DATA
# ===============================
raw = pd.read_csv("raw_news.csv")
filtered = pd.read_csv("filtered_news.csv")

# ===============================
# DATE RANGE PICKER
# ===============================
st.subheader("📅 Pilih Rentang Tanggal")

# Pastikan kolom tanggal dalam format datetime
raw["Tanggal_Ambil"] = pd.to_datetime(raw["Tanggal_Ambil"])
filtered["Tanggal_Ambil"] = pd.to_datetime(filtered["Tanggal_Ambil"])

min_date = raw["Tanggal_Ambil"].min()
max_date = raw["Tanggal_Ambil"].max()

date_range = st.date_input(
    "Pilih Tanggal",
    [min_date, max_date]
)

# Jika user pilih range lengkap
if len(date_range) == 2:
    start_date = pd.to_datetime(date_range[0])
    end_date = pd.to_datetime(date_range[1])

    raw_filtered = raw[
        (raw["Tanggal_Ambil"] >= start_date) &
        (raw["Tanggal_Ambil"] <= end_date)
    ]

    filtered_display = filtered[
        (filtered["Tanggal_Ambil"] >= start_date) &
        (filtered["Tanggal_Ambil"] <= end_date)
    ]

else:
    raw_filtered = raw
    filtered_display = filtered

# ===============================
# METRIC
# ===============================
st.metric("Total Berita RAW", len(raw_filtered))
st.metric("Total Lolos Keyword", len(filtered_display))

# ===============================
# GRAFIK PRIORITAS
# ===============================
st.subheader("Distribusi Prioritas")

priority_counts = filtered_display["Prioritas"].value_counts()

if not priority_counts.empty:
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(8,4))

    priority_counts.sort_values().plot(
        kind="barh",
        ax=ax
    )

    ax.set_xlabel("Jumlah Berita")
    ax.set_ylabel("")
    ax.set_title("Distribusi Prioritas Berita")

    plt.tight_layout()
    st.pyplot(fig)

else:
    st.warning("Belum ada data.")

# ===============================
# DASHBOARD BERITA PROFESIONAL
# ===============================
st.subheader("📋 Monitoring Berita Ketenagakerjaan")

# Pastikan ada kolom prioritas

# ===============================
# FILTER PRIORITAS
# ===============================
filter_option = st.selectbox(
    "Filter Berdasarkan Prioritas",
    ["SEMUA", "PRIORITAS TINGGI", "PRIORITAS SEDANG", "PRIORITAS RENDAH"]
)

df_display = filtered_display.copy()

if filter_option != "SEMUA":
    df_display = df_display[df_display["Prioritas"] == filter_option]

# ===============================
# URUTKAN PRIORITAS (TINGGI DI ATAS)
# ===============================
priority_order = {
    "PRIORITAS TINGGI": 1,
    "PRIORITAS SEDANG": 2,
    "PRIORITAS RENDAH": 3
}

df_display["Urutan"] = df_display["Prioritas"].map(priority_order)
df_display = df_display.sort_values("Urutan")
df_display = df_display.drop(columns=["Urutan"])

# Reset index mulai dari 1
df_display = df_display.reset_index(drop=True)
df_display.index = df_display.index + 1

# ===============================
# BADGE WARNA PRIORITAS
# ===============================
def badge(prioritas):
    if prioritas == "PRIORITAS TINGGI":
        return "🔴 PRIORITAS TINGGI"
    elif prioritas == "PRIORITAS SEDANG":
        return "🟡 PRIORITAS SEDANG"
    else:
        return "🟢 PRIORITAS RENDAH"

df_display["Prioritas"] = df_display["Prioritas"].apply(badge)

# ===============================
# LINK KLIK
# ===============================
df_display["Link"] = df_display["Link"].apply(
    lambda x: f'<a href="{x}" target="_blank">Buka Link</a>'
)

# ===============================
# TAMPILKAN TABEL
# ===============================
st.markdown("""
<style>
table {
    width: 100%;
    text-align: center;
}
th {
    text-align: center !important;
}
td {
    text-align: center !important;
}
</style>
""", unsafe_allow_html=True)

st.write(
    df_display[["Judul", "Tanggal", "Prioritas", "Link"]].to_html(escape=False),
    unsafe_allow_html=True
)

# ===============================
# ANALISIS NARATIF
# ===============================
st.subheader("🧠 Analisis Situasi")

tinggi = (filtered_display["Prioritas"] == "PRIORITAS TINGGI").sum()
sedang = (filtered_display["Prioritas"] == "PRIORITAS SEDANG").sum()
rendah = (filtered_display["Prioritas"] == "PRIORITAS RENDAH").sum()
total = len(filtered_display)

if tinggi > 3:
    kondisi = "menunjukkan eskalasi signifikan"
    rekomendasi = "Diperlukan perhatian dan mitigasi cepat dari pemangku kebijakan."
elif tinggi > 0:
    kondisi = "menunjukkan potensi peningkatan risiko"
    rekomendasi = "Perlu pemantauan intensif untuk mencegah eskalasi konflik."
else:
    kondisi = "relatif stabil tanpa indikasi eskalasi besar"
    rekomendasi = "Pemantauan rutin tetap diperlukan sebagai langkah preventif."

narasi = f"""
Berdasarkan pemantauan terhadap {total} berita terkait isu ketenagakerjaan,
terdapat {tinggi} berita prioritas tinggi, {sedang} prioritas sedang,
dan {rendah} prioritas rendah.

Kondisi ini {kondisi}. {rekomendasi}
"""

st.write(narasi)