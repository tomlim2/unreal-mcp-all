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
from http.server import HTTPServer, BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs
from pathlib import Path
import threading
from typing import Dict, Any, Optional

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Import session management
from tools.ai.session_management import SessionManager, SessionContext, get_session_manager
from tools.ai.session_management.utils.session_helpers import extract_session_id_from_request, generate_session_id

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("MCPHttpBridge")


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
        # For screenshot files, we can handle HEAD requests efficiently
        parsed_url = urlparse(self.path)
        path = parsed_url.path
        
        if path.startswith('/api/screenshot-file/'):
            # Handle HEAD request for screenshot files
            path_parts = path.split('/')
            if len(path_parts) == 4 and path_parts[1] == 'api' and path_parts[2] == 'screenshot-file':
                filename = path_parts[3]
                try:
                    # Get project path from environment
                    project_path = os.getenv('UNREAL_PROJECT_PATH')
                    if not project_path:
                        self.send_response(500)
                        self.send_header('Access-Control-Allow-Origin', '*')
                        self.end_headers()
                        return
                    
                    # Build path to screenshot file - check both WindowsEditor and styled directories  
                    screenshot_dir = Path(project_path) / "Saved" / "Screenshots" / "WindowsEditor"
                    styled_dir = Path(project_path) / "Saved" / "Screenshots" / "styled"
                    
                    file_path = screenshot_dir / filename
                    if not file_path.exists():
                        # Try styled directory if not found in WindowsEditor
                        file_path = styled_dir / filename
                    
                    # Check if file exists
                    if file_path.exists() and filename.lower().endswith('.png'):
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
        
        # For other paths, return 501 Not Implemented
        self.send_response(501)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
    
    def do_GET(self):
        """Handle GET requests"""
        logger.info(f"GET request received: {self.path}")
        try:
            # Parse URL path first
            parsed_url = urlparse(self.path)
            path = parsed_url.path
            
            # Handle file requests first (before sending any headers)
            if path.startswith('/api/screenshot-file/'):
                # Handle direct screenshot file serving: /api/screenshot-file/{filename}
                path_parts = path.split('/')
                if len(path_parts) == 4 and path_parts[1] == 'api' and path_parts[2] == 'screenshot-file':
                    filename = path_parts[3]
                    try:
                        # Get project path from environment
                        project_path = os.getenv('UNREAL_PROJECT_PATH')
                        if not project_path:
                            self._send_error("UNREAL_PROJECT_PATH not configured")
                            return
                        
                        # Build path to screenshot file - check both WindowsEditor and styled directories
                        screenshot_dir = Path(project_path) / "Saved" / "Screenshots" / "WindowsEditor"
                        styled_dir = Path(project_path) / "Saved" / "Screenshots" / "styled"
                        
                        file_path = screenshot_dir / filename
                        if not file_path.exists():
                            # Try styled directory if not found in WindowsEditor
                            file_path = styled_dir / filename
                        
                        # Validate file exists and is a PNG
                        if not file_path.exists():
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

            # Handle JSON API requests (send JSON headers)
            self.send_response(200)
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Content-Type', 'application/json')
            self.end_headers()

            if path == '/health':
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

            # Handle other GET requests (404)
            self.send_response(404)
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self._send_error(f"Endpoint not found: {path}")

        except Exception as e:
            logger.error(f"Error handling GET request: {e}")
            self._send_error(f"Server error: {e}")
    
    def do_POST(self):
        """Handle POST requests"""
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
                        from tools.ai.session_management.session_context import SessionContext
                        from tools.ai.session_management.utils.session_helpers import generate_session_id
                        from datetime import datetime
                        
                        session_manager = get_session_manager()
                        session_id = generate_session_id()
                        now = datetime.now()
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
                if user_input:
                    # This is an NLP request
                    context = request_data.get('context', 'User is working with Unreal Engine project')
                    session_id = request_data.get('session_id')
                    llm_model = request_data.get('llm_model')
                    
                    # Process with session-aware NLP
                    from tools.ai.nlp import process_natural_language
                    result = process_natural_language(
                        user_input, context, session_id, llm_model
                    )
                    
                    # Send response back to frontend
                    response_json = json.dumps(result)
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
            self._send_error(f"Endpoint not found: {path}")

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
            self._send_error(f"Endpoint not found: {path}")

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

    def _send_error(self, error_message: str):
        """Send an error response"""
        try:
            self.send_response(500)
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Content-Type', 'application/json')
            self.end_headers()

            response = {'error': error_message}
            response_json = json.dumps(response)
            self.wfile.write(response_json.encode('utf-8'))
        except Exception as e:
            logger.error(f"Error sending error response: {e}")


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