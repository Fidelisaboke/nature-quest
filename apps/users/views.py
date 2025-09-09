from rest_framework.decorators import api_view
from apps.common.responses.api_responses import api_response
from .serializers import UserRegistrationSerializer, LoginObtainPairSerializer
from drf_spectacular.utils import extend_schema
from .docs import (
    user_register_schema_args,
    user_login_schema_args,
    token_refresh_schema_args,
)
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView


@extend_schema(**user_register_schema_args, tags=["auth"])
@api_view(["POST"])
def register_user(request):
    """Register a new user and return authentication tokens."""
    user_serializer = UserRegistrationSerializer(data=request.data)
    if user_serializer.is_valid():
        user = user_serializer.save()
        refresh = RefreshToken.for_user(user)
        data = {
            "refresh": str(refresh),
            "access": str(refresh.access_token),
            "results": user_serializer.data,
        }
        return api_response(
            True, "User registered successfully", data=data, status_code=201
        )
    return api_response(
        False, "Validation error", errors=user_serializer.errors, status_code=400
    )


class LoginObtainPairView(TokenObtainPairView):
    """Custom token obtain view with API documentation."""

    serializer_class = LoginObtainPairSerializer

    @extend_schema(**user_login_schema_args, tags=["auth"])
    def post(self, request, *args, **kwargs):
        """Authenticate user and return JWT tokens."""
        response = super().post(request, *args, **kwargs)
        if response.status_code == 200:
            return api_response(
                True, "Login successful", data=response.data, status_code=200
            )
        return response


class LoginRefreshView(TokenRefreshView):
    """Custom token refresh view with API documentation."""

    @extend_schema(**token_refresh_schema_args, tags=["auth"])
    def post(self, request, *args, **kwargs):
        """Refresh access token using refresh token."""
        response = super().post(request, *args, **kwargs)
        if response.status_code == 200:
            return api_response(
                True,
                "Token refreshed successfully",
                data=response.data,
                status_code=200,
            )
        return response
