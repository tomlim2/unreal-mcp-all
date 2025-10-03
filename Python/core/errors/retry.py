"""Retry policies for external APIs and transient failures."""

try:
    from tenacity import (
        retry,
        stop_after_attempt,
        wait_exponential,
        retry_if_exception_type,
        before_sleep_log
    )
    TENACITY_AVAILABLE = True
except ImportError:
    TENACITY_AVAILABLE = False
    # Provide no-op decorator if tenacity not installed
    def retry(*args, **kwargs):
        def decorator(func):
            return func
        return decorator

import logging
from .base import AppError, ErrorCategory

logger = logging.getLogger("MegaMelange.Retry")


if TENACITY_AVAILABLE:
    # Retry policy for external APIs (NanoBanana, Gemini)
    retry_external_api = retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((ConnectionError, TimeoutError)),
        before_sleep=before_sleep_log(logger, logging.WARNING)
    )

    # Retry policy for Unreal Engine commands
    retry_unreal_command = retry(
        stop=stop_after_attempt(2),
        wait=wait_exponential(multiplier=1, min=1, max=5),
        retry=retry_if_exception_type(ConnectionError),
        before_sleep=before_sleep_log(logger, logging.INFO)
    )

    # No retry for rate limit errors (respect retry_after)
    def should_not_retry_rate_limit(exception):
        """Don't retry if it's a rate limit error with retry_after."""
        if isinstance(exception, AppError):
            return exception.category != ErrorCategory.RATE_LIMIT
        return True

    retry_with_rate_limit_respect = retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=should_not_retry_rate_limit,
        before_sleep=before_sleep_log(logger, logging.WARNING)
    )
else:
    # No-op decorators if tenacity not available
    logger.warning("tenacity not installed - retry policies disabled")

    def retry_external_api(func):
        """No-op decorator when tenacity unavailable."""
        return func

    def retry_unreal_command(func):
        """No-op decorator when tenacity unavailable."""
        return func

    def retry_with_rate_limit_respect(func):
        """No-op decorator when tenacity unavailable."""
        return func


__all__ = [
    'retry_external_api',
    'retry_unreal_command',
    'retry_with_rate_limit_respect',
    'TENACITY_AVAILABLE'
]
