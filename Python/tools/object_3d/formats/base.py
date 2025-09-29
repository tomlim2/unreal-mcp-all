"""
Base Format Handler for 3D Object Processing

Defines the interface and common functionality for all 3D format handlers.
Each specific format (OBJ, FBX, GLTF, etc.) implements this interface.
"""

import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

logger = logging.getLogger("UnrealMCP")


class BaseFormatHandler(ABC):
    """
    Abstract base class for 3D format handlers.

    Each format handler provides format-specific analysis, validation,
    and processing capabilities for a particular 3D file format.
    """

    def __init__(self, format_name: str, extensions: List[str]):
        """
        Initialize format handler.

        Args:
            format_name: Human-readable format name (e.g., "Wavefront OBJ")
            extensions: List of file extensions (e.g., ['.obj', '.mtl'])
        """
        self.format_name = format_name
        self.extensions = [ext.lower() for ext in extensions]
        self.logger = logger

    def supports_extension(self, extension: str) -> bool:
        """Check if this handler supports the given file extension."""
        return extension.lower() in self.extensions

    @abstractmethod
    def analyze_file(self, file_path: Path) -> Dict[str, Any]:
        """
        Analyze a 3D file and extract structural information.

        Args:
            file_path: Path to the 3D file

        Returns:
            Dictionary containing analysis results with standardized keys:
            - vertex_count: Number of vertices
            - face_count: Number of faces/polygons
            - triangle_count: Number of triangles
            - bounding_box: {"min": [x,y,z], "max": [x,y,z]}
            - has_normals: Boolean indicating presence of vertex normals
            - has_texture_coords: Boolean indicating presence of UV coordinates
            - material_references: List of material names/IDs
            - groups: List of group/object names
            - format_specific: Dict with format-specific analysis data
        """
        pass

    @abstractmethod
    def validate_file(self, file_path: Path) -> Tuple[bool, List[str]]:
        """
        Validate a 3D file for format-specific issues.

        Args:
            file_path: Path to the 3D file

        Returns:
            Tuple of (is_valid: bool, issues: List[str])
        """
        pass

    def get_associated_files(self, file_path: Path) -> List[Path]:
        """
        Get list of files associated with the main 3D file.

        Args:
            file_path: Path to the main 3D file

        Returns:
            List of associated file paths (materials, textures, etc.)
        """
        # Default implementation returns empty list
        # Override in specific handlers as needed
        return []

    def estimate_quality_score(self, analysis_data: Dict[str, Any]) -> float:
        """
        Estimate quality score based on analysis data.

        Args:
            analysis_data: Analysis results from analyze_file()

        Returns:
            Quality score from 0.0 to 1.0
        """
        try:
            score = 0.0
            max_score = 0.0

            # Base scoring criteria (can be overridden by specific handlers)

            # Geometry complexity score
            vertex_count = analysis_data.get('vertex_count', 0)
            face_count = analysis_data.get('face_count', 0)

            if vertex_count > 0:
                vertex_score = min(1.0, vertex_count / 10000.0)  # Normalize to 10k vertices
                score += vertex_score * 0.3
            max_score += 0.3

            if face_count > 0:
                face_score = min(1.0, face_count / 5000.0)  # Normalize to 5k faces
                score += face_score * 0.3
            max_score += 0.3

            # Structural completeness
            if analysis_data.get('has_normals', False):
                score += 0.15
            max_score += 0.15

            if analysis_data.get('has_texture_coords', False):
                score += 0.15
            max_score += 0.15

            if analysis_data.get('material_references', []):
                score += 0.1
            max_score += 0.1

            # Return normalized score
            return score / max_score if max_score > 0 else 0.0

        except Exception as e:
            self.logger.warning(f"Failed to calculate quality score: {e}")
            return 0.0

    def get_format_info(self) -> Dict[str, Any]:
        """Get information about this format handler."""
        return {
            'format_name': self.format_name,
            'extensions': self.extensions,
            'capabilities': self.get_capabilities()
        }

    def get_capabilities(self) -> Dict[str, bool]:
        """
        Get capabilities supported by this format handler.

        Returns:
            Dict with capability flags
        """
        return {
            'analysis': True,
            'validation': True,
            'associated_files': True,
            'quality_scoring': True,
            'conversion_target': False,  # Can this format be converted to?
            'conversion_source': False,  # Can this format be converted from?
            'animation_support': False,
            'skeletal_support': False,
            'material_support': True
        }

    def preprocess_file(self, file_path: Path, output_dir: Path) -> Optional[Path]:
        """
        Preprocess a file before storage (optional).

        Args:
            file_path: Original file path
            output_dir: Directory for processed output

        Returns:
            Path to processed file, or None if no preprocessing needed
        """
        # Default: no preprocessing
        return None

    def extract_metadata_extras(self, file_path: Path) -> Dict[str, Any]:
        """
        Extract format-specific metadata not covered by standard analysis.

        Args:
            file_path: Path to the 3D file

        Returns:
            Dictionary with format-specific metadata
        """
        return {}

    def repair_file(self, file_path: Path, issues: List[str]) -> Tuple[bool, str]:
        """
        Attempt to repair common file issues (optional feature).

        Args:
            file_path: Path to the file to repair
            issues: List of issues found during validation

        Returns:
            Tuple of (success: bool, message: str)
        """
        return False, f"Repair not implemented for {self.format_name}"