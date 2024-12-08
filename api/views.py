from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
from api.serializers import UserRegistrationSerializer, UserLoginSerializer, UserProfileSerializer, PlaceSerializer, ReviewSerializerForList, ReviewSerializerForCreate, RecommendationSerializer, FavouriteSerializer
from api.models import User, Place, Review, Favourite
from django.contrib.auth import authenticate
from api.renderers import CustomRenderer
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.response import Response
from api.utils.main import main
# from api.utils.collaborative_filtering import recommend_places
import pandas as pd
from django_filters import rest_framework as filters
from django_filters.rest_framework import DjangoFilterBackend
from django.db import models
from rest_framework.filters import OrderingFilter
from pyspark.sql import SparkSession
from pyspark.ml.recommendation import ALS
from pyspark.ml.feature import StringIndexer
# from pyspark.ml.evaluation import RegressionEvaluator
from .models import Review, Place
from pyspark.ml.recommendation import ALSModel
import os
from pathlib import Path
from django.conf import settings



def get_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)

    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }


class UserRegistrationView(APIView):
    renderer_classes = [CustomRenderer]

    def post(self, request, format=None):
        serializer = UserRegistrationSerializer(data=request.data)

        if (serializer.is_valid(raise_exception=True)):
            user = serializer.save()
            token = get_tokens_for_user(user)
            return Response({'token': token, 'message': 'Registation Success!'}, status=status.HTTP_201_CREATED)

        return Response(serializer.error, status=status.HTTP_400_BAD_REQUEST)


class UserLoginView(APIView):
    renderer_classes = [CustomRenderer]

    def post(self, request, format=None):
        serializer = UserLoginSerializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            email = (serializer.data.get('email')).lower()
            password = serializer.data.get('password')
            user = authenticate(email=email, password=password)
            token = get_tokens_for_user(user)

            return Response({'token': token, 'message': 'Login Success!'}, status=status.HTTP_200_OK)
        
        return Response(serializer.error, status=status.HTTP_400_BAD_REQUEST)


class UserProfileView(APIView):
    renderer_classes = [CustomRenderer]
    permission_classes = [IsAuthenticated]

    def get(self, request, format=None):
        serializer = UserProfileSerializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)

    # def patch(self, request, format=None):
    #     current_user = User.objects.get(email=request.user.email)
    #     serializer = UpdateUserProfileSerializer(
    #         current_user, data=request.data, partial=True)
    #     if serializer.is_valid(raise_exception=True):
    #         serializer.save()
    #         return Response({'message': 'Profile has been updated!', 'name': request.data['name'], 'email': request.user.email}, status=status.HTTP_200_OK)
    
    def delete(self, request, format=None):
        User.objects.get(email=request.user.email).delete()
        return Response({'message': 'Account has been deleted!'},  status=status.HTTP_200_OK)
    
class PlaceFilter(filters.FilterSet):
    min_rating = filters.NumberFilter(field_name="rating", lookup_expr="gte")
    max_rating = filters.NumberFilter(field_name="rating", lookup_expr="lte")
    min_reviews = filters.NumberFilter(field_name="number_of_reviews", lookup_expr="gte")
    max_reviews = filters.NumberFilter(field_name="number_of_reviews", lookup_expr="lte")
    query = filters.CharFilter(method="filter_by_query")
    amenities = filters.CharFilter(method="filter_by_amenities")

    class Meta:
        model = Place
        fields = ["rating", "number_of_reviews", "name", "combined_amenities", "city", "place_type", "category", "subcategories"]
        filter_overrides = {
            models.ImageField: {
                "filter_class": filters.CharFilter,
            },
        }

    def filter_by_query(self, queryset, name, value):
        if not value:
            return queryset
        return queryset.filter(
            models.Q(name__icontains=value)
            | models.Q(city__icontains=value)
            | models.Q(subcategories__icontains=value)
        )

    def filter_by_amenities(self, queryset, name, value):
        if not value:
            return queryset
        amenities_list = [amenity.strip() for amenity in value.split(",") if amenity.strip()]
        for amenity in amenities_list:
            queryset = queryset.filter(amenities__icontains=amenity)
        return queryset  

class PlaceListCreateView(ListCreateAPIView):
    # renderer_classes = [CustomRenderer]
    serializer_class = PlaceSerializer
    queryset = Place.objects.all().order_by('-id')
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_class = PlaceFilter
    ordering_fields = ['number_of_reviews', 'rating', 'name']
    ordering = ['-number_of_reviews']


class PlaceRetrieveUpdateDestroyView(RetrieveUpdateDestroyAPIView):
    renderer_classes = [CustomRenderer]
    serializer_class = PlaceSerializer
    queryset = Place.objects.all().order_by('-id')

