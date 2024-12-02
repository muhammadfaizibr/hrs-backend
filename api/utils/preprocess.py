import pandas as pd
import re
import os
import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from django.conf import settings
from pathlib import Path
            

def preprocess_data(dataset):
    df_attractions = dataset 
    # file_path = Path(settings.BASE_DIR) / 'static/datasets' / "attractions_data.csv"
    # df_attractions = pd.read_csv(file_path, encoding = "ISO-8859-1")
    # print(dataset)
    # df_attractions = df_attractions.rename(columns={"Attraction_Name": 'name'})
    df_attractions.columns = df_attractions.columns.str.lower()
    df_attractions.drop_duplicates(subset=['name'], inplace=True)
    df_attractions.reset_index(drop=True, inplace=True)
    df_attractions['name'] = df_attractions['name'].fillna("")
    df_attractions['city'] = df_attractions['city'].fillna("")
    df_attractions['address'] = df_attractions['address'].fillna("")
    df_attractions['title'] = df_attractions['title'].fillna("")
    df_attractions['description'] = df_attractions['description'].fillna("")
    df_attractions['subcategories'] = df_attractions['subcategories'].fillna("General")
    df_attractions['rating'] = df_attractions['rating'].fillna(0).astype(float)
    df_attractions['ranking'] = df_attractions['ranking'].fillna("Unknown ranking")
    df_attractions['id'] = df_attractions['id'].astype(int)


    def process_ranking(ranking):
        """Extract numeric rank from strings like '27 of 90 attractions in Lahore'."""
        match = re.search(r"(\d+) of (\d+)", ranking)
        if match:
            rank, total = map(int, match.groups())
            return rank / total 
        return 1.0  

    df_attractions['normalized_ranking'] = df_attractions['ranking'].apply(process_ranking)
    
    return df_attractions

def load_or_generate_tfidf_models(df_attractions):
    models_dir = "models"
    os.makedirs(models_dir, exist_ok=True)
    
    tfidf_title_path = os.path.join(models_dir, "tfidf_title.pkl")
    tfidf_city_path = os.path.join(models_dir, "tfidf_city.pkl")
    tfidf_subcategories_path = os.path.join(models_dir, "tfidf_subcategories.pkl")
    tfidf_matrix_title_path = os.path.join(models_dir, "tfidf_matrix_title.pkl")
    tfidf_matrix_city_path = os.path.join(models_dir, "tfidf_matrix_city.pkl")
    tfidf_matrix_subcategories_path = os.path.join(models_dir, "tfidf_matrix_subcategories.pkl")
    
    if os.path.exists(tfidf_title_path):
        print("Loading existing TF-IDF models...")
        tfidf_title = joblib.load(tfidf_title_path)
        tfidf_city = joblib.load(tfidf_city_path)
        tfidf_subcategories = joblib.load(tfidf_subcategories_path)
        tfidf_matrix_title = joblib.load(tfidf_matrix_title_path)
        tfidf_matrix_city = joblib.load(tfidf_matrix_city_path)
        tfidf_matrix_subcategories = joblib.load(tfidf_matrix_subcategories_path)

    else:
        print("Generating new TF-IDF models...")
        tfidf_title = TfidfVectorizer(stop_words="english")
        tfidf_city = TfidfVectorizer(stop_words="english")
        tfidf_subcategories = TfidfVectorizer(stop_words="english")
        
        tfidf_matrix_title = tfidf_title.fit_transform(df_attractions['name'] + ' ' + df_attractions['address'] + ' ' + df_attractions['title']+ ' ' + df_attractions['description'])
        tfidf_matrix_city = tfidf_city.fit_transform(df_attractions['city'])
        tfidf_matrix_subcategories = tfidf_subcategories.fit_transform(df_attractions['subcategories'])
        
        joblib.dump(tfidf_title, tfidf_title_path)
        joblib.dump(tfidf_city, tfidf_city_path)
        joblib.dump(tfidf_subcategories, tfidf_subcategories_path)
        joblib.dump(tfidf_matrix_title, tfidf_matrix_title_path)
        joblib.dump(tfidf_matrix_city, tfidf_matrix_city_path)
        joblib.dump(tfidf_matrix_subcategories, tfidf_matrix_subcategories_path)

    return (
        tfidf_title, tfidf_city, tfidf_subcategories,
        tfidf_matrix_title, tfidf_matrix_city, tfidf_matrix_subcategories
    )
