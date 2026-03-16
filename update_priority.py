import pandas as pd
import re
import streamlit as st

from gsheet_utils import (
    read_sheet,
    clear_and_write,
)

# =====================================
# KONTEKS INDONESIA
# =====================================

INDONESIA_CONTEXT = [
    "jakarta", "jawa", "sumatera", "kalimantan", "sulawesi", "papua", "bali",
    "kemnaker", "bpjs ketenagakerjaan", "bpjamsostek", "disnaker",
    "pekerja migran", "pmi", "tki", "buruh indonesia",
    "pekerja indonesia", "perusahaan indonesia", "pabrik di indonesia",
    "jabar", "jateng", "jatim", "bandung", "surabaya", "medan", "makassar",
    "karawang", "bekasi", "tangerang", "semarang", "batam"
]

GLOBAL_COMPANY = [
    "amazon", "google", "morgan stanley", "meta", "facebook",
    "apple", "tesla", "microsoft", "intel", "nvidia", "tiktok", "netflix"
]


def normalize_text(text):
    return str(text or "").lower().strip()


def split_keywords(keyword_text):
    if pd.isna(keyword_text) or str(keyword_text).strip() == "":
        return []
    return [k.strip().lower() for k in str(keyword_text).split(";") if k.strip()]


def safe_int(value, default=0):
    try:
        return int(float(value))
    except Exception:
        return default


def is_indonesia_related(text):
    text = normalize_text(text)

    pmi_keywords = [
        "pekerja migran indonesia",
        "pmi",
        "tki",
        "buruh indonesia",
        "pekerja indonesia"
    ]

    if any(k in text for k in pmi_keywords):
        return True

    if any(g in text for g in GLOBAL_COMPANY):
        indonesia_strong_context = [
            "di indonesia",
            "indonesia",
            "pekerja indonesia",
            "buruh indonesia",
            "pabrik di indonesia",
            "anak usaha indonesia",
            "operasi di indonesia",
            "karyawan di indonesia",
            "phk di indonesia",
            "kemnaker",
            "disnaker",
            "bpjs ketenagakerjaan",
            "bpjamsostek"
        ]

        media_only_context = [
            "cnbc indonesia",
            "cnn indonesia",
            "kompas.com",
            "detik",
            "tempo.co",
            "bisnis.com",
            "tribun",
            "kontan",
            "beritasatu"
        ]

        has_strong_id_context = any(k in text for k in indonesia_strong_context)
        has_only_media_context = any(m in text for m in media_only_context)

        if not has_strong_id_context or has_only_media_context:
            return False

    if any(k in text for k in INDONESIA_CONTEXT):
        return True

    return False


# =====================================
# ANALISIS JAMINAN SOSIAL LAMA
# =====================================

