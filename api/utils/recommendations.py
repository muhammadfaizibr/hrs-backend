from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import MinMaxScaler
from api.utils.description_generator import generate_description

def get_recommendations(query_title, query_city, query_subcategories, 
                        tfidf_title, tfidf_city, tfidf_subcategories, 
                        tfidf_matrix_title,
                        tfidf_matrix_city, tfidf_matrix_subcategories, df_attractions, llm, prompt, related):
    query_vector_title = tfidf_title.transform([query_title])
    query_vector_city = tfidf_city.transform([query_city])
    query_vector_subcategories = tfidf_subcategories.transform([query_subcategories])
    
    title_sim_scores = cosine_similarity(query_vector_title, tfidf_matrix_title).flatten()
    city_sim_scores = cosine_similarity(query_vector_city, tfidf_matrix_city).flatten()
    subcategories_sim_scores = cosine_similarity(query_vector_subcategories, tfidf_matrix_subcategories).flatten()
    
    scaler = MinMaxScaler()
    title_sim_scores = scaler.fit_transform(title_sim_scores.reshape(-1, 1)).flatten()
    city_sim_scores = scaler.fit_transform(city_sim_scores.reshape(-1, 1)).flatten()
    subcategories_sim_scores = scaler.fit_transform(subcategories_sim_scores.reshape(-1, 1)).flatten()
    
    print(len(title_sim_scores), len(city_sim_scores), len(subcategories_sim_scores), len(df_attractions))
    
    df_attractions['similarity_score'] = (
        0.4 * title_sim_scores +
        0.3 * city_sim_scores +
        0.3 * subcategories_sim_scores
    )
    
    df_attractions['final_score'] = (
        0.6 * df_attractions['similarity_score'] +
        0.3 * (df_attractions['rating'] / 5) - 
        0.1 * df_attractions['normalized_ranking']
    )
    
    top_results = df_attractions.nlargest(10, 'final_score')
    
    remaining_attractions = top_results.iloc[:][['name', 'id','city', 'address','subcategories', 'rating', 'ranking']]

    if not related:
        description = generate_description(llm, prompt, top_results.iloc[0])
        return description, remaining_attractions

    return remaining_attractions
    
