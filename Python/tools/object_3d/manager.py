"""
3D Object Resource Manager

Handles storage and retrieval of 3D object resources (.obj, .fbx, etc.) using obj_uid system.
Provides session-based storage with metadata management and size limit enforcement.
"""

import json
import logging
import shutil
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
from ..ai.uid_manager import generate_object_uid, add_uid_mapping, get_uid_mapping
from ..ai.session_management.utils.path_manager import get_path_manager
from .formats.manager import get_format_manager

logger = logging.getLogger("UnrealMCP")


@dataclass
class Object3DMetadata:
    """Enhanced metadata structure for 3D objects."""
    # Core identification
    obj_uid: str
    filename: str
    original_filename: str
    format_type: str  # 'obj', 'fbx', 'gltf', 'vrm', 'pmx'

    # User-provided information
    description: str
    purpose: str
    session_id: str

    # File information
    size_bytes: int
    created_at: str
    file_checksum: str = None  # MD5 hash for integrity checking

    # Material and asset information
    has_materials: bool = False
    material_files: List[str] = None  # For .mtl files, textures, etc.
    texture_count: int = 0

    # 3D model characteristics
    vertex_count: int = 0
    face_count: int = 0
    triangle_count: int = 0
    bounding_box: Dict[str, List[float]] = None  # {"min": [x,y,z], "max": [x,y,z]}

    # Object relationships
    parent_obj_uid: str = None  # For hierarchical objects
    related_obj_uids: List[str] = None  # Related objects (variants, LODs, etc.)
    source_info: Dict[str, Any] = None  # Source attribution (Roblox user, etc.)

    # Quality and validation metrics
    quality_score: float = 0.0  # 0.0-1.0 quality assessment
    validation_issues: List[str] = None  # Known validation issues
    last_validated_at: str = None

    # Usage and access tracking
    access_count: int = 0
    last_accessed_at: str = None
    tags: List[str] = None  # User-defined tags for categorization

    # Extensible metadata
    metadata_extras: Dict[str, Any] = None
    schema_version: str = "1.1"  # For metadata migration

    def __post_init__(self):
        if self.material_files is None:
            self.material_files = []
        if self.related_obj_uids is None:
            self.related_obj_uids = []
        if self.validation_issues is None:
            self.validation_issues = []
        if self.tags is None:
            self.tags = []
        if self.metadata_extras is None:
            self.metadata_extras = {}
        if self.bounding_box is None:
            self.bounding_box = {"min": [0.0, 0.0, 0.0], "max": [0.0, 0.0, 0.0]}
        if self.source_info is None:
            self.source_info = {}


