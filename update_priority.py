import pandas as pd
import re

def run_priority():

    print("Update prioritas dimulai...")

    df = pd.read_csv("filtered_news.csv")

    # ==============================
    # KEYWORD SCORE MAP (regex lebih fleksibel)
    # ==============================
    score_map = [
        # PRIORITAS TINGGI
        (r"phk.*massal|massal.*phk", 5),
        (r"gelombang phk|phk gelombang", 5),
        (r"ribuan (buruh|pekerja)", 5),
        (r"pabrik tutup|tutup permanen|bangkrut", 5),
        (r"kerusuhan|bentrok|ricuh", 4),
        (r"blokade|aksi besar|ancam tutup", 4),
        (r"dirumahkan|layoff", 4),

        # PRIORITAS SEDANG
        (r"mogok kerja|mogok", 3),
        (r"aksi buruh|unjuk rasa|demo", 3),
        (r"tuntutan upah", 3),
        (r"perselisihan|konflik buruh", 2),
        (r"upah tidak dibayar", 2),
        (r"serikat pekerja", 2),
        (r"penutupan sementara", 2),

        # PRIORITAS RENDAH
        (r"\bphk\b", 1),
        (r"upah|tenaga kerja|ketenagakerjaan", 1),
    ]

    # ==============================
    # FUNCTION HITUNG SKOR
    # ==============================
    def calculate_score(text):

        text = str(text).lower()
        score = 0

        for pattern, nilai in score_map:
            if re.search(pattern, text):
                score += nilai

        return score

    # ==============================
    # GABUNGKAN JUDUL + RINGKASAN JIKA ADA
    # ==============================
    text_series = df["Judul"].fillna("")

    if "Ringkasan" in df.columns:
        text_series = text_series + " " + df["Ringkasan"].fillna("")

    # ==============================
    # APPLY ANALISIS
    # ==============================
    df["Score"] = text_series.apply(calculate_score)

    def classify_priority(score):
        if score >= 6:
            return "PRIORITAS TINGGI"
        elif score >= 3:
            return "PRIORITAS SEDANG"
        else:
            return "PRIORITAS RENDAH"

    df["Prioritas"] = df["Score"].apply(classify_priority)

    # ==============================
    # STATUS NASIONAL (EWS)
    # ==============================
    tinggi = (df["Prioritas"] == "PRIORITAS TINGGI").sum()

    if tinggi >= 5:
        status = "MERAH"
    elif tinggi >= 1:
        status = "KUNING"
    else:
        status = "HIJAU"

    df["Status_EWS"] = status

    # ==============================
    # SAVE UPDATE
    # ==============================
    df.to_csv("filtered_news.csv", index=False)

    print("Prioritas berhasil diperbarui.")
    print("Status nasional:", status)


if __name__ == "__main__":
    run_priority()