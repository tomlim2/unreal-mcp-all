"""
Session management handlers.

Handles session CRUD operations (Create, Read, Update, Delete).
"""

from typing import Optional, Dict, Any
import datetime
import logging

from ..router import route
from ..middleware.trace_logger import log_request_start, log_error
from core.session import get_session_manager, SessionContext
from core.session.utils.session_helpers import generate_session_id

logger = logging.getLogger("http_bridge.handlers.session")


@route("/", method="POST", description="Get session context", tags=["Session"])
def handle_get_context(handler, request_data: dict, trace_id: str) -> Optional[Dict[str, Any]]:
    """
    Handle session context retrieval.

    Args:
        handler: HTTP request handler instance
        request_data: Parsed request body
        trace_id: Request trace ID

    Returns:
        Session context dict, or None if not this action

    Request Format:
        {
            "action": "get_context",
            "session_id": str (required)
        }

    Response Format:
        {
            "context": {
                "session_id": str,
                "created_at": ISO timestamp,
                "conversation_history": [...],
                ...
            }
        }
    """
    if request_data.get('action') != 'get_context':
        return None

    log_request_start(trace_id, "POST", "/", "get_context")

    session_id = request_data.get('session_id')
    if not session_id:
        raise ValueError("Missing 'session_id' for get_context action")

    try:
        session_manager = get_session_manager()
        session_context = session_manager.get_session(session_id)

        if not session_context:
            raise ValueError(f"Session not found: {session_id}")

        return {
            'context': session_context.to_dict()
        }

    except Exception as e:
        log_error(trace_id, e, "get_context")
        raise


@route("/", method="POST", description="Delete session", tags=["Session"])
def handle_delete_session(handler, request_data: dict, trace_id: str) -> Optional[Dict[str, Any]]:
    """
    Handle session deletion.

    Args:
        handler: HTTP request handler instance
        request_data: Parsed request body
        trace_id: Request trace ID

    Returns:
        Deletion result dict, or None if not this action

    Request Format:
        {
            "action": "delete_session",
            "session_id": str (required)
        }

    Response Format:
        {
            "success": bool,
            "message": str  (if success)
            "error": str    (if failure)
        }
    """
    if request_data.get('action') != 'delete_session':
        return None

    log_request_start(trace_id, "POST", "/", "delete_session")

    session_id = request_data.get('session_id')
    if not session_id:
        raise ValueError("Missing 'session_id' for delete_session action")

    try:
        session_manager = get_session_manager()
        success = session_manager.delete_session(session_id)

        if success:
            return {
                'success': True,
                'message': f'Session {session_id} deleted successfully'
            }
        else:
            return {
                'success': False,
                'error': f'Session not found: {session_id}'
            }

    except Exception as e:
        log_error(trace_id, e, "delete_session")
        raise


@route("/", method="POST", description="Create new session", tags=["Session"])
def handle_create_session(handler, request_data: dict, trace_id: str) -> Optional[Dict[str, Any]]:
    """
    Handle session creation.

    Args:
        handler: HTTP request handler instance
        request_data: Parsed request body
        trace_id: Request trace ID

    Returns:
        New session info dict, or None if not this action

    Request Format:
        {
            "action": "create_session",
            "session_name": str (required)
        }

    Response Format:
        {
            "session_id": str,
            "session_name": str,
            "created_at": ISO timestamp,
            "last_accessed": ISO timestamp
        }
    """
    if request_data.get('action') != 'create_session':
        return None

    log_request_start(trace_id, "POST", "/", "create_session")

    session_name = request_data.get('session_name')
    if not session_name:
        raise ValueError("Missing 'session_name' for create_session action")

    try:
        session_manager = get_session_manager()
        session_id = generate_session_id()
        now = datetime.datetime.now()

        session_context = SessionContext(
            session_id=session_id,
            session_name=session_name.strip(),
            created_at=now,
            last_accessed=now
        )

        # Save to storage
        if not session_manager.storage.create_session(session_context):
            raise Exception("Failed to save session to storage")

        return {
            'session_id': session_context.session_id,
            'session_name': session_context.session_name,
            'created_at': session_context.created_at.isoformat(),
            'last_accessed': session_context.last_accessed.isoformat()
        }

    except Exception as e:
        log_error(trace_id, e, "create_session")
        raise


