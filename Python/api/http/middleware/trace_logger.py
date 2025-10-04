"""
Request tracing and logging middleware.

Provides UUID-based request tracing for end-to-end debugging.
"""

import uuid
import logging
from typing import Optional

logger = logging.getLogger("http_bridge")


def generate_trace_id() -> str:
    """
    Generate a unique 8-character trace ID for request tracking.

    Returns:
        8-character trace ID (first 8 chars of UUID4)

    Example:
        >>> trace_id = generate_trace_id()
        >>> print(trace_id)
        'a3f2b4c1'
    """
    return str(uuid.uuid4())[:8]


def log_request_start(trace_id: str, method: str, path: str, action: Optional[str] = None):
    """
    Log request start with trace ID.

    Args:
        trace_id: Unique request identifier
        method: HTTP method (GET, POST, etc.)
        path: Request path
        action: Optional action parameter from request

    Example log:
        [a3f2b4c1] POST / action=nlp_processing
    """
    action_str = f" action={action}" if action else ""
    logger.info(f"[{trace_id}] {method} {path}{action_str}")


def log_request_end(trace_id: str, status: int, duration_ms: float):
    """
    Log request completion with duration.

    Args:
        trace_id: Unique request identifier
        status: HTTP status code
        duration_ms: Request duration in milliseconds

    Example log:
        [a3f2b4c1] Response 200 (345.67ms)
    """
    logger.info(f"[{trace_id}] Response {status} ({duration_ms:.2f}ms)")


def log_error(trace_id: str, error: Exception, context: str = ""):
    """
    Log error with trace ID and context.

    Args:
        trace_id: Unique request identifier
        error: Exception that occurred
        context: Additional context string

    Example log:
        [a3f2b4c1] ERROR in NLP processing: Invalid image format
    """
    context_str = f" in {context}" if context else ""
    logger.error(f"[{trace_id}] ERROR{context_str}: {error}")
