#!/usr/bin/env python3
"""
HTTP Bridge for Unreal MCP Server
Provides HTTP endpoint for frontend to communicate with MCP server
"""

import json
import logging
import os
import asyncio
import mimetypes
import datetime
import base64
import re
from http.server import HTTPServer, BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs
from pathlib import Path
import threading
from typing import Dict, Any, Optional, List
from core.session.utils.path_manager import get_path_manager

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Import session management
from core.session import SessionManager, SessionContext, get_session_manager
from core.session.utils.session_helpers import extract_session_id_from_request, generate_session_id

# Import error handling system
from core.errors import AppError, ErrorCategory, CATEGORY_STATUS_MAP

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("MCPHttpBridge")

# Custom JSON encoder to handle bytes objects
class SafeJSONEncoder(json.JSONEncoder):
    """JSON encoder that safely handles bytes objects and other non-serializable types."""
    def default(self, obj):
        if isinstance(obj, bytes):
            # Convert bytes to base64 string for JSON serialization
            return f"<bytes:{len(obj)} bytes>"
        elif hasattr(obj, '__dict__'):
            # Handle custom objects by converting to dict
            return obj.__dict__
        else:
            # Let the base class handle other types
            return super().default(obj)

# Image processing constants
MAX_IMAGE_SIZE_MB = 10
MAX_TOTAL_REQUEST_SIZE_MB = 30
ALLOWED_MIME_TYPES = {'image/png', 'image/jpeg', 'image/jpg'}


def _decode_base64_image(data_str: str) -> Dict[str, Any]:
    """
    Decode base64 image data with support for Data URI format.

    Args:
        data_str: Either "data:image/png;base64,iVBORw0..." or raw base64 string

    Returns:
        Dict with 'mime_type' and 'data' (bytes)

    Raises:
        ValueError: If the data is invalid
    """
    try:
        # Try Data URI format first: data:image/png;base64,iVBORw0...
        match = re.match(r"^data:(image/[\w]+);base64,(.*)", data_str)
        if match:
            mime_type, b64_data = match.groups()

            # Validate MIME type
            if mime_type not in ALLOWED_MIME_TYPES:
                raise ValueError(f"Unsupported MIME type: {mime_type}. Allowed: {ALLOWED_MIME_TYPES}")

            decoded_data = base64.b64decode(b64_data)
            return {
                "mime_type": mime_type,
                "data": decoded_data
            }

        # Fallback: try raw base64 (assume PNG)
        decoded_data = base64.b64decode(data_str)
        return {
            "mime_type": "image/png",
            "data": decoded_data
        }

    except Exception as e:
        raise ValueError(f"Invalid base64 image data: {e}")


def _validate_image_size(image_data: bytes, max_size_mb: int = MAX_IMAGE_SIZE_MB) -> None:
    """
    Validate image size.

    Args:
        image_data: Image bytes
        max_size_mb: Maximum allowed size in MB

    Raises:
        ValueError: If image is too large
    """
    size_mb = len(image_data) / (1024 * 1024)
    if size_mb > max_size_mb:
        raise ValueError(f"Image too large: {size_mb:.2f}MB (max: {max_size_mb}MB)")