class FavouriteView(ListCreateAPIView):
    # renderer_classes = [CustomRenderer]
    queryset = Favourite.objects.all().order_by('-id')
    filterset_fields = ['user', 'place']
    filter_backends = [DjangoFilterBackend]

    def get_serializer(self, *args, **kwargs):
        if self.request.method == 'GET':
            kwargs['depth'] = 1
        elif self.request.method == 'POST':
            kwargs['depth'] = 0
        return FavouriteSerializer(*args, **kwargs)


class ReviewListView(ListCreateAPIView):
    renderer_classes = [CustomRenderer]
    serializer_class = ReviewSerializerForList
    queryset = Review.objects.all().order_by('-id')
    filterset_fields = ['user', 'place',]
    filter_backends = [DjangoFilterBackend] 

class ReviewCreateView(ListCreateAPIView):
    renderer_classes = [CustomRenderer]
    serializer_class = ReviewSerializerForCreate
    queryset = Review.objects.all().order_by('-id')
    filterset_fields = ['user', 'place',]
    filter_backends = [DjangoFilterBackend] 

class ReviewRetrieveUpdateDestroyView(RetrieveUpdateDestroyAPIView):
    renderer_classes = [CustomRenderer]
    serializer_class = ReviewSerializerForList
    queryset = Review.objects.all().order_by('-id')


llm = ChatGroq(model_name="mixtral-8x7b-32768", temperature=0.7, groq_api_key="YOUR_GROQ_API_KEY")

system_prompt = (
    "You are a professional assistant that provides concise, engaging, and recommendation-focused attraction descriptions."
)
human_prompt = (
    "{name} in {city}, located at {address}, is highly recommended for its subcategory of {subcategories}. "
    "With a rating of {rating}/5.0 and ranked {ranking}, it stands out as a must-visit destination. {description} "
    "This attraction is praised for its unique features, making it an excellent option for travelers."
)
prompt = ChatPromptTemplate.from_messages([("system", system_prompt), ("human", human_prompt)])


class UserProfileView(APIView):
    renderer_classes = [CustomRenderer]
    permission_classes = [IsAuthenticated]

    def get(self, request, format=None):
        serializer = UserProfileSerializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)

class RecommendationView(APIView):
    def get(self, request):
        title = request.query_params.get("query", "Best hotels")
        amenities = request.query_params.get("amenities", "")
        city = request.query_params.get("city", "karachi")
        subcategories = request.query_params.get("subcategories", "Hotel")
        place_type = request.query_params.get("type", "")
        related = request.query_params.get("related", False)
        queryset = Place.objects.filter(place_type=place_type) if place_type not in ["all", ""] else Place.objects.all()

        df = pd.DataFrame(list(queryset.values()))
        description, results = main(df, title, amenities, city, subcategories, place_type, related)
        results = results.to_dict(orient='records') if not results.empty else []

        description_with_title = [
            {'title': results[index]['name'], 'description': description[index]} for element, index in enumerate(range(len(description)))
        ]
        print(description_with_title)

        # print(description)
        return Response({
            'description': description_with_title, 
            'results': results
        })



# Initialize Spark session
# class CollaborativeRecommendationView(APIView):
#     """
#     API endpoint to generate collaborative filtering recommendations for a specific user.
#     """

#     def get(self, request, user_id, *args, **kwargs):
#         try:
#             # Check if the user exists
#             if not User.objects.filter(id=user_id).exists():
#                 return Response({"error": "User not found."}, status=404)

#             # Initialize Spark session
#             spark = SparkSession.builder.master("local[*]").appName("CollaborativeFiltering").getOrCreate()

#             # Load review data
#             reviews = Review.objects.select_related("user", "place").values(
#                 "user__id", "place__id", "place__name", "rating"
#             )
#             df = pd.DataFrame(reviews)

#             # Check if review data is available
#             if df.empty:
#                 return Response({"message": "No reviews available to generate recommendations."}, status=200)

#             # Rename columns to match expected schema
#             df.columns = ["user_id", "place_id", "place_name", "rating"]

#             # Convert Pandas DataFrame to Spark DataFrame
#             spark_df = spark.createDataFrame(df)

#             # Index user IDs and place names to numerical IDs
#             user_indexer = StringIndexer(inputCol="user_id", outputCol="user_index").fit(spark_df)
#             place_indexer = StringIndexer(inputCol="place_name", outputCol="place_index").fit(spark_df)

#             spark_df = user_indexer.transform(spark_df)
#             spark_df = place_indexer.transform(spark_df)

#             # Train the ALS model
#             als = ALS(
#                 userCol="user_index",
#                 itemCol="place_index",
#                 ratingCol="rating",
#                 nonnegative=True,
#                 coldStartStrategy="drop",
#             )
#             als_model = als.fit(spark_df)