def analyze_jamsos(text):
    score = 0
    program = []
    kepesertaan = []
    klaim = []
    alasan = []

    if re.search(r"\bphk\b|\bdirumahkan\b", text):
        score += 4
        program.extend(["JKP", "JHT", "JP"])
        kepesertaan.append("PU")
        klaim.extend(["JKP", "JHT"])
        alasan.append(
            "Pemberitaan mengenai PHK berpotensi meningkatkan klaim JKP serta pencairan JHT bagi pekerja terdampak."
        )

    if re.search(r"phk.*massal|massal.*phk", text):
        score += 6
        alasan.append(
            "PHK massal berpotensi menurunkan jumlah kepesertaan pekerja penerima upah serta meningkatkan klaim JKP."
        )

    if re.search(r"kecelakaan kerja|ledakan|kebakaran pabrik|tertimbun", text):
        score += 4
        program.append("JKK")
        klaim.append("JKK")
        alasan.append(
            "Peristiwa kecelakaan kerja berpotensi menimbulkan klaim JKK."
        )

    if re.search(r"meninggal dunia|pekerja tewas|buruh tewas", text):
        score += 3
        program.append("JKM")
        klaim.append("JKM")
        alasan.append(
            "Kematian pekerja berpotensi menimbulkan klaim JKM bagi ahli waris."
        )

    if re.search(r"demo|unjuk rasa|aksi buruh|mogok", text):
        score += 3
        alasan.append(
            "Aksi buruh menunjukkan potensi konflik hubungan industrial yang dapat berdampak pada stabilitas ketenagakerjaan."
        )

    if re.search(r"\bthr\b|tunjangan hari raya", text):
        score += 2
        kepesertaan.append("PU")
        alasan.append(
            "Isu pembayaran THR menunjukkan potensi permasalahan hubungan industrial yang dapat mempengaruhi stabilitas pekerja penerima upah."
        )

    if re.search(r"thr.*tidak dibayar|tidak dibayar.*thr|thr.*terlambat|terlambat.*thr|thr.*dicicil|thr.*dipotong|pengaduan thr|posko thr", text):
        score += 3
        alasan.append(
            "Permasalahan pembayaran THR dapat memicu pengaduan pekerja, perselisihan hubungan industrial, dan berpotensi berdampak pada kepatuhan perusahaan."
        )

    if re.search(r"pmi|pekerja migran", text):
        kepesertaan.append("PMI")
        alasan.append(
            "Isu pekerja migran dapat mempengaruhi kepesertaan BPJS Ketenagakerjaan bagi PMI."
        )

    if re.search(r"konstruksi|proyek|pembangunan", text):
        kepesertaan.append("Jasa Konstruksi")
        program.append("JKK")
        alasan.append(
            "Sektor konstruksi memiliki risiko kecelakaan kerja tinggi sehingga berkaitan dengan program JKK."
        )

    if not alasan:
        alasan.append(
            "Berita berkaitan dengan isu ketenagakerjaan yang berpotensi mempengaruhi kepesertaan BPJS Ketenagakerjaan."
        )

    program = list(set(program))
    kepesertaan = list(set(kepesertaan))
    klaim = list(set(klaim))

    return (
        score,
        ", ".join(program),
        ", ".join(kepesertaan),
        ", ".join(klaim),
        " ".join(alasan)
    )


# =====================================
# MASTER ISU & REGULASI
# =====================================

def match_kategori_isu(text, master_kategori):
    best_match = None
    best_score = -1

    for _, row in master_kategori.iterrows():
        kata_utama = normalize_text(row.get("kata_kunci_utama", ""))
        kata_tambahan = split_keywords(row.get("kata_kunci_tambahan", ""))
        score = 0

        if kata_utama and kata_utama in text:
            score += 3

        for kata in kata_tambahan:
            if kata and kata in text:
                score += 1

        if score > best_score and score > 0:
            best_score = score
            best_match = row.to_dict()

    return best_match


def get_regulasi_by_kode_isu(kode_isu, master_regulasi):
    if not kode_isu:
        return None

    df = master_regulasi.copy()
    if df.empty:
        return None

    df["kode_isu"] = df["kode_isu"].astype(str).str.strip()
    df["status_regulasi"] = df["status_regulasi"].astype(str).str.strip().str.lower()

    kandidat = df[
        (df["kode_isu"] == str(kode_isu).strip()) &
        (df["status_regulasi"].isin(["aktif", "aktif-diubah"]))
    ]

    if kandidat.empty:
        return None

    return kandidat.iloc[0].to_dict()


