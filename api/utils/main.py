from langchain_groq import ChatGroq
from api.utils.preprocess import preprocess_data, load_or_generate_tfidf_models
from api.utils.recommendations import get_recommendations
from langchain_core.prompts import ChatPromptTemplate
# from related import fetch_related

def main(dataset, query_title, query_amenities,query_city, query_subcategories, place_type, related):
    df = preprocess_data(dataset, place_type)

    tfidf_title, tfidf_amenities, tfidf_city, tfidf_subcategories, \
    tfidf_matrix_title, tfidf_matrix_amenities, tfidf_matrix_city, tfidf_matrix_subcategories = load_or_generate_tfidf_models(df, place_type)

    llm = ChatGroq(model_name="mixtral-8x7b-32768", temperature=0.7, groq_api_key="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")
    system = (
        "You are a professional assistant who provides concise descriptions in exactly 3 to 4 bullet points. "
        "Each bullet point should be no more than 100 characters. "
        "Focus on key details like rating, ranking, and unique features, but keep everything short, clear, and to the point. "
        "Do not ask for additional details or clarification, and ensure the response is always natural and straightforward."
    )





    if place_type == "hotel":
        human = (
            "{name} in {city}, at {address}, is a top-rated hotel. "
            "Rated {rating}/5.0. Known for {amenities}, it ensures comfort."
        )
    else:
        human = (
            "{name} in {city}, at {address}, is a highly recommended attraction. "
            "Rated {rating}/5.0. Praised for unique features and comfort."
        )


    prompt = ChatPromptTemplate.from_messages([("system", system), ("human", human)])


    description, results = get_recommendations(
        query_title=query_title,
        query_amenities=query_amenities,
        query_city=query_city,
        query_subcategories=query_subcategories,
        tfidf_title=tfidf_title, tfidf_amenities=tfidf_amenities, tfidf_city=tfidf_city, tfidf_subcategories=tfidf_subcategories,
        tfidf_matrix_title=tfidf_matrix_title, tfidf_matrix_amenities=tfidf_matrix_amenities,
        tfidf_matrix_city=tfidf_matrix_city, tfidf_matrix_subcategories=tfidf_matrix_subcategories,
        df=df,
        llm=llm, prompt=prompt, 
        related=related, place_type=place_type
    )

    return description, results 


