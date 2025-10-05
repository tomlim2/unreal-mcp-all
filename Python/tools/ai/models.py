"""
Data models for AI natural language processing.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional


@dataclass
class ProcessingRequest:
    """Request parameters for natural language processing."""

    user_input: str
    context: str = "Assume as you are a creative cinematic director"
    session_id: Optional[str] = None
    llm_model: Optional[str] = None
    target_image_uid: Optional[str] = None
    main_image_data: Optional[Dict[str, Any]] = None
    main_prompt: Optional[str] = None
    reference_prompts: Optional[List[str]] = None
    reference_images: Optional[List[Dict[str, Any]]] = None

    def __post_init__(self):
        """Validate request parameters."""
        if not self.user_input or not self.user_input.strip():
            raise ValueError("user_input cannot be empty")

        if self.reference_prompts is None:
            self.reference_prompts = []

        if self.reference_images is None:
            self.reference_images = []


@dataclass
class ProcessingResponse:
    """Response from natural language processing."""

    explanation: str
    commands: List[Dict[str, Any]]
    expected_result: str
    execution_results: List[Dict[str, Any]] = field(default_factory=list)
    model_used: str = "unknown"
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert response to dictionary format."""
        result = {
            "explanation": self.explanation,
            "commands": self.commands,
            "expectedResult": self.expected_result,
            "executionResults": self.execution_results,
            "modelUsed": self.model_used
        }

        if self.error:
            result["error"] = self.error

        return result
