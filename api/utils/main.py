from langchain_groq import ChatGroq
from api.utils.preprocess import preprocess_data, load_or_generate_tfidf_models
from api.utils.recommendations import get_recommendations
from langchain_core.prompts import ChatPromptTemplate
# from related import fetch_related

def main(dataset, query_title, query_amenities,query_city, query_subcategories, place_type):
    df = preprocess_data(dataset, place_type)

    tfidf_title, tfidf_amenities, tfidf_city, tfidf_subcategories, \
    tfidf_matrix_title, tfidf_matrix_amenities, tfidf_matrix_city, tfidf_matrix_subcategories = load_or_generate_tfidf_models(df, place_type)

    llm = ChatGroq(model_name="mixtral-8x7b-32768", temperature=0.7, groq_api_key="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")

    system = (
        "You are a professional assistant that provides concise, engaging, and recommendation-focused descriptions. "
        "Your responses should summarize key details in a paragraph format in clear and precised way, highlight the most relevant features tailored to user preferences, "
        "and provide a personalized recommendation for the user."
    )


    human = (
        "{name} in {city}, located at {address}, is highly recommended for its subcategory of {subcategories}. "
        "With a rating of {rating}/5.0 and ranked {ranking}, it stands out as a must-visit destination. "
        "{description} This is praised for its unique features, making it an excellent option for travelers."
        "It offers amenities such as {amenities}, ensuring a comfortable and enjoyable stay." if place_type == "hotel" else ""
    )

    prompt = ChatPromptTemplate.from_messages([("system", system), ("human", human)])

    print(query_title, query_city, query_subcategories)

    description, remaining = get_recommendations(
        query_title=query_title,
        query_amenities=query_amenities,
        query_city=query_city,
        query_subcategories=query_subcategories,
        tfidf_title=tfidf_title, tfidf_amenities=tfidf_amenities, tfidf_city=tfidf_city, tfidf_subcategories=tfidf_subcategories,
        tfidf_matrix_title=tfidf_matrix_title, tfidf_matrix_amenities=tfidf_matrix_amenities,
        tfidf_matrix_city=tfidf_matrix_city, tfidf_matrix_subcategories=tfidf_matrix_subcategories,
        df=df,
        llm=llm, prompt=prompt, related=False, place_type=place_type
    )
    print(description, remaining)

    return description


