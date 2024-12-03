from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
from api import serializers, models
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

def get_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)

    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }


class UserRegistrationView(APIView):
    renderer_classes = [CustomRenderer]

    def post(self, request, format=None):
        serializer = serializers.UserRegistrationSerializer(data=request.data)

        if (serializer.is_valid(raise_exception=True)):
            user = serializer.save()
            token = get_tokens_for_user(user)
            return Response({'token': token, 'message': 'Registation Success!'}, status=status.HTTP_201_CREATED)

        return Response(serializers.error, status=status.HTTP_400_BAD_REQUEST)


class UserLoginView(APIView):
    renderer_classes = [CustomRenderer]

    def post(self, request, format=None):
        serializer = serializers.UserLoginSerializer(data=request.data)
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
        serializer = serializers.UserProfileSerializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def patch(self, request, format=None):
        current_user = models.User.objects.get(email=request.user.email)
        serializer = serializers.UpdateUserProfileSerializer(
            current_user, data=request.data, partial=True)
        if serializer.is_valid(raise_exception=True):
            serializer.save()
            return Response({'message': 'Profile has been updated!', 'name': request.data['name'], 'email': request.user.email}, status=status.HTTP_200_OK)
    
    def delete(self, request, format=None):
        models.User.objects.get(email=request.user.email).delete()
        return Response({'message': 'Account has been deleted!'},  status=status.HTTP_200_OK)


class PlaceListCreateView(ListCreateAPIView):
    renderer_classes = [CustomRenderer]
    serializer_class = serializers.PlaceSerializer
    queryset = models.Place.objects.all().order_by('-id')
    pagination_class = PageNumberPagination


class PlaceRetrieveUpdateDestroyView(RetrieveUpdateDestroyAPIView):
    renderer_classes = [CustomRenderer]
    serializer_class = serializers.PlaceSerializer
    queryset = models.Place.objects.all().order_by('-id')

    
class ReviewListCreateView(ListCreateAPIView):
    renderer_classes = [CustomRenderer]
    serializer_class = serializers.ReviewSerializer
    queryset = models.Review.objects.all().order_by('-id')
    pagination_class = PageNumberPagination

class ReviewRetrieveUpdateDestroyView(RetrieveUpdateDestroyAPIView):
    renderer_classes = [CustomRenderer]
    serializer_class = serializers.ReviewSerializer
    queryset = models.Review.objects.all().order_by('-id')

class CustomPagePagination(pagination.PageNumberPagination):
    page_size = 40
    page_size_query_param = 'pagesize'
    max_page_size = 80



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
        serializer = serializers.UserProfileSerializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)

class RecommendAttractionsView(APIView):
    def get(self, request):
        title = request.query_params.get("title", "Best hotels")
        amenities = request.query_params.get("amenities", "")
        city = request.query_params.get("city", "karachi")
        subcategories = request.query_params.get("subcategories", "Hotel")
        place_type = request.query_params.get("place_type", "all")

        queryset = models.Place.objects.all()
        if place_type != "all":
            queryset =  models.Place.objects.filter(place_type=place_type)

        print(title, city, subcategories)
    
        df = pd.DataFrame(list(queryset.values()))
        recommendations = main(df, title, amenities, city, subcategories, place_type)
        
        return Response({'results': recommendations})
