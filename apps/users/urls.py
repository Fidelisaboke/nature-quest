from django.urls import path
from .views import register_user, LoginObtainPairView, LoginRefreshView,get_user_profile, password_reset_request, password_reset_confirm

urlpatterns = [
    path("auth/register/", register_user, name="register"),
    path("auth/login/", LoginObtainPairView.as_view(), name="login"),
    path("auth/token/refresh/", LoginRefreshView.as_view(), name="token_refresh"),
    path("auth/password_reset/", password_reset_request, name="password_reset"),
    path("auth/password_reset_confirm/<uid>/<int:token>/", password_reset_confirm, name="password_reset_confirm"),
    
    path("auth/me/",get_user_profile,name="profile")
]
