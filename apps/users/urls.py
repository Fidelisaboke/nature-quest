from django.urls import path
from .views import register_user, LoginObtainPairView, LoginRefreshView,get_user_profile

urlpatterns = [
    path("auth/register/", register_user, name="register"),
    path("auth/login/", LoginObtainPairView.as_view(), name="login"),
    path("auth/token/refresh/", LoginRefreshView.as_view(), name="token_refresh"),
    path("auth/me/",get_user_profile,name="profile")
]
