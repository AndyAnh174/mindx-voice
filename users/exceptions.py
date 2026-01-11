"""
Custom exception handler for consistent error responses.
"""

from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status


def custom_exception_handler(exc, context):
    """
    Custom exception handler that provides consistent error format.
    
    Error response format:
    {
        "success": false,
        "error": {
            "code": "ERROR_CODE",
            "message": "Human readable message",
            "details": {...}  // Optional field-specific errors
        }
    }
    """
    # Call REST framework's default exception handler first
    response = exception_handler(exc, context)

    if response is not None:
        custom_response = {
            "success": False,
            "error": {
                "code": get_error_code(response.status_code),
                "message": get_error_message(response.status_code, exc),
            }
        }
        
        # Add field-specific errors if available
        if isinstance(response.data, dict):
            # Check if it's a field validation error
            field_errors = {}
            for key, value in response.data.items():
                if key not in ["detail", "non_field_errors"]:
                    if isinstance(value, list):
                        field_errors[key] = value[0] if len(value) == 1 else value
                    else:
                        field_errors[key] = value
            
            if field_errors:
                custom_response["error"]["details"] = field_errors
            
            # Handle non_field_errors
            if "non_field_errors" in response.data:
                errors = response.data["non_field_errors"]
                custom_response["error"]["message"] = errors[0] if isinstance(errors, list) else errors
            
            # Handle detail message
            if "detail" in response.data:
                custom_response["error"]["message"] = str(response.data["detail"])
        
        elif isinstance(response.data, list):
            custom_response["error"]["message"] = response.data[0] if response.data else "Đã xảy ra lỗi."
        
        response.data = custom_response

    return response


def get_error_code(status_code):
    """Map HTTP status code to error code."""
    error_codes = {
        400: "BAD_REQUEST",
        401: "UNAUTHORIZED",
        403: "FORBIDDEN",
        404: "NOT_FOUND",
        405: "METHOD_NOT_ALLOWED",
        429: "TOO_MANY_REQUESTS",
        500: "INTERNAL_SERVER_ERROR",
    }
    return error_codes.get(status_code, f"ERROR_{status_code}")


def get_error_message(status_code, exc):
    """Get default error message for status code."""
    error_messages = {
        400: "Dữ liệu không hợp lệ.",
        401: "Vui lòng đăng nhập để tiếp tục.",
        403: "Bạn không có quyền thực hiện thao tác này.",
        404: "Không tìm thấy tài nguyên yêu cầu.",
        405: "Phương thức không được hỗ trợ.",
        429: "Quá nhiều yêu cầu. Vui lòng thử lại sau.",
        500: "Đã xảy ra lỗi máy chủ. Vui lòng thử lại sau.",
    }
    
    # Try to get message from exception first
    if hasattr(exc, "detail"):
        return str(exc.detail)
    
    return error_messages.get(status_code, "Đã xảy ra lỗi.")
