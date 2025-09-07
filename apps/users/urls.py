from django.urls import path
from .views import registerUser
from rest_framework_simplejwt.views import TokenObtainPairView,TokenRefreshView

urlpatterns = [
    path('auth/register/',registerUser,name='register'),
    path('auth/login/',TokenObtainPairView.as_view(),name='login'),
    path('auth/token/refresh/',TokenRefreshView.as_view(),name='token_refresh'),
]