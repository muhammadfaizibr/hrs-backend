from django.urls import path, include
from api import views
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView, TokenVerifyView
from django.conf.urls.static import static
from django.conf import settings
from api.views import PlaceListCreateView, PlaceRetrieveUpdateDestroyView, ReviewListCreateView, ReviewRetrieveUpdateDestroyView, RecommendAttractionsView

router = DefaultRouter()



urlpatterns = [
    path('recommendations/', RecommendAttractionsView.as_view(), name='recommendations'),
    path('place-list-create/', PlaceListCreateView.as_view()),
    path('place-retrieve-update-destroy/<int:pk>', PlaceRetrieveUpdateDestroyView.as_view()),
    path('review-list-create/', ReviewListCreateView.as_view()),
    path('review-retrieve-update-destroy/<int:pk>', ReviewRetrieveUpdateDestroyView.as_view()),
    path('user/register/', views.UserRegistrationView.as_view()),
    path('user/login/', views.UserLoginView.as_view()),
    path('user/profile/', views.UserProfileView.as_view()),
    path('auth/', include('rest_framework.urls')),
    path('token/', TokenObtainPairView.as_view()),
    path('token/refresh/', TokenRefreshView.as_view()),
    path('token/verify/', TokenVerifyView.as_view()),
    path('', include(router.urls))
] + static(settings.MEDIA_URL, document_root= settings.MEDIA_ROOT)
