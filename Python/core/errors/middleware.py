"""Error handling middleware for HTTP bridge."""

import logging
import functools
from typing import Callable, Any
from .base import AppError, ErrorCategory

logger = logging.getLogger("MegaMelange.Middleware")


def handle_request_errors(request_id_getter: Callable = None):
    """
    Decorator to standardize error handling across HTTP endpoints.

    Args:
        request_id_getter: Optional function to extract request_id from args

    Example:
        @handle_request_errors(lambda args: args[1].get('request_id'))
        def handle_transform(self, params):
            ...
    """
    def decorator(handler_func):
        @functools.wraps(handler_func)
        def wrapper(*args, **kwargs):
            request_id = None
            try:
                # Extract request_id if getter provided
                if request_id_getter:
                    request_id = request_id_getter(args)

                return handler_func(*args, **kwargs)

            except AppError as e:
                # Structured error - log and return formatted response
                e.request_id = e.request_id or request_id
                e.log()
                return e.to_response()

            except Exception as e:
                # Unhandled error - log with full traceback
                logger.exception(f"Unhandled error in {handler_func.__name__}")

                error = AppError(
                    code="INTERNAL_ERROR",
                    message="An unexpected error occurred",
                    category=ErrorCategory.INTERNAL_SERVER,
                    details={
                        "exception_type": e.__class__.__name__,
                        "exception_message": str(e)
                    },
                    suggestion="Please try again or contact support",
                    request_id=request_id
                )

                return error.to_response()

        return wrapper
    return decorator
