"""
Base class for LLM model providers.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger("UnrealMCP")


class BaseModelProvider(ABC):
    """Abstract base class for LLM model providers."""
    
    def __init__(self, model_name: str):
        self.model_name = model_name
        
    @abstractmethod
    def is_available(self) -> bool:
        """Check if this model provider is available and configured."""
        pass
    
    @abstractmethod
    def generate_response(
        self, 
        messages: List[Dict[str, str]], 
        system_prompt: str,
        max_tokens: int = 1024,
        temperature: float = 0.1
    ) -> str:
        """Generate a response from the model."""
        pass
    
    @abstractmethod
    def get_model_name(self) -> str:
        """Get the display name of this model."""
        pass
    
    @abstractmethod
    def get_provider_name(self) -> str:
        """Get the name of this provider (e.g., 'anthropic', 'google')."""
        pass
    
    def validate_messages(self, messages: List[Dict[str, str]]) -> bool:
        """Validate message format."""
        for msg in messages:
            if not isinstance(msg, dict):
                return False
            if 'role' not in msg or 'content' not in msg:
                return False
            if msg['role'] not in ['user', 'assistant', 'system']:
                return False
        return True
    
    def prepare_error_response(self, error: Exception) -> Dict[str, Any]:
        """Prepare a standardized error response."""
        logger.error(f"{self.get_provider_name()} error: {error}")
        return {
            "error": str(error),
            "explanation": f"Error occurred with {self.get_model_name()} model",
            "commands": [],
            "executionResults": [],
            "provider": self.get_provider_name(),
            "model": self.get_model_name()
        }