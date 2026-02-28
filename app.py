import streamlit as st
import pandas as pd

st.title("Dashboard Early Warning System")

df_raw = pd.read_csv("raw_news.csv")
df_filtered = pd.read_csv("filtered_news.csv")
df_priority = pd.read_csv("prioritized_news.csv")

st.metric("Total Berita Raw", len(df_raw))
st.metric("Lolos Keyword", len(df_filtered))

tinggi = len(df_priority[df_priority["prioritas"] == "PRIORITAS TINGGI"])
st.metric("Prioritas Tinggi", tinggi)

st.bar_chart(df_priority["prioritas"].value_counts())

st.dataframe(df_priority)