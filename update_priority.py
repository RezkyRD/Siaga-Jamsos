import re
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
    "netflix", "warner bros", "ubisoft", "sony", "samsung", "epic games"
]

GLOBAL_STRICT = [
    "facebook", "meta", "instagram", "amazon", "google", "tesla",
    "microsoft", "apple", "netflix", "nvidia", "warner bros",
    "ubisoft", "epic games", "zuckerberg",
    "startup global", "perusahaan global", "raksasa teknologi",
    "raksasa e-commerce", "big tech"
]


# =====================================
# HELPERS
# =====================================

def clean_text(text: str) -> str:
    text = str(text or "").lower()
    text = re.sub(r"\s+", " ", text).strip()
    return text


def unique_join(items: list[str]) -> str:
    out = []
    seen = set()
    for item in items:
        item = str(item).strip()
        if item and item not in seen:
            seen.add(item)
            out.append(item)
    return ", ".join(out)


def contains_any(text: str, patterns: list[str]) -> bool:
    return any(re.search(p, text) for p in patterns)


def classify_priority(score: int, context_label: str, topic: str) -> str:
    if context_label != "INDONESIA":
        return "PRIORITAS RENDAH"

    if topic == "Layanan / Edukasi Klaim":
        if score >= 6:
            return "PRIORITAS SEDANG"
        return "PRIORITAS RENDAH"

    if score >= 8:
        return "PRIORITAS TINGGI"
    if score >= 4:
        return "PRIORITAS SEDANG"
    return "PRIORITAS RENDAH"


# =====================================
# RELEVANSI INDONESIA
# =====================================

def is_indonesia_related(text: str) -> bool:
    text = clean_text(text)

    # PMI / WNI tetap relevan
    if any(k in text for k in [
        "pekerja migran indonesia",
        "buruh migran indonesia",
        "pmi indonesia",
        "tki indonesia",
        "wni",
        "warga negara indonesia"
    ]):
        return True

    # kalau ada perusahaan global, wajib ada konteks Indonesia yang kuat
    if any(g in text for g in GLOBAL_COMPANY):
        strong_id_context = [
            "di indonesia",
            "indonesia",
            "pekerja indonesia",
            "buruh indonesia",
            "karyawan di indonesia",
            "operasi di indonesia",
            "anak usaha di indonesia",
            "anak usaha indonesia",
            "pabrik di indonesia",
            "kantor di indonesia",
            "kemnaker",
            "disnaker",
            "bpjs ketenagakerjaan",
            "bpjamsostek",
            "phk di indonesia",
            "buruh indonesia terdampak",
            "pekerja indonesia terdampak"
        ]
        return any(k in text for k in strong_id_context)

    return any(k in text for k in INDONESIA_CONTEXT)


def get_context_label(text: str) -> str:
    if is_indonesia_related(text):
        return "INDONESIA"
    if re.search(r"\bpmi\b|pekerja migran|\btki\b", text):
        return "PMI"
    return "LUAR NEGERI / TIDAK RELEVAN"


# =====================================
# EDUKASI LAYANAN
# =====================================

def is_service_education(text: str) -> bool:
    return contains_any(text, [
        r"cara klaim",
        r"syarat klaim",
        r"panduan",
        r"tutorial",
        r"begini cara",
        r"cara mencairkan",
        r"cara cairkan",
        r"bisa cairkan saldo",
        r"cek saldo",
        r"saldo jht",
        r"aplikasi jmo",
        r"\bjmo\b",
        r"prosedur",
        r"alur klaim",
        r"tips klaim",
        r"simak caranya",
        r"begini syarat",
        r"ini syarat",
        r"begini alurnya"
    ])


# =====================================
# IDENTIFIKASI TOPIK
# =====================================

