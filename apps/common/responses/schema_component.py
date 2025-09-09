from drf_spectacular.utils import OpenApiExample
from django.utils import timezone


def create_success_example(title, data=None, message="Operation successful"):
    """
    Create a standardized success response example for API documentation.

    Args:
        title (str): Title for the example
        data (dict): The data to include in the response
        message (str): Success message

    Returns:
        OpenApiExample: Formatted example for swagger documentation
    """
    return OpenApiExample(
        name=title,
        summary=title,
        description=f"Successful {title.lower()} response",
        value={
            "success": True,
            "message": message,
            "data": data,
            "errors": None,
            "timestamp": timezone.now().isoformat(),
        },
        response_only=True,
        status_codes=["200"],
    )


def create_error_example(title, message, errors=None, status_code="400"):
    """
    Create a standardized error response example for API documentation.

    Args:
        title (str): Title for the example
        message (str): Error message
        errors (dict): Error details
        status_code (str): HTTP status code

    Returns:
        OpenApiExample: Formatted example for swagger documentation
    """
    return OpenApiExample(
        name=title,
        summary=title,
        description=f"Error response: {title}",
        value={
            "success": False,
            "message": message,
            "data": None,
            "errors": errors or {},
            "timestamp": timezone.now().isoformat(),
        },
        response_only=True,
        status_codes=[status_code],
    )


def get_standard_responses(include=None):
    """
    Get standard error responses for common HTTP status codes.

    Args:
        include (list): List of status codes to include (e.g., [400, 401, 404, 405, 500])

    Returns:
        dict: Dictionary of status codes mapped to OpenApiExample objects
    """
    if include is None:
        include = [400, 401, 404, 405, 500]

    standard_responses = {
        400: create_error_example(
            "Validation Error",
            "Request validation failed",
            {"field": ["This field is required."]},
            "400",
        ),
        401: create_error_example(
            "Authentication Error",
            "Authentication credentials were not provided or are invalid",
            {"detail": "Authentication credentials were not provided."},
            "401",
        ),
        403: create_error_example(
            "Permission Denied",
            "You do not have permission to perform this action",
            {"detail": "You do not have permission to perform this action."},
            "403",
        ),
        404: create_error_example(
            "Not Found",
            "The requested resource was not found",
            {"detail": "Not found."},
            "404",
        ),
        405: create_error_example(
            "Method Not Allowed",
            "The method is not allowed for the requested URL",
            {"detail": "Method not allowed."},
            "405",
        ),
        500: create_error_example(
            "Internal Server Error",
            "An internal server error occurred",
            {"detail": "Internal server error."},
            "500",
        ),
    }

    return {
        code: standard_responses[code] for code in include if code in standard_responses
    }
