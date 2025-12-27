import streamlit as st
import pandas as pd
import json
from datetime import datetime
from transformers import pipeline
import torch

# 1. POPRAVEK: Onemogočimo gradiente za varčevanje s spominom
torch.set_grad_enabled(False)

st.set_page_config(layout="wide")

# --- Funkcija za nalaganje podatkov ---
@st.cache_data
def load_data():
    data = {}
    try:
        with open('data_products.json', 'r', encoding='utf-8') as f:
            data['products'] = pd.DataFrame(json.load(f))
    except FileNotFoundError:
        data['products'] = pd.DataFrame()

    try:
        with open('data_testimonials.json', 'r', encoding='utf-8') as f:
            data['testimonials'] = pd.DataFrame(json.load(f))
    except FileNotFoundError:
        data['testimonials'] = pd.DataFrame()

    try:
        with open('data_reviews.json', 'r', encoding='utf-8') as f:
            df_reviews = pd.DataFrame(json.load(f))
            df_reviews['date'] = pd.to_datetime(df_reviews['date'])
            data['reviews'] = df_reviews
    except FileNotFoundError:
        data['reviews'] = pd.DataFrame()
    return data

# 2. POPRAVEK: Pravilno nalaganje modela s predpomnilnikom
@st.cache_resource
def load_sentiment_model():
    # Model naložimo posebej, da lahko uporabimo low_cpu_mem_usage brez napak v pipeline
    model_name = "prajjwal1/bert-tiny"
    return pipeline(
        "sentiment-analysis", 
        model=model_name, 
        device=-1  # Prisili uporabo CPU
    )

# Nalaganje podatkov in modela
data = load_data()
products_df = data.get('products')
testimonials_df = data.get('testimonials')
reviews_df = data.get('reviews')
sentiment_pipeline = load_sentiment_model()

# --- Sidebar Navigacija ---
st.sidebar.title("Navigacija")
page = st.sidebar.radio("Izberi stran:", ["Izdelki", "Pričevanja", "Ocene"])

# --- Prikaz vsebine ---
if page == "Izdelki":
    st.header("Prikaz izdelkov")
    if not products_df.empty:
        st.dataframe(products_df)
    else:
        st.info("Ni podatkov o izdelkih.")

elif page == "Pričevanja":
    st.header("Prikaz pričevanj")
    if not testimonials_df.empty:
        st.dataframe(testimonials_df)
    else:
        st.info("Ni podatkov o pričevanjih.")

elif page == "Ocene":
    st.header("Prikaz ocen (2023)")

    if not reviews_df.empty:
        reviews_2023 = reviews_df[reviews_df['date'].dt.year == 2023]

        if not reviews_2023.empty:
            months_2023 = sorted(list(reviews_2023['date'].dt.to_period('M').unique()))
            month_labels = [m.strftime("%b %Y") for m in months_2023]

            if month_labels:
                selected_month_label = st.select_slider(
                    "Izberi mesec:",
                    options=month_labels,
                    value=month_labels[0]
                )

                selected_month_period = pd.Period(selected_month_label, freq='M')
                filtered_reviews = reviews_2023[reviews_2023['date'].dt.to_period('M') == selected_month_period].copy()

                if not filtered_reviews.empty:
                    st.subheader(f"Ocene za {selected_month_label}")
                    
                    if 'text' in filtered_reviews.columns:
                        review_texts = filtered_reviews['text'].fillna("").tolist()
                        
                        # 3. POPRAVEK: Dodan batch_size za stabilnost na Renderju
                        sentiment_results = sentiment_pipeline(review_texts, batch_size=4)
                        
                        filtered_reviews['Sentiment'] = [res['label'].capitalize() for res in sentiment_results]
                        filtered_reviews['Confidence'] = [res['score'] for res in sentiment_results]
                        
                        # Grafika in ostalo...
                        sentiment_counts = filtered_reviews['Sentiment'].value_counts().reset_index()
                        sentiment_counts.columns = ['Sentiment', 'Count']
                        
                        st.bar_chart(sentiment_counts, x='Sentiment', y='Count')
                        st.dataframe(filtered_reviews[['date', 'rating', 'text', 'Sentiment', 'Confidence']])
                else:
                    st.info(f"Ni ocen za {selected_month_label}.")