"""
Format Manager for 3D Object Processing

Manages multiple format handlers and provides unified interface for format detection,
analysis, validation, and processing across all supported 3D file formats.
"""

import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Type
from .base import BaseFormatHandler
from .obj_handler import OBJFormatHandler
from .fbx_handler import FBXFormatHandler
from .gltf_handler import GLTFFormatHandler

logger = logging.getLogger("UnrealMCP")


class FormatManager:
    """
    Manages format handlers for different 3D file formats.

    Provides unified interface for format detection, analysis, and validation
    across all supported formats.
    """

    def __init__(self):
        """Initialize format manager with default handlers."""
        self.handlers: Dict[str, BaseFormatHandler] = {}
        self.extension_map: Dict[str, str] = {}  # extension -> format_type mapping

        # Register default handlers
        self._register_default_handlers()

    def _register_default_handlers(self):
        """Register built-in format handlers."""
        default_handlers = [
            ('obj', OBJFormatHandler()),
            ('fbx', FBXFormatHandler()),
            ('gltf', GLTFFormatHandler()),
        ]

        for format_type, handler in default_handlers:
            self.register_handler(format_type, handler)

    def register_handler(self, format_type: str, handler: BaseFormatHandler):
        """
        Register a format handler.

        Args:
            format_type: Format identifier (e.g., 'obj', 'fbx')
            handler: Format handler instance
        """
        self.handlers[format_type] = handler

        # Map extensions to format type
        for extension in handler.extensions:
            self.extension_map[extension] = format_type

        logger.debug(f"Registered format handler: {format_type} -> {handler.format_name}")

    def detect_format(self, file_path: Path) -> Optional[str]:
        """
        Detect the format of a 3D file.

        Args:
            file_path: Path to the file

        Returns:
            Format type string, or None if not supported
        """
        extension = file_path.suffix.lower()
        return self.extension_map.get(extension)

    def get_handler(self, format_type: str) -> Optional[BaseFormatHandler]:
        """
        Get handler for a specific format.

        Args:
            format_type: Format identifier

        Returns:
            Format handler instance, or None if not found
        """
        return self.handlers.get(format_type)

    def get_handler_for_file(self, file_path: Path) -> Optional[BaseFormatHandler]:
        """
        Get appropriate handler for a file.

        Args:
            file_path: Path to the file

        Returns:
            Format handler instance, or None if format not supported
        """
        format_type = self.detect_format(file_path)
        if format_type:
            return self.get_handler(format_type)
        return None

    def analyze_file(self, file_path: Path) -> Dict[str, Any]:
        """
        Analyze a 3D file using the appropriate format handler.

        Args:
            file_path: Path to the file

        Returns:
            Analysis results dictionary
        """
        handler = self.get_handler_for_file(file_path)
        if handler:
            try:
                analysis = handler.analyze_file(file_path)
                analysis['format_handler'] = handler.format_name
                return analysis
            except Exception as e:
                logger.error(f"Failed to analyze file {file_path} with {handler.format_name}: {e}")
                return {'analysis_error': str(e), 'format_handler': handler.format_name}
        else:
            format_type = self.detect_format(file_path)
            error_msg = f"No handler available for format: {format_type or 'unknown'}"
            logger.warning(error_msg)
            return {'analysis_error': error_msg}

    def validate_file(self, file_path: Path) -> tuple[bool, List[str]]:
        """
        Validate a 3D file using the appropriate format handler.

        Args:
            file_path: Path to the file

        Returns:
            Tuple of (is_valid: bool, issues: List[str])
        """
        handler = self.get_handler_for_file(file_path)
        if handler:
            try:
                return handler.validate_file(file_path)
            except Exception as e:
                error_msg = f"Validation failed with {handler.format_name}: {str(e)}"
                logger.error(error_msg)
                return False, [error_msg]
        else:
            format_type = self.detect_format(file_path)
            error_msg = f"No handler available for validation of format: {format_type or 'unknown'}"
            return False, [error_msg]

    def get_associated_files(self, file_path: Path) -> List[Path]:
        """
        Get files associated with a 3D file.

        Args:
            file_path: Path to the main file

        Returns:
            List of associated file paths
        """
        handler = self.get_handler_for_file(file_path)
        if handler:
            try:
                return handler.get_associated_files(file_path)
            except Exception as e:
                logger.warning(f"Failed to get associated files for {file_path}: {e}")
                return []
        return []

    def estimate_quality_score(self, file_path: Path, analysis_data: Dict[str, Any] = None) -> float:
        """
        Estimate quality score for a 3D file.

        Args:
            file_path: Path to the file
            analysis_data: Optional pre-computed analysis data

        Returns:
            Quality score from 0.0 to 1.0
        """
        handler = self.get_handler_for_file(file_path)
        if handler:
            if analysis_data is None:
                analysis_data = self.analyze_file(file_path)

            try:
                return handler.estimate_quality_score(analysis_data)
            except Exception as e:
                logger.warning(f"Failed to estimate quality score for {file_path}: {e}")
                return 0.0
        return 0.0

    def get_supported_formats(self) -> Dict[str, Dict[str, Any]]:
        """
        Get information about all supported formats.

        Returns:
            Dictionary with format information
        """
        formats = {}
        for format_type, handler in self.handlers.items():
            formats[format_type] = handler.get_format_info()
        return formats

    def get_supported_extensions(self) -> List[str]:
        """Get list of all supported file extensions."""
        return list(self.extension_map.keys())

    def extract_metadata_extras(self, file_path: Path) -> Dict[str, Any]:
        """
        Extract format-specific metadata from a file.

        Args:
            file_path: Path to the file

        Returns:
            Format-specific metadata dictionary
        """
        handler = self.get_handler_for_file(file_path)
        if handler:
            try:
                return handler.extract_metadata_extras(file_path)
            except Exception as e:
                logger.warning(f"Failed to extract metadata extras for {file_path}: {e}")
                return {'metadata_error': str(e)}
        return {}

    def can_convert_between(self, source_format: str, target_format: str) -> bool:
        """
        Check if conversion is possible between two formats.

        Args:
            source_format: Source format type
            target_format: Target format type

        Returns:
            True if conversion is theoretically possible
        """
        source_handler = self.get_handler(source_format)
        target_handler = self.get_handler(target_format)

        if not source_handler or not target_handler:
            return False

        source_caps = source_handler.get_capabilities()
        target_caps = target_handler.get_capabilities()

        return (source_caps.get('conversion_source', False) and
                target_caps.get('conversion_target', False))

    def get_format_statistics(self) -> Dict[str, Any]:
        """Get statistics about registered format handlers."""
        stats = {
            'total_formats': len(self.handlers),
            'total_extensions': len(self.extension_map),
            'formats': {},
            'capabilities_summary': {
                'animation_support': 0,
                'skeletal_support': 0,
                'conversion_source': 0,
                'conversion_target': 0
            }
        }

        for format_type, handler in self.handlers.items():
            capabilities = handler.get_capabilities()
            stats['formats'][format_type] = {
                'name': handler.format_name,
                'extensions': handler.extensions,
                'capabilities': capabilities
            }

            # Update capability summary
            for capability in stats['capabilities_summary']:
                if capabilities.get(capability, False):
                    stats['capabilities_summary'][capability] += 1

        return stats

    def repair_file(self, file_path: Path, issues: List[str]) -> tuple[bool, str]:
        """
        Attempt to repair a file using format-specific repair capabilities.

        Args:
            file_path: Path to the file to repair
            issues: List of issues found during validation

        Returns:
            Tuple of (success: bool, message: str)
        """
        handler = self.get_handler_for_file(file_path)
        if handler:
            try:
                return handler.repair_file(file_path, issues)
            except Exception as e:
                error_msg = f"Repair failed with {handler.format_name}: {str(e)}"
                logger.error(error_msg)
                return False, error_msg
        else:
            format_type = self.detect_format(file_path)
            error_msg = f"No handler available for repair of format: {format_type or 'unknown'}"
            return False, error_msg


# Global format manager instance
_global_format_manager: Optional[FormatManager] = None


def get_format_manager() -> FormatManager:
    """
    Get global format manager instance (singleton pattern).

    Returns:
        Global FormatManager instance
    """
    global _global_format_manager

    if _global_format_manager is None:
        _global_format_manager = FormatManager()
        logger.info("Initialized global FormatManager")

    return _global_format_manager


# Convenience functions
def detect_3d_format(file_path: Path) -> Optional[str]:
    """Detect format of a 3D file."""
    return get_format_manager().detect_format(file_path)


def analyze_3d_file(file_path: Path) -> Dict[str, Any]:
    """Analyze a 3D file using appropriate handler."""
    return get_format_manager().analyze_file(file_path)


def validate_3d_file(file_path: Path) -> tuple[bool, List[str]]:
    """Validate a 3D file using appropriate handler."""
    return get_format_manager().validate_file(file_path)


def get_3d_associated_files(file_path: Path) -> List[Path]:
    """Get files associated with a 3D file."""
    return get_format_manager().get_associated_files(file_path)


def get_supported_3d_formats() -> Dict[str, Dict[str, Any]]:
    """Get information about all supported 3D formats."""
    return get_format_manager().get_supported_formats()