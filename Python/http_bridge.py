#!/usr/bin/env python3
"""
HTTP Bridge for Unreal MCP Server - Entry Point

This file now serves as a simple entry point that delegates to the modular
api.http.server implementation. The legacy MCPBridgeHandler is preserved only
for asset serving (screenshots, videos, 3D objects).

For the full legacy implementation, see: http_bridge_legacy_backup.py
"""

import json
import logging
import os
import mimetypes
import re
from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from pathlib import Path
from typing import Dict, Any, Optional
from core.session.utils.path_manager import get_path_manager

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("MCPHttpBridge")


class MCPBridgeHandler(BaseHTTPRequestHandler):
    """
    Legacy handler preserved ONLY for asset serving (GET requests).

    This class is kept minimal - only the do_GET method for serving:
    - Screenshots (/screenshots/*)
    - Videos (/videos/*)
    - 3D Objects (/objects/*)
    """

    def log_message(self, format, *args):
        """Override to use Python logging instead of print"""
        logger.info(f"{self.address_string()} - {format%args}")

    def do_GET(self):
        """Handle GET requests for asset serving"""
        try:
            parsed_url = urlparse(self.path)
            path = parsed_url.path

            # Health check
            if path == '/health':
                self.send_response(200)
                self.send_header('Access-Control-Allow-Origin', '*')
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                response = {
                    'status': 'healthy',
                    'service': 'MCP HTTP Bridge',
                    'version': '2.0.0',
                    'timestamp': '2025-10-05T00:00:00.000Z'
                }
                self.wfile.write(json.dumps(response).encode('utf-8'))
                return

            # Asset serving: screenshots, videos, objects
            # Support both /screenshots/ and /api/screenshot/ paths
            if (path.startswith('/screenshots/') or path.startswith('/api/screenshot/') or
                path.startswith('/api/screenshot-file/') or
                path.startswith('/videos/') or path.startswith('/objects/')):
                self._serve_asset(path)
                return

            # Unknown GET request
            self.send_response(404)
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            error_response = {'error': f'Not found: {path}'}
            self.wfile.write(json.dumps(error_response).encode('utf-8'))

        except Exception as e:
            logger.exception("Error in GET handler")
            self.send_response(500)
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            error_response = {'error': str(e)}
            self.wfile.write(json.dumps(error_response).encode('utf-8'))

    def _serve_asset(self, path: str):
        """Serve screenshot, video, or 3D object files"""
        try:
            path_manager = get_path_manager()

            # Map URL path to filesystem path
            if path.startswith('/screenshots/'):
                filename = path[len('/screenshots/'):]
                file_path = path_manager.get_screenshot_path(filename)
            elif path.startswith('/api/screenshot/'):
                filename = path[len('/api/screenshot/'):]
                # Try screenshots first, then generated images
                file_path = path_manager.get_screenshot_path(filename)
                if not file_path.exists():
                    # Check generated images folder
                    import os
                    generated_path = os.path.join(
                        os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                        'data_storage', 'assets', 'images', 'generated', filename
                    )
                    from pathlib import Path
                    file_path = Path(generated_path)
            elif path.startswith('/api/screenshot-file/'):
                filename = path[len('/api/screenshot-file/'):]
                file_path = path_manager.get_screenshot_path(filename)
                if not file_path.exists():
                    # Check generated images folder
                    import os
                    generated_path = os.path.join(
                        os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                        'data_storage', 'assets', 'images', 'generated', filename
                    )
                    from pathlib import Path
                    file_path = Path(generated_path)
            elif path.startswith('/videos/'):
                filename = path[len('/videos/'):]
                file_path = path_manager.get_video_path(filename)
            elif path.startswith('/objects/'):
                filename = path[len('/objects/'):]
                file_path = path_manager.get_object_path(filename)
            else:
                raise ValueError(f"Unknown asset type: {path}")

            # Check if file exists
            if not file_path.exists():
                self.send_response(404)
                self.send_header('Access-Control-Allow-Origin', '*')
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
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Content-Type', content_type)
            self.send_header('Content-Length', str(file_path.stat().st_size))
            self.end_headers()

            with open(file_path, 'rb') as f:
                self.wfile.write(f.read())

            logger.info(f"Served asset: {path} -> {file_path}")

        except Exception as e:
            logger.error(f"Error serving asset {path}: {e}")
            self.send_response(500)
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            error_response = {'error': str(e)}
            self.wfile.write(json.dumps(error_response).encode('utf-8'))


# Main entry point now uses new modular server
def main():
    """Main entry point - delegates to new modular HTTP server"""
    try:
        from api.http.server import main as new_server_main
        logger.info("Starting HTTP Bridge with new modular architecture...")
        return new_server_main()
    except Exception as e:
        logger.error(f"Failed to start HTTP Bridge: {e}")
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
