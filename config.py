# =========================================
# CONFIG SIAGA JAMSOS
# =========================================

# ==============================
# GOOGLE SHEETS
# ==============================
RAW_SHEET_NAME = "RAW"
FILTERED_SHEET_NAME = "FILTERED"

# ==============================
# WILAYAH WAKTU
# ==============================
TIMEZONE = "Asia/Jakarta"

# ==============================
# OPSI PRIORITAS
# ==============================
PRIORITY_OPTIONS = [
    "SEMUA",
    "PRIORITAS TINGGI",
    "PRIORITAS SEDANG",
    "PRIORITAS RENDAH",
]

PRIORITY_ORDER = {
    "PRIORITAS TINGGI": 1,
    "PRIORITAS SEDANG": 2,
    "PRIORITAS RENDAH": 3,
}

# ==============================
# KEYWORD KETENAGAKERJAAN
# ==============================
KEYWORDS_KETENAGAKERJAAN = [
    "phk",
    "pemutusan hubungan kerja",
    "dirumahkan",
    "buruh",
    "pekerja",
    "tenaga kerja",
    "ketenagakerjaan",
    "hubungan industrial",
    "perselisihan industrial",
    "mogok kerja",
    "demo buruh",
    "unjuk rasa buruh",
    "upah",
    "gaji",
    "upah minimum",
    "ump",
    "umk",
    "thr",
    "tunjangan hari raya",
    "pesangon",
    "pabrik tutup",
    "bangkrut",
    "pailit",
    "kecelakaan kerja",
    "buruh tewas",
    "pekerja tewas",
]

# ==============================
# KEYWORD JAMINAN SOSIAL
# ==============================
KEYWORDS_JAMSOS = [
    "bpjs ketenagakerjaan",
    "bpjamsostek",
    "jamsostek",
    "kepesertaan bpjs",
    "peserta bpjs",
    "jht",
    "jaminan hari tua",
    "klaim jht",
    "pencairan jht",
    "jkk",
    "jaminan kecelakaan kerja",
    "jkm",
    "jaminan kematian",
    "jkp",
    "jaminan kehilangan pekerjaan",
    "jp",
    "jaminan pensiun",
    "iuran bpjs",
    "tunggakan iuran",
    "klaim bpjs",
    "kendala klaim",
    "verifikasi klaim",
    "santunan kematian",
    "santunan jkk",
]

# ==============================
# DETEKSI TOPIK
# ==============================
TOPIC_RULES = {
    "PHK": [
        r"\bphk\b",
        r"pemutusan hubungan kerja",
        r"\bdirumahkan\b",
        r"gelombang phk",
        r"phk massal",
        r"pengurangan karyawan",
        r"efisiensi tenaga kerja",
    ],
    "THR / Kesejahteraan Pekerja": [
        r"\bthr\b",
        r"tunjangan hari raya",
        r"pengaduan thr",
        r"posko thr",
        r"thr tidak dibayar",
        r"thr terlambat",
        r"thr dicicil",
        r"thr dipotong",
    ],
    "Upah / Gaji": [
        r"\bupah\b",
        r"\bgaji\b",
        r"tunggakan upah",
        r"gaji tidak dibayar",
        r"ump",
        r"umk",
        r"upah minimum",
    ],
    "Aksi / Demo Buruh": [
        r"\bdemo\b",
        r"unjuk rasa",
        r"aksi buruh",
        r"mogok",
        r"mogok kerja",
    ],
    "Konflik Hubungan Industrial": [
        r"perselisihan",
        r"konflik buruh",
        r"sengketa",
        r"tripartit",
        r"mediasi hubungan industrial",
    ],
    "Pabrik Tutup / Pailit": [
        r"pabrik tutup",
        r"tutup permanen",
        r"\bpailit\b",
        r"\bbangkrut\b",
        r"likuidasi",
        r"stop operasional",
    ],
    "Kepesertaan BPJS": [
        r"bpjs ketenagakerjaan",
        r"bpjamsostek",
        r"jamsostek",
        r"kepesertaan bpjs",
        r"terdaftar bpjs",
        r"peserta bpjs",
    ],
    "Klaim JHT": [
        r"\bjht\b",
        r"jaminan hari tua",
        r"klaim jht",
        r"pencairan jht",
        r"saldo jht",
    ],
    "Manfaat JKP": [
        r"\bjkp\b",
        r"jaminan kehilangan pekerjaan",
        r"manfaat jkp",
        r"klaim jkp",
    ],
    "Jaminan Pensiun (JP)": [
        r"\bjp\b",
        r"jaminan pensiun",
        r"manfaat pensiun",
        r"iuran pensiun",
        r"usia pensiun",
    ],
    "Kecelakaan Kerja (JKK)": [
        r"\bjkk\b",
        r"jaminan kecelakaan kerja",
        r"kecelakaan kerja",
        r"santunan jkk",
        r"ledakan pabrik",
        r"buruh tewas",
        r"pekerja tewas",
    ],
    "Santunan Kematian (JKM)": [
        r"\bjkm\b",
        r"jaminan kematian",
        r"santunan kematian",
        r"ahli waris",
        r"meninggal dunia",
    ],
    "Tunggakan Iuran": [
        r"tunggakan iuran",
        r"menunggak iuran",
        r"telat bayar iuran",
        r"denda bpjs",
    ],
    "Pengawasan Kepatuhan": [
        r"pengawasan",
        r"pemeriksaan",
        r"sanksi perusahaan",
        r"kepatuhan perusahaan",
        r"tidak patuh",
    ],
    "Kendala Klaim BPJS": [
        r"klaim ditolak",
        r"kendala klaim",
        r"klaim lama",
        r"antrian klaim",
        r"verifikasi klaim",
    ],
    "Pekerja Migran Indonesia (PMI)": [
        r"\bpmi\b",
        r"pekerja migran",
        r"tki",
        r"buruh migran",
    ],
    "Jasa Konstruksi": [
        r"konstruksi",
        r"proyek",
        r"pembangunan",
        r"jasa konstruksi",
    ],
}