def detect_topic(text: str) -> str:
    if is_service_education(text):
        return "Layanan / Edukasi Klaim"

    topic_rules = [
        ("PHK", [
            r"\bphk\b", r"pemutusan hubungan kerja", r"\bdirumahkan\b",
            r"phk massal", r"gelombang phk", r"efisiensi tenaga kerja",
            r"pengurangan karyawan"
        ]),
        ("THR / Kesejahteraan Pekerja", [
            r"\bthr\b", r"tunjangan hari raya", r"pengaduan thr",
            r"posko thr", r"thr.*tidak dibayar", r"thr.*terlambat",
            r"thr.*dicicil", r"thr.*dipotong"
        ]),
        ("Upah / Gaji", [
            r"\bupah\b", r"\bgaji\b", r"\bump\b", r"\bumk\b",
            r"upah minimum", r"tunggakan upah", r"gaji tidak dibayar"
        ]),
        ("Aksi / Demo Buruh", [
            r"\bdemo\b", r"unjuk rasa", r"aksi buruh", r"mogok", r"mogok kerja"
        ]),
        ("Konflik Hubungan Industrial", [
            r"perselisihan", r"sengketa", r"konflik buruh",
            r"mediasi hubungan industrial", r"tripartit"
        ]),
        ("Kecelakaan Kerja (JKK)", [
            r"kecelakaan kerja", r"\bledakan\b", r"kebakaran pabrik",
            r"tertimbun", r"pekerja jatuh", r"buruh tewas", r"pekerja tewas"
        ]),
        ("Kepesertaan BPJS", [
            r"bpjs ketenagakerjaan", r"bpjamsostek", r"jamsostek",
            r"kepesertaan bpjs", r"peserta bpjs", r"terdaftar bpjs"
        ]),
        ("Klaim JHT", [
            r"\bjht\b", r"jaminan hari tua", r"klaim jht",
            r"pencairan jht", r"saldo jht"
        ]),
        ("Manfaat JKP", [
            r"\bjkp\b", r"jaminan kehilangan pekerjaan",
            r"klaim jkp", r"manfaat jkp"
        ]),
        ("Jaminan Pensiun (JP)", [
            r"\bjp\b", r"jaminan pensiun", r"iuran pensiun", r"usia pensiun"
        ]),
        ("Santunan Kematian (JKM)", [
            r"\bjkm\b", r"jaminan kematian", r"santunan kematian",
            r"ahli waris", r"meninggal dunia"
        ]),
        ("Tunggakan Iuran", [
            r"tunggakan iuran", r"menunggak iuran",
            r"telat bayar iuran", r"denda bpjs"
        ]),
        ("Pekerja Migran Indonesia (PMI)", [
            r"\bpmi\b", r"pekerja migran", r"\btki\b", r"buruh migran"
        ]),
        ("Jasa Konstruksi", [
            r"konstruksi", r"proyek", r"pembangunan", r"jasa konstruksi"
        ]),
    ]

    for topic, patterns in topic_rules:
        if contains_any(text, patterns):
            return topic

    if re.search(r"buruh|pekerja|ketenagakerjaan|tenaga kerja", text):
        return "Isu Ketenagakerjaan Umum"

    return "Lainnya"


# =====================================
# KLASIFIKASI KEPESERTAAN
# =====================================

def detect_kepesertaan(text: str) -> list[str]:
    hasil = []

    if contains_any(text, [
        r"perusahaan", r"karyawan", r"pekerja formal", r"buruh pabrik",
        r"pegawai", r"hubungan industrial", r"phk", r"thr", r"upah", r"gaji"
    ]):
        hasil.append("PU")

    if contains_any(text, [
        r"\bbpu\b", r"bukan penerima upah", r"pekerja informal",
        r"pedagang", r"nelayan", r"petani", r"ojek", r"driver",
        r"umkm", r"wirausaha"
    ]):
        hasil.append("BPU")

    if contains_any(text, [
        r"\bpmi\b", r"pekerja migran", r"\btki\b", r"buruh migran"
    ]):
        hasil.append("PMI")

    if contains_any(text, [
        r"konstruksi", r"proyek", r"pembangunan", r"jasa konstruksi"
    ]):
        hasil.append("Jasa Konstruksi")

    return hasil


