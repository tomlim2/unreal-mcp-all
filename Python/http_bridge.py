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
from urllib.parse import urlparse, parse_qs
from pathlib import Path
import threading
from typing import Dict, Any, Optional

# Import worker infrastructure
from tools.workers import JobManager, JobStatus, ScreenshotWorker

# Import the UnrealConnection from the main server
from unreal_mcp_server import get_unreal_connection, UnrealConnection

# Import session management
from tools.ai.session_management import SessionManager, SessionContext, get_session_manager
from tools.ai.session_management.utils.session_helpers import extract_session_id_from_request, generate_session_id

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("MCPHttpBridge")

# Global worker instances (will be initialized in MCPHttpBridge)
job_manager = None
screenshot_worker = None

def get_job_system():
    """Get the job system components (job_manager, screenshot_worker)."""
    global job_manager, screenshot_worker
    return job_manager, screenshot_worker

def _initialize_global_job_system():
    """Initialize global job system for module imports."""
    global job_manager, screenshot_worker
    
    if job_manager is not None and screenshot_worker is not None:
        return  # Already initialized
    
    try:
        # Initialize job manager with Supabase if available
        supabase_client = None
        try:
            from tools.ai.session_management.storage.supabase_storage import SupabaseStorage
            supabase_storage = SupabaseStorage()
            supabase_client = supabase_storage.supabase
            logger.info("Initialized global job manager with Supabase backend")
        except Exception as e:
            logger.warning(f"Could not initialize Supabase for global job manager: {e}")
        
        job_manager = JobManager(supabase_client)
        
        # Get Unreal connection for screenshot worker
        try:
            unreal_connection = get_unreal_connection()
            print(f"DEBUG: Got unreal_connection: {unreal_connection is not None}")
            screenshot_worker = ScreenshotWorker(
                job_manager=job_manager,
                unreal_connection=unreal_connection
            )
            print(f"DEBUG: Screenshot worker created successfully")
            logger.info("Screenshot worker initialized with Unreal connection")
        except Exception as e:
            print(f"DEBUG: Screenshot worker initialization failed: {e}")
            print(f"DEBUG: Trying to create screenshot worker without Unreal connection...")
            try:
                # Create screenshot worker without Unreal connection (will be set later)
                screenshot_worker = ScreenshotWorker(
                    job_manager=job_manager,
                    unreal_connection=None
                )
                print(f"DEBUG: Screenshot worker created without Unreal connection")
                logger.warning(f"Screenshot worker initialized without Unreal connection: {e}")
            except Exception as e2:
                print(f"DEBUG: Screenshot worker creation failed completely: {e2}")
                screenshot_worker = None
        
        logger.info("Global job system initialized successfully")
        
    except Exception as e:
        logger.error(f"Failed to initialize global job system: {e}")

# Initialize job system when module is imported
_initialize_global_job_system()