TOPIC_FALLBACK_BPJS = r"bpjs|bpjamsostek|jamsostek|klaim|iuran"
TOPIC_FALLBACK_KETENAGAKERJAAN = r"buruh|pekerja|ketenagakerjaan|tenaga kerja"
TOPIC_DEFAULT = "Kebijakan Ketenagakerjaan"

# ==============================
# KEYWORD RISIKO / PRIORITAS
# ==============================
HIGH_PRIORITY_PATTERNS = [
    r"phk massal",
    r"gelombang phk",
    r"kecelakaan kerja",
    r"buruh tewas",
    r"pekerja tewas",
    r"ledakan pabrik",
    r"pabrik tutup",
    r"tutup permanen",
    r"\bpailit\b",
    r"\bbangkrut\b",
    r"upah tidak dibayar",
    r"gaji tidak dibayar",
    r"pesangon tidak dibayar",
    r"klaim ditolak",
]

MEDIUM_PRIORITY_PATTERNS = [
    r"\bphk\b",
    r"dirumahkan",
    r"mogok kerja",
    r"demo buruh",
    r"unjuk rasa",
    r"tunggakan upah",
    r"telat bayar iuran",
    r"kendala klaim",
    r"antrian klaim",
    r"perselisihan",
    r"konflik buruh",
]

LOW_PRIORITY_PATTERNS = [
    r"sosialisasi",
    r"imbauan",
    r"edukasi",
    r"forum",
    r"seminar",
    r"pelatihan",
    r"kunjungan kerja",
]

# ==============================
# BOBOT SKOR
# ==============================
SCORE_HIGH_PRIORITY = 3
SCORE_MEDIUM_PRIORITY = 2
SCORE_LOW_PRIORITY = 1

PRIORITY_THRESHOLD_HIGH = 6
PRIORITY_THRESHOLD_MEDIUM = 3

# ==============================
# LABEL DAMPAK PROGRAM
# ==============================
PROGRAM_IMPACT_RULES = {
    "PHK": "PU",
    "THR / Kesejahteraan Pekerja": "PU",
    "Upah / Gaji": "PU",
    "Aksi / Demo Buruh": "PU",
    "Konflik Hubungan Industrial": "PU",
    "Pabrik Tutup / Pailit": "PU",
    "Kepesertaan BPJS": "PU, BPU, PMI, Jasa Konstruksi",
    "Klaim JHT": "JHT",
    "Manfaat JKP": "JKP",
    "Jaminan Pensiun (JP)": "JP",
    "Kecelakaan Kerja (JKK)": "JKK",
    "Santunan Kematian (JKM)": "JKM",
    "Tunggakan Iuran": "Kepatuhan Iuran",
    "Pengawasan Kepatuhan": "Kepatuhan Perusahaan",
    "Kendala Klaim BPJS": "Layanan Klaim",
    "Pekerja Migran Indonesia (PMI)": "PMI",
    "Jasa Konstruksi": "Jasa Konstruksi",
}

CLAIM_IMPACT_RULES = {
    "PHK": "JKP, JHT",
    "Klaim JHT": "JHT",
    "Manfaat JKP": "JKP",
    "Jaminan Pensiun (JP)": "JP",
    "Kecelakaan Kerja (JKK)": "JKK",
    "Santunan Kematian (JKM)": "JKM",
    "Kendala Klaim BPJS": "JHT/JKP/JKK/JKM",
}

# ==============================
# INDEKS ESKALASI
# ==============================
ESCALATION_WINDOW_1_HOURS = 24
ESCALATION_WINDOW_2_HOURS = 48
ESCALATION_MEDIA_WEIGHT = 3
ESCALATION_NEWS_WEIGHT = 1

# ==============================
# DASHBOARD
# ==============================
ITEMS_PER_PAGE = 10
TOP_NEWS_LIMIT = 5