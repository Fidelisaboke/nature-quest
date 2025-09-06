from django.urls import path
from .views import registerUser
from rest_framework_simplejwt.views import TokenObtainPairView,TokenRefreshView

urlpatterns = [
    path('auth/register/',registerUser,name='register_user'),
    path('auth/login/',TokenObtainPairView.as_view(),name='token_obtain_pair'),
    path('auth/token/refresh/',TokenRefreshView.as_view(),name='token_refresh'),
]