class Object3DManager:
    """Manages 3D object resource storage with UID-based access."""

    # Supported 3D formats and their extensions
    SUPPORTED_FORMATS = {
        'obj': ['.obj', '.mtl'],
        'fbx': ['.fbx'],
        'gltf': ['.gltf', '.glb'],
        'vrm': ['.vrm'],
        'pmx': ['.pmx']
    }

    def __init__(self, max_file_size_bytes: int = None):
        """
        Initialize Object3DManager.

        Args:
            max_file_size_bytes: Maximum file size limit (defaults to 1GB)
        """
        self.max_file_size_bytes = max_file_size_bytes or (1 * 1024 * 1024 * 1024)  # 1GB default
        self.path_manager = get_path_manager()
        self.format_manager = get_format_manager()

    def store_3d_object(
        self,
        session_id: str,
        file_path: str,
        description: str,
        purpose: str,
        format_type: str = None
    ) -> Tuple[bool, str, Optional[str]]:
        """
        Store a 3D object file with metadata.

        Args:
            session_id: Session ID for organization
            file_path: Path to the 3D object file
            description: Human-readable description
            purpose: Purpose/usage description
            format_type: Optional format override (auto-detected if None)

        Returns:
            Tuple of (success: bool, message: str, obj_uid: Optional[str])
        """
        try:
            source_path = Path(file_path)

            # Validate source file exists
            if not source_path.exists():
                return False, f"Source file not found: {file_path}", None

            # Auto-detect format if not provided
            if format_type is None:
                format_type = self.format_manager.detect_format(source_path)
                if format_type is None:
                    return False, f"Unsupported file format: {source_path.suffix}", None

            # Validate file size
            file_size = source_path.stat().st_size
            if file_size > self.max_file_size_bytes:
                size_mb = file_size / (1024 * 1024)
                limit_mb = self.max_file_size_bytes / (1024 * 1024)
                return False, f"File too large: {size_mb:.1f}MB exceeds limit of {limit_mb:.1f}MB", None

            # Generate UID
            obj_uid = generate_object_uid()

            # Get UID-specific storage path using new PathManager method
            uid_path = self.path_manager.get_3d_object_uid_path(obj_uid, session_id)
            session_path = Path(uid_path).parent  # Get parent to maintain compatibility with existing logic

            # Determine file naming strategy
            file_extension = source_path.suffix.lower()
            target_filename = f"{obj_uid}{file_extension}"
            target_path = session_path / target_filename

            # Copy primary file
            shutil.copy2(source_path, target_path)
            logger.info(f"Copied 3D object: {source_path} → {target_path}")

            # Handle associated files using format manager
            associated_files = self.format_manager.get_associated_files(source_path)
            material_files = []
            for assoc_file in associated_files:
                try:
                    # Copy associated file with obj_uid prefix
                    assoc_filename = f"{obj_uid}_{assoc_file.name}"
                    assoc_target = session_path / assoc_filename
                    shutil.copy2(assoc_file, assoc_target)
                    material_files.append(assoc_filename)
                    logger.info(f"Copied associated file: {assoc_file} → {assoc_target}")
                except Exception as e:
                    logger.warning(f"Failed to copy associated file {assoc_file}: {e}")

            # Analyze file for enhanced metadata using format handlers
            analysis_data = self.format_manager.analyze_file(target_path)

            # Calculate file checksum for integrity
            file_checksum = self._calculate_file_checksum(target_path)

            # Create enhanced metadata
            metadata = Object3DMetadata(
                obj_uid=obj_uid,
                filename=target_filename,
                original_filename=source_path.name,
                format_type=format_type,
                description=description,
                purpose=purpose,
                session_id=session_id,
                size_bytes=file_size,
                created_at=datetime.now().isoformat(),
                file_checksum=file_checksum,
                has_materials=len(material_files) > 0,
                material_files=material_files,
                texture_count=len(material_files),  # For now, approximate with material files
                vertex_count=analysis_data.get('vertex_count', 0),
                face_count=analysis_data.get('face_count', 0),
                triangle_count=analysis_data.get('triangle_count', 0),
                bounding_box=analysis_data.get('bounding_box', {"min": [0.0, 0.0, 0.0], "max": [0.0, 0.0, 0.0]}),
                quality_score=self.format_manager.estimate_quality_score(target_path, analysis_data),
                last_validated_at=datetime.now().isoformat()
            )

            # Save metadata file
            metadata_path = session_path / f"{obj_uid}_meta.json"
            with open(metadata_path, 'w', encoding='utf-8') as f:
                json.dump(asdict(metadata), f, indent=2, ensure_ascii=False)

            # Add to UID mapping system
            add_uid_mapping(
                uid=obj_uid,
                content_type='object',
                filename=target_filename,
                session_id=session_id,
                metadata={
                    'format_type': format_type,
                    'description': description,
                    'purpose': purpose,
                    'size_bytes': file_size,
                    'has_materials': len(material_files) > 0,
                    'original_filename': source_path.name
                }
            )

            logger.info(f"Stored 3D object {obj_uid} for session {session_id}: {description}")
            return True, f"Successfully stored 3D object as {obj_uid}", obj_uid

        except Exception as e:
            logger.error(f"Failed to store 3D object: {e}")
            return False, f"Storage failed: {str(e)}", None

    def get_3d_object(self, obj_uid: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve 3D object information and file paths.

        Args:
            obj_uid: Object UID to retrieve

        Returns:
            Dict with object metadata and file paths, or None if not found
        """
        try:
            # Get mapping from UID manager
            mapping = get_uid_mapping(obj_uid)
            if not mapping or mapping.get('type') != 'object':
                logger.warning(f"No object mapping found for obj_uid: {obj_uid}")
                return None

            session_id = mapping.get('session_id')
            if not session_id:
                logger.warning(f"No session_id in mapping for obj_uid: {obj_uid}")
                return None

            # Load metadata using new UID-based path
            uid_path = self.path_manager.get_3d_object_uid_path(obj_uid, session_id)
            session_path = Path(uid_path).parent  # Get parent to maintain compatibility
            metadata_path = session_path / f"{obj_uid}_meta.json"

            if not metadata_path.exists():
                logger.warning(f"Metadata not found: {metadata_path}")
                return None

            with open(metadata_path, 'r', encoding='utf-8') as f:
                metadata_dict = json.load(f)

            # Convert to metadata object for validation
            metadata = Object3DMetadata(**metadata_dict)

            # Check if main file exists
            main_file_path = session_path / metadata.filename
            if not main_file_path.exists():
                logger.warning(f"3D object file not found: {main_file_path}")
                return None

            # Build response
            return {
                'obj_uid': obj_uid,
                'metadata': asdict(metadata),
                'file_path': str(main_file_path),
                'material_file_paths': [
                    str(session_path / mat_file) for mat_file in metadata.material_files
                    if (session_path / mat_file).exists()
                ],
                'session_path': str(session_path)
            }

        except Exception as e:
            logger.error(f"Failed to retrieve 3D object {obj_uid}: {e}")
            return None

    def get_session_objects(self, session_id: str) -> List[Dict[str, Any]]:
        """
        Get all 3D objects for a session.

        Args:
            session_id: Session identifier

        Returns:
            List of 3D object metadata summaries
        """
        try:
            from ..ai.uid_manager import get_mappings_by_session_id

            # Get objects from UID manager
            session_mappings = get_mappings_by_session_id(session_id)
            objects = [mapping for mapping in session_mappings if mapping.get('type') == 'object']

            # Format for API response
            formatted_objects = []
            for obj in objects:
                obj_uid = obj['uid']
                metadata = obj.get('metadata', {})

                formatted_objects.append({
                    'obj_uid': obj_uid,
                    'filename': obj['filename'],
                    'format_type': metadata.get('format_type', 'unknown'),
                    'description': metadata.get('description', ''),
                    'purpose': metadata.get('purpose', ''),
                    'size_bytes': metadata.get('size_bytes', 0),
                    'has_materials': metadata.get('has_materials', False),
                    'original_filename': metadata.get('original_filename', obj['filename'])
                })

            return formatted_objects

        except Exception as e:
            logger.error(f"Failed to get session objects for {session_id}: {e}")
            return []

    def delete_3d_object(self, obj_uid: str) -> Tuple[bool, str]:
        """
        Delete a 3D object by obj_uid.

        Args:
            obj_uid: Object UID to delete

        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            # Get object info first
            obj_info = self.get_3d_object(obj_uid)
            if not obj_info:
                return False, f"3D object not found: {obj_uid}"

            session_path = Path(obj_info['session_path'])
            metadata = obj_info['metadata']

            # Delete main file
            main_file_path = Path(obj_info['file_path'])
            if main_file_path.exists():
                main_file_path.unlink()

            # Delete material files
            for mat_file_path in obj_info['material_file_paths']:
                mat_path = Path(mat_file_path)
                if mat_path.exists():
                    mat_path.unlink()

            # Delete metadata file
            metadata_path = session_path / f"{obj_uid}_meta.json"
            if metadata_path.exists():
                metadata_path.unlink()

            logger.info(f"Deleted 3D object {obj_uid}: {metadata['description']}")
            return True, f"Successfully deleted 3D object {obj_uid}"

        except Exception as e:
            logger.error(f"Failed to delete 3D object {obj_uid}: {e}")
            return False, f"Deletion failed: {str(e)}"

    def validate_3d_object(self, obj_uid: str) -> Tuple[bool, str, List[str]]:
        """
        Validate a 3D object's files and metadata integrity.

        Args:
            obj_uid: Object UID to validate

        Returns:
            Tuple of (is_valid: bool, message: str, issues: List[str])
        """
        issues = []

        try:
            obj_info = self.get_3d_object(obj_uid)
            if not obj_info:
                return False, f"Object not found: {obj_uid}", ["Object does not exist"]

            # Check main file
            main_file_path = Path(obj_info['file_path'])
            if not main_file_path.exists():
                issues.append(f"Main file missing: {main_file_path}")
            else:
                # Use format manager for validation
                format_valid, format_issues = self.format_manager.validate_file(main_file_path)
                if not format_valid:
                    issues.extend([f"Format validation: {issue}" for issue in format_issues])

            # Check material files
            for mat_file_path in obj_info['material_file_paths']:
                if not Path(mat_file_path).exists():
                    issues.append(f"Material file missing: {mat_file_path}")

            # Check size limits
            if main_file_path.exists():
                current_size = main_file_path.stat().st_size
                if current_size > self.max_file_size_bytes:
                    issues.append(f"File exceeds size limit: {current_size} > {self.max_file_size_bytes}")

            # Check metadata consistency
            metadata = obj_info['metadata']
            if main_file_path.exists() and metadata['size_bytes'] != main_file_path.stat().st_size:
                issues.append("Metadata size mismatch with actual file size")

            if issues:
                return False, f"Validation failed for {obj_uid}", issues
            else:
                return True, f"Object {obj_uid} is valid", []

        except Exception as e:
            error_msg = f"Validation error for {obj_uid}: {str(e)}"
            logger.error(error_msg)
            return False, error_msg, [str(e)]

    def get_storage_stats(self) -> Dict[str, Any]:
        """
        Get storage statistics for 3D objects.

        Returns:
            Dict with storage statistics
        """
        try:
            from ..ai.uid_manager import get_uid_manager

            # Get all object mappings
            uid_manager = get_uid_manager()
            all_mappings = uid_manager.get_all_mappings()
            object_mappings = {uid: mapping for uid, mapping in all_mappings.items()
                             if mapping.get('type') == 'object'}

            # Calculate stats
            total_objects = len(object_mappings)
            total_size_bytes = sum(mapping.get('metadata', {}).get('size_bytes', 0)
                                 for mapping in object_mappings.values())

            # Format breakdown
            format_counts = {}
            session_counts = {}

            for mapping in object_mappings.values():
                metadata = mapping.get('metadata', {})
                format_type = metadata.get('format_type', 'unknown')
                session_id = mapping.get('session_id', 'unknown')

                format_counts[format_type] = format_counts.get(format_type, 0) + 1
                session_counts[session_id] = session_counts.get(session_id, 0) + 1

            return {
                'total_objects': total_objects,
                'total_size_bytes': total_size_bytes,
                'total_size_mb': round(total_size_bytes / (1024 * 1024), 2),
                'max_size_limit_mb': round(self.max_file_size_bytes / (1024 * 1024), 2),
                'format_breakdown': format_counts,
                'session_breakdown': session_counts,
                'storage_path': self.path_manager.get_3d_objects_path()
            }

        except Exception as e:
            logger.error(f"Failed to get storage stats: {e}")
            return {'error': str(e)}

    def _calculate_file_checksum(self, file_path: Path) -> str:
        """Calculate MD5 checksum of file for integrity checking."""
        try:
            import hashlib

            hash_md5 = hashlib.md5()
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)

            return hash_md5.hexdigest()

        except Exception as e:
            logger.warning(f"Failed to calculate checksum for {file_path}: {e}")
            return None

    def update_object_metadata(
        self,
        obj_uid: str,
        updates: Dict[str, Any]
    ) -> Tuple[bool, str]:
        """
        Update metadata for an existing 3D object.

        Args:
            obj_uid: Object UID to update
            updates: Dictionary of metadata fields to update

        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            # Get current object info
            obj_info = self.get_3d_object(obj_uid)
            if not obj_info:
                return False, f"Object {obj_uid} not found"

            # Load current metadata
            metadata_dict = obj_info['metadata']
            metadata = Object3DMetadata(**metadata_dict)

            # Apply updates
            for field, value in updates.items():
                if hasattr(metadata, field):
                    setattr(metadata, field, value)
                else:
                    # Store in metadata_extras for unknown fields
                    metadata.metadata_extras[field] = value

            # Update access tracking
            metadata.access_count += 1
            metadata.last_accessed_at = datetime.now().isoformat()

            # Save updated metadata
            session_path = Path(obj_info['session_path'])
            metadata_path = session_path / f"{obj_uid}_meta.json"

            with open(metadata_path, 'w', encoding='utf-8') as f:
                json.dump(asdict(metadata), f, indent=2, ensure_ascii=False)

            logger.info(f"Updated metadata for {obj_uid}")
            return True, f"Successfully updated metadata for {obj_uid}"

        except Exception as e:
            error_msg = f"Failed to update metadata for {obj_uid}: {str(e)}"
            logger.error(error_msg)
            return False, error_msg

    def search_objects(
        self,
        query: str = None,
        format_type: str = None,
        session_id: str = None,
        tags: List[str] = None,
        min_quality_score: float = None,
        max_size_bytes: int = None
    ) -> List[Dict[str, Any]]:
        """
        Search 3D objects based on metadata criteria.

        Args:
            query: Text search in description/purpose
            format_type: Filter by format type
            session_id: Filter by session ID
            tags: Filter by tags (must have all tags)
            min_quality_score: Minimum quality score
            max_size_bytes: Maximum file size

        Returns:
            List of matching objects with metadata
        """
        try:
            from ..ai.uid_manager import get_uid_manager

            # Get all object mappings
            uid_manager = get_uid_manager()
            all_mappings = uid_manager.get_all_mappings()
            object_mappings = {uid: mapping for uid, mapping in all_mappings.items()
                             if mapping.get('type') == 'object'}

            matching_objects = []

            for uid, mapping in object_mappings.items():
                try:
                    # Get detailed object info
                    obj_info = self.get_3d_object(uid)
                    if not obj_info:
                        continue

                    metadata = obj_info['metadata']

                    # Apply filters
                    if session_id and metadata.get('session_id') != session_id:
                        continue

                    if format_type and metadata.get('format_type') != format_type:
                        continue

                    if min_quality_score is not None and metadata.get('quality_score', 0) < min_quality_score:
                        continue

                    if max_size_bytes is not None and metadata.get('size_bytes', 0) > max_size_bytes:
                        continue

                    if tags:
                        object_tags = metadata.get('tags', [])
                        if not all(tag in object_tags for tag in tags):
                            continue

                    if query:
                        # Text search in description and purpose
                        search_text = (
                            metadata.get('description', '') + ' ' +
                            metadata.get('purpose', '') + ' ' +
                            ' '.join(metadata.get('tags', []))
                        ).lower()

                        if query.lower() not in search_text:
                            continue

                    # Add to results
                    result_obj = {
                        'obj_uid': uid,
                        'filename': metadata.get('filename', ''),
                        'description': metadata.get('description', ''),
                        'purpose': metadata.get('purpose', ''),
                        'format_type': metadata.get('format_type', ''),
                        'session_id': metadata.get('session_id', ''),
                        'size_bytes': metadata.get('size_bytes', 0),
                        'quality_score': metadata.get('quality_score', 0.0),
                        'created_at': metadata.get('created_at', ''),
                        'tags': metadata.get('tags', [])
                    }

                    matching_objects.append(result_obj)

                except Exception as e:
                    logger.warning(f"Error processing object {uid} in search: {e}")
                    continue

            # Sort by quality score (highest first)
            matching_objects.sort(key=lambda x: x.get('quality_score', 0), reverse=True)

            return matching_objects

        except Exception as e:
            logger.error(f"Failed to search objects: {e}")
            return []

    def add_object_relationship(
        self,
        obj_uid: str,
        related_uid: str,
        relationship_type: str = "related"
    ) -> Tuple[bool, str]:
        """
        Add a relationship between two 3D objects.

        Args:
            obj_uid: Primary object UID
            related_uid: Related object UID
            relationship_type: Type of relationship (for future use)

        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            # Verify both objects exist
            obj1 = self.get_3d_object(obj_uid)
            obj2 = self.get_3d_object(related_uid)

            if not obj1:
                return False, f"Object {obj_uid} not found"
            if not obj2:
                return False, f"Related object {related_uid} not found"

            # Update primary object's relationships
            current_related = obj1['metadata'].get('related_obj_uids', [])
            if related_uid not in current_related:
                current_related.append(related_uid)

                success, message = self.update_object_metadata(
                    obj_uid,
                    {'related_obj_uids': current_related}
                )

                if success:
                    logger.info(f"Added relationship: {obj_uid} -> {related_uid}")
                    return True, f"Successfully linked {obj_uid} with {related_uid}"
                else:
                    return False, message
            else:
                return True, f"Relationship already exists between {obj_uid} and {related_uid}"

        except Exception as e:
            error_msg = f"Failed to add relationship: {str(e)}"
            logger.error(error_msg)
            return False, error_msg


