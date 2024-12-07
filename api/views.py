from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
from api.serializers import UserSerializer, UserRegistrationSerializer, UserLoginSerializer, UserProfileSerializer, PlaceSerializer, ReviewSerializerForList, ReviewSerializerForCreate, RecommendationSerializer
from api.models import User, Place, Review
from django.contrib.auth import authenticate
from api.renderers import CustomRenderer
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import IsAuthenticated
from rest_framework import pagination
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.response import Response
from api.utils.main import main
from api.utils.collaborative_filtering import recommend_places
import pandas as pd
from django_filters import rest_framework as filters
from django_filters.rest_framework import DjangoFilterBackend
from django.db import models
from rest_framework.filters import OrderingFilter
from pyspark.sql import SparkSession
from pyspark.ml.recommendation import ALS
from pyspark.ml.evaluation import RegressionEvaluator
from pyspark.sql.functions import col, explode
from pyspark.ml.feature import StringIndexer



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
        # print(description)
        return Response({
            'description': description, 
            'results': results.to_dict(orient='records') if not results.empty else []
        })




# class CollabrativeRecommendationView(APIView):
#     # def get(self, request):
#     #     user = request.query_params.get("user", "")
#     #     try:
#     #         if user:
#     #             user = User.objects.get(id=user) 
#     #             recommended_places = recommend_places(user, Review, Place)

#     #             serializer = PlaceSerializer(recommended_places, many=True)
#     #             return Response({"results": serializer.data })
#     #         else:
#     #             return Response({"results": [] })
            
#     #     except: 
#     #         return Response({"results": [] })
#     def post(self, request, *args, **kwargs):
#         user = request.data.get('user')

#         if not user:
#             return Response({"error": "user is required"}, status=status.HTTP_400_BAD_REQUEST)

#         reviews = Review.objects.all().values('user', 'place', 'rating')

#         df = pd.DataFrame(reviews)

#         spark_df = spark.createDataFrame(df[['user', 'place', 'rating']])

#         user_indexer = StringIndexer(inputCol="user", outputCol="user_index")
#         place_indexer = StringIndexer(inputCol="place", outputCol="place_index")

#         spark_df = user_indexer.fit(spark_df).transform(spark_df)
#         spark_df = place_indexer.fit(spark_df).transform(spark_df)

#         als = ALS(userCol="user_index", itemCol="place_index", ratingCol="rating", nonnegative=True, coldStartStrategy="drop")
#         als_model = als.fit(spark_df)

#         predictions = als_model.transform(spark_df)

#         user_recs = als_model.recommendForUserSubset(spark_df.filter(spark_df.user_index == user), 5)

#         user_recs = user_recs.withColumn("recommendations", explode("recommendations"))
#         user_recs = user_recs.withColumn("place_index", col("recommendations.place_index"))
#         user_recs = user_recs.withColumn("predicted_rating", col("recommendations.rating"))

#         user_recs = user_recs.join(spark_df.select("place_index", "place").dropDuplicates(), on="place_index", how="left")

#         recommended_places = user_recs.select("place", "predicted_rating").collect()

#         places = Place.objects.filter(id__in=[place.place for place in recommended_places])
#         place_data = [{"name": place.name, "address": place.address, "predicted_rating": place.predicted_rating} for place in places]

#         return Response(place_data, status=status.HTTP_200_OK)


class CollabrativeRecommendationView(APIView):

    def get(self, request, user_id):
        # Initialize Spark session
        spark = SparkSession.builder.appName("CollaborativeFiltering").getOrCreate()

        # Fetch data from the Review model
        reviews = Review.objects.select_related('user', 'place').all().values(
            'user__id', 'place__id', 'rating'
        )
        if not reviews:
            return Response({"error": "No reviews found"}, status=status.HTTP_400_BAD_REQUEST)

        # Convert the data to a Pandas DataFrame
        df = pd.DataFrame(list(reviews))
        df.rename(columns={'user__id': 'user', 'place__id': 'place', 'rating': 'predicted_rating'}, inplace=True)

        # Convert the Pandas DataFrame to a Spark DataFrame
        spark_df = spark.createDataFrame(df)

        # Encode user and place IDs to integer IDs for Spark
        user_indexer = StringIndexer(inputCol="user", outputCol="user_id")
        place_indexer = StringIndexer(inputCol="place", outputCol="place_id")

        spark_df = user_indexer.fit(spark_df).transform(spark_df)
        spark_df = place_indexer.fit(spark_df).transform(spark_df)

        # Build ALS model
        als = ALS(userCol="user_id", itemCol="place_id", ratingCol="predicted_rating", nonnegative=True, coldStartStrategy="drop")
        als_model = als.fit(spark_df)

        # Make predictions
        predictions = als_model.transform(spark_df)

        # Evaluate the model
        evaluator = RegressionEvaluator(metricName="rmse", labelCol="predicted_rating", predictionCol="prediction")
        rmse = evaluator.evaluate(predictions)
        print("Root Mean Squared Error (RMSE) for Collaborative Filtering: ", rmse)

        # Generate recommendations for all users
        user_recs = als_model.recommendForAllUsers(5)  # Top 5 recommendations for each user

        # Filter recommendations for the specific user
        user_index = spark_df.filter(col("user") == user_id).select("user_id").distinct().collect()
        if not user_index:
            return Response({"error": "User ID not found in the dataset"}, status=status.HTTP_404_NOT_FOUND)

        user_id_encoded = user_index[0]["user_id"]
        user_recs = user_recs.filter(col("user_id") == user_id_encoded)

        if user_recs.count() == 0:
            return Response({"error": "No recommendations found for this user"}, status=status.HTTP_404_NOT_FOUND)

        # Process recommendations
        user_recs = user_recs.withColumn("recommendations", explode("recommendations"))
        user_recs = user_recs.withColumn("place_id", col("recommendations.place_id"))
        user_recs = user_recs.withColumn("predicted_rating", col("recommendations.rating"))

        # Join with original data to get place names
        user_recs = user_recs.join(
            spark_df.select("place_id", "place").dropDuplicates(),
            on="place_id",
            how="left"
        )

        # Convert the results to a Pandas DataFrame
        recommendations = user_recs.select("place", "predicted_rating").toPandas()

        # Convert to a response-friendly format
        recommendation_list = recommendations.to_dict(orient="records")

        return Response(recommendation_list, status=status.HTTP_200_OK)
        # return Response({}, status=status.HTTP_200_OK)
    
