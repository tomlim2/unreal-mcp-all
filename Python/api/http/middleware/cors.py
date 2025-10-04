"""
CORS (Cross-Origin Resource Sharing) middleware.

Handles CORS headers for cross-origin requests from frontend.
"""

from http.server import BaseHTTPRequestHandler


def add_cors_headers(handler: BaseHTTPRequestHandler):
    """
    Add CORS headers to HTTP response.

    Args:
        handler: HTTP request handler instance

    Headers added:
        - Access-Control-Allow-Origin: * (allow all origins)
        - Access-Control-Allow-Methods: All common HTTP methods
        - Access-Control-Allow-Headers: Content-Type, Authorization
    """
    handler.send_header('Access-Control-Allow-Origin', '*')
    handler.send_header('Access-Control-Allow-Methods', 'POST, GET, PUT, DELETE, OPTIONS, HEAD')
    handler.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')


def handle_cors_preflight(handler: BaseHTTPRequestHandler):
    """
    Handle CORS preflight OPTIONS request.

    Args:
        handler: HTTP request handler instance

    Sends:
        - 200 OK response
        - CORS headers
        - Access-Control-Max-Age: 86400 (cache for 24 hours)
    """
    handler.send_response(200)
    add_cors_headers(handler)
    handler.send_header('Access-Control-Max-Age', '86400')  # Cache preflight for 24 hours
    handler.end_headers()
