from recommendations import get_recommendations
def fetch_related(attraction_id, tfidf_title, tfidf_city, tfidf_subcategories,
    tfidf_matrix_title,
    tfidf_matrix_city, tfidf_matrix_subcategories,df,
    llm, prompt):
    selected_attraction = df[df['id'] == attraction_id]
    if selected_attraction.empty:
        return "No attraction found with the given ID."
    
    selected_attraction = selected_attraction.iloc[0]

    return get_recommendations(selected_attraction["address"],selected_attraction["city"],selected_attraction["subcategories"], tfidf_title, tfidf_city, tfidf_subcategories,
    tfidf_matrix_title,
    tfidf_matrix_city, tfidf_matrix_subcategories,df,
    llm, prompt, True)
