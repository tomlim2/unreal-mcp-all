"""
Roblox 3D Avatar Integration with Object3DManager

Provides seamless integration between the existing Roblox Avatar 3D downloader
and the new Object3DManager UID system for centralized 3D object storage.
"""

import logging
import tempfile
import shutil
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from ..ai.command_handlers.roblox.scripts.roblox_obj_downloader import RobloxAvatar3DDownloader
from .manager import (
    get_object_3d_manager,
    store_3d_object,
    get_3d_object,
    get_session_objects
)

logger = logging.getLogger("UnrealMCP")


class RobloxObject3DIntegration:
    """Integration layer between Roblox downloader and Object3DManager."""

    def __init__(self, max_file_size_bytes: int = None):
        """
        Initialize Roblox 3D integration.

        Args:
            max_file_size_bytes: Maximum file size limit (defaults to Object3DManager default)
        """
        self.object_manager = get_object_3d_manager(max_file_size_bytes)
        self.roblox_downloader = None

    def download_and_store_avatar(
        self,
        session_id: str,
        user_input: str,
        description: str = None,
        purpose: str = "Roblox avatar download",
        include_textures: bool = True,
        include_thumbnails: bool = False
    ) -> Tuple[bool, str, Optional[List[str]]]:
        """
        Download a Roblox avatar and store it in the Object3DManager system.

        Args:
            session_id: Session ID for organization
            user_input: Roblox user ID or username
            description: Optional description (auto-generated if None)
            purpose: Purpose description
            include_textures: Whether to include texture files
            include_thumbnails: Whether to include 2D thumbnails

        Returns:
            Tuple of (success: bool, message: str, obj_uids: Optional[List[str]])
        """
        try:
            # Create temporary download directory
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)

                # Initialize Roblox downloader with temp directory
                self.roblox_downloader = RobloxAvatar3DDownloader(str(temp_path))

                # Resolve user input to user ID
                user_id = self.roblox_downloader.resolve_user_input(user_input)
                if user_id is None:
                    return False, f"Could not resolve user: {user_input}", None

                # Get user info for description
                user_info = self.roblox_downloader.get_user_info(user_id)
                if not user_info:
                    return False, f"Could not get user info for ID: {user_id}", None

                username = user_info.get('name', f'user_{user_id}')
                display_name = user_info.get('displayName', username)

                # Auto-generate description if not provided
                if description is None:
                    description = f"Roblox avatar: {display_name} (@{username})"

                logger.info(f"Downloading Roblox avatar for {display_name} (@{username})")

                # Download the complete 3D avatar
                download_success = self.roblox_downloader.download_avatar_3d_complete(
                    user_id=user_id,
                    include_textures=include_textures,
                    include_thumbnails=include_thumbnails
                )

                if not download_success:
                    return False, f"Failed to download avatar for {username}", None

                # Find the downloaded avatar directory
                avatar_dir = self._find_avatar_directory(temp_path, username, user_id)
                if not avatar_dir or not avatar_dir.exists():
                    return False, f"Downloaded avatar directory not found for {username}", None

                logger.info(f"Found downloaded avatar at: {avatar_dir}")

                # Store files in Object3DManager
                obj_uids = []
                stored_files = []

                # Store main OBJ file
                obj_file = avatar_dir / "avatar.obj"
                if obj_file.exists():
                    success, message, obj_uid = store_3d_object(
                        session_id=session_id,
                        file_path=str(obj_file),
                        description=f"{description} (OBJ model)",
                        purpose=purpose,
                        format_type="obj"
                    )

                    if success and obj_uid:
                        obj_uids.append(obj_uid)
                        stored_files.append(f"OBJ model as {obj_uid}")
                        logger.info(f"Stored OBJ file as {obj_uid}")
                    else:
                        logger.warning(f"Failed to store OBJ file: {message}")

                # Store additional files if requested
                additional_files = []

                # Include texture files
                if include_textures:
                    textures_dir = avatar_dir / "textures"
                    if textures_dir.exists():
                        texture_files = list(textures_dir.glob("texture_*.png"))
                        for i, texture_file in enumerate(texture_files[:5]):  # Limit to first 5 textures
                            success, message, tex_uid = store_3d_object(
                                session_id=session_id,
                                file_path=str(texture_file),
                                description=f"{description} (Texture {i+1})",
                                purpose=f"{purpose} - texture",
                                format_type="png"  # Treat textures as generic files
                            )

                            if success and tex_uid:
                                additional_files.append(f"Texture {i+1} as {tex_uid}")
                                logger.info(f"Stored texture {i+1} as {tex_uid}")

                # Store metadata file as reference
                metadata_file = avatar_dir / "metadata.json"
                if metadata_file.exists():
                    success, message, meta_uid = store_3d_object(
                        session_id=session_id,
                        file_path=str(metadata_file),
                        description=f"{description} (Metadata)",
                        purpose=f"{purpose} - metadata",
                        format_type="json"  # Treat as generic file
                    )

                    if success and meta_uid:
                        additional_files.append(f"Metadata as {meta_uid}")
                        logger.info(f"Stored metadata as {meta_uid}")

                # Prepare success message
                if obj_uids:
                    file_summary = [f"Main OBJ models: {len(obj_uids)} stored"] + additional_files
                    summary_msg = f"Successfully downloaded and stored Roblox avatar for {display_name}:\n" + \
                                "\n".join([f"  - {item}" for item in file_summary])

                    return True, summary_msg, obj_uids
                else:
                    return False, f"No OBJ files were successfully stored for {username}", None

        except Exception as e:
            error_msg = f"Failed to download and store Roblox avatar: {str(e)}"
            logger.error(error_msg)
            return False, error_msg, None

    def get_roblox_avatars_by_session(self, session_id: str) -> List[Dict[str, Any]]:
        """
        Get all Roblox avatars stored in a session.

        Args:
            session_id: Session ID to search

        Returns:
            List of Roblox avatar objects with enhanced metadata
        """
        try:
            session_objects = get_session_objects(session_id)

            # Filter for Roblox objects (purpose contains "Roblox")
            roblox_objects = [
                obj for obj in session_objects
                if "roblox" in obj.get('purpose', '').lower() or
                   "roblox" in obj.get('description', '').lower()
            ]

            # Enhance with Roblox-specific metadata
            enhanced_objects = []
            for obj in roblox_objects:
                enhanced_obj = obj.copy()

                # Extract Roblox user info from description
                description = obj.get('description', '')
                if '@' in description:
                    try:
                        # Extract username from "Roblox avatar: DisplayName (@username)"
                        username_part = description.split('@')[-1].rstrip(')')
                        enhanced_obj['roblox_username'] = username_part
                    except:
                        pass

                # Add Roblox-specific metadata
                enhanced_obj['is_roblox_avatar'] = True
                enhanced_obj['avatar_type'] = self._guess_avatar_type_from_description(description)

                enhanced_objects.append(enhanced_obj)

            return enhanced_objects

        except Exception as e:
            logger.error(f"Failed to get Roblox avatars for session {session_id}: {e}")
            return []

    def validate_roblox_avatar(self, obj_uid: str) -> Tuple[bool, str, List[str]]:
        """
        Validate a Roblox avatar object with Roblox-specific checks.

        Args:
            obj_uid: Object UID to validate

        Returns:
            Tuple of (is_valid: bool, message: str, issues: List[str])
        """
        try:
            # Use base Object3DManager validation
            is_valid, message, issues = self.object_manager.validate_3d_object(obj_uid)

            # Get object info for Roblox-specific validation
            obj_info = get_3d_object(obj_uid)
            if not obj_info:
                return False, f"Object {obj_uid} not found", ["Object does not exist"]

            # Add Roblox-specific validation
            metadata = obj_info.get('metadata', {})
            description = metadata.get('description', '')

            # Check if it's actually a Roblox object
            if not ("roblox" in description.lower() or "roblox" in metadata.get('purpose', '').lower()):
                issues.append("Object does not appear to be a Roblox avatar")

            # Check OBJ format for Roblox avatars
            if metadata.get('format_type') == 'obj':
                file_path = obj_info.get('file_path')
                if file_path and Path(file_path).exists():
                    roblox_issues = self._validate_roblox_obj_structure(Path(file_path))
                    issues.extend(roblox_issues)

            # Update validity based on Roblox-specific checks
            if issues and is_valid:
                is_valid = False
                message = f"Roblox avatar validation failed for {obj_uid}"

            return is_valid, message, issues

        except Exception as e:
            error_msg = f"Roblox avatar validation error for {obj_uid}: {str(e)}"
            logger.error(error_msg)
            return False, error_msg, [str(e)]

    def _find_avatar_directory(self, temp_path: Path, username: str, user_id: int) -> Optional[Path]:
        """Find the downloaded avatar directory."""
        # Try common patterns used by RobloxAvatar3DDownloader
        patterns = [
            f"{username}_{user_id}_3D",
            f"{username}_{user_id}",
            f"user_{user_id}_3D",
            f"user_{user_id}"
        ]

        for pattern in patterns:
            candidate = temp_path / pattern
            if candidate.exists() and candidate.is_dir():
                return candidate

        # Fall back to searching all directories
        for dir_path in temp_path.iterdir():
            if dir_path.is_dir() and str(user_id) in dir_path.name:
                return dir_path

        return None

    def _guess_avatar_type_from_description(self, description: str) -> str:
        """Guess Roblox avatar type (R6/R15) from description."""
        desc_lower = description.lower()
        if "r15" in desc_lower:
            return "R15"
        elif "r6" in desc_lower:
            return "R6"
        else:
            return "Unknown"

    def _validate_roblox_obj_structure(self, obj_path: Path) -> List[str]:
        """Validate OBJ file structure for Roblox-specific issues."""
        issues = []

        try:
            with open(obj_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()

                # Check for common Roblox OBJ patterns
                if 'player' not in content.lower() and 'group' not in content.lower():
                    issues.append("OBJ file doesn't contain expected Roblox group patterns")

                # Check for material references
                if 'usemtl' not in content:
                    issues.append("OBJ file lacks material references (usemtl statements)")

                # Basic structure validation
                vertex_count = content.count('\nv ')
                face_count = content.count('\nf ')

                if vertex_count < 10:
                    issues.append(f"Very low vertex count ({vertex_count}) for a 3D avatar")

                if face_count < 10:
                    issues.append(f"Very low face count ({face_count}) for a 3D avatar")

        except Exception as e:
            issues.append(f"Failed to validate OBJ structure: {str(e)}")

        return issues


# Global instance for shared access
_global_roblox_integration: Optional[RobloxObject3DIntegration] = None


def get_roblox_3d_integration(max_file_size_bytes: int = None) -> RobloxObject3DIntegration:
    """
    Get global RobloxObject3DIntegration instance (singleton pattern).

    Args:
        max_file_size_bytes: Maximum file size limit (only used on first call)

    Returns:
        Global RobloxObject3DIntegration instance
    """
    global _global_roblox_integration

    if _global_roblox_integration is None:
        _global_roblox_integration = RobloxObject3DIntegration(max_file_size_bytes)
        logger.info("Initialized global RobloxObject3DIntegration")

    return _global_roblox_integration


# Convenience functions
def download_roblox_avatar(
    session_id: str,
    user_input: str,
    description: str = None,
    purpose: str = "Roblox avatar download",
    include_textures: bool = True,
    include_thumbnails: bool = False
) -> Tuple[bool, str, Optional[List[str]]]:
    """Download and store Roblox avatar."""
    return get_roblox_3d_integration().download_and_store_avatar(
        session_id, user_input, description, purpose, include_textures, include_thumbnails
    )


def get_roblox_avatars_by_session(session_id: str) -> List[Dict[str, Any]]:
    """Get all Roblox avatars for a session."""
    return get_roblox_3d_integration().get_roblox_avatars_by_session(session_id)


def validate_roblox_avatar(obj_uid: str) -> Tuple[bool, str, List[str]]:
    """Validate Roblox avatar object."""
    return get_roblox_3d_integration().validate_roblox_avatar(obj_uid)