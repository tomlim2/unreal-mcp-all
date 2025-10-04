"""
HTTP Bridge Server.

Main server implementation with decorator-based routing and middleware.
"""

import json
import time
import logging
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse
from typing import Optional

# Import handlers to register routes
from . import handlers  # This triggers @route decorators

from .router import get_handler, get_all_routes
from .middleware import (
    add_cors_headers,
    handle_cors_preflight,
    generate_trace_id,
    log_request_start,
    log_request_end,
    log_error,
    build_error_response,
    get_http_status_from_error
)

logger = logging.getLogger("http_bridge")


class HTTPBridgeHandler(BaseHTTPRequestHandler):
    """
    HTTP request handler with decorator-based routing.

    Routes are registered via @route decorators in handler modules.
    """

    def log_message(self, format, *args):
        """Override to use Python logging instead of print"""
        logger.info(f"{self.address_string()} - {format%args}")

    def _serve_asset(self, path: str):
        """Serve screenshot, video, or 3D object files"""
        from pathlib import Path
        from core.utils.path_manager import get_path_manager
        import mimetypes
        import os

        try:
            path_manager = get_path_manager()
            # __file__ is at /path/to/Python/api/http/server.py
            # We need to go up 4 levels to reach project root
            base_path = Path(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

            # Map URL path to filesystem path
            if path.startswith('/screenshots/'):
                filename = path[len('/screenshots/'):]
                # Check Unreal screenshots
                unreal_screenshots = path_manager.get_unreal_screenshots_path()
                if unreal_screenshots:
                    file_path = Path(unreal_screenshots) / filename
                else:
                    file_path = base_path / 'data_storage' / 'assets' / 'images' / 'generated' / filename
            elif path.startswith('/api/screenshot/') or path.startswith('/api/screenshot-file/'):
                if path.startswith('/api/screenshot/'):
                    filename = path[len('/api/screenshot/'):]
                else:
                    filename = path[len('/api/screenshot-file/'):]

                # Try generated images first (most common for AI-generated images)
                file_path = base_path / 'data_storage' / 'assets' / 'images' / 'generated' / filename
                if not file_path.exists():
                    # Try Unreal screenshots
                    unreal_screenshots = path_manager.get_unreal_screenshots_path()
                    if unreal_screenshots:
                        file_path = Path(unreal_screenshots) / filename
            elif path.startswith('/videos/'):
                filename = path[len('/videos/'):]
                file_path = base_path / 'data_storage' / 'assets' / 'videos' / filename
            elif path.startswith('/objects/'):
                filename = path[len('/objects/'):]
                file_path = base_path / 'data_storage' / 'assets' / '3d_objects' / filename
            else:
                raise ValueError(f"Unknown asset type: {path}")

            # Check if file exists
            if not file_path.exists():
                self.send_response(404)
                add_cors_headers(self)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                error_response = {'error': f'File not found: {filename}'}
                self.wfile.write(json.dumps(error_response).encode('utf-8'))
                return

            # Determine content type
            content_type, _ = mimetypes.guess_type(str(file_path))
            if not content_type:
                content_type = 'application/octet-stream'

            # Send file
            self.send_response(200)
            add_cors_headers(self)
            self.send_header('Content-Type', content_type)
            self.send_header('Content-Length', str(file_path.stat().st_size))
            self.end_headers()

            with open(file_path, 'rb') as f:
                self.wfile.write(f.read())

            logger.info(f"Served asset: {path} -> {file_path}")

        except Exception as e:
            logger.error(f"Error serving asset {path}: {e}")
            self.send_response(500)
            add_cors_headers(self)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            error_response = {'error': str(e)}
            self.wfile.write(json.dumps(error_response).encode('utf-8'))

    def do_OPTIONS(self):
        """Handle CORS preflight requests"""
        handle_cors_preflight(self)

    def do_GET(self):
        """
        Handle GET requests with decorator-based routing.

        Falls back to legacy handler for asset serving (screenshots, videos, etc.)
        """
        trace_id = generate_trace_id()
        start_time = time.time()

        try:
            parsed_url = urlparse(self.path)
            path = parsed_url.path

            # Check for dynamic routes first (session latest image)
            import re
            latest_image_match = re.match(r'^/api/session/([^/]+)/latest-image$', path)
            if latest_image_match:
                # Call the handler directly
                from api.http.handlers import session_handler
                response = session_handler.handle_get_latest_image(self, {}, trace_id)

                self.send_response(200)
                add_cors_headers(self)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()

                response_json = json.dumps(response, cls=SafeJSONEncoder)
                self.wfile.write(response_json.encode('utf-8'))

                duration_ms = (time.time() - start_time) * 1000
                log_request_end(trace_id, 200, duration_ms)
                return

            # Try decorator-based routing for exact matches
            route_info = get_handler(path, "GET")
            if route_info:
                self.send_response(200)
                add_cors_headers(self)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()

                handler_func = route_info['handler']
                try:
                    response = handler_func(self, {}, trace_id)
                except Exception as e:
                    log_error(trace_id, e, route_info['name'])
                    response = build_error_response(e, trace_id)

                response_json = json.dumps(response, cls=SafeJSONEncoder)
                self.wfile.write(response_json.encode('utf-8'))

                duration_ms = (time.time() - start_time) * 1000
                log_request_end(trace_id, 200, duration_ms)
                return

            # Fallback: serve assets (screenshots, videos, objects)
            if (path.startswith('/screenshots/') or path.startswith('/api/screenshot/') or
                path.startswith('/api/screenshot-file/') or
                path.startswith('/videos/') or path.startswith('/objects/')):
                self._serve_asset(path)
                return

            # Unknown GET request
            self.send_response(404)
            add_cors_headers(self)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            error_response = {'error': f'Not found: {path}'}
            self.wfile.write(json.dumps(error_response).encode('utf-8'))

        except Exception as e:
            logger.exception(f"[{trace_id}] Unexpected error in GET handler")
            self.send_response(500)
            add_cors_headers(self)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            error_response = build_error_response(e, trace_id)
            self.wfile.write(json.dumps(error_response).encode('utf-8'))

    def do_POST(self):
        """
        Handle POST requests with decorator-based routing.

        Flow:
            1. Generate trace ID for request tracking
            2. Parse request body
            3. Look up handler by (path, method) in route registry
            4. Execute all matching handlers until one returns non-None
            5. Send response with CORS headers
            6. Log completion with duration
        """
        trace_id = generate_trace_id()
        start_time = time.time()

        try:
            parsed_url = urlparse(self.path)
            path = parsed_url.path

            # Set CORS headers for all responses
            self.send_response(200)
            add_cors_headers(self)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()

            # Parse request body
            content_length = int(self.headers.get('Content-Length', 0))
            if content_length == 0:
                error_response = {'error': 'No request data', 'trace_id': trace_id}
                self.wfile.write(json.dumps(error_response).encode('utf-8'))
                return

            post_data = self.rfile.read(content_length)
            request_data = json.loads(post_data.decode('utf-8'))

            # Log request keys for debugging
            logger.debug(f"[{trace_id}] Request keys: {list(request_data.keys())}")

            # Try all registered handlers for this route
            # Handlers return None if they don't handle the request
            response = None

            # Get primary handler for exact path match
            route_info = get_handler(path, "POST")
            if route_info:
                handler_func = route_info['handler']
                try:
                    response = handler_func(self, request_data, trace_id)
                except Exception as e:
                    # Handler raised an error - convert to error response
                    log_error(trace_id, e, route_info['name'])
                    response = build_error_response(e, trace_id)
                    status_code = get_http_status_from_error(e)
                    logger.error(f"[{trace_id}] Handler error: {e} (status: {status_code})")

            # If no handler matched, try all handlers (for action-based routing)
            if response is None:
                action_handlers = [
                    ('nlp_handler', handlers.nlp_handler.handle_nlp_request),
                    ('get_context', handlers.session_handler.handle_get_context),
                    ('delete_session', handlers.session_handler.handle_delete_session),
                    ('create_session', handlers.session_handler.handle_create_session),
                ]

                for handler_name, handler_func in action_handlers:
                    try:
                        result = handler_func(self, request_data, trace_id)
                        if result is not None:
                            response = result
                            break
                    except Exception as e:
                        log_error(trace_id, e, handler_name)
                        response = build_error_response(e, trace_id)
                        break

            # If still no response, return error
            if response is None:
                action = request_data.get('action')
                prompt = request_data.get('prompt')
                if action:
                    error_msg = f"Unknown action: {action}"
                elif not prompt:
                    error_msg = "Missing 'prompt' field or valid 'action' field"
                else:
                    error_msg = f"No handler found for path: {path}"

                response = {
                    'error': error_msg,
                    'trace_id': trace_id,
                    'path': path
                }

            # Send response
            response_json = json.dumps(response, cls=SafeJSONEncoder)
            self.wfile.write(response_json.encode('utf-8'))

            # Log completion
            duration_ms = (time.time() - start_time) * 1000
            log_request_end(trace_id, 200, duration_ms)

        except json.JSONDecodeError as e:
            error_msg = f"Invalid JSON: {e}"
            logger.error(f"[{trace_id}] {error_msg}")
            error_response = build_error_response(ValueError(error_msg), trace_id)
            self.wfile.write(json.dumps(error_response).encode('utf-8'))

        except Exception as e:
            logger.exception(f"[{trace_id}] Unexpected error in POST handler")
            error_response = build_error_response(e, trace_id)
            self.wfile.write(json.dumps(error_response).encode('utf-8'))

    def do_PUT(self):
        """Handle PUT requests (session name updates, etc.)"""
        # TODO: Migrate PUT handlers from http_bridge.py
        from http_bridge import MCPBridgeHandler as OriginalHandler
        original = OriginalHandler(self.request, self.client_address, self.server)
        original.do_PUT()

    def do_DELETE(self):
        """Handle DELETE requests"""
        # TODO: Migrate DELETE handlers from http_bridge.py
        from http_bridge import MCPBridgeHandler as OriginalHandler
        original = OriginalHandler(self.request, self.client_address, self.server)
        original.do_DELETE()


class SafeJSONEncoder(json.JSONEncoder):
    """JSON encoder that safely handles bytes objects and other non-serializable types."""
    def default(self, obj):
        if isinstance(obj, bytes):
            return f"<bytes:{len(obj)} bytes>"
        elif hasattr(obj, '__dict__'):
            return obj.__dict__
        else:
            return super().default(obj)


class HTTPBridge:
    """HTTP Bridge Server for MCP communication."""

    def __init__(self, host='127.0.0.1', port=8080):
        self.host = host
        self.port = port
        self.server = None
        logger.info("HTTP Bridge initialized with new decorator-based routing")

        # Log registered routes
        routes = get_all_routes()
        logger.info(f"Registered {len(routes)} routes:")
        for route_info in routes:
            logger.info(f"  {route_info['method']} {route_info['path']} -> {route_info['name']}")

    def start_server(self):
        """Start the HTTP server"""
        try:
            self.server = ThreadingHTTPServer((self.host, self.port), HTTPBridgeHandler)
            logger.info(f"HTTP Bridge started on http://{self.host}:{self.port}")
            logger.info("Server running with decorator-based routing. Press Ctrl+C to stop.")
            self.server.serve_forever()
        except KeyboardInterrupt:
            logger.info("Received interrupt signal, stopping server...")
            self.stop_server()
        except Exception as e:
            logger.error(f"Error starting HTTP bridge: {e}")
            raise

    def stop_server(self):
        """Stop the HTTP server"""
        if self.server:
            self.server.shutdown()
            self.server.server_close()
            logger.info("HTTP Bridge stopped")


def main():
    """Main entry point"""
    try:
        bridge = HTTPBridge()
        bridge.start_server()
    except Exception as e:
        logger.error(f"Failed to start HTTP Bridge: {e}")
        return 1
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
