import re
import json
import time
import urllib.request
import urllib.error
import pandas as pd
import streamlit as st

from gsheet_utils import read_sheet, clear_and_write


# =====================================
# KONTEKS INDONESIA
# =====================================

INDONESIA_CONTEXT = [
    "indonesia", "jakarta", "jawa", "sumatera", "kalimantan", "sulawesi", "papua", "bali",
    "aceh", "sumut", "sumbar", "riau", "kepri", "jambi", "sumsel", "babel", "bengkulu",
    "lampung", "banten", "dki", "jabar", "jateng", "jatim", "diy",
    "ntb", "ntt", "kalbar", "kalteng", "kalsel", "kaltim", "kaltara",
    "sulut", "gorontalo", "sulteng", "sulbar", "sulsel", "sultra",
    "maluku", "malut", "papua barat",
    "bandung", "surabaya", "medan", "makassar", "karawang", "bekasi",
    "tangerang", "semarang", "batam", "bogor", "depok", "cikarang",
    "kemnaker", "disnaker", "bpjs ketenagakerjaan", "bpjamsostek",
    "pekerja migran indonesia", "buruh indonesia", "pekerja indonesia",
    "kabupaten", "kota", "provinsi", "gubernur", "bupati", "wali kota"
]

GLOBAL_COMPANY = [
    "amazon", "google", "alphabet", "morgan stanley", "meta", "facebook",
    "instagram", "apple", "tesla", "microsoft", "intel", "nvidia", "tiktok",
    "netflix", "warner bros", "ubisoft", "sony", "samsung", "epic games",
    "oracle", "sap", "ibm", "adobe", "cisco", "paypal", "spotify", "bytedance",
    "xiaomi", "foxconn", "boeing", "dell", "hp", "ea", "electronic arts",
    "openai", "anthropic"
]

MEDIA_NOISE = [
    "cnn indonesia", "cnbc indonesia", "kompas.com", "detik", "tempo.co",
    "tribunnews", "bisnis.com", "liputan6", "kontan", "antara", "jpnn",
    "kumparan", "republika", "okezone", "sindonews", "suara.com", "idxchannel"
]


# =====================================
# PETA LOKASI
# =====================================

PROVINCE_ALIASES = {
    "aceh": "Aceh",
    "sumatera utara": "Sumatera Utara", "sumut": "Sumatera Utara",
    "sumatera barat": "Sumatera Barat", "sumbar": "Sumatera Barat",
    "riau": "Riau",
    "kepulauan riau": "Kepulauan Riau", "kepri": "Kepulauan Riau",
    "jambi": "Jambi",
    "sumatera selatan": "Sumatera Selatan", "sumsel": "Sumatera Selatan",
    "kepulauan bangka belitung": "Kepulauan Bangka Belitung",
    "bangka belitung": "Kepulauan Bangka Belitung", "babel": "Kepulauan Bangka Belitung",
    "bengkulu": "Bengkulu", "lampung": "Lampung", "banten": "Banten",
    "dki jakarta": "DKI Jakarta", "jakarta": "DKI Jakarta", "dki": "DKI Jakarta",
    "jawa barat": "Jawa Barat", "jabar": "Jawa Barat",
    "jawa tengah": "Jawa Tengah", "jateng": "Jawa Tengah",
    "di yogyakarta": "DI Yogyakarta", "diy": "DI Yogyakarta", "yogyakarta": "DI Yogyakarta",
    "jawa timur": "Jawa Timur", "jatim": "Jawa Timur",
    "bali": "Bali",
    "nusa tenggara barat": "Nusa Tenggara Barat", "ntb": "Nusa Tenggara Barat",
    "nusa tenggara timur": "Nusa Tenggara Timur", "ntt": "Nusa Tenggara Timur",
    "kalimantan barat": "Kalimantan Barat", "kalbar": "Kalimantan Barat",
    "kalimantan tengah": "Kalimantan Tengah", "kalteng": "Kalimantan Tengah",
    "kalimantan selatan": "Kalimantan Selatan", "kalsel": "Kalimantan Selatan",
    "kalimantan timur": "Kalimantan Timur", "kaltim": "Kalimantan Timur",
    "kalimantan utara": "Kalimantan Utara", "kaltara": "Kalimantan Utara",
    "sulawesi utara": "Sulawesi Utara", "sulut": "Sulawesi Utara",
    "gorontalo": "Gorontalo",
    "sulawesi tengah": "Sulawesi Tengah", "sulteng": "Sulawesi Tengah",
    "sulawesi barat": "Sulawesi Barat", "sulbar": "Sulawesi Barat",
    "sulawesi selatan": "Sulawesi Selatan", "sulsel": "Sulawesi Selatan",
    "sulawesi tenggara": "Sulawesi Tenggara", "sultra": "Sulawesi Tenggara",
    "maluku": "Maluku",
    "maluku utara": "Maluku Utara", "malut": "Maluku Utara",
    "papua": "Papua", "papua barat": "Papua Barat",
}

