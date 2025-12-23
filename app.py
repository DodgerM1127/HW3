import streamlit as st
import pandas as pd
import json
from datetime import datetime
from transformers import pipeline

st.set_page_config(layout="wide")

# --- Funkcija za nalaganje podatkov (s predpomnilnikom) ---
@st.cache_data
def load_data():
    data = {}
    # Check if files exist before trying to load them
    try:
        with open('data_products.json', 'r', encoding='utf-8') as f:
            data['products'] = pd.DataFrame(json.load(f))
    except FileNotFoundError:
        st.error("Datoteka data_products.json ni najdena.")
        data['products'] = pd.DataFrame()

    try:
        with open('data_testimonials.json', 'r', encoding='utf-8') as f:
            data['testimonials'] = pd.DataFrame(json.load(f))
    except FileNotFoundError:
        st.error("Datoteka data_testimonials.json ni najdena.")
        data['testimonials'] = pd.DataFrame()

    try:
        with open('data_reviews.json', 'r', encoding='utf-8') as f:
            df_reviews = pd.DataFrame(json.load(f))
            # Convert 'date' column to datetime objects
            df_reviews['date'] = pd.to_datetime(df_reviews['date'])
            data['reviews'] = df_reviews
    except FileNotFoundError:
        st.error("Datoteka data_reviews.json ni najdena.")
        data['reviews'] = pd.DataFrame()
    return data

# Nalaganje vseh podatkov
data = load_data()
products_df = data.get('products')
testimonials_df = data.get('testimonials')
reviews_df = data.get('reviews')
sentiment_pipeline = pipeline('sentiment-analysis')

# --- Sidebar Navigacija ---
st.sidebar.title("Navigacija")
page = st.sidebar.radio("Izberi stran:", ["Izdelki", "Pričevanja", "Ocene"])

# --- Prikaz vsebine glede na izbiro ---
if page == "Izdelki":
    st.header("Prikaz izdelkov")
    if not products_df.empty:
        st.dataframe(products_df)
    else:
        st.info("Ni podatkov o izdelkih za prikaz.")

elif page == "Pričevanja":
    st.header("Prikaz pričevanj")
    if not testimonials_df.empty:
        st.dataframe(testimonials_df)
    else:
        st.info("Ni podatkov o pričevanjih za prikaz.")

elif page == "Ocene":
    st.header("Prikaz ocen (2023)")

    if not reviews_df.empty:
        # Filtriranje za leto 2023
        reviews_2023 = reviews_df[reviews_df['date'].dt.year == 2023]

        if not reviews_2023.empty:
            # Ustvari seznam mesecev za drsnik
            months_2023 = sorted(list(reviews_2023['date'].dt.to_period('M').unique()))
            month_labels = [m.strftime("%b %Y") for m in months_2023]

            if month_labels:
                selected_month_label = st.select_slider(
                    "Izberi mesec:",
                    options=month_labels,
                    value=month_labels[0] # Privzeto izbran prvi mesec
                )

                # Pretvorba izbranega meseca nazaj v Period objekt za filtriranje
                selected_month_period = pd.Period(selected_month_label, freq='M')

                filtered_reviews = reviews_2023[reviews_2023['date'].dt.to_period('M') == selected_month_period]

                if not filtered_reviews.empty:
                    st.subheader(f"Ocene za {selected_month_label}")
                    # Apply sentiment analysis
                    if 'text' in filtered_reviews.columns and not filtered_reviews['text'].empty:
                        review_texts = filtered_reviews['text'].tolist()
                        sentiment_results = sentiment_pipeline(review_texts)
                        # Extract label and convert to 'Positive'/'Negative' for better display
                        filtered_reviews['Sentiment'] = [res['label'].capitalize() for res in sentiment_results]
                        filtered_reviews['Confidence'] = [res['score'] for res in sentiment_results] # Store confidence score
                    else:
                        filtered_reviews['Sentiment'] = 'N/A' # Handle cases with no text column or empty text
                        filtered_reviews['Confidence'] = 0.0 # Default confidence

                    # Prepare data for the bar chart
                    sentiment_counts = filtered_reviews['Sentiment'].value_counts().reset_index()
                    sentiment_counts.columns = ['Sentiment', 'Count']

                    # Calculate average confidence
                    avg_confidence = filtered_reviews.groupby('Sentiment')['Confidence'].mean().reset_index()
                    avg_confidence.columns = ['Sentiment', 'Average Confidence']

                    # Merge for display in chart if needed, or display separately
                    chart_data = pd.merge(sentiment_counts, avg_confidence, on='Sentiment')

                    st.subheader("Analiza sentimenta za izbrani mesec")

                    # Display the bar chart
                    st.bar_chart(chart_data, x='Sentiment', y='Count')

                    # Display average confidence scores below the chart
                    for index, row in chart_data.iterrows():
                        st.write(f"Povprečna zanesljivost za {row['Sentiment']} ocene: {row['Average Confidence']:.2f}")

                    st.dataframe(filtered_reviews[['date', 'rid', 'rating', 'text', 'Sentiment', 'Confidence']].reset_index(drop=True))
                else:
                    st.info(f"Ni ocen za {selected_month_label}.")
            else:
                st.info("Ni razpoložljivih mesecev za filtriranje v letu 2023.")
        else:
            st.info("Ni ocen za leto 2023 v podatkih.")
    else:
        st.info("Ni podatkov o ocenah za prikaz.")