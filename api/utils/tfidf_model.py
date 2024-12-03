# tfidf_model.py
from sklearn.feature_extraction.text import TfidfVectorizer

def initialize_tfidf(df, place_type):
    vectorizers = {
        "title": TfidfVectorizer(stop_words="english"),
        "city": TfidfVectorizer(stop_words="english"),
        "subcategories": TfidfVectorizer(stop_words="english"),
        "amenities": TfidfVectorizer(stop_words="english") if place_type == "hotel" else None,
        
    }
    tfidf_matrices = {
        key: vec.fit_transform(df[col])
        for key, (vec, col) in zip(
            vectorizers.keys(),
            [
                (vectorizers["title"], "name"),
                (vectorizers["amenities"], "combined_amenities") if place_type == "hotel" else None,

                (vectorizers["city"], "city"),
                (vectorizers["subcategories"], "subcategories"),
            ],
        )
    }
    return vectorizers, tfidf_matrices
