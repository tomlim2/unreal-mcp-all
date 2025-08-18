#!/usr/bin/env python3
"""
HTTP Bridge for Unreal MCP Server
Provides HTTP endpoint for frontend to communicate with MCP server
"""

import json
import logging
import asyncio
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import threading
from typing import Dict, Any, Optional

# Import the UnrealConnection from the main server
from unreal_mcp_server import get_unreal_connection, UnrealConnection

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("MCPHttpBridge")

class MCPBridgeHandler(BaseHTTPRequestHandler):
    """HTTP request handler for MCP bridge"""
    
    def do_OPTIONS(self):
        """Handle CORS preflight requests"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
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
            
            # Check if this is a natural language request
            if 'prompt' in request_data:
                # Handle natural language processing
                logger.info("Processing natural language request")
                try:
                    from tools.ai.nlp import _process_natural_language_impl, ANTHROPIC_AVAILABLE
                    logger.info(f"Import successful. ANTHROPIC_AVAILABLE = {ANTHROPIC_AVAILABLE}")
                    
                    user_input = request_data.get('prompt', '')
                    context = request_data.get('context', 'User is working with Unreal Engine project')
                    
                    if not user_input:
                        self._send_error("Missing 'prompt' field")
                        return
                    
                    # Process natural language using the implementation function
                    logger.info(f"Calling NLP function with input: {user_input[:50]}...")
                    result = _process_natural_language_impl(user_input, context)
                    logger.info(f"NLP response: {result}")
                    
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
    bridge = MCPHttpBridge(port=8080)
    
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