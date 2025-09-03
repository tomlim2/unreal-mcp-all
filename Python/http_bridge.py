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
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs, unquote
from pathlib import Path
import threading
from typing import Dict, Any, Optional

# Import the UnrealConnection from the main server
from unreal_mcp_server import get_unreal_connection, UnrealConnection

# Import session management
from tools.ai.session_management import SessionManager, SessionContext, get_session_manager
from tools.ai.session_management.utils.session_helpers import extract_session_id_from_request, generate_session_id

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("MCPHttpBridge")

# Global cache for screenshot paths from C++ responses
_screenshot_path_cache = {}

def cache_screenshot_path(filename: str, file_path: str):
    """Cache a screenshot file path from C++ response for later retrieval."""
    global _screenshot_path_cache
    _screenshot_path_cache[filename] = file_path
    logger.info(f"Cached screenshot path: {filename} -> {file_path}")

class MCPBridgeHandler(BaseHTTPRequestHandler):
    """HTTP request handler for MCP bridge"""
    
    def _resolve_screenshot_path(self, filename: str) -> Path:
        """Resolve screenshot file path using multiple methods in order of preference."""
        # Method 1: Check if we have cached path from C++ response
        if filename in _screenshot_path_cache:
            cached_path = Path(_screenshot_path_cache[filename])
            if cached_path.exists():
                logger.info(f"Found screenshot using cached C++ response: {cached_path}")
                return cached_path
            else:
                # Remove stale cache entry
                del _screenshot_path_cache[filename]
        
        # Method 2: Use UNREAL_PROJECT_PATH environment variable
        unreal_project_path = os.getenv("UNREAL_PROJECT_PATH")
        if unreal_project_path:
            project_path = Path(unreal_project_path)
            if project_path.exists() and project_path.is_dir():
                screenshot_path = project_path / "Saved" / "Screenshots" / filename
                if screenshot_path.exists():
                    logger.info(f"Found screenshot using UNREAL_PROJECT_PATH: {screenshot_path}")
                    return screenshot_path
        
        # Method 3: Auto-discovery - search for .uproject files
        current_dir = Path(__file__).parent.parent
        for search_path in [current_dir, current_dir.parent]:
            # Look for .uproject files
            uproject_files = list(search_path.glob("*.uproject"))
            if uproject_files:
                project_dir = uproject_files[0].parent
                screenshot_path = project_dir / "Saved" / "Screenshots" / filename
                if screenshot_path.exists():
                    logger.info(f"Found screenshot using auto-discovery: {screenshot_path}")
                    return screenshot_path
            
            # Look for subdirectories with .uproject files
            for subdir in search_path.iterdir():
                if subdir.is_dir():
                    uproject_files = list(subdir.glob("*.uproject"))
                    if uproject_files:
                        project_dir = uproject_files[0].parent
                        screenshot_path = project_dir / "Saved" / "Screenshots" / filename
                        if screenshot_path.exists():
                            logger.info(f"Found screenshot using auto-discovery in {subdir}: {screenshot_path}")
                            return screenshot_path
        
        # Method 4: Fallback to legacy hardcoded path
        legacy_path = current_dir / "MCPGameProject" / "Saved" / "Screenshots" / filename
        logger.warning(f"Using fallback legacy path (may not exist): {legacy_path}")
        return legacy_path
    
    def do_OPTIONS(self):
        """Handle CORS preflight requests"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, GET, PUT, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    def do_GET(self):
        """Handle GET requests"""
        try:
            # Handle CORS
            self.send_response(200)
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            
            # Parse URL path
            parsed_url = urlparse(self.path)
            path = parsed_url.path
            
            if path == '/sessions':
                # Handle sessions list request with pagination support
                try:
                    # Parse query parameters for pagination
                    query_params = parse_qs(parsed_url.query)
                    limit = int(query_params.get('limit', [50])[0])  # Default 50
                    offset = int(query_params.get('offset', [0])[0])  # Default 0
                    
                    # Validate pagination parameters
                    if limit < 1 or limit > 100:
                        self._send_error("Invalid limit. Must be between 1 and 100")
                        return
                    if offset < 0:
                        self._send_error("Invalid offset. Must be 0 or greater")
                        return
                    
                    session_manager = get_session_manager()
                    
                    # Get paginated sessions
                    logger.info(f"Requesting sessions with limit={limit}, offset={offset}")
                    sessions = session_manager.list_sessions(limit=limit, offset=offset)
                    total_count = session_manager.get_session_count()
                    logger.info(f"Retrieved {len(sessions)} sessions out of {total_count} total")
                    
                    # Convert sessions to JSON-serializable format
                    sessions_data = []
                    for session in sessions:
                        # Calculate interaction count (each interaction = 1 user + 1 assistant message)
                        # Count user messages as interactions since each user message triggers an assistant response
                        interaction_count = 0
                        if session.conversation_history:
                            interaction_count = len([msg for msg in session.conversation_history if msg.role == 'user'])
                        
                        sessions_data.append({
                            'session_id': session.session_id,
                            'session_name': session.session_name,
                            'llm_model': session.llm_model,
                            'created_at': session.created_at.isoformat() if session.created_at else None,
                            'last_accessed': session.last_accessed.isoformat() if session.last_accessed else None,
                            'interaction_count': interaction_count
                        })
                    
                    # Build response with pagination metadata
                    response = {
                        'sessions': sessions_data,
                        'pagination': {
                            'limit': limit,
                            'offset': offset,
                            'total': total_count,
                            'returned': len(sessions_data),
                            'has_more': offset + len(sessions_data) < total_count
                        }
                    }
                    response_json = json.dumps(response)
                    self.wfile.write(response_json.encode('utf-8'))
                    return
                    
                except Exception as e:
                    logger.error(f"Error listing sessions: {e}")
                    self._send_error(f"Error listing sessions: {e}")
                    return
            
            elif path == '/session-ids':
                # Handle session IDs list request (just the IDs, ordered by last_accessed)
                try:
                    session_manager = get_session_manager()
                    sessions = session_manager.list_sessions()
                    
                    # Sort sessions by last_accessed date (most recent first)
                    sessions_sorted = sorted(sessions, 
                                           key=lambda s: s.last_accessed if s.last_accessed else s.created_at, 
                                           reverse=True)
                    
                    # Extract just the session IDs in sorted order
                    session_ids = [{'session_id': session.session_id,'session_name': session.session_name} for session in sessions_sorted]
                    response = {'session_ids': session_ids}
                    response_json = json.dumps(response)
                    self.wfile.write(response_json.encode('utf-8'))
                    return
                    
                except Exception as e:
                    logger.error(f"Error listing session IDs: {e}")
                    self._send_error(f"Error listing session IDs: {e}")
                    return
            
            elif path.startswith('/screenshots/'):
                # Handle screenshot file serving
                try:
                    # Extract filename from path: /screenshots/{filename}
                    filename = path[len('/screenshots/'):]
                    filename = unquote(filename)  # Decode URL encoding
                    
                    # Validate filename for security
                    if not filename or '..' in filename or '/' in filename or '\\' in filename:
                        self.send_response(400)
                        self.send_header('Access-Control-Allow-Origin', '*')
                        self.send_header('Content-Type', 'application/json')
                        self.end_headers()
                        self._send_error("Invalid filename")
                        return
                    
                    # Construct file path using multi-method resolution
                    screenshot_path = self._resolve_screenshot_path(filename)
                    
                    # Check if file exists
                    if not screenshot_path.exists() or not screenshot_path.is_file():
                        self.send_response(404)
                        self.send_header('Access-Control-Allow-Origin', '*')
                        self.send_header('Content-Type', 'application/json')
                        self.end_headers()
                        self._send_error(f"Screenshot not found: {filename}")
                        return
                    
                    # Get file stats
                    file_size = screenshot_path.stat().st_size
                    
                    # Determine MIME type
                    mime_type, _ = mimetypes.guess_type(str(screenshot_path))
                    if mime_type is None:
                        mime_type = 'application/octet-stream'
                    
                    # Send response headers
                    self.send_response(200)
                    self.send_header('Access-Control-Allow-Origin', '*')
                    self.send_header('Content-Type', mime_type)
                    self.send_header('Content-Length', str(file_size))
                    self.send_header('Cache-Control', 'public, max-age=3600')  # Cache for 1 hour
                    self.end_headers()
                    
                    # Send file content
                    with open(screenshot_path, 'rb') as f:
                        chunk_size = 8192
                        while True:
                            chunk = f.read(chunk_size)
                            if not chunk:
                                break
                            self.wfile.write(chunk)
                    
                    logger.info(f"Served screenshot: {filename} ({file_size} bytes)")
                    return
                    
                except Exception as e:
                    logger.error(f"Error serving screenshot {filename}: {e}")
                    self.send_response(500)
                    self.send_header('Access-Control-Allow-Origin', '*')
                    self.send_header('Content-Type', 'application/json')
                    self.end_headers()
                    self._send_error(f"Error serving screenshot: {e}")
                    return
            
            # Handle other GET requests (404)
            self.send_response(404)
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self._send_error(f"Endpoint not found: {path}")
            
        except Exception as e:
            logger.error(f"Error handling GET request: {e}")
            self._send_error(f"Server error: {e}")
    
    def do_PUT(self):
        """Handle PUT requests"""
        try:
            # Handle CORS
            self.send_response(200)
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            
            # Parse URL path
            parsed_url = urlparse(self.path)
            path = parsed_url.path
            
            if path.startswith('/sessions/') and path.endswith('/name'):
                # Handle update session name request
                # Extract session_id from path: /sessions/{session_id}/name
                path_parts = path.split('/')
                if len(path_parts) == 4 and path_parts[1] == 'sessions' and path_parts[3] == 'name':
                    session_id = path_parts[2]
                    
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
            self._send_error(f"Endpoint not found: {path}")
            
        except Exception as e:
            logger.error(f"Error handling PUT request: {e}")
            self._send_error(f"Server error: {e}")
    
    def do_DELETE(self):
        """Handle DELETE requests"""
        try:
            # Handle CORS
            self.send_response(200)
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            
            # Parse request body
            content_length = int(self.headers.get('Content-Length', 0))
            delete_data = self.rfile.read(content_length)
            
            if not delete_data:
                self._send_error("No request data")
                return
                
            try:
                request_data = json.loads(delete_data.decode('utf-8'))
                session_id = request_data.get('session_id')
                action = request_data.get('action')
                
                if not session_id or action != 'delete_session':
                    self._send_error("Missing 'session_id' or invalid 'action' field")
                    return
                
                # Delete session
                session_manager = get_session_manager()
                success = session_manager.delete_session(session_id)
                
                if success:
                    response = {
                        'success': True,
                        'session_id': session_id,
                        'message': 'Session deleted successfully'
                    }
                    logger.info(f"Deleted session: {session_id}")
                else:
                    response = {
                        'success': False,
                        'error': 'Failed to delete session'
                    }
                
                response_json = json.dumps(response)
                self.wfile.write(response_json.encode('utf-8'))
                return
                
            except json.JSONDecodeError as e:
                self._send_error(f"Invalid JSON: {e}")
                return
            except Exception as e:
                logger.error(f"Error deleting session: {e}")
                self._send_error(f"Error deleting session: {e}")
                return
            
        except Exception as e:
            logger.error(f"Error handling DELETE request: {e}")
            self._send_error(f"Server error: {e}")
    
    def do_POST(self):
        """Handle POST requests"""
        try:
            # Handle CORS
            self.send_response(200)
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            
            # Parse request
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            
            if not post_data:
                self._send_error("No request data")
                return
                
            try:
                request_data = json.loads(post_data.decode('utf-8'))
                logger.info(f"Received HTTP request: {request_data}")
            except json.JSONDecodeError as e:
                self._send_error(f"Invalid JSON: {e}")
                return
            
            # Check if this is a session context request
            if 'session_id' in request_data and request_data.get('action') == 'get_context':
                # Handle session context fetch
                logger.info("Processing session context request")
                try:
                    session_id = request_data.get('session_id')
                    
                    if not session_id:
                        self._send_error("Missing 'session_id' field")
                        return
                    
                    # Get session context
                    session_manager = get_session_manager()
                    session_context = session_manager.get_session(session_id)
                    
                    if not session_context:
                        self._send_error("Session not found")
                        return
                    
                    # Return the full session context
                    response = {
                        'success': True,
                        'context': session_context.to_dict()
                    }
                    logger.info(f"Retrieved context for session: {session_id}")
                    
                    response_json = json.dumps(response)
                    self.wfile.write(response_json.encode('utf-8'))
                    return
                    
                except Exception as e:
                    logger.error(f"Error retrieving session context: {e}")
                    self._send_error(f"Context retrieval error: {e}")
                    return
            
            # Check if this is a session creation request (handle before other checks)
            if 'session_name' in request_data and 'prompt' not in request_data:
                # Handle session creation
                logger.info("Processing session creation request")
                try:
                    session_name = request_data.get('session_name')
                    
                    if not session_name:
                        self._send_error("Missing 'session_name' field")
                        return
                    
                    # Create new session with server-generated ID
                    session_manager = get_session_manager()
                    # Let session_manager generate the ID (pass None)
                    session_context = session_manager.create_session(None)
                    
                    if not session_context:
                        self._send_error("Failed to create session")
                        return
                    
                    # Set the session name
                    session_context.session_name = session_name
                    success = session_manager.update_session(session_context)
                    
                    if success:
                        response = {
                            'success': True,
                            'session_id': session_context.session_id,
                            'session_name': session_name,
                            'llm_model': session_context.llm_model,
                            'created_at': session_context.created_at.isoformat(),
                        }
                        logger.info(f"Created session {session_context.session_id} with name '{session_name}'")
                    else:
                        response = {
                            'success': False,
                            'error': 'Failed to update session with name'
                        }
                    
                    response_json = json.dumps(response)
                    self.wfile.write(response_json.encode('utf-8'))
                    return
                    
                except Exception as e:
                    logger.error(f"Error creating session: {e}")
                    self._send_error(f"Session creation error: {e}")
                    return
            
            # Check if this is a natural language request
            if 'prompt' in request_data:
                # Handle natural language processing with session management
                logger.info("Processing natural language request with session support")
                try:
                    from tools.ai.nlp import process_natural_language, ANTHROPIC_AVAILABLE
                    logger.info(f"Import successful. ANTHROPIC_AVAILABLE = {ANTHROPIC_AVAILABLE}")
                    
                    user_input = request_data.get('prompt', '')
                    context = request_data.get('context', 'User is working with Unreal Engine project')
                    llm_model = request_data.get('llm_model')  # Optional model parameter
                    
                    if not user_input:
                        self._send_error("Missing 'prompt' field")
                        return
                    
                    # Extract session ID from request - preserve if provided
                    session_id = request_data.get('session_id')
                    logger.info(f"Session ID from request: {session_id}")
                    logger.info(f"Model from request: {llm_model}")
                    
                    if session_id:
                        # Use the provided session ID (don't validate format strictly)
                        logger.info(f"Using provided session ID: {session_id}")
                    else:
                        # Only generate new session ID if none was provided
                        session_id = generate_session_id()
                        logger.info(f"No session ID provided, generated new one: {session_id}")
                    
                    # Process natural language with session context and model preference
                    logger.info(f"Calling NLP function with input: {user_input[:50]}... using model: {llm_model or 'default'}")
                    result = process_natural_language(user_input, context, session_id, llm_model)
                    logger.info(f"NLP response: {result}")
                    
                    # Include session_id in response for frontend
                    if result and not result.get('error'):
                        result['session_id'] = session_id
                    
                    # Send response back to frontend
                    response_json = json.dumps(result)
                    self.wfile.write(response_json.encode('utf-8'))
                    return
                    
                except Exception as e:
                    logger.error(f"Error in NLP processing: {e}")
                    self._send_error(f"NLP processing error: {e}")
                    return
            
            # Handle direct command execution (legacy support)
            command_type = request_data.get('type')
            params = request_data.get('params', {})
            
            if not command_type:
                self._send_error("Missing 'type' or 'prompt' field")
                return
            
            # Execute command via Unreal connection
            connection = get_unreal_connection()
            if not connection:
                self._send_error("Could not connect to Unreal Engine")
                return
            
            result = connection.send_command(command_type, params)
            if not result:
                self._send_error("No response from Unreal Engine")
                return
            
            logger.info(f"Unreal response: {result}")
            
            # Send response back to frontend
            response_json = json.dumps(result)
            self.wfile.write(response_json.encode('utf-8'))
            
        except Exception as e:
            logger.error(f"Error handling POST request: {e}")
            self._send_error(f"Server error: {e}")
    
    def _send_error(self, message: str):
        """Send error response"""
        error_response = {
            "status": "error",
            "error": message,
            "timestamp": "2025-08-11T23:51:31.676Z"
        }
        response_json = json.dumps(error_response)
        self.wfile.write(response_json.encode('utf-8'))
    
    def log_message(self, format, *args):
        """Override to reduce HTTP server logging noise"""
        logger.debug(format % args)

class MCPHttpBridge:
    """HTTP bridge server for MCP"""
    
    def __init__(self, port: int = 8080):
        self.port = port
        self.server = None
        self.server_thread = None
    
    def start(self):
        """Start the HTTP server"""
        try:
            self.server = HTTPServer(('127.0.0.1', self.port), MCPBridgeHandler)
            self.server_thread = threading.Thread(target=self.server.serve_forever)
            self.server_thread.daemon = True
            self.server_thread.start()
            logger.info(f"MCP HTTP Bridge started on http://127.0.0.1:{self.port}")
            return True
        except Exception as e:
            logger.error(f"Failed to start HTTP bridge: {e}")
            return False
    
    def stop(self):
        """Stop the HTTP server"""
        if self.server:
            self.server.shutdown()
            self.server.server_close()
            if self.server_thread:
                self.server_thread.join(timeout=5)
            logger.info("MCP HTTP Bridge stopped")

if __name__ == "__main__":
    # Start the bridge
    bridge_port = int(os.getenv("HTTP_BRIDGE_PORT", "8080"))
    bridge = MCPHttpBridge(port=bridge_port)
    
    if bridge.start():
        logger.info("HTTP Bridge running. Press Ctrl+C to stop.")
        try:
            # Keep the main thread alive
            while True:
                import time
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("Shutting down HTTP Bridge...")
            bridge.stop()
    else:
        logger.error("Failed to start HTTP Bridge")