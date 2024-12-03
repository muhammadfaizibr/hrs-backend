def generate_description(llm, prompt, df, place_type):
    input_data = {
        "name": df["name"],
        "city": df["city"],
        "rating": df["rating"],
        "ranking": df["ranking"],
        "address": df["address"],
        "description": df["description"],
        "subcategories": df["subcategories"],
        "amenities": ", ".join(df["combined_amenities"].split(", ")) if place_type == "hotel" else [""],
    }
    
    chain = prompt | llm
    response = chain.invoke(input_data)
    
    return response.content
