from django.core.mail import send_mail
from rest_framework.decorators import api_view,permission_classes
from apps.common.responses.api_responses import api_response
from .serializers import PasswordResetConfirmSerializer, PasswordResetSerializer, UserRegistrationSerializer, LoginObtainPairSerializer,UserProfileSerializer
from drf_spectacular.utils import extend_schema
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.permissions import AllowAny
from rest_framework.parsers import MultiPartParser, FormParser
from .docs import (
    user_register_schema_args,
    user_login_schema_args,
    token_refresh_schema_args,
    user_profile_schema_args,
)
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .models import RegisterUser, UserProfile

@extend_schema(
    summary="Initiate the password reset process",
    tags=["auth"],
    description="Send a password reset email to the user's registered email address.",
    request=PasswordResetSerializer,
    responses={200: "Password reset email sent successfully", 404: "User not found", 400: "Bad request", 500: "Internal Server Error"},
)
@api_view(["POST"])
@permission_classes([AllowAny])
def password_reset_request(request):
    """Initiate the password reset process."""
    serializer = PasswordResetSerializer(data=request.data)
    if serializer.is_valid():
        email = serializer.validated_data['email']

        try:
            user = RegisterUser.objects.get(email=email)

            # Generate a password reset token
            token = user.generate_password_reset_token()
            uid = user.id
            # TODO: Send the email with the reset link
            send_password_reset_email(user, token, uid)
        except RegisterUser.DoesNotExist:
            return api_response(
                False, "User not found", status_code=404
            )

@api_view(["POST"])
@permission_classes([AllowAny])
@extend_schema(
    summary="Confirm the password reset",
    tags=["auth"],
    request=PasswordResetConfirmSerializer,
    responses={200: "Password reset successfully", 400: "Bad request", 500: "Internal Server Error"},
)
def password_reset_confirm(request):
    """Confirm the password reset."""
    serializer = PasswordResetConfirmSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        return api_response(
            True, "Password reset successfully", status_code=200
        )
    return api_response(
        False, "Validation error", errors=serializer.errors, status_code=400
    )

def send_password_reset_email(user, token, uid):
    """Send a password reset email to the user."""
    subject = "Nature Quest - Password Reset"
    message = f"""
    Hello {user.first_name},
    You requested to reset your password. Please click the link below to set a new password:
    http://example.com/reset-password/{uid}/{token}

    This link will expire in 1 hour. If you did not request a password reset, please ignore this email.

    Best regards,
    The Nature Quest Team
    """

    send_mail(subject, message, "from_email@example.com", [user.email], fail_silently=False)
    return api_response(
        True, "Password reset email sent successfully", status_code=200
    )

@extend_schema(**user_register_schema_args, tags=["auth"])
@api_view(["POST"])
@permission_classes([AllowAny])
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
    """Custom token gets view with API documentation."""

    serializer_class = LoginObtainPairSerializer

    @extend_schema(**user_login_schema_args, tags=["auth"])
    def post(self, request, *args, **kwargs):
        """Authenticate the user and return JWT tokens."""
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
    Automatically creates a profile if it doesn't exist.
    """
    try:
        # Get or create a user profile (creates with default values if not exists)
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