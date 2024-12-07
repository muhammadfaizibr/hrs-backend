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
       "You are a professional assistant that provides concise, engaging, and recommendation-focused descriptions. Your responses should summarize key details about the given place, focusing on its most relevant features based on the provided variables. Offer a personalized recommendation for the user using the given information, emphasizing aspects like rating, ranking, amenities, and unique features."

    )

    # if place_type == "hotel":
    #     human = ("{name} in {city}, located at {address}, is highly recommended for its subcategory of {subcategories}. With rating of {rating}/5.0 and ranked {ranking}, it stands out as a must-visit destination. {description} This place is praised for its unique features, making it an excellent option for travelers, ensuring a comfortable and enjoyable stay.")

    # else:
    #     human = ("{name} in {city}, located at {address}, is highly recommended for its subcategory of {subcategories}. With a rating of {rating}/5.0 and ranked {ranking}, it stands out as a must-visit destination. {description} This place is praised for its unique features, making it an excellent option for travelers. It offers amenities such as {amenities}, ensuring a comfortable and enjoyable stay.")
    if place_type == "attraction":
        human = ("{name} in {city}, at {address}, is highly recommended for its {subcategories}. Rated {rating}/5.0 and ranked {ranking}, it's a must-visit. {description} Praised for unique features, it's perfect for travelers seeking comfort.")

    else:
        human = ("{name} in {city}, at {address}, is highly recommended for its {subcategories}. Rated {rating}/5.0 and ranked {ranking}, it's a must-visit. {description} Known for unique features, with amenities like {amenities}, it ensures a comfortable stay.")


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


