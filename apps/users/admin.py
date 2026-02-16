from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import RegisterUser

# Register your models here.

admin.site.register(RegisterUser, UserAdmin)