CITY_TO_PROVINCE = {
    "kabupaten bekasi": ("Kabupaten Bekasi", "Jawa Barat"),
    "kota bekasi": ("Kota Bekasi", "Jawa Barat"),
    "bekasi": ("Bekasi", "Jawa Barat"),
    "karawang": ("Karawang", "Jawa Barat"),
    "bandung": ("Bandung", "Jawa Barat"),
    "bogor": ("Bogor", "Jawa Barat"),
    "depok": ("Depok", "Jawa Barat"),
    "cikarang": ("Cikarang", "Jawa Barat"),
    "jakarta": ("DKI Jakarta", "DKI Jakarta"),
    "surabaya": ("Surabaya", "Jawa Timur"),
    "sidoarjo": ("Sidoarjo", "Jawa Timur"),
    "gresik": ("Gresik", "Jawa Timur"),
    "semarang": ("Semarang", "Jawa Tengah"),
    "batam": ("Batam", "Kepulauan Riau"),
    "medan": ("Medan", "Sumatera Utara"),
    "makassar": ("Makassar", "Sulawesi Selatan"),
    "kabupaten tangerang": ("Kabupaten Tangerang", "Banten"),
    "kota tangerang": ("Kota Tangerang", "Banten"),
    "tangerang": ("Tangerang", "Banten"),
}


# =====================================
# OUTPUT COLUMNS
# =====================================

OUTPUT_COLUMNS = [
    "Media", "Judul", "Tanggal", "Link", "Ringkasan",
    "Waktu_Publish_WIB", "Tanggal_Publish", "Waktu_Ambil_UTC",
    "Waktu_Ambil_WIB", "Tanggal_Ambil", "UID",
    "Konteks_Berita", "Kategori_Berita", "Provinsi", "Kabupaten_Kota",
    "Status_Lokasi", "Topik_Utama", "Score", "Dampak_Program",
    "Dampak_Kepesertaan", "Potensi_Klaim", "Alasan_Prioritas",
    "Prioritas", "Metode_Analisis",
]


# =====================================
# HELPERS
# =====================================

def clean_text(text: str) -> str:
    text = str(text or "").lower()
    text = re.sub(r"\s+", " ", text).strip()
    return text


def contains_any(text: str, patterns) -> bool:
    return any(re.search(p, text) for p in patterns)


def unique_join(items) -> str:
    out, seen = [], set()
    for item in items:
        item = str(item).strip()
        if item and item not in seen:
            seen.add(item)
            out.append(item)
    return ", ".join(out)


def ensure_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    for col in OUTPUT_COLUMNS:
        if col not in df.columns:
            df[col] = ""
    return df[OUTPUT_COLUMNS]


