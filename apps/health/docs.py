from drf_spectacular.utils import OpenApiExample, OpenApiResponse
from drf_spectacular.types import OpenApiTypes

health_schema_args = {
    "summary": "Health Check",
    "description": "Returns service status, Django and Python versions, uptime, and timestamp.",
    "tags": ["health"],
    "responses": {
        200: OpenApiResponse(
            response=OpenApiTypes.OBJECT,
            description="Service is healthy.",
            examples=[
                OpenApiExample(
                    "Health Success",
                    summary="Healthy response",
                    value={
                        "data": {
                            "status": "ok",
                            "timestamp": "2025-09-09T01:11:36.473264+00:00",
                            "django_version": "4.2.24",
                            "python_version": "3.11.13",
                            "app_name": "Nature Quest",
                            "app_version": "1.0.0",
                            "uptime_seconds": 12345,
                        },
                        "meta": {
                            "message": "Service is healthy",
                            "docs_url": "https://docs.example.com",
                        },
                    },
                    response_only=True,
                    status_codes=["200"],
                ),
            ],
        ),
        500: OpenApiResponse(
            response=OpenApiTypes.OBJECT,
            description="Unexpected server error",
            examples=[
                OpenApiExample(
                    "Internal Server Error",
                    summary="Unexpected server error",
                    value={
                        "data": None,
                        "meta": {
                            "message": "Internal server error",
                            "docs_url": "https://docs.example.com",
                        },
                    },
                    response_only=True,
                    status_codes=["500"],
                ),
            ],
        ),
    },
}