# Global instance for shared access
_global_object_3d_manager: Optional[Object3DManager] = None


def get_object_3d_manager(max_file_size_bytes: int = None) -> Object3DManager:
    """
    Get global Object3DManager instance (singleton pattern).

    Args:
        max_file_size_bytes: Maximum file size limit (only used on first call)

    Returns:
        Global Object3DManager instance
    """
    global _global_object_3d_manager

    if _global_object_3d_manager is None:
        _global_object_3d_manager = Object3DManager(max_file_size_bytes)
        logger.info(f"Initialized global Object3DManager with {max_file_size_bytes or '1GB'} size limit")

    return _global_object_3d_manager


# Convenience functions
def store_3d_object(session_id: str, file_path: str, description: str, purpose: str, format_type: str = None) -> Tuple[bool, str, Optional[str]]:
    """Store 3D object and return success status, message, and obj_uid."""
    return get_object_3d_manager().store_3d_object(session_id, file_path, description, purpose, format_type)


def get_3d_object(obj_uid: str) -> Optional[Dict[str, Any]]:
    """Get 3D object data by obj_uid."""
    return get_object_3d_manager().get_3d_object(obj_uid)


def get_session_objects(session_id: str) -> List[Dict[str, Any]]:
    """Get all 3D objects for a session."""
    return get_object_3d_manager().get_session_objects(session_id)


