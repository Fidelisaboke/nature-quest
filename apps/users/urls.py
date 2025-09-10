from django.urls import path
from .views import register_user, LoginObtainPairView, LoginRefreshView

urlpatterns = [
    path("auth/register/", register_user, name="register"),
    path("auth/login/", LoginObtainPairView.as_view(), name="login"),
    path("auth/token/refresh/", LoginRefreshView.as_view(), name="token_refresh"),
]
