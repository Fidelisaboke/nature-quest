from django.shortcuts import render
from rest_framework.decorators import api_view,permission_classes
from rest_framework.response import Response
from rest_framework import status
from django.http import HttpResponse
from .serializer import UserSerializer
from .models import RegisterUser
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView

# Create your views here.
@api_view(['POST'])
def register_user(request):
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
           
            return Response({
               'results':serializer.data
                },status=status.HTTP_201_CREATED)
        return Response(serializer.errors,status=status.HTTP_400_BAD_REQUEST)
class MyTokenObtainPairView(TokenObtainPairView):
    serializer_class = UserSerializer.MyTokenObtainPairSerializer
