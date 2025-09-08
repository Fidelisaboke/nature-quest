"""
URL configuration for naturequest project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework.authtoken.views import obtain_auth_token
from . import views

urlpatterns = [
    # Root endpoints
    path('', views.simple_root, name='root'),
    path('api/', views.api_root, name='api-root'),
    
    # Authentication
    path('api/auth/token/', obtain_auth_token, name='api_token_auth'),
    
    # Admin
    path('admin/', admin.site.urls),
    
    # Include app URLs with proper namespacing
    path('api/progress/', include('userprogress.urls')),
    path('api/quiz/', include('quiz.urls')),
    path('api/challenge-verification/', include('challengeverification.urls')),
]

# Serve media files during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
