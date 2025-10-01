import json
import time
from pathlib import Path
from typing import Dict, List, Optional, Callable

import requests


class RobloxAvatar3DDownloader:
    """Roblox 3D Avatar Downloader for OBJ/MTL/Textures"""

    def __init__(
        self,
        download_folder: str = "real_3d_avatars",
        progress_callback: Optional[Callable[[str, str], None]] = None
    ):
        """Initialize the downloader

        Args:
            download_folder: Base directory for downloads
            progress_callback: Optional callback for progress updates
        """
        self.download_folder = Path(download_folder)
        self.download_folder.mkdir(parents=True, exist_ok=True)
        self.progress_callback = progress_callback

        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            "Accept": "application/json",
        })

    def get_user_info(self, user_id: int) -> Optional[Dict]:
        """Get user information from Roblox API"""
        try:
            url = f"https://users.roblox.com/v1/users/{user_id}"
            resp = self.session.get(url, timeout=30)
            resp.raise_for_status()
            return resp.json()
        except requests.RequestException as e:
            print(f"❌ Failed to get user info (ID: {user_id}): {e}")
            return None

    def get_user_id_by_username(self, username: str) -> Optional[int]:
        """Get user ID by username"""
        try:
            url = "https://users.roblox.com/v1/usernames/users"
            data = {"usernames": [username]}
            resp = self.session.post(url, json=data, timeout=30)
            resp.raise_for_status()
            result = resp.json()
            if result.get("data"):
                user = result["data"][0]
                uid = user.get("id")
                uname = user.get("name")
                print(f"✅ Username '{username}' → ID: {uid} (@{uname})")
                return uid
            print(f"❌ Username '{username}' not found")
            return None
        except requests.RequestException as e:
            print(f"❌ Failed to search user ID ({username}): {e}")
            return None

    def resolve_user_input(self, user_input: str) -> Optional[int]:
        """Resolve user input to user ID (numeric or username)"""
        s = user_input.strip()
        if s.isdigit():
            uid = int(s)
            print(f"🔍 Recognized as user ID {uid}")
            return uid
        print(f"🔍 Searching for username '{s}'...")
        return self.get_user_id_by_username(s)

    def calculate_cdn_url(self, hash_id: str) -> str:
        """Calculate CDN URL from hash ID (2024 algorithm)"""
        i = 31
        for t in range(min(38, len(hash_id))):
            i ^= ord(hash_id[t])
        cdn_number = i % 8
        return f"https://t{cdn_number}.rbxcdn.com/{hash_id}"

    def get_avatar_3d_metadata(
        self,
        user_id: int,
        max_attempts: int = 10,
        delay: float = 1.0
    ) -> Optional[Dict]:
        """Get 3D avatar metadata with polling and backoff"""
        try:
            url = "https://thumbnails.roblox.com/v1/users/avatar-3d"
            params = {"userId": user_id}

            for attempt in range(1, max_attempts + 1):
                r1 = self.session.get(url, params=params, timeout=30)

                if r1.status_code == 429:
                    backoff = min(5.0, delay * attempt)
                    print(f"⏳ API rate limit (429). Waiting {backoff:.1f}s, retry {attempt}/{max_attempts}")
                    time.sleep(backoff)
                    continue

                r1.raise_for_status()
                data = r1.json()
                state = data.get("state")

                if state == "Completed":
                    image_url = data.get("imageUrl")
                    if not image_url:
                        print("❌ No imageUrl in response")
                        return None

                    r2 = self.session.get(image_url, timeout=30)
                    r2.raise_for_status()
                    try:
                        meta = r2.json()
                    except json.JSONDecodeError:
                        print("❌ JSON parsing failed (imageUrl response)")
                        return None

                    print("✅ 3D metadata acquired")
                    return meta

                if state in ("Pending", "InProgress", "InProgress_Unknown", None):
                    if attempt < max_attempts:
                        time.sleep(delay)
                        continue
                    print(f"⚠️ Avatar processing not completed: {state}")
                    return None

                print(f"⚠️ Unexpected state: {state}")
                return None

        except requests.RequestException as e:
            print(f"❌ Failed to get 3D metadata: {e}")
            return None
        except Exception as e:
            print(f"❌ Exception during 3D metadata processing: {e}")
            return None

    def download_file_from_hash(
        self,
        hash_id: str,
        file_path: Path,
        file_type: str = "File"
    ) -> bool:
        """Download file from hash ID (trying multiple CDN servers)"""
        headers = {
            "User-Agent": self.session.headers["User-Agent"],
            "Referer": "https://www.roblox.com/",
            "Accept": "*/*",
            "Connection": "keep-alive",
        }

        candidates: List[str] = []
        try:
            candidates.append(self.calculate_cdn_url(hash_id))
        except Exception as e:
            print(f"⚠️ Failed to calculate primary CDN URL: {e}")

        for n in range(8):
            u = f"https://t{n}.rbxcdn.com/{hash_id}"
            if u not in candidates:
                candidates.append(u)

        extra = [
            f"https://tr.rbxcdn.com/{hash_id}",
            f"https://c0.rbxcdn.com/{hash_id}",
            f"https://c1.rbxcdn.com/{hash_id}",
        ]
        for u in extra:
            if u not in candidates:
                candidates.append(u)

        print(f"➡️ Downloading {file_type}...")

        if self.progress_callback:
            try:
                self.progress_callback("downloading", file_type)
            except:
                pass

        for i, url in enumerate(candidates):
            try:
                label = "Primary server" if i == 0 else f"Backup server #{i}"
                print(f"   🔄 {label}: {url}")
                resp = self.session.get(url, headers=headers, stream=True, timeout=30, allow_redirects=True)
                if resp.status_code == 200:
                    with open(file_path, "wb") as f:
                        for chunk in resp.iter_content(chunk_size=8192):
                            if chunk:
                                f.write(chunk)
                    if file_path.exists() and file_path.stat().st_size > 0:
                        print(f"   ✅ {file_type} downloaded: {file_path}")

                        if self.progress_callback:
                            try:
                                self.progress_callback("completed", file_type)
                            except:
                                pass

                        return True
                    else:
                        print("   ⚠️ Empty file, trying next server")
                        if file_path.exists():
                            file_path.unlink()
                else:
                    print(f"   ❌ HTTP {resp.status_code}: {resp.reason}")
            except requests.Timeout:
                print("   ⏰ Timeout, trying next server")
            except requests.ConnectionError:
                print("   🔌 Connection error, trying next server")
            except requests.RequestException as e:
                print(f"   ❌ Request error: {e}")
            except Exception as e:
                print(f"   ❌ Exception: {e}")

            if i < len(candidates) - 1:
                time.sleep(0.4)

        print(f"   💔 Failed to download {file_type} from all CDN servers")

        if self.progress_callback:
            try:
                self.progress_callback("failed", file_type)
            except:
                pass

        return False

    def get_extended_avatar_info(self, user_id: int) -> Dict:
        """Collect extended information from multiple APIs (failures ignored)"""
        info: Dict = {
            "user_id": user_id,
            "collected_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "api_responses": {},
        }

        def safe_get(name: str, url: str):
            try:
                r = self.session.get(url, timeout=30)
                if r.status_code == 200:
                    info["api_responses"][name] = r.json()
            except Exception:
                pass

        safe_get("avatar_config", f"https://avatar.roblox.com/v1/users/{user_id}/avatar")
        safe_get("currently_wearing", f"https://avatar.roblox.com/v1/users/{user_id}/currently-wearing")
        safe_get(
            "thumbnails",
            f"https://thumbnails.roblox.com/v1/users/avatar?userIds={user_id}&size=720x720&format=Png&isCircular=false",
        )
        safe_get("games", f"https://games.roblox.com/v2/users/{user_id}/games?accessFilter=Public&limit=10")
        safe_get("groups", f"https://groups.roblox.com/v2/users/{user_id}/groups/roles")
        return info

    def _infer_rig_from_obj(self, obj_structure: Dict) -> str:
        """Infer rig type from OBJ structure (R6/R15)"""
        try:
            groups = [g.get("name", "").lower() for g in obj_structure.get("groups", [])]
            r15_markers = ("upper", "lower", "hand", "foot", "upperarm", "lowerarm", "upperleg", "lowerleg")
            if any(m in name for name in groups for m in r15_markers):
                return "R15"
            if len(groups) <= 8:
                return "R6"
        except Exception:
            pass
        return "Unknown"

    def _extract_avatar_type(self, extended_info: Optional[Dict], obj_structure: Optional[Dict]) -> str:
        """Extract avatar type from API or OBJ structure"""
        try:
            if extended_info and extended_info.get("api_responses", {}).get("avatar_config"):
                avatar_config = extended_info["api_responses"]["avatar_config"]
                at = avatar_config.get("playerAvatarType")
                if isinstance(at, str) and at.strip():
                    return at
        except Exception:
            pass

        if obj_structure:
            return self._infer_rig_from_obj(obj_structure)
        return "Unknown"

    def analyze_obj_structure(self, obj_path: Path) -> Dict:
        """Analyze OBJ file structure"""
        result: Dict = {
            "file_path": str(obj_path),
            "analyzed_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "groups": [],
            "materials": [],
            "vertices": 0,
            "faces": 0,
            "normals": 0,
            "texture_coords": 0,
            "body_parts": [],
        }
        with open(obj_path, "r", encoding="utf-8", errors="ignore") as f:
            for line_num, raw in enumerate(f, 1):
                line = raw.strip()
                if not line or line.startswith("#"):
                    continue
                if line.startswith("v "):
                    result["vertices"] += 1
                elif line.startswith("vn "):
                    result["normals"] += 1
                elif line.startswith("vt "):
                    result["texture_coords"] += 1
                elif line.startswith("f "):
                    result["faces"] += 1
                elif line.startswith("g "):
                    name = line[2:].strip()
                    g = {"name": name, "line": line_num, "type": self.classify_body_part(name)}
                    result["groups"].append(g)
                    if g["type"] != "unknown":
                        result["body_parts"].append(g)
                elif line.startswith("usemtl "):
                    mtl = line[7:].strip()
                    if mtl and mtl not in result["materials"]:
                        result["materials"].append(mtl)
        return result

    def classify_body_part(self, group_name: str) -> str:
        """Classify body part from group name"""
        n = group_name.lower()
        mapping = {
            "head": ["player1", "head"],
            "torso": ["player2", "torso", "chest"],
            "left_arm": ["player3", "leftarm", "left_arm"],
            "right_arm": ["player4", "rightarm", "right_arm"],
            "left_leg": ["player5", "leftleg", "left_leg"],
            "right_leg": ["player6", "rightleg", "right_leg"],
            "hat": ["player7", "hat", "cap", "helmet"],
            "hair": ["player8", "hair"],
            "face": ["player9", "face"],
            "shirt": ["player10", "shirt", "top"],
            "pants": ["player11", "pants", "bottom"],
            "shoes": ["player12", "shoes", "boot"],
            "accessory": ["player13", "player14", "player15", "accessory", "gear"],
            "handle": ["handle", "grip", "tool"],
        }
        for part, keys in mapping.items():
            if any(k in n for k in keys):
                return part
        return "unknown"

    def save_metadata(
        self,
        user_info: Dict,
        metadata: Dict,
        user_folder: Path,
        extended_info: Optional[Dict] = None,
    ) -> None:
        """Save metadata and README"""
        obj_structure = None
        if extended_info and isinstance(extended_info, dict):
            obj_structure = extended_info.get("obj_structure")

        avatar_type = self._extract_avatar_type(extended_info, obj_structure)

        full = {
            "user_info": user_info,
            "avatar_3d_metadata": metadata,
            "download_timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "avatar_type": avatar_type,
            "api_info": {
                "source": "Roblox Avatar 3D API",
                "endpoint": "https://thumbnails.roblox.com/v1/users/avatar-3d",
                "cdn_calculation": "Updated 2024 hash algorithm (heuristic)",
            },
        }
        if extended_info is not None:
            full["extended_avatar_info"] = extended_info

        with open(user_folder / "metadata.json", "w", encoding="utf-8") as f:
            json.dump(full, f, indent=2, ensure_ascii=False)

        self.create_extended_readme(user_info, metadata, user_folder, extended_info)

    def create_extended_readme(
        self,
        user_info: Dict,
        metadata: Dict,
        user_folder: Path,
        extended_info: Optional[Dict] = None,
    ) -> None:
        """Generate README file"""
        camera = metadata.get("camera", {})
        aabb = metadata.get("aabb", {})

        obj_structure = None
        if extended_info and isinstance(extended_info, dict):
            obj_structure = extended_info.get("obj_structure")
        avatar_type = self._extract_avatar_type(extended_info, obj_structure)

        lines: List[str] = [
            "# 3D Avatar Model Usage Guide",
            "",
            "## 📁 Downloaded Files",
            "- avatar.obj: 3D mesh file (OBJ)",
            "- avatar.mtl: Material info file (MTL)",
            "- textures/: Texture images",
            "- metadata.json: Complete metadata",
            "",
            "## 🎮 User Information",
            f"- Name: {user_info.get('displayName')} (@{user_info.get('name')})",
            f"- User ID: {user_info.get('id')}",
            f"- Created: {user_info.get('created', 'N/A')}",
            f"- Downloaded: {time.strftime('%Y-%m-%d %H:%M:%S')}",
            f"- Avatar Type: {avatar_type}",
            "",
            "## 📐 3D Model Information",
            f"- Camera Position: {camera.get('position', 'N/A')}",
            f"- Camera FOV: {camera.get('fov', 'N/A')}",
            f"- Bounding Box: {aabb.get('min', 'N/A')} ~ {aabb.get('max', 'N/A')}",
            "",
            "## 🛠️ Usage",
            "",
            "### Blender",
            "1. File > Import > Wavefront (.obj)",
            "2. Select avatar.obj and import (MTL applied automatically)",
            "",
            "### Unity",
            "1. Copy all files to Assets folder",
            "2. Drag avatar.obj to scene",
            "3. Manually connect textures to materials if needed",
            "",
            "### Three.js Example",
            "```javascript",
            "import { OBJLoader } from 'three/examples/jsm/loaders/OBJLoader.js';",
            "import { MTLLoader } from 'three/examples/jsm/loaders/MTLLoader.js';",
            "",
            "const mtlLoader = new MTLLoader();",
            "mtlLoader.load('avatar.mtl', (materials) => {",
            "  materials.preload();",
            "  const objLoader = new OBJLoader();",
            "  objLoader.setMaterials(materials);",
            "  objLoader.load('avatar.obj', (object) => {",
            "    scene.add(object);",
            "  });",
            "});",
            "```",
            "",
            "## ⚠️ Notes",
            "- This model is in Roblox R15/R6 format",
            "- Please comply with Roblox Terms of Service for commercial use",
            "",
            "## 🔧 Troubleshooting",
            "- If textures are missing, check MTL file paths",
            "- If model appears transparent, check material transparency/alpha settings",
            "",
        ]

        readme = "\n".join(lines)
        with open(user_folder / "README.md", "w", encoding="utf-8") as f:
            f.write(readme)