# =====================================
# ANALISIS RISIKO / PRIORITAS
# =====================================

def analyze_jamsos(text: str) -> dict:
    text = clean_text(text)

    score = 0
    program = []
    kepesertaan = detect_kepesertaan(text)
    klaim = []
    alasan = []
    topik = detect_topic(text)
    edukasi = is_service_education(text)

    # PHK
    if contains_any(text, [r"\bphk\b", r"pemutusan hubungan kerja", r"\bdirumahkan\b"]):
        if edukasi:
            score += 1
            program.extend(["JHT", "JKP"])
            kepesertaan.append("PU")
            klaim.extend(["JHT", "JKP"])
            alasan.append(
                "Berita memuat konteks PHK dalam bentuk informasi layanan atau panduan klaim, sehingga lebih bersifat edukatif daripada indikasi kejadian PHK baru."
            )
        else:
            score += 4
            program.extend(["JKP", "JHT", "JP"])
            kepesertaan.append("PU")
            klaim.extend(["JKP", "JHT"])
            alasan.append(
                "Pemberitaan mengenai PHK berpotensi meningkatkan klaim JKP serta pencairan JHT bagi pekerja terdampak."
            )

    if contains_any(text, [
        r"phk.*massal", r"massal.*phk", r"gelombang phk", r"ribuan karyawan",
        r"ratusan karyawan", r"tutup pabrik", r"pabrik tutup", r"\bpailit\b", r"\bbangkrut\b"
    ]):
        score += 4
        alasan.append(
            "Skala isu yang besar menunjukkan potensi penurunan kepesertaan aktif serta peningkatan tekanan klaim manfaat."
        )

    # JKK / kecelakaan kerja
    if contains_any(text, [
        r"kecelakaan kerja", r"\bledakan\b", r"kebakaran pabrik",
        r"tertimbun", r"pekerja jatuh", r"alat berat", r"lokasi proyek"
    ]):
        score += 4
        program.append("JKK")
        klaim.append("JKK")
        alasan.append("Peristiwa kecelakaan kerja berpotensi menimbulkan klaim JKK.")

    if contains_any(text, [
        r"meninggal dunia", r"pekerja tewas", r"buruh tewas", r"korban jiwa"
    ]):
        score += 3
        program.append("JKM")
        klaim.append("JKM")
        alasan.append("Kematian pekerja berpotensi menimbulkan klaim JKM bagi ahli waris.")

    # Demo / konflik industrial
    if contains_any(text, [r"\bdemo\b", r"unjuk rasa", r"aksi buruh", r"mogok", r"mogok kerja"]):
        score += 2
        alasan.append(
            "Aksi buruh menunjukkan potensi konflik hubungan industrial yang dapat berdampak pada stabilitas ketenagakerjaan."
        )

    if contains_any(text, [r"perselisihan", r"sengketa", r"konflik buruh", r"mediasi hubungan industrial"]):
        score += 2
        alasan.append(
            "Perselisihan hubungan industrial dapat berkembang menjadi gangguan kepatuhan perusahaan dan keberlanjutan hubungan kerja."
        )

    # THR / upah
    if contains_any(text, [r"\bthr\b", r"tunjangan hari raya"]):
        score += 1
        kepesertaan.append("PU")
        alasan.append("Isu THR menunjukkan potensi persoalan kesejahteraan pekerja dan kepatuhan perusahaan.")

    if contains_any(text, [
        r"thr.*tidak dibayar", r"tidak dibayar.*thr", r"thr.*terlambat",
        r"terlambat.*thr", r"thr.*dicicil", r"thr.*dipotong", r"pengaduan thr", r"posko thr"
    ]):
        score += 3
        alasan.append("Permasalahan pembayaran THR dapat memicu pengaduan pekerja dan perselisihan hubungan industrial.")

    if contains_any(text, [
        r"\bupah\b", r"\bgaji\b", r"\bump\b", r"\bumk\b",
        r"upah minimum", r"tunggakan upah", r"gaji tidak dibayar"
    ]):
        score += 2
        kepesertaan.append("PU")
        alasan.append("Permasalahan upah/gaji berpotensi memicu instabilitas hubungan kerja dan menurunkan kepatuhan perusahaan.")

    # Kepesertaan / kepatuhan
    if contains_any(text, [
        r"bpjs ketenagakerjaan", r"bpjamsostek", r"jamsostek",
        r"kepesertaan bpjs", r"peserta bpjs", r"terdaftar bpjs"
    ]):
        if edukasi:
            score += 1
            program.append("Kepesertaan")
            alasan.append("Pemberitaan berkaitan dengan informasi layanan dan akses manfaat BPJS Ketenagakerjaan.")
        else:
            score += 2
            program.append("Kepesertaan")
            alasan.append("Pemberitaan berkaitan langsung dengan cakupan perlindungan jaminan sosial ketenagakerjaan.")

    if contains_any(text, [
        r"tunggakan iuran", r"menunggak iuran", r"telat bayar iuran",
        r"denda bpjs", r"tidak patuh", r"sanksi perusahaan", r"pemeriksaan", r"pengawasan"
    ]):
        score += 3
        program.append("Kepesertaan")
        alasan.append("Isu kepatuhan dan tunggakan iuran berpotensi mempengaruhi kesinambungan perlindungan peserta.")

    # Manfaat spesifik
    if contains_any(text, [r"\bjht\b", r"jaminan hari tua", r"klaim jht", r"pencairan jht", r"saldo jht"]):
        if edukasi:
            score += 1
            program.append("JHT")
            klaim.append("JHT")
            alasan.append("Pemberitaan berkaitan dengan informasi layanan atau panduan akses manfaat JHT.")
        else:
            score += 2
            program.append("JHT")
            klaim.append("JHT")
            alasan.append("Isu JHT berkaitan dengan manfaat yang paling sering diakses oleh peserta saat terjadi pemutusan kerja atau kebutuhan tertentu.")

    if contains_any(text, [r"\bjkp\b", r"jaminan kehilangan pekerjaan", r"klaim jkp", r"manfaat jkp"]):
        if edukasi:
            score += 1
            program.append("JKP")
            klaim.append("JKP")
            alasan.append("Pemberitaan memuat informasi layanan atau penjelasan manfaat JKP.")
        else:
            score += 2
            program.append("JKP")
            klaim.append("JKP")
            alasan.append("Isu JKP berkaitan langsung dengan perlindungan bagi pekerja yang kehilangan pekerjaan.")

    if contains_any(text, [r"\bjp\b", r"jaminan pensiun", r"iuran pensiun", r"usia pensiun"]):
        score += 1
        program.append("JP")
        alasan.append("Isu JP dapat berdampak pada persepsi manfaat jangka panjang dan kepatuhan iuran.")

    if contains_any(text, [r"\bjkm\b", r"jaminan kematian", r"santunan kematian", r"ahli waris"]):
        score += 1
        program.append("JKM")
        klaim.append("JKM")
        alasan.append("Isu JKM berkaitan dengan santunan bagi ahli waris peserta yang meninggal dunia.")

    # PMI / konstruksi
    if contains_any(text, [r"\bpmi\b", r"pekerja migran", r"\btki\b"]):
        score += 2
        kepesertaan.append("PMI")
        program.append("Kepesertaan")
        alasan.append("Isu PMI berkaitan dengan perlindungan jaminan sosial ketenagakerjaan bagi pekerja migran Indonesia.")

    if contains_any(text, [r"konstruksi", r"proyek", r"pembangunan", r"jasa konstruksi"]):
        score += 1
        kepesertaan.append("Jasa Konstruksi")
        program.append("JKK")
        alasan.append("Sektor konstruksi memiliki risiko kecelakaan kerja tinggi sehingga relevan dengan program JKK.")

    # Penyesuaian edukasi
    if edukasi:
        score = max(score - 2, 1)

    if not alasan:
        alasan.append(
            "Berita berkaitan dengan isu ketenagakerjaan yang perlu dipantau karena berpotensi mempengaruhi perlindungan jaminan sosial tenaga kerja."
        )

    return {
        "Topik_Utama": topik,
        "Score": int(score),
        "Dampak_Program": unique_join(program),
        "Dampak_Kepesertaan": unique_join(kepesertaan),
        "Potensi_Klaim": unique_join(klaim),
        "Alasan_Prioritas": " ".join(alasan),
    }


