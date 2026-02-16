# serializers for the users app

from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_decode
from .models import RegisterUser,UserProfile
import re
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from rest_framework_simplejwt.serializers import (
    TokenObtainPairSerializer,
    TokenRefreshSerializer,
)


class UserRegistrationSerializer(serializers.ModelSerializer):
    """Serializer for the RegisterUser model."""

    password = serializers.CharField(
        write_only=True, required=True, validators=[validate_password]
    )

    class Meta:
        model = RegisterUser
        fields = "__all__"
        extra_kwargs = {"password": {"write_only": True}, "email": {"required": True}}

    def validate_email(self, value):
        """Validate email format and uniqueness."""
        email_regex = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        if not re.match(email_regex, value):
            raise serializers.ValidationError("Invalid email format")

        if RegisterUser.objects.filter(email=value).exists():
            raise serializers.ValidationError("Email is already in use")
        return value

    def create(self, validated_data):
        """Create a new user with an encrypted password."""
        user = RegisterUser.objects.create_user(
            email=validated_data["email"],
            password=validated_data["password"],
            username=validated_data.get("username"),
            first_name=validated_data.get("first_name", ""),
            last_name=validated_data.get("last_name", ""),
            interests=validated_data.get("interests", ""),
        )
        return user


class LoginObtainPairSerializer(TokenObtainPairSerializer):
    """Custom token serializer to include additional user info in the token response."""

    pass


class LoginRefreshSerializer(TokenRefreshSerializer):
    """Custom token refresh serializer to include a message in the response."""

    def validate(self, attrs):
        """Validate and refresh the token, adding a custom message."""
        data = super().validate(attrs)
        data["message"] = "Token refreshed successfully"
        return data

class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer for the UserProfile model."""
    display_name = serializers.CharField(source='user.username', read_only=True)
    class Meta:
        model = UserProfile
        fields = ['profile_pic','bio', 'display_name', 'points', 'level']
        read_only_fields = ['points', 'level']

class PasswordResetSerializer(serializers.Serializer):
    """Serializer for password reset functionality."""
    email = serializers.EmailField(required=True, help_text='Email associated with your account')

    def validate_email(self, value):
        """Validate that the email exists in the database."""
        try:
            user = RegisterUser.objects.get(email=value)
            if not user.is_active:
                raise serializers.ValidationError("User is not active")
        except RegisterUser.DoesNotExist:
            raise serializers.ValidationError("Email does not exist")
        return value

class PasswordResetConfirmSerializer(serializers.Serializer):
    """Serializer for password reset confirmation functionality."""
    uid = serializers.CharField(required=True)
    token = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True, write_only=True, validators=[validate_password])
    confirm_password = serializers.CharField(required=True, write_only=True, validators=[validate_password])

    def validate(self, attrs):
        if attrs['new_password'] != attrs['confirm_password']:
            raise serializers.ValidationError("Passwords do not match")

        # Validate the reset link
        try:
            uid = force_str(urlsafe_base64_decode(attrs['uid']))
            user = RegisterUser.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, RegisterUser.DoesNotExist):
            raise serializers.ValidationError("Invalid reset link")
        
        if not user.check_password_reset_token(attrs['token']):
            raise serializers.ValidationError("Invalid or expired reset link")

        attrs['user'] = user
        return attrs

    def save(self, **kwargs):
        """Save the new password for the user."""
        user = self.validated_data['user']
        user.set_password(self.validated_data['new_password'])
        user.save()
        return user
