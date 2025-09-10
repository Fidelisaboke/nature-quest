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
class UserProfile(models.Model):
    user = models.OneToOneField(RegisterUser, on_delete=models.CASCADE, related_name='profile')
    bio = models.TextField(blank=True)
    profile_pic = models.ImageField(upload_to='profile_pics/', blank=True, null=True)
    points = models.IntegerField(default=0)
    level = models.IntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)