from drf_spectacular.utils import OpenApiExample, OpenApiResponse
from drf_spectacular.types import OpenApiTypes

user_register_schema_args = {
    "summary": "Register New User",
    "description": "Creates a new user account and returns authentication tokens.",
    "request": OpenApiTypes.OBJECT,
    "responses": {
        201: OpenApiResponse(
            response=OpenApiTypes.OBJECT,
            description="User registered successfully.",
            examples=[
                OpenApiExample(
                    "Registration Success",
                    summary="Successful registration response",
                    value={
                        "success": True,
                        "message": "User registered successfully",
                        "data": {
                            "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
                            "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
                            "results": {
                                "id": 1,
                                "email": "wekesa@example.com",
                                "username": "wekesa",
                                "first_name": "Wekesa",
                                "last_name": "Nekesa",
                                "interests": "Python,Django,Rust,Cycling",
                                "is_active": True,
                                "is_staff": False,
                                "groups": [],
                                "user_permissions": [],
                            },
                        },
                        "errors": None,
                        "timestamp": "2025-09-09T09:46:30.103455+00:00",
                        "request_id": "5c8e9a84",
                    },
                    response_only=True,
                    status_codes=["201"],
                ),
            ],
        ),
        400: OpenApiResponse(
            response=OpenApiTypes.OBJECT,
            description="Validation error response",
            examples=[
                OpenApiExample(
                    "Registration Error",
                    summary="Validation error response",
                    value={
                        "success": False,
                        "message": "Validation failed",
                        "data": None,
                        "errors": {
                            "email": ["Email is already in use"],
                            "password": ["This password is too common."],
                            "username": ["A user with that username already exists."],
                        },
                        "timestamp": "2025-09-09T01:11:36.473264+00:00",
                    },
                    response_only=True,
                    status_codes=["400"],
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
                        "success": False,
                        "message": "An internal server error occurred",
                        "data": None,
                        "errors": {"detail": "Internal server error."},
                        "timestamp": "2025-09-09T01:11:36.473264+00:00",
                    },
                    response_only=True,
                    status_codes=["500"],
                ),
            ],
        ),
    },
    "examples": [
        OpenApiExample(
            "Registration Request",
            summary="Example user registration",
            value={
                "first_name": "Wekesa",
                "last_name": "Nekesa",
                "email": "wekesa@example.com",
                "username": "wekesa",
                "interests": "Python,Django,Rust,Cycling",
                "password": "SecurePassword123!",
            },
            request_only=True,
        ),
    ],
}


user_login_schema_args = {
    "summary": "User Login",
    "description": "Authenticates user and returns JWT tokens.",
    "request": OpenApiTypes.OBJECT,
    "responses": {
        200: OpenApiResponse(
            response=OpenApiTypes.OBJECT,
            description="Login successful.",
            examples=[
                OpenApiExample(
                    "Login Success",
                    summary="Successful login response",
                    value={
                        "success": True,
                        "message": "Login successful",
                        "data": {
                            "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
                            "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
                        },
                        "errors": None,
                        "timestamp": "2025-09-09T09:45:29.400641+00:00",
                        "request_id": "abfe3752",
                    },
                    response_only=True,
                    status_codes=["200"],
                ),
            ],
        ),
        401: OpenApiResponse(
            response=OpenApiTypes.OBJECT,
            description="Invalid credentials response",
            examples=[
                OpenApiExample(
                    "Login Error",
                    summary="Invalid credentials response",
                    value={
                        "success": False,
                        "message": "No active account found with the given credentials",
                        "data": None,
                        "errors": {
                            "detail": "No active account found with the given credentials"
                        },
                        "timestamp": "2025-09-09T01:11:36.473264+00:00",
                    },
                    response_only=True,
                    status_codes=["401"],
                ),
            ],
        ),
        400: OpenApiResponse(
            response=OpenApiTypes.OBJECT,
            description="Missing or invalid fields",
            examples=[
                OpenApiExample(
                    "Validation Error",
                    summary="Missing or invalid fields",
                    value={
                        "success": False,
                        "message": "Request validation failed",
                        "data": None,
                        "errors": {
                            "email": ["This field is required."],
                            "password": ["This field is required."],
                        },
                        "timestamp": "2025-09-09T01:11:36.473264+00:00",
                    },
                    response_only=True,
                    status_codes=["400"],
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
                        "success": False,
                        "message": "An internal server error occurred",
                        "data": None,
                        "errors": {"detail": "Internal server error."},
                        "timestamp": "2025-09-09T01:11:36.473264+00:00",
                    },
                    response_only=True,
                    status_codes=["500"],
                ),
            ],
        ),
    },
    "examples": [
        OpenApiExample(
            "Login Request",
            summary="Example login request",
            value={"email": "wekesa@example.com", "password": "SecurePassword123!"},
            request_only=True,
        ),
    ],
}

token_refresh_schema_args = {
    "summary": "Refresh Access Token",
    "description": "Refreshes the access token using a valid refresh token.",
    "request": OpenApiTypes.OBJECT,
    "responses": {
        200: OpenApiResponse(
            response=OpenApiTypes.OBJECT,
            description="Token refreshed successfully.",
            examples=[
                OpenApiExample(
                    "Token Refresh Success",
                    summary="Successful token refresh response",
                    value={
                        "success": True,
                        "message": "Token refreshed successfully",
                        "data": {
                            "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
                        },
                        "errors": None,
                        "timestamp": "2025-09-09T09:44:19.400641+00:00",
                        "request_id": "abfe3752",
                    },
                    response_only=True,
                    status_codes=["200"],
                ),
            ],
        ),
        401: OpenApiResponse(
            response=OpenApiTypes.OBJECT,
            description="Invalid or expired token response",
            examples=[
                OpenApiExample(
                    "Token Refresh Error",
                    summary="Invalid or expired token response",
                    value={
                        "success": False,
                        "message": "Token is invalid or expired",
                        "data": None,
                        "errors": {"detail": "Token is invalid or expired"},
                        "timestamp": "2025-09-09T01:11:36.473264+00:00",
                    },
                    response_only=True,
                    status_codes=["401"],
                ),
            ],
        ),
        400: OpenApiResponse(
            response=OpenApiTypes.OBJECT,
            description="Missing or invalid refresh token",
            examples=[
                OpenApiExample(
                    "Validation Error",
                    summary="Missing or invalid refresh token",
                    value={
                        "success": False,
                        "message": "Request validation failed",
                        "data": None,
                        "errors": {"refresh": ["This field is required."]},
                        "timestamp": "2025-09-09T01:11:36.473264+00:00",
                    },
                    response_only=True,
                    status_codes=["400"],
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
                        "success": False,
                        "message": "An internal server error occurred",
                        "data": None,
                        "errors": {"detail": "Internal server error."},
                        "timestamp": "2025-09-09T01:11:36.473264+00:00",
                    },
                    response_only=True,
                    status_codes=["500"],
                ),
            ],
        ),
    },
    "examples": [
        OpenApiExample(
            "Token Refresh Request",
            summary="Example token refresh request",
            value={"refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."},
            request_only=True,
        ),
    ],
}
