import streamlit as st
import pandas as pd
import json
from datetime import datetime
from transformers import pipeline
import torch

# 1. OPTIMIZACIJA SPOMINA: Onemogočimo gradiente, ker modela ne treniramo
torch.set_grad_enabled(False)

st.set_page_config(page_title="Analiza Izdelkov in Ocen", layout="wide")

# --- Funkcija za nalaganje podatkov (s predpomnilnikom) ---
@st.cache_data
def load_data():
    data = {}
    # Naloži izdelke
    try:
        with open('data_products.json', 'r', encoding='utf-8') as f:
            data['products'] = pd.DataFrame(json.load(f))
    except FileNotFoundError:
        data['products'] = pd.DataFrame()

    # Naloži pričevanja
    try:
        with open('data_testimonials.json', 'r', encoding='utf-8') as f:
            data['testimonials'] = pd.DataFrame(json.load(f))
    except FileNotFoundError:
        data['testimonials'] = pd.DataFrame()

    # Naloži ocene
    try:
        with open('data_reviews.json', 'r', encoding='utf-8') as f:
            df_reviews = pd.DataFrame(json.load(f))
            # Pretvori stolpec z datumi v datetime objekte
            df_reviews['date'] = pd.to_datetime(df_reviews['date'])
            data['reviews'] = df_reviews
    except FileNotFoundError:
        data['reviews'] = pd.DataFrame()
    
    return data

# --- Funkcija za nalaganje AI modela (s predpomnilnikom) ---
@st.cache_resource
def load_sentiment_model():
    # Uporabimo TinyBERT (cca 18MB), ki je edini varen za 512MB RAM na Renderju
    model_name = "prajjwal1/bert-tiny"
    return pipeline(
        "sentiment-analysis", 
        model=model_name, 
        device=-1  # Prisili uporabo procesorja (CPU)
    )

# Naložimo podatke in model ob zagonu
data = load_data()
products_df = data.get('products')
testimonials_df = data.get('testimonials')
reviews_df = data.get('reviews')
sentiment_pipeline = load_sentiment_model()

# --- Stranska vrstica (Sidebar) ---
st.sidebar.title("Navigacija")
page = st.sidebar.radio("Izberi stran:", ["Izdelki", "Pričevanja", "Ocene"])

# --- STRAN: IZDELKI ---
if page == "Izdelki":
    st.header("Seznam izdelkov")
    if not products_df.empty:
        st.dataframe(products_df, use_container_width=True)
    else:
        st.info("Ni podatkov o izdelkih.")

# --- STRAN: PRIČEVANJA ---
elif page == "Pričevanja":
    st.header("Pričevanja strank")
    if not testimonials_df.empty:
        st.dataframe(testimonials_df, use_container_width=True)
    else:
        st.info("Ni podatkov o pričevanjih.")

# --- STRAN: OCENE IN ANALIZA ---
elif page == "Ocene":
    st.header("Analiza ocen strank (2023)")

    if not reviews_df.empty:
        # Filtriramo samo leto 2023
        reviews_2023 = reviews_df[reviews_df['date'].dt.year == 2023].copy()

        if not reviews_2023.empty:
            # Priprava mesecev za drsnik
            months_2023 = sorted(list(reviews_2023['date'].dt.to_period('M').unique()))
            month_labels = [m.strftime("%b %Y") for m in months_2023]

            selected_month_label = st.select_slider(
                "Izberi mesec za analizo:",
                options=month_labels,
                value=month_labels[0]
            )

            # Filtriranje podatkov za izbran mesec
            selected_month_period = pd.Period(selected_month_label, freq='M')
            filtered_reviews = reviews_2023[reviews_2023['date'].dt.to_period('M') == selected_month_period].copy()

            if not filtered_reviews.empty:
                st.subheader(f"Rezultati za {selected_month_label}")
                
                if 'text' in filtered_reviews.columns:
                    # Priprava besedil (odstranimo prazne vrednosti)
                    texts = filtered_reviews['text'].fillna("").tolist()
                    
                    # Izvedba analize sentimenta (batch_size=4 prepreči skoke v porabi RAM-a)
                    with st.spinner('AI analizira sentiment...'):
                        results = sentiment_pipeline(texts, batch_size=4)

                    # Mapiranje LABEL_0/LABEL_1 v človeku prijazna imena
                    final_labels = []
                    for res in results:
                        if res['label'] == 'LABEL_1':
                            final_labels.append('Positive')
                        elif res['label'] == 'LABEL_0':
                            final_labels.append('Negative')
                        else:
                            final_labels.append(res['label'].capitalize())

                    filtered_reviews['Sentiment'] = final_labels
                    filtered_reviews['Confidence'] = [round(res['score'], 3) for res in results]

                    # --- VIZUALIZACIJA ---
                    
                    # 1. Grafikon porazdelitve
                    sentiment_counts = filtered_reviews['Sentiment'].value_counts().reset_index()
                    sentiment_counts.columns = ['Sentiment', 'Število']
                    
                    col1, col2 = st.columns([1, 2])
                    
                    with col1:
                        st.write("### Povzetek")
                        st.dataframe(sentiment_counts, hide_index=True)
                    
                    with col2:
                        st.bar_chart(sentiment_counts, x='Sentiment', y='Število', color="#29b5e8")

                    # 2. Podrobna tabela
                    st.write("### Podrobni seznami ocen")
                    display_cols = ['date', 'rating', 'text', 'Sentiment', 'Confidence']
                    # Prikažemo samo obstoječe stolpce
                    actual_cols = [c for c in display_cols if c in filtered_reviews.columns]
                    st.dataframe(filtered_reviews[actual_cols], use_container_width=True, hide_index=True)
                else:
                    st.error("Napaka: Stolpec 'text' ne obstaja v JSON datoteki.")
            else:
                st.info(f"Ni podatkov za mesec {selected_month_label}.")
        else:
            st.warning("V datoteki ni nobene ocene iz leta 2023.")
    else:
        st.info("Ni podatkov o ocenah (data_reviews.json manjka ali je prazen).")