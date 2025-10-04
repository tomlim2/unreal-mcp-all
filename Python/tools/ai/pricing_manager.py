"""
Pricing Manager for AI Token Cost Calculations

Handles loading pricing configuration and calculating costs for different models and token types.
"""

import json
import math
from pathlib import Path
from typing import Dict, Any, Tuple, Optional
import logging

logger = logging.getLogger(__name__)

class PricingManager:
    """Manages AI model pricing and token cost calculations."""
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize with pricing configuration file."""
        if config_path is None:
            # Default to pricing_config.json in tools/ai/ directory
            config_path = Path(__file__).parent / "pricing_config.json"

        self.config_path = Path(config_path)
        self.pricing_config = self._load_pricing_config()
    
    def _load_pricing_config(self) -> Dict[str, Any]:
        """Load pricing configuration from JSON file."""
        try:
            if self.config_path.exists():
                with open(self.config_path, 'r') as f:
                    config = json.load(f)
                    logger.info(f"Loaded pricing config from {self.config_path}")
                    return config
            else:
                logger.warning(f"Pricing config not found at {self.config_path}, using defaults")
                return self._get_default_config()
        except Exception as e:
            logger.error(f"Failed to load pricing config: {e}")
            return self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Return default pricing configuration as fallback."""
        return {
            "models": {
                "gemini-2": {
                    "text_input": 0.000000075,
                    "text_output": 0.0003,
                    "image_processing": 0.00000258,
                    "name": "Gemini-2.5-Flash"
                }
            },
            "image_token_calculation": {
                "small_image_threshold": 384,
                "small_image_tokens": 258,
                "tile_size": 768,
                "tokens_per_tile": 258
            }
        }
    
    def calculate_image_tokens(self, width: int, height: int, resolution_multiplier: float = 1.0) -> int:
        """
        Calculate image tokens using Google's official tile-based method.
        
        Args:
            width: Image width in pixels
            height: Image height in pixels  
            resolution_multiplier: Multiplier for resolution scaling
            
        Returns:
            Token count for the image
        """
        config = self.pricing_config.get("image_token_calculation", {})
        threshold = config.get("small_image_threshold", 384)
        small_tokens = config.get("small_image_tokens", 258)
        tile_size = config.get("tile_size", 768)
        tokens_per_tile = config.get("tokens_per_tile", 258)
        
        # Apply resolution multiplier to dimensions
        effective_width = int(width * resolution_multiplier)
        effective_height = int(height * resolution_multiplier)
        
        # Small image: both dimensions <= threshold
        if effective_width <= threshold and effective_height <= threshold:
            return small_tokens
        
        # Large image: tile-based calculation
        tiles_x = math.ceil(effective_width / tile_size)
        tiles_y = math.ceil(effective_height / tile_size)
        total_tiles = tiles_x * tiles_y
        
        return int(total_tiles * tokens_per_tile)
    
    def calculate_token_cost(self, tokens: int, model: str, token_type: str = "image_processing") -> float:
        """
        Calculate cost for given tokens and model.
        
        Args:
            tokens: Number of tokens
            model: Model identifier (e.g., 'gemini-2', 'claude-3-haiku-20240307')
            token_type: Type of tokens ('text_input', 'text_output', 'image_processing')
            
        Returns:
            Cost in USD
        """
        models = self.pricing_config.get("models", {})
        
        # Get model pricing, default to gemini-2 if not found
        model_key = model if model in models else "gemini-2"
        model_pricing = models.get(model_key, models.get("gemini-2", {}))
        
        if token_type not in model_pricing:
            logger.warning(f"Token type '{token_type}' not found for model '{model_key}', using image_processing")
            token_type = "image_processing"
        
        price_per_token = model_pricing.get(token_type, 0.00000258)  # Fallback to gemini rate
        return tokens * price_per_token
    
    def get_model_info(self, model: str) -> Dict[str, Any]:
        """Get model information including display name and pricing."""
        models = self.pricing_config.get("models", {})
        model_key = model if model in models else "gemini-2"
        return models.get(model_key, {})
    
    def reload_config(self) -> bool:
        """Reload pricing configuration from file."""
        try:
            self.pricing_config = self._load_pricing_config()
            return True
        except Exception as e:
            logger.error(f"Failed to reload pricing config: {e}")
            return False


# Global pricing manager instance
_pricing_manager = None

def get_pricing_manager() -> PricingManager:
    """Get global pricing manager instance."""
    global _pricing_manager
    if _pricing_manager is None:
        _pricing_manager = PricingManager()
    return _pricing_manager

def calculate_image_tokens(width: int, height: int, resolution_multiplier: float = 1.0) -> int:
    """Convenience function for image token calculation."""
    return get_pricing_manager().calculate_image_tokens(width, height, resolution_multiplier)

def calculate_token_cost(tokens: int, model: str, token_type: str = "image_processing") -> float:
    """Convenience function for token cost calculation."""
    return get_pricing_manager().calculate_token_cost(tokens, model, token_type)