def build_analisis_regulatif(kode_isu, topik_norma, program_terdampak):
    templates = {
        "PHK": (
            "Isu ini berkaitan langsung dengan pemutusan hubungan kerja dan berpotensi "
            "berdampak pada akses manfaat JKP serta kesinambungan kepesertaan jaminan sosial ketenagakerjaan."
        ),
        "JKK": (
            "Isu ini berkaitan langsung dengan perlindungan risiko kerja dan relevan "
            "ditelaah dalam kerangka penyelenggaraan program JKK serta manfaat turunan akibat kecelakaan kerja."
        ),
        "PAK": (
            "Isu ini relevan ditelaah dalam kerangka risiko kerja yang berpotensi "
            "menimbulkan hak atas perlindungan JKK, dengan kebutuhan verifikasi lanjutan."
        ),
        "JKM": (
            "Isu ini berkaitan dengan manfaat JKM dan relevan untuk ditelaah dari sisi "
            "hak ahli waris serta perlindungan dasar bagi peserta yang meninggal dunia."
        ),
        "JHT": (
            "Isu ini berkaitan dengan hak manfaat JHT dan perlu dibaca dalam kerangka "
            "ketentuan aktif mengenai syarat dan tata cara pembayaran manfaat hari tua."
        ),
        "JP": (
            "Isu ini berkaitan dengan manfaat jaminan pensiun dan relevan untuk ditelaah "
            "dari sisi keberlanjutan perlindungan peserta pada masa pensiun."
        ),
        "KEP": (
            "Isu ini berpotensi berkaitan dengan kepatuhan pendaftaran pekerja dalam "
            "program jaminan sosial ketenagakerjaan dan dapat berdampak pada perlindungan manfaat peserta."
        ),
        "BPU": (
            "Isu ini relevan ditelaah dalam kerangka perluasan cakupan kepesertaan "
            "pekerja bukan penerima upah serta perlindungan bagi pekerja informal dan kelompok rentan."
        ),
        "UPAH": (
            "Isu ini dapat memengaruhi kesinambungan kepesertaan dan kepatuhan iuran, "
            "sehingga relevan ditelaah dalam hubungannya dengan perlindungan jaminan sosial ketenagakerjaan."
        ),
        "HI": (
            "Isu ini relevan ditelaah dalam kerangka hubungan industrial, terutama jika "
            "berujung pada PHK, penurunan perlindungan, atau terganggunya akses pekerja terhadap program jaminan sosial ketenagakerjaan."
        ),
    }

    if kode_isu in templates:
        return templates[kode_isu]

    detail = []
    if topik_norma:
        detail.append(f"topik norma: {topik_norma}")
    if program_terdampak:
        detail.append(f"program terdampak: {program_terdampak}")

    if detail:
        return "Isu ini berpotensi berkaitan dengan ketentuan aktif yang relevan, " + ", ".join(detail) + "."

    return "Isu ini berpotensi berkaitan dengan ketentuan aktif yang relevan."


# =====================================
# SKOR TAMBAHAN
# =====================================

def extra_score_from_text(text):
    score = 0

    kata_massal = ["massal", "ribuan", "gelombang", "nasional", "serentak"]
    kata_fatal = ["tewas", "meninggal", "fatal", "ledakan", "luka berat"]
    kata_rentan = ["pekerja rentan", "informal", "buruh harian", "ojek online", "nelayan", "petani"]
    kata_besar = ["perusahaan besar", "pabrik besar", "industri besar", "sektor strategis"]

    if any(k in text for k in kata_massal):
        score += 2
    if any(k in text for k in kata_fatal):
        score += 2
    if any(k in text for k in kata_besar):
        score += 1
    if any(k in text for k in kata_rentan):
        score += 1

    return score


def classify(score):
    if score >= 8:
        return "PRIORITAS TINGGI"
    elif score >= 5:
        return "PRIORITAS SEDANG"
    else:
        return "PRIORITAS RENDAH"


# =====================================
# RUN PRIORITY
# =====================================