def _validate_and_process_images(images: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Validate and process a list of images.

    Args:
        images: List of image dictionaries with 'data' field

    Returns:
        List of processed images with 'mime_type', 'data', and optional 'purpose'

    Raises:
        ValueError: If validation fails
    """
    if not images:
        return []

    processed_images = []
    total_size = 0

    for i, img in enumerate(images):
        if not isinstance(img, dict):
            raise ValueError(f"Image {i}: Must be a dictionary")

        # Support both 'data' and 'image_data' fields (frontend compatibility)
        image_data = img.get('data') or img.get('image_data')
        if not image_data:
            raise ValueError(f"Image {i}: Missing 'data' or 'image_data' field")

        try:
            # Decode base64 image
            decoded_img = _decode_base64_image(image_data)

            # Validate size
            _validate_image_size(decoded_img['data'])

            # Track total size
            total_size += len(decoded_img['data'])

            processed_images.append(decoded_img)

        except ValueError as e:
            raise ValueError(f"Image {i}: {e}")

    # Check total request size
    total_size_mb = total_size / (1024 * 1024)
    if total_size_mb > MAX_TOTAL_REQUEST_SIZE_MB:
        raise ValueError(f"Total images too large: {total_size_mb:.2f}MB (max: {MAX_TOTAL_REQUEST_SIZE_MB}MB)")

    return processed_images


def _log_image_processing(images: List[Dict], reference_images: List[Dict]) -> None:
    """
    Log image processing metadata (safely, without actual image data).

    Args:
        images: Processed images list
        reference_images: Processed reference images list
    """
    if images:
        image_info = [
            f"{img.get('mime_type', 'unknown')}({len(img.get('data', b''))//1024}KB)"
            for img in images
        ]
        logger.info(f"Processing {len(images)} target images: {image_info}")

    if reference_images:
        ref_info = []
        for ref in reference_images:
            data_size = len(ref.get('data', b'')) // 1024
            ref_info.append(f"{ref.get('mime_type', 'unknown')}({data_size}KB)")
        logger.info(f"Processing {len(reference_images)} reference images: {ref_info}")


class MCPBridgeHandler(BaseHTTPRequestHandler):
    """HTTP request handler for MCP bridge"""
    
    def do_OPTIONS(self):
        """Handle CORS preflight requests"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, GET, PUT, DELETE, OPTIONS, HEAD')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.send_header('Access-Control-Max-Age', '86400')  # Cache preflight for 24 hours
        self.end_headers()
    
    def do_HEAD(self):
        """Handle HEAD requests (same as GET but without response body)"""
        # For screenshot and video files, we can handle HEAD requests efficiently
        parsed_url = urlparse(self.path)
        path = parsed_url.path

        if path.startswith('/api/screenshot-file/') or path.startswith('/api/screenshot/') or path.startswith('/api/video-file/') or path.startswith('/api/video/'):
            # Handle HEAD request for screenshot and video files
            path_parts = path.split('/')
            if len(path_parts) == 4 and path_parts[1] == 'api':
                endpoint_type = path_parts[2]
                filename = path_parts[3]

                # Handle screenshot files
                if endpoint_type in ['screenshot-file', 'screenshot']:
                    try:
                        # Get screenshot directories using direct PathManager
                        path_manager = get_path_manager()
                        screenshot_dir_path = path_manager.get_unreal_screenshots_path()
                        styled_dir_path = path_manager.get_unreal_styled_images_path()
                        generated_dir_path = path_manager.get_generated_images_path()

                        # Always have generated_dir available (doesn't require Unreal project)
                        if not generated_dir_path:
                            self.send_response(500)
                            self.send_header('Access-Control-Allow-Origin', '*')
                            self.end_headers()
                            return

                        # Build list of directories to check (generated is always available)
                        search_paths = []
                        if screenshot_dir_path:
                            search_paths.append(Path(screenshot_dir_path))
                        if styled_dir_path:
                            search_paths.append(Path(styled_dir_path))
                        search_paths.append(Path(generated_dir_path))

                        # Try to find file in all available directories
                        file_path = None
                        for search_dir in search_paths:
                            candidate_path = search_dir / filename
                            if candidate_path.exists():
                                file_path = candidate_path
                                break

                        # Check if file exists
                        if file_path and file_path.exists() and filename.lower().endswith('.png'):
                            file_size = file_path.stat().st_size

                            # Send success headers without body
                            self.send_response(200)
                            self.send_header('Access-Control-Allow-Origin', '*')
                            self.send_header('Content-Type', 'image/png')
                            self.send_header('Content-Length', str(file_size))
                            self.end_headers()
                            return
                        else:
                            self.send_response(404)
                            self.send_header('Access-Control-Allow-Origin', '*')
                            self.end_headers()
                            return
                        
                    except Exception as e:
                        logger.error(f"Error handling HEAD request for {filename}: {e}")
                        self.send_response(500)
                        self.send_header('Access-Control-Allow-Origin', '*')
                        self.end_headers()
                        return

                # Handle video files
                elif endpoint_type in ['video-file', 'video']:
                    try:
                        # Get project path using direct PathManager
                        path_manager = get_path_manager()
                        project_path = path_manager.get_unreal_project_path()
                        if not project_path:
                            self.send_response(500)
                            self.send_header('Access-Control-Allow-Origin', '*')
                            self.end_headers()
                            return

                        # Build path to video file - check generated directory
                        video_dir = Path(project_path) / "Saved" / "Videos" / "generated"
                        file_path = video_dir / filename

                        # Check if file exists
                        if file_path.exists() and filename.lower().endswith('.mp4'):
                            file_size = file_path.stat().st_size

                            # Send success headers without body
                            self.send_response(200)
                            self.send_header('Access-Control-Allow-Origin', '*')
                            self.send_header('Content-Type', 'video/mp4')
                            self.send_header('Content-Length', str(file_size))
                            self.end_headers()
                            return
                        else:
                            self.send_response(404)
                            self.send_header('Access-Control-Allow-Origin', '*')
                            self.end_headers()
                            return

                    except Exception as e:
                        logger.error(f"Error handling HEAD request for video {filename}: {e}")
                        self.send_response(500)
                        self.send_header('Access-Control-Allow-Origin', '*')
                        self.end_headers()
                        return
        
        # For other paths, return 501 Not Implemented
        self.send_response(501)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
    
    def do_GET(self):
        """Handle GET requests"""
        print(f"==== DEBUG: do_GET called for path: {self.path} ====", flush=True)
        logger.info(f"GET request received: {self.path}")
        try:
            # Parse URL path first
            parsed_url = urlparse(self.path)
            path = parsed_url.path

            # Handle Creative Hub tool registry
            if path == '/tools' or path == '/api/tools':
                self._handle_get_tools()
                return

            # Handle tool health check
            elif path.startswith('/tools/') or path.startswith('/api/tools/'):
                path_parts = path.split('/')
                if len(path_parts) >= 3:
                    tool_id = path_parts[2] if path_parts[1] == 'tools' else path_parts[3]
                    if tool_id == 'health':
                        self._handle_tools_health()
                    else:
                        self._handle_get_tool_info(tool_id)
                    return

            # Handle 3D object serving
            elif path.startswith('/3d-object/') or path.startswith('/api/3d-object/'):
                path_parts = path.split('/')
                if len(path_parts) >= 3:
                    uid = path_parts[2] if path_parts[1] == '3d-object' else path_parts[3]
                    self._handle_3d_object_file(uid)
                    return

            # Handle Roblox status endpoints
            elif path.startswith('/api/roblox-status/'):
                # Handle Roblox download status check
                path_parts = path.split('/')
                if len(path_parts) >= 4 and path_parts[2] == 'roblox-status':
                    uid = path_parts[3]
                    self._handle_roblox_status(uid)
                    return
                else:
                    self._send_error("Invalid Roblox status endpoint format")
                    return

            elif path.startswith('/api/roblox-cancel/'):
                # Handle Roblox download cancellation
                path_parts = path.split('/')
                if len(path_parts) >= 4 and path_parts[2] == 'roblox-cancel':
                    uid = path_parts[3]
                    self._handle_roblox_cancel(uid)
                    return
                else:
                    self._send_error("Invalid Roblox cancel endpoint format")
                    return

            elif path.startswith('/api/roblox-file/'):
                # Handle Roblox file serving
                path_parts = path.split('/')
                if len(path_parts) >= 5 and path_parts[2] == 'roblox-file':
                    uid = path_parts[3]
                    file_type = path_parts[4]
                    self._handle_roblox_file(uid, file_type)
                    return
                else:
                    self._send_error("Invalid Roblox file endpoint format")
                    return

            elif path.startswith('/api/roblox-cleanup'):
                # Handle Roblox cleanup operations
                self._handle_roblox_cleanup()
                return

            # Handle file requests first (before sending any headers)
            elif path.startswith('/api/screenshot-file/') or path.startswith('/api/screenshot/') or path.startswith('/api/video-file/') or path.startswith('/api/video/'):
                # Handle screenshot and video file serving
                path_parts = path.split('/')
                if len(path_parts) == 4 and path_parts[1] == 'api':
                    endpoint_type = path_parts[2]
                    filename = path_parts[3]

                    # Handle screenshot files
                    if endpoint_type in ['screenshot-file', 'screenshot']:
                        try:
                            # Get screenshot directories using centralized path management
                            path_manager = get_path_manager()
                            screenshot_dir_path = path_manager.get_unreal_screenshots_path()
                            styled_dir_path = path_manager.get_unreal_styled_images_path()
                            generated_dir_path = path_manager.get_generated_images_path()

                            # Always have generated_dir available (doesn't require Unreal project)
                            if not generated_dir_path:
                                self._send_error("Unable to determine generated images directory path")
                                return

                            # Build list of directories to check (generated is always available)
                            search_paths = []
                            if screenshot_dir_path:
                                search_paths.append(Path(screenshot_dir_path))
                            if styled_dir_path:
                                search_paths.append(Path(styled_dir_path))
                            search_paths.append(Path(generated_dir_path))

                            # Try to find file in all available directories
                            file_path = None
                            for search_dir in search_paths:
                                candidate_path = search_dir / filename
                                if candidate_path.exists():
                                    file_path = candidate_path
                                    break

                            # Validate file exists and is a PNG
                            if not file_path or not file_path.exists():
                                self._send_error(f"Screenshot file not found: {filename}")
                                return

                            if not filename.lower().endswith('.png'):
                                self._send_error(f"Invalid file type: {filename}")
                                return

                            # Serve the file
                            logger.info(f"Serving screenshot file: {filename}")
                            self._serve_file(file_path)
                            return

                        except Exception as e:
                            logger.error(f"Error serving screenshot file {filename}: {e}")
                            self._send_error(f"Error serving file: {e}")
                            return

                    # Handle video files
                    elif endpoint_type in ['video-file', 'video']:
                        try:
                            # Get project path using direct PathManager
                            path_manager = get_path_manager()
                            project_path = path_manager.get_unreal_project_path()
                            if not project_path:
                                self._send_error("Unable to determine Unreal project path")
                                return

                            # Build path to video file - check generated directory
                            video_dir = Path(project_path) / "Saved" / "Videos" / "generated"
                            file_path = video_dir / filename

                            # Validate file exists and is an MP4
                            if not file_path.exists():
                                self._send_error(f"Video file not found: {filename}")
                                return

                            if not filename.lower().endswith('.mp4'):
                                self._send_error(f"Invalid file type: {filename}")
                                return

                            # Serve the file
                            logger.info(f"Serving video file: {filename}")
                            self._serve_file(file_path)
                            return

                        except Exception as e:
                            logger.error(f"Error serving video file {filename}: {e}")
                            self._send_error(f"Error serving file: {e}")
                            return

            # Handle JSON API requests
            if path == '/test-no-session':
                # Test endpoint WITHOUT session management (control)
                self.send_response(200)
                self.send_header('Access-Control-Allow-Origin', '*')
                self.send_header('Content-Type', 'application/json')
                self.end_headers()

                response = {
                    'status': 'success',
                    'message': 'Control endpoint without session management',
                    'test_type': 'no_session'
                }
                response_json = json.dumps(response)
                self.wfile.write(response_json.encode('utf-8'))
                return

            elif path == '/test-with-session':
                # Test endpoint WITH session management (test case)
                self.send_response(200)
                self.send_header('Access-Control-Allow-Origin', '*')
                self.send_header('Content-Type', 'application/json')
                self.end_headers()

                # This should trigger the duplicate response issue
                try:
                    session_manager = get_session_manager()
                    response = {
                        'status': 'success',
                        'message': 'Test endpoint WITH session management',
                        'test_type': 'with_session',
                        'session_manager_loaded': True
                    }
                except Exception as e:
                    response = {
                        'status': 'error',
                        'message': f'Session manager error: {e}',
                        'test_type': 'with_session',
                        'session_manager_loaded': False
                    }

                response_json = json.dumps(response)
                self.wfile.write(response_json.encode('utf-8'))
                return

            elif path == '/health':
                # Handle health check request - send headers here
                self.send_response(200)
                self.send_header('Access-Control-Allow-Origin', '*')
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                # Handle health check request
                response = {
                    'status': 'healthy',
                    'service': 'MCP HTTP Bridge',
                    'version': '1.0.0',
                    'timestamp': '2025-09-04T06:38:00.000Z'
                }
                response_json = json.dumps(response)
                self.wfile.write(response_json.encode('utf-8'))
                return

            elif path == '/sessions':
                # Handle session list request - bypass NLP, direct to session manager
                self.send_response(200)
                self.send_header('Access-Control-Allow-Origin', '*')
                self.send_header('Content-Type', 'application/json')
                self.end_headers()

                try:
                    session_manager = get_session_manager()
                    sessions = session_manager.storage.list_sessions()

                    # Convert sessions to the expected format
                    session_list = []
                    for session_context in sessions:
                        session_list.append({
                            'session_id': session_context.session_id,
                            'session_name': session_context.session_name,
                            'created_at': session_context.created_at.isoformat(),
                            'last_accessed': session_context.last_accessed.isoformat(),
                            'interaction_count': len(session_context.conversation_history)
                        })

                    # Sort by last_accessed descending
                    session_list.sort(key=lambda s: s['last_accessed'], reverse=True)

                    response = {
                        'sessions': session_list
                    }
                    response_json = json.dumps(response)
                    self.wfile.write(response_json.encode('utf-8'))
                    return

                except Exception as e:
                    logger.error(f"Error getting session list: {e}")
                    self._send_error(f"Failed to get session list: {e}")
                    return

            elif path.startswith('/api/session/') and path.endswith('/latest-image'):
                # Handle latest image UID request - /api/session/{session_id}/latest-image
                self.send_response(200)
                self.send_header('Access-Control-Allow-Origin', '*')
                self.send_header('Content-Type', 'application/json')
                self.end_headers()

                try:
                    path_parts = path.split('/')
                    if len(path_parts) >= 4:
                        session_id = path_parts[3]

                        session_manager = get_session_manager()
                        session_context = session_manager.get_session(session_id)

                        if not session_context:
                            response = {
                                'success': False,
                                'error': 'Session not found',
                                'latest_image': {
                                    'uid': None,
                                    'filename': None,
                                    'thumbnail_url': None,
                                    'available': False
                                }
                            }
                        else:
                            latest_uid = session_context.get_latest_image_uid()
                            latest_filename = session_context.get_latest_image_path()

                            response = {
                                'success': True,
                                'latest_image': {
                                    'uid': latest_uid,
                                    'filename': latest_filename,
                                    'thumbnail_url': f'/api/screenshot-file/{latest_filename}' if latest_filename else None,
                                    'available': latest_uid is not None
                                }
                            }

                        response_json = json.dumps(response)
                        self.wfile.write(response_json.encode('utf-8'))
                        return
                    else:
                        response = {'error': 'Invalid session ID in path'}
                        response_json = json.dumps(response)
                        self.wfile.write(response_json.encode('utf-8'))
                        return

                except Exception as e:
                    logger.error(f"Error getting latest image for session: {e}")
                    response = {
                        'success': False,
                        'error': str(e),
                        'latest_image': {
                            'uid': None,
                            'filename': None,
                            'thumbnail_url': None,
                            'available': False
                        }
                    }
                    response_json = json.dumps(response)
                    self.wfile.write(response_json.encode('utf-8'))
                    return

            # Handle other GET requests (404)
            self.send_response(404)
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Content-Type', 'application/json')
            self.end_headers()

            response = {'error': f"Endpoint not found: {path}"}
            response_json = json.dumps(response)
            self.wfile.write(response_json.encode('utf-8'))

        except Exception as e:
            logger.error(f"Error handling GET request: {e}")
            self._send_error(f"Server error: {e}")
    
    def do_POST(self):
        """Handle POST requests"""
        print(f"==== HTTP BRIDGE POST REQUEST TO {self.path} ====", flush=True)
        logger.info(f"POST request received: {self.path}")
        try:
            parsed_url = urlparse(self.path)
            path = parsed_url.path
            
            # Handle CORS
            self.send_response(200)
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            
            # Parse request body
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            
            if not post_data:
                self._send_error("No request data")
                return
            
            request_data = json.loads(post_data.decode('utf-8'))
            print(f"DEBUG: Received request data keys: {list(request_data.keys())}", flush=True)

            # DEBUG: Check for new prompt fields
            if 'main_prompt' in request_data:
                print(f"DEBUG: main_prompt found: '{request_data['main_prompt']}'", flush=True)
            if 'reference_prompts' in request_data:
                print(f"DEBUG: reference_prompts found: {request_data['reference_prompts']}", flush=True)

            if 'referenceImageData' in request_data:
                print(f"DEBUG: referenceImageData found in request: {len(request_data['referenceImageData'])}", flush=True)

            # Handle main processing endpoint
            if path == '/':
                # Check if this is a session context request or NLP processing
                action = request_data.get('action')
                
                if action == 'get_context':
                    # Handle session context request
                    session_id = request_data.get('session_id')
                    if not session_id:
                        self._send_error("Missing 'session_id' for get_context action")
                        return
                    
                    try:
                        # Get session context from session manager
                        session_manager = get_session_manager()
                        session_context = session_manager.get_session(session_id)
                        
                        if not session_context:
                            self._send_error(f"Session not found: {session_id}")
                            return
                        
                        # Return the session context
                        result = {
                            'context': session_context.to_dict()
                        }
                        response_json = json.dumps(result)
                        self.wfile.write(response_json.encode('utf-8'))
                        return
                        
                    except Exception as e:
                        logger.error(f"Error getting session context: {e}")
                        self._send_error(f"Failed to get session context: {e}")
                        return
                
                elif action == 'delete_session':
                    # Handle session deletion request
                    session_id = request_data.get('session_id')
                    if not session_id:
                        self._send_error("Missing 'session_id' for delete_session action")
                        return
                    
                    try:
                        # Delete session from session manager
                        session_manager = get_session_manager()
                        success = session_manager.delete_session(session_id)
                        
                        if success:
                            result = {
                                'success': True,
                                'message': f'Session {session_id} deleted successfully'
                            }
                        else:
                            result = {
                                'success': False,
                                'error': f'Session not found: {session_id}'
                            }
                        
                        response_json = json.dumps(result)
                        self.wfile.write(response_json.encode('utf-8'))
                        return
                        
                    except Exception as e:
                        logger.error(f"Error deleting session: {e}")
                        self._send_error(f"Failed to delete session: {e}")
                        return
                
                elif action == 'create_session':
                    # Handle session creation request - bypass NLP
                    session_name = request_data.get('session_name')
                    if not session_name:
                        self._send_error("Missing 'session_name' for create_session action")
                        return
                    
                    try:
                        # Create session using session manager
                        from core.session.session_context import SessionContext
                        from core.session.utils.session_helpers import generate_session_id
                        import datetime
                        
                        session_manager = get_session_manager()
                        session_id = generate_session_id()
                        now = datetime.datetime.now()
                        session_context = SessionContext(
                            session_id=session_id,
                            session_name=session_name.strip(),
                            created_at=now,
                            last_accessed=now
                        )
                        
                        # Save the session to storage
                        if not session_manager.storage.create_session(session_context):
                            self._send_error("Failed to save session to storage")
                            return
                        
                        result = {
                            'session_id': session_context.session_id,
                            'session_name': session_context.session_name,
                            'created_at': session_context.created_at.isoformat(),
                            'last_accessed': session_context.last_accessed.isoformat()
                        }
                        
                        response_json = json.dumps(result)
                        self.wfile.write(response_json.encode('utf-8'))
                        return
                        
                    except Exception as e:
                        logger.error(f"Error creating session: {e}")
                        self._send_error(f"Failed to create session: {e}")
                        return
                
                # Handle main NLP processing endpoint (only if no action or unrecognized action)
                user_input = request_data.get('prompt')
                print(f"DEBUG HTTP BRIDGE: Processing request with user_input: {user_input is not None}", flush=True)
                if user_input:
                    print(f"DEBUG HTTP BRIDGE: Entering NLP processing path", flush=True)
                    # This is an NLP request
                    context = request_data.get('context', 'User is working with Unreal Engine project')
                    session_id = request_data.get('session_id')
                    llm_model = request_data.get('llm_model')

                    # Process image data using resource processor
                    from core.resources.images import process_main_image, process_reference_images

                    images = []
                    reference_images = []
                    target_image_uid = None
                    main_image_data = None

                    try:
                        # Process main/target image (supports both UID and user upload)
                        target_image_uid, main_image_data = process_main_image(
                            main_image_request=request_data.get('mainImageData'),
                            target_image_uid=request_data.get('target_image_uid')
                        )

                        # If no image source provided, try to fetch latest image from session
                        if not target_image_uid and not main_image_data and session_id:
                            try:
                                sess_manager = get_session_manager()
                                session_context = sess_manager.get_session(session_id)
                                if session_context:
                                    latest_image_uid = session_context.get_latest_image_uid()
                                    if latest_image_uid:
                                        target_image_uid = latest_image_uid
                                        print(f"DEBUG: Auto-fetched latest image from session: {target_image_uid}", flush=True)
                                    else:
                                        print(f"DEBUG: No latest image found in session {session_id}", flush=True)
                                else:
                                    print(f"DEBUG: Session {session_id} not found", flush=True)
                            except Exception as e:
                                print(f"DEBUG: Failed to auto-fetch latest image: {e}", flush=True)

                        if target_image_uid:
                            print(f"DEBUG: Using target image UID: {target_image_uid}", flush=True)
                        elif main_image_data:
                            print(f"DEBUG: Using user-uploaded main image (in-memory, no UID)", flush=True)

                        # Process legacy images (if any)
                        raw_images = request_data.get('images', [])
                        if raw_images:
                            images = _validate_and_process_images(raw_images)

                        # Process reference images using resource processor
                        raw_reference_images = request_data.get('referenceImageData', [])
                        reference_images = None  # Initialize to avoid NameError

                        if raw_reference_images:
                            print(f"DEBUG: Processing {len(raw_reference_images)} reference images", flush=True)
                            reference_images = process_reference_images(raw_reference_images)

                            print(f"DEBUG: Successfully processed {len(reference_images)} reference images (in-memory, no UID)", flush=True)
                            for i, ref in enumerate(reference_images):
                                print(f"DEBUG: Ref {i}: {ref['mime_type']}, {len(ref['data']) // 1024}KB", flush=True)

                        # Log image processing (safely)
                        if images or reference_images or main_image_data:
                            _log_image_processing(images, reference_images)

                    except ValueError as e:
                        error_msg = f"Image validation failed (strict mode): {e}"
                        logger.error(error_msg)
                        print(f"DEBUG: {error_msg}", flush=True)
                        self._send_image_error('validation_error', str(e), 400)
                        return
                    except Exception as e:
                        error_msg = f"Unexpected error during image processing: {e}"
                        logger.error(error_msg)
                        print(f"DEBUG: {error_msg}", flush=True)
                        self._send_image_error('processing_error', str(e), 500)
                        return

                    # Process with session-aware NLP (now with image support)
                    from tools.ai.nlp import process_natural_language
                    try:
                        # Get timestamp before any potential variable shadowing
                        import datetime as _dt_module
                        current_timestamp = _dt_module.datetime.now().isoformat()
                        
                        print(f"DEBUG: Preparing NLP call with images={len(images) if images else 0}, reference_images={len(reference_images) if reference_images else 0}", flush=True)

                        # Ensure reference images are properly formatted for NLP with strict validation
                        nlp_reference_images = None
                        if reference_images:
                            nlp_reference_images = []
                            for i, ref in enumerate(reference_images):
                                # Validate data-based reference image
                                if not ref.get('data'):
                                    raise ValueError(f"Reference image {i}: Missing 'data' field")
                                if not ref.get('mime_type'):
                                    raise ValueError(f"Reference image {i}: Missing 'mime_type' field")

                                nlp_ref = {
                                    'data': ref['data'],
                                    'mime_type': ref['mime_type']
                                }

                                nlp_reference_images.append(nlp_ref)
                                print(f"DEBUG: NLP ref {i}: mime_type={ref['mime_type']}, data_length={len(ref['data'])}", flush=True)

                            print(f"DEBUG: Successfully converted {len(nlp_reference_images)} reference images for NLP", flush=True)

                        print(f"DEBUG: About to call NLP with reference_images={len(nlp_reference_images) if nlp_reference_images else 0}", flush=True)

                        # Write debug info to file to ensure we can see it
                        with open('http_bridge_debug.log', 'a') as f:
                            f.write(f"[{current_timestamp}] Calling NLP with {len(nlp_reference_images) if nlp_reference_images else 0} reference images\n")
                            if nlp_reference_images:
                                for i, ref in enumerate(nlp_reference_images):
                                    f.write(f"  Ref {i}: {len(ref.get('data', ''))} chars, type={ref.get('mime_type')}, purpose={ref.get('purpose')}\n")

                        # Extract new prompt fields from request
                        main_prompt = request_data.get('main_prompt')
                        reference_prompts = request_data.get('reference_prompts', [])

                        print(f"🔍 DEBUG: Extracted prompts from request:", flush=True)
                        print(f"  - main_prompt: '{main_prompt}'", flush=True)
                        print(f"  - reference_prompts: {reference_prompts}", flush=True)

                        # Auto-generate main_prompt if empty but reference_prompts exist
                        original_main_prompt = main_prompt
                        if ((not main_prompt or main_prompt.strip() == '') and
                            reference_prompts and
                            any(p.strip() for p in reference_prompts)):

                            # Combine reference prompts into a coherent transformation request
                            combined_prompts = ", ".join(reference_prompts)
                            main_prompt = f"Apply style transformation: {combined_prompts}"
                            print(f"DEBUG: Auto-generated main_prompt (original was empty), reference_prompts: {reference_prompts}", flush=True)

                        print(f"DEBUG: Passing to NLP - main_prompt: '{main_prompt}', reference_prompts: {reference_prompts}", flush=True)

                        result = process_natural_language(
                            user_input, context, session_id, llm_model,
                            target_image_uid=target_image_uid,
                            main_image_data=main_image_data,
                            main_prompt=main_prompt,
                            reference_prompts=reference_prompts,
                            reference_images=nlp_reference_images
                        )

                        # Verify reference images made it through to commands
                        if nlp_reference_images and result.get('commands'):
                            for i, command in enumerate(result['commands']):
                                cmd_params = command.get('params', {})
                                if 'reference_images' in cmd_params:
                                    print(f"DEBUG: Command {i} has {len(cmd_params['reference_images'])} reference images ✅", flush=True)
                                else:
                                    print(f"DEBUG: Command {i} missing reference_images ❌", flush=True)
                        
                        # Wrap the NLP result in the expected frontend structure
                        wrapped_response = {
                            "conversation_context": {
                                "user_input": user_input,
                                "timestamp": current_timestamp
                            },
                            "ai_processing": {
                                "explanation": result.get("explanation", ""),
                                "generated_commands": result.get("commands", []),
                                "expected_result": result.get("expectedResult", ""),
                                "processing_error": result.get("error"),
                                "fallback_used": result.get("fallback", False)
                            },
                            "execution_results": result.get("executionResults", []),
                            "debug_notes": {
                                "message_role": "assistant",
                                "session_context": f"Session: {session_id}" if session_id else "No session"
                            }
                        }
                        
                        # Send response back to frontend
                        response_json = json.dumps(wrapped_response, cls=SafeJSONEncoder)
                        self.wfile.write(response_json.encode('utf-8'))
                        return
                    except AppError as e:
                        # Handle structured errors with proper HTTP status
                        logger.error(f"AppError in NLP processing: {e.code} - {e.message}")
                        self._send_app_error(e)
                        return
                    except Exception as e:
                        logger.error(f"Error in NLP processing: {e}")
                        # Get timestamp for error response
                        import datetime as _dt_module2
                        error_timestamp = _dt_module2.datetime.now().isoformat()
                        error_response = {
                            "conversation_context": {
                                "user_input": user_input,
                                "timestamp": error_timestamp
                            },
                            "ai_processing": {
                                "explanation": "",
                                "generated_commands": [],
                                "expected_result": "",
                                "processing_error": str(e),
                                "fallback_used": False
                            },
                            "execution_results": [],
                            "debug_notes": {
                                "message_role": "error",
                                "session_context": f"Session: {session_id}" if session_id else "No session"
                            }
                        }
                        response_json = json.dumps(error_response, cls=SafeJSONEncoder)
                        self.wfile.write(response_json.encode('utf-8'))
                        return
                else:
                    # No action matched and no prompt provided
                    if action:
                        self._send_error(f"Unknown action: {action}")
                    else:
                        self._send_error("Missing 'prompt' field or valid 'action' field")
                    return

            # Handle other POST requests (404)
            self.send_response(404)
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Content-Type', 'application/json')
            self.end_headers()

            response = {'error': f"Endpoint not found: {path}"}
            response_json = json.dumps(response)
            self.wfile.write(response_json.encode('utf-8'))

        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in POST request: {e}")
            self._send_error(f"Invalid JSON: {e}")
        except Exception as e:
            logger.error(f"Error handling POST request: {e}")
            self._send_error(f"Server error: {e}")

    def do_PUT(self):
        """Handle PUT requests for session management"""
        logger.info(f"PUT request received: {self.path}")
        try:
            parsed_url = urlparse(self.path)
            path = parsed_url.path

            # Handle CORS
            self.send_response(200)
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            
            # Handle session name updates
            if path.startswith('/api/sessions/') and path.endswith('/name'):
                # Extract session ID from path
                path_parts = path.split('/')
                if len(path_parts) >= 4:
                    session_id = path_parts[3]
                    
                    # Parse request body
                    content_length = int(self.headers.get('Content-Length', 0))
                    put_data = self.rfile.read(content_length)
                    
                    if not put_data:
                        self._send_error("No request data")
                        return
                        
                    try:
                        request_data = json.loads(put_data.decode('utf-8'))
                        session_name = request_data.get('session_name')
                        
                        if not session_name:
                            self._send_error("Missing 'session_name' field")
                            return
                        
                        # Update session name
                        session_manager = get_session_manager()
                        storage = session_manager._get_storage()
                        
                        if not storage:
                            self._send_error("Storage backend not available")
                            return
                        
                        success = storage.update_session_name(session_id, session_name)
                        
                        if success:
                            response = {'success': True, 'session_id': session_id, 'session_name': session_name}
                        else:
                            response = {'success': False, 'error': 'Failed to update session name'}
                        
                        response_json = json.dumps(response)
                        self.wfile.write(response_json.encode('utf-8'))
                        return
                        
                    except json.JSONDecodeError as e:
                        self._send_error(f"Invalid JSON: {e}")
                        return
                    except Exception as e:
                        logger.error(f"Error updating session name: {e}")
                        self._send_error(f"Error updating session name: {e}")
                        return

            # Handle other PUT requests (404)
            self.send_response(404)
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Content-Type', 'application/json')
            self.end_headers()

            response = {'error': f"Endpoint not found: {path}"}
            response_json = json.dumps(response)
            self.wfile.write(response_json.encode('utf-8'))

        except Exception as e:
            logger.error(f"Error handling PUT request: {e}")
            self._send_error(f"Server error: {e}")

    def _serve_file(self, file_path: Path):
        """Serve a file with appropriate headers."""
        try:
            # Get file info
            file_size = file_path.stat().st_size
            content_type, _ = mimetypes.guess_type(str(file_path))
            if not content_type:
                content_type = 'application/octet-stream'

            # Send headers
            self.send_response(200)
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Content-Type', content_type)
            self.send_header('Content-Length', str(file_size))
            self.send_header('Content-Disposition', f'inline; filename="{file_path.name}"')
            self.end_headers()

            # Send file content
            with open(file_path, 'rb') as f:
                while True:
                    chunk = f.read(8192)
                    if not chunk:
                        break
                    self.wfile.write(chunk)

            logger.info(f"Served file: {file_path.name} ({file_size} bytes)")

        except Exception as e:
            logger.error(f"Error serving file {file_path}: {e}")
            self._send_error(f"Error serving file: {e}")

    def _handle_roblox_status(self, uid: str):
        """Handle Roblox download status check"""
        try:
            from api.roblox_status import get_roblox_download_status

            status = get_roblox_download_status(uid)

            self.send_response(200)
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Content-Type', 'application/json')
            self.end_headers()

            response_json = json.dumps(status, cls=SafeJSONEncoder)
            self.wfile.write(response_json.encode('utf-8'))
            logger.info(f"Served Roblox download status for: {uid}")

        except Exception as e:
            logger.error(f"Error getting Roblox status for {uid}: {e}")
            self._send_error(f"Error getting download status: {e}")

    def _handle_roblox_cancel(self, uid: str):
        """Handle Roblox download cancellation"""
        try:
            from api.roblox_status import cancel_roblox_download

            result = cancel_roblox_download(uid)

            self.send_response(200)
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Content-Type', 'application/json')
            self.end_headers()

            response_json = json.dumps(result, cls=SafeJSONEncoder)
            self.wfile.write(response_json.encode('utf-8'))
            logger.info(f"Cancelled Roblox download: {uid}")

        except Exception as e:
            logger.error(f"Error cancelling Roblox download {uid}: {e}")
            self._send_error(f"Error cancelling download: {e}")

    def _handle_roblox_file(self, uid: str, file_type: str):
        """Handle Roblox file serving"""
        try:
            from api.roblox_status import get_roblox_file

            file_path = get_roblox_file(uid, file_type)
            if file_path:
                logger.info(f"Serving Roblox file: {uid}/{file_type} -> {file_path}")
                self._serve_file(file_path)
            else:
                self._send_error(f"Roblox file not found: {uid}/{file_type}")

        except Exception as e:
            logger.error(f"Error serving Roblox file {uid}/{file_type}: {e}")
            self._send_error(f"Error serving file: {e}")

    def _handle_roblox_cleanup(self):
        """Handle Roblox cleanup operations"""
        try:
            from api.roblox_status import cleanup_roblox_jobs

            result = cleanup_roblox_jobs(24)  # Clean up jobs older than 24 hours

            self.send_response(200)
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Content-Type', 'application/json')
            self.end_headers()

            response_json = json.dumps(result, cls=SafeJSONEncoder)
            self.wfile.write(response_json.encode('utf-8'))
            logger.info("Completed Roblox cleanup operation")

        except Exception as e:
            logger.error(f"Error during Roblox cleanup: {e}")
            self._send_error(f"Error during cleanup: {e}")

    def _send_error(self, error_message: str, status_code: int = 500):
        """Send an error response"""
        try:
            self.send_response(status_code)
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Content-Type', 'application/json')
            self.end_headers()

            response = {'error': error_message}
            response_json = json.dumps(response)
            self.wfile.write(response_json.encode('utf-8'))
        except Exception as e:
            logger.error(f"Error sending error response: {e}")

    def _send_app_error(self, error: AppError):
        """Send AppError with proper HTTP status code and structured response"""
        try:
            # Get HTTP status code from error category
            status_code = CATEGORY_STATUS_MAP.get(error.category, 500)

            # Log the error
            error.log()

            # Send HTTP response
            response_dict = error.to_response()
            self.send_response(status_code)
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Content-Type', 'application/json')
            self.end_headers()

            response_json = json.dumps(response_dict)
            self.wfile.write(response_json.encode('utf-8'))
        except Exception as e:
            logger.error(f"Error sending AppError response: {e}")
            self._send_error(str(e))

    def _send_image_error(self, error_type: str, message: str, status_code: int = 400):
        """
        Send standardized image processing error response.

        Args:
            error_type: Error category ('size_limit', 'invalid_mime', 'decode_error', etc.)
            message: Human-readable error message
            status_code: HTTP status code (default 400)
        """
        try:
            self.send_response(status_code)
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Content-Type', 'application/json')
            self.end_headers()

            response = {
                'error': message,
                'error_type': error_type,
                'status_code': status_code
            }
            response_json = json.dumps(response)
            self.wfile.write(response_json.encode('utf-8'))
        except Exception as e:
            logger.error(f"Error sending image error response: {e}")

    def _handle_get_tools(self):
        """Handle GET /tools request - return all available tools"""
        try:
            from core import get_registry, get_config

            config = get_config()

            # Check if plugin system is enabled
            if not config.features.enable_plugin_system:
                # Return legacy fallback
                tools = [
                    {
                        'tool_id': 'unreal_engine',
                        'display_name': 'Unreal Engine',
                        'version': '5.5.4',
                        'description': 'Real-time 3D creation',
                        'icon': '🎮',
                        'status': 'available',
                        'capabilities': ['rendering', 'lighting', 'camera']
                    },
                    {
                        'tool_id': 'nano_banana',
                        'display_name': 'Nano Banana',
                        'version': '1.0.0',
                        'description': 'AI image generation & editing',
                        'icon': '🍌',
                        'status': 'available',
                        'capabilities': ['image_editing', 'style_transfer']
                    }
                ]
                response = {
                    'tools': tools,
                    'source': 'legacy',
                    'plugin_system_enabled': False
                }
            else:
                # Use plugin registry
                registry = get_registry()
                metadata_dict = registry.get_all_metadata()
                health_status = registry.get_health_status()

                tools = []
                for tool_id, metadata in metadata_dict.items():
                    tool_data = {
                        'tool_id': metadata.tool_id,
                        'display_name': metadata.display_name,
                        'version': metadata.version,
                        'description': metadata.description,
                        'icon': metadata.icon,
                        'status': health_status.get(tool_id, 'unavailable').value if tool_id in health_status else 'unavailable',
                        'capabilities': [cap.value for cap in metadata.capabilities],
                        'requires_connection': metadata.requires_connection,
                        'pricing_tier': metadata.pricing_tier
                    }
                    tools.append(tool_data)

                response = {
                    'tools': tools,
                    'source': 'plugin_registry',
                    'plugin_system_enabled': True
                }

            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(response).encode('utf-8'))

        except Exception as e:
            logger.error(f"Error handling /tools request: {e}")
            self._send_error(f"Failed to get tools: {str(e)}", status_code=500)

    def _handle_get_tool_info(self, tool_id: str):
        """Handle GET /tools/{tool_id} request - return specific tool info"""
        try:
            from core import get_registry, get_config

            config = get_config()

            if not config.features.enable_plugin_system:
                self._send_error("Plugin system not enabled", status_code=501)
                return

            registry = get_registry()
            metadata = registry.get_all_metadata().get(tool_id)

            if not metadata:
                self._send_error(f"Tool not found: {tool_id}", status_code=404)
                return

            # Get tool instance for detailed info
            tool = registry.get_tool(tool_id)
            health = tool.health_check() if tool else 'unavailable'

            response = {
                'tool_id': metadata.tool_id,
                'display_name': metadata.display_name,
                'version': metadata.version,
                'description': metadata.description,
                'icon': metadata.icon,
                'status': health.value if hasattr(health, 'value') else str(health),
                'capabilities': [cap.value for cap in metadata.capabilities],
                'requires_connection': metadata.requires_connection,
                'pricing_tier': metadata.pricing_tier,
                'supported_commands': tool.get_supported_commands() if tool else []
            }

            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(response).encode('utf-8'))

        except Exception as e:
            logger.error(f"Error handling /tools/{tool_id} request: {e}")
            self._send_error(f"Failed to get tool info: {str(e)}", status_code=500)

    def _handle_tools_health(self):
        """Handle GET /tools/health request - return health status of all tools"""
        try:
            from core import get_registry, get_config

            config = get_config()

            if not config.features.enable_plugin_system:
                response = {
                    'plugin_system_enabled': False,
                    'message': 'Plugin system not enabled, using legacy handlers'
                }
            else:
                registry = get_registry()
                health_status = registry.get_health_status()

                response = {
                    'plugin_system_enabled': True,
                    'tools': {
                        tool_id: status.value
                        for tool_id, status in health_status.items()
                    }
                }

            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(response).encode('utf-8'))

        except Exception as e:
            logger.error(f"Error handling /tools/health request: {e}")
            self._send_error(f"Failed to get health status: {str(e)}", status_code=500)

    def _handle_3d_object_file(self, uid: str):
        """Handle GET /3d-object/{uid} request - serve 3D object files"""
        try:
            from core.resources.uid_manager import get_uid_mapping
            from pathlib import Path

            # Get file path from UID mapping
            mapping = get_uid_mapping(uid)

            if not mapping:
                self._send_error(f"3D object not found: {uid}", status_code=404)
                return

            file_path = Path(mapping.get('file_path', ''))

            if not file_path.exists():
                self._send_error(f"3D object file not found: {file_path}", status_code=404)
                return

            # Determine content type based on UID prefix or file extension
            content_type = 'application/octet-stream'
            if uid.startswith('fbx_') or file_path.suffix.lower() == '.fbx':
                content_type = 'application/octet-stream'
            elif uid.startswith('obj_') or file_path.suffix.lower() == '.obj':
                content_type = 'text/plain'
            elif file_path.suffix.lower() in ['.gltf', '.gltf']:
                content_type = 'model/gltf+json'
            elif file_path.suffix.lower() == '.glb':
                content_type = 'model/gltf-binary'

            # Read and serve file
            with open(file_path, 'rb') as f:
                file_data = f.read()

            self.send_response(200)
            self.send_header('Content-Type', content_type)
            self.send_header('Content-Disposition', f'attachment; filename="{file_path.name}"')
            self.send_header('Content-Length', str(len(file_data)))
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Cache-Control', 'public, max-age=31536000')
            self.end_headers()
            self.wfile.write(file_data)

            logger.info(f"Served 3D object: {uid} ({file_path.name})")

        except Exception as e:
            logger.error(f"Error serving 3D object {uid}: {e}")
            self._send_error(f"Failed to serve 3D object: {str(e)}", status_code=500)


class MCPHttpBridge:
    """HTTP Bridge Server for MCP communication."""

    def __init__(self, host='127.0.0.1', port=8080):
        self.host = host
        self.port = port
        self.server = None
        logger.info("MCP HTTP Bridge initialized")
    
    def start_server(self):
        """Start the HTTP server"""
        try:
            self.server = ThreadingHTTPServer((self.host, self.port), MCPBridgeHandler)
            logger.info(f"MCP HTTP Bridge started on http://{self.host}:{self.port}")
            logger.info("HTTP Bridge running. Press Ctrl+C to stop.")
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
            logger.info("MCP HTTP Bridge stopped")


def main():
    """Main entry point"""
    try:
        bridge = MCPHttpBridge()
        bridge.start_server()
    except Exception as e:
        logger.error(f"Failed to start MCP HTTP Bridge: {e}")
        return 1
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())