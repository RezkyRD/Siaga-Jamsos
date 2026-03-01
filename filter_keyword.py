import pandas as pd

def run_filter():

    keywords = ["PHK", "demo buruh", "BPJS", "JKP", "mogok","konflik buruh", "JHT", "JKK", "JKM", "JP", "buruh", "UMR", "Ketenagakerjaan"]

    df = pd.read_csv("raw_news.csv")

    def contains_keyword(text):
        if pd.isna(text):
            return False
        return any(k.lower() in text.lower() for k in keywords)

    df_filtered = df[df["Judul"].apply(contains_keyword)]

    df_filtered.to_csv("filtered_news.csv", index=False)

    print("Total RAW:", len(df))
    print("Total Lolos Keyword:", len(df_filtered))

if __name__ == "__main__":
    run_filter()