"""HTTP client for MegaMelange API"""
import requests
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class APIClient:
    """Client for communicating with MegaMelange HTTP bridge"""

    def __init__(self, host: str = 'localhost', port: int = 8080):
        """
        Initialize API client.

        Args:
            host: HTTP bridge hostname
            port: HTTP bridge port
        """
        self.base_url = f"http://{host}:{port}"
        self.session = requests.Session()

    def get(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Send GET request to API.

        Args:
            endpoint: API endpoint path
            params: Query parameters

        Returns:
            Response data as dict

        Raises:
            Exception: If request fails
        """
        url = f"{self.base_url}{endpoint}"
        try:
            response = self.session.get(url, params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"GET request failed: {e}")
            raise Exception(f"API request failed: {e}")

    def post(self, endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Send POST request to API.

        Args:
            endpoint: API endpoint path
            data: Request body data

        Returns:
            Response data as dict

        Raises:
            Exception: If request fails
        """
        url = f"{self.base_url}{endpoint}"
        try:
            response = self.session.post(url, json=data)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"POST request failed: {e}")
            raise Exception(f"API request failed: {e}")

    def get_selected_assets(self) -> Dict[str, Any]:
        """
        Get currently selected assets in Unreal Editor.

        Returns:
            Dict with assets information
        """
        return self.post("/api/assets/selected", {})

    def preview_rename(self, naming_convention: str = "by_type",
                      custom_prefixes: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """
        Preview asset renames without applying.

        Args:
            naming_convention: Naming convention to apply
            custom_prefixes: Optional custom prefix mapping

        Returns:
            Dict with preview information
        """
        data = {
            "naming_convention": naming_convention
        }
        if custom_prefixes:
            data["custom_prefixes"] = custom_prefixes

        return self.post("/api/assets/preview-rename", data)

    def rename_assets(self, operations: list) -> Dict[str, Any]:
        """
        Rename assets in batch.

        Args:
            operations: List of rename operations
                [{"old_path": "/Game/...", "new_name": "NewName"}, ...]

        Returns:
            Dict with rename results
        """
        return self.post("/api/assets/rename", {"operations": operations})