def strip_media_noise(text: str) -> str:
    text = clean_text(text)
    for noise in MEDIA_NOISE:
        text = re.sub(rf"\b{re.escape(noise)}\b", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def has_global_company(text: str) -> bool:
    return any(g in text for g in GLOBAL_COMPANY)


# =====================================
# LOKASI
# =====================================

def detect_location(text: str) -> dict:
    text = clean_text(text)
    for key, (city_name, province_name) in CITY_TO_PROVINCE.items():
        if re.search(rf"\b{re.escape(key)}\b", text):
            return {"Provinsi": province_name, "Kabupaten_Kota": city_name, "Status_Lokasi": "Spesifik"}
    for alias, province_name in PROVINCE_ALIASES.items():
        if re.search(rf"\b{re.escape(alias)}\b", text):
            return {"Provinsi": province_name, "Kabupaten_Kota": "", "Status_Lokasi": "Provinsi"}
    if any(k in text for k in ["indonesia", "nasional", "kemnaker", "bpjs ketenagakerjaan", "bpjamsostek"]):
        return {"Provinsi": "Nasional", "Kabupaten_Kota": "", "Status_Lokasi": "Nasional / Tidak Spesifik"}
    return {"Provinsi": "", "Kabupaten_Kota": "", "Status_Lokasi": "Tidak Diketahui"}


# =====================================
# KATEGORI & KONTEKS
# =====================================

def has_real_indonesia_context(text: str) -> bool:
    text = strip_media_noise(text)
    lokasi = detect_location(text)
    if lokasi["Provinsi"] not in ["", "Nasional"]:
        return True
    strong_context = [
        "di indonesia", "wilayah indonesia", "nasional", "kemnaker", "disnaker",
        "bpjs ketenagakerjaan", "bpjamsostek", "pekerja indonesia", "buruh indonesia",
        "karyawan di indonesia", "perusahaan di indonesia", "pabrik di indonesia",
        "peserta bpjs", "kepesertaan bpjs", "klaim jht", "klaim jkp",
        "jkk", "jkm", "jht", "jkp", "jp"
    ]
    return any(k in text for k in strong_context)


def is_indonesia_related(text: str) -> bool:
    text = clean_text(text)
    if any(k in text for k in ["pekerja migran indonesia", "buruh migran indonesia", "pmi indonesia", "tki indonesia", "wni"]):
        return True
    if has_global_company(text):
        return has_real_indonesia_context(text)
    return has_real_indonesia_context(text) or any(k in strip_media_noise(text) for k in INDONESIA_CONTEXT)


def get_context_label(text: str) -> str:
    if is_indonesia_related(text):
        return "INDONESIA"
    if re.search(r"\bpmi\b|pekerja migran|\btki\b", text):
        return "PMI"
    return "LUAR NEGERI / TIDAK RELEVAN"


def is_service_education(text: str) -> bool:
    return contains_any(text, [
        r"cara klaim", r"syarat klaim", r"panduan", r"tutorial",
        r"begini cara", r"cara mencairkan", r"cara cairkan",
        r"bisa cairkan saldo", r"cek saldo", r"saldo jht",
        r"aplikasi jmo", r"\bjmo\b", r"prosedur", r"alur klaim",
        r"tips klaim", r"simak caranya", r"begini syarat", r"ini syarat",
    ])


def detect_category(text: str) -> str:
    if is_service_education(text):
        return "EDUKASI"
    if is_indonesia_related(text):
        return "NASIONAL"
    return "GLOBAL"


# =====================================
# TOPIC & KEPESERTAAN (RULE-BASED)
# =====================================

def detect_topic(text: str) -> str:
    if is_service_education(text):
        return "Layanan / Edukasi Klaim"
    topic_rules = [
        ("PHK", [r"\bphk\b", r"pemutusan hubungan kerja", r"\bdirumahkan\b", r"phk massal", r"gelombang phk", r"efisiensi tenaga kerja", r"pengurangan karyawan"]),
        ("THR / Kesejahteraan Pekerja", [r"\bthr\b", r"tunjangan hari raya", r"pengaduan thr", r"posko thr", r"thr.*tidak dibayar", r"thr.*terlambat", r"thr.*dicicil", r"thr.*dipotong"]),
        ("Upah / Gaji", [r"\bupah\b", r"\bgaji\b", r"\bump\b", r"\bumk\b", r"upah minimum", r"tunggakan upah", r"gaji tidak dibayar"]),
        ("Aksi / Demo Buruh", [r"demo buruh", r"unjuk rasa", r"aksi buruh", r"mogok kerja"]),
        ("Konflik Hubungan Industrial", [r"perselisihan", r"sengketa", r"konflik buruh", r"mediasi hubungan industrial", r"tripartit"]),
        ("Kecelakaan Kerja (JKK)", [r"kecelakaan kerja", r"\bledakan\b", r"kebakaran pabrik", r"tertimbun", r"pekerja jatuh", r"buruh tewas", r"pekerja tewas"]),
        ("Kepesertaan BPJS", [r"bpjs ketenagakerjaan", r"bpjamsostek", r"jamsostek", r"kepesertaan bpjs", r"peserta bpjs", r"terdaftar bpjs"]),
        ("Klaim JHT", [r"\bjht\b", r"jaminan hari tua", r"klaim jht", r"pencairan jht", r"saldo jht"]),
        ("Manfaat JKP", [r"\bjkp\b", r"jaminan kehilangan pekerjaan", r"klaim jkp", r"manfaat jkp"]),
        ("Jaminan Pensiun (JP)", [r"jaminan pensiun", r"iuran pensiun", r"usia pensiun"]),
        ("Santunan Kematian (JKM)", [r"\bjkm\b", r"jaminan kematian", r"santunan kematian", r"ahli waris"]),
        ("Tunggakan Iuran", [r"tunggakan iuran", r"menunggak iuran", r"telat bayar iuran", r"denda bpjs"]),
        ("Pekerja Migran Indonesia (PMI)", [r"\bpmi\b", r"pekerja migran", r"\btki\b", r"buruh migran"]),
        ("Jasa Konstruksi", [r"konstruksi", r"proyek", r"pembangunan", r"jasa konstruksi"]),
    ]
    for topic, patterns in topic_rules:
        if contains_any(text, patterns):
            return topic
    if re.search(r"buruh|pekerja|ketenagakerjaan|tenaga kerja", text):
        return "Isu Ketenagakerjaan Umum"
    return "Regulasi & Kebijakan Ketenagakerjaan"


def detect_kepesertaan(text: str):
    hasil = []
    if contains_any(text, [r"perusahaan", r"karyawan", r"pekerja formal", r"buruh pabrik", r"pegawai", r"hubungan industrial", r"phk", r"thr", r"upah", r"gaji"]):
        hasil.append("PU")
    if contains_any(text, [r"\bbpu\b", r"bukan penerima upah", r"pekerja informal", r"pedagang", r"nelayan", r"petani", r"ojek", r"driver", r"umkm", r"wirausaha"]):
        hasil.append("BPU")
    if contains_any(text, [r"\bpmi\b", r"pekerja migran", r"\btki\b", r"buruh migran"]):
        hasil.append("PMI")
    if contains_any(text, [r"konstruksi", r"proyek", r"pembangunan", r"jasa konstruksi"]):
        hasil.append("Jasa Konstruksi")
    return hasil


# =====================================
# PRIORITY CLASSIFIER & REASON
# =====================================

def classify_priority(score: int, category: str, topic: str) -> str:
    if category in ["EDUKASI", "GLOBAL"]:
        return "PRIORITAS RENDAH"
    if score >= 7:
        return "PRIORITAS TINGGI"
    if score >= 4:
        return "PRIORITAS SEDANG"
    return "PRIORITAS RENDAH"


def build_short_reason(topic: str, programs: str, claims: str, category: str) -> str:
    if category == "EDUKASI":
        return "Berita bersifat edukasi layanan dan tidak memerlukan penanganan prioritas."
    if category == "GLOBAL":
        return "Berita global dipantau sebagai referensi dan bukan fokus utama analisis nasional."
    reasons = {
        "PHK": "PHK berpotensi meningkatkan klaim JKP dan pencairan JHT.",
        "Kecelakaan Kerja (JKK)": "Kecelakaan kerja berpotensi menimbulkan klaim JKK.",
        "THR / Kesejahteraan Pekerja": "Permasalahan THR berpotensi memicu konflik hubungan industrial.",
        "Upah / Gaji": "Isu upah berpotensi memicu perselisihan dan mempengaruhi stabilitas hubungan kerja.",
        "Kepesertaan BPJS": "Isu kepesertaan berdampak pada cakupan perlindungan tenaga kerja.",
        "Tunggakan Iuran": "Tunggakan iuran berdampak pada kepatuhan dan kesinambungan perlindungan peserta.",
        "Manfaat JKP": "Isu JKP berkaitan langsung dengan perlindungan pekerja terdampak PHK.",
        "Klaim JHT": "Isu JHT berkaitan dengan pencairan manfaat peserta.",
        "Santunan Kematian (JKM)": "Kasus kematian pekerja berpotensi menimbulkan klaim JKM.",
        "Jaminan Pensiun (JP)": "Isu JP berkaitan dengan kesinambungan manfaat jangka panjang peserta.",
        "Aksi / Demo Buruh": "Aksi buruh berpotensi meningkatkan tensi hubungan industrial.",
        "Konflik Hubungan Industrial": "Konflik hubungan industrial perlu dipantau karena dapat berkembang menjadi gangguan yang lebih besar.",
        "Pekerja Migran Indonesia (PMI)": "Isu PMI berkaitan dengan perlindungan jaminan sosial pekerja migran Indonesia.",
        "Jasa Konstruksi": "Sektor konstruksi memiliki risiko tinggi terhadap kecelakaan kerja.",
    }
    if topic in reasons:
        return reasons[topic]
    if claims:
        return f"Isu ini berpotensi mempengaruhi klaim {claims}."
    if programs:
        return f"Isu ini berdampak pada program {programs}."
    return "Isu ini perlu dipantau karena dapat mempengaruhi jaminan sosial ketenagakerjaan."


def get_time_boost(row) -> int:
    try:
        publish_str = str(row.get("Waktu_Publish_WIB", "")).strip()
        if not publish_str:
            return 0
        publish_dt = pd.to_datetime(publish_str, errors="coerce")
        if pd.isna(publish_dt):
            return 0
        # FIX: gunakan now() tanpa tz agar konsisten dengan publish_dt
        now = pd.Timestamp.now()
        diff_hours = (now - publish_dt).total_seconds() / 3600
        if diff_hours <= 6:
            return 3
        if diff_hours <= 24:
            return 2
        if diff_hours <= 48:
            return 1
        return 0
    except Exception:
        return 0


# =====================================
# RULE-BASED ANALYZER (tetap sebagai fallback)
# =====================================

def analyze_rule_based(text: str, row=None) -> dict:
    kategori = detect_category(text)
    topik = detect_topic(text)

    if has_global_company(text) and not has_real_indonesia_context(text):
        return {
            "Topik_Utama": topik, "Kategori_Berita": "GLOBAL",
            "Score": 0, "Dampak_Program": "", "Dampak_Kepesertaan": "",
            "Potensi_Klaim": "", "Alasan_Prioritas": "Berita global tidak relevan dengan konteks Indonesia.",
        }

    score = 0
    program = []
    kepesertaan = detect_kepesertaan(text)
    klaim = []
    edukasi = is_service_education(text)

    if contains_any(text, [r"\bphk\b", r"pemutusan hubungan kerja", r"\bdirumahkan\b"]):
        score += 4 if not edukasi else 1
        program.extend(["JKP", "JHT", "JP"]); kepesertaan.append("PU"); klaim.extend(["JKP", "JHT"])
    if contains_any(text, [r"phk.*massal", r"massal.*phk", r"gelombang phk", r"ribuan karyawan", r"ratusan karyawan", r"tutup pabrik", r"pabrik tutup", r"\bpailit\b", r"\bbangkrut\b"]):
        score += 4
    if contains_any(text, [r"kecelakaan kerja", r"\bledakan\b", r"kebakaran pabrik", r"tertimbun", r"pekerja jatuh", r"alat berat", r"lokasi proyek"]):
        score += 4; program.append("JKK"); klaim.append("JKK")
    if contains_any(text, [r"meninggal dunia", r"pekerja tewas", r"buruh tewas", r"korban jiwa"]):
        score += 3; program.append("JKM"); klaim.append("JKM")
    if contains_any(text, [r"demo buruh", r"unjuk rasa", r"aksi buruh", r"mogok kerja"]):
        score += 3
    if contains_any(text, [r"perselisihan", r"sengketa", r"konflik buruh", r"mediasi hubungan industrial"]):
        score += 2
    if contains_any(text, [r"\bthr\b", r"tunjangan hari raya"]):
        score += 2; kepesertaan.append("PU")
    if contains_any(text, [r"thr.*tidak dibayar", r"tidak dibayar.*thr", r"thr.*terlambat", r"thr.*dicicil", r"thr.*dipotong", r"pengaduan thr", r"posko thr"]):
        score += 2
    if contains_any(text, [r"\bupah\b", r"\bgaji\b", r"\bump\b", r"\bumk\b", r"upah minimum", r"tunggakan upah", r"gaji tidak dibayar"]):
        score += 2; kepesertaan.append("PU")
    if contains_any(text, [r"bpjs ketenagakerjaan", r"bpjamsostek", r"jamsostek", r"kepesertaan bpjs", r"peserta bpjs", r"terdaftar bpjs"]):
        score += 2 if not edukasi else 1; program.append("Kepesertaan")
    if contains_any(text, [r"tunggakan iuran", r"menunggak iuran", r"telat bayar iuran", r"denda bpjs", r"tidak patuh", r"sanksi perusahaan", r"pemeriksaan", r"pengawasan"]):
        score += 3; program.append("Kepesertaan")
    if contains_any(text, [r"\bjht\b", r"jaminan hari tua", r"klaim jht", r"pencairan jht", r"saldo jht"]):
        score += 2 if not edukasi else 1; program.append("JHT"); klaim.append("JHT")
    if contains_any(text, [r"\bjkp\b", r"jaminan kehilangan pekerjaan", r"klaim jkp", r"manfaat jkp"]):
        score += 2 if not edukasi else 1; program.append("JKP"); klaim.append("JKP")
    if contains_any(text, [r"jaminan pensiun", r"iuran pensiun", r"usia pensiun"]):
        score += 1; program.append("JP")
    if contains_any(text, [r"\bjkm\b", r"jaminan kematian", r"santunan kematian", r"ahli waris"]):
        score += 1; program.append("JKM"); klaim.append("JKM")
    if contains_any(text, [r"\bpmi\b", r"pekerja migran", r"\btki\b"]):
        score += 2; kepesertaan.append("PMI"); program.append("Kepesertaan")
    if contains_any(text, [r"konstruksi", r"proyek", r"pembangunan", r"jasa konstruksi"]):
        score += 1; kepesertaan.append("Jasa Konstruksi"); program.append("JKK")
    if row is not None and kategori == "NASIONAL":
        score += get_time_boost(row)
    if kategori == "GLOBAL":
        score = 0
    if kategori == "EDUKASI":
        score = min(score, 2)
    if kategori == "NASIONAL" and not has_real_indonesia_context(text):
        kategori = "GLOBAL"; score = 0

    program = unique_join(program)
    kepesertaan = unique_join(kepesertaan)
    klaim = unique_join(klaim)
    alasan = build_short_reason(topik, program, klaim, kategori)

    return {
        "Topik_Utama": topik, "Kategori_Berita": kategori,
        "Score": int(score), "Dampak_Program": program,
        "Dampak_Kepesertaan": kepesertaan, "Potensi_Klaim": klaim,
        "Alasan_Prioritas": alasan,
    }


# =====================================
# LLM ANALYZER — Claude Haiku
# =====================================

LLM_SYSTEM_PROMPT = """Kamu adalah sistem analisis berita otomatis untuk Early Warning System (EWS) Ketenagakerjaan Indonesia di Kementerian Ketenagakerjaan.

Tugasmu menganalisis setiap berita ketenagakerjaan dan menentukan:
1. Prioritas (TINGGI/SEDANG/RENDAH) berdasarkan dampak nyata ke pekerja dan program BPJS Ketenagakerjaan
2. Topik utama berita
3. Program BPJS yang terdampak (JHT, JKP, JKK, JKM, JP, Kepesertaan)
4. Provinsi/lokasi kejadian (jika ada)
5. Alasan prioritas yang spesifik dan kontekstual

PANDUAN PRIORITAS:
- TINGGI: PHK massal, kecelakaan kerja fatal, demo besar/mogok, tunggakan iuran besar, fraud BPJS
- SEDANG: PHK individual, konflik industrial, klaim bermasalah, peraturan baru berdampak
- RENDAH: Berita positif/informatif, edukasi, statistik rutin, kebijakan minor

PENTING:
- Baca konteks berita secara utuh. "Pemerintah CEGAH PHK Massal" = RENDAH, bukan TINGGI
- Berita edukasi/panduan = selalu RENDAH
- Berita global tanpa konteks Indonesia = RENDAH
- Score 1-10: 8-10=TINGGI, 4-7=SEDANG, 1-3=RENDAH

Kembalikan HANYA JSON valid tanpa teks lain:
{
  "Topik_Utama": "string",
  "Kategori_Berita": "NASIONAL|GLOBAL|EDUKASI",
  "Score": integer 1-10,
  "Dampak_Program": "JKP, JHT, JKK, ...",
  "Dampak_Kepesertaan": "PU, BPU, PMI, Jasa Konstruksi",
  "Potensi_Klaim": "JKP, JHT, ...",
  "Alasan_Prioritas": "kalimat spesifik berdasarkan isi berita"
}"""


def call_claude_api(judul: str, ringkasan: str, api_key: str, retries: int = 2) -> dict | None:
    """
    Panggil Claude Haiku API untuk satu berita.
    Return dict hasil atau None jika gagal.
    """
    prompt = f"Judul: {judul}\nRingkasan: {ringkasan}"
    payload = json.dumps({
        "model": "claude-haiku-4-5-20251001",
        "max_tokens": 400,
        "system": LLM_SYSTEM_PROMPT,
        "messages": [{"role": "user", "content": prompt}]
    }).encode()

    for attempt in range(retries + 1):
        try:
            req = urllib.request.Request(
                "https://api.anthropic.com/v1/messages",
                data=payload,
                headers={
                    "x-api-key": api_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                method="POST"
            )
            with urllib.request.urlopen(req, timeout=15) as resp:
                result = json.loads(resp.read())
                raw_text = result["content"][0]["text"].strip()

                # Bersihkan jika ada markdown code fence
                raw_text = re.sub(r"^```json\s*", "", raw_text)
                raw_text = re.sub(r"\s*```$", "", raw_text)

                parsed = json.loads(raw_text)

                # Validasi field wajib
                required = ["Topik_Utama", "Kategori_Berita", "Score", "Alasan_Prioritas"]
                if all(k in parsed for k in required):
                    # Normalisasi
                    parsed["Score"] = int(parsed.get("Score", 3))
                    parsed["Dampak_Program"] = str(parsed.get("Dampak_Program", ""))
                    parsed["Dampak_Kepesertaan"] = str(parsed.get("Dampak_Kepesertaan", ""))
                    parsed["Potensi_Klaim"] = str(parsed.get("Potensi_Klaim", ""))
                    return parsed

        except urllib.error.HTTPError as e:
            if e.code == 429 and attempt < retries:
                # Rate limit — tunggu dan retry
                time.sleep(2 ** attempt)
                continue
            return None
        except Exception:
            if attempt < retries:
                time.sleep(1)
                continue
            return None

    return None


def analyze_with_llm_batch(df: pd.DataFrame, api_key: str, batch_size: int = 20) -> list[dict | None]:
    """
    Analisis batch berita dengan LLM.
    Return list of (dict hasil | None) dengan panjang sama dengan df.
    """
    results = [None] * len(df)

    for i in range(0, len(df), batch_size):
        batch = df.iloc[i:i + batch_size]
        for j, (idx, row) in enumerate(batch.iterrows()):
            judul = str(row.get("Judul", "")).strip()
            ringkasan = str(row.get("Ringkasan", "")).strip()

            result = call_claude_api(judul, ringkasan, api_key)
            results[i + j] = result

            # Jeda kecil antar request agar tidak kena rate limit
            time.sleep(0.15)

    return results


# =====================================
# MAIN RUN
# =====================================

def run_priority(sheet_key=None):
    if sheet_key is None:
        sheet_key = st.secrets["SHEET_KEY"]

    # Ambil API key (opsional)
    api_key = ""
    try:
        api_key = st.secrets.get("ANTHROPIC_API_KEY", "")
    except Exception:
        pass

    use_llm = bool(api_key)

    try:
        df = read_sheet(sheet_key, "FILTERED")
    except Exception:
        df = pd.DataFrame()

    if df is None or df.empty:
        empty_df = pd.DataFrame(columns=OUTPUT_COLUMNS)
        clear_and_write(sheet_key, "ANALYZED", empty_df)
        return empty_df

    df = df.copy()
    df.columns = df.columns.astype(str).str.strip()

    judul_s = df.get("Judul", pd.Series([""] * len(df), index=df.index)).astype(str).fillna("")
    ringkasan_s = df.get("Ringkasan", pd.Series([""] * len(df), index=df.index)).astype(str).fillna("")
    text_series = (judul_s + " " + ringkasan_s).apply(clean_text)

    # Lokasi selalu dari rule-based (lebih akurat untuk regex nama tempat)
    konteks_list, provinsi_list, kabkota_list, status_lokasi_list = [], [], [], []
    for text in text_series:
        konteks_list.append(get_context_label(text))
        lokasi = detect_location(text)
        provinsi_list.append(lokasi["Provinsi"])
        kabkota_list.append(lokasi["Kabupaten_Kota"])
        status_lokasi_list.append(lokasi["Status_Lokasi"])

    # ── LLM batch analysis ──
    llm_results = [None] * len(df)
    if use_llm:
        try:
            llm_results = analyze_with_llm_batch(df, api_key)
        except Exception:
            llm_results = [None] * len(df)

    # ── Gabungkan: LLM utama, rule-based fallback ──
    hasil = []
    metode_list = []

    for idx, (text, row_llm) in enumerate(zip(text_series, llm_results)):
        row = df.iloc[idx].to_dict()

        if row_llm is not None:
            # LLM berhasil — tambahkan time boost jika NASIONAL
            if row_llm.get("Kategori_Berita") == "NASIONAL":
                row_llm["Score"] = min(10, int(row_llm["Score"]) + get_time_boost(row))
            hasil.append(row_llm)
            metode_list.append("LLM")
        else:
            # Fallback ke rule-based
            rb = analyze_rule_based(text, row=row)
            hasil.append(rb)
            metode_list.append("Rule-based")

    hasil_df = pd.DataFrame(hasil)

    df["Konteks_Berita"]    = konteks_list
    df["Kategori_Berita"]   = hasil_df["Kategori_Berita"]
    df["Provinsi"]          = provinsi_list
    df["Kabupaten_Kota"]    = kabkota_list
    df["Status_Lokasi"]     = status_lokasi_list
    df["Topik_Utama"]       = hasil_df["Topik_Utama"]
    df["Score"]             = pd.to_numeric(hasil_df["Score"], errors="coerce").fillna(0).astype(int)
    df["Dampak_Program"]    = hasil_df["Dampak_Program"]
    df["Dampak_Kepesertaan"]= hasil_df["Dampak_Kepesertaan"]
    df["Potensi_Klaim"]     = hasil_df["Potensi_Klaim"]
    df["Alasan_Prioritas"]  = hasil_df["Alasan_Prioritas"]
    df["Metode_Analisis"]   = metode_list

    df["Prioritas"] = df.apply(
        lambda r: classify_priority(int(r["Score"]), str(r["Kategori_Berita"]), str(r["Topik_Utama"])),
        axis=1
    )

    # Buang berita global tidak relevan
    df = df[
        ~(
            (df["Kategori_Berita"].astype(str) == "GLOBAL") &
            (df["Konteks_Berita"].astype(str) == "LUAR NEGERI / TIDAK RELEVAN") &
            (df["Score"] <= 0)
        )
    ].copy()

    df = ensure_columns(df)

    # Sort: prioritas → score → waktu publish
    priority_order = {"PRIORITAS TINGGI": 1, "PRIORITAS SEDANG": 2, "PRIORITAS RENDAH": 3}
    df["__prio_order"] = df["Prioritas"].map(priority_order).fillna(99)

    if "Waktu_Publish_WIB" in df.columns:
        df["__publish_dt"] = pd.to_datetime(df["Waktu_Publish_WIB"], errors="coerce")
        df = df.sort_values(["__prio_order", "Score", "__publish_dt"], ascending=[True, False, False])
        df = df.drop(columns=["__publish_dt"], errors="ignore")
    else:
        df = df.sort_values(["__prio_order", "Score"], ascending=[True, False])

    df = df.drop(columns=["__prio_order"], errors="ignore")

    clear_and_write(sheet_key, "ANALYZED", df)
    return df


if __name__ == "__main__":
    run_priority()
