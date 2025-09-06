from .models import RegisterUser
import re
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = RegisterUser
        fields = ('id','first_name','last_name','email','username','techstack','is_active','is_staff','password')
        extra_kwargs = {'password': {'write_only': True},
                        'email': {'required': True}}
    def validate_email(self,value):
            
             #Ensure email is unique and valid.
            if RegisterUser.objects.filter(email=value).exists():
                raise serializers.ValidationError("Email is already in use")
            return value
    def validate_password(self,value):
           #Password must be at least 8 chars, contain uppercase, number, special char.
           if len(value) < 8:
                raise serializers.ValidationError("Password must be at least 8 characters long")
           if not re.search(r"[A-Z]", value):
              raise serializers.ValidationError("Password must contain at least one uppercase letter.")
           if not re.search(r"\d", value):
              raise serializers.ValidationError("Password must contain at least one number.")
           if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", value):
              raise serializers.ValidationError("Password must contain at least one special character.")
           return value
    def create(self, validated_data):   
        return RegisterUser.objects.create_user(
            first_name = validated_data.get('first_name'),
            last_name = validated_data.get('last_name'),
            email = validated_data.get('email'),
            username = validated_data.get('username'),
            techstack = validated_data.get('techstack'),
            password = validated_data.get('password')
        )
    class myTokenObtainPairSerializer(TokenObtainPairSerializer):
         def validate(self, attrs):
             attrs['username'] = attrs.get('email')
             return super().validate(attrs)
