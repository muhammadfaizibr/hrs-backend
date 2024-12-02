def generate_description(llm, prompt, attraction_data):
    input_data = {
        "name": attraction_data["name"],
        "city": attraction_data["city"],
        "rating": attraction_data["rating"],
        "ranking": attraction_data["ranking"],
        "address": attraction_data["address"],
        "description": attraction_data["description"],
        "subcategories": attraction_data["subcategories"],
    }
    
    chain = prompt | llm
    response = chain.invoke(input_data)
    
    return response.content