@route("/sessions", method="GET", description="List all sessions", tags=["Session"])
def handle_list_sessions(handler, request_data: dict, trace_id: str) -> Dict[str, Any]:
    """
    Handle session list request.

    Args:
        handler: HTTP request handler instance
        request_data: Parsed request body (unused for GET)
        trace_id: Request trace ID

    Returns:
        Dict with list of all sessions

    Response Format:
        {
            "sessions": [
                {
                    "session_id": str,
                    "session_name": str,
                    "created_at": ISO timestamp,
                    "last_accessed": ISO timestamp,
                    "interaction_count": int
                },
                ...
            ]
        }
    """
    log_request_start(trace_id, "GET", "/sessions", None)

    try:
        session_manager = get_session_manager()
        sessions = session_manager.storage.list_sessions()

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

        return {'sessions': session_list}

    except Exception as e:
        log_error(trace_id, e, "list_sessions")
        raise


@route("/api/session/*/latest-image", method="GET", description="Get latest image for session", tags=["Session"])
def handle_get_latest_image(handler, request_data: dict, trace_id: str) -> Dict[str, Any]:
    """
    Handle latest image request for a session.

    Args:
        handler: HTTP request handler instance
        request_data: Parsed request body (unused for GET)
        trace_id: Request trace ID

    Returns:
        Dict with latest image info

    Response Format:
        {
            "success": bool,
            "latest_image": {
                "uid": str | None,
                "filename": str | None,
                "thumbnail_url": str | None,
                "available": bool
            }
        }
    """
    # Extract session ID from path
    path_parts = handler.path.split('/')
    if len(path_parts) < 4:
        raise ValueError("Invalid session ID in path")

    session_id = path_parts[3]
    log_request_start(trace_id, "GET", f"/api/session/{session_id}/latest-image", None)

    try:
        session_manager = get_session_manager()
        session_context = session_manager.get_session(session_id)

        if not session_context:
            return {
                'success': False,
                'error': 'Session not found',
                'latest_image': {
                    'uid': None,
                    'filename': None,
                    'thumbnail_url': None,
                    'available': False
                }
            }

        latest_uid = session_context.get_latest_image_uid()
        latest_filename = session_context.get_latest_image_path()

        return {
            'success': True,
            'latest_image': {
                'uid': latest_uid,
                'filename': latest_filename,
                'thumbnail_url': f'/api/screenshot-file/{latest_filename}' if latest_filename else None,
                'available': latest_uid is not None
            }
        }

    except Exception as e:
        log_error(trace_id, e, "get_latest_image")
        raise


@route("/api/session/*/images", method="GET", description="Get all images for session", tags=["Session"])
def handle_get_session_images(handler, request_data: dict, trace_id: str) -> Dict[str, Any]:
    """
    Handle request for all images in a session.

    Args:
        handler: HTTP request handler instance
        request_data: Parsed request body (unused for GET)
        trace_id: Request trace ID

    Returns:
        Dict with all session images

    Response Format:
        {
            "success": bool,
            "images": [
                {
                    "uid": str,
                    "url": str,
                    "thumbnail_url": str,
                    "filename": str,
                    "timestamp": ISO timestamp,
                    "command": str
                },
                ...
            ]
        }
    """
    # Extract session ID from path
    path_parts = handler.path.split('/')
    if len(path_parts) < 4:
        raise ValueError("Invalid session ID in path")

    session_id = path_parts[3]
    log_request_start(trace_id, "GET", f"/api/session/{session_id}/images", None)

    try:
        session_manager = get_session_manager()
        session_context = session_manager.get_session(session_id)

        if not session_context:
            return {
                'success': False,
                'error': 'Session not found',
                'images': []
            }

        # Get all recent images from session (up to 50)
        recent_images = session_context.get_recent_images(max_images=50)

        # Transform to frontend format
        images = []
        for img_info in recent_images:
            image_url = img_info.get('image_url', '')
            image_uid = img_info.get('image_uid', '')
            filename = img_info.get('filename', '')

            images.append({
                'uid': image_uid,
                'url': image_url,
                'thumbnail_url': image_url,  # Same as URL for thumbnails
                'filename': filename,
                'timestamp': img_info.get('timestamp', ''),
                'command': img_info.get('command', 'unknown')
            })

        logger.info(f"Returning {len(images)} images for session {session_id}")

        return {
            'success': True,
            'images': images
        }

    except Exception as e:
        log_error(trace_id, e, "get_session_images")
        raise