class MCPBridgeHandler(BaseHTTPRequestHandler):
    """HTTP request handler for MCP bridge"""
    
    def do_OPTIONS(self):
        """Handle CORS preflight requests"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, GET, PUT, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    def do_GET(self):
        """Handle GET requests"""
        global job_manager, screenshot_worker
        try:
            # Handle CORS
            self.send_response(200)
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            
            # Parse URL path
            parsed_url = urlparse(self.path)
            path = parsed_url.path
            
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
                
            elif path == '/debug-jobs':
                # Debug: List all jobs in job_manager
                if not job_manager:
                    self._send_error("Job manager not available")
                    return
                    
                jobs = job_manager.list_active_jobs()
                response = {
                    'total_jobs': len(jobs),
                    'jobs': [
                        {
                            'job_id': job.job_id,
                            'job_type': job.job_type,
                            'status': job.status.name.lower(),
                            'created_at': job.created_at.isoformat() if job.created_at else None,
                            'progress': job.progress
                        } for job in jobs
                    ]
                }
                response_json = json.dumps(response)
                self.wfile.write(response_json.encode('utf-8'))
                return
                
            elif path == '/test-job-system':
                # Test job system availability
                job_manager, screenshot_worker = get_job_system()
                response = {
                    'job_system_status': {
                        'job_manager_available': job_manager is not None,
                        'screenshot_worker_available': screenshot_worker is not None,
                        'both_available': job_manager is not None and screenshot_worker is not None
                    },
                    'debug_info': {
                        'job_manager_type': str(type(job_manager)) if job_manager else None,
                        'screenshot_worker_type': str(type(screenshot_worker)) if screenshot_worker else None,
                    }
                }
                response_json = json.dumps(response)
                self.wfile.write(response_json.encode('utf-8'))
                return
            
            elif path == '/sessions':
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
            
            # Generic job endpoints
            elif path == '/api/job':
                # Handle generic job status requests
                query_params = parse_qs(parsed_url.query)
                job_id = query_params.get('job_id')
                
                if job_id and len(job_id) > 0:
                    job_id = job_id[0]
                    try:
                        if not job_manager:
                            self._send_error("Job manager not available")
                            return
                        
                        print(f"DEBUG: HTTP bridge querying job_manager id {id(job_manager)} for job {job_id}")
                        job = job_manager.get_job(job_id)
                        if not job:
                            self._send_error(f"Job {job_id} not found")
                            return
                        
                        response = {
                            'success': True,
                            'job_id': job.job_id,
                            'job_type': job.job_type,
                            'status': job.status.name.lower(),
                            'created_at': job.created_at.isoformat() if job.created_at else None,
                            'updated_at': job.updated_at.isoformat() if job.updated_at else None,
                            'progress': job.progress,
                            'result': job.result.__dict__ if job.result else None,
                            'error': job.error
                        }
                        response_json = json.dumps(response)
                        self.wfile.write(response_json.encode('utf-8'))
                        return
                        
                    except Exception as e:
                        logger.error(f"Error getting job status: {e}")
                        self._send_error(f"Error getting job status: {e}")
                        return
                else:
                    self._send_error("Missing job_id parameter")
                    return
            
            # NEW: Screenshot job endpoints (legacy support)
            elif path.startswith('/api/screenshot/'):
                # Handle screenshot job-related requests
                path_parts = path.split('/')
                
                if len(path_parts) >= 4 and path_parts[3] == 'status':
                    # GET /api/screenshot/status/{job_id}
                    if len(path_parts) == 5:
                        job_id = path_parts[4]
                        try:
                            if not job_manager:
                                self._send_error("Job manager not available")
                                return
                            
                            job = job_manager.get_job(job_id)
                            if not job:
                                self._send_error(f"Job {job_id} not found")
                                return
                            
                            response = job.to_dict()
                            response_json = json.dumps(response)
                            self.wfile.write(response_json.encode('utf-8'))
                            return
                            
                        except Exception as e:
                            logger.error(f"Error getting job status: {e}")
                            self._send_error(f"Error getting job status: {e}")
                            return
                
                elif len(path_parts) >= 4 and path_parts[3] == 'download':
                    # GET /api/screenshot/download/{job_id}
                    if len(path_parts) == 5:
                        job_id = path_parts[4]
                        try:
                            job_manager, screenshot_worker = get_job_system()
                            if not screenshot_worker:
                                self._send_error("Screenshot worker not available")
                                return
                            
                            file_path = screenshot_worker.get_screenshot_file_path(job_id)
                            if not file_path or not file_path.exists():
                                self._send_error(f"Screenshot file not found for job {job_id}")
                                return
                            
                            # Serve the file
                            self._serve_file(file_path)
                            return
                            
                        except Exception as e:
                            logger.error(f"Error serving screenshot file: {e}")
                            self._send_error(f"Error serving screenshot file: {e}")
                            return
                
                elif len(path_parts) >= 4 and path_parts[3] == 'result':
                    # GET /api/screenshot/result/{job_id}
                    if len(path_parts) == 5:
                        job_id = path_parts[4]
                        try:
                            if not job_manager:
                                self._send_error("Job manager not available")
                                return
                            
                            job = job_manager.get_job(job_id)
                            if not job:
                                self._send_error(f"Job {job_id} not found")
                                return
                            
                            if job.status != JobStatus.COMPLETED or not job.result:
                                self._send_error(f"Job {job_id} not completed or no result available")
                                return
                            
                            response = {'result': job.result.__dict__}
                            response_json = json.dumps(response)
                            self.wfile.write(response_json.encode('utf-8'))
                            return
                            
                        except Exception as e:
                            logger.error(f"Error getting job result: {e}")
                            self._send_error(f"Error getting job result: {e}")
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
        global job_manager, screenshot_worker
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
                
            # Parse URL path for REST endpoints
            parsed_url = urlparse(self.path)
            path = parsed_url.path
            
            # Handle generic job endpoints
            if path == '/api/job':
                # Handle job operations (start/stop)
                try:
                    request_data = json.loads(post_data.decode('utf-8')) if post_data else {}
                    action = request_data.get('action')
                    
                    if action == 'start':
                        # Start new job
                        logger.info(f"Starting job with params: {request_data}")
                        
                        if not job_manager or not screenshot_worker:
                            self._send_error("Job infrastructure not available")
                            return
                        
                        job_type = request_data.get('job_type', 'screenshot')  # Default to screenshot
                        params = request_data.get('params', {})
                        session_id = request_data.get('session_id')
                        
                        # Create job with unique ID
                        job_id = job_manager.create_job(job_type, params, session_id)
                        
                        # Start the job based on type
                        if job_type == 'screenshot':
                            success = screenshot_worker.start_screenshot_job(job_id)
                        else:
                            success = False  # Other job types not implemented yet
                        
                        if success:
                            job = job_manager.get_job(job_id)
                            response = {
                                'success': True,
                                'job_id': job_id,
                                'job': {
                                    'job_id': job.job_id,
                                    'job_type': job.job_type,
                                    'status': job.status.name.lower(),
                                    'created_at': job.created_at.isoformat() if job.created_at else None,
                                    'progress': job.progress
                                } if job else None,
                                'message': f'{job_type.capitalize()} job started successfully'
                            }
                        else:
                            response = {
                                'success': False,
                                'error': f'Failed to start {job_type} job'
                            }
                        
                        response_json = json.dumps(response)
                        self.wfile.write(response_json.encode('utf-8'))
                        return
                    
                    elif action == 'stop':
                        # Stop/cancel job
                        job_id = request_data.get('job_id')
                        if not job_id:
                            self._send_error("Missing 'job_id' field for stop action")
                            return
                        
                        logger.info(f"Stopping job: {job_id}")
                        
                        if not job_manager:
                            self._send_error("Job manager not available")
                            return
                        
                        success = job_manager.cancel_job(job_id)
                        
                        if success:
                            response = {
                                'success': True,
                                'job_id': job_id,
                                'message': 'Job stopped successfully'
                            }
                        else:
                            response = {
                                'success': False,
                                'error': 'Failed to stop job or job not found'
                            }
                        
                        response_json = json.dumps(response)
                        self.wfile.write(response_json.encode('utf-8'))
                        return
                    
                    else:
                        self._send_error(f"Unknown action: {action}")
                        return
                        
                except json.JSONDecodeError as e:
                    self._send_error(f"Invalid JSON: {e}")
                    return
                except Exception as e:
                    logger.error(f"Error handling job request: {e}")
                    self._send_error(f"Job request error: {e}")
                    return
            
            # Handle REST-style screenshot job endpoints (legacy support)
            elif path == '/api/screenshot/start':
                # POST /api/screenshot/start - Create new screenshot job
                try:
                    request_data = json.loads(post_data.decode('utf-8')) if post_data else {}
                    logger.info(f"Starting screenshot job with params: {request_data}")
                    
                    if not job_manager or not screenshot_worker:
                        self._send_error("Job infrastructure not available")
                        return
                    
                    # Extract parameters
                    params = request_data.get('parameters', {})
                    session_id = request_data.get('session_id')
                    
                    # Create job with unique ID
                    job_id = job_manager.create_job('screenshot', params, session_id)
                    
                    # Start the job in background
                    success = screenshot_worker.start_screenshot_job(job_id)
                    
                    if success:
                        response = {
                            'success': True,
                            'job_id': job_id,
                            'message': 'Screenshot job started successfully'
                        }
                    else:
                        response = {
                            'success': False,
                            'error': 'Failed to start screenshot job'
                        }
                    
                    response_json = json.dumps(response)
                    self.wfile.write(response_json.encode('utf-8'))
                    return
                    
                except json.JSONDecodeError as e:
                    self._send_error(f"Invalid JSON: {e}")
                    return
                except Exception as e:
                    logger.error(f"Error creating screenshot job: {e}")
                    self._send_error(f"Screenshot job creation error: {e}")
                    return
                    
            elif path.startswith('/api/screenshot/cancel/'):
                # POST /api/screenshot/cancel/{job_id} - Cancel screenshot job
                path_parts = path.split('/')
                if len(path_parts) == 5:
                    job_id = path_parts[4]
                    try:
                        logger.info(f"Canceling screenshot job: {job_id}")
                        
                        if not job_manager:
                            self._send_error("Job manager not available")
                            return
                        
                        # Cancel the job
                        success = job_manager.cancel_job(job_id)
                        
                        if success:
                            response = {
                                'success': True,
                                'job_id': job_id,
                                'message': 'Screenshot job canceled successfully'
                            }
                        else:
                            response = {
                                'success': False,
                                'error': 'Failed to cancel screenshot job or job not found'
                            }
                        
                        response_json = json.dumps(response)
                        self.wfile.write(response_json.encode('utf-8'))
                        return
                        
                    except Exception as e:
                        logger.error(f"Error canceling screenshot job: {e}")
                        self._send_error(f"Screenshot job cancellation error: {e}")
                        return
                else:
                    self._send_error("Invalid cancel endpoint - job_id required")
                    return
            
            # Parse JSON for action-based endpoints
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
            
            # NEW: Handle screenshot job creation
            if request_data.get('action') == 'start_screenshot_job':
                # Handle screenshot job creation
                logger.info("Processing screenshot job creation request")
                try:
                    if not job_manager or not screenshot_worker:
                        self._send_error("Job infrastructure not available")
                        return
                    
                    # Extract parameters
                    params = request_data.get('params', {})
                    session_id = request_data.get('session_id')
                    
                    # Create job
                    job_id = job_manager.create_job('screenshot', params, session_id)
                    
                    # Start the job
                    success = screenshot_worker.start_screenshot_job(job_id)
                    
                    if success:
                        response = {
                            'success': True,
                            'jobId': job_id,
                            'status': 'pending',
                            'message': f'Screenshot job {job_id} started'
                        }
                    else:
                        response = {
                            'success': False,
                            'error': 'Failed to start screenshot job'
                        }
                    
                    response_json = json.dumps(response)
                    self.wfile.write(response_json.encode('utf-8'))
                    return
                    
                except Exception as e:
                    logger.error(f"Error creating screenshot job: {e}")
                    self._send_error(f"Screenshot job creation error: {e}")
                    return
                    
            # Handle screenshot job cancellation
            elif request_data.get('action') == 'cancel_job':
                # Handle job cancellation
                logger.info("Processing job cancellation request")
                try:
                    if not job_manager:
                        self._send_error("Job manager not available")
                        return
                    
                    job_id = request_data.get('job_id')
                    if not job_id:
                        self._send_error("Missing 'job_id' field")
                        return
                    
                    success = job_manager.cancel_job(job_id)
                    
                    response = {
                        'success': success,
                        'message': f'Job {job_id} {"cancelled" if success else "could not be cancelled"}'
                    }
                    
                    response_json = json.dumps(response)
                    self.wfile.write(response_json.encode('utf-8'))
                    return
                    
                except Exception as e:
                    logger.error(f"Error cancelling job: {e}")
                    self._send_error(f"Job cancellation error: {e}")
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
        self._initialize_workers()
    
    def _initialize_workers(self):
        """Initialize worker infrastructure."""
        global job_manager, screenshot_worker
        
        try:
            # Initialize job manager with Supabase if available
            supabase_client = None
            try:
                from tools.ai.session_management.storage.supabase_storage import SupabaseStorage
                supabase_storage = SupabaseStorage()
                supabase_client = supabase_storage.supabase
                logger.info("Initialized job manager with Supabase backend")
            except Exception as e:
                logger.warning(f"Could not initialize Supabase for job manager: {e}")
            
            job_manager = JobManager(supabase_client)
            
            # Initialize screenshot worker
            print("DEBUG: About to get Unreal connection...")
            unreal_connection = get_unreal_connection()
            print(f"DEBUG: Got Unreal connection: {unreal_connection}")
            
            if unreal_connection:
                screenshot_worker = ScreenshotWorker(
                    job_manager=job_manager,
                    unreal_connection=unreal_connection,
                    project_path=os.getenv('UNREAL_PROJECT_PATH')
                )
                logger.info("Screenshot worker initialized successfully")
                print("DEBUG: Screenshot worker initialized successfully with connection")
            else:
                logger.error("Could not get Unreal connection for screenshot worker - Unreal Engine may not be running")
                print("DEBUG: No Unreal connection available")
                # Initialize with None connection for testing
                screenshot_worker = ScreenshotWorker(
                    job_manager=job_manager,
                    unreal_connection=None,
                    project_path=os.getenv('UNREAL_PROJECT_PATH')
                )
                logger.warning("Screenshot worker initialized with no Unreal connection")
                print("DEBUG: Screenshot worker initialized without connection")
                
        except Exception as e:
            logger.error(f"Failed to initialize workers: {e}")
    
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