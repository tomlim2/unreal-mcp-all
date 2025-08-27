"""
Factory for creating session storage backends.
"""

import logging
from typing import Optional

from .base_storage import BaseStorage
from .file_storage import FileStorage

logger = logging.getLogger("SessionManager.Factory")

# Lazy imports for optional backends
_SupabaseStorage = None


def _get_supabase_storage():
    """Lazy import of SupabaseStorage to avoid errors if not available."""
    global _SupabaseStorage
    if _SupabaseStorage is None:
        try:
            from .supabase_storage import SupabaseStorage
            _SupabaseStorage = SupabaseStorage
        except ImportError as e:
            logger.error(f"Supabase storage not available: {e}")
            raise
    return _SupabaseStorage


class StorageFactory:
    """Factory for creating session storage backends."""
    
    @staticmethod
    def create(storage_type: str = 'supabase', **kwargs) -> BaseStorage:
        """
        Create a storage backend instance.
        
        Args:
            storage_type: Type of storage ('supabase', 'file')
            **kwargs: Additional arguments for storage backend
            
        Returns:
            BaseStorage instance
            
        Raises:
            ValueError: If storage type is unknown
            RuntimeError: If storage backend cannot be initialized
        """
        storage_type = storage_type.lower()
        
        try:
            if storage_type == 'supabase':
                supabase_class = _get_supabase_storage()
                return supabase_class(**kwargs)
            
            elif storage_type == 'file':
                return FileStorage(**kwargs)
            
            else:
                raise ValueError(f"Unknown storage type: {storage_type}")
                
        except Exception as e:
            logger.error(f"Failed to create {storage_type} storage: {e}")
            raise RuntimeError(f"Failed to initialize {storage_type} storage") from e
    
    @staticmethod
    def create_with_fallback(primary_type: str = 'supabase', 
                           fallback_type: str = 'file',
                           **kwargs) -> tuple[BaseStorage, Optional[BaseStorage]]:
        """
        Create primary storage with fallback.
        
        Args:
            primary_type: Primary storage type
            fallback_type: Fallback storage type (None for no fallback)
            **kwargs: Additional arguments for storage backends
            
        Returns:
            Tuple of (primary_storage, fallback_storage)
        """
        primary = None
        fallback = None
        
        # Try to create primary storage
        try:
            primary = StorageFactory.create(primary_type, **kwargs)
            logger.info(f"Primary storage ({primary_type}) initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize primary storage ({primary_type}): {e}")
        
        # Try to create fallback storage
        if fallback_type and fallback_type != primary_type:
            try:
                fallback = StorageFactory.create(fallback_type, **kwargs)
                logger.info(f"Fallback storage ({fallback_type}) initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize fallback storage ({fallback_type}): {e}")
        
        # Ensure we have at least one working storage
        if primary is None and fallback is None:
            raise RuntimeError("Failed to initialize any storage backend")
        
        return primary, fallback
    
    @staticmethod
    def get_available_backends() -> list[str]:
        """
        Get list of available storage backends.
        
        Returns:
            List of available backend names
        """
        backends = ['file']  # File storage is always available
        
        # Check if Supabase is available
        try:
            _get_supabase_storage()
            backends.append('supabase')
        except:
            pass
        
        return backends
    
    @staticmethod
    def test_backend(storage_type: str, **kwargs) -> bool:
        """
        Test if a storage backend is working.
        
        Args:
            storage_type: Type of storage to test
            **kwargs: Additional arguments for storage backend
            
        Returns:
            True if backend is working, False otherwise
        """
        try:
            storage = StorageFactory.create(storage_type, **kwargs)
            return storage.health_check()
        except Exception as e:
            logger.error(f"Backend test failed for {storage_type}: {e}")
            return False