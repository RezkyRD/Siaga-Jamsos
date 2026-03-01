import pandas as pd

def run_priority():

    print("Update prioritas dimulai...")

# ==============================
# LOAD DATA
# ==============================
    df = pd.read_csv("filtered_news.csv")

# ==============================
# KEYWORD SCORE MAP
# ==============================
    score_map = {
        # PRIORITAS TINGGI
        "phk massal": 5,
        "gelombang phk": 5,
        "ribuan buruh": 5,
        "pabrik tutup": 5,
        "bangkrut": 5,
        "kerusuhan": 5,
        "bentrok": 4,
        "ricuh": 4,
        "blokade": 4,
        "aksi besar": 4,
        "ancam tutup": 4,

        # PRIORITAS SEDANG
        "mogok kerja": 3,
        "mogok": 3,
        "aksi buruh": 3,
        "unjuk rasa": 3,
        "demo": 3,
        "tuntutan upah": 3,
        "perselisihan": 2,
        "kontrak kerja": 2,
        "serikat pekerja": 2,
        "upah minimum": 2,
        "upah tidak dibayar": 2,
        "penutupan sementara": 2,

        # PRIORITAS RENDAH
        "phk": 1,
        "upah": 1,
        "tenaga kerja": 1,
        "ketenagakerjaan": 1
    }

# ==============================
# FUNCTION HITUNG SKOR
# ==============================
    def calculate_score(judul):
        judul = str(judul).lower()
        score = 0

        for kata, nilai in score_map.items():
            if kata in judul:
                score += nilai

        return score


# ==============================
# FUNCTION KLASIFIKASI
# ==============================
    def classify_priority(score):
        if score >= 5:
            return "PRIORITAS TINGGI"
        elif score >= 3:
            return "PRIORITAS SEDANG"
        else:
            return "PRIORITAS RENDAH"


# ==============================
# APPLY ANALISIS
# ==============================
    df["Score"] = df["Judul"].apply(calculate_score)
    df["Prioritas"] = df["Score"].apply(classify_priority)

# ==============================
# SAVE UPDATE
# ==============================
    df.to_csv("filtered_news.csv", index=False)

    print("Prioritas berhasil diperbarui.")


# Supaya tetap bisa dijalankan manual
if __name__ == "__main__":
    run_priority()