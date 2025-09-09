from rest_framework import serializers


class HealthSerializer(serializers.Serializer):
    """Serializer for health check response data."""

    status = serializers.CharField()
    timestamp = serializers.DateTimeField()
    django_version = serializers.CharField()
    python_version = serializers.CharField()
    app_name = serializers.CharField()
    app_version = serializers.CharField()
    uptime_seconds = serializers.IntegerField()
