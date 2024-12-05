import pandas as pd
import re
import os
import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from django.conf import settings
from pathlib import Path
            

def preprocess_data(dataset, place_type):
    df = dataset 
    # file_path = Path(settings.BASE_DIR) / 'static/datasets' / "attractions_data.csv"
    # df = pd.read_csv(file_path, encoding = "ISO-8859-1")
    # df = df.rename(columns={"Attraction_Name": 'name'})
    df.columns = df.columns.str.lower()
    df.drop_duplicates(subset=['name'], inplace=True)
    df.reset_index(drop=True, inplace=True)
    df['name'] = df['name'].fillna("")
    df['city'] = df['city'].fillna("")
    df['address'] = df['address'].fillna("")
    df['title'] = df['title'].fillna("")
    df['description'] = df['description'].fillna("")
    df['subcategories'] = df['subcategories'].fillna("General")
    df['rating'] = df['rating'].fillna(0).astype(float)
    df['ranking'] = df['ranking'].fillna("Unknown ranking")
    df['id'] = df['id'].astype(int)
    if (place_type == "hotel"):
        df['combined_amenities'] = df['combined_amenities'].fillna("No amenities listed")


    def process_ranking(ranking):
        """Extract numeric rank from strings like '27 of 90 attractions in Lahore'."""
        match = re.search(r"(\d+) of (\d+)", ranking)
        if match:
            rank, total = map(int, match.groups())
            return rank / total 
        return 1.0  

    df['normalized_ranking'] = df['ranking'].apply(process_ranking)
    
    return df

def load_or_generate_tfidf_models(df, place_type):
    models_dir = "models"
    os.makedirs(models_dir, exist_ok=True)
    
    tfidf_title_path = os.path.join(models_dir, f"{place_type}_tfidf_title.pkl")
    tfidf_city_path = os.path.join(models_dir, f"{place_type}_tfidf_city.pkl")

    tfidf_amenities_path = os.path.join(models_dir, f"{place_type}_tfidf_amenities.pkl")
    tfidf_matrix_amenities_path = os.path.join(models_dir, f"{place_type}_tfidf_matrix_amenities.pkl")

    tfidf_subcategories_path = os.path.join(models_dir, f"{place_type}_tfidf_subcategories.pkl")
    tfidf_matrix_title_path = os.path.join(models_dir, f"{place_type}_tfidf_matrix_title.pkl")
    


    tfidf_matrix_city_path = os.path.join(models_dir, f"{place_type}_tfidf_matrix_city.pkl")
    tfidf_matrix_subcategories_path = os.path.join(models_dir, f"{place_type}_tfidf_matrix_subcategories.pkl")
    
    if os.path.exists(tfidf_title_path):
        print("Loading existing TF-IDF models...")
        tfidf_title = joblib.load(tfidf_title_path)
        tfidf_city = joblib.load(tfidf_city_path)
        
        tfidf_amenities = joblib.load(tfidf_amenities_path) if place_type == "hotel" else "" 
        tfidf_matrix_amenities = joblib.load(tfidf_matrix_amenities_path) if place_type == "hotel" else "" 

        tfidf_subcategories = joblib.load(tfidf_subcategories_path)
        tfidf_matrix_title = joblib.load(tfidf_matrix_title_path)
        tfidf_matrix_city = joblib.load(tfidf_matrix_city_path)
        tfidf_matrix_subcategories = joblib.load(tfidf_matrix_subcategories_path)

    else:
        print("Generating new TF-IDF models...")
        tfidf_title = TfidfVectorizer(stop_words="english")
        tfidf_amenities = TfidfVectorizer(stop_words="english") if place_type == "hotel" else ""

        tfidf_city = TfidfVectorizer(stop_words="english")
        tfidf_subcategories = TfidfVectorizer(stop_words="english")
        
        tfidf_matrix_title = tfidf_title.fit_transform(df['name'] + ' ' + df['address'] + ' ' + df['title']+ ' ' + df['description'])
        
        tfidf_matrix_amenities = tfidf_amenities.fit_transform(df['combined_amenities']) if place_type == "hotel" else ""
        if place_type == "hotel":
            joblib.dump(tfidf_matrix_amenities, tfidf_matrix_amenities_path)
            joblib.dump(tfidf_amenities, tfidf_amenities_path)

        tfidf_matrix_city = tfidf_city.fit_transform(df['city'])
        tfidf_matrix_subcategories = tfidf_subcategories.fit_transform(df['subcategories'])
        
        joblib.dump(tfidf_title, tfidf_title_path)
        joblib.dump(tfidf_city, tfidf_city_path)
        


        joblib.dump(tfidf_subcategories, tfidf_subcategories_path)
        joblib.dump(tfidf_matrix_title, tfidf_matrix_title_path)
        joblib.dump(tfidf_matrix_city, tfidf_matrix_city_path)
        joblib.dump(tfidf_matrix_subcategories, tfidf_matrix_subcategories_path)

    return (
        tfidf_title, tfidf_amenities, tfidf_city, tfidf_subcategories,
        tfidf_matrix_title, tfidf_matrix_amenities, tfidf_matrix_city, tfidf_matrix_subcategories
    )