def run_priority(sheet_key=None):
    if sheet_key is None:
        sheet_key = st.secrets["SHEET_KEY"]

    df = read_sheet(sheet_key, "FILTERED")
    master_kategori = read_sheet(sheet_key, "MASTER_KATEGORI_ISU")
    master_regulasi = read_sheet(sheet_key, "MASTER_REGULASI")

    if df is None or df.empty:
        return

    hasil = []

    for _, row in df.iterrows():
        judul = str(row.get("Judul", "") or "")
        ringkasan = str(row.get("Ringkasan", "") or "")
        media = str(row.get("Media", "") or "")
        url = str(row.get("Link", "") or row.get("URL", "") or "")
        tanggal = row.get("Tanggal", "")
        tanggal_ambil = row.get("Tanggal_Ambil", "")

        text = normalize_text(judul + " " + ringkasan)

        # Filter Indonesia
        if not is_indonesia_related(text):
            hasil.append({
                **row.to_dict(),
                "Kode_Isu": "",
                "Kategori_Isu": "Tidak Relevan Indonesia",
                "Subkategori_Isu": "",
                "Score": 0,
                "Dampak_Program": "",
                "Dampak_Kepesertaan": "",
                "Potensi_Klaim": "",
                "Alasan_Prioritas": "Berita ketenagakerjaan global yang tidak berkaitan langsung dengan kondisi ketenagakerjaan di Indonesia.",
                "Regulasi_Induk": "",
                "Regulasi_Teknis": "",
                "Status_Regulasi": "",
                "Topik_Norma": "",
                "Rujukan_Tampilan": "",
                "Catatan_Update": "",
                "Analisis_Regulatif": "",
                "Skor_Hukum": 0,
                "Skor_Tambahan": 0,
                "Skor_Akhir": 0,
                "Prioritas": "PRIORITAS RENDAH"
            })
            continue

        # Analisis lama
        score_lama, dampak_program, dampak_kepesertaan, potensi_klaim, alasan_prioritas = analyze_jamsos(text)

        # Mapping kategori isu
        kategori_match = match_kategori_isu(text, master_kategori) if master_kategori is not None and not master_kategori.empty else None

        kode_isu = ""
        kategori_isu = "Tidak Terpetakan"
        subkategori_isu = ""
        program_master = ""
        skor_master = 0

        if kategori_match:
            kode_isu = str(kategori_match.get("kode_isu", "")).strip()
            kategori_isu = kategori_match.get("kategori_isu", "")
            subkategori_isu = kategori_match.get("subkategori_isu", "")
            program_master = kategori_match.get("program_terdampak", "")
            skor_master = safe_int(kategori_match.get("bobot_awal", 0), 0)

        # Mapping regulasi
        regulasi_match = get_regulasi_by_kode_isu(kode_isu, master_regulasi)

        regulasi_induk = ""
        regulasi_teknis = ""
        status_regulasi = ""
        topik_norma = ""
        rujukan_tampilan = ""
        catatan_update = ""
        skor_hukum = 0

        if regulasi_match:
            regulasi_induk = regulasi_match.get("regulasi_induk", "")
            regulasi_teknis = regulasi_match.get("regulasi_teknis", "")
            status_regulasi = regulasi_match.get("status_regulasi", "")
            topik_norma = regulasi_match.get("topik_norma", "")
            rujukan_tampilan = regulasi_match.get("rujukan_tampilan", "")
            catatan_update = regulasi_match.get("catatan_update", "")
            skor_hukum = safe_int(regulasi_match.get("bobot_hukum", 0), 0)

        skor_tambahan = extra_score_from_text(text)

        # pakai skor tertinggi antara logika lama dan master isu
        skor_isu_final = max(score_lama, skor_master)

        skor_akhir = skor_isu_final + skor_hukum + skor_tambahan
        prioritas = classify(skor_akhir)

        analisis_regulatif = build_analisis_regulatif(
            kode_isu=kode_isu,
            topik_norma=topik_norma,
            program_terdampak=program_master or dampak_program
        )

        hasil.append({
            **row.to_dict(),
            "Kode_Isu": kode_isu,
            "Kategori_Isu": kategori_isu,
            "Subkategori_Isu": subkategori_isu,
            "Score": skor_isu_final,
            "Dampak_Program": dampak_program if dampak_program else program_master,
            "Dampak_Kepesertaan": dampak_kepesertaan,
            "Potensi_Klaim": potensi_klaim,
            "Alasan_Prioritas": alasan_prioritas,
            "Regulasi_Induk": regulasi_induk,
            "Regulasi_Teknis": regulasi_teknis,
            "Status_Regulasi": status_regulasi,
            "Topik_Norma": topik_norma,
            "Rujukan_Tampilan": rujukan_tampilan,
            "Catatan_Update": catatan_update,
            "Analisis_Regulatif": analisis_regulatif,
            "Skor_Hukum": skor_hukum,
            "Skor_Tambahan": skor_tambahan,
            "Skor_Akhir": skor_akhir,
            "Prioritas": prioritas
        })

    hasil_df = pd.DataFrame(hasil)

    clear_and_write(sheet_key, "HASIL_ANALISIS", hasil_df)

    return hasil_df


if __name__ == "__main__":
    run_priority()