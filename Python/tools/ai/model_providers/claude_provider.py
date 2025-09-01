"""
Anthropic Claude model provider implementation.
"""

import os
import logging
from typing import List, Dict, Any
from .base import BaseModelProvider

logger = logging.getLogger("UnrealMCP")

try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
    logger.info("Anthropic SDK imported successfully")
except ImportError as e:
    ANTHROPIC_AVAILABLE = False
    logger.warning(f"Anthropic SDK not available: {e}")


class ClaudeProvider(BaseModelProvider):
    """Anthropic Claude model provider."""
    
    def __init__(self, model_name: str = "claude-3-haiku-20240307"):
        super().__init__(model_name)
        self._client = None
        
    def _initialize_client(self):
        """Initialize the Anthropic client if not already done."""
        if self._client is None and ANTHROPIC_AVAILABLE:
            api_key = os.getenv('ANTHROPIC_API_KEY')
            if api_key and api_key != 'your-api-key-here':
                self._client = anthropic.Anthropic(api_key=api_key)
                logger.info(f"Claude client initialized with model: {self.model_name}")
            else:
                logger.error("ANTHROPIC_API_KEY not configured")
                
    def is_available(self) -> bool:
        """Check if Claude is available and configured."""
        if not ANTHROPIC_AVAILABLE:
            return False
            
        api_key = os.getenv('ANTHROPIC_API_KEY')
        return api_key is not None and api_key != 'your-api-key-here'
    
    def generate_response(
        self, 
        messages: List[Dict[str, str]], 
        system_prompt: str,
        max_tokens: int = 1024,
        temperature: float = 0.1
    ) -> str:
        """Generate response using Claude."""
        self._initialize_client()
        
        if not self._client:
            raise Exception("Claude client not initialized")
            
        if not self.validate_messages(messages):
            raise Exception("Invalid message format")
        
        try:
            # Claude supports system parameter and conversation messages
            conversation_messages = []
            
            # Add conversation history (excluding the system prompt from user messages)
            for msg in messages:
                if msg['role'] in ['user', 'assistant']:
                    content = msg['content']
                    
                    # If this is a user message with system prompt, extract just the user request
                    if msg['role'] == 'user' and "User request:" in content:
                        content = content.split("User request:")[-1].strip()
                    
                    conversation_messages.append({
                        "role": msg['role'],
                        "content": content
                    })
            
            # Generate response using Claude's API
            response = self._client.messages.create(
                model=self.model_name,
                system=system_prompt,  # Use system parameter
                max_tokens=max_tokens,
                temperature=temperature,
                messages=conversation_messages
            )
            
            if response.content and len(response.content) > 0:
                ai_response = response.content[0].text
                logger.info(f"Claude response generated successfully")
                return ai_response
            else:
                raise Exception("Claude returned empty response")
                
        except Exception as e:
            logger.error(f"Claude generation error: {e}")
            raise Exception(f"Claude error: {str(e)}")
    
    def get_model_name(self) -> str:
        """Get display name."""
        return f"Claude ({self.model_name})"
    
    def get_provider_name(self) -> str:
        """Get provider name."""
        return "anthropic"