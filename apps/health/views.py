from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
import django
import sys


class HealthView(APIView):
    def get(self, request):
        return Response(
            {
                "status": "ok",
                "timestamp": timezone.now().isoformat(),
                "django": django.VERSION[:3],
                "python": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
            },
            status=status.HTTP_200_OK,
        )
