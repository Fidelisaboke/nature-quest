from django.db import models
from django.contrib.auth.models import AbstractBaseUser
from django.contrib.auth.models import BaseUserManager,PermissionsMixin
# Create your models here.
class UserManager(BaseUserManager):
  def create_user(self,email,password, **extra_fields):
    if not email:
      raise ValueError('User must have an email address')
    email = self.normalize_email(email)
    user = self.model(email=email,**extra_fields)
    user.set_password(password)
    user.save(using=self._db)
    return user
  def create_superuser(self,email,password,**extra_fields):
    extra_fields.setdefault('is_staff', True)
    extra_fields.setdefault('is_superuser', True)
    extra_fields.setdefault('is_active', True)
    if extra_fields.get('is_staff') is not True:
      raise ValueError('Superuser must have is_staff=True.')
    if extra_fields.get('is_superuser') is not True:
      raise ValueError('Superuser must have is_superuser=True.')
    return self.create_user(email,password=password,**extra_fields)


class RegisterUser(AbstractBaseUser,PermissionsMixin):
  first_name = models.CharField(max_length=255)
  last_name = models.CharField(max_length=255)
  email = models.EmailField(max_length=255,unique=True) #main login field
  username = models.CharField(max_length=255)
  techstack = models.CharField(max_length=255)
  is_active = models.BooleanField(default=True)
  is_staff = models.BooleanField(default=False)  
  objects = UserManager()
  USERNAME_FIELD = 'email' #login with email
  REQUIRED_FIELDS = []

  def __str__(self):
        return self.email
# Create your models here.