#             # Map user_id to user_index
#             user_mapping = (
#                 spark_df.select("user_id", "user_index")
#                 .distinct()
#                 .toPandas()
#                 .set_index("user_id")["user_index"]
#                 .to_dict()
#             )

#             if user_id not in user_mapping:
#                 return Response(
#                     {"message": f"No sufficient data to generate recommendations for user_id={user_id}."},
#                     status=200,
#                 )

#             user_index = user_mapping[user_id]

#             # Generate recommendations for the user
#             user_recs = als_model.recommendForUserSubset(
#                 spark_df.filter(spark_df.user_index == user_index), 5
#             ).toPandas()

#             if user_recs.empty:
#                 return Response(
#                     {"message": f"No recommendations found for user_id={user_id}."},
#                     status=200,
#                 )

#             # Process recommendations
#             user_recs["recommendations"] = user_recs["recommendations"].apply(
#                 lambda recs: [{"place_index": rec[0], "rating": rec[1]} for rec in recs]
#             )

#             # Map place indices to place details
#             place_mapping = (
#                 spark_df.select("place_index", "place_id")
#                 .distinct()
#                 .toPandas()
#                 .set_index("place_index")["place_id"]
#                 .to_dict()
#             )

#             recommendations = []
#             for rec in user_recs["recommendations"].iloc[0]:
#                 place_id = place_mapping.get(rec["place_index"])
#                 if place_id:
#                     # Fetch full place details from the database
#                     place = Place.objects.filter(id=place_id).values().first()
#                     if place:
#                         # place["rating"] = rec["rating"]  # Append recommendation rating
#                         recommendations.append(place)

#             # Prepare response
#             response_data = {
#                 "user_id": user_id,
#                 "recommendations": recommendations,
#             }

#             return Response(response_data, status=200)

#         except Exception as e:
#             return Response({"error": str(e)}, status=500)


# class CollaborativeRecommendationView(APIView):
#     """
#     Optimized API endpoint to generate collaborative filtering recommendations for a specific user.
#     """

#     def get(self, request, user_id, *args, **kwargs):
#         try:
#             # Check if the user exists
#             if not User.objects.filter(id=user_id).exists():
#                 return Response({"error": "User not found."}, status=404)

#             # Load review data
#             reviews = Review.objects.select_related("user", "place").values(
#                 "user__id", "place__id", "rating"
#             )

#             df = pd.DataFrame(reviews)

#             # Check if review data is available
#             if df.empty:
#                 return Response({"message": "No reviews available to generate recommendations."}, status=200)

#             # Initialize Spark session
#             spark = SparkSession.builder.master("local[*]").appName("CollaborativeFiltering").getOrCreate()

#             # Convert Pandas DataFrame to Spark DataFrame
#             spark_df = spark.createDataFrame(df)

#             # Index user IDs and place IDs to numerical IDs
#             user_indexer = StringIndexer(inputCol="user__id", outputCol="user_index").fit(spark_df)
#             place_indexer = StringIndexer(inputCol="place__id", outputCol="place_index").fit(spark_df)

#             spark_df = user_indexer.transform(spark_df)
#             spark_df = place_indexer.transform(spark_df)

#             # Train the ALS model
#             als = ALS(
#                 userCol="user_index",
#                 itemCol="place_index",
#                 ratingCol="rating",
#                 nonnegative=True,
#                 coldStartStrategy="drop",
#             )
#             als_model = als.fit(spark_df)

#             # Map user_id to user_index
#             user_mapping = (
#                 spark_df.select("user__id", "user_index")
#                 .distinct()
#                 .toPandas()
#                 .set_index("user__id")["user_index"]
#                 .to_dict()
#             )

#             if user_id not in user_mapping:
#                 return Response(
#                     {"message": f"No sufficient data to generate recommendations for user_id={user_id}."},
#                     status=200,
#                 )

#             user_index = user_mapping[user_id]

#             # Generate recommendations for the user
#             user_recs = als_model.recommendForUserSubset(
#                 spark_df.filter(spark_df.user_index == user_index), 5
#             ).toPandas()

#             if user_recs.empty:
#                 return Response(
#                     {"message": f"No recommendations found for user_id={user_id}."},
#                     status=200,
#                 )

#             # Extract recommended place indices
#             user_recs["recommendations"] = user_recs["recommendations"].apply(
#                 lambda recs: [{"place_index": rec[0], "rating": rec[1]} for rec in recs]
#             )
#             place_indices = [rec["place_index"] for rec in user_recs["recommendations"].iloc[0]]

#             # Map place indices to place IDs
#             place_mapping = (
#                 spark_df.select("place_index", "place__id")
#                 .distinct()
#                 .toPandas()
#                 .set_index("place_index")["place__id"]
#                 .to_dict()
#             )

