# def generate_description(llm, prompt, df, place_type):
#     input_data = {
#         "name": df["name"],
#         "city": df["city"],
#         "rating": df["rating"],
#         "ranking": df["ranking"],
#         "address": df["address"],
#         "description": df["description"],
#         "subcategories": df["subcategories"],
#         "amenities": ", ".join(df["combined_amenities"].split(", ")) if place_type == "hotel" else [""],
#     }
    
#     chain = prompt | llm
#     response = chain.invoke(input_data)
    
#     return response.content


def generate_description(llm, prompt, top_results, place_type):
    recommendations = []

    for _, row in top_results.iterrows():
        input_data = {
            "name": row["name"],
            "city": row["city"],
            "rating": row["rating"],
            # "ranking": row["ranking"],
            "address": row["address"],
            # "description": row["description"],
            # "subcategories": row["subcategories"],
            "amenities": ", ".join(row["combined_amenities"].split(", ")) if place_type == "hotel" else "",
        }

        chain = prompt | llm
        response = chain.invoke(input_data)
        recommendations.append(response.content)

    return recommendations