# =====================================
# RUN PRIORITY
# =====================================

def run_priority(sheet_key=None):
    if sheet_key is None:
        sheet_key = st.secrets["SHEET_KEY"]

    df = read_sheet(sheet_key, "FILTERED")
    if df is None or df.empty:
        return df

    df = df.copy()
    df.columns = df.columns.astype(str).str.strip()

    judul = df.get("Judul", pd.Series([""] * len(df))).astype(str).fillna("")
    ringkasan = df.get("Ringkasan", pd.Series([""] * len(df))).astype(str).fillna("")
    text_series = (judul + " " + ringkasan).apply(clean_text)

    hasil = []
    konteks_list = []

    strong_id_context = [
        "di indonesia", "indonesia", "pekerja indonesia", "buruh indonesia",
        "karyawan di indonesia", "operasi di indonesia", "anak usaha di indonesia",
        "anak usaha indonesia", "pabrik di indonesia", "kantor di indonesia",
        "kemnaker", "disnaker", "bpjs ketenagakerjaan", "bpjamsostek",
        "phk di indonesia", "buruh indonesia terdampak", "pekerja indonesia terdampak"
    ]

    for text in text_series:
        # filter keras berita global
        if any(g in text for g in GLOBAL_STRICT) and not any(k in text for k in strong_id_context):
            konteks = "LUAR NEGERI / TIDAK RELEVAN"
            konteks_list.append(konteks)
            hasil.append({
                "Topik_Utama": "Tidak Relevan Indonesia",
                "Score": 0,
                "Dampak_Program": "",
                "Dampak_Kepesertaan": "",
                "Potensi_Klaim": "",
                "Alasan_Prioritas": "PHK atau isu ketenagakerjaan terjadi pada perusahaan global dan tidak berkaitan langsung dengan kondisi ketenagakerjaan di Indonesia."
            })
            continue

        konteks = get_context_label(text)
        konteks_list.append(konteks)

        if konteks != "INDONESIA":
            hasil.append({
                "Topik_Utama": "Tidak Relevan Indonesia",
                "Score": 0,
                "Dampak_Program": "",
                "Dampak_Kepesertaan": "",
                "Potensi_Klaim": "",
                "Alasan_Prioritas": "Berita ketenagakerjaan global yang tidak berkaitan langsung dengan kondisi ketenagakerjaan di Indonesia."
            })
            continue

        hasil.append(analyze_jamsos(text))

    hasil_df = pd.DataFrame(hasil)

    df["Konteks_Berita"] = konteks_list
    df["Topik_Utama"] = hasil_df["Topik_Utama"]
    df["Score"] = hasil_df["Score"]
    df["Dampak_Program"] = hasil_df["Dampak_Program"]
    df["Dampak_Kepesertaan"] = hasil_df["Dampak_Kepesertaan"]
    df["Potensi_Klaim"] = hasil_df["Potensi_Klaim"]
    df["Alasan_Prioritas"] = hasil_df["Alasan_Prioritas"]
    df["Prioritas"] = df.apply(
        lambda r: classify_priority(
            int(r["Score"]),
            str(r["Konteks_Berita"]),
            str(r["Topik_Utama"])
        ),
        axis=1
    )

    clear_and_write(sheet_key, "FILTERED", df)
    return df


if __name__ == "__main__":
    run_priority()