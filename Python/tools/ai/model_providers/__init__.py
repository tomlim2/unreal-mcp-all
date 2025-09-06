"""
Model provider factory and registry for different LLM providers.
"""

import logging
from typing import Dict, Optional, List
from .base import BaseModelProvider
from .gemini_provider import GeminiProvider
from .claude_provider import ClaudeProvider

logger = logging.getLogger("UnrealMCP")

# Available model providers
AVAILABLE_PROVIDERS = {
    'gemini': lambda: GeminiProvider("gemini-1.5-flash"),
    'gemini-2': lambda: GeminiProvider("gemini-2.5-flash"),
    'claude': lambda: ClaudeProvider(),
    'claude-3-haiku-20240307': lambda: ClaudeProvider("claude-3-haiku-20240307"),
}

# Default model configuration
DEFAULT_MODEL = 'gemini-2'
SUPPORTED_MODELS = list(AVAILABLE_PROVIDERS.keys())


class ModelProviderFactory:
    """Factory for creating model providers."""
    
    def __init__(self):
        self._providers: Dict[str, BaseModelProvider] = {}
        self._initialized = False
    
    def initialize(self):
        """Initialize all available providers."""
        if self._initialized:
            return
            
        for model_name, provider_factory in AVAILABLE_PROVIDERS.items():
            try:
                provider = provider_factory()
                self._providers[model_name] = provider
                availability = "✅ Available" if provider.is_available() else "❌ Not configured"
                logger.info(f"Model provider {model_name}: {availability}")
            except Exception as e:
                logger.error(f"Failed to initialize {model_name} provider: {e}")
        
        self._initialized = True
    
    def get_provider(self, model_name: str) -> Optional[BaseModelProvider]:
        """Get a provider by model name."""
        if not self._initialized:
            self.initialize()
            
        provider = self._providers.get(model_name)
        if not provider:
            logger.error(f"Unknown model provider: {model_name}")
            return None
            
        if not provider.is_available():
            logger.error(f"Model provider {model_name} is not available")
            return None
            
        return provider
    
    def get_available_models(self) -> List[str]:
        """Get list of available and configured models."""
        if not self._initialized:
            self.initialize()
            
        available = []
        for model_name, provider in self._providers.items():
            if provider.is_available():
                available.append(model_name)
        
        return available
    
    def get_default_model(self) -> str:
        """Get the default model name."""
        if not self._initialized:
            self.initialize()
            
        # Check if default is available, otherwise return first available
        available_models = self.get_available_models()
        
        if DEFAULT_MODEL in available_models:
            return DEFAULT_MODEL
        elif available_models:
            fallback = available_models[0]
            logger.warning(f"Default model {DEFAULT_MODEL} not available, using {fallback}")
            return fallback
        else:
            logger.error("No models available!")
            return DEFAULT_MODEL  # Return default even if not available
    
    def is_model_supported(self, model_name: str) -> bool:
        """Check if a model is supported."""
        return model_name in SUPPORTED_MODELS
    
    def get_model_info(self) -> Dict[str, Dict[str, str]]:
        """Get information about all models."""
        if not self._initialized:
            self.initialize()
            
        info = {}
        for model_name, provider in self._providers.items():
            info[model_name] = {
                'display_name': provider.get_model_name(),
                'provider': provider.get_provider_name(),
                'available': str(provider.is_available()),
                'is_default': str(model_name == DEFAULT_MODEL)
            }
        
        return info


# Global factory instance
_provider_factory = None

def get_provider_factory() -> ModelProviderFactory:
    """Get the global provider factory instance."""
    global _provider_factory
    if _provider_factory is None:
        _provider_factory = ModelProviderFactory()
        _provider_factory.initialize()
    return _provider_factory

def get_model_provider(model_name: str) -> Optional[BaseModelProvider]:
    """Convenience function to get a model provider."""
    factory = get_provider_factory()
    return factory.get_provider(model_name)

def get_available_models() -> List[str]:
    """Convenience function to get available models."""
    factory = get_provider_factory()
    return factory.get_available_models()

def get_default_model() -> str:
    """Convenience function to get default model."""
    factory = get_provider_factory()
    return factory.get_default_model()


# Export main classes and functions
__all__ = [
    'BaseModelProvider',
    'GeminiProvider', 
    'ClaudeProvider',
    'ModelProviderFactory',
    'get_provider_factory',
    'get_model_provider',
    'get_available_models',
    'get_default_model',
    'DEFAULT_MODEL',
    'SUPPORTED_MODELS'
]