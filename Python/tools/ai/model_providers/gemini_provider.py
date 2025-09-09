"""
Google Gemini model provider implementation.
"""

import os
import logging
from typing import List, Dict, Any
from .base import BaseModelProvider

logger = logging.getLogger("UnrealMCP")

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
    logger.info("Google Generative AI SDK imported successfully")
except ImportError as e:
    GEMINI_AVAILABLE = False
    logger.warning(f"Google Generative AI SDK not available: {e}")


class GeminiProvider(BaseModelProvider):
    """Google Gemini model provider."""
    
    def __init__(self, model_name: str = "gemini-1.5-flash"):
        super().__init__(model_name)
        self._client = None
        self._model = None
        
    def _initialize_client(self):
        """Initialize the Gemini client if not already done."""
        if self._client is None and GEMINI_AVAILABLE:
            api_key = os.getenv('GOOGLE_API_KEY')
            if api_key and api_key != 'your-google-api-key-here':
                genai.configure(api_key=api_key)
                self._model = genai.GenerativeModel(self.model_name)
                self._client = True
                logger.info(f"Gemini client initialized with model: {self.model_name}")
            else:
                logger.error("GOOGLE_API_KEY not configured")
                
    def is_available(self) -> bool:
        """Check if Gemini is available and configured."""
        if not GEMINI_AVAILABLE:
            return False
            
        api_key = os.getenv('GOOGLE_API_KEY')
        return api_key is not None and api_key != 'your-google-api-key-here'
    
    def generate_response(
        self, 
        messages: List[Dict[str, str]], 
        system_prompt: str,
        max_tokens: int = 2048,  # Increased default from 1024
        temperature: float = 0.1
    ) -> str:
        """Generate response using Gemini."""
        self._initialize_client()
        
        if not self._model:
            raise Exception("Gemini model not initialized")
            
        if not self.validate_messages(messages):
            raise Exception("Invalid message format")
        
        try:
            # Convert messages to Gemini format
            gemini_messages = self._convert_messages_to_gemini_format(messages, system_prompt)
            
            # Configure generation parameters with higher token limit
            generation_config = genai.types.GenerationConfig(
                max_output_tokens=max(max_tokens, 2048),  # Ensure minimum 2048 tokens
                temperature=temperature,
            )
            
            # Generate response
            response = self._model.generate_content(
                gemini_messages,
                generation_config=generation_config
            )
            
            # Check response status and finish reason
            if not response.candidates:
                raise Exception("Gemini returned no candidates")
            
            candidate = response.candidates[0]
            finish_reason = candidate.finish_reason if hasattr(candidate, 'finish_reason') else None
            
            logger.info(f"Gemini finish reason: {finish_reason}")
            
            # Handle different finish reasons
            if finish_reason:
                if finish_reason.name == 'MAX_TOKENS':
                    logger.warning(f"Gemini response truncated due to MAX_TOKENS. Consider increasing max_output_tokens.")
                elif finish_reason.name != 'STOP':
                    logger.warning(f"Gemini response may be incomplete. Finish reason: {finish_reason.name}")
            
            # Try multiple methods to extract text from response
            response_text = None
            
            # Method 1: Try response.text (may fail with MAX_TOKENS)
            try:
                if hasattr(response, 'text') and response.text:
                    response_text = response.text.strip()
                    logger.info(f"Gemini response via response.text (length: {len(response_text)} chars)")
            except Exception as e:
                logger.debug(f"Could not access response.text: {e}")
            
            # Method 2: Try to get text from candidate parts directly
            if not response_text and candidate.content and candidate.content.parts:
                try:
                    text_parts = []
                    for part in candidate.content.parts:
                        if hasattr(part, 'text') and part.text:
                            text_parts.append(part.text)
                    
                    if text_parts:
                        response_text = ''.join(text_parts).strip()
                        logger.info(f"Gemini response via candidate parts (length: {len(response_text)} chars)")
                except Exception as e:
                    logger.debug(f"Could not access candidate parts: {e}")
            
            # If we have response text, clean and return it
            if response_text:
                # Clean up markdown code block formatting from Gemini
                cleaned_response = response_text
                if cleaned_response.startswith('```json'):
                    # Remove ```json at the start and ``` at the end
                    cleaned_response = cleaned_response[7:]  # Remove ```json
                    if cleaned_response.endswith('```'):
                        cleaned_response = cleaned_response[:-3]  # Remove ```
                    cleaned_response = cleaned_response.strip()
                
                # For MAX_TOKENS, try to make the response valid JSON if it's cut off
                if finish_reason and finish_reason.name == 'MAX_TOKENS':
                    # If response looks like incomplete JSON, try to close it
                    if cleaned_response.count('{') > cleaned_response.count('}'):
                        logger.info("Attempting to fix truncated JSON response")
                        # Add missing closing braces
                        missing_braces = cleaned_response.count('{') - cleaned_response.count('}')
                        cleaned_response += '}' * missing_braces
                
                # Log the full response for debugging
                logger.info(f"Final Gemini response: {cleaned_response[:200]}..." if len(cleaned_response) > 200 else f"Final Gemini response: {cleaned_response}")
                return cleaned_response
            
            # If we still have no text, return a meaningful error
            finish_reason_name = finish_reason.name if finish_reason else 'UNKNOWN'
            raise Exception(f"Gemini returned no usable text content (finish_reason: {finish_reason_name}). This may be due to content filtering or API issues.")
                
        except Exception as e:
            logger.error(f"Gemini generation error: {e}")
            raise Exception(f"Gemini error: {str(e)}")
    
    def _convert_messages_to_gemini_format(self, messages: List[Dict[str, str]], system_prompt: str) -> str:
        """Convert conversation messages to Gemini prompt format."""
        # Gemini works best with a single prompt that includes context and current request
        
        prompt_parts = [system_prompt]
        
        # Add conversation history
        if len(messages) > 1:  # More than just the current message
            prompt_parts.append("\n## CONVERSATION HISTORY:")
            for msg in messages[:-1]:  # All but the last message
                role_label = "Human" if msg['role'] == 'user' else "Assistant"
                # Clean the content to avoid nested system prompts
                content = msg['content']
                if "User request:" in content:
                    # Extract just the user request part
                    content = content.split("User request:")[-1].strip()
                prompt_parts.append(f"{role_label}: {content}")
        
        # Add current request
        current_message = messages[-1]
        if current_message['role'] == 'user':
            # Extract the actual user request, avoiding duplicate system prompts
            content = current_message['content']
            if "User request:" in content:
                user_request = content.split("User request:")[-1].strip()
            else:
                user_request = content
            prompt_parts.append(f"\n## CURRENT REQUEST:\n{user_request}")
        
        return "\n".join(prompt_parts)
    
    def get_model_name(self) -> str:
        """Get display name."""
        return f"Gemini ({self.model_name})"
    
    def get_provider_name(self) -> str:
        """Get provider name."""
        return "google"