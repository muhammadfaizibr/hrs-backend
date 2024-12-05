from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import MinMaxScaler
from api.utils.description_generator import generate_description

def get_recommendations(query_title, query_city, query_amenities,query_subcategories, 
                        tfidf_title, tfidf_amenities,tfidf_city, tfidf_subcategories, 
                        tfidf_matrix_title, tfidf_matrix_amenities,
                        tfidf_matrix_city, tfidf_matrix_subcategories, df, 
                        # llm, prompt,
                         related, place_type):
    query_vector_title = tfidf_title.transform([query_title])
    query_vector_amenities = tfidf_amenities.transform([query_amenities]) if place_type == "hotel" else None

    query_vector_city = tfidf_city.transform([query_city])
    query_vector_subcategories = tfidf_subcategories.transform([query_subcategories])
    
    title_sim_scores = cosine_similarity(query_vector_title, tfidf_matrix_title).flatten()
    city_sim_scores = cosine_similarity(query_vector_city, tfidf_matrix_city).flatten()
    subcategories_sim_scores = cosine_similarity(query_vector_subcategories, tfidf_matrix_subcategories).flatten()
    
    scaler = MinMaxScaler()
    title_sim_scores = scaler.fit_transform(title_sim_scores.reshape(-1, 1)).flatten()

    city_sim_scores = scaler.fit_transform(city_sim_scores.reshape(-1, 1)).flatten()
    subcategories_sim_scores = scaler.fit_transform(subcategories_sim_scores.reshape(-1, 1)).flatten()
    
    if place_type == "hotel":
        amenities_sim_scores = cosine_similarity(query_vector_amenities, tfidf_matrix_amenities).flatten()
        amenities_sim_scores = scaler.fit_transform(amenities_sim_scores.reshape(-1, 1)).flatten() 

        df['similarity_score'] = (
            0.3 * title_sim_scores +
            0.3 * city_sim_scores +
            0.2 * amenities_sim_scores +
            0.2 * subcategories_sim_scores
        )
    
    else:
        df['similarity_score'] = (
            0.4 * title_sim_scores +
            0.3 * city_sim_scores +
            0.3 * subcategories_sim_scores
        )
    df['final_score'] = (
        0.6 * df['similarity_score'] +
        0.3 * (df['rating'] / 5) - 
        0.1 * df['normalized_ranking']
    )
    
    top_results = df.nlargest(40, 'final_score')
    if place_type == "hotel":
        remaining = top_results.iloc[:][['place_type', 'name', 'id','city', 'image_url','address','subcategories', 'rating', 'ranking', 'combined_amenities']]
    else:
        remaining = top_results.iloc[:][['place_type', 'name', 'id','city', 'image_url','address','subcategories', 'rating', 'ranking']]

    if not related:
        # description = generate_description(llm, prompt, top_results.iloc[0], place_type)
        description = "lorem ipsum"
        return description, remaining

    return remaining
    