#             # Fetch all recommended place details in a single query
#             place_ids = [place_mapping.get(index) for index in place_indices]
#             places = Place.objects.filter(id__in=place_ids).values()

#             # Create a dictionary for fast lookup of place details
#             places_dict = {place["id"]: place for place in places}

#             # Prepare recommendations
#             recommendations = []
#             for rec in user_recs["recommendations"].iloc[0]:
#                 place_id = place_mapping.get(rec["place_index"])
#                 if place_id and place_id in places_dict:
#                     place = places_dict[place_id]
#                     # Append recommendation rating
#                     place["rating"] = rec["rating"]
#                     recommendations.append(place)

#             # Prepare response
#             response_data = {
#                 "user_id": user_id,
#                 "recommendations": recommendations,
#             }

#             return Response(response_data, status=200)

#         except Exception as e:
#             return Response({"error": str(e)}, status=500)


class CollaborativeRecommendationView(APIView):
    """
    Optimized API endpoint with model persistence for collaborative filtering recommendations.
    """

    MODEL_PATH = str(Path(settings.BASE_DIR) / "models" / "als_model")
    print(MODEL_PATH,'MODEL_PATH')

    def get(self, request, user_id, *args, **kwargs):
        try:
            # Check if the user exists
            if not User.objects.filter(id=user_id).exists():
                return Response({"error": "User not found."}, status=404)

            # Load review data
            reviews = Review.objects.select_related("user", "place").values(
                "user__id", "place__id", "rating"
            )
            df = pd.DataFrame(reviews)

            # Check if review data is available
            if df.empty:
                return Response({"message": "No reviews available to generate recommendations."}, status=200)

            # Initialize Spark session
            spark = SparkSession.builder.master("local[*]").appName("CollaborativeFiltering").getOrCreate()

            # Convert Pandas DataFrame to Spark DataFrame
            spark_df = spark.createDataFrame(df)

            # Index user IDs and place IDs to numerical IDs
            user_indexer = StringIndexer(inputCol="user__id", outputCol="user_index").fit(spark_df)
            place_indexer = StringIndexer(inputCol="place__id", outputCol="place_index").fit(spark_df)

            spark_df = user_indexer.transform(spark_df)
            spark_df = place_indexer.transform(spark_df)

            # Check if the model exists
            if os.path.exists(self.MODEL_PATH):
                # Load the existing ALS model
                als_model = ALSModel.load(self.MODEL_PATH)
            else:
                # Train a new ALS model
                als = ALS(
                    userCol="user_index",
                    itemCol="place_index",
                    ratingCol="rating",
                    nonnegative=True,
                    coldStartStrategy="drop",
                )
                als_model = als.fit(spark_df)

                # Save the model for future use
                als_model.save(self.MODEL_PATH)

            # Map user_id to user_index
            user_mapping = (
                spark_df.select("user__id", "user_index")
                .distinct()
                .toPandas()
                .set_index("user__id")["user_index"]
                .to_dict()
            )

            if user_id not in user_mapping:
                return Response(
                    {"message": f"No sufficient data to generate recommendations for user_id={user_id}."},
                    status=200,
                )

            user_index = user_mapping[user_id]

            # Generate recommendations for the user
            user_recs = als_model.recommendForUserSubset(
                spark_df.filter(spark_df.user_index == user_index), 10
            ).toPandas()

            if user_recs.empty:
                return Response(
                    {"message": f"No recommendations found for user_id={user_id}."},
                    status=200,
                )

            # Extract recommended place indices
            user_recs["recommendations"] = user_recs["recommendations"].apply(
                lambda recs: [{"place_index": rec[0], "rating": rec[1]} for rec in recs]
            )
            place_indices = [rec["place_index"] for rec in user_recs["recommendations"].iloc[0]]

            # Map place indices to place IDs
            place_mapping = (
                spark_df.select("place_index", "place__id")
                .distinct()
                .toPandas()
                .set_index("place_index")["place__id"]
                .to_dict()
            )

            # Fetch all recommended place details in a single query
            place_ids = [place_mapping.get(index) for index in place_indices]
            places = Place.objects.filter(id__in=place_ids).values()

            # Create a dictionary for fast lookup of place details
            places_dict = {place["id"]: place for place in places}

            # Prepare recommendations
            recommendations = []
            for rec in user_recs["recommendations"].iloc[0]:
                place_id = place_mapping.get(rec["place_index"])
                if place_id and place_id in places_dict:
                    place = places_dict[place_id]
                    # Append recommendation rating
                    # place["rating"] = rec["rating"]
                    recommendations.append(place)

            # Prepare response
            response_data = {
                "user_id": user_id,
                "results": recommendations,
            }

            return Response(response_data, status=200)

        except Exception as e:
            return Response({"error": str(e)}, status=500)