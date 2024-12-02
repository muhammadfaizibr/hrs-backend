# tfidf_model.py
from sklearn.feature_extraction.text import TfidfVectorizer

def initialize_tfidf(df_attractions):
    vectorizers = {
        "title": TfidfVectorizer(stop_words="english"),
        "city": TfidfVectorizer(stop_words="english"),
        "subcategories": TfidfVectorizer(stop_words="english"),
    }
    tfidf_matrices = {
        key: vec.fit_transform(df_attractions[col])
        for key, (vec, col) in zip(
            vectorizers.keys(),
            [
                (vectorizers["title"], "name"),
                (vectorizers["city"], "city"),
                (vectorizers["subcategories"], "subcategories"),
            ],
        )
    }
    return vectorizers, tfidf_matrices
