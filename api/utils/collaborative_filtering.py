import numpy as np
from django.db.models import Q

def get_user_ratings(user_id, Rating):
    return Rating.objects.filter(user_id=user_id)

def get_all_ratings_except_user(user_id, Rating):
    return Rating.objects.exclude(user_id=user_id)

def calculate_similarity(user_ratings, other_user_ratings):
    user_dict = {rating.place_id: rating.rating for rating in user_ratings}
    other_user_dict = {}

    for rating in other_user_ratings:
        if rating.user_id not in other_user_dict:
            other_user_dict[rating.user_id] = {}
        other_user_dict[rating.user_id][rating.place_id] = rating.rating

    similarities = []
    for other_user, ratings in other_user_dict.items():
        common_places = set(user_dict.keys()) & set(ratings.keys())
        if not common_places:
            continue

        user_vector = np.array([user_dict[place] for place in common_places])
        other_vector = np.array([ratings[place] for place in common_places])

        similarity = np.dot(user_vector, other_vector) / (np.linalg.norm(user_vector) * np.linalg.norm(other_vector))
        similarities.append((other_user, similarity))

    similarities.sort(key=lambda x: x[1], reverse=True)
    return similarities

def recommend_places(user_id, Review, Place, top_n=5):
    user_ratings = get_user_ratings(user_id, Review)
    other_user_ratings = get_all_ratings_except_user(user_id, Review)

    similarities = calculate_similarity(user_ratings, other_user_ratings)

    recommendations = {}
    for similar_user, similarity in similarities:
        similar_user_ratings = Review.objects.filter(user=similar_user).exclude(
            place_id__in=[rating.place_id for rating in user_ratings]
        )

        for rating in similar_user_ratings:
            if rating.place_id not in recommendations:
                recommendations[rating.place_id] = 0
            recommendations[rating.place_id] += rating.rating * similarity

    sorted_recommendations = sorted(recommendations.items(), key=lambda x: x[1], reverse=True)
    place_ids = [rec[0] for rec in sorted_recommendations[:top_n]]
    return Place.objects.filter(id__in=place_ids)
