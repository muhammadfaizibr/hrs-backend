from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
from api.serializers import UserSerializer, UserRegistrationSerializer, UserLoginSerializer, UserProfileSerializer, PlaceSerializer, ReviewSerializer, RecommendationSerializer
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
import pandas as pd
from django_filters import rest_framework as filters
from django_filters.rest_framework import DjangoFilterBackend
from django.db import models

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

        return Response(serializers.error, status=status.HTTP_400_BAD_REQUEST)


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
        
        return Response(serializers.error, status=status.HTTP_400_BAD_REQUEST)


class UserProfileView(APIView):
    renderer_classes = [CustomRenderer]
    permission_classes = [IsAuthenticated]

    def get(self, request, format=None):
        serializer = UserProfileSerializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def patch(self, request, format=None):
        current_user = User.objects.get(email=request.user.email)
        serializer = UpdateUserProfileSerializer(
            current_user, data=request.data, partial=True)
        if serializer.is_valid(raise_exception=True):
            serializer.save()
            return Response({'message': 'Profile has been updated!', 'name': request.data['name'], 'email': request.user.email}, status=status.HTTP_200_OK)
    
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
        fields = ["rating", "number_of_reviews", "name", "amenities", "city",]
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
    filter_backends = [DjangoFilterBackend]
    filterset_class = PlaceFilter

class PlaceRetrieveUpdateDestroyView(RetrieveUpdateDestroyAPIView):
    renderer_classes = [CustomRenderer]
    serializer_class = PlaceSerializer
    queryset = Place.objects.all().order_by('-id')

    
class ReviewListCreateView(ListCreateAPIView):
    renderer_classes = [CustomRenderer]
    serializer_class = ReviewSerializer
    queryset = Review.objects.all().order_by('-id')
    pagination_class = PageNumberPagination
    filterset_fields = ['user', 'place']

class ReviewRetrieveUpdateDestroyView(RetrieveUpdateDestroyAPIView):
    renderer_classes = [CustomRenderer]
    serializer_class = ReviewSerializer
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
        title = request.query_params.get("title", "Best hotels")
        amenities = request.query_params.get("amenities", "")
        city = request.query_params.get("city", "karachi")
        subcategories = request.query_params.get("subcategories", "Hotel")
        place_type = request.query_params.get("place_type", "all")

        queryset = Place.objects.all()
        if place_type != "all":
            queryset =  Place.objects.filter(place_type=place_type)

    
        df = pd.DataFrame(list(queryset.values()))
        recommendations = main(df, title, amenities, city, subcategories, place_type)
        
        return Response({'results': recommendations})
