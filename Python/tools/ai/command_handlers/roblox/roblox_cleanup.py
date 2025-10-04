"""
Roblox download cleanup and duplicate management utilities.

Handles cleanup of existing downloads when the same user is requested again,
preventing storage waste and ensuring users always get the latest avatar version.
"""

import logging
import shutil
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from core.resources.uid_manager import get_uid_manager
from core.utils.path_manager import get_path_manager

logger = logging.getLogger("UnrealMCP.Roblox.Cleanup")


class RobloxCleanupManager:
    """
    Manager for cleaning up duplicate Roblox downloads and managing storage.

    Features:
    - Detect duplicate downloads by user ID/username
    - Clean up existing files and UID mappings
    - Optionally reuse existing UIDs for consistency
    - Session-aware cleanup (only clean within same session)
    """

    def __init__(self):
        self.uid_manager = get_uid_manager()
        self.path_manager = get_path_manager()

    def find_existing_downloads(self, user_input: str, session_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Find existing downloads for the same user.

        Args:
            user_input: Username or user ID to search for
            session_id: Optional session ID to limit search scope

        Returns:
            List of existing download mappings that match the user
        """
        try:
            # Get all UID mappings
            all_mappings = self.uid_manager.get_all_mappings()

            existing_downloads = []

            for uid, mapping in all_mappings.items():
                # Only check 3D object mappings
                if mapping.get('type') != '3d_object':
                    continue

                # Only check Roblox downloads
                metadata = mapping.get('metadata', {})
                if metadata.get('download_type') != 'roblox_3d_avatar':
                    continue

                # If session_id provided, only check within same session
                if session_id and mapping.get('session_id') != session_id:
                    continue

                # Check if user matches
                if self._is_same_user(user_input, metadata):
                    download_info = {
                        'uid': uid,
                        'mapping': mapping,
                        'username': metadata.get('username'),
                        'user_id': metadata.get('user_id'),
                        'downloaded_at': metadata.get('downloaded_at'),
                        'session_id': mapping.get('session_id')
                    }
                    existing_downloads.append(download_info)

            if existing_downloads:
                logger.info(f"Found {len(existing_downloads)} existing downloads for user '{user_input}'")

            return existing_downloads

        except Exception as e:
            logger.error(f"Error finding existing downloads for '{user_input}': {e}")
            return []

    def _is_same_user(self, user_input: str, metadata: Dict[str, Any]) -> bool:
        """
        Check if the user input matches the metadata user.

        Args:
            user_input: Input username or user ID
            metadata: Download metadata containing username and user_id

        Returns:
            True if they represent the same user
        """
        try:
            # Normalize input
            input_normalized = user_input.strip().lower()

            # Get stored user info
            stored_username = metadata.get('username', '').lower()
            stored_user_id = metadata.get('user_id')

            # Check username match
            if input_normalized == stored_username:
                return True

            # Check user ID match (if input is numeric)
            if input_normalized.isdigit():
                input_user_id = int(input_normalized)
                if input_user_id == stored_user_id:
                    return True

            # Check if stored user_id matches input as string
            if str(stored_user_id) == input_normalized:
                return True

            return False

        except Exception as e:
            logger.warning(f"Error comparing users '{user_input}' with metadata: {e}")
            return False

    def cleanup_existing_downloads(self, existing_downloads: List[Dict[str, Any]]) -> Tuple[int, List[str]]:
        """
        Clean up existing downloads (files and UID mappings).

        Args:
            existing_downloads: List of download info dicts to clean up

        Returns:
            Tuple of (cleanup_count, cleaned_uids)
        """
        cleanup_count = 0
        cleaned_uids = []

        for download_info in existing_downloads:
            uid = download_info['uid']
            mapping = download_info['mapping']

            try:
                # Clean up files
                if self._cleanup_download_files(uid, mapping):
                    logger.info(f"Cleaned up files for UID: {uid}")

                # Remove UID mapping
                if uid in self.uid_manager.get_all_mappings():
                    del self.uid_manager._uid_mappings[uid]
                    self.uid_manager._save_state()
                    logger.info(f"Removed UID mapping: {uid}")

                cleanup_count += 1
                cleaned_uids.append(uid)

            except Exception as e:
                logger.error(f"Error cleaning up download {uid}: {e}")

        if cleanup_count > 0:
            logger.info(f"Successfully cleaned up {cleanup_count} existing downloads")

        return cleanup_count, cleaned_uids

    def _cleanup_download_files(self, uid: str, mapping: Dict[str, Any]) -> bool:
        """
        Clean up downloaded files for a specific UID.

        Args:
            uid: UID of the download to clean up
            mapping: UID mapping containing file information

        Returns:
            True if cleanup was successful
        """
        try:
            # Try to determine download folder from mapping
            download_folder = self._get_download_folder_from_mapping(uid, mapping)

            if download_folder and download_folder.exists():
                # Remove entire download folder
                shutil.rmtree(download_folder)
                logger.info(f"Removed download folder: {download_folder}")
                return True
            else:
                logger.warning(f"Download folder not found for UID {uid}: {download_folder}")
                return False

        except Exception as e:
            logger.error(f"Error cleaning up files for UID {uid}: {e}")
            return False

    def _get_download_folder_from_mapping(self, uid: str, mapping: Dict[str, Any]) -> Optional[Path]:
        """
        Determine the download folder path from UID mapping.

        Args:
            uid: UID of the download
            mapping: UID mapping information

        Returns:
            Path to download folder if determinable
        """
        try:
            # Use new PathManager method for clean object_3d/[uid]/ structure
            session_id = mapping.get('session_id')
            uid_path = self.path_manager.get_3d_object_uid_path(uid, session_id)
            download_folder = Path(uid_path)

            # Verify this looks like a Roblox download folder
            if download_folder.exists():
                # Check for typical Roblox files
                expected_files = ['avatar.obj', 'avatar.mtl', 'metadata.json', 'README.md']
                found_files = [f for f in expected_files if (download_folder / f).exists()]

                if found_files:
                    return download_folder

            # With new UID-based structure, path should be deterministic
            return download_folder

        except Exception as e:
            logger.error(f"Error determining download folder for UID {uid}: {e}")
            return None

    def should_reuse_uid(self, existing_downloads: List[Dict[str, Any]],
                        session_id: Optional[str] = None) -> Optional[str]:
        """
        Determine if we should reuse an existing UID for consistency.

        Args:
            existing_downloads: List of existing downloads for the user
            session_id: Current session ID

        Returns:
            UID to reuse, or None to generate new UID
        """
        if not existing_downloads:
            return None

        try:
            # Prefer UID from same session
            if session_id:
                session_downloads = [d for d in existing_downloads
                                   if d.get('session_id') == session_id]
                if session_downloads:
                    # Use the most recent one in same session
                    latest = max(session_downloads,
                               key=lambda d: d.get('downloaded_at', ''))
                    return latest['uid']

            # Otherwise, use the most recent download overall
            latest = max(existing_downloads,
                        key=lambda d: d.get('downloaded_at', ''))
            return latest['uid']

        except Exception as e:
            logger.error(f"Error determining UID reuse: {e}")
            return None

    def prepare_download_cleanup(self, user_input: str, session_id: Optional[str] = None,
                               reuse_uid: bool = True) -> Tuple[Optional[str], int]:
        """
        Prepare for download by cleaning up existing downloads.

        Args:
            user_input: Username or user ID to download
            session_id: Optional session ID
            reuse_uid: Whether to reuse existing UID

        Returns:
            Tuple of (uid_to_use, cleanup_count)
        """
        try:
            # Find existing downloads
            existing_downloads = self.find_existing_downloads(user_input, session_id)

            uid_to_reuse = None
            if reuse_uid and existing_downloads:
                uid_to_reuse = self.should_reuse_uid(existing_downloads, session_id)

            # Clean up existing downloads
            cleanup_count = 0
            if existing_downloads:
                cleanup_count, cleaned_uids = self.cleanup_existing_downloads(existing_downloads)

                logger.info(f"Cleaned up {cleanup_count} existing downloads for user '{user_input}'")

                if uid_to_reuse:
                    logger.info(f"Will reuse UID: {uid_to_reuse}")

            return uid_to_reuse, cleanup_count

        except Exception as e:
            logger.error(f"Error preparing download cleanup for '{user_input}': {e}")
            return None, 0


# Global cleanup manager instance
_cleanup_manager: Optional[RobloxCleanupManager] = None


def get_cleanup_manager() -> RobloxCleanupManager:
    """Get global cleanup manager instance."""
    global _cleanup_manager
    if _cleanup_manager is None:
        _cleanup_manager = RobloxCleanupManager()
    return _cleanup_manager


def cleanup_existing_roblox_downloads(user_input: str, session_id: Optional[str] = None,
                                    reuse_uid: bool = True) -> Tuple[Optional[str], int]:
    """
    Convenience function to clean up existing downloads for a user.

    Args:
        user_input: Username or user ID
        session_id: Optional session ID to limit scope
        reuse_uid: Whether to reuse existing UID

    Returns:
        Tuple of (uid_to_use, cleanup_count)
    """
    cleanup_manager = get_cleanup_manager()
    return cleanup_manager.prepare_download_cleanup(user_input, session_id, reuse_uid)