# serializers for the users app

from .models import RegisterUser
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
        """Create a new user with encrypted password."""
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
