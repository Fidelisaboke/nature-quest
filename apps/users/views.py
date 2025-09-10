from rest_framework.decorators import api_view,permission_classes
from apps.common.responses.api_responses import api_response
from .serializers import UserRegistrationSerializer, LoginObtainPairSerializer,UserProfileSerializer
from drf_spectacular.utils import extend_schema
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser
from .docs import (
    user_register_schema_args,
    user_login_schema_args,
    token_refresh_schema_args,
    user_profile_schema_args,
)
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .models import UserProfile

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
@extend_schema(**user_profile_schema_args, tags=["profile"])
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_user_profile(request):
    """
    Retrieve the authenticated user's profile.
    Automatically creates profile if it doesn't exist.
    """
    try:
        # Get or create user profile (creates with default values if not exists)
        profile, created = UserProfile.objects.get_or_create(user=request.user)
        
        serializer = UserProfileSerializer(profile)
        
        message = "Profile retrieved successfully"
        if created:
            message = "Profile created and retrieved successfully"
        
        return api_response(
            True, 
            message, 
            data=serializer.data, 
            status_code=200
        )
    
    except Exception as e:
        # Log the actual error for debugging
        print(f"Error in get_user_profile: {str(e)}")
        import traceback
        traceback.print_exc()
        
        return api_response(
            False,
            "An internal server error occurred",
            errors={"detail": str(e)},  # Include the actual error message
            status_code=500
        )