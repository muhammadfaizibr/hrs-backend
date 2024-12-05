import numpy as np
from django.db.models import Q

def get_user_ratings(user, Reviews):
    return Reviews.objects.filter(user=user)

def get_all_ratings_except_user(user, Reviews):
    return Reviews.objects.exclude(user=user)

def calculate_user_similarity(user_ratings, other_user_ratings, threshold=0.2):
    user_dict = {rating.place.id: rating.rating for rating in user_ratings}
    other_user_dict = {}

    for rating in other_user_ratings:
        if rating.user.id not in other_user_dict:
            other_user_dict[rating.user.id] = {}
        other_user_dict[rating.user.id][rating.place.id] = rating.rating

    similarities = []
    for other_user, ratings in other_user_dict.items():
        common_places = set(user_dict.keys()) & set(ratings.keys())
        if not common_places:
            continue

        user_vector = np.array([user_dict[place] for place in common_places])
        other_vector = np.array([ratings[place] for place in common_places])

        similarity = np.dot(user_vector, other_vector) / (np.linalg.norm(user_vector) * np.linalg.norm(other_vector))

        if similarity >= threshold:
            similarities.append((other_user, similarity))

    similarities.sort(key=lambda x: x[1], reverse=True)
    return similarities

def recommend_places(user, Reviews, Place, top_n=20, threshold=0.2):
    user_ratings = get_user_ratings(user, Reviews)
    other_user_ratings = get_all_ratings_except_user(user, Reviews)

    similarities = calculate_user_similarity(user_ratings, other_user_ratings, threshold)

    if not similarities:
        return Place.objects.all()[:top_n]

    recommendations = {}

    for similar_user, similarity in similarities:
        similar_user_ratings = Reviews.objects.filter(user=similar_user).exclude(
            place__in=[rating.place for rating in user_ratings]
        )

        for rating in similar_user_ratings:
            if rating.place.id not in recommendations:
                recommendations[rating.place.id] = 0
            recommendations[rating.place.id] += rating.rating * similarity

    sorted_recommendations = sorted(recommendations.items(), key=lambda x: x[1], reverse=True)

    if not sorted_recommendations:
        return Place.objects.all()[:top_n]

    place_ids = [rec[0] for rec in sorted_recommendations[:top_n]]
    return Place.objects.filter(id__in=place_ids)
