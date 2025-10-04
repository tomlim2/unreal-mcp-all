"""
Factory for creating session storage backends.
"""

import logging

from .base_storage import BaseStorage

logger = logging.getLogger("SessionManager.Factory")

# Lazy import for file storage
_FileStorage = None


def _get_file_storage():
    """Lazy import of FileStorage."""
    global _FileStorage
    if _FileStorage is None:
        from .file_storage import FileStorage
        _FileStorage = FileStorage
    return _FileStorage


class StorageFactory:
    """Factory for creating session storage backends (file only)."""
    
    @staticmethod
    def create(storage_type: str = 'file', **kwargs) -> BaseStorage:
        """
        Create a storage backend instance.
        
        Args:
            storage_type: Type of storage ('file')
            **kwargs: Additional arguments for storage backend
            
        Returns:
            BaseStorage instance
            
        Raises:
            ValueError: If storage type is unknown
            RuntimeError: If storage backend cannot be initialized
        """
        storage_type = storage_type.lower()
        
        try:
            if storage_type == 'file':
                file_class = _get_file_storage()
                return file_class(**kwargs)
            else:
                raise ValueError(f"Unknown storage type: {storage_type}. Supported types: 'file'")
                
        except Exception as e:
            logger.error(f"Failed to create {storage_type} storage: {e}")
            raise RuntimeError(f"Failed to initialize {storage_type} storage") from e
    
    @staticmethod
    def get_available_backends() -> list[str]:
        """
        Get list of available storage backends.
        
        Returns:
            List of available backend names
        """
        backends = []
        
        # File storage is always available
        try:
            _get_file_storage()
            backends.append('file')
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