def delete_3d_object(obj_uid: str) -> Tuple[bool, str]:
    """Delete 3D object by obj_uid."""
    return get_object_3d_manager().delete_3d_object(obj_uid)


def validate_3d_object(obj_uid: str) -> Tuple[bool, str, List[str]]:
    """Validate 3D object integrity."""
    return get_object_3d_manager().validate_3d_object(obj_uid)


def get_3d_object_statistics() -> Dict[str, Any]:
    """Get 3D object storage statistics."""
    return get_object_3d_manager().get_storage_stats()


def update_3d_object_metadata(obj_uid: str, updates: Dict[str, Any]) -> Tuple[bool, str]:
    """Update metadata for a 3D object."""
    return get_object_3d_manager().update_object_metadata(obj_uid, updates)


def search_3d_objects(
    query: str = None,
    format_type: str = None,
    session_id: str = None,
    tags: List[str] = None,
    min_quality_score: float = None,
    max_size_bytes: int = None
) -> List[Dict[str, Any]]:
    """Search 3D objects based on metadata criteria."""
    return get_object_3d_manager().search_objects(
        query, format_type, session_id, tags, min_quality_score, max_size_bytes
    )


def add_3d_object_relationship(obj_uid: str, related_uid: str, relationship_type: str = "related") -> Tuple[bool, str]:
    """Add a relationship between two 3D objects."""
    return get_object_3d_manager().add_object_relationship(obj_uid, related_uid, relationship_type)


def get_supported_3d_formats() -> Dict[str, Dict[str, Any]]:
    """Get information about supported 3D formats."""
    return get_object_3d_manager().format_manager.get_supported_formats()


def get_format_statistics() -> Dict[str, Any]:
    """Get statistics about 3D format support."""
    return get_object_3d_manager().format_manager.get_format_statistics()