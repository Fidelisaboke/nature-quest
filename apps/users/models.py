from django.db import models
from django.contrib.auth.models import AbstractUser

class RegisterUser(AbstractUser):
  email = models.EmailField(unique=True)
  interests = models.CharField(max_length=255)
  is_active = models.BooleanField(default=True)
  is_staff = models.BooleanField(default=False)  

  USERNAME_FIELD = 'email' #login with email
  REQUIRED_FIELDS = []

  def __str__(self):
        return self.email
# Create your models here.
