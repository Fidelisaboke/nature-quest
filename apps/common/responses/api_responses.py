from rest_framework.response import Response
from django.utils import timezone
import uuid


def api_response(
    success, message, data=None, errors=None, status_code=200, request_id=None
):
    """
    Standardized API response format for consistent client communication.

    Args:
        success (bool): Whether the operation was successful
        message (str): Human-readable message describing the result
        data (dict|list): The actual response data
        errors (dict): Error details if any
        status_code (int): HTTP status code
        request_id (str): Optional request identifier for tracing

    Returns:
        Response: DRF Response object with standardized format
    """
    if request_id is None:
        request_id = str(uuid.uuid4())[:8]

    response_data = {
        "success": success,
        "message": message,
        "data": data,
        "errors": errors,
        "timestamp": timezone.now().isoformat(),
        "request_id": request_id,
    }

    return Response(response_data, status=status_code)
