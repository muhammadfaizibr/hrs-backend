from recommendations import get_recommendations
def fetch_related_attractions(attraction_id, tfidf_title, tfidf_city, tfidf_subcategories,
    tfidf_matrix_title,
    tfidf_matrix_city, tfidf_matrix_subcategories,df_attractions,
    llm, prompt):
    selected_attraction = df_attractions[df_attractions['id'] == attraction_id]
    if selected_attraction.empty:
        return "No attraction found with the given ID."
    
    selected_attraction = selected_attraction.iloc[0]

    return get_recommendations(selected_attraction["address"],selected_attraction["city"],selected_attraction["subcategories"], tfidf_title, tfidf_city, tfidf_subcategories,
    tfidf_matrix_title,
    tfidf_matrix_city, tfidf_matrix_subcategories,df_attractions,
    llm, prompt, True)
