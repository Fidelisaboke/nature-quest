from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
import django
import sys
from drf_spectacular.utils import extend_schema
from .docs import health_schema_args
from django.conf import settings
from datetime import datetime
from .serializers import HealthSerializer

tags = ["health"]


class HealthView(GenericAPIView):
    serializer_class = HealthSerializer
    server_start_time = datetime.utcnow()

    @extend_schema(**health_schema_args)
    def get(self, request):
        uptime = (datetime.utcnow() - self.server_start_time).total_seconds()
        data = {
            "status": "ok",
            "timestamp": timezone.now().isoformat(),
            "django_version": ".".join(map(str, django.VERSION[:3])),
            "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
            "app_name": getattr(settings, "APP_NAME", "Nature Quest"),
            "app_version": getattr(settings, "APP_VERSION", "1.0.0"),
            "uptime_seconds": int(uptime),
        }
        response = {
            "data": data,
            "meta": {
                "message": "Service is healthy",
                "docs_url": getattr(settings, "DOCS_URL", None),
            },
        }
        return Response(response, status=status.HTTP_200_OK)
