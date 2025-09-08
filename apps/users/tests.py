from django.test import TestCase
from rest_framework.test import APITestCase
from .models import RegisterUser
from rest_framework import status
from django.urls import reverse

# Create your tests here.
class AuthFlowTest(APITestCase):
    def setUp(self):
        self.register_url = reverse('register') # name your URL in urls.py
        self.login_url = reverse('login') # name your URL in urls.py
        self.user_data = {
            "first_name": "John",
            "last_name": "Doe",
            "email": "john@example.com",
            "username": "johndoe",
            "techstack": "Python,Django",
            "password": "Password@123"
        }
    def test_user_registration(self):
         """Test successful registration returns tokens + user info"""
         response = self.client.post(self.register_url,self.user_data,format='json')
         self.assertEqual(response.status_code,status.HTTP_201_CREATED)
          # Response must contain tokens and results
         self.assertIn('access',response.data)
         self.assertIn('refresh',response.data)
         self.assertIn('results',response.data)
         self.assertTrue(RegisterUser.objects.filter(email=self.user_data['email']).exists())
    def test_registration_with_existing_email(self):
         """Test registration fails if email already exists"""
         self.client.post(self.register_url,self.user_data,format='json')
         response = self.client.post(self.register_url,self.user_data,format='json')
         self.assertEqual(response.status_code,status.HTTP_400_BAD_REQUEST)
         self.assertIn('email',response.data)
    def test_login_user(self):
         """Helper method to login user and return tokens"""
         self.client.post(self.register_url,self.user_data,format='json')
         login_data = {
             "email": self.user_data['email'],
             "password": self.user_data['password']
         }
         response = self.client.post(self.login_url,login_data,format='json')
         self.assertEqual(response.status_code, status.HTTP_200_OK)
         self.assertIn("access", response.data)
         self.assertIn("refresh", response.data)
    def test_login_with_invalid_credentials(self):
            """Test login fails with wrong credentials"""
            self.client.post(self.register_url,self.user_data,format='json')
            login_data = {
                "email": self.user_data['email'],
                "password": "WrongPassword@123"
            }
            response = self.client.post(self.login_url,login_data,format='json')
            self.assertEqual(response.status_code,status.HTTP_401_UNAUTHORIZED)
          