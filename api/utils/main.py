from langchain_groq import ChatGroq
from api.utils.preprocess import preprocess_data, load_or_generate_tfidf_models
from api.utils.recommendations import get_recommendations
from langchain_core.prompts import ChatPromptTemplate
# from related_attractions import fetch_related_attractions

def main(dataset, query_title, query_city, query_subcategories):
    df_attractions = preprocess_data(dataset)

    tfidf_title, tfidf_city, tfidf_subcategories, \
    tfidf_matrix_title, tfidf_matrix_city, tfidf_matrix_subcategories = load_or_generate_tfidf_models(df_attractions)

    llm = ChatGroq(model_name="mixtral-8x7b-32768", temperature=0.7, groq_api_key="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")

    system = (
        "You are a professional assistant that provides concise, engaging, and recommendation-focused attractions descriptions. "
        "Your responses should summarize key details in a paragraph format in clear and precised way, highlight the most relevant features tailored to user preferences, "
        "and provide a personalized recommendation for the user."
    )


    human = (
        "{name} in {city}, located at {address}, is highly recommended for its subcategory of {subcategories}. "
        "With a rating of {rating}/5.0 and ranked {ranking}, it stands out as a must-visit destination. "
        "{description} The attraction is praised for its unique features, making it an excellent option for travelers."
    )

    prompt = ChatPromptTemplate.from_messages([("system", system), ("human", human)])
    print(query_title, query_city, query_subcategories, "hello")
    description, remaining_attractions = get_recommendations(
        query_title="islamabad best hotels",
        query_city="islamabad",
        query_subcategories="parks",
        tfidf_title=tfidf_title, tfidf_city=tfidf_city, tfidf_subcategories=tfidf_subcategories,
        tfidf_matrix_title=tfidf_matrix_title,
        tfidf_matrix_city=tfidf_matrix_city, tfidf_matrix_subcategories=tfidf_matrix_subcategories,
        df_attractions=df_attractions,
        llm=llm, prompt=prompt, related=False
    )
    print(description, remaining_attractions)
    return description

    # print(description)
    # # full_description = ""
    # # for word in description:
    # #     full_description += word + " "
    # #     print(word, end=" ", flush=True) 
    # print(remaining_attractions)

    # related_attractions = fetch_related_attractions(int(input("Enter attraction ID for realted recommnedations: ")),     tfidf_title=tfidf_title,tfidf_city=tfidf_city, tfidf_subcategories=tfidf_subcategories,
    #     tfidf_matrix_title=tfidf_matrix_title,
    #     tfidf_matrix_city=tfidf_matrix_city, tfidf_matrix_subcategories=tfidf_matrix_subcategories,df_attractions=df_attractions,
    #     llm=llm, prompt=prompt)

    # print(related_attractions)


