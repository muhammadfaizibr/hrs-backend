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
        current_user = models.User.objects.get(email=request.user.email).delete()
        return Response({'message': 'Account has been deleted!'},  status=status.HTTP_200_OK)


class PlaceListCreateView(ListCreateAPIView):
    renderer_classes = [CustomRenderer]
    serializer_class = serializersPlaceSerializer
    queryset = modelsPlace.objects.all().order_by('-id')
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

