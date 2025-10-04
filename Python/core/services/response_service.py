"""
Response building service.

Constructs standardized HTTP responses for different endpoints.
"""

import datetime
from typing import Dict, Any, Optional


def build_nlp_response(
    result: Dict[str, Any],
    user_input: str,
    session_id: Optional[str],
    trace_id: str
) -> Dict[str, Any]:
    """
    Build standardized NLP response.

    Args:
        result: NLP processing result from tools.ai.nlp
        user_input: Original user input
        session_id: Session ID (may be None)
        trace_id: Request trace ID

    Returns:
        Standardized response dict

    Response Structure:
        {
            "conversation_context": {
                "user_input": str,
                "timestamp": ISO timestamp,
                "trace_id": str
            },
            "ai_processing": {
                "explanation": str,
                "generated_commands": list,
                "expected_result": str,
                "processing_error": str | None,
                "fallback_used": bool
            },
            "execution_results": list,
            "debug_notes": {
                "message_role": "assistant",
                "session_context": str
            }
        }
    """
    return {
        "conversation_context": {
            "user_input": user_input,
            "timestamp": datetime.datetime.now().isoformat(),
            "trace_id": trace_id
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


def build_error_response(
    error: Exception,
    user_input: Optional[str],
    session_id: Optional[str],
    trace_id: str
) -> Dict[str, Any]:
    """
    Build standardized error response.

    Args:
        error: Exception that occurred
        user_input: Original user input (may be None)
        session_id: Session ID (may be None)
        trace_id: Request trace ID

    Returns:
        Error response dict (matches NLP response structure)

    Used for:
        - NLP processing errors
        - Image validation errors
        - Internal server errors
    """
    return {
        "conversation_context": {
            "user_input": user_input or "",
            "timestamp": datetime.datetime.now().isoformat(),
            "trace_id": trace_id
        },
        "ai_processing": {
            "explanation": "",
            "generated_commands": [],
            "expected_result": "",
            "processing_error": str(error),
            "fallback_used": False
        },
        "execution_results": [],
        "debug_notes": {
            "message_role": "error",
            "session_context": f"Session: {session_id}" if session_id else "No session"
        }
    }
