from .models import RegisterUser
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer


class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True, required=True, validators=[validate_password]
    )

    class Meta:
        model = RegisterUser
        fields = "__all__"
        extra_kwargs = {"password": {"write_only": True}, "email": {"required": True}}

    def validate_email(self, value):
        # Ensure email is unique and valid.
        if RegisterUser.objects.filter(email=value).exists():
            raise serializers.ValidationError("Email is already in use")
        return value

    def create(self, validated_data):
        user = RegisterUser.objects.create_user(
            email=validated_data["email"],
            password=validated_data["password"],
            username=validated_data.get("username"),
            first_name=validated_data.get("first_name", ""),
            last_name=validated_data.get("last_name", ""),
            interests=validated_data.get("interests", ""),
        )
        return user

    class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
        pass
